# Automobile Department Dashboard

## Overview

This module generates comprehensive dashboards for the **Automobile/Fleet Department** at Balasore Alloys Limited. It tracks vehicle operations, fuel consumption, trip management, and fleet performance metrics for a fleet of **35 MAN trucks**.

## File Structure

```
departments/automobile/
├── __init__.py           # Module exports (AutomobileDataProcessor, AutomobileTemplateEngine, AutomobileInsightsGenerator)
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
GET /api/v1/dashboard/automobile?date=2026-01-15

# Date range dashboard:
GET /api/v1/dashboard/automobile?start_date=2026-01-01&end_date=2026-01-15
```

### Template Location
`templates/automobile_dashboard.html`

---

## Database Table Schema

### Table: `truck_reports`

**Description:** Daily trip data for MAN trucks with telematics data (engine hours, motion hours, idle hours, fuel consumption, distance traveled, speed metrics).

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `slNo` | int | PRI | NO | Serial/truck number |
| `tripDate` | date | PRI | NO | Trip recording date |
| `vehicle_desc` | varchar(100) | - | YES | Vehicle description (e.g., "MAN-01") |
| `engine_hours` | time | - | YES | Total engine running hours (HH:MM:SS) |
| `in_motion_engine_hours` | time | - | YES | Hours when truck was in motion |
| `idling_engine_hours` | time | - | YES | Hours when engine was idling (no motion) |
| `avg_speed` | float | - | YES | Average speed (km/h) |
| `max_speed` | varchar(10) | - | YES | Maximum speed (format: "30 k" or "45") |
| `distance` | float | - | YES | Total distance traveled (km) |
| `fuel_consumed` | float | - | YES | Fuel consumed (liters) |
| `kmpl` | float | - | YES | Kilometers per liter (mileage) |
| `parkings_hours` | time | - | YES | Total parking/stationary time |
| `initial_fuel_level` | float | - | YES | Fuel level at day start (liters) |
| `final_fuel_level` | float | - | YES | Fuel level at day end (liters) |
| `total_fillings` | int | - | YES | Number of fueling events |
| `total_drains` | int | - | YES | Number of drain events (theft detection) |
| `filled` | float | - | YES | Total fuel filled (liters) |
| `drained` | float | - | YES | Total fuel drained (liters) |

**Primary Key:** (`slNo`, `tripDate`)

**Statistics:** ~5,303 rows, 1.52 MB

---

## Key Files Explained

### 1. `formatter.py` - AutomobileDataProcessor

The main data processor that queries the `truck_reports` table and builds the analysis data structure (~1,200 lines).

#### Key Constants

```python
# Fleet configuration
TOTAL_FLEET_SIZE = 35  # Total MAN trucks in fleet
ASSUMED_TANK_CAPACITY = 170  # Liters - for fuel gauge percentage

# Idle time thresholds
IDLE_THRESHOLDS = {
    "high": 50,      # >= 50% idle is HIGH (danger)
    "medium": 35,    # >= 35% idle is MEDIUM (warning)
    "low": 0         # < 35% idle is LOW (good)
}

# Fuel level thresholds
FUEL_LEVEL_THRESHOLDS = {
    "high": 100,     # > 100L is HIGH
    "medium": 50,    # 50-100L is MEDIUM
    "low": 0         # < 50L is LOW (critical)
}

# Mileage (KMPL) thresholds
MILEAGE_THRESHOLDS = {
    "excellent": 0.9,   # >= 0.9 KMPL (green)
    "good": 0.7,        # >= 0.7 KMPL (yellow-green)
    "poor": 0.5,        # >= 0.5 KMPL (yellow)
    "critical": 0       # < 0.5 KMPL (red)
}

# Anomaly detection
MAX_VALID_KMPL = 10  # Anything above this is sensor malfunction
MIN_VALID_FUEL_CONSUMED = 0.1  # Minimum to consider valid consumption
```

#### Helper Functions

```python
def time_to_hours(time_value: Any) -> float:
    """
    Convert TIME field (HH:MM:SS or timedelta) to decimal hours.
    Example: "2:30:00" → 2.5 hours
    """

def format_time_display(time_value: Any) -> str:
    """Format TIME field for display as "H:MM" or "HH:MM"."""

def parse_max_speed(speed_value: Any) -> int:
    """Parse max_speed from various formats like "30 k", "30", "0"."""

def calculate_idle_percentage(engine_hours: float, idle_hours: float) -> float:
    """Calculate idle percentage: (idle_hours / engine_hours) * 100"""

def get_idle_category(idle_pct: float) -> Tuple[str, str]:
    """Get idle category and CSS class based on percentage."""

def get_fuel_status(fuel_level: float) -> Tuple[str, str, bool]:
    """Get fuel status category, CSS class, and critical flag."""

def get_mileage_badge(kmpl: float, fuel_consumed: float) -> Tuple[str, str, bool]:
    """Get mileage badge class, display value, and anomaly flag."""
```

