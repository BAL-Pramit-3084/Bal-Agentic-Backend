# Environment Department Dashboard

## Overview

This module generates comprehensive dashboards for the **Environment Department** at Balasore Alloys Limited. It tracks environmental compliance, waste management, emissions, air quality, and sustainability metrics across 14 normalized database tables.

## File Structure

```
departments/env/
├── __init__.py           # Module exports (ENVDataProcessor, ENVTemplateEngine, ENVClaudeInsightsGenerator)
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
GET /api/v1/dashboard/env?date=2026-01-15

# Date range dashboard:
GET /api/v1/dashboard/env?start_date=2026-01-01&end_date=2026-01-15
```

### Template Location
`templates/env_dashboard.html`

---

## Database Tables Overview

This module queries **14 normalized tables**:

| # | Table Name | Description | Row Count |
|---|------------|-------------|-----------|
| 1 | `kpi_env_food_waste_data` | Daily food waste by location | ~481 |
| 2 | `kpi_env_stp_water_data` | STP water treatment readings | ~281 |
| 3 | `env_cbam` | CBAM emissions (daily) | ~225 |
| 4 | `kpi_env_compliance` | License/clearance status | ~17 |
| 5 | `kpi_env_compliance_return` | Regulatory return filings | ~23 |
| 6 | `kpi_env_slag_gcp_dust_data` | Industrial waste (monthly) | ~17 |
| 7 | `kpi_env_biomedical_waste_data` | Biomedical waste tracking | ~656 |
| 8 | `kpi_env_incident_report` | Environmental incidents | ~3 |
| 9 | `kpi_env_monitoring_report` | Air quality monitoring (monthly) | ~154 |
| 10 | `kpi_env_training_records` | ESG/Environment training | ~6 |
| 11 | `kpi_env_water_consumption_data` | Borewell consumption | ~502 |
| 12 | `kpi_env_horticulture_plantation` | Plantation tracking | ~1,807 |
| 13 | `kpi_env_used_oil_data` | Used oil management | ~6 |
| 14 | `kpi_env_observation_report` | Environmental observations | ~4 |

---

## Database Table Schemas

### Table 1: `kpi_env_food_waste_data`

**Description:** Daily food waste tracking by location (canteens).

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `DATE` | date | PRI | NO | Recording date |
| `PLANT` | varchar(4) | PRI | NO | Plant code |
| `LOCATION` | varchar(50) | PRI | NO | Canteen/location name |
| `WASTE_KG` | decimal(8,3) | - | YES | Food waste in kilograms |
| `PERSONS_COUNT` | int | - | YES | Number of persons served |
| `WASTE_PER_PERSON_GM` | decimal(10,3) | - | YES | Calculated waste per person (grams) |
| `ENTRY_ID` | int | - | YES | User who entered |
| `ENTRY_DATE` | date | - | YES | Entry timestamp |
| `UPDATED_DATE` | date | - | YES | Last update timestamp |

**Primary Key:** (`DATE`, `LOCATION`, `PLANT`)

**Statistics:** ~481 rows, 0.08 MB

---

### Table 2: `kpi_env_stp_water_data`

**Description:** Sewage Treatment Plant water flow readings.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `DATE` | date | PRI | NO | Recording date |
| `PLANT` | varchar(4) | PRI | NO | Plant code |
| `INITIAL_READING` | varchar(20) | - | YES | Meter initial reading |
| `FINAL_READING` | varchar(20) | - | YES | Meter final reading |
| `DIFFERENCE` | varchar(5) | - | YES | Daily flow (Final - Initial) |
| `ENTRY_ID` | int | - | YES | User who entered |
| `ENTRY_DATE` | date | - | YES | Entry timestamp |
| `UPDATED_DATE` | date | - | YES | Last update timestamp |

**Primary Key:** (`DATE`, `PLANT`)

**Statistics:** ~281 rows, 0.02 MB

---

### Table 3: `env_cbam`

**Description:** Carbon Border Adjustment Mechanism (CBAM) emissions data.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `POSTING_DATE` | date | PRI | NO | Emission recording date |
| `CARBON_PCT_WEIGHTED_AVG` | decimal(5,2) | - | YES | Weighted average carbon % |
| `CHROMIUM_PCT_WEIGHTED_AVG` | decimal(5,2) | - | YES | Weighted average chromium % |
| `TOTAL_CARBON_LOT_QTY` | decimal(11,3) | - | YES | Total carbon lot quantity |
| `TOTAL_CHROMIUM_LOT_QTY` | decimal(11,3) | - | YES | Total chromium lot quantity |
| `HCFC_PRODUCTION` | decimal(11,3) | - | YES | High Carbon FeCr production |
| `ELECTRICITY_CONSUMPTION` | decimal(11,3) | - | YES | Electricity consumed (MWh) |
| `B_EMLNST` | decimal(11,3) | - | YES | Base emission standard |
| `EMBEDDED_ELECTRICITY` | decimal(11,3) | - | YES | Embedded electricity emissions |
| `SEE_DIRECT` | decimal(11,3) | - | YES | Specific Embedded Emissions (Direct) |
| `SEE_INDIRECT` | decimal(11,3) | - | YES | Specific Embedded Emissions (Indirect) |
| `SEE_TOTAL` | decimal(11,3) | - | YES | Total SEE (Direct + Indirect) |

