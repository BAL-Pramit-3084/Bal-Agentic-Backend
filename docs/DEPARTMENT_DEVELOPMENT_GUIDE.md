# Department Development Guide

## Overview

This guide explains how each department developer can work independently on their dashboard without breaking other departments' code.

## Your Department Files

Each department has **exactly 3 Python files** you own:

```
departments/<your-dept>/
├── formatter.py          # Data processing & business logic
├── template_engine.py    # HTML generation from template
└── claude_analyzer.py    # AI insights (optional)
```

### 1. `formatter.py` - Data Processing

**Purpose**: Query database, process data, build `analysisData` dictionary

**What you do**:
- Query your tables from database
- Calculate KPIs, metrics, aggregations
- Build the `analysisData` structure
- Return a dictionary that template_engine will use

**Template**:
```python
"""
<Department> Data Processor
Handles all data querying and processing for <Department> dashboard
"""
import logging
from typing import Dict, List, Any
from datetime import datetime
from core.mcp_server import MCPServer

logger = logging.getLogger(__name__)

class <Department>DataProcessor:
    """Process <department> data for dashboard"""

    def __init__(self, mcp: MCPServer, database: str = "balcorpdb"):
        self.mcp = mcp
        self.database = database

    def process_single_date(self, date: str) -> Dict[str, Any]:
        """
        Process data for a single date.

        Args:
            date: Date string in YYYY-MM-DD format

        Returns:
            Dictionary with structure:
            {
                "date": "2025-12-24",
                "formatted_date": "December 24, 2025",
                "today_kpis": {...},
                "mtd_kpis": {...},
                "charts": {...}
            }
        """
        # 1. Parse date
        date_obj = datetime.strptime(date, '%Y-%m-%d')

        # 2. Query your tables
        data_today = self._query_data(date, date)
        data_mtd = self._query_data(f"{date[:7]}-01", date)

        # 3. Build analysis data
        return {
            "date": date,
            "formatted_date": date_obj.strftime("%B %d, %Y"),
            "today_kpis": self._build_today_kpis(data_today),
            "mtd_kpis": self._build_mtd_kpis(data_mtd),
            "charts": self._build_charts(data_today, data_mtd),
        }

    def process_date_range(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Process data for a date range"""
        # Similar structure but aggregated across range
        pass

    def _query_data(self, start_date: str, end_date: str) -> List[Dict]:
        """Query your department tables"""
        query = f"""
            SELECT * FROM your_table
            WHERE date >= '{start_date}' AND date <= '{end_date}'
        """
        result = self.mcp.query(sql=query, database=self.database)
        return result['data'] if result['success'] else []

    def _build_today_kpis(self, data: List[Dict]) -> Dict[str, Any]:
        """Build today's KPIs"""
        return {
            "metric1": {"value": 123, "formatted": "123"},
            "metric2": {"value": 456.7, "formatted": "456.7"},
        }
```

### 2. `template_engine.py` - HTML Generation

**Purpose**: Take template HTML + analysisData, inject data, return final HTML

**What you do**:
- Read your department's template file
- Use regex to find placeholders
- Replace placeholders with actual data
- Return complete HTML

