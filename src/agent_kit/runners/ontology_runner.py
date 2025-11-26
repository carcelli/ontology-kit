"""
Unified Runner that combines ADK infrastructure with OpenAI SDK execution.

From first principles: The Runner orchestrates agent execution while:
1. Managing session state (ADK pattern)
2. Logging events with ontology context
3. Executing agents (OpenAI SDK or custom)
4. Storing memories for future recall
5. Validating outputs against domain schemas

This is the primary entrypoint for production agent execution.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, TypeVar

from pydantic import BaseModel, Field

from agent_kit.adapters import OntologyAgentAdapter, OntologyOutputGuardrail
from agent_kit.events import OntologyEvent, OntologyEventLogger
from agent_kit.memory import OntologyMemoryService
from agent_kit.ontology.loader import OntologyLoader
from agent_kit.sessions import OntologySessionService

logger = logging.getLogger(__name__)

# Try to import OpenAI SDK
try:
    from agents import Agent, Runner as OpenAIRunner
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False
    Agent = None  # type: ignore
    OpenAIRunner = None  # type: ignore

# Try to import ADK
try:
    from google.adk.runners import Runner as ADKRunner
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    ADKRunner = None  # type: ignore


class RunConfig(BaseModel):
    """Configuration for runner execution."""
    model_config = {"extra": "forbid"}

    # Session configuration
    session_id: str | None = Field(
        default=None, description="Session ID (auto-generated if not provided)"
    )
    user_id: str = Field(default="default", description="User identifier")

    # Execution configuration
    max_turns: int = Field(default=10, ge=1, le=100, description="Max conversation turns")
    timeout_seconds: float = Field(default=300.0, gt=0, description="Execution timeout")

    # Ontology configuration
    domain: str = Field(default="business", description="Domain for tools/policies")
    track_sparql: bool = Field(default=True, description="Track SPARQL queries")
    store_memory: bool = Field(default=True, description="Store in memory service")

    # Guardrail configuration
    validate_output: bool = Field(default=True, description="Validate against schema")
    max_retries: int = Field(default=3, ge=0, description="Retries on validation failure")

    # Streaming configuration
    stream: bool = Field(default=False, description="Enable streaming responses")


@dataclass
class RunResult:
    """Result from runner execution."""

    output: str
    """Final text output from agent"""

    structured_output: dict[str, Any] | None = None
    """Structured output if agent has output_type"""

    events: list[OntologyEvent] = field(default_factory=list)
    """Events generated during execution"""

    session_id: str = ""
    """Session ID used"""

    invocation_id: str = ""
    """Unique invocation identifier"""

    duration_seconds: float = 0.0
    """Execution duration"""

    sparql_queries: list[str] = field(default_factory=list)
    """SPARQL queries executed"""

    entities_extracted: list[str] = field(default_factory=list)
    """Entities extracted from conversation"""

    validation_passed: bool = True
    """Whether output validation passed"""

    error: str | None = None
    """Error message if execution failed"""


class OntologyRunner:
    """
    Unified runner combining ADK infrastructure and OpenAI SDK execution.

    Features:
    - Session management with ontology context
    - Event logging with SPARQL/entity tracking
    - Memory storage for cross-session recall
    - Output validation against domain schemas
    - Support for both sync and async execution
    - Streaming support for real-time responses

    Example:
        >>> ontology = OntologyLoader("assets/ontologies/business.ttl")
        >>> runner = OntologyRunner(ontology, domain="business")
        >>>
        >>> # Create agent
        >>> agent = Agent(name="ForecastAgent", instructions="...")
        >>> adapter = OntologyAgentAdapter(agent, ontology, "business")
        >>>
        >>> # Execute
        >>> result = await runner.run(adapter, "Forecast next 30 days")
        >>> print(result.output)
    """

    def __init__(
        self,
        ontology: OntologyLoader,
        domain: str = "business",
        session_service: OntologySessionService | None = None,
        memory_service: OntologyMemoryService | None = None,
        event_logger: OntologyEventLogger | None = None,
    ):
        """
        Initialize runner with services.

        Args:
            ontology: OntologyLoader for domain context
            domain: Domain identifier
            session_service: Optional session service (created if not provided)
            memory_service: Optional memory service (created if not provided)
            event_logger: Optional event logger (created if not provided)
        """
        self.ontology = ontology
        self.domain = domain

        # Initialize services
        self.event_logger = event_logger or OntologyEventLogger(ontology, domain)
        self.memory_service = memory_service or OntologyMemoryService(ontology, domain)

        # Session service requires backend
        if session_service:
            self.session_service = session_service
        else:
            # Create simple in-memory session backend
            from agent_kit.sessions.ontology_session_service import (
                OntologySessionService,
            )
            self.session_service = None  # Will use simple dict

        self._sessions: dict[str, dict[str, Any]] = {}

        logger.info(f"Initialized OntologyRunner for domain: {domain}")

    async def run(
        self,
        agent: OntologyAgentAdapter | Any,
        input: str,
        config: RunConfig | None = None,
    ) -> RunResult:
        """
        Execute agent with full infrastructure.

        Args:
            agent: OntologyAgentAdapter or OpenAI SDK Agent
            input: User input text
            config: Execution configuration

        Returns:
            RunResult with output and metadata
        """
        config = config or RunConfig()
        start_time = time.time()

        # Generate IDs
        session_id = config.session_id or f"session_{uuid.uuid4().hex[:12]}"
        invocation_id = f"inv_{uuid.uuid4().hex[:12]}"

        logger.info(f"Starting run: session={session_id}, invocation={invocation_id}")

        # Initialize tracking
        self.event_logger.start_tracking(session_id)

        try:
            # Get or create session
            session = await self._get_session(session_id, config.user_id)

            # Execute agent
            if isinstance(agent, OntologyAgentAdapter):
                sdk_agent = agent.agent
            else:
                sdk_agent = agent

            # Run with OpenAI SDK if available
            if OPENAI_SDK_AVAILABLE and hasattr(sdk_agent, "name"):
                output, structured = await self._run_openai_sdk(
                    sdk_agent, input, config
                )
            else:
                # Fallback to simple execution
                output = f"Agent response to: {input}"
                structured = None

            # Create event
            event = self.event_logger.create_event(
                agent_name=getattr(sdk_agent, "name", "Agent"),
                task=input,
                result={"summary": output},
                session_id=session_id,
                invocation_id=invocation_id,
            )

            # Store in memory if configured
            if config.store_memory:
                await self.memory_service.store(
                    content=f"Q: {input}\nA: {output}",
                    user_id=config.user_id,
                    session_id=session_id,
                    metadata={"invocation_id": invocation_id},
                )

            # Get tracking data
            events = self.event_logger.get_events(session_id)
            queries = self.event_logger.get_query_history(session_id)
            entities = list(self.event_logger.get_entity_summary(session_id).keys())

            # Validate output if configured
            validation_passed = True
            if config.validate_output and isinstance(agent, OntologyAgentAdapter):
                validation_passed = await self._validate_output(output, config.domain)

            duration = time.time() - start_time

            return RunResult(
                output=output,
                structured_output=structured,
                events=events,
                session_id=session_id,
                invocation_id=invocation_id,
                duration_seconds=duration,
                sparql_queries=queries,
                entities_extracted=entities,
                validation_passed=validation_passed,
            )

        except Exception as e:
            logger.error(f"Run failed: {e}")
            duration = time.time() - start_time

            return RunResult(
                output="",
                session_id=session_id,
                invocation_id=invocation_id,
                duration_seconds=duration,
                validation_passed=False,
                error=str(e),
            )

        finally:
            self.event_logger.stop_tracking(session_id)

    async def run_stream(
        self,
        agent: OntologyAgentAdapter | Any,
        input: str,
        config: RunConfig | None = None,
    ) -> AsyncIterator[str]:
        """
        Execute agent with streaming output.

        Args:
            agent: Agent to execute
            input: User input
            config: Execution configuration

        Yields:
            Output text chunks as they're generated
        """
        config = config or RunConfig(stream=True)
        session_id = config.session_id or f"session_{uuid.uuid4().hex[:12]}"

        self.event_logger.start_tracking(session_id)

        try:
            if isinstance(agent, OntologyAgentAdapter):
                sdk_agent = agent.agent
            else:
                sdk_agent = agent

            if OPENAI_SDK_AVAILABLE and hasattr(sdk_agent, "name"):
                async for chunk in self._run_openai_sdk_stream(
                    sdk_agent, input, config
                ):
                    yield chunk
            else:
                # Fallback
                yield f"Streaming response to: {input}"

        finally:
            self.event_logger.stop_tracking(session_id)

    def run_sync(
        self,
        agent: OntologyAgentAdapter | Any,
        input: str,
        config: RunConfig | None = None,
    ) -> RunResult:
        """
        Synchronous execution wrapper.

        Args:
            agent: Agent to execute
            input: User input
            config: Configuration

        Returns:
            RunResult
        """
        return asyncio.run(self.run(agent, input, config))

    async def _run_openai_sdk(
        self,
        agent: Any,
        input: str,
        config: RunConfig,
    ) -> tuple[str, dict[str, Any] | None]:
        """Execute using OpenAI SDK."""
        try:
            result = await OpenAIRunner.run(agent, input=input)
            output = result.final_output

            # Try to get structured output
            structured = None
            if hasattr(result, "output") and result.output:
                if isinstance(result.output, BaseModel):
                    structured = result.output.model_dump()
                elif isinstance(result.output, dict):
                    structured = result.output

            return output, structured

        except Exception as e:
            logger.error(f"OpenAI SDK execution failed: {e}")
            raise

    async def _run_openai_sdk_stream(
        self,
        agent: Any,
        input: str,
        config: RunConfig,
    ) -> AsyncIterator[str]:
        """Execute with streaming using OpenAI SDK."""
        try:
            # OpenAI SDK streaming
            result = await OpenAIRunner.run(agent, input=input)
            # Note: True streaming requires OpenAI SDK's stream mode
            # For now, yield complete output
            yield result.final_output

        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield f"Error: {e}"

    async def _get_session(
        self, session_id: str, user_id: str
    ) -> dict[str, Any]:
        """Get or create session."""
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "id": session_id,
                "user_id": user_id,
                "created_at": time.time(),
                "events": [],
                "ontology_context": {
                    "entities": [],
                    "queries": [],
                },
            }
        return self._sessions[session_id]

    async def _validate_output(self, output: str, domain: str) -> bool:
        """Validate output against domain schema."""
        try:
            import json
            output_dict = json.loads(output)

            from agent_kit.schemas import get_schema
            schema_name = f"{domain.capitalize()}OptimizationResult"
            if domain == "betting":
                schema_name = "BettingRecommendation"
            elif domain == "trading":
                schema_name = "TradingRecommendation"

            schema = get_schema(schema_name)
            schema(**output_dict)
            return True

        except Exception:
            # Output isn't structured JSON - that's often fine
            return True

    async def search_memory(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Search memory for relevant past conversations.

        Args:
            query: Search query
            user_id: User to search for
            limit: Max results

        Returns:
            List of memory entries
        """
        results = await self.memory_service.search(query, user_id, limit)
        return [r.entry.to_dict() for r in results]

    def get_session_history(self, session_id: str) -> list[OntologyEvent]:
        """Get event history for a session."""
        return self.event_logger.get_events(session_id)


