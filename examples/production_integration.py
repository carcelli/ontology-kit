#!/usr/bin/env python
"""
Production-Ready Integration: ADK + OpenAI Agents SDK

This example demonstrates the complete, production-ready integration of:
- Google ADK (Infrastructure): Sessions, Events, Memory
- OpenAI Agents SDK (Execution): Handoffs, Guardrails, Tools
- Ontology-Kit (Domain): SPARQL, Entities, Validation

Run:
    export OPENAI_API_KEY='your-key'
    python examples/production_integration.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Core imports
from agents import Agent, Runner
from agent_kit.adapters import (
    OntologyAgentAdapter,
    OntologyOutputGuardrail,
    OntologyInputGuardrail,
)
from agent_kit.adapters.handoff_manager import OntologyHandoffManager
from agent_kit.events import OntologyEventLogger
from agent_kit.evaluation import OntologyEvaluator, EvalSet, EvalCase
from agent_kit.memory import OntologyMemoryService
from agent_kit.ontology.loader import OntologyLoader
from agent_kit.orchestrator import UnifiedOrchestrator, OrchestratorConfig
from agent_kit.runners import OntologyRunner, RunConfig, StreamingRunner
from agent_kit.sessions import OntologySessionService, SqliteSessionBackend
from agent_kit.tools.business import predict, optimize
from agent_kit.tools.ontology import query_ontology


# =============================================================================
# Configuration
# =============================================================================

class ProductionConfig:
    """Production configuration."""
    
    ONTOLOGY_PATH = Path(__file__).parent.parent / "assets" / "ontologies" / "business.ttl"
    SESSION_DB = Path(__file__).parent.parent / "data" / "sessions.db"
    DOMAIN = "business"
    
    # Feature flags
    ENABLE_MEMORY = True
    ENABLE_GUARDRAILS = True
    ENABLE_STREAMING = True
    ENABLE_EVALUATION = True


# =============================================================================
# Setup Functions
# =============================================================================

def setup_ontology() -> OntologyLoader:
    """Load and configure ontology."""
    print("📚 Loading ontology...")
    ontology = OntologyLoader(str(ProductionConfig.ONTOLOGY_PATH))
    
    if ProductionConfig.ONTOLOGY_PATH.exists():
        ontology.load()
        print(f"   ✅ Loaded from {ProductionConfig.ONTOLOGY_PATH}")
    else:
        print(f"   ⚠️ Ontology not found, using empty graph")
    
    return ontology


def setup_session_service(ontology: OntologyLoader) -> OntologySessionService:
    """Configure session service with SQLite backend."""
    print("💾 Setting up session service...")
    
    # Ensure data directory exists
    ProductionConfig.SESSION_DB.parent.mkdir(parents=True, exist_ok=True)
    
    backend = SqliteSessionBackend(ProductionConfig.SESSION_DB)
    service = OntologySessionService(backend, ontology)
    print(f"   ✅ SQLite backend at {ProductionConfig.SESSION_DB}")
    
    return service


def setup_memory_service(ontology: OntologyLoader) -> OntologyMemoryService:
    """Configure memory service."""
    print("🧠 Setting up memory service...")
    service = OntologyMemoryService(ontology, domain=ProductionConfig.DOMAIN)
    print("   ✅ In-memory backend (upgrade to VertexAI RAG for production)")
    return service


def setup_event_logger(ontology: OntologyLoader) -> OntologyEventLogger:
    """Configure event logger."""
    print("📝 Setting up event logger...")
    logger = OntologyEventLogger(ontology, domain=ProductionConfig.DOMAIN)
    print("   ✅ Ontology-enriched event logging")
    return logger


# =============================================================================
# Agent Factory
# =============================================================================

def create_forecast_agent(ontology: OntologyLoader) -> OntologyAgentAdapter:
    """Create revenue forecasting specialist."""
    agent = Agent(
        name="ForecastAgent",
        instructions="""You are an expert revenue forecasting specialist.

Your responsibilities:
1. Generate accurate revenue forecasts using historical data
2. Provide confidence intervals and uncertainty estimates
3. Identify key factors affecting the forecast
4. Explain your methodology clearly

When forecasting:
- Use the predict tool to generate forecasts
- Query the ontology for business context
- Consider seasonality, trends, and external factors
- Always provide actionable insights

Output format:
- Forecast values with confidence levels
- Key assumptions
- Recommended actions based on forecast
""",
        tools=[predict, query_ontology],
    )
    
    adapter = OntologyAgentAdapter(agent, ontology, ProductionConfig.DOMAIN)
    
    if ProductionConfig.ENABLE_GUARDRAILS:
        adapter.agent.output_guardrails = [
            OntologyOutputGuardrail(ProductionConfig.DOMAIN)
        ]
    
    return adapter


def create_optimizer_agent(ontology: OntologyLoader) -> OntologyAgentAdapter:
    """Create business optimization specialist."""
    agent = Agent(
        name="OptimizerAgent",
        instructions="""You are an expert business optimization specialist.

