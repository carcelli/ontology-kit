# Consolidation Action Plan

**Goal**: Reduce complexity from 6/10 to 4/10 by consolidating agent creation patterns.

---

## Immediate Fixes (This Week)

### 1. Migrate Direct Instantiations to Factory

**Found in:**
- `examples/04_orchestrated_agents.py` (lines 40-41)
- `examples/05_hybrid_orchestration.py` (lines 38, 87)
- `examples/money_making_agents_demo.py` (lines 85, 162)
- `examples/grok_agent_demo.py` (line 130)

**Before:**
```python
# ❌ Direct instantiation
forecast_agent = ForecastAgent()
optimizer_agent = OptimizerAgent()
```

**After:**
```python
# ✅ Factory pattern
factory = AgentFactory()
forecast_agent = factory.create_agent("ForecastAgent", domain="business")
optimizer_agent = factory.create_agent("OptimizerAgent", domain="business")
```

**Impact**: Reduces creation paths from 3 to 1.

---

### 2. Consolidate Orchestrator Creation

**Found in:** `examples/04_orchestrated_agents.py`

**Before:**
```python
# ❌ Manual orchestrator setup
orchestrator = OntologyOrchestrator(str(ontology_path))
orchestrator.register_agent("forecaster", ForecastAgent())
orchestrator.register_agent("optimizer", OptimizerAgent())
```

**After:**
```python
# ✅ Factory creates orchestrator with specialists
factory = AgentFactory()
orchestrator = factory.create_orchestrator("business")
# Specialists already registered via domain config
```

**Impact**: Removes manual registration step.

---

### 3. Choose One Integration Path

**Current state**: Both BaseAgent-first AND SDK-first coexist.

**Decision needed**: Which do you prefer?

**Option A: BaseAgent-First** (Recommended - you already have this working)
```python
# BaseAgent is the foundation
class BaseAgent:
    def run(self, task: AgentTask) -> AgentResult:
        # Your lifecycle
        
# SDK Agent wraps BaseAgent when needed
class OntologyAgentAdapter:
    def __init__(self, base_agent: BaseAgent):
        self.base = base_agent
        self.sdk_agent = self._wrap_for_sdk()
```

**Option B: SDK-First** (If you want OpenAI SDK features)
```python
# SDK Agent is the foundation
class BaseAgent(Agent):  # Inherit from SDK Agent
    def __init__(self, ...):
        super().__init__(...)
        self._enhance_with_ontology()
```

**Recommendation**: Option A (less refactoring, you control the lifecycle).

---

## Short-term Fixes (This Month)

### 4. Complete SPARQL Routing

**Current:** Heuristic keyword matching  
**Target:** Ontology-driven SPARQL queries

**File:** `src/agent_kit/agents/orchestrator.py` (line 136)

**Before:**
```python
def _route_via_ontology(self, goal: str) -> list[str]:
    # Heuristic routing
    if "forecast" in goal_lower:
        specialists.append("ForecastAgent")
```

**After:**
```python
def _route_via_ontology(self, goal: str) -> list[str]:
    # SPARQL query for agent capabilities
    sparql = """
        PREFIX core: <http://agent-kit.com/ontology/core#>
        SELECT ?agent WHERE {
            ?agent core:canHandle ?capability .
            ?capability core:matchesGoal ?goal .
            FILTER(CONTAINS(LCASE(?goal), LCASE(""" + goal + """)))
        }
    """
    results = self.ontology.query(sparql)
    # Parse results, return agent names
    # Fallback to heuristic if query fails
```

**Impact**: Makes routing extensible via ontology, not code changes.

---

### 5. Flatten Inheritance Hierarchy

**Current:** BaseAgent → GrokAgent → AlgoTradingAgent (3 levels)

**Option A: Composition**
```python
class AlgoTradingAgent(BaseAgent):
    def __init__(self, grok_client: GrokClient, ...):
        self.grok = grok_client  # Composition, not inheritance
        super().__init__(...)
```

**Option B: Mixin Pattern**
```python
class GrokMixin:
    """Mixin for Grok capabilities."""
    def __init__(self, grok_config, ...):
        self.grok_client = GrokClient(grok_config)
    
class AlgoTradingAgent(BaseAgent, GrokMixin):
    def __init__(self, ...):
        BaseAgent.__init__(self, ...)
        GrokMixin.__init__(self, grok_config, ...)
```

**Recommendation**: Option A (simpler, clearer dependencies).

---

### 6. Unify Tool Loading

**Current:** Tools come from 3 places:
1. Constructor arguments
2. Domain config (`allowed_tools`)
3. Adapter filtering

**Target:** Single source of truth

**Fix:**
```python
# In AgentFactory._create_specialists()
tools = self._load_tools(cfg.allowed_tools)  # From domain config
specialist = agent_class(
    tools=tools,  # Always inject from config
    **agent_kwargs
)
```

**Impact**: Predictable tool availability, easier debugging.

---

## Long-term Improvements (Next Quarter)

### 7. Add Observability

**Track:**
- Agent creation (which factory method, which domain)
- Routing decisions (why this agent was chosen)
- Handoffs (when/why agents hand off)

**Implementation:**
```python
# In AgentFactory
def create_agent(self, ...):
    logger.info("agent.created", {
        "agent_name": agent_name,
        "domain": domain,
        "method": "factory",
        "timestamp": datetime.now()
    })
```

### 8. Version SharedContext

**Current:** Simple dict, no thread safety

**Enhance:**
```python
class SharedContext:
    def __init__(self):
        self._data: dict[str, Any] = {}
        self._lock = threading.Lock()  # Thread safety
        self._version = 0  # Version tracking
    
    def set(self, key: str, value: Any):
        with self._lock:
            self._data[key] = value
            self._version += 1
```

**Or remove if unused** (check usage first).

---

## Success Metrics

After consolidation, you should be able to answer:

1. ✅ **How do I create an agent?** → `factory.create_agent(...)`
2. ✅ **Where do tools come from?** → Domain config → Factory → Agent
3. ✅ **How does routing work?** → SPARQL query → fallback to heuristic
4. ✅ **What's the agent lifecycle?** → Observe → Plan → Act → Reflect
5. ✅ **How do agents coordinate?** → Orchestrator via handoffs

**Target complexity score: 4/10** (down from 6/10)

---

## Checklist

- [ ] Week 1: Migrate all direct instantiations to Factory
- [ ] Week 1: Update examples to use Factory
- [ ] Week 2: Choose integration path (BaseAgent-first OR SDK-first)
- [ ] Week 2: Flatten inheritance (composition over inheritance)
- [ ] Week 3: Implement SPARQL routing
- [ ] Week 3: Unify tool loading
- [ ] Week 4: Add observability hooks
- [ ] Week 4: Audit SharedContext usage (enhance or remove)

---

## Questions to Answer Before Scaling

1. **Do you need both GrokAgent and OntologyAgent?**
   - If yes: Document the difference clearly
   - If no: Remove one

2. **Is SharedContext actually used?**
   - Check: `grep -r "SharedContext" src/ examples/`
   - If unused: Remove it
   - If used: Enhance with thread safety

3. **How many domains will you have?**
   - If <10: Current design is fine
   - If >10: Consider domain registry optimization

4. **Do you need IndustryAgentBuilder?**
   - If Factory can handle custom industries: Remove Builder
   - If Builder adds value: Make it use Factory internally

---

## Run Audit Script

```bash
python scripts/audit_complexity.py
```

This will show you exactly where agents are created outside the Factory pattern.
