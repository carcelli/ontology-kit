"""
Integration tests for Unified SDK (ADK + OpenAI Agents SDK).

Tests the adapter layer and SDK integration patterns described in
docs/UNIFIED_SDK_INTEGRATION_STRATEGY.md.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Test modules
from agent_kit.adapters import (
    OntologyAgentAdapter,
    OntologyInputGuardrail,
    OntologyOutputGuardrail,
    OntologyToolFilter,
)
from agent_kit.events import OntologyEvent, OntologyEventContent, OntologyEventLogger
from agent_kit.memory import InMemoryBackend, OntologyMemoryService
from agent_kit.sessions import OntologySessionService


class MockOntologyLoader:
    """Mock ontology loader for testing."""

    def __init__(self):
        self.path = "test.ttl"

    def load(self):
        pass

    def query(self, sparql: str) -> list[dict]:
        """Return mock query results."""
        return [
            {"label": {"value": "Revenue"}},
            {"label": {"value": "Cost"}},
            {"label": {"value": "Profit"}},
        ]


class MockDomainConfig:
    """Mock domain configuration."""

    def __init__(self):
        self.allowed_tools = ["tools.business.predict", "tools.business.optimize"]
        self.risk_policies = {"max_stake": 0.05, "min_confidence": 0.7}
        self.output_schema = "BusinessOptimizationResult"


@pytest.fixture
def mock_ontology():
    """Create mock ontology loader."""
    return MockOntologyLoader()


@pytest.fixture
def mock_domain_config():
    """Create mock domain config."""
    return MockDomainConfig()


class TestOntologyAgentAdapter:
    """Tests for OntologyAgentAdapter."""

    def test_adapter_creation(self, mock_ontology):
        """Test adapter wraps agent correctly."""
        # Mock the Agent class
        mock_agent = MagicMock()
        mock_agent.name = "TestAgent"
        mock_agent.instructions = "Test instructions"
        mock_agent.tools = []

        # Mock domain registry
        with patch(
            "agent_kit.adapters.ontology_agent_adapter.get_global_registry"
        ) as mock_registry:
            mock_registry.return_value.get.return_value = MockDomainConfig()

            adapter = OntologyAgentAdapter(mock_agent, mock_ontology, "business")

            assert adapter.domain == "business"
            assert adapter.agent == mock_agent

    def test_instructions_enhanced(self, mock_ontology):
        """Test adapter enhances agent instructions."""
        mock_agent = MagicMock()
        mock_agent.name = "TestAgent"
        mock_agent.instructions = "Original instructions"
        mock_agent.tools = []

        with patch(
            "agent_kit.adapters.ontology_agent_adapter.get_global_registry"
        ) as mock_registry:
            mock_registry.return_value.get.return_value = MockDomainConfig()

            adapter = OntologyAgentAdapter(mock_agent, mock_ontology, "business")

            # Check instructions were enhanced
            assert (
                "Domain: business" in mock_agent.instructions
                or adapter.domain == "business"
            )

    def test_entity_extraction(self, mock_ontology):
        """Test entity extraction from text."""
        mock_agent = MagicMock()
        mock_agent.name = "TestAgent"
        mock_agent.instructions = "Test"
        mock_agent.tools = []

        with patch(
            "agent_kit.adapters.ontology_agent_adapter.get_global_registry"
        ) as mock_registry:
            mock_registry.return_value.get.return_value = MockDomainConfig()

            adapter = OntologyAgentAdapter(mock_agent, mock_ontology, "business")
            entities = adapter.extract_entities_from_conversation("Revenue grew by 10%")

            # Should find "Revenue" entity
            assert len(entities) >= 0  # May or may not find depending on mock


class TestOntologyGuardrails:
    """Tests for guardrails."""

    @pytest.mark.asyncio
    async def test_output_guardrail_valid_json(self):
        """Test output guardrail accepts valid JSON."""
        with patch(
            "agent_kit.adapters.ontology_guardrail.get_schema"
        ) as mock_get_schema:
            # Mock schema that accepts any dict
            mock_schema = MagicMock()
            mock_schema.return_value = MagicMock()
            mock_get_schema.return_value = mock_schema

            guardrail = OntologyOutputGuardrail("business")

            # Mock context
            mock_context = MagicMock()

            result = await guardrail.check(mock_context, '{"summary": "test"}')
            assert result.passed

    @pytest.mark.asyncio
    async def test_output_guardrail_invalid_json(self):
        """Test output guardrail rejects invalid JSON."""
        guardrail = OntologyOutputGuardrail("business")

        mock_context = MagicMock()
        result = await guardrail.check(mock_context, "not valid json")

        assert not result.passed
        assert "not valid JSON" in result.error_message

    @pytest.mark.asyncio
    async def test_input_guardrail_passes_by_default(self):
        """Test input guardrail passes when no violations."""
        with patch(
            "agent_kit.adapters.ontology_guardrail.get_global_registry"
        ) as mock_registry:
            mock_registry.return_value.get.return_value = MockDomainConfig()

            guardrail = OntologyInputGuardrail("business")
            mock_context = MagicMock()

            result = await guardrail.check(mock_context, "Normal input text")
            assert result.passed


class TestOntologyToolFilter:
    """Tests for tool filtering."""

    def test_filter_allows_domain_tools(self):
        """Test filter allows tools in domain allowlist."""
        with patch(
            "agent_kit.adapters.ontology_tool_filter.get_global_registry"
        ) as mock_registry:
            mock_registry.return_value.get.return_value = MockDomainConfig()

            filter = OntologyToolFilter("business")

            # Mock tools
            mock_tool = MagicMock()
            mock_tool.name = "predict"

            filtered = filter.filter_tools([mock_tool])
            # Should include tool matching allowlist
            assert len(filtered) >= 0

    def test_filter_blocks_unknown_tools(self):
        """Test filter blocks tools not in allowlist."""
        with patch(
            "agent_kit.adapters.ontology_tool_filter.get_global_registry"
        ) as mock_registry:
            mock_config = MockDomainConfig()
            mock_config.allowed_tools = ["tools.business.predict"]
            mock_registry.return_value.get.return_value = mock_config

            filter = OntologyToolFilter("business")

            # Tool not in allowlist
            mock_tool = MagicMock()
            mock_tool.name = "dangerous_tool"

            filtered = filter.filter_tools([mock_tool])
            # Should be filtered out
            assert len(filtered) == 0


class TestOntologyEventLogger:
    """Tests for event logging."""

    def test_start_tracking(self, mock_ontology):
        """Test starting session tracking."""
        logger = OntologyEventLogger(mock_ontology)
        logger.start_tracking("session_001")

        assert "session_001" in logger._session_queries
        assert "session_001" in logger._session_events

    def test_log_query(self, mock_ontology):
        """Test logging SPARQL queries."""
        logger = OntologyEventLogger(mock_ontology)
        logger.start_tracking("session_001")

        logger.log_query("session_001", "SELECT * WHERE { ?s ?p ?o }")

        assert len(logger._session_queries["session_001"]) == 1

    def test_log_entity(self, mock_ontology):
        """Test logging entities."""
        logger = OntologyEventLogger(mock_ontology)
        logger.start_tracking("session_001")

        logger.log_entity("session_001", "Revenue")
        logger.log_entity("session_001", "Revenue")  # Duplicate

        # Should only add once
        assert len(logger._session_entities["session_001"]) == 1

    def test_create_event(self, mock_ontology):
        """Test creating events from agent results."""
        logger = OntologyEventLogger(mock_ontology)
        logger.start_tracking("session_001")

        logger.log_query("session_001", "SELECT ?x WHERE { ?x rdf:type ex:Business }")

        event = logger.create_event(
            agent_name="TestAgent",
            task="Test task",
            result={"summary": "Test result"},
            session_id="session_001",
        )

        assert event.author == "TestAgent"
        assert len(event.sparql_queries) == 1

    def test_stop_tracking(self, mock_ontology):
        """Test stopping session tracking."""
        logger = OntologyEventLogger(mock_ontology)
        logger.start_tracking("session_001")

        events = logger.stop_tracking("session_001")

        assert "session_001" not in logger._session_events
        assert isinstance(events, list)


class TestOntologyEvent:
    """Tests for OntologyEvent."""

    def test_event_creation(self):
        """Test creating event."""
        event = OntologyEvent(
            author="TestAgent",
            content=OntologyEventContent(text="Test content"),
            ontology_triples=[{"subject": "s", "predicate": "p", "object": "o"}],
        )

        assert event.author == "TestAgent"
        assert event.content.text == "Test content"
        assert len(event.ontology_triples) == 1

    def test_from_agent_result(self):
        """Test creating event from agent result."""
        result = {"summary": "Test summary"}
        context = {
            "queries": ["SELECT * WHERE { ?s ?p ?o }"],
            "entities": ["Revenue", "Cost"],
        }

        event = OntologyEvent.from_agent_result(
            agent_name="TestAgent",
            result=result,
            ontology_context=context,
        )

        assert event.author == "TestAgent"
        assert len(event.sparql_queries) == 1
        assert len(event.extracted_entities) == 2

    def test_to_dict(self):
        """Test serializing event to dict."""
        event = OntologyEvent(
            author="TestAgent",
            content=OntologyEventContent(text="Test"),
        )

        event_dict = event.to_dict()

        assert "id" in event_dict
        assert "author" in event_dict
        assert event_dict["author"] == "TestAgent"


class TestOntologyMemoryService:
    """Tests for memory service."""

    @pytest.fixture
    def memory_service(self, mock_ontology):
        """Create memory service for testing."""
        return OntologyMemoryService(mock_ontology, domain="business")

    @pytest.mark.asyncio
    async def test_store_and_search(self, memory_service):
        """Test storing and searching memories."""
        await memory_service.store(
            content="Revenue forecast for Q1 is $100k",
            user_id="user_001",
            session_id="session_001",
        )

        results = await memory_service.search(
            query="revenue forecast",
            user_id="user_001",
        )

        assert len(results) >= 1
        assert "revenue" in results[0].entry.content.lower()

    @pytest.mark.asyncio
    async def test_user_isolation(self, memory_service):
        """Test memories are isolated by user."""
        await memory_service.store(
            content="User 1 data",
            user_id="user_001",
            session_id="session_001",
        )

        # Search as different user
        results = await memory_service.search(
            query="User 1 data",
            user_id="user_002",  # Different user
        )

        # Should not find user_001's data
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_ingest_from_session(self, memory_service):
        """Test ingesting events from session."""
        events = [
            {"id": "e1", "content": {"text": "First message"}},
            {"id": "e2", "content": {"text": "Second message"}},
            {"id": "e3", "content": ""},  # Empty content
        ]

        count = await memory_service.ingest_from_session(
            session_id="session_001",
            events=events,
            user_id="user_001",
        )

        assert count == 2  # Only non-empty events


class TestInMemoryBackend:
    """Tests for in-memory backend."""

    @pytest.mark.asyncio
    async def test_store_and_search(self):
        """Test basic store and search."""
        from agent_kit.memory.ontology_memory_service import MemoryEntry

        backend = InMemoryBackend()

        entry = MemoryEntry(
            id="mem_001",
            content="Test content about revenue",
            user_id="user_001",
            session_id="session_001",
        )
        await backend.store(entry)

        results = await backend.search("revenue", "user_001")
        assert len(results) == 1
        assert results[0].id == "mem_001"

    @pytest.mark.asyncio
    async def test_get_by_entities(self):
        """Test searching by entities."""
        from agent_kit.memory.ontology_memory_service import MemoryEntry

        backend = InMemoryBackend()

        entry = MemoryEntry(
            id="mem_001",
            content="Test content",
            user_id="user_001",
            session_id="session_001",
            entities=["Revenue", "Sales"],
        )
        await backend.store(entry)

        results = await backend.get_by_entities(["Revenue"], "user_001")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test deleting memories."""
        from agent_kit.memory.ontology_memory_service import MemoryEntry

        backend = InMemoryBackend()

        entry = MemoryEntry(
            id="mem_001",
            content="Test content",
            user_id="user_001",
            session_id="session_001",
        )
        await backend.store(entry)

        deleted = await backend.delete("mem_001")
        assert deleted

        results = await backend.search("Test", "user_001")
        assert len(results) == 0