#### Key Methods

| Method | Source Table | Description |
|--------|--------------|-------------|
| `process_date(date)` | `truck_reports` | Main entry point for single-date processing |
| `process_date_range(start_date, end_date)` | `truck_reports` | Process date range with aggregations |
| `_query_day_data(date)` | `truck_reports` | Query all truck data for a specific date |
| `_query_mtd_data(start, end)` | `truck_reports` | Query aggregated MTD data |
| `_query_mtd_by_truck(start, end)` | `truck_reports` | Query MTD totals grouped by truck |
| `_query_trend_data(end_date, days)` | `truck_reports` | Query daily aggregates for trend charts |
| `_build_kpis(today, yesterday)` | - | Build daily KPI metrics (8 cards) |
| `_build_mtd_summary(mtd_data, by_truck)` | - | Build MTD summary (6 cards) |
| `_build_top_performers(today_data)` | - | Build top 5 trucks by distance |
| `_build_idle_analysis(today_data)` | - | Build idle time breakdown |
| `_build_truck_details(today_data)` | - | Build complete truck table data |
| `_build_idle_trucks_list(today_data)` | - | Categorize idle/unused trucks |
| `_build_chart_data(...)` | - | Build data for 4 Chart.js charts |
| `_build_alerts(today_data)` | - | Build critical alerts |

### 2. `template_engine.py` - AutomobileTemplateEngine

Injects processed data into the HTML template.

**Key Methods:**
- `generate_dashboard(analysis_data, claude_insights_html, date)` - Main entry point
- Replaces all KPI values, truck details, chart data
- Injects JavaScript data for Chart.js visualizations

### 3. `claude_analyzer.py` - AutomobileInsightsGenerator

Generates AI-powered fleet insights using OpenAI GPT-4 (or local LLM).

**Key Methods:**
- `generate_insights(analysis_data, date)` - Generates 5-6 actionable insights
- Analyzes idle patterns, fuel efficiency, sensor anomalies
- Returns formatted HTML for dashboard injection

---

## KPIs and Calculations

### Daily KPIs (8 Cards)

| KPI | Source Table | Column(s) | Calculation |
|-----|--------------|-----------|-------------|
| Fleet Utilization (%) | `truck_reports` | `distance`, `engine_hours` | `active_trucks / TOTAL_FLEET_SIZE * 100` |
| Active Trucks | `truck_reports` | `distance`, `engine_hours` | `COUNT(*)` where distance > 0 OR engine_hours > 0 |
| Total Distance (km) | `truck_reports` | `distance` | `SUM(distance)` for date |
| Fuel Consumed (L) | `truck_reports` | `fuel_consumed` | `SUM(fuel_consumed)` for date |
| Average Mileage (KMPL) | `truck_reports` | `distance`, `fuel_consumed` | `SUM(distance) / SUM(fuel_consumed)` |
| Fuel Filled (L) | `truck_reports` | `filled` | `SUM(filled)` for date |
| Max Speed (km/h) | `truck_reports` | `max_speed` | `MAX(parse_max_speed(max_speed))` |
| Fuel Drained (L) | `truck_reports` | `drained` | `SUM(drained)` for date (theft detection) |

### MTD Summary (6 Cards)

| KPI | Source Table | Column(s) | Calculation |
|-----|--------------|-----------|-------------|
| MTD Distance | `truck_reports` | `distance` | `SUM(distance)` for month |
| MTD Fuel Consumed | `truck_reports` | `fuel_consumed` | `SUM(fuel_consumed)` for month |
| MTD Fuel Filled | `truck_reports` | `filled` | `SUM(filled)` for month |
| MTD Fuel Drained | `truck_reports` | `drained` | `SUM(drained)` for month |
| MTD Avg KMPL | `truck_reports` | `distance`, `fuel_consumed` | `mtd_distance / mtd_fuel_consumed` |
| Fuel Balance | Calculated | - | `mtd_filled - mtd_fuel_consumed` |

