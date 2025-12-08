# Repository Breakdown: Tools & Agents Architecture

**Purpose**: Comprehensive breakdown of every main file in ontology-kit, showing how tools and agents integrate for future task orchestration.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  ONTOLOGY LAYER (Foundation)                │
│  • RDF/OWL Knowledge Graphs                                  │
│  • SPARQL Queries                                            │
│  • SHACL Validation                                          │
└─────────────────┬───────────────────────────────────────────┘
                  │
    ┌─────────────┴─────────────┬─────────────────────┐
    │                           │                     │
┌───▼────┐   ┌──────────────┐   │   ┌──────────────┐   │
│ Agents │   │    Tools     │   │   │ Orchestrator │   │
│        │   │              │   │   │              │   │
└────────┘   └──────────────┘   │   └──────────────┘   │
                                │                     │
    ┌───────────────────────────┴─────────────────────┐
    │                                                 │
┌───▼──────────────────────────────────────────────┐  │
│         ADAPTERS & INTEGRATIONS                   │  │
│  • OpenAI Agents SDK                              │  │
│  • MCP Servers                                    │  │
│  • Guardrails & Filters                           │  │
└───────────────────────────────────────────────────┘  │
    │                                                 │
    ▼                                                 │
┌─────────────────────────────────────────────────────┘
│         CLI & WEB INTERFACE                          │
│  • Command-line orchestration                        │
│  • Interactive dashboards                            │
│  • Workflow management                               │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Core Components Breakdown

### 1. **AGENTS** (`src/agent_kit/agents/`)

**Purpose**: Specialized agents that execute domain-specific tasks.

#### `base.py` - Foundation
- **`BaseAgent`**: Abstract base class implementing Observe-Plan-Act-Reflect lifecycle
- **Data Models**: `AgentTask`, `AgentObservation`, `AgentPlan`, `AgentActionResult`, `AgentResult`
- **Pattern**: Template Method - defines skeleton algorithm, subclasses implement steps
- **Usage**: All agents inherit from this

#### `orchestrator.py` - Coordination Layer
- **`OntologyOrchestratorAgent`**: Mediator pattern coordinator
- **Responsibilities**:
  - Routes tasks to specialists via ontology queries
  - Enforces pre/post-execution policies
  - Aggregates results from multiple specialists
  - Validates outputs against Pydantic schemas
- **Key Methods**:
  - `_route_via_ontology()`: SPARQL-based routing (currently heuristic-based)
  - `_check_pre_execution_policies()`: Risk checks before execution
  - `_check_post_execution_policies()`: Domain-specific limits (forecast horizon, exposure, drawdown)
  - `_aggregate_results()`: Combines specialist outputs
  - `_structure_output()`: Pydantic validation

#### `business_agents.py` - Business Domain Specialists
- **`ForecastAgent`**: Revenue/metric forecasting
- **`OptimizerAgent`**: Business optimization recommendations
- **Domain**: Small business optimization

#### `algo_trading_agent.py` - Trading Specialist
- **`AlgoTradingAgent`**: Algorithmic trading with technical analysis
- **Features**: Portfolio management, risk metrics, signal generation
- **Integration**: Uses Grok API, ontology for strategy selection

#### `prop_betting_agent.py` - Betting Specialist
- **`PropBettingAgent`**: Sports betting edge detection
- **Features**: Kelly criterion, probability estimation, bankroll management
- **Integration**: Uses Grok API, ontology for betting strategies

#### `grok_agent.py` - LLM Integration
- **`GrokAgent`**: Base class for xAI/Grok API integration
- **`GrokConfig`**: Configuration (API key, temperature, max_tokens)
- **Usage**: Extended by domain-specific agents needing LLM reasoning

#### `ontology_agent.py` - Ontology-Aware Agent
- **`OntologyAgent`**: Agent that queries and manipulates ontologies
- **Use Case**: Semantic reasoning, knowledge graph operations

#### `planner_agent.py` - Planning Specialist
- **Purpose**: Multi-step task planning and decomposition

#### `code_writer_agent.py` - Code Generation
- **Purpose**: Generate code based on specifications

#### `repository_agent.py` - Repository Operations
- **Purpose**: GitHub/code repository interactions

---

### 2. **TOOLS** (`src/agent_kit/tools/`)

**Purpose**: Callable functions that agents invoke during execution. Bridge agents to core capabilities.

