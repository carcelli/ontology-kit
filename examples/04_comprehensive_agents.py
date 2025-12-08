#!/usr/bin/env python
"""
Example 4: Ontology-Enhanced Agents

Demonstrates ontology-driven agent capabilities:
- Ontology-aware agent instructions and tool discovery
- Semantic memory with ontology-enhanced context
- Intelligent MCP tool filtering based on business rules
- SPARQL-based reasoning for agent behavior
- Knowledge graph integration for contextual understanding
"""

import asyncio
import sys
from pathlib import Path

# Add src to path (for development)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents import Runner

from agent_kit.agents.orchestrator import OntologyOrchestratorAgent
from agent_kit.ontology_extensions import OntologyMemorySession


async def main() -> None:
    print("=" * 80)
    print("Ontology-Kit - Example 4: Comprehensive Agents with SDK Extensions")
    print("=" * 80)
    print()

    # Path to ontology file
    ontology_path = Path(__file__).parent.parent / "assets" / "ontologies" / "core.ttl"

    if not ontology_path.exists():
        print(f"❌ Ontology file not found: {ontology_path}")
        print("Please ensure the ontology file exists.")
        return

    print(f"📚 Using ontology: {ontology_path}")
    print()

    # 1. Initialize Ontology-Enhanced Memory System
    print("🧠 Setting up Ontology-Enhanced Memory System...")
    try:
        memory_session = OntologyMemorySession(
            session_id="comprehensive_demo",
            ontology_path=str(ontology_path),
            db_path=":memory:",  # Use in-memory for demo
        )
        print("   ✅ Ontology-enhanced memory session initialized")
        has_memory = True
    except Exception as e:
        print(f"   ⚠️  Memory system unavailable: {e}")
        print("   ℹ️  Continuing without memory persistence")
        memory_session = None
        has_memory = False
    print()

    # 2. Create Ontology Orchestrator
    print("🎯 Creating Ontology Orchestrator...")
    try:
        orchestrator = OntologyOrchestratorAgent(ontology_path=str(ontology_path))
        print("   ✅ Ontology orchestrator initialized")
        print("   🔄 Agent handoffs: Specialized agent delegation")
        print("   🧬 Ontology integration: SPARQL-based reasoning")
        has_orchestrator = True
    except Exception as e:
        print(f"   ⚠️  Orchestrator unavailable: {e}")
        print("   ℹ️  SDK dependency may not be installed")
        orchestrator = None
        has_orchestrator = False
    print()

    # 4. Demonstrate Complex Multi-Agent Workflow
    print("🚀 Example: Complex Business Analysis Workflow")
    print("-" * 50)

    # Complex goal that would benefit from multiple specialized agents
    complex_goal = """
    Analyze our current business ontology, identify optimization opportunities,
    forecast market trends using available data, and recommend specific
    interventions with implementation plans. Coordinate between forecasting,
    optimization, and analysis agents to provide comprehensive insights.
    """

    print(f"🎯 Complex Goal: {complex_goal.strip()}")
    print()

    if has_orchestrator:
        try:
            # Configure run config based on available components
            run_config = {"workflow_name": "Ontology Business Analysis"}
            if has_memory and memory_session:
                run_config["session"] = memory_session

            # Run with ontology-driven orchestration
            result = await Runner.run(orchestrator, complex_goal, run_config=run_config)

            print("✅ Analysis Complete!")
            print(f"📊 Final Result: {result.final_output[:200]}...")
            print()

            if has_memory and memory_session:
                # Show session memory capabilities
                print("💾 Session Memory Analysis:")
                history_items = await memory_session.get_items(limit=5)
                print(
                    f"   📝 Conversation history: {len(history_items)} items preserved"
                )
                print("   🧬 Ontology context: Integrated with agent reasoning")
                print()

        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            print("Note: Full SDK capabilities require 'pip install openai-agents'")
            print()
    else:
        print("⚠️  Skipping workflow execution - orchestrator not available")
        print("   ℹ️  Install openai-agents package for full functionality")
        print()

    # 4. Demonstrate Ontology Integration Structure
    print("🔧 Ontology Integration Architecture:")
    print("-" * 50)
    print("📚 Ontology-Kit Core:")
    print("   • Knowledge graph management (RDF/OWL)")
    print("   • SPARQL query execution")
    print("   • Vector space embeddings")
    print("   • Business rule validation")
    print()
    print("🧬 Ontology Extensions:")
    print("   • Ontology-enhanced agents with SPARQL instructions")
    print("   • Semantic memory with knowledge graph context")
    print("   • Intelligent MCP tool filtering")
    print("   • SPARQL-based reasoning and validation")
    print()

    # 6. Show Advanced Capabilities Overview
    print("⚡ Advanced Agent Capabilities Unlocked:")
    print("-" * 50)
    capabilities = [
        "🧬 Ontology-driven agent instructions from SPARQL queries",
        "🔄 Multi-agent orchestration with semantic handoffs",
        "🧠 Ontology-enhanced memory with knowledge graph context",
        "🎯 Intelligent MCP tool filtering based on business rules",
        "🔍 SPARQL-based reasoning and validation",
        "📚 Knowledge graph integration for contextual understanding",
        "💡 Semantic tool discovery from ontology relationships",
        "🔧 Extensible architecture for domain-specific agents",
    ]

    for capability in capabilities:
        print(f"   {capability}")
    print()

    print("=" * 80)
    print("✅ Comprehensive Agent Demo Complete!")
    print()
    print("🚀 Ready for Production:")
    print("   • Install core dependencies: pip install -e .")
    print("   • Install SDK for full agent capabilities: pip install openai-agents")
    print("   • Configure ontology files (business.ttl, core.ttl)")
    print("   • Customize agents for your domain-specific needs")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