### Idle Analysis Section

| Metric | Source Table | Column(s) | Calculation |
|--------|--------------|-----------|-------------|
| Total Idle Hours | `truck_reports` | `idling_engine_hours` | `SUM(time_to_hours(idling_engine_hours))` |
| Avg Idle % | `truck_reports` | `engine_hours`, `idling_engine_hours` | `AVG(idle_hours / engine_hours * 100)` |
| Idle by Truck | `truck_reports` | `vehicle_desc`, `idling_engine_hours`, `engine_hours` | Per-truck idle percentage |
| Best Performer | Calculated | - | Truck with lowest idle % |

**Idle Category Logic:**
```python
if idle_pct >= 50:
    category = "High"   # CSS: danger (red)
elif idle_pct >= 35:
    category = "Medium" # CSS: warning (yellow)
else:
    category = "Low"    # CSS: success (green)
```

### Top Performers Section

| Metric | Source Table | Column(s) | Calculation |
|--------|--------------|-----------|-------------|
| Rank | Calculated | - | By distance DESC |
| Distance | `truck_reports` | `distance` | Direct value |
| Fuel Consumed | `truck_reports` | `fuel_consumed` | Direct value |
| KMPL | `truck_reports` | `kmpl` | Direct value |
| Engine Hours | `truck_reports` | `engine_hours` | Formatted as "H:MM" |

### Truck Details Table

| Metric | Source Table | Column(s) | Calculation |
|--------|--------------|-----------|-------------|
| Vehicle | `truck_reports` | `vehicle_desc` | Direct value |
| Distance | `truck_reports` | `distance` | Direct value |
| Engine Hours | `truck_reports` | `engine_hours` | `format_time_display()` |
| Motion Hours | `truck_reports` | `in_motion_engine_hours` | `format_time_display()` |
| Idle Hours | `truck_reports` | `idling_engine_hours` | `format_time_display()` |
| Idle % | Calculated | `engine_hours`, `idling_engine_hours` | `idle_hours / engine_hours * 100` |
| Fuel Consumed | `truck_reports` | `fuel_consumed` | Direct value |
| KMPL | `truck_reports` | `kmpl` | Direct value |
| Max Speed | `truck_reports` | `max_speed` | `parse_max_speed()` |
| Fuel Filled | `truck_reports` | `filled` | Direct value |
| Final Fuel Level | `truck_reports` | `final_fuel_level` | Direct value |
| Fuel Gauge % | Calculated | `final_fuel_level` | `(final_fuel_level / 170) * 100` |

### Alerts Section

| Alert Type | Source Table | Column(s) | Trigger Condition |
|------------|--------------|-----------|-------------------|
| Low Fuel | `truck_reports` | `final_fuel_level` | `0 < final_fuel_level < 50` |
| Sensor Issues | `truck_reports` | `kmpl`, `distance`, `fuel_consumed`, `engine_hours` | `kmpl > 10` OR `distance > 0 AND fuel_consumed = 0` OR `engine_hours = 0 AND distance > 0` |
| High Idle | `truck_reports` | `engine_hours`, `idling_engine_hours` | `idle_pct >= 80%` |
| Poor Mileage | `truck_reports` | `kmpl` | `0 < kmpl < 0.5 AND kmpl <= 10` |

### Anomaly Detection

| Anomaly | Detection Logic |
|---------|-----------------|
| Impossible Mileage | `kmpl > MAX_VALID_KMPL (10)` → Sensor malfunction |
| Movement without Fuel | `distance > 0 AND fuel_consumed = 0` → Fuel sensor issue |
| Distance without Engine | `engine_hours = 0 AND distance > 0` → Engine sensor issue |
| Fuel Theft | `drained > 0` → Potential fuel theft |

---

## Data Flow

```
1. API Request (/api/v1/dashboard/automobile?date=YYYY-MM-DD)
        ↓
2. AutomobileDataProcessor.process_date(date)
   - Queries truck_reports for:
     • today_data: All trucks for requested date
     • yesterday_data: All trucks for previous day (comparison)
     • mtd_data: Aggregated month-to-date metrics
     • trend_data: Last 16 days for charts
     • mtd_by_truck: MTD totals grouped by truck
   - Builds sections:
     • kpis: 8 daily KPI cards
     • mtd: 6 MTD summary cards
     • top_performers: Top 5 trucks by distance
     • idle_analysis: Idle time breakdown
     • truck_details: Complete truck table
     • idle_trucks: Categorized idle trucks
     • charts: 4 Chart.js data structures
     • alerts: Critical alerts
        ↓
3. AutomobileInsightsGenerator.generate_insights(analysis_data, date)
   - Builds data context with fleet metrics
   - Calls OpenAI GPT-4 API
   - Returns AI-generated insights HTML
        ↓
4. AutomobileTemplateEngine.generate_dashboard(...)
   - Loads automobile_dashboard.html
   - Replaces all KPI placeholders
   - Injects truck detail rows
   - Injects chart data into JavaScript
   - Injects AI insights HTML
        ↓
5. Returns complete HTML dashboard
```

