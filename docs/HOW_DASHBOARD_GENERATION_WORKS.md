# How Dashboard Generation Works - Step by Step

## 🤔 Your Question: `python app_main.py geology 2025-12-24`

Let me explain **exactly** what happens when you run this command.

---

## 📍 Step-by-Step Execution Flow

### Step 1: You Run the Command

```bash
# You type this in terminal (Windows Command Prompt or PowerShell)
python app_main.py geology 2025-12-24
```

**What this means:**
- `python` - Run Python interpreter
- `app_main.py` - Execute this file
- `geology` - Department to generate
- `2025-12-24` - Date to generate for

### Step 2: Python Starts Executing app_main.py

**File Location:** `E:\MCP-with-API\app_main.py`

Let me show you the relevant code in `app_main.py`:

```python
# Around line 2320-2380 in app_main.py

if __name__ == '__main__':
    import sys

    # Check if command-line arguments provided
    if len(sys.argv) >= 3:
        dept_id = sys.argv[1]  # "geology"
        date = sys.argv[2]     # "2025-12-24"

        # Optional: date range
        if len(sys.argv) >= 4:
            end_date = sys.argv[3]
        else:
            end_date = None
```

**What happens:**
```
sys.argv = ["app_main.py", "geology", "2025-12-24"]
           [0]            [1]        [2]

dept_id = "geology"
date = "2025-12-24"
end_date = None (not provided)
```

### Step 3: app_main.py Calls Geology Department

```python
# Still in app_main.py

# Import geology modules
from departments.geology.formatter import GeologySurveyDataProcessor
from departments.geology.template_engine import GeologySurveyTemplateEngine

# Create instances
mcp = MCPServer()  # Database connection
processor = GeologySurveyDataProcessor(mcp)

# Process data for the date
if end_date is None:
    # Single date mode
    analysis_data = processor.process_single_date(date)
else:
    # Date range mode
    analysis_data = processor.process_date_range(date, end_date)
```

**What happens:**
1. Opens database connection via MCPServer
2. Creates geology data processor
3. Calls `process_single_date("2025-12-24")`

### Step 4: Geology Formatter Processes Data

**File:** `E:\MCP-with-API\departments\geology\formatter.py`

```python
# Inside GeologySurveyDataProcessor class

def process_single_date(self, date: str) -> Dict[str, Any]:
    """Process data for single date"""

    # 1. Query database for geology data
    excavation_today = self._query_excavation(date, date)
    samples_today = self._query_sample_analysis(date, date)

    # 2. Query month-to-date data
    month_start = f"{date[:7]}-01"  # "2025-12-01"
    excavation_mtd = self._query_excavation(month_start, date)
    samples_mtd = self._query_sample_analysis(month_start, date)

    # 3. Calculate KPIs
    today_kpis = self._build_today_kpis(excavation_today, samples_today)
    mtd_kpis = self._build_mtd_kpis(excavation_mtd, samples_mtd)

    # 4. Build charts data
    daily_trend = self._build_daily_trend(excavation_mtd, date)

    # 5. Return structured data
    return {
        "date": "2025-12-24",
        "formatted_date": "December 24, 2025",
        "today_kpis": {
            "excavation": {"value": 1250, "formatted": "1,250"},
            "trips": {"value": 98, "formatted": "98"},
            ...
        },
        "mtd_kpis": {
            "total_excavation": {"value": 10188, "formatted": "10,188"},
            "working_days": {"value": 8, "formatted": "8"},
            ...
        },
        "charts": {
            "daily_trend": [...],
            "location_breakdown": [...],
            ...
        }
    }
```

**What happens:**
1. Queries MySQL database for excavation records
2. Queries sample analysis records
3. Calculates all metrics (totals, averages, working days)
4. Returns a big dictionary with all the data

### Step 5: Template Engine Generates HTML

**File:** `E:\MCP-with-API\departments\geology\template_engine.py`