**Primary Key:** (`POSTING_DATE`)

**Statistics:** ~225 rows, 0.05 MB

---

### Table 4: `kpi_env_compliance`

**Description:** Environmental licenses and clearances master.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `SL_NO` | int | PRI | NO | Serial number (auto-increment) |
| `LOCATION` | varchar(15) | - | YES | Plant/location |
| `CLEARANCE_TYPE` | varchar(100) | - | YES | Type of clearance/license |
| `LICENSE_NO` | varchar(100) | - | YES | License number |
| `DESCRIPTION` | text | - | YES | License description |
| `LICENSING_AUTHORITY` | varchar(100) | - | YES | Issuing authority |
| `VALID_UPTO` | date | - | YES | License expiry date |
| `RENEWAL_DATE` | date | - | YES | Next renewal date |
| `PAYMENT_DUE` | varchar(50) | - | YES | Payment due information |
| `REMARKS` | text | - | YES | Additional remarks |
| `ENTRY_ID` | int | - | YES | User who entered |
| `ENTRY_DATE` | date | - | YES | Entry timestamp |
| `UPDATED_DATE` | date | - | YES | Last update timestamp |

**Primary Key:** (`SL_NO`)

**Statistics:** ~17 rows, 0.02 MB

---

### Table 5: `kpi_env_compliance_return`

**Description:** Regulatory return filings and compliance status.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `SL_NO` | int | PRI | NO | Serial number (auto-increment) |
| `AREA` | varchar(15) | - | YES | Compliance area (Air, Water, etc.) |
| `SUBJECT` | varchar(100) | - | YES | Return subject |
| `ACT_RULE` | varchar(100) | - | YES | Applicable act/rule |
| `FORMAT` | varchar(50) | - | YES | Return format |
| `SUBMISSION_PERIOD` | varchar(50) | - | YES | Submission frequency |
| `SUBMISSION_DATE` | date | - | YES | Actual submission date |
| `COMPLIANCE_STATUS` | varchar(50) | - | YES | Status (Submitted/Pending) |
| `COMPLIANCE_AUTHORITY` | varchar(100) | - | YES | Authority name |
| `REMARKS` | varchar(100) | - | YES | Additional remarks |
| `ENTRY_ID` | int | - | YES | User who entered |
| `ENTRY_DATE` | date | - | YES | Entry timestamp |
| `UPDATED_DATE` | date | - | YES | Last update timestamp |

**Primary Key:** (`SL_NO`)

**Statistics:** ~23 rows, 0.02 MB

---

### Table 6: `kpi_env_slag_gcp_dust_data`

**Description:** Industrial waste - Slag and GCP Dust generation (monthly).

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `YEAR` | varchar(10) | PRI | NO | Calendar year |
| `MONTH` | varchar(10) | PRI | NO | Month name |
| `PRODUCTION_MT` | decimal(12,3) | - | YES | Production in metric tons |
| `SLAG_MT` | decimal(12,3) | - | YES | Slag generated (MT) |
| `GCP_DUST_MT` | decimal(12,3) | - | YES | GCP Dust generated (MT) |

**Primary Key:** (`YEAR`, `MONTH`)

**Statistics:** ~17 rows, 0.02 MB

---

### Table 7: `kpi_env_biomedical_waste_data`

**Description:** Biomedical waste tracking by container type.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `DATE` | date | PRI | NO | Recording date |
| `PLANT` | varchar(4) | PRI | NO | Plant code |
| `CONTAINER_TYPE` | varchar(20) | PRI | NO | Container type (Yellow/Red/Blue/White) |
| `GENERETED_GRAMS` | decimal(10,3) | - | NO | Waste generated (grams) |
| `DISPOSED_GRAMS` | decimal(10,3) | - | YES | Waste disposed (grams) |
| `STOCK_GRAMS` | decimal(10,3) | - | YES | Stock remaining (grams) |
| `ENTRY_ID` | int | - | YES | User who entered |
| `ENTRY_DATE` | date | - | YES | Entry timestamp |
| `UPDATED_DATE` | date | - | YES | Last update timestamp |

