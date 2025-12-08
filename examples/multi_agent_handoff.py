#!/usr/bin/env python
"""
Example: Multi-Agent Handoff with OpenAI Agents SDK

Demonstrates how to use OpenAI SDK's handoff system for multi-agent coordination
with ontology-kit's adapter layer.

Architecture:
    BusinessOrchestrator
        ├── ForecastAgent (handles revenue forecasting)
        └── OptimizerAgent (handles business optimization)

The orchestrator routes tasks to specialists based on user intent.
OpenAI SDK handles the handoff logic automatically.

Prerequisites:
    - Set OPENAI_API_KEY environment variable
    - Install dependencies: pip install openai-agents

Run:
    python examples/multi_agent_handoff.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents import Agent, Runner

from agent_kit.adapters import OntologyAgentAdapter, OntologyOutputGuardrail
from agent_kit.ontology.loader import OntologyLoader
from agent_kit.tools.business import optimize, predict
from agent_kit.tools.ontology import query_ontology


def create_forecast_agent(ontology: OntologyLoader) -> OntologyAgentAdapter:
    """Create the ForecastAgent specialist."""
    agent = Agent(
        name="ForecastAgent",
        instructions="""You are a revenue forecasting specialist.

Your responsibilities:
1. Generate revenue forecasts using historical data
2. Provide confidence intervals for predictions
3. Explain the methodology used

When forecasting:
- Use the predict tool to generate forecasts
- Query the ontology to understand business context
- Provide actionable insights based on the forecast

Always respond with:
- Forecast values for the requested period
- Confidence level (high/medium/low)
- Key factors affecting the forecast
""",
        tools=[predict, query_ontology],
    )

    return OntologyAgentAdapter(agent, ontology, "business")


def create_optimizer_agent(ontology: OntologyLoader) -> OntologyAgentAdapter:
    """Create the OptimizerAgent specialist."""
    agent = Agent(
        name="OptimizerAgent",
        instructions="""You are a business optimization specialist.

Your responsibilities:
1. Identify leverage points to improve business metrics
2. Recommend interventions with expected impact
3. Assess risk and cost of recommendations

When optimizing:
- Use the optimize tool to analyze improvement opportunities
- Query the ontology for business relationships
- Provide ranked recommendations

Always respond with:
- Top 3 recommended interventions
- Expected impact percentage
- Implementation considerations
""",
        tools=[optimize, query_ontology],
    )

    return OntologyAgentAdapter(agent, ontology, "business")


def create_orchestrator(
    forecast_agent: OntologyAgentAdapter,
    optimizer_agent: OntologyAgentAdapter,
    ontology: OntologyLoader,
) -> OntologyAgentAdapter:
    """Create the BusinessOrchestrator with handoffs."""
    orchestrator = Agent(
        name="BusinessOrchestrator",
        instructions="""You are a business intelligence orchestrator.

Your role is to understand user requests and route them to the appropriate specialist:
- For forecasting, predictions, or trend analysis → Transfer to ForecastAgent
- For optimization, improvements, or recommendations → Transfer to OptimizerAgent
- For complex requests requiring both → Coordinate between both agents

When routing:
1. Analyze the user's request to understand intent
2. Transfer to the appropriate specialist
3. If the request needs multiple specialists, handle sequentially

You can also handle simple queries directly if they don't require specialized analysis.
""",
        # Handoffs to specialist agents - OpenAI SDK handles the transfer
        handoffs=[forecast_agent.agent, optimizer_agent.agent],
    )

    return OntologyAgentAdapter(orchestrator, ontology, "business")


async def run_single_task(
    orchestrator: OntologyAgentAdapter,
    task: str,
) -> str:
    """Run a single task through the orchestrator."""
    print(f"\n📝 Task: {task}")
    print("-" * 60)

    try:
        result = await Runner.run(orchestrator.agent, input=task)
        output = result.final_output
        print(f"\n✅ Result:\n{output}")
        return output
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return ""


async def main() -> None:
    """Run multi-agent handoff example."""
    print("=" * 80)
    print("Multi-Agent Handoff Example")
    print("=" * 80)
    print()

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='your-key'")
        return

    print(f"✅ OpenAI API key found: {api_key[:10]}...")
    print()

    # Setup ontology
    print("📚 Loading ontology...")
    ontology_path = (
        Path(__file__).parent.parent / "assets" / "ontologies" / "business.ttl"
    )
    ontology = OntologyLoader(str(ontology_path))

    if ontology_path.exists():
        ontology.load()
        print("✅ Ontology loaded")
    else:
        print(f"⚠️  Ontology not found at {ontology_path}, using empty loader")
    print()

    # Create specialist agents
    print("🤖 Creating specialist agents...")
    forecast_agent = create_forecast_agent(ontology)
    print(f"   - {forecast_agent.agent.name}: Revenue forecasting")

    optimizer_agent = create_optimizer_agent(ontology)
    print(f"   - {optimizer_agent.agent.name}: Business optimization")
    print()

    # Create orchestrator with handoffs
    print("🎭 Creating orchestrator with handoffs...")
    orchestrator = create_orchestrator(forecast_agent, optimizer_agent, ontology)
    print(f"   - {orchestrator.agent.name}: Routes to specialists")
    print()

    # Add guardrails
    print("🛡️  Adding output guardrails...")
    orchestrator.agent.output_guardrails = [OntologyOutputGuardrail("business")]
    print("✅ Guardrails added")
    print()

    # Run example tasks
    print("=" * 80)
    print("Running Example Tasks")
    print("=" * 80)

    tasks = [
        # Forecasting task - should route to ForecastAgent
        "What's the revenue forecast for the next 30 days?",
        # Optimization task - should route to OptimizerAgent
        "How can we improve our revenue by 10%?",
        # Combined task - may need coordination
        "Forecast revenue for Q1 and suggest optimizations to reach our target.",
    ]

    for task in tasks:
        await run_single_task(orchestrator, task)
        print()
        print("=" * 80)

    print()
    print("✅ Multi-agent handoff example completed!")
    print()
    print("Key takeaways:")
    print("  1. OpenAI SDK handles handoff logic automatically")
    print("  2. Ontology adapters enrich each agent with domain context")
    print("  3. Guardrails validate outputs against Pydantic schemas")
    print("  4. Tools are filtered by domain allowlist")


if __name__ == "__main__":
    asyncio.run(main())
