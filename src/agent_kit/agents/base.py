# src/agent_kit/agents/base.py
"""
Base agent framework with Grok integration for ontology-driven reasoning.

Provides abstract BaseAgent and concrete GrokAgent for xAI API-powered workflows.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, NamedTuple, Optional, Union
import os
from pydantic import BaseModel, Field

# Lazy imports for optional dependencies
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from tenacity import retry, stop_after_attempt, wait_exponential
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False


class AgentTask(NamedTuple):
    """A task for an agent to perform."""
    prompt: str

class AgentObservation(NamedTuple):
    """An observation made by an agent."""
    content: str

class AgentPlan(NamedTuple):
    """A plan created by an agent."""
    thought: str
    action: str

class AgentActionResult(NamedTuple):
    """The result of an agent's action."""
    output: str

class AgentResult(NamedTuple):
    """The final result of an agent's work."""
    result: str

class BaseAgent(ABC):
    """Base class for all agents."""

    @abstractmethod
    def run(self, task: AgentTask) -> AgentResult:
        """Run the agent on a given task."""
        pass


# ============================================================================
# Grok Agent Integration (xAI API)
# ============================================================================

class GrokConfig(BaseModel):
    """
    Configuration for Grok agent integration.
    
    References:
        - xAI API docs: https://x.ai/api
        - OpenAI Python SDK for compatibility: https://github.com/openai/openai-python
    """
    api_key: str = Field(..., description="xAI API key (get from https://x.ai/api)")
    base_url: str = Field(
        default="https://api.x.ai/v1",
        description="xAI API endpoint"
    )
    model: str = Field(
        default="grok-beta",
        description="Grok model version (grok-beta, grok-4 when available)"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for response generation"
    )
    max_tokens: int = Field(
        default=2048,
        ge=1,
        le=131072,
        description="Maximum tokens in response"
    )
    seed: Optional[int] = Field(
        default=42,
        description="Random seed for reproducible outputs"
    )


