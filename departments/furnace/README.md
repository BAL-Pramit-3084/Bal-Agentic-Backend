# Furnace Department Dashboard

## Overview

The Furnace dashboard provides real-time monitoring and analysis of FeCr (Ferrochrome) production across multiple furnaces.

## Metrics Tracked

### Production Metrics
- **Daily Production** - Total FeCr output per furnace
- **Monthly Target** - Planned vs actual production
- **Production Rate** - Percentage of target achieved
- **Variance** - Deviation from plan

### Operational Metrics
- **Tapping Cycles** - Number of taps per shift/day
- **Tap Intervals** - Time between taps
- **OEE (Overall Equipment Effectiveness)** - Availability × Performance × Quality
- **Uptime/Downtime** - Operating hours vs breakdown hours

### Power Metrics
- **Total Power Consumption** - kWh consumed
- **Specific Power** - kWh per MT of FeCr produced
- **Power Efficiency** - Comparison against norms (3500-3700 kWh/MT)

### Recovery Metrics
- **Chromium Recovery** - % of Cr recovered from ore (target: ≥85%)
- **Slag Generation** - MT of slag per MT of FeCr (norm: 1.2-1.5)

## Data Sources

### Database Tables

1. **furnace_day_wise_production** - Daily production data
   - Columns: `Prod_Date`, `Furnace`, `Shift`, `Tapped_Qty`, `Power_Consumed`

2. **furnace_monthly_targets** - Monthly production plans
   - Columns: `Month`, `Year`, `Furnace`, `Target_Qty`

3. **furnace_tapping_log** - Tapping cycle details
   - Columns: `Tap_Datetime`, `Furnace`, `Qty_Tapped`, `Slag_Qty`

4. **furnace_downtime_log** - Breakdown/maintenance records
   - Columns: `Start_Time`, `End_Time`, `Furnace`, `Reason`, `Duration_Hours`

## File Structure

```
departments/furnace/
├── formatter.py           # Data processing & KPI calculation
├── template_engine.py     # HTML generation from template
├── claude_analyzer.py     # AI insights generation
└── README.md             # This file
```

### `formatter.py`

**Key Functions**:

- `process_single_date(date)` - Generate dashboard for specific date
- `process_date_range(start, end)` - Generate dashboard for date range
- `_build_today_kpis()` - Calculate today's metrics
- `_build_mtd_kpis()` - Calculate month-to-date metrics
- `_build_production_summary()` - Aggregate production data
- `_build_power_analysis()` - Power consumption analysis
- `_build_tapping_analysis()` - Tapping cycle analysis

**Key Calculations**:

```python
# Specific Power (kWh/MT)
specific_power = total_power_kwh / total_production_mt

# OEE (%)
oee = (uptime_hours / total_hours) * (actual_qty / target_qty) * (quality_rate)

# Cr Recovery (%)
cr_recovery = (cr_in_fecr / cr_in_ore) * 100

# Slag Ratio
slag_ratio = total_slag_mt / total_fecr_mt
```

### `template_engine.py`

**Key Functions**:

- `generate_dashboard()` - Main HTML generation
- `_inject_kpis()` - Inject KPI values into template
- `_inject_charts()` - Build chart data arrays
- `_inject_analysis_data()` - Inject JavaScript `analysisData` object

### `claude_analyzer.py`

**AI Insights**:

Generates 5-6 actionable insights covering:
1. Production performance vs targets
2. Power efficiency (specific power analysis)
3. Chromium recovery optimization
4. Operational efficiency (OEE, downtime)
5. Tapping performance
6. Slag management

## Development

### Testing

```bash
# Generate test dashboard for single date
python app_main.py furnace 2025-12-24

# Generate test dashboard for date range
python -c "from departments.furnace.formatter import FurnaceDataProcessor; from core.mcp_server import MCPServer; mcp = MCPServer(); processor = FurnaceDataProcessor(mcp); data = processor.process_date_range('2025-12-10', '2025-12-24'); print(data['period_kpis'])"

# Run unit tests
pytest tests/test_furnace.py -v
```

### Adding New Metrics

1. **Add data query** in `formatter.py`:
```python
def _query_new_metric(self, date: str) -> List[Dict]:
    query = "SELECT * FROM furnace_new_table WHERE date = %s"
    result = self.mcp.query(sql=query, database=self.database)
    return result['data']
```

2. **Calculate metric** in `_build_today_kpis()`:
```python
new_metric = sum(r['value'] for r in new_data)
```

3. **Add to analysisData**:
```python
"new_metric": {
    "value": new_metric,
    "formatted": f"{new_metric:.1f}",
    "unit": "MT"
}
```

4. **Update template** (`templates/furnace_dashboard.html`):
```html
<div class="kpi-card">
    <div class="kpi-value">{{NEW_METRIC}}</div>
    <div class="kpi-label">New Metric</div>
</div>
```

5. **Update template_engine** to inject value:
```python
pattern = r'(<div class="kpi-value">)[^<]+(</div><!--new-metric-->)'
html = re.sub(pattern, f"\\g<1>{new_metric}\\g<2>", html)
```

## Known Issues

- **Null handling**: Ensure all database values handle NULL gracefully
- **Date range edge cases**: Month boundaries require special handling
- **Power data gaps**: Some furnaces may have missing power readings

## Future Enhancements

- [ ] Hourly production breakdown
- [ ] Real-time alerts for low recovery
- [ ] Predictive maintenance indicators
- [ ] Energy cost calculations
- [ ] Comparison with industry benchmarks

## Contact

**Department Lead**: @furnace-lead
**Branch**: `dept/furnace`

For questions or issues, create a GitHub issue with label `furnace`.
