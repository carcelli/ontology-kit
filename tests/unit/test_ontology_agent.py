"""Unit tests for ontology-aware SDK agent wrapper."""

from pathlib import Path

from agent_kit.agents.ontology_agent import OntologyAgent


class StubSDKAgent:
    """Simple stand-in for the OpenAI Agents SDK Agent."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.name = kwargs.get("name", "stub")

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"StubSDKAgent(name={self.name})"


def test_ontology_agent_builds_instructions_and_context() -> None:
    """OntologyAgent should load ontology metadata and wrap the SDK agent."""
    ontology_path = Path("assets/ontologies/business.ttl")
    agent = OntologyAgent(
        name="Forecaster",
        ontology_path=ontology_path,
        agent_cls=StubSDKAgent,
        tools=[lambda data: data],
    )

    assert isinstance(agent.sdk_agent, StubSDKAgent)
    assert "Forecaster" in agent.instructions
    assert "ontology-grounded" in agent.instructions

    context = agent.generate_context("Revenue")
    assert context["goal"] == "Revenue"
    assert "ontology_matches" in context
    assert agent.tool_signatures()
