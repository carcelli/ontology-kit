"""
Agent Kit: Hyperdimensional Vector Space Navigation

Ontology-driven agents that navigate high-dimensional embeddings with
self-optimizing ML pipelines.
"""

__version__ = '0.1.0'
__author__ = 'Agent Kit Team'

from agent_kit.ontology import OntologyLoader
from agent_kit.vectorspace import Embedder, VectorIndex

__all__ = ['Embedder', 'VectorIndex', 'OntologyLoader']

