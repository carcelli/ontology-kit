"""Repository tree utilities for describing code bases."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class RepoNodeType(str, Enum):
    """Node categories represented inside a repository tree."""

    REPOSITORY = 'repository'
    DIRECTORY = 'directory'
    FILE = 'file'


@dataclass(slots=True)
class RepoTreeNode:
    """Node in the repository tree with optional children."""

    name: str
    path: Path
    node_type: RepoNodeType
    children: list[RepoTreeNode] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_child(self, child: RepoTreeNode) -> None:
        """Attach a child node."""
        self.children.append(child)

    def is_directory(self) -> bool:
        """Return True when node represents a directory-like object."""
        return self.node_type in {RepoNodeType.REPOSITORY, RepoNodeType.DIRECTORY}

    def walk(self) -> Iterator[RepoTreeNode]:
        """Depth-first traversal over the subtree rooted at this node."""
        yield self
        for child in self.children:
            yield from child.walk()

    def to_dict(self) -> dict[str, Any]:
        """Convert the node (and children) into a serializable dictionary."""
        return {
            'name': self.name,
            'path': str(self.path),
            'type': self.node_type.value,
            'metadata': self.metadata,
            'children': [child.to_dict() for child in self.children],
        }


class RepositoryTreeBuilder:
    """Builds a RepoTreeNode hierarchy for a given repository root."""

    DEFAULT_EXCLUDE_DIRS: set[str] = frozenset(
        {
            '.git',
            '.venv',
            '__pycache__',
            '.pytest_cache',
            '.mypy_cache',
            '.ruff_cache',
            'htmlcov',
            'dist',
            'build',
        }
    )

    DEFAULT_EXCLUDE_EXTS: set[str] = frozenset({'.pyc', '.pyo', '.pyd'})

    def __init__(
        self,
        root_dir: str | Path,
        *,
        exclude_dirs: Sequence[str] | None = None,
        exclude_exts: Sequence[str] | None = None,
        max_depth: int | None = None,
        follow_symlinks: bool = False,
    ) -> None:
        self.root_dir = Path(root_dir).resolve()
        if not self.root_dir.exists():
            raise FileNotFoundError(f'Repository root not found: {self.root_dir}')

        self.exclude_dirs = set(self.DEFAULT_EXCLUDE_DIRS)
        if exclude_dirs:
            self.exclude_dirs.update(exclude_dirs)

        self.exclude_exts = set(self.DEFAULT_EXCLUDE_EXTS)
        if exclude_exts:
            normalized = [ext if ext.startswith('.') else f'.{ext}' for ext in exclude_exts]
            self.exclude_exts.update(normalized)

        self.max_depth = max_depth
        self.follow_symlinks = follow_symlinks

    def build(self) -> RepoTreeNode:
        """Return the repository tree for the configured root."""
        return self._build_node(self.root_dir, depth=0, is_root=True)

    def _build_node(
        self,
        path: Path,
        *,
        depth: int,
        is_root: bool = False,
    ) -> RepoTreeNode:
        if path.is_symlink() and not self.follow_symlinks:
            node_type = RepoNodeType.FILE
        elif path.is_dir():
            node_type = RepoNodeType.REPOSITORY if is_root else RepoNodeType.DIRECTORY
        else:
            node_type = RepoNodeType.FILE

        metadata: dict[str, Any] = {}
        if path.is_file():
            metadata['extension'] = path.suffix
            try:
                metadata['size_bytes'] = path.stat().st_size
            except OSError:
                metadata['size_bytes'] = None

        name = path.name or str(path)
        node = RepoTreeNode(name=name, path=path, node_type=node_type, metadata=metadata)

        if node.is_directory():
            if self.max_depth is None or depth < self.max_depth:
                children = self._iter_children(path)
                for child in children:
                    child_node = self._build_node(
                        child,
                        depth=depth + 1,
                        is_root=False,
                    )
                    node.add_child(child_node)

        return node

    def _iter_children(self, directory: Path) -> Iterable[Path]:
        entries = []
        for entry in directory.iterdir():
            if entry.is_dir():
                if entry.name in self.exclude_dirs:
                    continue
                if entry.is_symlink() and not self.follow_symlinks:
                    continue
            else:
                if entry.suffix in self.exclude_exts:
                    continue
            entries.append(entry)

        # Directories first (alphabetically), then files
        return sorted(entries, key=lambda p: (p.is_file(), p.name.lower()))


def render_tree(node: RepoTreeNode) -> str:
    """Return a human-readable ASCII tree."""

    lines: list[str] = []
    root_suffix = '/' if node.is_directory() else ''
    lines.append(f'{node.name}{root_suffix}')

    def _render(children: list[RepoTreeNode], prefix: str) -> None:
        for index, child in enumerate(children):
            connector = '└── ' if index == len(children) - 1 else '├── '
            suffix = '/' if child.is_directory() else ''
            lines.append(f'{prefix}{connector}{child.name}{suffix}')

            if child.children:
                extension = '    ' if index == len(children) - 1 else '│   '
                _render(child.children, prefix + extension)

    _render(node.children, '')
    return '\n'.join(lines)
