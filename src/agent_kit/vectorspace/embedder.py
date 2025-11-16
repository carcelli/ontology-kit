"""Embedding generation using SentenceTransformers or custom models."""

import numpy as np
from sentence_transformers import SentenceTransformer


class Embedder:
    """
    Wrapper for embedding text/code/tasks into high-dimensional vectors.

    Uses SentenceTransformer by default; supports custom models via extend.

    Example:
        >>> embedder = Embedder(model_name='all-MiniLM-L6-v2')
        >>> embeddings = embedder.embed_batch(['Task 1', 'Task 2'])
        >>> embeddings.shape
        (2, 384)
    """

    def __init__(
        self,
        model_name: str = 'all-MiniLM-L6-v2',
        device: str | None = None,
        cache_folder: str | None = None
    ) -> None:
        """
        Initialize embedder with specified model.

        Args:
            model_name: HuggingFace model name or path
            device: 'cuda', 'cpu', or None (auto-detect)
            cache_folder: Where to cache downloaded models
        """
        self.model_name = model_name
        self.model = SentenceTransformer(
            model_name,
            device=device,
            cache_folder=cache_folder
        )
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> np.ndarray:
        """
        Embed a single text string.

        Args:
            text: Input text

        Returns:
            1D numpy array of shape (dimension,)
        """
        return self.model.encode(text, convert_to_numpy=True)

    def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Embed a batch of texts efficiently.

        Args:
            texts: List of input strings
            batch_size: Number of texts to process per batch
            show_progress: Whether to show progress bar

        Returns:
            2D numpy array of shape (len(texts), dimension)
        """
        return self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )

    def save(self, path: str) -> None:
        """Save model to disk."""
        self.model.save(path)

    @classmethod
    def load(cls, path: str, device: str | None = None) -> 'Embedder':
        """Load model from disk."""
        embedder = cls.__new__(cls)
        embedder.model = SentenceTransformer(path, device=device)
        embedder.model_name = path
        embedder.dimension = embedder.model.get_sentence_embedding_dimension()
        return embedder

    def __repr__(self) -> str:
        return f"Embedder(model='{self.model_name}', dim={self.dimension})"

