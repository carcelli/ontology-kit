# Agent Kit — Ontology-Driven ML for Small Businesses

**Multi-SDK agentic framework** for building ontology-grounded machine learning systems. Enables flexible orchestration across OpenAI Agents SDK, LangChain, AutoGen, and custom agents—all anchored by SPARQL-queryable knowledge graphs.

[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/carcelli/ontology-kit/actions)
[![Coverage](https://img.shields.io/badge/coverage-64%25-yellow)](https://github.com/carcelli/ontology-kit)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 🎯 Mission

**Democratize ML for small businesses** by providing an agentic framework that:
- Grounds agents in **ontologies** (SPARQL + SHACL) to reduce hallucinations
- Enables **multi-SDK flexibility** (OpenAI, LangChain, AutoGen) for diverse use cases
- Provides **hyperdimensional navigation** (FAISS vector spaces) for semantic reasoning
- Optimizes **leverage points** via graph-structured business knowledge

**Target**: Small businesses in Wisconsin/Illinois lacking data science teams.

---

## 🏗️ Architecture

### Ontology as Backbone, SDKs as Plugins

```
┌─────────────────────────────────────────────────────────┐
│                  ONTOLOGY LAYER                         │
│  • RDF/OWL Knowledge Graphs (business.ttl, core.ttl)  │
│  • SPARQL Queries (agent routing, context injection)   │
│  • SHACL Validation (business rules, constraints)      │
└─────────────────┬───────────────────────────────────────┘
                  │
      ┌───────────┴───────────┬───────────────────┐
      │                       │                   │
┌─────▼──────┐      ┌────────▼────────┐   ┌─────▼──────┐
│   Custom   │      │  OpenAI Agents  │   │ LangChain  │
│ BaseAgent  │      │   SDK Adapter   │   │  Adapter   │
│            │      │                 │   │  (Future)  │
└────────────┘      └─────────────────┘   └────────────┘
```

**Key Decision** (see [`docs/guides/ARCHITECTURE_DECISION.md`](docs/guides/ARCHITECTURE_DECISION.md)):
- **Don't refactor to OpenAI SDK** — keep ontology-first architecture
- **Use adapters** for SDK integration (composition, not inheritance)
- **Enable multi-SDK testing** for diverse use cases

---

## 🚀 Quick Start

### Installation

```bash
# Clone repo
git clone https://github.com/carcelli/ontology-kit.git
cd ontology-kit

# Install with dev dependencies
python -m pip install -e .[dev]

# Verify installation
make test
```

### Run Examples

#### Example 1: Custom Ontology-Driven Agents

```bash
# Run multi-agent orchestration (custom BaseAgent)
python examples/04_orchestrated_agents.py
```

**Output**: ForecastAgent → OptimizerAgent handoff via ontology routing

#### Example 2: OpenAI SDK Integration

```bash
# Run ontology-ML pipeline (OpenAI SDK)
python -m examples.ontology_ml.main
```

**Output**: SchemaAgent + MapperAgent for CSV → RDF → features

#### Example 3: Hybrid Orchestration

```bash
# Run both custom + SDK agents
python examples/05_hybrid_orchestration.py
```

**Output**: ForecastAgent (custom) + InsightExtractor (SDK)

---

## 📂 Project Structure

```
agent_kit/
├── src/agent_kit/
│   ├── agents/
│   │   ├── base.py                  # Custom BaseAgent (observe/plan/act/reflect)
│   │   ├── business_agents.py       # ForecastAgent, OptimizerAgent
│   │   └── orchestrator.py          # OntologyOrchestrator (custom handoffs)
│   ├── adapters/
│   │   └── openai_sdk.py            # OpenAI SDK adapter (composition)
│   ├── ontology/
│   │   ├── loader.py                # SPARQL queries, SHACL validation
│   │   └── business_schema.py       # Pydantic models for ontology entities
│   ├── vectorspace/
│   │   ├── index.py                 # FAISS vector index
│   │   └── embedder.py              # SentenceTransformer embeddings
│   └── optimization/                # (Future: RL-based optimization)
├── assets/ontologies/
│   ├── core.ttl                     # Core ontology (Agent, Tool, Capability)
│   └── business.ttl                 # Business domain (Business, Revenue, LeveragePoint)
├── examples/
│   ├── 01_embed_and_search.py       # Vector space navigation
│   ├── 02_ontology_query.py         # SPARQL querying
│   ├── 03_business_ontology.py      # Business domain demo
│   ├── 04_orchestrated_agents.py    # Custom multi-agent workflow
│   ├── 05_hybrid_orchestration.py   # Custom + SDK hybrid
│   └── ontology_ml/                 # OpenAI SDK example (CSV → ontology → ML)
│       ├── agents/                  # SchemaAgent, MapperAgent (SDK)
│       ├── tools/                   # graph_tools.py (@function_tool)
│       ├── manager.py               # Deterministic orchestrator
│       └── main.py                  # Entry point
├── tests/
│   ├── unit/                        # Unit tests (BaseAgent, ontology, vectorspace)
│   └── integration/                 # (Future: E2E workflows)
├── docs/guides/ARCHITECTURE_DECISION.md         # Why modular > full refactor
├── AGENTS.md                        # Agent design patterns
└── BUSINESS_ONTOLOGY_PLAN.md        # Business domain ontology spec
```

---

## 🤖 Agent Patterns

### 1. **Custom BaseAgent** (Ontology-Driven)

**Use for**: Complex reasoning, SPARQL-based routing, multi-step workflows

```python
from agent_kit.agents.base import BaseAgent, AgentTask
from agent_kit.ontology.loader import OntologyLoader

class ForecastAgent(BaseAgent):
    def __init__(self, name: str, description: str, ontology_loader: OntologyLoader):
        super().__init__(name, description)
        self.ontology_loader = ontology_loader

    def observe(self, task: AgentTask) -> AgentObservation:
        # Query ontology for context
        sparql_query = "SELECT ?revenue WHERE { ... }"
        results = self.ontology_loader.query(sparql_query)
        return AgentObservation(data=results, notes=["Observed revenue data"])

    def plan(self, task: AgentTask, observation: AgentObservation) -> AgentPlan:
        return AgentPlan(steps=["Generate Q1-Q3 forecast"], metadata={"model": "ARIMA"})

    def act(self, task: AgentTask, plan: AgentPlan, observation: AgentObservation) -> AgentActionResult:
        # Run ML model
        forecast = {"Q1": 145000, "Q2": 150000, "Q3": 160000}
        return AgentActionResult(summary="Forecast complete", artifacts={"forecast": forecast})
```

**Run**:
```python
agent = ForecastAgent(name="ForecastAgent", description="...", ontology_loader=loader)
result = agent.run(AgentTask(description="Forecast Q1-Q3 revenue"))
```

---

### 2. **OpenAI SDK Adapter** (Structured Outputs)

**Use for**: Schema design, data mapping, deterministic pipelines

```python
from agents import Agent as SDKAgent
from agent_kit.adapters import OpenAISDKAdapter
from pydantic import BaseModel

class SchemaProposal(BaseModel):
    classes: list[str]
    properties: list[str]

sdk_agent = SDKAgent(
    name="SchemaAgent",
    instructions="Propose ontology schema from CSV",
    model="gpt-4.1",
    output_type=SchemaProposal
)

adapter = OpenAISDKAdapter(
    sdk_agent=sdk_agent,
    ontology_path="assets/ontologies/business.ttl"
)

result = await adapter.run("Propose schema for invoices.csv")
proposal: SchemaProposal = result.action_result.artifacts['sdk_result'].output
```

---

### 3. **Hybrid Orchestration** (Best of Both)

```python
from agent_kit.agents.orchestrator import OntologyOrchestrator
from agent_kit.adapters import OpenAISDKAdapter

# Custom agents for complex reasoning
orchestrator = OntologyOrchestrator(ontology_path="assets/ontologies/business.ttl")

# SDK agents for structured outputs
schema_agent_adapter = OpenAISDKAdapter(sdk_agent=schema_agent, ontology_loader=loader)

# Coordinate both
forecast_result = orchestrator.run_workflow(task1)  # Custom agent
schema_result = await schema_agent_adapter.run(task2)  # SDK agent
```

---

## 🔬 Key Features

### 1. **SPARQL-Driven Agent Routing**

```python
# Orchestrator queries ontology to select agent
sparql_query = """
SELECT ?agent ?capability
WHERE {
    ?agent a core:Agent ;
           core:hasCapability ?capability .
    ?capability core:solves ?problem .
    FILTER(?problem = "revenue_forecasting")
}
"""
results = ontology_loader.query(sparql_query)
agent_name = results[0]['agent']  # → "ForecastAgent"
```

### 2. **SHACL Validation** (Business Rules)

```turtle
# assets/ontologies/shapes.ttl
ex:InvoiceShape a sh:NodeShape ;
    sh:targetClass ex:Invoice ;
    sh:property [
        sh:path ex:hasTotal ;
        sh:minInclusive 0.0 ;  # No negative invoices
    ] .
```

```python
from pyshacl import validate
conforms, _, report = validate(data_graph, shacl_graph=shapes_graph)
assert conforms, f"Validation failed: {report}"
```

### 3. **Vector Space Navigation** (FAISS)

```python
from agent_kit.vectorspace.embedder import Embedder
from agent_kit.vectorspace.index import VectorIndex

embedder = Embedder()
index = VectorIndex(dimension=384, metric='cosine')

# Add business entities
entities = ["Sunshine Bakery", "Client acquisition", "Revenue optimization"]
embeddings = embedder.embed_batch(entities)
index.add(embeddings, ids=[0, 1, 2])

# Query for similar concepts
query_vec = embedder.embed("increase sales")
results = index.query(query_vec, k=2)
# → [{"id": 1, "distance": 0.15}, {"id": 2, "distance": 0.22}]
```

---

## 📊 Ontology Schema

### Core Ontology (`core.ttl`)

```turtle
@prefix core: <http://example.org/core#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

core:Agent a owl:Class .
core:hasCapability a owl:ObjectProperty ;
    rdfs:domain core:Agent ;
    rdfs:range core:Capability .
```

### Business Ontology (`business.ttl`)

```turtle
@prefix ex: <http://example.org/retail#> .

ex:Business a owl:Class .
ex:hasName a owl:DatatypeProperty ;
    rdfs:domain ex:Business ;
    rdfs:range xsd:string .

ex:generates a owl:ObjectProperty ;
    rdfs:domain ex:Business ;
    rdfs:range ex:RevenueStream .
```

**See** [`BUSINESS_ONTOLOGY_PLAN.md`](BUSINESS_ONTOLOGY_PLAN.md) for full specification.

---

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test suite
pytest tests/unit/test_base_agent.py

# Check coverage
make coverage

# Lint + typecheck
make lint
```

---

## 🛠️ Development

### Add a New Agent

```python
# src/agent_kit/agents/my_agent.py
from agent_kit.agents.base import BaseAgent, AgentTask, AgentActionResult

class MyAgent(BaseAgent):
    def observe(self, task: AgentTask):
        # Implement observation logic
        pass
    
    def plan(self, task: AgentTask, observation):
        # Implement planning logic
        pass
    
    def act(self, task: AgentTask, plan, observation):
        # Implement action logic
        pass
```

### Add an SDK Adapter

```python
# src/agent_kit/adapters/langchain.py
from langchain.agents import AgentExecutor
from agent_kit.agents.base import AgentResult

class LangChainAdapter:
    def __init__(self, agent_executor: AgentExecutor, ontology_loader):
        self.executor = agent_executor
        self.ontology = ontology_loader
    
    async def run(self, task: str) -> AgentResult:
        # Enrich with ontology context
        result = await self.executor.ainvoke(task)
        return self._map_result(result)
```

---

## 📈 Roadmap

### Phase 1: Foundation (✅ Complete)
- [x] BaseAgent abstraction (observe/plan/act/reflect)
- [x] OntologyLoader (SPARQL + SHACL)
- [x] VectorIndex (FAISS + embeddings)
- [x] Business ontology (Business, Revenue, LeveragePoint)

### Phase 2: SDK Integration (🚧 In Progress)
- [x] OpenAI SDK adapter
- [x] Ontology-ML example (SchemaAgent + MapperAgent)
- [x] Hybrid orchestration example
- [ ] LangChain adapter (RAG + vector stores)
- [ ] AutoGen adapter (crew-based workflows)

### Phase 3: Production (🔲 Planned)
- [ ] Multi-SDK orchestrator
- [ ] RL-based optimization (`optimization/`)
- [ ] Real business data integration (WI/IL)
- [ ] Web UI for agent monitoring
- [ ] MLOps pipeline (MLflow, model registry)

---

## 🤝 Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for:
- Code style (Black, Ruff, mypy)
- Commit conventions (Conventional Commits)
- PR process (tests + coverage required)

---

## 📚 Documentation

- **[docs/guides/ARCHITECTURE_DECISION.md](docs/guides/ARCHITECTURE_DECISION.md)**: Why modular > full refactor
- **[AGENTS.md](AGENTS.md)**: Agent design patterns
- **[BUSINESS_ONTOLOGY_PLAN.md](BUSINESS_ONTOLOGY_PLAN.md)**: Business domain spec
- **[examples/ontology_ml/README.md](examples/ontology_ml/README.md)**: OpenAI SDK integration

---

## 📝 License

MIT License — see [`LICENSE`](LICENSE)

---

## 🙏 Acknowledgments

- **OpenAI Agents SDK**: Structured outputs, handoffs, streaming
- **RDFLib**: Python library for RDF graphs
- **FAISS**: Facebook AI Similarity Search
- **Sentence-Transformers**: Semantic embeddings

---

**Ship it!** 🚀 Ontology as backbone, SDKs as tools.

**Questions?** Open an issue or contribute via PR.
