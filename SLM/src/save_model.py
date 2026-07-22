# What: Import the model class definition.
# Why:  Loading weights requires rebuilding the exact same architecture first;
#       weights alone are meaningless without matching layer shapes.
from tiny_transformer import TinyTransformer
# What: Import PyTorch for file I/O on tensors and model state.
# Why:  torch.save / torch.load are the standard way to persist trained models.
import torch

# What: Define a function that writes trained weights to disk.
# Why:  Training is expensive; saving lets us reuse the model in api.py without retraining.
#       enc is accepted for a consistent API but not used inside this function.
def save_model(model, enc):
    # What: Extract only the learned weight tensors and save them to slm_model.pt.
    # Why:  state_dict() excludes optimizer state and buffers we don't need at inference time,
    #       keeping the file small and focused on what the model learned.
    torch.save(model.state_dict(), "slm_model.pt")

# What: Define a function that reconstructs the model and loads saved weights.
# Why:  api.py and other scripts need a ready-to-use model without running training again.
def load_model(enc):
    # What: Instantiate a fresh TinyTransformer with the correct vocabulary size.
    # Why:  Layer shapes (especially the embedding and output layers) must match the
    #       tokenizer — enc.n_vocab tells us how many rows/columns those layers need.
    model = TinyTransformer(vocab_size=enc.n_vocab)
    # What: Read slm_model.pt from disk and copy values into the model's layers.
    # Why:  This restores the knowledge learned during training into the empty architecture.
    model.load_state_dict(torch.load("slm_model.pt"))
    # What: Switch the model to evaluation (inference) mode.
    # Why:  Disables dropout and other training-only randomness so predictions are
    #       consistent and reproducible when serving text generation.
    model.eval()
    # What: Return the loaded model to the caller.
    # Why:  The caller (e.g. api.py) can immediately call model(x) to generate text.
    return model
