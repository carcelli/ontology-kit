# src/agent_kit/agents/orchestrator.py
from agents import Runner as SDKRunner
from agent_kit.agents.ontology_agent import OntologyAgent
from agent_kit.tools.business import predict, optimize
from typing import Any

class BusinessOrchestrator:
    """Orchestrates ontology-driven agents using SDK."""

    def __init__(self, ontology_path: str):
        self.agents = {
            'forecaster': OntologyAgent('Forecaster', ontology_path, tools=[predict]),
            'optimizer': OntologyAgent('Optimizer', ontology_path, tools=[optimize]),
        }

    async def run(self, goal: str) -> Any:
        """Decompose via ontology, orchestrate with SDK Runner."""
        # Placeholder for ontology-driven decomposition
        # In a real scenario, you would query the ontology to determine the sequence of agents.
        print(f"Received goal: {goal}")
        print("Running Forecaster agent...")
        response = await SDKRunner.run(self.agents['forecaster'], goal)

        if 'optimize' in response.final_output.lower():  # Handoff trigger
            print("Handoff to Optimizer agent...")
            response = await SDKRunner.run(self.agents['optimizer'], response.final_output)

        return response.final_output