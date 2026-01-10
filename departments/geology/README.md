# Geology & Mines Department Dashboard

## Overview

The Geology dashboard tracks ore excavation, quality analysis, and mining operations across multiple locations.

## Metrics Tracked

### Excavation Metrics
- **Daily Excavation** - Total ore extracted (MT)
- **Total Trips** - Number of hauler trips
- **Average Load** - MT per trip
- **Working Days** - Actual operational days
- **Active Locations** - Number of active mining sites

### Quality Metrics
- **Avg Cr₂O₃** - Average chromium content (%)
- **Avg FeO** - Average iron oxide content (%)
- **Cr:Fe Ratio** - Quality indicator
- **Grade Classification** - High/Medium/Low grade

### Performance Metrics
- **MTD Achievement** - % of monthly target
- **Daily Average** - Average excavation per day
- **Samples Analyzed** - Number of quality tests performed

## Grade Classification

- **High Grade**: Cr₂O₃ ≥ 52%
- **Medium Grade**: 40% ≤ Cr₂O₃ < 52%
- **Low Grade**: Cr₂O₃ < 40%

## Data Sources

### Database Tables

1. **mines_day_wise_excavation** - Daily excavation records
   - Columns: `Prod_date`, `Shift`, `Loc_Id`, `Variant`, `Agency`, `No_Of_trips`, `Qty`
   - **Note**: `Qty` column stores strings like "312 Mt", "564 CuM" - needs parsing

2. **mines_geology_face_sample_analysis** - Quality analysis
   - Columns: `Prod_date`, `Loc_Id`, `SAMPLE_ID`, `Cr2O3`, `FeO`, `Ratio`

3. **mines_monthly_excavation_plan** - Monthly targets
   - Columns: `Month`, `Year`, `Planned_Qty`

4. **mines_location_master** - Mining location details
   - Columns: `Loc_Id`, `Location_Name`, `Status`

## File Structure

```
departments/geology/
├── formatter.py           # Data processing
├── template_engine.py     # HTML generation
├── claude_analyzer.py     # AI insights (optional)
└── README.md             # This file
```

## Key Implementation Details

### Excavation Data Parsing

**Issue**: Database stores excavation as strings with units ("312 Mt", "564 CuM")

**Solution**: `safe_float()` function in `formatter.py:60-82`

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

### Working Days Calculation

**Method**: Count unique dates with actual data

```python
working_days = len(set(r.get('Prod_date') for r in excavation_data))
```

**Note**: This counts ACTUAL working days, not calendar days or business days.

Example:
- Date range: Dec 10-24, 2025 (15 calendar days)
- Actual working days with data: 8 days
- Dashboard shows: **8 working days** ✓

## Development

### Testing

```bash
# Test geology dashboard generation
python app_main.py geology 2025-12-24

# Test date range
python app_main.py geology 2025-12-10 2025-12-24

# Test safe_float parsing
python test_safe_float.py
```

### Common Issues

**Issue 1: Working days showing incorrect count**

Check if you're using:
- ❌ `days_in_range` (calendar days)
- ❌ Business days calculation
- ✅ `len(set(dates_with_data))` (actual working days)

**Issue 2: Excavation totals wrong**

Check:
- Is `safe_float()` being used? ✓
- Are you handling `None` values? ✓
- Are you parsing units correctly? ✓

**Issue 3: Grade classification not showing**

Check:
- Cr₂O₃ values are being read correctly
- Threshold comparisons (52%, 40%)
- Default handling when no samples

## Adding New Features

### Example: Add Location-wise Efficiency

1. **Query data** (`formatter.py`):
```python
def _build_location_efficiency(self, data: List[Dict]) -> Dict:
    location_data = defaultdict(lambda: {"qty": 0, "trips": 0})

    for record in data:
        loc_id = record['Loc_Id']
        location_data[loc_id]["qty"] += safe_float(record['Qty'])
        location_data[loc_id]["trips"] += safe_int(record['No_Of_trips'])

    # Calculate efficiency (MT/trip)
    for loc_id, values in location_data.items():
        values["efficiency"] = values["qty"] / values["trips"] if values["trips"] > 0 else 0

    return dict(location_data)
```

2. **Add to analysisData**:
```python
"location_efficiency": self._build_location_efficiency(excavation_data)
```

3. **Update template** to display chart

## Contact

**Department Lead**: @geology-lead
**Branch**: `dept/geology`

For questions or issues, create a GitHub issue with label `geology`.
