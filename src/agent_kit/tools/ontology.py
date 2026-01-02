# src/agent_kit/tools/ontology.py
"""
Ontology Tools: Interface for agents to interact with the Knowledge Graph.

From First Principles:
Agents need a structured way to "know" things about the business domain (entities, relationships)
beyond just text patterns. The Ontology provides this ground truth.

This module exposes tools to:
1. Query the graph (READ): Answer questions like "Which clients are at risk?"
2. Add statements (WRITE): Record new insights like "Client X is price-sensitive."

Dependencies:
- rdflib: For SPARQL query execution
- OntologyLoader: Wraps the raw RDF file access
"""

from typing import Optional

from rdflib import Literal, Namespace, URIRef

from agent_kit.ontology.loader import OntologyLoader

# Define function_tool as a no-op decorator to keep functions callable in tests.
# This is used by the tool registry to identify tool functions.


def function_tool(func):  # type: ignore
    return func


# Business Ontology Namespace
# TODO: Move this to a central config or the TTL file itself
NS = Namespace("http://agent_kit.io/business#")

# Singleton instance for the loader
_LOADER_INSTANCE: Optional[OntologyLoader] = None
_DEFAULT_ONTOLOGY_PATH = "assets/ontologies/business.ttl"


def get_ontology_loader(path: str = _DEFAULT_ONTOLOGY_PATH) -> OntologyLoader:
    """
    Get or create the global ontology loader instance.

    Implements the Singleton pattern to ensure we only load the graph once.
    Lazy loading prevents import-time errors if the file is missing during tests.
    """
    global _LOADER_INSTANCE

    if _LOADER_INSTANCE is None:
        _LOADER_INSTANCE = OntologyLoader(path)
        try:
            _LOADER_INSTANCE.load()
        except FileNotFoundError:
            # Fallback for dev/test environments where assets might be elsewhere
            # or allow the agent to start with an empty graph if appropriate
            print(
                f"WARNING: Ontology file not found at {path}. Starting with empty graph.")
            # We still return the loader, it just won't have data until added

    return _LOADER_INSTANCE


def reset_loader():
    """Reset the global loader (useful for testing)."""
    global _LOADER_INSTANCE
    _LOADER_INSTANCE = None


@function_tool
def query_ontology(
    sparql_query: str,
    ontology_loader: OntologyLoader | None = None
) -> list[dict]:
    """
    Execute a SPARQL query against the business ontology.

    Use this tool to answer questions about:
    - Business entities (Clients, Products, Markets)
    - Relationships (who bought what, which campaign targeted whom)
    - derived insights (what is the revenue trend)

    Args:
        sparql_query: Valid SPARQL SELECT query.
        ontology_loader: Optional loader instance (for injection). 
                         Defaults to global instance.

    Returns:
        List of results as dictionaries.
    """
    loader = ontology_loader or get_ontology_loader()

    try:
        results = loader.query(sparql_query)
        return results
    except Exception as e:
        # Return error as result so agent can self-correct query
        return [{"error": f"SPARQL execution failed: {str(e)}"}]


@function_tool
def add_ontology_statement(
    subject: str,
    predicate: str,
    object_value: str,
    object_type: str | None = "literal",
    ontology_loader: OntologyLoader | None = None,
) -> str:
    """
    Add a new fact (triple) to the business knowledge graph.

    Use this when the agent discovers new information that should be persisted,
    such as a new customer preference, a verified leverage point, or a completed task.

    Args:
        subject: Subject URI fragment (e.g., "insight_002" -> NS:insight_002).
        predicate: Predicate URI fragment (e.g., "informs_process").
        object_value: Object value (URI fragment or literal text).
        object_type: "uri" for relationships, "literal" for data values (strings, numbers).
        ontology_loader: Optional loader instance.

    Returns:
        Confirmation message.
    """
    try:
        # 1. Resolve URIs using the Business Namespace
        subj = URIRef(NS[subject])
        pred = URIRef(NS[predicate])

        if object_type == "uri":
            obj = URIRef(NS[object_value])
        elif object_type == "literal":
            obj = Literal(object_value)
        else:
            raise ValueError(
                f"Invalid object_type: {object_type}. Must be 'uri' or 'literal'.")

        # 2. Get Loader
        loader = ontology_loader or get_ontology_loader()

        # 3. Add & Persist
        loader.add_triple(subj, pred, obj)

        # NOTE: In high-throughput production, we would batch saves or use a proper Triplestore (Fuseki/Neptune).
        # For this file-based implementation, we save on write to ensure durability.
        loader.save()

        return f"Successfully added fact: {subject} {predicate} {object_value}"

    except Exception as e:
        return f"Error adding statement: {str(e)}"


if __name__ == "__main__":
    # Self-test / Demo when running this file directly
    print("--- Ontology Tool Demo ---")

    # 1. Test Query
    print("\n1. Testing Query...")
    q = """
    PREFIX : <http://agent_kit.io/business#>
    SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 1
    """
    res = query_ontology(q)
    print(f"Result: {res}")

    # 2. Test Add
    print("\n2. Testing Add Statement...")
    msg = add_ontology_statement("TestSubject", "hasTestProperty", "TestValue")
    print(msg)
