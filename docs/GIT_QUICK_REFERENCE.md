# Git Quick Reference Guide

## Initial Setup (One-time)

### For Tech Lead (Repository Owner)

```bash
# 1. Navigate to project directory
cd E:\MCP-with-API

# 2. Run setup script (Windows)
scripts\setup_git_structure.bat

# 3. Create GitHub repository (on GitHub.com)
# - Go to github.com
# - Click "New Repository"
# - Name: balasore-alloys-dashboard
# - Private repository
# - Do NOT initialize with README

# 4. Add remote and push all branches
git remote add origin https://github.com/your-org/balasore-alloys-dashboard.git
git push -u origin main
git push -u origin develop
git push -u origin dept/furnace
git push -u origin dept/geology
git push -u origin dept/qc
git push -u origin dept/scm
git push -u origin dept/automobile
git push -u origin dept/crm
git push -u origin dept/env

# 5. Set branch protection rules on GitHub
# - Go to Settings → Branches
# - Protect 'main' and 'develop' branches
# - Require pull request reviews
```

### For Department Developers

```bash
# 1. Clone repository
git clone https://github.com/your-org/balasore-alloys-dashboard.git
cd balasore-alloys-dashboard

# 2. Checkout your department branch
git checkout dept/furnace

# 3. Set up Python environment
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 5. Test your setup
python app_main.py furnace 2025-12-24
```

## Daily Workflow

### Start Your Day

```bash
# 1. Checkout your branch
git checkout dept/furnace

# 2. Pull latest changes from develop
git pull origin develop

# 3. Check status
git status
```

### Make Changes

```bash
# 1. Edit your files
# - departments/furnace/formatter.py
# - departments/furnace/template_engine.py
# - templates/furnace_dashboard.html

# 2. Test your changes
python app_main.py furnace 2025-12-24

# 3. Check what changed
git status
git diff

# 4. Stage your changes
git add departments/furnace/
git add templates/furnace_dashboard.html

# 5. Commit with descriptive message
git commit -m "feat(furnace): add power efficiency trend chart

Added hourly power consumption chart to show efficiency trends
throughout the day. Includes comparison against 3600 kWh/MT norm.

Fixes #123"

# 6. Push to your branch
git push origin dept/furnace
```

### Create Pull Request

```bash
# 1. Push your branch (if not already pushed)
git push origin dept/furnace

# 2. Go to GitHub repository
# 3. Click "Pull requests" → "New pull request"
# 4. Set base: develop, compare: dept/furnace
# 5. Fill in PR template
# 6. Request review from @tech-lead
# 7. Wait for approval and merge
```

## Common Scenarios

### Scenario 1: Need to Modify Shared File (app_main.py)

```bash
# 1. Create issue on GitHub first
# "Need to add /api/v1/furnace/hourly endpoint"

# 2. Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feat/furnace-hourly-endpoint

# 3. Make minimal changes to app_main.py
# Add only what's necessary for your feature

# 4. Test thoroughly
python app_main.py furnace 2025-12-24
python app_main.py geology 2025-12-24  # Ensure other depts still work

# 5. Commit and push
git add app_main.py departments/furnace/
git commit -m "feat(furnace): add hourly breakdown endpoint"
git push origin feat/furnace-hourly-endpoint

# 6. Create PR: feat/furnace-hourly-endpoint → develop
# Tag @tech-lead and explain why app_main.py change is needed
```

### Scenario 2: Merge Conflict

```bash
# Situation: You try to pull and get conflict

git checkout dept/furnace
git pull origin develop

# Output: CONFLICT in departments/furnace/formatter.py

# 1. If conflict is in YOUR department files:
#    YOU resolve it (you know your code best)
git status  # See conflicted files
# Edit file, look for <<<<<<< markers
# Choose which code to keep
git add departments/furnace/formatter.py
git commit -m "fix: resolve merge conflict in formatter"

# 2. If conflict is in SHARED files (app_main.py):
#    STOP! Contact tech lead
#    Do NOT resolve alone
```

### Scenario 3: Accidentally Modified Wrong File

```bash
# You edited departments/geology/formatter.py by mistake

# Discard changes to that file
git checkout -- departments/geology/formatter.py

# Or discard ALL uncommitted changes
git reset --hard HEAD
```

