# What: Import FastAPI (web framework) and Response (HTTP response wrapper).
# Why:  We expose the trained model as a REST API so any client can request generated text.
from fastapi import FastAPI, Response
# What: Import our TinyTransformer class.
# Why:  load_model() rebuilds this architecture when the server starts.
from tiny_transformer import TinyTransformer
# What: Import PyTorch and its functional helpers (softmax, etc.).
# Why:  Generation runs tensor math — converting logits to probabilities and sampling tokens.
import torch, torch.nn.functional as F
# What: Import the GPT-2 tokenizer library.
# Why:  The model was trained on GPT-2 token IDs; we must use the same mapping at inference.
import tiktoken

# What: Import the helper that loads weights from slm_model.pt.
# Why:  Separates "how to load" from "how to serve" so training and API stay decoupled.
from save_model import load_model

def load_tokenizer_explicit():
    # What: Create a GPT-2 tokenizer instance.
    # Why:  User prompts arrive as plain text; the model only understands integer token IDs.
    #       Using the same tokenizer as training prevents vocabulary mismatches.
    enc = tiktoken.get_encoding("gpt2")
    return enc

def load_model_explicit(enc):
    # What: Load the trained model once when the server starts.
    # Why:  Loading from disk on every HTTP request would be far too slow; startup load
    #       keeps each /generate call fast.
    loaded_model = load_model(enc)
    return loaded_model

# What: Create the FastAPI application object.
# Why:  This is the central object that registers routes and handles incoming requests.
app = FastAPI()

# What: Register the URL path /generate for HTTP GET requests.
# Why:  Clients call this endpoint with a prompt (?q=...) to receive generated text.
@app.get("/generate")
# What: Define the handler function. q = prompt string, max_tokens = length limit.
# Why:  FastAPI automatically reads query parameters from the URL and validates types.
def generate_text(q: str, max_tokens: int = 50, model = None, enc = None):
    if enc is None:
        enc = load_tokenizer_explicit()
    if model is None:
        model = load_model_explicit(enc)

    # What: Convert the user's text prompt into a list of integer token IDs.
    # Why:  The model's input layer expects numbers, not raw strings.
    tokens = enc.encode(q)
    # What: Wrap token IDs in a PyTorch tensor and add a batch dimension.
    # Why:  The model always expects shape (batch_size, seq_len); unsqueeze(0) makes
    #       a batch of 1 even when we only have a single prompt.
    x = torch.tensor(tokens, dtype=torch.long).unsqueeze(0)

    # What: Loop max_tokens times to grow the sequence one token at a time.
    # Why:  Language models predict one next token per step; we repeat until we
    #       have generated enough new text (autoregressive generation).
    for _ in range(max_tokens):
        # What: Enter a context where PyTorch does not build the computation graph.
        # Why:  We are only predicting, not training — skipping gradients saves memory
        #       and speeds up each forward pass.
        with torch.no_grad():
            # What: Run the current sequence through the model.
            # Why:  This produces logits — raw scores for every vocabulary token at
            #       every position in the sequence.
            logits = model (x)
            # What: Keep only the logits at the last position of the first batch item.
            # Why:  We want to predict what comes *after* the current end of the text;
            #       earlier positions are already fixed and irrelevant for the next token.
            next_token_logits = logits[0, -1, :]
            # What: Convert logits to probabilities via softmax, with temperature 0.8.
            # Why:  Probabilities let us sample naturally. Temperature < 1 sharpens the
            #       distribution so the model favors more confident (likely) words.
            probs = F.softmax(next_token_logits / 0.8, dim=-1)
            # What: Randomly draw one token index according to the probability distribution.
            # Why:  Pure argmax (always pick the top word) produces repetitive text;
            #       sampling adds variety while still respecting what the model learned.
            next_token = torch.multinomial(probs, num_samples=1)
        # What: Append the sampled token to the end of the sequence tensor.
        # Why:  The next loop iteration needs the longer sequence as context to predict
        #       the following token — each new word conditions on all previous words.
        x = torch.cat([x, next_token.unsqueeze(0)], dim=1)

    # What: Decode token IDs back to a string and return as plain-text HTTP response.
    # Why:  The client expects readable text, not raw numbers; Response sets the correct
    #       Content-Type so browsers and tools display it properly.
    return Response(content=enc.decode(x[0].tolist()), media_type="text/plain")
