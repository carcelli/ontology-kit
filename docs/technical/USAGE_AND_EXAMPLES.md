# Usage and Examples Guide

This guide details how to use the `ontology-kit` to build and orchestrate agents. It covers basic patterns, advanced orchestration, and hybrid workflows.

## 1. Basic Usage: The Adapter Pattern
The simplest way to use the framework is by wrapping an existing agent (e.g., from `openai-agents`) with the `OntologyAgentAdapter`.

**Why?**
*   Injects domain knowledge from the ontology.
*   Enforces output guardrails (schemas).
*   Logs events to the standardized event system.

**Code Snippet:**
```python
from agents import Agent
from agent_kit import OntologyAgentAdapter, OntologyLoader

# 1. Load Ontology
ontology = OntologyLoader("assets/ontologies/business.ttl")
ontology.load()

# 2. Create Base Agent
base_agent = Agent(name="Analyst", instructions="Analyze market trends.")

# 3. Wrap with Adapter
adapter = OntologyAgentAdapter(base_agent, ontology, domain="business")

# 4. Run
result = await adapter.run("What are the trends for Q3?")
```

## 2. Ontology-Driven Orchestration
For complex tasks, use the `OntologyOrchestratorAgent`. This agent acts as a manager, routing sub-tasks to specialists.

**How it works:**
1.  **Goal Analysis**: The orchestrator receives a high-level goal (e.g., "Optimize revenue").
2.  **Semantic Routing**: It queries the ontology to find agents with the required capabilities. (e.g., Find an agent where `?agent :canPerform :RevenueOptimization`).
3.  **Delegation**: It dispatches tasks to the selected agents.
4.  **Synthesis**: It combines the results into a final answer.

**Example File**: `examples/04_sdk_orchestrator.py`
This example demonstrates a `BusinessOrchestrator` coordinating a `ForecastAgent` and an `OptimizerAgent`.

## 3. Hybrid Orchestration
The framework supports mixing "native" agents (built with `src/agent_kit`) and "external" agents (from SDKs).

**Key Component**: `OpenAISDKAdapter` (`src/agent_kit/adapters/openai_sdk.py`).
This adapter ensures external agents speak the same protocol (`AgentTask`, `AgentResult`) as native agents, allowing them to participate in the same workflow.

**Example File**: `examples/05_hybrid_orchestration.py`
*   **ForecastAgent**: A native, ontology-aware agent for deep reasoning.
*   **ExternalAgent**: An OpenAI SDK agent for reliable data extraction, wrapped in an adapter.
*   **Workflow**: The native agent generates a plan, and the external agent executes specific steps.

## running Examples
All examples are located in the `examples/` directory.

**Prerequisites:**
*   Install dependencies: `pip install -r requirements.txt`
*   Set API key: `export OPENAI_API_KEY='...'`

**Run Command:**
```bash
python examples/05_hybrid_orchestration.py
```
