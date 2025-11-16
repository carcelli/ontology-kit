#!/usr/bin/env python3
"""Sync the vendored OpenAI Agents SDK into src/agents."""

from __future__ import annotations

import argparse
import filecmp
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_DIR = ROOT / "upstream" / "openai-agents" / "src" / "agents"
TARGET_DIR = ROOT / "src" / "agents"


def _remove_zone_identifier_files(root: Path) -> None:
    """Remove Windows Zone.Identifier files that ship in OpenAI's archive."""
    for path in root.rglob("*:Zone.Identifier"):
        path.unlink()


def _dir_is_equal(a: Path, b: Path) -> bool:
    """Shallow equality check used for --check mode."""
    comparison = filecmp.dircmp(a, b)
    if comparison.left_only or comparison.right_only or comparison.diff_files:
        return False
    for subdir in comparison.common_dirs:
        if not _dir_is_equal(a / subdir, b / subdir):
            return False
    return True


def sync_agents(remove_existing: bool = True) -> None:
    if not UPSTREAM_DIR.exists():
        raise SystemExit(
            f"Upstream OpenAI Agents package not found at {UPSTREAM_DIR}. "
            "Populate upstream/openai-agents first."
        )

    if TARGET_DIR.exists() and remove_existing:
        shutil.rmtree(TARGET_DIR)

    shutil.copytree(UPSTREAM_DIR, TARGET_DIR)
    _remove_zone_identifier_files(TARGET_DIR)


def check_sync() -> bool:
    if not TARGET_DIR.exists() or not UPSTREAM_DIR.exists():
        return False
    return _dir_is_equal(UPSTREAM_DIR, TARGET_DIR)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync vendored OpenAI Agents SDK")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only verify whether src/agents matches the upstream snapshot",
    )
    args = parser.parse_args()

    if args.check:
        if check_sync():
            print("✅ src/agents is up-to-date with upstream snapshot")
            return
        raise SystemExit(
            "Vendored src/agents differs from upstream snapshot. Run without --check to sync."
        )

    sync_agents()
    print("✅ Synced OpenAI Agents SDK into src/agents")


if __name__ == "__main__":
    main()
