# ADK Python Integration Recommendations

**Date**: 2025-01-XX  
**Status**: 📋 Analysis Complete  
**Goal**: Identify high-value ADK components to integrate into ontology-kit

> **📌 Update**: See [UNIFIED_SDK_INTEGRATION_STRATEGY.md](UNIFIED_SDK_INTEGRATION_STRATEGY.md) for integration with both ADK and OpenAI Agents SDK.

---

## Executive Summary

ADK Python provides **production-grade infrastructure** that complements ontology-kit's domain expertise. Key opportunities:

1. **Event System** (🔴 High Priority) - Conversation tracking & observability
2. **Session Management** (🔴 High Priority) - Multi-backend persistence
3. **Memory Service** (🟡 Medium Priority) - Long-term recall across sessions
4. **Evaluation Framework** (🟡 Medium Priority) - Systematic agent testing
5. **Runner Architecture** (🟢 Low Priority) - Stateless orchestration patterns
6. **Tool Ecosystem** (🟢 Low Priority) - MCP, OpenAPI, Google API integrations

**Integration Strategy**: Adapter pattern—wrap ADK services behind ontology-kit interfaces to maintain domain-first architecture.

---

## 1. Event System (🔴 High Priority)

### What ADK Provides

```python
# ADK Event structure
class Event(LlmResponse):
    invocation_id: str
    author: str  # 'user' or agent name
    actions: EventActions  # Function calls, responses, etc.
    branch: Optional[str]  # For multi-agent isolation
    timestamp: float
    id: str
```

**Key Features:**
- Immutable event log for full conversation history
- Branch isolation (agent_1.agent_2.agent_3) for parallel execution
- Function call/response tracking
- Event compaction for context window management
- Streaming support (`run_live()`)

### Current Gap in Ontology-Kit

- No structured event logging
- Conversation history not persisted
- No observability for agent decisions
- Hard to debug multi-agent workflows

### Integration Approach

**Option A: Lightweight Wrapper** (Recommended)
```python
# src/agent_kit/events/ontology_event.py
from google.adk.events.event import Event as ADKEvent
from agent_kit.ontology.loader import OntologyLoader

class OntologyEvent(ADKEvent):
    """Event enriched with ontology context."""
    
    ontology_triples: list[dict] = Field(default_factory=list)
    """SPARQL queries executed during this event"""
    
    leverage_scores: dict[str, float] = Field(default_factory=dict)
    """Leverage analysis results if applicable"""
    
    @classmethod
    def from_agent_action(
        cls,
        agent: BaseAgent,
        action: AgentActionResult,
        ontology: OntologyLoader,
    ) -> "OntologyEvent":
        """Create event from agent action with ontology context."""
        # Extract SPARQL queries from action
        # Compute leverage scores if domain is business
        # Return enriched event
```

**Option B: Full Integration**
- Replace `AgentResult` with `Event` as primary data structure
- Requires refactoring orchestrator and all agents
- Higher risk, higher reward

### Benefits

✅ **Observability**: Track every agent decision with full context  
✅ **Debugging**: Replay conversations to diagnose failures  
✅ **Analytics**: Measure agent performance over time  
✅ **Compliance**: Audit trail for financial decisions (betting/trading)

### Implementation Effort

- **Option A**: 2-3 days (wrapper + integration)
- **Option B**: 1-2 weeks (full refactor)

---

## 2. Session Management (🔴 High Priority)

### What ADK Provides

**Multiple Backends:**
- `InMemorySessionService` - Development/testing
- `SqliteSessionService` - Local persistence
- `VertexAISessionService` - Cloud-managed
- `DatabaseSessionService` - Spanner/PostgreSQL

**Key Features:**
- Session retrieval by ID
- Event appending with automatic ID generation
- Event compaction (summarize old events)
- Thread-safe operations
- Async/await support

### Current Gap in Ontology-Kit

- No session persistence
- Each run is stateless
- Can't resume interrupted workflows
- No conversation history across invocations

### Integration Approach