```python
# Back in app_main.py, after getting analysis_data

# Create template engine
engine = GeologySurveyTemplateEngine()

# Generate HTML
html = engine.generate_dashboard(
    analysis_data=analysis_data,
    claude_insights_html="",
    date=date
)
```

**What template_engine.py does:**

```python
# Inside template_engine.py

def generate_dashboard(self, analysis_data, claude_insights_html, date):
    # 1. READ the template file
    template_path = "templates/geology_dashboard.html"
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 2. INJECT date and title
    html = html.replace("{{DATE}}", "December 24, 2025")

    # 3. INJECT KPI values
    excavation = analysis_data['today_kpis']['excavation']['formatted']
    html = html.replace("{{EXCAVATION}}", excavation)

    # 4. INJECT JavaScript analysisData
    import json
    data_json = json.dumps(analysis_data, indent=2)

    # Find this in template:
    # const analysisData = {placeholder};

    # Replace with actual data:
    # const analysisData = {"date": "2025-12-24", "today_kpis": {...}};

    html = re.sub(
        r'const analysisData = \{[^}]+\};',
        f'const analysisData = {data_json};',
        html
    )

    # 5. Return complete HTML
    return html
```

**What happens:**
1. Reads `templates/geology_dashboard.html` (the base template)
2. Finds placeholders like `{{DATE}}`, `{{EXCAVATION}}`
3. Replaces them with actual values from `analysis_data`
4. Injects JavaScript `analysisData` object for charts
5. Returns complete HTML string

### Step 6: Save to File

**Back in app_main.py:**

```python
# Save the generated HTML
output_dir = "generated_dashboards"
filename = f"geology_{date.replace('-', '_')}.html"
filepath = os.path.join(output_dir, filename)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✓ Dashboard generated: {filepath}")
```

**What happens:**
1. Creates filename: `geology_2025_12_24.html`
2. Saves to: `E:\MCP-with-API\generated_dashboards\geology_2025_12_24.html`
3. Prints success message

### Step 7: You Open the File

```bash
# The file is saved, now you can open it
start generated_dashboards/geology_2025_12_24.html
```

**Or manually:**
1. Go to folder: `E:\MCP-with-API\generated_dashboards\`
2. Find file: `geology_2025_12_24.html`
3. Double-click to open in browser

**Browser displays:**
- All KPIs populated with real data
- Charts render using Chart.js
- AI insights section (if enabled)
- Interactive, responsive dashboard

---

## 🔍 Visual Flow Diagram

```
YOU TYPE COMMAND
    ↓
┌─────────────────────────────────────┐
│ python app_main.py geology 2025-12-24│
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ app_main.py starts                  │
│ - Parses arguments                  │
│ - dept_id = "geology"               │
│ - date = "2025-12-24"               │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Import geology modules              │
│ - formatter.py                      │
│ - template_engine.py                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ GeologySurveyDataProcessor          │
│ .process_single_date("2025-12-24")  │
│                                      │
│ QUERIES DATABASE:                   │
│ - mines_day_wise_excavation         │
│ - mines_geology_face_sample_analysis│
│                                      │
│ CALCULATES:                         │
│ - Today KPIs (excavation, trips)    │
│ - MTD KPIs (total, working days)    │
│ - Charts data (trends, breakdowns)  │
│                                      │
│ RETURNS:                            │
│ {                                    │
│   "date": "2025-12-24",             │
│   "today_kpis": {...},              │
│   "mtd_kpis": {...},                │
│   "charts": {...}                   │
│ }                                    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ GeologySurveyTemplateEngine         │
│ .generate_dashboard(analysis_data)  │
│                                      │
│ READS:                              │
│ templates/geology_dashboard.html    │
│                                      │
│ REPLACES:                           │
│ {{DATE}} → "December 24, 2025"      │
│ {{EXCAVATION}} → "10,188"           │
│ const analysisData = {...}          │
│                                      │
│ RETURNS:                            │
│ Complete HTML string                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Save to file                        │
│                                      │
│ FILE PATH:                          │
│ E:\MCP-with-API\generated_dashboards│
│   \geology_2025_12_24.html          │
│                                      │
│ PRINT:                              │
│ ✓ Dashboard generated               │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ YOU OPEN FILE IN BROWSER            │
│                                      │
│ Browser loads HTML                  │
│ Chart.js renders charts             │
│ Dashboard is interactive            │
└─────────────────────────────────────┘
```

---

## 📂 Where Are the Files?

### Template File (Base HTML)

**Location:** `E:\MCP-with-API\templates\geology_dashboard.html`

**What it contains:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Geology Dashboard - {{DATE}}</title>
    <style>
        /* All CSS styles here */
    </style>
</head>
<body>
    <div class="header">
        <h1>Geology & Survey Dashboard</h1>
        <h2>Date: {{DATE}}</h2>
    </div>

    <div class="kpi-card">
        <div class="kpi-value">{{EXCAVATION}}</div>
        <div class="kpi-label">Total Excavation</div>
    </div>

    <!-- More HTML structure -->

    <script>
        // This gets replaced with actual data
        const analysisData = {placeholder};

        // Chart rendering code
        new Chart(ctx, {
            data: analysisData.charts.daily_trend
        });
    </script>
</body>
</html>
```

