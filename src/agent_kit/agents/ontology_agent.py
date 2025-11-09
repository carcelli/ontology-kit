# src/agent_kit/agents/ontology_agent.py
from agents import Agent as SDKAgent
from agent_kit.ontology.loader import OntologyLoader
from typing import Any, Dict, List

class OntologyAgent(SDKAgent):
    """SDK Agent with ontology integration."""

    def __init__(self, name: str, ontology_path: str, tools: List = [], **kwargs):
        self.ontology = OntologyLoader(ontology_path).load()
        instructions = self._generate_instructions()  # Ontology-derived
        super().__init__(name=name, instructions=instructions, tools=tools, **kwargs)

    def _generate_instructions(self) -> str:
        """Query ontology for dynamic instructions."""
        # This is a placeholder query. You'll need to adapt it to your ontology.
        sparql = """
            PREFIX : <http://www.agentkit.io/ontologies/business#>
            SELECT ?instructions WHERE {
                ?agent a :Agent ;
                       :hasName ?name ;
                       :hasInstructions ?instructions .
                FILTER(?name = "Forecaster")
            }
        """
        results = self.ontology.query(sparql)
        for row in results:
            return str(row.instructions)
        return "You are a helpful agent."

    async def act(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Override to validate actions against ontology."""
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