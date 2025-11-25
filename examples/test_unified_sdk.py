#!/usr/bin/env python
"""
Quick test script to validate unified SDK integration.

Tests:
1. OpenAI SDK agent creation
2. Ontology adapter wrapping
3. Basic agent execution

Run:
    python examples/test_unified_sdk.py
"""

from __future__ import annotations
from agents import Agent, Runner
from agent_kit.adapters import OntologyAgentAdapter
from agent_kit.ontology.loader import OntologyLoader

import asyncio
import os
import sys
from pathlib import Path

# Add src to path BEFORE importing agent_kit modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Now import after path is set up


async def test_basic_integration() -> None:
    """Test basic integration without tools."""
    print("🧪 Testing Basic Integration...")

    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set")
        return False

    # Create minimal ontology
    ontology = OntologyLoader("assets/ontologies/business.ttl")
    try:
        ontology.load()
    except Exception:
        print("⚠️  Could not load ontology, continuing with empty loader")

    # Create simple agent
    agent = Agent(
        name="TestAgent",
        instructions="You are a helpful assistant. Respond briefly.",
    )

    # Wrap with adapter
    adapter = OntologyAgentAdapter(agent, ontology, "business")
    print(f"✅ Adapter created: domain={adapter.domain}")

    # Execute
    try:
        result = await Runner.run(
            adapter.agent,
            input="Say hello in one sentence",
        )
        print(f"✅ Agent executed: {result.final_output[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        return False


async def main() -> None:
    """Run all tests."""
    print("=" * 60)
    print("Unified SDK Integration Test")
    print("=" * 60)
    print()

    success = await test_basic_integration()

    print()
    print("=" * 60)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Tests failed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