**Who can see this:**
- Developer: YES - can edit this file
- Browser: NO - this is the template, not the final output

### Generated File (Final Output)

**Location:** `E:\MCP-with-API\generated_dashboards\geology_2025_12_24.html`

**What it contains:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Geology Dashboard - December 24, 2025</title>
    <style>
        /* All CSS styles here */
    </style>
</head>
<body>
    <div class="header">
        <h1>Geology & Survey Dashboard</h1>
        <h2>Date: December 24, 2025</h2>
    </div>

    <div class="kpi-card">
        <div class="kpi-value">10,188</div>
        <div class="kpi-label">Total Excavation</div>
    </div>

    <!-- More HTML structure -->

    <script>
        // Actual data injected
        const analysisData = {
            "date": "2025-12-24",
            "today_kpis": {
                "excavation": {"value": 10188, "formatted": "10,188"},
                ...
            },
            "charts": {
                "daily_trend": [
                    {"date": "2025-12-10", "qty": 1200},
                    {"date": "2025-12-11", "qty": 1350},
                    ...
                ]
            }
        };

        // Chart rendering code (same)
        new Chart(ctx, {
            data: analysisData.charts.daily_trend
        });
    </script>
</body>
</html>
```

**Who can see this:**
- Developer: YES - but this is auto-generated, don't edit
- Browser: YES - this is what you open
- User: YES - this is the final dashboard

---

## 📅 Date Range Mode

### How to Run Date Range

```bash
# Single date (what you asked about)
python app_main.py geology 2025-12-24

# Date range (3 arguments)
python app_main.py geology 2025-12-10 2025-12-24
```

### What Changes in Date Range Mode

**Command:**
```bash
python app_main.py geology 2025-12-10 2025-12-24
```

**In app_main.py:**
```python
if len(sys.argv) >= 4:
    # Date range mode!
    start_date = sys.argv[2]  # "2025-12-10"
    end_date = sys.argv[3]    # "2025-12-24"

    # Call different method
    analysis_data = processor.process_date_range(start_date, end_date)
```

**In formatter.py:**
```python
def process_date_range(self, start_date: str, end_date: str):
    """Process data for date range"""

    # Query ALL data in range
    excavation_range = self._query_excavation(start_date, end_date)
    samples_range = self._query_sample_analysis(start_date, end_date)

    # Calculate PERIOD KPIs (aggregated)
    period_kpis = {
        "excavation": sum(all excavation in range),
        "working_days": count(unique dates with data),
        "avg_daily": total / working_days,
        ...
    }

    return {
        "start_date": "2025-12-10",
        "end_date": "2025-12-24",
        "date_range_formatted": "December 10-24, 2025",
        "period_kpis": period_kpis,  # Aggregated metrics
        "charts": {
            "daily_trend": [...15 days of data...],
            ...
        }
    }
