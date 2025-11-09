# src/agent_kit/agents/base.py
from abc import ABC, abstractmethod
from typing import NamedTuple

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