---

## Sample SQL Queries Used

### Daily Truck Data Query
```sql
SELECT
    slNo, tripDate, vehicle_desc, engine_hours,
    in_motion_engine_hours, idling_engine_hours,
    avg_speed, max_speed, distance, fuel_consumed,
    kmpl, parkings_hours, initial_fuel_level,
    final_fuel_level, total_fillings, total_drains,
    filled, drained
FROM truck_reports
WHERE tripDate = '2026-01-15'
ORDER BY distance DESC
```

### MTD Aggregation Query
```sql
SELECT
    COUNT(DISTINCT vehicle_desc) as trucks_active,
    SUM(distance) as total_distance,
    SUM(fuel_consumed) as total_fuel_consumed,
    SUM(filled) as total_filled,
    SUM(drained) as total_drained,
    SUM(total_fillings) as total_filling_events,
    SUM(total_drains) as total_drain_events
FROM truck_reports
WHERE tripDate >= '2026-01-01' AND tripDate <= '2026-01-15'
AND (distance > 0 OR fuel_consumed > 0)
```

### MTD by Truck Query
```sql
SELECT
    vehicle_desc,
    SUM(distance) as mtd_distance,
    SUM(fuel_consumed) as mtd_fuel,
    COUNT(*) as trip_days
FROM truck_reports
WHERE tripDate >= '2026-01-01' AND tripDate <= '2026-01-15'
AND distance > 0
GROUP BY vehicle_desc
ORDER BY mtd_distance DESC
```

### Trend Data Query (Last 16 Days)
```sql
SELECT
    tripDate,
    SUM(distance) as total_distance,
    SUM(fuel_consumed) as total_fuel_consumed,
    SUM(filled) as total_filled,
    SUM(drained) as total_drained,
    COUNT(DISTINCT CASE WHEN distance > 0 THEN vehicle_desc END) as active_trucks
FROM truck_reports
WHERE tripDate >= '2025-12-30' AND tripDate <= '2026-01-15'
GROUP BY tripDate
ORDER BY tripDate ASC
```

---

## Charts Generated

### 1. Distance Trend Chart (Line)
- **Data:** Last 16 days of total fleet distance
- **Source:** `_query_trend_data()` → `total_distance`
- **Labels:** Date formatted as "Jan 15"

### 2. Fuel Balance Chart (Bar)
- **Data:** Daily consumed vs filled fuel
- **Source:** `_query_trend_data()` → `total_fuel_consumed`, `total_filled`
- **Type:** Grouped bar chart

### 3. Top MTD Trucks Chart (Horizontal Bar)
- **Data:** Top 10 trucks by MTD distance
- **Source:** `_query_mtd_by_truck()` → `mtd_distance`
- **Labels:** Vehicle descriptions

### 4. Mileage Performance Chart (Bar)
- **Data:** KMPL for top 15 active trucks
- **Source:** Today's data filtered for valid fuel consumption
- **Excludes:** Anomalies (KMPL > 10)

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
| No data displayed | Check if data exists for the requested date in `truck_reports` |
| Mileage showing "Sensor?" | Fuel consumed is < 0.1L - check fuel sensor |
| Mileage with asterisk (*) | KMPL > 10 indicates sensor malfunction |
| Idle percentage 0% | Check if `engine_hours` is being recorded |
| Fleet utilization wrong | Verify `TOTAL_FLEET_SIZE` constant (default: 35) |
| Time display wrong | Check `engine_hours` format (should be TIME HH:MM:SS) |
| Max speed showing 0 | Verify `max_speed` column format (e.g., "30 k") |
| Fuel theft not detected | Check `drained` column values in database |
| Trend chart empty | Verify data exists for the last 16 days |

---

## Contact

**Department Lead**: @automobile-lead
**Branch**: `dept/automobile`

For questions or issues, contact the BAL-Agentic-Backend Team.
