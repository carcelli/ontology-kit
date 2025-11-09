"""Unit tests for vectorspace.embedder module."""

import pytest
import numpy as np
from agent_kit.vectorspace import Embedder


def test_embedder_initialization() -> None:
    """Test embedder initializes correctly."""
    embedder = Embedder(model_name='all-MiniLM-L6-v2')
    assert embedder.model_name == 'all-MiniLM-L6-v2'
    assert embedder.dimension == 384


def test_embed_single_text() -> None:
    """Test embedding a single string."""
    embedder = Embedder(model_name='all-MiniLM-L6-v2')
    text = "Sort a list of numbers"
    embedding = embedder.embed(text)
    
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (384,)
    assert not np.isnan(embedding).any()


def test_embed_batch() -> None:
    """Test batch embedding."""
    embedder = Embedder(model_name='all-MiniLM-L6-v2')
    texts = [
        "Task 1",
        "Task 2",
        "Task 3",
    ]
    embeddings = embedder.embed_batch(texts, show_progress=False)
    
    assert embeddings.shape == (3, 384)
    assert not np.isnan(embeddings).any()


def test_embed_empty_string() -> None:
    """Test embedding empty string doesn't crash."""
    embedder = Embedder(model_name='all-MiniLM-L6-v2')
    embedding = embedder.embed("")
    
    assert embedding.shape == (384,)


def test_embeddings_normalized() -> None:
    """Test embeddings have reasonable magnitude."""
    embedder = Embedder(model_name='all-MiniLM-L6-v2')
    embedding = embedder.embed("Test sentence")
    
    norm = np.linalg.norm(embedding)
    assert 0.5 < norm < 2.0  # Reasonable range


def test_similar_texts_have_similar_embeddings() -> None:
    """Test similar texts produce similar embeddings."""
    embedder = Embedder(model_name='all-MiniLM-L6-v2')
    
    text1 = "Sort a list of numbers"
    text2 = "Order array ascending"
    text3 = "Calculate the square root"
    
    emb1 = embedder.embed(text1)
    emb2 = embedder.embed(text2)
    emb3 = embedder.embed(text3)
    
    # Cosine similarity
    def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    sim_12 = cosine_sim(emb1, emb2)
    sim_13 = cosine_sim(emb1, emb3)
    
    # Similar texts should be more similar than dissimilar ones
    assert sim_12 > sim_13

