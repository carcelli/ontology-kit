# Architecture Overview

The `ontology-kit` framework is designed to build domain-specific, multi-agent applications using a sophisticated three-layered architecture. This design promotes decoupling, flexibility, and dynamic capability discovery.

## The Three Layers

1.  **Ontology Layer**:
    *   **Role**: Defines the knowledge graph, domain concepts, relationships, and tool definitions using RDF/TTL (Turtle) files.
    *   **Key Components**: `OntologyLoader`, `OntologyOrchestrator`.
    *   **Mechanism**: Uses SPARQL queries to dynamically discover available tools and their capabilities based on the current context.

2.  **Adapter Layer**:
    *   **Role**: Bridges the gap between the abstract ontology definitions and the concrete Python implementations.
    *   **Key Components**: `OntologyAgentAdapter`, `OntologyRunner`.
    *   **Mechanism**: Translates ontological concepts into executable code and standardized interfaces.

3.  **SDK Layer (Agent Kit)**:
    *   **Role**: Provides the runtime environment, agent definitions, orchestration logic, and developer tools.
    *   **Key Components**: `UnifiedOrchestrator`, `AgentProtocol`, `schemas.py`.
    *   **Mechanism**: Manages the application lifecycle, state, memory, and high-level workflows.

## Core Concepts

### Unified Orchestration
The `UnifiedOrchestrator` (`src/agent_kit/orchestrator/unified_orchestrator.py`) serves as the central nervous system. It:
*   Integrates session management, memory, and event handling.
*   Routes tasks to specialized agents.
*   Manages the flow of data using standardized Pydantic schemas.

### Dynamic Tool Discovery
A key innovation is the `OntologyOrchestrator` (`src/agent_kit/orchestrator/ontology_orchestrator.py`). Instead of hard-coding tools, it:
*   Queries the loaded ontology to find tools that match a specific need.
*   Allows the system to extend its capabilities simply by updating the ontology files, without changing the core codebase.

### Protocols & Contracts
The system relies heavily on strict protocols (`src/agent_kit/protocols.py`) and Pydantic models (`src/agent_kit/schemas.py`) to ensure:
*   **Type Safety**: Data exchanged between agents and tools is validated.
*   **Interoperability**: Components can be swapped or upgraded as long as they adhere to the defined interfaces.
