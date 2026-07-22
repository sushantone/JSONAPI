# What: Import Path for building filesystem paths.
# Why:  We need a reliable way to locate the cached dataset folder on any operating system.
from pathlib import Path

# What: Import the function that saves model weights after training.
# Why:  Training and serving are separate scripts; saving bridges them.
from api import generate_text
from save_model import save_model
# What: Import the TinyTransformer model class.
# Why:  We must instantiate the same architecture we will train and later load in api.py.
from tiny_transformer import TinyTransformer
# What: Import math (perplexity), torch (tensors), nn (layers), F (loss functions).
# Why:  Training requires numerical computation, loss calculation, and optimization.
import math, torch, torch.nn as nn, torch.nn.functional as F
# What: Import PyTorch's DataLoader utility.
# Why:  Included for potential batching patterns; this script batches manually instead.
from torch.utils.data import DataLoader
# What: Import Hugging Face dataset loaders (download and local cache).
# Why:  WikiText-2 is hosted on Hugging Face; these functions fetch or reload it.
from datasets import load_dataset, load_from_disk
# What: Import the GPT-2 tokenizer.
# Why:  Text must become token IDs before the model can learn from it.
import tiktoken
# What: Import tqdm for a terminal progress bar.
# Why:  Training loops can take minutes; a progress bar shows that work is happening.
from tqdm import tqdm

# --- STEP 1: Load training data ---

# What: Compute the local folder path: project_root/data/wikitext2.
# Why:  Caching the dataset avoids re-downloading ~100MB on every training run.
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "wikitext2"
# What: Check whether we already saved a copy of the dataset locally.
# Why:  A cache hit means faster startup and no internet dependency.
if DATA_DIR.exists():
    # What: Load the dataset from the on-disk cache.
    # Why:  Reading from disk is much faster than downloading from Hugging Face again.
    dataset = load_from_disk(str(DATA_DIR))
# What: Branch taken on first run when no cache exists yet.
# Why:  Someone cloning the repo still needs a way to obtain training data automatically.
else:
    # What: Download WikiText-2 (raw Wikipedia text) from Hugging Face Hub.
    # Why:  We need real text for the model to learn language patterns from.
    dataset = load_dataset("Salesforce/wikitext", "wikitext-2-raw-v1")
    # What: Create the parent data/ directory if it is missing.
    # Why:  save_to_disk will fail if the target folder path does not exist.
    DATA_DIR.parent.mkdir(parents=True, exist_ok=True)
    # What: Write the downloaded dataset to disk for future runs.
    # Why:  Next training run will hit the if-branch above and skip the download.
    dataset.save_to_disk(str(DATA_DIR))

# What: Take the first 5000 documents from the training split.
# Why:  Full WikiText-2 is large; a subset keeps training fast on a laptop.
train_texts = dataset["train"]["text"][:5000]
# What: Take 1000 documents from the validation split.
# Why:  Validation data must never be used for weight updates — only to measure
#       whether the model generalizes to unseen text.
val_texts = dataset["validation"]["text"][:1000]

# --- STEP 2: Tokenization ---

# What: Load the GPT-2 byte-pair encoding tokenizer.
# Why:  The model's embedding table has one row per token; we need a fixed mapping
#       from text fragments to integers that matches that table size.
enc = tiktoken.get_encoding("gpt2")
# What: Define a helper that tokenizes a list of strings.
# Why:  Encapsulates the encode step so we don't repeat enc.encode(t) everywhere.
def tokenize(texts): return [enc.encode(t) for t in texts]
# What: Convert all training documents to lists of token IDs.
# Why:  The training loop operates on numbers, not raw strings.
train_tokens = tokenize(train_texts)
# What: Convert all validation documents to lists of token IDs.
# Why:  Evaluation uses the same encoding scheme as training for fair comparison.
val_tokens = tokenize(val_texts)

# --- STEP 3: Flatten token streams ---

# What: Concatenate all training token lists into one 1D PyTorch tensor.
# Why:  Language-model training treats text as one continuous stream of tokens;
#       random windows can then be cut from anywhere in that stream.
train_ids = torch.tensor([id for seq in train_tokens for id in seq], dtype=torch.long)
# What: Same flattening for validation tokens.
# Why:  get_batch() expects a single 1D tensor it can sample windows from.
val_ids = torch.tensor([id for seq in val_tokens for id in seq], dtype=torch.long)

# --- STEP 4: Batch sampling ---

# What: Set the context window length to 64 tokens per training example.
# Why:  The model has limited memory; fixed-length chunks make batching efficient.
#       64 is a compromise between context and speed for this tiny model.
block_size = 64
# What: Define a function that returns random (input, target) batch pairs.
# Why:  Each training step needs many examples at once; random windows provide
#       diverse contexts and prevent memorizing document order.
def get_batch(data, batch_size=16):
    # What: Sample batch_size random starting indices in the token stream.
    # Why:  Random positions expose the model to varied contexts each step,
    #       improving generalization compared to always reading sequentially.
    ix = torch.randint(len(data)-block_size, (batch_size,))
    # What: Build input tensor x — 64 consecutive tokens starting at each index.
    # Why:  x is what the model sees; it must predict the token that follows each position.
    x = torch.stack([data[i:i+block_size] for i in ix])
    # What: Build target tensor y — same windows shifted right by one token.
    # Why:  At position t the correct answer is token t+1; shifting creates those labels.
    y = torch.stack([data[i+1:i+block_size+1] for i in ix])
    # What: Return both tensors with shape (batch_size, block_size).
    # Why:  The training loop unpacks these as xb (inputs) and yb (correct next tokens).
    return x, y




