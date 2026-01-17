"""
Geology Survey Template Engine - FIXED VERSION 6
=================================================
COMPLETE FIX for all hardcoded sections:
1. Today's KPIs - FIXED with simpler pattern
2. MTD Section - FIXED
3. All Charts - FIXED with correct patterns
4. All Tables - FIXED with replacer functions

Author: Senior ML Engineer
Date: January 2026
"""

import re
import os
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


def format_number(value: float, decimals: int = 0) -> str:
    """Format number with commas."""
    if value is None:
        return "0"
    if decimals == 0:
        return f"{value:,.0f}"
    return f"{value:,.{decimals}f}"


def to_js_array(data: List) -> str:
    """Convert Python list to JavaScript array string."""
    return json.dumps(data)


def get_ordinal(n: int) -> str:
    """Get ordinal suffix for a number."""
    if 11 <= n <= 13:
        return f"{n}th"
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


class GeologySurveyTemplateEngine:
    """Template engine for Geology & Survey Department Dashboard."""

    def __init__(self, template_path: str = None):
        if template_path is None:
            possible_paths = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "templates", "geology_survey_dashboard.html"),
                "/app/templates/geology_survey_dashboard.html",
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    template_path = path
                    break
            if template_path is None:
                template_path = possible_paths[0]

        self.template_path = template_path
        logger.info(f"Template Engine initialized: {template_path}")

    def generate_dashboard(self, analysis_data: Dict[str, Any], claude_insights_html: str, date: str, ai_summary_html: str = None) -> str:
        """Generate complete dashboard HTML with real data and AI insights."""
        logger.info(f"Generating dashboard for: {date}")
        self._ai_summary_html = ai_summary_html  # Store for later use

        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template not found: {self.template_path}")

        with open(self.template_path, 'r', encoding='utf-8') as f:
            html = f.read()

        try:
            # Apply replacements in order
            html = self._replace_title_and_date(html, analysis_data)
            html = self._remove_section_dates(html, analysis_data)  # NEW: Remove dates from section titles
            html = self._replace_today_kpis(html, analysis_data)
            html = self._replace_mtd_section(html, analysis_data)
            html = self._replace_shift_table(html, analysis_data)
            html = self._replace_location_table(html, analysis_data)
            html = self._replace_mtd_location_table(html, analysis_data)
            html = self._replace_agency_today_table(html, analysis_data)
            html = self._replace_sample_analysis_table(html, analysis_data)
            html = self._replace_plan_vs_actual(html, analysis_data)
            html = self._replace_excavation_details(html, analysis_data)
            html = self._replace_mtd_agency_table(html, analysis_data)
            html = self._replace_mtd_quality_stats(html, analysis_data)

            # AI SECTIONS
            html = self._replace_insights_section(html, claude_insights_html)
            html = self._replace_gap_analysis_section(html, analysis_data)
            html = self._replace_ai_summary(html, analysis_data)

            html = self._replace_footer(html, analysis_data)

            # CHARTS - Must be last as they modify JavaScript
            html = self._replace_all_charts(html, analysis_data)

        except Exception as e:
            logger.error(f"Error in template replacement: {e}", exc_info=True)
            raise

        logger.info(f"Dashboard generated: {len(html)} chars")
        return html

    # =========================================================================
    # HEADER & DATE
    # =========================================================================

    def _replace_title_and_date(self, html: str, data: Dict) -> str:
        """Replace title and date badge.

        NEW: Supports both single date and date range.
        """
        # Check if this is range data
        is_range = 'date_range_formatted' in data

        if is_range:
            # DATE RANGE MODE
            date_formatted = data.get('date_range_formatted', 'Date Range')
            year = data.get('year', 2025)
        else:
            # SINGLE DATE MODE
            month = data.get('month', 'December')
            day = data.get('day', 1)
            year = data.get('year', 2025)
            day_name = data.get('day_name', 'Monday')
            date_formatted = f"{month} {day}, {year} ({day_name})"

        # Title
        html = re.sub(
            r'<title>[^<]+</title>',
            f'<title>Geology & Survey Dashboard - {date_formatted}</title>',
            html
        )

        # Date badge
        html = re.sub(
            r'<div class="date-badge">📅[^<]+</div>',
            f'<div class="date-badge">📅 {date_formatted}</div>',
            html
        )

        return html

    def _remove_section_dates(self, html: str, data: Dict) -> str:
        """
        Remove ALL date references from section titles.

        Examples:
        - "December 2025 - Daily Production Trend (MTD)" → "Production Trend"
        - "Detailed Excavation Records - December 16, 2025" → "Detailed Excavation Records"
        - "December 2025 - Monthly Plan vs Actual Progress" → "Plan vs Actual Progress"
        - "Executive Summary - December 16, 2025" → "Executive Summary"
        """
        try:
            # Pattern 1: "December 2025 - Daily Production Trend (MTD)" → "Production Trend"
            html = re.sub(
                r'(<div class="icon">📈</div>)[^<]*December \d{4} - Daily Production Trend \(MTD\)',
                r'\1Production Trend',
                html
            )

            # Pattern 2: "Quality Parameter Trends - MTD" → "Quality Parameter Trends"
            html = re.sub(
                r'(<div class="icon">🧪</div>Quality Parameter Trends) - MTD',
                r'\1',
                html
            )

            # Pattern 3: "MTD Location Performance" → "Location Performance"
            html = re.sub(
                r'(<div class="icon">🗺️</div>)MTD Location Performance',
                r'\1Location Performance',
                html
            )

            # Pattern 4: "December 2025 - Monthly Plan vs Actual Progress" → "Plan vs Actual Progress"
            html = re.sub(
                r'(<div class="icon">🎯</div>)[^<]*December \d{4} - Monthly Plan vs Actual Progress',
                r'\1Plan vs Actual Progress',
                html
            )

            # Pattern 5: "Detailed Excavation Records - December 16, 2025" → "Detailed Excavation Records"
            html = re.sub(
                r'(<div class="icon">📋</div>Detailed Excavation Records) - [^<]+',
                r'\1',
                html
            )

            # Pattern 6: "MTD Agency Performance" → "Agency Performance"
            html = re.sub(
                r'(<div class="icon">🏭</div>)MTD Agency Performance',
                r'\1Agency Performance',
                html
            )

            # Pattern 7: "MTD Quality Statistics" → "Quality Statistics"
            html = re.sub(
                r'(<div class="icon">📊</div>)MTD Quality Statistics',
                r'\1Quality Statistics',
                html
            )

            # Pattern 8: No longer needed - "AI Insight Summary" doesn't have dates

            # Pattern 9: Remove "MTD" from table headers like "Actual MTD (MT)"
            html = re.sub(
                r'<th>Actual MTD \(MT\)</th>',
                r'<th>Actual (MT)</th>',
                html
            )

            # Pattern 10: "Geology Face Sample Analysis - Dec 16" → "Face Sample Analysis"
            html = re.sub(
                r'(<div class="icon">🔬</div>)Geology Face Sample Analysis - [^<]+',
                r'\1Face Sample Analysis',
                html
            )

            logger.info("Section dates removed successfully")
            return html

        except Exception as e:
            logger.warning(f"Error removing section dates: {e}")
            return html

    # =========================================================================
    # TODAY'S KPIs - COMPLETE REWRITE
    # =========================================================================

    def _replace_today_kpis(self, html: str, data: Dict) -> str:
        """Replace today's KPI cards - FIXED with individual card replacement.

        NEW: Supports both today_kpis (single date) and period_kpis (date range).
        """
        # Check if this is range data
        is_range = 'period_kpis' in data
        kpis = data.get('period_kpis' if is_range else 'today_kpis', {})

        exc = kpis.get('excavation', {})
        trips = kpis.get('trips', {})
        load = kpis.get('avg_load', {})
        cr2o3 = kpis.get('avg_cr2o3', {})
        ratio = kpis.get('avg_ratio', {})
        locs = kpis.get('active_locations', {})

        # Change labels based on mode
        exc_label = "Period Excavation (MT)" if is_range else "Today's Excavation (MT)"
        trips_label = "Total Trips" if is_range else "Total Trips Today"

        # Build the complete new KPI grid
        cr2o3_label = "Avg Cr₂O₃" if is_range else "Avg Cr₂O₃ Today"
        new_kpi_html = f'''<div class="kpi-grid">
        <div class="kpi-card"><div class="kpi-value">{exc.get('formatted', '0')}</div><div class="kpi-label">{exc_label}</div><div class="kpi-change {exc.get('change', {}).get('type', 'neutral')}">{exc.get('change', {}).get('text', '')}</div></div>
        <div class="kpi-card"><div class="kpi-value">{trips.get('formatted', '0')}</div><div class="kpi-label">{trips_label}</div><div class="kpi-change {trips.get('change', {}).get('type', 'neutral')}">{trips.get('change', {}).get('text', '')}</div></div>
        <div class="kpi-card"><div class="kpi-value">{load.get('formatted', '0')}</div><div class="kpi-label">Avg Load/Trip (MT)</div><div class="kpi-change {load.get('change', {}).get('type', 'neutral')}">{load.get('change', {}).get('text', '')}</div></div>
        <div class="kpi-card"><div class="kpi-value">{cr2o3.get('formatted', '0%')}</div><div class="kpi-label">{cr2o3_label}</div><div class="kpi-change {cr2o3.get('change', {}).get('type', 'neutral')}">{cr2o3.get('change', {}).get('text', '')}</div></div>
        <div class="kpi-card"><div class="kpi-value">{ratio.get('formatted', '0.00')}</div><div class="kpi-label">Avg Cr:Fe Ratio</div><div class="kpi-change {ratio.get('change', {}).get('type', 'neutral')}">{ratio.get('change', {}).get('text', '')}</div></div>
        <div class="kpi-card"><div class="kpi-value">{locs.get('formatted', '0')}</div><div class="kpi-label">Active Locations</div><div class="kpi-change {locs.get('change', {}).get('type', 'neutral')}">{locs.get('change', {}).get('text', '')}</div></div>
    </div>'''

        # Pattern: Match from <div class="kpi-grid"> to just before next section
        # The template has: </div>\n\n    <div class="section-card full-width"
        pattern = r'<div class="kpi-grid">[\s\S]*?</div>\s*</div>\s*</div>\s*</div>\s*</div>\s*</div>\s*</div>\s*(?=<div class="section-card full-width")'

        new_html = re.sub(pattern, new_kpi_html + '\n\n    ', html, count=1)

        if new_html == html:
            logger.warning("KPI pattern didn't match - trying alternate")
            # Alternate: Match the 6 kpi-card divs inside kpi-grid
            pattern2 = r'(<div class="kpi-grid">)\s*<div class="kpi-card">.*?</div>\s*<div class="kpi-card">.*?</div>\s*<div class="kpi-card">.*?</div>\s*<div class="kpi-card">.*?</div>\s*<div class="kpi-card">.*?</div>\s*<div class="kpi-card">.*?</div>\s*(</div>)'

            def replacer(match):
                cards = f'''
        <div class="kpi-card"><div class="kpi-value">{exc.get('formatted', '0')}</div><div class="kpi-label">{exc_label}</div><div class="kpi-change {exc.get('change', {}).get('type', 'neutral')}">{exc.get('change', {}).get('text', '')}</div></div>
        <div class="kpi-card"><div class="kpi-value">{trips.get('formatted', '0')}</div><div class="kpi-label">{trips_label}</div><div class="kpi-change {trips.get('change', {}).get('type', 'neutral')}">{trips.get('change', {}).get('text', '')}</div></div>
        <div class="kpi-card"><div class="kpi-value">{load.get('formatted', '0')}</div><div class="kpi-label">Avg Load/Trip (MT)</div><div class="kpi-change {load.get('change', {}).get('type', 'neutral')}">{load.get('change', {}).get('text', '')}</div></div>
        <div class="kpi-card"><div class="kpi-value">{cr2o3.get('formatted', '0%')}</div><div class="kpi-label">{cr2o3_label}</div><div class="kpi-change {cr2o3.get('change', {}).get('type', 'neutral')}">{cr2o3.get('change', {}).get('text', '')}</div></div>
        <div class="kpi-card"><div class="kpi-value">{ratio.get('formatted', '0.00')}</div><div class="kpi-label">Avg Cr:Fe Ratio</div><div class="kpi-change {ratio.get('change', {}).get('type', 'neutral')}">{ratio.get('change', {}).get('text', '')}</div></div>
        <div class="kpi-card"><div class="kpi-value">{locs.get('formatted', '0')}</div><div class="kpi-label">Active Locations</div><div class="kpi-change {locs.get('change', {}).get('type', 'neutral')}">{locs.get('change', {}).get('text', '')}</div></div>
    '''
                return match.group(1) + cards + match.group(2)

            new_html = re.sub(pattern2, replacer, html, count=1, flags=re.DOTALL)

        return new_html

    # =========================================================================
    # MTD SECTION
    # =========================================================================

    def _replace_mtd_section(self, html: str, data: Dict) -> str:
        """Replace MTD/Periodic Summary section title and KPI cards.

        NEW: Shows ORE, OB, SILT breakdown instead of total excavation.
        """
        is_range = 'start_date' in data and 'end_date' in data

        # Use period_kpis for date ranges, mtd_kpis for single dates
        kpis = data.get('period_kpis', {}) if is_range else data.get('mtd_kpis', {})

        # Material breakdown values
        ore_qty = kpis.get('ore_qty', {}).get('formatted', '0')
        ob_qty = kpis.get('ob_qty', {}).get('formatted', '0')
        silt_qty = kpis.get('silt_qty', {}).get('formatted', '0')
        total_trips = kpis.get('trips' if is_range else 'total_trips', {}).get('formatted', '0')
        working_days = kpis.get('working_days', {}).get('formatted', '0')
        avg_cr2o3 = kpis.get('avg_cr2o3', {}).get('formatted', '0%')

        logger.info(f"MTD Section values - ORE: {ore_qty}, OB: {ob_qty}, SILT: {silt_qty}, Trips: {total_trips}, Days: {working_days}, Cr2O3: {avg_cr2o3}")

        # Replace section title "Periodic Summary" -> "Summary"
        pattern_title = r'(<div class="icon">📊</div>)\s*Periodic Summary'
        html = re.sub(pattern_title, r'\1 Summary', html, count=1)

        # Replace each KPI card value - new structure with ORE, OB, SILT
        # Card 1: ORE (green)
        pattern = r'(<div class="mtd-kpi-card green">\s*<div class="mtd-value green">)[^<]+(</div>\s*<div class="kpi-label">)[^<]+(</div>)'
        replacement = rf'\g<1>{ore_qty}\g<2>ORE (MT)\g<3>'
        html = re.sub(pattern, replacement, html, count=1)

        # Card 2: Overburden (orange)
        pattern = r'(<div class="mtd-kpi-card orange">\s*<div class="mtd-value orange">)[^<]+(</div>\s*<div class="kpi-label">)[^<]+(</div>)'
        replacement = rf'\g<1>{ob_qty}\g<2>Overburden (MT)\g<3>'
        html = re.sub(pattern, replacement, html, count=1)

        # Card 3: SILT (brown - custom style)
        pattern = r'(<div class="mtd-kpi-card brown"[^>]*>\s*<div class="mtd-value"[^>]*>)[^<]+(</div>\s*<div class="kpi-label">)[^<]+(</div>)'
        replacement = rf'\g<1>{silt_qty}\g<2>SILT (MT)\g<3>'
        html = re.sub(pattern, replacement, html, count=1)

        # Card 4: Total Trips (blue)
        pattern = r'(<div class="mtd-kpi-card blue">\s*<div class="mtd-value blue">)[^<]+(</div>\s*<div class="kpi-label">)[^<]+(</div>)'
        replacement = rf'\g<1>{total_trips}\g<2>Total Trips\g<3>'
        html = re.sub(pattern, replacement, html, count=1)

        # Card 5: Working Days (purple)
        pattern = r'(<div class="mtd-kpi-card purple">\s*<div class="mtd-value purple">)[^<]+(</div>\s*<div class="kpi-label">)[^<]+(</div>)'
        replacement = rf'\g<1>{working_days}\g<2>Working Days\g<3>'
        html = re.sub(pattern, replacement, html, count=1)

        # Card 6: Avg Cr2O3 (pink)
        pattern = r'(<div class="mtd-kpi-card pink">\s*<div class="mtd-value pink">)[^<]+(</div>\s*<div class="kpi-label">)[^<]+(</div>)'
        replacement = rf'\g<1>{avg_cr2o3}\g<2>Avg Cr₂O₃\g<3>'
        html = re.sub(pattern, replacement, html, count=1)

        return html

    # =========================================================================
    # TABLE REPLACEMENTS
    # =========================================================================

    def _replace_shift_table(self, html: str, data: Dict) -> str:
        """Replace shift Plan vs Actual table.

        NEW: Uses shift_plan_vs_actual data with columns:
        - Shift, Planned (MT), Actual (MT), Achievement %, Variance
        Falls back to shift_breakdown if shift_plan_vs_actual not available.
        """
        # Try new shift_plan_vs_actual first
        shift_data = data.get('shift_plan_vs_actual', {})
        has_plan_data = shift_data.get('has_plan_data', False)

        if has_plan_data and shift_data.get('rows'):
            # Use Plan vs Actual format
            rows = shift_data.get('rows', [])
            total_planned = shift_data.get('total_planned', 0)
            total_actual = shift_data.get('total_actual', 0)
            total_achievement = shift_data.get('total_achievement_pct', 0)
            total_variance = shift_data.get('total_variance', 0)
            total_variance_class = shift_data.get('total_variance_class', '')
            total_variance_fmt = shift_data.get('total_variance_formatted', '0')

            rows_html = ""
            for row in rows:
                shift = row.get('shift', '?')
                planned = row.get('planned', 0)
                actual = row.get('actual', 0)
                achievement = row.get('achievement_pct', 0)
                variance = row.get('variance', 0)
                variance_class = row.get('variance_class', '')
                variance_fmt = row.get('variance_formatted', '0')

                rows_html += f'                    <tr><td><span class="badge badge-shift-{shift.lower()}">Shift {shift}</span></td><td>{format_number(planned)}</td><td>{format_number(actual)}</td><td>{achievement:.1f}%</td><td class="{variance_class}">{variance_fmt}</td></tr>\n'

            rows_html += f'                    <tr style="background: #f7fafc; font-weight: 600;"><td>Total</td><td>{format_number(total_planned)}</td><td>{format_number(total_actual)}</td><td>{total_achievement:.1f}%</td><td class="{total_variance_class}">{total_variance_fmt}</td></tr>'
        else:
            # Fall back to old shift_breakdown format (no plan data available)
            shift_data = data.get('shift_breakdown', {})
            rows = shift_data.get('rows', [])
            total_trips = shift_data.get('total_trips', 0)
            total_qty = shift_data.get('total_qty', 0)

            rows_html = ""
            for row in rows:
                shift = row.get('shift', '?')
                qty = row.get('qty', 0)
                pct = row.get('pct', 0)
                # Show actual as both planned and actual (no plan data)
                rows_html += f'                    <tr><td><span class="badge badge-shift-{shift.lower()}">Shift {shift}</span></td><td>-</td><td>{format_number(qty)}</td><td>{pct:.1f}%</td><td>-</td></tr>\n'

            rows_html += f'                    <tr style="background: #f7fafc; font-weight: 600;"><td>Total</td><td>-</td><td>{format_number(total_qty)}</td><td>100%</td><td>-</td></tr>'

        # Pattern handles both "Shift-wise Production" and "Shift-wise Plan vs Actual" titles
        pattern = r"(<div class=\"section-title\">\s*<div class=\"icon\">🔄</div>Shift-wise (?:Production|Plan vs Actual)\s*</div>\s*<table class=\"data-table\">\s*<thead>.*?</thead>\s*<tbody>).*?(</tbody>)"

        def replacer(match):
            return match.group(1) + "\n" + rows_html + "\n                " + match.group(2)

        html = re.sub(pattern, replacer, html, flags=re.DOTALL)
        return html

    def _replace_location_table(self, html: str, data: Dict) -> str:
        """Replace location breakdown table."""
        loc_data = data.get('location_breakdown', {})
        rows = loc_data.get('rows', [])
        total_trips = loc_data.get('total_trips', 0)
        total_qty = loc_data.get('total_qty', 0)

        rows_html = ""
        for row in rows:
            pct = row.get('pct', 0)
            rows_html += f'                    <tr><td>{row.get("location", "Unknown")}</td><td>{row.get("trips", 0)}</td><td>{format_number(row.get("qty", 0))}</td><td>{pct:.1f}%</td></tr>\n'

        rows_html += f'                    <tr style="background: #f7fafc; font-weight: 600;"><td>Total</td><td>{total_trips}</td><td>{format_number(total_qty)}</td><td>100%</td></tr>'

        pattern = r"(<div class=\"section-title\"><div class=\"icon\">📍</div>Location-wise Excavation</div>\s*<table class=\"data-table\">\s*<thead>.*?</thead>\s*<tbody>).*?(</tbody>)"

        def replacer(match):
            return match.group(1) + "\n" + rows_html + "\n                " + match.group(2)

        html = re.sub(pattern, replacer, html, flags=re.DOTALL)

        # Also fix the pattern to handle whitespace
        pattern2 = r"(<div class=\"section-title\">\s*<div class=\"icon\">📍</div>Location-wise Excavation\s*</div>\s*<table class=\"data-table\">\s*<thead>.*?</thead>\s*<tbody>).*?(</tbody>)"
        html = re.sub(pattern2, replacer, html, flags=re.DOTALL)

        return html

    def _replace_mtd_location_table(self, html: str, data: Dict) -> str:
        """Replace MTD Location Performance table.

        For date range mode, uses mtd_location_performance data.
        """
        is_range = 'start_date' in data and 'end_date' in data
        loc_data = data.get('mtd_location_performance', {})
        rows = loc_data.get('rows', [])

        if not rows:
            rows_html = '                    <tr><td colspan="4" style="text-align: center;">No location data</td></tr>'
        else:
            rows_html = ""
            for row in rows:
                pct = row.get('pct', 0)
                rows_html += f'                    <tr><td>{row.get("location", "Unknown")}</td><td>{row.get("trips", 0)}</td><td>{format_number(row.get("qty", 0))}</td><td>{pct:.1f}%</td></tr>\n'

        # Pattern handles whitespace between tags
        pattern = r"(<div class=\"section-title\">\s*<div class=\"icon\">🗺️</div>MTD Location Performance\s*</div>\s*<table class=\"data-table\">\s*<thead>.*?</thead>\s*<tbody>).*?(</tbody>)"

        def replacer(match):
            return match.group(1) + "\n" + rows_html + "                " + match.group(2)

        html = re.sub(pattern, replacer, html, flags=re.DOTALL)
        return html

    def _replace_agency_today_table(self, html: str, data: Dict) -> str:
        """Replace today's agency performance table.

        For date range mode, uses the same data as MTD (agency_performance.rows).
        For single date mode, uses agency_performance.today.rows.
        """
        is_range = 'start_date' in data and 'end_date' in data
        agency_data = data.get('agency_performance', {})

        # Date range mode: use rows directly (same as MTD)
        # Single date mode: use 'today' sub-object
        if is_range:
            rows = agency_data.get('rows', [])
            total_trips = agency_data.get('total_trips', 0)
            total_qty = agency_data.get('total_qty', 0)
        else:
            today = agency_data.get('today', {})
            rows = today.get('rows', [])
            total_trips = today.get('total_trips', 0)
            total_qty = today.get('total_qty', 0)

        rows_html = ""
        for row in rows:
            pct = row.get('pct', 0)
            rows_html += f'                    <tr><td>{row.get("agency", "Unknown")}</td><td>{row.get("trips", 0)}</td><td>{format_number(row.get("qty", 0))}</td><td>{pct:.1f}%</td></tr>\n'

        rows_html += f'                    <tr style="background: #f7fafc; font-weight: 600;"><td>Total</td><td>{total_trips}</td><td>{format_number(total_qty)}</td><td>100%</td></tr>'

        # Pattern handles whitespace and various title formats
        pattern = r"(<div class=\"section-title\">\s*<div class=\"icon\">🏢</div>Agency Performance[^<]*</div>\s*<table class=\"data-table\">\s*<thead>.*?</thead>\s*<tbody>).*?(</tbody>)"

        def replacer(match):
            return match.group(1) + "\n" + rows_html + "\n                " + match.group(2)

        html = re.sub(pattern, replacer, html, flags=re.DOTALL)

        # Update progress bars for agency contribution
        if rows:
            top_pct = rows[0].get('pct', 0)
            top_name = rows[0].get('agency', 'Agency')

            # Replace agency contribution label
            pattern = r'<div class="progress-label"><span>[^<]*Agency Contribution</span><span>[\d.]+%</span></div>'
            new_label = f'<div class="progress-label"><span>{top_name} Agency Contribution</span><span>{top_pct:.1f}%</span></div>'
            html = re.sub(pattern, new_label, html, count=1)

            # Replace progress bar width
            pattern = r'(style="width: )[\d.]+(%; background: linear-gradient\(90deg, #667eea, #764ba2\)")'
            def width_replacer(m):
                return f'{m.group(1)}{top_pct}{m.group(2)}'
            html = re.sub(pattern, width_replacer, html, count=1)

        return html

    def _replace_sample_analysis_table(self, html: str, data: Dict) -> str:
        """Replace sample analysis table."""
        sample_data = data.get('sample_analysis', {})
        rows = sample_data.get('rows', [])

        # Determine title based on mode (single date vs range)
        is_range = 'start_date' in data and 'end_date' in data
        if is_range:
            title_suffix = "Period"
        else:
            title_suffix = data.get('date_formatted', 'Today')

        # Update title - pattern handles whitespace between tags
        pattern = r'(<div class="section-title">\s*<div class="icon">🔬</div>)[^<]+(</div>)'
        def title_replacer(m):
            return f'{m.group(1)}Geology Face Sample Analysis - {title_suffix}{m.group(2)}'
        html = re.sub(pattern, title_replacer, html, count=1)

        if not rows:
            rows_html = '                    <tr><td colspan="7" style="text-align: center; color: #718096;">No sample analysis data for today</td></tr>'
        else:
            rows_html = ""
            for row in rows:
                shift = row.get('shift', '?')
                grade = row.get('grade', '-')
                grade_class = f"badge-{grade.lower()}" if grade in ['HG', 'MG', 'LG'] else ''
                cr2o3 = row.get('cr2o3', 0)
                feo = row.get('feo', 0)
                ratio = row.get('ratio', 0)
                rows_html += f'                    <tr><td><span class="badge badge-shift-{shift.lower()}">Shift {shift}</span></td><td>{row.get("location", "Unknown")}</td><td>{row.get("sample_id", "-")}</td><td>{cr2o3:.1f}%</td><td>{feo:.1f}%</td><td>{ratio:.2f}</td><td><span class="badge {grade_class}">{grade}</span></td></tr>\n'

        pattern = r"(<div class=\"section-title\"><div class=\"icon\">🔬</div>[^<]*</div>\s*<table class=\"data-table\">\s*<thead>.*?</thead>\s*<tbody>).*?(</tbody>)"

        def replacer(match):
            return match.group(1) + "\n" + rows_html + "                " + match.group(2)

        html = re.sub(pattern, replacer, html, flags=re.DOTALL)
        return html

    def _replace_plan_vs_actual(self, html: str, data: Dict) -> str:
        """Replace plan vs actual table and progress bar."""
        plan_data = data.get('plan_vs_actual', {})
        rows = plan_data.get('rows', [])
        totals = plan_data.get('totals', {})
        gap = data.get('gap_analysis', {})

        rows_html = ""
        for row in rows:
            grade = row.get('grade', '-')
            grade_class = f"badge-{grade.lower()}" if grade in ['HG', 'MG', 'LG'] else ''
            status_class = row.get('status_class', 'warning')

            if status_class == 'success':
                style = 'background: rgba(72, 187, 120, 0.15); color: #2f855a;'
            elif status_class == 'danger':
                style = 'background: rgba(245, 101, 101, 0.15); color: #c53030;'
            else:
                style = 'background: rgba(237, 137, 54, 0.15); color: #c05621;'

            actual = row.get('actual', 0)
            actual_str = format_number(actual) if actual > 0 else '-'
            ach_pct = row.get('achievement_pct', 0)
            rows_html += f'                <tr><td>{row.get("location", "Unknown")}</td><td><span class="badge {grade_class}">{grade}</span></td><td>{format_number(row.get("planned", 0))}</td><td>{actual_str}</td><td>{ach_pct:.1f}%</td><td>{format_number(row.get("remaining", 0))}</td><td><span class="badge" style="{style}">{row.get("status", "Unknown")}</span></td></tr>\n'

        # Totals row
        t_planned = totals.get('planned', 0)
        t_actual = totals.get('actual', 0)
        t_ach = totals.get('achievement_pct', 0)
        t_rem = totals.get('remaining', 0)
        t_style = 'background: rgba(72, 187, 120, 0.15); color: #2f855a;' if t_ach >= 80 else 'background: rgba(237, 137, 54, 0.15); color: #c05621;'
        t_status = 'On Track' if t_ach >= 80 else 'Behind Plan'

        rows_html += f'                <tr style="background: #f7fafc; font-weight: 600;"><td colspan="2">TOTAL ORE</td><td>{format_number(t_planned)}</td><td>{format_number(t_actual)}</td><td>{t_ach:.1f}%</td><td>{format_number(t_rem)}</td><td><span class="badge" style="{t_style}">{t_status}</span></td></tr>'

        # Build dynamic title based on month/year from data
        month_name = data.get('month', 'Current Month')
        year = data.get('year', '')
        is_range = 'start_date' in data and 'end_date' in data

        if is_range:
            title_text = f"Period - Plan vs Actual Progress"
        else:
            title_text = f"{month_name} {year} - Monthly Plan vs Actual Progress"

        # Pattern with \s* to handle whitespace/newlines between tags
        # Matches any title ending in "Plan vs Actual Progress" (e.g., "December 2025 - Monthly Plan vs Actual Progress")
        pattern = r"(<div class=\"section-title\">\s*<div class=\"icon\">🎯</div>)[^<]*Plan vs Actual Progress\s*(</div>\s*<table class=\"data-table\">\s*<thead>.*?</thead>\s*<tbody>).*?(</tbody>)"

        def table_replacer(match):
            return match.group(1) + title_text + match.group(2) + "\n" + rows_html + "\n            " + match.group(3)

        html = re.sub(pattern, table_replacer, html, flags=re.DOTALL)

        # Update progress bar
        is_range = 'start_date' in data and 'end_date' in data

        if is_range:
            # For date range: show "Period Progress (X working days)"
            working_days = data.get('period_kpis', {}).get('working_days', {}).get('value', 0)
            start_date = data.get('start_date', '')
            end_date = data.get('end_date', '')
            progress_title = "Period Progress"
            progress_text = f'{working_days} working days ({start_date} to {end_date})'
        else:
            # For single date: show "Monthly Target Achievement (X days / Y days = Z% time elapsed)"
            days_elapsed = gap.get('days_elapsed', data.get('days_elapsed', 0))
            days_in_month = data.get('days_in_month', 31)
            time_pct = (days_elapsed / days_in_month * 100) if days_in_month > 0 else 0
            progress_title = "Monthly Target Achievement"
            progress_text = f'{days_elapsed} days / {days_in_month} days = {time_pct:.1f}% time elapsed'

        old_label = r'<div class="progress-label"><span>[^<]+</span><span>[\d.]+%[^<]*</span></div>'
        new_label = f'<div class="progress-label"><span>{progress_title} ({progress_text})</span><span>{t_ach:.1f}% Achieved</span></div>'
        html = re.sub(old_label, new_label, html, count=1)

        # Replace progress bar width
        old_width = r'(<div class="progress-bar" style="height: 20px;"><div class="progress-fill" style="width: )[\d.]+(%;)'
        def width_replacer(m):
            return f'{m.group(1)}{t_ach}{m.group(2)}'
        html = re.sub(old_width, width_replacer, html, count=1)

        return html

    def _replace_excavation_details(self, html: str, data: Dict) -> str:
        """Replace excavation details table."""
        details = data.get('excavation_details', [])

        # Determine title based on mode
        is_range = 'start_date' in data and 'end_date' in data
        if is_range:
            title_suffix = "Period"
        else:
            title_suffix = data.get('date_formatted', 'Today')

        if not details:
            rows_html = '                <tr><td colspan="7" style="text-align: center; color: #718096;">No excavation records</td></tr>'
        else:
            rows_html = ""
            for row in details:
                shift = row.get('shift', '?')
                avg_load = row.get('avg_load', 0)
                rows_html += f'                <tr><td><span class="badge badge-shift-{shift.lower()}">{shift}</span></td><td>{row.get("location", "Unknown")}</td><td>{row.get("material", "Unknown")}</td><td>{row.get("agency", "Unknown")}</td><td>{row.get("trips", 0)}</td><td>{format_number(row.get("qty", 0))}</td><td>{avg_load:.1f}</td></tr>\n'

        # Pattern handles whitespace between tags, scroll container, and matches any title variant
        pattern = r"(<div class=\"section-title\">\s*<div class=\"icon\">📋</div>)Detailed Excavation Records[^<]*(</div>\s*<div class=\"table-scroll-container\"[^>]*>\s*<table class=\"data-table\">\s*<thead>.*?</thead>\s*<tbody>).*?(</tbody>)"

        def replacer(match):
            return f'{match.group(1)}Detailed Excavation Records - {title_suffix}{match.group(2)}\n{rows_html}            {match.group(3)}'

        result = re.sub(pattern, replacer, html, flags=re.DOTALL)

        # Fallback: try pattern without scroll container (for backwards compatibility)
        if result == html:
            pattern_old = r"(<div class=\"section-title\">\s*<div class=\"icon\">📋</div>)Detailed Excavation Records[^<]*(</div>\s*<table class=\"data-table\">\s*<thead>.*?</thead>\s*<tbody>).*?(</tbody>)"
            result = re.sub(pattern_old, replacer, html, flags=re.DOTALL)

        return result

    def _replace_mtd_agency_table(self, html: str, data: Dict) -> str:
        """Replace MTD agency performance table.

        Handles both single date mode (agency_performance.mtd.rows) and
        date range mode (agency_performance.rows directly).
        """
        is_range = 'start_date' in data and 'end_date' in data
        agency_data = data.get('agency_performance', {})

        # Date range mode: rows are at top level
        # Single date mode: rows are under 'mtd' key
        if is_range:
            rows = agency_data.get('rows', [])
        else:
            mtd = agency_data.get('mtd', {})
            rows = mtd.get('rows', [])

        if not rows:
            rows_html = '                    <tr><td colspan="4" style="text-align: center;">No MTD data</td></tr>'
        else:
            rows_html = ""
            for row in rows:
                pct = row.get('pct', 0)
                rows_html += f'                    <tr><td>{row.get("agency", "Unknown")}</td><td>{format_number(row.get("trips", 0))}</td><td>{format_number(row.get("qty", 0))}</td><td>{pct:.1f}%</td></tr>\n'

        # Pattern handles whitespace between tags - matches both "MTD Agency Performance" and "Agency Performance"
        pattern = r"(<div class=\"section-title\">\s*<div class=\"icon\">🏭</div>(?:MTD )?Agency Performance\s*</div>\s*<table class=\"data-table\">\s*<thead>.*?</thead>\s*<tbody>).*?(</tbody>)"

        def replacer(match):
            return match.group(1) + "\n" + rows_html + "                " + match.group(2)

        html = re.sub(pattern, replacer, html, flags=re.DOTALL)
        return html

    def _replace_mtd_quality_stats(self, html: str, data: Dict) -> str:
        """Replace MTD quality statistics."""
        is_range = 'start_date' in data and 'end_date' in data
        # Use quality_stats for date range mode, mtd_quality_stats for single date
        stats = data.get('quality_stats', {}) if is_range else data.get('mtd_quality_stats', {})

        # Replace title: "Today's Quality Summary" → "Period Quality Summary" if range mode
        quality_title = "Period Quality Summary" if is_range else "Today's Quality Summary"
        title_pattern = r'(<div class="summary-title">📊\s*)(Today\'s Quality Summary|Period Quality Summary)(</div>)'
        html = re.sub(title_pattern, lambda m: m.group(1) + quality_title + m.group(3), html, count=1)

        replacements = [
            ('Average Cr₂O₃', f'{stats.get("avg_cr2o3", 0):.1f}%'),
            ('Min Cr₂O₃', f'{stats.get("min_cr2o3", 0):.1f}%'),
            ('Max Cr₂O₃', f'{stats.get("max_cr2o3", 0):.1f}%'),
            ('Average FeO', f'{stats.get("avg_feo", 0):.1f}%'),
            ('Min FeO', f'{stats.get("min_feo", 0):.1f}%'),
            ('Max FeO', f'{stats.get("max_feo", 0):.1f}%'),
            ('Average Cr:Fe Ratio', f'{stats.get("avg_ratio", 0):.2f}'),
            ('Total Samples Analyzed', str(stats.get("total_samples", 0))),
        ]

        for metric_name, value in replacements:
            # Pattern handles whitespace/newlines between tags
            pattern = f'(<span class="metric-name">{re.escape(metric_name)}</span>\\s*<span\\s*class="metric-value">)[^<]+(</span>)'
            def make_replacer(val):
                return lambda m: f'{m.group(1)}{val}{m.group(2)}'
            html = re.sub(pattern, make_replacer(value), html, count=1)

        return html

    # =========================================================================
    # AI SECTIONS
    # =========================================================================

    def _replace_insights_section(self, html: str, claude_insights_html: str) -> str:
        """Replace Critical Insights section with LLM-generated cards."""
        if not claude_insights_html:
            logger.warning("No Claude insights HTML provided")
            return html

        # Pattern handles whitespace between tags
        pattern = r'(<div class="section-title">\s*<div class="icon">💡</div>Critical Insights & Hidden Patterns\s*</div>\s*<div class="insights-grid">).*?(</div>\s*</div>\s*<div class="section-card full-width"[^>]*>\s*<div class="section-title">\s*<div class="icon">🎯</div>)'

        def replacer(match):
            return match.group(1) + "\n            " + claude_insights_html + "\n        " + match.group(2)

        html = re.sub(pattern, replacer, html, flags=re.DOTALL)
        return html

    def _replace_gap_analysis_section(self, html: str, data: Dict) -> str:
        """Replace Gap Analysis & Recommendations section."""
        is_range = 'start_date' in data and 'end_date' in data
        gap = data.get('gap_analysis', {})

        # Get KPIs based on mode
        if is_range:
            period_kpis = data.get('period_kpis', {})
            avg_daily = gap.get('avg_daily_production', 0)
        else:
            mtd_kpis = data.get('mtd_kpis', {})
            avg_daily = mtd_kpis.get('avg_daily_production', {}).get('value', 0)

        total_planned = gap.get('total_planned', 0)
        total_actual = gap.get('total_actual', 0)
        achievement_pct = gap.get('achievement_pct', 0)
        remaining = gap.get('remaining_target', 0)
        days_remaining = gap.get('days_remaining', 0)
        working_days = gap.get('working_days', 0)
        required_daily = gap.get('required_daily_production', 0)
        increase_pct = gap.get('increase_needed_pct', 0)
        expected_month_end = gap.get('expected_month_end', 0)
        expected_achievement = gap.get('expected_achievement_pct', 0)

        # Build different content for range vs single date
        if is_range:
            days_in_range = gap.get('days_in_range', 0)
            summary_html = f'''<div class="summary-box">
            <div class="summary-title">📌 Period Production Analysis</div>
            <div class="summary-content">
                <p><strong>Period Performance:</strong> Over {working_days} working days, total production reached <strong>{format_number(total_actual)} MT</strong>, averaging <strong>{format_number(avg_daily)} MT/day</strong>.</p><br>
                <p><strong>Monthly Target Progress:</strong> Current production represents <strong>{achievement_pct:.1f}%</strong> of the monthly target ({format_number(total_planned)} MT). Remaining target: <strong>{format_number(remaining)} MT</strong>.</p><br>
                <p><strong>Projection:</strong> At current pace, expected month-end production is approximately <strong>{format_number(expected_month_end)} MT ({expected_achievement:.1f}% of plan)</strong>. To meet target, daily production needs to increase by <strong>{increase_pct:.0f}%</strong> to {format_number(required_daily)} MT/day.</p>
            </div>
        </div>'''
        else:
            summary_html = f'''<div class="summary-box">
            <div class="summary-title">📌 Production Gap Analysis</div>
            <div class="summary-content">
                <p><strong>Required Daily Production for Target:</strong> To achieve the monthly target of {format_number(total_planned)} MT, the remaining {days_remaining} days need to produce {format_number(remaining)} MT, requiring an average of <strong>{format_number(required_daily)} MT/day</strong> - which is <strong>{increase_pct:.0f}% higher</strong> than the current average of {format_number(avg_daily)} MT/day.</p><br>
                <p><strong>Realistic Adjusted Target:</strong> At current pace ({format_number(avg_daily)} MT/day), expected month-end production is approximately <strong>{format_number(expected_month_end)} MT ({expected_achievement:.1f}% of plan)</strong>.</p>
            </div>
        </div>'''

        # Add recommendations grid
        summary_html += '''
        <div class="insights-grid" style="margin-top: 20px;">
            <div class="insight-card"><div class="insight-title">1️⃣ Activate DVS West & East</div><div class="insight-text">Immediate mobilization needed for DVS West and DVS East locations to recover planned tonnage.</div></div>
            <div class="insight-card"><div class="insight-title">2️⃣ Shift Productivity Review</div><div class="insight-text">Review shift-wise performance. Implement corrective actions for underperforming shifts.</div></div>
            <div class="insight-card"><div class="insight-title">3️⃣ Optimize Load Factor</div><div class="insight-text">Improve load per trip back to 15 MT standard for optimal efficiency.</div></div>
            <div class="insight-card"><div class="insight-title">4️⃣ Increase Shift C Operations</div><div class="insight-text">Expand night shift operations to add capacity without capital investment.</div></div>
            <div class="insight-card"><div class="insight-title">5️⃣ Sample Analysis Protocol</div><div class="insight-text">Mandate minimum 3 samples per day for continuous quality monitoring.</div></div>
            <div class="insight-card"><div class="insight-title">6️⃣ Agency Diversification</div><div class="insight-text">Consider engaging additional agencies to reduce dependency risk.</div></div>
        </div>'''

        # Pattern handles whitespace between tags
        pattern = r'(<div class="section-title">\s*<div class="icon">🎯</div>Gap Analysis & Recommendations\s*</div>\s*)<div class="summary-box">.*?</div>\s*<div class="insights-grid"[^>]*>.*?</div>\s*</div>\s*(</div>\s*<div class="section-card full-width">\s*<div class="section-title">\s*<div class="icon">📝</div>)'

        def replacer(match):
            return match.group(1) + summary_html + "\n    " + match.group(2)

        html = re.sub(pattern, replacer, html, flags=re.DOTALL)
        return html

    def _replace_ai_summary(self, html: str, data: Dict) -> str:
        """Replace AI Insight Summary section with LLM-generated content."""
        # Get the AI summary from instance variable (set in generate_dashboard)
        ai_summary = getattr(self, '_ai_summary_html', None)

        if not ai_summary:
            # Fallback if no AI summary available
            ai_summary = "<p>AI summary generation in progress...</p>"

        # Pattern matches the new AI Insight Summary section
        # Looking for: <div class="icon">🤖</div>AI Insight Summary
        pattern = r'(<div class="section-title">\s*<div class="icon">🤖</div>AI Insight Summary\s*</div>\s*<div class="summary-box">\s*<div class="summary-content[^"]*"[^>]*>).*?(</div>\s*</div>\s*</div>\s*<div class="footer">)'

        def replacer(match):
            return match.group(1) + "\n                " + ai_summary + "\n            " + match.group(2)

        html = re.sub(pattern, replacer, html, flags=re.DOTALL)
        return html

    # =========================================================================
    # FOOTER
    # =========================================================================

    def _replace_footer(self, html: str, data: Dict) -> str:
        """Replace footer."""
        month = data.get('month', 'Unknown')
        day = data.get('day', 0)
        year = data.get('year', 0)

        new_footer = f'''<div class="footer">
        <p>Generated on {month} {day}, {year} | Balasore Alloys Limited - Geology & Survey Department</p>
        <p>Data Source: balcorpdb - mines_day_wise_excavation, mines_geology_face_sample_analysis, mines_monthly_excavation_plan</p>
    </div>'''

        html = re.sub(r'<div class="footer">.*?</div>\s*</div>', new_footer, html, flags=re.DOTALL)
        return html

    # =========================================================================
    # ALL CHARTS - COMPLETE REWRITE
    # =========================================================================

    def _replace_all_charts(self, html: str, data: Dict) -> str:
        """Replace all chart data in JavaScript section - FIXED patterns."""

        # SHIFT CHART - new Chart(document.getElementById('shiftChart')...
        # Pattern: data: [280, 760, 270]
        # Try shift_plan_vs_actual first, then fall back to shift_breakdown
        shift_plan = data.get('shift_plan_vs_actual', {})
        if shift_plan.get('has_plan_data') and shift_plan.get('chart'):
            shift = shift_plan.get('chart', {})
        else:
            shift = data.get('shift_breakdown', {}).get('chart', {})
        shift_labels = shift.get('labels', ['Shift A', 'Shift B', 'Shift C'])
        shift_data = shift.get('data', [0, 0, 0])

        # Match: getElementById('shiftChart')...labels: [...], datasets: [{ data: [...]
        pattern = r"(getElementById\('shiftChart'\)[^}]+labels:\s*)\[[^\]]*\]([^}]+data:\s*)\[[^\]]*\]"
        def shift_replacer(m):
            return f"{m.group(1)}{to_js_array(shift_labels)}{m.group(2)}{to_js_array(shift_data)}"
        html = re.sub(pattern, shift_replacer, html)

        # LOCATION CHART - ALWAYS replace to prevent stale template data
        loc = data.get('location_breakdown', {}).get('chart', {})
        loc_labels = loc.get('labels', [])
        loc_data = loc.get('data', [])

        # ALWAYS replace (use "No Data" / [0] if empty)
        pattern = r"(getElementById\('locationChart'\)[^}]+labels:\s*)\[[^\]]*\]([^}]+data:\s*)\[[^\]]*\]"
        def loc_replacer(m):
            labels = loc_labels if loc_labels else ['No Data']
            values = loc_data if loc_data else [0]
            return f"{m.group(1)}{to_js_array(labels)}{m.group(2)}{to_js_array(values)}"
        html = re.sub(pattern, loc_replacer, html)

        # TREND CHART - ALWAYS replace to prevent stale template data
        trend = data.get('daily_trend', {})
        trend_labels = trend.get('labels', [])
        trend_data = trend.get('production_data', [])
        avg_value = trend.get('average_value', 0)

        # ALWAYS replace labels
        pattern = r"(getElementById\('trendChart'\)[^}]+labels:\s*)\[[^\]]*\]"
        def trend_label_replacer(m):
            labels = trend_labels if trend_labels else ['No Data']
            return f"{m.group(1)}{to_js_array(labels)}"
        html = re.sub(pattern, trend_label_replacer, html)

        # ALWAYS replace Daily Production data
        pattern = r"(label:\s*'Daily Production[^}]+data:\s*)\[[^\]]*\]"
        def trend_data_replacer(m):
            values = trend_data if trend_data else [0]
            return f"{m.group(1)}{to_js_array(values)}"
        html = re.sub(pattern, trend_data_replacer, html)

        # ALWAYS replace Average line data
        avg_line = [avg_value] * len(trend_labels) if trend_labels else [0]
        pattern = r"(label:\s*'Average[^']*'[^}]+data:\s*)\[[^\]]*\]"
        def avg_replacer(m):
            return f"{m.group(1)}{to_js_array(avg_line)}"
        html = re.sub(pattern, avg_replacer, html)

        # Update average label
        avg_str = format_number(avg_value)
        html = re.sub(r"label:\s*'Average \([^)]+\)'", f"label: 'Average ({avg_str} MT)'", html)

        # QUALITY CHART - has two datasets with yAxisID
        # ALWAYS replace, even when empty - prevents showing old template data
        qual = data.get('quality_trend', {})
        qual_labels = qual.get('labels', [])
        cr2o3_data = qual.get('cr2o3_data', [])
        ratio_data = qual.get('ratio_data', [])

        # ALWAYS replace labels (empty array if no data)
        pattern = r"(getElementById\('qualityChart'\)[^}]+labels:\s*)\[[^\]]*\]"
        def qual_label_replacer(m):
            return f"{m.group(1)}{to_js_array(qual_labels if qual_labels else ['No Data'])}"
        html = re.sub(pattern, qual_label_replacer, html)

        # ALWAYS replace Cr2O3 data
        pattern = r"(label:\s*'Cr₂O₃[^}]+data:\s*)\[[^\]]*\]"
        def cr_replacer(m):
            return f"{m.group(1)}{to_js_array(cr2o3_data if cr2o3_data else [0])}"
        html = re.sub(pattern, cr_replacer, html)

        # ALWAYS replace Ratio data
        pattern = r"(label:\s*'Cr:Fe Ratio'[^}]+data:\s*)\[[^\]]*\]"
        def ratio_replacer(m):
            return f"{m.group(1)}{to_js_array(ratio_data if ratio_data else [0])}"
        html = re.sub(pattern, ratio_replacer, html)

        # MTD/LOCATION PERFORMANCE CHART - Check both keys for date range vs single date mode
        is_range = 'start_date' in data and 'end_date' in data
        if is_range:
            mtd_loc = data.get('location_performance', {}).get('chart', {})
        else:
            mtd_loc = data.get('mtd_location_performance', {}).get('chart', {})
        mtd_labels = mtd_loc.get('labels', [])
        mtd_data = mtd_loc.get('data', [])

        pattern = r"(getElementById\('mtdLocationChart'\)[^}]+labels:\s*)\[[^\]]*\]([^}]+data:\s*)\[[^\]]*\]"
        def mtd_replacer(m):
            labels = mtd_labels if mtd_labels else ['No Data']
            values = mtd_data if mtd_data else [0]
            return f"{m.group(1)}{to_js_array(labels)}{m.group(2)}{to_js_array(values)}"
        html = re.sub(pattern, mtd_replacer, html)

        # AGENCY PIE CHART - ALWAYS replace
        agency = data.get('agency_performance', {}).get('chart', {})
        agency_labels = agency.get('labels', [])
        agency_data = agency.get('data', [])

        pattern = r"(getElementById\('agencyChart'\)[^}]+labels:\s*)\[[^\]]*\]([^}]+data:\s*)\[[^\]]*\]"
        def agency_replacer(m):
            labels = agency_labels if agency_labels else ['No Data']
            values = agency_data if agency_data else [0]
            return f"{m.group(1)}{to_js_array(labels)}{m.group(2)}{to_js_array(values)}"
        html = re.sub(pattern, agency_replacer, html)

        return html


# Convenience function
def generate_geology_survey_dashboard(analysis_data: Dict[str, Any], claude_insights_html: str, date: str, template_path: str = None) -> str:
    engine = GeologySurveyTemplateEngine(template_path)
    return engine.generate_dashboard(analysis_data, claude_insights_html, date)


__all__ = ['GeologySurveyTemplateEngine', 'generate_geology_survey_dashboard']