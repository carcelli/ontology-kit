# [Tools Overview] Semantic Leverage Tools: Complete Documentation

**Comprehensive guide to finding high-leverage business interventions using t-SNE, semantic graphs, and ontology-driven discovery**

---

## Quick Links

- **[Semantic Leverage Guide](SEMANTIC_LEVERAGE_GUIDE.md)** — Complete theoretical framework and practical examples
- **[Leverage Tool Integration](../LEVERAGE_TOOL_INTEGRATION.md)** — Integration details and production checklist
- **[ML Tool Ontology](../ML_TOOL_ONTOLOGY.md)** — Architecture and design philosophy

---

## What You Get

### 1. **Basic t-SNE Leverage Analysis** (Already Had)

**Tool**: `hyperdim_leverage_viz.py` → `analyze_leverage`

```python
Leverage(i) = Actionability(i) × (Sensitivity(i) + Uncertainty(i) + Centrality(i))
```

**Use when**: You need quick visualization of high-leverage business entities
**Output**: PNG visualization + ranked list of levers
**Runtime**: <10 seconds for 15-50 terms

### 2. **Semantic Graph Construction** (New)

**Tool**: `semantic_graph.py` → `build_semantic_graph`

Builds weighted graphs where:
- Nodes = business entities (Budget, Marketing, Revenue, etc.)
- Edges = semantic similarity (cosine > threshold) + extracted relations
- Weights = embedding similarity × relation strength

**Use when**: You need to understand relationships and pathways between entities
**Output**: JSON graph with nodes, edges, centrality metrics
**Runtime**: <5 seconds for 15-50 terms

### 3. **Targeted Leverage Analysis** (New)

**Tool**: `semantic_graph.py` → `compute_target_leverage`

```python
Leverage(i → T) = Betweenness_T(i) × PathStrength(i → T) × Actionability(i) × SHAP_T(i)
```

**Use when**: You need leverage scores for a **specific KPI** (Revenue, Satisfaction, etc.)
**Output**: Ranked levers with path analysis and score breakdowns
**Runtime**: <3 seconds after graph is built

### 4. **Intervention Recommendations** (New)

**Tool**: `semantic_graph.py` → `recommend_interventions`

Generates A/B test specifications:
- Recommended actions (domain-specific)
- Expected effect sizes
- Sample sizes (power analysis)
- Duration estimates
- KPIs and guardrails

**Use when**: You need experiment specs for high-leverage nodes
**Output**: Experiment plans ready for execution
**Runtime**: <2 seconds per lever

---

## Architecture: How It All Fits Together

```
┌─────────────────────────────────────────────────────────────┐
│                    Ontology Layer                            │
│  ml_tools.ttl: Classes, Properties, Python Bindings         │
│  • LeverageAnalysisTool                                     │
│  • SemanticGraphTool                                        │
│  • TargetLeverageTool                                       │
│  • InterventionRecommenderTool                              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ SPARQL Discovery
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Ontology Orchestrator                           │
│  • discover_tool(class_iri)                                 │
│  • discover_tools_by_algorithm('t-SNE')                     │
│  • get_openai_tools([...])                                  │
│  • call(class_iri, params)                                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Tool Execution
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                  Tool Registry                               │
│  ML_TOOL_REGISTRY = {                                       │
│    'analyze_leverage': {...},                               │
│    'build_semantic_graph': {...},                           │
│    'compute_target_leverage': {...},                        │
│    'recommend_interventions': {...}                         │
│  }                                                          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Python Functions
                 ▼
┌──────────────────────┬──────────────────────────────────────┐
│  hyperdim_leverage_  │  semantic_graph.py                   │
│  viz.py              │  • build_semantic_graph()            │
│  • analyze_leverage()│  • compute_target_leverage()         │
│                      │  • recommend_interventions()         │
└──────────────────────┴──────────────────────────────────────┘
```

---

## Complete Workflow Example

### Step 1: Basic Leverage Visualization

