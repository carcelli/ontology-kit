# Agent Kit: Hyperdimensional Vector Space Navigation

**Ontology-driven agents that navigate high-dimensional embeddings with self-optimizing ML pipelines.**

---

## What It Does

Agent Kit combines three powerful concepts:

1. **Hyperdimensional Vector Space**: Every concept, task, tool, and state exists as a point in a learned embedding space (768–1536D)
2. **Ontology Grounding**: RDF/OWL knowledge graphs define semantic relationships, constraints, and reasoning rules
3. **Self-Optimization**: Reinforcement learning + gradient-based fine-tuning continuously improve embeddings, retrieval, and decision-making

**Result**: Agents that generalize better, explain their reasoning via ontology paths, and self-improve from feedback.

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/your-org/agent_kit.git
cd agent_kit
python -m pip install -e .[dev]

# Run example
python examples/01_embed_and_search.py
```

**Expected output**:
```
Embedding 100 task descriptions...
Building FAISS index...
Query: "Sort a list of numbers"
Top 3 results:
  1. "Sort array ascending" (similarity: 0.94)
  2. "Order elements by value" (similarity: 0.89)
  3. "Arrange items in sequence" (similarity: 0.85)
```

---

## Documentation Map

| File | Primary Value | Read It When |
|------|---------------|--------------|
| `README.md` (this) | Product overview, architecture sketch, and feature tour | You need the “why” and “what” behind Agent Kit |
| `QUICKSTART.md` | Two-week execution plan for Phase 1 bootstrap | You are spinning up the repo and need a sequenced checklist |
| `ARCHITECTURE_PLAN.md` | Deep-dive design (components, risks, math) | You are implementing features or debating design trade-offs |
| `AGENTS.md` | Contributor expectations, coding/testing standards, ontology governance | You are writing code or reviewing a PR |

Each document now owns a distinct layer of context so readers can quickly find ontology guidance, reproducibility rules, or architecture details without wading through duplicated text.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  User Query                                                 │
└─────────────────┬───────────────────────────────────────────┘
                  ▼
         ┌────────────────┐
         │  Embedder      │  → 768D vector
         └────────┬───────┘
                  ▼
         ┌────────────────┐
         │ Vector Index   │  ← k-NN retrieval (FAISS)
         │                │
         └────────┬───────┘
                  ▼
         ┌────────────────┐
         │ Agent Planner  │  ← SPARQL to Ontology (RDF)
         └────────┬───────┘
                  ▼
         ┌────────────────┐
         │ Policy Network │  → action (PPO/RL)
         └────────┬───────┘
                  ▼
         ┌────────────────┐
         │ Execute        │  → state transition
         └────────┬───────┘
                  ▼
         ┌────────────────┐
         │ Optimizer      │  → update embeddings + policy
         └────────────────┘
```

See [`ARCHITECTURE_PLAN.md`](ARCHITECTURE_PLAN.md) for full details.

---

## Project Structure

```
agent_kit/
├── src/agent_kit/
│   ├── vectorspace/       # Embeddings, FAISS index, distance metrics
│   ├── ontology/          # RDF/OWL loader, reasoner, schema
│   ├── agents/            # Agent loop (observe/plan/act/reflect)
│   ├── optimization/      # Training, tuning, evaluation
│   └── tools/             # Utilities, CLI
├── assets/
│   └── ontologies/        # TTL/RDF/OWL files (core.ttl, etc.)
├── tests/
│   ├── unit/              # Fast, isolated tests
│   └── integration/       # End-to-end, slow tests
├── examples/              # Demo scripts
├── scripts/               # Benchmarks, profiling, utilities
├── pyproject.toml         # Dependencies & build config
├── Makefile               # Dev commands (lint, test, etc.)
└── ARCHITECTURE_PLAN.md   # Full design doc
```

---

## Development Workflow

```bash
# Before every commit
make quality    # lint + format + typecheck
make test       # run full test suite

# Before prod deploy
make dryrun     # validation gate (quality + test + smoke test)
```

**CI/CD**: GitHub Actions runs `make dryrun` on every PR; merge blocked if it fails.

---

## Ontology & Reproducibility Principles

- **Single source of truth**: All classes/relations live in `assets/ontologies/` and are mirrored in `src/agent_kit/ontology/schema.py`. Any schema change must regenerate embeddings via `python scripts/refresh_embeddings.py --ontology assets/ontologies/core.ttl --seed 42`.
- **Version everything**: Vector indices, ontology dumps, and training corpora get semantic tags (`vX.Y.Z`) and link back to git SHAs. Store artifacts under `artifacts/hyperdimensional/<version>/`.
- **Deterministic navigation**: Agents carry the ontology path and embedding version IDs in every log line (`trace_id`, `ontology_sha`, `embedding_sha`) so hyperdimensional traversals can be replayed.
- **Local-first dev**: Default to local models (SentenceTransformers + FAISS) for reproducible experiments; cloud endpoints are opt-in and must store their configs alongside result artifacts.
- **Fail-safe tests**: Integration tests in `tests/integration` recreate minimal ontology + vector spaces to verify navigation works before shipping.

These principles keep ontology-grounded, hyperdimensional navigation reproducible across contributors, CI, and production deployments.

