"""
Ontology-aware memory service for cross-session recall.

From first principles: Memory enables agents to recall context from past
conversations. Ontology integration provides:
- Entity-based query expansion (search for "revenue" also finds "sales")
- Semantic linking across sessions
- Domain-scoped memory (business memories separate from trading memories)

Wraps ADK memory backends when available, with fallback to in-memory storage.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from agent_kit.ontology.loader import OntologyLoader

logger = logging.getLogger(__name__)

# Try to import ADK memory services
try:
    from google.adk.memory.base_memory_service import BaseMemoryService  # type: ignore[import-not-found]
    ADK_MEMORY_AVAILABLE = True
except ImportError:
    ADK_MEMORY_AVAILABLE = False
    BaseMemoryService = None  # type: ignore[assignment]


@dataclass
class MemoryEntry:
    """A single memory entry."""

    id: str
    content: str
    user_id: str
    session_id: str
    timestamp: float = field(default_factory=time.time)
    entities: list[str] = field(default_factory=list)
    domain: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "entities": self.entities,
            "domain": self.domain,
            "metadata": self.metadata,
        }


@dataclass
class SearchResult:
    """Result from memory search."""

    entry: MemoryEntry
    score: float
    matched_entities: list[str] = field(default_factory=list)


@runtime_checkable
class MemoryBackend(Protocol):
    """Protocol for memory storage backends."""

    async def store(self, entry: MemoryEntry) -> None:
        """Store a memory entry."""
        ...

    async def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """Search memories by query text."""
        ...

    async def get_by_entities(
        self,
        entities: list[str],
        user_id: str,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """Get memories containing specific entities."""
        ...

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory entry."""
        ...


class InMemoryBackend:
    """
    Simple in-memory storage backend for testing and development.

    For production, use ADK's VertexAIRagMemoryService or similar.
    """

    def __init__(self) -> None:
        """Initialize empty memory store."""
        self._memories: dict[str, MemoryEntry] = {}

    async def store(self, entry: MemoryEntry) -> None:
        """Store a memory entry."""
        self._memories[entry.id] = entry
        logger.debug(f"Stored memory: {entry.id}")

    async def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """
        Search memories by query text (simple keyword matching).

        Args:
            query: Search query
            user_id: User scope
            limit: Max results

        Returns:
            Matching memories sorted by relevance (keyword count)
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())

        results = []
        for entry in self._memories.values():
            if entry.user_id != user_id:
                continue

            content_lower = entry.content.lower()
            # Count matching words
            matches = sum(1 for word in query_words if word in content_lower)
            if matches > 0:
                results.append((entry, matches))

        # Sort by match count descending
        results.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in results[:limit]]

    async def get_by_entities(
        self,
        entities: list[str],
        user_id: str,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """
        Get memories containing specific entities.

        Args:
            entities: Entity identifiers to search for
            user_id: User scope
            limit: Max results

        Returns:
            Memories containing any of the specified entities
        """
        entity_set = set(e.lower() for e in entities)
        results = []

        for entry in self._memories.values():
            if entry.user_id != user_id:
                continue

            entry_entities = set(e.lower() for e in entry.entities)
            overlap = entity_set & entry_entities
            if overlap:
                results.append((entry, len(overlap)))

        # Sort by entity overlap descending
        results.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in results[:limit]]

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory entry."""
        if memory_id in self._memories:
            del self._memories[memory_id]
            return True
        return False

    def clear(self) -> None:
        """Clear all memories."""
        self._memories.clear()


