"""
furnace_template_engine.py
==========================
Template engine for injecting real data into furnace dashboard HTML.

This module:
1. Loads the furnace_dashboard.html template
2. Replaces hardcoded analysisData with real database data
3. Replaces JavaScript-generated insights with Claude API HTML
4. Returns complete, ready-to-display HTML

Author: Senior ML Engineer
Date: November 2024
"""

import os
import re
import json
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# TEMPLATE PATHS
# ============================================================================

# Template is in root templates/ folder (not department subfolder)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_DIR = os.path.join(PROJECT_ROOT, "templates")
TEMPLATE_FILE = "furnace_dashboard.html"


# ============================================================================
# FURNACE TEMPLATE ENGINE
# ============================================================================

class FurnaceTemplateEngine:
    """
    Inject real data into the furnace dashboard template.
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

        logger.info(f"Template engine initialized: {self.template_path}")

    def generate_dashboard(
        self,
        analysis_data: Dict[str, Any],
        claude_insights_html: str,
        date: str
    ) -> str:
        """
        Generate complete dashboard HTML.

        Args:
            analysis_data: The analysisData dict from FurnaceDataProcessor
            claude_insights_html: HTML from ClaudeInsightsGenerator
            date: Date string (YYYY-MM-DD) or date range info in analysis_data

        Returns:
            Complete HTML string ready to display
        """
        logger.info(f"Generating furnace dashboard for date: {date}")

        # Detect if this is a date range
        is_range = 'start_date' in analysis_data and 'end_date' in analysis_data

        # Load template
        template_html = self._load_template()

        # Step 1: Replace date in title and header
        html = self._replace_date(template_html, date, analysis_data, is_range)

        # Step 2: Replace MTD labels with period-aware labels
        html = self._replace_mtd_labels(html, is_range)

        # Step 3: Replace analysisData JavaScript object
        html = self._replace_analysis_data(html, analysis_data)

        # Step 4: Replace insights section
        html = self._replace_insights_section(html, claude_insights_html)

        logger.info(f"Dashboard generated successfully ({len(html)} characters)")
        return html

    def _load_template(self) -> str:
        """Load HTML template from file."""
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template not found: {self.template_path}")

        with open(self.template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        logger.info(f"Template loaded: {len(template)} characters")
        return template

    def _replace_date(self, html: str, date: str, analysis_data: Dict[str, Any], is_range: bool) -> str:
        """
        Replace date in title and header.

        Changes:
        - Title: "Furnace Operations Dashboard - 2025-11-17" → actual date/range
        - Header: Date badge with formatted date/range
        """
        try:
            if is_range:
                # For date range
                start_date = analysis_data.get('start_date', '')
                end_date = analysis_data.get('end_date', '')
                date_range_formatted = analysis_data.get('date_range_formatted', f'{start_date} - {end_date}')

                # Replace in title tag
                html = re.sub(
                    r'<title>Furnace Operations Dashboard - \d{4}-\d{2}-\d{2}</title>',
                    f'<title>Furnace Operations Dashboard - {date_range_formatted}</title>',
                    html
                )

                # Replace date displays
                html = html.replace('November 17, 2025', date_range_formatted)
                html = html.replace('2025-11-17', date_range_formatted)

                logger.info(f"Date range replaced: {date_range_formatted}")
            else:
                # For single date
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%B %d, %Y')  # "November 17, 2025"

                # Replace in title tag
                html = re.sub(
                    r'<title>Furnace Operations Dashboard - \d{4}-\d{2}-\d{2}</title>',
                    f'<title>Furnace Operations Dashboard - {date}</title>',
                    html
                )

                # Replace ALL occurrences of "November 17, 2025" with the actual date
                html = html.replace('November 17, 2025', formatted_date)

                # Also replace the YYYY-MM-DD format if it appears
                html = html.replace('2025-11-17', date)

                logger.info(f"Date replaced: {date} → {formatted_date}")

            return html

        except Exception as e:
            logger.warning(f"Error replacing date: {e}")
            return html

    def _replace_mtd_labels(self, html: str, is_range: bool) -> str:
        """
        Replace MTD (Month-to-Date) labels with period-aware labels.

        When is_range=True:
        - "MTD" → "Period"
        - "Month-to-Date" → "Period"
        - "(MTD)" → "(Period)"

        Args:
            html: Template HTML
            is_range: Whether this is a date range dashboard

        Returns:
            Modified HTML with replaced labels
        """
        if not is_range:
            return html  # Keep original MTD labels for single date

        try:
            # Replace label text: "MTD Variance" → "Period Variance"
            html = re.sub(r'\bMTD\s+([\w\s]+)</div>', r'Period \1</div>', html)

            # Replace in metric labels: <div class="metric-label">MTD ...
            html = re.sub(r'(<div class="metric-label">)MTD\s+', r'\1Period ', html)

            # Replace MTD in parentheses: (MTD) → (Period)
            html = html.replace('(MTD)', '(Period)')

            # Replace standalone MTD references
            html = re.sub(r'\bMTD\b(?![a-z_])', 'Period', html)

            logger.info("MTD labels replaced with Period labels")
            return html

        except Exception as e:
            logger.warning(f"Error replacing MTD labels: {e}")
            return html

    def _replace_analysis_data(self, html: str, analysis_data: Dict[str, Any]) -> str:
        """
        Replace the hardcoded analysisData JavaScript object with real data.

        Template has (around line 331):
        const analysisData = {
            production: { ... },
            power: { ... },
            ...
        };

        We replace this entire object with our real data.
        """
        try:
            # Convert analysis_data to JavaScript format
            js_data = self._dict_to_js_object(analysis_data)

            # Find and replace the analysisData object
            # Pattern: const analysisData = { ... };
            # Use DOTALL flag to match across multiple lines
            pattern = r'const analysisData = \{[\s\S]*?\n        \};'

            replacement = f'const analysisData = {js_data};'

            html = re.sub(pattern, replacement, html, count=1)

            logger.info("analysisData object replaced successfully")
            return html

        except Exception as e:
            logger.error(f"Error replacing analysisData: {e}", exc_info=True)
            return html

    def _replace_insights_section(self, html: str, claude_insights_html: str) -> str:
        """
        Replace the JavaScript-generated insights section with Claude's HTML.

        Template has (around lines 1054-1178):
        insightsContainer.innerHTML = `
            ${plantProductionRate >= 98 ? `...` : `...`}
            ...
        `;

        We replace everything between innerHTML = ` and the closing `;
        """
        try:
            # Find the insights generation block
            # Pattern: insightsContainer.innerHTML = `...`;
            pattern = r"insightsContainer\.innerHTML = `[\s\S]*?`;(?=\n    </script>)"

            # Escape backticks in Claude's HTML for JavaScript string
            escaped_html = claude_insights_html.replace('`', '\\`').replace('${', '\\${')

            replacement = f"insightsContainer.innerHTML = `{escaped_html}`;"

            html = re.sub(pattern, replacement, html, count=1)

            logger.info("Insights section replaced with Claude HTML")
            return html

        except Exception as e:
            logger.error(f"Error replacing insights section: {e}", exc_info=True)
            return html

    def _dict_to_js_object(self, data: Dict[str, Any]) -> str:
        """
        Convert Python dict to JavaScript object literal string.

        Handles:
        - None → null
        - Python booleans → JavaScript booleans
        - Proper indentation for readability
        """
        def convert_value(obj, indent_level=0):
            """Recursively convert Python objects to JS format."""
            indent = "    " * indent_level
            next_indent = "    " * (indent_level + 1)

            if obj is None:
                return "null"
            elif isinstance(obj, bool):
                return "true" if obj else "false"
            elif isinstance(obj, (int, float)):
                return str(obj)
            elif isinstance(obj, str):
                # Escape quotes and special chars
                escaped = obj.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                return f'"{escaped}"'
            elif isinstance(obj, list):
                if not obj:
                    return "[]"
                items = [convert_value(item, indent_level + 1) for item in obj]
                return "[\n" + next_indent + f",\n{next_indent}".join(items) + "\n" + indent + "]"
            elif isinstance(obj, dict):
                if not obj:
                    return "{}"
                items = []
                for key, value in obj.items():
                    # Keys don't need quotes if they're valid identifiers
                    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                        key_str = f'"{key}"'
                    else:
                        key_str = f'"{key}"'
                    value_str = convert_value(value, indent_level + 1)
                    items.append(f"{key_str}: {value_str}")
                return "{\n" + next_indent + f",\n{next_indent}".join(items) + "\n" + indent + "}"
            else:
                return str(obj)

        return convert_value(data, 2)  # Start with indent level 2 to match template


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def generate_furnace_dashboard(
    analysis_data: Dict[str, Any],
    claude_insights_html: str,
    date: str,
    template_path: str = None
) -> str:
    """
    Convenience function to generate dashboard.

    Args:
        analysis_data: Data from FurnaceDataProcessor
        claude_insights_html: HTML from ClaudeInsightsGenerator
        date: Date string (YYYY-MM-DD)
        template_path: Optional custom template path

    Returns:
        Complete HTML string
    """
    engine = FurnaceTemplateEngine(template_path)
    return engine.generate_dashboard(analysis_data, claude_insights_html, date)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['FurnaceTemplateEngine', 'generate_furnace_dashboard']


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test template engine with sample data"""

    print("Testing Furnace Template Engine...")
    print("=" * 70)

    # Check if template exists
    engine = FurnaceTemplateEngine()
    print(f"Template path: {engine.template_path}")

    if os.path.exists(engine.template_path):
        print("✅ Template file found")

        # Load and show size
        template = engine._load_template()
        print(f"✅ Template loaded: {len(template)} characters")

        # Test with minimal data
        test_data = {
            "date": "2025-11-17",
            "production": {
                "plant_total": {
                    "td_plan": 350.0,
                    "td_actual": 345.0,
                    "td_variance": -5.0
                },
                "individual_furnaces": []
            },
            "power": {"plant_total": {}, "individual_furnaces": []},
            "recovery": {"plant_avg": {}, "individual_furnaces": []},
            "operational": {"plant_metrics": {}, "individual_furnaces": []},
            "tapping": {"overall_stats": {}, "individual_furnaces": []},
            "slag": {"plant_metrics": {}, "individual_furnaces": []}
        }

        test_insights = """
<div class="insights-section">
    <div class="insights-title">💡 Test Insights</div>
    <div class="insight-item">
        <div>This is a test insight from the template engine.</div>
    </div>
</div>
"""

        # Generate dashboard
        try:
            html = engine.generate_dashboard(test_data, test_insights, "2025-11-17")
            print(f"✅ Dashboard generated: {len(html)} characters")

            # Save test output
            test_output = "/tmp/test_furnace_dashboard.html"
            with open(test_output, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"✅ Test dashboard saved: {test_output}")
            print("\nOpen this file in a browser to verify!")

        except Exception as e:
            print(f"❌ Error generating dashboard: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"❌ Template file not found: {engine.template_path}")
        print("Make sure furnace_dashboard.html exists in templates/ directory")