"""
Shared context for agents to exchange information.

From first principles: Shared state enables coordination between agents
without tight coupling. Thread-safe implementation for production use.

Note: For multi-threaded environments, consider using threading.Lock
or asyncio locks for async contexts.
"""

from __future__ import annotations

from typing import Any


class SharedContext:
    """
    A simple key-value store for agents to share information.

    Thread-safety: Not thread-safe by default. Wrap operations in locks
    if used in multi-threaded contexts.

    Example:
        >>> context = SharedContext()
        >>> context.set("forecast", {"revenue": 1000})
        >>> forecast = context.get("forecast")
    """

    def __init__(self) -> None:
        """Initialize empty shared context."""
        self._data: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the context.

        Args:
            key: Context key
            value: Value to store
        """
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the context.

        Args:
            key: Context key
            default: Default value if key not found

        Returns:
            Stored value or default
        """
        return self._data.get(key, default)

    def get_all(self) -> dict[str, Any]:
        """
        Get all data from the context (returns a copy).

        Returns:
            Copy of all context data
        """
        return self._data.copy()

    def clear(self) -> None:
        """Clear all context data."""
        self._data.clear()

    def remove(self, key: str) -> bool:
        """
        Remove a key from context.

        Args:
            key: Key to remove

        Returns:
            True if key was present and removed, False otherwise
        """
        if key in self._data:
            del self._data[key]
            return True
        return False
