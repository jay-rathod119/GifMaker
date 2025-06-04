#!/bin/bash

# GitHub token and repository info
GITHUB_TOKEN="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"
REPO_NAME="GifMaker"
GITHUB_USERNAME="jay-rathod119"

# Update remote URL to include the token directly (this is the key fix)
git remote set-url origin "https://$GITHUB_USERNAME:$GITHUB_TOKEN@github.com/$GITHUB_USERNAME/$REPO_NAME.git"

# Push to GitHub
BRANCH=$(git branch --show-current)
echo "Pushing to branch: $BRANCH..."
git push -u origin $BRANCH

echo "Push completed!"



# chmod +x github_push.sh
# ./github_push.sh


