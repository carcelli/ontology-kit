## Tool Organization Guide

**Last Updated**: November 23, 2025  
**Status**: ✅ Complete

---

## Overview

The tool organization system provides a structured way to manage, discover, and use tools across all agents. It uses **ontology-driven categorization** and a **central registry** for maximum flexibility.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   TOOL ONTOLOGY (tools.ttl)                  │
│  • Tool categories, metadata, dependencies                   │
│  • API provider definitions                                  │
│  • Agent-tool compatibility rules                            │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼──────────┐    ┌─────────▼─────────┐
│  ToolRegistry    │    │  Ontology Query   │
│  (Python)        │◄───┤  (SPARQL)         │
│  • In-memory     │    │  • Dynamic tool   │
│    registration  │    │    discovery      │
│  • Filtering     │    │  • Compatibility  │
│  • Cost tracking │    │    checks         │
└────────┬─────────┘    └───────────────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼───┐  ┌──────┐  ┌────────┐  ┌────────┐
│Betting│  │Trading│  │  ML  │  │Business│  │ Ontology│
│ Tools │  │ Tools │  │Tools │  │ Tools  │  │  Tools  │
└───────┘  └───────┘  └──────┘  └────────┘  └────────┘
```

---

## Tool Categories

### 1. **Betting Tools** (`ToolCategory.BETTING`)
- `fetch_odds`: Live odds from sportsbooks
- `fetch_player_props`: Player proposition bets
- `detect_arbitrage`: Arbitrage opportunity detection
- `calculate_implied_probability`: Odds conversion

**Use Case**: PropBettingAgent

### 2. **Trading Tools** (`ToolCategory.TRADING`)
- `fetch_market_data`: Historical OHLCV data
- `calculate_rsi`, `calculate_macd`, `calculate_bollinger_bands`: Technical indicators
- `calculate_indicators`: All indicators at once
- `calculate_volatility`: Historical volatility
- `execute_trade`: Trade execution (paper or live)
- `calculate_sharpe_ratio`: Risk-adjusted returns

**Use Case**: AlgoTradingAgent

### 3. **ML Training Tools** (`ToolCategory.ML_TRAINING`)
- `train_model`: Schedule model training jobs
- `run_cross_validation`: K-fold validation
- `check_job_status`: Job monitoring
- `analyze_leverage`: Leverage point analysis
- `cluster_data`: Clustering algorithms

**Use Case**: ML optimization agents

### 4. **Business Tools** (`ToolCategory.BUSINESS`)
- `predict`: Business outcome prediction
- `optimize`: Business optimization

**Use Case**: Business intelligence agents

### 5. **Ontology Tools** (`ToolCategory.ONTOLOGY`)
- `query_ontology`: SPARQL queries
- `add_ontology_statement`: RDF manipulation

**Use Case**: All agents (foundational)

### 6. **Vector Space Tools** (`ToolCategory.VECTOR_SPACE`)
- `embed`: Text to embeddings
- `embed_batch`: Batch embedding
- `query_vector_index`: Semantic search

**Use Case**: Semantic agents

### 7. **Visualization Tools** (`ToolCategory.VISUALIZATION`)
- `generate_hyperdim_viz`: Hyperdimensional visualizations
- `generate_interactive_leverage_viz`: Interactive charts

**Use Case**: Reporting agents

### 8. **Semantic Graph Tools** (`ToolCategory.SEMANTIC_GRAPH`)
- `build_semantic_graph`: Graph construction
- `compute_target_leverage`: Leverage scoring
- `recommend_interventions`: Experiment recommendations

**Use Case**: Graph analysis agents

### 9. **GitHub Tools** (`ToolCategory.GITHUB`)
- `write_to_github`: Push code to GitHub

**Use Case**: Code generation agents

---

## Usage Examples

### Example 1: Get Tools by Category

```python
from agent_kit.tools.tool_registry import get_global_registry, ToolCategory

registry = get_global_registry()

# Get all betting tools
betting_tools = registry.get_tools_by_category(ToolCategory.BETTING)

# Use with agent
from agents import Agent
agent = Agent(name="BettingAgent", tools=betting_tools)
```

### Example 2: Filter Tools by Cost and Latency

```python
# Get low-cost, fast tools
tools = registry.filter_tools(
    categories=[ToolCategory.TRADING, ToolCategory.BETTING],
    max_cost=0.01,  # Max $0.01 per call
    max_latency_ms=200  # Max 200ms latency
)
```

### Example 3: Estimate Cost

```python
# Estimate cost of running analysis
tool_names = ["fetch_odds", "detect_arbitrage", "calculate_implied_probability"]
total_cost = registry.estimate_cost(tool_names)
print(f"Estimated cost: ${total_cost:.4f}")
```

### Example 4: Ontology-Driven Tool Discovery

```python
from agent_kit.ontology.loader import OntologyLoader

loader = OntologyLoader('assets/ontologies/tools.ttl')
loader.load()

# Query for tools by category
sparql = """
    PREFIX tool: <http://agent-kit.com/ontology/tool#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?tool ?label ?cost ?latency
    WHERE {
        ?tool tool:belongsToCategory tool:BettingCategory ;
              rdfs:label ?label ;
              tool:hasCostEstimate ?cost ;
              tool:hasLatency ?latency .
    }
"""
results = list(loader.graph.query(sparql))
for row in results:
    print(f"{row.label}: ${float(row.cost):.4f}, {row.latency}ms")
```

### Example 5: Agent Factory with Auto Tool Discovery

```python
from agent_kit.factories import AgentFactory

loader = OntologyLoader('assets/ontologies/betting.ttl')
loader.load()

factory = AgentFactory(loader)

