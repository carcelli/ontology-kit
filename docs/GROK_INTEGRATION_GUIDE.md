# Grok Agent Integration Guide

Complete guide for integrating xAI's Grok into Agent Kit for ontology-driven business intelligence.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Performance & Cost](#performance--cost)
- [Troubleshooting](#troubleshooting)
- [Ethical Considerations](#ethical-considerations)

---

## Overview

### What is GrokAgent?

`GrokAgent` is an ontology-aware AI agent that uses xAI's Grok for advanced reasoning while grounding decisions in RDF/OWL ontologies. This prevents hallucinations and ensures semantic consistency with your business data.

### Key Features

- **Observe-Plan-Act-Reflect Loop**: Complete autonomous agent workflow
- **SPARQL Grounding**: All reasoning anchored in ontology facts
- **Tool Invocation**: Seamlessly calls ML/visualization tools
- **Multi-Turn Learning**: Memory-based improvement over time
- **Retry Logic**: Exponential backoff for rate limit handling

### Use Cases

1. **Small Business Optimization**: Forecast revenue, identify leverage points
2. **Semantic Data Analysis**: Query knowledge graphs with natural language
3. **Automated Reporting**: Generate insights from ontology data
4. **Dynamic Tool Orchestration**: Chain tools based on reasoning

---

## Architecture

### Agent Loop

```
┌─────────────────────────────────────────────────────────────┐
│                       GrokAgent Loop                        │
└─────────────────────────────────────────────────────────────┘
          │
          ├─► 1. OBSERVE
          │    └─► SPARQL query ontology for task context
          │
          ├─► 2. PLAN
          │    └─► Grok generates actionable plan from observations
          │
          ├─► 3. ACT
          │    └─► Execute plan via tool registry
          │
          └─► 4. REFLECT
               └─► Critique results, store learnings in memory
```

### Component Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                        GrokAgent                             │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────────┐ │
│  │ Ontology   │  │ xAI Grok    │  │ Tool Registry        │ │
│  │ (RDF/OWL)  │  │ (grok-beta) │  │ - hyperdim_viz       │ │
│  │            │  │             │  │ - cluster_data       │ │
│  │ SPARQL ────┼─►│ Reasoning   ├─►│ - train_model        │ │
│  │ Query      │  │ (Chat API)  │  │ - custom_tools       │ │
│  └────────────┘  └─────────────┘  └──────────────────────┘ │
│                         │                                    │
│                         ▼                                    │
│                  ┌─────────────┐                            │
│                  │   Memory    │                            │
│                  │ (Reflections)│                           │
│                  └─────────────┘                            │
└──────────────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites

- Python 3.12+
- Agent Kit repository
- xAI API key (get from [https://x.ai/api](https://x.ai/api))

### Install Dependencies

```bash
# Install Agent Kit with Grok support
cd /path/to/agent_kit
pip install -e .[dev]

# Or install specific dependencies
pip install openai>=1.0.0 tenacity>=8.2.0
```

### Set API Key

```bash
# Method 1: Environment variable (recommended for development)
export XAI_API_KEY='your-xai-api-key-here'

# Method 2: .env file (for persistent config)
echo "XAI_API_KEY=your-xai-api-key-here" >> .env

# Method 3: Pass directly in code (not recommended for production)
config = GrokConfig(api_key="your-key")
```

---

## Configuration

### GrokConfig Parameters

```python
from agent_kit.agents import GrokConfig

config = GrokConfig(
    api_key="your-xai-api-key",        # Required: xAI API key
    base_url="https://api.x.ai/v1",    # Optional: API endpoint
    model="grok-beta",                  # Optional: Model version
    temperature=0.7,                    # Optional: 0.0-2.0 (higher = more creative)
    max_tokens=2048,                    # Optional: Max response length
    seed=42                             # Optional: For reproducibility
)
```

### Model Selection

| Model | Description | Best For |
|-------|-------------|----------|
| `grok-beta` | Current production model | General business reasoning |
| `grok-4` | Next-gen (when available) | Complex multi-step analysis |
| `grok-vision` | Multimodal (future) | Image + text analysis |

### Temperature Tuning

- **0.0-0.3**: Deterministic, factual responses (forecasting, data analysis)
- **0.4-0.7**: Balanced creativity and accuracy (recommendations)
- **0.8-1.5**: Creative, exploratory (brainstorming, ideation)
- **1.6-2.0**: Highly creative (edge cases, unconventional solutions)

---

## Usage Examples

### Example 1: Basic Revenue Analysis

```python
import os
from agent_kit.agents import GrokAgent, GrokConfig, AgentTask
from agent_kit.ontology.loader import OntologyLoader

# 1. Load business ontology
loader = OntologyLoader('assets/ontologies/business.ttl')
ontology_graph = loader.load()

# Wrap for agent compatibility
class OntologyWrapper:
    def __init__(self, graph):
        self.g = graph
    def query(self, sparql):
        return self.g.query(sparql)

ontology = OntologyWrapper(ontology_graph)

# 2. Configure Grok
config = GrokConfig(
    api_key=os.getenv('XAI_API_KEY'),
    temperature=0.5,  # Balanced for business analysis
    seed=42
)

# 3. Initialize agent
agent = GrokAgent(config, ontology)

# 4. Run task
task = AgentTask(prompt="Analyze Q4 revenue opportunities for Sunshine Bakery")
result = agent.run(task)

print(result.result)
```

**Output:**
```
Task: Analyze Q4 revenue opportunities for Sunshine Bakery
Observation: Retrieved ontology data: revenue=$140K, budget=$5K, conversion_rate=0.12
Plan: 1. Calculate potential uplift from timing optimization
      2. Identify high-ROI channels for budget reallocation
      3. Generate visualization of leverage points
Action: execute_plan
Result: Top 3 opportunities:
        - Email timing optimization: +$6K (ROI: 2.4x)
        - Channel reallocation: +$4K (ROI: 1.8x)
        - Customer segmentation: +$3K (ROI: 1.6x)
        Total potential: +$13K (9.3% uplift)
```

### Example 2: Tool Invocation (Visualization)

```python
from agent_kit.tools.ml_training import ML_TOOL_REGISTRY

# Register tools
tool_registry = {
    tool_name: tool_entry['function']
    for tool_name, tool_entry in ML_TOOL_REGISTRY.items()
}

agent = GrokAgent(config, ontology, tool_registry=tool_registry)

task = AgentTask(
    prompt="Create an interactive 3D visualization of revenue leverage points"
)
result = agent.run(task)

# Agent will:
# 1. Query ontology for business entities
# 2. Plan to use generate_interactive_leverage_viz tool
# 3. Invoke tool with extracted parameters
# 4. Return path to generated HTML file
```

### Example 3: Multi-Turn Learning

```python
# First task: Initial analysis
task1 = AgentTask(prompt="What are the top revenue drivers?")
result1 = agent.run(task1)

# Second task: Build on previous insights (uses memory)
task2 = AgentTask(
    prompt="Based on those drivers, what's the highest ROI optimization?"
)
result2 = agent.run(task2)

# Third task: Refine further
task3 = AgentTask(
    prompt="How can we improve that optimization for next quarter?"
)
result3 = agent.run(task3)

# Check accumulated learnings
print(f"Agent memory: {len(agent.memory)} reflections")
for i, reflection in enumerate(agent.memory, 1):
    print(f"{i}. {reflection}")
```

### Example 4: Custom System Prompt

```python
custom_prompt = """
You are a retail analytics specialist for small bakeries.
Focus on seasonal patterns, local competition, and supply chain optimization.
Always quantify recommendations with ROI projections.
"""

agent = GrokAgent(
    config,
    ontology,
    tool_registry=tool_registry,
    system_prompt=custom_prompt
)

task = AgentTask(prompt="Optimize inventory for holiday season")
result = agent.run(task)
```

### Example 5: Integration with Existing Agents

```python
# In examples/04_orchestrated_agents.py
from agent_kit.agents import GrokAgent, GrokConfig

# Replace traditional agents with Grok-powered versions
orchestrator = OntologyOrchestrator(ontology_path)

grok_config = GrokConfig(api_key=os.getenv('XAI_API_KEY'))
grok_forecaster = GrokAgent(
    grok_config,
    orchestrator.ontology,
    system_prompt="You are a forecasting specialist. Use time-series analysis."
)

orchestrator.register_agent("grok_forecaster", grok_forecaster)

# Now orchestrator routes tasks to Grok agents
task = AgentTask(prompt="Forecast Q1-Q3 revenue")
result = orchestrator.run(task, max_handoffs=3)
```

---

## API Reference

### GrokAgent Class

#### `__init__(config, ontology, tool_registry=None, system_prompt=None)`

Initialize Grok agent.

**Parameters:**
- `config` (GrokConfig): API configuration
- `ontology` (Ontology): Loaded RDF/OWL ontology
- `tool_registry` (Dict[str, Callable], optional): Tool name → function mapping
- `system_prompt` (str, optional): Custom instructions for agent

**Raises:**
- `ImportError`: If openai package not installed

#### `run(task: AgentTask) -> AgentResult`

Execute full observe-plan-act-reflect loop.

**Parameters:**
- `task` (AgentTask): Task with prompt

**Returns:**
- `AgentResult`: Result with reasoning trace

#### `observe(task: AgentTask) -> AgentObservation`

Query ontology for task-relevant context.

**Returns:**
- `AgentObservation`: SPARQL query results

#### `plan(task, observation) -> AgentPlan`

Generate plan using Grok.

**Returns:**
- `AgentPlan`: Plan with thought process and action

#### `act(plan) -> AgentActionResult`

Execute plan via tools.

**Returns:**
- `AgentActionResult`: Tool execution output

#### `reflect(task, result) -> None`

Critique and store learnings in memory.

**Side Effects:**
- Appends reflection to `agent.memory`

---

## Testing

### Run Unit Tests

```bash
# All Grok agent tests
pytest tests/unit/test_grok_agent.py -v

# Specific test class
pytest tests/unit/test_grok_agent.py::TestGrokAgentInitialization -v

# With coverage
pytest tests/unit/test_grok_agent.py --cov=agent_kit.agents.base --cov-report=html
```

### Mock API Calls

Tests use `pytest-mock` to avoid actual API calls:

```python
@patch('agent_kit.agents.base.OpenAI')
def test_my_feature(mock_openai_class):
    mock_client = MagicMock()
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Test response"))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_class.return_value = mock_client
    
    # Test code here
```

### Integration Testing

Mark tests requiring real API:

```python
@pytest.mark.requires_api
def test_real_grok_integration():
    """Integration test with live xAI API."""
    config = GrokConfig(api_key=os.getenv('XAI_API_KEY'))
    # ... test with real API
```

Run with: `pytest -m requires_api`

---

## Performance & Cost

### Latency

| Operation | Typical Latency | Notes |
|-----------|-----------------|-------|
| Observe (SPARQL) | 10-50ms | Depends on ontology size |
| Plan (Grok API) | 500-2000ms | Network + model inference |
| Act (Tool) | Varies | Depends on tool complexity |
| Reflect (Grok API) | 500-1500ms | Usually shorter prompts |
| **Full Loop** | **1-4 seconds** | End-to-end task execution |

### Optimization Tips

1. **Cache SPARQL Results**: Store frequent queries
2. **Batch Reflections**: Reflect after every N tasks, not every task
3. **Async Execution**: Use `asyncio` for parallel tool calls
4. **Reduce max_tokens**: Lower to 512-1024 for concise tasks

### Cost Estimation

Based on xAI pricing (as of Jan 2025, check [x.ai/pricing](https://x.ai/pricing) for updates):

| Metric | Value |
|--------|-------|
| Price per 1K input tokens | $0.001 |
| Price per 1K output tokens | $0.002 |
| Typical task tokens | 500 input + 300 output |
| Cost per task | ~$0.0011 |

**Monthly Costs for Small Business Use Case:**

- 100 tasks/day × 30 days = 3,000 tasks/month
- 3,000 × $0.0011 = **$3.30/month**

**Scaling:**

- 1,000 tasks/day = ~$33/month
- 10,000 tasks/day = ~$330/month

---

## Troubleshooting

### Issue: `ImportError: openai package required`

**Solution:**
```bash
pip install openai>=1.0.0
```

### Issue: `Authentication error: Invalid API key`

**Solution:**
1. Verify key: `echo $XAI_API_KEY`
2. Regenerate key at [x.ai/api](https://x.ai/api)
3. Ensure no leading/trailing spaces

### Issue: `Rate limit exceeded`

**Solution:**
- Retry logic is automatic (3 attempts with exponential backoff)
- If persistent, reduce request frequency or upgrade plan
- Check usage: [x.ai/dashboard](https://x.ai/dashboard)

### Issue: `Ontology query returns empty results`

**Solution:**
1. Verify ontology loaded: `len(ontology.g) > 0`
2. Check SPARQL syntax in `observe()` method
3. Validate ontology structure with SHACL
4. Add debug print: `print(list(ontology.query(sparql)))`

### Issue: `Tools not being invoked`

**Solution:**
1. Ensure tool registered: `print(agent.tool_registry.keys())`
2. Check action parsing in `plan()` method
3. Add explicit tool mention in system prompt:
   ```python
   system_prompt="You have access to tools: generate_visualization, cluster_data. Use them when appropriate."
   ```

### Issue: `Agent memory not persisting across runs`

**Cause:** Memory is in-memory only (not persisted to disk).

**Solution:** Implement persistence:
```python
import json

# Save memory
with open('agent_memory.json', 'w') as f:
    json.dump(agent.memory, f)

# Load memory
with open('agent_memory.json', 'r') as f:
    agent.memory = json.load(f)
```

---

## Ethical Considerations

### 1. Transparency

**Always disclose AI-generated insights to end users:**

```python
result = agent.run(task)
print("⚠️  This analysis was generated by AI. Please validate with domain experts.")
print(result.result)
```

### 2. Bias Mitigation

**Ontology data can encode biases:**

- Audit ontology for demographic/social biases
- Validate recommendations against diverse stakeholder groups
- Log all agent decisions for accountability

```python
# Log decisions
import structlog
logger = structlog.get_logger()

def run_with_logging(agent, task):
    logger.info("agent.task_start", task=task.prompt)
    result = agent.run(task)
    logger.info("agent.task_complete", result=result.result, memory=agent.memory)
    return result
```

### 3. Data Privacy

**Ontology may contain sensitive business data:**

- Anonymize data before SPARQL queries (remove PII)
- Use xAI's [data retention policies](https://x.ai/privacy)
- Consider on-premise deployment for sensitive industries

```python
def anonymize_ontology(ontology):
    """Remove PII before agent processing."""
    # Example: Replace customer names with IDs
    for subj, pred, obj in ontology.g:
        if "customerName" in str(pred):
            ontology.g.remove((subj, pred, obj))
            ontology.g.add((subj, pred, Literal(f"Customer_{hash(obj)}")))
    return ontology
```

### 4. Human-in-the-Loop

**Critical decisions should require human approval:**

```python
def run_with_approval(agent, task):
    result = agent.run(task)
    print(f"Proposed action: {result.result}")
    
    approval = input("Approve? (y/n): ")
    if approval.lower() == 'y':
        # Execute action
        return result
    else:
        print("Action cancelled by user.")
        return None
```

---

## References

### Papers & Documentation

1. **xAI Grok**: [https://x.ai/blog/grok](https://x.ai/blog/grok)
2. **Ontology-Driven Agents**: Russell & Norvig (2020), *Artificial Intelligence: A Modern Approach*
3. **Tool Use in LLMs**: Schick et al. (2023), "Toolformer: Language Models Can Teach Themselves to Use Tools"
4. **SPARQL 1.1**: [https://www.w3.org/TR/sparql11-query/](https://www.w3.org/TR/sparql11-query/)
5. **ReAct Pattern**: Yao et al. (2023), "ReAct: Synergizing Reasoning and Acting in Language Models"

### External Links

- **xAI API Docs**: [https://x.ai/api](https://x.ai/api)
- **OpenAI Python SDK**: [https://github.com/openai/openai-python](https://github.com/openai/openai-python)
- **Agent Kit Repository**: [Your GitHub URL]

---

## License

This integration is part of Agent Kit, licensed under MIT License.

xAI's Grok usage subject to [xAI Terms of Service](https://x.ai/legal/terms-of-service).

---

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/agent_kit/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/agent_kit/discussions)
- **Email**: dev@agent_kit.io

---

**Last Updated**: January 2025  
**Version**: 0.1.0

