# src/agent_kit/agents/orchestrator.py
from typing import Any

from agents import Runner as SDKRunner

from agent_kit.agents.code_writer_agent import CodeWriterAgent
from agent_kit.agents.ontology_agent import OntologyAgent
from agent_kit.agents.planner_agent import PlannerAgent
from agent_kit.shared_context import SharedContext


class BusinessOrchestrator:
    """Orchestrates ontology-driven agents using SDK."""

    def __init__(self, ontology_path: str):
        self.planner = PlannerAgent('Planner', ontology_path)
        self.agents = {
            'forecaster': OntologyAgent('Forecaster', ontology_path),
            'optimizer': OntologyAgent('Optimizer', ontology_path),
            'codewriter': CodeWriterAgent('CodeWriter', ontology_path),
        }

    async def run(self, goal: str) -> Any:
        """Decompose via ontology, orchestrate with SDK Runner."""
        print(f"Received goal: {goal}")

        context = SharedContext()
        context.set("goal", goal)

        # 1. Create a plan using the PlannerAgent
        plan = self.planner.create_plan(goal)

        print("Generated Plan:")
        for i, step in enumerate(plan):
            print(f"  Step {i+1}: Agent '{step['agent']}' with prompt: \"{step['prompt']}\"")

        # 2. Execute the plan
        for step in plan:
            agent_name = step.get('agent')
            prompt = step.get('prompt')

            if agent_name not in self.agents:
                raise ValueError(f"Agent '{agent_name}' not found in orchestrator.")

            agent = self.agents[agent_name]

            print(f"Running {agent_name} agent...")

            # Pass the current context to the agent
            state = {"context": context}
            response = await SDKRunner.run(agent, prompt, state=state)

            # Store the output in the context for the next agent
            context.set(f"{agent_name}_output", response.final_output)

        return context.get_all()
