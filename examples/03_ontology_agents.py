#!/usr/bin/env python
"""
Example 3: Ontology Agents with SDK

Demonstrates proper OpenAI Agents SDK usage:
- OntologyAgent with proper Agent inheritance
- OntologyOrchestratorAgent with handoffs
- Tool usage with @function_tool decorator
- Runner.run() for orchestration
"""

import asyncio
import sys
from pathlib import Path

# Add src to path (for development)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents import Runner

from agent_kit.agents.orchestrator import OntologyOrchestratorAgent


async def main() -> None:
    print("=" * 70)
    print("Agent Kit - Example 3: Ontology Agents with SDK")
    print("=" * 70)
    print()

    # Path to ontology file
    ontology_path = Path(__file__).parent.parent / "assets" / "ontologies" / "core.ttl"

    if not ontology_path.exists():
        print(f"❌ Ontology file not found: {ontology_path}")
        print("Please ensure the ontology file exists.")
        return

    print(f"📚 Using ontology: {ontology_path}")
    print()

    # Create the orchestrator agent with handoffs
    print("🤖 Creating Ontology Orchestrator Agent...")
    orchestrator = OntologyOrchestratorAgent(ontology_path=str(ontology_path))

    print("   - Orchestrator agent initialized")
    print(f"   - Available handoffs: {[h.agent_name for h in orchestrator.handoffs]}")
    print()

    # Example 1: Simple forecasting task
    print("🔮 Example 1: Forecasting Task")
    goal1 = "Analyze sales data and provide a forecast for next quarter"

    print(f"Goal: {goal1}")
    try:
        result1 = await Runner.run(orchestrator, goal1)
        print("✅ Result:")
        print(result1.final_output)
    except Exception as e:
        print(f"❌ Error: {e}")
    print()

    # Example 2: Optimization task
    print("⚡ Example 2: Optimization Task")
    goal2 = "Optimize our marketing budget allocation for maximum ROI"

    print(f"Goal: {goal2}")
    try:
        result2 = await Runner.run(orchestrator, goal2)
        print("✅ Result:")
        print(result2.final_output)
    except Exception as e:
        print(f"❌ Error: {e}")
    print()

    # Example 3: Complex multi-step task
    print("🔄 Example 3: Complex Multi-step Task")
    goal3 = "First forecast customer acquisition costs, then optimize our customer acquisition strategy"

    print(f"Goal: {goal3}")
    try:
        result3 = await Runner.run(orchestrator, goal3)
        print("✅ Result:")
        print(result3.final_output)
    except Exception as e:
        print(f"❌ Error: {e}")
    print()

    print("=" * 70)
    print("✅ Example complete!")
    print()
    print("Key SDK patterns demonstrated:")
    print("  - Agent inheritance from SDK Agent class")
    print("  - Handoff system for delegation")
    print("  - Runner.run() for orchestration")
    print("  - @function_tool decorator for tools")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
