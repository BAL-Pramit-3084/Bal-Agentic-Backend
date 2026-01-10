"""
crm_template_engine.py
======================
Template engine for CRM / Sales & Distribution Dashboard.

This module:
1. Loads the sd_dashboard.html template
2. Replaces all hardcoded values with real data
3. Updates charts with actual data
4. Injects Claude-generated insights
5. Handles empty data gracefully

Replacement Strategy:
- Header: Date badge, title
- Alert Banner: Daily highlights
- KPI Cards: All 6 metric cards
- Comparison Stats: TD vs MTD
- Tables: Sales Orders, Top Billed Customers
- Charts: Order Value, Channel Split, Survey
- Insights Section: Claude-generated content
- Footer: Report metadata

Author: Senior ML Engineer
Date: November 2025
"""

import re
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_currency_cr(value: float) -> str:
    """Format value in Crores."""
    if value >= 10000000:
        return f"₹{value/10000000:.2f} Cr"
    elif value >= 100000:
        return f"₹{value/100000:.2f} L"
    else:
        return f"₹{value:,.0f}"


def format_currency_lakhs(value: float) -> str:
    """Format value in Lakhs."""
    if value >= 100000:
        return f"₹{value/100000:.2f} L"
    else:
        return f"₹{value:,.0f}"


def format_number(value: float, decimals: int = 0) -> str:
    """Format number with commas."""
    if decimals == 0:
        return f"{value:,.0f}"
    return f"{value:,.{decimals}f}"


def safe_get(data: Dict, *keys, default=0):
    """Safely get nested dictionary value."""
    result = data
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key, default)
        else:
            return default
    return result if result is not None else default


# ============================================================================
# CRM TEMPLATE ENGINE CLASS
# ============================================================================

