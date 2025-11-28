#!/usr/bin/env python
"""
Agent Factory Demo

Demonstrates how AgentFactory creates domain-specific orchestrators
with all dependencies automatically injected.

Run:
    python examples/agent_factory_demo.py
"""

from __future__ import annotations
from agent_kit.domains.registry import get_global_registry
from agent_kit.agents.base import AgentTask
from agent_kit.factories import AgentFactory

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def demo_factory_basics():
    """Demonstrate basic factory usage."""
    print("=" * 80)
    print("Agent Factory Demo: Basic Usage")
    print("=" * 80)
    print()

    # Create factory
    print("1️⃣  Creating AgentFactory...")
    factory = AgentFactory()
    print("   ✅ Factory created")
    print()

    # List available domains
    print("2️⃣  Available domains:")
    registry = get_global_registry()
    domains = registry.list_domains()
    for domain in domains:
        cfg = registry.get(domain)
        print(
            f"   • {domain}: {len(cfg.default_agents)} agents, {len(cfg.allowed_tools)} tools")
    print()

    # Create orchestrator
    print("3️⃣  Creating business orchestrator...")
    try:
        orchestrator = factory.create_orchestrator("business")
        print(f"   ✅ Orchestrator created: {orchestrator.domain}")
        print(f"   ✅ Specialists: {len(orchestrator.specialists)}")
        print(f"   ✅ Tools: {len(orchestrator.tools)}")
        print(f"   ✅ Risk policies: {len(orchestrator.risk_policies)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    print()

    # List available agents
    print("4️⃣  Available agents in registry:")
    for agent_name in factory.AGENT_REGISTRY.keys():
        print(f"   • {agent_name}")
    print()


def demo_single_agent():
    """Demonstrate creating a single agent."""
    print("=" * 80)
    print("Agent Factory Demo: Single Agent Creation")
    print("=" * 80)
    print()

    factory = AgentFactory()

    print("Creating ForecastAgent...")
    try:
        agent = factory.create_agent("ForecastAgent", domain="business")
        print(f"   ✅ Agent created: {agent.name}")
        print(f"   ✅ Type: {type(agent).__name__}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()


def demo_custom_config():
    """Demonstrate custom configuration."""
    print("=" * 80)
    print("Agent Factory Demo: Custom Configuration")
    print("=" * 80)
    print()

    from agent_kit.agents.grok_agent import GrokConfig

    print("Creating factory with custom Grok config...")
    grok_config = GrokConfig(
        api_key=os.getenv("XAI_API_KEY", "test-key"),
        temperature=0.5,
        max_tokens=2048,
    )

    factory = AgentFactory(grok_api_key=os.getenv("XAI_API_KEY"))
    print("   ✅ Factory created with custom config")
    print()


def demo_tool_loading():
    """Demonstrate dynamic tool loading."""
    print("=" * 80)
    print("Agent Factory Demo: Dynamic Tool Loading")
    print("=" * 80)
    print()

    factory = AgentFactory()
    registry = get_global_registry()
    cfg = registry.get("business")

    print(f"Loading tools for domain 'business'...")
    print(f"   Tool paths: {cfg.allowed_tools[:3]}...")  # Show first 3

    tools = factory._load_tools(cfg.allowed_tools)
    print(f"   ✅ Loaded {len(tools)} tools")
    print(f"   Tool names: {[t.__name__ for t in tools[:3]]}")
    print()


def demo_ontology_loading():
    """Demonstrate ontology loading."""
    print("=" * 80)
    print("Agent Factory Demo: Ontology Loading")
    print("=" * 80)
    print()

    factory = AgentFactory()
    registry = get_global_registry()
    cfg = registry.get("business")

    print(f"Loading ontology for domain 'business'...")
    print(f"   IRI: {cfg.ontology_iri}")

    ontology = factory._load_ontology(cfg.ontology_iri)
    print(f"   ✅ Ontology loaded: {ontology.path}")
    print(
        f"   ✅ Graph size: {len(ontology.graph) if hasattr(ontology, 'graph') else 'N/A'} triples")
    print()


def main():
    """Run all demos."""
    import os

    # Check if API key is set (optional for demos)
    if not os.getenv("XAI_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: No API keys set. Some demos may fail.")
        print("   Set XAI_API_KEY or OPENAI_API_KEY environment variable")
        print()

    try:
        demo_factory_basics()
        demo_single_agent()
        demo_tool_loading()
        demo_ontology_loading()
        # demo_custom_config()  # Requires API key

        print("=" * 80)
        print("✅ All demos completed!")
        print("=" * 80)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import os
    main()
