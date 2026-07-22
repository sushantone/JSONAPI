# What: Load PyTorch and its neural-network module (nn) for building layers.
# Why:  Every layer below (Embedding, Transformer, Linear) comes from this library.
import torch, torch.nn as nn

# What: Declare a custom language-model class that inherits from nn.Module.
# Why:  nn.Module is PyTorch's standard way to define models; it handles parameters,
#       saving, and GPU movement automatically.
class TinyTransformer(nn.Module):
    # What: Constructor — runs once when we create a new model object.
    # Why:  All layers must be created here so they exist before any data flows through.
    #       vocab_size = number of unique tokens. n_embd = vector size per token.
    #       n_head = parallel attention views. n_layer = depth of the network.
    def __init__(self, vocab_size, n_embd=128, n_head=2, n_layer=2):
        # What: Call the parent nn.Module initializer.
        # Why:  Without this, PyTorch cannot register our layers as trainable parameters.
        super().__init__()
        # What: Create an embedding lookup table of shape (vocab_size, n_embd).
        # Why:  Neural networks need numbers, not raw token IDs. Embeddings turn each
        #       integer token into a learned vector the model can do math on.
        self.embed = nn.Embedding(vocab_size, n_embd)
        # What: Build a list of n_layer transformer encoder blocks.
        # Why:  One layer can only capture simple patterns. Stacking layers lets the
        #       model learn richer relationships between words in a sentence.
        self.blocks = nn.ModuleList([
            # What: One transformer block — self-attention plus a small feed-forward network.
            # Why:  Attention lets each token gather context from other tokens in the sequence
            #       (e.g. "it" can look back at "robot" to understand what "it" refers to).
            nn.TransformerEncoderLayer(d_model=n_embd, nhead=n_head, dim_feedforward=256)
            # What: Repeat the block n_layer times (default 2).
            # Why:  Deeper stacks improve expressiveness; we keep it small for fast training.
            for _ in range(n_layer)
        ])
        # What: Layer normalization over the n_embd dimension.
        # Why:  Keeps activations in a stable numeric range so training does not explode
        #       or vanish before the final prediction layer.
        self.ln = nn.LayerNorm(n_embd)
        # What: A linear (fully connected) layer from n_embd → vocab_size.
        # Why:  After understanding context, we must output one score per possible next
        #       token so the model can choose (or sample) the most likely word.
        self.fc = nn.Linear(n_embd, vocab_size)

    # What: Define the forward pass — how input data flows through the model.
    # Why:  PyTorch calls this automatically when we write model(x). Training and
    #       generation both depend on this single path through the network.
    #       x shape: (batch_size, sequence_length) of token IDs.
    def forward(self, x):
        # What: Replace each token ID with its embedding vector.
        # Why:  This is the entry point from discrete tokens into continuous math;
        #       shape becomes (batch, seq_len, n_embd).
        x = self.embed(x)
        # What: Pass embeddings through every transformer block in order.
        # Why:  Each block refines representations using context from the full sequence;
        #       later blocks see increasingly abstract patterns.
        for block in self.blocks: x = block(x)
        # What: Apply layer normalization to the final hidden states.
        # Why:  Prepares stable inputs for the output layer so logits are well-scaled.
        x = self.ln(x)
        # What: Project each position to vocab_size raw scores (logits).
        # Why:  Logits are the model's answer to "how likely is each token here?"
        #       Shape: (batch, seq_len, vocab_size).
        return self.fc(x)
