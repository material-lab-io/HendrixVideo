#!/bin/bash
# Script to help set up GitHub repository settings
# Run this after pushing the code to GitHub

echo "=== GitHub Repository Setup Helper ==="
echo "This script provides commands to set up your GitHub repository."
echo "Run these commands using GitHub CLI (gh) or do them manually on GitHub.com"
echo ""

REPO="yourusername/hendrix_12aug"

echo "1. Set repository description and topics:"
echo "gh repo edit $REPO --description \"AI-powered video analysis pipeline with shot detection, transcription, and caption generation\""
echo "gh repo edit $REPO --add-topic video-analysis,ai,computer-vision,speech-recognition,caption-generation,llava,whisper"
echo ""

echo "2. Configure repository settings:"
echo "# Enable issues"
echo "gh repo edit $REPO --enable-issues"
echo "# Enable discussions"
echo "gh repo edit $REPO --enable-discussions"
echo "# Enable wiki (optional)"
echo "gh repo edit $REPO --enable-wiki"
echo ""

echo "3. Set up branch protection for main branch:"
cat << 'EOF'
gh api repos/$REPO/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["lint","test"]}' \
  --field enforce_admins=false \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null \
  --field allow_force_pushes=false \
  --field allow_deletions=false
EOF
echo ""

echo "4. Create initial labels:"
echo "gh label create \"good first issue\" --description \"Good for newcomers\" --color 7057ff"
echo "gh label create \"help wanted\" --description \"Extra attention is needed\" --color 008672"
echo "gh label create \"model-request\" --description \"Request for new model support\" --color 0052CC"
echo "gh label create \"performance\" --description \"Performance improvements\" --color F9D71C"
echo ""

echo "5. Create initial milestones:"
echo "gh api repos/$REPO/milestones --method POST --field title=\"v2.2.0\" --field description=\"Next minor release\""
echo "gh api repos/$REPO/milestones --method POST --field title=\"v3.0.0\" --field description=\"Next major release\""
echo ""

echo "6. Set up GitHub Pages (for documentation):"
echo "gh api repos/$REPO/pages --method POST --field source='{"branch":"gh-pages","path":"/"}"
echo ""

echo "7. Create first release:"
echo "gh release create v2.1.0 --title \"Hendrix v2.1.0 - Enhanced Documentation & Infrastructure\" --notes-file .github/RELEASE_TEMPLATE.md"
echo ""

echo "=== Manual Steps ==="
echo "1. Go to Settings > General:"
echo "   - Add repository avatar/logo"
echo "   - Configure features (Wikis, Projects, etc.)"
echo ""
echo "2. Go to Settings > Secrets and variables > Actions:"
echo "   - Add any required secrets (PYPI_TOKEN, etc.)"
echo ""
echo "3. Go to Settings > Pages:"
echo "   - Configure custom domain if desired"
echo ""
echo "4. Create a Project board for tracking work"
echo ""
echo "5. Pin important issues or discussions"
echo ""

echo "=== Community Setup ==="
echo "1. Create a Discord server and add webhook for GitHub notifications"
echo "2. Set up social media accounts for announcements"
echo "3. Consider creating a project website"
echo ""

echo "Repository URL: https://github.com/$REPO"