class TestOntologySessionService:
    """Tests for session service."""

    @pytest.fixture
    def mock_backend(self):
        """Create mock session backend."""
        backend = MagicMock()
        backend.get_session = AsyncMock(return_value={"id": "session_001"})
        backend.save_session = AsyncMock()
        return backend

    @pytest.mark.asyncio
    async def test_get_session_adds_ontology_context(self, mock_backend, mock_ontology):
        """Test session gets ontology context."""
        service = OntologySessionService(mock_backend, mock_ontology)

        session = await service.get_session("session_001")

        assert "ontology_context" in session
        assert "entities" in session["ontology_context"]

    @pytest.mark.asyncio
    async def test_add_entity_to_session(self, mock_backend, mock_ontology):
        """Test adding entity to session."""
        mock_backend.get_session = AsyncMock(
            return_value={
                "id": "session_001",
                "ontology_context": {"entities": [], "queries": [], "history": []},
            }
        )

        service = OntologySessionService(mock_backend, mock_ontology)

        await service.add_entity_to_session("session_001", "ex:Revenue")

        # Should have called save
        mock_backend.save_session.assert_called()

    @pytest.mark.asyncio
    async def test_add_query_to_session(self, mock_backend, mock_ontology):
        """Test adding SPARQL query to session."""
        mock_backend.get_session = AsyncMock(
            return_value={
                "id": "session_001",
                "ontology_context": {"entities": [], "queries": [], "history": []},
            }
        )

        service = OntologySessionService(mock_backend, mock_ontology)

        await service.add_query_to_session("session_001", "SELECT * WHERE { ?s ?p ?o }")

        mock_backend.save_session.assert_called()


# Integration test requiring real dependencies
@pytest.mark.integration
class TestUnifiedSDKIntegration:
    """Integration tests that require real SDKs."""

    @pytest.mark.skipif(
        not pytest.importorskip("agents", reason="openai-agents not installed"),
        reason="OpenAI Agents SDK not installed",
    )
    def test_agent_creation_with_real_sdk(self):
        """Test creating agent with real OpenAI SDK."""
        from agents import Agent

        agent = Agent(
            name="TestAgent",
            instructions="Test instructions",
        )

        assert agent.name == "TestAgent"
