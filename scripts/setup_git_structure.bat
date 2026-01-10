@echo off
REM ============================================================================
REM Git Repository Setup Script (Windows)
REM Sets up the modular branch structure for Balasore Alloys Dashboard
REM ============================================================================

echo ==========================================
echo Balasore Alloys Dashboard - Git Setup
echo ==========================================
echo.

REM Check if git is initialized
if not exist .git (
    echo Initializing Git repository...
    git init
    echo ✓ Git initialized
) else (
    echo ✓ Git repository already exists
)

REM Create main branch
git checkout -b main 2>nul || git checkout main
echo ✓ On main branch

REM Create .gitkeep files for empty directories
echo Creating .gitkeep files...
if not exist generated_dashboards mkdir generated_dashboards
if not exist test_output mkdir test_output
if not exist test_outputs mkdir test_outputs
if not exist here-is-output mkdir here-is-output
if not exist logs mkdir logs

type nul > generated_dashboards\.gitkeep
type nul > test_output\.gitkeep
type nul > test_outputs\.gitkeep
type nul > here-is-output\.gitkeep
type nul > logs\.gitkeep
echo ✓ .gitkeep files created

REM Check if initial commit exists
git rev-parse HEAD >nul 2>&1
if errorlevel 1 (
    echo Creating initial commit...
    git add .
    git commit -m "chore: initial project structure" -m "- Add department folders (furnace, geology, qc, scm, automobile, crm, env)" -m "- Add core infrastructure (app_main.py, config, templates)" -m "- Add documentation (CONTRIBUTING.md, DEPARTMENT_DEVELOPMENT_GUIDE.md)" -m "- Add .gitignore for Python, logs, generated files" -m "- Add shared utilities (MCP server, auth, database)" -m "" -m "This is the base structure before department-specific development begins."
    echo ✓ Initial commit created
) else (
    echo ✓ Repository already has commits
)

REM Create develop branch
echo Creating develop branch...
git checkout -b develop 2>nul || git checkout develop
echo ✓ Develop branch ready

REM Create department branches
echo.
echo Creating department branches...

git show-ref --verify --quiet refs/heads/dept/furnace 2>nul || (
    git checkout -b dept/furnace develop
    echo   ✓ Created dept/furnace
)
git show-ref --verify --quiet refs/heads/dept/furnace >nul 2>&1 && echo   ✓ dept/furnace already exists

git show-ref --verify --quiet refs/heads/dept/geology 2>nul || (
    git checkout -b dept/geology develop
    echo   ✓ Created dept/geology
)
git show-ref --verify --quiet refs/heads/dept/geology >nul 2>&1 && echo   ✓ dept/geology already exists

git show-ref --verify --quiet refs/heads/dept/qc 2>nul || (
    git checkout -b dept/qc develop
    echo   ✓ Created dept/qc
)
git show-ref --verify --quiet refs/heads/dept/qc >nul 2>&1 && echo   ✓ dept/qc already exists

git show-ref --verify --quiet refs/heads/dept/scm 2>nul || (
    git checkout -b dept/scm develop
    echo   ✓ Created dept/scm
)
git show-ref --verify --quiet refs/heads/dept/scm >nul 2>&1 && echo   ✓ dept/scm already exists

git show-ref --verify --quiet refs/heads/dept/automobile 2>nul || (
    git checkout -b dept/automobile develop
    echo   ✓ Created dept/automobile
)
git show-ref --verify --quiet refs/heads/dept/automobile >nul 2>&1 && echo   ✓ dept/automobile already exists

git show-ref --verify --quiet refs/heads/dept/crm 2>nul || (
    git checkout -b dept/crm develop
    echo   ✓ Created dept/crm
)
git show-ref --verify --quiet refs/heads/dept/crm >nul 2>&1 && echo   ✓ dept/crm already exists

git show-ref --verify --quiet refs/heads/dept/env 2>nul || (
    git checkout -b dept/env develop
    echo   ✓ Created dept/env
)
git show-ref --verify --quiet refs/heads/dept/env >nul 2>&1 && echo   ✓ dept/env already exists

REM Return to develop
git checkout develop

echo.
echo ==========================================
echo Git Setup Complete!
echo ==========================================
echo.
echo Branch Structure:
echo   main                  (production)
echo   develop               (integration)
echo   dept/furnace          (furnace team)
echo   dept/geology          (geology team)
echo   dept/qc               (qc team)
echo   dept/scm              (scm team)
echo   dept/automobile       (automobile team)
echo   dept/crm              (crm team)
echo   dept/env              (environment team)
echo.
echo Next Steps:
echo 1. Set up remote repository:
echo    git remote add origin [your-github-url]
echo.
echo 2. Push all branches:
echo    git push -u origin main
echo    git push -u origin develop
echo    git push -u origin dept/furnace
echo    git push -u origin dept/geology
echo    git push -u origin dept/qc
echo    git push -u origin dept/scm
echo    git push -u origin dept/automobile
echo    git push -u origin dept/crm
echo    git push -u origin dept/env
echo.
echo 3. Share branch assignments with team:
echo    - Furnace Lead → dept/furnace
echo    - Geology Lead → dept/geology
echo    - QC Lead → dept/qc
echo    - SCM Lead → dept/scm
echo    - Automobile Lead → dept/automobile
echo    - CRM Lead → dept/crm
echo    - Environment Lead → dept/env
echo.
pause
