# Git Setup Checklist

Use this checklist to ensure your modular Git structure is set up correctly.

## ☐ Phase 1: Local Git Setup

### Step 1: Run Setup Script
```bash
cd E:\MCP-with-API
scripts\setup_git_structure.bat
```

**Verify:**
- [ ] Git repository initialized (.git folder exists)
- [ ] Main branch created
- [ ] Develop branch created
- [ ] All department branches created (dept/furnace, dept/geology, etc.)
- [ ] .gitkeep files in empty directories
- [ ] Initial commit created

**Test:**
```bash
git branch -a
# Should show:
#   * develop
#     main
#     dept/furnace
#     dept/geology
#     dept/qc
#     dept/scm
#     dept/automobile
#     dept/crm
#     dept/env
```

---

## ☐ Phase 2: GitHub Repository Setup

### Step 2: Create GitHub Repository

**Actions:**
1. Go to https://github.com/new
2. Repository name: `balasore-alloys-dashboard`
3. Description: "Manufacturing dashboard system for Balasore Alloys"
4. Visibility: **Private**
5. Do NOT initialize with README, .gitignore, or license
6. Click "Create repository"

**Verify:**
- [ ] Repository created successfully
- [ ] You see instructions for pushing existing repository

### Step 3: Add Remote and Push

```bash
# Replace YOUR-ORG with your actual organization/username
git remote add origin https://github.com/YOUR-ORG/balasore-alloys-dashboard.git

# Push all branches
git push -u origin main
git push -u origin develop
git push -u origin dept/furnace
git push -u origin dept/geology
git push -u origin dept/qc
git push -u origin dept/scm
git push -u origin dept/automobile
git push -u origin dept/crm
git push -u origin dept/env
```

**Verify:**
- [ ] All branches visible on GitHub
- [ ] Code is visible on GitHub
- [ ] No errors during push

---

## ☐ Phase 3: Repository Configuration

### Step 4: Configure Branch Protection

**For 'main' branch:**
1. Go to Settings → Branches
2. Click "Add rule"
3. Branch name pattern: `main`
4. Enable:
   - [x] Require a pull request before merging
   - [x] Require approvals (1 reviewer)
   - [x] Dismiss stale pull request approvals when new commits are pushed
   - [x] Require status checks to pass before merging (if CI/CD setup)
   - [x] Require branches to be up to date before merging
   - [x] Include administrators
   - [ ] Allow force pushes (UNCHECKED)
   - [ ] Allow deletions (UNCHECKED)
5. Click "Create"

**For 'develop' branch:**
1. Repeat above with pattern: `develop`
2. Same settings as main

**Verify:**
- [ ] Branch protection rules visible under Settings → Branches
- [ ] Cannot push directly to main
- [ ] Cannot push directly to develop

### Step 5: Update CODEOWNERS File

**Edit `.github/CODEOWNERS`:**

Replace placeholders with actual GitHub usernames:

```
# Before
* @tech-lead
/departments/furnace/ @furnace-lead

# After (example)
* @john-doe
/departments/furnace/ @amit-kumar
/departments/geology/ @rajesh-sharma
/departments/qc/ @priya-singh
```

**Verify:**
- [ ] All placeholders replaced
- [ ] All GitHub usernames correct
- [ ] File committed and pushed

```bash
git add .github/CODEOWNERS
git commit -m "docs: update CODEOWNERS with team members"
git push origin main
```

### Step 6: Configure Collaborators

1. Go to Settings → Collaborators and teams
2. Click "Add people"
3. Add each team member:
   - [ ] Furnace Lead
   - [ ] Geology Lead
   - [ ] QC Lead
   - [ ] SCM Lead
   - [ ] Automobile Lead
   - [ ] CRM Lead
   - [ ] Environment Lead
4. Set permissions: **Write** (not Admin)

**Verify:**
- [ ] All team members added
- [ ] Each received invitation email
- [ ] Permissions set to "Write"

---

## ☐ Phase 4: Documentation Updates

### Step 7: Update README.md

**Edit `README.md`:**

