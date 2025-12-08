"""
Event system integration with ADK for conversation tracking.

From first principles: Events are immutable records of agent actions that enable
observability, debugging, and compliance. ADK provides production-grade event
infrastructure; we enrich it with ontology context.

This module provides:
- OntologyEvent: Enriched event with SPARQL queries, entities, leverage scores
- OntologyEventLogger: Automatic event capture during agent execution
- OntologyEventContent: Content wrapper for events
"""

from .ontology_event import OntologyEvent, OntologyEventContent
from .ontology_event_logger import OntologyEventLogger

__all__ = [
    "OntologyEvent",
    "OntologyEventContent",
    "OntologyEventLogger",
]
