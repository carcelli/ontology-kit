"""
Ontology-enriched event for agent action tracking.

From first principles: Events capture what happened; ontology context captures
why it happened (which entities, SPARQL queries, leverage scores).

This implementation is compatible with both:
- Google ADK's Event system (when available)
- A standalone Event for when ADK is not installed
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# Try to import ADK Event, fallback to standalone if not available
try:
    # type: ignore[import-not-found]
    from google.adk.events.event import Event as ADKEvent
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    ADKEvent = None  # type: ignore[assignment]


class OntologyEventContent(BaseModel):
    """Content for an ontology event."""
    model_config = {"extra": "forbid"}

    text: str = Field(default="", description="Text content of the event")
    parts: list[dict[str, Any]] = Field(
        default_factory=list, description="Additional content parts"
    )


class OntologyEvent(BaseModel):
    """
    Event enriched with ontology context for domain-aware tracking.

    Extends tracking with:
    - SPARQL queries executed during agent reasoning
    - Leverage scores computed (for business domain)
    - Entity extractions from conversation
    - Ontology triples added/modified

    Compatible with ADK's Event system when available, but works standalone.

    Example:
        >>> event = OntologyEvent(
        ...     author="ForecastAgent",
        ...     content=OntologyEventContent(text="Forecast complete"),
        ...     ontology_triples=[{"subject": "forecast_001", "predicate": "forecasts", "object": "revenue"}],
        ... )
    """
    model_config = {"extra": "forbid"}

    # Core event fields (ADK-compatible)
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique event identifier",
    )
    author: str = Field(...,
                        description="Agent or user that created this event")
    content: OntologyEventContent = Field(
        default_factory=OntologyEventContent, description="Event content"
    )
    timestamp: float = Field(
        default_factory=time.time, description="Event timestamp (Unix epoch)"
    )
    invocation_id: str = Field(
        default="", description="ID of the invocation this event belongs to"
    )
    branch: str | None = Field(
        default=None, description="Branch identifier for multi-agent isolation"
    )

    # Ontology-specific fields
    ontology_triples: list[dict[str, str]] = Field(
        default_factory=list,
        description="SPARQL triples added/modified during this event",
    )
    sparql_queries: list[str] = Field(
        default_factory=list,
        description="SPARQL queries executed during agent reasoning",
    )
    leverage_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Leverage scores computed (for business domain)",
    )
    extracted_entities: list[str] = Field(
        default_factory=list,
        description="Entities extracted from conversation using ontology",
    )
    domain: str = Field(
        default="", description="Domain this event belongs to"
    )

    @classmethod
    def from_agent_result(
        cls,
        agent_name: str,
        result: dict[str, Any],
        ontology_context: dict[str, Any] | None = None,
        invocation_id: str = "",
    ) -> "OntologyEvent":
        """
        Create ontology event from agent result.

        Args:
            agent_name: Name of agent that produced result
            result: Agent result dictionary
            ontology_context: Optional ontology metadata (SPARQL queries, etc.)
            invocation_id: Optional invocation ID

        Returns:
            OntologyEvent with enriched context
        """
        # Extract text summary from result
        summary = result.get("summary", "")
        content = OntologyEventContent(text=summary)

        # Build event with ontology context
        ontology_context = ontology_context or {}
        event = cls(
            author=agent_name,
            content=content,
            invocation_id=invocation_id,
            ontology_triples=ontology_context.get("triples", []),
            sparql_queries=ontology_context.get("queries", []),
            leverage_scores=ontology_context.get("leverage_scores", {}),
            extracted_entities=ontology_context.get("entities", []),
            domain=ontology_context.get("domain", ""),
        )

        return event

    def to_adk_event(self) -> Any | None:
        """
        Convert to ADK Event if ADK is available.

        Returns:
            ADK Event instance or None if ADK not installed
        """
        if not ADK_AVAILABLE:
            return None

        try:
            from google.genai import types  # type: ignore[import-not-found]

            # Create ADK-compatible content
            parts = [types.Part(text=self.content.text)]
            content = types.Content(parts=parts)

            # Create ADK event with our data as metadata
            return ADKEvent(
                id=self.id,
                author=self.author,
                content=content,
                timestamp=self.timestamp,
                invocation_id=self.invocation_id,
                branch=self.branch,
            )
        except Exception:
            return None

    @classmethod
    def from_adk_event(
        cls,
        adk_event: Any,
        ontology_context: dict[str, Any] | None = None,
    ) -> "OntologyEvent":
        """
        Create OntologyEvent from an ADK Event.

        Args:
            adk_event: ADK Event instance
            ontology_context: Additional ontology metadata

        Returns:
            OntologyEvent with ADK event data
        """
        ontology_context = ontology_context or {}

        # Extract text from ADK content
        text = ""
        if hasattr(adk_event, "content") and adk_event.content:
            if hasattr(adk_event.content, "parts"):
                for part in adk_event.content.parts:
                    if hasattr(part, "text"):
                        text += part.text

        return cls(
            id=getattr(adk_event, "id", str(uuid.uuid4())),
            author=getattr(adk_event, "author", "unknown"),
            content=OntologyEventContent(text=text),
            timestamp=getattr(adk_event, "timestamp", time.time()),
            invocation_id=getattr(adk_event, "invocation_id", ""),
            branch=getattr(adk_event, "branch", None),
            ontology_triples=ontology_context.get("triples", []),
            sparql_queries=ontology_context.get("queries", []),
            leverage_scores=ontology_context.get("leverage_scores", {}),
            extracted_entities=ontology_context.get("entities", []),
            domain=ontology_context.get("domain", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "id": self.id,
            "author": self.author,
            "content": self.content.model_dump(),
            "timestamp": self.timestamp,
            "timestamp_iso": datetime.fromtimestamp(self.timestamp).isoformat(),
            "invocation_id": self.invocation_id,
            "branch": self.branch,
            "ontology_triples": self.ontology_triples,
            "sparql_queries": self.sparql_queries,
            "leverage_scores": self.leverage_scores,
            "extracted_entities": self.extracted_entities,
            "domain": self.domain,
        }
