"""Embedding generation using SentenceTransformers or custom models."""

from __future__ import annotations

import hashlib
import logging
import os

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


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
        model_name: str = "all-MiniLM-L6-v2",
        device: str | None = None,
        cache_folder: str | None = None,
        offline: bool | None = None,
    ) -> None:
        """
        Initialize embedder with specified model.

        Args:
            model_name: HuggingFace model name or path
            device: 'cuda', 'cpu', or None (auto-detect)
            cache_folder: Where to cache downloaded models
            offline: Force lightweight offline embedding (no model download)
        """
        self.model_name = model_name
        self._use_fallback = (
            offline
            if offline is not None
            else os.getenv("EMBEDDER_OFFLINE", "0") == "1"
        )

        if not self._use_fallback:
            try:
                self.model = SentenceTransformer(
                    model_name, device=device, cache_folder=cache_folder
                )
                self.dimension = self.model.get_sentence_embedding_dimension()
                return
            except Exception as exc:
                logger.warning(
                    "Falling back to lightweight embedder for %s: %s", model_name, exc
                )
                self._use_fallback = True

        # Lightweight deterministic fallback to avoid external downloads.
        self.model = None
        self.dimension = 384

    def embed(self, text: str) -> np.ndarray:
        """
        Embed a single text string.

        Args:
            text: Input text

        Returns:
            1D numpy array of shape (dimension,)
        """
        if self._use_fallback:
            return self._fallback_encode(text)

        return self.model.encode(text, convert_to_numpy=True)

    def embed_batch(
        self, texts: list[str], batch_size: int = 32, show_progress: bool = True
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
        if self._use_fallback:
            return np.vstack([self._fallback_encode(text) for text in texts])

        return self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )

    def save(self, path: str) -> None:
        """Save model to disk."""
        self.model.save(path)

    @classmethod
    def load(cls, path: str, device: str | None = None) -> Embedder:
        """Load model from disk."""
        embedder = cls.__new__(cls)
        embedder.model = SentenceTransformer(path, device=device)
        embedder.model_name = path
        embedder.dimension = embedder.model.get_sentence_embedding_dimension()
        return embedder

    def __repr__(self) -> str:
        return f"Embedder(model='{self.model_name}', dim={self.dimension})"

    def _fallback_encode(self, text: str) -> np.ndarray:
        """Deterministic, lightweight embedding using hashed token bucket."""
        vec = np.zeros(self.dimension, dtype=float)
        tokens = text.lower().split()
        if not tokens:
            return vec

        for token in tokens:
            # Token-level bucket
            token_hash = int(hashlib.sha256(token.encode()).hexdigest(), 16)
            vec[token_hash % self.dimension] += 1.0

            # Character n-gram buckets to capture fuzzy similarity
            for n in (2, 3):
                for i in range(len(token) - n + 1):
                    ngram = token[i : i + n]
                    ngram_hash = int(hashlib.sha256(ngram.encode()).hexdigest(), 16)
                    vec[ngram_hash % self.dimension] += 0.5

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec
