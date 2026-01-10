# Architecture Diagram

## Git Branch Flow

```
┌─────────────────────────────────────────────────────────────┐
│                         MAIN BRANCH                          │
│                    (Production Code)                         │
│                  Protected - No Direct Push                  │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ (Merge via PR)
                              │
┌─────────────────────────────────────────────────────────────┐
│                       DEVELOP BRANCH                         │
│                   (Integration Branch)                       │
│            All department changes merge here first           │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ (Pull Requests)
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ dept/furnace  │    │ dept/geology  │    │   dept/qc     │
│               │    │               │    │               │
│ Furnace Team  │    │ Geology Team  │    │   QC Team     │
└───────────────┘    └───────────────┘    └───────────────┘

┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  dept/scm     │    │ dept/auto     │    │   dept/crm    │
│               │    │               │    │               │
│   SCM Team    │    │  Auto Team    │    │   CRM Team    │
└───────────────┘    └───────────────┘    └───────────────┘

┌───────────────┐
│  dept/env     │
│               │
│   Env Team    │
└───────────────┘
```

## File Ownership Model

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP-with-API Project                      │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ SHARED FILES │    │  DEPARTMENT  │    │   FRONTEND   │
│              │    │    FILES     │    │   ASSETS     │
│ Tech Lead    │    │ Dept Owners  │    │  UI/UX Lead  │
│   Approval   │    │ Full Access  │    │   Approval   │
└──────────────┘    └──────────────┘    └──────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│app_main.py   │    │departments/  │    │templates/    │
│config.py     │    │  furnace/    │    │  base.html   │
│core/         │    │  geology/    │    │static/       │
│requirements  │    │  qc/         │    │frontend/     │
└──────────────┘    │  scm/        │    └──────────────┘
                    │  automobile/ │
                    │  crm/        │
                    │  env/        │
                    └──────────────┘
```

## Department Isolation Architecture

```
FURNACE DEPARTMENT
┌────────────────────────────────────────────┐
│ departments/furnace/                       │
│ ├── formatter.py                           │
│ │   ├── FurnaceDataProcessor               │
│ │   ├── _query_production()                │
│ │   ├── _build_today_kpis()                │
│ │   └── _build_mtd_kpis()                  │
│ │                                           │
│ ├── template_engine.py                     │
│ │   ├── FurnaceTemplateEngine              │
│ │   ├── generate_dashboard()               │
│ │   └── _inject_kpis()                     │
│ │                                           │
│ └── claude_analyzer.py                     │
│     ├── FurnaceInsightsGenerator           │
│     └── generate_insights()                │
│                                             │
│ templates/furnace_dashboard.html           │
│ ├── KPI Cards                              │
│ ├── Charts (Production, Power, Recovery)   │
│ └── AI Insights Section                    │
└────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────┐
│         SHARED INFRASTRUCTURE              │
│                                             │
│ ┌─────────────────────────────────────┐   │
│ │  app_main.py                        │   │
│ │  @app.route('/api/v1/furnace')      │   │
│ │  Calls: FurnaceDataProcessor()      │   │
│ └─────────────────────────────────────┘   │
│                                             │
│ ┌─────────────────────────────────────┐   │
│ │  core/mcp_server.py                 │   │
│ │  Database connection & queries      │   │
│ └─────────────────────────────────────┘   │
│                                             │
│ ┌─────────────────────────────────────┐   │
│ │  config_modules/config.py           │   │
│ │  Global configuration               │   │
│ └─────────────────────────────────────┘   │
└────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────┐
│           DATABASE (MySQL)                 │
│                                             │
│ ┌─────────────────────────────────────┐   │
│ │ furnace_day_wise_production         │   │
│ │ furnace_tapping_log                 │   │
│ │ furnace_monthly_targets             │   │
│ └─────────────────────────────────────┘   │
└────────────────────────────────────────────┘
```

## Pull Request Flow

```
DEVELOPER WORKFLOW
┌────────────────────────────────────────────┐
│ 1. Developer on dept/furnace branch        │
│    - Makes changes to department files     │
│    - Tests locally                         │
│    - Commits to dept/furnace               │
└────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────┐
│ 2. Push to GitHub                          │
│    git push origin dept/furnace            │
└────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────┐
│ 3. Create Pull Request                     │
│    dept/furnace → develop                  │
│    - Fill in PR template                   │
│    - CODEOWNERS auto-assigns reviewer      │
└────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────┐
│ 4. Code Review                             │
│    - If dept files only: @furnace-lead     │
│    - If shared files: @tech-lead           │
│    - Reviews code, tests, documentation    │
└────────────────────────────────────────────┘
                    │
              ┌─────┴─────┐
              │           │
         Changes          Approved
         Requested
              │           │
              ▼           ▼
┌────────────────┐  ┌────────────────┐
│ 5a. Fix Issues │  │ 5b. Merge PR   │
│    - Update PR │  │    to develop  │
│    - Re-review │  └────────────────┘
└────────────────┘         │
              │            ▼
              │   ┌────────────────┐
              │   │ 6. Sync Other  │
              │   │    Branches    │
              │   │ All teams pull │
              │   │ from develop   │
              │   └────────────────┘
              │            │
              └────────────┘
```

## Data Flow Architecture

```
USER REQUEST
     │
     ▼
┌─────────────────────────────────────┐
│   app_main.py                       │
│   @app.route('/api/v1/furnace')     │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│   FurnaceDataProcessor              │
│   (departments/furnace/formatter.py)│
└─────────────────────────────────────┘
     │
     ├─► Query Database (MCP Server)
     │   - Production data
     │   - Power consumption
     │   - Tapping logs
     │
     ├─► Process Data
     │   - Calculate KPIs
     │   - Aggregate metrics
     │   - Build analysisData dict
     │
     └─► Return structured data
             │
             ▼
┌─────────────────────────────────────┐
│   FurnaceTemplateEngine             │
│   (template_engine.py)              │
└─────────────────────────────────────┘
     │
     ├─► Read Template
     │   (templates/furnace_dashboard.html)
     │
     ├─► Inject Data
     │   - Replace placeholders
     │   - Build JavaScript object
     │   - Add AI insights
     │
     └─► Return HTML
             │
             ▼
┌─────────────────────────────────────┐
│   Response to User                  │
│   - Complete HTML dashboard         │
│   - Charts render in browser        │
└─────────────────────────────────────┘
```

## Merge Conflict Resolution

```
SCENARIO: Two developers modify same file

Developer A                    Developer B
(dept/furnace)                (dept/geology)
     │                              │
     │ Modifies                     │ Modifies
     │ app_main.py                  │ app_main.py
     │                              │
     ├─► PR to develop              ├─► PR to develop
     │                              │
     ▼                              ▼
┌──────────────────────────────────────────┐
│        develop branch on GitHub          │
│                                           │
│  ├─ A's PR arrives first                 │
│  │  ✓ Merges cleanly                     │
│  │                                        │
│  ├─ B's PR arrives second                │
│  │  ⚠️  MERGE CONFLICT!                  │
│  │  - GitHub shows conflict              │
│  │  - Cannot auto-merge                  │
│  │                                        │
│  └─ Resolution Required                  │
└──────────────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────────┐
│     Developer B's Action                 │
│                                           │
│  1. git checkout dept/geology            │
│  2. git pull origin develop              │
│  3. ⚠️  CONFLICT in app_main.py          │
│  4. Contact @tech-lead                   │
│  5. Tech lead resolves conflict          │
│  6. git add app_main.py                  │
│  7. git commit                           │
│  8. git push origin dept/geology         │
│  9. PR now can merge                     │
└──────────────────────────────────────────┘
```

## File Change Impact Matrix

```
File Modified          │ Requires Review By │ Risk Level │ Merge Frequency
─────────────────────────────────────────────────────────────────────────
departments/furnace/   │ @furnace-lead      │ Low        │ Daily
departments/geology/   │ @geology-lead      │ Low        │ Daily
templates/*_dash.html  │ Dept lead          │ Medium     │ Weekly
app_main.py            │ @tech-lead + All   │ High       │ Weekly
config.py              │ @tech-lead         │ High       │ Monthly
core/                  │ @tech-lead         │ Critical   │ Rarely
requirements.txt       │ @tech-lead         │ High       │ Monthly
.env                   │ NEVER COMMIT       │ N/A        │ Never
```

## Deployment Pipeline (Future)

```
┌─────────────────────────────────────────────────────────────┐
│                     DEVELOPMENT                             │
│                                                              │
│  dept/furnace ─┐                                            │
│  dept/geology ─┼─► develop branch ─► Run Tests              │
│  dept/qc ──────┘                                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ (All tests pass)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      STAGING                                │
│                                                              │
│  develop ─► main ─► Deploy to Staging Server                │
│                 ─► Manual Testing                           │
│                 ─► Stakeholder Review                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ (Approved)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION                               │
│                                                              │
│  main ─► Tag Release (v1.2.0)                               │
│      ─► Deploy to Production                                │
│      ─► Monitor Logs                                        │
│      ─► Rollback if Issues                                  │
└─────────────────────────────────────────────────────────────┘
```

---

**Legend:**
- `┌─┐` Box/Container
- `│` Vertical connection
- `─` Horizontal connection
- `▼` Flow direction
- `⚠️` Warning/Attention needed
- `✓` Success/Approved
- `⚡` Action required

**Visual Tools:**
- For interactive diagrams: https://mermaid.live/
- For flowcharts: https://app.diagrams.net/
- For architecture: https://www.lucidchart.com/