# --- STEP 5: Model, device, optimizer ---

# What: Choose "cuda" (GPU) if available, otherwise "cpu".
# Why:  GPUs parallelize matrix math and can train orders of magnitude faster.
device = "cuda" if torch.cuda.is_available() else "cpu"
# What: Create the model and move all parameters to the chosen device.
# Why:  vocab_size must match the tokenizer so embedding and output layers align.
model = TinyTransformer(vocab_size=enc.n_vocab).to(device)
# What: Create an AdamW optimizer with learning rate 0.001.
# Why:  The optimizer applies gradient updates; AdamW is a robust default for transformers.
#       lr controls how big each weight update is — too high diverges, too low learns slowly.
opt = torch.optim.AdamW(model.parameters(), lr=1e-3)

# --- STEP 6: Training loop ---

# What: Repeat the training procedure for 3 epochs.
# Why:  One pass is rarely enough; multiple epochs let the model refine its weights.
#       We keep epochs small because this is a demo on a subset of data.
for epoch in range(3):
    # What: Set the model to training mode.
    # Why:  Enables behaviors like dropout (if present) that help learning but hurt inference.
    model.train()
    # What: Run 200 optimization steps per epoch with a progress bar.
    # Why:  Each step processes one mini-batch; 200 steps × 3 epochs = 600 updates total.
    for step in tqdm(range(200)):
        # What: Sample a fresh random batch of inputs and targets from training tokens.
        # Why:  Stochastic (random) batches reduce overfitting to any single document order.
        xb, yb = get_batch(train_ids)
        # What: Move batch tensors to the same device as the model.
        # Why:  PyTorch requires inputs and parameters to live on the same GPU/CPU.
        xb, yb = xb.to(device), yb.to(device)
        # What: Forward pass — compute predicted logits for every position.
        # Why:  We need predictions before we can measure how wrong they are (loss).
        logits = model(xb)
        # What: Compute cross-entropy loss between predictions and true next tokens.
        # Why:  Cross-entropy penalizes confident wrong guesses heavily, encouraging
        #       the model to assign high probability to the correct next token.
        #       .view(-1, ...) merges batch and sequence dims for the loss function.
        loss = F.cross_entropy(logits.view(-1, logits.size(-1)), yb.view(-1))
        # What: Reset stored gradients from the previous step to zero.
        # Why:  PyTorch accumulates gradients by default; without zeroing, old gradients
        #       would pollute the current update.
        opt.zero_grad()
        # What: Backpropagate — compute gradients of loss w.r.t. every weight.
        # Why:  Gradients tell the optimizer which direction to nudge each weight to reduce loss.
        loss.backward()
        # What: Apply the optimizer step — actually update all model weights.
        # Why:  This is where learning happens; each step should slightly improve predictions.
        opt.step()
    # What: Print the loss value from the last batch of this epoch.
    # Why:  A decreasing loss over epochs is a simple signal that training is working.
    print(f"Epoch {epoch} loss: {loss.item():.4f}")

# --- STEP 7: Validation (perplexity) ---

# What: Switch model to evaluation mode.
# Why:  Disables training-only randomness so we measure true predictive quality.
model.eval()
# What: Disable gradient computation for the evaluation block.
# Why:  We are not updating weights here; skipping gradients saves memory and time.
with torch.no_grad():
    # What: Sample a larger batch (64 windows) from validation tokens.
    # Why:  A bigger batch gives a less noisy estimate of validation performance.
    xb, yb = get_batch(val_ids, batch_size=64)
    # What: Move validation batch to the model's device.
    # Why:  Same device requirement as during training.
    xb, yb = xb.to(device), yb.to(device)
    # What: Forward pass on validation data.
    # Why:  We need predictions on text the model was never trained on.
    logits = model(xb)
    # What: Compute cross-entropy loss on validation batch.
    # Why:  Same metric as training, but on held-out data — reveals overfitting.
    val_loss = F.cross_entropy(logits.view(-1, logits.size(-1)), yb.view(-1))
    # What: Convert loss to perplexity via exp(loss).
    # Why:  Perplexity is easier to interpret: "how many equally likely choices is the
    #       model as confused as?" Lower is better. exp(4) ≈ 55 means ~55-way uncertainty.
    perplexity = math.exp(val_loss.item())
    # What: Print the validation perplexity to the console.
    # Why:  Gives a single number to compare across training runs or model sizes.
    print(f"Validation perplexity: {perplexity:.2f}")

# --- STEP 8: Text generation demo ---



# What: Call generate_text with a sample prompt and print the result.
# Why:  Immediate feedback after training so we can eyeball output quality.
print(generate_text("The little robot", model = model, enc = enc).body)
# What: Save trained weights to slm_model.pt.
# Why:  api.py loads this file to serve generations without re-running training.
save_model(model, enc)
