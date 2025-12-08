# src/agent_kit/agents/base.py
"""
Base agent framework with flexible observe-plan-act-reflect lifecycle.

Design goals:
- Minimal dependencies for unit tests (works offline and without OpenAI installed)
- Backward compatibility with SDK-style AgentTask objects
- Simple RL-style helpers (run_episode, memory utilities)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

# Optional OpenAI + retry dependencies (patched in tests)
try:  # pragma: no cover - environment dependent
    from openai import OpenAI  # type: ignore[import-not-found]

    OPENAI_AVAILABLE = True
except Exception:  # pragma: no cover
    OPENAI_AVAILABLE = False
    OpenAI = None  # type: ignore[assignment]

try:  # pragma: no cover - environment dependent
    from tenacity import retry  # type: ignore[import-not-found]

    TENACITY_AVAILABLE = True
except Exception:  # pragma: no cover
    TENACITY_AVAILABLE = False

    def retry(fn: Callable | None = None, *args: Any, **kwargs: Any):  # type: ignore[misc]
        """Lightweight passthrough when tenacity is unavailable."""

        def decorator(func: Callable) -> Callable:
            return func

        if fn is None:
            return decorator
        return fn


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

    model_config = {"extra": "allow"}
    result: Any


class BaseAgent:
    """
    Base class for all agents.

    Implements a standard Observe-Plan-Act-Reflect lifecycle with
    additional helpers for simple episodic execution.
    """

    def __init__(
        self,
        name: str = "BaseAgent",
        description: str = "",
        agent_id: str | None = None,
        config: dict[str, Any] | None = None,
        **_: Any,
    ):
        if self.__class__ is BaseAgent:
            raise TypeError("BaseAgent is abstract and must be subclassed")
        self.name = name
        self.agent_id = agent_id or name
        self.description = description
        self.config = config or {}
        self.memory: list[Any] = []

    # ------------------------------------------------------------------
    # High-level OPA loop (used by GrokAgent and orchestrator agents)
    # ------------------------------------------------------------------
    def run(self, task: AgentTask) -> AgentResult:
        """
        Execute full observe-plan-act-reflect loop.
        """
        observation = self.observe(task)
        plan = self.plan(task, observation)
        action_result = self.act(task, plan, observation)
        self.reflect(task, action_result)

        result_text = (
            action_result.output or action_result.summary or str(action_result)
        )

        return AgentResult(result=result_text)

    def observe(
        self, task: Any, *args: Any, **kwargs: Any
    ) -> Any:  # pragma: no cover - to be overridden
        """Gather context and data relevant to the task."""
        raise NotImplementedError

    def plan(
        self, task: Any, observation: Any | None = None, *args: Any, **kwargs: Any
    ) -> Any:  # pragma: no cover
        """Decide on a course of action based on observations."""
        raise NotImplementedError

    def act(
        self,
        task: Any,
        plan: Any | None = None,
        observation: Any | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:  # pragma: no cover
        """Execute the plan."""
        raise NotImplementedError

    def reflect(self, task: Any, result: Any | None = None) -> None:
        """Review the result and learn from it (optional)."""
        res = result if result is not None else task
        if isinstance(res, AgentActionResult):
            if res.summary:
                self.memory.append(res.summary)
            elif res.output:
                self.memory.append(str(res.output))
        elif res is not None:
            self.memory.append(res)

    # ------------------------------------------------------------------
    # RL-style helpers used in unit tests
    # ------------------------------------------------------------------
    def run_episode(
        self, initial_state: Any, max_steps: int = 10
    ) -> list[dict[str, Any]]:
        """
        Run observe-plan-act-reflect loop for a fixed number of steps.
        """
        trajectory: list[dict[str, Any]] = []
        state = initial_state

        for step in range(max_steps):
            observation = self.observe(state)
            plan = self.plan(observation)
            result = self.act(plan)
            self.reflect(result)

            trajectory.append(
                {
                    "step": step,
                    "state": state,
                    "observation": observation,
                    "plan": plan,
                    "result": result,
                }
            )

            if isinstance(result, dict) and result.get("terminal"):
                break

            state = (
                result.get("next_state", state) if isinstance(result, dict) else state
            )

        return trajectory

    def get_memory(self, k: int | None = None) -> list[Any]:
        """Return memory entries (optionally last k)."""
        if k is None or k >= len(self.memory):
            return list(self.memory)
        return self.memory[-k:]

    def reset(self) -> None:
        """Clear memory."""
        self.memory.clear()

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"{self.__class__.__name__}(id={self.agent_id}, memory_size={len(self.memory)})"
