# Quality Control (QC) Department Dashboard

## Overview

This module generates comprehensive dashboards for the **Quality Control (QC) Department** at Balasore Alloys Limited. It tracks despatch performance, furnace heat analysis with turnaround times, product quality deviations by furnace, stock movements, and QC lot inspections.

## File Structure

```
departments/qc/
├── __init__.py           # Module exports (QCDataProcessor, QCTemplateEngine, QCClaudeInsightsGenerator)
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
GET /api/v1/dashboard/qc?date=2026-01-15

# Date range dashboard:
GET /api/v1/dashboard/qc?start_date=2026-01-01&end_date=2026-01-15
```

### Template Location
`templates/quality_control_dashboard.html`

---

## Database Tables

### Table: `kpi_qc_despatch_performance`

**Description:** Daily despatch performance by customer with planned vs actual quantities.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `report_date` | date | PRI | NO | Report date |
| `customer` | varchar(100) | PRI | NO | Customer name |
| `planned_qty` | decimal(10,3) | - | YES | Planned quantity (MT) |
| `actual_qty` | decimal(10,3) | - | YES | Actual despatched quantity (MT) |
| `variance` | decimal(10,3) | - | YES | Actual - Planned |
| `reason` | varchar(255) | - | YES | Reason for variance |
| `dept_responsible` | varchar(100) | - | YES | Department responsible for variance |

**Primary Key:** (`report_date`, `customer`)

**Statistics:** ~1,234 rows, 0.11 MB

---

### Table: `kpi_qc_furnace_heat_composite_analysis`

**Description:** Heat-wise turnaround time tracking from sample receiving to reporting.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `FURNACE` | varchar(2) | PRI | NO | Furnace number ("1", "2", "3", "4", "5") |
| `DATE` | date | PRI | NO | Date of analysis |
| `HEAT_NO` | varchar(2) | PRI | NO | Heat number within furnace |
| `RECEIVING_TIME` | varchar(10) | - | YES | Time sample received (HH:MM:SS) |
| `REPORTING_TIME` | varchar(10) | - | YES | Time results reported (HH:MM:SS) |

**Primary Key:** (`FURNACE`, `DATE`, `HEAT_NO`)

**Statistics:** ~4,123 rows, 0.27 MB

---

### Table: `kpi_qc_product_deviation`

**Description:** Monthly product quality deviations aggregated by week ranges per furnace.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `MONTH` | varchar(20) | PRI | NO | Month name (e.g., "January") |
| `YEAR` | int | PRI | NO | Year |
| `FURNACE_NO` | varchar(6) | PRI | NO | Furnace number ("1", "2", "3", "4", "5") |
| `WEEK` | varchar(20) | PRI | NO | Cumulative week range (e.g., "1-8", "1-15", "1-23", "1-31") |
| `PROD_QTY_MT` | decimal(12,3) | - | YES | Production quantity (MT) |
| `CR_DEVIATION_QTY` | decimal(12,3) | - | YES | Chromium deviation quantity |
| `SI_DEVIATION_QTY` | decimal(12,3) | - | YES | Silicon deviation quantity |
| `C_DEVIATION_QTY` | decimal(12,3) | - | YES | Carbon deviation quantity |
| `S_DEVIATION_QTY` | decimal(12,3) | - | YES | Sulphur deviation quantity |
| `P_DEVIATION_QTY` | decimal(12,3) | - | YES | Phosphorus deviation quantity |
| `TOTAL_DEVIATION_MT` | decimal(12,3) | - | YES | Total deviation (MT) |
| `DEFECT_PERCENTAGE` | decimal(5,2) | - | YES | Defect rate (%) |
| `QUALITY_RATE_PERCENTAGE` | decimal(5,2) | - | YES | Quality rate (%) |

**Primary Key:** (`YEAR`, `MONTH`, `FURNACE_NO`, `WEEK`)

