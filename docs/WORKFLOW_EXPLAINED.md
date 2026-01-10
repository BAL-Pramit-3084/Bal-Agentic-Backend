# Workflow Explained - Simple Guide

This document explains **exactly** how the Git workflow works from different perspectives.

---

# 🎯 The Big Picture

You have **7 departments**, each with **1 developer**. They all need to work on the **same codebase** without breaking each other's work.

**Solution**: Each developer gets their own **branch** (like their own copy) where they can work freely.

---

# 👨‍💼 YOUR PERSPECTIVE (Project Manager / Tech Lead)

## What You See

```
GitHub Repository
├── main branch (LOCKED - production code)
├── develop branch (LOCKED - integration)
└── 7 department branches (developers work here)
    ├── dept/furnace (Amit works here)
    ├── dept/geology (Rajesh works here)
    ├── dept/qc (Priya works here)
    ├── dept/scm (Suresh works here)
    ├── dept/automobile (Kiran works here)
    ├── dept/crm (Neha works here)
    └── dept/env (Vijay works here)
```

## Your Daily Workflow

### Morning: Check What's Happening

1. **Open GitHub** → Go to repository
2. **Check "Pull Requests" tab**
   - See who submitted work for review
   - Example: "Amit (Furnace): Add power efficiency chart"

3. **Review each PR:**
   ```
   PR #12: feat(furnace): Add power efficiency chart
   From: dept/furnace → develop
   By: @amit-kumar

   Files Changed:
   ✅ departments/furnace/formatter.py (Safe - only his department)
   ✅ departments/furnace/template_engine.py (Safe - only his department)
   ✅ templates/furnace_dashboard.html (Safe - his template)
   ```

4. **Your actions:**
   - Click "Files changed" - review the code
   - If good: Click "Approve" → Click "Merge pull request"
   - If issues: Click "Request changes" → Add comments

### What Happens When You Merge a PR?

```
BEFORE:
dept/furnace: [Amit's new code]
develop:      [Old code]

YOU MERGE PR

AFTER:
dept/furnace: [Amit's new code]
develop:      [Amit's new code is now here]

All other developers can now get Amit's changes
```

### When Someone Modifies Shared Files (app_main.py)

**Example: Amit needs to add API endpoint in app_main.py**

1. Amit creates PR with changes to `app_main.py`
2. GitHub **auto-tags you** (because CODEOWNERS says tech-lead reviews app_main.py)
3. You get notification
4. You review carefully:
   ```python
   # Amit's change in app_main.py
   @app.route('/api/v1/furnace/hourly', methods=['GET'])
   def furnace_hourly_data():
       # Amit's code
   ```
5. You check:
   - ✅ Does this break other departments? (No - only furnace route)
   - ✅ Is code quality good?
   - ✅ Is it necessary? (Yes - needed for his feature)
6. You approve and merge

**Why this matters:** If you don't check, Amit might break Rajesh's geology code!

---

## Your Weekly Workflow

### Monday: Sprint Planning

```
Team Meeting:
- Amit (Furnace): I'll add tapping efficiency chart
- Rajesh (Geology): I'll fix working days bug
- Priya (QC): I'll add test results table

You: Great! Amit, create GitHub issue #15 for your task
     Rajesh, create issue #16
     Priya, create issue #17
```

### Throughout Week: Monitor Progress

**GitHub → Insights → Network**
- See visual graph of all branches
- See who's working on what

**GitHub → Pull Requests**
- Review and merge completed work
- Provide feedback on issues

### Friday: Release Planning

```
All PRs merged to develop
✅ Amit's feature
✅ Rajesh's bug fix
✅ Priya's enhancement

Now merge develop → main (production)
```

---

## Your Management Tools

### 1. **GitHub Issues** - Track Tasks

```
Issue #15: Add tapping efficiency chart
Assigned to: @amit-kumar
Labels: furnace, enhancement
Due: 2026-01-15

Issue #16: Fix geology working days calculation
Assigned to: @rajesh-sharma
Labels: geology, bug
Due: 2026-01-12
```

