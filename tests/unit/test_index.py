"""Unit tests for vectorspace.index module."""

import numpy as np
import pytest

from agent_kit.vectorspace import VectorIndex


def test_index_initialization() -> None:
    """Test index initializes correctly."""
    index = VectorIndex(dim=384, metric='cosine')
    assert index.dim == 384
    assert index.metric == 'cosine'
    assert len(index) == 0


def test_add_vectors() -> None:
    """Test adding vectors to index."""
    index = VectorIndex(dim=10, metric='cosine')
    vectors = np.random.randn(100, 10)

    index.add(vectors)
    assert len(index) == 100


def test_add_vectors_with_ids() -> None:
    """Test adding vectors with custom IDs."""
    index = VectorIndex(dim=10, metric='cosine')
    vectors = np.random.randn(5, 10)
    ids = [10, 20, 30, 40, 50]

    index.add(vectors, ids=ids)

    # Query should return these IDs
    results = index.query(vectors[0], k=1)
    assert results[0]['id'] in ids


def test_add_vectors_with_metadata() -> None:
    """Test adding vectors with metadata."""
    index = VectorIndex(dim=10, metric='cosine')
    vectors = np.random.randn(3, 10)
    metadata = ['task 1', 'task 2', 'task 3']

    index.add(vectors, metadata=metadata)

    results = index.query(vectors[0], k=1)
    assert 'metadata' in results[0]
    assert results[0]['metadata'] in metadata


def test_query_returns_self() -> None:
    """Test querying a vector returns itself as top result."""
    index = VectorIndex(dim=10, metric='cosine')
    vectors = np.random.randn(10, 10)

    index.add(vectors, ids=list(range(10)))

    # Query with first vector
    results = index.query(vectors[0], k=5)

    # Top result should be the vector itself (id=0)
    assert results[0]['id'] == 0
    # Distance should be very small (near 0 for cosine with normalized vectors)
    assert results[0]['distance'] < 0.01


def test_query_k_results() -> None:
    """Test query returns exactly k results."""
    index = VectorIndex(dim=10, metric='cosine')
    vectors = np.random.randn(100, 10)

    index.add(vectors)

    results = index.query(vectors[0], k=10)
    assert len(results) == 10


def test_euclidean_metric() -> None:
    """Test index with Euclidean distance."""
    index = VectorIndex(dim=10, metric='euclidean')
    vectors = np.random.randn(50, 10)

    index.add(vectors)
    results = index.query(vectors[0], k=5)

    # Top result should be self with distance ~0
    assert results[0]['distance'] < 0.01


def test_invalid_metric_raises_error() -> None:
    """Test invalid metric raises ValueError."""
    with pytest.raises(ValueError):
        VectorIndex(dim=10, metric='invalid')


def test_add_wrong_dimension_raises_error() -> None:
    """Test adding vectors with wrong dimension raises error."""
    index = VectorIndex(dim=10, metric='cosine')
    vectors = np.random.randn(5, 20)  # Wrong dim

    with pytest.raises(ValueError):
        index.add(vectors)


def test_empty_index_query() -> None:
    """Test querying empty index doesn't crash."""
    index = VectorIndex(dim=10, metric='cosine')
    query_vec = np.random.randn(10)

    results = index.query(query_vec, k=5)
    assert len(results) == 0