**Note:** Week ranges are cumulative: "1-8" = days 1-8, "1-15" = days 1-15, etc.

**Statistics:** ~136 rows, 0.02 MB

---

### Table: `kpi_qc_stock_summary`

**Description:** Daily stock summary by product with movements.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `report_date` | date | PRI | NO | Report date |
| `product` | varchar(50) | PRI | NO | Product name |
| `os_mt` | decimal(10,3) | - | YES | Opening stock (MT) |
| `td_mt` | decimal(10,3) | - | YES | Today's production (MT) |
| `rec_qty_mtd` | decimal(10,3) | - | YES | MTD received quantity |
| `fines_add` | decimal(10,3) | - | YES | Fines added |
| `fines_less` | decimal(10,3) | - | YES | Fines removed |
| `returned` | decimal(10,3) | - | YES | Returned quantity |
| `mtd_despatch` | decimal(10,3) | - | YES | MTD despatch |
| `closing_stock` | decimal(10,3) | - | YES | Closing stock (MT) |

**Primary Key:** (`report_date`, `product`)

**Statistics:** ~591 rows, 0.11 MB

---

### Table: `qm_quality_control`

**Description:** QC inspection lot master data from SAP QM module.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `LOT_NUMBER` | varchar(12) | PRI | NO | Inspection lot number |
| `PLANT` | varchar(4) | PRI | NO | Plant code |
| `MATERIAL_NO` | varchar(40) | PRI | NO | Material number |
| `MATERIAL_DESC` | varchar(40) | - | YES | Material description |
| `MATERIAL_TYPE` | varchar(4) | - | YES | Material type code |
| `LOT_QUANTITY` | double(13,3) | - | YES | Lot quantity |
| `LOT_QTY_UNIT` | varchar(3) | - | YES | Unit of measure |
| `QLT_START_DATE` | date | - | YES | Quality start date |
| `QLT_END_DATE` | date | - | YES | Quality end date |
| `INSPECTION_TYPE` | varchar(8) | PRI | NO | Inspection type code |
| `ACTUAL_LOT_QUANTITY` | double(13,3) | - | YES | Actual inspected quantity |
| `SUPPLIER` | varchar(10) | - | YES | Supplier code |
| `BATCH` | varchar(10) | - | YES | Batch number |
| `PO_NO` | varchar(10) | - | YES | Purchase order number |
| `STORAGE_LOCATION` | varchar(4) | - | YES | Storage location |
| ... | ... | ... | ... | *(43 columns total)* |

**Primary Key:** (`LOT_NUMBER`, `PLANT`, `MATERIAL_NO`, `INSPECTION_TYPE`)

**Statistics:** ~31,982 rows, 10.56 MB

---

### Table: `qm_quality_control_result`

**Description:** QC test results with inspection characteristics and measured values.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `LOT_NUMBER` | varchar(12) | PRI | NO | Inspection lot number (FK to qm_quality_control) |
| `NODE_NUMBER` | varchar(8) | - | NO | Node number in inspection plan |
| `INSPEC_CHAR_NO` | varchar(4) | PRI | NO | Inspection characteristic number |
| `SHORT_TEXT_INS_CHAR` | varchar(40) | - | YES | Characteristic description (e.g., "Moisture", "Over Size") |
| `RESULTS` | varchar(25) | - | YES | Test result value |
| `PLANT` | varchar(4) | - | YES | Plant code |
| `MATERIAL_NO` | varchar(40) | - | YES | Material number |
| `MATERIAL_DESC` | varchar(40) | - | YES | Material description |
| `MATERIAL_TYPE` | varchar(4) | - | YES | Material type |
| `ORDER_NUMBER` | varchar(12) | - | YES | Production order number |
| `USAGES` | varchar(3) | - | YES | Usage code |
| `GROUPS_NAME` | varchar(8) | - | YES | Characteristic group |

**Primary Key:** (`INSPEC_CHAR_NO`, `LOT_NUMBER`)

