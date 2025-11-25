"""
Agent Kit: Ontology-Driven Enterprise Agents

Comprehensive agent framework extending OpenAI Agents SDK with ontology-driven
capabilities, MCP integration, persistent memory, and enterprise-grade orchestration.

Architecture:
    Ontology Layer (Foundation)
        - OntologyLoader: RDF/OWL graph management
        - SPARQL queries for entity relationships
        - Domain schemas (business, betting, trading)
    
    Adapter Layer (Integration)
        - OntologyAgentAdapter: Wraps OpenAI SDK agents
        - OntologyEventLogger: Enriches ADK events
        - OntologySessionService: Wraps ADK sessions
        - OntologyMemoryService: Cross-session recall
    
    SDK Layer (Execution)
        - ADK (Google): Sessions, events, memory infrastructure
        - OpenAI SDK: Agent execution, handoffs, guardrails
"""

__version__ = '0.1.0'
__author__ = 'Agent Kit Team'

# Core vector space and ontology functionality
from agent_kit.ontology import OntologyLoader
from agent_kit.vectorspace import Embedder, VectorIndex

# Ontology-enhanced SDK extensions
from agent_kit.ontology_extensions import (
    OntologyAgent,
    OntologyMCPToolFilter,
    OntologyMemorySession,
)

# Base agent implementations
from agent_kit.agents import BaseAgent, GrokAgent, GrokConfig

# SDK Integration adapters
from agent_kit.adapters import (
    OntologyAgentAdapter,
    OntologyInputGuardrail,
    OntologyOutputGuardrail,
    OntologyToolFilter,
    OpenAISDKAdapter,
)

# Event system
from agent_kit.events import OntologyEvent, OntologyEventContent, OntologyEventLogger

# Session management
from agent_kit.sessions import OntologySessionService

# Memory service
from agent_kit.memory import InMemoryBackend, OntologyMemoryService

__all__ = [
    # Core functionality
    'Embedder',
    'VectorIndex',
    'OntologyLoader',

    # Ontology-enhanced SDK extensions
    'OntologyAgent',
    'OntologyMemorySession',
    'OntologyMCPToolFilter',

    # Base agent implementations
    'BaseAgent',
    'GrokAgent',
    'GrokConfig',

    # SDK Integration adapters
    'OntologyAgentAdapter',
    'OntologyOutputGuardrail',
    'OntologyInputGuardrail',
    'OntologyToolFilter',
    'OpenAISDKAdapter',

    # Event system
    'OntologyEvent',
    'OntologyEventContent',
    'OntologyEventLogger',

    # Session management
    'OntologySessionService',

    # Memory service
    'OntologyMemoryService',
    'InMemoryBackend',
]
