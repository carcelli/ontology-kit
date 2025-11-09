# src/agent_kit/tools/vector_space.py
from agents import function_tool
from agent_kit.vectorspace.embedder import Embedder
from agent_kit.vectorspace.index import VectorIndex
from typing import List, Dict
import numpy as np

embedder = Embedder()

# Create a dummy index for demonstration purposes.
# In a real application, this would be loaded from a file.
dummy_index = VectorIndex(dim=embedder.dimension)
dummy_vectors = np.random.rand(10, embedder.dimension)
dummy_index.add(dummy_vectors)

@function_tool
def embed(text: str) -> List[float]:
    """Embed a single text string."""
    embedding = embedder.embed(text)
    return embedding.tolist()

@function_tool
def embed_batch(texts: List[str]) -> List[List[float]]:
    """Embed a batch of texts efficiently."""
    embeddings = embedder.embed_batch(texts)
    return embeddings.tolist()

@function_tool
def query_vector_index(query_text: str, k: int = 5) -> List[Dict]:
    """Query the vector index for similar items."""
    query_vector = embedder.embed(query_text)
    results = dummy_index.query(query_vector, k=k)
    return results
