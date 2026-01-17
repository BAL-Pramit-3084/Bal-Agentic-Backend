# Furnace Department Dashboard

## Overview

This module generates comprehensive dashboards for the **Furnace Operations Department** at Balasore Alloys Limited. It tracks FeCr (Ferrochrome) production across 5 furnaces (I-V), power consumption, chromium recovery, tapping operations, and operational efficiency metrics.

## File Structure

```
departments/furnace/
├── __init__.py           # Module exports (FurnaceDataProcessor, FurnaceTemplateEngine, FurnaceClaudeInsightsGenerator)
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
GET /api/v1/dashboard/furnace?date=2026-01-15

# Date range dashboard:
GET /api/v1/dashboard/furnace?start_date=2026-01-01&end_date=2026-01-15
```

### Template Location
`templates/furnace_dashboard.html`

---

## Database Tables

### Table: `kpi_furnace_oper_summary`

**Description:** Entity-Attribute-Value (EAV) table storing 22 KPIs per furnace per day. Each row represents one KPI for one furnace on one date.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `KPI_DATE` | date | PRI | NO | Date of the KPI record |
| `FCE_NO` | varchar(5) | PRI | NO | Furnace identifier ("I", "II", "III", "IV", "V", "PLANT") |
| `KPI_NO` | int | PRI | NO | KPI number (1-22, see KPI mapping below) |
| `KPI_DESC` | varchar(100) | - | YES | Human-readable KPI description |
| `UOM` | varchar(10) | - | YES | Unit of measurement (MW, MWH, MT, %, Kg, etc.) |
| `TD_PLAN` | decimal(15,3) | - | YES | Today's planned value |
| `MTD_PLAN` | decimal(15,3) | - | YES | Month-to-date planned value |
| `TD_ACTUAL` | decimal(15,3) | - | YES | Today's actual value |
| `MTD_ACTUAL` | decimal(15,3) | - | YES | Month-to-date actual value |
| `TD_VAR` | decimal(10,2) | - | YES | Today's variance (actual vs plan) |
| `MTD_VAR` | decimal(10,2) | - | YES | Month-to-date variance |

**Primary Key:** (`KPI_DATE`, `FCE_NO`, `KPI_NO`)

**Statistics:** ~23,191 rows, 3.52 MB

---

### Table: `kpi_furnace_tapping_clock`

**Description:** Individual tapping event records with timing, temperature, and output data.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `KPI_DATE` | date | PRI | NO | Date of tapping |
| `FCE_NO` | varchar(3) | PRI | NO | Furnace identifier ("I", "II", "III", "IV", "V") |
| `TAP_NO` | int | PRI | NO | Tap sequence number for the day |
| `ST_TIME` | varchar(10) | - | NO | Start time of tapping (HH:MM format) |
| `ED_TIME` | varchar(10) | - | NO | End time of tapping |
| `DUR` | varchar(10) | - | NO | Duration of tapping |
| `TT_INTERVAL` | varchar(10) | - | YES | Tap-to-tap interval |
| `TTI_MWH` | decimal(10,3) | - | YES | Power consumption during tap interval (MWH) |
| `SLAG_TEMP` | int | - | YES | Slag temperature (°C) |
| `MOULD_TEMP` | int | - | YES | Mould temperature (°C) |
| `METAL_OUT` | int | - | YES | Metal output (Kg) |
| `SLAG_OUT` | int | - | YES | Slag output (Kg) |
| `REMARKS` | varchar(255) | - | YES | Additional notes |

**Primary Key:** (`KPI_DATE`, `FCE_NO`, `TAP_NO`)

**Statistics:** ~3,979 rows, 0.39 MB

---

## KPI Mapping (KPI_NO to Metric)

The `kpi_furnace_oper_summary` table uses an EAV structure where `KPI_NO` identifies each metric:

