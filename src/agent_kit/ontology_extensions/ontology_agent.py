"""
Ontology-enhanced agent that extends the OpenAI Agents SDK Agent class.

This class adds ontology-driven capabilities including:
- SPARQL-based instruction generation
- Ontology-aware tool discovery and filtering
- Semantic reasoning for action validation
- Knowledge graph integration for context
"""

from __future__ import annotations

from collections.abc import Callable
from typing import (
    TYPE_CHECKING,
    Any,
)

from ..ontology.loader import OntologyLoader

# Try to import from agents SDK, with fallbacks
try:
    from agents import Agent, RunContextWrapper, TContext
    AGENTS_AVAILABLE = True
except ImportError:
    # Fallback definitions when SDK is not available
    from typing import Any as TContext
    RunContextWrapper = Any
    Agent = object
    AGENTS_AVAILABLE = False

if TYPE_CHECKING:
    try:
        from agents import MaybeAwaitable
    except ImportError:
        MaybeAwaitable = Any


class OntologyAgent(Agent if AGENTS_AVAILABLE else object):
    """
    Ontology-enhanced agent that extends the SDK Agent with knowledge graph capabilities.

    This agent can:
    - Generate instructions dynamically from ontology queries
    - Discover and filter tools based on ontology relationships
    - Validate actions against business rules defined in the ontology
    - Maintain semantic context across interactions
    """

    def __init__(
        self,
        name: str,
        ontology_path: str,
        **kwargs
    ):
        """
        Initialize the ontology-enhanced agent.

        Args:
            name: Agent name
            ontology_path: Path to the ontology file (.ttl, .owl)
            **kwargs: Additional arguments passed to the base Agent class
        """
        self.ontology_path = ontology_path
        self.ontology = OntologyLoader(ontology_path).load()

        # Generate ontology-driven instructions
        instructions = self._generate_ontology_instructions()

        # Discover ontology-relevant tools
        tools = self._discover_ontology_tools()

        super().__init__(
            name=name,
            instructions=instructions,
            tools=tools,
            **kwargs
        )

    def _generate_ontology_instructions(self) -> str | Callable[[RunContextWrapper[TContext], Agent[TContext]], str] | None:
        """
        Generate instructions dynamically from the ontology.

        Queries the ontology for agent-specific instructions and capabilities.
        """
        base_instructions = f"""You are {self.name}, an ontology-driven agent with access to a comprehensive knowledge graph.

Your capabilities are defined by the ontology at {self.ontology_path}. You can:
- Query the knowledge graph using SPARQL for information
- Use tools that are relevant to your defined capabilities
- Make decisions based on semantic relationships in the ontology
- Maintain context across interactions using the knowledge graph

Always consider the semantic relationships and business rules defined in the ontology when making decisions."""

        # Query for agent-specific instructions from ontology
        try:
            sparql = f"""
                PREFIX : <http://agent_kit.io/business#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT ?instructions
                WHERE {{
                    ?agent rdfs:label "{self.name}" ;
                           :hasInstructions ?instructions .
                }}
            """
            results = list(self.ontology.query(sparql))
            if results and results[0].instructions:
                return f"{base_instructions}\n\nSpecific instructions: {str(results[0].instructions)}"
        except Exception:
            # If ontology query fails, continue with base instructions
            pass

        return base_instructions

    def _discover_ontology_tools(self) -> list:
        """
        Discover tools relevant to this agent based on ontology relationships.

        Queries the ontology to find tools that this agent can or should use.
        """
        tools = []

        try:
            # Query for tools this agent can perform
            sparql = f"""
                PREFIX : <http://agent_kit.io/business#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT ?toolName
                WHERE {{
                    ?agent rdfs:label "{self.name}" ;
                           :canPerform ?capability .
                    ?capability :requiresTool ?tool .
                    ?tool rdfs:label ?toolName .
                }}
            """
            results = list(self.ontology.query(sparql))

            # Import and add tools based on ontology relationships
            for result in results:
                tool_name = str(result.toolName)
                try:
                    # Try to import the tool from our tool registry
                    if tool_name == "Predict Tool":
                        from ..tools.business import predict
                        tools.append(predict)
                    elif tool_name == "Optimize Tool":
                        from ..tools.business import optimize
                        tools.append(optimize)
                    elif tool_name == "GitHub Tool":
                        from ..tools.github_tools import write_to_github
                        tools.append(write_to_github)
                    # Add more tool mappings as needed
                except ImportError:
                    continue

        except Exception:
            # If ontology queries fail, return empty tools list
            pass

        return tools

    async def validate_action_against_ontology(
        self,
        action: str,
        context: RunContextWrapper[TContext] | None = None
    ) -> bool:
        """
        Validate a proposed action against ontology business rules.

        Args:
            action: The action to validate
            context: Current run context

        Returns:
            True if action is valid according to ontology rules
        """
        try:
            # Query ontology for allowed actions
            sparql = f"""
                PREFIX : <http://agent_kit.io/business#>
                ASK {{
                    ?action a :AllowedAction .
                    FILTER(?action = :{action})
                }}
            """
            results = list(self.ontology.query(sparql))
            return bool(results)

        except Exception:
            # If validation fails, allow the action (fail-open)
            return True

    async def get_ontology_context(
        self,
        query: str,
        context: RunContextWrapper[TContext] | None = None
    ) -> dict[str, Any]:
        """
        Retrieve relevant context from the ontology for a given query.

        Args:
            query: Natural language query or SPARQL query
            context: Current run context

        Returns:
            Dictionary containing relevant ontology information
        """
        try:
            # For now, return basic ontology metadata
            # In a full implementation, this could use semantic search
            return {
                "ontology_path": self.ontology_path,
                "agent_name": self.name,
                "available_triples": len(list(self.ontology)) if hasattr(self.ontology, '__iter__') else 0,
                "query": query,
            }
        except Exception:
            return {"error": "Failed to retrieve ontology context"}
