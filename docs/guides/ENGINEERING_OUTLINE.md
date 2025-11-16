# Engineering Outline – How Agent Kit Works

This outline distills how the current codebase operates so engineers can see the _working_ parts at a glance. Use it as the orientation layer before diving into specific modules or demos.

## System Layers (What Is Working Where)

| Layer | Responsibility | Key Paths & Modules |
| --- | --- | --- |
| Ontology Assets | RDF/OWL definitions that ground every decision | `assets/ontologies/**/*.ttl`, `src/agent_kit/ontology/loader.py`, `src/agent_kit/ontology/business_schema.py`, `repository_schema.py` |
| Agent Core & Adapters | Observe→plan→act loop plus SDK bridges | `src/agent_kit/agents/base.py`, `business_agents.py`, `ontology_agent.py`, `planner_agent.py`, `adapters/openai_sdk.py` |
| Toolchain & Vector Space | Executable tools discovered via ontology bindings, FAISS navigation, leverage calculators | `src/agent_kit/tools/*.py`, `src/agent_kit/vectorspace/{embedder.py,index.py,geometry.py}` |
| Orchestration & Workflows | Ontology lookups that route work, plus workflow analyzer | `src/agent_kit/orchestrator/ontology_orchestrator.py`, `src/agent_kit/ontology_ml_workflow.py`, `examples/ontology_ml/` |
| Observability & Dashboards | Data capture, task-flow visualization, dashboards | `src/agent_kit/data_collection.py`, `task_flow_visualizer.py`, `interactive_dashboard.py`, outputs under `outputs/` |
| Demonstrations | Ready-to-run workflows proving the paths above work | `examples/*.py`, `examples/ontology_ml/*`, `scripts/create_tree_visualization.py` |

## Primary Workflows (Working Breakdown)

### 1. Ontology-Grounded Agent Loop
1. **Ontology context** – Load and query ontologies via `OntologyLoader` (`src/agent_kit/ontology/loader.py`) and helper schemas in `business_schema.py` / `repository_schema.py`. Every agent receives a loader instance.
2. **Agent execution** – `BaseAgent` (`src/agent_kit/agents/base.py`) defines the observe→plan→act→reflect contract. Concrete agents such as `ForecastAgent` and `OptimizerAgent` (`business_agents.py`) implement business logic, while `GrokAgent` leverages xAI’s client with ontology-grounded prompts.
3. **Shared state** – `SharedContext` (`src/agent_kit/shared_context.py`) lets collaborating agents exchange artifacts or metadata during a run.
4. **Instrumentation** – `AgentDataCollector` and `PerformanceAnalytics` (`src/agent_kit/data_collection.py`) wrap executions so every ontology query, tool use, and decision is persisted to `outputs/agent_data/`.
5. **Entry points** – Run `python examples/04_orchestrated_agents.py` for pure custom agents or `python examples/grok_agent_demo.py` for Grok + ontology grounding.

### 2. Ontology-to-Tool Orchestration & SDK Bridges
1. **Tool discovery** – `OntologyOrchestrator` (`src/agent_kit/orchestrator/ontology_orchestrator.py`) queries classes like `ml:ModelTrainerTool`, resolves `ml:hasPythonIdentifier`, and maps to the Python callable plus schema in the tool registry.
2. **Tool registry** – Each tool module (e.g., `src/agent_kit/tools/ml_training.py`, `semantic_graph.py`, `hyperdim_leverage_viz.py`, `ontology.py`) exposes typed inputs/outputs and registers specifications consumed both by custom agents and OpenAI SDK adapters.
3. **Vector search** – `VectorIndex` and friends under `src/agent_kit/vectorspace/` generate embeddings, persist FAISS indices, and drive the hyperdimensional navigation tools invoked by leverage analyses.
4. **SDK adapters** – `OpenAISDKAdapter` (`src/agent_kit/adapters/openai_sdk.py`) wraps SDK agents so ontology context, discovered tool specs, and deterministic schemas get injected before handing the run over to OpenAI’s runner. Hybrid demos live in `examples/05_hybrid_orchestration.py` and `examples/ontology_ml/`.