| KPI_NO | Metric Key | Description | UOM |
|--------|------------|-------------|-----|
| 1 | `avg_load_mw` | AVG. LOAD (On Time) | MW |
| 2 | `power_consumption_mwh` | POWER CONSUMPTION | MWH |
| 3 | `production_mt` | PRODUCTION | MT |
| 4 | `production_rate_pct` | PRODUCTION RATE | % |
| 5 | `sp_power_kwh` | SP.POWER (Specific Power) | KwH |
| 6 | `sp_carbon_kg` | SP.CARBON (Specific Carbon) | Kg |
| 7 | `no_of_batch` | No. of BATCH | Count |
| 8 | `carbon_per_batch` | CARBON / BATCH | Kg |
| 9 | `cr_recovery_pct` | Cr. RECOVERY | % |
| 10 | `sp_cr_ore_kg` | SP. CR. ORE (Specific Cr Ore) | Kg |
| 11 | `sp_paste_kg` | SP.PASTE (Specific Paste) | Kg |
| 12 | `sp_flux_kg` | SP. FLUX (Specific Flux) | Kg |
| 13 | `slag_mt` | SLAG | MT |
| 14 | `metal_slag_ratio` | METAL SLAG RATIO | Ratio |
| 15 | `pct_sio2` | % SiO2 | % |
| 16 | `pct_cr2o3` | % Cr2O3 | % |
| 17 | `pct_feo` | % FeO | % |
| 18 | `cr_plus_fe` | Cr+Fe | % |
| 19 | `pct_cr2o3_in_slag` | % Cr2O3 in SLAG | % |
| 20 | `downtime_hours` | DOWNTIME | Hours |
| 21 | `oee_pct` | OEE (Overall Equipment Effectiveness) | % |
| 22 | `ope_pct` | OPE (Overall Production Efficiency) | % |

---

## Key Files Explained

### 1. `formatter.py` - FurnaceDataProcessor

The main data processor that queries the database and builds the analysis data structure.

#### Constants

```python
# KPI number to metric name mapping
KPI_MAPPING = {
    1: "avg_load_mw",           # AVG. LOAD (On Time)
    2: "power_consumption_mwh",  # POWER CONSUMPTION - MWH
    3: "production_mt",          # PRODUCTION - MT
    # ... (22 KPIs total)
}

# List of furnaces (excluding PLANT which is aggregated)
FURNACE_LIST = ["I", "II", "III", "IV", "V"]
```

#### Key Methods

| Method | Description |
|--------|-------------|
| `process_date(date)` | Main entry point for single-date processing. Queries both tables and builds complete analysisData structure |
| `process_date_range(start_date, end_date)` | Processes date range by aggregating TD_ACTUAL values across days |
| `_query_kpi_summary(date)` | Queries `kpi_furnace_oper_summary` for a specific date |
| `_query_tapping_clock(date)` | Queries `kpi_furnace_tapping_clock` for a specific date |
| `_query_kpi_summary_range(start_date, end_date)` | Queries KPI summary for date range |
| `_query_tapping_clock_range(start_date, end_date)` | Queries tapping clock for date range |
| `_get_kpi_value(kpi_data, furnace, kpi_no)` | Extracts specific KPI value for a furnace |
| `_build_production_section(kpi_data)` | Builds production metrics (KPI 3, 4) |
| `_build_power_section(kpi_data)` | Builds power metrics (KPI 1, 2, 5) |
| `_build_recovery_section(kpi_data)` | Builds recovery metrics (KPI 6, 9, 10) |
| `_build_operational_section(kpi_data)` | Builds operational metrics (KPI 7, 20, 21, 22) |
| `_build_tapping_section(tapping_data)` | Builds tapping statistics from tapping clock table |
| `_build_slag_section(kpi_data)` | Builds slag metrics (KPI 13, 14, 16, 19) |
| `_aggregate_section_by_td(kpi_data, kpi_numbers)` | Sums TD_ACTUAL across days for absolute metrics |
| `_aggregate_averages(kpi_data, kpi_numbers)` | Averages TD_ACTUAL across days for rate/percentage metrics |

#### Helper Functions

```python
def safe_float(value, default=0.0) -> Optional[float]:
    """
    Convert value to float, handling NULL/None/Decimal gracefully.
    Returns None if value is NULL, otherwise returns float.
    """

def safe_int(value, default=0) -> Optional[int]:
    """
    Convert value to int, handling NULL gracefully.
    """
```

#### Data Flow in `process_date()`

```python
def process_date(self, date: str) -> Dict[str, Any]:
    # 1. Query both tables
    kpi_data = self._query_kpi_summary(date)      # Get all 22 KPIs for all furnaces
    tapping_data = self._query_tapping_clock(date) # Get tapping events

    # 2. Build analysisData structure matching template
    analysis_data = {
        "date": date,
        "production": self._build_production_section(kpi_data),
        "power": self._build_power_section(kpi_data),
        "recovery": self._build_recovery_section(kpi_data),
        "operational": self._build_operational_section(kpi_data),
        "tapping": self._build_tapping_section(tapping_data),
        "slag": self._build_slag_section(kpi_data)
    }

    # 3. Check if data exists
    analysis_data["has_data"] = self._check_has_data(analysis_data)
    return analysis_data
```

