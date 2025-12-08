#!/usr/bin/env python
"""
Example 4: Orchestrated Multi-Agent Workflow

Demonstrates:
- OntologyOrchestrator coordinating multiple agents
- Task routing via ontology queries
- Agent handoffs for complex business tasks
- Ontology-grounded reasoning for small business optimization
"""

import sys
from pathlib import Path

# Add src to path (for development)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_kit.agents.base import AgentTask
from agent_kit.agents.business_agents import ForecastAgent, OptimizerAgent
from agent_kit.agents.orchestrator import OntologyOrchestrator


def main() -> None:
    print("=" * 70)
    print("Agent Kit - Example 4: Orchestrated Multi-Agent Workflow")
    print("=" * 70)
    print()

    # ========================================================================
    # Setup: Initialize orchestrator with business ontology
    # ========================================================================
    print("🔧 Initializing Ontology Orchestrator...")
    ontology_path = (
        Path(__file__).parent.parent / "assets" / "ontologies" / "business.ttl"
    )

    orchestrator = OntologyOrchestrator(str(ontology_path))

    # Register business agents
    orchestrator.register_agent("forecaster", ForecastAgent())
    orchestrator.register_agent("optimizer", OptimizerAgent())

    print(orchestrator.describe_routing())
    print()

    # ========================================================================
    # Task 1: Simple forecast (single agent)
    # ========================================================================
    print("📈 Task 1: Revenue Forecast for Sunshine Bakery")
    print("-" * 70)

    task1 = AgentTask(
        description="Forecast Q1-Q3 revenue for Sunshine Bakery",
        parameters={"business_id": "biz_001", "horizon": 3},
    )

    result1 = orchestrator.run(task1, max_handoffs=3)

    print(f"Agent: {result1.task.description}")
    print(f"Result: {result1.action_result.summary}")
    print(f"Artifacts: {result1.action_result.artifacts}")
    print()
    print("Reflections:")
    for reflection in result1.reflections:
        print(f"  {reflection}")
    print()

    # ========================================================================
    # Task 2: Optimization (handoff trigger)
    # ========================================================================
    print("🎯 Task 2: Revenue Optimization (Multi-Agent Handoff)")
    print("-" * 70)

    task2 = AgentTask(
        description="Optimize Q4 revenue for Sunshine Bakery",
        parameters={"business_id": "biz_001", "quarter": "Q4"},
    )

    result2 = orchestrator.run(task2, max_handoffs=3)

    print(f"Agent: {result2.task.description}")
    print(f"Result: {result2.action_result.summary}")
    print(f"Artifacts: {result2.action_result.artifacts}")
    print()
    print("Reflections:")
    for reflection in result2.reflections:
        print(f"  {reflection}")
    print()

    # ========================================================================
    # Handoff History
    # ========================================================================
    print("🔗 Orchestration Handoff History:")
    print("-" * 70)

    handoffs = orchestrator.get_handoff_history()

    if handoffs:
        for i, handoff in enumerate(handoffs, 1):
            print(f"{i}. {handoff.from_agent} → {handoff.to_agent}")
            print(f"   Reason: {handoff.reason}")
            print(f"   Intermediate: {handoff.intermediate_result.get('summary', 'N/A')}")
            print()
    else:
        print("(No handoffs occurred)")
    print()

    # ========================================================================
    # Business Impact
    # ========================================================================
    print("💰 Business Impact Analysis:")
    print("-" * 70)

    if "expected_uplift" in result2.action_result.artifacts:
        uplift = result2.action_result.artifacts["expected_uplift"]
        roi = result2.action_result.artifacts["roi"]
        cost = result2.action_result.artifacts["cost"]

        print(f"Expected Revenue Uplift: ${uplift:.0f}K")
        print(f"Investment Required: ${cost}K")
        print(f"Return on Investment: {roi:.2f}x")
        print(f"Net Gain: ${uplift - cost:.0f}K")
    print()

    print("=" * 70)
    print("✅ Example complete!")
    print()
    print("Key Takeaways:")
    print("  - Orchestrator used ontology to route 'optimize' → OptimizerAgent")
    print("  - ForecastAgent identified optimization trigger → automatic handoff")
    print("  - Ontology-grounded reasoning reduced hallucinations")
    print("  - Multi-agent coordination via structured task/result dataclasses")
    print()
    print("Next steps:")
    print("  - Add more agents (ClientSegmenter, InsightGenerator)")
    print("  - Enhance ontology with handoff rules (core:handsOffTo relation)")
    print("  - Integrate real ML models (ARIMA, Prophet) in ForecastAgent")
    print("  - Add async execution for parallel agent workflows")
    print()
    print("🚀 Advanced: Grok Agent Integration")
    print("  - Replace business agents with GrokAgent for LLM-powered reasoning")
    print("  - See examples/grok_agent_demo.py for full implementation")
    print("  - Set XAI_API_KEY to enable: export XAI_API_KEY='your-key'")
    print("=" * 70)


