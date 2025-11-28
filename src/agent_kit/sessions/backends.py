"""
Session backend implementations for different storage options.

From first principles: Sessions need different backends for different use cases:
- InMemory: Development and testing
- SQLite: Local persistence
- PostgreSQL/Spanner: Production scalability
- VertexAI: Cloud-managed (if using GCP)

Each backend implements the SessionBackend protocol.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class SessionBackend(Protocol):
    """Protocol for session storage backends."""

    async def get_session(self, session_id: str) -> dict[str, Any]:
        """Retrieve session by ID."""
        ...

    async def save_session(self, session_id: str, session_data: dict[str, Any]) -> None:
        """Save session data."""
        ...

    async def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        ...

    async def list_sessions(self, user_id: str | None = None) -> list[str]:
        """List session IDs, optionally filtered by user."""
        ...


class InMemorySessionBackend:
    """
    In-memory session backend for development and testing.

    Sessions are lost when process exits.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}

    async def get_session(self, session_id: str) -> dict[str, Any]:
        """Get or create session."""
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "id": session_id,
                "created_at": time.time(),
                "updated_at": time.time(),
                "events": [],
                "metadata": {},
            }
        return self._sessions[session_id].copy()

    async def save_session(self, session_id: str, session_data: dict[str, Any]) -> None:
        """Save session."""
        session_data["updated_at"] = time.time()
        self._sessions[session_id] = session_data

    async def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    async def list_sessions(self, user_id: str | None = None) -> list[str]:
        """List session IDs."""
        if user_id:
            return [
                sid for sid, data in self._sessions.items()
                if data.get("user_id") == user_id
            ]
        return list(self._sessions.keys())

    def clear(self) -> None:
        """Clear all sessions."""
        self._sessions.clear()


class SqliteSessionBackend:
    """
    SQLite-backed session storage for local persistence.

    Compatible with ADK's SqliteSessionService pattern.
    """

    def __init__(self, db_path: str | Path = "sessions.db"):
        """
        Initialize SQLite backend.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    data TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_user 
                ON sessions(user_id)
            """)
            conn.commit()

    async def get_session(self, session_id: str) -> dict[str, Any]:
        """Get or create session."""
        def _get() -> dict[str, Any]:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT data FROM sessions WHERE session_id = ?",
                    (session_id,)
                )
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])

                # Create new session
                now = time.time()
                session = {
                    "id": session_id,
                    "created_at": now,
                    "updated_at": now,
                    "events": [],
                    "metadata": {},
                }
                conn.execute(
                    """INSERT INTO sessions (session_id, user_id, data, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (session_id, None, json.dumps(session), now, now)
                )
                conn.commit()
                return session

        return await asyncio.to_thread(_get)

    async def save_session(self, session_id: str, session_data: dict[str, Any]) -> None:
        """Save session."""
        def _save() -> None:
            now = time.time()
            session_data["updated_at"] = now
            user_id = session_data.get("user_id")

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO sessions 
                       (session_id, user_id, data, created_at, updated_at)
                       VALUES (?, ?, ?, COALESCE(
                           (SELECT created_at FROM sessions WHERE session_id = ?),
                           ?
                       ), ?)""",
                    (session_id, user_id, json.dumps(session_data),
                     session_id, now, now)
                )
                conn.commit()

        await asyncio.to_thread(_save)

    async def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        def _delete() -> bool:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM sessions WHERE session_id = ?",
                    (session_id,)
                )
                conn.commit()
                return cursor.rowcount > 0

        return await asyncio.to_thread(_delete)

    async def list_sessions(self, user_id: str | None = None) -> list[str]:
        """List session IDs."""
        def _list() -> list[str]:
            with sqlite3.connect(self.db_path) as conn:
                if user_id:
                    cursor = conn.execute(
                        "SELECT session_id FROM sessions WHERE user_id = ?",
                        (user_id,)
                    )
                else:
                    cursor = conn.execute("SELECT session_id FROM sessions")
                return [row[0] for row in cursor.fetchall()]

        return await asyncio.to_thread(_list)


class ADKSessionBackendAdapter:
    """
    Adapter that wraps ADK's session services.

    Use this to integrate with ADK's production backends:
    - VertexAISessionService
    - DatabaseSessionService (Spanner/PostgreSQL)
    """

    def __init__(self, adk_service: Any):
        """
        Initialize with ADK session service.

        Args:
            adk_service: ADK BaseSessionService implementation
        """
        self.adk_service = adk_service

    async def get_session(self, session_id: str) -> dict[str, Any]:
        """Get session from ADK backend."""
        try:
            session = await self.adk_service.get_session(session_id)
            # Convert ADK Session to dict
            return {
                "id": session.id,
                "user_id": getattr(session, "user_id", None),
                "events": [self._event_to_dict(e) for e in session.events],
                "metadata": getattr(session, "state", {}),
            }
        except Exception as e:
            logger.error(f"ADK get_session failed: {e}")
            # Return empty session
            return {
                "id": session_id,
                "events": [],
                "metadata": {},
            }

    async def save_session(self, session_id: str, session_data: dict[str, Any]) -> None:
        """Save to ADK backend (via event appending)."""
        # ADK sessions are event-append only
        # This is a simplified adapter
        logger.warning(
            "ADK sessions don't support full save; use append_event instead")

    async def delete_session(self, session_id: str) -> bool:
        """Delete from ADK backend."""
        try:
            await self.adk_service.delete_session(session_id)
            return True
        except Exception as e:
            logger.error(f"ADK delete_session failed: {e}")
            return False

    async def list_sessions(self, user_id: str | None = None) -> list[str]:
        """List sessions from ADK backend."""
        try:
            sessions = await self.adk_service.list_sessions(user_id=user_id)
            return [s.id for s in sessions]
        except Exception as e:
            logger.error(f"ADK list_sessions failed: {e}")
            return []

    def _event_to_dict(self, event: Any) -> dict[str, Any]:
        """Convert ADK Event to dict."""
        return {
            "id": getattr(event, "id", ""),
            "author": getattr(event, "author", ""),
            "timestamp": getattr(event, "timestamp", 0),
            "content": str(getattr(event, "content", "")),
        }


def create_session_backend(
    backend_type: str = "memory",
    **kwargs: Any,
) -> SessionBackend:
    """
    Factory function to create session backend.

    Args:
        backend_type: Type of backend ("memory", "sqlite", "adk")
        **kwargs: Backend-specific configuration

    Returns:
        SessionBackend instance
    """
    if backend_type == "memory":
        return InMemorySessionBackend()

    elif backend_type == "sqlite":
        db_path = kwargs.get("db_path", "sessions.db")
        return SqliteSessionBackend(db_path)

    elif backend_type == "adk":
        adk_service = kwargs.get("adk_service")
        if not adk_service:
            raise ValueError("adk backend requires adk_service parameter")
        return ADKSessionBackendAdapter(adk_service)

    else:
        raise ValueError(f"Unknown backend type: {backend_type}")