### 2. `template_engine.py` - FurnaceTemplateEngine

Injects processed data into the HTML template.

**Key Methods:**
- `generate_dashboard(analysis_data, claude_insights_html, date)` - Main entry point
- Uses regex replacement and JavaScript injection for chart data
- Handles both single-date and date-range formatting

### 3. `claude_analyzer.py` - FurnaceClaudeInsightsGenerator

Generates AI-powered furnace insights using OpenAI GPT-4 (or local LLM).

**Key Methods:**
- `generate_insights(analysis_data, date)` - Generates 5-6 actionable insights
- Builds context from production, power, recovery, operational data
- Returns formatted HTML for dashboard injection

---

## KPIs and Calculations

### Production Metrics

| KPI | Source | Calculation |
|-----|--------|-------------|
| Total Production | `KPI_NO=3`, `FCE_NO='PLANT'` | `TD_ACTUAL` from kpi_furnace_oper_summary |
| Furnace Production | `KPI_NO=3`, `FCE_NO='I'..'V'` | `TD_ACTUAL` per furnace |
| Production Rate (%) | `KPI_NO=4` | `TD_ACTUAL` (pre-calculated in source) |
| Production Variance | `KPI_NO=3` | `TD_VAR` (actual - plan) |

### Power Metrics

| KPI | Source | Calculation |
|-----|--------|-------------|
| Power Consumption (MWH) | `KPI_NO=2` | `TD_ACTUAL` |
| Specific Power (KWH/MT) | `KPI_NO=5` | `TD_ACTUAL` (pre-calculated) |
| Average Load (MW) | `KPI_NO=1` | `TD_ACTUAL` |

### Recovery Metrics

| KPI | Source | Calculation |
|-----|--------|-------------|
| Cr Recovery (%) | `KPI_NO=9` | `TD_ACTUAL`, Plant avg = `AVG(furnace values)` |
| Specific Cr Ore (Kg/MT) | `KPI_NO=10` | `TD_ACTUAL` |
| Specific Carbon (Kg/MT) | `KPI_NO=6` | `TD_ACTUAL` |

### Operational Metrics

| KPI | Source | Calculation |
|-----|--------|-------------|
| OEE (%) | `KPI_NO=21` | `TD_ACTUAL` |
| OPE (%) | `KPI_NO=22` | `TD_ACTUAL` |
| Downtime (Hours) | `KPI_NO=20` | `TD_ACTUAL` |
| Total Batches | `KPI_NO=7` | `SUM(TD_ACTUAL)` across furnaces |

### Tapping Metrics (from `kpi_furnace_tapping_clock`)

| KPI | Calculation |
|-----|-------------|
| Total Taps | `COUNT(*)` per furnace |
| Avg TTI (MWH) | `AVG(TTI_MWH)` excluding NULLs |
| Avg Slag Temp | `AVG(SLAG_TEMP)` excluding NULLs |
| Avg Mould Temp | `AVG(MOULD_TEMP)` excluding NULLs |
| Total Metal Out | `SUM(METAL_OUT)` |
| Total Slag Out | `SUM(SLAG_OUT)` |
| Metal-Slag Ratio | `METAL_OUT / SLAG_OUT` |

### Slag Metrics

| KPI | Source | Calculation |
|-----|--------|-------------|
| Slag (MT) | `KPI_NO=13` | `SUM(TD_ACTUAL)` across furnaces |
| Metal-Slag Ratio | `KPI_NO=14` | `AVG(TD_ACTUAL)` across furnaces |
| % Cr2O3 | `KPI_NO=16` | `TD_ACTUAL` per furnace |
| % Cr2O3 in Slag | `KPI_NO=19` | `AVG(TD_ACTUAL)` across furnaces |

---

## Date Range Aggregation Logic

For date range queries, different aggregation strategies are used:

