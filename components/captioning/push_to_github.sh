#!/bin/bash

echo "Setting up git and pushing to GitHub..."

# Configure git with your information
echo "1. Configuring git..."
git config --global user.name "hardik121121"
git config --global user.email "hardikarora483@gmail.com"

# Initialize git repository if not already
echo "2. Initializing git repository..."
git init

# Add all files
echo "3. Adding files to git..."
git add .
git add -f output/production/*.json output/production/*.srt output/production/*.html
git add -f output/production_improved/*.json output/production_improved/*.srt output/production_improved/*.html
git add -f output/improvement_evaluation_report.txt output/improvement_statistics.json
git add -f output/README.md

# Create initial commit
echo "4. Creating commit..."
git commit -m "Initial commit: Comprehensive Video Captioning System

- Multi-modal video captioning with LLaVA-NeXT
- Fuses audio analysis (dialogue, emotions, speakers) with visual scenes
- Improved prompt templates for concise, natural captions
- Multiple output formats (JSON, SRT, WebVTT, HTML)
- 63% reduction in caption length with better quality
- Includes evaluation tools and documentation"

# Add remote repository
echo "5. Adding remote repository..."
git remote add origin git@github.com:material-lab-io/Hendrix_Comprehensive_Captioning.git

# Set main branch
echo "6. Setting main branch..."
git branch -M main

# Push to GitHub
echo "7. Pushing to GitHub..."
git push -u origin main

echo ""
echo "Done! Repository pushed to: https://github.com/material-lab-io/Hendrix_Comprehensive_Captioning"
echo ""
echo "You can view it at: https://github.com/material-lab-io/Hendrix_Comprehensive_Captioning"