from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
from src.config import EMBEDDING_MODEL


class Embedder:
    """Generates embeddings using sentence-transformers."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"Model loaded. Embedding dimension: {self.embedding_dim}")

    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        return self.model.encode(text, convert_to_numpy=True)

    def embed_batch(self, texts: List[str], batch_size: int = 32, show_progress: bool = True) -> np.ndarray:
        """Generate embeddings for a batch of texts."""
        return self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )

    def get_embedding_dim(self) -> int:
        """Return the dimension of embeddings."""
        return self.embedding_dim
