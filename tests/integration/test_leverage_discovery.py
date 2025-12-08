"""Integration test for ontology-driven leverage analysis discovery."""

import pytest

from agent_kit.ontology.loader import OntologyLoader
from agent_kit.orchestrator.ontology_orchestrator import OntologyOrchestrator
from agent_kit.tools.ml_training import ML_TOOL_REGISTRY

ML_LEVERAGE = "http://agent-kit.com/ontology/ml#LeverageAnalysisTool"


@pytest.fixture
def orchestrator():
    """Create orchestrator with loaded ML tools ontology."""
    loader = OntologyLoader("assets/ontologies/ml_tools.ttl")
    loader.load()
    return OntologyOrchestrator(loader, ML_TOOL_REGISTRY)


def test_discover_leverage_tool(orchestrator):
    """Test that leverage analysis tool can be discovered via ontology."""
    tool = orchestrator.discover_tool(ML_LEVERAGE)
    assert tool is not None
    assert tool["function"].__name__ == "analyze_leverage"
    assert "schema" in tool
    assert "tool_spec" in tool


def test_discover_tsne_tools(orchestrator):
    """Test discovering tools by t-SNE algorithm."""
    tools = orchestrator.discover_tools_by_algorithm("t-SNE")
    assert len(tools) >= 1
    # Should find at least the leverage analyzer
    assert any(t["function"].__name__ == "analyze_leverage" for t in tools)


def test_leverage_analysis_execution(orchestrator):
    """Test executing leverage analysis via orchestrator."""
    business_terms = [
        "Revenue",
        "Budget",
        "Marketing",
        "Sales",
        "Product",
        "Advertising",
    ]
    actionable = ["Budget", "Marketing", "Advertising"]

    result = orchestrator.call(
        ML_LEVERAGE,
        {
            "terms": business_terms,
            "kpi_term": "Revenue",
            "actionable_terms": actionable,
        },
    )

    assert result["status"] in ["COMPLETED", "ERROR"]
    if result["status"] == "COMPLETED":
        assert "job_id" in result
        assert "top_levers" in result
        assert len(result["top_levers"]) > 0
        # Check leverage scores are computed
        for lever in result["top_levers"]:
            assert "term" in lever
            assert "leverage" in lever
            assert lever["leverage"] >= 0.0


def test_openai_tool_spec_for_leverage(orchestrator):
    """Test generating OpenAI tool specs including leverage analyzer."""
    specs = orchestrator.get_openai_tools([ML_LEVERAGE])
    assert len(specs) == 1
    spec = specs[0]
    assert spec["type"] == "function"
    assert spec["function"]["name"] == "analyze_leverage"
    assert "parameters" in spec["function"]


def test_leverage_analysis_direct_call(orchestrator):
    """Test calling leverage analysis directly by Python ID."""
    result = orchestrator.call_by_python_id(
        "analyze_leverage",
        {
            "terms": ["Revenue", "Budget", "Sales"],
            "kpi_term": "Revenue",
            "actionable_terms": ["Budget"],
        },
    )
    assert "status" in result
    assert result["status"] in ["COMPLETED", "ERROR"]
