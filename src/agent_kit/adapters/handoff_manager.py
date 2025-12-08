"""
Enhanced handoff management for OpenAI SDK multi-agent coordination.

From first principles: Handoffs enable agents to transfer control to specialists.
We enhance this with:
- Ontology context passing between agents
- Session state preservation across handoffs
- Domain-aware routing decisions
- Event logging for handoff tracing
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from agent_kit.events import OntologyEventLogger
from agent_kit.ontology.loader import OntologyLoader

logger = logging.getLogger(__name__)

# Try to import OpenAI SDK
try:
    from agents import Agent, Runner, handoff
    from agents.handoffs import Handoff

    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False
    Agent = None  # type: ignore
    Runner = None  # type: ignore
    Handoff = None  # type: ignore

    def handoff(*args, **kwargs):
        raise ImportError("OpenAI SDK not installed")


@dataclass
class HandoffContext: 
    """Context passed during agent handoffs."""

    original_input: str = ""
    """Original user input"""

    summary: str = ""
    """Summary of work done so far"""

    entities: list[str] = field(default_factory=list)
    """Entities extracted from conversation"""

    sparql_queries: list[str] = field(default_factory=list)
    """SPARQL queries executed"""

    artifacts: dict[str, Any] = field(default_factory=dict)
    """Artifacts produced (forecasts, recommendations, etc.)"""

    session_id: str = ""
    """Session identifier"""

    handoff_chain: list[str] = field(default_factory=list)
    """Chain of agents that have handled this request"""

    def to_prompt_context(self) -> str:
        """Convert to context string for agent prompts."""
        parts = []

        if self.summary:
            parts.append(f"Previous work summary: {self.summary}")

        if self.entities:
            parts.append(f"Relevant entities: {', '.join(self.entities[:10])}")

        if self.artifacts:
            parts.append(f"Available artifacts: {list(self.artifacts.keys())}")

        if self.handoff_chain:
            parts.append(f"Previous agents: {' → '.join(self.handoff_chain)}")

        return "\n".join(parts)


class OntologyHandoffManager:
    """
    Manager for ontology-aware agent handoffs.

    Features:
    - Context preservation across handoffs
    - Domain-based routing
    - Event logging for tracing
    - Graceful fallbacks

    Example:
        >>> manager = OntologyHandoffManager(ontology)
        >>>
        >>> # Create agents
        >>> forecast_agent = manager.create_specialist("ForecastAgent", forecast_instructions)
        >>> optimizer_agent = manager.create_specialist("OptimizerAgent", optimizer_instructions)
        >>>
        >>> # Create orchestrator with handoffs
        >>> orchestrator = manager.create_orchestrator(
        ...     "BusinessOrchestrator",
        ...     [forecast_agent, optimizer_agent],
        ... )
        >>>
        >>> # Execute
        >>> result = await manager.run(orchestrator, "Forecast and optimize")
    """

    def __init__(
        self,
        ontology: OntologyLoader,
        domain: str = "business",
    ):
        """
        Initialize handoff manager.

        Args:
            ontology: OntologyLoader for context
            domain: Domain identifier
        """
        if not OPENAI_SDK_AVAILABLE:
            raise ImportError("OpenAI SDK required for handoff management")

        self.ontology = ontology
        self.domain = domain
        self.event_logger = OntologyEventLogger(ontology, domain)
        self._agents: dict[str, Agent] = {}
        self._context: HandoffContext | None = None

    def create_specialist(
        self,
        name: str,
        instructions: str,
        tools: list[Any] | None = None,
    ) -> Agent:
        """
        Create a specialist agent.

        Args:
            name: Agent name
            instructions: Agent instructions
            tools: Agent tools

        Returns:
            OpenAI SDK Agent
        """
        # Enhance instructions with ontology context
        enhanced = self._enhance_instructions(instructions)

        agent = Agent(
            name=name,
            instructions=enhanced,
            tools=tools or [],
        )

        self._agents[name] = agent
        return agent

    def create_orchestrator(
        self,
        name: str,
        specialists: list[Agent],
        instructions: str | None = None,
    ) -> Agent:
        """
        Create an orchestrator agent with handoffs to specialists.

        Args:
            name: Orchestrator name
            specialists: List of specialist agents to route to
            instructions: Optional custom instructions

        Returns:
            Orchestrator Agent with handoffs configured
        """
        # Build specialist descriptions
        specialist_info = "\n".join(
            [
                f"- {agent.name}: {self._get_agent_description(agent)}"
                for agent in specialists
            ]
        )

        default_instructions = f"""You are an orchestrator that routes tasks to specialist agents.

Available specialists:
{specialist_info}

When a user request comes in:
1. Analyze the intent
2. Transfer to the appropriate specialist using handoff
3. If the request needs multiple specialists, handle sequentially
4. Only handle simple queries yourself

