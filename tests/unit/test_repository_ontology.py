"""Tests for repository ontology mapping."""

from agent_kit.ontology.repository_schema import (
    RepoEntityType,
    RepositoryOntologyBuilder,
)
from agent_kit.tools.repository_tree import RepositoryTreeBuilder


def test_repository_ontology_computes_stats(tmp_path) -> None:
    """Ontology builder should infer languages and counts."""
    (tmp_path / 'src').mkdir()
    (tmp_path / 'src' / 'module.py').write_text('def main():\n    return 1\n', encoding='utf-8')
    (tmp_path / 'src' / 'utils.ts').write_text('export const x = 1;', encoding='utf-8')
    (tmp_path / 'README.md').write_text('Example repo', encoding='utf-8')

    tree = RepositoryTreeBuilder(tmp_path).build()
    ontology = RepositoryOntologyBuilder().from_tree(tree)

    stats = ontology.stats()
    assert stats['files'] == 3
    assert stats['directories'] == 1  # only src

    python_files = ontology.find(entity_type=RepoEntityType.FILE, language='Python')
    assert len(python_files) == 1

    languages = stats['languages']
    assert languages['Python'] == 1
    assert languages['TypeScript'] == 1
