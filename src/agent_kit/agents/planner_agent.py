# src/agent_kit/agents/planner_agent.py

from __future__ import annotations

from agents import Agent

from agent_kit.ontology.loader import OntologyLoader


class PlannerAgent(Agent):
    """An agent that creates a plan to achieve a high-level goal."""

    def __init__(self, name: str, ontology_path: str, tools: list = None, **kwargs):
        if tools is None:
            tools = []
        self.ontology = OntologyLoader(ontology_path).load()
        instructions = self._generate_instructions()
        super().__init__(name=name, instructions=instructions, tools=tools, **kwargs)

    def _generate_instructions(self) -> str:
        """Generates instructions for the planner agent."""
        return (
            "You are a planner agent. Your role is to take a high-level goal "
            "and break it down into a series of concrete steps for other agents to execute. "
            "You will use your knowledge of the available agents and their capabilities "
            "to construct a plan."
        )

    def create_plan(self, goal: str) -> list[dict]:
        """Creates a plan to achieve the given goal by querying the ontology."""
        sparql = """
            PREFIX : <http://agent_kit.io/business#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?agentName ?capabilityName
            WHERE {
                ?agent a :Agent ;
                       rdfs:label ?agentName ;
                       :canPerform ?capability .
                ?capability rdfs:label ?capabilityName .
            }
        """

        results = self.ontology.query(sparql)

        plan = []
        for row in results:
            agent_name = str(row.agentName).lower()
            capability_name = str(row.capabilityName)
            # This is a simple mapping from capability to a prompt.
            # A more advanced implementation would use an LLM to generate the prompt.
            if "plan" not in agent_name:
                prompt = f"Perform the '{capability_name}' task."
                plan.append({"agent": agent_name, "prompt": prompt})

        # A simple heuristic to order the plan: forecast before optimize.
        plan.sort(key=lambda x: (x["agent"] != "forecaster", x["agent"] != "optimizer"))

        return plan
