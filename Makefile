.PHONY: help install install-dev lint format typecheck test test-unit test-integration test-slow coverage clean benchmark dryrun profile

# Default target
help:
	@echo "Agent Kit - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install         Install production dependencies"
	@echo "  make install-dev     Install with dev dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint            Run ruff linter"
	@echo "  make format          Format code with black"
	@echo "  make typecheck       Run mypy type checker"
	@echo "  make quality         Run all quality checks (lint + format + typecheck)"
	@echo ""
	@echo "Testing:"
	@echo "  make test            Run full test suite"
	@echo "  make test-unit       Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-slow       Run slow/expensive tests"
	@echo "  make coverage        Generate HTML coverage report"
	@echo ""
	@echo "Performance:"
	@echo "  make benchmark       Run performance benchmarks"
	@echo "  make profile         Profile embedder with py-spy"
	@echo ""
	@echo "Deployment:"
	@echo "  make dryrun          Validate config + run smoke tests (gate before prod)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean           Remove build artifacts, cache, etc."

# Installation
install:
	python -m pip install -e .

install-dev:
	python -m pip install -e .[dev]

# Code Quality
lint:
	@echo "Running ruff..."
	python -m ruff check src tests
	@echo "✅ Linting passed"

format:
	@echo "Running black..."
	python -m black src tests
	@echo "✅ Formatting complete"

typecheck:
	@echo "Running mypy..."
	python -m mypy src
	@echo "✅ Type checking passed"

quality: lint format typecheck
	@echo "✅ All quality checks passed"

# Testing
test:
	pytest tests/ -v

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v

test-slow:
	pytest tests/integration -m slow -v

coverage:
	pytest tests/ --cov=agent_kit --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

# Performance
benchmark:
	python scripts/benchmark_embedder.py
	python scripts/benchmark_index.py

profile:
	py-spy record -o profile.svg -- python scripts/benchmark_embedder.py
	@echo "Profile saved to profile.svg"

# Deployment Gate
dryrun:
	@echo "🔍 Running pre-production validation..."
	@make quality
	@make test
	@echo "🔍 Validating ontology..."
	rapper -i turtle -o ntriples assets/ontologies/core.ttl > /dev/null
	@echo "🔍 Smoke test..."
	python examples/01_embed_and_search.py
	@echo "✅ Dryrun passed - safe to deploy"

# Cleanup
clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "✅ Cleanup complete"