class OntologyMemoryService:
    """
    Memory service that uses ontology for entity-aware recall.

    Features:
    - Query expansion using ontology relationships
    - Entity extraction from conversations
    - Domain-scoped memory (business, betting, trading)
    - Session-to-memory ingestion

    Works with ADK memory backends when available, fallback to InMemoryBackend.

    Example:
        >>> ontology = OntologyLoader("assets/ontologies/business.ttl")
        >>> memory = OntologyMemoryService(ontology, domain="business")
        >>>
        >>> # Store from session
        >>> await memory.ingest_from_session("session_001", events, "user_123")
        >>>
        >>> # Search with entity expansion
        >>> results = await memory.search("What was the revenue forecast?", "user_123")
    """

    def __init__(
        self,
        ontology: OntologyLoader,
        domain: str = "business",
        backend: MemoryBackend | Any | None = None,
    ):
        """
        Initialize memory service.

        Args:
            ontology: OntologyLoader for entity expansion
            domain: Domain scope (business, betting, trading)
            backend: Memory backend (ADK or InMemoryBackend)
        """
        self.ontology = ontology
        self.domain = domain

        # Use provided backend or fallback
        if backend is not None:
            self.backend = backend
        else:
            self.backend = InMemoryBackend()

        logger.info(f"Initialized OntologyMemoryService for domain: {domain}")

    async def store(
        self,
        content: str,
        user_id: str,
        session_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry:
        """
        Store content in memory with entity extraction.

        Args:
            content: Text content to store
            user_id: User identifier
            session_id: Session this came from
            metadata: Optional metadata

        Returns:
            Created MemoryEntry
        """
        # Generate ID from content hash
        memory_id = self._generate_id(content, user_id, session_id)

        # Extract entities from content using ontology
        entities = self._extract_entities(content)

        # Create entry
        entry = MemoryEntry(
            id=memory_id,
            content=content,
            user_id=user_id,
            session_id=session_id,
            entities=entities,
            domain=self.domain,
            metadata=metadata or {},
        )

        # Store
        await self.backend.store(entry)
        logger.info(f"Stored memory {memory_id} with {len(entities)} entities")

        return entry

    async def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        expand_query: bool = True,
    ) -> list[SearchResult]:
        """
        Search memory with ontology-enhanced query expansion.

        Args:
            query: Search query
            user_id: User scope
            limit: Max results
            expand_query: Whether to expand query with related entities

        Returns:
            Search results with relevance scores
        """
        # Extract entities from query
        query_entities = self._extract_entities(query)

        # Expand with related entities from ontology
        if expand_query:
            expanded_entities = self._expand_entities(query_entities)
        else:
            expanded_entities = query_entities

        # Search by expanded query
        expanded_query = self._build_expanded_query(query, expanded_entities)
        text_results = await self.backend.search(expanded_query, user_id, limit)

        # Also search by entities
        if expanded_entities:
            entity_results = await self.backend.get_by_entities(
                expanded_entities, user_id, limit
            )
        else:
            entity_results = []

        # Merge and deduplicate results
        seen_ids: set[str] = set()
        results: list[SearchResult] = []

        # Text results get higher base score
        for entry in text_results:
            if entry.id not in seen_ids:
                seen_ids.add(entry.id)
                matched = [e for e in entry.entities if e.lower() in
                          [qe.lower() for qe in query_entities]]
                results.append(SearchResult(
                    entry=entry,
                    score=0.8 + 0.1 * len(matched),
                    matched_entities=matched,
                ))

        # Entity results get lower base score
        for entry in entity_results:
            if entry.id not in seen_ids:
                seen_ids.add(entry.id)
                matched = [e for e in entry.entities if e.lower() in
                          [qe.lower() for qe in expanded_entities]]
                results.append(SearchResult(
                    entry=entry,
                    score=0.5 + 0.1 * len(matched),
                    matched_entities=matched,
                ))

        # Sort by score
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    async def ingest_from_session(
        self,
        session_id: str,
        events: list[dict[str, Any]],
        user_id: str,
    ) -> int:
        """
        Ingest events from a session into memory.

        Args:
            session_id: Session identifier
            events: List of event dictionaries
            user_id: User identifier

        Returns:
            Number of memories created
        """
        count = 0
        for event in events:
            # Get content from event
            content = ""
            if "content" in event:
                if isinstance(event["content"], dict):
                    content = event["content"].get("text", "")
                else:
                    content = str(event["content"])

            if not content:
                continue

            # Store with event metadata
            await self.store(
                content=content,
                user_id=user_id,
                session_id=session_id,
                metadata={
                    "event_id": event.get("id", ""),
                    "author": event.get("author", ""),
                    "timestamp": event.get("timestamp", time.time()),
                },
            )
            count += 1

        logger.info(f"Ingested {count} memories from session {session_id}")
        return count

    def _generate_id(self, content: str, user_id: str, session_id: str) -> str:
        """Generate unique ID for memory entry."""
        data = f"{content}:{user_id}:{session_id}:{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _extract_entities(self, text: str) -> list[str]:
        """
        Extract entities from text using ontology.

        Simple implementation: find ontology labels in text.
        Could be enhanced with NER models.
        """
        entities = []
        text_lower = text.lower()

        # Query ontology for entity labels
        query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?label WHERE {
            ?entity rdfs:label ?label .
        }
        LIMIT 100
        """
        try:
            results = self.ontology.query(query)
            for result in results:
                label = result.get("label", {})
                if isinstance(label, dict):
                    label_text = label.get("value", "")
                else:
                    label_text = str(label)

                if label_text and label_text.lower() in text_lower:
                    entities.append(label_text)
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")

        return entities

    def _expand_entities(self, entities: list[str]) -> list[str]:
        """
        Expand entities using ontology relationships.

        Finds related entities via SPARQL queries.
        """
        expanded = list(entities)  # Start with original entities

        for entity in entities:
            # Query for related entities
            query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            
            SELECT DISTINCT ?relatedLabel WHERE {{
                ?entity rdfs:label "{entity}" .
                {{
                    ?entity ?prop ?related .
                    ?related rdfs:label ?relatedLabel .
                }}
                UNION
                {{
                    ?related ?prop ?entity .
                    ?related rdfs:label ?relatedLabel .
                }}
            }}
            LIMIT 5
            """
            try:
                results = self.ontology.query(query)
                for result in results:
                    label = result.get("relatedLabel", {})
                    if isinstance(label, dict):
                        label_text = label.get("value", "")
                    else:
                        label_text = str(label)

                    if label_text and label_text not in expanded:
                        expanded.append(label_text)
            except Exception:
                pass  # Continue if expansion fails

        return expanded

    def _build_expanded_query(self, original: str, entities: list[str]) -> str:
        """Build expanded query string with entities."""
        if not entities:
            return original

        # Add entity terms to query
        entity_terms = " ".join(entities[:5])  # Limit to prevent query explosion
        return f"{original} {entity_terms}"


