# tests/unit/test_orchestrator.py
from unittest.mock import AsyncMock, MagicMock

import pytest

from agent_kit.agents.orchestrator import BusinessOrchestrator


@pytest.mark.asyncio
async def test_orchestrator_run():
    """
    Test the BusinessOrchestrator's run method, mocking the SDK's Runner.
    """
    # Mock the SDK Runner
    mock_runner = AsyncMock()
    mock_runner.run.side_effect = [
        MagicMock(final_output="Forecast complete. Now optimize."),
        MagicMock(final_output="Optimization complete."),
    ]

    # Patch the SDK Runner in the orchestrator's module
    import agent_kit.agents.orchestrator

    agent_kit.agents.orchestrator.SDKRunner = mock_runner

    # Instantiate the orchestrator
    orchestrator = BusinessOrchestrator("assets/ontologies/business.ttl")

    # Run the orchestrator
    result = await orchestrator.run("Optimize revenue for Sunshine Bakery")

    # Assertions
    assert mock_runner.run.call_count == 2
    assert result == "Optimization complete."

    # Check that the correct agents were called
    forecaster_agent = orchestrator.agents["forecaster"]
    optimizer_agent = orchestrator.agents["optimizer"]

    # Get the agent from the call
    first_call_agent = mock_runner.run.call_args_list[0][0][0]
    second_call_agent = mock_runner.run.call_args_list[1][0][0]

    assert first_call_agent.name == forecaster_agent.name
    assert second_call_agent.name == optimizer_agent.name
