# src/agent_kit/agents/ontology_agent.py
from typing import Any

from agents import Agent as SDKAgent

from agent_kit.ontology.loader import OntologyLoader
from agent_kit.shared_context import SharedContext
from agent_kit.tools.business import optimize, predict
from agent_kit.tools.github_tools import write_to_github

# A simple registry to map tool names to functions
TOOL_REGISTRY = {
    "Predict Tool": predict,
    "Optimize Tool": optimize,
    "GitHub Tool": write_to_github,
}

class OntologyAgent(SDKAgent):
    """SDK Agent with ontology integration."""

    def __init__(self, name: str, ontology_path: str, **kwargs):
        self.ontology = OntologyLoader(ontology_path).load()
        self.agent_name = name
        instructions = self._generate_instructions()
        tools = self._discover_tools()
        super().__init__(name=name, instructions=instructions, tools=tools, **kwargs)

    def _generate_instructions(self) -> str:
        """Query ontology for dynamic instructions."""
        base_instructions = f"You are the {self.agent_name} agent. You have access to a shared context to communicate with other agents."
        sparql = f"""
            PREFIX : <http://agent_kit.io/business#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?instructions
            WHERE {{
                ?agent rdfs:label "{self.agent_name}" ;
                       :hasInstructions ?instructions .
            }}
        """
        results = self.ontology.query(sparql)
        for row in results:
            return f"{base_instructions} Your specific instructions are: {str(row.instructions)}"
        return f"{base_instructions} You are a helpful agent."

    def _discover_tools(self) -> list:
        """Discovers tools for the agent by querying the ontology."""
        sparql = f"""
            PREFIX : <http://agent_kit.io/business#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?toolName
            WHERE {{
                ?agent rdfs:label "{self.agent_name}" ;
                       :canPerform ?capability .
                ?capability :requiresTool ?tool .
                ?tool rdfs:label ?toolName .
            }}
        """
        results = self.ontology.query(sparql)

        tools = []
        for row in results:
            tool_name = str(row.toolName)
            if tool_name in TOOL_REGISTRY:
                tools.append(TOOL_REGISTRY[tool_name])

        return tools

    async def act(self, state: dict[str, Any]) -> dict[str, Any]:
        """Override to validate actions against ontology and use shared context."""
        context: SharedContext = state.get("context")
        if context and self.agent_name == "Optimizer":
            forecaster_output = context.get("forecaster_output")
            if forecaster_output:
                state["prompt"] = f"Based on the forecast: {forecaster_output}\n\n{state.get('prompt', '')}"

        action = state.get('action')
        if action and not await self._validate_action(action):
            raise ValueError(f"Action '{action}' is invalid per the ontology")
        return await super().act(state)

    async def _validate_action(self, action: str) -> bool:
        """SPARQL validate action."""
        # This is a placeholder query.
        sparql = f"""
            PREFIX : <http://www.agentkit.io/ontologies/business#>
            ASK {{ ?action a :AllowedAction . FILTER(?action = :{action}) }}
        """
        results = self.ontology.query(sparql)
        return bool(results)
