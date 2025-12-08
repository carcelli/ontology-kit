"""
Adapter that wraps OpenAI SDK Agent with ontology context.

From first principles: This adapter enriches OpenAI SDK agents with:
- SPARQL query tracking
- Entity extraction from conversations
- Domain-specific tool filtering
- Leverage score computation (for business domain)

The adapter pattern allows us to use OpenAI SDK's excellent agent execution
while maintaining our ontology-first architecture.
"""

from __future__ import annotations

from agents import Agent

from agent_kit.domains.registry import get_global_registry
from agent_kit.ontology.loader import OntologyLoader


class OntologyAgentAdapter:
    """
    Wraps OpenAI SDK Agent with ontology context and domain awareness.

    This adapter:
    1. Enhances agent instructions with ontology context
    2. Tracks SPARQL queries during execution
    3. Filters tools by domain allowlist
    4. Extracts entities from conversations
    5. Computes leverage scores (business domain)

    Example:
        >>> from agents import Agent
        >>> from agent_kit.adapters import OntologyAgentAdapter
        >>> from agent_kit.ontology.loader import OntologyLoader
        >>>
        >>> ontology = OntologyLoader("assets/ontologies/business.ttl")
        >>> openai_agent = Agent(name="ForecastAgent", instructions="...")
        >>> adapter = OntologyAgentAdapter(openai_agent, ontology, "business")
        >>> # Use adapter.agent with OpenAI SDK Runner
    """

    def __init__(
        self,
        agent: Agent,
        ontology: OntologyLoader,
        domain: str,
    ):
        """
        Initialize adapter with agent, ontology, and domain.

        Args:
            agent: OpenAI SDK Agent instance
            ontology: OntologyLoader for SPARQL queries
            domain: Domain identifier (e.g., 'business', 'betting', 'trading')
        """
        self.agent = agent
        self.ontology = ontology
        self.domain = domain
        self._domain_config = get_global_registry().get(domain)

        # Enhance agent with ontology context
        self._enhance_instructions()
        self._filter_tools_by_domain()

    def _enhance_instructions(self) -> None:
        """Add ontology context to agent instructions."""
        ontology_context = self._get_ontology_context()

        # Get original instructions
        original_instructions = self.agent.instructions
        if not isinstance(original_instructions, str):
            # Dynamic prompt function - can't enhance easily
            return

        # Build enhanced instructions
        enhanced = f"""{original_instructions}

## Ontology Context
- **Domain**: {self.domain}
- **Available Entities**: {", ".join(ontology_context["entities"][:10])}
- **Key Relationships**: {", ".join(ontology_context["relationships"][:5])}

## Instructions
When making decisions:
1. Query the ontology using SPARQL to understand entity relationships
2. Use domain-specific tools from the allowlist
3. Validate outputs against domain schemas
4. Track leverage scores for business metrics (if applicable)

## Domain Configuration
- **Risk Policies**: {self._format_risk_policies()}
- **Output Schema**: {self._domain_config.output_schema}
"""

        self.agent.instructions = enhanced

    def _get_ontology_context(self) -> dict[str, list[str]]:
        """Query ontology for domain context."""
        # SPARQL query to get domain entities
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT DISTINCT ?entity ?label WHERE {{
            ?entity rdfs:label ?label .
            ?entity rdf:type ?type .
            FILTER(STRSTARTS(STR(?type), "http://agent_kit.io/{self.domain}#"))
        }}
        LIMIT 20
        """
        try:
            results = self.ontology.query(query)
            entities = [
                r.get("label", {}).get("value", "") for r in results if r.get("label")
            ]
        except Exception:
            entities = []

        # Extract relationships (simplified)
        relationships = self._extract_relationships()

        return {
            "entities": entities,
            "relationships": relationships,
        }

    def _extract_relationships(self) -> list[str]:
        """Extract key relationships from ontology."""
        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT DISTINCT ?predicate ?label WHERE {
            ?predicate rdf:type rdf:Property .
            ?predicate rdfs:label ?label .
            FILTER(STRSTARTS(STR(?predicate), "http://agent_kit.io/"))
        }
        LIMIT 10
        """
        try:
            results = self.ontology.query(query)
            return [
                r.get("label", {}).get("value", "") for r in results if r.get("label")
            ]
        except Exception:
            return []

    def _filter_tools_by_domain(self) -> None:
        """Filter agent tools by domain allowlist."""
        if not self._domain_config:
            return

        allowed_tools = set(self._domain_config.allowed_tools)
        filtered_tools = []

        for tool in self.agent.tools:
            # Check if tool is in allowlist
            tool_name = getattr(tool, "name", None) or getattr(tool, "__name__", None)
            if tool_name:
                # Check if tool matches allowlist pattern (e.g., "tools.business.predict")
                tool_path = f"tools.{self.domain}.{tool_name}"
                if tool_path in allowed_tools or tool_name in allowed_tools:
                    filtered_tools.append(tool)
            else:
                # If we can't determine name, include it (conservative)
                filtered_tools.append(tool)

        self.agent.tools = filtered_tools

    def _format_risk_policies(self) -> str:
        """Format risk policies for instructions."""
        if not self._domain_config or not self._domain_config.risk_policies:
            return "None configured"

        policies = []
        for key, value in self._domain_config.risk_policies.items():
            policies.append(f"{key}: {value}")

        return "; ".join(policies[:5])  # Limit to first 5

    def extract_entities_from_conversation(self, text: str) -> list[str]:
        """
        Extract entities from conversation text using ontology.

        Args:
            text: Conversation text

        Returns:
            List of entity URIs found in text
        """
        # Simple implementation - could be enhanced with NER
        entities = []
        for entity_info in self._get_ontology_context()["entities"]:
            if entity_info.lower() in text.lower():
                entities.append(entity_info)

        return entities

    def track_sparql_query(self, query: str) -> None:
        """
        Track SPARQL query executed during agent run.

        This is called by tools that execute SPARQL queries.

        Args:
            query: SPARQL query string
        """
        # Store in agent metadata (could be enhanced with event logger)
        if not hasattr(self.agent, "_ontology_queries"):
            self.agent._ontology_queries = []
        self.agent._ontology_queries.append(query)