### 2. **GitHub Projects** - Kanban Board

```
TODO          IN PROGRESS       REVIEW          DONE
Issue #17     Issue #15         PR #12          Issue #10
Issue #18     Issue #16         PR #13          Issue #11
```

### 3. **Pull Requests** - Code Review

```
Open (3)
✓ PR #12: Amit - Power chart (Approved, ready to merge)
⏳ PR #13: Rajesh - Working days fix (Waiting for review)
❌ PR #14: Priya - QC dashboard (Changes requested)

Closed (125)
All merged PRs in history
```

---

## Your Control Points

### You Have Full Control Over:

1. **Who can merge to main/develop** (via branch protection)
2. **Who reviews what** (via CODEOWNERS)
3. **What gets released** (you merge develop → main)
4. **Shared files** (app_main.py, config.py require your approval)

### You DON'T Need to Control:

1. Department-specific code (developers handle their own)
2. Daily commits (developers push to their branches freely)
3. Individual file edits (Git tracks everything automatically)

---

# 👨‍💻 DEVELOPER PERSPECTIVE (e.g., Amit - Furnace Developer)

## Day 1: Getting Started

### Step 1: You Receive Assignment

**Email from you:**
```
Hi Amit,

You're assigned to Furnace department.
Repository: https://github.com/balasore/dashboard
Your branch: dept/furnace

Setup instructions in README.md
Questions? Ask me or create GitHub issue.
```

### Step 2: Amit Clones Repository

```bash
# Amit opens terminal
git clone https://github.com/balasore/dashboard.git
cd dashboard

# Amit checks out HIS branch
git checkout dept/furnace

# Amit sees only his branch
# He can't accidentally break other code
```

### Step 3: Amit Sets Up Environment

```bash
# Amit follows README.md
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Amit creates .env file with database credentials
cp .env.example .env
# Edits .env

# Amit tests if it works
python app_main.py furnace 2025-12-24
# ✓ Dashboard generates successfully!
```

---

## Day 2-5: Amit Works on Feature

### Step 1: Amit Gets Task

**GitHub Issue #15 (created by you):**
```
Title: Add tapping efficiency chart to furnace dashboard
Description: Show efficiency trend over time
Assigned: @amit-kumar
Due: Jan 15, 2026
```

### Step 2: Amit Starts Work

```bash
# Amit makes sure he's on his branch
git checkout dept/furnace

# Amit pulls latest changes (in case you merged something)
git pull origin develop

# Amit starts coding
```

### Step 3: Amit Edits HIS Files

Amit opens his code editor:

```
departments/furnace/
├── formatter.py       ← Amit adds calculation here
├── template_engine.py ← Amit adds HTML injection here
└── claude_analyzer.py ← Amit updates AI prompt here

templates/furnace_dashboard.html ← Amit adds chart here
```

**Amit can edit these freely - they're HIS files!**

### Step 4: Amit Tests Locally

```bash
# Amit generates dashboard to test
python app_main.py furnace 2025-12-24

# Opens generated_dashboards/furnace_2025-12-24.html
# Sees his new chart - looks good!
```

### Step 5: Amit Commits Changes

```bash
# Amit sees what he changed
git status
# Output:
#   modified: departments/furnace/formatter.py
#   modified: templates/furnace_dashboard.html

# Amit stages changes
git add departments/furnace/
git add templates/furnace_dashboard.html

# Amit commits with good message
git commit -m "feat(furnace): add tapping efficiency trend chart

Added Chart.js line chart showing tapping efficiency over time.
Includes comparison against target efficiency of 85%.

Fixes #15"

# Amit pushes to HIS branch
git push origin dept/furnace
```

**Important:** Amit pushed to `dept/furnace`, NOT to `main` or `develop`!

---

## Day 6: Amit Submits Work for Review

### Step 1: Amit Creates Pull Request