def demo_grok_integration():
    """
    Optional: Demonstrate Grok-powered agents in orchestration.
    
    This is an advanced example showing how to replace traditional agents
    with GrokAgent for LLM-powered reasoning. Requires XAI_API_KEY.
    
    Run this with: python examples/04_orchestrated_agents.py --grok
    """
    import os

    # Check if Grok is available
    if not os.getenv("XAI_API_KEY"):
        print("\n⚠️  XAI_API_KEY not set. Skipping Grok integration demo.")
        print("   To enable: export XAI_API_KEY='your-key'")
        print("   Get key from: https://x.ai/api")
        return

    try:
        from agent_kit.agents import GrokAgent, GrokConfig
        from agent_kit.tools.ml_training import ML_TOOL_REGISTRY
    except ImportError as e:
        print(f"\n⚠️  Grok dependencies not installed: {e}")
        print("   Install with: pip install openai>=1.0.0 tenacity>=8.2.0")
        return

    print("\n" + "=" * 70)
    print("  🚀 Grok-Powered Agent Orchestration")
    print("=" * 70)
    print()

    # Load ontology
    ontology_path = Path(__file__).parent.parent / "assets" / "ontologies" / "business.ttl"
    from agent_kit.ontology.loader import OntologyLoader
    loader = OntologyLoader(str(ontology_path))
    ontology_graph = loader.load()

    # Wrap for agent compatibility
    class OntologyWrapper:
        def __init__(self, graph):
            self.g = graph
        def query(self, sparql):
            return self.g.query(sparql)

    ontology = OntologyWrapper(ontology_graph)

    # Configure Grok
    config = GrokConfig(
        api_key=os.getenv("XAI_API_KEY"),
        model="grok-beta",
        temperature=0.5,
        seed=42
    )

    # Create tool registry
    tool_registry = {
        tool_name: tool_entry['function']
        for tool_name, tool_entry in ML_TOOL_REGISTRY.items()
    }

    # Create Grok-powered forecaster
    grok_forecaster = GrokAgent(
        config=config,
        ontology=ontology,
        tool_registry=tool_registry,
        system_prompt=(
            "You are a revenue forecasting specialist for small businesses. "
            "Use ontology data to ground predictions in real business metrics. "
            "When appropriate, invoke ML tools like train_model or analyze_leverage."
        )
    )

    print("✓ Grok-powered ForecastAgent initialized")
    print(f"  Model: {config.model}")
    print(f"  Tools: {len(tool_registry)} available")
    print()

    # Run a forecast task
    print("Running Grok-powered forecast task...")
    task = AgentTask(
        prompt="Forecast Q1-Q3 revenue for Sunshine Bakery and identify optimization opportunities"
    )

    result = grok_forecaster.run(task)

    print("Grok Agent Result:")
    print("-" * 70)
    print(result.result[:500] + "..." if len(result.result) > 500 else result.result)
    print("-" * 70)
    print()
    print("✅ Grok integration demo complete!")
    print()
    print("Key Benefits:")
    print("  - Natural language reasoning over ontology data")
    print("  - Automatic tool selection and invocation")
    print("  - Multi-turn learning via agent memory")
    print("  - Reduced need for hardcoded business logic")
    print()


if __name__ == "__main__":
    import sys

    # Run main demo
    main()

    # Optionally run Grok integration demo
    if "--grok" in sys.argv:
        demo_grok_integration()

