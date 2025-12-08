"""
Memory service for long-term recall across sessions.

From first principles: Memory enables agents to recall context from past
conversations, building richer understanding over time. ADK provides RAG
and Memory Bank services; we enhance with ontology-aware query expansion.

This module provides:
- OntologyMemoryService: Cross-session recall with entity linking
- InMemoryBackend: Simple memory backend for testing
"""

from .ontology_memory_service import InMemoryBackend, OntologyMemoryService

__all__ = [
    "OntologyMemoryService",
    "InMemoryBackend",
]
