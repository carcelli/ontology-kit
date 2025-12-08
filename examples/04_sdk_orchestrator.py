# examples/04_sdk_orchestrator.py
import asyncio
from unittest.mock import AsyncMock, MagicMock

from agent_kit.agents.orchestrator import BusinessOrchestrator


async def main():
    # Mock the SDK Runner
    mock_runner = AsyncMock()
    mock_runner.run.side_effect = [
        MagicMock(final_output="Forecast complete. Now optimize."),
        MagicMock(final_output="Optimization complete."),
    ]

    # Patch the SDK Runner in the orchestrator's module
    import agent_kit.agents.orchestrator

    agent_kit.agents.orchestrator.SDKRunner = mock_runner

    orch = BusinessOrchestrator("assets/ontologies/business.ttl")
    result = await orch.run("Optimize revenue for Sunshine Bakery")
    print("Orchestrator finished with result:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
