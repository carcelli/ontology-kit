"""Ontology models for reasoning about repository structures."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from agent_kit.tools.repository_tree import RepoNodeType, RepoTreeNode


class RepoEntityType(str, Enum):
    """Semantic categories for repository entities."""

    REPOSITORY = 'repository'
    DIRECTORY = 'directory'
    FILE = 'file'
    OBJECT = 'object'


class RepoEntity(BaseModel):
    """Ontology entity describing a repository object."""

    id: str
    name: str
    path: str
    entity_type: RepoEntityType
    parent_id: str | None = None
    children: list[str] = Field(default_factory=list)
    language: str | None = None
    size_bytes: int | None = None
    tags: list[str] = Field(default_factory=list)
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RepositoryOntology(BaseModel):
    """Repository ontology container with helper introspection methods."""

    repository: RepoEntity
    entities: dict[str, RepoEntity] = Field(default_factory=dict)

    def add_entity(self, entity: RepoEntity) -> None:
        """Register an entity and link it to its parent."""
        self.entities[entity.id] = entity
        if entity.parent_id:
            parent = self.entities.get(entity.parent_id)
            if parent is None:
                return
            if entity.id not in parent.children:
                parent.children.append(entity.id)

    def get(self, entity_id: str) -> RepoEntity:
        """Return entity with the provided identifier."""
        try:
            return self.entities[entity_id]
        except KeyError as exc:
            raise KeyError(f'Entity {entity_id} not found') from exc

    def children_of(self, entity_id: str) -> list[RepoEntity]:
        """Return direct children of the specified entity."""
        entity = self.get(entity_id)
        return [self.entities[child_id] for child_id in entity.children if child_id in self.entities]

    def find(
        self,
        *,
        entity_type: RepoEntityType | None = None,
        language: str | None = None,
        tag: str | None = None,
    ) -> list[RepoEntity]:
        """Filter entities by type, language, or tag."""
        matches: list[RepoEntity] = []
        for entity in self.entities.values():
            if entity_type and entity.entity_type != entity_type:
                continue
            if language and entity.language != language:
                continue
            if tag and tag not in entity.tags:
                continue
            matches.append(entity)
        return matches

    def language_histogram(self) -> dict[str, int]:
        """Count files per detected language."""
        histogram: dict[str, int] = {}
        for entity in self.entities.values():
            if entity.language:
                histogram[entity.language] = histogram.get(entity.language, 0) + 1
        return histogram

    def stats(self) -> dict[str, Any]:
        """High-level statistics over the ontology."""
        directories = len(self.find(entity_type=RepoEntityType.DIRECTORY))
        files = len(self.find(entity_type=RepoEntityType.FILE))
        languages = self.language_histogram()
        return {
            'total_entities': len(self.entities),
            'directories': directories,
            'files': files,
            'languages': languages,
        }


class RepositoryOntologyBuilder:
    """Construct a RepositoryOntology from a RepoTreeNode hierarchy."""

    DEFAULT_LANGUAGE_MAP: dict[str, str] = {
        '.py': 'Python',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript',
        '.rs': 'Rust',
        '.go': 'Go',
        '.java': 'Java',
        '.cs': 'C#',
        '.cpp': 'C++',
        '.c': 'C',
        '.md': 'Markdown',
        '.rst': 'reStructuredText',
        '.toml': 'TOML',
        '.yml': 'YAML',
        '.yaml': 'YAML',
        '.json': 'JSON',
        '.sh': 'Shell',
    }

    def __init__(self, language_map: dict[str, str] | None = None) -> None:
        self.language_map = language_map or self.DEFAULT_LANGUAGE_MAP
        self._root_path: Path | None = None

    def from_tree(self, root: RepoTreeNode) -> RepositoryOntology:
        """Convert RepoTreeNode tree to a RepositoryOntology."""
        self._root_path = root.path
        repository = RepoEntity(
            id='.',
            name=root.name,
            path=self._as_posix(root.path),
            entity_type=RepoEntityType.REPOSITORY,
            tags=['repository'],
            metadata={'node_type': root.node_type.value},
            description='Repository root',
        )
        ontology = RepositoryOntology(repository=repository, entities={repository.id: repository})
        self._walk(root, ontology, repository.id)
        return ontology

    def _walk(self, node: RepoTreeNode, ontology: RepositoryOntology, parent_id: str) -> None:
        for child in node.children:
            entity = self._node_to_entity(child, parent_id)
            ontology.add_entity(entity)
            if child.children:
                self._walk(child, ontology, entity.id)

    def _node_to_entity(self, node: RepoTreeNode, parent_id: str) -> RepoEntity:
        entity_type = self._map_node_type(node.node_type)
        language = self._infer_language(node)
        tags = [entity_type.value]
        if language:
            tags.append(language.lower())

        metadata = {'node_type': node.node_type.value}
        metadata.update(node.metadata)

        return RepoEntity(
            id=self._make_id(node.path),
            name=node.name,
            path=self._as_posix(node.path),
            entity_type=entity_type,
            parent_id=parent_id,
            language=language,
            size_bytes=node.metadata.get('size_bytes'),
            tags=tags,
            metadata=metadata,
        )

    def _map_node_type(self, node_type: RepoNodeType) -> RepoEntityType:
        if node_type == RepoNodeType.FILE:
            return RepoEntityType.FILE
        if node_type == RepoNodeType.DIRECTORY:
            return RepoEntityType.DIRECTORY
        return RepoEntityType.REPOSITORY

    def _infer_language(self, node: RepoTreeNode) -> str | None:
        if node.node_type != RepoNodeType.FILE:
            return None
        suffix = node.path.suffix.lower()
        return self.language_map.get(suffix)

    def _make_id(self, path: Path) -> str:
        if self._root_path is None:
            return path.as_posix()
        try:
            relative = path.relative_to(self._root_path)
        except ValueError:
            return path.as_posix()
        value = relative.as_posix()
        return value or '.'

    def _as_posix(self, path: Path) -> str:
        return path.as_posix()
