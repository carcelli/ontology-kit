"""
Adapter layer for integrating ADK and OpenAI Agents SDK with ontology-kit.

From first principles: Adapters bridge external SDKs to our ontology-first
architecture. They enrich SDK components with ontology context without
modifying SDK code directly.

Design pattern: Adapter (GoF) - wraps external interfaces to match our domain.

Key adapters:
- OntologyAgentAdapter: Wraps OpenAI SDK agents with ontology context
- OntologyOutputGuardrail: Validates outputs against domain schemas
- OntologyInputGuardrail: Validates inputs against domain constraints
- OntologyToolFilter: Filters tools by domain allowlist
- OpenAISDKAdapter: Legacy adapter for simple ontology-enriched execution

Usage:
    >>> from agent_kit.adapters import OntologyAgentAdapter, OntologyOutputGuardrail
    >>> from agents import Agent
    >>>
    >>> agent = Agent(name="ForecastAgent", instructions="...")
    >>> adapter = OntologyAgentAdapter(agent, ontology, "business")
    >>> adapter.agent.output_guardrails = [OntologyOutputGuardrail("business")]
"""

from .ontology_agent_adapter import OntologyAgentAdapter
from .ontology_guardrail import OntologyInputGuardrail, OntologyOutputGuardrail
from .ontology_tool_filter import OntologyToolFilter
from .openai_sdk import OpenAISDKAdapter

__all__ = [
    # Primary adapter for OpenAI SDK integration
    "OntologyAgentAdapter",
    # Guardrails for input/output validation
    "OntologyOutputGuardrail",
    "OntologyInputGuardrail",
    # Tool filtering by domain
    "OntologyToolFilter",
    # Legacy adapter (simpler interface)
    "OpenAISDKAdapter",
]