**Primary Key:** (`DATE`, `PLANT`, `CONTAINER_TYPE`)

**Statistics:** ~656 rows, 0.08 MB

---

### Table 8: `kpi_env_incident_report`

**Description:** Environmental incident records.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `DATE` | date | PRI | NO | Incident date |
| `PLANT` | varchar(4) | PRI | NO | Plant code |
| `NAME` | varchar(100) | - | YES | Reporter name |
| `DEPARTMENT` | varchar(50) | - | YES | Department involved |
| `INCIDENT_DESCRIPTION` | varchar(100) | - | YES | Incident description |
| `ENTRY_ID` | int | - | YES | User who entered |
| `ENTRY_DATE` | date | - | YES | Entry timestamp |
| `UPDATED_DATE` | date | - | YES | Last update timestamp |

**Primary Key:** (`DATE`, `PLANT`)

**Statistics:** ~3 rows, 0.02 MB

---

### Table 9: `kpi_env_monitoring_report`

**Description:** Air quality monitoring data (monthly, by pollutant and station).

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `YEAR` | int | PRI | NO | Calendar year |
| `MONTH` | varchar(3) | PRI | NO | Month abbreviation (Jan, Feb, etc.) |
| `POLLUTANT` | varchar(10) | PRI | NO | Pollutant code (PM10, PM2.5, SO2, NO2, CO) |
| `STATION` | varchar(10) | PRI | NO | Monitoring station code |
| `VALUE` | decimal(8,3) | - | YES | Measured value (µg/m³) |

**Primary Key:** (`YEAR`, `MONTH`, `POLLUTANT`, `STATION`)

**Statistics:** ~154 rows, 0.02 MB

---

### Table 10: `kpi_env_training_records`

**Description:** Environment/ESG training records.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `DATE` | date | PRI | NO | Training date |
| `PLANT` | varchar(50) | PRI | NO | Plant/location |
| `TRAINING_NAME` | varchar(100) | - | YES | Training program name |
| `TRAINER_NAME` | varchar(100) | - | YES | Trainer name |
| `ATTENDEES_COUNT` | int | - | YES | Number of attendees |
| `ENTRY_ID` | int | - | YES | User who entered |
| `ENTRY_DATE` | date | - | YES | Entry timestamp |
| `UPDATED_DATE` | date | - | YES | Last update timestamp |

**Primary Key:** (`DATE`, `PLANT`)

**Statistics:** ~6 rows, 0.02 MB

---

### Table 11: `kpi_env_water_consumption_data`

**Description:** Borewell water consumption tracking.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `DATE` | date | PRI | NO | Recording date |
| `MONTH` | varchar(20) | PRI | NO | Month name |
| `BOREWELL_1` | decimal(10,3) | - | YES | Borewell 1 consumption |
| `BOREWELL_2` | decimal(10,3) | - | YES | Borewell 2 consumption |
| `BOREWELL_3` | decimal(10,3) | - | YES | Borewell 3 consumption |
| `BOREWELL_4` | decimal(10,3) | - | YES | Borewell 4 consumption |
| `BOREWELL_5` | decimal(10,3) | - | YES | Borewell 5 consumption |
| `TOTAL_CONSUMPTION` | decimal(10,3) | - | YES | Total consumption (sum of all borewells) |

**Primary Key:** (`DATE`, `MONTH`)

**Statistics:** ~502 rows, 0.06 MB

---

### Table 12: `kpi_env_horticulture_plantation`

**Description:** Tree plantation and horticulture tracking.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `DATE` | date | PRI | NO | Recording date |
| `PLANT` | varchar(4) | PRI | NO | Plant code |
| `AREA` | varchar(100) | PRI | NO | Plantation area |
| `PLANT_NAME` | varchar(100) | PRI | NO | Plant/tree species name |
| `TARGET` | int | - | YES | Plantation target count |
| `ACTUAL` | int | - | YES | Actual plantation count |
| `REMARKS` | varchar(100) | - | YES | Additional remarks |
| `ENTRY_ID` | int | - | NO | User who entered |
| `ENTRY_DATE` | date | - | YES | Entry timestamp |
| `UPDATED_DATE` | date | - | YES | Last update timestamp |

**Primary Key:** (`DATE`, `PLANT`, `AREA`, `PLANT_NAME`)

**Statistics:** ~1,807 rows, 0.16 MB

---

### Table 13: `kpi_env_used_oil_data`

