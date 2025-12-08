# src/agent_kit/agents/github_agent.py

from agents import Agent as SDKAgent

from agent_kit.ontology.loader import OntologyLoader
from agent_kit.tools.github_tools import write_to_github

# A simple registry to map tool names to functions
TOOL_REGISTRY = {
    "GitHub Tool": write_to_github,
}


class GitHubAgent(SDKAgent):
    """SDK Agent for interacting with GitHub."""

    def __init__(self, name: str, ontology_path: str, **kwargs):
        self.ontology = OntologyLoader(ontology_path).load()
        self.agent_name = name
        instructions = self._generate_instructions()
        tools = self._discover_tools()
        super().__init__(name=name, instructions=instructions, tools=tools, **kwargs)

    def _generate_instructions(self) -> str:
        """Query ontology for dynamic instructions."""
        return f"You are the {self.agent_name} agent. Your role is to write code to GitHub based on the user's request."

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