#### `__init__.py` - Tool Registry
- **Exports**: All tool functions for agent discovery
- **Categories**:
  - Visualization: `generate_hyperdim_viz`, `generate_hyperdim_leverage_viz`, `generate_interactive_leverage_viz`
  - Business: `predict`, `optimize`
  - ML: `train_model`, `run_cross_validation`, `analyze_leverage`, `cluster_data`, `check_job_status`
  - Ontology: `query_ontology`, `add_ontology_statement`
  - Vector Space: `embed`, `embed_batch`, `query_vector_index`
  - Semantic Graph: `build_semantic_graph`, `compute_target_leverage`, `recommend_interventions`
  - GitHub: `write_to_github`

#### `business.py` - Business Domain Tools
- **`predict()`**: Revenue/metric forecasting
- **`optimize()`**: Business optimization recommendations
- **Integration**: Used by `ForecastAgent` and `OptimizerAgent`

#### `ml_training.py` - ML Workflow Tools
- **`train_model()`**: Train ML models with cross-validation
- **`run_cross_validation()`**: K-fold CV with metrics
- **`analyze_leverage()`**: Compute leverage scores for business terms
- **`cluster_data()`**: Clustering analysis
- **`check_job_status()`**: Async job status checking
- **Registry**: `ML_TOOL_REGISTRY` maps Python identifiers to tool metadata

#### `semantic_graph.py` - Graph Analysis Tools
- **`build_semantic_graph()`**: Create semantic graphs from business entities
- **`compute_target_leverage()`**: Targeted leverage analysis for specific KPIs
- **`recommend_interventions()`**: Generate intervention recommendations
- **Output**: JSON graphs with nodes, edges, centrality metrics

#### `hyperdim_viz.py` - Hyperdimensional Visualization
- **`generate_hyperdim_viz()`**: High-dimensional vector space visualization
- **Use Case**: Embedding visualization, semantic space exploration

#### `hyperdim_leverage_viz.py` - Leverage Visualization
- **`generate_hyperdim_leverage_viz()`**: Visualize leverage points in hyperdimensional space
- **Integration**: Combines leverage analysis with visualization

#### `interactive_viz.py` - Interactive Dashboards
- **`generate_interactive_leverage_viz()`**: Plotly-based interactive visualizations
- **Output**: HTML files with interactive charts

#### `ontology.py` - Ontology Manipulation
- **`query_ontology()`**: Execute SPARQL queries
- **`add_ontology_statement()`**: Add triples to ontology
- **Integration**: Used by ontology-aware agents

#### `vector_space.py` - Vector Operations
- **`embed()`**: Generate embeddings for text
- **`embed_batch()`**: Batch embedding generation
- **`query_vector_index()`**: Semantic search in vector space
- **Backend**: Uses `vectorspace/` module (FAISS, sentence-transformers)

#### `github_tools.py` - GitHub Integration
- **`write_to_github()`**: Write files to GitHub repositories
- **Integration**: MCP server for GitHub operations

#### `repository_tree.py` - Repository Structure
- **Purpose**: Analyze repository structure

#### `tool_registry.py` - Tool Discovery
- **Purpose**: Registry for dynamic tool discovery via ontology

---

### 3. **FACTORIES** (`src/agent_kit/factories/`)

**Purpose**: Dependency injection and agent instantiation.

#### `agent_factory.py` - Agent Factory
- **`AgentFactory`**: Central factory for creating agents and orchestrators
- **Pattern**: Factory + Dependency Injection
- **Key Methods**:
  - `create_orchestrator(domain)`: Creates domain-specific orchestrator with specialists
  - `create_agent(name, domain)`: Creates individual agent
  - `_create_specialists()`: Instantiates specialist agents from config
  - `_load_tools()`: Dynamically loads tools via importlib
  - `_load_ontology()`: Loads ontology by IRI
- **Registry**: `AGENT_REGISTRY` maps agent names to classes
- **`IndustryAgentBuilder`**: Builder for custom industry agents
- **Usage**: Primary entry point for agent creation

---

### 4. **DOMAINS** (`src/agent_kit/domains/`)

**Purpose**: Domain-specific configurations (YAML).

#### `business.yaml` - Business Domain Config
- **Agents**: `ForecastAgent`, `OptimizerAgent`
- **Tools**: Business tools, semantic graph, ML training, ontology, vector space
- **Policies**: Max forecast horizon (90 days), confidence thresholds, leverage requirements
- **Schema**: `BusinessOptimizationResult`

