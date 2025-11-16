#!/bin/bash
# Update GitHub token in .env file
# Run this after regenerating your token

echo "🔄 Updating GitHub token in .env file"
echo "Enter your new GitHub Personal Access Token:"
read -s NEW_TOKEN

if [ -z "$NEW_TOKEN" ]; then
    echo "❌ No token provided"
    exit 1
fi

# Update the .env file
sed -i.bak "s/GITHUB_TOKEN=.*/GITHUB_TOKEN=$NEW_TOKEN/" .env

if [ $? -eq 0 ]; then
    echo "✅ Token updated successfully!"
    echo "🧪 Testing new token..."
    export $(grep -v '^#' .env | xargs)
    if git ls-remote origin > /dev/null 2>&1; then
        echo "✅ New token works!"
        rm -f .env.bak
    else
        echo "❌ New token doesn't work. Check permissions."
        # Restore backup
        mv .env.bak .env
        exit 1
    fi
else
    echo "❌ Failed to update token"
    exit 1
fi