Your responsibilities:
1. Identify leverage points to improve business metrics
2. Recommend interventions with expected ROI
3. Assess implementation risks and costs
4. Prioritize recommendations by impact

When optimizing:
- Use the optimize tool for analysis
- Query the ontology for business relationships
- Consider constraints and resources
- Provide actionable, prioritized recommendations

Output format:
- Top 3-5 recommendations ranked by impact
- Expected ROI for each
- Implementation timeline
- Risk assessment
""",
        tools=[optimize, query_ontology],
    )
    
    adapter = OntologyAgentAdapter(agent, ontology, ProductionConfig.DOMAIN)
    
    if ProductionConfig.ENABLE_GUARDRAILS:
        adapter.agent.output_guardrails = [
            OntologyOutputGuardrail(ProductionConfig.DOMAIN)
        ]
    
    return adapter


# =============================================================================
# Demo Functions
# =============================================================================

async def demo_basic_execution(
    runner: OntologyRunner,
    forecast_agent: OntologyAgentAdapter,
) -> None:
    """Demonstrate basic agent execution."""
    print("\n" + "=" * 80)
    print("Demo 1: Basic Agent Execution")
    print("=" * 80)
    
    config = RunConfig(
        domain=ProductionConfig.DOMAIN,
        store_memory=ProductionConfig.ENABLE_MEMORY,
    )
    
    result = await runner.run(
        forecast_agent,
        "Forecast revenue for the next 30 days",
        config,
    )
    
    print(f"\n📊 Result:")
    print(f"   Output: {result.output[:200]}..." if len(result.output) > 200 else f"   Output: {result.output}")
    print(f"   Session: {result.session_id}")
    print(f"   Duration: {result.duration_seconds:.2f}s")
    print(f"   Events: {len(result.events)}")
    print(f"   SPARQL queries: {len(result.sparql_queries)}")


async def demo_multi_agent_handoff(
    ontology: OntologyLoader,
    forecast_agent: OntologyAgentAdapter,
    optimizer_agent: OntologyAgentAdapter,
) -> None:
    """Demonstrate multi-agent handoffs."""
    print("\n" + "=" * 80)
    print("Demo 2: Multi-Agent Handoff")
    print("=" * 80)
    
    # Create orchestrator with handoffs
    orchestrator = Agent(
        name="BusinessOrchestrator",
        instructions="""You coordinate business analysis tasks.
        
Route to ForecastAgent for: forecasting, predictions, trends
Route to OptimizerAgent for: optimization, improvements, recommendations

