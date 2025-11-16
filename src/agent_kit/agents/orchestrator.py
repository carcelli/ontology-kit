"""Ontology-aware business orchestrator using SDK handoffs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agents import Agent, Runner, handoff

from agent_kit.agents.ontology_agent import OntologyAgent
from agent_kit.agents.planner_agent import PlannerAgent

if TYPE_CHECKING:
    from agents.run_context import RunContextWrapper


class OntologyOrchestratorAgent(Agent):
    """Ontology-aware orchestrator agent that uses handoffs to delegate tasks."""

    def __init__(self, ontology_path: str, **kwargs):
        self.ontology_path = ontology_path
        self.planner = PlannerAgent('Planner', ontology_path)

        # Create the specialist agents that this orchestrator can hand off to
        self.forecaster = OntologyAgent(
            name="Forecaster",
            ontology_path=ontology_path,
            handoff_description="Specializes in forecasting and prediction tasks"
        )
        self.optimizer = OntologyAgent(
            name="Optimizer",
            ontology_path=ontology_path,
            handoff_description="Specializes in optimization and improvement tasks"
        )

        # Set up handoffs to specialist agents
        handoffs = [
            handoff(self.forecaster),
            handoff(self.optimizer),
        ]

        instructions = self._generate_orchestrator_instructions()

        super().__init__(
            name="Orchestrator",
            instructions=instructions,
            handoffs=handoffs,
            **kwargs
        )

    def _generate_orchestrator_instructions(self) -> str:
        """Generate instructions for the orchestrator based on ontology."""
        return """You are an ontology-aware orchestrator agent that coordinates specialized agents to accomplish complex tasks.

Based on the user's goal, analyze what needs to be done and delegate to the appropriate specialist agents:
- Forecaster: For prediction, forecasting, and data analysis tasks
- Optimizer: For optimization, improvement, and strategic planning tasks

Use handoffs to delegate specific subtasks to these specialists, then synthesize their results into a comprehensive response.

Always provide clear reasoning for which agent you're delegating to and why."""


async def run_ontology_orchestration(goal: str, ontology_path: str) -> str:
    """
    Convenience function to run ontology-aware orchestration.

    Args:
        goal: The business objective to accomplish
        ontology_path: Path to the ontology file

    Returns:
        Final result from the orchestrated agents
    """
    orchestrator = OntologyOrchestratorAgent(ontology_path=ontology_path)
    result = await Runner.run(orchestrator, goal)
    return result.final_output
