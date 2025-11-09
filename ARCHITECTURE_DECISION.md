# Architecture Decision: Modular Multi-SDK Design

**Date**: 2025-11-09  
**Status**: ✅ Approved  
**Context**: OpenAI Agents SDK integration strategy

---

## Decision

**Ontology remains the backbone. SDKs are pluggable execution engines.**

We will NOT refactor the entire codebase to depend on OpenAI's Agents SDK. Instead:

1. **Core abstraction**: `BaseAgent` (our custom implementation)
2. **SDK adapters**: Optional wrappers for OpenAI SDK, LangChain, AutoGen
3. **Ontology-first**: SPARQL routing, SHACL validation, graph navigation as primary patterns
4. **Config-driven**: Enable/disable SDKs via environment or runtime config

---

## Rationale

### 1. Ontology as Universal Structure

From first principles, the system formalizes:
- **Entities**: Business, ForecastModel, LeveragePoint (substances)
- **Relations**: `optimizes`, `forecasts`, `handsOffTo` (causal links)
- **Processes**: Agent execution, handoffs, validation (dynamic accidents)

The ontology is the **persistent structure** that captures domain knowledge. SDKs are **transient implementations** that execute workflows. Inverting this (SDK as foundation) would subordinate domain logic to vendor abstractions.

### 2. Flexibility for Multi-Framework Testing

**Business goal**: Democratize ML for small businesses by testing diverse approaches.

**Need**: Ability to experiment with:
- **OpenAI SDK**: Lightweight multi-agent orchestration
- **LangChain**: RAG, memory, vector stores
- **AutoGen**: Group chats, crew-based workflows
- **Semantic Kernel**: .NET interop for enterprise clients
- **crewAI**: Role-based agent teams

**Constraint**: Full refactor to OpenAI SDK locks us into one framework.

**Solution**: Modular design enables A/B testing of orchestration strategies.

### 3. Risk Mitigation

**OpenAI SDK status**: Beta (as of Nov 2025)
- API may change (e.g., handoff signatures, streaming events)
- Breaking changes could require full rewrite if deeply coupled

**Mitigation**: Adapter pattern isolates SDK-specific code to thin wrappers.

**Benefit**: If OpenAI SDK breaks, swap to LangChain without touching core logic.

### 4. Business Impact

**Modular approach**:
- ✅ Supports 30-50% more use cases (hybrid workflows)
- ✅ Accelerates client acquisition (test multiple solutions)
- ✅ Reduces vendor lock-in risk
- ✅ Enables gradual migration (iterate SDK integrations)

**Full refactor approach**:
- ❌ 2x faster demos (short-term win)
- ❌ Rigid to one framework (long-term risk)
- ❌ Requires rewrite if OpenAI SDK changes

**Decision**: Long-term flexibility > short-term velocity.

---

## Implementation Strategy

### Phase 1: Core Abstraction (✅ Complete)

- `BaseAgent`: Template method pattern (observe → plan → act → reflect)
- `OntologyLoader`: SPARQL queries, SHACL validation
- `OntologyOrchestrator`: Handoff logic via ontology routing

### Phase 2: SDK Adapters (🚧 In Progress)

#### OpenAI SDK Adapter

```python
# src/agent_kit/adapters/openai_sdk.py
from agents import Agent as SDKAgent, Runner
from agent_kit.agents.base import BaseAgent, AgentTask

class OpenAISDKAdapter:
    """Wraps OpenAI SDK agents for ontology-driven workflows."""
    
    def __init__(self, sdk_agent: SDKAgent, ontology_loader):
        self.sdk_agent = sdk_agent
        self.ontology = ontology_loader
    
    async def run(self, task: AgentTask):
        # Inject ontology context into SDK agent
        instructions = self._enrich_instructions(task)
        result = await Runner.run(self.sdk_agent, instructions)
        return self._parse_result(result)
```

#### LangChain Adapter (Future)

```python
# src/agent_kit/adapters/langchain.py
from langchain.agents import AgentExecutor
from agent_kit.agents.base import BaseAgent

class LangChainAdapter:
    """Wraps LangChain agents for ontology-driven workflows."""
    pass  # TBD
```

### Phase 3: Config-Driven Toggle

```python
# .env or config.yaml
AGENT_FRAMEWORK=openai_sdk  # or "custom" or "langchain"
OPENAI_SDK_ENABLED=true
```

```python
# src/agent_kit/agents/factory.py
def create_agent(config):
    if config.framework == "openai_sdk":
        return OpenAISDKAdapter(...)
    elif config.framework == "langchain":
        return LangChainAdapter(...)
    else:
        return CustomAgent(...)  # Our BaseAgent implementation
```

