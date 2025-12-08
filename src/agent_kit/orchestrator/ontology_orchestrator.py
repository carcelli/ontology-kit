# src/agent_kit/orchestrator/ontology_orchestrator.py
"""
Ontology-driven orchestrator that discovers and executes tools via SPARQL queries.

Workflow:
1. Query ontology to find tools by class/IO/algorithm
2. Extract Python identifier from ml:hasPythonIdentifier
3. Map to function + schema in registry
4. Execute and return result
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from rdflib import Namespace

from ..ontology.loader import OntologyLoader

ML = Namespace("http://agent-kit.com/ontology/ml#")
CORE = Namespace("http://agent-kit.com/ontology/core#")


class OntologyOrchestrator:
    """
    Orchestrate tool execution by discovering tools through ontology queries.

    Example:
        >>> from agent_kit.ontology.loader import OntologyLoader
        >>> from agent_kit.tools.ml_training import ML_TOOL_REGISTRY
        >>> loader = OntologyLoader('assets/ontologies/ml_tools.ttl')
        >>> loader.load()
        >>> orch = OntologyOrchestrator(loader, ML_TOOL_REGISTRY)
        >>> result = orch.call('http://agent-kit.com/ontology/ml#ModelTrainerTool',
        ...                    {'dataset_uri': 's3://bucket/data.parquet'})
    """

    def __init__(
        self, ontology: OntologyLoader, registry: dict[str, dict[str, Any]]
    ) -> None:
        """
        Initialize orchestrator.

        Args:
            ontology: Loaded OntologyLoader with graph
            registry: Tool registry mapping Python identifiers to functions/schemas
        """
        self.ontology = ontology
        self.registry = registry

    def discover_tool(self, class_iri: str) -> dict[str, Any]:
        """
        Discover a tool by its ontology class IRI.

        Args:
            class_iri: Full IRI of the tool class (e.g., 'http://agent-kit.com/ontology/ml#ModelTrainerTool')

        Returns:
            Tool metadata with function, schema, and OpenAI tool spec

        Raises:
            RuntimeError: If no tool found for class or Python identifier not in registry
        """
        q = f"""
        PREFIX ml: <{ML}>
        SELECT ?py
        WHERE {{
          ?tool a <{class_iri}> ;
                ml:hasPythonIdentifier ?py .
        }}
        LIMIT 1
        """
        rows = self.ontology.query(q)
        if not rows:
            raise RuntimeError(f"No tool bound for class {class_iri}")
        py = str(rows[0]["py"])
        tool = self.registry.get(py)
        if not tool:
            raise RuntimeError(f"Python identifier '{py}' not found in registry")
        return tool

    def discover_tools_by_algorithm(self, algorithm: str) -> list[dict[str, Any]]:
        """
        Find all tools that implement a given algorithm.

        Args:
            algorithm: Algorithm name (e.g., 'GradientDescent')

        Returns:
            List of tool metadata dictionaries
        """
        q = f"""
        PREFIX ml: <{ML}>
        SELECT ?py
        WHERE {{
          ?tool ml:implementsAlgorithm "{algorithm}" ;
                ml:hasPythonIdentifier ?py .
        }}
        """
        rows = self.ontology.query(q)
        tools = []
        for row in rows:
            py = str(row["py"])
            if py in self.registry:
                tools.append(self.registry[py])
        return tools

    def get_openai_tools(self, classes: list[str]) -> list[dict[str, Any]]:
        """
        Get OpenAI tool specs for a list of ontology class IRIs.

        Args:
            classes: List of full class IRIs

        Returns:
            List of OpenAI function tool specifications
        """
        specs = []
        for cls in classes:
            t = self.discover_tool(cls)
            specs.append(t["tool_spec"])
        return specs

    def call(self, class_iri: str, params: dict[str, Any]) -> Any:
        """
        Execute a tool by its ontology class IRI.

        Args:
            class_iri: Full IRI of the tool class
            params: Parameters matching the tool's Pydantic schema

        Returns:
            Tool execution result
        """
        tool = self.discover_tool(class_iri)
        schema = tool["schema"]
        fn: Callable = tool["function"]
        validated = schema(**params)
        return fn.on_invoke_tool(None, validated.model_dump_json())

    def call_by_python_id(self, python_id: str, params: dict[str, Any]) -> Any:
        """
        Execute a tool directly by its Python identifier.

        Args:
            python_id: Python function name (e.g., 'train_model')
            params: Parameters matching the tool's Pydantic schema

        Returns:
            Tool execution result
        """
        tool = self.registry.get(python_id)
        if not tool:
            raise RuntimeError(f"Python identifier '{python_id}' not found in registry")
        schema = tool["schema"]
        fn: Callable = tool["function"]
        validated = schema(**params)
        return fn.on_invoke_tool(None, validated.model_dump_json())
