#!/bin/bash

# Setup script for FPI Data Automation
# Run this script to set up GitHub Actions workflow

echo "=================================="
echo "🚀 FPI Data Automation Setup"
echo "=================================="
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Error: Not a git repository"
    echo "Run: git init"
    exit 1
fi

echo "✓ Git repository detected"
echo ""

# Create workflow directory
echo "📁 Creating GitHub Actions workflow directory..."
mkdir -p .github/workflows

# Check if workflow file exists
if [ -f ".github/workflows/update_data.yml" ]; then
    echo "⚠️  Workflow file already exists"
    read -p "Overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping workflow creation"
    fi
fi

# Create requirements.txt additions
echo ""
echo "📦 Checking requirements.txt..."
if [ -f "requirements.txt" ]; then
    # Check if beautifulsoup4 is already in requirements
    if ! grep -q "beautifulsoup4" requirements.txt; then
        echo "Adding scraper dependencies..."
        echo "beautifulsoup4>=4.12.0" >> requirements.txt
        echo "openpyxl>=3.1.0" >> requirements.txt
        echo "xlrd>=2.0.1" >> requirements.txt
        echo "✓ Dependencies added to requirements.txt"
    else
        echo "✓ Dependencies already present"
    fi
else
    echo "❌ requirements.txt not found"
    exit 1
fi

# Create FPI_Reports directory
echo ""
echo "📁 Creating FPI_Reports directory..."
mkdir -p FPI_Reports

# Create .gitignore entry for reports
if [ -f ".gitignore" ]; then
    if ! grep -q "FPI_Reports/" .gitignore; then
        echo "FPI_Reports/*.xls*" >> .gitignore
        echo "FPI_Reports/*.csv" >> .gitignore
        echo "✓ Added FPI_Reports to .gitignore"
    fi
else
    echo "FPI_Reports/*.xls*" > .gitignore
    echo "FPI_Reports/*.csv" >> .gitignore
    echo "✓ Created .gitignore"
fi

# Test if scraper.py exists
echo ""
if [ -f "scraper.py" ]; then
    echo "✓ scraper.py found"
else
    echo "⚠️  scraper.py not found - please create it"
fi

# Git status check
echo ""
echo "📊 Current git status:"
git status --short

# Commit prompt
echo ""
read -p "🔄 Commit changes now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add .
    git commit -m "Setup: Add automated data update workflow"
    echo "✓ Changes committed"
    echo ""
    read -p "📤 Push to GitHub? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git push
        echo "✓ Pushed to GitHub"
    fi
fi

# Instructions
echo ""
echo "=================================="
echo "📋 NEXT STEPS:"
echo "=================================="
echo ""
echo "1. Get Render Deploy Hook:"
echo "   → https://dashboard.render.com"
echo "   → Select your app → Settings"
echo "   → Create Deploy Hook"
echo ""
echo "2. Add to GitHub Secrets:"
echo "   → Repository Settings → Secrets"
echo "   → New secret: RENDER_DEPLOY_HOOK"
echo "   → Paste the webhook URL"
echo ""
echo "3. Test the workflow:"
echo "   → Go to Actions tab"
echo "   → Select 'Auto-Update FPI Data'"
echo "   → Click 'Run workflow'"
echo ""
echo "✅ Setup complete!"
echo "=================================="