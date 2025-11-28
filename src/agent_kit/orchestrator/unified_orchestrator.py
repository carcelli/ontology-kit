"""
Unified orchestrator combining ADK infrastructure and OpenAI SDK execution.

From first principles: The orchestrator is the brain that coordinates:
1. Task understanding (intent classification)
2. Agent selection (routing to specialists)
3. Execution management (handoffs, retries)
4. Result aggregation (combining outputs)
5. State management (sessions, context)

This implementation uses:
- ADK patterns for infrastructure (sessions, events, memory)
- OpenAI SDK for agent execution (handoffs, guardrails)
- Ontology for domain knowledge (entities, relationships)
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from pydantic import BaseModel, Field

from agent_kit.adapters import OntologyAgentAdapter, OntologyOutputGuardrail
from agent_kit.adapters.handoff_manager import HandoffContext, OntologyHandoffManager
from agent_kit.events import OntologyEvent, OntologyEventLogger
from agent_kit.memory import OntologyMemoryService
from agent_kit.ontology.loader import OntologyLoader
from agent_kit.runners import OntologyRunner, RunConfig, RunResult
from agent_kit.sessions import OntologySessionService, create_session_backend

logger = logging.getLogger(__name__)

# Try to import SDKs
try:
    from agents import Agent, Runner as OpenAIRunner
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False
    Agent = None  # type: ignore
    OpenAIRunner = None  # type: ignore


class OrchestratorConfig(BaseModel):
    """Configuration for unified orchestrator."""
    model_config = {"extra": "forbid"}

    domain: str = Field(default="business", description="Domain identifier")

    # Session configuration
    session_backend: str = Field(
        default="memory", description="Session backend type"
    )
    session_db_path: str = Field(
        default="sessions.db", description="Path for SQLite backend"
    )

    # Execution configuration
    max_retries: int = Field(default=3, ge=0, description="Max retries on failure")
    timeout_seconds: float = Field(default=300.0, gt=0, description="Execution timeout")
    max_handoffs: int = Field(default=5, ge=1, description="Max handoffs per request")

    # Feature flags
    enable_memory: bool = Field(default=True, description="Enable memory service")
    enable_guardrails: bool = Field(default=True, description="Enable output guardrails")
    enable_event_logging: bool = Field(default=True, description="Enable event logging")
    enable_ontology_context: bool = Field(default=True, description="Enrich with ontology")


@dataclass
class OrchestratorResult:
    """Result from orchestrator execution."""

    output: str
    """Final output text"""

    structured_output: dict[str, Any] | None = None
    """Structured output if available"""

    agents_used: list[str] = field(default_factory=list)
    """Chain of agents that handled the request"""

    events: list[OntologyEvent] = field(default_factory=list)
    """Events generated"""

    session_id: str = ""
    """Session used"""

    duration_seconds: float = 0.0
    """Total execution time"""

    handoff_count: int = 0
    """Number of handoffs"""

    validation_passed: bool = True
    """Whether validation passed"""

    error: str | None = None
    """Error if failed"""


class UnifiedOrchestrator:
    """
    Unified orchestrator combining ADK infrastructure and OpenAI SDK execution.

    This is the main entry point for production agent systems.

    Features:
    - Multi-agent coordination with OpenAI SDK handoffs
    - Session management with ADK-compatible backends
    - Event logging with ontology context
    - Memory for cross-session recall
    - Domain-aware validation

    Example:
        >>> ontology = OntologyLoader("assets/ontologies/business.ttl")
        >>> orchestrator = UnifiedOrchestrator(ontology)
        >>>
        >>> # Register specialists
        >>> orchestrator.register_agent("ForecastAgent", forecast_agent)
        >>> orchestrator.register_agent("OptimizerAgent", optimizer_agent)
        >>>
        >>> # Execute
        >>> result = await orchestrator.run("Forecast and optimize revenue")
        >>> print(result.output)
    """

    def __init__(
        self,
        ontology: OntologyLoader,
        config: OrchestratorConfig | None = None,
    ):
        """
        Initialize unified orchestrator.

        Args:
            ontology: OntologyLoader for domain context
            config: Configuration options
        """
        self.ontology = ontology
        self.config = config or OrchestratorConfig()

        # Initialize services
        self._init_services()

        # Agent registry
        self._agents: dict[str, OntologyAgentAdapter] = {}
        self._orchestrator_agent: Agent | None = None

        logger.info(f"Initialized UnifiedOrchestrator for domain: {self.config.domain}")

    def _init_services(self) -> None:
        """Initialize infrastructure services."""
        # Session service
        backend = create_session_backend(
            self.config.session_backend,
            db_path=self.config.session_db_path,
        )
        self.session_service = OntologySessionService(backend, self.ontology)

        # Event logger
        if self.config.enable_event_logging:
            self.event_logger = OntologyEventLogger(
                self.ontology, self.config.domain
            )
        else:
            self.event_logger = None

        # Memory service
        if self.config.enable_memory:
            self.memory_service = OntologyMemoryService(
                self.ontology, self.config.domain
            )
        else:
            self.memory_service = None

        # Runner
        self.runner = OntologyRunner(
            self.ontology,
            self.config.domain,
            event_logger=self.event_logger,
            memory_service=self.memory_service,
        )

        # Handoff manager (if OpenAI SDK available)
        if OPENAI_SDK_AVAILABLE:
            self.handoff_manager = OntologyHandoffManager(
                self.ontology, self.config.domain
            )
        else:
            self.handoff_manager = None

    def register_agent(
        self,
        name: str,
        agent: OntologyAgentAdapter | Any,
    ) -> None:
        """
        Register a specialist agent.

        Args:
            name: Agent name (used for routing)
            agent: OntologyAgentAdapter or OpenAI SDK Agent
        """
        if isinstance(agent, OntologyAgentAdapter):
            self._agents[name] = agent
        else:
            # Wrap with adapter
            adapter = OntologyAgentAdapter(
                agent, self.ontology, self.config.domain
            )
            self._agents[name] = adapter

        logger.info(f"Registered agent: {name}")

    def create_orchestrator_agent(
        self,
        instructions: str | None = None,
    ) -> None:
        """
        Create the orchestrator agent that routes to specialists.

        Args:
            instructions: Custom orchestrator instructions
        """
        if not OPENAI_SDK_AVAILABLE:
            logger.warning("OpenAI SDK not available, using simple routing")
            return

        # Get specialist agents
        specialists = [adapter.agent for adapter in self._agents.values()]

        if not specialists:
            raise ValueError("No specialists registered. Register agents first.")

        # Build default instructions
        specialist_info = "\n".join([
            f"- {name}: Handles {adapter.domain} tasks"
            for name, adapter in self._agents.items()
        ])

        default_instructions = f"""You are a business intelligence orchestrator.

