"""Unit tests for ontology.loader module."""

from pathlib import Path

import pytest

from agent_kit.ontology import OntologyLoader


@pytest.fixture
def ontology_path() -> str:
    """Get path to test ontology."""
    return str(
        Path(__file__).parent.parent.parent / "assets" / "ontologies" / "core.ttl"
    )


def test_loader_initialization(ontology_path: str) -> None:
    """Test loader initializes correctly."""
    loader = OntologyLoader(ontology_path)
    assert loader.path.exists()


def test_loader_nonexistent_file_raises_error() -> None:
    """Test loading nonexistent file raises error."""
    with pytest.raises(FileNotFoundError):
        OntologyLoader("nonexistent.ttl")


def test_load_ontology(ontology_path: str) -> None:
    """Test loading ontology creates graph."""
    loader = OntologyLoader(ontology_path)
    graph = loader.load()

    assert graph is not None
    assert len(graph) > 0  # Should have some triples


def test_get_classes(ontology_path: str) -> None:
    """Test retrieving all classes."""
    loader = OntologyLoader(ontology_path)
    loader.load()

    classes = loader.get_classes()

    assert len(classes) >= 5  # Agent, Task, Tool, State, Action at minimum

    # Check for expected classes (local names)
    class_names = [c.split("#")[-1] for c in classes]
    assert "Agent" in class_names
    assert "Task" in class_names
    assert "Tool" in class_names


def test_get_properties(ontology_path: str) -> None:
    """Test retrieving all properties."""
    loader = OntologyLoader(ontology_path)
    loader.load()

    properties = loader.get_properties()

    assert len(properties) >= 5

    # Check for expected properties
    prop_names = [p.split("#")[-1] for p in properties]
    assert "hasPrerequisite" in prop_names or "requiresTool" in prop_names


def test_sparql_query(ontology_path: str) -> None:
    """Test SPARQL query execution."""
    loader = OntologyLoader(ontology_path)
    loader.load()

    # Query for all tasks
    sparql = """
    PREFIX : <http://agent_kit.io/ontology#>
    SELECT ?task WHERE {
        ?task a :Task .
    }
    """
    results = loader.query(sparql)

    assert len(results) > 0
    assert "task" in results[0]


def test_query_before_load_raises_error(ontology_path: str) -> None:
    """Test querying before loading raises error."""
    loader = OntologyLoader(ontology_path)

    with pytest.raises(RuntimeError):
        loader.query("SELECT * WHERE { ?s ?p ?o }")


def test_task_tool_relationships(ontology_path: str) -> None:
    """Test querying task-tool relationships."""
    loader = OntologyLoader(ontology_path)
    loader.load()

    sparql = """
    PREFIX : <http://agent_kit.io/ontology#>
    SELECT ?task ?tool WHERE {
        ?task :requiresTool ?tool .
    }
    """
    results = loader.query(sparql)

    # core.ttl has some example tasks with tools
    assert len(results) > 0
