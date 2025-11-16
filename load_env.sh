#!/bin/bash
# Load Agent Kit environment variables from .env file
# Usage: source load_env.sh

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✅ Agent Kit environment variables loaded"
else
    echo "❌ No .env file found in $(pwd)"
    echo "Run ./setup_github_auth.sh first"
    return 1 2>/dev/null || exit 1
fi
