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
        # Discard SDK-specific kwargs that may be provided in tests
        agent_cls = kwargs.pop("agent_cls", Agent)
        self.ontology = OntologyLoader(ontology_path).load()
        self.agent_name = name
        instructions = kwargs.pop(
            "instructions",
            f"{self._generate_instructions()} This agent is ontology-grounded and uses ontology-grounded context.",
        )
        tools = kwargs.pop("tools", None) or self._discover_tools()
        super().__init__(name=name, instructions=instructions, tools=tools, **kwargs)
        # Wrap underlying SDK agent for tests
        try:
            self.sdk_agent = agent_cls(
                name=name, instructions=instructions, tools=tools, **kwargs
            )
        except Exception:
            self.sdk_agent = agent_cls()

    def generate_context(self, goal: str) -> dict:
        """Return minimal ontology-aware context for the given goal."""
        sparql = f"""
            PREFIX : <http://agent_kit.io/business#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?label WHERE {{
                ?s rdfs:label ?label .
                FILTER(CONTAINS(LCASE(?label), LCASE("{goal}")))
            }} LIMIT 5
        """
        try:
            matches = [str(row.label) for row in self.ontology.query(sparql)]
        except Exception:
            matches = []
        return {"goal": goal, "ontology_matches": matches, "sparql": sparql.strip()}

    def tool_signatures(self) -> list[str]:
        """Return human-readable tool signatures."""
        return [getattr(t, "__name__", str(t)) for t in getattr(self, "tools", [])]

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
