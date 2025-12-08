# SDK Integration Quick Reference

**TL;DR**: Use **ADK for infrastructure**, **OpenAI SDK for agents**, **Ontology for domain logic**.

---

## Architecture Layers

```
Ontology Layer (Foundation)
    ↓
Adapter Layer (Integration) ← You are here
    ↓
SDK Layer (Execution)
    ├── ADK (Infrastructure)
    └── OpenAI SDK (Agents)
```

---

## Component Mapping

| What You Need | Use This SDK | Integration Point |
|---------------|--------------|-------------------|
| **Event Logging** | ADK | `OntologyEventLogger` |
| **Session Management** | ADK | `OntologySessionService` |
| **Memory Service** | ADK | `OntologyMemoryService` |
| **Evaluation** | ADK | `OntologyEvaluator` |
| **Agent Execution** | OpenAI SDK | `OntologyAgentAdapter` |
| **Handoffs** | OpenAI SDK | Built-in handoffs |
| **Guardrails** | OpenAI SDK | `OntologyOutputGuardrail` |
| **Tool Filtering** | Both | `OntologyToolFilter` |
| **MCP Tools** | Both | Direct integration |

---

## Quick Start Example

```python
from agents import Agent, Runner
from agent_kit.adapters import OntologyAgentAdapter, OntologyOutputGuardrail
from agent_kit.ontology.loader import OntologyLoader
from agent_kit.tools.business import predict, optimize

# Setup
ontology = OntologyLoader("assets/ontologies/business.ttl")

# Create OpenAI SDK agent
agent = Agent(
    name="ForecastAgent",
    instructions="Forecast business metrics.",
    tools=[predict, optimize],
)

# Wrap with ontology adapter
adapter = OntologyAgentAdapter(agent, ontology, "business")

# Add guardrails
adapter.agent.output_guardrails = [
    OntologyOutputGuardrail("business")
]

# Execute
result = await Runner.run(adapter.agent, input="Forecast revenue")
print(result.final_output)
```

---

## Multi-Agent with Handoffs

```python
from agents import Agent, Runner, handoff

# Create specialists
forecast_agent = OntologyAgentAdapter(
    Agent(name="ForecastAgent", instructions="..."),
    ontology, "business"
)

optimizer_agent = OntologyAgentAdapter(
    Agent(name="OptimizerAgent", instructions="..."),
    ontology, "business"
)

# Orchestrator with handoffs
orchestrator = OntologyAgentAdapter(
    Agent(
        name="Orchestrator",
        instructions="Route tasks to specialists.",
        handoffs=[forecast_agent.agent, optimizer_agent.agent],
    ),
    ontology, "business"
)

# Execute - OpenAI SDK handles handoffs automatically
result = await Runner.run(
    orchestrator.agent,
    input="Forecast and optimize revenue"
)
```

---

## Decision Matrix

### When to Use Which SDK

| Feature | ADK | OpenAI SDK | Choose |
|---------|-----|------------|--------|
| Events | ✅ | ⚠️ | **ADK** |
| Sessions | ✅ | ⚠️ | **ADK** |
| Memory | ✅ | ❌ | **ADK** |
| Evaluation | ✅ | ❌ | **ADK** |
| Agent Execution | ⚠️ | ✅ | **OpenAI SDK** |
| Handoffs | ⚠️ | ✅ | **OpenAI SDK** |
| Guardrails | ⚠️ | ✅ | **OpenAI SDK** |
| MCP | ✅ | ✅ | **Either** |

---

## Integration Checklist

### Phase 1: Foundation
- [ ] Install dependencies: `openai-agents`, `google-adk`
- [ ] Create `OntologyAgentAdapter`
- [ ] Create `OntologyEventLogger`
- [ ] Test basic agent execution

### Phase 2: Multi-Agent
- [ ] Implement handoffs with OpenAI SDK
- [ ] Add `OntologyOutputGuardrail`
- [ ] Add `OntologyToolFilter`
- [ ] Test multi-agent workflows

### Phase 3: Production
- [ ] Integrate ADK session service
- [ ] Add ADK memory service
- [ ] Create evaluation test cases
- [ ] Deploy with cloud backends

---

## Key Files

| File | Purpose |
|------|---------|
| `src/agent_kit/adapters/ontology_agent_adapter.py` | Wraps OpenAI SDK agents |
| `src/agent_kit/adapters/ontology_guardrail.py` | Validates outputs |
| `src/agent_kit/adapters/ontology_tool_filter.py` | Filters tools by domain |
| `src/agent_kit/events/ontology_event_logger.py` | Enriches ADK events |
| `docs/UNIFIED_SDK_INTEGRATION_STRATEGY.md` | Full strategy doc |

---

## Common Patterns

### Pattern 1: Simple Agent
```python
agent = OntologyAgentAdapter(
    Agent(name="Agent", instructions="..."),
    ontology, "business"
)
result = await Runner.run(agent.agent, input="...")
```

### Pattern 2: With Session
```python
from agent_kit.sessions import OntologySessionService
from google.adk.sessions.sqlite_session_service import SqliteSessionService

session_backend = SqliteSessionService("sessions.db")
session_service = OntologySessionService(session_backend, ontology)

session = await session_service.get_session("session_001")
result = await Runner.run(agent.agent, input="...", session=session)
```

### Pattern 3: With Guardrails
```python
agent.agent.output_guardrails = [
    OntologyOutputGuardrail("business")
]
```

---

## References

- **Full Strategy**: [UNIFIED_SDK_INTEGRATION_STRATEGY.md](UNIFIED_SDK_INTEGRATION_STRATEGY.md)
- **ADK Details**: [ADK_INTEGRATION_RECOMMENDATIONS.md](ADK_INTEGRATION_RECOMMENDATIONS.md)
- **OpenAI SDK Docs**: https://openai.github.io/openai-agents-python/
- **ADK Docs**: https://github.com/google/adk-python

---

**Status**: ✅ Ready to use  
**Next**: See `examples/unified_sdk_integration.py` (coming soon)