```python
# src/agent_kit/sessions/ontology_session_service.py
from google.adk.sessions.base_session_service import BaseSessionService
from google.adk.sessions.session import Session
from agent_kit.ontology.loader import OntologyLoader

class OntologySessionService(BaseSessionService):
    """Session service that enriches events with ontology context."""
    
    def __init__(
        self,
        backend: BaseSessionService,  # Delegate to ADK backend
        ontology: OntologyLoader,
    ):
        self.backend = backend
        self.ontology = ontology
    
    async def get_session(self, session_id: str) -> Session:
        """Retrieve session and enrich with ontology queries."""
        session = await self.backend.get_session(session_id)
        # Optionally: Query ontology for related entities
        return session
    
    async def append_event(self, session_id: str, event: Event) -> None:
        """Append event and update ontology with new knowledge."""
        await self.backend.append_event(session_id, event)
        # Extract entities from event and add to ontology
        await self._update_ontology_from_event(event)
```

### Benefits

✅ **Resumability**: Continue workflows after interruption  
✅ **Multi-turn Conversations**: Build context over time  
✅ **Production Ready**: Battle-tested backends (Spanner, Vertex AI)  
✅ **Scalability**: Cloud backends handle high concurrency

### Implementation Effort

- **Wrapper**: 1-2 days
- **Full Integration**: 3-5 days (including testing)

---

## 3. Memory Service (🟡 Medium Priority)

### What ADK Provides

**Memory Services:**
- `InMemoryMemoryService` - Development
- `VertexAIRagMemoryService` - RAG-based recall
- `VertexAIMemoryBankService` - Structured memory bank

**Key Features:**
- Ingest sessions into long-term memory
- Semantic search across past conversations
- User-scoped memory (per `user_id`)
- Automatic embedding and indexing

### Current Gap in Ontology-Kit

- `OntologyMemorySession` exists but is basic
- No cross-session recall
- No semantic search over conversation history
- Memory not integrated with agent execution

### Integration Approach

```python
# src/agent_kit/memory/ontology_memory_service.py
from google.adk.memory.base_memory_service import BaseMemoryService
from agent_kit.ontology.loader import OntologyLoader

class OntologyMemoryService(BaseMemoryService):
    """Memory service that uses ontology for entity-aware recall."""
    
    def __init__(
        self,
        backend: BaseMemoryService,  # ADK RAG service
        ontology: OntologyLoader,
    ):
        self.backend = backend
        self.ontology = ontology
    
    async def search_memory(
        self,
        *,
        app_name: str,
        user_id: str,
        query: str,
    ) -> SearchMemoryResponse:
        """Search memory with ontology-enhanced query expansion."""
        # 1. Extract entities from query using SPARQL
        entities = self.ontology.extract_entities(query)
        
        # 2. Expand query with related concepts
        expanded_query = self._expand_with_ontology(query, entities)
        
        # 3. Search ADK memory service
        results = await self.backend.search_memory(
            app_name=app_name,
            user_id=user_id,
            query=expanded_query,
        )
        
        # 4. Rank results by ontology relevance
        ranked = self._rank_by_ontology_relevance(results, entities)
        return ranked
```

### Benefits

✅ **Context Awareness**: Agents remember past conversations  
✅ **Entity Linking**: Connect queries to ontology entities  
✅ **RAG Integration**: Leverage ADK's RAG infrastructure  
✅ **User Personalization**: Per-user memory banks

### Implementation Effort

- **Wrapper**: 2-3 days
- **Full Integration**: 1 week (including ontology query expansion)

---

## 4. Evaluation Framework (🟡 Medium Priority)

### What ADK Provides

**Comprehensive Testing Infrastructure:**
- `EvalSet` - Test case collections
- `AgentEvaluator` - Run evaluations
- `LLMAsJudge` - Automated scoring
- `RubricBasedEvaluator` - Structured criteria
- `TrajectoryEvaluator` - Multi-turn analysis
- `SafetyEvaluator` - Content safety checks

