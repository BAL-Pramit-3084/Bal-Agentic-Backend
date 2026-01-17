# Geology & Survey Department Dashboard

## Overview

This module generates comprehensive dashboards for the **Geology & Survey Department** at Balasore Alloys Limited. It tracks mining excavation data, ore quality analysis, grade distribution, and production planning metrics from the chromite mines.

## File Structure

```
departments/geology/
├── __init__.py           # Module exports (GeologyDataProcessor, GeologyTemplateEngine, GeologyClaudeInsightsGenerator)
├── formatter.py          # Data processing and KPI calculations
├── template_engine.py    # HTML dashboard generation
├── claude_analyzer.py    # AI-powered insights generation
└── README.md             # This file
```

## How to Run

The dashboard is generated through the main Flask application:

```bash
# Start the Flask server
python app_main.py

# API Endpoints:
# Single date dashboard:
GET /api/v1/dashboard/geology?date=2026-01-15

# Date range dashboard:
GET /api/v1/dashboard/geology?start_date=2026-01-01&end_date=2026-01-15
```

### Template Location
`templates/geology_survey_dashboard.html`

---

## Database Tables & Schema

### 1. `mines_day_wise_excavation` (Primary Operational Data)

Daily excavation records by location, shift, and material type.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `Prod_date` | date | PRI | NO | Production date |
| `Shift` | varchar(1) | PRI | NO | Shift identifier (A/B/C) |
| `Loc_Id` | int | PRI | NO | Location ID (FK to mines_location_master) |
| `Variant` | varchar(5) | PRI | NO | Material variant ID (1=ORE, 3=OB, 4=SILT) |
| `Agency` | varchar(20) | PRI | NO | Contractor/agency name |
| `No_Of_trips` | int | | YES | Number of tipper trips |
| `Units` | varchar(10) | | YES | Measurement unit |
| `Qty` | varchar(50) | | YES | Quantity excavated (stored as string with unit) |
| `Entry_Id` | varchar(10) | | YES | User who entered the record |
| `Entry_Date` | date | | YES | Date of entry |

**Primary Key**: `(Prod_date, Shift, Loc_Id, Variant, Agency)`

### 2. `mines_geology_face_sample_analysis` (Quality Analysis)

Chemical analysis results for ore samples from mining faces.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `Prod_date` | date | PRI | NO | Sample date |
| `Shift` | varchar(1) | PRI | NO | Shift identifier |
| `LAB_ID` | int | | YES | Laboratory ID |
| `Loc_Id` | int | PRI | NO | Location ID |
| `SAMPLE_ID` | varchar(50) | | YES | Unique sample identifier |
| `Cr2O3` | float | | YES | Chromium oxide percentage (%) |
| `FeO` | float | | YES | Iron oxide percentage (%) |
| `Ratio` | float | | YES | Cr:Fe ratio |
| `Analysis_Name` | varchar(45) | | YES | Type of analysis |
| `Entry_Id` | varchar(10) | | YES | User who entered the record |
| `Entry_Date` | date | | YES | Date of entry |

**Primary Key**: `(Prod_date, Shift, Loc_Id)`

### 3. `mines_daily_excavation_plan` (Daily Planning)

Daily excavation targets and planned quantities by grade.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `Prod_date` | date | PRI | NO | Planned date |
| `Shift` | varchar(1) | PRI | NO | Shift identifier |
| `Loc_Id` | int | PRI | NO | Location ID |
| `Face_Desc` | varchar(30) | | YES | Face description |
| `OB_QTY_Cum` | varchar(50) | | YES | Cumulative overburden quantity |
| `ORE_QTY` | float | | YES | Total ore planned (MT) |
| `HG_QTY` | float | | YES | High-grade ore planned (MT) |
| `MG_QTY` | float | | YES | Medium-grade ore planned (MT) |
| `LG_QTY` | float | | YES | Low-grade ore planned (MT) |
| `Entry_Id` | varchar(10) | | YES | User who entered the record |
| `Entry_Date` | date | | YES | Date of entry |

**Primary Key**: `(Prod_date, Shift, Loc_Id)`

### 4. `mines_monthly_excavation_plan` (Monthly Planning)

