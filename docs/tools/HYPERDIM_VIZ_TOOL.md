# [Tool] Hyperdimensional Visualization Tool

**Agent-callable tool** for generating t-SNE visualizations of semantic spaces from ontologies or custom terms.

---

## Overview

The `generate_hyperdim_viz` tool enables agents to:
- **Extract terms** from RDF/OWL ontologies automatically
- **Embed semantically** using SentenceTransformers (384D)
- **Reduce dimensions** via t-SNE (2D/3D)
- **Visualize clusters** to reveal semantic relationships
- **Save plots** as PNG files for analysis or viewing

---

## Usage

### Direct Invocation

```python
from agent_kit.tools import generate_hyperdim_viz

# From ontology file
path = generate_hyperdim_viz(
    ontology_path='assets/ontologies/business.ttl',
    n_components=2,
    output_file='business_space.png'
)
# Returns: '/absolute/path/to/business_space.png'
```

### Custom Terms

```python
terms = ['Business', 'Client', 'Revenue', 'Forecast', 'Agent']
path = generate_hyperdim_viz(
    terms=terms,
    n_components=3,  # 3D visualization
    output_file='custom_3d.png'
)
```

### Agent-Driven (OpenAI SDK)

```python
from agents import Agent, Runner, function_tool
from agent_kit.tools import generate_hyperdim_viz

@function_tool
def visualize_ontology(ontology_path: str) -> str:
    """Visualize ontology semantic space."""
    return generate_hyperdim_viz(
        ontology_path=ontology_path,
        output_file='outputs/ontology_viz.png'
    )

agent = Agent(
    name="SemanticAnalyst",
    instructions="Visualize ontologies when asked",
    tools=[visualize_ontology]
)

result = await Runner.run(agent, "Visualize business.ttl")
```

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ontology_path` | `str \| None` | `None` | Path to RDF/OWL file (*.ttl, *.owl) |
| `terms` | `list[str] \| None` | `None` | Custom terms to visualize |
| `model_name` | `str` | `'all-MiniLM-L6-v2'` | SentenceTransformer model |
| `n_components` | `int` | `2` | Output dimensions (2 or 3) |
| `perplexity` | `int \| None` | Auto | t-SNE perplexity (auto: min(30, n-1)) |
| `max_terms` | `int` | `50` | Max terms from ontology |
| `output_file` | `str` | `'hyperdim_viz.png'` | Output PNG path |

**Returns**: Absolute path to saved PNG file (`str`)

**Raises**:
- `ValueError`: No input, <2 terms, invalid dims
- `FileNotFoundError`: Ontology file not found

---

## What the Visualizations Show

### 2D Plot
- **X-axis**: t-SNE Dimension 1
- **Y-axis**: t-SNE Dimension 2
- **Points**: Terms colored by semantic similarity
- **Labels**: Term names annotated

### 3D Plot
- **X, Y, Z**: t-SNE Dimensions 1-3
- **Interactive**: Rotate to explore clusters
- **Depth**: Reveals more nuanced relationships

### Interpretation

| Pattern | Meaning |
|---------|---------|
| **Close proximity** | Semantically related terms |
| **Distant** | Semantically distinct |
| **Clusters** | Groups of related concepts |
| **Bridges** | Terms linking clusters (leverage points!) |

**Example**: "Revenue" near "Forecast" indicates semantic similarity in the embedding space, reflecting their co-occurrence in business contexts.

---

## Examples

### Example 1: Business Ontology

```python
generate_hyperdim_viz(
    ontology_path='assets/ontologies/business.ttl',
    output_file='business_clusters.png'
)
```

**Expected clusters**:
- Business entities: `Business`, `Client`, `Customer`
- Financial terms: `Revenue`, `Forecast`, `Valuation`
- ML terms: `ForecastModel`, `MachineLearning`, `Algorithm`

### Example 2: Core Ontology

```python
generate_hyperdim_viz(
    ontology_path='assets/ontologies/core.ttl',
    max_terms=30,
    output_file='core_structure.png'
)
```

**Expected clusters**:
- Agent concepts: `Agent`, `Tool`, `Capability`
- Relations: `optimizes`, `forecasts`, `generates`
- Processes: `Execution`, `Observation`, `Planning`

### Example 3: Custom Domain Terms

```python
ml_terms = [
    'supervised', 'unsupervised', 'classification', 'regression',
    'neural network', 'decision tree', 'random forest', 'gradient boosting',
    'feature engineering', 'cross-validation', 'hyperparameter tuning'
]
generate_hyperdim_viz(
    terms=ml_terms,
    n_components=3,
    output_file='ml_taxonomy.png'
)
```

---

## Technical Details

### Embedding

- **Model**: `all-MiniLM-L6-v2` (default)
- **Dimension**: 384D
- **Library**: SentenceTransformers
- **Speed**: ~1000 terms/second

### Dimensionality Reduction

- **Algorithm**: t-SNE (t-Distributed Stochastic Neighbor Embedding)
- **Perplexity**: Auto-tuned to `min(30, n_terms - 1)`
- **Random seed**: 42 (deterministic)
- **Preserves**: Local structure (nearby points stay nearby)
- **Trade-off**: Global structure may distort

### Alternative: UMAP

For larger datasets (>100 terms), consider UMAP:

```python
# Install: pip install umap-learn
from umap import UMAP

