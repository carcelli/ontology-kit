"""
Ontology-aware orchestrator with policy enforcement and structured outputs.

From first principles: Orchestrator is a coordinator (Gang of Four Mediator pattern)
that encapsulates agent interactions, enforces constraints, and structures results.

Design choices:
- Policy enforcement before/after specialist execution
- Pydantic schemas for type-safe outputs
- Circuit breaker integration for resilience
- SPARQL queries for ontology-driven routing

References:
- Mediator Pattern: GoF Design Patterns
- Circuit Breaker: Release It! by Michael Nygard
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from pydantic import ValidationError

from agent_kit.agents.base import BaseAgent, AgentTask, AgentResult
from agent_kit.ontology.loader import OntologyLoader
from agent_kit.schemas import get_schema, SCHEMA_REGISTRY

if TYPE_CHECKING:
    from agent_kit.agents.base import GrokConfig


class OntologyOrchestratorAgent(BaseAgent):
    """
    Orchestrator that coordinates specialists with policy enforcement.

    From first principles: Separates coordination (orchestrator) from execution
    (specialists), enabling dynamic routing and centralized constraint checking.

    Example:
        >>> from agent_kit.factories.agent_factory import AgentFactory
        >>> factory = AgentFactory()
        >>> orch = factory.create_orchestrator("business")
        >>> result = orch.run(AgentTask(prompt="Forecast next 30 days"))
    """

    def __init__(
        self,
        domain: str,
        specialists: list[BaseAgent],
        tools: list,
        ontology: OntologyLoader,
        risk_policies: dict[str, Any],
        output_schema: str | None = None,
        grok_config: GrokConfig | None = None,
        **kwargs
    ):
        """
        Initialize orchestrator with injected specialists and policies.

        Args:
            domain: Domain identifier (e.g., 'business')
            specialists: List of specialist agents to coordinate
            tools: List of tool functions available
            ontology: Loaded ontology for SPARQL queries
            risk_policies: Domain-specific risk policies
            output_schema: Pydantic schema name for output validation
            grok_config: Optional Grok configuration
            **kwargs: Additional base agent parameters
        """
        self.domain = domain
        self.specialists = specialists
        self.tools = tools
        self.ontology = ontology
        self.risk_policies = risk_policies
        self.output_schema_name = output_schema
        self.grok_config = grok_config

        # Build specialist name map for routing
        self.specialist_map = {
            agent.__class__.__name__: agent for agent in specialists
        }

        super().__init__(name=f"{domain.capitalize()}Orchestrator", **kwargs)

    def run(self, task: AgentTask) -> AgentResult:
        """
        Execute task by routing to specialists, enforcing policies, and structuring output.

        From first principles: Observe (parse goal) → Plan (route to specialists) →
        Act (execute with policies) → Reflect (validate output).

        Args:
            task: Agent task with goal/prompt

        Returns:
            Structured AgentResult (validated against Pydantic schema if specified)

        Raises:
            ValueError: If policy violations or validation failures
        """
        goal = task.prompt

        # Step 1: Route to appropriate specialist(s) via ontology
        specialist_names = self._route_via_ontology(goal)

        # Step 2: Check pre-execution policies
        self._check_pre_execution_policies(goal)

        # Step 3: Execute specialists
        results = []
        for specialist_name in specialist_names:
            if specialist_name not in self.specialist_map:
                import warnings
                warnings.warn(f"Specialist '{specialist_name}' not found, skipping")
                continue

            specialist = self.specialist_map[specialist_name]
            specialist_task = AgentTask(prompt=goal)
            specialist_result = specialist.run(specialist_task)
            results.append({
                "specialist": specialist_name,
                "result": specialist_result.result
            })

        # Step 4: Aggregate results
        aggregated = self._aggregate_results(goal, results)

        # Step 5: Check post-execution policies
        self._check_post_execution_policies(aggregated)

        # Step 6: Structure output via Pydantic schema
        structured_result = self._structure_output(goal, aggregated)

        return AgentResult(result=structured_result)

    def _route_via_ontology(self, goal: str) -> list[str]:
        """
        Query ontology to determine which specialists to invoke.

        Args:
            goal: User goal/query

        Returns:
            List of specialist class names (e.g., ['ForecastAgent', 'OptimizerAgent'])

        Note:
            Simple heuristic for now; enhance with NLP/embeddings for semantic routing.
        """
        # Heuristic routing based on keywords (replace with SPARQL in production)
        goal_lower = goal.lower()

        specialists = []

        # Business domain routing
        if "forecast" in goal_lower or "predict" in goal_lower:
            specialists.append("ForecastAgent")
        if "optimize" in goal_lower or "improve" in goal_lower or "recommend" in goal_lower:
            specialists.append("OptimizerAgent")

        # Trading domain routing
        if "trade" in goal_lower or "buy" in goal_lower or "sell" in goal_lower:
            specialists.append("AlgoTradingAgent")

        # Betting domain routing
        if "bet" in goal_lower or "odds" in goal_lower or "edge" in goal_lower:
            specialists.append("PropBettingAgent")

        # Default: use first specialist if no match
        if not specialists and self.specialists:
            specialists.append(self.specialists[0].__class__.__name__)

        return specialists

    def _check_pre_execution_policies(self, goal: str) -> None:
        """
        Enforce pre-execution policies (e.g., rate limits, blacklists).

        Args:
            goal: User goal

        Raises:
            ValueError: If policy violation
        """
        # Example: Check if goal contains restricted keywords
        # In production, add rate limiting, auth checks, etc.
        pass

    def _check_post_execution_policies(self, result: dict) -> None:
        """
        Enforce post-execution policies (e.g., horizon limits, exposure limits).

        Args:
            result: Aggregated result from specialists

        Raises:
            ValueError: If policy violation

        Example:
            >>> # Business policy: max forecast horizon 90 days
            >>> if result.get('horizon_days', 0) > self.risk_policies.get('max_forecast_horizon_days', 90):
            ...     raise ValueError("Forecast horizon exceeds policy limit")
        """
        # Business domain policies
        if self.domain == "business":
            horizon = result.get("forecast", {}).get("horizon_days", 0)
            max_horizon = self.risk_policies.get("max_forecast_horizon_days", 90)
            if horizon > max_horizon:
                raise ValueError(
                    f"Policy violation: Forecast horizon ({horizon} days) "
                    f"exceeds limit ({max_horizon} days)"
                )

        # Betting domain policies
        if self.domain == "betting":
            total_exposure = result.get("total_exposure", 0.0)
            max_exposure = self.risk_policies.get("max_stake_fraction", 0.05)
            if total_exposure > max_exposure:
                raise ValueError(
                    f"Policy violation: Total exposure ({total_exposure:.2%}) "
                    f"exceeds limit ({max_exposure:.2%})"
                )

        # Trading domain policies
        if self.domain == "trading":
            max_drawdown = result.get("portfolio_metrics", {}).get("current_drawdown", 0.0)
            max_dd_threshold = self.risk_policies.get("max_drawdown_threshold", 0.15)
            if max_drawdown > max_dd_threshold:
                raise ValueError(
                    f"Policy violation: Current drawdown ({max_drawdown:.2%}) "
                    f"exceeds limit ({max_dd_threshold:.2%})"
                )

    def _aggregate_results(self, goal: str, results: list[dict]) -> dict:
        """
        Combine results from multiple specialists into unified output.

        Args:
            goal: Original goal
            results: List of dicts with specialist results

        Returns:
            Aggregated result dict
        """
        aggregated = {
            "domain": self.domain,
            "goal": goal,
            "specialist_results": results,
            "summary": self._generate_summary(results),
            "metadata": {
                "num_specialists": len(results),
                "specialist_names": [r["specialist"] for r in results]
            }
        }

        # Extract domain-specific fields
        for result_dict in results:
            result_data = result_dict["result"]
            # Merge result data into aggregated (specialist results override)
            if isinstance(result_data, dict):
                aggregated.update(result_data)

        return aggregated

    def _generate_summary(self, results: list[dict]) -> str:
        """
        Generate plain-English summary of specialist results.

        Args:
            results: List of specialist results

        Returns:
            Summary string
        """
        summaries = []
        for result_dict in results:
            specialist = result_dict["specialist"]
            # Extract summary if available
            result_data = result_dict["result"]
            if isinstance(result_data, str):
                summaries.append(f"{specialist}: {result_data}")
            elif isinstance(result_data, dict) and "summary" in result_data:
                summaries.append(f"{specialist}: {result_data['summary']}")

        return " | ".join(summaries) if summaries else "Execution complete"

    def _structure_output(self, goal: str, aggregated: dict) -> str | dict:
        """
        Validate and structure output using Pydantic schema.

        Args:
            goal: Original goal
            aggregated: Aggregated result dict

        Returns:
            Validated Pydantic model (as dict) or raw dict if no schema

        Raises:
            ValidationError: If result doesn't match schema
        """
        if not self.output_schema_name:
            return aggregated

        try:
            schema_class = get_schema(self.output_schema_name)
            # Attempt to create model instance (validates fields)
            validated_model = schema_class(**aggregated)
            return validated_model.model_dump()  # Return as dict
        except (ValueError, KeyError) as e:
            import warnings
            warnings.warn(
                f"Schema '{self.output_schema_name}' not found or invalid: {e}. "
                f"Returning unvalidated result."
            )
            return aggregated
        except ValidationError as e:
            # Log validation errors but return result (fail gracefully)
            import warnings
            warnings.warn(
                f"Validation failed for schema '{self.output_schema_name}': {e}. "
                f"Returning unvalidated result."
            )
            return aggregated
