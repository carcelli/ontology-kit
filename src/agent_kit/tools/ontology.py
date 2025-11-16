# src/agent_kit/tools/ontology.py

from agents import function_tool
from rdflib import Literal, Namespace, URIRef

from agent_kit.ontology.loader import OntologyLoader

# Define namespace for your ontology (best practice: avoid string URIs)
NS = Namespace("http://agent_kit.io/business#")

# In a real application, the path to the ontology would be configurable.
global_ontology_loader = OntologyLoader('assets/ontologies/business.ttl')
global_ontology_loader.load()

@function_tool
def query_ontology(sparql_query: str, ontology_loader: OntologyLoader = global_ontology_loader) -> list[dict]:
    """Execute a SPARQL query against the ontology."""
    results = ontology_loader.query(sparql_query)
    return results

@function_tool
def add_ontology_statement(
    subject: str,
    predicate: str,
    object_value: str,
    ontology_loader: OntologyLoader = global_ontology_loader, # Added parameter
    object_type: str | None = "literal"  # "uri" or "literal" for flexibility
) -> str:
    """
    Adds a new RDF triple to the ontology graph and persists it.

    Args:
        subject: Subject URI (e.g., "insight_002").
        predicate: Predicate URI (e.g., "informs_process").
        object_value: Object value (e.g., "outreach_campaign_005").
        ontology_loader: Instance of OntologyLoader to modify.
        object_type: "uri" for URIRef, "literal" for Literal.

    Returns:
        Confirmation message (e.g., for agent logging).

    Raises:
        ValueError: If triple is invalid.
    """
    try:
        subj = URIRef(NS[subject])  # Prefix for consistency
        pred = URIRef(NS[predicate])
        if object_type == "uri":
            obj = URIRef(NS[object_value])
        elif object_type == "literal":
            obj = Literal(object_value)
        else:
            raise ValueError(f"Invalid object_type: {object_type}")

        # Basic validation: check if predicate is known (extend with your schema)
        # For now, we'll allow any predicate to simplify, but in a real system,
        # you'd validate against your ontology's defined properties.
        # if pred not in [RDFS.subClassOf, RDF.type]:
        #     raise ValueError(f"Unknown predicate: {predicate}")

        ontology_loader.add_triple(subj, pred, obj)
        ontology_loader.save()  # Persist immediately (or batch in prod)
        return f"Added triple: {subj} {pred} {obj}"

    except Exception as e:  # Broad catch for robustness
        raise ValueError(f"Failed to add triple: {str(e)}") from e