Monthly excavation targets by location and grade.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `Prod_Month` | varchar(10) | PRI | NO | Month in YYYY-MM format |
| `Shift` | varchar(4) | | YES | Shift (if applicable) |
| `Loc_Id` | int | PRI | NO | Location ID |
| `Mode` | varchar(20) | PRI | NO | Mining mode |
| `Z_Range` | varchar(20) | | YES | Elevation range |
| `Grade` | varchar(10) | PRI | NO | Grade classification (HG/MG/LG) |
| `Tonnage` | float | | YES | Planned tonnage (MT) |
| `Cr2O3_Percentage` | varchar(20) | | YES | Expected Cr2O3 percentage |
| `CrFe_Ratio` | varchar(20) | | YES | Expected Cr:Fe ratio |
| `Remarks` | varchar(255) | | YES | Additional notes |
| `Entry_Id` | int | | YES | User who entered the record |
| `Entry_Date` | date | | YES | Date of entry |

**Primary Key**: `(Prod_Month, Loc_Id, Mode, Grade)`

### 5. Master Tables

#### `mines_location_master`
| Column | Type | Description |
|--------|------|-------------|
| `Loc_Id` | int (PK) | Unique location identifier |
| `Loc_Desc` | varchar | Location name/description |
| `Status` | varchar | Active/Inactive status |

#### `mines_variant_master`
| Column | Type | Description |
|--------|------|-------------|
| `Variant_Id` | int (PK) | Variant code |
| `Variant_Desc` | varchar | Description (ORE, OVERBURDEN, SILT) |
| `Status` | varchar | Active/Inactive status |

**Variant Mappings:**
- `1` = ORE (Chromite ore)
- `3` = OVERBURDEN (OB - waste material)
- `4` = SILT (fine material)

#### `mines_agency_master`
| Column | Type | Description |
|--------|------|-------------|
| `Agency_Id` | int (PK) | Agency code |
| `Agency_Desc` | varchar | Contractor name |
| `Status` | varchar | Active/Inactive status |

---

## Key Files Explained

### 1. `formatter.py` - GeologyDataProcessor

**Purpose**: Main data processor that queries the database and builds the analysis data structure.

**Class: `GeologyDataProcessor`**

```python
class GeologyDataProcessor:
    def __init__(self, mcp_server):
        self.mcp = mcp_server  # MCP server for database queries
```

**Key Methods:**

| Method | Description | Returns |
|--------|-------------|---------|
| `process_date(date)` | Process all geology data for a single date | `Dict[str, Any]` with all KPIs |
| `process_date_range(start, end)` | Process data for a date range | `Dict[str, Any]` with aggregated KPIs |
| `_query_excavation_data(date)` | Query mines_day_wise_excavation | `List[Dict]` of excavation records |
| `_query_sample_analysis(date)` | Query mines_geology_face_sample_analysis | `List[Dict]` of quality data |
| `_query_daily_plan(date)` | Query mines_daily_excavation_plan | `List[Dict]` of planned targets |
| `_query_monthly_plan(month)` | Query mines_monthly_excavation_plan | `List[Dict]` of monthly targets |
| `_build_excavation_section()` | Build excavation KPIs with grade breakdown | `Dict` with production metrics |
| `_build_quality_section()` | Build quality analysis KPIs | `Dict` with Cr2O3/FeO averages |
| `_build_plan_vs_actual()` | Calculate plan adherence | `Dict` with variance analysis |

**Key Constants:**
```python
# Variant ID mappings
VARIANT_ORE = "1"          # Chromite ore
VARIANT_OVERBURDEN = "3"   # Waste material (OB)
VARIANT_SILT = "4"         # Silt/fine material

# Grade classification thresholds (based on Cr2O3 percentage)
GRADE_HG_THRESHOLD = 52.0  # High Grade >= 52%
GRADE_MG_THRESHOLD = 40.0  # Medium Grade >= 40% and < 52%
# Low Grade: < 40%
```

**Data Parsing:**
The database stores excavation quantities as strings with units (e.g., "312 Mt", "564 CuM"). The `safe_float()` function handles this:

