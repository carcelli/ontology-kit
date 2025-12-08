#!/usr/bin/env python
"""
Complexity audit script: Find all agent creation patterns and inconsistencies.

Run this to see where you're creating agents outside the Factory pattern.
"""

import ast
from pathlib import Path


class AgentCreationAuditor(ast.NodeVisitor):
    """AST visitor to find agent instantiations."""

    def __init__(self):
        self.creations: list[tuple[str, int, str]] = []  # (file, line, pattern)
        self.imports: dict[str, list[str]] = {}  # file -> [imports]

    def visit_Import(self, node):
        """Track imports."""
        for alias in node.names:
            if "agent" in alias.name.lower():
                file = getattr(node, "file", "unknown")
                if file not in self.imports:
                    self.imports[file] = []
                self.imports[file].append(alias.name)

    def visit_ImportFrom(self, node):
        """Track from imports."""
        if node.module and "agent" in node.module.lower():
            file = getattr(node, "file", "unknown")
            if file not in self.imports:
                self.imports[file] = []
            for alias in node.names:
                self.imports[file].append(f"{node.module}.{alias.name}")

    def visit_Call(self, node):
        """Find agent instantiations."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if "Agent" in func_name and func_name != "AgentFactory":
                self.creations.append(
                    (
                        getattr(node, "file", "unknown"),
                        node.lineno,
                        f"Direct: {func_name}()",
                    )
                )
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                obj_name = node.func.value.id
                if obj_name == "factory":
                    if node.func.attr in ["create_agent", "create_orchestrator"]:
                        self.creations.append(
                            (
                                getattr(node, "file", "unknown"),
                                node.lineno,
                                f"Factory: {node.func.attr}()",
                            )
                        )
                elif "Builder" in obj_name:
                    self.creations.append(
                        (
                            getattr(node, "file", "unknown"),
                            node.lineno,
                            f"Builder: {obj_name}.build_agent()",
                        )
                    )


def audit_file(file_path: Path) -> dict:
    """Audit a single Python file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        auditor = AgentCreationAuditor()

        # Add file path to nodes for tracking
        for node in ast.walk(tree):
            node.file = str(file_path)

        auditor.visit(tree)
        return {
            "creations": auditor.creations,
            "imports": auditor.imports.get(str(file_path), []),
        }
    except Exception as e:
        return {"error": str(e)}


def main():
    """Run complexity audit."""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src" / "agent_kit"
    examples_dir = project_root / "examples"

    print("=" * 70)
    print("Agent System Complexity Audit")
    print("=" * 70)
    print()

    all_creations = []
    all_imports = {}

    # Audit source files
    print("📁 Auditing source files...")
    for py_file in src_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        result = audit_file(py_file)
        if "error" not in result:
            all_creations.extend(result["creations"])
            if result["imports"]:
                all_imports[str(py_file)] = result["imports"]

    # Audit examples
    print("📁 Auditing examples...")
    for py_file in examples_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        result = audit_file(py_file)
        if "error" not in result:
            all_creations.extend(result["creations"])
            if result["imports"]:
                all_imports[str(py_file)] = result["imports"]

    # Analyze patterns
    print()
    print("=" * 70)
    print("Creation Pattern Analysis")
    print("=" * 70)
    print()

    factory_count = sum(1 for _, _, p in all_creations if "Factory" in p)
    direct_count = sum(1 for _, _, p in all_creations if "Direct" in p)
    builder_count = sum(1 for _, _, p in all_creations if "Builder" in p)

    print(f"✅ Factory pattern: {factory_count}")
    print(f"⚠️  Direct instantiation: {direct_count}")
    print(f"⚠️  Builder pattern: {builder_count}")
    print()

    if direct_count > 0:
        print("🔴 Direct instantiations found (should use Factory):")
        for file, line, pattern in all_creations:
            if "Direct" in pattern:
                print(f"   {file}:{line} - {pattern}")
        print()

    if builder_count > 0:
        print("🟡 Builder pattern found (consider migrating to Factory):")
        for file, line, pattern in all_creations:
            if "Builder" in pattern:
                print(f"   {file}:{line} - {pattern}")
        print()

    # Complexity score
    total = factory_count + direct_count + builder_count
    if total == 0:
        print("ℹ️  No agent creations found (may need manual inspection)")
    else:
        factory_ratio = factory_count / total if total > 0 else 0
        complexity_score = (
            10 - (factory_ratio * 5) - (direct_count * 2) - (builder_count * 1)
        )
        complexity_score = max(0, min(10, complexity_score))

        print("=" * 70)
        print("Complexity Score")
        print("=" * 70)
        print(f"Factory usage: {factory_ratio:.1%}")
        print(f"Complexity score: {complexity_score:.1f}/10")
        print()

        if complexity_score < 5:
            print("🔴 High complexity: Multiple creation patterns detected")
            print("   Recommendation: Consolidate to Factory pattern")
        elif complexity_score < 7:
            print("🟡 Medium complexity: Some consolidation needed")
            print("   Recommendation: Migrate direct instantiations to Factory")
        else:
            print("✅ Low complexity: Mostly using Factory pattern")
            print("   Recommendation: Continue current approach")

    print()
    print("=" * 70)
    print("Next Steps")
    print("=" * 70)
    print("1. Review ARCHITECTURE_COMPLEXITY_ASSESSMENT.md")
    print("2. Migrate direct instantiations to Factory pattern")
    print("3. Consider removing Builder if Factory can handle it")
    print("4. Re-run this audit after consolidation")
    print()


if __name__ == "__main__":
    main()