```python
from agent_kit.tools.ml_training import analyze_leverage

terms = [
    'Revenue', 'Budget', 'Marketing', 'Advertising', 
    'Sales', 'Product', 'Website', 'EmailTiming'
]
actionable = ['Budget', 'Marketing', 'Advertising', 'Website', 'EmailTiming']

result = analyze_leverage({
    'terms': terms,
    'kpi_term': 'Revenue',
    'actionable_terms': actionable
})

# Output:
# top_levers: [
#   {'term': 'Marketing', 'leverage': 1.237},
#   {'term': 'Budget', 'leverage': 1.218},
#   ...
# ]
```

**Gives you**: Quick prioritization + visualization

### Step 2: Build Semantic Graph

```python
from agent_kit.tools.semantic_graph import build_semantic_graph

result = build_semantic_graph({
    'terms': terms,
    'similarity_threshold': 0.65,  # Lower = more edges
    'output_path': 'outputs/graph.json'
})

# Output:
# {
#   'n_nodes': 8,
#   'n_edges': 12,
#   'avg_degree': 3.0,
#   'n_clusters': 2
# }
```

**Gives you**: Graph structure + relationships

### Step 3: Targeted Leverage for Specific KPI

```python
from agent_kit.tools.semantic_graph import compute_target_leverage

result = compute_target_leverage({
    'graph_path': 'outputs/graph.json',
    'target': 'Revenue',
    'top_k': 5
})

# Output:
# levers: [
#   {
#     'term': 'Marketing',
#     'total_leverage': 0.847,
#     'betweenness': 0.75,  # High betweenness to Revenue
#     'path_strength': 0.89,
#     'strongest_path': ['Marketing', 'Sales', 'Revenue']
#   },
#   ...
# ]
```

**Gives you**: Precise scoring with path analysis

### Step 4: Generate Experiment Specs

```python
from agent_kit.tools.semantic_graph import recommend_interventions

result = recommend_interventions({
    'graph_path': 'outputs/graph.json',
    'node': 'Marketing',
    'target': 'Revenue',
    'top_paths': 3
})

# Output:
# recommendations: [
#   {
#     'name': 'Experiment 1: Marketing Intervention',
#     'path': 'Marketing → Sales → Revenue',
#     'action': 'Optimize marketing spend via A/B testing across channels',
#     'expected_lift': 0.22,  # 22%
#     'sample_size': 1250,
#     'duration': '2-4 weeks',
#     'primary_kpi': 'Revenue',
#     'guardrails': ['Customer satisfaction score', 'Cost per acquisition']
#   },
#   ...
# ]
```

**Gives you**: Ready-to-execute experiment plans

---

## Agent-Driven Discovery

Agents can discover and chain these tools automatically via ontology queries:

```python
from agent_kit.orchestrator import OntologyOrchestrator
from openai_agents import Agent, Runner

# Agent discovers tools via SPARQL
specs = orch.get_openai_tools([
    'ml#LeverageAnalysisTool',
    'ml#SemanticGraphTool',
    'ml#TargetLeverageTool',
    'ml#InterventionRecommenderTool'
])

agent = Agent(
    name="Business Optimizer",
    instructions="""
    You identify high-leverage business interventions.
    
    Workflow:
    1. Build semantic graph from business entities
    2. Compute targeted leverage for the specified KPI
    3. Generate experiment recommendations
    4. Present ranked interventions with expected impact
    """,
    tools=specs
)

# User asks a question → agent chains tools automatically
result = await Runner.run(
    agent,
    "What should I focus on to increase revenue by 20% this quarter?"
)

# Agent automatically:
# 1. Calls build_semantic_graph(terms=[...])
# 2. Calls compute_target_leverage(target='Revenue')
# 3. Calls recommend_interventions(node='Marketing', target='Revenue')
# 4. Presents: "Focus on Marketing (leverage: 0.847). Run A/B test on 
#     spend allocation across channels. Expected +22% revenue lift.
#     Sample size: 1,250/group. Duration: 2-4 weeks."
```

---

## Key Concepts Explained

### 1. **Semantic Distance vs. Causality**

**What t-SNE Shows**:
- "Budget" is close to "Advertising" → They co-occur in business documents
- Semantic similarity based on how terms are **discussed together**

**What It Doesn't Show**:
- Direction of causation (Does Budget → Advertising? Or Advertising → Budget?)
- Magnitude of effects (How much does changing Budget affect Revenue?)

**Solution**: Use **semantic graph + predictive models (SHAP)** to get both structure and effects

