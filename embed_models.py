from config import EMBED_MODEL
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np

def get_embedder():
    if EMBED_MODEL.startswith("avichr/"):
        tok = AutoTokenizer.from_pretrained(EMBED_MODEL)
        mod = AutoModel.from_pretrained(EMBED_MODEL, add_pooling_layer=False)

        def embed(texts):
            embs = []
            for text in texts:
                tokens = tok(
                    text,
                    return_tensors="pt",
                    padding="max_length",
                    truncation=True,
                    max_length=512
                )
                with torch.no_grad():
                    output = mod(**tokens)
                    emb = output.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
                    embs.append(emb)
            return np.array(embs)

        return embed

    else:
        model = SentenceTransformer(EMBED_MODEL)

        def embed(texts):
            return model.encode(texts, convert_to_numpy=True)

        return embed