# Create agent - tools auto-discovered from ontology
agent = factory.create_agent("bet:PropBettingAgent", bankroll=10000)

# Agent automatically has access to:
# - fetch_odds
# - fetch_player_props
# - detect_arbitrage
# - query_ontology
```

---

## Adding New Tools

### Step 1: Create the Tool Function

```python
# src/agent_kit/tools/my_new_tools.py

from agents import function_tool
from agent_kit.tools.tool_registry import register_tool, ToolCategory

@register_tool(
    category=ToolCategory.BETTING,
    cost_estimate=0.02,
    latency_ms=150,
    requires_api_key=True,
    api_provider="my_provider",
    tags=["sports", "analysis"]
)
@function_tool
def my_new_tool(param1: str, param2: int) -> dict:
    """
    Description of what the tool does.
    
    Args:
        param1: Description
        param2: Description
    
    Returns:
        Result dictionary
    """
    return {"result": "success"}
```

### Step 2: Add to Ontology (Optional)

```turtle
# assets/ontologies/tools.ttl

tool:MyNewTool a tool:Tool ;
    rdfs:label "my_new_tool" ;
    rdfs:comment "Description of what the tool does." ;
    tool:belongsToCategory tool:BettingCategory ;
    tool:hasCostEstimate "0.02"^^xsd:decimal ;
    tool:hasLatency 150 ;
    tool:requiresApiKey "true"^^xsd:boolean ;
    tool:hasPythonIdentifier "my_new_tool" ;
    tool:hasTag "sports", "analysis" .
```

### Step 3: Register in Registry

```python
# src/agent_kit/tools/tool_registry.py (in register_all_tools function)

from agent_kit.tools import my_new_tools

_global_registry.register_tool(
    my_new_tools.my_new_tool,
    ToolCategory.BETTING,
    cost_estimate=0.02,
    latency_ms=150,
    requires_api_key=True,
    api_provider="my_provider",
    tags=["sports", "analysis"]
)
```

---

## Tool Metadata

Each tool has the following metadata:

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Tool function name |
| `category` | str | Tool category |
| `description` | str | What the tool does |
| `cost_estimate` | float | Cost per call ($) |
| `latency_ms` | int | Expected latency (ms) |
| `requires_api_key` | bool | Needs API key? |
| `api_provider` | str | API provider name |
| `dependencies` | list | Other tools required |
| `tags` | list | Search tags |

---

## Tool Dependencies

Some tools depend on others:

```
detect_arbitrage
  └── depends on: fetch_odds

calculate_rsi
  └── depends on: fetch_market_data

compute_target_leverage
  └── depends on: build_semantic_graph
```

The registry tracks dependencies to ensure correct execution order.

---

## Cost & Latency Tracking

### Cost Tracking
```python
# Estimate cost before running
tools_to_use = ["fetch_odds", "fetch_player_props", "detect_arbitrage"]
estimated_cost = registry.estimate_cost(tools_to_use)

if estimated_cost > budget:
    print("Budget exceeded!")
else:
    # Run tools
    pass
```

### Latency Tracking
```python
# Get fast tools only
fast_tools = registry.filter_tools(max_latency_ms=100)
```

---

## API Key Management

Tools that require API keys:

| Tool | Provider | Env Var |
|------|----------|---------|
| `fetch_odds` | The Odds API | `ODDS_API_KEY` |
| `fetch_player_props` | The Odds API | `ODDS_API_KEY` |
| `fetch_market_data` | Alpha Vantage | `ALPHAVANTAGE_API_KEY` |
| `execute_trade` | Broker (Alpaca/Binance) | `BROKER_API_KEY` |
| `write_to_github` | GitHub | `GITHUB_TOKEN` |

Set environment variables:

```bash
export ODDS_API_KEY="your_key_here"
export ALPHAVANTAGE_API_KEY="your_key_here"
export BROKER_API_KEY="your_key_here"
export GITHUB_TOKEN="your_token_here"
```

---

## Best Practices

### 1. **Use Categories for Organization**
Group related tools together. Makes discovery easier.

### 2. **Track Costs**
Always estimate costs before running expensive tools.

### 3. **Tag Everything**
Use descriptive tags for flexible search.

### 4. **Document Dependencies**
Explicit dependencies prevent runtime errors.

### 5. **Ontology-First Design**
Define tools in ontology first, then implement.

### 6. **Test Independently**
Each tool should work standalone.

### 7. **Mock External APIs**
Provide mock implementations for testing.

---

## Troubleshooting

### Tool Not Found
```python
tool = registry.get_tool("my_tool")
if tool is None:
    print("Tool not registered!")
    # Check: Is it imported in tool_registry.py?
```

### API Key Missing
```python
import os
if not os.getenv("ODDS_API_KEY"):
    print("Set ODDS_API_KEY environment variable")
```

### High Costs
```python
# Filter to low-cost tools
cheap_tools = registry.filter_tools(max_cost=0.01)
```

---

## Future Enhancements

1. **Dynamic Tool Loading**: Load tools from plugins
2. **Tool Versioning**: Multiple versions of same tool
3. **Usage Analytics**: Track which tools are used most
4. **Auto-Optimization**: Suggest cheaper tool alternatives
5. **Caching**: Cache tool results to reduce costs
6. **Rate Limiting**: Prevent API quota exhaustion

---

## Summary

The tool organization system provides:

✅ **Centralized registry** for all tools  
✅ **Ontology-driven** categorization  
✅ **Cost and latency** tracking  
✅ **Flexible filtering** by category, tags, cost, latency  
✅ **Dependency management**  
✅ **Easy extensibility** for new tools  

This enables agents to discover and use tools intelligently while staying within budget and latency constraints.