#### `betting.yaml` - Betting Domain Config
- **Agents**: `PropBettingAgent`
- **Tools**: Betting-specific tools
- **Policies**: Max stake fraction, bankroll limits

#### `trading.yaml` - Trading Domain Config
- **Agents**: `AlgoTradingAgent`
- **Tools**: Trading-specific tools
- **Policies**: Max drawdown, position limits

#### `registry.py` - Domain Registry
- **`DomainRegistry`**: Loads and manages domain configs
- **`get_global_registry()`**: Singleton registry instance
- **Usage**: Factory queries registry for domain configs

---

### 5. **ONTOLOGY** (`src/agent_kit/ontology/`)

**Purpose**: Knowledge graph loading and querying.

#### `loader.py` - Ontology Loader
- **`OntologyLoader`**: Loads RDF/OWL/TTL files into RDFLib Graph
- **Features**:
  - Query caching (LRU cache)
  - Namespace extraction
  - SPARQL query execution
  - Cache statistics
- **Usage**: Foundation for all ontology operations

#### `business_schema.py` - Business Ontology Schema
- **Purpose**: Python representation of business ontology concepts

#### `repository_schema.py` - Repository Ontology Schema
- **Purpose**: Code repository ontology concepts

---

### 6. **ADAPTERS** (`src/agent_kit/adapters/`)

**Purpose**: Bridge external SDKs to ontology-kit architecture.

#### `__init__.py` - Adapter Exports
- **Exports**: `OntologyAgentAdapter`, `OntologyOutputGuardrail`, `OntologyInputGuardrail`, `OntologyToolFilter`

#### `ontology_agent_adapter.py` - Agent Adapter
- **`OntologyAgentAdapter`**: Wraps OpenAI Agents SDK agents with ontology context
- **Purpose**: Enriches SDK agents with ontology-driven routing and tool filtering

#### `ontology_guardrail.py` - Input/Output Guardrails
- **`OntologyInputGuardrail`**: Validates inputs against ontology constraints
- **`OntologyOutputGuardrail`**: Validates outputs against ontology schemas
- **Use Case**: Prevents invalid operations, ensures compliance

#### `ontology_tool_filter.py` - Tool Filtering
- **`OntologyToolFilter`**: Filters available tools based on ontology queries
- **Purpose**: Context-aware tool selection

#### `handoff_manager.py` - Multi-Agent Handoffs
- **`OntologyHandoffManager`**: Manages handoffs between agents with ontology context
- **`HandoffContext`**: Context passed during handoffs (entities, artifacts, session)
- **Features**: Domain-aware routing, event logging, session preservation
- **Integration**: Used by `UnifiedOrchestrator` for multi-agent coordination

#### `openai_sdk.py` - OpenAI SDK Integration
- **Purpose**: Direct integration with OpenAI Agents SDK

---

### 7. **ONTOLOGY EXTENSIONS** (`src/agent_kit/ontology_extensions/`)

**Purpose**: Enhanced ontology capabilities for agents.

#### `ontology_agent.py` - Ontology-Aware Agent
- **Purpose**: Agent that uses ontology for reasoning

#### `ontology_mcp.py` - MCP Integration
- **Purpose**: Model Context Protocol integration for ontology operations

#### `ontology_memory.py` - Semantic Memory
- **`OntologyMemorySession`**: Persistent memory with ontology context
- **Features**: Embedding cache, semantic similarity search
- **Use Case**: Long-term memory for agents across sessions

---

### 8. **ORCHESTRATOR** (`src/agent_kit/orchestrator/`)

**Purpose**: Advanced orchestration capabilities.

#### `ontology_orchestrator.py` - Ontology-Driven Tool Orchestrator
- **`OntologyOrchestrator`**: Orchestrator that uses ontology for tool discovery and routing
- **Features**: SPARQL-based tool discovery, algorithm-based filtering
- **Integration**: Works with `ML_TOOL_REGISTRY` for ML tool discovery
- **Use Case**: Tool-level orchestration (not agent-level)

#### `unified_orchestrator.py` - Unified Agent Orchestrator
- **`UnifiedOrchestrator`**: Combines ADK infrastructure with OpenAI SDK execution
- **Features**:
  - Task understanding and intent classification
  - Agent selection and routing
  - Handoff management
  - Result aggregation
  - Session and state management