Replace placeholders:
```markdown
# Before
- **Tech Lead**: [@tech-lead](https://github.com/tech-lead)
- **Furnace Lead**: [@furnace-lead](https://github.com/furnace-lead)

# After (example)
- **Tech Lead**: [@john-doe](https://github.com/john-doe)
- **Furnace Lead**: [@amit-kumar](https://github.com/amit-kumar)
```

**Verify:**
- [ ] All team member links updated
- [ ] Repository URL updated
- [ ] Contact information correct

### Step 8: Create .env.example

**Create `.env.example`:**

```bash
cp .env .env.example
```

**Edit `.env.example` to remove sensitive values:**

```bash
# Before (in .env.example)
MYSQL_PASSWORD=actual_password

# After (in .env.example)
MYSQL_PASSWORD=your_password_here
```

**Verify:**
- [ ] .env.example has NO real passwords
- [ ] .env.example has placeholders only
- [ ] .env is in .gitignore

```bash
git add .env.example
git commit -m "chore: add environment variables template"
git push origin main
```

---

## ☐ Phase 5: Team Onboarding

### Step 9: Prepare Onboarding Package

**Create welcome document for each team:**

File: `TEAM_ONBOARDING.md`

```markdown
# Welcome to Balasore Alloys Dashboard Project

## Your Assignment
- **Department**: Furnace
- **Branch**: dept/furnace
- **Files You Own**:
  - departments/furnace/formatter.py
  - departments/furnace/template_engine.py
  - departments/furnace/claude_analyzer.py
  - templates/furnace_dashboard.html

## Getting Started
1. Clone repository: git clone https://github.com/...
2. Checkout your branch: git checkout dept/furnace
3. Read CONTRIBUTING.md
4. Read docs/DEPARTMENT_DEVELOPMENT_GUIDE.md
5. Read departments/furnace/README.md
6. Setup environment (see below)
7. Generate test dashboard

## Setup Commands
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python app_main.py furnace 2025-12-24
```

## Need Help?
- Tech Lead: @john-doe
- Documentation: CONTRIBUTING.md
- Questions: Create GitHub issue
```

**Verify:**
- [ ] Onboarding document created
- [ ] Department assignments documented
- [ ] Setup instructions clear

### Step 10: Send Invitations

**Email each team member:**

```
Subject: Balasore Alloys Dashboard - Your Department Assignment

Hi [Name],

You've been assigned to the [Department] team for our dashboard project.

Repository: https://github.com/YOUR-ORG/balasore-alloys-dashboard
Your Branch: dept/[department]

Please:
1. Accept GitHub invitation
2. Clone repository
3. Read CONTRIBUTING.md and TEAM_ONBOARDING.md
4. Join our kickoff meeting [Date/Time]

See you at the meeting!

Tech Lead
```

**Verify:**
- [ ] All team members emailed
- [ ] Kickoff meeting scheduled
- [ ] Questions channel setup (Slack/Teams/etc.)

---

## ☐ Phase 6: Testing & Validation

### Step 11: Test Department Isolation

**Test each department can work independently:**

```bash
# Clone as if you're a new developer
cd /tmp
git clone https://github.com/YOUR-ORG/balasore-alloys-dashboard.git test-clone
cd test-clone

# Test furnace department
git checkout dept/furnace
# Make test change
echo "# Test" >> departments/furnace/README.md
git add departments/furnace/
git commit -m "test: verify department isolation"
git push origin dept/furnace
# ✓ Should work without errors