class CRMTemplateEngine:
    """
    Template engine for CRM/Sales & Distribution Dashboard.
    """

    def __init__(self, template_path: str = None):
        """
        Initialize with template path.

        Args:
            template_path: Path to sd_dashboard.html template
        """
        if template_path is None:
            # Template is in root templates/ folder (not department subfolder)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            template_path = os.path.join(project_root, "templates", "sd_dashboard.html")

        self.template_path = template_path
        logger.info(f"CRM Template Engine initialized with template: {template_path}")

    def generate_dashboard(self, analysis_data: Dict[str, Any],
                          claude_insights_html: str,
                          date: str) -> str:
        """
        Generate complete dashboard HTML with real data.

        Args:
            analysis_data: The analysisData dict from CRMDataProcessor
            claude_insights_html: HTML string from Claude analyzer
            date: Date string (YYYY-MM-DD)

        Returns:
            Complete HTML string for the dashboard
        """
        logger.info(f"Generating CRM dashboard for date: {date}")

        # Load template
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template not found: {self.template_path}")

        with open(self.template_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # Apply all replacements
        html = self._replace_header(html, analysis_data)
        html = self._replace_alert_banner(html, analysis_data)
        html = self._replace_kpi_cards(html, analysis_data)
        html = self._replace_comparison_stats(html, analysis_data)
        html = self._replace_sales_orders_table(html, analysis_data)
        html = self._replace_top_customers_table(html, analysis_data)
        html = self._replace_delivery_stats(html, analysis_data)
        html = self._replace_all_charts(html, analysis_data)
        html = self._replace_insights(html, claude_insights_html)
        html = self._replace_footer(html, analysis_data, date)

        logger.info(f"Dashboard generation complete ({len(html)} characters)")
        return html

    # ========================================================================
    # REPLACEMENT METHODS
    # ========================================================================

    def _replace_header(self, html: str, data: Dict) -> str:
        """Replace header section with real date."""
        date_formatted = data.get('date_formatted', 'Unknown Date')
        month = data.get('month', 'Unknown')
        day = data.get('day', 0)
        year = data.get('year', 0)

        # Replace title
        html = re.sub(
            r'<title>.*?</title>',
            f'<title>Sales & Marketing Daily Report - {month} {day}, {year} | Balasore Alloys</title>',
            html
        )

        # Replace date badge
        html = re.sub(
            r'<div class="date-badge">.*?</div>',
            f'<div class="date-badge">{date_formatted}</div>',
            html,
            count=1
        )

        return html

    def _replace_alert_banner(self, html: str, data: Dict) -> str:
        """Replace alert banner with daily highlights."""
        highlights = data.get('highlights', {})

        orders = highlights.get('orders', {})
        billing = highlights.get('billing', {})
        deliveries = highlights.get('deliveries', {})
        concentration = highlights.get('concentration', {})
        channel_split = highlights.get('channel_split', {})

        order_count = orders.get('count', 0)
        order_value = orders.get('value_formatted', '₹0')
        order_qty = format_number(orders.get('qty', 0))

        invoice_count = billing.get('count', 0)
        invoice_value = billing.get('value_formatted', '₹0')
        invoice_weight = format_number(billing.get('weight', 0))

        delivery_count = deliveries.get('count', 0)
        delivery_weight = format_number(deliveries.get('weight', 0))
        delivery_customers = deliveries.get('customers', 0)

        top_customer = concentration.get('top_customer', 'N/A')
        top_customer_pct = concentration.get('top_customer_pct', 0)

        export_pct = channel_split.get('export_pct', 0)

        new_banner = f'''<div class="alert-banner">
        <h2>🎯 Daily Highlights</h2>
        <ul style="list-style: none; padding: 0; margin-top: 10px;">
            <li style="padding: 5px 0;">✓ <strong>{order_count} Sales Orders</strong> booked totaling <strong>{order_value}</strong> ({order_qty} MT)</li>
            <li style="padding: 5px 0;">✓ <strong>{invoice_count} Invoices</strong> processed totaling <strong>{invoice_value}</strong> ({invoice_weight} MT)</li>
            <li style="padding: 5px 0;">✓ <strong>{delivery_count} Deliveries</strong> executed totaling <strong>{delivery_weight} MT</strong> to {delivery_customers} customers</li>
            <li style="padding: 5px 0;">⚠️ <strong>Customer Concentration:</strong> {top_customer} = {top_customer_pct}% of daily billing revenue</li>
            <li style="padding: 5px 0;">⚠️ <strong>Export Dominance:</strong> {export_pct}% of order value from Export channel</li>
        </ul>
    </div>'''

        # Replace entire alert banner
        html = re.sub(
            r'<div class="alert-banner">.*?</ul>\s*</div>',
            new_banner,
            html,
            flags=re.DOTALL,
            count=1
        )

        return html

    def _replace_kpi_cards(self, html: str, data: Dict) -> str:
        """Replace all 6 KPI cards with real data."""
        sales_orders = data.get('sales_orders', {})
        billing = data.get('billing', {})
        deliveries = data.get('deliveries', {})

        so_td = sales_orders.get('td', {})
        so_mtd = sales_orders.get('mtd', {})
        so_pct = sales_orders.get('td_pct_of_mtd', {})

        bill_td = billing.get('td', {})
        bill_pct = billing.get('td_pct_of_mtd', {})

        del_td = deliveries.get('td', {})
        del_pct = deliveries.get('td_pct_of_mtd', 0)

        # Card 1: Sales Orders (TD)
        html = re.sub(
            r'(<div class="metric-card">\s*<h3>📋 Sales Orders \(TD\)</h3>\s*<div class="metric-value">)\d+(</div>\s*<div class="metric-label">).*?(</div>\s*<div class="metric-trend[^"]*">)[\d.]+% of MTD(</div>)',
            rf'\g<1>{so_td.get("count", 0)}\g<2>{format_number(so_td.get("qty", 0))} MT | {so_td.get("customers", 0)} Customers\g<3>{so_pct.get("count", 0):.1f}% of MTD\g<4>',
            html
        )

        # Card 2: Order Value (TD)
        html = re.sub(
            r'(<div class="metric-card">\s*<h3>💰 Order Value \(TD\)</h3>\s*<div class="metric-value">)₹[\d.,]+ Cr(</div>\s*<div class="metric-label">).*?(</div>\s*<div class="metric-trend[^"]*">)[\d.]+% of MTD(</div>)',
            rf'\g<1>{so_td.get("value_formatted", "₹0")}\g<2>Avg: {format_currency_cr(so_td.get("avg_order_value", 0))}/order\g<3>{so_pct.get("value", 0):.1f}% of MTD\g<4>',
            html
        )

        # Card 3: Deliveries (TD)
        html = re.sub(
            r'(<div class="metric-card">\s*<h3>🚚 Deliveries \(TD\)</h3>\s*<div class="metric-value">)\d+(</div>\s*<div class="metric-label">).*?(</div>\s*<div class="metric-trend[^"]*">)[\d.]+% of MTD(</div>)',
            rf'\g<1>{del_td.get("count", 0)}\g<2>{format_number(del_td.get("weight", 0))} MT | {del_td.get("customers", 0)} Customers\g<3>{del_pct:.1f}% of MTD\g<4>',
            html
        )

        # Card 4: Invoices (TD)
        html = re.sub(
            r'(<div class="metric-card">\s*<h3>📄 Invoices \(TD\)</h3>\s*<div class="metric-value">)\d+(</div>\s*<div class="metric-label">).*?(</div>\s*<div class="metric-trend[^"]*">)[\d.]+% of MTD(</div>)',
            rf'\g<1>{bill_td.get("invoice_count", 0)}\g<2>{format_number(bill_td.get("weight", 0))} MT | {bill_td.get("value_formatted", "₹0")}\g<3>{bill_pct.get("invoices", 0):.1f}% of MTD\g<4>',
            html
        )

        # Card 5: Active Customers
        mtd_customers = billing.get('mtd', {}).get('customers', 0)
        customer_pct = (bill_td.get('customers', 0) / mtd_customers * 100) if mtd_customers > 0 else 0
        html = re.sub(
            r'(<div class="metric-card">\s*<h3>👥 Active Customers</h3>\s*<div class="metric-value">)\d+(</div>\s*<div class="metric-label">).*?(</div>\s*<div class="metric-trend[^"]*">).*?(</div>)',
            rf'\g<1>{bill_td.get("customers", 0)}\g<2>Billed today\g<3>{customer_pct:.0f}% of MTD base\g<4>',
            html
        )

        # Card 6: Avg Price/MT
        html = re.sub(
            r'(<div class="metric-card">\s*<h3>💹 Avg Price/MT</h3>\s*<div class="metric-value">)₹[\d.,]+ L(</div>\s*<div class="metric-label">).*?(</div>\s*<div class="metric-trend[^"]*">).*?(</div>)',
            rf'\g<1>{so_td.get("avg_price_formatted", "₹0")}\g<2>Order pricing\g<3>Premium\g<4>',
            html
        )

        return html

    def _replace_comparison_stats(self, html: str, data: Dict) -> str:
        """Replace TD vs MTD comparison stats."""
        sales_orders = data.get('sales_orders', {})
        billing = data.get('billing', {})

        so_td = sales_orders.get('td', {})
        so_mtd = sales_orders.get('mtd', {})
        so_pct = sales_orders.get('td_pct_of_mtd', {})

        bill_td = billing.get('td', {})
        bill_mtd = billing.get('mtd', {})
        bill_pct = billing.get('td_pct_of_mtd', {})

        # Orders comparison
        html = re.sub(
            r'(<div class="stat-item">\s*<div class="stat-item-label">Orders TD</div>\s*<div class="stat-item-value">)\d+(</div>\s*</div>\s*<div class="stat-item">\s*<div class="stat-item-label">Orders MTD</div>\s*<div class="stat-item-value">)\d+(</div>\s*</div>\s*<div class="stat-item">\s*<div class="stat-item-label">TD % of MTD</div>\s*<div class="stat-item-value">)[\d.]+%(</div>)',
            rf'\g<1>{so_td.get("count", 0)}\g<2>{so_mtd.get("count", 0)}\g<3>{so_pct.get("count", 0):.1f}%\g<4>',
            html
        )

        # Value comparison
        html = re.sub(
            r'(<div class="stat-item">\s*<div class="stat-item-label">Value TD</div>\s*<div class="stat-item-value">)₹[\d.]+ Cr(</div>\s*</div>\s*<div class="stat-item">\s*<div class="stat-item-label">Value MTD</div>\s*<div class="stat-item-value">)₹[\d.]+ Cr(</div>\s*</div>\s*<div class="stat-item">\s*<div class="stat-item-label">TD % of MTD</div>\s*<div class="stat-item-value">)[\d.]+%(</div>)',
            rf'\g<1>{so_td.get("value_formatted", "₹0")}\g<2>{so_mtd.get("value_formatted", "₹0")}\g<3>{so_pct.get("value", 0):.1f}%\g<4>',
            html
        )

        # Invoices comparison
        html = re.sub(
            r'(<div class="stat-item">\s*<div class="stat-item-label">Invoices TD</div>\s*<div class="stat-item-value">)\d+(</div>\s*</div>\s*<div class="stat-item">\s*<div class="stat-item-label">Invoices MTD</div>\s*<div class="stat-item-value">)\d+(</div>\s*</div>\s*<div class="stat-item">\s*<div class="stat-item-label">TD % of MTD</div>\s*<div class="stat-item-value">)[\d.]+%(</div>)',
            rf'\g<1>{bill_td.get("invoice_count", 0)}\g<2>{bill_mtd.get("invoice_count", 0)}\g<3>{bill_pct.get("invoices", 0):.1f}%\g<4>',
            html
        )

        return html

    def _replace_sales_orders_table(self, html: str, data: Dict) -> str:
        """Replace sales orders table with real data."""
        sales_orders = data.get('sales_orders', {})
        order_details = sales_orders.get('order_details', [])
        date_formatted = f"{data.get('month', 'Unknown')} {data.get('day', 0)}, {data.get('year', 0)}"

        # Update table header with date
        html = re.sub(
            r'<h2>📋 Sales Orders - .*?</h2>',
            f'<h2>📋 Sales Orders - {date_formatted}</h2>',
            html
        )

        if not order_details:
            # No orders - show empty table message
            empty_row = '''<tr>
                    <td colspan="8" style="text-align: center; color: #888; padding: 20px;">No sales orders for this date</td>
                </tr>'''
            html = re.sub(
                r'(<table>\s*<thead>.*?</thead>\s*<tbody>).*?(</tbody>\s*</table>)',
                rf'\g<1>{empty_row}\g<2>',
                html,
                flags=re.DOTALL,
                count=1
            )
            return html

        # Build table rows
        rows_html = ""
        for i, order in enumerate(order_details[:10]):
            is_top = i == 0
            row_style = ' style="background: #fff5f5;"' if is_top else ''

            so_no = order.get('so_no', '')
            customer = order.get('customer', '')[:20]
            material = order.get('material', '')[:25]
            qty = format_number(order.get('qty', 0))
            unit_price = format_currency_lakhs(order.get('unit_price', 0))
            net_value = format_currency_cr(order.get('net_value', 0))
            plant = order.get('plant', '')[:12]
            channel = order.get('channel', 'Unknown')

            badge_class = 'badge-export' if 'export' in channel.lower() else 'badge-domestic'
            badge_text = 'Export' if 'export' in channel.lower() else 'Domestic'

            if is_top:
                rows_html += f'''<tr{row_style}>
                    <td><strong>{so_no}</strong></td>
                    <td><strong>{customer}</strong></td>
                    <td>{material}</td>
                    <td><strong>{qty}</strong></td>
                    <td>{unit_price}</td>
                    <td><strong>{net_value}</strong></td>
                    <td>{plant}</td>
                    <td><span class="badge {badge_class}">{badge_text}</span></td>
                </tr>
'''
            else:
                rows_html += f'''<tr>
                    <td>{so_no}</td>
                    <td>{customer}</td>
                    <td>{material}</td>
                    <td>{qty}</td>
                    <td>{unit_price}</td>
                    <td>{net_value}</td>
                    <td>{plant}</td>
                    <td><span class="badge {badge_class}">{badge_text}</span></td>
                </tr>
'''

        # Replace table body - find first data-table with Sales Orders
        pattern = r'(<div class="data-table">\s*<h2>📋 Sales Orders.*?<tbody>).*?(</tbody>\s*</table>\s*</div>)'
        html = re.sub(pattern, rf'\g<1>{rows_html}\g<2>', html, flags=re.DOTALL, count=1)

        return html

    def _replace_top_customers_table(self, html: str, data: Dict) -> str:
        """Replace top billed customers table with real data."""
        billing = data.get('billing', {})
        top_customers = billing.get('top_customers', [])
        date_formatted = f"{data.get('month', 'Unknown')} {data.get('day', 0)}, {data.get('year', 0)}"

        # Update table header with date
        html = re.sub(
            r'<h2>💳 Top Billed Customers - .*?</h2>',
            f'<h2>💳 Top Billed Customers - {date_formatted}</h2>',
            html
        )

        if not top_customers:
            empty_row = '''<tr>
                    <td colspan="6" style="text-align: center; color: #888; padding: 20px;">No billing data for this date</td>
                </tr>'''
            # Find the Top Billed Customers table
            pattern = r'(<h2>💳 Top Billed Customers.*?<tbody>).*?(</tbody>\s*</table>\s*</div>)'
            html = re.sub(pattern, rf'\g<1>{empty_row}\g<2>', html, flags=re.DOTALL, count=1)
            return html

        # Build table rows
        rows_html = ""
        for i, customer in enumerate(top_customers[:10]):
            is_top = i == 0
            row_style = ' style="background: #fff5f5;"' if is_top else ''

            name = customer.get('name', '')[:25]
            invoices = customer.get('invoices', 0)
            weight = format_number(customer.get('weight', 0), 2)
            value = format_currency_cr(customer.get('value', 0))
            rate = format_currency_lakhs(customer.get('rate', 0))
            pct_revenue = f"{customer.get('pct_revenue', 0):.1f}%"

            if is_top:
                rows_html += f'''<tr{row_style}>
                    <td><strong>{name}</strong></td>
                    <td>{invoices}</td>
                    <td>{weight}</td>
                    <td><strong>{value}</strong></td>
                    <td>{rate}</td>
                    <td><strong>{pct_revenue}</strong></td>
                </tr>
'''
            else:
                rows_html += f'''<tr>
                    <td>{name}</td>
                    <td>{invoices}</td>
                    <td>{weight}</td>
                    <td>{value}</td>
                    <td>{rate}</td>
                    <td>{pct_revenue}</td>
                </tr>
'''

        # Replace table body
        pattern = r'(<h2>💳 Top Billed Customers.*?<tbody>).*?(</tbody>\s*</table>\s*</div>)'
        html = re.sub(pattern, rf'\g<1>{rows_html}\g<2>', html, flags=re.DOTALL, count=1)

        return html

    def _replace_delivery_stats(self, html: str, data: Dict) -> str:
        """Replace delivery performance stats."""
        deliveries = data.get('deliveries', {})
        del_td = deliveries.get('td', {})
        month = data.get('month', 'Unknown')
        day = data.get('day', 0)

        # Update header
        html = re.sub(
            r'<h2>🚛 Delivery Performance - .*?</h2>',
            f'<h2>🚛 Delivery Performance - {month} {day}</h2>',
            html
        )

        # Replace delivery stats
        html = re.sub(
            r'(<div class="stat-item">\s*<div class="stat-item-label">Deliveries</div>\s*<div class="stat-item-value">)\d+(</div>)',
            rf'\g<1>{del_td.get("count", 0)}\g<2>',
            html
        )

        html = re.sub(
            r'(<div class="stat-item">\s*<div class="stat-item-label">Total Weight</div>\s*<div class="stat-item-value">)\d+ MT(</div>)',
            rf'\g<1>{format_number(del_td.get("weight", 0))} MT\g<2>',
            html
        )

        html = re.sub(
            r'(<div class="stat-item">\s*<div class="stat-item-label">Customers</div>\s*<div class="stat-item-value">)\d+(</div>)',
            rf'\g<1>{del_td.get("customers", 0)}\g<2>',
            html
        )

        html = re.sub(
            r'(<div class="stat-item">\s*<div class="stat-item-label">Avg/Truck</div>\s*<div class="stat-item-value">)\d+ MT(</div>)',
            rf'\g<1>{format_number(del_td.get("avg_per_delivery", 0))} MT\g<2>',
            html
        )

        return html

    def _replace_all_charts(self, html: str, data: Dict) -> str:
        """Replace all chart data."""
        html = self._replace_order_value_chart(html, data)
        html = self._replace_channel_chart(html, data)
        html = self._replace_survey_chart(html, data)
        return html

    def _replace_order_value_chart(self, html: str, data: Dict) -> str:
        """Replace order value bar chart data."""
        sales_orders = data.get('sales_orders', {})
        order_details = sales_orders.get('order_details', [])

        if not order_details:
            # Empty chart
            labels = "[]"
            values = "[]"
        else:
            # Get top 5 orders
            top_orders = order_details[:5]
            labels = [o.get('customer', '')[:15] for o in top_orders]
            values = [round(o.get('net_value', 0) / 10000000, 2) for o in top_orders]  # Convert to Cr

            labels = str(labels).replace("'", '"')
            values = str(values)

        # Replace chart labels
        html = re.sub(
            r"(const orderValueCtx.*?labels: )\[.*?\](,)",
            rf"\g<1>{labels}\g<2>",
            html,
            flags=re.DOTALL
        )

        # Replace chart data
        html = re.sub(
            r"(const orderValueCtx.*?data: )\[[\d.,\s]+\](,)",
            rf"\g<1>{values}\g<2>",
            html,
            flags=re.DOTALL
        )

        return html

    def _replace_channel_chart(self, html: str, data: Dict) -> str:
        """Replace channel split doughnut chart data."""
        highlights = data.get('highlights', {})
        channel_split = highlights.get('channel_split', {})

        export_pct = channel_split.get('export_pct', 50)
        domestic_pct = channel_split.get('domestic_pct', 50)

        # Replace chart data
        html = re.sub(
            r"(const channelCtx.*?data: )\[[\d.,\s]+\](,)",
            rf"\g<1>[{export_pct}, {domestic_pct}]\g<2>",
            html,
            flags=re.DOTALL
        )

        return html

    def _replace_survey_chart(self, html: str, data: Dict) -> str:
        """Replace customer survey bar chart data."""
        survey = data.get('customer_survey', {})
        # Use the actual FY of the survey data, not the report date FY
        survey_fy = data.get('survey_financial_year', data.get('financial_year', 'Unknown'))

        if not survey.get('has_data', False):
            # No survey data - use zeros
            chart_data = "[0, 0, 0, 0, 0, 0, 0, 0]"
        else:
            chart_data = str(survey.get('chart_data', [0, 0, 0, 0, 0, 0, 0, 0]))

        # Update chart header with correct FY
        html = re.sub(
            r'<h2>⭐ Customer Satisfaction \(FY [\d-]+\)</h2>',
            f'<h2>⭐ Customer Satisfaction (FY {survey_fy})</h2>',
            html
        )

        # Replace chart data
        html = re.sub(
            r"(const surveyCtx.*?data: )\[[\d.,\s]+\](,)",
            rf"\g<1>{chart_data}\g<2>",
            html,
            flags=re.DOTALL
        )

        return html

    def _replace_insights(self, html: str, claude_insights_html: str) -> str:
        """Replace insights section with Claude-generated content."""
        if not claude_insights_html:
            logger.warning("No Claude insights provided - keeping template insights")
            return html

        # Find the insights section and replace everything from first insight-section to footer
        # The template has two insight sections - Key Insights and Action Items

        # Find position of first insights-section
        first_insight_match = re.search(r'<div class="insights-section">', html)
        if not first_insight_match:
            logger.warning("Could not find insights section in template")
            return html

        # Find position of footer
        footer_match = re.search(r'<div class="footer">', html)
        if not footer_match:
            logger.warning("Could not find footer in template")
            return html

        # Get positions
        insight_start = first_insight_match.start()
        footer_start = footer_match.start()

        # Build new insights section
        before_insights = html[:insight_start]
        after_insights = html[footer_start:]

        new_insights = f'''
    <div class="insights-section">
        <h2>🔍 AI-Powered Analysis</h2>
        {claude_insights_html}
    </div>

    '''

        return before_insights + new_insights + after_insights

    def _replace_footer(self, html: str, data: Dict, date: str) -> str:
        """Replace footer with report metadata."""
        month = data.get('month', 'Unknown')
        day = data.get('day', 0)
        year = data.get('year', 0)
        survey_fy = data.get('survey_financial_year', data.get('financial_year', 'Unknown'))

        generated_date = datetime.now().strftime('%b %d, %Y')

        new_footer = f'''<div class="footer">
        <p><strong>Report Generated:</strong> {generated_date} | <strong>Report Date:</strong> {month} {day}, {year}</p>
        <p style="margin-top: 10px;"><strong>Data Sources:</strong> Sales Orders, Billing, Deliveries | <strong>Customer Survey:</strong> FY {survey_fy}</p>
    </div>'''

        html = re.sub(
            r'<div class="footer">.*?</div>',
            new_footer,
            html,
            flags=re.DOTALL
        )

        return html


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def generate_crm_dashboard(
    analysis_data: Dict[str, Any],
    claude_insights_html: str,
    date: str,
    template_path: str = None
) -> str:
    """
    Convenience function to generate CRM dashboard.

    Args:
        analysis_data: Analysis data from CRMDataProcessor
        claude_insights_html: HTML from Claude analyzer
        date: Date string
        template_path: Optional template path

    Returns:
        Complete HTML string
    """
    engine = CRMTemplateEngine(template_path)
    return engine.generate_dashboard(analysis_data, claude_insights_html, date)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['CRMTemplateEngine', 'generate_crm_dashboard']


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test template engine"""
    print("CRM Template Engine module loaded successfully")
    print("Use CRMTemplateEngine(template_path).generate_dashboard(...) to generate dashboard")