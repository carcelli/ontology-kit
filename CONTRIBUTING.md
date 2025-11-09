# Contributing to Agent Kit

Thank you for your interest in contributing to Agent Kit! This document provides guidelines for contributing to the ontology-driven ML agent framework.

---

## 🎯 Project Vision

Agent Kit enables small businesses to leverage ML insights through ontology-guided agents that navigate hyperdimensional vector spaces. Contributions should prioritize:

1. **Business value**: Faster agent prototyping, better accuracy, lower cost
2. **Reproducibility**: Deterministic navigation, versioned ontologies
3. **Explainability**: Ontology paths for every decision
4. **Accessibility**: Democratize ML for <$50/month per business

---

## 🚀 Quick Start for Contributors

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/agent_kit.git
cd agent_kit
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e .[dev]

# Verify installation
make test
```

### 3. Create a Branch

Use descriptive names with conventional prefixes:

```bash
git checkout -b feat/add-business-agent
git checkout -b fix/vector-index-normalization
git checkout -b docs/improve-quickstart
```

---

## 📝 Contribution Workflow

### Before You Start

1. **Check existing issues**: Search for related issues/PRs to avoid duplication
2. **Open an issue**: For major changes, discuss the approach first
3. **Read the docs**: Review `ARCHITECTURE_PLAN.md` and `BUSINESS_ONTOLOGY_PLAN.md`

### Development Process

1. **Write code**: Follow style guidelines (see below)
2. **Add tests**: Maintain ≥90% coverage for new code
3. **Update docs**: Add docstrings, update README if needed
4. **Run quality checks**:

```bash
make quality    # lint + format + typecheck
make test       # unit tests
make dryrun     # full validation (lint + test + ontology validation)
```

5. **Commit changes**: Use Conventional Commits (see below)
6. **Push and create PR**: Include description + test output

---

## 🧪 Testing Requirements

### Unit Tests

- **Location**: `tests/unit/test_<module>.py`
- **Coverage**: ≥90% for new code, ≥70% overall
- **Run**: `pytest tests/unit -v --cov=agent_kit`

Example:
```python
def test_embedder_batch():
    """Test batch embedding."""
    embedder = Embedder(model_name='all-MiniLM-L6-v2')
    texts = ["Task 1", "Task 2"]
    embeddings = embedder.embed_batch(texts)
    assert embeddings.shape == (2, 384)
```

### Integration Tests

- **Location**: `tests/integration/test_<feature>.py`
- **Scope**: End-to-end workflows (load ontology → embed → query)
- **Mark**: Use `@pytest.mark.slow` for expensive tests
- **Run**: `pytest tests/integration -m slow`

### Test Guidelines

- ✅ Test happy paths and edge cases
- ✅ Use fixtures for repeated setup
- ✅ Mock external APIs (OpenAI, etc.)
- ✅ Add docstrings explaining what's tested
- ❌ Don't test implementation details
- ❌ Don't commit commented-out tests

---

## 🎨 Code Style

### Python Style

- **Formatter**: Black (88 chars, single quotes)
- **Linter**: Ruff (with pyupgrade, flake8-bugbear)
- **Type hints**: Full typing with mypy strict mode
- **Naming**:
  - `snake_case` for functions, variables, methods
  - `PascalCase` for classes
  - `UPPER_SNAKE` for constants
  - `kebab-case` for YAML files

### Docstrings

Use Google-style docstrings:

```python
def embed(self, text: str) -> np.ndarray:
    """
    Embed a single text string.
    
    Args:
        text: Input text
        
    Returns:
        1D numpy array of shape (dimension,)
        
    Raises:
        ValueError: If text is None
    """
    pass
```

### Code Organization

- **Modules**: `src/agent_kit/<component>/`
- **One class per file** (unless tightly coupled)
- **Imports**: Sorted by stdlib → third-party → local
- **Max function length**: ~50 lines (prefer composition)

---

## 📦 Commit Guidelines

### Conventional Commits

Format: `<type>(<scope>): <subject>`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Add/update tests
- `refactor`: Code change (no behavior change)
- `perf`: Performance improvement
- `chore`: Maintenance (deps, tooling)

**Examples**:
```bash
git commit -m "feat(agents): add BaseAgent with observe/plan/act/reflect loop"
git commit -m "fix(vectorspace): normalize vectors before FAISS indexing"
git commit -m "docs(ontology): add business domain examples to README"
git commit -m "test(embedder): increase coverage to 95%"
```

### Commit Best Practices

- ✅ Atomic commits (one logical change per commit)
- ✅ Descriptive subjects (≤72 chars)
- ✅ Body for complex changes (wrap at 72 chars)
- ✅ Reference issues: `Fixes #42`, `Closes #123`
- ❌ Don't commit commented-out code
- ❌ Don't mix refactoring with feature changes

