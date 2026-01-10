# Migration Plan: Daily Dashboard → Date Range Dashboard

**Date**: January 8, 2026
**Objective**: Convert all department dashboards from single-day to date range (from/to) functionality
**Departments Affected**: Geology, QC, SCM (and potentially others)

---

## 📋 Current Architecture Analysis

### Current Flow (Single Date):
1. **API Endpoint**: `/api/v1/dashboard/<dept_id>?date=YYYY-MM-DD`
2. **Processing**: `processor.process_date(date_str)`
3. **Data Structure**: Returns `today_kpis`, `mtd_kpis`, etc.
4. **Template**: Displays single date with MTD calculations

### Files Per Department (3 files each):
```
departments/<dept>/
├── formatter.py          # Data processor with process_date() method
├── claude_analyzer.py    # AI insights generator
└── template_engine.py    # HTML template renderer
```

### Example Department Structure (Geology):
- **formatter.py**: `GeologySurveyDataProcessor.process_date(date)`
  - Queries database for single date
  - Calculates MTD from month_start to date
  - Returns `today_kpis` and `mtd_kpis`

- **claude_analyzer.py**: `ClaudeInsightsGenerator.generate_insights(data, date)`
  - Receives single date data
  - Generates 8 insight cards

- **template_engine.py**: `GeologySurveyTemplateEngine.generate_dashboard(data, insights, date)`
  - Replaces template placeholders
  - Single date display logic

---

## 🎯 Target Architecture (Date Range)

### New Flow:
1. **API Endpoint**: `/api/v1/dashboard/<dept_id>?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
2. **Processing**: `processor.process_date_range(start_date, end_date)`
3. **Data Structure**: Returns `period_kpis` (aggregated over range)
4. **Template**: Displays date range with aggregated metrics

### Key Changes:

#### 1. **API Layer Changes** (`app_main.py`)
```python
# OLD
date_str = request.args.get('date')
analysis_data = processor.process_date(date_str)

