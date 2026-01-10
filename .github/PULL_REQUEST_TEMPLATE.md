## Description

<!-- Provide a brief description of what this PR does -->

## Type of Change

<!-- Mark the relevant option with an [x] -->

- [ ] 🐛 Bug fix (fixes an issue in my department)
- [ ] ✨ New feature (adds functionality to my department)
- [ ] 🔧 Configuration change (department_config.json or app_main.py)
- [ ] 📝 Documentation update
- [ ] 🎨 UI/Template change
- [ ] 🔥 Hotfix (critical production issue)
- [ ] ♻️ Refactoring (no functional changes)

## Department

<!-- Which department does this affect? -->

- Department: **[furnace/geology/qc/scm/automobile/crm/env]**
- Branch: `dept/[your-department]`

## Changes Made

<!-- Describe the changes in detail -->

### Files Modified

- [ ] `departments/[dept]/formatter.py` - [What changed?]
- [ ] `departments/[dept]/template_engine.py` - [What changed?]
- [ ] `departments/[dept]/claude_analyzer.py` - [What changed?]
- [ ] `templates/[dept]_dashboard.html` - [What changed?]
- [ ] `app_main.py` - [What changed? Why was this necessary?]
- [ ] `dashboards/department_config.json` - [What changed?]
- [ ] Other: _____

### What problem does this solve?

<!-- Link to issue if applicable: Fixes #123 -->

### How was it tested?

<!-- Describe testing performed -->

```bash
# Example test commands
python app_main.py furnace 2025-12-24
```

## Impact on Other Departments

<!-- IMPORTANT: Does this change affect other departments? -->

- [ ] ✅ No impact - changes are isolated to my department
- [ ] ⚠️ Possible impact - changes to shared files (app_main.py, config, templates)
- [ ] 🚨 High impact - requires coordination with other teams

### If there is impact, explain:

<!-- Which departments are affected and how? -->

## Checklist

<!-- Ensure all items are checked before submitting PR -->

- [ ] I have tested my changes locally
- [ ] Dashboard generates without errors
- [ ] No breaking changes to other departments
- [ ] Code follows project style guidelines
- [ ] I have updated documentation (if needed)
- [ ] Commit messages follow convention: `type(scope): message`
- [ ] I have pulled latest changes from `develop` before creating this PR
- [ ] I have added comments to complex code sections

## Screenshots (if applicable)

<!-- Add screenshots of dashboard changes -->

### Before
<!-- Screenshot or description of current state -->

### After
<!-- Screenshot or description of new state -->

## Additional Context

<!-- Any other information reviewers should know -->

## Reviewer Notes

<!-- Special instructions for reviewers -->

---

**For Reviewers:**
- [ ] Code quality is acceptable
- [ ] Tests pass
- [ ] No merge conflicts
- [ ] Shared file changes are justified
- [ ] Documentation is updated
- [ ] No security concerns

<!--
Department Leads: @furnace-lead @geology-lead @qc-lead @scm-lead @automobile-lead @crm-lead @env-lead
Tech Lead: @tech-lead
-->
