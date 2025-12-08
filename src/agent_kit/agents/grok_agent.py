"""
Ontology-aware agent using Grok (xAI) for advanced reasoning.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

import agent_kit.agents.base as base_module
from agent_kit.agents.base import (
    TENACITY_AVAILABLE,
    AgentActionResult,
    AgentObservation,
    AgentPlan,
    AgentResult,
    AgentTask,
    BaseAgent,
    retry,
)

try:  # pragma: no cover - optional dependency
    from tenacity import stop_after_attempt, wait_exponential
except Exception:  # pragma: no cover
    stop_after_attempt = wait_exponential = None


class GrokConfig(BaseModel):
    """
    Configuration for Grok agent integration.

    References:
        - xAI API docs: https://x.ai/api
        - OpenAI Python SDK for compatibility: https://github.com/openai/openai-python
    """

    api_key: str = Field(..., description="xAI API key (get from https://x.ai/api)")
    base_url: str = Field(default="https://api.x.ai/v1", description="xAI API endpoint")
    model: str = Field(
        default="grok-beta",
        description="Grok model version (grok-beta, grok-4 when available)",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for response generation",
    )
    max_tokens: int = Field(
        default=2048, ge=1, le=131072, description="Maximum tokens in response"
    )
    seed: int | None = Field(
        default=42, description="Random seed for reproducible outputs"
    )


class GrokAgent(BaseAgent):
    """
    Ontology-aware agent using Grok (xAI) for advanced reasoning.

    Implements observe-plan-act-reflect loop with SPARQL grounding to prevent
    hallucinations and ensure semantic consistency with business ontology.
    """

    def __init__(
        self,
        config: GrokConfig,
        ontology: Any,
        tool_registry: dict[str, Any] | None = None,
        system_prompt: str | None = None,
    ) -> None:
        """
        Initialize Grok agent with ontology and tool access.
        """
        super().__init__(
            name="GrokAgent",
            description="Grok-powered ontology agent",
            agent_id="GrokAgent",
            config={"model": config.model},
        )

        if not base_module.OPENAI_AVAILABLE:
            raise ImportError(
                "openai package required for GrokAgent. Install: pip install openai>=1.0.0"
            )

        self.config = config
        self.ontology = ontology
        self.tool_registry = tool_registry or {}
        # memory is initialized in BaseAgent in our new design, but we can init here too just in case
        if not hasattr(self, "memory"):
            self.memory: list[str] = []

        if not config.api_key:
            raise ValueError(
                "Grok API key is required. Set XAI_API_KEY env var or pass api_key to GrokConfig."
            )

        self.client = base_module.OpenAI(api_key=config.api_key, base_url=config.base_url)

        self.system_prompt = system_prompt or (
            "You are an ontology-driven AI agent for small business optimization. "
            "Your decisions MUST be grounded in the provided RDF ontology and SPARQL query results. "
            "Always prioritize semantic consistency over speculation. "
            "When uncertain, query the ontology for clarification."
        )

    def observe(self, task: AgentTask) -> AgentObservation:
        """
        Query ontology for task-relevant context via SPARQL.
        """
        # Extract key terms from task for SPARQL query
        # In production: use NER or keyword extraction
        task_lower = task.prompt.lower()

        # Construct SPARQL query based on task type
        sparql = """
        PREFIX : <http://agent_kit.io/business#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?entity ?property ?value
        WHERE {
            ?entity a :BusinessEntity ;
                    ?property ?value .
        }
        LIMIT 10
        """

        try:
            # Check if ontology has query method (OntologyLoader) or graph.query (rdflib Graph)
            if hasattr(self.ontology, "query"):
                results = self.ontology.query(sparql)
            elif hasattr(self.ontology, "graph") and self.ontology.graph is not None:
                results = self.ontology.graph.query(sparql)
                # Convert rdflib results to list of dicts
                results = [
                    {
                        str(var): str(row[var]) if row[var] is not None else None
                        for var in results.vars
                    }
                    for row in results
                ]
            else:
                results = []

            observations = [
                f"{row.get('entity', 'N/A')}: {row.get('property', 'N/A')} = {row.get('value', 'N/A')}"
                for row in results
            ]
            content = (
                "\n".join(observations)
                if observations
                else "No ontology data found for task."
            )
        except Exception as e:
            content = f"Ontology query failed: {str(e)}"

        # Return object compatible with Pydantic or NamedTuple
        # We will make AgentObservation flexible in base.py
        return AgentObservation(
            content=content, data={"raw_sparql": sparql, "task_lower": task_lower}
        )

    def plan(self, task: AgentTask, observation: AgentObservation) -> AgentPlan:
        """
        Use Grok to generate actionable plan from observations.
        """
        obs_content = getattr(observation, "content", str(observation))

        user_prompt = f"""
