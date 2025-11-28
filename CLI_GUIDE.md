# Ontology-Kit CLI Guide

## Overview

The Ontology-Kit CLI provides comprehensive access to orchestration, ontology queries, ML workflows, and agent management. It's designed as the foundation for what will become full software.

## Quick Start

```bash
# Show all commands
ontology-kit --help

# Run orchestration
ontology-kit orchestrate run --domain business --goal "Forecast revenue for next 30 days"

# Interactive mode
ontology-kit interactive
```

## Command Groups

### 1. Orchestration (`orchestrate`)

**Run domain orchestration:**
```bash
ontology-kit orchestrate run \
  --domain business \
  --goal "Forecast revenue and find leverage points" \
  --output results.json \
  --verbose
```

**Execute workflows:**
```bash
# Create workflow template
ontology-kit orchestrate workflow --save my_workflow.json

# Execute workflow
ontology-kit orchestrate workflow --workflow-file my_workflow.json
```

### 2. Ontology (`ontology`)

**Query with SPARQL:**
```bash
ontology-kit ontology query \
  --sparql "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10" \
  --ontology business \
  --format table
```

**Explore entities:**
```bash
# Overview
ontology-kit ontology explore --ontology business

# Specific entity
ontology-kit ontology explore --ontology business --entity "Business"
```

### 3. ML Workflows (`ml`)

**Leverage analysis:**
```bash
ontology-kit ml leverage \
  -t Revenue -t Budget -t Marketing \
  -k Revenue \
  -a Budget -a Marketing \
  -o leverage_results.json
```

**Build semantic graph:**
```bash
ontology-kit ml graph \
  -t Revenue -t Budget -t Marketing -t Sales \
  --threshold 0.7 \
  -o outputs/graph.json
```

**Targeted leverage:**
```bash
ontology-kit ml target-leverage \
  --graph outputs/graph.json \
  --target Revenue \
  --top-k 5
```

**Generate interventions:**
```bash
ontology-kit ml interventions \
  --graph outputs/graph.json \
  --node Marketing \
  --target Revenue
```

### 4. Agents (`agent`)

**List agents:**
```bash
ontology-kit agent list
```

**Run individual agent:**
```bash
ontology-kit agent run \
  --name ForecastAgent \
  --domain business \
  --goal "Forecast next quarter"
```

### 5. Tools (`tool`)

**Discover tools:**
```bash
# All tools
ontology-kit tool discover --ontology ml_tools

# By algorithm
ontology-kit tool discover --ontology ml_tools --algorithm t-SNE
```

### 6. Domains

**List domains:**
```bash
ontology-kit list-domains
```

**Validate configs:**
```bash
ontology-kit validate-config --domain business
```

**Status:**
```bash
ontology-kit status
```

## Interactive Mode

Launch REPL for complex workflows:

```bash
ontology-kit interactive
```

Commands:
- `domains` - List domains
- `agents` - List agents
- `run <domain> <goal>` - Execute orchestration
- `help` - Show help
- `exit` - Quit

## Workflow Examples

### Complete Business Analysis

```bash
# 1. Build semantic graph
ontology-kit ml graph -t Revenue Budget Marketing Sales -o graph.json

# 2. Find leverage points
ontology-kit ml target-leverage --graph graph.json --target Revenue --top-k 3

# 3. Generate interventions
ontology-kit ml interventions --graph graph.json --node Marketing --target Revenue

# 4. Run orchestration
ontology-kit orchestrate run --domain business --goal "Forecast and optimize revenue"
```

### Multi-Step Workflow File

Create `workflow.json`:
```json
{
  "name": "Revenue Optimization",
  "steps": [
    {"domain": "business", "goal": "Forecast revenue for next 30 days"},
    {"domain": "business", "goal": "Find top 3 leverage points"},
    {"domain": "business", "goal": "Generate intervention recommendations"}
  ],
  "output": "optimization_results.json"
}
```

Execute:
```bash
ontology-kit orchestrate workflow --workflow-file workflow.json
```

## Architecture

The CLI delegates to:
- **Orchestrator**: Coordinates agents via ontology-driven routing
- **Ontology Loader**: SPARQL queries and entity exploration
- **Agent Factory**: Creates domain-specific agents
- **Tool Registry**: Discovers and executes ML tools
- **Domain Registry**: Manages domain configurations

## Next Steps

This CLI is the foundation for:
1. Web UI (REST API wrapper)
2. Dashboard (real-time monitoring)
3. Workflow builder (visual editor)
4. Agent marketplace (discover/share agents)

