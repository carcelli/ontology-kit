#!/usr/bin/env python
"""
Example: ADK Infrastructure + OpenAI SDK Agent Execution

Demonstrates the unified SDK architecture:
- ADK for infrastructure (sessions, events, memory)
- OpenAI SDK for agent execution (handoffs, guardrails)
- Ontology layer for domain knowledge

This is the recommended pattern for production deployments.

Prerequisites:
    - Set OPENAI_API_KEY environment variable
    - Install: pip install openai-agents google-adk

Run:
    python examples/adk_openai_integration.py
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
from agent_kit.events import OntologyEventLogger
from agent_kit.memory import OntologyMemoryService
from agent_kit.ontology.loader import OntologyLoader
from agent_kit.sessions import OntologySessionService
from agent_kit.tools.business import predict, optimize
from agent_kit.tools.ontology import query_ontology


# Simple in-memory session backend for testing
class SimpleSessionBackend:
    """Simple session backend for demonstration."""
    
    def __init__(self):
        self._sessions: dict[str, dict] = {}
    
    async def get_session(self, session_id: str) -> dict:
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "id": session_id,
                "events": [],
                "metadata": {},
            }
        return self._sessions[session_id]
    
    async def save_session(self, session_id: str, session_data: dict) -> None:
        self._sessions[session_id] = session_data


async def main() -> None:
    """Run ADK + OpenAI SDK integration example."""
    print("=" * 80)
    print("ADK Infrastructure + OpenAI SDK Agent Execution")
    print("=" * 80)
    print()
    print("Architecture:")
    print("  ┌─────────────────────────────────────┐")
    print("  │   Ontology Layer (Foundation)      │")
    print("  │   SPARQL, Entities, Domain Logic   │")
    print("  └─────────────────────────────────────┘")
    print("                  ↓")
    print("  ┌─────────────────────────────────────┐")
    print("  │   Adapter Layer (Integration)      │")
    print("  │   OntologyAgentAdapter             │")
    print("  │   OntologyEventLogger              │")
    print("  │   OntologySessionService           │")
    print("  │   OntologyMemoryService            │")
    print("  └─────────────────────────────────────┘")
    print("                  ↓")
    print("  ┌────────────────┬────────────────────┐")
    print("  │ ADK (Infra)    │ OpenAI SDK (Agents)│")
    print("  │ • Sessions     │ • Execution        │")
    print("  │ • Events       │ • Handoffs         │")
    print("  │ • Memory       │ • Guardrails       │")
    print("  └────────────────┴────────────────────┘")
    print()

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='your-key'")
        return

    print(f"✅ OpenAI API key found: {api_key[:10]}...")
    print()

    # ==========================================================================
    # Setup Ontology Layer
    # ==========================================================================
    print("1️⃣  Setting up Ontology Layer...")
    ontology_path = Path(__file__).parent.parent / "assets" / "ontologies" / "business.ttl"
    ontology = OntologyLoader(str(ontology_path))

    if ontology_path.exists():
        ontology.load()
        print("   ✅ Ontology loaded from:", ontology_path)
    else:
        print(f"   ⚠️  Ontology not found, using empty loader")
    print()

    # ==========================================================================
    # Setup Infrastructure (ADK-style)
    # ==========================================================================
    print("2️⃣  Setting up Infrastructure (ADK-style)...")

    # Session service - wraps backend with ontology awareness
    session_backend = SimpleSessionBackend()
    session_service = OntologySessionService(session_backend, ontology)
    print("   ✅ Session service initialized")

    # Event logger - tracks ontology context in events
    event_logger = OntologyEventLogger(ontology, domain="business")
    print("   ✅ Event logger initialized")

    # Memory service - cross-session recall with entity expansion
    memory_service = OntologyMemoryService(ontology, domain="business")
    print("   ✅ Memory service initialized")
    print()

    # ==========================================================================
    # Setup Agent (OpenAI SDK)
    # ==========================================================================
    print("3️⃣  Setting up Agent (OpenAI SDK)...")

    # Create OpenAI SDK agent
    agent = Agent(
        name="BusinessAnalystAgent",
        instructions="""You are a business analyst that helps small businesses with:
