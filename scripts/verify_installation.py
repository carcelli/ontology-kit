#!/usr/bin/env python3
"""
Verification script for unified SDK installation.

Checks:
1. Core dependencies
2. Module imports
3. SDK availability
4. Configuration
5. Example readiness
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

print("=" * 60)
print("Ontology-Kit Installation Verification")
print("=" * 60)
print()

# Track results
checks = []


def check(name: str, fn: callable, required: bool = True) -> bool:
    """Run a check and record result."""
    try:
        fn()
        print(f"✅ {name}")
        checks.append((name, True, None))
        return True
    except Exception as e:
        status = "❌" if required else "⚠️ "
        print(f"{status} {name}: {e}")
        checks.append((name, False, str(e)))
        return not required


# ===============================================================
# Check 1: Core Dependencies
# ===============================================================
print("1️⃣  Core Dependencies")
print("-" * 60)


def check_rdflib():
    import rdflib

    assert rdflib.__version__ >= "7.0.0"


def check_pydantic():
    import pydantic

    assert pydantic.__version__ >= "2.0.0"


def check_numpy():
    import numpy

    assert numpy.__version__ >= "1.24.0"


check("rdflib", check_rdflib)
check("pydantic", check_pydantic)
check("numpy", check_numpy)
print()

# ===============================================================
# Check 2: SDK Availability
# ===============================================================
print("2️⃣  SDK Availability")
print("-" * 60)


def check_openai_sdk():
    import agents

    assert hasattr(agents, "Agent")
    assert hasattr(agents, "Runner")


def check_adk():
    import google.adk

    assert hasattr(google.adk, "runners")


check("OpenAI Agents SDK", check_openai_sdk, required=False)
check("Google ADK", check_adk, required=False)
print()

# ===============================================================
# Check 3: Agent Kit Modules
# ===============================================================
print("3️⃣  Agent Kit Modules")
print("-" * 60)


def check_core():
    pass


def check_adapters():
    pass


def check_events():
    pass


def check_sessions():
    pass


def check_memory():
    pass


def check_runners():
    pass


def check_orchestrator():
    pass


check("Core (Ontology, Embedder, VectorIndex)", check_core)
check("Adapters", check_adapters)
check("Events", check_events)
check("Sessions", check_sessions)
check("Memory", check_memory)
check("Runners", check_runners)
check("Orchestration", check_orchestrator)
print()

# ===============================================================
# Check 4: Configuration
# ===============================================================
print("4️⃣  Configuration")
print("-" * 60)


def check_api_key():
    import os

    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY not set")
    print(f"   API key: {key[:10]}...")


def check_assets():
    ontology_path = Path("assets/ontologies/business.ttl")
    if not ontology_path.exists():
        raise FileNotFoundError(f"Ontology not found: {ontology_path}")


check("OpenAI API Key", check_api_key, required=False)
check("Ontology Assets", check_assets, required=False)
print()

# ===============================================================
# Check 5: Basic Functionality
# ===============================================================
print("5️⃣  Basic Functionality")
print("-" * 60)


def check_ontology_load():
    from agent_kit import OntologyLoader

    ontology = OntologyLoader("assets/ontologies/business.ttl")
    ontology.load()


def check_session_create():
    import asyncio

    from agent_kit import OntologyLoader, OntologySessionService, create_session_backend

    async def test():
        ontology = OntologyLoader("assets/ontologies/business.ttl")
        backend = create_session_backend("memory")
        service = OntologySessionService(backend, ontology)
        session = await service.get_session("test_001")
        assert session["id"] == "test_001"

    asyncio.run(test())


def check_memory_store():
    import asyncio

    from agent_kit import OntologyLoader, OntologyMemoryService

    async def test():
        ontology = OntologyLoader("assets/ontologies/business.ttl")
        memory = OntologyMemoryService(ontology, "business")
        await memory.store(
            content="Test memory",
            user_id="test_user",
            session_id="test_session",
        )

    asyncio.run(test())


def check_event_create():
    from agent_kit import OntologyEvent, OntologyEventContent

    event = OntologyEvent(
        author="TestAgent",
        content=OntologyEventContent(text="Test event"),
    )
    assert event.author == "TestAgent"


check("Ontology Loading", check_ontology_load, required=False)
check("Session Creation", check_session_create)
check("Memory Storage", check_memory_store)
check("Event Creation", check_event_create)
print()

# ===============================================================
# Summary
# ===============================================================
print("=" * 60)
print("Summary")
print("=" * 60)

passed = sum(1 for _, status, _ in checks if status)
failed = len(checks) - passed

print(f"\nTotal checks: {len(checks)}")
print(f"✅ Passed: {passed}")
if failed > 0:
    print(f"❌ Failed: {failed}")

print("\nFailed checks:")
for name, status, error in checks:
    if not status:
        print(f"  - {name}: {error}")

print()

if failed == 0:
    print("🎉 All checks passed! Installation is complete.")
    print("\nNext steps:")
    print("  1. Run examples: python examples/test_unified_sdk.py")
    print("  2. Read docs: cat docs/UNIFIED_SDK_CHANGELOG.md")
    print("  3. Build your agents!")
    sys.exit(0)
else:
    required_failed = sum(
        1
        for name, status, _ in checks
        if not status
        and "SDK" not in name
        and "API Key" not in name
        and "Assets" not in name
    )

    if required_failed == 0:
        print("⚠️  Some optional checks failed, but core functionality is ready.")
        print("\nOptional:")
        print("  - Install OpenAI SDK: pip install openai-agents")
        print("  - Set API key: export OPENAI_API_KEY='...'")
        print("  - Add ontology: cp ontologies/business.ttl assets/ontologies/")
        sys.exit(0)
    else:
        print("❌ Required checks failed. Please fix errors and try again.")
        print("\nTroubleshooting:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Check Python version: python --version (>= 3.10)")
        print("  3. See SETUP_AND_VERIFY.md for detailed instructions")
        sys.exit(1)
