"""
qc_template_engine.py
=====================
Template engine for injecting real data into QC dashboard HTML.

COMPLETELY REWRITTEN to handle hardcoded HTML values and Chart.js data arrays.

The template has data embedded in TWO places:
1. HTML metric values (like <div class="metric-value">269<span...)
2. Chart.js data arrays (like data: [39, 18, 50, 49, 25, 38, 25, 25])

This engine replaces BOTH with real database values.

Author: Senior ML Engineer
Date: November 2025
"""

import os
import re
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# TEMPLATE PATHS
# ============================================================================

# Template is in root templates/ folder (not department subfolder)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_DIR = os.path.join(PROJECT_ROOT, "templates")
TEMPLATE_FILE = "quality_control_dashboard.html"


# ============================================================================
# QC TEMPLATE ENGINE - COMPLETE REWRITE
# ============================================================================

class QCTemplateEngine:
    """
    Inject real data into the QC dashboard template.

    This engine replaces:
    1. Date in title and header
    2. All HTML metric values
    3. All Chart.js data arrays
    4. Stock table rows
    5. Insights section with Claude HTML
    """

    def __init__(self, template_path: str = None):
        """
        Initialize template engine.

        Args:
            template_path: Optional custom path to template file
        """
        if template_path:
            self.template_path = template_path
        else:
            self.template_path = os.path.join(TEMPLATE_DIR, TEMPLATE_FILE)

        logger.info(f"QC Template engine initialized: {self.template_path}")

    def generate_dashboard(self, analysis_data: Dict[str, Any], claude_insights_html: str, date: str) -> str:
        """
        Generate complete dashboard HTML WITH real data and Claude AI insights.

        Args:
            analysis_data: The analysisData dict from QCDataProcessor
            claude_insights_html: HTML from QCClaudeInsightsGenerator
            date: Date string (YYYY-MM-DD)

        Returns:
            Complete HTML string ready to display
        """
        logger.info(f"Generating QC dashboard for date: {date}")

        # Load template
        html = self._load_template()

        # Step 1: Replace date in title and header
        html = self._replace_date(html, date, analysis_data.get('month', ''))

        # Step 2: Replace Executive Summary metrics
        html = self._replace_executive_summary(html, analysis_data)

        # Step 3: Replace Despatch Performance section
        html = self._replace_despatch_section(html, analysis_data.get('despatch', {}))

        # Step 4: Replace Product Quality section
        html = self._replace_product_quality_section(html, analysis_data.get('product_quality', {}))

        # Step 5: Replace Stock Summary table
        html = self._replace_stock_table(html, analysis_data.get('stock', {}))

        # Step 6: Replace QC Lots section
        html = self._replace_qc_lots_section(html, analysis_data.get('qc_lots', {}))

        # Step 7: Replace Heat Analysis section
        html = self._replace_heat_analysis_section(html, analysis_data.get('heat_analysis', {}))

        # Step 8: Replace Testing Results section
        html = self._replace_testing_section(html, analysis_data.get('tests', {}))

        # Step 9: Replace Chart.js data
        html = self._replace_all_charts(html, analysis_data)

        # Step 10: Replace insights section with Claude HTML
        html = self._replace_insights_section(html, claude_insights_html)

        logger.info(f"QC Dashboard generated successfully ({len(html)} characters)")
        return html

    def _load_template(self) -> str:
        """Load HTML template from file."""
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template not found: {self.template_path}")

        with open(self.template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        logger.info(f"Template loaded: {len(template)} characters")
        return template

    def _replace_date(self, html: str, date: str, month_name: str) -> str:
        """Replace date in title and header."""
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%B %d, %Y')
            day_of_week = date_obj.strftime('%A')

            # Replace title
            html = re.sub(
                r'<title>Quality Control Dashboard[^<]*</title>',
                f'<title>Quality Control Dashboard - {formatted_date}</title>',
                html
            )

            # Replace date badge (handles both div and span)
            html = re.sub(
                r'(<(?:div|span)[^>]*class="date-badge"[^>]*>)[^<]*(</(?:div|span)>)',
                rf'\g<1>📅 {formatted_date} ({day_of_week})\g<2>',
                html
            )

            # Fallback: direct string replacement
            html = re.sub(
                r'📅 [A-Za-z]+ \d{1,2}, \d{4}',
                f'📅 {formatted_date}',
                html
            )

            # Replace Product Quality date range
            if month_name:
                html = re.sub(
                    r'Product Quality \([^)]+\)',
                    f'Product Quality ({month_name[:3]} 1-{date_obj.day})',
                    html
                )

            logger.info(f"Date replaced: {formatted_date}")
            return html

        except Exception as e:
            logger.error(f"Error replacing date: {e}")
            return html

    def _replace_metric(self, html: str, label: str, value: Any, unit: str = "") -> str:
        """
        Replace a single metric value in HTML.

        Looks for pattern like:
        <div class="metric-label">Total Planned</div>
        <div class="metric-value">269<span class="metric-unit">MT</span></div>
        """
        # Format the value
        if isinstance(value, float):
            if value >= 1000:
                formatted_value = f"{value:,.0f}" if value == int(value) else f"{value:,.2f}"
            else:
                formatted_value = f"{value:.2f}" if value != int(value) else str(int(value))
        else:
            formatted_value = str(value) if value is not None else "0"

        # Pattern to find the metric by label and replace its value
        pattern = rf'(<div class="metric-label">{re.escape(label)}</div>\s*<div class="metric-value">)[^<]*(<span class="metric-unit">)'
        replacement = rf'\g<1>{formatted_value}\g<2>'

        new_html = re.sub(pattern, replacement, html, flags=re.IGNORECASE)

        if new_html != html:
            logger.debug(f"Replaced metric '{label}': {formatted_value}")

        return new_html

    def _replace_executive_summary(self, html: str, data: Dict) -> str:
        """Replace Executive Summary metrics."""
        despatch = data.get('despatch', {})
        qc_lots = data.get('qc_lots', {})
        tests = data.get('tests', {})
        product_quality = data.get('product_quality', {})

        # Calculate achievement percentage
        total_planned = despatch.get('total_planned', 0) or 0
        total_actual = despatch.get('total_actual', 0) or 0
        achievement = (total_actual / total_planned * 100) if total_planned > 0 else 0

        # Calculate quality rate from product quality
        furnaces = product_quality.get('by_furnace', [])
        quality_rates = [f.get('quality_rate_pct', 0) or 0 for f in furnaces]
        avg_quality_rate = sum(quality_rates) / len(quality_rates) if quality_rates else 100

        html = self._replace_metric(html, "Despatch Performance", int(achievement), "%")
        html = self._replace_metric(html, "Quality Rate", int(avg_quality_rate), "%")
        html = self._replace_metric(html, "QC Lots Processed", qc_lots.get('total_lots', 0), "lots")
        html = self._replace_metric(html, "Total Tests", tests.get('total_tests', 0), "tests")

        return html

    def _replace_despatch_section(self, html: str, despatch: Dict) -> str:
        """Replace Despatch Performance section metrics."""
        total_planned = despatch.get('total_planned', 0) or 0
        total_actual = despatch.get('total_actual', 0) or 0
        variance = despatch.get('total_variance', 0) or 0
        customers = despatch.get('customers', [])

        html = self._replace_metric(html, "Total Planned", int(total_planned), "MT")
        html = self._replace_metric(html, "Total Actual", int(total_actual), "MT")
        html = self._replace_metric(html, "Variance", int(variance), "MT")
        html = self._replace_metric(html, "Customers Served", len(customers), "")

        return html

    def _replace_product_quality_section(self, html: str, product_quality: Dict) -> str:
        """Replace Product Quality section metrics."""
        furnaces = product_quality.get('by_furnace', [])

        total_production = sum(f.get('production_mt', 0) or 0 for f in furnaces)
        total_deviation = sum(f.get('deviation_mt', 0) or 0 for f in furnaces)

        # Calculate rates
        defect_rate = (total_deviation / total_production * 100) if total_production > 0 else 0
        quality_rate = 100 - defect_rate

        html = self._replace_metric(html, "Total Production", total_production, "MT")
        html = self._replace_metric(html, "Total Deviation", total_deviation, "MT")
        html = self._replace_metric(html, "Defect Rate", defect_rate, "%")
        html = self._replace_metric(html, "Quality Rate", quality_rate, "%")

        return html

    def _replace_qc_lots_section(self, html: str, qc_lots: Dict) -> str:
        """Replace QC Lots section metrics."""
        total_lots = qc_lots.get('total_lots', 0) or 0
        by_material = qc_lots.get('by_material', [])
        by_plant = qc_lots.get('by_plant', [])

        total_qty = sum(m.get('total_qty', 0) or 0 for m in by_material)
        num_plants = len(by_plant)
        num_materials = len(by_material)

        html = self._replace_metric(html, "Total Lots", total_lots, "lots")
        html = self._replace_metric(html, "Total Quantity", int(total_qty), "TO")
        html = self._replace_metric(html, "Plants Involved", num_plants, "")
        html = self._replace_metric(html, "Material Types", num_materials, "")

        return html

    def _replace_heat_analysis_section(self, html: str, heat_analysis: Dict) -> str:
        """Replace Heat Analysis section metrics."""
        by_furnace = heat_analysis.get('by_furnace', [])
        total_heats = heat_analysis.get('total_heats', 0) or 0

        # Count active furnaces
        active_furnaces = sum(1 for f in by_furnace if f.get('num_heats', 0) > 0)

        # Calculate average turnaround
        turnarounds = [f.get('avg_turnaround_minutes', 0) or 0 for f in by_furnace if f.get('num_heats', 0) > 0]
        avg_turnaround = sum(turnarounds) / len(turnarounds) if turnarounds else 0

        # Find most active furnace
        most_active = max(by_furnace, key=lambda f: f.get('num_heats', 0), default={'furnace': '1', 'num_heats': 0})
        most_active_name = f"Furn {most_active.get('furnace', '1')}"
        most_active_heats = most_active.get('num_heats', 0)

        html = self._replace_metric(html, "Total Heats", total_heats, "heats")
        html = self._replace_metric(html, "Active Furnaces", active_furnaces, "")
        html = self._replace_metric(html, "Avg Turnaround", int(avg_turnaround), "mins")

        # Replace most active furnace (special format)
        pattern = r'(<div class="metric-label">Most Active</div>\s*<div class="metric-value">)[^<]*(<span class="metric-unit">)[^<]*(</span>)'
        replacement = rf'\g<1>{most_active_name}\g<2>{most_active_heats} heats\g<3>'
        html = re.sub(pattern, replacement, html, flags=re.IGNORECASE)

        return html

    def _replace_testing_section(self, html: str, tests: Dict) -> str:
        """Replace Testing Results section metrics."""
        by_type = tests.get('by_type', [])

        # Find moisture and size test counts
        moisture_tests = 0
        size_tests = 0

        for test in by_type:
            test_type = test.get('test_type', '').lower()
            count = test.get('count', 0) or 0

            if 'moisture' in test_type:
                moisture_tests += count
            elif 'size' in test_type or 'over' in test_type:
                size_tests += count

        html = self._replace_metric(html, "Moisture Tests", moisture_tests, "tests")
        html = self._replace_metric(html, "Size Tests", size_tests, "tests")

        return html

    def _replace_stock_table(self, html: str, stock: Dict) -> str:
        """Replace Stock Summary table with real data."""
        products = stock.get('products', [])

        if not products:
            # No data - replace with empty table body and "No data" message
            logger.warning("No stock data - showing empty table")
            pattern = r'(<table class="data-table">.*?<tbody>)(.*?)(</tbody>)'
            empty_row = '''
                    <tr>
                        <td colspan="5" style="text-align: center; color: #888;">No stock data available for this date</td>
                    </tr>
'''
            html = re.sub(pattern, rf'\g<1>{empty_row}\g<3>', html, flags=re.DOTALL, count=1)
            return html

        # Build new table rows
        rows_html = ""
        total_opening = 0
        total_receipt = 0
        total_closing = 0
        total_despatch = 0

        for product in products:
            name = product.get('product', 'Unknown')
            opening = product.get('opening_stock', 0) or 0
            receipt = product.get('today_production', 0) or 0
            closing = product.get('closing_stock', 0) or 0
            despatch = product.get('mtd_despatch', 0) or 0

            total_opening += opening
            total_receipt += receipt
            total_closing += closing
            total_despatch += despatch

            # Highlight PRIME LUMPS row
            if 'PRIME' in name.upper():
                rows_html += f"""                    <tr>
                        <td><strong>{name}</strong></td>
                        <td><strong>{opening:,.2f}</strong></td>
                        <td><strong>{receipt:,.2f}</strong></td>
                        <td><strong>{closing:,.2f}</strong></td>
                        <td><strong>{despatch:,.2f}</strong></td>
                    </tr>
"""
            else:
                rows_html += f"""                    <tr>
                        <td>{name}</td>
                        <td>{opening:,.2f}</td>
                        <td>{receipt:,.2f}</td>
                        <td>{closing:,.2f}</td>
                        <td>{despatch:,.2f}</td>
                    </tr>
"""

        # Add total row
        rows_html += f"""                    <tr style="background: #f0f4f8; font-weight: 600;">
                        <td>TOTAL</td>
                        <td>{total_opening:,.2f}</td>
                        <td>{total_receipt:,.2f}</td>
                        <td>{total_closing:,.2f}</td>
                        <td>{total_despatch:,.2f}</td>
                    </tr>
"""

        # Replace the tbody content
        pattern = r'(<table class="data-table">.*?<tbody>).*?(</tbody>)'
        replacement = rf'\g<1>\n{rows_html}                \g<2>'
        html = re.sub(pattern, replacement, html, flags=re.DOTALL)

        return html

    def _replace_all_charts(self, html: str, data: Dict) -> str:
        """Replace all Chart.js data arrays with real data."""

        # 1. Despatch Chart
        html = self._replace_despatch_chart(html, data.get('despatch', {}))

        # 2. Product Quality Chart
        html = self._replace_quality_chart(html, data.get('product_quality', {}))

        # 3. Lots by Material Chart
        html = self._replace_lots_chart(html, data.get('qc_lots', {}))

        # 4. Heat Analysis Chart
        html = self._replace_heat_chart(html, data.get('heat_analysis', {}))

        # 5. Test Type Chart
        html = self._replace_test_type_chart(html, data.get('tests', {}))

        # 6. Plant Distribution Chart
        html = self._replace_plant_chart(html, data.get('qc_lots', {}))

        return html

    def _replace_despatch_chart(self, html: str, despatch: Dict) -> str:
        """Replace despatch chart data."""
        customers = despatch.get('customers', [])

        if not customers:
            # No data - replace with empty arrays to show empty chart
            logger.warning("No despatch customers data - showing empty chart")

            # Replace labels with empty
            html = re.sub(
                r"(const despatchCtx.*?labels: \[)[^\]]+(\])",
                r"\g<1>\g<2>",
                html,
                flags=re.DOTALL
            )

            # Replace planned data with empty
            html = re.sub(
                r"(label: 'Planned \(MT\)',\s*data: \[)[^\]]+(\])",
                r"\g<1>\g<2>",
                html
            )

            # Replace actual data with empty
            html = re.sub(
                r"(label: 'Actual \(MT\)',\s*data: \[)[^\]]+(\])",
                r"\g<1>\g<2>",
                html
            )

            return html

        labels = [c.get('customer', 'Unknown')[:15] for c in customers]
        planned = [c.get('planned_qty', 0) or 0 for c in customers]
        actual = [c.get('actual_qty', 0) or 0 for c in customers]

        # Replace labels
        html = re.sub(
            r"(const despatchCtx.*?labels: \[)[^\]]+(\])",
            rf"\g<1>{', '.join(repr(l) for l in labels)}\g<2>",
            html,
            flags=re.DOTALL
        )

        # Replace planned data
        html = re.sub(
            r"(label: 'Planned \(MT\)',\s*data: \[)[^\]]+(\])",
            rf"\g<1>{', '.join(map(str, planned))}\g<2>",
            html
        )

        # Replace actual data
        html = re.sub(
            r"(label: 'Actual \(MT\)',\s*data: \[)[^\]]+(\])",
            rf"\g<1>{', '.join(map(str, actual))}\g<2>",
            html
        )

        return html

    def _replace_quality_chart(self, html: str, product_quality: Dict) -> str:
        """Replace product quality chart data."""
        furnaces = product_quality.get('by_furnace', [])

        if not furnaces:
            # No data - replace with empty arrays
            logger.warning("No furnace quality data - showing empty chart")

            html = re.sub(
                r"(label: 'Production \(MT\)',\s*data: \[)[^\]]+(\])",
                r"\g<1>\g<2>",
                html
            )
            html = re.sub(
                r"(label: 'Quality Rate \(%\)',\s*data: \[)[^\]]+(\])",
                r"\g<1>\g<2>",
                html
            )
            return html

        production = [f.get('production_mt', 0) or 0 for f in furnaces]
        quality_rates = [f.get('quality_rate_pct', 100) or 100 for f in furnaces]

        # Replace production data
        html = re.sub(
            r"(label: 'Production \(MT\)',\s*data: \[)[^\]]+(\])",
            rf"\g<1>{', '.join(f'{x:.2f}' for x in production)}\g<2>",
            html
        )

        # Replace quality rate data
        html = re.sub(
            r"(label: 'Quality Rate \(%\)',\s*data: \[)[^\]]+(\])",
            rf"\g<1>{', '.join(map(str, quality_rates))}\g<2>",
            html
        )

        return html

    def _replace_lots_chart(self, html: str, qc_lots: Dict) -> str:
        """Replace lots by material doughnut chart data."""
        by_material = qc_lots.get('by_material', [])

        if not by_material:
            # No data - replace with empty arrays
            logger.warning("No lots by material data - showing empty chart")
            pattern = r"(const lotsCtx.*?labels: \[)[^\]]+(\].*?data: \[)[^\]]+(\])"
            html = re.sub(pattern, r"\g<1>\g<2>\g<3>", html, flags=re.DOTALL)
            return html

        sorted_materials = sorted(by_material, key=lambda x: x.get('count', 0), reverse=True)[:4]

        labels = [m.get('material', 'Unknown')[:20] for m in sorted_materials]
        counts = [m.get('count', 0) or 0 for m in sorted_materials]

        pattern = r"(const lotsCtx.*?labels: \[)[^\]]+(\].*?data: \[)[^\]]+(\])"

        labels_str = ', '.join(repr(l) for l in labels)
        counts_str = ', '.join(map(str, counts))

        replacement = rf"\g<1>{labels_str}\g<2>{counts_str}\g<3>"
        html = re.sub(pattern, replacement, html, flags=re.DOTALL)

        return html

    def _replace_heat_chart(self, html: str, heat_analysis: Dict) -> str:
        """Replace heat analysis chart data."""
        by_furnace = heat_analysis.get('by_furnace', [])

        if not by_furnace:
            # No data - replace with empty arrays
            logger.warning("No heat analysis data - showing empty chart")
            html = re.sub(
                r"(label: 'Number of Heats',\s*data: \[)[^\]]+(\])",
                r"\g<1>\g<2>",
                html
            )
            html = re.sub(
                r"(label: 'Avg Turnaround \(mins\)',\s*data: \[)[^\]]+(\])",
                r"\g<1>\g<2>",
                html
            )
            return html

        heats = [f.get('num_heats', 0) or 0 for f in by_furnace]
        turnarounds = [int(f.get('avg_turnaround_minutes', 0) or 0) for f in by_furnace]

        html = re.sub(
            r"(label: 'Number of Heats',\s*data: \[)[^\]]+(\])",
            rf"\g<1>{', '.join(map(str, heats))}\g<2>",
            html
        )

        html = re.sub(
            r"(label: 'Avg Turnaround \(mins\)',\s*data: \[)[^\]]+(\])",
            rf"\g<1>{', '.join(map(str, turnarounds))}\g<2>",
            html
        )

        return html

    def _replace_test_type_chart(self, html: str, tests: Dict) -> str:
        """Replace test type pie chart data."""
        by_type = tests.get('by_type', [])

        moisture_tests = 0
        size_tests = 0

        for test in by_type:
            test_type = test.get('test_type', '').lower()
            count = test.get('count', 0) or 0

            if 'moisture' in test_type:
                moisture_tests += count
            elif 'size' in test_type or 'over' in test_type:
                size_tests += count

        pattern = r"(const testTypeCtx.*?data: \[)[^\]]+(\])"
        replacement = rf"\g<1>{moisture_tests}, {size_tests}\g<2>"
        html = re.sub(pattern, replacement, html, flags=re.DOTALL)

        return html

    def _replace_plant_chart(self, html: str, qc_lots: Dict) -> str:
        """Replace plant distribution chart data."""
        by_plant = qc_lots.get('by_plant', [])

        if not by_plant:
            # No data - replace with empty arrays
            logger.warning("No plant distribution data - showing empty chart")
            pattern = r"(const plantCtx.*?labels: \[)[^\]]+(\].*?data: \[)[^\]]+(\])"
            html = re.sub(pattern, r"\g<1>\g<2>\g<3>", html, flags=re.DOTALL)
            return html

        labels = [f"Plant {p.get('plant', 'Unknown')}" for p in by_plant]
        counts = [p.get('count', 0) or 0 for p in by_plant]

        pattern = r"(const plantCtx.*?labels: \[)[^\]]+(\].*?data: \[)[^\]]+(\])"

        labels_str = ', '.join(repr(l) for l in labels)
        counts_str = ', '.join(map(str, counts))

        replacement = rf"\g<1>{labels_str}\g<2>{counts_str}\g<3>"
        html = re.sub(pattern, replacement, html, flags=re.DOTALL)
        return html

    def _replace_insights_section(self, html: str, claude_insights_html: str) -> str:
        """Replace the insights section with Claude's HTML."""
        if not claude_insights_html:
            return html

        pattern = r'(<div class="insight-box">)[\s\S]*?(</div>\s*</div>\s*</div>\s*<script>)'
        replacement = rf'\g<1>\n{claude_insights_html}\n            \g<2>'

        new_html = re.sub(pattern, replacement, html)

        if new_html != html:
            logger.info("Insights section replaced with Claude HTML")

        return new_html


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def generate_qc_dashboard(
    analysis_data: Dict[str, Any],
    claude_insights_html: str,
    date: str,
    template_path: str = None
) -> str:
    """Convenience function to generate dashboard."""
    engine = QCTemplateEngine(template_path)
    return engine.generate_dashboard(analysis_data, claude_insights_html, date)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['QCTemplateEngine', 'generate_qc_dashboard']