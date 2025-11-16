# OpenAI Agents SDK Integration

Agent Kit carries a full copy of the upstream [openai-agents](https://github.com/openai/openai-agents-python) repository so ontology-driven extensions can be developed side-by-side with the official SDK.

## Layout

```
ontology-kit/
├── src/agents/                  # Installable OpenAI Agents package vendored into Agent Kit
└── upstream/openai-agents/      # Upstream repository snapshot (docs, tests, workflows, mkdocs)
```

- `src/agents/` is what ships inside the `agent_kit` Python distribution. Anything under this path should match the upstream SDK exactly so imports such as `from agents import Agent` behave the same way they do in the OpenAI release.
- `upstream/openai-agents/` is a convenience mirror of the public repository. It contains documentation (`docs/`), tests, mkdocs configuration, the OpenAI LICENSE, GitHub workflows, and examples. You can diff this snapshot against OpenAI's repo when you need to debug or port new functionality.

## Sync Workflow

1. Update the contents of `upstream/openai-agents/` with the latest official release (either by extracting a tarball/zip or by copying files manually).
2. Run the sync helper:
   ```bash
   make sync-openai-agents
   # or
   python scripts/sync_openai_agents.py
   ```
   The script wipes `src/agents/`, copies the upstream package, and removes stray `*:Zone.Identifier` files that appear in the published archive.
3. Commit the resulting changes alongside any Agent Kit extensions.

## Running Upstream Tests

You can execute OpenAI's own pytest suite directly from the snapshot to make sure the vendored package still behaves identically:

```bash
cd upstream/openai-agents
python -m pip install -e .[test]
pytest
```

> **Tip:** keep a separate virtual environment for running upstream tests so Agent Kit's dependencies do not interfere with the SDK matrix.

## Licensing

OpenAI's SDK is MIT licensed. The original `LICENSE` file is preserved at `upstream/openai-agents/LICENSE`. When distributing Agent Kit, ensure that file remains intact and reference it in any attribution/NOTICE documents for downstream consumers.