```python
def safe_float(value: Any, default: float = 0.0) -> float:
    """Parse strings like '312 Mt' or '564 CuM' to float"""
    if isinstance(value, str):
        value = value.strip()
        match = re.match(r'^[\d,.]+', value)
        if match:
            num_str = match.group().replace(',', '')
            return float(num_str)
    return default
```

**Data Flow in `process_date()`:**
```python
def process_date(self, date: str) -> Dict[str, Any]:
    # 1. Parse date and get month for monthly plan
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    month_str = date_obj.strftime('%Y-%m')

    # 2. Query all data sources
    excavation_data = self._query_excavation_data(date)
    sample_data = self._query_sample_analysis(date)
    daily_plan = self._query_daily_plan(date)
    monthly_plan = self._query_monthly_plan(month_str)

    # 3. Build analysis structure
    return {
        "date": date,
        "excavation": self._build_excavation_section(excavation_data),
        "quality": self._build_quality_section(sample_data),
        "plan_vs_actual": self._build_plan_vs_actual(daily_plan, excavation_data),
        "monthly_progress": self._build_monthly_progress(monthly_plan, ...)
    }
```

### 2. `template_engine.py` - GeologySurveyTemplateEngine

**Purpose**: Injects processed data into the HTML template by replacing placeholders.

**Class: `GeologySurveyTemplateEngine`**

**Key Methods:**
| Method | Description |
|--------|-------------|
| `generate_dashboard()` | Main entry point - coordinates all replacements |
| `_replace_today_kpis()` | Updates KPI cards (excavation, trips, quality) |
| `_replace_mtd_section()` | Updates MTD summary (ORE, OB, SILT breakdown) |
| `_replace_shift_table()` | Updates shift plan vs actual table |
| `_replace_location_table()` | Updates location-wise breakdown |
| `_replace_sample_analysis_table()` | Updates quality analysis table |
| `_replace_plan_vs_actual()` | Updates plan achievement tables |
| `_replace_all_charts()` | Injects Chart.js data as JSON |
| `_replace_insights_section()` | Injects AI-generated insights |

**Template Placeholders:**
| Placeholder | Source | Description |
|-------------|--------|-------------|
| `{{DATE}}` | Input parameter | Dashboard date |
| `{{TOTAL_ORE}}` | excavation.total_ore | Total ore excavated (MT) |
| `{{TOTAL_OB}}` | excavation.total_ob | Total overburden (MT) |
| `{{HG_QTY}}` | excavation.hg_qty | High-grade quantity |
| `{{MG_QTY}}` | excavation.mg_qty | Medium-grade quantity |
| `{{LG_QTY}}` | excavation.lg_qty | Low-grade quantity |
| `{{AVG_CR2O3}}` | quality.avg_cr2o3 | Average Cr2O3 percentage |
| `{{AVG_RATIO}}` | quality.avg_ratio | Average Cr:Fe ratio |
| `{{PLAN_ADHERENCE}}` | plan_vs_actual.adherence_pct | Plan achievement % |

### 3. `claude_analyzer.py` - ClaudeInsightsGenerator

**Purpose**: Generates AI-powered insights using OpenAI GPT-4.

**Class: `ClaudeInsightsGenerator`**

**Key Methods:**
| Method | Description |
|--------|-------------|
| `generate_insights(analysis_data, date)` | Generates 8 insight cards |
| `generate_ai_summary(analysis_data, date)` | Generates executive summary |
| `_build_context()` | Builds context string from analysis data |

**Insight Categories Generated:**
1. Plan Achievement Status
2. Shift Performance
3. Quality Analysis
4. Location Patterns
5. Zero Progress Alert
6. Load Efficiency
7. Agency Analysis
8. Sampling Coverage

**LLM Configuration:**
```python
self.use_openai = True
self.model = "gpt-4o"
self.temperature = 0.3
self.max_tokens = 4096
```

---

## KPIs and Calculations

### Daily Excavation KPIs

