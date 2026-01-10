# Contributing to Balasore Alloys Dashboard System

## Project Structure

This is a modular dashboard system where each department has its own dedicated developer working independently on department-specific branches.

## Department Ownership

Each department has one responsible developer:

- **Furnace**: `dept/furnace` branch
- **Geology**: `dept/geology` branch
- **QC**: `dept/qc` branch
- **SCM**: `dept/scm` branch
- **Automobile**: `dept/automobile` branch
- **CRM**: `dept/crm` branch
- **Environment**: `dept/env` branch

## Git Branching Strategy

### Branch Structure

```
main (production)
├── develop (integration branch)
├── dept/furnace (furnace team)
├── dept/geology (geology team)
├── dept/qc (qc team)
├── dept/scm (scm team)
├── dept/automobile (automobile team)
├── dept/crm (crm team)
└── dept/env (environment team)
```

### Workflow for Department Developers

#### 1. Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd MCP-with-API

# Create and checkout your department branch
git checkout -b dept/furnace origin/dept/furnace

# Install dependencies
pip install -r requirements.txt
```

#### 2. Daily Development Workflow

```bash
# Start your work day - pull latest changes from develop
git checkout dept/furnace
git pull origin develop

# Make your changes to your department files
# Edit files in: departments/furnace/

# Test your changes
python test_department.py furnace

# Commit your changes
git add departments/furnace/
git commit -m "feat(furnace): add new tapping efficiency chart"

# Push to your department branch
git push origin dept/furnace
```

#### 3. Creating a Pull Request

When you're ready to merge your changes to `develop`:

1. Push your branch: `git push origin dept/furnace`
2. Go to GitHub and create a Pull Request from `dept/furnace` → `develop`
3. Request review from the tech lead
4. After approval, the tech lead will merge to `develop`

### Shared Files - IMPORTANT

⚠️ **DO NOT MODIFY** these shared files without coordination:

**Core Infrastructure** (requires tech lead approval):
- `app_main.py` - Main application entry point
- `config_modules/config.py` - Global configuration
- `core/` - Core utilities (MCP server, database)
- `requirements.txt` - Dependencies

**Shared Frontend** (requires UI/UX approval):
- `templates/base.html` - Base template
- `templates/common/` - Shared components
- `static/` - Shared CSS/JS/images

**Department Configuration** (coordinate with tech lead):
- `dashboards/department_config.json` - Department registry

### What You CAN Modify Freely

✅ **Your Department Folder** - Full ownership:
```
departments/<your-dept>/
├── __init__.py
├── formatter.py          # Your data processing logic
├── template_engine.py    # Your HTML generation
├── claude_analyzer.py    # Your AI insights (if any)
└── README.md            # Your documentation
```

✅ **Your Department Template** (with caution):
```
templates/<your-dept>_dashboard.html
```
- You can modify the structure/layout
- Do NOT break the JavaScript API contract
- Maintain the `analysisData` format expected by frontend

✅ **Your Department Tests**:
```
tests/test_<your-dept>.py
```

## File Ownership Matrix

| File/Folder | Ownership | Modification Rights |
|-------------|-----------|---------------------|
| `departments/furnace/*` | Furnace Team | Full access |
| `departments/geology/*` | Geology Team | Full access |
| `departments/qc/*` | QC Team | Full access |
| `departments/scm/*` | SCM Team | Full access |
| `departments/automobile/*` | Automobile Team | Full access |
| `departments/crm/*` | CRM Team | Full access |
| `departments/env/*` | Environment Team | Full access |
| `templates/furnace_dashboard.html` | Furnace Team | With caution |
| `templates/geology_dashboard.html` | Geology Team | With caution |
| `app_main.py` | Tech Lead | PR required |
| `dashboards/department_config.json` | Tech Lead | PR required |
| `core/*` | Tech Lead | PR required |
| `config_modules/*` | Tech Lead | PR required |
| `templates/base.html` | UI/UX Lead | PR required |

## How to Request Shared File Changes

If you need changes to shared files (e.g., `app_main.py`, `department_config.json`):

1. **Document the requirement**:
   - Create an issue: "Need to add new API endpoint for furnace power analytics"
   - Explain what you need and why

2. **Propose the change**:
   - Create a feature branch: `feat/furnace-power-endpoint`
   - Make minimal changes to shared files
   - Update only what's necessary for your feature

3. **Submit PR with context**:
   - Reference the issue
   - Explain impact on other departments
   - Request review from tech lead + affected teams

## Merge Conflicts - Resolution Strategy

### Scenario 1: Conflict in Your Department Files

**Rare** - only happens if two people work on same department

```bash
# Pull latest develop
git checkout dept/furnace
git pull origin develop

# If conflicts in departments/furnace/
# YOU resolve them (you know your code best)
git mergetool
git commit
```

### Scenario 2: Conflict in Shared Files

**Common** - multiple departments modifying `app_main.py`

```bash
# Pull latest develop
git pull origin develop

# If conflict in app_main.py or department_config.json
# Contact tech lead IMMEDIATELY
# DO NOT resolve alone
```

## Testing Your Changes

Before pushing:

```bash
# 1. Test your department specifically
python -c "from departments.furnace.formatter import FurnaceDataProcessor; print('✓ Import works')"

# 2. Generate a test dashboard
python app_main.py furnace 2025-12-24

# 3. Check for errors in logs
cat logs/app.log | grep ERROR

# 4. Run department-specific tests (if available)
pytest tests/test_furnace.py -v
```

## Code Style Guidelines

### Python Code
- Follow PEP 8
- Use type hints where possible
- Document complex functions
- Keep functions small and focused

### Naming Conventions
```python
# Department-specific classes - prefix with department name
class FurnaceDataProcessor:
    pass

class GeologyAnalyzer:
    pass

# Shared utilities - generic names
class MCPServer:
    pass
```

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `docs`: Documentation
- `test`: Tests
- `style`: Formatting

**Scopes**:
- `furnace`, `geology`, `qc`, `scm`, `automobile`, `crm`, `env`
- `core`, `config`, `api`, `ui`

**Examples**:
```
feat(furnace): add tapping efficiency chart to dashboard

Added new chart showing tapping cycles per shift with
efficiency calculations based on power consumption.

Closes #123
```

```
fix(geology): correct working days calculation for date ranges

Working days were showing 9 instead of 8 due to off-by-one
error in date range query.

Fixes #456
```

## Emergency Hotfixes

If production is broken:

1. Create hotfix branch from `main`: `git checkout -b hotfix/critical-bug main`
2. Fix the issue
3. Test thoroughly
4. PR directly to `main` (tag tech lead)
5. After merge to `main`, backport to `develop`

## Questions?

- **Technical Issues**: Create GitHub issue with `question` label
- **Git Help**: Tag @tech-lead in PR or Slack
- **Merge Conflicts**: Contact tech lead immediately
- **Architecture Decisions**: Schedule meeting with tech lead

## Useful Git Commands

```bash
# See what branch you're on
git branch

# See what files changed
git status

# Discard changes to a file
git checkout -- departments/furnace/formatter.py

# Create new branch from develop
git checkout develop
git pull origin develop
git checkout -b feat/furnace-new-feature

# Stash changes temporarily
git stash
git pull origin develop
git stash pop

# See commit history
git log --oneline --graph --all

# Compare your branch with develop
git diff develop..dept/furnace
```

---

**Last Updated**: 2026-01-10
**Maintained By**: Tech Lead Team