1. Amit goes to GitHub
2. Clicks "Pull requests" → "New pull request"
3. Selects:
   - Base: `develop`
   - Compare: `dept/furnace`
4. Fills in PR template:
   ```
   ## Description
   Added tapping efficiency trend chart showing hourly efficiency.

   ## Type of Change
   - [x] ✨ New feature

   ## Department
   - Department: furnace
   - Branch: dept/furnace

   ## Changes Made
   - [x] departments/furnace/formatter.py - Added efficiency calculation
   - [x] templates/furnace_dashboard.html - Added chart section

   ## Testing
   ```bash
   python app_main.py furnace 2025-12-24
   # Chart displays correctly with test data
   ```

   ## Impact on Other Departments
   - [x] ✅ No impact - changes isolated to furnace

   Fixes #15
   ```
5. Clicks "Create pull request"

### Step 2: What Happens Automatically

```
GitHub automatically:
1. Checks CODEOWNERS file
2. Sees furnace files changed
3. Assigns YOU as reviewer
4. Sends you email notification
```

### Step 3: Amit Waits for Review

**Amit's View:**
```
Pull Request #12
Status: ⏳ Waiting for review from @tech-lead
```

**Your View (you get email):**
```
New Pull Request:
feat(furnace): add tapping efficiency trend chart
From: @amit-kumar

[Review] [Approve] [Request Changes]
```

---

## Day 7: You Review and Amit Responds

### Scenario A: You Approve ✅

**You click "Approve" → "Merge pull request"**

**Amit's view:**
```
Pull Request #12
Status: ✅ Merged!
```

**What happened:**
```
Amit's code moved from dept/furnace → develop

Now Amit's feature is available to everyone!
```

### Scenario B: You Request Changes ❌

**You comment:**
```
Please add error handling for when no data is available.
Also, fix the typo in line 45.
```

**Amit sees your comments, fixes issues:**
```bash
# Amit edits code to fix issues
git add departments/furnace/
git commit -m "fix(furnace): add error handling per review feedback"
git push origin dept/furnace
```

**The SAME PR updates automatically!** No need to create new PR.

**You see update, review again, approve.**

---

## Day 8+: Amit Continues Working

### Amit Stays Updated

```bash
# Every morning, Amit pulls latest from develop
git checkout dept/furnace
git pull origin develop

# This gets him:
# - Rajesh's geology fixes
# - Priya's QC updates
# - Any changes you made to shared files
```

### Amit Starts Next Feature

```bash
# Amit just continues on his branch
# No need to create new branch for each feature
git checkout dept/furnace

# Edit code for next feature
# Commit, push, create PR
# Repeat cycle
```

---

# 🔄 COMPLETE WORKFLOW EXAMPLE

## Week 1: Real Scenario

### Monday Morning

**You (Tech Lead):**
```
Sprint Planning Meeting:
- Amit: Add power efficiency chart
- Rajesh: Fix working days bug
- Priya: Add test results table

Creates 3 GitHub issues
Assigns to respective developers
```

**Developers:**
```
Amit: Sees GitHub Issue #20 assigned to him
Rajesh: Sees GitHub Issue #21 assigned to him
Priya: Sees GitHub Issue #22 assigned to her

All start working on their branches:
- Amit: dept/furnace
- Rajesh: dept/geology
- Priya: dept/qc
```

### Tuesday

**Developers Working:**
```
Amit:
  - Edits departments/furnace/formatter.py
  - Tests dashboard
  - Commits to dept/furnace

Rajesh:
  - Edits departments/geology/formatter.py
  - Tests dashboard
  - Commits to dept/geology

Priya:
  - Edits departments/qc/formatter.py
  - Tests dashboard
  - Commits to dept/qc

✅ No conflicts! Each works on different files.
```

### Wednesday - Rajesh Finishes First

**Rajesh:**
```bash
git push origin dept/geology
# Creates PR #30: dept/geology → develop
```

**You:**
```
Receive notification
Review PR #30
See only geology files changed
Approve and merge
```