**Description:** Used oil generation and disposal tracking.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `DATE` | date | PRI | NO | Recording date |
| `PLANT` | varchar(4) | PRI | NO | Plant code |
| `GENERATION_KL` | decimal(8,3) | - | YES | Used oil generated (kiloliters) |
| `DISPOSED_KL` | decimal(8,3) | - | YES | Used oil disposed (kiloliters) |
| `BALANCE_KL` | decimal(8,3) | - | YES | Balance remaining (kiloliters) |
| `ENTRY_ID` | int | - | YES | User who entered |
| `ENTRY_DATE` | date | - | YES | Entry timestamp |
| `UPDATED_DATE` | date | - | YES | Last update timestamp |

**Primary Key:** (`DATE`, `PLANT`)

**Statistics:** ~6 rows, 0.02 MB

---

### Table 14: `kpi_env_observation_report`

**Description:** Environmental observation and audit reports.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `DATE` | date | PRI | NO | Observation date |
| `PLANT` | varchar(4) | PRI | NO | Plant code |
| `OBSERVER_NAME` | varchar(100) | - | NO | Observer name |
| `AREA` | varchar(100) | - | NO | Observation area |
| `DESCRIPTION` | text | - | YES | Observation details |
| `ENTRY_ID` | int | - | YES | User who entered |
| `ENTRY_DATE` | date | - | YES | Entry timestamp |
| `UPDATED_DATE` | date | - | YES | Last update timestamp |

**Primary Key:** (`DATE`, `PLANT`)

**Statistics:** ~4 rows, 0.02 MB

---

## Key Files Explained

### 1. `formatter.py` - ENVDataProcessor

The main data processor that queries all 14 tables and builds the analysis data structure (~1,431 lines).

#### Key Constants

```python
# Month name mappings
MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}

MONTH_ABBREV = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
}

# Air quality limits (NAAQS standards)
AIR_QUALITY_LIMITS = {
    "PM10": 100,    # µg/m³
    "PM2.5": 60,    # µg/m³
    "SO2": 80,      # µg/m³
    "NO2": 80,      # µg/m³
    "CO": 4000,     # µg/m³
}
```

#### Helper Functions

```python
def get_financial_year(date_obj: datetime) -> str:
    """
    Calculate Indian financial year (April-March).
    Example: 2026-01-15 → "2025-26"
    """
    if date_obj.month >= 4:
        return f"{date_obj.year}-{str(date_obj.year + 1)[2:]}"
    else:
        return f"{date_obj.year - 1}-{str(date_obj.year)[2:]}"

def get_license_status(valid_upto, today) -> Tuple[str, str]:
    """
    Determine license status based on expiry date.
    Returns: (status_class, status_text)
    """
    if valid_upto is None:
        return ("status-na", "Perpetual")
    days_remaining = (valid_upto - today).days
    if days_remaining < 0:
        return ("status-expired", f"Expired {abs(days_remaining)} days ago")
    elif days_remaining <= 90:
        return ("status-expiring", f"Expires in {days_remaining} days")
    else:
        return ("status-valid", f"Valid for {days_remaining} days")
```

#### Key Methods

| Method | Source Table(s) | Description |
|--------|-----------------|-------------|
| `process_date(date)` | All 14 tables | Main entry point for single-date processing |
| `process_date_range(start_date, end_date)` | All 14 tables | Process date range with aggregations |
| `_query_food_waste(date)` | `kpi_env_food_waste_data` | Food waste by location |
| `_query_stp_water(date)` | `kpi_env_stp_water_data` | STP water flow data |
| `_query_cbam_emissions(date)` | `env_cbam` | CBAM emission metrics |
| `_query_licenses()` | `kpi_env_compliance` | All licenses with status |
| `_query_compliance_returns()` | `kpi_env_compliance_return` | Regulatory filings |
| `_query_air_quality(year, month)` | `kpi_env_monitoring_report` | Air quality by pollutant/station |
| `_query_industrial_waste(year, month)` | `kpi_env_slag_gcp_dust_data` | Slag and GCP dust |
| `_query_biomedical_waste(date)` | `kpi_env_biomedical_waste_data` | Biomedical waste by container |
| `_query_incidents(date)` | `kpi_env_incident_report` | Environmental incidents |
| `_query_training(date)` | `kpi_env_training_records` | Training records |
| `_query_water_consumption(date)` | `kpi_env_water_consumption_data` | Borewell consumption |
| `_query_horticulture(date)` | `kpi_env_horticulture_plantation` | Plantation data |
| `_query_used_oil(date)` | `kpi_env_used_oil_data` | Used oil data |
| `_query_observations(date)` | `kpi_env_observation_report` | Observation reports |
| `_build_executive_summary(...)` | Multiple | Build 6-card summary |
| `_build_food_waste_section(...)` | `kpi_env_food_waste_data` | Food waste analysis |
| `_build_stp_water_section(...)` | `kpi_env_stp_water_data` | STP water analysis |
| `_build_cbam_section(...)` | `env_cbam` | CBAM emissions analysis |
| `_build_licenses_section(...)` | `kpi_env_compliance` | License status cards |
| `_build_air_quality_section(...)` | `kpi_env_monitoring_report` | Air quality vs limits |
| `_build_industrial_waste_section(...)` | `kpi_env_slag_gcp_dust_data` | Waste ratio analysis |
| `_build_compliance_returns_section(...)` | `kpi_env_compliance_return` | Filing status |
| `_build_training_section(...)` | `kpi_env_training_records` | Training summary |
| `_build_incidents_section(...)` | `kpi_env_incident_report` | Incident listing |
| `_build_biomedical_waste_section(...)` | `kpi_env_biomedical_waste_data` | Waste by container |

