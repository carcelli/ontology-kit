# Integration Map: How Components Connect

**Quick reference for understanding data flow and component interactions.**

---

## 🔄 Data Flow: User Request → Result

```
User Request (CLI/API)
    │
    ▼
┌─────────────────────────────────────┐
│  CLI (cli.py)                       │
│  • Parses command                   │
│  • Creates AppContext                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  AgentFactory (factories/)         │
│  • Loads domain config (YAML)       │
│  • Instantiates specialists         │
│  • Loads tools dynamically         │
│  • Creates orchestrator             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  OntologyOrchestratorAgent          │
│  (agents/orchestrator.py)           │
│  • Routes via ontology              │
│  • Checks policies                  │
│  • Executes specialists             │
└──────────────┬──────────────────────┘
               │
               ├──► ForecastAgent ────► tools/business.py ──► predict()
               │
               ├──► OptimizerAgent ───► tools/business.py ──► optimize()
               │
               ├──► AlgoTradingAgent ─► tools/trading_tools.py
               │
               └──► PropBettingAgent ─► tools/betting_tools.py
               │
               ▼
┌─────────────────────────────────────┐
│  Result Aggregation                 │
│  • Combines specialist outputs      │
│  • Validates against schema         │
│  • Applies post-execution policies  │
└──────────────┬──────────────────────┘
               │
               ▼
         Structured Result
    (Pydantic Model / JSON)
```

---

## 🧩 Component Interaction Matrix

| Component | Interacts With | Purpose |
|-----------|---------------|---------|
| **CLI** | Factory, Registry, Collector | Entry point, command parsing |
| **AgentFactory** | Domain Registry, Ontology Loader, Agent Classes | Creates agents/orchestrators |
| **Orchestrator** | Specialists, Tools, Ontology, Schemas | Coordinates execution |
| **BaseAgent** | Tools, Shared Context | Executes tasks |
| **Tools** | Vectorspace, Ontology, ML Libraries | Provides capabilities |
| **OntologyLoader** | RDFLib, TTL Files | Loads knowledge graphs |
| **Domain Registry** | YAML Configs | Manages domain configs |
| **Schemas** | Pydantic | Validates outputs |
| **Circuit Breaker** | Agents, Tools | Prevents failures |
| **Data Collector** | Agents | Tracks performance |

---

## 🔗 Dependency Graph (Simplified)

```
┌─────────────┐
│     CLI     │
└──────┬──────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│   Factory   │   │  Registry   │
└──────┬──────┘   └─────────────┘
       │
       ├──────────────┬──────────────┐
       │              │              │
       ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Orchestrator│ │  Ontology   │ │   Tools     │
└──────┬──────┘ └─────────────┘ └──────┬──────┘
       │                                │
       ├──────────────┬────────────────┘
       │              │
       ▼              ▼
┌─────────────┐ ┌─────────────┐
│ Specialists │ │  Vectorspace │
└─────────────┘ └─────────────┘
```

---

## 🎯 Common Integration Scenarios

### Scenario 1: Business Forecasting

```
User: "Forecast revenue for next 30 days"
    │
    ├─► CLI parses command
    ├─► Factory creates BusinessOrchestrator
    ├─► Orchestrator routes to ForecastAgent
    ├─► ForecastAgent calls tools/business.predict()
    ├─► Tool uses ML models (via ml_training.py)
    ├─► Result validated against ForecastResult schema
    └─► Structured output returned
```

### Scenario 2: Leverage Analysis

```
User: "Find leverage points for Revenue"
    │
    ├─► CLI routes to ML workflow
    ├─► Calls tools/semantic_graph.build_semantic_graph()
    ├─► Calls tools/ml_training.analyze_leverage()
    ├─► Uses vectorspace for embeddings
    ├─► Generates leverage scores
    ├─► Calls tools/semantic_graph.compute_target_leverage()
    └─► Returns ranked interventions
```

### Scenario 3: Multi-Domain Workflow

```
User: "Forecast revenue, then find betting edges"
    │
    ├─► CLI creates workflow
    ├─► Step 1: BusinessOrchestrator → ForecastAgent
    ├─► Step 2: BettingOrchestrator → PropBettingAgent
    ├─► Results aggregated
    └─► Combined output saved
```

---

## 🔌 Tool Integration Points

### How Tools Are Discovered

1. **Static Registration**: Tools exported in `tools/__init__.py`
2. **Domain Config**: Listed in `domains/*.yaml` → `allowed_tools`
3. **Dynamic Loading**: Factory uses `importlib` to load tools
4. **Ontology Discovery**: `OntologyOrchestrator` queries ontology for tools

### How Tools Are Invoked

1. **Direct Call**: Agent calls tool function directly
2. **Via Decorator**: `@function_tool` (OpenAI SDK integration)
3. **Via Registry**: Lookup in `ML_TOOL_REGISTRY` or similar
4. **Via Orchestrator**: Orchestrator filters tools before passing to agents

---

## 🛡️ Safety & Validation Layers

```
User Input
    │
    ├─► OntologyInputGuardrail (validates against ontology)
    │
    ├─► Pre-execution Policies (orchestrator checks)
    │
    ├─► Circuit Breaker (monitors error rates)
    │
    ├─► Agent Execution (with error handling)
    │
    ├─► Post-execution Policies (orchestrator validates)
    │
    ├─► OntologyOutputGuardrail (validates output)
    │
    ├─► Pydantic Schema Validation (type checking)
    │
    └─► Structured Output
```

---

## 📦 Module Import Hierarchy

```
Top Level (CLI/API)
    │
    ├─► agent_kit.factories.agent_factory
    │     ├─► agent_kit.agents.*
    │     ├─► agent_kit.domains.registry
    │     ├─► agent_kit.ontology.loader
    │     └─► agent_kit.tools.*
    │
    ├─► agent_kit.cli
    │     └─► agent_kit.factories.agent_factory
    │
    └─► agent_kit.interactive_dashboard
          └─► agent_kit.data_collection
```

---

## 🎨 Design Patterns Used

| Pattern | Location | Purpose |
|---------|----------|---------|
| **Factory** | `factories/agent_factory.py` | Creates agents/orchestrators |
| **Mediator** | `agents/orchestrator.py` | Coordinates specialists |
| **Template Method** | `agents/base.py` | Defines agent lifecycle |
| **Adapter** | `adapters/*.py` | Bridges external SDKs |
| **Registry** | `domains/registry.py` | Manages domain configs |
| **Circuit Breaker** | `monitoring/circuit_breaker.py` | Prevents cascading failures |
| **Builder** | `factories/agent_factory.py` (IndustryAgentBuilder) | Constructs custom agents |

---

## 🚦 Entry Points

1. **CLI**: `ontology-kit orchestrate run --domain business --goal "..."` 
2. **Python API**: `AgentFactory().create_orchestrator("business").run(task)`
3. **Interactive Mode**: `ontology-kit interactive`
4. **Web Dashboard**: `InteractiveDashboard.generate_full_dashboard()`

---

**Use this map to understand how to extend the system or debug integration issues.**
