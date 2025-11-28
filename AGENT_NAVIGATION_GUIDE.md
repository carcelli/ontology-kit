# Agent Navigation Guide & Repository Map

> **For AI Agents:** This file is your primary map to understanding the `ontology-kit` repository. Use it to locate logic, understand architectural boundaries, and find the right tools for the job.

## 🗺️ Repository Map

### 🟢 Core Logic (`src/agent_kit/`)

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| **`ontology/`** | **Foundational Layer.** Loading RDF files, querying SPARQL, and defining Pydantic schemas. | `loader.py` (Graph loading), `business_schema.py` (Data models) |
| **`agents/`** | **Actor Layer.** Individual agent implementations. Start here to create or modify specific agent behaviors. | `base.py` (Base class), `ontology_agent.py` (Logic-driven agent) |
| **`orchestrator/`** | **Coordination Layer.** Logic for managing multiple agents to achieve a shared goal. | `ontology_orchestrator.py` (Task delegation) |
| **`tools/`** | **Capability Layer.** Discrete tools agents can use (e.g., visualizations, GitHub ops). | `semantic_graph.py`, `hyperdim_viz.py` |
| **`ontology_extensions/`** | **Advanced/Experimental.** Specialized features like memory and MCP integration. | `ontology_memory.py`, `ontology_mcp.py` |
| **`vectorspace/`** | **Embedding Layer.** Vector database and geometric embedding logic. | `embedder.py`, `index.py` |

### 🔵 Usage & Examples (`examples/`)
*Use these files to understand how to instantiate and run the code.*

- **Basic Operations:**
    - `01_embed_and_search.py`: Vector search demo.
    - `02_ontology_query.py`: Direct SPARQL querying.
- **Agent Workflows:**
    - `03_ontology_agents.py`: Running a single ontology-aware agent.
    - `04_orchestrated_agents.py`: Multi-agent coordination example.
- **Visualizations:**
    - `06_hyperdim_viz_tool.py`: Generating 3D/2D visual outputs.

### 🟤 Assets (`assets/`)
- **`ontologies/`**: The "Brain" of the system.
    - `core.ttl`: Base ontology definitions.
    - `business.ttl`: Business-specific rules and entities.
    - `ml_tools.ttl`: Definitions for ML tool capabilities.

---

## 🧭 Navigation Heuristics for Agents

### 1. "I need to add a new type of Agent."
- **Go to:** `src/agent_kit/agents/`
- **Action:** Inherit from `BaseAgent` in `base.py`.
- **Reference:** See `ontology_agent.py` for how to integrate tools/ontology.

### 2. "I need to change how we query the Knowledge Graph."
- **Go to:** `src/agent_kit/ontology/loader.py`
- **Action:** Modify `OntologyLoader` class.

### 3. "I need to define a new concept (like 'Competitor' or 'Market')."
- **Step 1:** Update `assets/ontologies/business.ttl` (Turtle format).
- **Step 2:** Update `src/agent_kit/ontology/business_schema.py` (Pydantic model) to reflect the new RDF structure.

### 4. "I need to fix a bug in the visualization output."
- **Go to:** `src/agent_kit/tools/`
- **Check:** `hyperdim_viz.py` or `semantic_graph.py`.

### 5. "I need to see how the system is currently being run."
- **Go to:** `examples/`
- **Action:** Read the numbered examples (`01_...`, `02_...`) as they represent the intended progression of complexity.

---

## 🗝️ Core Concepts

- **OntologyLoader:** The singleton-like service that holds the RDF graph. All agents usually share one instance to access the "world state".
- **BaseAgent:** The parent class implementing the `observe -> plan -> act -> reflect` loop.
- **Orchestrator:** High-level manager that breaks complex user requests into subtasks for individual agents.
- **Pydantic Schemas:** Used strictly to enforce type safety when "extracting" data from the loose graph structure of RDF.

## ⚠️ Important Constraints

1. **Circular Imports:** Be careful when importing between `agents/` and `orchestrator/`.
2. **State Management:** The ontology graph acts as the shared state. Changes there are global.
3. **Dependencies:** `rdflib` is critical for all ontology operations.