### 2. `template_engine.py` - ENVTemplateEngine

Injects processed data into the HTML template.

**Key Methods:**
- `generate_dashboard(analysis_data, claude_insights_html, date)` - Main entry point
- Replaces all section-specific data (food waste, STP, CBAM, licenses, etc.)
- Injects chart data into JavaScript (Chart.js format)

### 3. `claude_analyzer.py` - ENVClaudeInsightsGenerator

Generates AI-powered environmental insights using OpenAI GPT-4 (or local LLM).

**Key Methods:**
- `generate_insights(analysis_data, date)` - Generates 5-6 actionable insights
- Analyzes compliance gaps, emission trends, waste patterns
- Returns formatted HTML for dashboard injection

---

## KPIs and Calculations

### Executive Summary (6 KPI Cards)

| KPI | Source Table | Column(s) | Calculation |
|-----|--------------|-----------|-------------|
| Food Waste (kg) | `kpi_env_food_waste_data` | `WASTE_KG` | `SUM(WASTE_KG)` |
| Persons Served | `kpi_env_food_waste_data` | `PERSONS_COUNT` | `SUM(PERSONS_COUNT)` |
| STP Water Flow (KL) | `kpi_env_stp_water_data` | `DIFFERENCE` | `SUM(CAST(DIFFERENCE AS DECIMAL))` |
| Compliance Score (%) | `kpi_env_compliance_return` | `COMPLIANCE_STATUS` | `COUNT(status='Submitted') / COUNT(*) * 100` |
| Incidents | `kpi_env_incident_report` | `*` | `COUNT(*)` |
| CBAM Emissions | `env_cbam` | `SEE_TOTAL` | Latest `SEE_TOTAL` value |

### Food Waste Section

| Metric | Source Table | Column(s) | Calculation |
|--------|--------------|-----------|-------------|
| Total Waste (kg) | `kpi_env_food_waste_data` | `WASTE_KG` | `SUM(WASTE_KG)` for date/range |
| Total Persons | `kpi_env_food_waste_data` | `PERSONS_COUNT` | `SUM(PERSONS_COUNT)` |
| Waste per Person (g) | `kpi_env_food_waste_data` | `WASTE_KG`, `PERSONS_COUNT` | `(SUM(WASTE_KG) * 1000) / SUM(PERSONS_COUNT)` |
| Zero Waste Days | `kpi_env_food_waste_data` | `WASTE_KG` | `COUNT(*) WHERE WASTE_KG = 0` |
| Locations | `kpi_env_food_waste_data` | `LOCATION` | `GROUP BY LOCATION` |

### STP Water Section

| Metric | Source Table | Column(s) | Calculation |
|--------|--------------|-----------|-------------|
| Initial Reading | `kpi_env_stp_water_data` | `INITIAL_READING` | Direct value |
| Final Reading | `kpi_env_stp_water_data` | `FINAL_READING` | Direct value |
| Daily Flow (KL) | `kpi_env_stp_water_data` | `DIFFERENCE` | `CAST(DIFFERENCE AS DECIMAL)` |
| MTD Total | `kpi_env_stp_water_data` | `DIFFERENCE` | `SUM(DIFFERENCE)` for month |
| MTD Average | `kpi_env_stp_water_data` | `DIFFERENCE` | `AVG(DIFFERENCE)` for month |
| Anomaly Flag | Calculated | - | `daily_flow > (avg * 1.2)` |

### CBAM Emissions Section

| Metric | Source Table | Column(s) | Calculation |
|--------|--------------|-----------|-------------|
| Direct Emissions | `env_cbam` | `SEE_DIRECT` | Latest value (tCO2e/MT) |
| Indirect Emissions | `env_cbam` | `SEE_INDIRECT` | Latest value (tCO2e/MT) |
| Total Emissions | `env_cbam` | `SEE_TOTAL` | Latest value (tCO2e/MT) |
| Threshold Gap (%) | `env_cbam` | `SEE_TOTAL` | `(5.45 - SEE_TOTAL) / 5.45 * 100` |
| HCFC Production | `env_cbam` | `HCFC_PRODUCTION` | Latest value (MT) |
| Electricity Consumption | `env_cbam` | `ELECTRICITY_CONSUMPTION` | Latest value (MWh) |
| Carbon % Avg | `env_cbam` | `CARBON_PCT_WEIGHTED_AVG` | Weighted average |
| Chromium % Avg | `env_cbam` | `CHROMIUM_PCT_WEIGHTED_AVG` | Weighted average |

