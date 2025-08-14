# Git Push and Repository Setup Guide

This guide covers pushing your code to GitHub and setting up the repository for collaboration.

## Prerequisites

1. GitHub account
2. Git installed locally
3. SSH key configured (recommended) or HTTPS credentials

## Step 1: Verify Local Repository

```bash
# Check current status
git status

# View commit history
git log --oneline -5

# Check remote configuration
git remote -v
```

## Step 2: Configure SSH (if not already done)

### Generate SSH Key
```bash
# Generate new SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Start SSH agent
eval "$(ssh-agent -s)"

# Add SSH key to agent
ssh-add ~/.ssh/id_ed25519
```

### Add SSH Key to GitHub
```bash
# Copy public key
cat ~/.ssh/id_ed25519.pub

# Then:
# 1. Go to GitHub Settings > SSH and GPG keys
# 2. Click "New SSH key"
# 3. Paste the key and save
```

### Test Connection
```bash
ssh -T git@github.com
# Should see: "Hi username! You've successfully authenticated..."
```

## Step 3: Configure Repository Remote

```bash
# If you haven't set up the remote yet
git remote add origin git@github.com:yourusername/hendrix_12aug.git

# Or switch from HTTPS to SSH
git remote set-url origin git@github.com:yourusername/hendrix_12aug.git

# Verify
git remote -v
```

## Step 4: Push to GitHub

### Initial Push
```bash
# Push main branch and set upstream
git push -u origin main

# If the branch doesn't exist on GitHub yet
git push --set-upstream origin main
```

### Subsequent Pushes
```bash
# Regular push
git push

# Push all branches
git push --all

# Push tags
git push --tags
```

## Step 5: Post-Push Setup

### Using GitHub CLI
```bash
# Install GitHub CLI if needed
# macOS: brew install gh
# Linux: See https://github.com/cli/cli#installation

# Authenticate
gh auth login

# Run setup script
bash scripts/setup_github_repo.sh
```

### Manual Setup on GitHub.com

1. **Repository Settings**
   - Go to Settings > General
   - Add description
   - Add website (if applicable)
   - Add topics: `video-analysis`, `ai`, `computer-vision`, etc.

2. **Branch Protection**
   - Go to Settings > Branches
   - Add rule for `main`
   - Enable: Require PR reviews, status checks, up-to-date branches

3. **Enable Features**
   - Issues (enabled by default)
   - Discussions (Settings > General > Features)
   - Wiki (optional)
   - Projects (for task tracking)

4. **Create Labels**
   - Go to Issues > Labels
   - Create custom labels for your workflow

5. **Set Up Actions**
   - Go to Actions tab
   - Workflows should run automatically on next push

## Step 6: Create Initial Release

```bash
# Using GitHub CLI
gh release create v2.1.0 \
  --title "Hendrix v2.1.0 - Enhanced Documentation & Infrastructure" \
  --notes "See CHANGELOG.md for details" \
  --draft

# Or on GitHub.com
# 1. Go to Releases
# 2. Click "Create a new release"
# 3. Tag: v2.1.0
# 4. Use RELEASE_TEMPLATE.md content
```

## Step 7: Announce Your Project

1. **Update Social Profiles**
   - Add repository to your GitHub profile README
   - Share on LinkedIn/Twitter
   - Post in relevant communities

2. **Submit to Directories**
   - Awesome lists related to video analysis
   - ML/AI project directories
   - Python package indexes

3. **Create Documentation Site** (optional)
   ```bash
   # Using MkDocs
   pip install mkdocs mkdocs-material
   mkdocs new docs-site
   # Configure and deploy to GitHub Pages
   ```

## Troubleshooting

### Permission Denied
```bash
# Check SSH key is loaded
ssh-add -l

# Re-add key if needed
ssh-add ~/.ssh/id_ed25519
```

### Remote Already Exists
```bash
# Remove and re-add
git remote remove origin
git remote add origin git@github.com:yourusername/hendrix_12aug.git
```

### Large Files Issue
```bash
# If you have large files, use Git LFS
git lfs track "*.model"
git lfs track "*.pth"
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

### Force Push (use carefully!)
```bash
# Only if absolutely necessary
git push --force origin main
```

## Best Practices

1. **Commit Messages**: Use conventional commits
   - `feat:` New features
   - `fix:` Bug fixes
   - `docs:` Documentation
   - `chore:` Maintenance

2. **Branch Strategy**
   - `main`: Stable releases
   - `develop`: Active development
   - `feature/*`: New features
   - `hotfix/*`: Emergency fixes

3. **Regular Maintenance**
   - Keep dependencies updated
   - Review and merge Dependabot PRs
   - Respond to issues promptly
   - Tag releases consistently

## Next Steps

1. Monitor GitHub Actions for CI status
2. Set up project board for tracking work
3. Create initial issues for known tasks
4. Invite collaborators
5. Start working on v2.2.0 features!

---

For more help, see the [GitHub documentation](https://docs.github.com/) or ask in our [Discord community](https://discord.gg/hendrix).