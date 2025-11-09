# [Tool Guide] Semantic Leverage Analysis: From t-SNE Maps to Business Action

**A comprehensive guide to finding high-leverage intervention points using semantic relations**

---

## Table of Contents

1. [Quick Start: Reading Your t-SNE Map](#quick-start-reading-your-t-sne-map)
2. [First Principles: Semantic Distance ≠ Causality](#first-principles-semantic-distance--causality)
3. [The Leverage Formula](#the-leverage-formula)
4. [Complete Workflow: Semantic Graph → Action](#complete-workflow-semantic-graph--action)
5. [Interpreting Your 3D t-SNE Business Map](#interpreting-your-3d-t-sne-business-map)
6. [Operational Framework: From Analysis to Experiment](#operational-framework-from-analysis-to-experiment)
7. [Code Examples & Agent Integration](#code-examples--agent-integration)
8. [Common Pitfalls & Edge Cases](#common-pitfalls--edge-cases)

---

## Quick Start: Reading Your t-SNE Map

### What Each Element Means

**Points (Nodes)**:
- Each point = a domain concept (e.g., Budget, Revenue, Marketing)
- Position = semantic similarity in 384D embedding space, compressed to 2D/3D
- **Distance reflects co-occurrence in language**, not causal relationships

**Colors**:
- 🔴 **Red/Orange** (high scores ~1.0-1.5): High-leverage candidates
- 🟡 **Yellow** (medium scores ~0.5-1.0): Secondary levers
- 🔵 **Blue** (low scores ~0.0-0.5): Outcomes/targets or low-leverage

**Shapes**:
- ○ **Circles**: Actionable terms (you can intervene)
- □ **Squares**: Fixed terms (observe only)

**Numbers** (e.g., "Budget (1.22)"):
- Leverage score = Actionability × (Sensitivity + Uncertainty + Centrality)
- Higher = more impactful intervention point

---

## First Principles: Semantic Distance ≠ Causality

### What t-SNE Actually Shows

**t-SNE reveals linguistic/conceptual proximity**, not cause-and-effect:

```
"Budget" near "Advertising" → these words co-occur in business text
                            → they're discussed together
                            → likely related concepts

BUT this does NOT prove: Budget causes Advertising outcomes
                       OR Advertising causes budget changes
```

### Why This Matters for Leverage

**Semantic clusters identify potential pathways**:
- Nodes **between clusters** = bridges (high betweenness centrality)
- Bridges = leverage points where interventions propagate
- BUT: Must validate with **causal inference** or **experiments**

**Example from your map**:

```
Red cluster (Budget, Advertising, Website):
- Semantically close → "marketing/resource allocation" concepts
- Bridge position → connects tactics to outcomes
- High leverage → interventions here likely affect multiple outcomes

Blue cluster (Revenue, Sales, Forecast):
- Semantically close → "business outcomes" concepts
- Terminal nodes → these are what you measure, not what you pull
- Low leverage → can't directly "increase Revenue"; act on its drivers
```

---

## The Leverage Formula

### Basic Multi-Factor Score (Current Implementation)

```
Leverage(i) = A(i) × (S(i) + U(i) + C(i))
```

Where:
- **A**: Actionability (0 or 1) — Can we intervene?
- **S**: Sensitivity (0 to 1) — Distance to KPI in t-SNE space (closer = higher)
- **U**: Uncertainty (0 to 1) — Cluster variance (higher = more info gain)
- **C**: Centrality (0 to 1) — Betweenness in ontology graph

### Advanced Targeted Leverage (Semantic Graph Extension)

For a **specific target T** (e.g., Revenue), compute:

```
Leverage(i → T) = Betweenness_T(i) × PathStrength(i → T) × Actionability(i) × ModelEffect_T(i)
```

**Components**:

1. **Targeted Betweenness** `Betweenness_T(i)`:
   ```
   How often node i appears on shortest paths ending at target T
   Computed via: NetworkX single_source_shortest_path with target as destination
   Range: [0, 1] normalized by max betweenness in graph
   ```

2. **Path Strength** `PathStrength(i → T)`:
   ```
   Sum over all paths from i to T:
     ∏(edge weights along path)
   
   Edge weights = f(semantic_similarity, extracted_relations)
   - semantic_similarity: cosine(embed(i), embed(j)) > threshold
   - extracted_relations: "drives", "depends on", "precedes" from text
   ```

3. **Actionability** `Actionability(i)`:
   ```
   Binary or continuous [0, 1]:
   - 1.0: Direct control (Budget, Advertising spend)
   - 0.7: Indirect influence (EmailTiming, Website UX)
   - 0.3: Observable metric (Engagement rate)
   - 0.0: Fixed outcome (Market size)
   ```

4. **Model Effect** `ModelEffect_T(i)`:
   ```
   From trained predictive model (e.g., SHAP values):
   SHAP_T(i) = impact of feature i on target T
   
   Measures: If we change i by 1σ, how much does T change?
   Range: Normalized to [0, 1] by max |SHAP| in model
   ```

---

## Complete Workflow: Semantic Graph → Action

### Step 1: Build Semantic Graph

**Input**: 
- Domain concepts/terms (from ontology or corpus)
- Embeddings (384D semantic vectors)
- Optional: Extracted relations from text

**Process**:
```python
# Pseudo-code
G = Graph()
for term in terms:
    G.add_node(term, embedding=embed(term))

for i, j in combinations(terms, 2):
    sim = cosine_similarity(embed(i), embed(j))
    if sim > threshold:  # e.g., 0.7
        G.add_edge(i, j, weight=sim)
    
    # Augment with extracted relations
    if extract_relation(corpus, i, j):
        G[i][j]['relation_type'] = 'drives' | 'depends_on' | 'precedes'
        G[i][j]['weight'] *= 1.5  # Boost confirmed relations
```

**Output**: Weighted graph with semantic + relational edges

### Step 2: Compute Target Leverage

**Input**:
- Semantic graph G
- Target node T (e.g., "Revenue")
- Model with SHAP values (optional but recommended)

**Process**:
```python
leverage_scores = {}
for node in G.nodes():
    if node == target:
        continue
    
    # 1. Targeted betweenness
    paths_to_target = all_shortest_paths(G, source=node, target=T)
    betweenness_T = len(paths_to_target) / max_paths
    
    # 2. Path strength
    path_strength = sum(
        prod(G[u][v]['weight'] for u,v in path)
        for path in paths_to_target
    )
    
    # 3. Actionability (from metadata or heuristic)
    actionability = G.nodes[node].get('actionable', 0.0)
    
    # 4. Model effect (from SHAP)
    shap_score = model.shap_values[node][target] if model else 1.0
    
    leverage_scores[node] = (
        betweenness_T * path_strength * actionability * abs(shap_score)
    )

return sorted(leverage_scores.items(), key=lambda x: x[1], reverse=True)
```

**Output**: Ranked list of levers with scores

### Step 3: Recommend Interventions

**Input**:
- High-leverage node (e.g., "Budget")
- Target (e.g., "Revenue")
- Historical data or model

**Process**:
```python
def recommend_interventions(node, target, graph, model):
    # Analyze paths from node to target
    paths = list(all_simple_paths(graph, node, target, cutoff=3))
    
    recommendations = []
    for path in paths[:3]:  # Top 3 paths
        # Extract intermediate nodes
        intermediates = path[1:-1]
        
        # Generate experiment plan
        experiment = {
            'lever': node,
            'path': ' → '.join(path),
            'action': generate_action(node),  # Domain-specific
            'kpis': [target] + intermediates,
            'sample_size': compute_mde_sample_size(effect_size=0.1, power=0.8),
            'duration': '2-4 weeks',
            'guardrails': identify_risks(path, graph)
        }
        recommendations.append(experiment)
    
    return recommendations
```

**Output**: Experiment specifications with actions, KPIs, sample sizes

---

## Interpreting Your 3D t-SNE Business Map

### Example: Small Business Revenue Optimization

**Your Map Shows**:

```
🔴 Red/Orange Circles (High Leverage, Actionable):
  • Budget (1.22)        → Resource allocation lever
  • Advertising (1.21)   → Marketing channel spend
  • Website (1.07)       → Conversion funnel
  • EmailTiming (1.00)   → Outreach optimization
  • OutreachCampaign (1.00) → Campaign design

🔵 Blue Squares (Outcomes/Low Leverage):
  • Revenue (0.00)       → Primary target
  • Sales (0.00)         → Outcome metric
  • Forecast (0.00)      → Prediction target
  • Product (0.00)       → Offering (slower to change)
  • Service (0.00)       → Delivery mechanism
```

### What This Tells You

#### 1. **Cluster Analysis**

**Marketing Tactics Cluster** (Red):
- Budget, Advertising, Website, EmailTiming cluster together
- **Interpretation**: These concepts are discussed together in business contexts
- **Implication**: Likely interdependent; changing one affects others
- **Position**: Bridge between operations and outcomes

**Business Outcomes Cluster** (Blue):
- Revenue, Sales, Forecast form tight cluster
- **Interpretation**: These are result metrics, not drivers
- **Implication**: Don't try to "increase Revenue" directly; act on its inputs
- **Position**: Terminal nodes in causal graph

#### 2. **Leverage Ranking Explained**

**Budget (1.22) — Highest Leverage**:
- ✅ **High Actionability**: Direct control over allocation
- ✅ **High Sensitivity**: Close to Revenue in semantic space (co-occur in planning docs)
- ✅ **High Centrality**: Bridges "resource" and "outcome" concepts
- ✅ **High Uncertainty**: Optimal allocation is unknown → experimentation opportunity

**Advertising (1.21) — Second Highest**:
- ✅ **High Actionability**: Can adjust spend/targeting
- ✅ **High Sensitivity**: Directly mentioned with Sales/Revenue
- ✅ **Medium Centrality**: Connects Budget → Engagement → Sales
- ⚠️ **Medium Uncertainty**: Some data exists, but optimal strategy unclear

**Website (1.07) — Tertiary Lever**:
- ✅ **Medium Actionability**: Can modify UX, but requires dev work
- ✅ **Medium Sensitivity**: Conversion funnel sits between marketing and sales
- ✅ **High Centrality**: All digital paths flow through website
- ⚠️ **Lower Uncertainty**: Conversion best practices are known

**Revenue (0.00) — Not a Lever**:
- ❌ **Zero Actionability**: Can't directly "set" revenue
- ❌ **Target Node**: This is what you're trying to move
- ℹ️ **Outcome**: Measure this; act on its drivers

#### 3. **Semantic Paths to Revenue**

**Direct Path** (Highest Impact):
```
Budget → Advertising → Sales → Revenue
       (1.22)  (1.21)    (0.00)  (Target)

Action: Reallocate 15% of budget to high-ROI advertising channels
Expected: +20-30% sales lift → +15-25% revenue increase
Test: A/B split by customer segment, 4 weeks
```

**Indirect Path** (Medium Impact, Lower Risk):
```
EmailTiming → OutreachCampaign → Customer → Sales → Revenue
     (1.00)         (1.00)          (0.00)   (0.00)  (Target)

Action: Optimize send times for max open rate
Expected: +10-15% engagement → +5-10% sales
Test: Time-series A/B test, 2 weeks
```

**Conversion Path** (High Impact, Higher Effort):
```
Website → Customer → Sales → Revenue
 (1.07)     (0.00)   (0.00)  (Target)

Action: Redesign checkout flow, reduce friction
Expected: +15-20% conversion rate → +10-15% revenue
Test: Sequential rollout with control group, 3 weeks
```

---

## Operational Framework: From Analysis to Experiment

### Phase 1: Discovery (Week 1)

**Objective**: Identify top 5 levers

**Steps**:
1. Generate t-SNE map with leverage scores (10 min)
2. Build semantic graph with cosine similarity edges (30 min)
3. Compute targeted leverage for KPI (5 min)
4. Review top 5 levers with stakeholders (1 hour)

**Deliverables**:
- Visualization (PNG)
- Ranked lever list (CSV)
- Path analysis (report)

### Phase 2: Validation (Week 2-3)

**Objective**: Confirm levers with causal analysis or pilot

**Steps**:
1. Train predictive model (Revenue ~ features) → get SHAP values
2. Cross-reference semantic levers with model effects
3. Run micro-experiment on top lever (small sample)
4. Measure outcome + guardrails

**Deliverables**:
- Model report (MAE, SHAP values)
- Pilot results (effect size, CI)
- Go/no-go recommendation

### Phase 3: Intervention (Week 4-6)

**Objective**: Execute high-leverage experiments at scale

**Steps**:
1. Design A/B test with proper power analysis
2. Implement intervention on treatment group
3. Monitor primary KPI + intermediates + guardrails
4. Analyze results, compute ROI

**Deliverables**:
- Experiment spec (sample size, duration, KPIs)
- Live dashboard (treatment vs. control)
- Final analysis (lift, significance, ROI)

### Phase 4: Iteration (Week 7+)

**Objective**: Close the loop, refine graph

**Steps**:
1. Update semantic graph edge weights with experiment results
2. Retrain model with new data → refresh SHAP
3. Recompute leverage scores (detect shifts)
4. Prioritize next lever

**Deliverables**:
- Updated leverage map
- Model drift report
- Next quarter roadmap

---

## Code Examples & Agent Integration

### Example 1: Basic Leverage Analysis (Current Tool)

```python
from agent_kit.tools.ml_training import analyze_leverage

# Define your business domain
terms = [
    'Revenue', 'Forecast', 'Client', 'Customer', 'OutreachCampaign',
    'EmailTiming', 'Budget', 'Marketing', 'Sales', 'Product', 'Service',
    'Website', 'SocialMedia', 'Advertising', 'CustomerSatisfaction'
]

# Mark actionable levers
actionable = [
    'OutreachCampaign', 'EmailTiming', 'Budget', 
    'Marketing', 'Website', 'SocialMedia', 'Advertising'
]

# Run analysis
result = analyze_leverage({
    'terms': terms,
    'kpi_term': 'Revenue',
    'actionable_terms': actionable
})

# Review top levers
for lever in result['top_levers'][:5]:
    print(f"{lever['term']}: {lever['leverage']:.3f}")
    # Output:
    # Marketing: 1.237
    # Budget: 1.218
    # Advertising: 1.206
```

### Example 2: Semantic Graph Construction (New Tool)

```python
from agent_kit.tools.semantic_graph import build_semantic_graph

# Build graph from embeddings + optional text corpus
result = build_semantic_graph({
    'terms': terms,
    'similarity_threshold': 0.7,  # Only connect if cosine > 0.7
    'corpus_path': 'data/business_docs.txt',  # Extract relations
    'output_path': 'outputs/semantic_graph.json'
})

# Graph structure
print(f"Nodes: {result['n_nodes']}")        # 15
print(f"Edges: {result['n_edges']}")        # 42
print(f"Avg degree: {result['avg_degree']}")  # 2.8
print(f"Clusters: {result['n_clusters']}")   # 3 (marketing, outcomes, operations)
```

### Example 3: Targeted Leverage with SHAP (Advanced)

```python
from agent_kit.tools.semantic_graph import compute_target_leverage

# Train model first (optional but recommended)
model_result = train_model({
    'dataset_uri': 's3://bucket/revenue_drivers.parquet',
    'hyperparameters': {'model_type': 'xgboost', 'compute_shap': True}
})

# Compute leverage for specific target
leverage = compute_target_leverage({
    'graph_path': 'outputs/semantic_graph.json',
    'target': 'Revenue',
    'model_uri': model_result['artifact_uri'],  # For SHAP values
    'top_k': 5
})

# Results with detailed breakdown
for item in leverage['levers']:
    print(f"\n{item['term']}: {item['total_leverage']:.3f}")
    print(f"  Betweenness: {item['betweenness']:.2f}")
    print(f"  Path strength: {item['path_strength']:.2f}")
    print(f"  Actionability: {item['actionability']:.2f}")
    print(f"  SHAP effect: {item['shap_score']:.2f}")
    print(f"  Top path: {' → '.join(item['strongest_path'])}")
```

### Example 4: Experiment Recommendation (End-to-End)

```python
from agent_kit.tools.semantic_graph import recommend_interventions

# Get experiment plans for top lever
experiments = recommend_interventions({
    'node': 'Budget',
    'target': 'Revenue',
    'graph_path': 'outputs/semantic_graph.json',
    'historical_data': 'data/past_campaigns.csv',
    'top_paths': 3
})

# Review recommendations
for exp in experiments['recommendations']:
    print(f"\n📊 Experiment: {exp['name']}")
    print(f"   Lever: {exp['lever']}")
    print(f"   Path: {exp['path']}")
    print(f"   Action: {exp['action']}")
    print(f"   Expected lift: {exp['expected_lift']:.1%}")
    print(f"   Sample size: {exp['sample_size']} per group")
    print(f"   Duration: {exp['duration']}")
    print(f"   Primary KPI: {exp['primary_kpi']}")
    print(f"   Guardrails: {', '.join(exp['guardrails'])}")
```

### Example 5: Agent-Driven Workflow

```python
from agent_kit.orchestrator import OntologyOrchestrator
from openai_agents import Agent, Runner

# Agent discovers and chains tools automatically
agent = Agent(
    name="Revenue Optimizer",
    instructions="""
    You identify high-leverage interventions for business KPIs.
    
    Workflow:
    1. Use analyze_leverage to find top levers for the target KPI
    2. Use build_semantic_graph to understand relationships
    3. Use compute_target_leverage to get targeted scores with SHAP
    4. Use recommend_interventions to generate experiment plans
    5. Present ranked recommendations with expected impact
    """,
    tools=orch.get_openai_tools([
        'ml#LeverageAnalysisTool',
        'ml#SemanticGraphTool',
        'ml#TargetLeverageTool',
        'ml#InterventionRecommenderTool'
    ])
)

# User asks a question → agent chains tools automatically
result = await Runner.run(
    agent,
    "What are the top 3 things I should do to increase revenue this quarter?"
)

# Agent output:
# "Based on semantic leverage analysis and predictive modeling:
#  
#  1. **Budget Reallocation** (Leverage: 1.22)
#     - Action: Shift 15% of budget from low-ROI to high-ROI channels
#     - Expected lift: +20-25% revenue
#     - Path: Budget → Advertising → Sales → Revenue
#     - Experiment: A/B test by customer segment, 4 weeks, n=5000/group
#  
#  2. **Advertising Optimization** (Leverage: 1.21)
#     - Action: Target ads to high-conversion customer segments
#     - Expected lift: +15-20% revenue
#     - Path: Advertising → Customer → Sales → Revenue
#     - Experiment: Multi-armed bandit, 3 weeks, continuous optimization
#  
#  3. **Website Conversion Improvements** (Leverage: 1.07)
#     - Action: Redesign checkout flow to reduce friction
#     - Expected lift: +10-15% revenue
#     - Path: Website → Customer → Sales → Revenue
#     - Experiment: Sequential rollout, 3 weeks, n=10000/group
#  
#  Prioritize #1 (Budget) for fastest impact with lowest implementation risk."
```

---

## Common Pitfalls & Edge Cases

### Pitfall 1: Confusing Correlation with Causation

**Problem**: 
```
Budget and Advertising are semantically close
→ I'll increase both together
```

**Why It Fails**:
- They might be **substitutes** (more budget on ads means less elsewhere)
- Or **complements** (budget enables ads, ads require budget)
- Semantic distance doesn't tell you the relationship direction

**Solution**:
- Use **causal inference** (do-calculus, instrumental variables)
- Run **A/B tests** to measure actual effects
- Build **structural equation models** from data

### Pitfall 2: Over-Interpreting t-SNE Distances

**Problem**:
```
"Website" is 3 units from "Revenue" in the plot
"Budget" is 2 units from "Revenue"
→ Budget must be more important
```

**Why It Fails**:
- t-SNE **doesn't preserve global distances**, only local neighborhoods
- Different runs produce different layouts (stochastic)
- Distances are arbitrary; only clustering matters

**Solution**:
- Use leverage **scores**, not visual distances
- Focus on **cluster membership** and **betweenness**
- Validate with **quantitative metrics** (SHAP, path analysis)

### Pitfall 3: Ignoring Actionability

**Problem**:
```
"Revenue" has high centrality
→ It's a leverage point
```

**Why It Fails**:
- Revenue is an **outcome**, not a lever
- You can't directly "set" revenue
- High centrality ≠ actionable

**Solution**:
- **Always filter by actionability** before ranking
- Mark terms as actionable/observable/fixed in metadata
- Use `actionable_terms` parameter in tools

### Pitfall 4: Not Closing the Loop

**Problem**:
```
Ran experiment, saw lift, moved on
→ Leverage scores remain static
```

**Why It Fails**:
- Real-world dynamics change (seasonality, competition)
- Optimal levers shift over time
- One-time analysis becomes stale

**Solution**:
- **Update graph** with experiment results (strengthen confirmed edges)
- **Retrain models** quarterly with new data
- **Monitor leverage drift** (track top-5 changes over time)
- **Set alerts** if high-leverage nodes drop below threshold

### Edge Case 1: Too Few Terms

**Problem**: Only 3-5 terms provided

**Symptoms**:
- t-SNE fails (needs ≥ perplexity + 1 samples)
- No meaningful clusters
- All leverage scores similar

**Solution**:
- Use `perplexity=2` for small datasets
- Skip dimensionality reduction; use raw embeddings
- Expand term list with ontology extraction

### Edge Case 2: Too Many High-Leverage Nodes

**Problem**: 80% of nodes score >1.0

**Symptoms**:
- Everything looks important
- Hard to prioritize
- Analysis paralysis

**Solution**:
- **Increase specificity**: Add more features to distinguish nodes
- **Filter by practicality**: Consider implementation cost/time
- **Sequential testing**: Start with top 1-2, measure, then move to next

### Edge Case 3: No Actionable Terms

**Problem**: All high-leverage nodes are fixed (market size, regulations)

**Symptoms**:
- Top levers all have `actionability=0`
- Can't find interventions

**Solution**:
- **Expand scope**: Include indirect levers (e.g., if you can't change market size, target niche segments)
- **Change KPI**: Focus on a more actionable target (e.g., conversion rate instead of market share)
- **Long-term horizon**: Some levers are slow (product redesign) but still valuable

---

## Summary: The Semantic Leverage Playbook

### 5-Minute Checklist

✅ **Generate t-SNE map** with leverage scores
```bash
python examples/ml_leverage_discovery_demo.py
```

✅ **Identify high-leverage, actionable nodes**
- Look for red circles
- Filter by actionability

✅ **Build semantic graph** to understand pathways
```python
build_semantic_graph({'terms': [...], 'threshold': 0.7})
```

✅ **Compute targeted leverage** for your KPI
```python
compute_target_leverage({'target': 'Revenue', 'graph_path': '...'})
```

✅ **Generate experiment recommendations**
```python
recommend_interventions({'node': 'Budget', 'target': 'Revenue'})
```

✅ **Run A/B test** on top lever

✅ **Close the loop**: Update graph + models with results

---

## Next Steps

### For Practitioners
1. **Run the demo**: `python examples/ml_leverage_discovery_demo.py`
2. **Adapt to your domain**: Replace example terms with your business entities
3. **Validate with data**: Train model, compute SHAP, cross-check leverage scores
4. **Ship experiments**: Start with top 1-2 levers, measure lift

### For Researchers
1. **Extend to causal graphs**: Replace semantic edges with learned causal structure
2. **Dynamic leverage**: Track how scores shift over time (drift detection)
3. **Multi-objective**: Pareto frontier for competing KPIs (Revenue vs. Satisfaction)
4. **Uncertainty quantification**: Bayesian leverage scores with credible intervals

### For Agent Builders
1. **Implement SemanticGraphToolset** (see next section)
2. **Wire into OpenAI SDK**: Auto-discover and chain tools
3. **Add feedback loops**: Agent tracks experiments, updates leverage automatically
4. **Multi-agent**: Planner agent → Leverage agent → Experiment agent → Monitor agent

---

**Status**: Ready to operationalize semantic leverage analysis in production workflows.

**Contact**: See `LEVERAGE_TOOL_INTEGRATION.md` for implementation details.