# NEW
start_date = request.args.get('start_date')
end_date = request.args.get('end_date')
analysis_data = processor.process_date_range(start_date, end_date)
```

#### 2. **Formatter Changes** (Each `departments/<dept>/formatter.py`)

**Add new method**:
```python
def process_date_range(self, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Process data for a date range instead of single day.

    Returns:
        - period_kpis: Aggregated metrics for the entire period
        - daily_breakdown: Day-by-day breakdown within range
        - has_data: Boolean flag
    """
```

**Key Differences**:
- **Query changes**: `WHERE Prod_date >= start_date AND Prod_date <= end_date`
- **KPI structure**:
  - Replace `today_kpis` → `period_kpis` (aggregated totals)
  - Remove `mtd_kpis` (no longer relevant)
  - Add `daily_breakdown` (optional day-by-day view)
- **Calculations**:
  - Total excavation across all days in range
  - Average daily production = total / working_days
  - Quality metrics averaged across all samples in range

#### 3. **Analyzer Changes** (Each `departments/<dept>/claude_analyzer.py`)

**Minimal changes needed**:
```python
def generate_insights(self, analysis_data: Dict[str, Any], date_range: str) -> str:
    # Change prompt to reference "period" instead of "today"
    # Update metrics extraction: period_kpis instead of today_kpis
```

#### 4. **Template Engine Changes** (Each `departments/<dept>/template_engine.py`)

**Key Updates**:
```python
def generate_dashboard(self, analysis_data: Dict, insights: str, date_range: str) -> str:
    # Update title: "Dec 16-22, 2025" instead of "Dec 22, 2025"
    # Change KPI labels: "Period Total" instead of "Today's Production"
    # Update all references: period_kpis instead of today_kpis
    # Remove MTD section entirely (no longer needed)
```

---

## 🔧 Implementation Strategy (Step-by-Step)

### Phase 1: Add Range Support (Backwards Compatible)
**Goal**: Add new method without breaking existing functionality

For each department (Geology, QC, SCM):

1. **formatter.py**:
   - ✅ Keep existing `process_date()` method
   - ➕ Add new `process_date_range()` method
   - 🔧 Refactor common query logic into helper methods

2. **claude_analyzer.py**:
   - ✅ Keep existing `generate_insights(data, date)` signature
   - 🔧 Make it work with both `today_kpis` and `period_kpis`

3. **template_engine.py**:
   - ✅ Keep existing template
   - ➕ Create new range-specific template (or make existing template adaptive)

### Phase 2: Update API Endpoint
**Goal**: Support both old and new request formats

```python
@app.route('/api/v1/dashboard/<dept_id>', methods=['GET'])
@smart_auth
def generate_dashboard(dept_id: str):
    # Support both formats:
    # OLD: ?date=YYYY-MM-DD
    # NEW: ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD

    date_str = request.args.get('date')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if date_str:
        # Use old single-date logic
        analysis_data = processor.process_date(date_str)
    elif start_date and end_date:
        # Use new range logic
        analysis_data = processor.process_date_range(start_date, end_date)
    else:
        return error_response()
```

### Phase 3: Migrate Department by Department
**Order**: Geology → QC → SCM

For each department:
1. Test `process_date_range()` independently
2. Verify data aggregation is correct
3. Update insights generation
4. Test template rendering
5. Deploy and monitor

### Phase 4: Deprecate Old Endpoint (Optional)
- After all departments migrated
- Frontend updated to use range format
- Remove `process_date()` methods

---

## 📊 Data Structure Comparison

### OLD (Single Date):
```python
{
    "date": "2025-12-22",
    "date_formatted": "Monday, December 22, 2025",
    "today_kpis": {
        "excavation": {"value": 1500, "formatted": "1,500"},
        "trips": {"value": 100, "formatted": "100"},
        # ... more today metrics
    },
    "mtd_kpis": {
        "total_excavation": {"value": 30000, "formatted": "30,000"},
        "working_days": {"value": 20, "formatted": "20"},
        # ... more MTD metrics
    },
    "shift_breakdown": [...],  # Today's shifts
    "daily_trend": [...]        # T-12 to T
}
```

### NEW (Date Range):
```python
{
    "start_date": "2025-12-16",
    "end_date": "2025-12-22",
    "date_range_formatted": "December 16-22, 2025",
    "period_kpis": {
        "total_excavation": {"value": 10500, "formatted": "10,500"},
        "total_trips": {"value": 700, "formatted": "700"},
        "working_days": {"value": 7, "formatted": "7"},
        "avg_daily_production": {"value": 1500, "formatted": "1,500"},
        "avg_cr2o3": {"value": 51.2, "formatted": "51.2%"},
        # ... aggregated metrics for entire period
    },
    "daily_breakdown": [
        {"date": "2025-12-16", "excavation": 1400, "trips": 95, ...},
        {"date": "2025-12-17", "excavation": 1550, "trips": 102, ...},
        # ... one entry per day in range
    ],
    "shift_breakdown": [...],     # Aggregated across all days in range
    "location_breakdown": [...],  # Aggregated across all days
    "quality_stats": {...}        # Averaged across all samples in range
}
```

---

## 🚨 Breaking Changes & Migration Risks

### High Risk Areas:
1. **Frontend Dependencies**:
   - Any frontend code expecting `today_kpis` will break
   - Need coordination with frontend team

2. **Existing Dashboards**:
   - Saved dashboard URLs with `?date=` will need redirect logic

3. **Database Query Performance**:
   - Range queries may be slower than single-date queries
   - Need indexes on date columns

### Mitigation Strategies:
1. **Dual Support Period**: Keep both endpoints active for 1 month
2. **Data Validation**: Add comprehensive unit tests
3. **Performance Testing**: Benchmark range queries
4. **Rollback Plan**: Keep old code in comments

---

## ✅ Testing Checklist

For each department migration:

### Unit Tests:
- [ ] `process_date_range()` returns correct structure
- [ ] Empty date ranges handled gracefully
- [ ] Single-day range equals `process_date()` output
- [ ] Large ranges (30+ days) perform acceptably

### Integration Tests:
- [ ] API endpoint accepts new parameters
- [ ] Dashboard generates successfully
- [ ] AI insights reference correct metrics
- [ ] HTML template renders properly

### Edge Cases:
- [ ] start_date > end_date (should error)
- [ ] Future dates (should error or return no data)
- [ ] Leap year boundaries
- [ ] Month/year boundaries

---

## 📝 Sample Implementation (Geology Department)

### Step 1: Add `process_date_range()` to `formatter.py`

```python
def process_date_range(self, start_date: str, end_date: str) -> Dict[str, Any]:
    """Process data for date range."""
    logger.info(f"Processing Geology data for range: {start_date} to {end_date}")

    # Validate dates
    start_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_obj = datetime.strptime(end_date, '%Y-%m-%d')

    if start_obj > end_obj:
        raise ValueError("start_date must be before end_date")

    # Query data for entire range
    excavation_data = self._query_excavation(start_date, end_date)
    sample_data = self._query_sample_analysis(start_date, end_date)

    # Build period KPIs (aggregated)
    period_kpis = self._build_period_kpis(excavation_data, sample_data)

    # Build daily breakdown
    daily_breakdown = self._build_daily_breakdown(excavation_data, sample_data)

    return {
        "start_date": start_date,
        "end_date": end_date,
        "date_range_formatted": self._format_date_range(start_obj, end_obj),
        "period_kpis": period_kpis,
        "daily_breakdown": daily_breakdown,
        "shift_breakdown": self._build_shift_breakdown(excavation_data),
        "location_breakdown": self._build_location_breakdown(excavation_data),
        "has_data": len(excavation_data) > 0
    }

def _build_period_kpis(self, excavation_data, sample_data):
    """Aggregate KPIs across entire period."""
    total_qty = sum(safe_float(r.get('Qty')) for r in excavation_data)
    total_trips = sum(safe_int(r.get('No_Of_trips')) for r in excavation_data)
    working_days = len(set(r.get('Prod_date') for r in excavation_data))
    avg_daily = total_qty / working_days if working_days > 0 else 0

    # Quality metrics (averaged)
    cr2o3_values = [safe_float(r.get('Cr2O3')) for r in sample_data if r.get('Cr2O3')]
    avg_cr2o3 = sum(cr2o3_values) / len(cr2o3_values) if cr2o3_values else 0

    return {
        "total_excavation": {"value": total_qty, "formatted": format_number(total_qty)},
        "total_trips": {"value": total_trips, "formatted": format_number(total_trips)},
        "working_days": {"value": working_days, "formatted": str(working_days)},
        "avg_daily_production": {"value": avg_daily, "formatted": format_number(avg_daily)},
        "avg_cr2o3": {"value": avg_cr2o3, "formatted": f"{avg_cr2o3:.1f}%"},
    }
```

### Step 2: Update API Handler in `app_main.py`

```python
def _generate_geology_dashboard_internal(user, ip_address: str, start_date: str, end_date: str):
    """Internal helper for Geology dashboard (DATE RANGE version)."""
    try:
        logger.info(f"GEOLOGY dashboard request: {start_date} to {end_date}, user={user.user_id}")

        # STEP 1: Process data using NEW range method
        processor = GeologyDataProcessor(mcp_server)
        analysis_data = processor.process_date_range(start_date, end_date)

        if not analysis_data.get('has_data'):
            return jsonify({
                'success': False,
                'error': 'NO_DATA',
                'message': f'No data found for {start_date} to {end_date}'
            }), 404

        # STEP 2: Generate AI insights
        date_range_label = f"{start_date} to {end_date}"
        insights_generator = GeologyClaudeInsightsGenerator(...)
        insights_html = insights_generator.generate_insights(analysis_data, date_range_label)

        # STEP 3: Generate HTML
        template_engine = GeologyTemplateEngine()
        html_content = template_engine.generate_dashboard(
            analysis_data,
            insights_html,
            date_range_label
        )

        # ... save and return
```

---

## 🎯 Success Criteria

1. ✅ All 3 departments (Geology, QC, SCM) support date ranges
2. ✅ API accepts both old and new formats during transition
3. ✅ Dashboards display aggregated metrics correctly
4. ✅ Performance is acceptable (< 5 seconds for 30-day range)
5. ✅ No data loss or corruption
6. ✅ AI insights adapt to range data
7. ✅ Comprehensive test coverage (>80%)

---

## 📅 Estimated Timeline

- **Phase 1 (Geology)**: 2-3 days
  - Day 1: Add `process_date_range()` + tests
  - Day 2: Update analyzer + template
  - Day 3: Integration testing

- **Phase 2 (QC)**: 1-2 days (pattern established)
- **Phase 3 (SCM)**: 1-2 days
- **Phase 4 (API Update)**: 1 day
- **Phase 5 (Testing & QA)**: 2 days

**Total**: ~7-10 days

---

## 🔄 Rollback Plan

If issues arise:
1. Revert API endpoint to single-date only
2. Keep `process_date_range()` methods for future use
3. Restore old template files from git
4. Communicate downtime to users

---

## 📞 Questions for Clarification

Before proceeding, please confirm:

1. **Date Range Limits**: Maximum allowed range? (e.g., 90 days)
2. **Default Behavior**: If no dates provided, use today? Last 7 days?
3. **Frontend Impact**: Is frontend team ready to consume new API format?
4. **Performance Requirements**: Acceptable load time for dashboards?
5. **Backward Compatibility**: How long to support old `?date=` format?
6. **Other Departments**: Do Furnace, CRM, ENV, Automobile also need ranges?

---

**End of Plan**