**Statistics:** ~102,868 rows, 27.56 MB

---

## Key Files Explained

### 1. `formatter.py` - QCDataProcessor

The main data processor that queries the database and builds the analysis data structure.

#### Constants

```python
# Furnace identifiers used in QC
FURNACE_LIST = ["1", "2", "3", "4", "5"]

# Month name mapping for product deviation query
MONTH_NAMES = {
    1: "January", 2: "February", ..., 12: "December"
}
```

#### Key Methods

| Method | Description |
|--------|-------------|
| `process_date(date)` | Main entry point for single-date processing |
| `process_date_range(start_date, end_date)` | Processes date range with aggregations |
| `_query_despatch_performance(date)` | Queries despatch data for a date |
| `_query_heat_analysis(date)` | Queries heat turnaround data |
| `_query_product_deviation(month_name, year)` | Queries monthly quality deviation data |
| `_query_stock_summary(date)` | Queries stock movements |
| `_query_qc_lots(date)` | Queries QC inspection lots |
| `_query_test_results(date)` | Queries test results with lot join |
| `_build_despatch_section(data)` | Builds customer despatch metrics |
| `_build_heat_analysis_section(data)` | Builds turnaround time analysis by furnace |
| `_build_product_quality_section(data, day_of_month)` | Selects appropriate week range for day |
| `_build_stock_section(data)` | Builds stock summary |
| `_build_qc_lots_section(data)` | Aggregates lots by material and plant |
| `_build_tests_section(data)` | Aggregates tests by characteristic type |

#### Helper Functions

```python
def calculate_turnaround_minutes(receiving_time: str, reporting_time: str) -> Optional[int]:
    """
    Calculate turnaround time in minutes between two time strings.
    Handles midnight rollover (e.g., 22:30 to 01:45 next day).

    Args:
        receiving_time: Time string (HH:MM:SS)
        reporting_time: Time string (HH:MM:SS)

    Returns:
        Turnaround time in minutes, or None if calculation fails
    """
    # Parse times
    rec_dt = datetime.combine(today, rec_time)
    rep_dt = datetime.combine(today, rep_time)

    # Handle midnight rollover
    if rep_dt < rec_dt:
        rep_dt += timedelta(days=1)

    # Return minutes
    return int((rep_dt - rec_dt).total_seconds() / 60)
```

#### Week Range Selection Logic

The product deviation table uses cumulative week ranges. The processor selects the appropriate range based on the selected day:

```python
def _build_product_quality_section(self, data, day_of_month):
    """
    Week ranges are cumulative:
    - 1-8: Week 1 (days 1-8)
    - 1-15: Week 1+2 (days 1-15)
    - 1-23: Week 1+2+3 (days 1-23)
    - 1-31: Full month (days 1-31)

    For day 5, use "1-8"; for day 12, use "1-15"
    """
    # Find smallest range that includes the day_of_month
    valid_weeks = [w for w in weeks if int(w.split('-')[-1]) >= day_of_month]
    selected_week = min(valid_weeks, key=lambda x: int(x.split('-')[-1]))
```

### 2. `template_engine.py` - QCTemplateEngine

Injects processed data into the HTML template.

**Key Methods:**
- `generate_dashboard(analysis_data, claude_insights_html, date)` - Main entry point
- Handles turnaround time formatting
- Injects quality rate data per furnace

### 3. `claude_analyzer.py` - QCClaudeInsightsGenerator

Generates AI-powered quality insights using OpenAI GPT-4.

**Key Methods:**
- `generate_insights(analysis_data, date)` - Generates 5-6 actionable insights
- Analyzes despatch achievement, turnaround times, quality rates
- Returns formatted HTML for dashboard injection

---

## KPIs and Calculations

### Despatch Performance