- **Integration**: Uses `OntologyHandoffManager`, `OntologyMemoryService`, `OntologyEventLogger`
- **Configuration**: `OrchestratorConfig` with feature flags
- **Use Case**: Production-grade multi-agent orchestration with full observability

**Note**: There are now THREE orchestrator implementations:
1. `agents/orchestrator.py` - Basic orchestrator with policy enforcement
2. `orchestrator/ontology_orchestrator.py` - Tool discovery orchestrator
3. `orchestrator/unified_orchestrator.py` - Full-featured unified orchestrator

**Recommendation**: Consolidate into single orchestrator (see ARCHITECTURE_SUMMARY.md)

---

### 9. **VECTORSPACE** (`src/agent_kit/vectorspace/`)

**Purpose**: Embedding and vector operations.

#### `embedder.py` - Embedding Generation
- **`Embedder`**: Text-to-vector embedding (sentence-transformers)
- **Models**: Configurable model selection

#### `index.py` - Vector Index
- **`VectorIndex`**: FAISS-based vector search index
- **Features**: Add vectors, query by similarity, batch operations

#### `geometry.py` - Geometric Operations
- **Purpose**: Hyperdimensional geometry utilities

---

### 10. **MONITORING** (`src/agent_kit/monitoring/`)

**Purpose**: Observability and resilience.

#### `circuit_breaker.py` - Circuit Breaker Pattern
- **Purpose**: Prevents cascading failures
- **Features**: Error rate tracking, automatic circuit opening/closing
- **Integration**: Used by agents and tools for resilience

---

### 11. **EVENTS** (`src/agent_kit/events/`)

**Purpose**: Event logging and tracking.

#### `ontology_event.py` - Event Models
- **Purpose**: Structured event models for ontology operations

#### `ontology_event_logger.py` - Event Logger
- **Purpose**: Logs ontology-related events for observability

---

### 12. **SESSIONS** (`src/agent_kit/sessions/`)

**Purpose**: Session management for agents.

- **`OntologySessionService`**: Manages agent sessions with persistence
- **Backends**: Memory (in-memory) and SQLite (persistent)
- **Integration**: Used by `UnifiedOrchestrator` for state management
- **Features**: Session creation, retrieval, state tracking

### 12a. **RUNNERS** (`src/agent_kit/runners/`)

**Purpose**: Execution runners for agents.

#### `ontology_runner.py` - Ontology-Aware Runner
- **`OntologyRunner`**: Runs agents with ontology context
- **`RunConfig`**: Configuration for execution (timeout, retries, etc.)
- **`RunResult`**: Structured execution results
- **Integration**: Used by `UnifiedOrchestrator`

#### `streaming_runner.py` - Streaming Execution
- **Purpose**: Stream agent outputs in real-time
- **Use Case**: Long-running tasks, progress updates

### 12b. **MEMORY** (`src/agent_kit/memory/`)

**Purpose**: Persistent memory service for agents.

#### `ontology_memory_service.py` - Semantic Memory
- **`OntologyMemoryService`**: Stores and retrieves agent memories with ontology context
- **Features**: Embedding-based similarity search, context-aware retrieval
- **Integration**: Used by `UnifiedOrchestrator` for long-term memory
- **Backend**: Vector database (FAISS) for semantic search

### 12c. **EVALUATION** (`src/agent_kit/evaluation/`)

**Purpose**: Agent evaluation and testing framework.

#### `evaluators.py` - Evaluation Framework
- **Purpose**: Evaluate agent performance on test cases
- **Features**: Metrics collection, comparison, reporting

#### `ontology_evaluator.py` - Ontology-Aware Evaluation
- **Purpose**: Evaluate agents using ontology-based test cases
- **Use Case**: Domain-specific agent testing

---

### 13. **SCHEMAS** (`src/agent_kit/schemas.py`)

**Purpose**: Pydantic schemas for structured outputs.

- **Schemas**:
  - `BusinessOptimizationResult`: Forecasts + interventions + leverage scores
  - `BettingRecommendation`: Edges + risk checks
  - `TradingRecommendation`: Signals + portfolio metrics
  - `ForecastResult`: Time series forecasts with confidence intervals
  - `InterventionRecommendation`: Actionable business interventions
  - `BettingEdge`: Individual betting opportunities
  - `TradingSignal`: Buy/sell signals
  - `PortfolioMetrics`: Risk metrics
