# Repository Guidelines

## Project Structure & Module Organization
Target Python 3.12 via `.venv/` and keep importable code inside `src/agent_kit/` with subpackages mirroring agent capabilities (e.g., `src/agent_kit/tools/vectorstore.py`). Ontology schemas and semantic adapters live in `src/agent_kit/ontology/`, while serialized graphs (*.ttl, *.jsonld) belong in `assets/ontologies/`. Tests split between `tests/unit` and `tests/integration`, and runnable blueprints stay inside `examples/`.

## Build, Test, and Development Commands
Install everything with `python -m pip install -e .[dev]`. Run `python -m ruff check src tests && python -m black src tests && python -m mypy src`, then execute `pytest` (or `pytest tests/integration -m slow` for ontology-heavy flows). When touching embeddings or adapters, also run `pytest tests/integration -m hyperdim` to confirm navigation still works.

## Ontology-Driven Machine Learning
Ontology-driven ML anchors every agent. Define classes, relations, and feature bindings in `src/agent_kit/ontology/schema.py`, keep source graphs in `assets/ontologies/`, and refresh embeddings via `python scripts/refresh_embeddings.py --ontology assets/ontologies/core.ttl --seed 42` whenever the schema shifts. Tie each capability to the entities it consumes and extend `tests/unit/test_ontology_context.py` (or create it) to lock in the reasoning path.

## Reproducibility & Hyperdimensional Navigation
Keep ontology-derived datasets reproducible so agents traverse the hyperdimensional space deterministically. Version raw snapshots in `data/<domain>/<version>/`, regenerate embeddings with pinned commands like `python scripts/refresh_embeddings.py --ontology ... --seed 42`, store tensors in `artifacts/hyperdimensional/<version>/`, and record navigation heuristics or coordinate transforms in module docstrings.

## Coding Style & Naming Conventions
Target Python 3.12 with strict typing, stick to Black’s 88-column default, prefer single quotes, and keep classes/functions/constants in `PascalCase`, `snake_case`, and `UPPER_SNAKE`. Agent configuration YAML files stay kebab-cased (e.g., `multi-tool-agent.yaml`). Ensure each public function exposes full type hints plus return annotations.

## Testing Guidelines
Organize files as `tests/<area>/test_<feature>.py`, lean on fixtures for I/O seams, reserve `pytest.mark.integration` for end-to-end ontology flows, and maintain ≥90% statement coverage via `pytest --cov=agent_kit --cov-report=term-missing`. Each new tool requires a behavior test hitting the agent loop plus a focused unit test.

## Commit & Pull Request Guidelines
Stick to Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`) with subjects ≤72 chars, concise bullet bodies, and linked issues. Every PR must include representative test output (or justification) and request review only after lint + tests succeed locally.

## Security & Configuration Tips
Store secrets in `.env` or your shell profile and load them via `os.getenv`. Gate outbound network integrations behind interfaces in `src/agent_kit/services/` so they can be mocked. Keep `.venv/` ignored and recreate it after dependency bumps to avoid stale binaries entering CI artifacts.