| Metric Type | Strategy | Example KPIs |
|-------------|----------|--------------|
| **Absolute values** | SUM TD_ACTUAL | Production (3), Power (2), Slag (13), Batches (7) |
| **Rates/Percentages** | AVG TD_ACTUAL | Sp. Power (5), OEE (21), Recovery (9), Ratios (14) |
| **Tapping data** | SUM for totals, AVG for rates | Metal Out, Slag Out, TTI |

---

## Data Flow

```
1. API Request (/api/v1/dashboard/furnace?date=YYYY-MM-DD)
        ↓
2. FurnaceDataProcessor.process_date(date)
   - Queries kpi_furnace_oper_summary (22 KPIs × 6 entities = 132 rows/day)
   - Queries kpi_furnace_tapping_clock (variable rows based on taps)
   - Extracts KPI values using _get_kpi_value()
   - Builds 6 sections: production, power, recovery, operational, tapping, slag
        ↓
3. FurnaceClaudeInsightsGenerator.generate_insights(analysis_data, date)
   - Builds data context with production, efficiency, recovery metrics
   - Calls OpenAI GPT-4 API
   - Returns AI-generated insights HTML
        ↓
4. FurnaceTemplateEngine.generate_dashboard(...)
   - Loads furnace_dashboard.html
   - Injects KPI values via regex replacement
   - Injects chart data into JavaScript `analysisData` object
        ↓
5. Returns complete HTML dashboard
```

---

## Sample SQL Queries Used

### KPI Summary Query
```sql
SELECT
    KPI_DATE, FCE_NO, KPI_NO, KPI_DESC, UOM,
    TD_PLAN, MTD_PLAN, TD_ACTUAL, MTD_ACTUAL,
    TD_VAR, MTD_VAR
FROM kpi_furnace_oper_summary
WHERE KPI_DATE = '2026-01-15'
ORDER BY FCE_NO, KPI_NO
```

### Tapping Clock Query
```sql
SELECT
    KPI_DATE, FCE_NO, TAP_NO, ST_TIME, ED_TIME, DUR,
    TT_INTERVAL, TTI_MWH, SLAG_TEMP, MOULD_TEMP,
    METAL_OUT, SLAG_OUT, REMARKS
FROM kpi_furnace_tapping_clock
WHERE KPI_DATE = '2026-01-15'
ORDER BY FCE_NO, TAP_NO
```

### Date Range Query
```sql
SELECT
    KPI_DATE, FCE_NO, KPI_NO, KPI_DESC, UOM,
    TD_PLAN, MTD_PLAN, TD_ACTUAL, MTD_ACTUAL,
    TD_VAR, MTD_VAR
FROM kpi_furnace_oper_summary
WHERE KPI_DATE BETWEEN '2026-01-01' AND '2026-01-15'
ORDER BY KPI_DATE, FCE_NO, KPI_NO
```

### Production by Furnace
```sql
SELECT
    FCE_NO,
    TD_ACTUAL as production_mt,
    TD_PLAN as plan_mt,
    TD_VAR as variance
FROM kpi_furnace_oper_summary
WHERE KPI_DATE = '2026-01-15'
  AND KPI_NO = 3  -- Production KPI
ORDER BY FCE_NO
```

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

## Industry Benchmarks

| Metric | Norm/Target | Status Thresholds |
|--------|-------------|-------------------|
| Specific Power | 3500-3700 kWH/MT | Green: <3700, Yellow: 3700-4000, Red: >4000 |
| Cr Recovery | ≥85% | Green: ≥85%, Yellow: 80-85%, Red: <80% |
| Slag Ratio | 1.2-1.5 MT slag/MT FeCr | Green: ≤1.5, Yellow: 1.5-1.8, Red: >1.8 |
| OEE | ≥80% | Green: ≥80%, Yellow: 70-80%, Red: <70% |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No data displayed | Check if data exists for the requested date in both KPI tables |
| Production showing 0 | Verify `KPI_NO=3` and `FCE_NO` values in kpi_furnace_oper_summary |
| Tapping count wrong | Check `kpi_furnace_tapping_clock` for the date and furnace |
| MTD values incorrect | MTD values are cumulative; check previous days' data integrity |
| Rate calculations off | Rates/percentages should be averaged, not summed, in date ranges |
| NULL handling errors | Use `safe_float()` and `safe_int()` functions for all numeric conversions |

---

## Contact

**Department Lead**: @furnace-lead
**Branch**: `dept/furnace`

For questions or issues, contact the BAL-Agentic-Backend Team.