# Test cannot modify other departments directly
git checkout dept/geology
# Try to modify furnace (should work but trigger review)
echo "# Test" >> departments/furnace/README.md
git add departments/furnace/
# ✓ Git allows but CODEOWNERS will flag in PR
```

**Verify:**
- [ ] Can commit to own department
- [ ] Can create PRs
- [ ] CODEOWNERS assigns correct reviewer
- [ ] Branch protection prevents direct push to main/develop

### Step 12: Test Pull Request Flow

**Create test PR:**

1. Make small change on dept/furnace
2. Push to GitHub
3. Create PR: dept/furnace → develop
4. Check PR template appears
5. Check CODEOWNERS auto-assigns reviewer
6. Get review and merge
7. Verify develop has the changes

**Verify:**
- [ ] PR template shows up
- [ ] Reviewer auto-assigned
- [ ] Review required before merge
- [ ] Merge successful
- [ ] Changes appear in develop

### Step 13: Test Shared File Protection

**Create test PR modifying app_main.py:**

1. Create feature branch from develop
2. Modify app_main.py
3. Create PR to develop
4. Check multiple reviewers assigned
5. Verify tech lead gets notification

**Verify:**
- [ ] Tech lead notified
- [ ] Cannot bypass review
- [ ] Status checks run (if configured)

---

## ☐ Phase 7: Production Readiness

### Step 14: Security Review

**Check .gitignore:**
- [ ] .env file ignored
- [ ] Sensitive credentials not in repo
- [ ] Logs directory ignored
- [ ] Generated dashboards ignored
- [ ] Python cache ignored

**Search for secrets:**
```bash
# Search for potential secrets
git log -p | grep -i "password"
git log -p | grep -i "api_key"
git log -p | grep -i "secret"
```

**Verify:**
- [ ] No secrets in commit history
- [ ] .env.example has placeholders only
- [ ] Database passwords not committed

### Step 15: CI/CD Setup (Optional)

**Create `.github/workflows/test.yml`:**

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pytest tests/
```

**Verify:**
- [ ] Workflow file created
- [ ] Tests run on PR
- [ ] Status checks appear on PRs

---

## ☐ Phase 8: Launch

### Step 16: Kickoff Meeting

**Meeting Agenda:**
1. Project overview (5 min)
2. Git workflow explanation (10 min)
3. Department assignments (5 min)
4. Demo: Create PR (10 min)
5. Q&A (10 min)

**Present:**
- CONTRIBUTING.md workflow
- How to create PR
- How to resolve conflicts
- Who to contact for help

**Verify:**
- [ ] Meeting scheduled
- [ ] All team members invited
- [ ] Screen sharing tested
- [ ] Demo repository prepared

### Step 17: First Sprint Planning

**Define first tasks for each department:**

| Department | First Task | Target Date |
|------------|-----------|-------------|
| Furnace | Add hourly production chart | Week 1 |
| Geology | Fix working days calculation | Week 1 |
| QC | Implement test result dashboard | Week 2 |
| SCM | Add inventory tracking | Week 2 |

**Verify:**
- [ ] Tasks assigned
- [ ] Deadlines set
- [ ] Dependencies identified
- [ ] GitHub issues created

---

## ☐ Phase 9: Monitoring & Support

### Step 18: Set Up Monitoring

**GitHub Notifications:**
- [ ] Watch repository (for tech lead)
- [ ] Enable email notifications for PR reviews
- [ ] Setup Slack/Teams integration (optional)

**Weekly Sync:**
- [ ] Schedule weekly team sync
- [ ] Review open PRs
- [ ] Discuss blockers
- [ ] Plan next week

### Step 19: Documentation Maintenance

**Monthly review:**
- [ ] Update README with new features
- [ ] Archive old documentation
- [ ] Update team assignments
- [ ] Review and improve CONTRIBUTING.md

---

## ✅ Final Verification

Run through this final checklist:

**Git Structure:**
- [x] Main branch protected
- [x] Develop branch protected
- [x] All dept branches created
- [x] All branches pushed to GitHub

**Documentation:**
- [x] README.md updated
- [x] CONTRIBUTING.md exists
- [x] CODEOWNERS updated
- [x] Department READMEs created
- [x] .env.example created

**Team:**
- [x] All members added to GitHub
- [x] Branch assignments communicated
- [x] Kickoff meeting completed
- [x] First tasks assigned

**Security:**
- [x] No secrets in repository
- [x] .gitignore configured
- [x] Branch protection enabled

**Testing:**
- [x] PR flow tested
- [x] Department isolation verified
- [x] Shared file protection tested

---

## 📞 Support

If you encounter issues during setup:

1. **Git Issues**: Check docs/GIT_QUICK_REFERENCE.md
2. **Configuration**: Check CONTRIBUTING.md
3. **Permissions**: Verify GitHub collaborators
4. **Still stuck**: Create issue with label "setup-help"

---

**Setup completed on**: _______________
**Completed by**: _______________
**Verified by**: _______________

**Notes**:
_____________________________________________
_____________________________________________
_____________________________________________
