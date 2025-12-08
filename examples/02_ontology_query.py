#!/usr/bin/env python
"""
Example 2: Ontology Query

Demonstrates ontology operations:
- Loading TTL ontology
- Querying classes and properties
- SPARQL queries for task relationships
"""

import sys
from pathlib import Path

# Add src to path (for development)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_kit.ontology import OntologyLoader


def main() -> None:
    print("=" * 70)
    print("Agent Kit - Example 2: Ontology Query")
    print("=" * 70)
    print()

    # Load ontology
    ontology_path = Path(__file__).parent.parent / "assets" / "ontologies" / "core.ttl"
    print(f"📚 Loading ontology from: {ontology_path}")

    loader = OntologyLoader(str(ontology_path))
    graph = loader.load()

    print(f"   {loader}")
    print()

    # 1. Get all classes
    print("🏷️  Classes defined in ontology:")
    classes = loader.get_classes()
    for cls in classes:
        # Extract local name
        local_name = cls.split("#")[-1] if "#" in cls else cls.split("/")[-1]
        print(f"   - {local_name}")
    print()

    # 2. Get all properties
    print("🔗 Properties (relations) defined:")
    properties = loader.get_properties()
    for prop in properties[:10]:  # Show first 10
        local_name = prop.split("#")[-1] if "#" in prop else prop.split("/")[-1]
        print(f"   - {local_name}")
    print(f"   ... ({len(properties)} total)")
    print()

    # 3. Query task-tool relationships
    print("🔍 Query: Which tasks require which tools?")
    sparql = """
    PREFIX : <http://agent_kit.io/ontology#>
    SELECT ?task ?tool WHERE {
        ?task a :Task .
        ?task :requiresTool ?tool .
    }
    """
    results = loader.query(sparql)

    for res in results:
        task_name = str(res["task"]).split("#")[-1]
        tool_name = str(res["tool"]).split("#")[-1]
        print(f"   - {task_name} requires {tool_name}")
    print()

    # 4. Query task prerequisites
    print("🔍 Query: Which tasks have prerequisites?")
    sparql = """
    PREFIX : <http://agent_kit.io/ontology#>
    SELECT ?task ?prereq WHERE {
        ?task :hasPrerequisite ?prereq .
    }
    """
    results = loader.query(sparql)

    if results:
        for res in results:
            task_name = str(res["task"]).split("#")[-1]
            prereq_name = str(res["prereq"]).split("#")[-1]
            print(f"   - {task_name} requires {prereq_name} first")
    else:
        print("   (No prerequisites defined)")
    print()

    # 5. Query agent capabilities
    print("🔍 Query: What capabilities does AgentAlpha have?")
    sparql = """
    PREFIX : <http://agent_kit.io/ontology#>
    SELECT ?tool WHERE {
        :AgentAlpha :hasCapability ?tool .
    }
    """
    results = loader.query(sparql)

    for res in results:
        tool_name = str(res["tool"]).split("#")[-1]
        print(f"   - {tool_name}")
    print()

    print("=" * 70)
    print("✅ Example complete!")
    print()
    print("Next steps:")
    print("  - Explore assets/ontologies/core.ttl to see the full schema")
    print("  - Try adding your own classes and relations")
    print("  - Run examples/03_ontology_agents.py to see agents in action")
    print("=" * 70)


if __name__ == "__main__":
    main()