| KPI | Description | Table | Columns | Calculation |
|-----|-------------|-------|---------|-------------|
| Total Ore (MT) | Total chromite ore excavated | `mines_day_wise_excavation` | `Qty`, `Variant` | `SUM(Qty) WHERE Variant = '1'` |
| Total OB (MT) | Total overburden removed | `mines_day_wise_excavation` | `Qty`, `Variant` | `SUM(Qty) WHERE Variant = '3'` |
| Total SILT (MT) | Total silt removed | `mines_day_wise_excavation` | `Qty`, `Variant` | `SUM(Qty) WHERE Variant = '4'` |
| Stripping Ratio | OB to Ore ratio | Calculated | - | `Total_OB / Total_Ore` |
| Total Trips | Number of tipper trips | `mines_day_wise_excavation` | `No_Of_trips` | `SUM(No_Of_trips)` |
| Avg Load/Trip | Average load per trip | Calculated | - | `Total_Qty / Total_Trips` |
| Active Locations | Locations with production | `mines_day_wise_excavation` | `Loc_Id` | `COUNT(DISTINCT Loc_Id)` |

### Grade Distribution KPIs

| KPI | Description | Table | Columns | Calculation |
|-----|-------------|-------|---------|-------------|
| HG Quantity | High Grade ore (Cr2O3 >= 52%) | `mines_daily_excavation_plan` | `HG_QTY` | Direct or classified from samples |
| MG Quantity | Medium Grade ore (40-52%) | `mines_daily_excavation_plan` | `MG_QTY` | Direct or classified |
| LG Quantity | Low Grade ore (< 40%) | `mines_daily_excavation_plan` | `LG_QTY` | Direct or classified |
| HG Percentage | % of total ore that is HG | Calculated | - | `(HG_QTY / Total_Ore) * 100` |

### Quality Analysis KPIs

| KPI | Description | Table | Columns | Calculation |
|-----|-------------|-------|---------|-------------|
| Avg Cr2O3 (%) | Average chromium oxide | `mines_geology_face_sample_analysis` | `Cr2O3` | `AVG(Cr2O3)` |
| Min Cr2O3 (%) | Minimum Cr2O3 | `mines_geology_face_sample_analysis` | `Cr2O3` | `MIN(Cr2O3)` |
| Max Cr2O3 (%) | Maximum Cr2O3 | `mines_geology_face_sample_analysis` | `Cr2O3` | `MAX(Cr2O3)` |
| Avg FeO (%) | Average iron oxide | `mines_geology_face_sample_analysis` | `FeO` | `AVG(FeO)` |
| Avg Cr:Fe Ratio | Chromium to iron ratio | `mines_geology_face_sample_analysis` | `Ratio` | `AVG(Ratio)` |
| Samples Analyzed | Number of quality samples | `mines_geology_face_sample_analysis` | - | `COUNT(*)` |
| Best Location | Location with highest Cr2O3 | `mines_geology_face_sample_analysis` | `Loc_Id`, `Cr2O3` | `MAX(Cr2O3) GROUP BY Loc_Id` |

### Plan vs Actual KPIs

| KPI | Description | Tables | Calculation |
|-----|-------------|--------|-------------|
| Plan Achievement (%) | Actual vs planned | `mines_daily_excavation_plan` + `mines_day_wise_excavation` | `(Actual_Ore / Planned_Ore) * 100` |
| Ore Variance (MT) | Difference from plan | Both tables | `Actual_Ore - Planned_Ore` |
| OB Variance (MT) | OB removal vs plan | Both tables | `Actual_OB - Planned_OB` |
| Monthly Progress (%) | MTD vs monthly target | `mines_monthly_excavation_plan` | `(MTD_Actual / Monthly_Plan) * 100` |

### Gap Analysis KPIs

| Metric | Calculation |
|--------|-------------|
| `avg_daily_production` | `Total Actual / Working Days` |
| `required_daily_production` | `Remaining Target / Days Remaining` |
| `increase_needed_pct` | `((Required - Avg) / Avg) * 100` |
| `expected_month_end` | `Avg Daily * Days in Month` |
| `expected_achievement_pct` | `(Expected / Planned) * 100` |

---

## Data Flow