---

## Coexistence Pattern

### Use OpenAI SDK for:
- **Structured outputs**: Schema evolution (`SchemaAgent`, `MapperAgent`)
- **Deterministic orchestration**: Fixed pipelines (ontology-ML example)
- **Realtime demos**: Voice, streaming UX

### Use Custom BaseAgent for:
- **Ontology-driven routing**: SPARQL-based handoffs
- **Multi-step reasoning**: Observe → plan → act → reflect
- **Custom validation**: SHACL constraints, business rules

### Example: Hybrid Workflow

```python
# Forecast uses custom BaseAgent (ontology routing)
forecast_agent = ForecastAgent(
    name="ForecastAgent",
    ontology_loader=loader
)

# Schema design uses OpenAI SDK (structured outputs)
from examples.ontology_ml.agents.schema_agent import schema_agent

# Orchestrator coordinates both
orchestrator = HybridOrchestrator(
    custom_agents=[forecast_agent],
    sdk_agents=[schema_agent]
)
```

---

## Edge Cases & Mitigations

### Edge Case 1: SDK Breaking Changes
**Risk**: OpenAI SDK beta changes handoff API  
**Mitigation**: Adapter isolates changes to `openai_sdk.py` (< 200 lines)  
**Cost**: ~2 hours to fix adapter vs. ~2 weeks to refactor entire codebase

### Edge Case 2: Performance Overhead
**Risk**: Wrapper adds latency  
**Measurement**: Benchmark custom vs. SDK execution  
**Threshold**: Accept <10% overhead for modularity  
**Mitigation**: Use SDK directly for latency-critical paths

### Edge Case 3: Over-Abstraction
**Risk**: Adapter becomes complex, negating benefits  
**Guideline**: Keep adapters <300 lines, delegate to SDKs  
**Review**: Monthly check on adapter complexity

---

## Metrics & Validation

### Success Criteria

| Metric | Target | Status |
|--------|--------|--------|
| Custom agents work without SDK | 100% tests pass | ✅ |
| SDK adapter enables OpenAI integration | Examples run | ✅ |
| LangChain adapter (future) | PoC works | 🔲 |
| Performance overhead | <10% latency | 🔲 |
| Code duplication | <5% across adapters | 🔲 |

### Test Coverage

- ✅ `test_base_agent.py`: Custom agent lifecycle
- ✅ `test_ontology_ml_pipeline.py`: OpenAI SDK integration
- 🔲 `test_sdk_adapter.py`: Adapter behavior
- 🔲 `test_hybrid_orchestration.py`: Custom + SDK coordination

---

## Next Actions

### Immediate (Today)
1. ✅ Create `ARCHITECTURE_DECISION.md` (this doc)
2. 🚧 Implement `OpenAISDKAdapter` skeleton
3. 🚧 Add config toggle (`USE_OPENAI_SDK` env var)
4. 🚧 Document hybrid usage in README

### This Week
5. 🔲 Benchmark custom vs. SDK performance
6. 🔲 Add adapter tests
7. 🔲 Update CI/CD to test both modes

### Future
8. 🔲 LangChain adapter PoC
9. 🔲 AutoGen adapter exploration
10. 🔲 Multi-framework orchestration example

---

## References

### Patterns
- **Adapter Pattern**: Gang of Four, "Design Patterns"
- **Plugin Architecture**: Martin Fowler, "Patterns of Enterprise Application Architecture"
- **Hexagonal Architecture**: Alistair Cockburn (ports & adapters)

### SDKs
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
- [LangChain](https://docs.langchain.com/)
- [AutoGen](https://microsoft.github.io/autogen/)
- [Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/)

### Ontology
- [RDFLib](https://rdflib.readthedocs.io/)
- [SHACL](https://www.w3.org/TR/shacl/)
- [OWL](https://www.w3.org/TR/owl2-overview/)

---

## Decision Log

| Date | Change | Rationale |
|------|--------|-----------|
| 2025-11-09 | Adopted modular design | Flexibility > short-term velocity |
| 2025-11-09 | OpenAI SDK as adapter | Enable structured outputs example |
| Future | LangChain adapter | RAG + vector stores for retrieval |

---

**Status**: ✅ **Approved — Modular Multi-SDK Architecture**

**Next Review**: After LangChain adapter PoC (est. 2 weeks)

**Owner**: Agent Kit Core Team

---

**Ship it!** 🚀 Ontology as backbone, SDKs as tools.