### 2. **Leverage Score Breakdown**

```
Basic Score = A × (S + U + C)
```

- **A (Actionability)**: Can we intervene? (0 or 1)
  - Example: Budget=1.0, Market size=0.0
- **S (Sensitivity)**: Distance to KPI in t-SNE space
  - Example: Marketing close to Revenue → high S
- **U (Uncertainty)**: Cluster variance (info gain opportunity)
  - Example: High variance → experiment to learn
- **C (Centrality)**: Graph betweenness (bridges)
  - Example: Budget connects multiple clusters → high C

```
Advanced Score = Betweenness_T × PathStrength × A × SHAP
```

- **Betweenness_T**: How often node is on paths **to target T**
- **PathStrength**: Sum of weighted paths from node to T
- **SHAP**: Model-derived effect size (if model available)

### 3. **When to Use Which Tool**

| Tool | Use Case | Output | Time |
|------|----------|--------|------|
| `analyze_leverage` | Quick prioritization, visualization | PNG + ranked list | 10s |
| `build_semantic_graph` | Understand relationships | JSON graph | 5s |
| `compute_target_leverage` | Precise KPI-specific scoring | Ranked levers + paths | 3s |
| `recommend_interventions` | Experiment design | A/B test specs | 2s/lever |

**Recommended Workflow**:
1. Start with `analyze_leverage` for quick insights
2. If you need path analysis, build semantic graph
3. Use `compute_target_leverage` for precise KPI targeting
4. Generate experiments with `recommend_interventions`

---

## Production Checklist

### Before Deploying

- [ ] **Validate semantic similarity threshold**: Test 0.5-0.8 range for your domain
- [ ] **Train predictive model**: Get SHAP values for model effect component
- [ ] **Define actionability**: Mark which entities you can actually intervene on
- [ ] **Set up monitoring**: Track leverage score drift over time
- [ ] **Prepare corpus**: If using relation extraction, curate domain-specific text

### After Deploying

- [ ] **Run pilot experiments**: Validate top 1-2 levers with small sample
- [ ] **Update graph**: Strengthen edges confirmed by experiments
- [ ] **Retrain models**: Incorporate new data → refresh SHAP values
- [ ] **Recompute leverage**: Detect shifts in high-leverage nodes
- [ ] **Close the loop**: Feed experiment results back into analysis

---

## FAQ

### Q: Why are all my leverage scores 0?

**A**: Likely because:
1. **Similarity threshold too high**: Try lowering from 0.7 to 0.5-0.6
2. **No paths to target**: Graph is disconnected; add more edges
3. **All nodes have actionability=0**: Mark some as actionable

**Fix**: 
```python
build_semantic_graph({'similarity_threshold': 0.5})  # Lower threshold
```

### Q: How do I add SHAP values for better leverage scores?

**A**: 
1. Train a predictive model (Revenue ~ features)
2. Compute SHAP values for each feature
3. Save as JSON: `{"Revenue": {"Budget": 0.23, "Marketing": 0.18, ...}}`
4. Pass to `compute_target_leverage({'model_shap_path': 'shap.json'})`

### Q: Can I use this for non-business domains?

**A**: Yes! Works for any domain with:
- Entities/concepts (nodes)
- Relationships (edges)
- A target/KPI to optimize

Examples: Healthcare (optimize patient outcomes), Supply chain (reduce lead time), Product (increase retention)

### Q: What if my graph has multiple disconnected clusters?

**A**: This is fine! It reveals structure:
- Cluster 1: Financial terms (Budget, Revenue, Cost)
- Cluster 2: Customer terms (Satisfaction, Engagement)
- Cluster 3: Operational terms (Process, Efficiency)

Bridge nodes connecting clusters = highest leverage

### Q: How often should I recompute leverage scores?

**A**:
- **Static domains**: Quarterly (after major experiments)
- **Dynamic domains**: Monthly (e.g., e-commerce, advertising)
- **Trigger-based**: When big changes happen (new product, market shift)

---

## Examples & Demos

### Run All Demos

```bash
# Basic leverage analysis (existing tool)
python examples/07_leverage_analysis.py

# Ontology-driven leverage discovery
python examples/ml_leverage_discovery_demo.py

# Complete semantic graph workflow
python examples/semantic_graph_workflow_demo.py
```

