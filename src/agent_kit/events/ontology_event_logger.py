"""
Event logger that captures ontology context during agent execution.

From first principles: Logging should be automatic and non-intrusive.
Agents shouldn't need to manually create events; the logger captures
context from agent actions and ontology interactions.

Integrates with:
- OpenAI Agents SDK tracing
- ADK Event system (when available)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from agent_kit.agents.base import AgentResult, AgentTask
from agent_kit.ontology.loader import OntologyLoader

from .ontology_event import OntologyEvent, OntologyEventContent

logger = logging.getLogger(__name__)


class OntologyEventLogger:
    """
    Logger that creates ontology-enriched events from agent actions.

    Tracks:
    - SPARQL queries executed via OntologyLoader
    - Entities extracted from conversations
    - Leverage scores computed (business domain)
    - Triples added to ontology

    Integrates with both OpenAI SDK tracing and ADK event system.

    Example:
        >>> ontology = OntologyLoader("assets/ontologies/business.ttl")
        >>> logger = OntologyEventLogger(ontology)
        >>> logger.start_tracking("session_001")
        >>> # ... agent executes ...
        >>> event = logger.create_event("ForecastAgent", task, result, "session_001")
        >>> events = logger.get_events("session_001")
    """

    def __init__(
        self,
        ontology: OntologyLoader,
        domain: str = "business",
    ):
        """
        Initialize logger with ontology loader.

        Args:
            ontology: OntologyLoader instance for tracking queries
            domain: Domain identifier for events (business, betting, trading)
        """
        self.ontology = ontology
        self.domain = domain
        self._session_queries: dict[str, list[str]] = {}
        self._session_triples: dict[str, list[dict[str, str]]] = {}
        self._session_entities: dict[str, list[str]] = {}
        self._session_events: dict[str, list[OntologyEvent]] = {}

    def start_tracking(self, session_id: str) -> None:
        """
        Start tracking events for a session.

        Args:
            session_id: Unique session identifier
        """
        self._session_queries[session_id] = []
        self._session_triples[session_id] = []
        self._session_entities[session_id] = []
        self._session_events[session_id] = []
        logger.debug(f"Started tracking for session: {session_id}")

    def stop_tracking(self, session_id: str) -> list[OntologyEvent]:
        """
        Stop tracking and return all events for session.

        Args:
            session_id: Session identifier

        Returns:
            List of events captured during session
        """
        events = self._session_events.get(session_id, [])

        # Clean up
        self._session_queries.pop(session_id, None)
        self._session_triples.pop(session_id, None)
        self._session_entities.pop(session_id, None)
        self._session_events.pop(session_id, None)

        logger.debug(f"Stopped tracking for session: {session_id}, {len(events)} events")
        return events

    def log_query(self, session_id: str, query: str) -> None:
        """
        Log a SPARQL query executed during session.

        Args:
            session_id: Session identifier
            query: SPARQL query string
        """
        if session_id in self._session_queries:
            self._session_queries[session_id].append(query)
            logger.debug(f"Logged query for session {session_id}")

    def log_triple(self, session_id: str, triple: dict[str, str]) -> None:
        """
        Log a triple added to ontology during session.

        Args:
            session_id: Session identifier
            triple: Triple dict with subject, predicate, object keys
        """
        if session_id in self._session_triples:
            self._session_triples[session_id].append(triple)
            logger.debug(f"Logged triple for session {session_id}")

    def log_entity(self, session_id: str, entity: str) -> None:
        """
        Log an entity extracted from conversation.

        Args:
            session_id: Session identifier
            entity: Entity URI or identifier
        """
        if session_id in self._session_entities:
            if entity not in self._session_entities[session_id]:
                self._session_entities[session_id].append(entity)
                logger.debug(f"Logged entity for session {session_id}: {entity}")

    def create_event(
        self,
        agent_name: str,
        task: AgentTask | str,
        result: AgentResult | dict[str, Any],
        session_id: str,
        invocation_id: str = "",
    ) -> OntologyEvent:
        """
        Create ontology event from agent execution.

        Args:
            agent_name: Name of agent that executed
            task: Original task (AgentTask or string)
            result: Agent result (AgentResult or dict)
            session_id: Session identifier
            invocation_id: Optional invocation identifier

        Returns:
            OntologyEvent with full ontology context
        """
        # Build ontology context from tracked data
        ontology_context = {
            "queries": self._session_queries.get(session_id, []).copy(),
            "triples": self._session_triples.get(session_id, []).copy(),
            "entities": self._session_entities.get(session_id, []).copy(),
            "leverage_scores": self._extract_leverage_scores(result),
            "domain": self.domain,
        }

        # Get result dict
        if isinstance(result, AgentResult):
            result_dict = result.result if hasattr(result, "result") else {}
        elif isinstance(result, dict):
            result_dict = result
        else:
            result_dict = {"summary": str(result)}

        # Create event
        event = OntologyEvent.from_agent_result(
            agent_name=agent_name,
            result=result_dict,
            ontology_context=ontology_context,
            invocation_id=invocation_id,
        )

        # Store event
        if session_id in self._session_events:
            self._session_events[session_id].append(event)

        # Clear session data for next event (queries are per-event)
        self._session_queries[session_id] = []
        self._session_triples[session_id] = []
        # Keep entities across events within session

        logger.info(f"Created event for {agent_name} in session {session_id}")
        return event

    def _extract_leverage_scores(
        self, result: AgentResult | dict[str, Any]
    ) -> dict[str, float]:
        """Extract leverage scores from result if present."""
        if isinstance(result, AgentResult):
            if hasattr(result, "result") and isinstance(result.result, dict):
                return result.result.get("leverage_scores", {})
        elif isinstance(result, dict):
            return result.get("leverage_scores", {})

        return {}

    def get_events(self, session_id: str) -> list[OntologyEvent]:
        """
        Get all events for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of events for session
        """
        return self._session_events.get(session_id, []).copy()

    def get_event_count(self, session_id: str) -> int:
        """Get count of events in session."""
        return len(self._session_events.get(session_id, []))

    def export_events(self, session_id: str) -> list[dict[str, Any]]:
        """
        Export events as dictionaries for serialization.

        Args:
            session_id: Session identifier

        Returns:
            List of event dictionaries
        """
        events = self._session_events.get(session_id, [])
        return [event.to_dict() for event in events]

    def get_query_history(self, session_id: str) -> list[str]:
        """Get all SPARQL queries executed in session."""
        events = self._session_events.get(session_id, [])
        queries = []
        for event in events:
            queries.extend(event.sparql_queries)
        return queries

    def get_entity_summary(self, session_id: str) -> dict[str, int]:
        """
        Get summary of entities mentioned in session.

        Returns:
            Dict mapping entity to mention count
        """
        events = self._session_events.get(session_id, [])
        entity_counts: dict[str, int] = {}

        for event in events:
            for entity in event.extracted_entities:
                entity_counts[entity] = entity_counts.get(entity, 0) + 1

        return entity_counts