```

**Output File:**
```
generated_dashboards/geology_2025_12_10_to_2025_12_24.html
```

**Dashboard Shows:**
- Date range at top: "December 10-24, 2025"
- Aggregated totals for entire period
- Working days: 8 (actual days with data)
- Daily trend chart spanning all 15 calendar days

---

## 🔄 How Updates Work

### Scenario: Developer Wants to Add New Metric

**Step 1: Developer Edits formatter.py**

```python
# In departments/geology/formatter.py

def _build_today_kpis(self, excavation_data, samples_data):
    # Existing metrics
    total_qty = sum(...)
    total_trips = sum(...)

    # NEW METRIC - Developer adds this
    avg_load_per_truck = total_qty / total_trips if total_trips > 0 else 0

    return {
        "excavation": {...},
        "trips": {...},
        # NEW - Add to output
        "avg_load_per_truck": {
            "value": avg_load_per_truck,
            "formatted": f"{avg_load_per_truck:.1f}",
            "unit": "MT/truck"
        }
    }
```

**Step 2: Developer Edits Template**

```html
<!-- In templates/geology_dashboard.html -->

<!-- Existing KPI card -->
<div class="kpi-card">
    <div class="kpi-value">{{EXCAVATION}}</div>
    <div class="kpi-label">Total Excavation</div>
</div>

<!-- NEW KPI card -->
<div class="kpi-card">
    <div class="kpi-value">{{AVG_LOAD}}</div><!--avg-load-per-truck-->
    <div class="kpi-label">Avg Load per Truck</div>
</div>
```

**Step 3: Developer Edits template_engine.py**

```python
# In departments/geology/template_engine.py

def _inject_kpis(self, html, data):
    # Existing injections
    excavation = data['today_kpis']['excavation']['formatted']
    html = html.replace("{{EXCAVATION}}", excavation)

    # NEW - Inject new metric
    avg_load = data['today_kpis']['avg_load_per_truck']['formatted']
    pattern = r'(<div class="kpi-value">)[^<]+(</div><!--avg-load-per-truck-->)'
    html = re.sub(pattern, f"\\g<1>{avg_load}\\g<2>", html)

    return html
```

**Step 4: Developer Tests**

```bash
python app_main.py geology 2025-12-24
start generated_dashboards/geology_2025_12_24.html
```

**Step 5: Developer Sees New Metric**

Dashboard now shows:
```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ 10,188      │  │    821      │  │    12.4     │  ← NEW!
│ Excavation  │  │   Trips     │  │ Avg Load/Truck│
└─────────────┘  └─────────────┘  └─────────────┘
```

**Step 6: Developer Commits**

```bash
git add departments/geology/
git add templates/geology_dashboard.html
git commit -m "feat(geology): add avg load per truck metric"
git push origin dept/geology
```

---

## 👀 Where Developer Can See Template

### Option 1: File Explorer

1. Navigate to: `E:\MCP-with-API\templates\`
2. Find: `geology_dashboard.html`
3. Right-click → Open with → Notepad / VS Code / Any editor

### Option 2: VS Code (Recommended)

```bash
# Open entire project in VS Code
cd E:\MCP-with-API
code .

# In VS Code sidebar, navigate to:
templates/geology_dashboard.html
```

### Option 3: Command Line

```bash
# View template content
cd E:\MCP-with-API
cat templates/geology_dashboard.html

# Or edit in nano/vim
nano templates/geology_dashboard.html
```

### What Developer Sees in Template

```html
<!-- templates/geology_dashboard.html -->

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Geology & Survey Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        /* All CSS styles */
        .kpi-card { ... }
        .chart-container { ... }
    </style>
</head>

