# tests/unit/test_ontology_tools.py

import pytest
from rdflib import Literal, URIRef

from agent_kit.ontology.loader import OntologyLoader
from agent_kit.tools.ontology import NS, add_ontology_statement, query_ontology


# Define a temporary ontology file for testing
@pytest.fixture
def temp_ontology_file(tmp_path):
    file = tmp_path / "test_ontology.ttl"
    # Create a minimal initial ontology for testing, using the correct namespace
    initial_content = """
        @prefix : <http://agent_kit.io/business#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        :Business rdfs:label "Business" .
        :biz_001 a :Business ;
                 rdfs:label "Test Business 1" .
    """
    file.write_text(initial_content)
    return str(file)


@pytest.fixture
def temp_ontology_loader(temp_ontology_file):
    loader = OntologyLoader(temp_ontology_file)
    loader.load()
    return loader


def test_query_ontology(temp_ontology_loader):
    """Test querying the ontology."""
    results = query_ontology(
        """
        PREFIX : <http://agent_kit.io/business#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?name WHERE {
            ?s a :Business ;
               rdfs:label ?name .
        }
    """,
        ontology_loader=temp_ontology_loader,
    )
    assert len(results) == 1
    assert str(results[0]["name"]) == "Test Business 1"


def test_add_ontology_statement(temp_ontology_file):
    """Test adding a new statement to the ontology and persisting it."""
    # Create a new loader instance for this test to ensure a clean state
    loader = OntologyLoader(temp_ontology_file)
    loader.load()
    initial_triples = len(loader.graph)

    subject = "new_insight_001"
    predicate = "hasText"
    object_value = "This is a new insight."

    result = add_ontology_statement(
        subject, predicate, object_value, ontology_loader=loader, object_type="literal"
    )
    assert "Added triple" in result

    # Reload the ontology to ensure persistence
    reloaded_loader = OntologyLoader(temp_ontology_file)
    reloaded_loader.load()

    # Verify the triple was added and persisted
    assert len(reloaded_loader.graph) == initial_triples + 1

    # Construct the expected triple using the same NS as the tool
    expected_subject = URIRef(NS[subject])
    expected_predicate = URIRef(NS[predicate])
    expected_object = Literal(object_value)
    assert (
        expected_subject,
        expected_predicate,
        expected_object,
    ) in reloaded_loader.graph

    # Test with object_type="uri"
    subject_uri = "campaign_001"
    predicate_uri = "informsProcess"
    object_value_uri = "process_001"
    result_uri = add_ontology_statement(
        subject_uri,
        predicate_uri,
        object_value_uri,
        ontology_loader=loader,
        object_type="uri",
    )
    assert "Added triple" in result_uri

    reloaded_loader_uri = OntologyLoader(temp_ontology_file)
    reloaded_loader_uri.load()
    expected_subject_uri = URIRef(NS[subject_uri])
    expected_predicate_uri = URIRef(NS[predicate_uri])
    expected_object_uri = URIRef(NS[object_value_uri])
    assert (
        expected_subject_uri,
        expected_predicate_uri,
        expected_object_uri,
    ) in reloaded_loader_uri.graph


def test_add_ontology_statement_invalid_object_type(temp_ontology_file):
    """Test adding a statement with an invalid object type."""
    loader = OntologyLoader(temp_ontology_file)
    loader.load()
    with pytest.raises(ValueError, match="Invalid object_type"):
        add_ontology_statement(
            "s", "p", "o", ontology_loader=loader, object_type="invalid"
        )