# Replace t-SNE in code:
umap = UMAP(n_components=2, random_state=42)
embed_low_d = umap.fit_transform(embeddings)
```

**UMAP advantages**:
- Faster on large datasets
- Better global structure preservation
- More stable clusters

---

## Performance

| Terms | Embedding Time | t-SNE Time | Total |
|-------|---------------|------------|-------|
| 10 | <1s | <1s | <2s |
| 50 | <1s | ~2s | ~3s |
| 100 | ~1s | ~5s | ~6s |
| 500 | ~5s | ~30s | ~35s |

**Note**: Times on typical CPU. GPU embedding can be 10x faster.

---

## Edge Cases & Mitigations

### Edge Case 1: Few Terms (<5)

**Issue**: t-SNE may not converge or produce meaningful clusters.

**Mitigation**: Tool accepts ≥2 terms but warns if <5. Consider adding more terms or using direct distance metrics instead of visualization.

### Edge Case 2: Many Terms (>100)

**Issue**: Plot becomes crowded, labels overlap.

**Mitigation**:
- Use `max_terms` parameter to limit extraction
- Consider 3D visualization (`n_components=3`)
- Post-process: Remove labels, color by cluster

### Edge Case 3: Invalid Ontology Format

**Issue**: Parser fails on non-TTL/OWL files.

**Mitigation**: Tool raises `ValueError` with parsing error. Ensure file is valid RDF/OWL.

### Edge Case 4: Memory Exhaustion

**Issue**: Large embeddings (>10K terms) consume RAM.

**Mitigation**:
- Batch process in chunks
- Use `max_terms` to limit
- Consider dimensionality reduction before t-SNE (PCA to 50D first)

---

## Integration Patterns

### Pattern 1: Ontology Quality Assurance

```python
# Agent checks if ontology terms cluster logically
viz_path = generate_hyperdim_viz(ontology_path='new_ontology.ttl')
# Human reviews viz, provides feedback
# Agent iterates ontology design
```

### Pattern 2: Knowledge Discovery

```python
# Agent explores semantic relationships
for ontology in ['business.ttl', 'core.ttl', 'extended.ttl']:
    path = generate_hyperdim_viz(ontology_path=ontology)
    # Agent analyzes clusters, identifies leverage points
```

### Pattern 3: Multi-Ontology Comparison

```python
terms_business = extract_terms('business.ttl')
terms_core = extract_terms('core.ttl')
combined_terms = list(set(terms_business + terms_core))

# Visualize overlap
path = generate_hyperdim_viz(
    terms=combined_terms,
    output_file='ontology_overlap.png'
)
```

---

## Testing

Run unit tests:

```bash
pytest tests/unit/test_hyperdim_viz.py -v
```

**Coverage**:
- ✅ 2D visualization from terms
- ✅ 3D visualization from terms
- ✅ Ontology extraction
- ✅ Terms override ontology
- ✅ Error handling (insufficient terms, invalid input)
- ✅ Custom perplexity
- ✅ Output path validation

---

## Troubleshooting

### Issue: "Need at least 2 terms"

**Cause**: Ontology extraction returned <2 terms or empty `terms` list.

**Fix**: Verify ontology file is valid and contains entities/relations. Or provide `terms` explicitly.

### Issue: "FileNotFoundError"

**Cause**: Ontology path doesn't exist.

**Fix**: Check path is correct and file exists. Use absolute paths if needed.

### Issue: "ValueError: Failed to parse ontology"

**Cause**: Invalid RDF/OWL syntax.

**Fix**: Validate ontology with `rapper` or online validators. Ensure format is Turtle (*.ttl).

### Issue: Crowded Plot

**Cause**: Too many terms extracted.

**Fix**: Reduce `max_terms` parameter or filter terms manually before visualization.

---

## Future Enhancements

### Planned Features

1. **Interactive plots**: Plotly for zoom/pan/hover
2. **Cluster coloring**: Automatic semantic grouping
3. **Hierarchical visualization**: Show ontology class hierarchy
4. **Annotation filtering**: Show only key terms, hide clutter
5. **Comparison mode**: Side-by-side ontology visualizations
6. **Export formats**: SVG, PDF for publications

### Contribution Ideas

- Add PCA pre-reduction for large datasets
- Implement UMAP as alternative to t-SNE
- Support multiple ontology formats (JSON-LD, N-Triples)
- Add agent-driven cluster analysis (identify leverage points)

---

## References

### Papers

- **t-SNE**: ["Visualizing Data using t-SNE"](http://jmlr.org/papers/v9/vandermaaten08a.html), van der Maaten & Hinton, 2008
- **UMAP**: ["UMAP: Uniform Manifold Approximation and Projection"](https://arxiv.org/abs/1802.03426), McInnes et al., 2018
- **SentenceTransformers**: ["Sentence-BERT"](https://arxiv.org/abs/1908.10084), Reimers & Gurevych, 2019

### Libraries

- [SentenceTransformers](https://www.sbert.net/)
- [scikit-learn (t-SNE)](https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html)
- [RDFLib](https://rdflib.readthedocs.io/)
- [Matplotlib](https://matplotlib.org/)

---

## Example Output

### Business Ontology (2D)

```
        Revenue
            |
    Forecast---Client
       |         |
   Business---Customer
       |
  LeveragePoint
```

**Interpretation**: `Revenue`, `Forecast`, and `Business` form a tight cluster (financial domain). `Client` and `Customer` are nearby (semantically similar). `LeveragePoint` bridges to optimization concepts.

---

## Conclusion

The hyperdimensional visualization tool provides **semantic X-ray vision** into ontologies and term relationships. By embedding terms in high-dimensional space and projecting to 2D/3D, it reveals hidden structures that inform:

- **Ontology design**: Identify gaps or redundancies
- **Knowledge discovery**: Find leverage points and semantic bridges
- **Agent navigation**: Guide SPARQL queries toward related concepts
- **Stakeholder communication**: Visual explanations of knowledge structure

**Use it to make the invisible visible.** 🔍

---

**Ship it!** 🚀 Hyperdimensional navigation made visible.

