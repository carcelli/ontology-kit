# Agent Kit — Comprehensive Ontology-Driven ML for Enterprise Agents

**Ontology-driven agent framework** that extends the OpenAI Agents SDK with knowledge graph capabilities. Enables intelligent agent orchestration with SPARQL-based reasoning, semantic memory, and ontology-aware tool filtering—all powered by RDF/OWL knowledge graphs.

[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/carcelli/ontology-kit/actions)
[![Coverage](https://img.shields.io/badge/coverage-64%25-yellow)](https://github.com/carcelli/ontology-kit)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![Web Demo](https://img.shields.io/badge/web-demo-live-blue)](https://agent-kit.vercel.app)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 🎯 Mission

**Empower organizations with intelligent agent systems** by providing an ontology-driven framework that:
- Grounds agents in **ontologies** (SPARQL + SHACL) to reduce hallucinations and ensure consistency
- Enables **semantic reasoning** with knowledge graph integration
- Provides **ontology-enhanced agents** with SPARQL-based instructions and tool discovery
- Supports **intelligent MCP tool filtering** based on business rules
- Includes **semantic memory** with ontology-aware context preservation
- Enables **hyperdimensional navigation** (FAISS vector spaces) for semantic reasoning
- Optimizes **leverage points** via graph-structured business knowledge

**Target**: Organizations requiring knowledge-driven agent orchestration, from research institutions to enterprise deployments.

**🎉 Live Demo**: Try Agent Kit's capabilities at [agent-kit.vercel.app](https://agent-kit.vercel.app)

---

## 🏗️ Architecture

### Ontology-Driven Enterprise Agent Framework

```
┌─────────────────────────────────────────────────────────────┐
│                  ONTOLOGY LAYER                              │
│  • RDF/OWL Knowledge Graphs (business.ttl, core.ttl)       │
│  • SPARQL Queries (agent routing, tool filtering)           │
│  • SHACL Validation (business rules, constraints)           │
│  • Semantic Memory & Context Preservation                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
    ┌─────────────┴─────────────┬─────────────────────┐
    │                           │                     │
┌───▼────┐   ┌──────────────┐   │   ┌──────────────┐   │
│  MCP   │   │  Computer    │   │   │ Multi-Model  │   │
│ Servers│   │ Automation   │   │   │   Routing    │   │
│ GitHub │   │   Browser    │   │   │ Intelligence │   │
│ Browser│   │   Code Edit  │   │   │              │   │
└────────┘   └──────────────┘   │   └──────────────┘   │
                                │                     │
    ┌───────────────────────────┴─────────────────────┐
    │                                                 │
┌───▼──────────────────────────────────────────────┐  │
│         OPENAI AGENTS SDK EXTENSIONS              │  │
│  • Ontology-Aware Agent Orchestration             │  │
│  • Advanced Handoffs & Tool Filtering             │  │
│  • Persistent Memory Integration                  │  │
│  • Tracing & Observability                        │  │
└───────────────────────────────────────────────────┘  │
    │                                                 │
    ▼                                                 │
┌─────────────────────────────────────────────────────┘
│         WEB & INTEGRATION LAYER                       │
│  • Streamlit Interactive Dashboards                     │
│  • Ontology Explorer & SPARQL Interface                │
│  • Vector Search Demonstrations                         │
│  • Agent Playground & Business Analytics               │
│  • Vercel Serverless Deployment                        │
└─────────────────────────────────────────────────────────┘
```

**Key Decisions**:
- **Ontology-First Architecture**: Knowledge graphs drive agent behavior
- **Multi-SDK Flexibility**: Adapters enable OpenAI, LangChain, AutoGen integration
- **Web Demo Accessibility**: Streamlit interface for easy exploration
- **Quality Assurance**: Automated linting, testing, and deployment validation

**See**: [`docs/guides/ARCHITECTURE_DECISION.md`](docs/guides/ARCHITECTURE_DECISION.md) for detailed design rationale.

---

## 🚀 Quick Start

### 🌐 Try the Live Demo (No Installation Required!)

Visit **[agent-kit.vercel.app](https://agent-kit.vercel.app)** to explore Agent Kit's capabilities interactively:
- 🔍 **Ontology Explorer**: Query knowledge graphs with SPARQL
- 📊 **Vector Search**: Test semantic embeddings and similarity
- 🎯 **Business Analytics**: Explore leverage point analysis
- ⚙️ **Agent Playground**: Interact with forecasting agents

### 💻 Local Development

#### Installation

```bash
# Clone repo
git clone https://github.com/carcelli/ontology-kit.git
cd ontology-kit

# Install with dev dependencies
python -m pip install -e .[dev]

# Verify installation
make test
```

#### Run Examples

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

#### Example 4: Interactive Web Demo

```bash
# Launch interactive web interface
streamlit run web_app.py

# Or deploy to Vercel for live demo
# See VERCEL_DEPLOYMENT.md for details
```

**Output**: Live interactive dashboard at `http://localhost:8501`

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
│   ├── tools/                       # GitHub, visualization, and utility tools
│   │   ├── github_tools.py          # GitHub API integration
│   │   ├── hyperdim_leverage_viz.py # Business leverage visualization
│   │   ├── hyperdim_viz.py          # General hyperdimensional viz
│   │   ├── interactive_viz.py       # Interactive Plotly dashboards
│   │   └── [other tools...]
│   └── optimization/                # (Future: RL-based optimization)
├── src/agents/                      # Vendored OpenAI Agents SDK (pristine upstream code)
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
├── scripts/
│   ├── code_quality_checker.py      # AI-assisted development QA
│   ├── validate_vercel_config.py    # Vercel deployment validation
│   ├── sync_openai_agents.py        # Keeps vendored SDK aligned with upstream release
│   └── [benchmark tools...]
├── tests/
│   ├── unit/                        # Unit tests (BaseAgent, ontology, vectorspace)
│   └── integration/                 # (Future: E2E workflows)
├── web_app.py                       # Streamlit interactive demo
├── vercel.json                      # Vercel deployment configuration
├── package.json                     # Node.js wrapper for Vercel
├── requirements.txt                 # Python dependencies
├── setup_github_auth.sh             # Secure GitHub authentication setup
├── update_token.sh                  # Token rotation utility
├── load_env.sh                      # Environment loading helper
├── docs/
│   ├── guides/
│   │   ├── ARCHITECTURE_DECISION.md # Design rationale
│   │   └── ENGINEERING_OUTLINE.md   # Technical implementation
│   └── index.md                     # Documentation index
├── AI_DEVELOPMENT_GUIDE.md          # Quality assurance for AI-assisted dev
├── QUALITY_CHECKLIST.md             # Code review checklist
├── VERCEL_DEPLOYMENT.md             # Deployment guide
├── CONTRIBUTING.md                  # Development guidelines
├── AGENTS.md                        # Agent design patterns
├── BUSINESS_ONTOLOGY_PLAN.md        # Ontology specification
├── QUICKSTART.md                    # Alternative quick start guide
├── GROK_INTEGRATION_SUMMARY.md      # xAI integration details
└── upstream/openai-agents/          # Full OpenAI Agents SDK snapshot (docs, tests, mkdocs, workflows)
```

## 🔗 OpenAI Agents SDK Upstream

Agent Kit now vendors the official OpenAI Agents SDK directly inside this repository:

- `src/agents/` exposes OpenAI's `agents` Python package so ontology extensions can import the exact same runtime shipped by OpenAI.
- `upstream/openai-agents/` is a bit-for-bit snapshot of the upstream repository, including docs, examples, mkdocs configuration, GitHub workflows, and the original LICENSE.
- `scripts/sync_openai_agents.py` refreshes `src/agents` from the snapshot so that vendored code stays pristine and free of Windows Zone metadata.
- `docs/openai_agents_sdk.md` details the sync workflow, how to run upstream tests, and attribution requirements.

Update workflow:

1. Drop a new upstream release into `upstream/openai-agents/` (or pull latest files into that directory).
2. Run `make sync-openai-agents` to rebuild `src/agents` from the snapshot.
3. Run your regression suite (`make test`) plus any relevant upstream tests as documented in `docs/openai_agents_sdk.md`.
4. Commit and push the refreshed SDK alongside ontology extensions.

---

## 🛠️ Development Workflow

### Quality Assurance for AI-Assisted Development

Agent Kit includes comprehensive quality assurance tools designed for AI-assisted development:

#### Automated Quality Checks
```bash
# Run full quality suite
make quality          # Lint, format, type-check
make test            # Unit and integration tests
make dryrun          # Pre-deployment validation

# AI-specific quality checker
python scripts/code_quality_checker.py
```

#### Development Guides
- **[`AI_DEVELOPMENT_GUIDE.md`](AI_DEVELOPMENT_GUIDE.md)**: Best practices for AI-assisted coding
- **[`QUALITY_CHECKLIST.md`](QUALITY_CHECKLIST.md)**: Systematic code review checklist
- **[`VERCEL_DEPLOYMENT.md`](VERCEL_DEPLOYMENT.md)**: Web deployment guide

### Secure Authentication Setup

```bash
# Set up GitHub authentication securely
./setup_github_auth.sh

# Update tokens when needed
./update_token.sh
```

**See**: [`docs/guides/ENGINEERING_OUTLINE.md`](docs/guides/ENGINEERING_OUTLINE.md) for technical implementation details.

---

## 🚀 Deployment

### Vercel (Recommended)

Deploy the interactive web demo to Vercel for instant sharing:

```bash
# Automatic deployment via GitHub integration
# 1. Push changes to GitHub
# 2. Connect repository to Vercel
# 3. Auto-deploy on every push

# Manual deployment
npm install -g vercel
vercel --prod
```

**Live Demo**: [agent-kit.vercel.app](https://agent-kit.vercel.app)

### Local Development

```bash
# Run web demo locally
streamlit run web_app.py

# Run examples
python examples/04_orchestrated_agents.py

# Run tests
make test
```

### Production Deployment

For full production deployment with all features:

```bash
# Install all dependencies
pip install -e .[dev]

# Set up environment
./setup_github_auth.sh

# Run quality checks
make dryrun

# Deploy agents to your infrastructure
```

**See**: [`VERCEL_DEPLOYMENT.md`](VERCEL_DEPLOYMENT.md) for detailed deployment instructions.

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

### 1. **Interactive Web Demos**
- Live Streamlit dashboards for ontology exploration
- Vector search demonstrations with real-time embeddings
- Agent playground for testing forecasting capabilities
- Business leverage analysis visualizations
- Vercel-deployed demos accessible worldwide

### 2. **SPARQL-Driven Agent Routing**

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

### Phase 3: Web & Production (🚧 Recently Added)
- [x] Interactive web demos (Streamlit + Vercel)
- [x] Quality assurance system for AI-assisted development
- [x] Secure authentication and deployment tools
- [x] Code linting and testing automation
- [ ] Real business data integration (WI/IL)
- [ ] Advanced agent monitoring dashboard
- [ ] MLOps pipeline (MLflow, model registry)
- [ ] Multi-SDK orchestrator with web interface

---

## 🤝 Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for:
- Code style (Black, Ruff, mypy)
- Commit conventions (Conventional Commits)
- PR process (tests + coverage required)

### AI-Assisted Development
- **[`AI_DEVELOPMENT_GUIDE.md`](AI_DEVELOPMENT_GUIDE.md)**: Best practices for AI-assisted coding
- **[`QUALITY_CHECKLIST.md`](QUALITY_CHECKLIST.md)**: Systematic code review checklist
- Run `python scripts/code_quality_checker.py` for automated QA

---

## 📚 Documentation

### Core Documentation
- **[docs/guides/ARCHITECTURE_DECISION.md](docs/guides/ARCHITECTURE_DECISION.md)**: Why modular > full refactor
- **[docs/guides/ENGINEERING_OUTLINE.md](docs/guides/ENGINEERING_OUTLINE.md)**: Technical implementation details
- **[AGENTS.md](AGENTS.md)**: Agent design patterns
- **[BUSINESS_ONTOLOGY_PLAN.md](BUSINESS_ONTOLOGY_PLAN.md)**: Business domain specification

### Development & Quality Assurance
- **[AI_DEVELOPMENT_GUIDE.md](AI_DEVELOPMENT_GUIDE.md)**: Best practices for AI-assisted development
- **[QUALITY_CHECKLIST.md](QUALITY_CHECKLIST.md)**: Systematic code review checklist
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Development guidelines and processes

### Deployment & Integration
- **[VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md)**: Web demo deployment guide
- **[examples/ontology_ml/README.md](examples/ontology_ml/README.md)**: OpenAI SDK integration
- **[GROK_INTEGRATION_SUMMARY.md](GROK_INTEGRATION_SUMMARY.md)**: xAI integration details

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

**Ship it!** 🚀 Ontology as backbone, SDKs as tools, web as interface.

**Try it live:** [agent-kit.vercel.app](https://agent-kit.vercel.app)

**Questions?** Open an issue or contribute via PR.
