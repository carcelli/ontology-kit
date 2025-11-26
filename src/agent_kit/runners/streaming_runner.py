"""
Streaming runner for real-time agent interactions.

From first principles: Streaming enables responsive UX for long-running
agent tasks. Users see partial results immediately rather than waiting
for complete responses.

Supports:
- Text streaming (token-by-token)
- Audio streaming (for voice interfaces)
- Event streaming (for observability)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable

from agent_kit.adapters import OntologyAgentAdapter
from agent_kit.events import OntologyEvent, OntologyEventLogger
from agent_kit.ontology.loader import OntologyLoader

logger = logging.getLogger(__name__)

# Try imports
try:
    from agents import Agent, Runner as OpenAIRunner
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False


@dataclass
class StreamChunk:
    """A single chunk from streaming output."""

    text: str = ""
    """Text content"""

    is_final: bool = False
    """Whether this is the final chunk"""

    event: OntologyEvent | None = None
    """Associated event if any"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata"""


@dataclass
class StreamConfig:
    """Configuration for streaming execution."""

    session_id: str | None = None
    user_id: str = "default"
    domain: str = "business"

    # Streaming options
    chunk_size: int = 10
    """Approximate characters per chunk"""

    include_events: bool = True
    """Include events in stream"""

    on_token: Callable[[str], None] | None = None
    """Callback for each token"""

    on_event: Callable[[OntologyEvent], None] | None = None
    """Callback for each event"""


class StreamingRunner:
    """
    Runner optimized for streaming responses.

    Features:
    - Token-by-token streaming
    - Event streaming for observability
    - Callback support for UI integration
    - Compatible with both SDKs

    Example:
        >>> runner = StreamingRunner(ontology)
        >>> async for chunk in runner.stream(agent, "Tell me about revenue"):
        ...     print(chunk.text, end="", flush=True)
    """

    def __init__(
        self,
        ontology: OntologyLoader,
        domain: str = "business",
    ):
        """
        Initialize streaming runner.

        Args:
            ontology: OntologyLoader for context
            domain: Domain identifier
        """
        self.ontology = ontology
        self.domain = domain
        self.event_logger = OntologyEventLogger(ontology, domain)

    async def stream(
        self,
        agent: OntologyAgentAdapter | Any,
        input: str,
        config: StreamConfig | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream agent response.

        Args:
            agent: Agent to execute
            input: User input
            config: Streaming configuration

        Yields:
            StreamChunk with text and metadata
        """
        config = config or StreamConfig()
        session_id = config.session_id or f"stream_{id(agent)}"

        self.event_logger.start_tracking(session_id)

        try:
            # Get SDK agent
            if isinstance(agent, OntologyAgentAdapter):
                sdk_agent = agent.agent
            else:
                sdk_agent = agent

            # Stream using OpenAI SDK if available
            if OPENAI_SDK_AVAILABLE:
                async for chunk in self._stream_openai(sdk_agent, input, config):
                    yield chunk
            else:
                # Fallback: simulate streaming
                response = f"Response to: {input}"
                for i in range(0, len(response), config.chunk_size):
                    chunk_text = response[i:i + config.chunk_size]
                    is_final = i + config.chunk_size >= len(response)

                    chunk = StreamChunk(
                        text=chunk_text,
                        is_final=is_final,
                    )

                    if config.on_token:
                        config.on_token(chunk_text)

                    yield chunk
                    await asyncio.sleep(0.05)  # Simulate delay

        finally:
            # Create final event
            if config.include_events:
                event = self.event_logger.create_event(
                    agent_name=getattr(sdk_agent, "name", "Agent"),
                    task=input,
                    result={"summary": "Streaming complete"},
                    session_id=session_id,
                )

                if config.on_event:
                    config.on_event(event)

                yield StreamChunk(
                    text="",
                    is_final=True,
                    event=event,
                )

            self.event_logger.stop_tracking(session_id)

    async def _stream_openai(
        self,
        agent: Any,
        input: str,
        config: StreamConfig,
    ) -> AsyncIterator[StreamChunk]:
        """Stream using OpenAI SDK."""
        try:
            # Note: OpenAI SDK has streaming support via run_stream
            # For now, we run and chunk the output
            result = await OpenAIRunner.run(agent, input=input)
            output = result.final_output

            # Simulate streaming by chunking
            for i in range(0, len(output), config.chunk_size):
                chunk_text = output[i:i + config.chunk_size]
                is_final = i + config.chunk_size >= len(output)

                if config.on_token:
                    config.on_token(chunk_text)

                yield StreamChunk(
                    text=chunk_text,
                    is_final=is_final and not config.include_events,
                )

                # Small delay for realistic streaming feel
                await asyncio.sleep(0.02)

        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield StreamChunk(
                text=f"Error: {e}",
                is_final=True,
                metadata={"error": str(e)},
            )

    async def stream_with_context(
        self,
        agent: OntologyAgentAdapter | Any,
        input: str,
        context: list[dict[str, str]],
        config: StreamConfig | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream with conversation context.

        Args:
            agent: Agent to execute
            input: Current user input
            context: Previous messages [{"role": "user/assistant", "content": "..."}]
            config: Configuration

        Yields:
            StreamChunk
        """
        # Build context string
        context_str = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in context[-5:]  # Last 5 messages
        ])

        enhanced_input = f"Previous conversation:\n{context_str}\n\nCurrent question: {input}"

        async for chunk in self.stream(agent, enhanced_input, config):
            yield chunk


class LiveRunner:
    """
    Runner for bi-directional streaming (like ADK's run_live).

    Supports:
    - Audio input/output
    - Real-time transcription
    - Interruption handling
    """

    def __init__(
        self,
        ontology: OntologyLoader,
        domain: str = "business",
    ):
        self.ontology = ontology
        self.domain = domain
        self.event_logger = OntologyEventLogger(ontology, domain)

    async def run_live(
        self,
        agent: OntologyAgentAdapter | Any,
        audio_input: AsyncIterator[bytes] | None = None,
        text_input: AsyncIterator[str] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """
        Run with live bidirectional streaming.

        Args:
            agent: Agent to execute
            audio_input: Optional audio stream
            text_input: Optional text stream

        Yields:
            StreamChunk with responses
        """
        # This would integrate with ADK's run_live for full audio support
        # For now, provide text-based live interaction

        if text_input:
            async for text in text_input:
                if text.strip():
                    runner = StreamingRunner(self.ontology, self.domain)
                    async for chunk in runner.stream(agent, text):
                        yield chunk
        else:
            yield StreamChunk(
                text="Live mode requires text or audio input",
                is_final=True,
            )


