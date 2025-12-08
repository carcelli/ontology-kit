# ADK Integration Quick Reference

**TL;DR**: ADK Python provides production infrastructure. Integrate via adapter pattern—wrap ADK services, don't replace ontology-first architecture.

---

## Priority Matrix

| Component | Priority | Effort | Value | Status |
|-----------|----------|--------|-------|--------|
| **Event System** | 🔴 High | 2-3 days | ✅ Observability, debugging | 📋 Ready |
| **Session Management** | 🔴 High | 1-2 days | ✅ Multi-turn conversations | 📋 Ready |
| **Memory Service** | 🟡 Medium | 2-3 days | ✅ Cross-session recall | 📋 Planned |
| **Evaluation Framework** | 🟡 Medium | 2-3 days | ✅ Regression testing | 📋 Planned |
| **Runner Architecture** | 🟢 Low | 1-2 weeks | ⚠️ Pattern study only | 📋 Future |
| **Tool Ecosystem** | 🟢 Low | 1-2 weeks | ⚠️ Nice-to-have | 📋 Future |

---

## Key ADK Components

### 1. Event System (`google.adk.events`)
- **What**: Immutable conversation log
- **Why**: Observability, debugging, compliance
- **Integration**: `OntologyEvent` wrapper (✅ Implemented)

### 2. Session Management (`google.adk.sessions`)
- **What**: Conversation state persistence
- **Why**: Multi-turn conversations, resumability
- **Backends**: InMemory, SQLite, Vertex AI, Spanner
- **Integration**: `OntologySessionService` adapter

### 3. Memory Service (`google.adk.memory`)
- **What**: Long-term recall across sessions
- **Why**: Context awareness, personalization
- **Backends**: InMemory, Vertex AI RAG, Memory Bank
- **Integration**: `OntologyMemoryService` with entity expansion

### 4. Evaluation Framework (`google.adk.evaluation`)
- **What**: Systematic agent testing
- **Why**: Regression testing, quality metrics
- **Components**: EvalSet, AgentEvaluator, LLMAsJudge
- **Integration**: `OntologyEvaluator` with schema validation

---

## Integration Pattern

```python
# Adapter Pattern: Wrap ADK, enrich with ontology
from google.adk.sessions.base_session_service import BaseSessionService
from agent_kit.ontology.loader import OntologyLoader

class OntologySessionService(BaseSessionService):
    """Wrapper that adds ontology context to ADK sessions."""
    
    def __init__(self, backend: BaseSessionService, ontology: OntologyLoader):
        self.backend = backend  # Delegate to ADK
        self.ontology = ontology  # Add ontology layer
```

**Principle**: ADK = Infrastructure, Ontology = Domain Logic

---

## Implementation Checklist

### Phase 1: Foundation (Week 1-2)
- [ ] Integrate `OntologyEvent` into orchestrator
- [ ] Add `OntologySessionService` with SQLite backend
- [ ] Update agents to emit events
- [ ] Add event logging to tool calls

### Phase 2: Observability (Week 3-4)
- [ ] Integrate `OntologyMemoryService`
- [ ] Create evaluation test cases
- [ ] Add CI integration for regression tests
- [ ] Build event replay/debugging tools

### Phase 3: Production (Week 5-6)
- [ ] Add Vertex AI session backend
- [ ] Integrate MCP tools
- [ ] Add OpenAPI tool generation
- [ ] Documentation and examples

---

## Quick Start Example

```python
from agent_kit.events import OntologyEventLogger
from agent_kit.sessions import OntologySessionService
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from agent_kit.ontology.loader import OntologyLoader

# Setup
ontology = OntologyLoader("assets/ontologies/business.ttl")
session_backend = SqliteSessionService("sessions.db")
session_service = OntologySessionService(session_backend, ontology)
event_logger = OntologyEventLogger(ontology)

# Use in orchestrator
session_id = "session_001"
event_logger.start_tracking(session_id)

# ... agent executes ...
result = agent.run(task)

# Create and store event
event = event_logger.create_event("ForecastAgent", task, result, session_id)
await session_service.append_event(session_id, event)
```

---

## References

- **Full Analysis**: [ADK_INTEGRATION_RECOMMENDATIONS.md](ADK_INTEGRATION_RECOMMENDATIONS.md)
- **ADK Docs**: https://github.com/google/adk-python
- **Implementation**: `src/agent_kit/events/` (✅ Started)

---

**Next Action**: Review recommendations doc and create GitHub issues for Phase 1.

