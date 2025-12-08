"""Unit tests for agents.base module."""

import pytest

from agent_kit.agents.base import BaseAgent


class MockAgent(BaseAgent):
    """Concrete agent for testing."""

    def observe(self, state):
        return state.get("value", 0)

    def plan(self, observation):
        return {"action": "increment", "confidence": 0.9}

    def act(self, plan):
        # Don't set 'success' here to allow multi-step episodes
        return {"next_state": {"value": 1}, "reward": 1.0, "terminal": False}

    def reflect(self, result):
        self.memory.append(result)


def test_agent_initialization() -> None:
    """Test agent creates with ID and config."""
    agent = MockAgent(agent_id="test_agent", config={"param": 123})

    assert agent.agent_id == "test_agent"
    assert agent.config["param"] == 123
    assert len(agent.memory) == 0


def test_agent_observe() -> None:
    """Test observe method."""
    agent = MockAgent(agent_id="test")
    state = {"value": 42}

    observation = agent.observe(state)
    assert observation == 42


def test_agent_plan() -> None:
    """Test plan method."""
    agent = MockAgent(agent_id="test")
    plan = agent.plan(observation=10)

    assert "action" in plan
    assert plan["confidence"] == 0.9


def test_agent_act() -> None:
    """Test act method."""
    agent = MockAgent(agent_id="test")
    plan = {"action": "increment"}

    result = agent.act(plan)
    assert result["terminal"] is False
    assert "reward" in result


def test_agent_reflect() -> None:
    """Test reflect stores in memory."""
    agent = MockAgent(agent_id="test")
    result = {"reward": 1.0, "success": True}

    agent.reflect(result)
    assert len(agent.memory) == 1
    assert agent.memory[0]["reward"] == 1.0


def test_agent_run_episode() -> None:
    """Test full episode execution."""
    agent = MockAgent(agent_id="test")
    initial_state = {"value": 0}

    trajectory = agent.run_episode(initial_state, max_steps=3)

    # Should have 3 steps
    assert len(trajectory) == 3

    # Each step has required fields
    for step in trajectory:
        assert "step" in step
        assert "state" in step
        assert "observation" in step
        assert "plan" in step
        assert "result" in step


def test_agent_get_memory() -> None:
    """Test retrieving memory."""
    agent = MockAgent(agent_id="test")

    # Add memories
    for i in range(5):
        agent.reflect({"step": i})

    # Get all
    all_mem = agent.get_memory()
    assert len(all_mem) == 5

    # Get last 2
    recent = agent.get_memory(k=2)
    assert len(recent) == 2
    assert recent[0]["step"] == 3


def test_agent_reset() -> None:
    """Test reset clears memory."""
    agent = MockAgent(agent_id="test")

    agent.reflect({"data": 1})
    agent.reflect({"data": 2})
    assert len(agent.memory) == 2

    agent.reset()
    assert len(agent.memory) == 0


def test_agent_repr() -> None:
    """Test string representation."""
    agent = MockAgent(agent_id="test_agent")
    agent.reflect({"data": 1})

    repr_str = repr(agent)
    assert "MockAgent" in repr_str
    assert "test_agent" in repr_str
    assert "memory_size=1" in repr_str


def test_abstract_methods_enforced() -> None:
    """Test BaseAgent can't be instantiated directly."""
    with pytest.raises(TypeError):
        BaseAgent(agent_id="test")  # type: ignore
