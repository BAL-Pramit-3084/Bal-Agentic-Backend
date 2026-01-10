# Quick Setup Guide - Git Repository for Your Team

## 🎯 Your Goal
Set up Git repository so 7 developers can work on different departments without conflicts.

---

## ⚡ FAST SETUP (15 Minutes)

### Step 1: Initialize Git Locally (2 minutes)

```bash
# Open Command Prompt in your project folder
cd E:\MCP-with-API

# Run the setup script
scripts\setup_git_structure.bat
```

**What this does:**
- ✅ Creates Git repository
- ✅ Creates `main` branch
- ✅ Creates `develop` branch
- ✅ Creates 7 department branches (dept/furnace, dept/geology, etc.)
- ✅ Makes initial commit

**Verify it worked:**
```bash
git branch -a
```

**You should see:**
```
* develop
  main
  dept/furnace
  dept/geology
  dept/qc
  dept/scm
  dept/automobile
  dept/crm
  dept/env
```

---

### Step 2: Create GitHub Repository (3 minutes)

**Go to GitHub:**
1. Open browser: https://github.com/new
2. Fill in:
   - **Repository name:** `balasore-alloys-dashboard`
   - **Description:** `Manufacturing dashboard system`
   - **Visibility:** Private
   - **DO NOT check:** "Initialize with README"
3. Click **"Create repository"**

**You'll see a page with instructions - IGNORE THEM, use these instead:**

---

### Step 3: Push to GitHub (2 minutes)

```bash
# Still in E:\MCP-with-API

# Add GitHub as remote (REPLACE with your actual URL!)
git remote add origin https://github.com/YOUR-USERNAME/balasore-alloys-dashboard.git

# Push main branch
git push -u origin main

# Push develop branch
git push -u origin develop

# Push all department branches
git push -u origin dept/furnace
git push -u origin dept/geology
git push -u origin dept/qc
git push -u origin dept/scm
git push -u origin dept/automobile
git push -u origin dept/crm
git push -u origin dept/env
```

**Verify on GitHub:**
- Refresh GitHub page
- Click "branches" dropdown
- Should see all 9 branches

---

### Step 4: Protect Main and Develop Branches (3 minutes)

**On GitHub:**

1. Go to **Settings** (top right)
2. Click **Branches** (left sidebar)
3. Click **Add rule**
4. Branch name pattern: `main`
5. Check these boxes:
   - ✅ Require a pull request before merging
   - ✅ Require approvals (set to 1)
6. Click **Create**
7. Repeat for `develop` branch

**Why?** This prevents anyone from directly pushing to main/develop. They must create Pull Requests.

---

### Step 5: Add Team Members (5 minutes)

**On GitHub:**

1. Go to **Settings** → **Collaborators and teams**
2. Click **Add people**
3. Enter each developer's GitHub username
4. Set role to **Write**
5. Click **Add**

**Each developer will receive email invitation**

---

## 📧 What to Send Each Developer

### Email Template:

```
Subject: Balasore Dashboard - Your Department Assignment

Hi [Name],

You've been assigned to the [DEPARTMENT] department.

🔗 Repository: https://github.com/YOUR-ORG/balasore-alloys-dashboard
🌿 Your Branch: dept/[department]

📋 SETUP STEPS:

1. Accept GitHub invitation (check your email)

2. Install Git (if not already):
   https://git-scm.com/download/win

3. Clone repository:
   git clone https://github.com/YOUR-ORG/balasore-alloys-dashboard.git
   cd balasore-alloys-dashboard

4. Checkout your branch:
   git checkout dept/[department]

5. Setup Python environment:
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt

6. Create .env file:
   copy .env.example .env
   (I'll send you database credentials separately)

7. Test it works:
   python app_main.py
   Open browser: http://localhost:5100

📖 Read these docs:
- README.md - Project overview
- docs/WORKFLOW_EXPLAINED.md - How workflow works
- docs/HOW_IT_ACTUALLY_WORKS.md - How system works
- departments/[department]/README.md - Your department guide

🆘 Questions? Reply to this email or create GitHub issue.

- Your Tech Lead
```

---

## 🎓 Optional: Update CODEOWNERS (5 minutes)

**Edit file:** `.github/CODEOWNERS`

**Replace placeholders with real GitHub usernames:**

```bash
# Before:
* @tech-lead
/departments/furnace/ @furnace-lead

# After (example):
* @your-github-username
/departments/furnace/ @amit-kumar-github
/departments/geology/ @rajesh-sharma-github
/departments/qc/ @priya-singh-github
```

**Commit the change:**
```bash
git add .github/CODEOWNERS
git commit -m "docs: update CODEOWNERS with team members"
git push origin main
```

---

## 🎯 What Happens Next

### Week 1: Developers Get Familiar

Each developer:
1. Clones repository
2. Checks out their branch (dept/furnace, etc.)
3. Reads documentation
4. Makes a small test change
5. Creates first Pull Request

### Week 2: Real Development Starts

