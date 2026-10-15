import numpy as np
from sentence_transformers import SentenceTransformer
import torch

class STEmbedder:
    """sentence-transformers model behind a small, swappable interface."""

    def __init__(self, model_name: str = "BAAI/bge-m3", max_tokens: int = 4096, batch_size: int = 64):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(model_name, device=device)
        if device == "cuda":
            self.model.half()                      # fp16: ~2x faster on T4
        self.model.max_seq_length = max_tokens
        self.name, self.max_tokens, self.batch_size = model_name, max_tokens, batch_size
        self.device = device
        self.dim = self.model.get_embedding_dimension()   # renamed in newer versions

    def count_tokens(self, texts: list[str]) -> list[int]:
        return [len(ids) for ids in self.model.tokenizer(texts)["input_ids"]]

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(texts, batch_size=self.batch_size,
                                 normalize_embeddings=True, show_progress_bar=True)

    def embed_query(self, text: str) -> np.ndarray:
        return self.model.encode([text], normalize_embeddings=True)[0]