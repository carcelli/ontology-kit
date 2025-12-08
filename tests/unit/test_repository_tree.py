"""Tests for repository tree construction utilities."""

from pathlib import Path

from agent_kit.tools.repository_tree import (
    RepoNodeType,
    RepositoryTreeBuilder,
    render_tree,
)


def _setup_repo(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "agent.py").write_text('print("hello")', encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_agent.py").write_text("assert True", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Sample Repo", encoding="utf-8")


def test_repository_tree_builder_creates_structure(tmp_path) -> None:
    """Tree builder should walk the repository hierarchy."""
    _setup_repo(tmp_path)

    builder = RepositoryTreeBuilder(tmp_path, max_depth=None)
    tree = builder.build()

    assert tree.node_type == RepoNodeType.REPOSITORY
    names = [node.name for node in tree.walk()]
    assert "src" in names
    assert "tests" in names
    assert "agent.py" in names


def test_render_tree_formats_ascii(tmp_path) -> None:
    """render_tree returns a readable ascii diagram."""
    _setup_repo(tmp_path)
    tree = RepositoryTreeBuilder(tmp_path, max_depth=None).build()

    ascii_tree = render_tree(tree)
    assert tmp_path.name in ascii_tree
    assert "├── src/" in ascii_tree or "└── src/" in ascii_tree