**Template**:
```python
"""
<Department> Template Engine
Generates HTML dashboard from template + data
"""
import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)

class <Department>TemplateEngine:
    """Generate HTML dashboard from template"""

    def __init__(self, template_path: str = "templates/<dept>_dashboard.html"):
        self.template_path = template_path

    def generate_dashboard(self, analysis_data: Dict[str, Any],
                          claude_insights_html: str = "",
                          date: str = None) -> str:
        """
        Generate complete HTML dashboard.

        Args:
            analysis_data: Data from formatter.py
            claude_insights_html: AI insights HTML (optional)
            date: Display date

        Returns:
            Complete HTML string
        """
        # 1. Read template
        with open(self.template_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # 2. Inject date/title
        html = self._inject_header(html, analysis_data)

        # 3. Inject KPIs
        html = self._inject_kpis(html, analysis_data)

        # 4. Inject analysisData JavaScript
        html = self._inject_analysis_data(html, analysis_data)

        # 5. Inject AI insights (if provided)
        if claude_insights_html:
            html = self._inject_insights(html, claude_insights_html)

        return html

    def _inject_header(self, html: str, data: Dict) -> str:
        """Inject date and title"""
        pattern = r'(<h2>Dashboard - )[^<]+(</h2>)'
        replacement = f"\\g<1>{data.get('formatted_date', 'N/A')}\\g<2>"
        return re.sub(pattern, replacement, html, count=1)

    def _inject_kpis(self, html: str, data: Dict) -> str:
        """Inject KPI values"""
        kpis = data.get('today_kpis', {})

        # Example: Replace metric1 value
        pattern = r'(<div class="kpi-value">)[^<]+(</div><!--metric1-->)'
        value = kpis.get('metric1', {}).get('formatted', '0')
        html = re.sub(pattern, f"\\g<1>{value}\\g<2>", html, count=1)

        return html

    def _inject_analysis_data(self, html: str, data: Dict) -> str:
        """Inject JavaScript analysisData object"""
        import json

        # Find the analysisData placeholder
        pattern = r'const analysisData = \{[^}]+\};'

        # Convert data to JSON
        json_data = json.dumps(data, indent=2, default=str)

        # Replace
        replacement = f"const analysisData = {json_data};"
        html = re.sub(pattern, replacement, html, count=1, flags=re.DOTALL)

        return html
```

### 3. `claude_analyzer.py` - AI Insights (Optional)

**Purpose**: Generate AI-powered insights using LLM

**What you do**:
- Take analysisData
- Build prompt for LLM
- Call LLM API
- Return HTML with insights

**Template**:
```python
"""
<Department> AI Insights Generator
"""
import logging
from typing import Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)

class <Department>InsightsGenerator:
    """Generate AI insights for <department>"""

    def __init__(self, api_key: str, model: str, base_url: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def generate_insights(self, analysis_data: Dict[str, Any]) -> str:
        """
        Generate AI insights HTML.

        Args:
            analysis_data: Data from formatter

        Returns:
            HTML string with insights
        """
        try:
            # Build prompt
            prompt = self._build_prompt(analysis_data)

            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            insights_html = response.choices[0].message.content

            # Clean up markdown artifacts
            insights_html = self._clean_markdown(insights_html)

            return insights_html

        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return self._generate_fallback_insights(analysis_data)

    def _build_prompt(self, data: Dict) -> str:
        """Build LLM prompt"""
        import json
        data_json = json.dumps(data, indent=2, default=str)

        return f"""Analyze <department> data and generate 5-6 actionable insights.

DATA:
{data_json}

OUTPUT FORMAT (Pure HTML - NO markdown):

<div class="insights-section">
    <div class="insights-title">💡 Key Insights</div>
    <div class="insight-item">
        <span class="insight-icon">📊</span>
        <div><strong>Metric 1:</strong> [Insight with specific numbers]</div>
    </div>
    <!-- More insights -->
</div>

RULES:
- Use actual numbers from data
- Be specific and actionable
- Pure HTML only - NO markdown
"""

    def _clean_markdown(self, html: str) -> str:
        """Remove markdown code fences"""
        html = html.strip()
        if html.startswith('```html'):
            html = html[7:]
        if html.startswith('```'):
            html = html[3:]
        if html.endswith('```'):
            html = html[:-3]
        return html.strip()
```

## Your Template File

Location: `templates/<your_dept>_dashboard.html`

**Key Sections**:

1. **Header** - Date display
2. **KPI Cards** - Top metrics
3. **Charts Section** - Visualizations
4. **AI Insights** - LLM analysis
5. **JavaScript** - `analysisData` object + chart rendering

**Important placeholders**:

```html
<!-- Date -->
<h2>Dashboard - {{DATE}}</h2>

<!-- KPI Values -->
<div class="kpi-value">{{METRIC1}}</div><!--metric1-->

