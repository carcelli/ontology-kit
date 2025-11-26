"""
Session management for multi-turn conversations.

From first principles: Sessions enable stateful conversations across multiple
invocations. They store:
- Conversation history (events)
- Extracted entities and context
- User preferences and state

This module provides:
- OntologySessionService: Session service with ontology awareness
- SessionBackend protocol and implementations
- Backend adapters for ADK integration
"""

from .backends import (
    ADKSessionBackendAdapter,
    InMemorySessionBackend,
    SessionBackend,
    SqliteSessionBackend,
    create_session_backend,
)
from .ontology_session_service import OntologySessionService

__all__ = [
    # Main service
    "OntologySessionService",
    # Backends
    "SessionBackend",
    "InMemorySessionBackend",
    "SqliteSessionBackend",
    "ADKSessionBackendAdapter",
    # Factory
    "create_session_backend",
]