- **Registry**: `SCHEMA_REGISTRY` for dynamic lookup
- **Validation**: Field validators enforce business rules

---

### 14. **SHARED CONTEXT** (`src/agent_kit/shared_context.py`)

**Purpose**: Inter-agent communication.

- **`SharedContext`**: Key-value store for agents to share information
- **Use Case**: Coordination between specialists in orchestrator

### 14a. **PROTOCOLS** (`src/agent_kit/protocols.py`)

**Purpose**: Type protocols and interfaces for type checking and dependency injection.

- **`AgentProtocol`**: Protocol for agents (name, instructions, tools)
- **`RunnableAgentProtocol`**: Protocol for agents with `run()` method
- **`StructuredAgentProtocol`**: Protocol for agents with structured output
- **`EventProtocol`**: Protocol for events
- **`EventLoggerProtocol`**: Protocol for event loggers
- **`OrchestratorProtocol`**: Protocol for orchestrators
- **`MemoryProtocol`**: Protocol for memory services
- **`SessionProtocol`**: Protocol for session services
- **Use Case**: Type safety, dependency injection, mocking in tests

---

### 15. **CLI** (`src/agent_kit/cli.py`)

**Purpose**: Command-line interface for orchestration.

#### Command Groups:
- **`orchestrate`**: Domain orchestration (`run`, `workflow`)
- **`ontology`**: SPARQL queries and exploration (`query`, `explore`)
- **`ml`**: ML workflows (`leverage`, `graph`, `target-leverage`, `interventions`)
- **`agent`**: Agent management (`list`, `run`)
- **`tool`**: Tool discovery (`discover`)
- **`dashboard`**: Dashboard generation (`full`, `performance`)
- **`interactive`**: REPL mode for complex workflows

#### Key Features:
- Rich terminal output (tables, panels, trees)
- Workflow tracking and performance analytics
- Circuit breaker status monitoring
- Domain validation

---

### 16. **DATA COLLECTION** (`src/agent_kit/data_collection.py`)

**Purpose**: Performance tracking and analytics.

- **`AgentDataCollector`**: Tracks agent execution metrics
- **`PerformanceAnalytics`**: Analyzes performance data
- **`MonitoringConfig`**: Configuration for monitoring
- **Use Case**: Observability, performance optimization

---

### 17. **WORKFLOWS** (`src/agent_kit/ontology_ml_workflow.py`)

**Purpose**: ML workflow orchestration.

- **`OntologyMLWorkflowAnalyzer`**: Analyzes ML workflows with ontology context
- **Features**: Workflow tracking, decision logging, learning reports

---

### 18. **VISUALIZATION** (`src/agent_kit/interactive_dashboard.py`)

**Purpose**: Dashboard generation.

- **`InteractiveDashboard`**: Generates HTML dashboards
- **Methods**: `generate_full_dashboard()`, `generate_performance_focused_dashboard()`
- **Output**: HTML files with charts and metrics

### 18a. **WEB APP** (`web_app.py`)

**Purpose**: Streamlit web interface for demos and exploration.

- **Features**:
  - Ontology visualization (network graphs)
  - Agent playground
  - SPARQL query interface
  - Vector space exploration
- **Deployment**: Vercel, Heroku, or any Python hosting
- **Tech**: Streamlit, Plotly, NetworkX

---

### 19. **TASK FLOW** (`src/agent_kit/task_flow_visualizer.py`)

**Purpose**: Visualize agent task flows.

- **Purpose**: Generate visualizations of agent execution flows

---

### 20. **BACKTESTING** (`src/agent_kit/backtesting/`)

**Purpose**: Backtesting for trading/betting agents.

#### `backtest_engine.py` - Backtest Engine
- **Purpose**: Historical simulation of agent strategies

---

## 🔗 Integration Patterns

### How Agents Use Tools

1. **Tool Registration**: Tools are registered in `tools/__init__.py`
2. **Domain Configuration**: Domains specify allowed tools in YAML (`allowed_tools`)
3. **Factory Loading**: `AgentFactory._load_tools()` dynamically imports tools
4. **Agent Execution**: Agents call tools during `act()` phase
5. **Tool Discovery**: `OntologyOrchestrator` can discover tools via SPARQL queries

