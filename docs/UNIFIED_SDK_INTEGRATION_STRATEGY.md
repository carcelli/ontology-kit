# Unified SDK Integration Strategy: ADK + OpenAI Agents SDK

**Date**: 2025-01-XX  
**Status**: 📋 Architecture Design  
**Goal**: Integrate both ADK Python (Google) and OpenAI Agents SDK while maintaining ontology-first architecture

---

## Executive Summary

**Three-Layer Architecture:**
1. **Ontology Layer** (Foundation) - Domain knowledge, SPARQL routing, entity extraction
2. **SDK Layer** (Execution) - ADK (infrastructure) + OpenAI SDK (agent orchestration)
3. **Adapter Layer** (Integration) - Bridge ontology to SDKs, enrich SDK events with ontology context

**Key Principle**: Ontology is the source of truth. SDKs are execution engines that we wrap and enhance.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Ontology Layer (Foundation)              │
│  • SPARQL queries for routing                               │
│  • Entity extraction & linking                               │
│  • Domain schemas (business, betting, trading)              │
│  • Leverage score computation                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Adapter Layer (Integration)               │
│  • OntologyEventLogger (enriches ADK events)               │
│  • OntologySessionService (wraps ADK sessions)              │
│  • OntologyAgentAdapter (wraps OpenAI SDK agents)           │
│  • OntologyToolFilter (filters tools by domain)             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    SDK Layer (Execution)                    │
│  ┌──────────────────────┐  ┌──────────────────────────┐   │
│  │   ADK (Infrastructure)│  │  OpenAI SDK (Agents)     │   │
│  │  • Event System      │  │  • Handoffs              │   │
│  │  • Session Mgmt      │  │  • Guardrails            │   │
│  │  • Memory Service    │  │  • MCP Tools             │   │
│  │  • Evaluation        │  │  • Tracing               │   │
│  └──────────────────────┘  └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Mapping

### ADK Python (Google) - Infrastructure Layer

