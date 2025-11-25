"""
Ontology-aware session service.

Wraps a standard session backend (like ADK's) to add ontology context persistence.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from agent_kit.ontology.loader import OntologyLoader


@runtime_checkable
class SessionBackend(Protocol):
    """Protocol for session backends (compatible with ADK)."""

    async def get_session(self, session_id: str) -> dict[str, Any]:
        """Retrieve a session by ID."""
        ...

    async def save_session(self, session_id: str, session_data: dict[str, Any]) -> None:
        """Save a session."""
        ...


class OntologySessionService:
    """
    Wraps a session backend to manage ontology context within sessions.
    
    Ensures that:
    1. Ontology entities extracted in previous turns are persisted.
    2. SPARQL query history is maintained across turns.
    3. Session metadata is linked to ontology concepts.
    """

    def __init__(self, backend: SessionBackend, ontology: OntologyLoader):
        """
        Initialize with a backend and ontology loader.

        Args:
            backend: Persistence backend (e.g., SqliteSessionService)
            ontology: OntologyLoader for validating stored context
        """
        self.backend = backend
        self.ontology = ontology

    async def get_session(self, session_id: str) -> dict[str, Any]:
        """
        Retrieve session and enrich with ontology context.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Session dictionary with 'ontology_context' key
        """
        session = await self.backend.get_session(session_id)
        
        if "ontology_context" not in session:
            session["ontology_context"] = {
                "entities": [],
                "queries": [],
                "history": []
            }
            
        return session

    async def save_session(self, session_id: str, session_data: dict[str, Any]) -> None:
        """
        Save session data, ensuring ontology context is preserved.
        
        Args:
            session_id: Unique session identifier
            session_data: Session dictionary to save
        """
        # Validate entities before saving (optional)
        if "ontology_context" in session_data:
            entities = session_data["ontology_context"].get("entities", [])
            # (Optional) Verify entities exist in ontology
            
        await self.backend.save_session(session_id, session_data)

    async def add_entity_to_session(self, session_id: str, entity_uri: str) -> None:
        """
        Add an extracted entity to the session context.
        
        Args:
            session_id: Session ID
            entity_uri: URI of the entity to add
        """
        session = await self.get_session(session_id)
        entities = session["ontology_context"]["entities"]
        
        if entity_uri not in entities:
            entities.append(entity_uri)
            await self.save_session(session_id, session)

    async def add_query_to_session(self, session_id: str, query: str) -> None:
        """
        Add a SPARQL query to the session history.
        
        Args:
            session_id: Session ID
            query: SPARQL query string
        """
        session = await self.get_session(session_id)
        queries = session["ontology_context"]["queries"]
        queries.append(query)
        await self.save_session(session_id, session)
