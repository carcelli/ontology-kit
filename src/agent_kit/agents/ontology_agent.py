# src/agent_kit/agents/ontology_agent.py
from __future__ import annotations

from typing import TYPE_CHECKING

from agents import Agent

from agent_kit.ontology.loader import OntologyLoader
from agent_kit.tools.business import optimize, predict
from agent_kit.tools.github_tools import write_to_github

if TYPE_CHECKING:
    pass

# Ontology-driven tools registered with SDK decorators
TOOL_REGISTRY = {
    "Predict Tool": predict,
    "Optimize Tool": optimize,
    "GitHub Tool": write_to_github,
}


class OntologyAgent(Agent):
    """SDK Agent with ontology integration and proper context management."""

    def __init__(self, name: str, ontology_path: str, **kwargs):
        self.ontology = OntologyLoader(ontology_path).load()
        self.agent_name = name
        instructions = self._generate_instructions()
        tools = self._discover_tools()
        super().__init__(name=name, instructions=instructions, tools=tools, **kwargs)

    def _generate_instructions(self) -> str | None:
        """Query ontology for dynamic instructions."""
        base_instructions = (
            f"You are the {self.agent_name} agent with ontology-driven capabilities."
        )

        # Check if we need dynamic instructions based on ontology
        sparql = f"""
            PREFIX : <http://agent_kit.io/business#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?instructions
            WHERE {{
                ?agent rdfs:label "{self.agent_name}" ;
                       :hasInstructions ?instructions .
            }}
        """
        results = list(self.ontology.query(sparql))
        if results:
            return f"{base_instructions} Your specific instructions are: {str(results[0].instructions)}"

        return base_instructions

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
