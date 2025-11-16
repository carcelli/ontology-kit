"""
Agent Kit: Ontology-Driven Enterprise Agents

Comprehensive agent framework extending OpenAI Agents SDK with ontology-driven
capabilities, MCP integration, persistent memory, and enterprise-grade orchestration.
"""

__version__ = '0.1.0'
__author__ = 'Agent Kit Team'

# Core vector space and ontology functionality
from agent_kit.ontology import OntologyLoader
from agent_kit.vectorspace import Embedder, VectorIndex

# Ontology-enhanced SDK extensions
from agent_kit.ontology_extensions import OntologyAgent, OntologyMemorySession, OntologyMCPToolFilter

# Agent implementations
from agent_kit.agents import OntologyAgent as BaseOntologyAgent, OntologyOrchestratorAgent

__all__ = [
    # Core functionality
    'Embedder',
    'VectorIndex',
    'OntologyLoader',

    # Ontology-enhanced SDK extensions
    'OntologyAgent',
    'OntologyMemorySession',
    'OntologyMCPToolFilter',

    # Agent implementations
    'BaseOntologyAgent',
    'OntologyOrchestratorAgent',
]