class GrokAgent(BaseAgent):
    """
    Ontology-aware agent using Grok (xAI) for advanced reasoning.
    
    Implements observe-plan-act-reflect loop with SPARQL grounding to prevent
    hallucinations and ensure semantic consistency with business ontology.
    
    Architecture:
        1. Observe: Query ontology (SPARQL) for task-relevant context
        2. Plan: Use Grok to generate actionable plan from observations
        3. Act: Execute plan via tool registry (hyperdim_viz, ml_training, etc.)
        4. Reflect: Critique results and store learnings in memory
    
    Example:
        >>> from agent_kit.ontology.loader import OntologyLoader
        >>> config = GrokConfig(api_key=os.getenv('XAI_API_KEY'))
        >>> loader = OntologyLoader('assets/ontologies/business.ttl')
        >>> ontology_graph = loader.load()
        >>> # Wrap for query method compatibility
        >>> class OntologyWrapper:
        ...     def __init__(self, g): self.g = g
        ...     def query(self, q): return self.g.query(q)
        >>> ontology = OntologyWrapper(ontology_graph)
        >>> agent = GrokAgent(config, ontology)
        >>> task = AgentTask(prompt="Optimize Q4 revenue for Sunshine Bakery")
        >>> result = agent.run(task)
        >>> print(result.result)
    
    References:
        - xAI Grok: https://x.ai/blog/grok
        - SPARQL 1.1: https://www.w3.org/TR/sparql11-query/
        - Tool Use in LLMs: Schick et al. (2023), "Toolformer"
    """
    
    def __init__(
        self,
        config: GrokConfig,
        ontology: Any,  # Type: agent_kit.ontology.loader.Ontology
        tool_registry: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> None:
        """
        Initialize Grok agent with ontology and tool access.
        
        Args:
            config: Grok API configuration
            ontology: Loaded ontology for SPARQL queries
            tool_registry: Dict mapping tool names to callables
            system_prompt: Custom system instructions (defaults to ontology-driven)
        
        Raises:
            ImportError: If openai package not installed
            ValueError: If API key invalid
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai package required for GrokAgent. Install: pip install openai>=1.0.0"
            )
        
        self.config = config
        self.ontology = ontology
        self.tool_registry = tool_registry or {}
        self.memory: List[str] = []  # Store reflections for multi-turn learning
        
        # Initialize OpenAI client with xAI endpoint
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
        
        # System prompt: emphasize ontology grounding
        self.system_prompt = system_prompt or (
            "You are an ontology-driven AI agent for small business optimization. "
            "Your decisions MUST be grounded in the provided RDF ontology and SPARQL query results. "
            "Always prioritize semantic consistency over speculation. "
            "When uncertain, query the ontology for clarification."
        )
    
    def run(self, task: AgentTask) -> AgentResult:
        """
        Execute full observe-plan-act-reflect loop.
        
        Args:
            task: Task with prompt describing business objective
        
        Returns:
            AgentResult with final output and reasoning trace
        """
        # 1. Observe
        observation = self.observe(task)
        
        # 2. Plan
        plan = self.plan(task, observation)
        
        # 3. Act
        action_result = self.act(plan)
        
        # 4. Reflect
        self.reflect(task, action_result)
        
        # Compile final result
        result_summary = (
            f"Task: {task.prompt}\n"
            f"Observation: {observation.content}\n"
            f"Plan: {plan.thought}\n"
            f"Action: {plan.action}\n"
            f"Result: {action_result.output}\n"
        )
        
        return AgentResult(result=result_summary)
    
    def observe(self, task: AgentTask) -> AgentObservation:
        """
        Query ontology for task-relevant context via SPARQL.
        
        Constructs semantic query from task description to extract relevant
        entities, relations, and constraints from business ontology.
        
        Args:
            task: Task to observe context for
        
        Returns:
            AgentObservation with SPARQL query results
        """
        # Extract key terms from task for SPARQL query
        # In production: use NER or keyword extraction
        task_lower = task.prompt.lower()
        
        # Construct SPARQL query based on task type
        # This is a simplified heuristic; expand with more sophisticated parsing
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
        
        # Execute SPARQL query
        try:
            results = list(self.ontology.query(sparql))
            observations = [
                f"{row['entity']}: {row['property']} = {row['value']}"
                for row in results
            ]
            content = "\n".join(observations) if observations else "No ontology data found for task."
        except Exception as e:
            content = f"Ontology query failed: {str(e)}"
        
        return AgentObservation(content=content)
    
    def plan(self, task: AgentTask, observation: AgentObservation) -> AgentPlan:
        """
        Use Grok to generate actionable plan from observations.
        
        Leverages Grok's reasoning capabilities to synthesize observations
        into structured plan with tool invocations.
        
        Args:
            task: Original task
            observation: Ontology-grounded observations
        
        Returns:
            AgentPlan with reasoning and action specification
        """
        # Construct prompt for Grok
        user_prompt = f"""
Task: {task.prompt}

Ontology Context:
{observation.content}

Available Tools:
{', '.join(self.tool_registry.keys()) if self.tool_registry else 'None'}

Previous Learnings:
{chr(10).join(self.memory[-3:]) if self.memory else 'None'}

Generate a step-by-step plan to accomplish the task, grounded in the ontology.
Specify which tools to invoke and why.
"""
        
        # Call Grok API with retry logic
        try:
            response = self._call_grok_with_retry(user_prompt)
            plan_text = response.choices[0].message.content or "No plan generated."
        except Exception as e:
            plan_text = f"Planning failed: {str(e)}"
        
        # Parse plan to extract action (simplified; use structured output in production)
        action = "execute_plan"  # Default action
        if "visualize" in plan_text.lower():
            action = "generate_visualization"
        elif "cluster" in plan_text.lower():
            action = "cluster_data"
        elif "train" in plan_text.lower():
            action = "train_model"
        
        return AgentPlan(thought=plan_text, action=action)
    
    def act(self, plan: AgentPlan) -> AgentActionResult:
        """
        Execute plan by invoking tools from registry.
        
        Maps plan actions to tool calls, passing extracted parameters.
        
        Args:
            plan: Plan with action specification
        
        Returns:
            AgentActionResult with tool output
        """
        # Map action to tool
        action = plan.action
        
        if action == "generate_visualization" and "generate_interactive_leverage_viz" in self.tool_registry:
            # Example: Call interactive viz tool
            try:
                viz_tool = self.tool_registry["generate_interactive_leverage_viz"]
                # Extract params from plan (simplified; use structured extraction in production)
                # The tool uses direct parameters, not a Pydantic class
                result = viz_tool(
                    terms=["Revenue", "Budget", "Marketing", "Sales"],
                    kpi_term="Revenue",
                    actionable_terms=["Budget", "Marketing"],
                    output_file="outputs/grok_agent_viz.html"
                )
                viz_path = result.get('viz_path', 'unknown') if isinstance(result, dict) else str(result)
                return AgentActionResult(output=f"Visualization generated: {viz_path}")
            except Exception as e:
                return AgentActionResult(output=f"Visualization failed: {str(e)}")
        
        elif action == "cluster_data" and "cluster_data" in self.tool_registry:
            # Example: Call clustering tool
            try:
                cluster_tool = self.tool_registry["cluster_data"]
                # Stub data; extract from plan in production
                result = cluster_tool({"data": [[1, 2], [2, 3], [10, 11]], "algorithm": "DBSCAN"})
                return AgentActionResult(output=f"Clustering result: {result}")
            except Exception as e:
                return AgentActionResult(output=f"Clustering failed: {str(e)}")
        
        else:
            # Fallback: return plan as-is
            return AgentActionResult(output=f"Executed plan: {plan.thought}")
    
    def reflect(self, task: AgentTask, result: AgentActionResult) -> None:
        """
        Use Grok to critique results and store learnings.
        
        Enables multi-turn improvement by accumulating reflections in memory.
        
        Args:
            task: Original task
            result: Action result to reflect on
        """
        reflection_prompt = f"""
Task: {task.prompt}
Result: {result.output}

Reflect on this result:
1. Was the ontology query sufficient? What was missing?
2. Did the plan align with the task objective?
3. How can future iterations improve?

Provide 2-3 concise insights for learning.
"""
        
        try:
            response = self._call_grok_with_retry(reflection_prompt)
            reflection = response.choices[0].message.content or "No reflection generated."
            self.memory.append(reflection)
        except Exception as e:
            self.memory.append(f"Reflection failed: {str(e)}")
    
    def _call_grok_with_retry(self, user_prompt: str) -> Any:
        """
        Call Grok API with exponential backoff retry logic.
        
        Handles rate limits and transient failures gracefully.
        
        Args:
            user_prompt: User message content
        
        Returns:
            OpenAI ChatCompletion response
        
        Raises:
            Exception: After max retries exhausted
        """
        if TENACITY_AVAILABLE:
            @retry(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=2, max=10)
            )
            def _call() -> Any:
                return self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    seed=self.config.seed
                )
            return _call()
        else:
            # Fallback: single attempt without retry
            return self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                seed=self.config.seed
            )