### 3. Workflow Analytics & Learning Loop
1. **Workflow definition** – `OntologyMLWorkflowAnalyzer` (`src/agent_kit/ontology_ml_workflow.py`) expresses the six-stage breakdown (load/validate, semantic analysis, tool selection, hyperdimensional navigation, ML execution, integration/learning) and records agent decisions per workflow.
2. **Performance capture** – `AgentDataCollector` writes structured JSON (execution metrics, ontology queries, tool calls, decisions). Summaries roll up via `PerformanceAnalytics`.
3. **Visualization/inspection** – `TaskFlowVisualizer` (`src/agent_kit/task_flow_visualizer.py`) turns captured sessions into flow diagrams, ontology navigation maps, and dashboards. `InteractiveDashboard` (`src/agent_kit/interactive_dashboard.py`) merges ontology graphs with performance charts for longer-term trend analysis.
4. **Outputs** – Rich HTML dashboards land under `outputs/dashboards/`, and workflow/playback artifacts live in `outputs/flow_visualizations/`.

### 4. Semantic Vector Navigation (Supporting Workflow)
1. **Embedding generation** – `src/agent_kit/vectorspace/embedder.py` wraps SentenceTransformer models for deterministic embeddings tied to ontology entities.
2. **Geometry utilities** – `vectorspace/geometry.py` computes centroids, projections, and leverage-friendly transforms consumed by hyperdimensional visualization tools.
3. **Working demos** – `python examples/01_embed_and_search.py` and `python examples/06_hyperdim_viz_tool.py` demonstrate the functioning embedding/indexing pipeline feeding analytics.

## Working Demos & Entry Points

| Goal | Command | What It Exercises |
| --- | --- | --- |
| Ontology query basics | `python examples/02_ontology_query.py` | Validates ontology loading & SPARQL queries |
| Multi-agent orchestration | `python examples/04_orchestrated_agents.py` | Base agents + Ontology handoffs + data collection |
| Hybrid (custom + OpenAI SDK) | `python examples/05_hybrid_orchestration.py` | Adapter path, ontology-discovered tools |
| Hyperdim leverage analysis | `python examples/07_leverage_analysis.py` | Vector embeddings, leverage tooling, dashboard output |
| Workflow analytics breakdown | `python examples/08_ontology_ml_breakdown_demo.py` | `OntologyMLWorkflowAnalyzer`, task-flow viz, dashboards |

## Extension Playbooks (How Engineers Contribute Work)

### Add or Extend an Ontology Tool
1. Define/extend the ontology class + bindings in the relevant `.ttl` under `assets/ontologies/`.
2. Implement typed inputs/outputs inside the appropriate module under `src/agent_kit/tools/` and register the callable + schema in the module-level registry.
3. Update tests (e.g., `tests/unit/tools/`) to cover success/failure paths.
4. If the tool should be discoverable by OpenAI SDK agents, expose an OpenAI function spec and wire it into the adapter configuration.

### Create a New Agent or Adapter
1. Subclass `BaseAgent` (custom reasoning) or wrap an SDK agent inside `OpenAISDKAdapter`.
2. Inject ontology context (via `OntologyLoader`) during `observe()` or adapter instruction composition so every action remains grounded.
3. Register the agent inside orchestrators or examples, and update `examples/` to showcase the new capability.
4. Add observability hooks via `AgentDataCollector` and provide an example run command in the README/docs.

### Instrument a Workflow
1. Use `OntologyMLWorkflowAnalyzer` to define the stages and add decisions with `AgentDecision`.
2. Persist execution artifacts through `AgentDataCollector`.
3. Generate dashboards or flow diagrams using `InteractiveDashboard` / `TaskFlowVisualizer` so stakeholders can see the working system.

## Validation & Diagnostics

- `make test` or `pytest` – regression suite over `src/agent_kit`.
- `python -m ruff check src tests` and `python -m black src tests` – lint/format.
- `pytest tests/unit/test_vectorspace.py` (or similar) – targeted checks when editing FAISS/navigation code.
- `python examples/semantic_graph_workflow_demo.py` – verifies semantic graph tooling end to end.
- Inspect new data under `outputs/agent_data/` plus dashboards under `outputs/dashboards/` to confirm observability pieces are working.

## Reference Material

- `README.md` – mission, architecture diagram, quick start.
- `docs/index.md` – documentation map for semantic leverage tooling.
- `docs/guides/ARCHITECTURE_DECISION.md` – rationale for modular multi-SDK design.
- `docs/guides/AGENTS.md` – repository conventions and SDK integration guardrails.

This outline should make it clear what is already working, which modules own each slice of functionality, and where to plug in when extending the system.