| KPI | Source Table | Calculation |
|-----|--------------|-------------|
| Total Planned | `kpi_qc_despatch_performance` | `SUM(planned_qty)` |
| Total Actual | `kpi_qc_despatch_performance` | `SUM(actual_qty)` |
| Variance | Calculated | `actual_qty - planned_qty` |
| Achievement % | Calculated | `(total_actual / total_planned) * 100` |
| Customers Served | `kpi_qc_despatch_performance` | `COUNT(DISTINCT customer)` |

### Heat Analysis Turnaround

| KPI | Source Table | Calculation |
|-----|--------------|-------------|
| Total Heats | `kpi_qc_furnace_heat_composite_analysis` | `COUNT(*)` per furnace |
| Turnaround Time | Calculated | `REPORTING_TIME - RECEIVING_TIME` (handles midnight) |
| Avg Turnaround | Calculated | `AVG(turnaround_minutes)` excluding NULLs |

**Turnaround Time Categories:**

| Category | Time Range |
|----------|------------|
| Excellent | < 30 minutes |
| Good | 30-60 minutes |
| Average | 60-120 minutes |
| Needs Improvement | > 120 minutes |

### Product Quality by Furnace

| KPI | Source Table | Column |
|-----|--------------|--------|
| Production (MT) | `kpi_qc_product_deviation` | `PROD_QTY_MT` |
| Quality Rate (%) | `kpi_qc_product_deviation` | `QUALITY_RATE_PERCENTAGE` |
| Defect Rate (%) | `kpi_qc_product_deviation` | `DEFECT_PERCENTAGE` |
| Total Deviation (MT) | `kpi_qc_product_deviation` | `TOTAL_DEVIATION_MT` |
| Cr Deviation | `kpi_qc_product_deviation` | `CR_DEVIATION_QTY` |
| Si Deviation | `kpi_qc_product_deviation` | `SI_DEVIATION_QTY` |
| C Deviation | `kpi_qc_product_deviation` | `C_DEVIATION_QTY` |

### Stock Summary

| KPI | Source Table | Column |
|-----|--------------|--------|
| Opening Stock | `kpi_qc_stock_summary` | `os_mt` |
| Today Production | `kpi_qc_stock_summary` | `td_mt` |
| MTD Received | `kpi_qc_stock_summary` | `rec_qty_mtd` |
| Fines Added | `kpi_qc_stock_summary` | `fines_add` |
| Fines Removed | `kpi_qc_stock_summary` | `fines_less` |
| MTD Despatch | `kpi_qc_stock_summary` | `mtd_despatch` |
| Closing Stock | `kpi_qc_stock_summary` | `closing_stock` |

### QC Lots & Tests

| KPI | Source Table | Calculation |
|-----|--------------|-------------|
| Total Lots | `qm_quality_control` | `COUNT(*)` where `QLT_START_DATE = date` |
| Lots by Material | `qm_quality_control` | `GROUP BY MATERIAL_DESC` |
| Lots by Plant | `qm_quality_control` | `GROUP BY PLANT` |
| Total Qty Inspected | `qm_quality_control` | `SUM(ACTUAL_LOT_QUANTITY)` |
| Total Tests | `qm_quality_control_result` | `COUNT(*)` joined with lots |
| Tests by Type | `qm_quality_control_result` | `GROUP BY SHORT_TEXT_INS_CHAR` |

---

## Data Flow

```
1. API Request (/api/v1/dashboard/qc?date=YYYY-MM-DD)
        ↓
2. QCDataProcessor.process_date(date)
   - Queries kpi_qc_despatch_performance
   - Queries kpi_qc_furnace_heat_composite_analysis
   - Queries kpi_qc_product_deviation (month, year from date)
   - Queries kpi_qc_stock_summary
   - Queries qm_quality_control (QC lots)
   - Queries qm_quality_control_result (joined with lots)
   - Calculates turnaround times with midnight handling
   - Selects appropriate week range for product quality
   - Builds 6 sections: despatch, qc_lots, tests, heat_analysis, product_quality, stock
        ↓
3. QCClaudeInsightsGenerator.generate_insights(analysis_data, date)
   - Builds data context with despatch, turnaround, quality metrics
   - Calls OpenAI GPT-4 API
   - Returns AI-generated insights HTML
        ↓
4. QCTemplateEngine.generate_dashboard(...)
   - Loads quality_control_dashboard.html
   - Injects KPI values via regex replacement
   - Injects chart data into JavaScript
        ↓
5. Returns complete HTML dashboard
```