Always transfer complex analysis tasks to specialists.
"""

        final_instructions = instructions or default_instructions
        enhanced = self._enhance_instructions(final_instructions)

        orchestrator = Agent(
            name=name,
            instructions=enhanced,
            handoffs=specialists,
        )

        self._agents[name] = orchestrator
        return orchestrator

    async def run(
        self,
        agent: Agent,
        input: str,
        context: HandoffContext | None = None,
    ) -> tuple[str, HandoffContext]:
        """
        Run agent with handoff context tracking.

        Args:
            agent: Agent to execute
            input: User input
            context: Optional initial context

        Returns:
            Tuple of (output, updated_context)
        """
        # Initialize or update context
        self._context = context or HandoffContext(original_input=input)
        self._context.original_input = input

        session_id = self._context.session_id or f"handoff_{id(agent)}"
        self.event_logger.start_tracking(session_id)

        try:
            # Build enhanced input with context
            if self._context.handoff_chain:
                enhanced_input = (
                    f"{self._context.to_prompt_context()}\n\nNew request: {input}"
                )
            else:
                enhanced_input = input

            # Execute
            result = await Runner.run(agent, input=enhanced_input)
            output = result.final_output

            # Update context
            self._context.summary = output[:500] if len(
                output) > 500 else output
            self._context.handoff_chain.append(agent.name)

            # Log event
            self.event_logger.create_event(
                agent_name=agent.name,
                task=input,
                result={"summary": output},
                session_id=session_id,
            )

            return output, self._context

        finally:
            self.event_logger.stop_tracking(session_id)

    def create_dynamic_handoff(
        self,
        routing_fn: Callable[[str], str],
    ) -> Callable[[str], Agent]:
        """
        Create a dynamic handoff function based on input analysis.

        Args:
            routing_fn: Function that takes input and returns agent name

        Returns:
            Function that returns appropriate agent
        """

        def dynamic_router(input: str) -> Agent:
            agent_name = routing_fn(input)
            if agent_name in self._agents:
                return self._agents[agent_name]
            # Fallback to first agent
            return next(iter(self._agents.values()))

        return dynamic_router

    def create_ontology_router(self) -> Callable[[str], str]:
        """
        Create a routing function based on ontology entity matching.

        Returns:
            Function that analyzes input and returns best agent name
        """

        def route_by_entities(input: str) -> str:
            input_lower = input.lower()

            # Simple keyword-based routing
            if any(word in input_lower for word in ["forecast", "predict", "trend"]):
                return "ForecastAgent"

            if any(
                word in input_lower for word in ["optimize", "improve", "recommend"]
            ):
                return "OptimizerAgent"

            if any(word in input_lower for word in ["bet", "odds", "probability"]):
                return "PropBettingAgent"

            if any(word in input_lower for word in ["trade", "buy", "sell", "stock"]):
                return "AlgoTradingAgent"

            # Default
            return "ForecastAgent"

        return route_by_entities

    def _enhance_instructions(self, instructions: str) -> str:
        """Enhance instructions with ontology context."""
        context = self._get_ontology_context()

        return f"""{instructions}

## Domain Context
- Domain: {self.domain}
- Available entities: {", ".join(context["entities"][:5])}

## Guidelines
- Query the ontology for entity relationships when needed
- Validate outputs against domain schemas
- Track important entities and decisions
"""

    def _get_ontology_context(self) -> dict[str, list[str]]:
        """Get context from ontology."""
        query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?label WHERE {
            ?entity rdfs:label ?label .
        }
        LIMIT 10
        """
        try:
            results = self.ontology.query(query)
            entities = [
                r.get("label", {}).get("value", "") for r in results if r.get("label")
            ]
        except Exception:
            entities = []

        return {"entities": entities}

    def _get_agent_description(self, agent: Agent) -> str:
        """Extract description from agent instructions."""
        instructions = agent.instructions
        if isinstance(instructions, str):
            # Take first sentence
            first_line = instructions.split("\n")[0]
            return first_line[:100]
        return "Specialist agent"


def create_handoff_pipeline(
    ontology: OntologyLoader,
    domain: str,
    agent_configs: list[dict[str, Any]],
) -> tuple[Agent, OntologyHandoffManager]:
    """
    Create a complete handoff pipeline from configuration.

    Args:
        ontology: OntologyLoader
        domain: Domain identifier
        agent_configs: List of agent configurations

    Returns:
        Tuple of (orchestrator_agent, handoff_manager)

    Example:
        >>> configs = [
        ...     {"name": "ForecastAgent", "instructions": "...", "tools": [predict]},
        ...     {"name": "OptimizerAgent", "instructions": "...", "tools": [optimize]},
        ... ]
        >>> orchestrator, manager = create_handoff_pipeline(ontology, "business", configs)
    """
    manager = OntologyHandoffManager(ontology, domain)

    specialists = []
    for config in agent_configs:
        agent = manager.create_specialist(
            name=config["name"],
            instructions=config["instructions"],
            tools=config.get("tools", []),
        )
        specialists.append(agent)

    orchestrator = manager.create_orchestrator(
        name=f"{domain.capitalize()}Orchestrator",
        specialists=specialists,
    )

    return orchestrator, manager