**What happens:**
```
Rajesh's bug fix now in develop branch

Amit and Priya get it next time they pull:
git pull origin develop
```

### Thursday - Amit Needs to Modify app_main.py

**Amit:**
```
Issue: I need new API endpoint for hourly data
This requires editing app_main.py (shared file!)
```

**Amit's process:**
```bash
# Amit creates FEATURE BRANCH (not from dept/furnace)
git checkout develop
git pull origin develop
git checkout -b feat/furnace-hourly-api

# Amit edits app_main.py (minimal changes)
# Also edits departments/furnace/formatter.py

git add app_main.py departments/furnace/
git commit -m "feat(furnace): add hourly breakdown API endpoint

Added /api/v1/furnace/hourly endpoint for detailed hourly analysis.

Changes to app_main.py are minimal and isolated to furnace-only route.

Need this for Issue #20"

git push origin feat/furnace-hourly-api

# Creates PR: feat/furnace-hourly-api → develop
```

**You:**
```
Receive notification
PR #31 from @amit modifies app_main.py

Review carefully:
- Will this break geology? No - only furnace route
- Will this break qc? No - isolated
- Code quality good? Yes
- Really necessary? Yes - needed for his feature

Approve and merge
```

### Friday - Priya Finishes

**Priya:**
```bash
git push origin dept/qc
# Creates PR #32: dept/qc → develop
```

**You:**
```
Review and merge
All 3 features now in develop!
```

### Friday Evening - Release to Production

**You:**
```bash
# All features tested in develop
# Ready to release

git checkout main
git merge develop
git tag -a v1.3.0 -m "Release: Power chart, Working days fix, QC table"
git push origin main --tags

# Deploy to production server
```

**Result:**
```
Week 1 Complete:
✅ 3 features delivered
✅ 0 conflicts
✅ All code reviewed
✅ Production deployed
```

---

# ⚠️ CONFLICT SCENARIO - How You Handle It

## Scenario: Two Developers Edit Same Line

### What Happens

**Monday:**
```
Amit edits app_main.py line 500
Rajesh edits app_main.py line 500

Both push to their branches
```

**Amit submits PR first:**
```
PR #40: Amit's changes
You review and merge
app_main.py now has Amit's version on develop
```

**Rajesh submits PR second:**
```
PR #41: Rajesh's changes
GitHub says: ⚠️ MERGE CONFLICT
Cannot auto-merge
```

### Your Options

**Option 1: You Handle It (Recommended)**

```bash
# You pull both branches
git checkout develop
git pull origin develop  # Has Amit's changes

git checkout -b resolve-conflict-41
git merge origin/dept/geology  # Rajesh's branch

# Conflict appears
# File: app_main.py
<<<<<<< HEAD
# Amit's code
=======
# Rajesh's code
>>>>>>> origin/dept/geology

# You edit file, keep both or choose one
# Save file

git add app_main.py
git commit -m "fix: resolve conflict between furnace and geology"
git push origin resolve-conflict-41

# Merge to develop
```

**Option 2: Ask Rajesh to Fix**

```
You comment on PR #41:
"Hey Rajesh, there's a conflict with Amit's recent merge.
Can you pull latest develop and resolve?"

Rajesh:
git checkout dept/geology
git pull origin develop  # Gets Amit's changes
# Conflict appears
# Rajesh fixes it
git add app_main.py
git commit -m "fix: merge with develop"
git push origin dept/geology

# PR #41 updates, conflict resolved
```

**Which option?**
- Small conflict + you understand both changes = Option 1 (faster)
- Complex conflict + developer knows better = Option 2

---

# 📊 YOUR DASHBOARD VIEW

## GitHub Dashboard Shows You:

### 1. **Activity Feed**
```
Today:
🔄 @amit pushed to dept/furnace (3 commits)
📝 @rajesh created Issue #25
✅ @priya PR #40 merged
👀 @kiran commented on PR #41
```