**Key Features:**
- JSON-based test cases
- Multiple evaluators (LLM-as-judge, rubric, trajectory)
- Metrics: correctness, safety, tool use quality
- Integration with Vertex AI Evaluation
- Local and cloud backends

### Current Gap in Ontology-Kit

- No systematic evaluation framework
- Manual testing only
- No regression testing
- Can't measure agent improvements over time

### Integration Approach

```python
# src/agent_kit/evaluation/ontology_evaluator.py
from google.adk.evaluation.agent_evaluator import AgentEvaluator
from agent_kit.schemas import BusinessOptimizationResult

class OntologyEvaluator(AgentEvaluator):
    """Evaluator that validates ontology consistency."""
    
    def evaluate(
        self,
        agent: BaseAgent,
        eval_set: EvalSet,
    ) -> EvalResult:
        """Run evaluation with ontology validation."""
        # 1. Run standard ADK evaluation
        result = await super().evaluate(agent, eval_set)
        
        # 2. Validate outputs against ontology
        for case_result in result.case_results:
            if case_result.output:
                self._validate_ontology_compliance(case_result.output)
        
        # 3. Check SPARQL query correctness
        self._validate_sparql_queries(result)
        
        return result
    
    def _validate_ontology_compliance(self, output: dict) -> None:
        """Ensure output entities exist in ontology."""
        # Extract entities from output
        # Query ontology to verify existence
        # Flag violations
```

### Benefits

✅ **Regression Testing**: Catch breaking changes  
✅ **Quality Metrics**: Measure agent performance  
✅ **Automated Scoring**: LLM-as-judge for subjective criteria  
✅ **Domain Validation**: Ensure outputs match ontology schema

### Implementation Effort

- **Basic Integration**: 2-3 days
- **Full Integration with Ontology Validation**: 1 week

---

## 5. Runner Architecture (🟢 Low Priority)

### What ADK Provides

**Stateless Orchestration Engine:**
- `Runner.run_async()` - Async execution
- `Runner.run_live()` - Bi-directional streaming
- `Runner.run()` - Synchronous execution
- Event streaming during execution
- Automatic event compaction
- Plugin system integration

### Current Gap in Ontology-Kit

- `OntologyOrchestratorAgent` is stateful
- No streaming support
- No event compaction
- Manual orchestration logic

### Integration Approach

**Option A: Pattern Adoption** (Recommended)
- Study ADK's stateless design
- Refactor `OntologyOrchestratorAgent` to be stateless
- Add event streaming to orchestrator
- Keep ontology-first architecture

**Option B: Full Replacement**
- Replace orchestrator with ADK Runner
- Wrap agents as ADK-compatible
- Higher risk, requires significant refactoring

### Benefits

✅ **Scalability**: Stateless design enables horizontal scaling  
✅ **Streaming**: Real-time updates for long-running tasks  
✅ **Event Compaction**: Manage context window limits  
✅ **Production Patterns**: Battle-tested orchestration

### Implementation Effort

- **Pattern Adoption**: 1-2 weeks
- **Full Replacement**: 3-4 weeks (high risk)

---

## 6. Tool Ecosystem (🟢 Low Priority)

### What ADK Provides

**Tool Integrations:**
- `MCPTool` - Model Context Protocol
- `OpenAPITool` - OpenAPI spec integration
- `GoogleAPITool` - Google API discovery
- `LangChainTool` - LangChain compatibility
- `CrewAITool` - CrewAI integration
- `BigQueryTool`, `SpannerTool` - Database tools

### Current Gap in Ontology-kit

- Basic tool registry exists
- No MCP integration (though `OntologyMCPToolFilter` exists)
- No OpenAPI tool generation
- Manual tool registration

### Integration Approach

