"""Vector index using FAISS for fast k-NN retrieval."""

import pickle
from typing import Any

import faiss
import numpy as np


class VectorIndex:
    """
    FAISS-based vector index for efficient similarity search.
    
    Supports add, query, save/load operations with metadata tracking.
    
    Example:
        >>> index = VectorIndex(dim=384)
        >>> index.add(embeddings, ids=list(range(100)))
        >>> results = index.query(query_vector, k=10)
        >>> results[0]['id'], results[0]['distance']
        (42, 0.12)
    """

    def __init__(self, dim: int, metric: str = 'cosine') -> None:
        """
        Initialize vector index.
        
        Args:
            dim: Dimensionality of vectors
            metric: 'cosine' or 'euclidean'
        """
        self.dim = dim
        self.metric = metric

        # Create FAISS index
        if metric == 'cosine':
            # Inner product (assumes normalized vectors)
            self.index = faiss.IndexFlatIP(dim)
        elif metric == 'euclidean':
            self.index = faiss.IndexFlatL2(dim)
        else:
            raise ValueError(f"Unsupported metric: {metric}")

        # Metadata store and ID mapping
        # FAISS uses internal sequential indices, so we maintain:
        # - faiss_idx → custom_id mapping
        # - custom_id → metadata mapping
        self.id_map: dict[int, int] = {}  # faiss_idx → custom_id
        self.metadata: dict[int, Any] = {}  # custom_id → metadata
        self._next_id = 0

    def add(
        self,
        vectors: np.ndarray,
        ids: list[int] | None = None,
        metadata: list[Any] | None = None
    ) -> None:
        """
        Add vectors to the index.
        
        Args:
            vectors: 2D numpy array of shape (N, dim)
            ids: Optional list of IDs; auto-generated if None
            metadata: Optional metadata per vector
        """
        if vectors.ndim != 2 or vectors.shape[1] != self.dim:
            raise ValueError(f"Expected shape (N, {self.dim}), got {vectors.shape}")

        N = len(vectors)

        # Normalize if using cosine similarity
        if self.metric == 'cosine':
            vectors = vectors / (np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-8)

        # Generate IDs if not provided
        if ids is None:
            ids = list(range(self._next_id, self._next_id + N))
            self._next_id += N

        # Track current FAISS index size (before adding)
        faiss_start_idx = self.index.ntotal

        # Add to FAISS
        self.index.add(vectors.astype(np.float32))

        # Map FAISS indices to custom IDs
        for i, custom_id in enumerate(ids):
            faiss_idx = faiss_start_idx + i
            self.id_map[faiss_idx] = custom_id

        # Store metadata
        if metadata is not None:
            for custom_id, meta in zip(ids, metadata):
                self.metadata[custom_id] = meta

    def query(
        self,
        vector: np.ndarray,
        k: int = 10
    ) -> list[dict[str, Any]]:
        """
        Find k nearest neighbors.
        
        Args:
            vector: 1D or 2D query vector(s)
            k: Number of neighbors to return
            
        Returns:
            List of dicts with 'id', 'distance', and optional 'metadata'
        """
        # Handle 1D input
        if vector.ndim == 1:
            vector = vector.reshape(1, -1)

        # Normalize if using cosine
        if self.metric == 'cosine':
            vector = vector / (np.linalg.norm(vector, axis=1, keepdims=True) + 1e-8)

        # Search
        distances, indices = self.index.search(vector.astype(np.float32), k)

        # Format results
        results = []
        for dist, faiss_idx in zip(distances[0], indices[0]):
            # Skip invalid indices (happens with empty index or k > size)
            if faiss_idx == -1:
                continue

            # Map FAISS index to custom ID
            custom_id = self.id_map.get(int(faiss_idx), int(faiss_idx))

            # For IndexFlatIP (cosine), FAISS returns inner product (similarity)
            # Convert to distance: distance = 1 - similarity
            if self.metric == 'cosine':
                distance = 1.0 - float(dist)
            else:
                distance = float(dist)

            result = {
                'id': custom_id,
                'distance': distance
            }
            if custom_id in self.metadata:
                result['metadata'] = self.metadata[custom_id]
            results.append(result)

        return results

    def save(self, path: str) -> None:
        """Save index and metadata to disk."""
        # Save FAISS index
        faiss.write_index(self.index, f"{path}.faiss")

        # Save metadata
        with open(f"{path}.meta", 'wb') as f:
            pickle.dump({
                'dim': self.dim,
                'metric': self.metric,
                'id_map': self.id_map,
                'metadata': self.metadata,
                'next_id': self._next_id
            }, f)

    @classmethod
    def load(cls, path: str) -> 'VectorIndex':
        """Load index from disk."""
        # Load FAISS index
        faiss_index = faiss.read_index(f"{path}.faiss")

        # Load metadata
        with open(f"{path}.meta", 'rb') as f:
            meta = pickle.load(f)

        # Reconstruct
        index = cls.__new__(cls)
        index.dim = meta['dim']
        index.metric = meta['metric']
        index.index = faiss_index
        index.id_map = meta.get('id_map', {})  # Backward compat
        index.metadata = meta['metadata']
        index._next_id = meta['next_id']

        return index

    def __len__(self) -> int:
        """Return number of vectors in index."""
        return self.index.ntotal

    def __repr__(self) -> str:
        return f"VectorIndex(dim={self.dim}, metric='{self.metric}', size={len(self)})"

