"""
Automobile Template Engine - FIXED VERSION
===========================================
Template engine for Automobile/Fleet Management Dashboard.

FIXES APPLIED:
- Direct string replacement instead of complex regex for KPIs
- Proper table replacement for Top Performers
- Fixed MTD values replacement
- Fixed idle summary dynamic text

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


def to_js_string_array(data: List[str]) -> str:
    """Convert Python list of strings to JS array with quotes."""
    return json.dumps(data)


# ============================================================================
# AUTOMOBILE TEMPLATE ENGINE CLASS
# ============================================================================

class AutomobileTemplateEngine:
    """
    Template engine for Automobile/Fleet Management Dashboard.
    Uses direct string replacement for reliability.
    """

    def __init__(self, template_path: str = None):
        """
        Initialize with template path.

        Args:
            template_path: Path to automobile_dashboard.html template
        """
        if template_path is None:
            # Default: Template is in templates/ folder at project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            template_path = os.path.join(project_root, "templates", "automobile_dashboard.html")

        self.template_path = template_path
        logger.info(f"Automobile Template Engine initialized with template: {template_path}")

    def generate_dashboard(
        self,
        analysis_data: Dict[str, Any],
        claude_insights_html: str,
        date: str
    ) -> str:
        """
        Generate complete dashboard HTML with real data.

        Args:
            analysis_data: The data dict from AutomobileDataProcessor
            claude_insights_html: HTML string from Claude analyzer
            date: Date string (YYYY-MM-DD)

        Returns:
            Complete HTML string for the dashboard
        """
        logger.info(f"Generating Automobile dashboard for date: {date}")

        # Load template
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template not found: {self.template_path}")

        with open(self.template_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # Apply all replacements in order
        html = self._replace_header(html, analysis_data)
        html = self._replace_daily_kpis(html, analysis_data)
        html = self._replace_mtd_summary(html, analysis_data)
        html = self._replace_top_performers_table(html, analysis_data)
        html = self._replace_idle_analysis(html, analysis_data)
        html = self._replace_truck_details_table(html, analysis_data)
        html = self._replace_chart_data(html, analysis_data)
        html = self._replace_idle_trucks_section(html, analysis_data)
        html = self._replace_insights_section(html, claude_insights_html)
        html = self._replace_footer(html, analysis_data)

        logger.info(f"Dashboard generation complete ({len(html)} characters)")
        return html

    # ========================================================================
    # REPLACEMENT METHODS
    # ========================================================================

    def _replace_header(self, html: str, data: Dict) -> str:
        """Replace header section with real date."""
        month = data.get('month', 'Unknown')
        month_abbrev = data.get('month_abbrev', 'Unk')
        day = data.get('day', 1)
        year = data.get('year', 2025)
        day_name = data.get('day_name', 'Unknown')

        # Replace <title>
        html = re.sub(
            r'<title>.*?</title>',
            f'<title>Truck Fleet Dashboard - {month} {day}, {year}</title>',
            html
        )

        # Replace date badge: "📅 December 16, 2025 (Monday)"
        html = re.sub(
            r'<div class="date-badge">📅.*?</div>',
            f'<div class="date-badge">📅 {month} {day}, {year} ({day_name})</div>',
            html
        )

        # Replace section titles with dates
        # "Top Performers - Dec 16, 2025"
        html = re.sub(
            r'(Top Performers - )\w{3} \d{1,2}, \d{4}',
            rf'\g<1>{month_abbrev} {day}, {year}',
            html
        )

        # "Idle Time Analysis - Dec 16"
        html = re.sub(
            r'(Idle Time Analysis - )\w{3} \d{1,2}',
            rf'\g<1>{month_abbrev} {day}',
            html
        )

        # "Complete Truck Trip Report - December 16, 2025"
        html = re.sub(
            r'(Complete Truck Trip Report - )\w+ \d{1,2}, \d{4}',
            rf'\g<1>{month} {day}, {year}',
            html
        )

        # "Mileage Performance - Dec 16"
        html = re.sub(
            r'(Mileage Performance - )\w{3} \d{1,2}',
            rf'\g<1>{month_abbrev} {day}',
            html
        )

        # "Idle Trucks Analysis - Dec 16"
        html = re.sub(
            r'(Idle Trucks Analysis - )\w{3} \d{1,2}',
            rf'\g<1>{month_abbrev} {day}',
            html
        )

        # "Daily Distance Trend (Dec 1-16)"
        html = re.sub(
            r'Daily Distance Trend \(\w{3} \d{1,2}-\d{1,2}\)',
            f'Daily Distance Trend ({month_abbrev} 1-{day})',
            html
        )

        # "Executive Summary - December 16, 2025"
        html = re.sub(
            r'(Executive Summary - )\w+ \d{1,2}, \d{4}',
            rf'\g<1>{month} {day}, {year}',
            html
        )

        return html

    def _replace_daily_kpis(self, html: str, data: Dict) -> str:
        """
        Replace all 8 daily KPI cards using DIRECT string replacement.
        This is more reliable than complex regex.
        """
        kpis = data.get('kpis', {})

        # =====================================================================
        # KPI 1: Total Trucks (static 35, just ensure it's there)
        # =====================================================================
        # No change needed - always 35

        # =====================================================================
        # KPI 2: Active Trucks
        # =====================================================================
        active_trucks = kpis.get('active_trucks', 0)
        utilization = kpis.get('utilization_pct', 0)
        util_class = "negative" if utilization < 60 else "positive"

        # Find and replace Active Trucks card
        old_active = re.search(
            r'<div class="kpi-card">\s*<div class="kpi-value">\d+</div>\s*<div class="kpi-label">Active Trucks</div>\s*<div class="kpi-change \w+">[^<]+</div>\s*</div>',
            html, re.DOTALL
        )
        if old_active:
            new_active = f'''<div class="kpi-card">
            <div class="kpi-value">{active_trucks}</div>
            <div class="kpi-label">Active Trucks</div>
            <div class="kpi-change {util_class}">{utilization}% Utilized</div>
        </div>'''
            html = html[:old_active.start()] + new_active + html[old_active.end():]

        # =====================================================================
        # KPI 3: Total Distance
        # =====================================================================
        total_distance = kpis.get('total_distance', 0)
        yesterday_dist = kpis.get('yesterday_distance', 0)
        dist_trend = kpis.get('distance_trend', '▼')
        dist_class = kpis.get('distance_class', 'negative')

        old_distance = re.search(
            r'<div class="kpi-card">\s*<div class="kpi-value">[\d,.]+</div>\s*<div class="kpi-label">Total Distance \(KM\)</div>\s*<div class="kpi-change \w+">[^<]+</div>\s*</div>',
            html, re.DOTALL
        )
        if old_distance:
            new_distance = f'''<div class="kpi-card">
            <div class="kpi-value">{format_number(total_distance, 1)}</div>
            <div class="kpi-label">Total Distance (KM)</div>
            <div class="kpi-change {dist_class}">{dist_trend} vs {format_number(yesterday_dist, 1)} Yesterday</div>
        </div>'''
            html = html[:old_distance.start()] + new_distance + html[old_distance.end():]

        # =====================================================================
        # KPI 4: Fuel Consumed
        # =====================================================================
        fuel_consumed = kpis.get('fuel_consumed', 0)
        yesterday_fuel = kpis.get('yesterday_fuel', 0)
        fuel_trend = kpis.get('fuel_trend', '▲')
        fuel_class = kpis.get('fuel_class', 'negative')

        old_fuel = re.search(
            r'<div class="kpi-card">\s*<div class="kpi-value">[\d,.]+</div>\s*<div class="kpi-label">Fuel Consumed \(L\)</div>\s*<div class="kpi-change \w+">[^<]+</div>\s*</div>',
            html, re.DOTALL
        )
        if old_fuel:
            new_fuel = f'''<div class="kpi-card">
            <div class="kpi-value">{format_number(fuel_consumed, 1)}</div>
            <div class="kpi-label">Fuel Consumed (L)</div>
            <div class="kpi-change {fuel_class}">{fuel_trend} vs {format_number(yesterday_fuel, 1)} Yesterday</div>
        </div>'''
            html = html[:old_fuel.start()] + new_fuel + html[old_fuel.end():]

        # =====================================================================
        # KPI 5: Avg Mileage
        # =====================================================================
        avg_kmpl = kpis.get('avg_kmpl', 0)

        old_mileage = re.search(
            r'<div class="kpi-card">\s*<div class="kpi-value">[\d.]+</div>\s*<div class="kpi-label">Avg Mileage \(KMPL\)</div>\s*<div class="kpi-change \w+">[^<]+</div>\s*</div>',
            html, re.DOTALL
        )
        if old_mileage:
            new_mileage = f'''<div class="kpi-card">
            <div class="kpi-value">{avg_kmpl}</div>
            <div class="kpi-label">Avg Mileage (KMPL)</div>
            <div class="kpi-change neutral">Fleet Average</div>
        </div>'''
            html = html[:old_mileage.start()] + new_mileage + html[old_mileage.end():]

        # =====================================================================
        # KPI 6: Fuel Filled
        # =====================================================================
        fuel_filled = kpis.get('fuel_filled', 0)
        fillings_count = kpis.get('fillings_count', 0)

        old_filled = re.search(
            r'<div class="kpi-card">\s*<div class="kpi-value">[\d,.]+</div>\s*<div class="kpi-label">Fuel Filled \(L\)</div>\s*<div class="kpi-change \w+">[^<]+</div>\s*</div>',
            html, re.DOTALL
        )
        if old_filled:
            new_filled = f'''<div class="kpi-card">
            <div class="kpi-value">{format_number(fuel_filled, 1)}</div>
            <div class="kpi-label">Fuel Filled (L)</div>
            <div class="kpi-change positive">{fillings_count} Fillings</div>
        </div>'''
            html = html[:old_filled.start()] + new_filled + html[old_filled.end():]

        # =====================================================================
        # KPI 7: Max Speed
        # =====================================================================
        max_speed = kpis.get('max_speed', 0)
        speed_class = "positive" if max_speed <= 50 else "warning"
        speed_text = "Safe Range" if max_speed <= 50 else "⚠️ Check Speed"

        old_speed = re.search(
            r'<div class="kpi-card">\s*<div class="kpi-value">\d+</div>\s*<div class="kpi-label">Max Speed \(KM/H\)</div>\s*<div class="kpi-change \w+">[^<]+</div>\s*</div>',
            html, re.DOTALL
        )
        if old_speed:
            new_speed = f'''<div class="kpi-card">
            <div class="kpi-value">{max_speed}</div>
            <div class="kpi-label">Max Speed (KM/H)</div>
            <div class="kpi-change {speed_class}">{speed_text}</div>
        </div>'''
            html = html[:old_speed.start()] + new_speed + html[old_speed.end():]

        # =====================================================================
        # KPI 8: Fuel Drained
        # =====================================================================
        fuel_drained = kpis.get('fuel_drained', 0)
        theft_class = "positive" if fuel_drained == 0 else "negative"
        theft_text = "No Theft" if fuel_drained == 0 else "⚠️ Alert"

        old_drained = re.search(
            r'<div class="kpi-card">\s*<div class="kpi-value">\d+</div>\s*<div class="kpi-label">Fuel Drained \(L\)</div>\s*<div class="kpi-change \w+">[^<]+</div>\s*</div>',
            html, re.DOTALL
        )
        if old_drained:
            new_drained = f'''<div class="kpi-card">
            <div class="kpi-value">{int(fuel_drained)}</div>
            <div class="kpi-label">Fuel Drained (L)</div>
            <div class="kpi-change {theft_class}">{theft_text}</div>
        </div>'''
            html = html[:old_drained.start()] + new_drained + html[old_drained.end():]

        return html

    def _replace_mtd_summary(self, html: str, data: Dict) -> str:
        """Replace MTD summary section with direct replacements."""
        mtd = data.get('mtd', {})
        month_abbrev = data.get('month_abbrev', 'Dec')
        day = data.get('day', 1)
        year = data.get('year', 2025)

        # Update section title - handle first day of month gracefully
        if day == 1:
            mtd_date_range = f"{month_abbrev} {day}, {year}"
        else:
            mtd_date_range = f"{month_abbrev} 1-{day}, {year}"

        # Pattern matches both "Dec 1-16, 2025" and "Dec 1, 2025" formats
        html = re.sub(
            r'(Month-to-Date Summary \()\w{3} \d{1,2}(?:-\d{1,2})?, \d{4}\)',
            rf'\g<1>{mtd_date_range})',
            html
        )

        # =====================================================================
        # MTD Distance
        # =====================================================================
        mtd_distance = mtd.get('distance', 0)
        old_mtd_dist = re.search(
            r'<div class="mtd-card blue">\s*<div class="mtd-value blue">[\d,.]+ KM</div>\s*<div class="kpi-label">MTD Total Distance</div>\s*</div>',
            html, re.DOTALL
        )
        if old_mtd_dist:
            new_mtd_dist = f'''<div class="mtd-card blue">
                <div class="mtd-value blue">{format_number(mtd_distance, 1)} KM</div>
                <div class="kpi-label">MTD Total Distance</div>
            </div>'''
            html = html[:old_mtd_dist.start()] + new_mtd_dist + html[old_mtd_dist.end():]

        # =====================================================================
        # MTD Fuel Consumed
        # =====================================================================
        mtd_fuel_consumed = mtd.get('fuel_consumed', 0)
        old_mtd_fuel = re.search(
            r'<div class="mtd-card orange">\s*<div class="mtd-value orange">[\d,.]+ L</div>\s*<div class="kpi-label">MTD Fuel Consumed</div>\s*</div>',
            html, re.DOTALL
        )
        if old_mtd_fuel:
            new_mtd_fuel = f'''<div class="mtd-card orange">
                <div class="mtd-value orange">{format_number(mtd_fuel_consumed, 1)} L</div>
                <div class="kpi-label">MTD Fuel Consumed</div>
            </div>'''
            html = html[:old_mtd_fuel.start()] + new_mtd_fuel + html[old_mtd_fuel.end():]

        # =====================================================================
        # MTD Fuel Filled
        # =====================================================================
        mtd_fuel_filled = mtd.get('fuel_filled', 0)
        old_mtd_filled = re.search(
            r'<div class="mtd-card green">\s*<div class="mtd-value green">[\d,.]+ L</div>\s*<div class="kpi-label">MTD Fuel Filled</div>\s*</div>',
            html, re.DOTALL
        )
        if old_mtd_filled:
            new_mtd_filled = f'''<div class="mtd-card green">
                <div class="mtd-value green">{format_number(mtd_fuel_filled, 1)} L</div>
                <div class="kpi-label">MTD Fuel Filled</div>
            </div>'''
            html = html[:old_mtd_filled.start()] + new_mtd_filled + html[old_mtd_filled.end():]

        # =====================================================================
        # MTD Avg Mileage
        # =====================================================================
        mtd_avg_kmpl = mtd.get('avg_kmpl', 0)
        old_mtd_kmpl = re.search(
            r'<div class="mtd-card purple">\s*<div class="mtd-value purple">[\d.]+ KMPL</div>\s*<div class="kpi-label">MTD Avg Mileage</div>\s*</div>',
            html, re.DOTALL
        )
        if old_mtd_kmpl:
            new_mtd_kmpl = f'''<div class="mtd-card purple">
                <div class="mtd-value purple">{mtd_avg_kmpl} KMPL</div>
                <div class="kpi-label">MTD Avg Mileage</div>
            </div>'''
            html = html[:old_mtd_kmpl.start()] + new_mtd_kmpl + html[old_mtd_kmpl.end():]

        # =====================================================================
        # MTD Fuel Drained
        # =====================================================================
        mtd_fuel_drained = mtd.get('fuel_drained', 0)
        old_mtd_drained = re.search(
            r'<div class="mtd-card red">\s*<div class="mtd-value red">[\d.]+ L</div>\s*<div class="kpi-label">MTD Fuel Drained</div>\s*</div>',
            html, re.DOTALL
        )
        if old_mtd_drained:
            new_mtd_drained = f'''<div class="mtd-card red">
                <div class="mtd-value red">{format_number(mtd_fuel_drained, 1)} L</div>
                <div class="kpi-label">MTD Fuel Drained</div>
            </div>'''
            html = html[:old_mtd_drained.start()] + new_mtd_drained + html[old_mtd_drained.end():]

        # =====================================================================
        # Trucks With Trips
        # =====================================================================
        trucks_active = mtd.get('trucks_active', 0)
        old_trucks = re.search(
            r'<div class="mtd-card teal">\s*<div class="mtd-value teal">\d+</div>\s*<div class="kpi-label">Trucks With Trips</div>\s*</div>',
            html, re.DOTALL
        )
        if old_trucks:
            new_trucks = f'''<div class="mtd-card teal">
                <div class="mtd-value teal">{trucks_active}</div>
                <div class="kpi-label">Trucks With Trips</div>
            </div>'''
            html = html[:old_trucks.start()] + new_trucks + html[old_trucks.end():]

        return html

    def _replace_top_performers_table(self, html: str, data: Dict) -> str:
        """Replace top performers table - COMPLETE tbody replacement."""
        top_performers = data.get('top_performers', [])

        if not top_performers:
            logger.warning("No top performers data - keeping template")
            return html

        # Build table rows
        rows = []
        for perf in top_performers:
            row_class = 'class="highlight"' if perf.get('is_top3') else ''
            rank_display = perf.get('rank_display', str(perf.get('rank', '')))
            vehicle = perf.get('vehicle', '')
            distance = perf.get('distance', 0)
            fuel = perf.get('fuel', 0)
            kmpl_display = perf.get('kmpl_display', '0.00')
            badge_class = perf.get('badge_class', 'badge-warning')
            engine_hours = perf.get('engine_hours', '0:00')

            # Bold for top 3
            vehicle_display = f'<strong>{vehicle}</strong>' if perf.get('is_top3') else vehicle

            rows.append(f'''                    <tr {row_class}>
                        <td>{rank_display}</td>
                        <td>{vehicle_display}</td>
                        <td>{distance:.2f} km</td>
                        <td>{fuel:.1f} L</td>
                        <td><span class="badge {badge_class}">{kmpl_display}</span></td>
                        <td>{engine_hours}</td>
                    </tr>''')

        rows_html = '\n'.join(rows)

        # Build anomaly note
        anomalies = [p for p in top_performers if p.get('is_anomaly')]
        if anomalies:
            anomaly_note = "; ".join([
                f"* {a['vehicle']}: Anomalous mileage ({a['kmpl']:.1f} KMPL) indicates sensor malfunction"
                for a in anomalies
            ])
        else:
            anomaly_note = "All trucks operating within normal mileage parameters"

        # Find the Top Performers section and replace tbody
        # Pattern: from <tbody> after Top Performers to </tbody>
        pattern = r'(<div class="section-title"><div class="icon">🏆</div>Top Performers[^<]*</div>\s*<table class="data-table">\s*<thead>[\s\S]*?</thead>\s*<tbody>)[\s\S]*?(</tbody>\s*</table>\s*<div class="summary-box"[^>]*>\s*<div[^>]*>)[^<]*(</div>)'

        replacement = rf'\g<1>\n{rows_html}\n                \g<2>{anomaly_note}\g<3>'

        html = re.sub(pattern, replacement, html, count=1)

        return html

    def _replace_idle_analysis(self, html: str, data: Dict) -> str:
        """Replace idle time analysis section - progress bars and summary."""
        idle_analysis = data.get('idle_analysis', {})
        by_truck = idle_analysis.get('by_truck', [])[:5]  # Top 5 idlers

        if not by_truck:
            logger.warning("No idle analysis data - keeping template")
            return html

        # Build progress bars HTML
        progress_bars = []
        for truck in by_truck:
            vehicle = truck.get('vehicle', '')
            idle_hours_display = truck.get('idle_hours_display', '0:00')
            idle_pct = truck.get('idle_pct', 0)
            category = truck.get('category', 'Low')
            css_class = truck.get('css_class', 'low')
            progress_color = truck.get('progress_color', 'green')

            progress_bars.append(f'''            <div class="progress-bar-container">
                <div class="progress-label"><span>{vehicle} - Idle: {idle_hours_display} hrs ({idle_pct}% of engine time)</span><span class="idle-indicator {css_class}">{category}</span></div>
                <div class="progress-bar"><div class="progress-fill {progress_color}" style="width: {idle_pct}%;"></div></div>
            </div>''')

        progress_html = '\n'.join(progress_bars)

        # Build summary
        total_idle = idle_analysis.get('total_idle_hours', 0)
        avg_idle_pct = idle_analysis.get('avg_idle_pct', 0)
        best = idle_analysis.get('best_performer', {})
        best_vehicle = best.get('vehicle', 'N/A') if best else 'N/A'
        best_idle_pct = best.get('idle_pct', 0) if best else 0

        summary_html = f'''            <div class="summary-box">
                <div class="summary-title">⚠️ Total Idle Hours Today: ~{total_idle} Hours</div>
                <div class="summary-content">Average idle ratio: {avg_idle_pct}% of engine time. Best performer: {best_vehicle} ({best_idle_pct}% idle).</div>
            </div>'''

        # Find and replace the idle analysis section content
        pattern = r'(<div class="section-title"><div class="icon">⏱️</div>Idle Time Analysis[^<]*</div>\s*)((?:<div class="progress-bar-container">[\s\S]*?</div>\s*</div>\s*)+)(<div class="summary-box">[\s\S]*?</div>\s*</div>)'

        replacement = rf'\g<1>{progress_html}\n{summary_html}'

        html = re.sub(pattern, replacement, html, count=1)

        return html

    def _replace_truck_details_table(self, html: str, data: Dict) -> str:
        """Replace complete truck details table - full tbody replacement."""
        truck_details = data.get('truck_details', [])

        if not truck_details:
            logger.warning("No truck details data - keeping template")
            return html

        # Build table rows
        rows = []
        for truck in truck_details:
            row_class = truck.get('row_class', '')
            row_attr = f'class="{row_class}"' if row_class else ''

            vehicle = truck.get('vehicle', '')
            distance = truck.get('distance', 0)
            engine_hours = truck.get('engine_hours', '0:00')
            motion_hours = truck.get('motion_hours', '0:00')
            idle_hours = truck.get('idle_hours', '0:00')
            idle_pct = truck.get('idle_pct', 0)
            idle_badge = truck.get('idle_badge', 'badge-warning')
            fuel_consumed = truck.get('fuel_consumed', 0)
            mileage_display = truck.get('mileage_display', '0.00')
            mileage_badge = truck.get('mileage_badge', 'badge-warning')
            max_speed = truck.get('max_speed', 0)
            filled = truck.get('filled', 0)
            final_fuel = truck.get('final_fuel_level', 0)
            fuel_class = truck.get('fuel_class', 'medium')
            fuel_gauge_pct = truck.get('fuel_gauge_pct', 50)
            is_fuel_critical = truck.get('is_fuel_critical', False)
            has_data = truck.get('has_data', True)

            # Fuel status display
            if not has_data:
                fuel_status_html = '<span class="badge badge-danger">No Data</span>'
            elif is_fuel_critical:
                fuel_status_html = f'''<div class="fuel-gauge">
                            <div class="fuel-bar"><div class="fuel-level {fuel_class}" style="width: {fuel_gauge_pct}%;"></div></div>
                            <span style="font-size: 0.68rem; color: #c53030;">{final_fuel:.0f}L ⚠️</span>
                        </div>'''
            else:
                fuel_status_html = f'''<div class="fuel-gauge">
                            <div class="fuel-bar"><div class="fuel-level {fuel_class}" style="width: {fuel_gauge_pct}%;"></div></div>
                            <span style="font-size: 0.68rem;">{final_fuel:.0f}L</span>
                        </div>'''

            # Mileage display with coloring
            if 'Sensor' in mileage_display or '*' in mileage_display:
                mileage_html = f'<span class="badge {mileage_badge}">{mileage_display}</span>'
            elif truck.get('kmpl', 0) >= 0.9:
                mileage_html = f'<span style="color: #2f855a; font-weight: 600;">{mileage_display}</span>'
            elif truck.get('kmpl', 0) < 0.7:
                mileage_html = f'<span style="color: #c53030;">{mileage_display}</span>'
            else:
                mileage_html = mileage_display

            # Format filled - handle zero gracefully
            filled_display = f"{filled:.1f}" if filled > 0 else "0.0"

            rows.append(f'''                <tr {row_attr}>
                    <td><strong>{vehicle}</strong></td>
                    <td>{distance:.2f} km</td>
                    <td>{engine_hours}</td>
                    <td>{motion_hours}</td>
                    <td>{idle_hours}</td>
                    <td><span class="badge {idle_badge}">{idle_pct}%</span></td>
                    <td>{fuel_consumed:.1f} L</td>
                    <td>{mileage_html}</td>
                    <td>{max_speed} km/h</td>
                    <td>{filled_display}</td>
                    <td>
                        {fuel_status_html}
                    </td>
                </tr>''')

        rows_html = '\n'.join(rows)

        # Replace the truck details table tbody
        pattern = r'(<div class="section-title"><div class="icon">📋</div>Complete Truck Trip Report[\s\S]*?<tbody>)[\s\S]*?(</tbody>)'
        replacement = rf'\g<1>\n{rows_html}\n            \g<2>'

        html = re.sub(pattern, replacement, html, count=1)

        return html

    def _replace_chart_data(self, html: str, data: Dict) -> str:
        """Replace all Chart.js data arrays."""
        charts = data.get('charts', {})

        # Chart 1: Distance Trend
        distance_trend = charts.get('distance_trend', {})
        if distance_trend:
            labels = distance_trend.get('labels', [])
            chart_data = distance_trend.get('data', [])

            # Replace labels
            html = re.sub(
                r"(new Chart\(document\.getElementById\('distanceTrendChart'\)[\s\S]*?labels: )\[[^\]]+\](,)",
                rf"\g<1>{to_js_array(labels)}\g<2>",
                html
            )

            # Replace data
            html = re.sub(
                r"(new Chart\(document\.getElementById\('distanceTrendChart'\)[\s\S]*?data: )\[[^\]]+\](,)",
                rf"\g<1>{to_js_array(chart_data)}\g<2>",
                html
            )

            # Update highlight index to current day
            day = data.get('day', 1)
            html = re.sub(
                r'context\.dataIndex === \d+',
                f'context.dataIndex === {day - 1}',
                html
            )

        # Chart 2: Fuel Balance
        fuel_balance = charts.get('fuel_balance', {})
        if fuel_balance:
            labels = fuel_balance.get('labels', [])
            consumed = fuel_balance.get('consumed', [])
            filled = fuel_balance.get('filled', [])

            # Replace in fuelTrendChart
            html = re.sub(
                r"(new Chart\(document\.getElementById\('fuelTrendChart'\)[\s\S]*?labels: )\[[^\]]+\](,)",
                rf"\g<1>{to_js_array(labels)}\g<2>",
                html
            )

            # Replace consumed data - need to be more specific
            html = re.sub(
                r"(label: 'Fuel Consumed \(L\)'[\s\S]*?data: )\[[^\]]+\](,)",
                rf"\g<1>{to_js_array(consumed)}\g<2>",
                html
            )

            # Replace filled data
            html = re.sub(
                r"(label: 'Fuel Filled \(L\)'[\s\S]*?data: )\[[^\]]+\](,)",
                rf"\g<1>{to_js_array(filled)}\g<2>",
                html
            )

        # Chart 3: Top Trucks MTD
        top_mtd = charts.get('top_mtd', {})
        if top_mtd:
            labels = top_mtd.get('labels', [])
            chart_data = top_mtd.get('data', [])

            html = re.sub(
                r"(new Chart\(document\.getElementById\('topTrucksChart'\)[\s\S]*?labels: )\[[^\]]+\](,)",
                rf"\g<1>{to_js_string_array(labels)}\g<2>",
                html
            )

            html = re.sub(
                r"(new Chart\(document\.getElementById\('topTrucksChart'\)[\s\S]*?data: )\[[^\]]+\](,)",
                rf"\g<1>{to_js_array(chart_data)}\g<2>",
                html
            )

        # Chart 4: Mileage Performance
        mileage = charts.get('mileage', {})
        if mileage:
            labels = mileage.get('labels', [])
            chart_data = mileage.get('data', [])

            html = re.sub(
                r"(new Chart\(document\.getElementById\('mileageChart'\)[\s\S]*?labels: )\[[^\]]+\](,)",
                rf"\g<1>{to_js_string_array(labels)}\g<2>",
                html
            )

            html = re.sub(
                r"(new Chart\(document\.getElementById\('mileageChart'\)[\s\S]*?data: )\[[^\]]+\](,)",
                rf"\g<1>{to_js_array(chart_data)}\g<2>",
                html
            )

        return html

    def _replace_idle_trucks_section(self, html: str, data: Dict) -> str:
        """Replace idle trucks analysis section."""
        idle_trucks = data.get('idle_trucks', {})
        kpis = data.get('kpis', {})

        total_idle = idle_trucks.get('total_idle', 0)
        no_data = idle_trucks.get('no_data', [])
        engine_only = idle_trucks.get('engine_only', [])
        with_fuel = idle_trucks.get('with_fuel', [])

        # Update section title count
        html = re.sub(
            r'(Idle Trucks Analysis - \w{3} \d{1,2} \()\d+ Trucks Not Used\)',
            rf'\g<1>{total_idle} Trucks Not Used)',
            html
        )

        # Build insight cards
        cards = []

        # No data trucks
        if no_data:
            no_data_vehicles = [t['vehicle'] for t in no_data]
            vehicles_str = ', '.join(no_data_vehicles[:15])
            if len(no_data_vehicles) > 15:
                vehicles_str += f'... (+{len(no_data_vehicles) - 15} more)'

            cards.append(f'''<div class="insight-card danger">
                <div class="insight-title">Zero Engine Hours - No Telematics</div>
                <div class="insight-text"><strong>{vehicles_str}</strong> - Complete fleet underutilization. No GPS data, no engine activity. Check if breakdown/maintenance or just not assigned.</div>
            </div>''')

        # Engine only trucks
        for truck in engine_only[:2]:
            cards.append(f'''<div class="insight-card warning">
                <div class="insight-title">{truck['vehicle']} - Engine Idling Only</div>
                <div class="insight-text">{truck['engine_hours']} engine time, zero distance, {truck['fuel_consumed']}L fuel consumed. Truck started but never moved - pure fuel waste.</div>
            </div>''')

        # Trucks with fuel
        for truck in with_fuel[:1]:
            cards.append(f'''<div class="insight-card warning">
                <div class="insight-title">{truck['vehicle']} - Parked with Fuel</div>
                <div class="insight-text">{truck['final_fuel']}L fuel sitting unused. ~24 hours parked. Fuel could be reallocated to active trucks.</div>
            </div>''')

        # Fleet utilization gap
        utilization = kpis.get('utilization_pct', 0)
        active = kpis.get('active_trucks', 0)
        total = kpis.get('total_trucks', 35)
        cards.append(f'''<div class="insight-card">
                <div class="insight-title">Fleet Utilization Gap</div>
                <div class="insight-text">Only {utilization}% ({active}/{total}) trucks operational. Review fleet right-sizing to optimize asset utilization.</div>
            </div>''')

        cards_html = '\n            '.join(cards)

        # Replace the insights grid in idle trucks section
        html = re.sub(
            r'(<div class="section-title"><div class="icon">🚫</div>Idle Trucks Analysis[\s\S]*?<div class="insights-grid">)[\s\S]*?(</div>\s*</div>\s*<!-- Critical Insights -->)',
            rf'\g<1>\n            {cards_html}\n        \g<2>',
            html
        )

        return html

    def _replace_insights_section(self, html: str, claude_insights_html: str) -> str:
        """Replace insights sections with Claude-generated content."""
        if not claude_insights_html:
            logger.warning("No Claude insights provided - keeping template insights")
            return html

        # Find the Critical Insights section and replace everything up to footer
        # This includes: Critical Insights, Recommendations, Executive Summary

        # Look for the Critical Insights section
        critical_match = re.search(r'<!-- Critical Insights -->', html)
        if not critical_match:
            # Try finding by section title
            critical_match = re.search(r'<div class="section-title"><div class="icon">💡</div>Critical Insights', html)

        if not critical_match:
            logger.warning("Could not find Critical Insights section")
            return html

        # Find the footer
        footer_match = re.search(r'<div class="footer">', html)
        if not footer_match:
            logger.warning("Could not find footer")
            return html

        # Get positions
        insight_start = critical_match.start()
        footer_start = footer_match.start()

        # Build the new insights sections
        before_insights = html[:insight_start]
        after_insights = html[footer_start:]

        new_insights_section = f'''<!-- Critical Insights - AI Generated -->
    <div class="section-card full-width" style="margin-bottom: 25px;">
        <div class="section-title"><div class="icon">💡</div>AI-Powered Fleet Analytics</div>
        <div class="insights-grid">
            {claude_insights_html}
        </div>
    </div>

    '''

        return before_insights + new_insights_section + after_insights

    def _replace_footer(self, html: str, data: Dict) -> str:
        """Replace footer with report metadata."""
        month = data.get('month', 'Unknown')
        day = data.get('day', 1)
        year = data.get('year', 2025)
        total_trucks = safe_get(data, 'kpis', 'total_trucks', default=35)

        generated_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        new_footer = f'''<div class="footer">
        <p>Generated for {month} {day}, {year} | Balasore Alloys Limited - Fleet Management System</p>
        <p>Data Source: truck_reports table | {total_trucks} MAN Trucks Tracked | Report Generated: {generated_time}</p>
    </div>'''

        html = re.sub(
            r'<div class="footer">[\s\S]*?</div>\s*</div>',
            new_footer,
            html,
            count=1
        )

        return html


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def generate_automobile_dashboard(
    analysis_data: Dict[str, Any],
    claude_insights_html: str,
    date: str,
    template_path: str = None
) -> str:
    """
    Convenience function to generate Automobile dashboard.

    Args:
        analysis_data: Analysis data from AutomobileDataProcessor
        claude_insights_html: HTML from Claude analyzer
        date: Date string
        template_path: Optional template path

    Returns:
        Complete HTML string
    """
    engine = AutomobileTemplateEngine(template_path)
    return engine.generate_dashboard(analysis_data, claude_insights_html, date)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['AutomobileTemplateEngine', 'generate_automobile_dashboard']


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test template engine"""
    print("Automobile Template Engine - FIXED VERSION")
    print("=" * 60)
    print("Fixes applied:")
    print("  ✅ Direct string replacement for KPI cards")
    print("  ✅ Full tbody replacement for Top Performers")
    print("  ✅ Full tbody replacement for Truck Details")
    print("  ✅ Fixed MTD values (including Drained & Trucks Active)")
    print("  ✅ Dynamic idle analysis summary text")
    print("  ✅ Proper NULL/zero value handling")
    print("=" * 60)