```
1. API Request (/api/v1/dashboard/geology?date=YYYY-MM-DD)
        ↓
2. GeologyDataProcessor.process_date(date)
   - Queries mines_day_wise_excavation (filter: Prod_date = date)
   - Queries mines_geology_face_sample_analysis (filter: Prod_date = date)
   - Queries mines_daily_excavation_plan (filter: Prod_date = date)
   - Queries mines_monthly_excavation_plan (filter: Prod_Month = YYYY-MM)
   - Joins with master tables for descriptions
   - Calculates all KPIs
        ↓
3. ClaudeInsightsGenerator.generate_insights(analysis_data, date)
   - Builds context from production and quality data
   - Calls OpenAI GPT-4 API
   - Returns AI-generated insights HTML (8 cards)
        ↓
4. ClaudeInsightsGenerator.generate_ai_summary(analysis_data, date)
   - Generates executive summary paragraphs
        ↓
5. GeologySurveyTemplateEngine.generate_dashboard(...)
   - Loads geology_survey_dashboard.html
   - Replaces all {{PLACEHOLDER}} values
   - Injects chart data into JavaScript variables
   - Injects AI insights into designated section
        ↓
6. Returns complete HTML dashboard
```

---

## Sample SQL Queries Used

### Daily Excavation Data
```sql
SELECT
    e.Prod_date, e.Shift, e.Loc_Id, e.Variant, e.Agency,
    e.No_Of_trips, e.Qty,
    l.Loc_Desc as location_name,
    v.Variant_Desc as variant_name
FROM mines_day_wise_excavation e
LEFT JOIN mines_location_master l ON e.Loc_Id = l.Loc_Id
LEFT JOIN mines_variant_master v ON e.Variant = v.Variant_Id
WHERE e.Prod_date = '2026-01-15'
ORDER BY e.Shift, e.Loc_Id
```

### Quality Analysis
```sql
SELECT
    Prod_date, Shift, Loc_Id, SAMPLE_ID,
    Cr2O3, FeO, Ratio, Analysis_Name
FROM mines_geology_face_sample_analysis
WHERE Prod_date = '2026-01-15'
ORDER BY Loc_Id, Shift
```

### Daily Plan
```sql
SELECT
    Prod_date, Shift, Loc_Id, Face_Desc,
    OB_QTY_Cum, ORE_QTY, HG_QTY, MG_QTY, LG_QTY
FROM mines_daily_excavation_plan
WHERE Prod_date = '2026-01-15'
```

### Monthly Plan
```sql
SELECT
    Prod_Month, Loc_Id, Mode, Grade, Tonnage,
    Cr2O3_Percentage, CrFe_Ratio
FROM mines_monthly_excavation_plan
WHERE Prod_Month = '2026-01'
ORDER BY Loc_Id, Grade
```

---

## Charts Generated

| Chart | Type | Data Source |
|-------|------|-------------|
| Shift Production | Doughnut | `shift_breakdown.chart` |
| Location Distribution | Doughnut | `location_breakdown.chart` |
| Daily Production Trend | Line | `daily_trend` |
| Quality Parameter Trends | Dual-axis Line | `quality_trend` (Cr2O3% + Ratio) |
| MTD Location Performance | Bar | `mtd_location_performance.chart` |
| Agency Performance | Pie | `agency_performance.chart` |

---

## Configuration

Environment variables required in `.env`:
```bash
# Database
DB_HOST=80.9.2.78
DB_PORT=3306
DB_NAME=balcorpdb
DB_USER=your_user
DB_PASSWORD=your_password

# AI (OpenAI - Default)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No data displayed | Check if data exists for the requested date in `mines_day_wise_excavation` |
| Grade breakdown missing | Verify `Variant` column has correct values (1, 3, 4) |
| Quality data empty | Check `mines_geology_face_sample_analysis` has samples for the date |
| Location names showing IDs | Verify `mines_location_master` has entries for all `Loc_Id` values |
| Plan vs actual incorrect | Ensure both plan and actual tables have data for the same date |
| Cr2O3 showing 0 | Check for NULL values in the `Cr2O3` column |
| Excavation totals wrong | Ensure `safe_float()` is parsing string values like "312 Mt" correctly |
| AI insights not generating | Verify `OPENAI_API_KEY` is set correctly |

---

## Contact

**Department Lead**: @geology-lead
**Branch**: `dept/geology`

For questions or issues, contact the BAL-Agentic-Backend Team.