### How Orchestrator Coordinates Agents

1. **Domain Config**: YAML defines specialists (`default_agents`)
2. **Factory Creation**: `AgentFactory.create_orchestrator()` instantiates specialists
3. **Routing**: `_route_via_ontology()` determines which specialists to invoke
4. **Execution**: Orchestrator calls `specialist.run(task)` for each specialist
5. **Aggregation**: `_aggregate_results()` combines outputs
6. **Validation**: `_structure_output()` validates against Pydantic schema

### How Ontology Drives Behavior

1. **Loading**: `OntologyLoader` loads TTL files into RDFLib Graph
2. **Querying**: SPARQL queries extract agent configs, tool metadata, routing rules
3. **Routing**: Orchestrator uses ontology to route tasks to specialists
4. **Tool Filtering**: `OntologyToolFilter` filters tools based on ontology queries
5. **Validation**: Guardrails validate inputs/outputs against ontology constraints

---

## 🎯 Usage Patterns for Future Tasks

### Pattern 1: Create Domain-Specific Orchestrator

```python
from agent_kit.factories.agent_factory import AgentFactory

factory = AgentFactory()
orchestrator = factory.create_orchestrator("business")
result = orchestrator.run(AgentTask(prompt="Forecast revenue for next 30 days"))
```

### Pattern 2: Add New Tool

1. Create tool function in `tools/your_tool.py`
2. Decorate with `@function_tool` (if using OpenAI SDK)
3. Export in `tools/__init__.py`
4. Add to domain YAML `allowed_tools`
5. Agents can now invoke it

### Pattern 3: Create Custom Agent

1. Inherit from `BaseAgent` or `GrokAgent`
2. Implement `observe()`, `plan()`, `act()`
3. Register in `AgentFactory.AGENT_REGISTRY`
4. Add to domain YAML `default_agents`

### Pattern 4: Add New Domain

1. Create `domains/your_domain.yaml`
2. Define `default_agents`, `allowed_tools`, `risk_policies`
3. Create ontology file `assets/ontologies/your_domain.ttl`
4. Use `AgentFactory.create_orchestrator("your_domain")`

### Pattern 5: Ontology-Driven Tool Discovery

```python
from agent_kit.orchestrator.ontology_orchestrator import OntologyOrchestrator
from agent_kit.ontology.loader import OntologyLoader

loader = OntologyLoader("assets/ontologies/ml_tools.ttl")
loader.load()
orchestrator = OntologyOrchestrator(loader, ML_TOOL_REGISTRY)
tools = orchestrator.discover_tools_by_algorithm("t-SNE")
```

---

## 📊 File Dependencies Map

```
cli.py
  ├── factories/agent_factory.py
  │     ├── agents/orchestrator.py
  │     │     ├── agents/base.py
  │     │     ├── agents/business_agents.py
  │     │     ├── agents/algo_trading_agent.py
  │     │     └── agents/prop_betting_agent.py
  │     ├── domains/registry.py
  │     │     └── domains/*.yaml
  │     ├── ontology/loader.py
  │     └── tools/*.py
  ├── orchestrator/ontology_orchestrator.py
  │     ├── ontology/loader.py
  │     └── tools/ml_training.py (ML_TOOL_REGISTRY)
  ├── data_collection.py
  └── interactive_dashboard.py
```

---

## 🚀 Key Takeaways for Future Development

1. **Modularity**: Agents, tools, and domains are decoupled via factory pattern
2. **Extensibility**: Add new domains by creating YAML configs and ontologies
3. **Type Safety**: Pydantic schemas enforce structured outputs
4. **Observability**: Circuit breakers, event logging, performance tracking built-in
5. **Ontology-First**: Ontology drives routing, tool filtering, and validation
6. **CLI-Driven**: Rich CLI enables complex workflows without code changes

---

## 📝 Next Steps for Consolidation

1. **Unify Orchestrators**: Merge `agents/orchestrator.py` and `orchestrator/ontology_orchestrator.py`
2. **Tool Registry**: Centralize tool registry (currently scattered across modules)
3. **Session Management**: Integrate sessions with shared context
4. **Event System**: Connect event logging to monitoring/observability
5. **Testing**: Add integration tests for agent-tool-orchestrator flows

---

**Last Updated**: 2025-01-09
**Maintainer**: Agent Kit Team