**CBAM Threshold:** 5.45 tCO2e/MT (EU default value for FeCr)

### License Status Section

| Status | Logic | Display |
|--------|-------|---------|
| `status-expired` | `VALID_UPTO < today` | Red badge |
| `status-expiring` | `0 <= days_remaining <= 90` | Yellow badge |
| `status-valid` | `days_remaining > 90` | Green badge |
| `status-na` | `VALID_UPTO IS NULL` | Gray badge (Perpetual) |

| Metric | Source Table | Column(s) | Calculation |
|--------|--------------|-----------|-------------|
| License Type | `kpi_env_compliance` | `CLEARANCE_TYPE` | Direct value |
| License No | `kpi_env_compliance` | `LICENSE_NO` | Direct value |
| Authority | `kpi_env_compliance` | `LICENSING_AUTHORITY` | Direct value |
| Valid Until | `kpi_env_compliance` | `VALID_UPTO` | Direct value |
| Days Remaining | `kpi_env_compliance` | `VALID_UPTO` | `(VALID_UPTO - CURDATE()).days` |
| Expired Count | `kpi_env_compliance` | `VALID_UPTO` | `COUNT(*) WHERE VALID_UPTO < CURDATE()` |
| Expiring Count | `kpi_env_compliance` | `VALID_UPTO` | `COUNT(*) WHERE VALID_UPTO BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 90 DAY)` |

### Air Quality Section (NAAQS Standards)

| Pollutant | Limit (µg/m³) | Source Table | Column(s) |
|-----------|---------------|--------------|-----------|
| PM10 | 100 | `kpi_env_monitoring_report` | `VALUE WHERE POLLUTANT='PM10'` |
| PM2.5 | 60 | `kpi_env_monitoring_report` | `VALUE WHERE POLLUTANT='PM2.5'` |
| SO2 | 80 | `kpi_env_monitoring_report` | `VALUE WHERE POLLUTANT='SO2'` |
| NO2 | 80 | `kpi_env_monitoring_report` | `VALUE WHERE POLLUTANT='NO2'` |
| CO | 4000 | `kpi_env_monitoring_report` | `VALUE WHERE POLLUTANT='CO'` |

| Metric | Source Table | Column(s) | Calculation |
|--------|--------------|-----------|-------------|
| Station Reading | `kpi_env_monitoring_report` | `VALUE`, `STATION` | `VALUE` per station |
| Compliance Status | Calculated | - | `VALUE <= LIMIT` → "Compliant" |
| % of Limit | Calculated | - | `(VALUE / LIMIT) * 100` |
| Station Count | `kpi_env_monitoring_report` | `STATION` | `COUNT(DISTINCT STATION)` |

### Industrial Waste Section

| Metric | Source Table | Column(s) | Calculation |
|--------|--------------|-----------|-------------|
| Production (MT) | `kpi_env_slag_gcp_dust_data` | `PRODUCTION_MT` | Direct value for month |
| Slag (MT) | `kpi_env_slag_gcp_dust_data` | `SLAG_MT` | Direct value for month |
| GCP Dust (MT) | `kpi_env_slag_gcp_dust_data` | `GCP_DUST_MT` | Direct value for month |
| Slag Ratio (%) | `kpi_env_slag_gcp_dust_data` | `SLAG_MT`, `PRODUCTION_MT` | `(SLAG_MT / PRODUCTION_MT) * 100` |
| GCP Dust Ratio (%) | `kpi_env_slag_gcp_dust_data` | `GCP_DUST_MT`, `PRODUCTION_MT` | `(GCP_DUST_MT / PRODUCTION_MT) * 100` |
| YTD Production | `kpi_env_slag_gcp_dust_data` | `PRODUCTION_MT` | `SUM(PRODUCTION_MT)` for year |

### Compliance Returns Section

| Metric | Source Table | Column(s) | Calculation |
|--------|--------------|-----------|-------------|
| Total Returns | `kpi_env_compliance_return` | `*` | `COUNT(*)` |
| Submitted | `kpi_env_compliance_return` | `COMPLIANCE_STATUS` | `COUNT(*) WHERE COMPLIANCE_STATUS LIKE '%submitted%'` |
| Pending | `kpi_env_compliance_return` | `COMPLIANCE_STATUS` | `COUNT(*) WHERE COMPLIANCE_STATUS NOT LIKE '%submitted%'` |
| Compliance Rate (%) | Calculated | - | `(Submitted / Total) * 100` |
| By Area | `kpi_env_compliance_return` | `AREA` | `GROUP BY AREA` |
| By Authority | `kpi_env_compliance_return` | `COMPLIANCE_AUTHORITY` | `GROUP BY COMPLIANCE_AUTHORITY` |

