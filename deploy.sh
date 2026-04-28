#!/bin/bash
# Deploy script for Gym Tracker Bot
# Usage: GITHUB_TOKEN=xxx DISCORD_TOKEN=xxx ./deploy.sh

set -e

GITHUB_TOKEN="${GITHUB_TOKEN}"
DISCORD_TOKEN="${DISCORD_TOKEN}"
REPO_NAME="gym-tracker-data"
GITHUB_USERNAME=""

# Get GitHub username
echo "Getting GitHub username..."
GITHUB_USERNAME=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | jq -r '.login')
echo "GitHub Username: $GITHUB_USERNAME"

# Create GitHub repo
echo "Creating GitHub repo: $REPO_NAME..."
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user/repos \
  -d "{\"name\":\"$REPO_NAME\",\"description\":\"Gym Tracker Data - Workouts stored as JSON\",\"homepage\":\"https://$GITHUB_USERNAME.github.io/$REPO_NAME\",\"private\":false}"

# Initialize local repo
cd /home/susu/.gymbot
git init
git remote add origin https://$GITHUB_TOKEN@github.com/$GITHUB_USERNAME/$REPO_NAME.git

# Create necessary directories
mkdir -p workouts active

# Add all files
git add .
git commit -m "Initial commit: Gym Tracker Bot"

# Push to GitHub
git branch -M main
git push -u origin main

echo "========================================="
echo "SUCCESS! Repo created: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo ""
echo "NEXT STEPS:"
echo "1. Go to https://railway.app"
echo "2. Click 'New Project' → 'Deploy from GitHub repo'"
echo "3. Select: $GITHUB_USERNAME/$REPO_NAME"
echo "4. Add environment variables:"
echo "   - DISCORD_TOKEN = $DISCORD_TOKEN"
echo "   - GITHUB_TOKEN = $GITHUB_TOKEN"
echo "   - GITHUB_REPO = $GITHUB_USERNAME/$REPO_NAME"
echo "5. Deploy!"
echo ""
echo "Enable GitHub Pages:"
echo "1. Go to repo settings → Pages"
echo "2. Source: Deploy from a branch → main"
echo "========================================="