- Revenue forecasting and trend analysis
- Business optimization recommendations
- Data-driven decision making

When analyzing:
1. Query the ontology to understand business context
2. Use forecasting tools for predictions
3. Identify optimization opportunities
4. Provide clear, actionable recommendations

Always explain your reasoning and provide confidence levels.
""",
        tools=[predict, optimize, query_ontology],
    )
    print(f"   ✅ Created agent: {agent.name}")

    # Wrap with ontology adapter
    adapter = OntologyAgentAdapter(agent, ontology, "business")
    print(f"   ✅ Wrapped with ontology adapter (domain: {adapter.domain})")

    # Add guardrails
    adapter.agent.output_guardrails = [
        OntologyOutputGuardrail("business")
    ]
    print("   ✅ Added output guardrails")
    print()

    # ==========================================================================
    # Execute with Full Infrastructure
    # ==========================================================================
    print("4️⃣  Executing with Full Infrastructure...")
    print()

    session_id = "demo_session_001"
    user_id = "demo_user"

    # Start tracking
    event_logger.start_tracking(session_id)
    session = await session_service.get_session(session_id)
    print(f"   📋 Session: {session_id}")
    print()

    # Example tasks
    tasks = [
        "What's our revenue forecast for the next 30 days?",
        "What are the top 3 ways to improve revenue?",
    ]

    for i, task in enumerate(tasks, 1):
        print(f"   📝 Task {i}: {task}")
        print("   " + "-" * 50)

        try:
            # Execute via OpenAI SDK
            result = await Runner.run(adapter.agent, input=task)
            output = result.final_output
            print(f"   ✅ Result: {output[:200]}..." if len(output) > 200 else f"   ✅ Result: {output}")

            # Log event with ontology context
            event = event_logger.create_event(
                agent_name=adapter.agent.name,
                task=task,
                result={"summary": output},
                session_id=session_id,
            )
            print(f"   📊 Event logged: {event.id[:8]}...")

            # Store in memory for future recall
            await memory_service.store(
                content=f"Task: {task}\nResult: {output}",
                user_id=user_id,
                session_id=session_id,
            )
            print("   💾 Stored in memory")

        except Exception as e:
            print(f"   ❌ Error: {e}")

        print()

    # ==========================================================================
    # Demonstrate Memory Recall
    # ==========================================================================
    print("5️⃣  Demonstrating Memory Recall...")
    print()

    # Search for past conversations
    search_results = await memory_service.search(
        query="revenue forecast",
        user_id=user_id,
        limit=3,
    )

    if search_results:
        print(f"   Found {len(search_results)} relevant memories:")
        for i, result in enumerate(search_results, 1):
            preview = result.entry.content[:100].replace("\n", " ")
            print(f"   {i}. Score: {result.score:.2f} - {preview}...")
    else:
        print("   No memories found (this is expected for first run)")
    print()

    # ==========================================================================
    # Show Event Summary
    # ==========================================================================
    print("6️⃣  Event Summary...")
    print()

    events = event_logger.get_events(session_id)
    print(f"   Total events: {len(events)}")

    for event in events:
        print(f"   - {event.author}: {event.content.text[:50]}...")
        if event.sparql_queries:
            print(f"     SPARQL queries: {len(event.sparql_queries)}")
        if event.extracted_entities:
            print(f"     Entities: {', '.join(event.extracted_entities[:5])}")
    print()

    # Stop tracking
    event_logger.stop_tracking(session_id)

    print("=" * 80)
    print("✅ Integration example completed!")
    print("=" * 80)
    print()
    print("Key Integration Points:")
    print("  • Ontology provides domain context for all components")
    print("  • Sessions persist conversation state (ADK pattern)")
    print("  • Events track agent actions with ontology metadata")
    print("  • Memory enables cross-session recall")
    print("  • OpenAI SDK handles agent execution and guardrails")
    print()
    print("For production, replace SimpleSessionBackend with:")
    print("  • google.adk.sessions.SqliteSessionService (local)")
    print("  • google.adk.sessions.VertexAISessionService (cloud)")


if __name__ == "__main__":
    asyncio.run(main())