---

## Sample SQL Queries Used

### Despatch Performance
```sql
SELECT customer, planned_qty, actual_qty, variance, reason, dept_responsible
FROM kpi_qc_despatch_performance
WHERE report_date = '2026-01-15'
ORDER BY customer
```

### Heat Analysis (Turnaround Times)
```sql
SELECT FURNACE, HEAT_NO, RECEIVING_TIME, REPORTING_TIME
FROM kpi_qc_furnace_heat_composite_analysis
WHERE DATE = '2026-01-15'
ORDER BY FURNACE, HEAT_NO
```

### Product Deviation (Monthly)
```sql
SELECT FURNACE_NO, WEEK, PROD_QTY_MT, QUALITY_RATE_PERCENTAGE,
       DEFECT_PERCENTAGE, TOTAL_DEVIATION_MT
FROM kpi_qc_product_deviation
WHERE MONTH = 'January' AND YEAR = 2026
ORDER BY FURNACE_NO, WEEK
```

### Stock Summary
```sql
SELECT product, os_mt, td_mt, rec_qty_mtd, fines_add, fines_less,
       returned, mtd_despatch, closing_stock
FROM kpi_qc_stock_summary
WHERE report_date = '2026-01-15'
ORDER BY product
```

### QC Lots
```sql
SELECT LOT_NUMBER, PLANT, MATERIAL_DESC, MATERIAL_TYPE, ACTUAL_LOT_QUANTITY
FROM qm_quality_control
WHERE QLT_START_DATE = '2026-01-15'
ORDER BY PLANT, MATERIAL_DESC
```

### Test Results (with Lot Join)
```sql
SELECT r.LOT_NUMBER, r.SHORT_TEXT_INS_CHAR, r.RESULTS, r.MATERIAL_DESC, r.PLANT
FROM qm_quality_control_result r
INNER JOIN qm_quality_control q ON r.LOT_NUMBER = q.LOT_NUMBER
WHERE q.QLT_START_DATE = '2026-01-15'
ORDER BY r.SHORT_TEXT_INS_CHAR, r.LOT_NUMBER
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

## Quality Benchmarks

| Metric | Target | Status Thresholds |
|--------|--------|-------------------|
| Despatch Achievement | ≥95% | Green: ≥95%, Yellow: 85-95%, Red: <85% |
| Avg Turnaround Time | ≤60 min | Green: ≤60, Yellow: 60-90, Red: >90 |
| Quality Rate | ≥98% | Green: ≥98%, Yellow: 95-98%, Red: <95% |
| Defect Rate | ≤2% | Green: ≤2%, Yellow: 2-5%, Red: >5% |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No data displayed | Check if data exists for the requested date in QC tables |
| Turnaround time negative | Verify `RECEIVING_TIME` and `REPORTING_TIME` formats (HH:MM:SS) |
| Furnace data missing | Verify furnace IDs are "1", "2", "3", "4", "5" in the data |
| Quality rate 0% | Check `QUALITY_RATE_PERCENTAGE` column values |
| Product deviation empty | Check MONTH name (e.g., "January" not "Jan") and YEAR in query |
| QC lots not showing | Verify `QLT_START_DATE` matches the selected date |
| Test results missing | Ensure `qm_quality_control_result` has matching `LOT_NUMBER` values |

---

## Contact

**Department Lead**: @qc-lead
**Branch**: `dept/qc`

For questions or issues, contact the BAL-Agentic-Backend Team.
