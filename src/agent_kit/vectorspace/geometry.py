"""Geometric operations and distance metrics for vector spaces."""


import numpy as np


def cosine_similarity(x: np.ndarray, y: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    
    Args:
        x: First vector
        y: Second vector
        
    Returns:
        Cosine similarity in [-1, 1]
    """
    dot = np.dot(x, y)
    norm_x = np.linalg.norm(x)
    norm_y = np.linalg.norm(y)
    return dot / (norm_x * norm_y + 1e-8)


def euclidean_distance(x: np.ndarray, y: np.ndarray) -> float:
    """
    Compute Euclidean (L2) distance between two vectors.
    
    Args:
        x: First vector
        y: Second vector
        
    Returns:
        Euclidean distance (non-negative)
    """
    return np.linalg.norm(x - y)


def pairwise_distances(
    X: np.ndarray,
    Y: np.ndarray | None = None,
    metric: str = 'euclidean'
) -> np.ndarray:
    """
    Compute pairwise distances between vectors.
    
    Args:
        X: Matrix of shape (N, D)
        Y: Optional matrix of shape (M, D); if None, compute X vs X
        metric: 'euclidean' or 'cosine'
        
    Returns:
        Distance matrix of shape (N, M) or (N, N)
    """
    if Y is None:
        Y = X

    if metric == 'euclidean':
        # ||x - y||^2 = ||x||^2 + ||y||^2 - 2<x, y>
        X_norm = (X**2).sum(axis=1, keepdims=True)
        Y_norm = (Y**2).sum(axis=1, keepdims=True).T
        dists = X_norm + Y_norm - 2 * X @ Y.T
        return np.sqrt(np.maximum(dists, 0))  # Avoid negative due to numerical error

    elif metric == 'cosine':
        # Normalize
        X_norm = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-8)
        Y_norm = Y / (np.linalg.norm(Y, axis=1, keepdims=True) + 1e-8)
        # Cosine similarity
        similarities = X_norm @ Y_norm.T
        # Convert to distance: 1 - sim
        return 1 - similarities

    else:
        raise ValueError(f"Unsupported metric: {metric}")

