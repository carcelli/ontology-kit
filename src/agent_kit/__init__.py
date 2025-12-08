"""
Agent Kit: Ontology-Driven Enterprise Agents

Comprehensive agent framework extending OpenAI Agents SDK with ontology-driven
capabilities, MCP integration, persistent memory, and enterprise-grade orchestration.

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    Ontology Layer (Foundation)              │
    │  • SPARQL queries for routing                               │
    │  • Entity extraction & linking                              │
    │  • Domain schemas (business, betting, trading)              │
    │  • Leverage score computation                               │
    └─────────────────────────────────────────────────────────────┘
                                ↓
    ┌─────────────────────────────────────────────────────────────┐
    │                    Adapter Layer (Integration)              │
    │  • OntologyEventLogger (enriches ADK events)                │
    │  • OntologySessionService (wraps ADK sessions)              │
    │  • OntologyAgentAdapter (wraps OpenAI SDK agents)           │
    │  • OntologyToolFilter (filters tools by domain)             │
    │  • OntologyMemoryService (cross-session recall)             │
    │  • OntologyHandoffManager (multi-agent coordination)        │
    └─────────────────────────────────────────────────────────────┘
                                ↓
    ┌─────────────────────────────────────────────────────────────┐
    │                    SDK Layer (Execution)                    │
    │  ┌──────────────────────┐  ┌──────────────────────────┐    │
    │  │   ADK (Infrastructure)│  │  OpenAI SDK (Agents)     │    │
    │  │  • Event System      │  │  • Handoffs              │    │
    │  │  • Session Mgmt      │  │  • Guardrails            │    │
    │  │  • Memory Service    │  │  • MCP Tools             │    │
    │  │  • Evaluation        │  │  • Tracing               │    │
    │  └──────────────────────┘  └──────────────────────────┘    │
    └─────────────────────────────────────────────────────────────┘

Quick Start:
    >>> from agent_kit import OntologyRunner, OntologyAgentAdapter
    >>> from agents import Agent
    >>>
    >>> ontology = OntologyLoader("business.ttl")
    >>> agent = Agent(name="ForecastAgent", instructions="...")
    >>> adapter = OntologyAgentAdapter(agent, ontology, "business")
    >>>
    >>> runner = OntologyRunner(ontology)
    >>> result = await runner.run(adapter, "Forecast next 30 days")
"""

__version__ = "0.2.0"
__author__ = "Agent Kit Team"

# =============================================================================
# Core: Ontology and Vector Space
# =============================================================================
# =============================================================================
# SDK Adapters
# =============================================================================
from agent_kit.adapters import (
    OntologyAgentAdapter,
    OntologyInputGuardrail,
    OntologyOutputGuardrail,
    OntologyToolFilter,
    OpenAISDKAdapter,
)

# =============================================================================
# Base Agents
# =============================================================================
from agent_kit.agents import (
    BaseAgent,
    GrokAgent,
    GrokConfig,
)

# =============================================================================
# Evaluation
# =============================================================================
from agent_kit.evaluation import (
    EvalCase,
    EvalMetrics,
    EvalResult,
    EvalSet,
    OntologyEvaluator,
)

# =============================================================================
# Event System
# =============================================================================
from agent_kit.events import (
    OntologyEvent,
    OntologyEventContent,
    OntologyEventLogger,
)

# =============================================================================
# Memory Service
# =============================================================================
from agent_kit.memory import (
    InMemoryBackend,
    OntologyMemoryService,
)
from agent_kit.ontology import OntologyLoader

# =============================================================================
# Ontology Extensions (Legacy)
# =============================================================================
from agent_kit.ontology_extensions import (
    OntologyAgent,
    OntologyMCPToolFilter,
    OntologyMemorySession,
)

# =============================================================================
# Orchestration
# =============================================================================
from agent_kit.orchestrator import (
    OrchestratorConfig,
    OrchestratorResult,
    UnifiedOrchestrator,
    create_business_orchestrator,
)

# =============================================================================
# Protocols
# =============================================================================
from agent_kit.protocols import (
    AgentProtocol,
    EvaluatorProtocol,
    EventProtocol,
    MemoryServiceProtocol,
    OrchestratorProtocol,
    RunnerProtocol,
    SessionProtocol,
)

# =============================================================================
# Runners
# =============================================================================
from agent_kit.runners import (
    OntologyRunner,
    RunConfig,
    RunResult,
    StreamingRunner,
)

# =============================================================================
# Session Management
# =============================================================================
from agent_kit.sessions import (
    InMemorySessionBackend,
    OntologySessionService,
    SqliteSessionBackend,
    create_session_backend,
)
from agent_kit.vectorspace import Embedder, VectorIndex

__all__ = [
    # Version
    "__version__",
    "__author__",
    # Core
    "OntologyLoader",
    "Embedder",
    "VectorIndex",
    # Adapters
    "OntologyAgentAdapter",
    "OntologyOutputGuardrail",
    "OntologyInputGuardrail",
    "OntologyToolFilter",
    "OpenAISDKAdapter",
    # Events
    "OntologyEvent",
    "OntologyEventContent",
    "OntologyEventLogger",
    # Sessions
    "OntologySessionService",
    "InMemorySessionBackend",
    "SqliteSessionBackend",
    "create_session_backend",
    # Memory
    "OntologyMemoryService",
    "InMemoryBackend",
    # Runners
    "OntologyRunner",
    "RunConfig",
    "RunResult",
    "StreamingRunner",
    # Evaluation
    "OntologyEvaluator",
    "EvalCase",
    "EvalSet",
    "EvalResult",
    "EvalMetrics",
    # Orchestration
    "UnifiedOrchestrator",
    "OrchestratorConfig",
    "OrchestratorResult",
    "create_business_orchestrator",
    # Base Agents
    "BaseAgent",
    "GrokAgent",
    "GrokConfig",
    # Ontology Extensions
    "OntologyAgent",
    "OntologyMCPToolFilter",
    "OntologyMemorySession",
    # Protocols
    "AgentProtocol",
    "EventProtocol",
    "SessionProtocol",
    "MemoryServiceProtocol",
    "RunnerProtocol",
    "EvaluatorProtocol",
    "OrchestratorProtocol",
]