### Biomedical Waste Section

| Metric | Source Table | Column(s) | Calculation |
|--------|--------------|-----------|-------------|
| Generated (g) | `kpi_env_biomedical_waste_data` | `GENERETED_GRAMS` | `SUM(GENERETED_GRAMS)` |
| Disposed (g) | `kpi_env_biomedical_waste_data` | `DISPOSED_GRAMS` | `SUM(DISPOSED_GRAMS)` |
| Stock (g) | `kpi_env_biomedical_waste_data` | `STOCK_GRAMS` | `SUM(STOCK_GRAMS)` |
| By Container | `kpi_env_biomedical_waste_data` | `CONTAINER_TYPE` | `GROUP BY CONTAINER_TYPE` |
| Disposal Rate (%) | Calculated | - | `(Disposed / Generated) * 100` |

**Container Types:** Yellow, Red, Blue, White (as per BMW Rules)

### Training Section

| Metric | Source Table | Column(s) | Calculation |
|--------|--------------|-----------|-------------|
| Training Count | `kpi_env_training_records` | `*` | `COUNT(*)` |
| Total Attendees | `kpi_env_training_records` | `ATTENDEES_COUNT` | `SUM(ATTENDEES_COUNT)` |
| Programs | `kpi_env_training_records` | `TRAINING_NAME` | `GROUP BY TRAINING_NAME` |
| By Plant | `kpi_env_training_records` | `PLANT` | `GROUP BY PLANT` |

### Horticulture Section

| Metric | Source Table | Column(s) | Calculation |
|--------|--------------|-----------|-------------|
| Target Plants | `kpi_env_horticulture_plantation` | `TARGET` | `SUM(TARGET)` |
| Actual Plants | `kpi_env_horticulture_plantation` | `ACTUAL` | `SUM(ACTUAL)` |
| Achievement (%) | Calculated | - | `(Actual / Target) * 100` |
| By Species | `kpi_env_horticulture_plantation` | `PLANT_NAME` | `GROUP BY PLANT_NAME` |
| By Area | `kpi_env_horticulture_plantation` | `AREA` | `GROUP BY AREA` |

### Used Oil Section

| Metric | Source Table | Column(s) | Calculation |
|--------|--------------|-----------|-------------|
| Generated (KL) | `kpi_env_used_oil_data` | `GENERATION_KL` | `SUM(GENERATION_KL)` |
| Disposed (KL) | `kpi_env_used_oil_data` | `DISPOSED_KL` | `SUM(DISPOSED_KL)` |
| Balance (KL) | `kpi_env_used_oil_data` | `BALANCE_KL` | Latest `BALANCE_KL` |
| Disposal Rate (%) | Calculated | - | `(Disposed / Generated) * 100` |

### Incident Section

| Metric | Source Table | Column(s) | Calculation |
|--------|--------------|-----------|-------------|
| Incident Count | `kpi_env_incident_report` | `*` | `COUNT(*)` for date/range |
| By Department | `kpi_env_incident_report` | `DEPARTMENT` | `GROUP BY DEPARTMENT` |
| By Plant | `kpi_env_incident_report` | `PLANT` | `GROUP BY PLANT` |

---

## Data Flow

```
1. API Request (/api/v1/dashboard/env?date=YYYY-MM-DD)
        ↓
2. ENVDataProcessor.process_date(date)
   - Queries all 14 tables:
     • kpi_env_food_waste_data → Food waste metrics
     • kpi_env_stp_water_data → STP water flow
     • env_cbam → CBAM emissions
     • kpi_env_compliance → License status
     • kpi_env_compliance_return → Filing status
     • kpi_env_slag_gcp_dust_data → Industrial waste
     • kpi_env_biomedical_waste_data → BMW tracking
     • kpi_env_incident_report → Incidents
     • kpi_env_monitoring_report → Air quality
     • kpi_env_training_records → Training
     • kpi_env_water_consumption_data → Borewell consumption
     • kpi_env_horticulture_plantation → Plantation
     • kpi_env_used_oil_data → Used oil
     • kpi_env_observation_report → Observations
   - Builds sections: executive_summary, food_waste, stp_water,
     cbam_emissions, licenses, air_quality, industrial_waste,
     compliance_returns, training, incidents, biomedical_waste,
     horticulture, used_oil, observations, data_gaps
        ↓
3. ENVClaudeInsightsGenerator.generate_insights(analysis_data, date)
   - Builds data context with all metrics
   - Calls OpenAI GPT-4 API
   - Returns AI-generated insights HTML
        ↓
4. ENVTemplateEngine.generate_dashboard(...)
   - Loads env_dashboard.html
   - Replaces all hardcoded values via regex
   - Injects chart data into JavaScript (Chart.js)
   - Injects AI insights HTML
        ↓
5. Returns complete HTML dashboard
```