### Scenario 4: Need to Stash Changes Temporarily

```bash
# You're in middle of work, need to switch branches

# 1. Stash your changes
git stash save "WIP: power efficiency feature"

# 2. Switch to other branch
git checkout develop

# 3. Do what you need to do...

# 4. Return to your branch
git checkout dept/furnace

# 5. Restore your changes
git stash pop
```

### Scenario 5: Made Commit to Wrong Branch

```bash
# You committed to 'develop' instead of 'dept/furnace'

# 1. Create your branch from current state
git branch dept/furnace

# 2. Reset develop to before your commit
git checkout develop
git reset --hard origin/develop

# 3. Your commit is now on dept/furnace
git checkout dept/furnace
```

## Commit Message Format

### Structure

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat` - New feature
- `fix` - Bug fix
- `refactor` - Code restructuring
- `docs` - Documentation only
- `style` - Formatting, missing semicolons, etc
- `test` - Adding tests
- `chore` - Maintenance tasks

### Scopes

- `furnace`, `geology`, `qc`, `scm`, `automobile`, `crm`, `env`
- `core`, `api`, `ui`, `config`

### Examples

```bash
# Good commits
git commit -m "feat(furnace): add tapping cycle efficiency chart"
git commit -m "fix(geology): correct working days calculation for date ranges"
git commit -m "refactor(qc): simplify test result aggregation logic"
git commit -m "docs(furnace): add README for new developers"

# Bad commits (avoid these)
git commit -m "fixed stuff"
git commit -m "updates"
git commit -m "WIP"
```

## Useful Commands

### Check Status

```bash
# What branch am I on?
git branch

# What files changed?
git status

# What exactly changed?
git diff

# Show commit history
git log --oneline --graph --all

# See who changed what
git blame departments/furnace/formatter.py
```

### Branch Management

```bash
# List all branches
git branch -a

# Switch to branch
git checkout dept/furnace

# Create new branch from current
git checkout -b feat/new-feature

# Delete local branch
git branch -d feat/old-feature

# See branch tracking
git branch -vv
```

### Syncing

```bash
# Get latest from remote
git fetch origin

# Pull latest develop
git pull origin develop

# Pull your branch
git pull origin dept/furnace

# See differences with remote
git diff origin/dept/furnace
```

### Undoing Changes

```bash
# Discard uncommitted changes to file
git checkout -- departments/furnace/formatter.py

# Discard ALL uncommitted changes
git reset --hard HEAD

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Undo commit that's already pushed
# DON'T DO THIS - talk to tech lead instead
```

## Branch Protection Rules (GitHub)

### Main Branch

- ✅ Require pull request reviews (1 reviewer)
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ✅ Include administrators
- ❌ Allow force pushes
- ❌ Allow deletions

### Develop Branch

- ✅ Require pull request reviews (1 reviewer)
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ❌ Include administrators
- ❌ Allow force pushes
- ❌ Allow deletions

### Department Branches (dept/*)

- ❌ Require pull request reviews (developers can push directly)
- ❌ Require status checks
- ❌ Allow force pushes (with caution)
- ❌ Allow deletions

## Troubleshooting

### "Permission denied (publickey)"

```bash
# Set up SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"
# Add to GitHub: Settings → SSH Keys → New SSH Key
```

### "refusing to merge unrelated histories"

```bash
git pull origin develop --allow-unrelated-histories
```

### "Your branch is behind 'origin/dept/furnace'"

```bash
git pull origin dept/furnace
```

### "Changes not staged for commit"

```bash
# You edited files but didn't stage them
git add departments/furnace/
git commit -m "your message"
```

## Getting Help

### In Terminal

```bash
# Help for any command
git help commit
git commit --help

# Short help
git commit -h
```

### Resources

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- Project CONTRIBUTING.md
- Tech Lead: @tech-lead

## Emergency Contacts

- **Merge Conflicts in Shared Files**: @tech-lead
- **Lost Commits**: @tech-lead
- **Branch Protection Issues**: @tech-lead
- **Repository Access**: @tech-lead

---

**Last Updated**: 2026-01-10
**Maintained By**: Tech Lead