<!-- AI Insights -->
<div id="claude-insights">
    {{CLAUDE_INSIGHTS}}
</div>

<!-- analysisData JavaScript -->
<script>
const analysisData = {{ANALYSIS_DATA}};
</script>
```

## How to Modify Shared Files

### Scenario 1: Need to add a new API endpoint

**File**: `app_main.py`

**Process**:
1. Create issue: "Need new endpoint for furnace hourly data"
2. Create branch: `feat/furnace-hourly-endpoint`
3. Add minimal code to `app_main.py`:

```python
# In app_main.py, find the department routes section

@app.route('/api/v1/furnace/hourly', methods=['GET'])
@jwt_required
def furnace_hourly_data():
    """Furnace hourly breakdown endpoint"""
    try:
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))

        # Import your processor
        from departments.furnace.formatter import FurnaceDataProcessor
        from core.mcp_server import MCPServer

        mcp = MCPServer()
        processor = FurnaceDataProcessor(mcp)

        # Call YOUR method (add this to formatter.py first)
        data = processor.get_hourly_breakdown(date)

        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"Error in furnace hourly: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
```

4. Submit PR with clear description
5. Tag tech lead for review

### Scenario 2: Need to update department_config.json

**File**: `dashboards/department_config.json`

**Process**:
1. Create branch: `feat/furnace-config-update`
2. Edit ONLY your department section:

```json
{
  "furnace": {
    "name": "Furnace Operations",
    "enabled": true,
    "features": {
      "ai_insights": true,
      "date_range": true,
      "hourly_breakdown": true  // <-- NEW
    }
  }
}
```

3. Submit PR
4. Coordinate with other departments if conflict

## Testing Your Changes

### 1. Unit Test Your Processor

```python
# tests/test_furnace.py
import pytest
from departments.furnace.formatter import FurnaceDataProcessor
from core.mcp_server import MCPServer

def test_furnace_processor():
    mcp = MCPServer()
    processor = FurnaceDataProcessor(mcp)

    data = processor.process_single_date('2025-12-24')

    assert 'today_kpis' in data
    assert 'mtd_kpis' in data
    assert data['today_kpis']['production']['value'] >= 0
```

### 2. Test Dashboard Generation

```bash
# Generate test dashboard
python app_main.py furnace 2025-12-24

# Check output
ls generated_dashboards/
```

### 3. Check for Breaking Changes

```bash
# Ensure other departments still work
python app_main.py geology 2025-12-24
python app_main.py qc 2025-12-24
```

## Common Issues & Solutions

### Issue 1: Import Error

```
ImportError: cannot import name 'FurnaceDataProcessor'
```

**Solution**: Check your class name matches filename
```python
# departments/furnace/formatter.py
class FurnaceDataProcessor:  # Must match
```

### Issue 2: Merge Conflict in app_main.py

```
<<<<<<< HEAD
# Their code
=======
# Your code
>>>>>>> dept/furnace
```

**Solution**: Contact tech lead, DO NOT resolve alone

### Issue 3: Template Not Found

```
FileNotFoundError: templates/furnace_dashboard.html
```

**Solution**: Check template exists and path is correct
```python
template_path = "templates/furnace_dashboard.html"  # Relative to project root
```

## Best Practices

1. **Keep your department isolated** - Don't import other departments
2. **Document your functions** - Use docstrings
3. **Handle errors gracefully** - Try-except with fallbacks
4. **Test before pushing** - Generate dashboards locally
5. **Commit often** - Small, focused commits
6. **Write clear commit messages** - `feat(furnace): add hourly breakdown`

## Getting Help

- **Git issues**: Tag @tech-lead
- **Database queries**: Check `core/mcp_server.py` examples
- **Template questions**: Look at `templates/furnace_dashboard.html`
- **API questions**: Read `app_main.py` route handlers

---

**Next Steps**:
1. Clone the repo
2. Create your department branch
3. Make your first change
4. Test locally
5. Submit your first PR

Good luck! 🚀