Task: {task.prompt}

Ontology Context:
{obs_content}

Available Tools:
{", ".join(self.tool_registry.keys()) if self.tool_registry else "None"}

Previous Learnings:
{chr(10).join(self.memory[-3:]) if self.memory else "None"}

Generate a step-by-step plan to accomplish the task, grounded in the ontology.
Specify which tools to invoke and why.
"""

        try:
            response = self._call_grok_with_retry(user_prompt)
            plan_text = response.choices[0].message.content or "No plan generated."
        except Exception as e:
            plan_text = f"Planning failed: {str(e)}"

        action = "execute_plan"
        if "visualize" in plan_text.lower():
            action = "generate_visualization"
        elif "cluster" in plan_text.lower():
            action = "cluster_data"
        elif "train" in plan_text.lower():
            action = "train_model"

        return AgentPlan(thought=plan_text, action=action)

    def act(
        self, plan: AgentPlan, observation: AgentObservation | None = None, task: AgentTask | None = None
    ) -> AgentActionResult:
        """
        Execute plan by invoking tools from registry.
        """
        action = plan.action

        if (
            action == "generate_visualization"
            and "generate_interactive_leverage_viz" in self.tool_registry
        ):
            try:
                viz_tool = self.tool_registry["generate_interactive_leverage_viz"]
                result = viz_tool(
                    terms=["Revenue", "Budget", "Marketing", "Sales"],
                    kpi_term="Revenue",
                    actionable_terms=["Budget", "Marketing"],
                    output_file="outputs/grok_agent_viz.html",
                )
                viz_path = (
                    result.get("viz_path", "unknown")
                    if isinstance(result, dict)
                    else str(result)
                )
                return AgentActionResult(output=f"Visualization generated: {viz_path}")
            except Exception as e:
                return AgentActionResult(output=f"Visualization failed: {str(e)}")

        elif action == "cluster_data" and "cluster_data" in self.tool_registry:
            try:
                cluster_tool = self.tool_registry["cluster_data"]
                result = cluster_tool(
                    {"data": [[1, 2], [2, 3], [10, 11]], "algorithm": "DBSCAN"}
                )
                return AgentActionResult(output=f"Clustering result: {result}")
            except Exception as e:
                return AgentActionResult(output=f"Clustering failed: {str(e)}")

        else:
            return AgentActionResult(output=f"Executed plan: {plan.thought}")

    def reflect(self, task: AgentTask, result: AgentActionResult) -> None:
        """
        Use Grok to critique results and store learnings.
        """
        result_output = getattr(
            result, "output", getattr(result, "summary", str(result))
        )

        reflection_prompt = f"""
Task: {task.prompt}
Result: {result_output}

Reflect on this result:
1. Was the ontology query sufficient? What was missing?
2. Did the plan align with the task objective?
3. How can future iterations improve?

Provide 2-3 concise insights for learning.
"""

        try:
            response = self._call_grok_with_retry(reflection_prompt)
            reflection = (
                response.choices[0].message.content or "No reflection generated."
            )
            self.memory.append(reflection)
        except Exception as e:
            self.memory.append(f"Reflection failed: {str(e)}")

    def _call_grok_with_retry(self, user_prompt: str) -> Any:
        if TENACITY_AVAILABLE:

            @retry(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=2, max=10),
            )
            def _call() -> Any:
                return self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                seed=self.config.seed,
            )

            return _call()
        else:
            return self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                seed=self.config.seed,
            )

    def run(self, task: AgentTask) -> AgentResult:
        """
        Structured run that matches unit test expectations.
        """
        observation = self.observe(task)
        plan = self.plan(task, observation)
        action_result = self.act(plan, observation=observation, task=task)
        self.reflect(task, action_result)

        summary = (
            f"Task: {task.prompt}\n"
            f"Observation: {getattr(observation, 'content', observation)}\n"
            f"Plan: {plan.thought or plan.action}\n"
            f"Result: {action_result.output or action_result.summary}"
        )
        return AgentResult(result=summary)
