"""Vector space operations: embeddings, indexing, distance metrics."""

from agent_kit.vectorspace.embedder import Embedder
from agent_kit.vectorspace.index import VectorIndex
from agent_kit.vectorspace.geometry import cosine_similarity, euclidean_distance

__all__ = ['Embedder', 'VectorIndex', 'cosine_similarity', 'euclidean_distance']

