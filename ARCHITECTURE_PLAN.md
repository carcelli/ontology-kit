# Architecture Plan: Evolving to an Agent Swarm

Based on the analysis of the current architecture, this document outlines a plan to evolve the existing agent framework from a sequential pipeline into a collaborative swarm of specialized agents.

## Current Architecture Summary

The current system is a simple, sequential pipeline. A central `BusinessOrchestrator` runs a hardcoded sequence of two `OntologyAgent` instances (`forecaster` and `optimizer`). Communication is limited to passing the output of one agent to the next. The system's unique feature is its use of an RDF ontology, which is currently used at the individual agent level to provide a domain model. The ontology is NOT used for orchestration, task decomposition, or dynamic agent/tool selection.

## Proposed Architectural Evolution

To evolve this into a swarm, the following architectural changes are proposed:

### 1. Implement a "Planner" Agent for Dynamic Task Decomposition
- **Objective:** Replace the current hardcoded agent sequence with a dynamic task planning system.
- **Action:** Create a new `PlannerAgent` responsible for breaking down high-level goals into a structured plan or a task graph. This agent will use the ontology to understand the problem domain and generate a sequence of steps.

### 2. Enhance the Ontology for Agent and Tool Discovery
- **Objective:** Make the system ontology-driven, enabling dynamic dispatch and tool selection.
- **Action:**
    - Extend the ontology to formally define agent capabilities (e.g., `:CanWriteCode`, `:CanAnalyzeData`).
    - Model tools within the ontology, describing their inputs, outputs, and capabilities.
    - The orchestrator will query the ontology to dispatch tasks to the most suitable agent and for agents to discover tools dynamically.

### 3. Introduce a Shared Communication Context
- **Objective:** Enable true, non-linear collaboration between agents.
- **Action:** Implement a shared state mechanism, such as a "blackboard" or a message bus, where agents can publish and subscribe to information, allowing for more complex and dynamic interactions.

### 4. Generalize Agent Capabilities
- **Objective:** Move beyond the current `OntologyAgent` to support a wider range of specialized agents.
- **Action:**
    - Create new agent classes for specialized tasks (e.g., `GitHubAgent`, `VisualizationAgent`).
    - These agents will leverage the enhanced ontology to discover and use tools relevant to their tasks.