| Component | Purpose | Integration Approach |
|-----------|---------|---------------------|
| **Event System** | Conversation tracking | `OntologyEvent` wrapper that adds SPARQL queries, leverage scores |
| **Session Management** | Multi-turn persistence | `OntologySessionService` adapter with entity extraction |
| **Memory Service** | Long-term recall | `OntologyMemoryService` with ontology-aware query expansion |
| **Evaluation Framework** | Agent testing | `OntologyEvaluator` with schema validation |
| **Runner** | Stateless orchestration | Pattern study only (don't replace orchestrator yet) |

**When to Use ADK:**
- ✅ Production infrastructure needs (sessions, events, memory)
- ✅ Enterprise backends (Spanner, Vertex AI)
- ✅ Systematic evaluation and testing
- ✅ Event compaction for context management

### OpenAI Agents SDK - Agent Execution Layer

| Component | Purpose | Integration Approach |
|-----------|---------|---------------------|
| **Agent** | LLM execution | `OntologyAgentAdapter` wraps OpenAI Agent with ontology context |
| **Handoffs** | Multi-agent coordination | Use for agent-to-agent transfers (replaces custom orchestrator logic) |
| **Guardrails** | Input/output validation | `OntologyGuardrail` validates against domain schemas |
| **MCP Tools** | Model Context Protocol | `OntologyMCPToolFilter` filters by domain allowlist |
| **Tracing** | Observability | Integrate with ADK event system |
| **Sessions** | Conversation history | Delegate to ADK session service (more robust) |

**When to Use OpenAI SDK:**
- ✅ Agent execution and handoffs
- ✅ Tool calling and MCP integration
- ✅ Guardrails for domain-specific validation
- ✅ Provider-agnostic LLM support (OpenAI, Anthropic, etc.)

---

## Integration Patterns

### Pattern 1: Ontology-Enriched Agent Execution

**Use OpenAI SDK for agent execution, enrich with ontology context:**

```python
from agents import Agent, Runner
from agent_kit.adapters.ontology_agent_adapter import OntologyAgentAdapter
from agent_kit.events import OntologyEventLogger
from agent_kit.ontology.loader import OntologyLoader

# Setup
ontology = OntologyLoader("assets/ontologies/business.ttl")
event_logger = OntologyEventLogger(ontology)

# Create OpenAI SDK agent
openai_agent = Agent(
    name="ForecastAgent",
    instructions="You forecast business metrics using ontology-driven tools.",
    tools=[query_ontology, predict, optimize],  # Ontology-aware tools
)

# Wrap with ontology adapter
ontology_agent = OntologyAgentAdapter(
    agent=openai_agent,
    ontology=ontology,
    domain="business",
)

# Execute with event logging
result = await Runner.run(ontology_agent, input="Forecast next 30 days")
event = event_logger.create_event("ForecastAgent", task, result, session_id)
```

**Benefits:**
- ✅ Leverage OpenAI SDK's handoff system
- ✅ Add ontology context to all agent actions
- ✅ Track SPARQL queries and leverage scores

### Pattern 2: ADK Infrastructure + OpenAI Execution

**Use ADK for infrastructure, OpenAI SDK for agent execution:**

```python
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from agents import Agent, Runner
from agent_kit.sessions import OntologySessionService
from agent_kit.adapters.ontology_agent_adapter import OntologyAgentAdapter

# ADK session backend
adk_session_backend = SqliteSessionService("sessions.db")
session_service = OntologySessionService(adk_session_backend, ontology)

# OpenAI SDK agent
openai_agent = Agent(
    name="ForecastAgent",
    instructions="...",
    tools=[...],
)

# Wrap with ontology adapter
ontology_agent = OntologyAgentAdapter(openai_agent, ontology, "business")

# Execute with ADK session management
session_id = "session_001"
session = await session_service.get_session(session_id)
result = await Runner.run(ontology_agent, input="Forecast next 30 days", session=session)
```

**Benefits:**
- ✅ Production-grade session persistence (ADK)
- ✅ Flexible agent execution (OpenAI SDK)
- ✅ Ontology context throughout

### Pattern 3: Multi-Agent Orchestration with Handoffs

**Use OpenAI SDK handoffs for agent coordination:**

```python
from agents import Agent, Runner, handoff
from agent_kit.adapters.ontology_agent_adapter import OntologyAgentAdapter

# Create specialist agents
forecast_agent = OntologyAgentAdapter(
    Agent(name="ForecastAgent", instructions="..."),
    ontology, "business"
)

optimizer_agent = OntologyAgentAdapter(
    Agent(name="OptimizerAgent", instructions="..."),
    ontology, "business"
)

# Create orchestrator with handoffs
orchestrator = OntologyAgentAdapter(
    Agent(
        name="BusinessOrchestrator",
        instructions="Route tasks to specialists based on ontology queries.",
        handoffs=[forecast_agent, optimizer_agent],
    ),
    ontology, "business"
)

# Execute - OpenAI SDK handles handoff logic
result = await Runner.run(orchestrator, input="Forecast and optimize revenue")
```

**Benefits:**
- ✅ Built-in handoff system (no custom orchestrator logic)
- ✅ Ontology-driven routing via adapter
- ✅ Automatic conversation history management

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

**Goal**: Establish adapter layer and basic integration

1. **OntologyAgentAdapter** - Wrap OpenAI SDK agents
   - Add ontology context to agent instructions
   - Track SPARQL queries during execution
   - Extract entities from conversations

2. **OntologyEventLogger** - Enrich ADK events
   - Capture ontology metadata (SPARQL queries, entities)
   - Integrate with OpenAI SDK tracing

3. **Basic Session Integration** - ADK sessions + OpenAI execution
   - Wrap ADK session service
   - Pass sessions to OpenAI SDK Runner

**Deliverables:**
- `src/agent_kit/adapters/ontology_agent_adapter.py`
- Updated `src/agent_kit/events/ontology_event_logger.py`
- Integration example in `examples/`

### Phase 2: Multi-Agent Orchestration (Week 3-4)

**Goal**: Leverage OpenAI SDK handoffs for agent coordination

1. **Handoff Integration** - Replace custom orchestrator logic
   - Use OpenAI SDK handoffs for agent transfers
   - Add ontology-driven routing via adapter

2. **Guardrail Integration** - Domain-specific validation
   - `OntologyGuardrail` validates outputs against Pydantic schemas
   - Input guardrails check domain allowlists

3. **Tool Filtering** - Domain-aware tool access
   - Filter tools by domain configuration
   - Integrate with OpenAI SDK tool system

**Deliverables:**
- `src/agent_kit/adapters/ontology_guardrail.py`
- `src/agent_kit/adapters/ontology_tool_filter.py`
- Updated orchestrator using handoffs

### Phase 3: Production Infrastructure (Week 5-6)

**Goal**: Full ADK infrastructure integration

1. **Memory Service** - Long-term recall
   - `OntologyMemoryService` with entity expansion
   - Integrate with OpenAI SDK context

2. **Evaluation Framework** - Systematic testing
   - `OntologyEvaluator` with schema validation
   - Test cases for all domains

3. **Cloud Backends** - Production scalability
   - Vertex AI session/memory services
   - Spanner backend for enterprise

**Deliverables:**
- `src/agent_kit/memory/ontology_memory_service.py`
- `src/agent_kit/evaluation/ontology_evaluator.py`
- Production deployment examples

---

## Code Examples

### Example 1: OntologyAgentAdapter

```python
# src/agent_kit/adapters/ontology_agent_adapter.py
from __future__ import annotations

from agents import Agent, RunContextWrapper
from agent_kit.ontology.loader import OntologyLoader

class OntologyAgentAdapter:
    """
    Wraps OpenAI SDK Agent with ontology context.
    
    Enriches agent execution with:
    - SPARQL query tracking
    - Entity extraction
    - Domain-specific tool filtering
    - Leverage score computation (business domain)
    """
    
    def __init__(
        self,
        agent: Agent,
        ontology: OntologyLoader,
        domain: str,
    ):
        self.agent = agent
        self.ontology = ontology
        self.domain = domain
        
        # Enhance instructions with ontology context
        self._enhance_instructions()
    
    def _enhance_instructions(self) -> None:
        """Add ontology context to agent instructions."""
        ontology_context = self._get_ontology_context()
        original_instructions = self.agent.instructions
        
        if isinstance(original_instructions, str):
            enhanced = f"""{original_instructions}

Ontology Context:
- Domain: {self.domain}
- Available entities: {ontology_context['entities']}
- Key relationships: {ontology_context['relationships']}

When making decisions, query the ontology using SPARQL to understand entity relationships.
"""
            self.agent.instructions = enhanced
    
    def _get_ontology_context(self) -> dict:
        """Query ontology for domain context."""
        # SPARQL query to get domain entities
        query = f"""
        SELECT ?entity ?label WHERE {{
            ?entity rdfs:label ?label .
            ?entity rdf:type <http://agent_kit.io/{self.domain}#Entity> .
        }}
        """
        results = self.ontology.query(query)
        return {
            "entities": [r["label"] for r in results],
            "relationships": [],  # TODO: Extract relationships
        }
```

### Example 2: OntologyGuardrail

```python
# src/agent_kit/adapters/ontology_guardrail.py
from __future__ import annotations

from agents import OutputGuardrail, RunContextWrapper
from agent_kit.schemas import get_schema, BusinessOptimizationResult
from pydantic import ValidationError

class OntologyOutputGuardrail(OutputGuardrail):
    """
    Validates agent outputs against domain schemas.
    
    Ensures outputs conform to Pydantic schemas defined in ontology-kit.
    """
    
    def __init__(self, domain: str):
        self.domain = domain
        self.schema = get_schema(f"{domain.capitalize()}OptimizationResult")
    
    async def check(
        self,
        context: RunContextWrapper,
        output: str,
    ) -> OutputGuardrailResult:
        """Validate output against domain schema."""
        try:
            # Parse output as JSON and validate
            import json
            output_dict = json.loads(output)
            validated = self.schema(**output_dict)
            return OutputGuardrailResult(passed=True)
        except (json.JSONDecodeError, ValidationError) as e:
            return OutputGuardrailResult(
                passed=False,
                error_message=f"Output validation failed: {e}",
            )
```

### Example 3: Complete Integration

```python
# examples/unified_sdk_integration.py
from agents import Agent, Runner
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from agent_kit.adapters import OntologyAgentAdapter, OntologyOutputGuardrail
from agent_kit.sessions import OntologySessionService
from agent_kit.ontology.loader import OntologyLoader
from agent_kit.tools.business import predict, optimize

async def main():
    # Setup
    ontology = OntologyLoader("assets/ontologies/business.ttl")
    
    # ADK session backend
    adk_backend = SqliteSessionService("sessions.db")
    session_service = OntologySessionService(adk_backend, ontology)
    
    # Create OpenAI SDK agents
    forecast_agent = Agent(
        name="ForecastAgent",
        instructions="Forecast business metrics using historical data.",
        tools=[predict],
        output_type=BusinessOptimizationResult,
    )
    
    optimizer_agent = Agent(
        name="OptimizerAgent",
        instructions="Optimize business processes using leverage analysis.",
        tools=[optimize],
        output_type=BusinessOptimizationResult,
    )
    
    # Wrap with ontology adapters
    forecast_adapter = OntologyAgentAdapter(forecast_agent, ontology, "business")
    optimizer_adapter = OntologyAgentAdapter(optimizer_agent, ontology, "business")
    
    # Add guardrails
    forecast_adapter.agent.output_guardrails = [
        OntologyOutputGuardrail("business")
    ]
    
    # Create orchestrator with handoffs
    orchestrator = OntologyAgentAdapter(
        Agent(
            name="BusinessOrchestrator",
            instructions="Route tasks to specialists based on user intent.",
            handoffs=[forecast_adapter.agent, optimizer_adapter.agent],
        ),
        ontology, "business"
    )
    
    # Execute
    session_id = "session_001"
    session = await session_service.get_session(session_id)
    
    result = await Runner.run(
        orchestrator.agent,
        input="Forecast revenue for next 30 days and optimize marketing spend",
        session=session,
    )
    
    print(result.final_output)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## Decision Matrix

### When to Use ADK vs OpenAI SDK

| Feature | ADK | OpenAI SDK | Recommendation |
|---------|-----|------------|---------------|
| **Event Logging** | ✅ Production-grade | ⚠️ Basic tracing | **ADK** - More robust |
| **Session Management** | ✅ Multiple backends | ⚠️ Basic sessions | **ADK** - Enterprise-ready |
| **Memory Service** | ✅ RAG + Memory Bank | ❌ Not available | **ADK** - Only option |
| **Evaluation** | ✅ Comprehensive | ❌ Not available | **ADK** - Only option |
| **Agent Execution** | ⚠️ Complex | ✅ Simple, flexible | **OpenAI SDK** - Better API |
| **Handoffs** | ⚠️ Custom logic | ✅ Built-in | **OpenAI SDK** - Native support |
| **Guardrails** | ⚠️ Basic | ✅ Rich API | **OpenAI SDK** - More features |
| **MCP Tools** | ✅ Supported | ✅ Supported | **Either** - Both work |
| **Tracing** | ✅ Event-based | ✅ Span-based | **Both** - Integrate together |

### Integration Strategy Summary

1. **Use ADK for Infrastructure**
   - Event system (conversation tracking)
   - Session management (multi-turn persistence)
   - Memory service (long-term recall)
   - Evaluation framework (testing)

2. **Use OpenAI SDK for Agent Execution**
   - Agent definition and execution
   - Handoffs (multi-agent coordination)
   - Guardrails (input/output validation)
   - Tool calling and MCP integration

3. **Use Ontology Layer for Domain Logic**
   - SPARQL routing
   - Entity extraction
   - Leverage score computation
   - Domain schema validation

---

## Migration Path

### Current State → Unified Architecture

**Step 1**: Keep existing `OntologyOrchestratorAgent` but add adapters
- ✅ No breaking changes
- ✅ Gradual migration

**Step 2**: Replace orchestrator logic with OpenAI SDK handoffs
- ✅ Simpler code
- ✅ Better multi-agent coordination

**Step 3**: Integrate ADK infrastructure
- ✅ Production-ready sessions
- ✅ Event tracking
- ✅ Memory service

**Step 4**: Full integration
- ✅ Unified adapter layer
- ✅ Best of both SDKs
- ✅ Ontology-first architecture maintained

---

## Benefits

### Technical Benefits

✅ **Best of Both Worlds**: ADK infrastructure + OpenAI SDK agent execution  
✅ **Maintainability**: Clear separation of concerns (ontology, infrastructure, execution)  
✅ **Flexibility**: Can swap SDKs without changing ontology layer  
✅ **Production Ready**: Enterprise backends (Spanner, Vertex AI) + robust agent execution

### Business Benefits

✅ **Faster Development**: Leverage existing SDKs instead of building from scratch  
✅ **Lower Risk**: Battle-tested infrastructure from Google and OpenAI  
✅ **Better Observability**: ADK events + OpenAI SDK tracing  
✅ **Domain Expertise**: Ontology layer preserves your competitive advantage

---

## References

- [ADK Integration Recommendations](ADK_INTEGRATION_RECOMMENDATIONS.md)
- [OpenAI Agents SDK Docs](https://openai.github.io/openai-agents-python/)
- [ADK Python Docs](https://github.com/google/adk-python)
- [Ontology-Kit Architecture](docs/guides/ARCHITECTURE_DECISION.md)

---

**Status**: ✅ Ready for implementation  
**Next Step**: Create `src/agent_kit/adapters/` module and implement `OntologyAgentAdapter`

