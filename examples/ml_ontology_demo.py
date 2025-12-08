#!/usr/bin/env python3
"""
Demo: Ontology-driven ML tool discovery and execution.

This script demonstrates the complete workflow:
1. Load ML tools ontology
2. Discover tools via SPARQL queries
3. Schedule training job
4. Poll for completion
5. Schedule cross-validation
6. Poll and retrieve metrics

Run from repo root:
    python examples/ml_ontology_demo.py
"""

import sys
import time
from pathlib import Path

# Add src to path for demo purposes
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))

from agent_kit.ontology.loader import OntologyLoader
from agent_kit.orchestrator.ontology_orchestrator import OntologyOrchestrator
from agent_kit.tools.ml_training import ML_TOOL_REGISTRY, advance_mock_jobs

# Tool class IRIs from ontology
ML_TRAIN = "http://agent-kit.com/ontology/ml#ModelTrainerTool"
ML_CV = "http://agent-kit.com/ontology/ml#CrossValidatorTool"
ML_JOB = "http://agent-kit.com/ontology/ml#JobStatusTool"


def print_section(title: str) -> None:
    """Print formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print("=" * 70)


def main() -> None:
    """Run the complete ML workflow demo."""
    print_section("ML Tool Ontology Demo")
    print("\nThis demo shows how agents discover and call ML tools via ontology.")

    # Step 1: Load ontology
    print_section("Step 1: Load ML Tools Ontology")
    ontology_path = repo_root / "assets" / "ontologies" / "ml_tools.ttl"
    print(f"Loading: {ontology_path}")
    loader = OntologyLoader(str(ontology_path))
    loader.load()
    print(f"✓ Loaded {len(loader.graph)} triples")

    # Step 2: Create orchestrator
    print_section("Step 2: Initialize Orchestrator")
    orch = OntologyOrchestrator(loader, ML_TOOL_REGISTRY)
    print("✓ Orchestrator ready with ML_TOOL_REGISTRY")

    # Step 3: Discover tools by class
    print_section("Step 3: Discover Tools via SPARQL")
    print(f"Query: Find tool for class {ML_TRAIN.split('#')[1]}")
    trainer = orch.discover_tool(ML_TRAIN)
    print(f"✓ Discovered: {trainer['function'].__name__}")

    # Step 4: Discover tools by algorithm
    print("\nQuery: Find tools implementing GradientDescent")
    gd_tools = orch.discover_tools_by_algorithm("GradientDescent")
    print(f"✓ Found {len(gd_tools)} tool(s):")
    for t in gd_tools:
        print(f"  - {t['function'].__name__}")

    # Step 5: Get OpenAI tool specs
    print_section("Step 4: Generate OpenAI Tool Specs")
    print("Classes: ModelTrainerTool, CrossValidatorTool, JobStatusTool")
    specs = orch.get_openai_tools([ML_TRAIN, ML_CV, ML_JOB])
    print(f"✓ Generated {len(specs)} OpenAI function specs:")
    for spec in specs:
        print(f"  - {spec['function']['name']}: {spec['function']['description']}")

    # Step 6: Schedule training
    print_section("Step 5: Schedule Model Training")
    train_params = {
        "dataset_uri": "s3://demo-bucket/customer_data.parquet",
        "hyperparameters": {"lr": 0.001, "batch_size": 32},
    }
    print(f"Params: {train_params}")
    train_result = orch.call(ML_TRAIN, train_params)
    print(f"✓ Status: {train_result['status']}")
    print(f"✓ Job ID: {train_result['job_id']}")
    job_id = train_result["job_id"]

    # Step 7: Poll for training completion
    print_section("Step 6: Poll Training Job Status")
    print(f"Polling job: {job_id}")
    model_uri = None
    start_time = time.time()
    for i in range(15):
        # Advance mock time deterministically (1 second per iteration)
        advance_mock_jobs(start_time + (i + 1) * 1.0)
        status = orch.call(ML_JOB, {"job_id": job_id})
        if status["status"] == "RUNNING":
            progress = status.get("progress", 0.0)
            print(f"  [{i + 1}] Status: RUNNING ({progress:.1%} complete)")
        elif status["status"] == "COMPLETED":
            model_uri = status["artifact_uri"]
            print(f"  [{i + 1}] Status: COMPLETED")
            print(f"✓ Trained model: {model_uri}")
            break
        else:
            print(f"  [{i + 1}] Status: {status['status']}")
        time.sleep(0.2)  # Visual delay for demo

    if not model_uri:
        print("✗ Training did not complete in time")
        return

    # Step 8: Schedule cross-validation
    print_section("Step 7: Schedule Cross-Validation")
    cv_params = {
        "model_uri": model_uri,
        "dataset_uri": "s3://demo-bucket/customer_data.parquet",
        "k_folds": 5,
    }
    print(f"Params: {cv_params}")
    cv_result = orch.call(ML_CV, cv_params)
    print(f"✓ Status: {cv_result['status']}")
    print(f"✓ Job ID: {cv_result['job_id']}")
    cv_job_id = cv_result["job_id"]

    # Step 9: Poll for CV completion
    print_section("Step 8: Poll Cross-Validation Status")
    print(f"Polling job: {cv_job_id}")
    metrics = None
    cv_start = time.time()
    for i in range(15):
        advance_mock_jobs(cv_start + (i + 1) * 1.0)
        status = orch.call(ML_JOB, {"job_id": cv_job_id})
        if status["status"] == "RUNNING":
            progress = status.get("progress", 0.0)
            print(f"  [{i + 1}] Status: RUNNING ({progress:.1%} complete)")
        elif status["status"] == "COMPLETED":
            metrics = status.get("metrics", {})
            print(f"  [{i + 1}] Status: COMPLETED")
            print(f"✓ Metrics: {metrics}")
            break
        else:
            print(f"  [{i + 1}] Status: {status['status']}")
        time.sleep(0.2)

    if not metrics:
        print("✗ Cross-validation did not complete in time")
        return

    # Summary
    print_section("Summary")
    print("✓ Ontology → Tool Discovery → Async Execution → Result")
    print(f"✓ Model: {model_uri}")
    print(
        f"✓ Metrics: Accuracy={metrics.get('accuracy', 'N/A')}, F1={metrics.get('f1', 'N/A')}"
    )
    print("\nNext steps:")
    print("  - Swap mock job store with Celery/K8s")
    print("  - Add real training/validation implementations")
    print("  - Extend ontology with EvaluationProcess, InferenceTool")
    print("  - Wire OpenAI SDK adapter to auto-discover tools")
    print()


if __name__ == "__main__":
    main()
