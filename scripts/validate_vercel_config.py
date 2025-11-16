#!/usr/bin/env python3
"""
Validate Vercel Configuration

Checks vercel.json for common issues and conflicts.
Usage: python scripts/validate_vercel_config.py
"""

import json
import sys
from pathlib import Path


def validate_vercel_config(config_path: Path = Path("vercel.json")) -> bool:
    """Validate vercel.json configuration for common issues."""

    if not config_path.exists():
        print(f"❌ {config_path} not found")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {config_path}: {e}")
        return False

    print(f"✅ {config_path} is valid JSON")

    # Check for version
    version = config.get("version", 1)
    print(f"   Version: {version}")

    # Check for conflicting properties
    has_builds = "builds" in config
    has_functions = "functions" in config

    if has_builds and has_functions:
        print("❌ ERROR: Both 'builds' and 'functions' present - Vercel conflict!")
        print("   Remove 'builds' (deprecated) or 'functions' to resolve")
        return False
    elif has_functions:
        print("✅ Modern functions-only configuration")
        functions = config["functions"]
        print(f"   Functions: {list(functions.keys())}")

        # Check each function config
        for func_path, func_config in functions.items():
            runtime = func_config.get("runtime")
            if not runtime:
                print(f"⚠️  Function {func_path} missing runtime specification")
            else:
                print(f"   {func_path} → {runtime}")

    elif has_builds:
        print("⚠️  Legacy builds configuration (consider migrating to functions)")
        builds = config["builds"]
        print(f"   Builds: {len(builds)} entries")

    else:
        print("❌ ERROR: Neither 'builds' nor 'functions' configured")
        return False

    # Check routes
    routes = config.get("routes", [])
    if routes:
        print(f"✅ Routes configured: {len(routes)}")
        for route in routes:
            src = route.get("src", "unknown")
            dest = route.get("dest", "unknown")
            print(f"   {src} → {dest}")
    else:
        print("ℹ️  No routes configured (may be auto-generated)")

    return True


if __name__ == "__main__":
    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("vercel.json")
    success = validate_vercel_config(config_path)
    sys.exit(0 if success else 1)
