"""
Type protocols and interfaces for agent-kit.

From first principles: Protocols define the contracts between components.
They enable:
- Type checking at development time
- Dependency injection
- Easy mocking for tests
- Clear API documentation

These protocols follow the ADK patterns while supporting OpenAI SDK integration.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Protocol, TypeVar, runtime_checkable

# Type variables
T = TypeVar("T")
EventT = TypeVar("EventT")


# =============================================================================
# Agent Protocols
# =============================================================================


@runtime_checkable
class AgentProtocol(Protocol):
    """Protocol for agents that can be executed."""

    @property
    def name(self) -> str:
        """Agent name."""
        ...

    @property
    def instructions(self) -> str:
        """Agent instructions."""
        ...

    @property
    def tools(self) -> list[Any]:
        """Agent tools."""
        ...


@runtime_checkable
class RunnableAgentProtocol(Protocol):
    """Protocol for agents that implement the run method."""

    async def run(self, input: str) -> str:
        """Execute agent with input."""
        ...


@runtime_checkable
class StructuredAgentProtocol(Protocol[T]):
    """Protocol for agents with structured output."""

    @property
    def output_type(self) -> type[T]:
        """Output type."""
        ...

    async def run(self, input: str) -> T:
        """Execute and return structured output."""
        ...


# =============================================================================
# Event Protocols
# =============================================================================


@runtime_checkable
class EventProtocol(Protocol):
    """Protocol for events (compatible with ADK Event)."""

    @property
    def id(self) -> str:
        """Unique event ID."""
        ...

    @property
    def author(self) -> str:
        """Event author (agent or user)."""
        ...

    @property
    def timestamp(self) -> float:
        """Unix timestamp."""
        ...


@runtime_checkable
class EventLoggerProtocol(Protocol):
    """Protocol for event loggers."""

    def start_tracking(self, session_id: str) -> None:
        """Start tracking events for session."""
        ...

    def stop_tracking(self, session_id: str) -> list[EventProtocol]:
        """Stop tracking and return events."""
        ...

    def log_query(self, session_id: str, query: str) -> None:
        """Log a SPARQL query."""
        ...

    def log_entity(self, session_id: str, entity: str) -> None:
        """Log an extracted entity."""
        ...


# =============================================================================
# Session Protocols
# =============================================================================


@runtime_checkable
class SessionProtocol(Protocol):
    """Protocol for sessions (compatible with ADK Session)."""

    @property
    def id(self) -> str:
        """Session ID."""
        ...

    @property
    def events(self) -> list[EventProtocol]:
        """Session events."""
        ...


@runtime_checkable
class SessionServiceProtocol(Protocol):
    """Protocol for session services (compatible with ADK BaseSessionService)."""

    async def get_session(self, session_id: str) -> SessionProtocol:
        """Get or create session."""
        ...

    async def append_event(self, session_id: str, event: EventProtocol) -> None:
        """Append event to session."""
        ...

    async def delete_session(self, session_id: str) -> None:
        """Delete session."""
        ...


@runtime_checkable
class SessionBackendProtocol(Protocol):
    """Protocol for session storage backends."""

    async def get_session(self, session_id: str) -> dict[str, Any]:
        """Get session data."""
        ...

    async def save_session(self, session_id: str, session_data: dict[str, Any]) -> None:
        """Save session data."""
        ...

    async def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        ...


# =============================================================================
# Memory Protocols
# =============================================================================


@runtime_checkable
class MemoryEntryProtocol(Protocol):
    """Protocol for memory entries."""

    @property
    def id(self) -> str:
        """Entry ID."""
        ...

    @property
    def content(self) -> str:
        """Entry content."""
        ...

    @property
    def user_id(self) -> str:
        """User who owns this memory."""
        ...


@runtime_checkable
class MemoryServiceProtocol(Protocol):
    """Protocol for memory services (compatible with ADK BaseMemoryService)."""

    async def store(
        self,
        content: str,
        user_id: str,
        session_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntryProtocol:
        """Store content in memory."""
        ...

    async def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
    ) -> list[Any]:
        """Search memories."""
        ...


# =============================================================================
# Runner Protocols
# =============================================================================


@runtime_checkable
class RunResultProtocol(Protocol):
    """Protocol for run results."""

    @property
    def output(self) -> str:
        """Final output."""
        ...

    @property
    def session_id(self) -> str:
        """Session ID used."""
        ...

    @property
    def events(self) -> list[EventProtocol]:
        """Events generated."""
        ...


@runtime_checkable
class RunnerProtocol(Protocol):
    """Protocol for runners (compatible with ADK Runner pattern)."""

    async def run(
        self,
        agent: AgentProtocol,
        input: str,
        config: Any | None = None,
    ) -> RunResultProtocol:
        """Execute agent."""
        ...


@runtime_checkable
class StreamingRunnerProtocol(Protocol):
    """Protocol for streaming runners."""

    async def stream(
        self,
        agent: AgentProtocol,
        input: str,
        config: Any | None = None,
    ) -> AsyncIterator[str]:
        """Stream agent response."""
        ...


# =============================================================================
# Evaluation Protocols
# =============================================================================


@runtime_checkable
class EvaluatorProtocol(Protocol):
    """Protocol for evaluators."""

    @property
    def name(self) -> str:
        """Evaluator name."""
        ...

    async def evaluate(
        self,
        case: Any,
        result: Any,
    ) -> float:
        """Evaluate case and return score 0-1."""
        ...


@runtime_checkable
class EvalResultProtocol(Protocol):
    """Protocol for evaluation results."""

    @property
    def accuracy(self) -> float:
        """Overall accuracy."""
        ...

    @property
    def total_cases(self) -> int:
        """Total test cases."""
        ...

    @property
    def passed_cases(self) -> int:
        """Passed test cases."""
        ...


# =============================================================================
# Tool Protocols
# =============================================================================


@runtime_checkable
class ToolProtocol(Protocol):
    """Protocol for tools."""

    @property
    def name(self) -> str:
        """Tool name."""
        ...

    async def __call__(self, **kwargs: Any) -> Any:
        """Execute tool."""
        ...


@runtime_checkable
class ToolFilterProtocol(Protocol):
    """Protocol for tool filters."""

    def filter_tools(self, tools: list[ToolProtocol]) -> list[ToolProtocol]:
        """Filter tools by criteria."""
        ...


# =============================================================================
# Ontology Protocols
# =============================================================================


@runtime_checkable
class OntologyLoaderProtocol(Protocol):
    """Protocol for ontology loaders."""

    @property
    def path(self) -> str:
        """Ontology file path."""
        ...

    def load(self) -> None:
        """Load ontology from file."""
        ...

    def query(self, sparql: str) -> list[dict[str, Any]]:
        """Execute SPARQL query."""
        ...


@runtime_checkable
class EntityExtractorProtocol(Protocol):
    """Protocol for entity extraction."""

    def extract_entities(self, text: str) -> list[str]:
        """Extract entities from text."""
        ...


# =============================================================================
# Guardrail Protocols
# =============================================================================


@runtime_checkable
class OutputGuardrailProtocol(Protocol):
    """Protocol for output guardrails."""

    async def check(
        self,
        context: Any,
        output: str,
    ) -> Any:
        """Check output validity."""
        ...


@runtime_checkable
class InputGuardrailProtocol(Protocol):
    """Protocol for input guardrails."""

    async def check(
        self,
        context: Any,
        input: str,
    ) -> Any:
        """Check input validity."""
        ...


# =============================================================================
# Orchestrator Protocols
# =============================================================================


@runtime_checkable
class OrchestratorProtocol(Protocol):
    """Protocol for orchestrators."""

    def register_agent(self, name: str, agent: AgentProtocol) -> None:
        """Register a specialist agent."""
        ...

    async def run(
        self,
        input: str,
        session_id: str | None = None,
    ) -> Any:
        """Execute through orchestrator."""
        ...


# =============================================================================
# Adapter Protocols
# =============================================================================


@runtime_checkable
class AgentAdapterProtocol(Protocol):
    """Protocol for agent adapters."""

    @property
    def agent(self) -> AgentProtocol:
        """Wrapped agent."""
        ...

    @property
    def domain(self) -> str:
        """Domain identifier."""
        ...
