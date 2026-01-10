#!/bin/bash

# ============================================================================
# Git Repository Setup Script
# Sets up the modular branch structure for Balasore Alloys Dashboard
# ============================================================================

set -e  # Exit on error

echo "=========================================="
echo "Balasore Alloys Dashboard - Git Setup"
echo "=========================================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "Initializing Git repository..."
    git init
    echo "✓ Git initialized"
else
    echo "✓ Git repository already exists"
fi

# Create main branch (if not exists)
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "Creating main branch..."
    git checkout -b main 2>/dev/null || git checkout main
    echo "✓ On main branch"
fi

# Create .gitkeep files for empty directories
echo "Creating .gitkeep files..."
mkdir -p generated_dashboards test_output test_outputs here-is-output logs
touch generated_dashboards/.gitkeep
touch test_output/.gitkeep
touch test_outputs/.gitkeep
touch here-is-output/.gitkeep
touch logs/.gitkeep
echo "✓ .gitkeep files created"

# Initial commit (if no commits yet)
if ! git rev-parse HEAD >/dev/null 2>&1; then
    echo "Creating initial commit..."
    git add .
    git commit -m "chore: initial project structure

- Add department folders (furnace, geology, qc, scm, automobile, crm, env)
- Add core infrastructure (app_main.py, config, templates)
- Add documentation (CONTRIBUTING.md, DEPARTMENT_DEVELOPMENT_GUIDE.md)
- Add .gitignore for Python, logs, generated files
- Add shared utilities (MCP server, auth, database)

This is the base structure before department-specific development begins."
    echo "✓ Initial commit created"
else
    echo "✓ Repository already has commits"
fi

# Create develop branch
echo "Creating develop branch..."
git checkout -b develop 2>/dev/null || git checkout develop
echo "✓ Develop branch ready"

# Create department branches
DEPARTMENTS=("furnace" "geology" "qc" "scm" "automobile" "crm" "env")

echo ""
echo "Creating department branches..."
for dept in "${DEPARTMENTS[@]}"; do
    BRANCH_NAME="dept/$dept"

    if git show-ref --verify --quiet refs/heads/$BRANCH_NAME; then
        echo "  ✓ $BRANCH_NAME already exists"
    else
        git checkout -b $BRANCH_NAME develop
        echo "  ✓ Created $BRANCH_NAME"
    fi
done

# Return to develop
git checkout develop

echo ""
echo "=========================================="
echo "Git Setup Complete!"
echo "=========================================="
echo ""
echo "Branch Structure:"
echo "  main                  (production)"
echo "  develop               (integration)"
echo "  dept/furnace          (furnace team)"
echo "  dept/geology          (geology team)"
echo "  dept/qc               (qc team)"
echo "  dept/scm              (scm team)"
echo "  dept/automobile       (automobile team)"
echo "  dept/crm              (crm team)"
echo "  dept/env              (environment team)"
echo ""
echo "Next Steps:"
echo "1. Set up remote repository:"
echo "   git remote add origin <your-github-url>"
echo ""
echo "2. Push all branches:"
echo "   git push -u origin main"
echo "   git push -u origin develop"
echo "   git push -u origin dept/furnace"
echo "   git push -u origin dept/geology"
echo "   git push -u origin dept/qc"
echo "   git push -u origin dept/scm"
echo "   git push -u origin dept/automobile"
echo "   git push -u origin dept/crm"
echo "   git push -u origin dept/env"
echo ""
echo "3. Share branch assignments with team:"
echo "   - Furnace Lead → dept/furnace"
echo "   - Geology Lead → dept/geology"
echo "   - QC Lead → dept/qc"
echo "   - SCM Lead → dept/scm"
echo "   - Automobile Lead → dept/automobile"
echo "   - CRM Lead → dept/crm"
echo "   - Environment Lead → dept/env"
echo ""
echo "4. Each developer should:"
echo "   git clone <repository-url>"
echo "   git checkout dept/<their-department>"
echo ""
