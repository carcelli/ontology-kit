"""
OpenAI Agents SDK adapter for ontology-driven workflows.

This adapter wraps OpenAI's Agent/Runner to inject ontology context
while preserving their orchestration capabilities (structured outputs,
handoffs, streaming).

Usage:
    from agents import Agent as SDKAgent
    from agent_kit.adapters import OpenAISDKAdapter
    from agent_kit.ontology import OntologyLoader

    # Create OpenAI SDK agent
    sdk_agent = SDKAgent(
        name="ForecastAgent",
        instructions="Generate revenue forecasts",
        model="gpt-4.1"
    )

    # Wrap with ontology context
    adapter = OpenAISDKAdapter(
        sdk_agent=sdk_agent,
        ontology_path="assets/ontologies/business.ttl"
    )

    # Run with ontology grounding
    result = await adapter.run("Forecast Q1-Q3 revenue for Sunshine Bakery")
"""

from typing import Any

from agent_kit.agents.base import (
    AgentActionResult,
    AgentObservation,
    AgentPlan,
    AgentResult,
    AgentTask,
)
from agent_kit.ontology.loader import OntologyLoader

try:
    from agents import Agent as SDKAgent
    from agents import Runner

    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False
    SDKAgent = None  # type: ignore
    Runner = None  # type: ignore


class OpenAISDKAdapter:
    """
    Adapter that wraps OpenAI SDK agents with ontology context.

    This enables using OpenAI's structured outputs, handoffs, and streaming
    while grounding agent behavior in SPARQL-queryable ontologies.

    Attributes:
        sdk_agent: The wrapped OpenAI SDK Agent instance
        ontology_loader: Loader for querying ontology context
        enrich_instructions: Whether to inject ontology context into prompts
    """

    def __init__(
        self,
        sdk_agent: Any,  # SDKAgent type
        ontology_path: str | None = None,
        ontology_loader: OntologyLoader | None = None,
        enrich_instructions: bool = True,
    ):
        """
        Initialize the adapter.

        Args:
            sdk_agent: OpenAI SDK Agent instance
            ontology_path: Path to ontology file (*.ttl, *.owl)
            ontology_loader: Pre-initialized OntologyLoader (alternative to ontology_path)
            enrich_instructions: Whether to augment agent instructions with ontology context

        Raises:
            ImportError: If openai-agents SDK is not installed
            ValueError: If neither ontology_path nor ontology_loader is provided
        """
        if not OPENAI_SDK_AVAILABLE:
            raise ImportError(
                "openai-agents SDK not installed. Install via: pip install openai-agents>=0.5.0"
            )

        self.sdk_agent = sdk_agent
        self.enrich_instructions = enrich_instructions

        # Initialize ontology loader
        if ontology_loader:
            self.ontology_loader = ontology_loader
        elif ontology_path:
            self.ontology_loader = OntologyLoader(ontology_path)
            self.ontology_loader.load()
        else:
            raise ValueError("Must provide either ontology_path or ontology_loader")

    def _enrich_prompt(self, task_description: str) -> str:
        """
        Inject ontology context into task description.

        Queries ontology for relevant entities/relations and augments
        the prompt with structured context.

        Args:
            task_description: Original task from user

        Returns:
            Enriched task description with ontology context
        """
        if not self.enrich_instructions:
            return task_description

        # Example: Query ontology for relevant business entities
        # In practice, this could use semantic search or keyword extraction
        sparql_query = """
        PREFIX ex: <http://example.org/retail#>
        SELECT ?business ?name
        WHERE {
            ?business a ex:Business ;
                      ex:hasName ?name .
        }
        LIMIT 5
        """
        try:
            results = self.ontology_loader.query(sparql_query)
            if results:
                business_context = '\n'.join([f"- {r['name']}" for r in results])
                enriched = (
                    f"Ontology Context (Available Businesses):\n{business_context}\n\n" f"Task: {task_description}"
                )
                return enriched
        except Exception:
            pass  # Fallback to original if query fails

        return task_description

    async def run(self, task: AgentTask | str) -> AgentResult:
        """
        Execute the wrapped SDK agent with ontology grounding.

        Args:
            task: AgentTask or string description

        Returns:
            AgentResult with SDK output mapped to our dataclass structure
        """
        # Convert to string if AgentTask
        if isinstance(task, AgentTask):
            task_str = task.description
            task_obj = task
        else:
            task_str = task
            task_obj = AgentTask(description=task_str)

        # Enrich with ontology context
        enriched_input = self._enrich_prompt(task_str)

        # Run SDK agent
        sdk_result = await Runner.run(self.sdk_agent, enriched_input)

        # Map SDK result to our AgentResult structure
        return self._map_sdk_result(task_obj, sdk_result)

    def _map_sdk_result(self, task: AgentTask, sdk_result: Any) -> AgentResult:
        """
        Map OpenAI SDK result to our AgentResult dataclass.

        Args:
            task: Original task
            sdk_result: Result from Runner.run()

        Returns:
            AgentResult matching our interface
        """
        # Extract output from SDK result
        # SDK result structure: RunResult with .final_output, .output, .context_wrapper
        final_output = getattr(sdk_result, 'final_output', str(sdk_result))

        # Create observation (stub for now)
        observation = AgentObservation(data={'sdk_output': final_output}, notes=['SDK execution completed'])

        # Create plan (stub)
        plan = AgentPlan(steps=['Execute via OpenAI SDK'], metadata={'model': self.sdk_agent.model})

        # Create action result
        action_result = AgentActionResult(
            summary=final_output,
            artifacts={'sdk_result': sdk_result},
            log=['Executed via OpenAI SDK adapter'],
        )

        # Reflections
        reflections = [
            f"{self.sdk_agent.name} completed task via OpenAI SDK",
            f"Model: {self.sdk_agent.model}",
        ]

        return AgentResult(
            task=task, observation=observation, plan=plan, action_result=action_result, reflections=reflections
        )

    def describe(self) -> str:
        """Return description of the adapted agent."""
        return (
            f"OpenAI SDK Adapter:\n"
            f"  Agent: {self.sdk_agent.name}\n"
            f"  Model: {self.sdk_agent.model}\n"
            f"  Ontology: {self.ontology_loader.path}\n"
            f"  Enrichment: {'Enabled' if self.enrich_instructions else 'Disabled'}"
        )