<body>
    <!-- Header Section -->
    <div class="header">
        <h1>Geology & Survey Dashboard</h1>
        <h2>{{DATE}}</h2>  ← Placeholder, gets replaced
    </div>

    <!-- KPI Cards -->
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-value">{{EXCAVATION}}</div>  ← Placeholder
            <div class="kpi-label">Period Excavation (MT)</div>
        </div>

        <div class="kpi-card">
            <div class="kpi-value">{{TRIPS}}</div>  ← Placeholder
            <div class="kpi-label">Total Trips</div>
        </div>
    </div>

    <!-- Charts Section -->
    <div class="charts-container">
        <canvas id="dailyTrendChart"></canvas>
    </div>

    <!-- JavaScript Section -->
    <script>
        // This entire object gets replaced with real data
        const analysisData = {
            date: "placeholder",
            today_kpis: {},
            charts: {}
        };

        // Chart rendering code
        const ctx = document.getElementById('dailyTrendChart');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: analysisData.charts.daily_trend.map(d => d.date),
                datasets: [{
                    label: 'Daily Excavation',
                    data: analysisData.charts.daily_trend.map(d => d.qty)
                }]
            }
        });
    </script>
</body>
</html>
```

---

## 🎯 Complete File Structure

```
E:\MCP-with-API\
│
├── app_main.py                    ← YOU RUN THIS
│   └── Orchestrates everything
│
├── departments\geology\
│   ├── formatter.py               ← PROCESSES DATA
│   │   └── Queries DB, calculates metrics
│   │
│   ├── template_engine.py         ← GENERATES HTML
│   │   └── Injects data into template
│   │
│   └── claude_analyzer.py         ← AI INSIGHTS (optional)
│       └── Generates AI analysis
│
├── templates\
│   └── geology_dashboard.html     ← BASE TEMPLATE
│       └── HTML structure with placeholders
│
└── generated_dashboards\
    ├── geology_2025_12_24.html    ← FINAL OUTPUT (single date)
    └── geology_2025_12_10_to_2025_12_24.html  ← FINAL OUTPUT (range)
```

---

## 🔧 Developer Workflow Summary

### 1. Developer Makes Changes

```bash
# Edit department files
departments/geology/formatter.py         ← Add calculation
departments/geology/template_engine.py   ← Add injection logic
templates/geology_dashboard.html         ← Add HTML element
```

### 2. Developer Tests Locally

```bash
# Generate dashboard
python app_main.py geology 2025-12-24

# Check output
start generated_dashboards/geology_2025_12_24.html
```

### 3. Developer Commits to Git

```bash
git add departments/geology/ templates/geology_dashboard.html
git commit -m "feat(geology): add new truck load metric"
git push origin dept/geology
```

### 4. Developer Creates PR

- Go to GitHub
- Create Pull Request: dept/geology → develop
- You review and approve

### 5. Changes Go Live

- You merge PR
- Code is now in develop branch
- Other developers can pull updates
- Next production release includes it

---

## ❓ FAQ

### Q: Where is the database?
**A:** MySQL server at `80.9.2.78`, database `balcorpdb`

### Q: How does it connect to database?
**A:** Via `core/mcp_server.py` using credentials from `.env` file

### Q: Where are generated files saved?
**A:** `E:\MCP-with-API\generated_dashboards\`

### Q: Can I delete generated files?
**A:** YES - they're temporary, regenerate anytime

### Q: What if template has errors?
**A:** Dashboard won't display correctly. Check browser console (F12)

### Q: How to see errors during generation?
**A:** Errors print to console. Check `logs/app.log` for details

### Q: Can I preview without saving?
**A:** No, currently saves to file first, then you open it

---

## 🚀 Quick Reference

### Generate Single Date Dashboard
```bash
python app_main.py geology 2025-12-24
```

### Generate Date Range Dashboard
```bash
python app_main.py geology 2025-12-10 2025-12-24
```

### Open Generated Dashboard
```bash
# Windows
start generated_dashboards\geology_2025_12_24.html

# Or just double-click the file
```

### Check for Errors
```bash
# Check logs
type logs\app.log

# Or open in editor
code logs\app.log
```

---

**Now you understand the complete flow!** 🎉

From command → database → calculations → template → HTML file → browser display
