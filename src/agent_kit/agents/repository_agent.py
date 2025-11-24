"""
Repository Analysis Agent for codebase introspection.

From first principles: Self-awareness enables improvement—agent analyzes its own
codebase to identify unused tools, missing integrations, and coverage gaps.

Design choices:
- AST parsing for static analysis (no execution needed)
- Semantic graph for concept relations
- Pattern matching for tool/agent discovery

References:
- Python AST: https://docs.python.org/3/library/ast.html
- Code analysis: "Refactoring" by Martin Fowler
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from agent_kit.agents.base import AgentResult, AgentTask, BaseAgent


class RepositoryAnalysisAgent(BaseAgent):
    """
    Agent that analyzes the ontology-kit codebase for insights.

    Capabilities:
    - Find unused tools/agents
    - Detect missing integrations
    - Generate semantic graphs of concepts
    - Identify coverage gaps
    """

    def __init__(self, repo_path: str | Path | None = None):
        """
        Initialize repository agent.

        Args:
            repo_path: Path to repository root (defaults to src/agent_kit)
        """
        super().__init__(
            name="RepositoryAnalysisAgent",
            description="Analyzes codebase structure and identifies improvements",
        )
        self.repo_path = Path(repo_path) if repo_path else Path(__file__).parent.parent

    def run(self, task: AgentTask) -> AgentResult:
        """
        Analyze repository based on task.

        Args:
            task: Analysis task (e.g., "Find unused tools", "Generate coverage report")

        Returns:
            AgentResult with analysis findings
        """
        prompt = task.prompt.lower()

        # Route to appropriate analysis
        if "unused" in prompt or "orphan" in prompt:
            result = self._find_unused_tools()
        elif "coverage" in prompt or "gaps" in prompt:
            result = self._analyze_coverage()
        elif "graph" in prompt or "semantic" in prompt:
            result = self._build_semantic_graph()
        else:
            # Default: comprehensive analysis
            result = self._comprehensive_analysis()

        return AgentResult(result=result)

    def _find_unused_tools(self) -> dict[str, Any]:
        """
        Find tools that are defined but never used.

        Returns:
            Dict with unused tools and recommendations
        """
        tools_path = self.repo_path / "tools"

        # Discover all defined tools
        defined_tools = self._discover_tools(tools_path)

        # Find tool usages in agents/orchestrators
        used_tools = self._find_tool_usages()

        # Identify unused
        unused = set(defined_tools) - set(used_tools)

        return {
            "analysis_type": "unused_tools",
            "total_tools": len(defined_tools),
            "used_tools": len(used_tools),
            "unused_tools": list(unused),
            "unused_count": len(unused),
            "recommendations": [
                f"Remove or integrate unused tool: {tool}" for tool in unused
            ],
            "summary": f"Found {len(unused)} unused tools out of {len(defined_tools)} total",
        }

    def _analyze_coverage(self) -> dict[str, Any]:
        """
        Analyze test coverage and integration completeness.

        Returns:
            Dict with coverage metrics
        """
        agents_path = self.repo_path / "agents"
        tools_path = self.repo_path / "tools"

        # Count agents and tools
        agent_files = list(agents_path.glob("*_agent.py"))
        tool_files = list(tools_path.glob("*.py"))

        # Count tests (simplified)
        tests_path = self.repo_path.parent.parent / "tests"
        test_files = list(tests_path.rglob("test_*.py")) if tests_path.exists() else []

        return {
            "analysis_type": "coverage",
            "agents": {
                "total": len(agent_files),
                "files": [f.name for f in agent_files],
            },
            "tools": {
                "total": len(tool_files),
                "files": [f.name for f in tool_files],
            },
            "tests": {
                "total": len(test_files),
                "files": [f.name for f in test_files],
            },
            "coverage_estimate": len(test_files) / (len(agent_files) + len(tool_files))
            if (len(agent_files) + len(tool_files)) > 0
            else 0.0,
            "summary": f"Found {len(agent_files)} agents, {len(tool_files)} tools, {len(test_files)} test files",
        }

    def _build_semantic_graph(self) -> dict[str, Any]:
        """
        Build semantic graph of concepts in the codebase.

        Returns:
            Dict with graph structure
        """
        # Simplified: extract class/function names
        nodes = []
        edges = []

        for py_file in self.repo_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            try:
                with py_file.open("r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))

                # Extract classes and functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        nodes.append({"type": "class", "name": node.name, "file": py_file.name})
                    elif isinstance(node, ast.FunctionDef):
                        if not node.name.startswith("_"):  # Skip private
                            nodes.append({"type": "function", "name": node.name, "file": py_file.name})
            except Exception:
                # Skip files with parse errors
                pass

        return {
            "analysis_type": "semantic_graph",
            "nodes": nodes[:50],  # Limit for output
            "total_nodes": len(nodes),
            "edges": edges,  # TODO: Implement import tracking for edges
            "summary": f"Extracted {len(nodes)} concepts from codebase",
        }

    def _comprehensive_analysis(self) -> dict[str, Any]:
        """
        Run all analyses and combine results.

        Returns:
            Dict with comprehensive findings
        """
        unused = self._find_unused_tools()
        coverage = self._analyze_coverage()
        graph = self._build_semantic_graph()

        return {
            "analysis_type": "comprehensive",
            "unused_tools": unused,
            "coverage": coverage,
            "semantic_graph": graph,
            "summary": (
                f"Comprehensive analysis: {unused['unused_count']} unused tools, "
                f"{coverage['coverage_estimate']:.1%} test coverage, "
                f"{graph['total_nodes']} concepts identified"
            ),
        }

    def _discover_tools(self, tools_path: Path) -> list[str]:
        """
        Discover all tools defined in tools directory.

        Args:
            tools_path: Path to tools directory

        Returns:
            List of tool function names
        """
        tools = []

        for py_file in tools_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            try:
                with py_file.open("r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))

                # Find functions decorated with @function_tool
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check for @function_tool decorator
                        for decorator in node.decorator_list:
                            if (
                                isinstance(decorator, ast.Name)
                                and decorator.id == "function_tool"
                            ):
                                tools.append(node.name)
            except Exception:
                pass

        return tools

    def _find_tool_usages(self) -> list[str]:
        """
        Find tool usages across agents and orchestrators.

        Returns:
            List of used tool names
        """
        used = set()

        # Search in agents, orchestrators, factories
        search_paths = [
            self.repo_path / "agents",
            self.repo_path / "orchestrator",
            self.repo_path / "factories",
        ]

        for search_path in search_paths:
            if not search_path.exists():
                continue

            for py_file in search_path.rglob("*.py"):
                try:
                    with py_file.open("r", encoding="utf-8") as f:
                        content = f.read()

                    # Simple text search for function calls (not perfect but fast)
                    # Look for common tool names
                    common_tools = [
                        "fetch_odds",
                        "fetch_market_data",
                        "predict",
                        "optimize",
                        "train_model",
                        "query_ontology",
                        "embed",
                    ]

                    for tool in common_tools:
                        if f"{tool}(" in content or f'"{tool}"' in content:
                            used.add(tool)
                except Exception:
                    pass

        return list(used)