```python
# src/agent_kit/tools/adk_tool_adapter.py
from google.adk.tools.mcp_tool import MCPTool
from agent_kit.ontology.loader import OntologyLoader

class OntologyMCPTool(MCPTool):
    """MCP tool filtered by ontology rules."""
    
    def __init__(
        self,
        mcp_server: str,
        ontology: OntologyLoader,
        domain: str,
    ):
        super().__init__(mcp_server)
        self.ontology = ontology
        self.domain = domain
    
    async def call(self, tool_name: str, **kwargs) -> Any:
        """Call MCP tool if allowed by ontology."""
        # Check if tool is allowed for domain
        if not self._is_tool_allowed(tool_name):
            raise ValueError(f"Tool {tool_name} not allowed for domain {self.domain}")
        
        return await super().call(tool_name, **kwargs)
```

### Benefits

✅ **Tool Discovery**: Auto-discover tools from OpenAPI specs  
✅ **MCP Integration**: Standard protocol for tool communication  
✅ **Google APIs**: Access to Google Cloud services  
✅ **Reduced Boilerplate**: Less manual tool registration

### Implementation Effort

- **MCP Integration**: 2-3 days
- **OpenAPI Integration**: 3-5 days
- **Full Tool Ecosystem**: 1-2 weeks

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
1. ✅ **Event System** - Integrate ADK events with ontology context
2. ✅ **Session Management** - Add SQLite backend for local development

**Deliverables:**
- `OntologyEvent` wrapper
- `OntologySessionService` adapter
- Updated orchestrator to emit events

### Phase 2: Observability (Week 3-4)
3. ✅ **Memory Service** - Cross-session recall with ontology enhancement
4. ✅ **Evaluation Framework** - Basic test infrastructure

**Deliverables:**
- `OntologyMemoryService` wrapper
- Evaluation test cases for business domain
- CI integration for regression testing

### Phase 3: Production Readiness (Week 5-6)
5. ✅ **Cloud Backends** - Vertex AI session/memory services
6. ✅ **Tool Ecosystem** - MCP and OpenAPI integration

**Deliverables:**
- Production session backend
- MCP tool filtering
- Documentation and examples

---

## Design Principles

### 1. Ontology-First Architecture
- ADK services are **infrastructure**, not the foundation
- Ontology remains the source of truth for domain knowledge
- ADK components are wrapped, not replaced

### 2. Adapter Pattern
- Thin wrappers around ADK services
- Enrich ADK events/results with ontology context
- Maintain backward compatibility with existing code

### 3. Gradual Migration
- Start with event system (low risk, high value)
- Add session management incrementally
- Keep existing orchestrator until Runner integration is proven

### 4. Domain-Specific Enhancements
- Every ADK component gets ontology-aware wrapper
- SPARQL queries logged in events
- Leverage scores computed and stored
- Entity extraction from conversations

---

## Risk Assessment

### Low Risk ✅
- **Event System**: Additive, doesn't break existing code
- **Session Management**: Optional, can run without it
- **Evaluation Framework**: Separate testing infrastructure

### Medium Risk ⚠️
- **Memory Service**: May require refactoring agent interfaces
- **Tool Ecosystem**: Could introduce dependency conflicts

### High Risk 🔴
- **Runner Replacement**: Would require full orchestrator rewrite
- **Full ADK Migration**: Loses ontology-first architecture

---

## Recommendations

### Immediate Actions (This Sprint)
1. **Integrate Event System** - Highest ROI, lowest risk
2. **Add Session Management** - Enables multi-turn conversations
3. **Create Evaluation Test Cases** - Establish baseline metrics

### Next Quarter
4. **Memory Service Integration** - Enable long-term recall
5. **Cloud Backend Support** - Production scalability
6. **Tool Ecosystem Expansion** - MCP and OpenAPI

### Future Considerations
7. **Runner Pattern Adoption** - Study stateless design
8. **Full ADK Migration** - Only if ontology-first proves limiting

---

## References

- [ADK Python Documentation](https://github.com/google/adk-python)
- [ADK Architecture Overview](https://github.com/google/adk-python/blob/main/contributing/adk_project_overview_and_architecture.md)
- [Ontology-Kit Architecture Decision](docs/guides/ARCHITECTURE_DECISION.md)

---

**Status**: ✅ Ready for implementation  
**Next Step**: Create GitHub issues for Phase 1 tasks