---

## 🔀 Pull Request Process

### PR Template

When opening a PR, include:

1. **Description**: What does this PR do? Why?
2. **Related issues**: `Closes #<issue_number>`
3. **Testing**: Show test output or explain why tests aren't needed
4. **Checklist**:
   - [ ] Tests pass locally (`make test`)
   - [ ] Lint/format pass (`make quality`)
   - [ ] Added tests for new code
   - [ ] Updated docs if needed
   - [ ] Follows commit conventions

### Review Process

1. **CI checks**: Must pass (tests, lint, type check)
2. **Code review**: At least 1 approval required
3. **Merge**: Squash and merge (keep commit history clean)

### PR Labels

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Test improvements
- `breaking`: Breaking API change
- `good-first-issue`: Beginner-friendly
- `help-wanted`: Community input needed

---

## 🧩 Areas to Contribute

### High-Priority (Always Welcome)

1. **Tests**: Increase coverage (current: 64%, target: 90%)
2. **Business ontology**: Add more entities/relations to `business.ttl`
3. **Agent loop**: Implement Phase 2C (observe/plan/act/reflect)
4. **Documentation**: Examples, tutorials, API docs

### Medium-Priority

5. **Optimization**: Fine-tune embeddings (triplet loss)
6. **Integration tests**: E2E workflows
7. **Profiling**: Cost-per-query, latency analysis
8. **Ontology validation**: OWL-RL consistency checks

### Advanced

9. **RL policies**: PPO for action selection
10. **Hybrid search**: FAISS + Neo4j
11. **Meta-optimization**: Hyperparameter tuning with Optuna

---

## 📂 Project Structure

```
agent_kit/
├── src/agent_kit/          # Core library
│   ├── vectorspace/        # Embeddings, FAISS index
│   ├── ontology/           # RDF/OWL loader, business schema
│   ├── agents/             # BaseAgent, planning, memory
│   ├── optimization/       # Training, tuning, evaluation
│   └── tools/              # Utilities
├── tests/
│   ├── unit/               # Fast, isolated tests
│   └── integration/        # E2E tests (slower)
├── assets/ontologies/      # TTL/RDF ontology files
├── examples/               # Demo scripts
├── scripts/                # Utilities (benchmarks, validation)
└── docs/                   # Sphinx documentation
```

---

## 🐛 Bug Reports

### Before Opening an Issue

1. Search existing issues (open + closed)
2. Test on latest `main` branch
3. Reproduce with minimal example

### Issue Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. ...
2. ...

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened (include error messages).

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.12.3]
- Agent Kit version: [e.g., 0.1.0]

**Additional context**
Screenshots, logs, etc.
```

---

## ✨ Feature Requests

Use the issue template and tag with `enhancement`. Include:

1. **Use case**: Why is this needed?
2. **Proposed solution**: How might it work?
3. **Alternatives**: What else have you considered?
4. **Business value**: How does this help small businesses?

---

## 📚 Resources

- **Architecture**: `ARCHITECTURE_PLAN.md` (10 sections, technical design)
- **Business Domain**: `BUSINESS_ONTOLOGY_PLAN.md` (metaphysics → ML)
- **Quick Start**: `QUICKSTART.md` (Phase 1 checklist)
- **Execution Summary**: `EXECUTION_SUMMARY.md` (metrics, roadmap)
- **Makefile**: `make help` (list all commands)

---

## 🤝 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment. We do not tolerate harassment or discrimination of any kind.

### Our Standards

**Positive behavior**:
- Using welcoming and inclusive language
- Respecting differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what's best for the community

**Unacceptable behavior**:
- Trolling, insulting, or derogatory comments
- Personal or political attacks
- Public or private harassment
- Publishing others' private information

### Enforcement

Report violations to [dev@agent_kit.io]. All complaints will be reviewed and investigated promptly.

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License (see `LICENSE` file).

---

## 🙏 Thank You!

Every contribution—code, docs, bug reports, ideas—makes Agent Kit better for small businesses. We appreciate your help in democratizing ML insights!

**Questions?** Open an issue or discussion, or check existing docs.

**Ready to contribute?** Fork, code, test, commit, and open a PR. Let's ship it! 🚀

