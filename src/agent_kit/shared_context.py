# src/agent_kit/shared_context.py
from typing import Any


class SharedContext:
    """A simple key-value store for agents to share information."""

    def __init__(self):
        self._data: dict[str, Any] = {}

    def set(self, key: str, value: Any):
        """Sets a value in the context."""
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Gets a value from the context."""
        return self._data.get(key, default)

    def get_all(self) -> dict[str, Any]:
        """Gets all data from the context."""
        return self._data.copy()