### Expected Outputs

**Visualizations** (in `outputs/`):
- `business_leverage.png` — 2D t-SNE with leverage colors
- `business_intervention_3d.png` — 3D rotation for nuance
- `leverage_leverage-job-*.png` — Dynamic job outputs

**Data Files** (in `outputs/`):
- `business_semantic_graph.json` — Graph structure with metrics
- Various experiment specs and SHAP JSONs

---

## Advanced Topics

### 1. **Causal Inference Integration**

Replace semantic edges with learned causal structure:

```python
from causalnex.structure import notears

# Learn causal DAG from data
causal_graph = notears.from_pandas(df)

# Replace semantic graph edges with causal edges
# Now betweenness represents causal pathways, not semantic similarity
```

### 2. **Multi-Objective Optimization**

Optimize for multiple KPIs simultaneously:

```python
targets = ['Revenue', 'CustomerSatisfaction', 'OperationalEfficiency']
pareto_front = []

for target in targets:
    levers = compute_target_leverage({'target': target})
    pareto_front.append(levers)

# Find levers that score high across all objectives (Pareto optimal)
```

### 3. **Dynamic Leverage Tracking**

Monitor how leverage scores shift over time:

```python
import pandas as pd

leverage_history = []
for month in months:
    result = compute_target_leverage({'target': 'Revenue', ...})
    leverage_history.append({
        'month': month,
        'scores': result['levers']
    })

df = pd.DataFrame(leverage_history)
# Plot: Which levers are rising/falling in importance?
```

---

## Performance & Scalability

### Current Limits

- **Terms**: Tested up to 100 entities (<15s total)
- **Edges**: Scales to ~5,000 edges (sparse graphs)
- **Paths**: Cutoff at 5 hops to avoid combinatorial explosion

### Optimization Tips

1. **Embeddings**: Cache and reuse (don't recompute every run)
2. **Graph pruning**: Remove low-weight edges (<0.5) for speed
3. **PCA pre-reduction**: If >100 terms, reduce to 50D before t-SNE
4. **GPU acceleration**: Use `openTSNE` or `cuML` for t-SNE
5. **Parallel processing**: Compute leverage for multiple targets in parallel

---

## Troubleshooting

### Issue: "Node not found in graph"

**Cause**: Typo in node name or graph doesn't contain that node

**Fix**: Check `graph_data['nodes']` for exact spelling

### Issue: "No paths found from X to Y"

**Cause**: Graph is disconnected; nodes in separate clusters

**Fix**: Lower similarity threshold or add relations manually

### Issue: Import errors for semantic_graph tools

**Cause**: Tool registry couldn't import new module

**Fix**: Ensure `networkx` is installed:
```bash
pip install networkx>=3.0
```

---

## References & Further Reading

### Theory
- [Visualizing Data using t-SNE (van der Maaten, 2008)](http://jmlr.org/papers/v9/vandermaaten08a.html)
- [Causal Inference (Pearl, 2009)](http://bayes.cs.ucla.edu/BOOK-2K/)
- [SHAP Values (Lundberg & Lee, 2017)](https://arxiv.org/abs/1705.07874)

### Tools
- [NetworkX Documentation](https://networkx.org/)
- [Sentence-BERT](https://www.sbert.net/)
- [scikit-learn t-SNE](https://scikit-learn.org/stable/modules/manifold.html#t-sne)

### Internal Docs
- [ML Tool Ontology](../ML_TOOL_ONTOLOGY.md)
- [Leverage Tool Integration](../LEVERAGE_TOOL_INTEGRATION.md)
- [Semantic Leverage Guide](SEMANTIC_LEVERAGE_GUIDE.md) ← **Start here**

---

## Status

✅ **Complete**: All tools implemented, tested, and documented

🚀 **Production-Ready**: Ontology integration + agent discovery working

📊 **Examples**: 3 runnable demos + comprehensive tests

📖 **Documentation**: Theory + practice + troubleshooting guides

---

**Questions?** See `docs/SEMANTIC_LEVERAGE_GUIDE.md` for detailed examples and edge cases.

**Ship it!** 🚀 Semantic leverage → Actionable experiments → Business impact

