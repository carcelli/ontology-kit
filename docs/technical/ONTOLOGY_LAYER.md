# Ontology Layer

The Ontology Layer is the foundation of the `ontology-kit` framework. It serves as the "semantic nervous system," providing a shared vocabulary, a dynamic registry for capabilities, and a mechanism for intelligent memory.

## Ontology Loading & Management
*   **Component**: `OntologyLoader` (`src/agent_kit/ontology/loader.py`).
*   **Technology**: Wraps `rdflib.Graph`.
*   **Functions**:
    *   **Loading**: Parses RDF/TTL files (e.g., `assets/ontologies/*.ttl`) into an in-memory graph.
    *   **Querying**: Executes SPARQL queries with result caching for performance.
    *   **Persistence**: Saves changes back to the ontology files, allowing the system to learn and evolve.

## Type-Safe Schema
*   **Component**: `src/agent_kit/ontology/business_schema.py`.
*   **Role**: Bridges the gap between the loose graph structure of RDF and the strict typing of Python.
*   **Implementation**: Uses Pydantic models (e.g., `Business`, `LeveragePoint`) to validate and structure data retrieved from the ontology. This ensures that agents operate on reliable, well-defined objects.

## Semantic Memory
*   **Component**: `OntologyMemoryService` (`src/agent_kit/memory/ontology_memory_service.py`).
*   **Concept**: Instead of simple keyword matching, memory retrieval is "semantically aware."
*   **Mechanism**:
    1.  **Entity Extraction**: Identifies key entities in the conversation using the ontology.
    2.  **Query Expansion**: Uses the ontology to find related concepts (e.g., if discussing "Sales", also look for "Revenue" and "Marketing").
    3.  **Storage**: Persists conversation context and learned facts, linked to the ontological concepts.

## Ontology Files
The actual knowledge definitions are located in `assets/ontologies/`:
*   `core.ttl`: Fundamental concepts.
*   `business.ttl`: Business domain specific concepts.
*   `tools.ttl`: Tool definitions and capabilities.