Developers:
1. Work on their branches
2. Submit Pull Requests
3. You review and approve
4. Code merges to develop

### Week 3+: Continuous Development

- Developers push updates daily
- You review PRs as they come
- Merge to develop regularly
- Release to production weekly/monthly

---

## 🛠️ Your Daily Management Routine

### Morning (5 minutes)

1. Open GitHub repository
2. Check **Pull Requests** tab
3. Review any new PRs:
   - Read description
   - Check files changed
   - Approve or request changes

### During Day (as needed)

- Respond to developer questions
- Test merged features
- Check if CI/CD passed (if configured)

### Friday (30 minutes)

1. Review all PRs merged this week
2. Merge develop → main
3. Tag release: `git tag v1.2.0`
4. Deploy to production

---

## 📊 Your GitHub Dashboard

### What You'll See:

**Pull Requests Tab:**
```
Open (3):
⏳ PR #42: Amit - Power efficiency chart (needs review)
✅ PR #43: Rajesh - Working days fix (approved)
❌ PR #44: Priya - QC table (changes requested)
```

**Issues Tab:**
```
Open (5):
🔴 #10: Production bug (assigned: Amit)
🟡 #11: Add export feature (assigned: Priya)
🟢 #12: Improve docs (unassigned)
```

**Insights → Network:**
```
Visual graph showing all branches and merges
```

---

## 🆘 Troubleshooting

### Problem: "Permission denied (publickey)"

**Solution:**
```bash
# Use HTTPS instead of SSH
git remote set-url origin https://github.com/YOUR-ORG/balasore-alloys-dashboard.git
```

### Problem: "fatal: not a git repository"

**Solution:**
```bash
# You're in wrong folder, navigate to project
cd E:\MCP-with-API
```

### Problem: Developer can't push

**Solution:**
- Check they accepted GitHub invitation
- Check they're collaborators (Settings → Collaborators)
- Check they're pushing to their branch (dept/furnace), not main

### Problem: Merge conflict

**Solution:**
- Read `docs/WORKFLOW_EXPLAINED.md` - "CONFLICT SCENARIO" section
- Usually: Pull latest develop, resolve conflict, push again

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Git initialized locally (`git status` works)
- [ ] All branches created (`git branch -a` shows 9 branches)
- [ ] GitHub repository created
- [ ] All branches visible on GitHub
- [ ] Branch protection enabled for main/develop
- [ ] Team members added as collaborators
- [ ] Team members accepted invitations
- [ ] CODEOWNERS updated (optional but recommended)

---

## 🚀 Next Steps After Setup

1. **Schedule Kickoff Meeting**
   - Explain Git workflow
   - Show how to create PRs
   - Demo the system
   - Q&A session

2. **Assign First Tasks**
   - Create GitHub issues
   - Assign to respective developers
   - Set deadlines

3. **Monitor First PRs**
   - Help developers with first PR
   - Review quickly to build confidence
   - Provide constructive feedback

4. **Weekly Sync Meetings**
   - Review progress
   - Discuss blockers
   - Plan next week

---

## 📚 Key Documents for Reference

**For You (Manager):**
- `SETUP_CHECKLIST.md` - Detailed setup steps
- `docs/WORKFLOW_EXPLAINED.md` - How to manage team
- `docs/GIT_QUICK_REFERENCE.md` - Git commands

**For Developers:**
- `README.md` - Project overview
- `CONTRIBUTING.md` - Git workflow
- `docs/WORKFLOW_EXPLAINED.md` - How it all works
- `docs/HOW_IT_ACTUALLY_WORKS.md` - System architecture
- `departments/[dept]/README.md` - Department guide

---

## 🎯 Timeline

| Day | Task | Duration |
|-----|------|----------|
| Day 1 | Run setup script | 15 min |
| Day 1 | Create GitHub repo & push | 10 min |
| Day 1 | Add collaborators | 10 min |
| Day 1 | Send emails to team | 15 min |
| Day 2 | Developers clone & setup | 30 min each |
| Day 3 | Kickoff meeting | 1 hour |
| Week 1 | First test PRs | Ongoing |
| Week 2+ | Real development | Ongoing |

---

## 🎉 You're Ready!

After following these steps, you'll have:

✅ Git repository with proper branch structure
✅ GitHub repository with team access
✅ Protected branches preventing accidents
✅ Team members ready to start
✅ Documentation for everyone

**Just run `scripts\setup_git_structure.bat` and follow Steps 2-5!**

---

## 💡 Pro Tips

1. **Start Small:** Have each developer make a tiny change first (add comment) to learn workflow
2. **Be Patient:** First week is learning, second week is productive
3. **Quick Reviews:** Review PRs within 24 hours to keep momentum
4. **Celebrate Wins:** When first PR merges, acknowledge the developer
5. **Weekly Demos:** Show completed features to stakeholders

---

**Need help? All answers are in `docs/WORKFLOW_EXPLAINED.md`!** 🚀

**Questions? Create GitHub issue or ask me!** 💬