Your role is to understand user requests and route them to specialist agents.

Available specialists:
{specialist_info}

Routing guidelines:
1. Analyze the user's request to understand their intent
2. Transfer to the appropriate specialist
3. For complex requests, break into subtasks and coordinate specialists
4. Synthesize results if multiple specialists are involved

If unsure, ask clarifying questions before routing.
"""

        self._orchestrator_agent = Agent(
            name=f"{self.config.domain.capitalize()}Orchestrator",
            instructions=instructions or default_instructions,
            handoffs=specialists,
        )

        # Add guardrails if enabled
        if self.config.enable_guardrails:
            self._orchestrator_agent.output_guardrails = [
                OntologyOutputGuardrail(self.config.domain)
            ]

        logger.info(f"Created orchestrator with {len(specialists)} specialists")

    async def run(
        self,
        input: str,
        session_id: str | None = None,
        user_id: str = "default",
    ) -> OrchestratorResult:
        """
        Execute request through orchestrator.

        Args:
            input: User input text
            session_id: Optional session ID (auto-generated if not provided)
            user_id: User identifier

        Returns:
            OrchestratorResult with output and metadata
        """
        start_time = time.time()
        session_id = session_id or f"orch_{int(time.time())}_{id(self)}"

        # Initialize tracking
        if self.event_logger:
            self.event_logger.start_tracking(session_id)

        try:
            # Get session
            session = await self.session_service.get_session(session_id)
            session["user_id"] = user_id

            # Run with orchestrator or simple routing
            if self._orchestrator_agent and OPENAI_SDK_AVAILABLE:
                output, agents_used = await self._run_with_handoffs(
                    input, session_id
                )
            else:
                output, agents_used = await self._run_simple_routing(
                    input, session_id
                )

            # Store in memory if enabled
            if self.memory_service:
                await self.memory_service.store(
                    content=f"Q: {input}\nA: {output}",
                    user_id=user_id,
                    session_id=session_id,
                )

            # Get events
            events = []
            if self.event_logger:
                events = self.event_logger.get_events(session_id)

            duration = time.time() - start_time

            return OrchestratorResult(
                output=output,
                agents_used=agents_used,
                events=events,
                session_id=session_id,
                duration_seconds=duration,
                handoff_count=len(agents_used) - 1 if agents_used else 0,
            )

        except Exception as e:
            logger.error(f"Orchestrator failed: {e}")
            duration = time.time() - start_time

            return OrchestratorResult(
                output="",
                session_id=session_id,
                duration_seconds=duration,
                validation_passed=False,
                error=str(e),
            )

        finally:
            if self.event_logger:
                self.event_logger.stop_tracking(session_id)

    async def _run_with_handoffs(
        self,
        input: str,
        session_id: str,
    ) -> tuple[str, list[str]]:
        """Run using OpenAI SDK handoffs."""
        result = await OpenAIRunner.run(
            self._orchestrator_agent,
            input=input,
        )

        # Track agents used (would need proper handoff tracking)
        agents_used = [self._orchestrator_agent.name]

        return result.final_output, agents_used

    async def _run_simple_routing(
        self,
        input: str,
        session_id: str,
    ) -> tuple[str, list[str]]:
        """Run with simple keyword-based routing."""
        # Simple routing based on keywords
        input_lower = input.lower()

        selected_agent = None
        for name, adapter in self._agents.items():
            name_lower = name.lower()
            if any(word in name_lower for word in input_lower.split()):
                selected_agent = adapter
                break

        # Fallback to first agent
        if not selected_agent and self._agents:
            selected_agent = next(iter(self._agents.values()))

        if not selected_agent:
            return "No agents available to handle this request.", []

        # Run selected agent
        config = RunConfig(
            session_id=session_id,
            domain=self.config.domain,
        )
        result = await self.runner.run(selected_agent, input, config)

        return result.output, [selected_agent.agent.name]

    async def search_context(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Search memory for relevant context.

        Args:
            query: Search query
            user_id: User to search for
            limit: Max results

        Returns:
            List of relevant memory entries
        """
        if not self.memory_service:
            return []

        results = await self.memory_service.search(query, user_id, limit)
        return [r.entry.to_dict() for r in results]

    def get_registered_agents(self) -> list[str]:
        """Get list of registered agent names."""
        return list(self._agents.keys())

    def get_session_history(self, session_id: str) -> list[OntologyEvent]:
        """Get event history for session."""
        if self.event_logger:
            return self.event_logger.get_events(session_id)
        return []


# Convenience function to create pre-configured orchestrator
def create_business_orchestrator(
    ontology_path: str = "assets/ontologies/business.ttl",
) -> UnifiedOrchestrator:
    """
    Create orchestrator pre-configured for business domain.

    Args:
        ontology_path: Path to ontology file

    Returns:
        UnifiedOrchestrator configured for business
    """
    ontology = OntologyLoader(ontology_path)
    try:
        ontology.load()
    except Exception as e:
        logger.warning(f"Could not load ontology: {e}")

    config = OrchestratorConfig(
        domain="business",
        session_backend="memory",
        enable_memory=True,
        enable_guardrails=True,
    )

    return UnifiedOrchestrator(ontology, config)


