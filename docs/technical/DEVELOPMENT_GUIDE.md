# Development Guide

This guide covers the tools and processes for developing within the `ontology-kit` repository.

## Testing
The project uses `pytest` for testing. Tests are located in the `tests/` directory.

### Structure
*   `tests/unit/`: Fast, isolated tests for individual components (e.g., `test_ontology_loader.py`, `test_base_agent.py`).
*   `tests/integration/`: End-to-end tests ensuring components work together (e.g., `test_unified_sdk.py`, `test_business_flow.py`).

### Running Tests
Run all tests:
```bash
pytest
```

Run specific category:
```bash
pytest tests/unit
pytest tests/integration
```

Run a specific test file:
```bash
pytest tests/integration/test_unified_sdk.py
```

## Utility Scripts
The `scripts/` directory contains helper scripts for maintenance and verification.

*   `verify_installation.py`: Checks that all dependencies and core modules are working correctly. Use this after setup.
*   `code_quality_checker.py`: likely runs linting and style checks.
*   `audit_complexity.py`: Analyzes code complexity.
*   `sync_openai_agents.py`: Utility to sync/update external agent definitions.
*   `create_tree_visualization.py`: Generates visual representations of the directory structure or ontology.

## CI/CD
GitHub Actions are configured in `.github/workflows/`:
*   `lint.yml`: Checks code style.
*   `test.yml`: Runs the test suite on pull requests.