For complex requests, use both agents sequentially.""",
        handoffs=[forecast_agent.agent, optimizer_agent.agent],
    )
    
    # Wrap orchestrator
    orch_adapter = OntologyAgentAdapter(orchestrator, ontology, ProductionConfig.DOMAIN)
    
    print("\n🎭 Running orchestrator with handoffs...")
    result = await Runner.run(
        orch_adapter.agent,
        input="Forecast revenue and suggest ways to improve it by 10%",
    )
    
    print(f"\n📊 Result:")
    print(f"   {result.final_output[:300]}...")


async def demo_streaming(
    streaming_runner: StreamingRunner,
    forecast_agent: OntologyAgentAdapter,
) -> None:
    """Demonstrate streaming responses."""
    if not ProductionConfig.ENABLE_STREAMING:
        print("\n⏭️ Streaming disabled, skipping...")
        return
    
    print("\n" + "=" * 80)
    print("Demo 3: Streaming Response")
    print("=" * 80)
    
    print("\n📡 Streaming response:")
    print("   ", end="", flush=True)
    
    async for chunk in streaming_runner.stream(
        forecast_agent,
        "Give me a brief revenue outlook",
    ):
        print(chunk.text, end="", flush=True)
    
    print("\n")


async def demo_memory_recall(
    memory_service: OntologyMemoryService,
) -> None:
    """Demonstrate memory recall."""
    if not ProductionConfig.ENABLE_MEMORY:
        print("\n⏭️ Memory disabled, skipping...")
        return
    
    print("\n" + "=" * 80)
    print("Demo 4: Memory Recall")
    print("=" * 80)
    
    # Store some memories
    user_id = "demo_user"
    await memory_service.store(
        "Revenue forecast shows 15% growth expected in Q1",
        user_id=user_id,
        session_id="demo_session",
    )
    
    await memory_service.store(
        "Top optimization: Increase email marketing frequency by 2x",
        user_id=user_id,
        session_id="demo_session",
    )
    
    # Search
    results = await memory_service.search(
        "revenue growth",
        user_id=user_id,
        limit=3,
    )
    
    print(f"\n🔍 Search results for 'revenue growth':")
    for i, result in enumerate(results, 1):
        print(f"   {i}. Score: {result.score:.2f}")
        print(f"      Content: {result.entry.content[:80]}...")


async def demo_evaluation(
    evaluator: OntologyEvaluator,
    forecast_agent: OntologyAgentAdapter,
) -> None:
    """Demonstrate evaluation framework."""
    if not ProductionConfig.ENABLE_EVALUATION:
        print("\n⏭️ Evaluation disabled, skipping...")
        return
    
    print("\n" + "=" * 80)
    print("Demo 5: Evaluation Framework")
    print("=" * 80)
    
    # Create simple eval set
    eval_set = EvalSet(
        name="Business Forecast Tests",
        domain=ProductionConfig.DOMAIN,
        cases=[
            EvalCase(
                id="forecast_basic",
                name="Basic Forecast",
                input="What's the revenue forecast?",
                expected_entities=["revenue", "forecast"],
            ),
            EvalCase(
                id="forecast_30day",
                name="30-Day Forecast",
                input="Forecast revenue for next 30 days",
                expected_entities=["revenue"],
            ),
        ],
    )
    
    print(f"\n📋 Running {len(eval_set.cases)} test cases...")
    result = await evaluator.evaluate(forecast_agent, eval_set)
    
    print(result.summary())


async def demo_unified_orchestrator(
    ontology: OntologyLoader,
    forecast_agent: OntologyAgentAdapter,
    optimizer_agent: OntologyAgentAdapter,
) -> None:
    """Demonstrate unified orchestrator."""
    print("\n" + "=" * 80)
    print("Demo 6: Unified Orchestrator")
    print("=" * 80)
    
    config = OrchestratorConfig(
        domain=ProductionConfig.DOMAIN,
        session_backend="memory",
        enable_memory=True,
        enable_guardrails=True,
    )
    
    orchestrator = UnifiedOrchestrator(ontology, config)
    orchestrator.register_agent("ForecastAgent", forecast_agent)
    orchestrator.register_agent("OptimizerAgent", optimizer_agent)
    orchestrator.create_orchestrator_agent()
    
    print(f"\n🎭 Registered agents: {orchestrator.get_registered_agents()}")
    
    result = await orchestrator.run(
        "What's our revenue outlook and how can we improve?",
        user_id="demo_user",
    )
    
    print(f"\n📊 Result:")
    print(f"   Output: {result.output[:200]}..." if len(result.output) > 200 else f"   Output: {result.output}")
    print(f"   Agents used: {result.agents_used}")
    print(f"   Duration: {result.duration_seconds:.2f}s")


# =============================================================================
# Main
# =============================================================================

async def main() -> None:
    """Run production integration demo."""
    print("=" * 80)
    print("Production Integration Demo")
    print("ADK Infrastructure + OpenAI SDK Execution")
    print("=" * 80)
    print()
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        print("   Run: export OPENAI_API_KEY='your-key'")
        return
    
    print(f"✅ OpenAI API key: {api_key[:10]}...")
    print()
    
    # Setup infrastructure
    print("=" * 80)
    print("Infrastructure Setup")
    print("=" * 80)
    
    ontology = setup_ontology()
    session_service = setup_session_service(ontology)
    memory_service = setup_memory_service(ontology)
    event_logger = setup_event_logger(ontology)
    
    # Create runner
    runner = OntologyRunner(
        ontology,
        domain=ProductionConfig.DOMAIN,
        memory_service=memory_service,
        event_logger=event_logger,
    )
    
    streaming_runner = StreamingRunner(ontology, domain=ProductionConfig.DOMAIN)
    evaluator = OntologyEvaluator(ontology, domain=ProductionConfig.DOMAIN)
    
    # Create agents
    print("\n" + "=" * 80)
    print("Agent Creation")
    print("=" * 80)
    print()
    
    forecast_agent = create_forecast_agent(ontology)
    print(f"✅ Created: {forecast_agent.agent.name}")
    
    optimizer_agent = create_optimizer_agent(ontology)
    print(f"✅ Created: {optimizer_agent.agent.name}")
    
    # Run demos
    try:
        await demo_basic_execution(runner, forecast_agent)
        await demo_multi_agent_handoff(ontology, forecast_agent, optimizer_agent)
        await demo_streaming(streaming_runner, forecast_agent)
        await demo_memory_recall(memory_service)
        await demo_evaluation(evaluator, forecast_agent)
        await demo_unified_orchestrator(ontology, forecast_agent, optimizer_agent)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ Production Integration Demo Complete!")
    print("=" * 80)
    print()
    print("Key Components Demonstrated:")
    print("  1. OntologyRunner - Unified execution with event logging")
    print("  2. Multi-Agent Handoffs - OpenAI SDK handoff system")
    print("  3. Streaming - Real-time response streaming")
    print("  4. Memory - Cross-session recall with entity linking")
    print("  5. Evaluation - Systematic testing with metrics")
    print("  6. Unified Orchestrator - Combined ADK + OpenAI SDK")
    print()
    print("For production deployment:")
    print("  - Replace InMemoryBackend with SqliteSessionBackend or VertexAI")
    print("  - Add monitoring with OntologyEventLogger")
    print("  - Run evaluations in CI/CD pipeline")
    print("  - Configure guardrails for your domain")


if __name__ == "__main__":
    asyncio.run(main())

