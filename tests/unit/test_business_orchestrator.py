"""Unit tests for the BusinessOrchestrator."""

from pathlib import Path
from typing import Any

import pytest

from agent_kit.agents.orchestrator import BusinessOrchestrator


class StubSDKAgent:
    """Stub SDK Agent used for orchestration tests."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.name = kwargs.get('name', 'stub')

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return self.name


class StubRunner:
    """Minimal runner conforming to the orchestrator contract."""

    def __init__(self) -> None:
        self.calls = []

    async def run(self, agent: Any, input: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls.append(agent)
        goal = input.get('goal', '')
        return {'final_output': f"{agent} → {goal}"}


class StubHandoff:
    """Stub handoff capturing constructor arguments."""

    def __init__(self, source: Any, target: Any, reason: str, state: Any) -> None:
        self.source = source
        self.target = target
        self.reason = reason
        self.state = state


def _orchestrator() -> BusinessOrchestrator:
    ontology_path = Path('assets/ontologies/business.ttl')
    configs = {
        'forecaster': {'agent_cls': StubSDKAgent},
        'optimizer': {'agent_cls': StubSDKAgent},
    }
    return BusinessOrchestrator(str(ontology_path), agent_configs=configs, handoff_cls=StubHandoff)


@pytest.mark.asyncio
async def test_orchestrator_routes_and_creates_handoff() -> None:
    """The orchestrator should run two agents and capture a handoff."""
    orchestrator = _orchestrator()
    runner = StubRunner()
    goal = 'Optimize Q4 revenue forecast'

    result = await orchestrator.run(goal, runner=runner)

    assert result.route == ['forecaster', 'optimizer']
    assert 'forecaster' in result.agent_outputs
    assert result.handoffs
    handoff = result.handoffs[0]
    assert handoff.source == 'forecaster'
    assert isinstance(handoff.sdk_object, StubHandoff)


@pytest.mark.asyncio
async def test_orchestrator_with_single_agent_when_optimize_missing() -> None:
    """Fallback route should only run the first registered agent."""
    ontology_path = Path('assets/ontologies/business.ttl')
    configs = {'forecaster': {'agent_cls': StubSDKAgent}}
    orchestrator = BusinessOrchestrator(str(ontology_path), agent_configs=configs)
    runner = StubRunner()
    result = await orchestrator.run('Forecast next quarter', runner=runner)

    assert result.route == ['forecaster']
    assert not result.handoffs
