# src/agent_kit/agents/base.py
"""
Base agent framework for ontology-driven reasoning.

Provides abstract BaseAgent and data structures for the agent lifecycle.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field

class AgentTask(BaseModel):
    """A task for an agent to perform."""
    prompt: str
    parameters: dict[str, Any] = Field(default_factory=dict)

class AgentObservation(BaseModel):
    """An observation made by an agent."""
    content: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)

class AgentPlan(BaseModel):
    """A plan created by an agent."""
    thought: str | None = None
    action: str | None = None
    steps: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class AgentActionResult(BaseModel):
    """The result of an agent's action."""
    output: str | None = None
    summary: str | None = None
    artifacts: dict[str, Any] = Field(default_factory=dict)
    log: list[str] = Field(default_factory=list)

class AgentResult(BaseModel):
    """The final result of an agent's work."""
    result: Any

class BaseAgent(ABC):
    """
    Base class for all agents.
    
    Implements a standard Observe-Plan-Act-Reflect lifecycle.
    """
    
    def __init__(self, name: str = "BaseAgent", description: str = ""):
        self.name = name
        self.description = description
        self.memory: list[str] = []

    def run(self, task: AgentTask) -> AgentResult:
        """
        Execute full observe-plan-act-reflect loop.
        
        Args:
            task: The task to perform.
            
        Returns:
            AgentResult with the final output.
        """
        # 1. Observe
        observation = self.observe(task)

        # 2. Plan
        plan = self.plan(task, observation)

        # 3. Act
        action_result = self.act(task, plan, observation)

        # 4. Reflect (Optional)
        self.reflect(task, action_result)

        # Compile final result
        # Fallback to whatever field is available
        result_text = action_result.output or action_result.summary or str(action_result)
        
        return AgentResult(result=result_text)

    @abstractmethod
    def observe(self, task: AgentTask) -> AgentObservation:
        """
        Gather context and data relevant to the task.
        """
        pass

    @abstractmethod
    def plan(self, task: AgentTask, observation: AgentObservation) -> AgentPlan:
        """
        Decide on a course of action based on observations.
        """
        pass

    @abstractmethod
    def act(self, task: AgentTask, plan: AgentPlan, observation: AgentObservation) -> AgentActionResult:
        """
        Execute the plan.
        """
        pass

    def reflect(self, task: AgentTask, result: AgentActionResult) -> None:
        """
        Review the result and learn from it (optional).
        """
        pass