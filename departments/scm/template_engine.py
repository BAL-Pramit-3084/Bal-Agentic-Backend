"""
scm_template_engine.py
======================
Template engine for injecting real data into SCM dashboard HTML.

Replaces ALL hardcoded values:
1. Date in title and header
2. Daily Highlights alert banner
3. All 6 KPI metric cards
4. PO details table
5. PR details table
6. Chart.js data arrays (3 charts)
7. Insights section with Claude HTML
8. Footer summary

Author: Senior ML Engineer
Date: November 2025
"""

import os
import re
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class SCMTemplateEngine:
    """Inject real data into the SCM dashboard template."""

    def __init__(self, template_path: str = None):
        """Initialize template engine."""
        if template_path:
            self.template_path = template_path
        else:
            # Template is in root templates/ folder (not department subfolder)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.template_path = os.path.join(project_root, "templates", "scm_dashboard.html")
        logger.info(f"SCM Template Engine initialized: {self.template_path}")

    def generate_dashboard(self, analysis_data: Dict[str, Any],
                          claude_insights_html: str, date: str) -> str:
        """Generate complete dashboard HTML with real data."""
        logger.info(f"Generating SCM dashboard for date: {date}")

        # Store for fallback use
        self._current_date = analysis_data.get('formatted_date', date)

        # Load template
        html = self._load_template()
        logger.debug(f"Template loaded: {len(html)} chars")

        # Step 1: Replace dates
        html = self._replace_dates(html, date, analysis_data.get('formatted_date', ''))
        logger.debug("Step 1: Dates replaced")

        # Step 2: Replace daily highlights banner
        html = self._replace_daily_highlights(html, analysis_data)
        logger.debug("Step 2: Daily highlights replaced")

        # Step 3: Replace metric cards
        html = self._replace_metric_cards(html, analysis_data)
        logger.debug("Step 3: Metric cards replaced")

        # Step 4: Replace PO table
        html = self._replace_po_table(html, analysis_data)
        logger.debug("Step 4: PO table replaced")

        # Step 5: Replace PR table
        html = self._replace_pr_table(html, analysis_data)
        logger.debug("Step 5: PR table replaced")

        # Step 6: Replace charts
        html = self._replace_charts(html, analysis_data)
        logger.debug("Step 6: Charts replaced")

        # Step 7: Replace insights section
        html = self._replace_insights(html, claude_insights_html)
        logger.debug("Step 7: Insights replaced")

        # Step 8: Replace footer
        html = self._replace_footer(html, analysis_data)
        logger.debug("Step 8: Footer replaced")

        logger.info(f"SCM Dashboard generated: {len(html)} chars")
        return html

    def _load_template(self) -> str:
        """Load HTML template from file."""
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template not found: {self.template_path}")
        with open(self.template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _replace_dates(self, html: str, date: str, formatted_date: str) -> str:
        """Replace all date occurrences."""
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            if not formatted_date:
                formatted_date = date_obj.strftime('%B %d, %Y')
            day_name = date_obj.strftime('%A')
            full_date = f"{day_name}, {formatted_date}"

            # Title
            html = re.sub(
                r'<title>SCM Daily Report[^<]*</title>',
                f'<title>SCM Daily Report - {formatted_date} | Balasore Alloys</title>',
                html
            )

            # Date badge
            html = re.sub(
                r'(<div class="date-badge">)[^<]*(</div>)',
                rf'\g<1>{full_date}\g<2>',
                html
            )

            # Replace hardcoded "November 18, 2025" everywhere
            html = re.sub(r'November 18, 2025', formatted_date, html)
            html = re.sub(r'Monday, November 18, 2025', full_date, html)

            logger.info(f"Dates replaced: {formatted_date}")
            return html
        except Exception as e:
            logger.error(f"Error replacing dates: {e}")
            return html

    def _replace_daily_highlights(self, html: str, data: Dict) -> str:
        """Replace the daily highlights alert banner."""
        highlights = data.get('daily_highlights', [])
        metrics = data.get('summary_metrics', {})
        po = data.get('purchase_orders', {})
        pr = data.get('purchase_requisitions', {})

        # Build highlights HTML
        if highlights:
            items_html = ""
            for h in highlights:
                items_html += f'            <li style="padding: 5px 0;">{h.get("icon", "•")} {h.get("text", "")}</li>\n'
        else:
            # Fallback - build from metrics
            po_count = metrics.get('po_count', 0)
            po_value = metrics.get('po_total_value', 0)
            pr_count = pr.get('count', 0)

            value_str = self._format_currency(po_value)
            items_html = f"""            <li style="padding: 5px 0;">✓ <strong>{po_count} Purchase Orders</strong> created totaling <strong>{value_str}</strong></li>
            <li style="padding: 5px 0;">⚠️ <strong>100% Pending Delivery:</strong> All orders from today are pending delivery</li>
            <li style="padding: 5px 0;">📋 <strong>{pr_count} Purchase Requisitions</strong> created</li>
"""

        # Replace the ul content in alert-banner
        pattern = r'(<div class="alert-banner">.*?<ul[^>]*>)(.*?)(</ul>)'
        replacement = rf'\g<1>\n{items_html}        \g<3>'
        html = re.sub(pattern, replacement, html, flags=re.DOTALL)

        logger.info("Daily highlights replaced")
        return html

    def _replace_metric_cards(self, html: str, data: Dict) -> str:
        """Replace all 6 metric card values."""
        metrics = data.get('summary_metrics', {})
        po = data.get('purchase_orders', {})
        pr = data.get('purchase_requisitions', {})

        # Card 1: Purchase Orders Created
        html = self._replace_metric(html, "Purchase Orders Created",
            str(metrics.get('po_count', 0)),
            f"{metrics.get('po_line_items', 0)} line items")

        # Card 2: Total PO Value
        value_display = metrics.get('po_value_display', {})
        value_str = f"{value_display.get('prefix', '₹')}{value_display.get('value', 0)} {value_display.get('unit', '')}".strip()
        avg_display = metrics.get('avg_per_item_display', {})
        avg_str = f"Average: {avg_display.get('prefix', '₹')}{avg_display.get('value', 0)} {avg_display.get('unit', '')}/item".strip()
        html = self._replace_metric(html, "Total PO Value", value_str, avg_str)

        # Card 3: Purchase Requisitions
        html = self._replace_metric(html, "Purchase Requisitions",
            str(pr.get('count', 0)),
            f"{pr.get('line_items', 0)} line items created")

        # Card 4: Vendors Engaged
        html = self._replace_metric(html, "Vendors Engaged",
            str(metrics.get('vendor_count', 0)),
            "Unique vendors")

        # Card 5: Delivery Status
        pending_pct = po.get('pending_pct', 100)
        html = self._replace_metric(html, "Delivery Status",
            f"{pending_pct:.0f}%",
            "All items pending" if pending_pct >= 100 else f"{pending_pct:.0f}% pending")

        # Card 6: Active Buyers
        html = self._replace_metric(html, "Active Buyers",
            str(metrics.get('purch_groups', 0)),
            "Purchasing groups")

        logger.info("Metric cards replaced")
        return html

    def _replace_metric(self, html: str, title: str, value: str, label: str) -> str:
        """Replace a single metric card."""
        pattern = rf'(<div class="metric-card">\s*<h3>{re.escape(title)}</h3>\s*<div class="metric-value">)[^<]*(</div>\s*<div class="metric-label">)[^<]*(</div>)'
        replacement = rf'\g<1>{value}\g<2>{label}\g<3>'
        return re.sub(pattern, replacement, html, flags=re.IGNORECASE | re.DOTALL)

    def _replace_po_table(self, html: str, data: Dict) -> str:
        """Replace PO details table."""
        po = data.get('purchase_orders', {})
        details = po.get('details', [])
        formatted_date = data.get('formatted_date', '')

        if not details:
            logger.warning("No PO details to replace")
            return html

        # Build table rows
        rows_html = ""
        for item in details[:15]:
            value = item.get('value', 0)
            is_high_value = value > 100000

            row_style = ' style="background: #fff3cd;"' if is_high_value else ""
            bold_start = "<strong>" if is_high_value else ""
            bold_end = "</strong>" if is_high_value else ""

            rows_html += f"""                <tr{row_style}>
                    <td>{bold_start}{item.get('po_no', '')}{bold_end}</td>
                    <td>{item.get('vendor', '')[:25]}</td>
                    <td>{item.get('material', '')[:30]}</td>
                    <td>{item.get('quantity', 0):,.0f} {item.get('unit', '')}</td>
                    <td>{bold_start}{item.get('value_formatted', '')}{bold_end}</td>
                    <td>{item.get('category', '')[:20]}</td>
                    <td>{item.get('plant', '')[:20]}</td>
                </tr>
"""

        # Replace table tbody
        pattern = r'(📦 Purchase Orders Created on[^<]*</h2>\s*<table>.*?<tbody>)(.*?)(</tbody>)'
        replacement = rf'\g<1>\n{rows_html}            \g<3>'
        html = re.sub(pattern, replacement, html, flags=re.DOTALL)

        logger.info(f"PO table replaced with {len(details)} rows")
        return html

    def _replace_pr_table(self, html: str, data: Dict) -> str:
        """Replace PR details table."""
        pr = data.get('purchase_requisitions', {})
        details = pr.get('details', [])

        if not details:
            logger.warning("No PR details to replace")
            return html

        # Build table rows
        rows_html = ""
        for item in details[:15]:
            is_converted = item.get('is_converted', False)
            row_style = ' style="background: #d4edda;"' if is_converted else ' style="background: #fff3cd;"'

            rows_html += f"""                <tr{row_style}>
                    <td>{item.get('pr_number', '')}</td>
                    <td>{item.get('description', '')[:35]}</td>
                    <td>{item.get('value_formatted', '₹0')}</td>
                    <td>{item.get('status', '⏳ Pending')}</td>
                    <td>{item.get('po_no', '-')}</td>
                    <td>{item.get('requisitioner', '')}</td>
                    <td>{item.get('category', '')[:18]}</td>
                </tr>
"""

        # Replace table tbody - find PR table by its header
        pattern = r'(📋 Purchase Requisitions Created on[^<]*</h2>\s*<table>.*?<tbody>)(.*?)(</tbody>)'
        replacement = rf'\g<1>\n{rows_html}            \g<3>'
        html = re.sub(pattern, replacement, html, flags=re.DOTALL)

        logger.info(f"PR table replaced with {len(details)} rows")
        return html

    def _replace_charts(self, html: str, data: Dict) -> str:
        """Replace all Chart.js data arrays."""
        charts = data.get('charts', {})

        # Vendor Chart
        vendor = charts.get('vendor', {})
        vendor_labels = vendor.get('labels', [])
        vendor_values = vendor.get('values', [])
        if vendor_labels and vendor_values:
            labels_str = ", ".join(f"'{l}'" for l in vendor_labels)
            values_str = ", ".join(str(int(v)) for v in vendor_values)
            pattern = r"(const vendorCtx.*?labels: \[)[^\]]+(\].*?data: \[)[^\]]+(\])"
            html = re.sub(pattern, rf"\g<1>{labels_str}\g<2>{values_str}\g<3>", html, flags=re.DOTALL)
            logger.debug(f"Vendor chart: {len(vendor_labels)} items")

        # Plant Chart
        plant = charts.get('plant', {})
        plant_labels = plant.get('labels', [])
        plant_values = plant.get('values', [])
        if plant_labels and plant_values:
            labels_str = ", ".join(f"'{l}'" for l in plant_labels)
            values_str = ", ".join(str(int(v)) for v in plant_values)
            pattern = r"(const plantCtx.*?labels: \[)[^\]]+(\].*?data: \[)[^\]]+(\])"
            html = re.sub(pattern, rf"\g<1>{labels_str}\g<2>{values_str}\g<3>", html, flags=re.DOTALL)
            logger.debug(f"Plant chart: {len(plant_labels)} items")

        # Category Chart
        category = charts.get('category', {})
        category_labels = category.get('labels', [])
        category_values = category.get('values', [])
        if category_labels and category_values:
            labels_str = ", ".join(f"'{l}'" for l in category_labels)
            values_str = ", ".join(str(int(v)) for v in category_values)
            pattern = r"(const categoryCtx.*?labels: \[)[^\]]+(\].*?data: \[)[^\]]+(\])"
            html = re.sub(pattern, rf"\g<1>{labels_str}\g<2>{values_str}\g<3>", html, flags=re.DOTALL)
            logger.debug(f"Category chart: {len(category_labels)} items")

        logger.info("Charts replaced")
        return html

    def _replace_insights(self, html: str, claude_insights_html: str) -> str:
        """Replace ALL insights sections with Claude-generated HTML."""
        if not claude_insights_html:
            logger.warning("No Claude insights to replace")
            return html

        # The template has THREE insights-section divs:
        # 1. "Key Insights for November 18, 2025" (lines 555-614)
        # 2. "Daily Performance vs. Historical Context" (lines 615-626)
        # 3. "Action Items for November 19, 2025" (lines 627-645)

        # We need to replace ALL of them with the Claude-generated content

        # Find the first insights-section and replace everything up to the footer
        pattern = r'(<div class="insights-section">.*?<h2>🔍 Key Insights).*?(</div>\s*<div class="footer">)'

        # Build replacement with Claude insights
        replacement = rf'''<div class="insights-section">
        <h2>🔍 AI-Powered Analysis</h2>
        {claude_insights_html}
    </div>

    \g<2>'''

        new_html = re.sub(pattern, replacement, html, flags=re.DOTALL, count=1)

        if new_html != html:
            logger.info("All insights sections replaced with Claude HTML")
            return new_html

        # Fallback: try simpler pattern
        logger.warning("Primary insights pattern didn't match, trying fallback")

        # Just replace the date in insight headers at minimum
        html = re.sub(r'November 18, 2025', self._current_date if hasattr(self, '_current_date') else 'the selected date', html)
        html = re.sub(r'November 19, 2025', 'the next day', html)

        return html

    def _replace_footer(self, html: str, data: Dict) -> str:
        """Replace footer summary."""
        formatted_date = data.get('formatted_date', '')
        metrics = data.get('summary_metrics', {})
        pr = data.get('purchase_requisitions', {})

        po_count = metrics.get('po_count', 0)
        po_items = metrics.get('po_line_items', 0)
        pr_count = pr.get('count', 0)
        pr_items = pr.get('line_items', 0)

        # Replace footer content
        pattern = r'(<div class="footer">)(.*?)(</div>\s*<script>)'
        footer_content = f"""
        <p><strong>Report Date:</strong> {formatted_date} (Single Day Analysis)</p>
        <p style="margin-top: 10px;"><strong>Data Summary:</strong> {po_count} Purchase Orders ({po_items} line items) | {pr_count} Purchase Requisitions ({pr_items} line items)</p>
        <p style="margin-top: 10px; font-size: 0.85em;">This report covers procurement activity for {formatted_date} only</p>
    """
        replacement = rf'\g<1>{footer_content}\g<3>'
        html = re.sub(pattern, replacement, html, flags=re.DOTALL)

        logger.info("Footer replaced")
        return html

    def _format_currency(self, value: float) -> str:
        """Format currency value."""
        if value >= 10000000:
            return f"₹{value/10000000:.2f} Cr"
        elif value >= 100000:
            return f"₹{value/100000:.2f} L"
        else:
            return f"₹{value:,.0f}"


# Convenience function
def generate_scm_dashboard(analysis_data: Dict, claude_insights_html: str,
                          date: str, template_path: str = None) -> str:
    """Convenience function to generate dashboard."""
    engine = SCMTemplateEngine(template_path)
    return engine.generate_dashboard(analysis_data, claude_insights_html, date)


__all__ = ['SCMTemplateEngine', 'generate_scm_dashboard']