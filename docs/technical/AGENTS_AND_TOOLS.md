# Agents and Tools Architecture

The `ontology-kit` employs a hybrid agent architecture and a sophisticated tool management system. This allows for both highly customized, policy-driven agents and the integration of external agent frameworks.

## Agents

The framework utilizes two distinct agent patterns:

### 1. Custom Base Agent
*   **Definition**: `src/agent_kit/agents/base.py`
*   **Lifecycle**: Defines a strict `Observe-Plan-Act-Reflect` loop.
*   **Key Implementation**: `OntologyOrchestratorAgent` (`src/agent_kit/agents/orchestrator.py`).
    *   Acts as the central coordinator.
    *   Routes tasks to specialist agents.
    *   Enforces domain-specific policies defined in the ontology.

### 2. External SDK Agents
*   **Definition**: Wraps the `agents.Agent` class from the `openai-agents` library.
*   **Key Implementations**:
    *   `OntologyAgent` (`src/agent_kit/agents/ontology_agent.py`): Dynamically generates its system instructions and discovers tools using SPARQL queries against the ontology.
    *   `GitHubAgent` (`src/agent_kit/agents/code_writer_agent.py`): Specialized for code operations, also leveraging ontology-based configuration.

## Tools

Tools are managed centrally but discovered dynamically.

### Tool Registry
*   **Location**: `src/agent_kit/tools/tool_registry.py`.
*   **Role**:
    *   Registers all available Python functions as tools.
    *   Collects metadata (categories, tags, costs).
    *   Generates OpenAI-compatible tool specifications (`ToolSpec`).

### Ontology-Driven Discovery
*   Tools can be linked to ontological concepts.
*   The `OntologyOrchestrator` can query the ontology to find tools that match a specific "capability" or "intent" requested by the user.
*   This allows the system to support new tools simply by updating the ontology and registering the python function, without changing agent code.

### Tool Implementation
*   Tools are standard Python functions.
*   They often use the `OntologyLoader` (`src/agent_kit/tools/ontology.py`) to read from or write to the shared knowledge graph.