---

## Key Features

### 1. Vector Space (`src/agent_kit/vectorspace/`)
- **Embeddings**: SentenceTransformers (local) or OpenAI (API)
- **Index**: FAISS for fast k-NN retrieval (<10ms for 1M vectors)
- **Metrics**: Cosine, Euclidean, learned Mahalanobis distance

### 2. Ontology (`src/agent_kit/ontology/`)
- **Schema**: Define classes (Agent, Task, Tool) and relations (hasPrerequisite, requiresTool)
- **Reasoning**: SPARQL queries + OWL-RL inference
- **Adapter**: Bidirectional mapping between ontology entities ↔ embeddings

### 3. Agents (`src/agent_kit/agents/`)
- **Loop**: Observe → Plan (SPARQL) → Act (policy) → Reflect (log feedback)
- **Memory**: Episodic buffer with vector-based retrieval
- **Policy**: Neural network trained via PPO (Proximal Policy Optimization)

### 4. Optimization (`src/agent_kit/optimization/`)
- **Fine-tuning**: Contrastive learning (triplet loss) for embeddings
- **RL**: PPO with ontology-aware reward shaping
- **Hyperparameter Tuning**: Bayesian optimization via Optuna
- **Profiling**: Track cost-per-task, latency p95, memory usage

---

## Optimization Hooks (What Can Be Tuned)

| Component       | Method                          | Target Metric                     |
|-----------------|---------------------------------|-----------------------------------|
| Embeddings      | Triplet loss (anchor/pos/neg)   | Retrieval precision@10            |
| Distance Metric | Learn Mahalanobis matrix M      | Task success rate                 |
| Policy Network  | PPO (gradient ascent)           | Cumulative reward                 |
| Hyperparameters | Optuna (Bayesian optimization)  | Cost-per-task, latency p95        |
| Ontology        | Relation embeddings (TransE)    | Explainability (ontology coverage)|

---

## Example Usage

### Embed and Search
```python
from agent_kit.vectorspace import Embedder, VectorIndex

# 1. Embed tasks
embedder = Embedder(model_name='all-MiniLM-L6-v2')
tasks = ["Sort list", "Find maximum", "Reverse array"]
embeddings = embedder.embed_batch(tasks)

# 2. Build index
index = VectorIndex(dim=384)
index.add(embeddings, ids=list(range(len(tasks))))

# 3. Query
query_vec = embedder.embed("Order items")
results = index.query(query_vec, k=2)
print(results)  # [{'id': 0, 'distance': 0.12}, {'id': 2, 'distance': 0.35}]
```

### Load Ontology
```python
from agent_kit.ontology import OntologyLoader

loader = OntologyLoader('assets/ontologies/core.ttl')
graph = loader.load()

# SPARQL query
query = """
SELECT ?task ?tool WHERE {
  ?task rdf:type :Task .
  ?task :requiresTool ?tool .
}
"""
results = graph.query(query)
for row in results:
    print(f"Task {row.task} needs {row.tool}")
```

### Run Agent
```python
from agent_kit.agents import Agent

agent = Agent(
    embedder=embedder,
    index=index,
    ontology=graph,
    policy_path='models/ppo_policy.pth'
)

# Execute task
state = {"goal": "Sort list of numbers"}
action = agent.plan(state)  # SPARQL + policy network
result = agent.act(action)
print(result)
```

---

## Roadmap

**Phase 1** (Weeks 1-2): ✅ Foundation (embeddings + ontology + tests)  
**Phase 2** (Weeks 3-4): 🔄 Agent loop with heuristics  
**Phase 3** (Weeks 5-6): ⬜ Fine-tuning embeddings (triplet loss)  
**Phase 4** (Weeks 7-8): ⬜ Reinforcement learning (PPO)  
**Phase 5** (Weeks 9-10): ⬜ Meta-optimization + auto-tuning  

See [`QUICKSTART.md`](QUICKSTART.md) for detailed Phase 1 checklist.

---

## Performance

| Metric                  | Target       | Current (v0.1.0) |
|-------------------------|--------------|------------------|
| Task success rate       | 90%          | 70% (Phase 2)    |
| Retrieval precision@10  | ≥0.80        | 0.72             |
| Latency (p95)           | <200ms       | 150ms            |
| Cost per task           | <$0.01       | $0.005           |

---

## Contributing

1. Fork repo, create feature branch (`git checkout -b feature/your-feature`)
2. Make changes, add tests (maintain ≥90% coverage)
3. Run `make quality` and `make test` — must pass
4. Commit with Conventional Commits (`feat:`, `fix:`, `docs:`)
5. Open PR with description + test output

---

## License

MIT License - see [`LICENSE`](LICENSE) for details.

---

## Citation

```bibtex
@software{agent_kit_2025,
  title={Agent Kit: Hyperdimensional Vector Space Navigation},
  author={Agent Kit Team},
  year={2025},
  url={https://github.com/your-org/agent_kit}
}
```

---

## Support

- **Docs**: [agent-kit.readthedocs.io](https://agent-kit.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/your-org/agent_kit/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/agent_kit/discussions)

---

**Built with**: Python 3.12 • PyTorch • FAISS • RDFLib • Stable-Baselines3 • Optuna
