"""Tests for the repository analysis agent."""

from agent_kit.agents.base import AgentResult
from agent_kit.agents.repository_agent import RepositoryAnalysisAgent


def test_repository_analysis_agent_returns_tree_and_ontology(tmp_path) -> None:
    """Agent should produce both tree and ontology artifacts."""
    (tmp_path / 'src').mkdir()
    (tmp_path / 'src' / 'app.py').write_text('print("ok")', encoding='utf-8')
    (tmp_path / 'pyproject.toml').write_text('[project]\nname="demo"', encoding='utf-8')

    agent = RepositoryAnalysisAgent(tmp_path, max_depth=None)
    result = agent.analyze('Break down repo tree and ontology')

    assert isinstance(result, AgentResult)
    tree_output = result.action_result.artifacts['tree']
    ontology_output = result.action_result.artifacts['ontology']

    assert tmp_path.name in tree_output
    assert 'stats' in ontology_output
    assert ontology_output['stats']['files'] >= 2
    assert any('tree' in step.lower() for step in result.plan.steps)
