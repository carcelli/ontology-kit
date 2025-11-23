"""
Ontology-enhanced MCP tool filtering for intelligent tool selection.

This module provides ontology-driven tool filtering that can determine
which MCP tools are relevant based on semantic reasoning and business rules.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Try to import from agents SDK, with fallbacks
try:
    from agents.mcp import ToolFilterContext, ToolFilterStatic
    AGENTS_AVAILABLE = True
except ImportError:
    # Fallback definitions when SDK is not available
    from typing import TypedDict
    ToolFilterContext = dict
    ToolFilterStatic = TypedDict('ToolFilterStatic', {})
    AGENTS_AVAILABLE = False

if TYPE_CHECKING:
    try:
        from agents import Agent as AgentBase
        from agents.run_context import RunContextWrapper
    except ImportError:
        AgentBase = Any
        RunContextWrapper = Any


class OntologyMCPToolFilter:
    """
    Ontology-driven MCP tool filter that uses semantic reasoning to determine tool relevance.

    This filter can:
    - Query ontologies to determine tool capabilities
    - Filter tools based on agent roles and permissions
    - Consider semantic relationships between tools and tasks
    - Apply business rules from the knowledge graph
    """

    def __init__(self, ontology_path: str | None = None):
        """
        Initialize the ontology tool filter.

        Args:
            ontology_path: Path to ontology file for semantic filtering
        """
        self.ontology_path = ontology_path
        self.ontology = None
        self.ontology_loader = None

        if ontology_path:
            try:
                from ..ontology.loader import OntologyLoader
                self.ontology_loader = OntologyLoader(ontology_path)
                self.ontology = self.ontology_loader.load()
            except Exception:
                pass  # Continue without ontology if loading fails

        # Initialize embedder for semantic matching (lazy loading)
        self._embedder = None
        self._embedding_cache: dict[str, np.ndarray] = {}

    def create_ontology_filter(
        self,
        agent_name: str | None = None,
        task_domain: str | None = None,
        required_capabilities: list[str] | None = None,
    ) -> ToolFilterStatic:
        """
        Create an ontology-aware tool filter configuration.

        Args:
            agent_name: Name of the agent for role-based filtering
            task_domain: Domain/context for task-based filtering
            required_capabilities: Specific capabilities tools must have

        Returns:
            ToolFilterStatic configuration for ontology-driven filtering
        """
        filter_config: ToolFilterStatic = {}

        if self.ontology and agent_name:
            # Query ontology for tools this agent can use
            allowed_tools = self._get_agent_allowed_tools(agent_name)
            if allowed_tools:
                filter_config["allowed_tool_names"] = allowed_tools

        if required_capabilities:
            filter_config["agent_capabilities"] = required_capabilities

        # Add ontology concepts for semantic filtering
        if task_domain:
            ontology_concepts = self._get_domain_concepts(task_domain)
            if ontology_concepts:
                filter_config["ontology_concepts"] = ontology_concepts

        return filter_config

    def _get_agent_allowed_tools(self, agent_name: str) -> list[str] | None:
        """Query ontology for tools an agent is allowed to use."""
        if not self.ontology:
            return None

        try:
            sparql = f"""
                PREFIX : <http://agent_kit.io/business#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT ?toolName
                WHERE {{
                    ?agent rdfs:label "{agent_name}" ;
                           :canPerform ?capability .
                    ?capability :requiresTool ?tool .
                    ?tool rdfs:label ?toolName .
                }}
            """
            results = list(self.ontology.query(sparql))
            return [str(result.toolName) for result in results if result.toolName]
        except Exception:
            return None

    def _get_domain_concepts(self, domain: str) -> list[str] | None:
        """Get ontology concepts related to a domain."""
        if not self.ontology:
            return None

        try:
            # Simple domain-to-concept mapping
            # In a full implementation, this would query the ontology
            domain_concepts = {
                "development": ["GitHub", "Repository", "Code", "VersionControl"],
                "analysis": ["DataAnalysis", "Visualization", "Statistics"],
                "research": ["WebSearch", "Documentation", "Research"],
                "automation": ["Browser", "Testing", "Deployment"],
            }
            return domain_concepts.get(domain.lower(), [])
        except Exception:
            return None

    def _get_embedder(self):
        """Lazy-load embedder for semantic matching."""
        if self._embedder is None:
            try:
                from ..vectorspace.embedder import Embedder
                self._embedder = Embedder(model_name='all-MiniLM-L6-v2')
            except Exception:
                return None
        return self._embedder

    def _get_embedding(self, text: str) -> np.ndarray | None:
        """Get embedding for text with caching."""
        cache_key = hashlib.md5(text.encode()).hexdigest()
        
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        embedder = self._get_embedder()
        if embedder is None:
            return None
        
        try:
            embedding = embedder.embed(text)
            self._embedding_cache[cache_key] = embedding
            return embedding
        except Exception:
            return None

    def _extract_ontology_concepts(self, text: str) -> list[str]:
        """Extract ontology concepts mentioned in text."""
        if not self.ontology_loader:
            return []
        
        try:
            text_lower = text.lower()
            concepts = []
            
            # Get all classes from ontology
            classes = self.ontology_loader.get_classes()
            for cls_uri in classes:
                local_name = cls_uri.split('#')[-1] if '#' in cls_uri else cls_uri.split('/')[-1]
                if local_name.lower() in text_lower:
                    concepts.append(local_name)
            
            return concepts[:10]
        except Exception:
            return []

    def filter_by_semantic_relevance(
        self,
        tool_name: str,
        tool_description: str,
        agent_context: str | None = None,
        task_context: str | None = None,
        similarity_threshold: float = 0.3,
    ) -> bool:
        """
        Determine if a tool is semantically relevant for the given context.

        Args:
            tool_name: Name of the tool
            tool_description: Description of the tool
            agent_context: Context about the agent using the tool
            task_context: Context about the current task
            similarity_threshold: Minimum cosine similarity for relevance (0.0-1.0)

        Returns:
            True if tool is relevant, False otherwise
        """
        if not self.ontology:
            return True  # Allow all tools if no ontology

        # Build context text
        context_parts = []
        if agent_context:
            context_parts.append(agent_context)
        if task_context:
            context_parts.append(task_context)
        
        if not context_parts:
            return True  # No context to match against
        
        context_text = ' '.join(context_parts)
        tool_text = f"{tool_name} {tool_description}"

        # Use semantic similarity if embedder available
        tool_embedding = self._get_embedding(tool_text)
        context_embedding = self._get_embedding(context_text)
        
        if tool_embedding is not None and context_embedding is not None:
            similarity = float(cosine_similarity([tool_embedding], [context_embedding])[0][0])
            
            # Boost similarity if ontology concepts match
            tool_concepts = self._extract_ontology_concepts(tool_text)
            context_concepts = self._extract_ontology_concepts(context_text)
            
            concept_overlap = len(set(tool_concepts) & set(context_concepts))
            if concept_overlap > 0:
                similarity += 0.2 * min(concept_overlap / max(len(tool_concepts), 1), 1.0)
            
            return similarity >= similarity_threshold

        # Fallback to keyword matching
        relevance_keywords = []
        if agent_context:
            relevance_keywords.extend([w for w in agent_context.lower().split() if len(w) > 3])
        if task_context:
            relevance_keywords.extend([w for w in task_context.lower().split() if len(w) > 3])

        tool_text_lower = tool_text.lower()
        for keyword in relevance_keywords:
            if keyword in tool_text_lower:
                return True

        return False

    def get_tool_capability_score(
        self,
        tool_name: str,
        required_capabilities: list[str],
    ) -> float:
        """
        Score how well a tool matches required capabilities using ontology relationships.

        Args:
            tool_name: Name of the tool
            required_capabilities: List of required capabilities

        Returns:
            Score from 0.0 to 1.0 indicating capability match
        """
        if not required_capabilities:
            return 1.0

        if not self.ontology or not self.ontology_loader:
            # Fallback to simple string matching
            tool_lower = tool_name.lower()
            matches = sum(1 for cap in required_capabilities if cap.lower() in tool_lower)
            return matches / len(required_capabilities) if required_capabilities else 1.0

        # Query ontology for tool capabilities
        tool_capabilities = set()
        
        try:
            # Try to find tool in ontology and its capabilities
            sparql = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX : <http://agent_kit.io/business#>
            SELECT DISTINCT ?capability WHERE {{
                {{
                    ?tool rdfs:label ?toolLabel .
                    FILTER(REGEX(?toolLabel, "{tool_name}", "i"))
                    ?tool :providesCapability ?capability .
                    ?capability rdfs:label ?capLabel .
                }}
                UNION
                {{
                    ?tool rdfs:label ?toolLabel .
                    FILTER(REGEX(?toolLabel, "{tool_name}", "i"))
                    ?capability :requiresTool ?tool .
                    ?capability rdfs:label ?capLabel .
                }}
            }}
            """
            results = self.ontology_loader.query(sparql)
            for result in results:
                cap_uri = str(result.get('capability', ''))
                if cap_uri:
                    # Extract local name
                    cap_name = cap_uri.split('#')[-1] if '#' in cap_uri else cap_uri.split('/')[-1]
                    tool_capabilities.add(cap_name.lower())
        except Exception:
            pass

        # Also check for direct string matches
        tool_lower = tool_name.lower()
        for cap in required_capabilities:
            cap_lower = cap.lower()
            if cap_lower in tool_lower:
                tool_capabilities.add(cap_lower)

        # Calculate semantic similarity for capabilities not found via ontology
        if self._get_embedder():
            tool_embedding = self._get_embedding(tool_name)
            if tool_embedding is not None:
                for cap in required_capabilities:
                    cap_embedding = self._get_embedding(cap)
                    if cap_embedding is not None:
                        similarity = float(cosine_similarity([tool_embedding], [cap_embedding])[0][0])
                        if similarity > 0.5:  # Threshold for semantic match
                            tool_capabilities.add(cap.lower())

        # Score based on how many required capabilities match
        required_lower = {c.lower() for c in required_capabilities}
        matches = len(tool_capabilities & required_lower)
        
        # Also check for partial matches (substring)
        for req_cap in required_capabilities:
            req_lower = req_cap.lower()
            for tool_cap in tool_capabilities:
                if req_lower in tool_cap or tool_cap in req_lower:
                    matches += 0.5
        
        # Normalize score
        score = min(matches / len(required_capabilities), 1.0) if required_capabilities else 1.0
        return score