---

## Sample SQL Queries Used

### Food Waste Query
```sql
SELECT DATE, PLANT, LOCATION, WASTE_KG, PERSONS_COUNT, WASTE_PER_PERSON_GM
FROM kpi_env_food_waste_data
WHERE DATE >= '2026-01-01' AND DATE <= '2026-01-15'
ORDER BY DATE, LOCATION
```

### CBAM Emissions Query
```sql
SELECT POSTING_DATE, SEE_DIRECT, SEE_INDIRECT, SEE_TOTAL,
       HCFC_PRODUCTION, ELECTRICITY_CONSUMPTION,
       CARBON_PCT_WEIGHTED_AVG, CHROMIUM_PCT_WEIGHTED_AVG
FROM env_cbam
WHERE POSTING_DATE >= '2026-01-01' AND POSTING_DATE <= '2026-01-15'
ORDER BY POSTING_DATE DESC
LIMIT 1
```

### License Status Query
```sql
SELECT SL_NO, LOCATION, CLEARANCE_TYPE, LICENSE_NO, DESCRIPTION,
       LICENSING_AUTHORITY, VALID_UPTO, RENEWAL_DATE, PAYMENT_DUE, REMARKS
FROM kpi_env_compliance
ORDER BY VALID_UPTO ASC
```

### Compliance Returns Query
```sql
SELECT SL_NO, AREA, SUBJECT, ACT_RULE, FORMAT,
       SUBMISSION_PERIOD, SUBMISSION_DATE, COMPLIANCE_STATUS,
       COMPLIANCE_AUTHORITY, REMARKS
FROM kpi_env_compliance_return
ORDER BY AREA, SUBJECT
```

### Air Quality Query
```sql
SELECT YEAR, MONTH, POLLUTANT, STATION, VALUE
FROM kpi_env_monitoring_report
WHERE YEAR = 2026 AND MONTH = 'Jan'
ORDER BY STATION, POLLUTANT
```

### Industrial Waste Query
```sql
SELECT YEAR, MONTH, PRODUCTION_MT, SLAG_MT, GCP_DUST_MT
FROM kpi_env_slag_gcp_dust_data
WHERE YEAR = '2026' AND MONTH = 'January'
```

### Biomedical Waste Query
```sql
SELECT DATE, PLANT, CONTAINER_TYPE, GENERETED_GRAMS, DISPOSED_GRAMS, STOCK_GRAMS
FROM kpi_env_biomedical_waste_data
WHERE DATE = '2026-01-15'
ORDER BY CONTAINER_TYPE
```

### Training Records Query
```sql
SELECT DATE, PLANT, TRAINING_NAME, TRAINER_NAME, ATTENDEES_COUNT
FROM kpi_env_training_records
WHERE DATE >= '2026-01-01' AND DATE <= '2026-01-15'
ORDER BY DATE
```

### Horticulture Query
```sql
SELECT DATE, PLANT, AREA, PLANT_NAME, TARGET, ACTUAL, REMARKS
FROM kpi_env_horticulture_plantation
WHERE DATE >= '2026-01-01' AND DATE <= '2026-01-15'
ORDER BY PLANT_NAME, AREA
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

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No data displayed | Check if data exists for the requested date in the relevant tables |
| Compliance score wrong | Verify `COMPLIANCE_STATUS` column values (should contain "submitted" or "complied") |
| Air quality data stale | Air quality is monthly; check `kpi_env_monitoring_report` for the current month |
| License status incorrect | Check `VALID_UPTO` date format (should be YYYY-MM-DD) |
| CBAM showing N/A | Verify `env_cbam` table has data for the requested date range |
| Food waste per person high | Check if `PERSONS_COUNT` is accurately recorded for all locations |
| STP anomaly false positive | Adjust anomaly threshold (currently 1.2x average) |
| Industrial waste missing | Data is monthly; check if current month exists in `kpi_env_slag_gcp_dust_data` |
| Biomedical waste balance wrong | Check `STOCK_GRAMS` calculation: `cumulative_generated - cumulative_disposed` |

---

## Contact

**Department Lead**: @env-lead
**Branch**: `dept/env`

For questions or issues, contact the BAL-Agentic-Backend Team.
