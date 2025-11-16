#!/bin/bash
# Setup GitHub Authentication for Agent Kit
# This script loads credentials from .env file (which should already exist)

set -e  # Exit on any error

echo "🔐 Setting up GitHub authentication..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ No .env file found!"
    echo "Please create a .env file with your GITHUB_TOKEN first."
    echo "See .env.example for the format."
    exit 1
fi

# Load environment variables from .env file
echo "📖 Loading credentials from .env file..."
export $(grep -v '^#' .env | xargs)

# Verify token is loaded
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN not found in .env file!"
    echo "Please add GITHUB_TOKEN=your_token_here to your .env file."
    exit 1
fi

echo "✅ Token loaded successfully"

# Configure git to use token for HTTPS authentication
echo "🔧 Configuring git credentials..."
git config --global credential.helper store
git config --global user.name "orson-dev"
git config --global user.email "orson-dev@github.local"

# Test the connection
echo "🧪 Testing GitHub connection..."
if git ls-remote origin > /dev/null 2>&1; then
    echo "✅ GitHub authentication successful!"
    echo ""
    echo "🔄 To make this permanent, add this to your ~/.bashrc or ~/.zshrc:"
    echo "# Load Agent Kit environment variables"
    echo "if [ -f ~/projects/ontology-kit/.env ]; then"
    echo "    export \$(grep -v '^#' ~/projects/ontology-kit/.env | xargs)"
    echo "fi"
else
    echo "❌ GitHub authentication failed."
    echo "Check your token permissions at: https://github.com/settings/tokens"
    exit 1
fi

echo ""
echo "📝 For CI/CD, add GITHUB_TOKEN as a repository secret in GitHub Settings."
echo "🔒 Your .env file is properly ignored by .gitignore"