### 2. **Pull Requests** (Your Review Queue)
```
Open (4):
⏳ PR #42: Amit - Power chart (needs review)
⏳ PR #43: Rajesh - Geology update (needs review)
✅ PR #44: Priya - QC table (approved, ready to merge)
❌ PR #45: Suresh - SCM fix (changes requested)

Your turn to review: 2
Ready to merge: 1
Waiting for developer: 1
```

### 3. **Issues** (Task Tracking)
```
Open (7):
🔴 High Priority (2)
  #50: Production bug in furnace (assigned: Amit)
  #51: Database connection issue (assigned: You)

🟡 Medium Priority (3)
  #52: Add export feature (assigned: Priya)
  #53: Improve chart loading (assigned: Amit)
  #54: Update documentation (assigned: Rajesh)

🟢 Low Priority (2)
  #55: UI improvement (unassigned)
  #56: Add dark mode (unassigned)
```

### 4. **Insights → Network** (Visual Branch Graph)
```
       main ──────────────────────────
           \
            develop ──┬──┬──┬──────
                      │  │  │
         dept/furnace ┘  │  │
         dept/geology ───┘  │
         dept/qc ───────────┘
```

---

# 🎯 KEY BENEFITS OF THIS WORKFLOW

## For You (Manager):

1. ✅ **Full Control** - You approve everything that goes to production
2. ✅ **Clear Accountability** - Know who did what
3. ✅ **No Surprises** - Review before code goes live
4. ✅ **Easy Rollback** - Can undo bad merges
5. ✅ **Track Progress** - See who's working on what
6. ✅ **Prevent Conflicts** - Isolated branches reduce collisions

## For Developers:

1. ✅ **Freedom** - Work on their branch without fear
2. ✅ **Safety** - Can't break production
3. ✅ **Clarity** - Know exactly what they own
4. ✅ **Learning** - See others' code in PRs
5. ✅ **Collaboration** - Can comment on each other's PRs
6. ✅ **No Waiting** - Don't wait for others to finish

---

# 📱 YOUR DAILY ROUTINE

## Morning (15 minutes)

1. Open GitHub
2. Check notifications
3. Review pending PRs (approve or request changes)
4. Check if any production issues

## During Day (as needed)

1. Developers create PRs
2. You get notifications
3. Review when convenient
4. Merge good ones, request changes for others

## Friday (30 minutes)

1. Check all PRs merged this week
2. Merge develop → main
3. Tag release
4. Deploy to production
5. Plan next week

---

# 🆘 TROUBLESHOOTING

## "I Don't Know How to Review Code"

**Simple checklist:**

```
When reviewing PR:
1. Does it only change their department files? ✅ Probably safe
2. Does it change shared files? ⚠️ Read carefully
3. Can you understand the code?
   - Yes: Approve
   - No: Ask developer to add comments
4. Did they test it? Check PR description
5. When in doubt: Ask developer to demo it
```

## "Too Many PRs to Review"

**Options:**

1. **Delegate**: Make senior developers review juniors
2. **Automate**: Set up automated tests
3. **Batch**: Review all PRs Friday instead of daily
4. **Trust**: After developer proves themselves, approve faster

## "Developer Pushed Bad Code"

**No problem:**

```bash
# Undo the merge
git checkout develop
git revert <commit-hash>
git push origin develop

# Or rollback develop to before merge
git reset --hard <commit-before-merge>
git push --force origin develop

# Developer fixes, submits new PR
```

---

# ✅ SUMMARY

## Your Job:
1. Review PRs (15 min/day)
2. Merge good code
3. Request changes for bad code
4. Protect shared files
5. Release to production (weekly)

## Developer's Job:
1. Work on their branch
2. Test their code
3. Create PRs
4. Respond to your review
5. Keep learning

## Git's Job:
1. Track all changes
2. Prevent conflicts
3. Allow parallel work
4. Enable rollback
5. Show history

---

**Questions?**

Read this document again, or ask specific questions like:
- "What happens when..."
- "How do I handle..."
- "What if developer..."

I'll update this guide with answers!
