#!/usr/bin/env python
"""
Example: Unified SDK Integration (ADK + OpenAI Agents SDK)

Demonstrates how to use both ADK infrastructure and OpenAI Agents SDK
with ontology-kit's adapter layer.

Prerequisites:
    - Set OPENAI_API_KEY environment variable
    - Install dependencies: pip install openai-agents

Run:
    python examples/unified_sdk_integration.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from agents import Agent, Runner

from agent_kit.adapters import OntologyAgentAdapter, OntologyOutputGuardrail
from agent_kit.ontology.loader import OntologyLoader
from agent_kit.tools.business import optimize, predict
from agent_kit.tools.ontology import query_ontology

# Add src to path BEFORE importing agent_kit modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Now import after path is set up


async def main() -> None:
    """Run unified SDK integration example."""
    print("=" * 80)
    print("Unified SDK Integration Example")
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
    ontology_path = Path(__file__).parent.parent / \
        "assets" / "ontologies" / "business.ttl"
    if not ontology_path.exists():
        print(f"⚠️  Warning: Ontology file not found: {ontology_path}")
        print("   Creating minimal ontology loader...")
        ontology = OntologyLoader(str(ontology_path))
    else:
        ontology = OntologyLoader(str(ontology_path))
        ontology.load()
    print("✅ Ontology loaded")
    print()

    # Create OpenAI SDK agent
    print("🤖 Creating OpenAI SDK agent...")
    agent = Agent(
        name="BusinessForecastAgent",
        instructions="""
        You are a business forecasting agent that helps small businesses predict revenue.
        
        Your capabilities:
        - Forecast revenue using historical data
        - Query the ontology to understand business entities
        - Optimize business processes using leverage analysis
        
        When forecasting:
        1. Use the predict tool to generate forecasts
        2. Query the ontology to understand business context
        3. Provide actionable insights based on the forecast
        """,
        tools=[predict, optimize, query_ontology],
    )
    print("✅ Agent created")
    print()

    # Wrap with ontology adapter
    print("🔗 Wrapping agent with ontology adapter...")
    adapter = OntologyAgentAdapter(agent, ontology, "business")
    print("✅ Adapter created")
    print(f"   Domain: {adapter.domain}")
    print(f"   Tools: {len(adapter.agent.tools)}")
    print()

    # Add guardrails
    print("🛡️  Adding output guardrails...")
    adapter.agent.output_guardrails = [
        OntologyOutputGuardrail("business")
    ]
    print("✅ Guardrails added")
    print()

    # Execute agent
    print("🚀 Executing agent...")
    print("-" * 80)
    try:
        result = await Runner.run(
            adapter.agent,
            input="Forecast revenue for the next 30 days and suggest one optimization",
        )
        print("-" * 80)
        print()
        print("✅ Agent execution completed")
        print()
        print("📊 Result:")
        print(result.final_output)
        print()

        # Show ontology context if available
        if hasattr(adapter.agent, "_ontology_queries"):
            queries = adapter.agent._ontology_queries
            if queries:
                print("🔍 SPARQL Queries Executed:")
                for i, query in enumerate(queries, 1):
                    print(f"   {i}. {query[:100]}...")
                print()

    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return

    print("=" * 80)
    print("✅ Example completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
