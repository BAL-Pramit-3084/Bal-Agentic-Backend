"""
ENV Template Engine
===================
Template engine for Environment Department Dashboard.

This module:
1. Loads the env_dashboard.html template
2. Replaces all hardcoded values with real data
3. Updates charts with actual data
4. Injects Claude-generated insights
5. Handles empty data gracefully

Replacement Strategy:
- Header: Date badge, title
- Executive Summary: 6 KPI cards
- Data Gap Alert: Dynamic warnings
- Food Waste: Chart + metrics
- STP Water: Chart + metrics
- CBAM Emissions: Chart + metrics
- License Status: Status list
- Air Quality: Chart data
- Industrial Waste: Metrics grid
- Compliance Returns: Table
- Insights Section: Claude-generated content
- Footer: Report metadata

Author: BAL-Agentic-Backend Team
Date: December 2025
"""

import re
import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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


def to_js_array(data: List) -> str:
    """Convert Python list to JavaScript array string."""
    return json.dumps(data)


# ============================================================================
# ENV TEMPLATE ENGINE CLASS
# ============================================================================

class ENVTemplateEngine:
    """
    Template engine for Environment Department Dashboard.
    """

    def __init__(self, template_path: str = None):
        """
        Initialize with template path.

        Args:
            template_path: Path to env_dashboard.html template
        """
        if template_path is None:
            # Template is in root templates/ folder
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            template_path = os.path.join(project_root, "templates", "env_dashboard.html")

        self.template_path = template_path
        logger.info(f"ENV Template Engine initialized with template: {template_path}")

    def generate_dashboard(
        self,
        analysis_data: Dict[str, Any],
        claude_insights_html: str,
        date: str
    ) -> str:
        """
        Generate complete dashboard HTML with real data.

        Args:
            analysis_data: The analysisData dict from ENVDataProcessor
            claude_insights_html: HTML string from Claude analyzer
            date: Date string (YYYY-MM-DD)

        Returns:
            Complete HTML string for the dashboard
        """
        logger.info(f"Generating ENV dashboard for date: {date}")

        # Load template
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template not found: {self.template_path}")

        with open(self.template_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # Apply all replacements
        html = self._replace_header(html, analysis_data)
        html = self._replace_executive_summary(html, analysis_data)
        html = self._replace_data_gap_alert(html, analysis_data)
        html = self._replace_food_waste_section(html, analysis_data)
        html = self._replace_stp_water_section(html, analysis_data)
        html = self._replace_cbam_section(html, analysis_data)
        html = self._replace_license_status(html, analysis_data)
        html = self._replace_air_quality_chart(html, analysis_data)
        html = self._replace_industrial_waste(html, analysis_data)
        html = self._replace_compliance_returns_table(html, analysis_data)
        html = self._replace_insights(html, claude_insights_html)
        html = self._replace_footer(html, analysis_data, date)

        # Fix JavaScript highlight index (hardcoded as 16 for Nov 17)
        day = analysis_data.get('day', 1)
        html = re.sub(
            r'if \(index === \d+\)',
            f'if (index === {day - 1})',
            html
        )

        logger.info(f"Dashboard generation complete ({len(html)} characters)")
        return html

    # ========================================================================
    # REPLACEMENT METHODS
    # ========================================================================

    def _replace_header(self, html: str, data: Dict) -> str:
        """Replace header section with real date."""
        date_formatted = data.get('date_formatted', 'Unknown Date')
        month = data.get('month', 'Unknown')
        month_abbrev = data.get('month_abbrev', month[:3])
        day = data.get('day', 0)
        year = data.get('year', 0)
        day_name = data.get('day_name', 'Unknown')

        # Replace title
        html = re.sub(
            r'<title>.*?</title>',
            f'<title>Environmental KPI Dashboard | {month} {day}, {year} | Balasore Alloys</title>',
            html
        )

        # Replace date in date-badge
        html = re.sub(
            r'<div class="date-text">.*?</div>',
            f'<div class="date-text">{month} {day}, {year}</div>',
            html,
            count=1
        )

        # Replace day name
        html = re.sub(
            r'<div class="day">.*?</div>',
            f'<div class="day">{day_name}</div>',
            html,
            count=1
        )

        # Replace ALL hardcoded "November 2025" style month/year references
        # Pattern: "Month YYYY" (full month name)
        html = re.sub(
            r'(Food Waste Tracking - )\w+ \d{4}',
            rf'\g<1>{month} {year}',
            html
        )

        html = re.sub(
            r'(STP Water Flow Trend - )\w+ \d{4}',
            rf'\g<1>{month} {year}',
            html
        )

        # Air Quality label - will be updated in _replace_air_quality_chart with actual data month

        # Replace "Nov 17 Breakdown" with actual date
        html = re.sub(
            r'(card-title">)\w{3} \d{1,2} Breakdown',
            rf'\g<1>{month_abbrev} {day} Breakdown',
            html
        )

        # Also handle "Nov Avg Flow" label
        html = re.sub(
            r'\w{3} Avg Flow',
            f'{month_abbrev} Avg Flow',
            html
        )

        return html

    def _replace_executive_summary(self, html: str, data: Dict) -> str:
        """Replace all 6 executive summary cards."""
        exec_summary = data.get('executive_summary', {})

        # Card 1: Food Waste
        food = exec_summary.get('food_waste', {})
        html = self._replace_summary_card(
            html,
            card_index=1,
            label="Food Waste",
            value=str(food.get('value', 0)),
            subtext=food.get('subtext', 'kg')
        )

        # Card 2: Persons Served
        persons = exec_summary.get('persons_served', {})
        html = self._replace_summary_card(
            html,
            card_index=2,
            label="Persons Served",
            value=str(persons.get('value', 0)),
            subtext=persons.get('subtext', 'Across all locations')
        )

        # Card 3: STP Water Treated
        stp = exec_summary.get('stp_water', {})
        html = self._replace_summary_card(
            html,
            card_index=3,
            label="STP Water Treated",
            value=str(int(stp.get('value', 0))),
            subtext=f"KL {stp.get('subtext', 'daily flow')}"
        )

        # Card 4: Compliance Score
        compliance = exec_summary.get('compliance_score', {})
        html = self._replace_summary_card(
            html,
            card_index=4,
            label="Compliance Score",
            value=str(compliance.get('value', '0%')),
            subtext=compliance.get('subtext', 'All returns filed')
        )

        # Card 5: Env Incidents
        incidents = exec_summary.get('incidents', {})
        html = self._replace_summary_card(
            html,
            card_index=5,
            label="Env Incidents",
            value=str(incidents.get('value', 0)),
            subtext=incidents.get('subtext', 'Zero incidents reported')
        )

        # Card 6: CBAM Emissions
        cbam = exec_summary.get('cbam_emissions', {})
        html = self._replace_summary_card(
            html,
            card_index=6,
            label="CBAM Emissions",
            value=str(cbam.get('value', '0.00')),
            subtext=f"tCO₂e/MT ({cbam.get('subtext', 'trend')})"
        )

        return html

    def _replace_summary_card(
        self,
        html: str,
        card_index: int,
        label: str,
        value: str,
        subtext: str
    ) -> str:
        """Replace a single summary card by finding its pattern."""
        # Pattern to find summary cards by their label
        pattern = rf'(<div class="summary-card[^"]*">\s*<div class="summary-label">{label}</div>\s*<div class="summary-value">)([^<]*)(</div>\s*<div class="summary-subtext">)([^<]*)(</div>)'

        replacement = rf'\g<1>{value}\g<3>{subtext}\g<5>'

        html = re.sub(pattern, replacement, html, flags=re.IGNORECASE | re.DOTALL)
        return html

    def _replace_data_gap_alert(self, html: str, data: Dict) -> str:
        """Replace or hide data gap alert."""
        data_gaps = data.get('data_gaps', [])

        if not data_gaps:
            # Hide the alert by replacing with empty div
            html = re.sub(
                r'<div class="data-gap-alert">.*?</div>\s*</div>',
                '<!-- No data gaps detected -->',
                html,
                flags=re.DOTALL,
                count=1
            )
        else:
            # Replace with first gap alert
            gap = data_gaps[0]
            new_alert = f'''<div class="data-gap-alert">
            <span class="alert-icon">{gap.get('icon', '⚠️')}</span>
            <div class="alert-content">
                <h4>{gap.get('title', 'Data Gap Identified')}</h4>
                <p>{gap.get('message', '')}</p>
            </div>
        </div>'''

            html = re.sub(
                r'<div class="data-gap-alert">.*?</div>\s*</div>',
                new_alert,
                html,
                flags=re.DOTALL,
                count=1
            )

        return html

    def _replace_food_waste_section(self, html: str, data: Dict) -> str:
        """Replace food waste section data and chart."""
        food_waste = data.get('food_waste', {})
        td = food_waste.get('td', {})
        mtd = food_waste.get('mtd', {})
        chart = food_waste.get('chart', {})
        by_location = td.get('by_location', {})

        # Define known locations with their default values (0 if no data)
        # Also include aliases for common typos/variations in database
        location_aliases = {
            "Plant Canteen": ["plant canteen", "plant canteen balasore"],
            "Bachelor Hostel": ["bachelor hostel", "batchelor hostel", "batchelor hostel canteen", "bachelor hostel canteen"],
            "Plant Rest House": ["plant rest house", "rest house", "plant rest house canteen"],
        }

        known_locations = {
            "Plant Canteen": {"waste_kg": 0, "persons": 0},
            "Bachelor Hostel": {"waste_kg": 0, "persons": 0},
            "Plant Rest House": {"waste_kg": 0, "persons": 0},
        }

        # Override with actual data if available (using aliases for matching)
        for loc, loc_data in by_location.items():
            loc_lower = loc.lower().strip()
            for known_loc, aliases in location_aliases.items():
                # Check if database location matches any alias
                if any(alias in loc_lower or loc_lower in alias for alias in aliases):
                    known_locations[known_loc] = loc_data
                    break

        # Replace each location's waste and persons
        for location, loc_data in known_locations.items():
            waste = loc_data.get('waste_kg', 0)
            persons = loc_data.get('persons', 0)

            # Replace waste kg value
            html = re.sub(
                rf'(<div class="metric-label">{re.escape(location)}</div>\s*<div class="metric-value">)[\d.]+(<span class="metric-unit">kg</span>)',
                rf'\g<1>{waste}\g<2>',
                html,
                flags=re.DOTALL
            )

            # Replace persons count (in separate div after the waste value)
            html = re.sub(
                rf'({re.escape(location)}.*?<span class="metric-unit">kg</span></div>.*?)(\d+)( persons</div>)',
                rf'\g<1>{persons}\g<3>',
                html,
                flags=re.DOTALL
            )

        # Replace waste per person
        waste_per_person = td.get('waste_per_person', 0)
        html = re.sub(
            r'(<div class="metric-label">Waste/Person</div>\s*<div class="metric-value">)[\d.]+(<span class="metric-unit">gm</span>)',
            rf'\g<1>{waste_per_person:.0f}\g<2>',
            html
        )

        # Replace chart data
        chart_labels = chart.get('labels', [])
        chart_waste = chart.get('waste_data', [])
        chart_persons = chart.get('persons_data', [])

        # Food Waste Chart - labels
        html = re.sub(
            r"(const foodWasteCtx.*?labels: )\[.*?\](,)",
            rf"\g<1>{to_js_array(chart_labels)}\g<2>",
            html,
            flags=re.DOTALL
        )

        # Food Waste Chart - waste data
        html = re.sub(
            r"(label: 'Food Waste \(kg\)'.*?data: )\[.*?\](,)",
            rf"\g<1>{to_js_array(chart_waste)}\g<2>",
            html,
            flags=re.DOTALL
        )

        # Food Waste Chart - persons data
        html = re.sub(
            r"(label: 'Persons Served'.*?data: )\[.*?\](,)",
            rf"\g<1>{to_js_array(chart_persons)}\g<2>",
            html,
            flags=re.DOTALL
        )

        # Update card badge if zero waste
        if td.get('is_zero_waste', False):
            html = re.sub(
                r'<span class="card-badge badge-\w+">.*?Zero Waste.*?</span>',
                '<span class="card-badge badge-success">✓ Zero Waste</span>',
                html
            )

        return html

    def _replace_stp_water_section(self, html: str, data: Dict) -> str:
        """Replace STP water section data and chart."""
        stp = data.get('stp_water', {})
        td = stp.get('td', {})
        mtd = stp.get('mtd', {})
        chart = stp.get('chart', {})

        # Replace metric values
        html = re.sub(
            r'(<div class="metric-label">Initial Reading</div>\s*<div class="metric-value">)[\d,]+',
            rf'\g<1>{format_number(td.get("initial_reading", 0))}',
            html
        )

        html = re.sub(
            r'(<div class="metric-label">Final Reading</div>\s*<div class="metric-value">)[\d,]+',
            rf'\g<1>{format_number(td.get("final_reading", 0))}',
            html
        )

        html = re.sub(
            r'(<div class="metric-label">Daily Flow</div>\s*<div class="metric-value">)[\d]+(<span class="metric-unit">KL</span>)',
            rf'\g<1>{int(td.get("daily_flow", 0))}\g<2>',
            html
        )

        html = re.sub(
            r'(<div class="metric-label">\w{3} Avg Flow</div>\s*<div class="metric-value">)[\d.]+(<span class="metric-unit">KL</span>)',
            rf'\g<1>{mtd.get("avg_flow", 0):.1f}\g<2>',
            html
        )

        # Replace chart data
        chart_labels = chart.get('labels', [])
        chart_data = chart.get('data', [])
        avg_flow = mtd.get("avg_flow", 0)

        html = re.sub(
            r"(const stpWaterCtx.*?labels: )\[.*?\](,)",
            rf"\g<1>{to_js_array(chart_labels)}\g<2>",
            html,
            flags=re.DOTALL
        )

        html = re.sub(
            r"(label: 'Daily Flow \(KL\)'.*?data: )\[.*?\](,)",
            rf"\g<1>{to_js_array(chart_data)}\g<2>",
            html,
            flags=re.DOTALL
        )

        # Fix the chart annotation line (yMin and yMax hardcoded values)
        html = re.sub(
            r'(yMin: )[\d.]+',
            rf'\g<1>{avg_flow:.1f}',
            html
        )
        html = re.sub(
            r'(yMax: )[\d.]+',
            rf'\g<1>{avg_flow:.1f}',
            html
        )

        return html

    def _replace_cbam_section(self, html: str, data: Dict) -> str:
        """Replace CBAM emissions section data and chart."""
        cbam = data.get('cbam_emissions', {})

        if not cbam.get('has_data', False):
            return html

        current = cbam.get('current', {})
        trend = cbam.get('trend', {})
        chart = cbam.get('chart', {})

        # Replace CBAM metric cards
        direct = current.get('direct', 0)
        indirect = current.get('indirect', 0)
        total = current.get('total', 0)

        # Direct emissions
        html = re.sub(
            r'(<div class="cbam-card direct">.*?<div class="value">)[\d.]+',
            rf'\g<1>{direct:.3f}',
            html,
            flags=re.DOTALL
        )

        # Indirect emissions
        html = re.sub(
            r'(<div class="cbam-card indirect">.*?<div class="value">)[\d.]+',
            rf'\g<1>{indirect:.3f}',
            html,
            flags=re.DOTALL
        )

        # Total emissions
        html = re.sub(
            r'(<div class="cbam-card total">.*?<div class="value">)[\d.]+',
            rf'\g<1>{total:.3f}',
            html,
            flags=re.DOTALL
        )

        # Replace trend indicators
        direct_trend = trend.get('direct', {})
        indirect_trend = trend.get('indirect', {})
        total_trend = trend.get('total', {})
        prev_month = trend.get('prev_month', 'Sep')

        def get_trend_html(trend_data: Dict, prev: str) -> str:
            direction = trend_data.get('direction', 'stable')
            pct = trend_data.get('pct', 0)
            if direction == 'up':
                return f'<div class="trend-indicator trend-up">↑ +{pct}% vs {prev}</div>'
            elif direction == 'down':
                return f'<div class="trend-indicator trend-down">↓ -{pct}% vs {prev}</div>'
            else:
                return f'<div class="trend-indicator trend-stable">→ {pct}% vs {prev}</div>'

        # Update trend indicators (simplified - just update percentages)
        html = re.sub(
            r'<div class="trend-indicator trend-\w+">.*?vs \w+</div>',
            get_trend_html(direct_trend, prev_month),
            html,
            count=1
        )

        # Replace CBAM chart data
        chart_labels = chart.get('labels', [])
        chart_direct = chart.get('direct', [])
        chart_indirect = chart.get('indirect', [])
        chart_total = chart.get('total', [])
        chart_threshold = chart.get('threshold', [])

        html = re.sub(
            r"(const cbamCtx.*?labels: )\[.*?\](,)",
            rf"\g<1>{to_js_array(chart_labels)}\g<2>",
            html,
            flags=re.DOTALL
        )

        # Replace each dataset
        html = re.sub(
            r"(label: 'Direct Emissions'.*?data: )\[.*?\](,)",
            rf"\g<1>{to_js_array(chart_direct)}\g<2>",
            html,
            flags=re.DOTALL
        )

        html = re.sub(
            r"(label: 'Indirect Emissions'.*?data: )\[.*?\](,)",
            rf"\g<1>{to_js_array(chart_indirect)}\g<2>",
            html,
            flags=re.DOTALL
        )

        html = re.sub(
            r"(label: 'Total Emissions'.*?data: )\[.*?\](,)",
            rf"\g<1>{to_js_array(chart_total)}\g<2>",
            html,
            flags=re.DOTALL
        )

        html = re.sub(
            r"(label: 'Transitional Threshold'.*?data: )\[.*?\](,)",
            rf"\g<1>{to_js_array(chart_threshold)}\g<2>",
            html,
            flags=re.DOTALL
        )

        return html

    def _replace_license_status(self, html: str, data: Dict) -> str:
        """Replace license status section."""
        licenses_data = data.get('licenses', {})
        licenses_list = licenses_data.get('licenses', [])[:5]  # Show top 5

        if not licenses_list:
            return html

        # Build new license status HTML
        license_items = []
        for lic in licenses_list:
            location = lic.get('location', '')
            lic_type = lic.get('type', '').strip()
            status_class = lic.get('status_class', 'status-valid')
            status_text = lic.get('status_text', 'Valid')

            # Determine badge symbol
            if 'valid' in status_class:
                symbol = '✓'
            elif 'expiring' in status_class:
                symbol = '⚡'
            else:
                symbol = '✗'

            license_items.append(f'''
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid var(--border-color);">
                        <span style="color: var(--text-secondary);">{lic_type} {location}</span>
                        <span class="status-badge {status_class}">{symbol} {status_text}</span>
                    </div>''')

        # Join items and replace
        items_html = ''.join(license_items)

        # Find and replace the license status content
        html = re.sub(
            r'(<div class="card-header">.*?License Status.*?</div>\s*<div style="margin-top: 10px;">).*?(</div>\s*</div>\s*<!-- Air Quality)',
            rf'\g<1>{items_html}\g<2>',
            html,
            flags=re.DOTALL
        )

        return html

    def _replace_air_quality_chart(self, html: str, data: Dict) -> str:
        """Replace air quality chart data."""
        air_quality = data.get('air_quality', {})

        if not air_quality.get('has_data', False):
            return html

        # Replace the air quality section title with actual data month
        data_month = air_quality.get('data_month', '')
        data_year = air_quality.get('data_year', '')
        if data_month and data_year:
            html = re.sub(
                r'(Ambient Air Quality \()\w+ \d{4}(\))',
                rf'\g<1>{data_month} {data_year}\g<2>',
                html
            )

        chart = air_quality.get('chart', {})
        labels = chart.get('labels', [])
        datasets = chart.get('datasets', {})

        # Replace chart labels
        html = re.sub(
            r"(const airQualityCtx.*?labels: )\[.*?\](,)",
            rf"\g<1>{to_js_array(labels)}\g<2>",
            html,
            flags=re.DOTALL
        )

        # Replace each pollutant dataset
        for pollutant, values in datasets.items():
            pattern = rf"(label: '{pollutant}.*?data: )\[.*?\](,)"
            html = re.sub(
                pattern,
                rf"\g<1>{to_js_array(values)}\g<2>",
                html,
                flags=re.DOTALL
            )

        return html

    def _replace_industrial_waste(self, html: str, data: Dict) -> str:
        """Replace industrial waste (slag/GCP) section."""
        industrial = data.get('industrial_waste', {})

        if not industrial.get('has_data', False):
            return html

        current = industrial.get('current', {})

        # Replace metric values
        production = current.get('production_mt', 0)
        slag = current.get('slag_mt', 0)
        gcp_dust = current.get('gcp_dust_mt', 0)
        slag_ratio = current.get('slag_ratio_pct', 0)

        html = re.sub(
            r'(<div class="metric-label">Production</div>\s*<div class="metric-value">)[\d,]+(<span class="metric-unit">MT</span>)',
            rf'\g<1>{format_number(production)}\g<2>',
            html
        )

        html = re.sub(
            r'(<div class="metric-label">Slag Generated</div>\s*<div class="metric-value">)[\d,]+(<span class="metric-unit">MT</span>)',
            rf'\g<1>{format_number(slag)}\g<2>',
            html
        )

        html = re.sub(
            r'(<div class="metric-label">GCP Dust</div>\s*<div class="metric-value">)[\d,]+(<span class="metric-unit">MT</span>)',
            rf'\g<1>{format_number(gcp_dust)}\g<2>',
            html
        )

        html = re.sub(
            r'(<div class="metric-label">Slag Ratio</div>\s*<div class="metric-value">)[\d.]+(<span class="metric-unit">%</span>)',
            rf'\g<1>{slag_ratio:.1f}\g<2>',
            html
        )

        return html

    def _replace_compliance_returns_table(self, html: str, data: Dict) -> str:
        """Replace compliance returns table."""
        compliance = data.get('compliance_returns', {})
        returns_list = compliance.get('returns', [])[:5]  # Show top 5

        if not returns_list:
            return html

        # Build table rows
        rows = []
        for ret in returns_list:
            area = ret.get('area', '')
            subject = ret.get('subject', '')
            frequency = ret.get('frequency', '')
            authority = ret.get('authority', '')[:30]
            status = ret.get('status', '')
            is_complied = ret.get('is_complied', False)

            status_class = 'status-valid' if is_complied else 'status-expiring'
            status_symbol = '✓' if is_complied else '⚠'

            rows.append(f'''
                        <tr>
                            <td>{area}</td>
                            <td>{subject}</td>
                            <td>{frequency}</td>
                            <td>{authority}</td>
                            <td><span class="status-badge {status_class}">{status_symbol} {status[:30]}</span></td>
                        </tr>''')

        rows_html = ''.join(rows)

        # Replace table body
        html = re.sub(
            r'(<table class="compliance-table">.*?<tbody>).*?(</tbody>)',
            rf'\g<1>{rows_html}\g<2>',
            html,
            flags=re.DOTALL
        )

        # Update compliance rate badge
        rate = compliance.get('compliance_rate', 0)
        badge_class = 'badge-success' if rate == 100 else 'badge-warning'
        html = re.sub(
            r'<span class="card-badge badge-\w+">.*?Complied</span>',
            f'<span class="card-badge {badge_class}">{rate:.0f}% Complied</span>',
            html
        )

        return html

    def _replace_insights(self, html: str, claude_insights_html: str) -> str:
        """Replace insights section with Claude-generated content."""
        if not claude_insights_html:
            logger.warning("No Claude insights provided - keeping template insights")
            return html

        # Find the insights section
        insight_match = re.search(r'<section class="insights-section">', html)
        if not insight_match:
            logger.warning("Could not find insights section in template")
            return html

        # Find position of footer
        footer_match = re.search(r'<footer class="footer">', html)
        if not footer_match:
            logger.warning("Could not find footer in template")
            return html

        # Get positions
        insight_start = insight_match.start()
        footer_start = footer_match.start()

        # Build new insights section
        before_insights = html[:insight_start]
        after_insights = html[footer_start:]

        new_insights = f'''<section class="insights-section">
            <div class="insights-header">
                <h2>🤖 AI-Powered Environmental Insights</h2>
                <span class="ai-badge">Deep Analysis</span>
            </div>

            {claude_insights_html}
        </section>

        '''

        return before_insights + new_insights + after_insights

    def _replace_footer(self, html: str, data: Dict, date: str) -> str:
        """Replace footer with report metadata."""
        month = data.get('month', 'Unknown')
        day = data.get('day', 0)
        year = data.get('year', 0)

        generated_date = datetime.now().strftime('%B %d, %Y')

        new_footer = f'''<footer class="footer">
            <div>
                <strong>Environmental KPI Dashboard</strong> • Balasore Alloys Limited
                <br><span style="font-size: 0.85em;">Data Source: balcorpdb | Report Generated: {generated_date}</span>
            </div>
            <div class="footer-stats">
                <div class="footer-stat">
                    <span>📊</span> 14 Tables Analyzed
                </div>
                <div class="footer-stat">
                    <span>🔍</span> {day} Days MTD Coverage
                </div>
                <div class="footer-stat">
                    <span>✅</span> Real-time Data
                </div>
            </div>
        </footer>'''

        html = re.sub(
            r'<footer class="footer">.*?</footer>',
            new_footer,
            html,
            flags=re.DOTALL
        )

        return html


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def generate_env_dashboard(
    analysis_data: Dict[str, Any],
    claude_insights_html: str,
    date: str,
    template_path: str = None
) -> str:
    """
    Convenience function to generate ENV dashboard.

    Args:
        analysis_data: Analysis data from ENVDataProcessor
        claude_insights_html: HTML from Claude analyzer
        date: Date string
        template_path: Optional template path

    Returns:
        Complete HTML string
    """
    engine = ENVTemplateEngine(template_path)
    return engine.generate_dashboard(analysis_data, claude_insights_html, date)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['ENVTemplateEngine', 'generate_env_dashboard']


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test template engine"""
    print("ENV Template Engine module loaded successfully")
    print("Use ENVTemplateEngine(template_path).generate_dashboard(...) to generate dashboard")