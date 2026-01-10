"""
Export Service
==============
Converts HTML dashboards to PDF and Excel formats.

Uses QuickChart.io API to convert Chart.js charts to static images,
then generates PDF using Playwright with proper vertical A4 layout.

Usage:
    from core.export_service import ExportService

    export = ExportService()
    pdf_bytes = export.html_to_pdf(html_content)
    excel_bytes = export.html_to_excel(html_content)
"""

import os
import re
import json
import logging
import tempfile
import requests
import base64
import urllib.parse
from io import BytesIO
from typing import Optional, Tuple, List, Dict
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# QuickChart.io API endpoint
QUICKCHART_API = "https://quickchart.io/chart"


class ExportService:
    """
    Service for exporting dashboards to different formats.
    Supports: PDF, Excel (XLSX)

    Uses QuickChart.io for server-side chart rendering (no JS needed).
    """

    def __init__(self):
        """Initialize export service and check available converters."""
        self._playwright_installed = None
        self.pdf_available = self._check_pdf_support()
        self.excel_available = self._check_excel_support()

    def _check_pdf_support(self) -> bool:
        """Check if PDF generation is available (via Playwright)."""
        try:
            from playwright.sync_api import sync_playwright
            self._playwright_installed = True
            return True
        except ImportError:
            logger.warning("Playwright not installed. PDF export disabled.")
            return False

    def _check_excel_support(self) -> bool:
        """Check if Excel generation is available."""
        try:
            import openpyxl
            return True
        except ImportError:
            logger.warning("openpyxl not installed. Excel export disabled.")
            return False

    def _extract_chartjs_configs(self, html_content: str) -> List[Dict]:
        """
        Extract Chart.js configurations from HTML/JavaScript.

        Looks for patterns like: new Chart(ctx, { ... })
        Returns list of chart configs with their canvas IDs.
        """
        charts = []

        # Pattern to match Chart.js instantiation
        # new Chart(document.getElementById('chartId'), { config })
        # or new Chart(ctx, { config })
        pattern = r"new\s+Chart\s*\(\s*(?:document\.getElementById\s*\(\s*['\"]([^'\"]+)['\"]\s*\)|(\w+))\s*,\s*(\{[\s\S]*?\})\s*\)(?:\s*;)?"

        matches = re.finditer(pattern, html_content, re.MULTILINE)

        for match in matches:
            canvas_id = match.group(1) or match.group(2)
            config_str = match.group(3)

            try:
                # Try to parse the config (it's JavaScript, not JSON)
                # We need to handle JS syntax -> JSON
                config_str = self._js_to_json(config_str)
                config = json.loads(config_str)
                charts.append({
                    'id': canvas_id,
                    'config': config
                })
                logger.info(f"Extracted chart config for: {canvas_id}")
            except Exception as e:
                logger.warning(f"Failed to parse chart config for {canvas_id}: {e}")
                continue

        return charts

    def _js_to_json(self, js_str: str) -> str:
        """Convert JavaScript object notation to JSON."""
        # Remove comments
        js_str = re.sub(r'//.*$', '', js_str, flags=re.MULTILINE)
        js_str = re.sub(r'/\*[\s\S]*?\*/', '', js_str)

        # Add quotes to unquoted keys
        js_str = re.sub(r'(\s*)(\w+)\s*:', r'\1"\2":', js_str)

        # Replace single quotes with double quotes
        js_str = re.sub(r"'([^']*)'", r'"\1"', js_str)

        # Remove trailing commas
        js_str = re.sub(r',\s*([\]}])', r'\1', js_str)

        # Handle special values
        js_str = js_str.replace('true', 'true').replace('false', 'false')
        js_str = js_str.replace('null', 'null')

        return js_str

    def _generate_quickchart_url(self, chart_config: Dict, width: int = 400, height: int = 250) -> str:
        """
        Generate a QuickChart.io URL for a chart configuration.

        Args:
            chart_config: Chart.js configuration object
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            QuickChart.io URL that renders the chart as PNG
        """
        # Simplify config for URL (remove animation, etc.)
        if 'options' in chart_config:
            chart_config['options']['animation'] = False
            chart_config['options']['responsive'] = False
        else:
            chart_config['options'] = {'animation': False, 'responsive': False}

        config_json = json.dumps(chart_config, separators=(',', ':'))
        encoded_config = urllib.parse.quote(config_json, safe='')

        url = f"{QUICKCHART_API}?c={encoded_config}&w={width}&h={height}&bkg=white"
        return url

    def _generate_quickchart_image(self, chart_config: Dict, width: int = 400, height: int = 250) -> Optional[str]:
        """
        Generate chart image using QuickChart.io API (POST method for complex charts).

        Returns base64 encoded image or None on failure.
        """
        try:
            # Simplify config
            if 'options' in chart_config:
                chart_config['options']['animation'] = False
                chart_config['options']['responsive'] = False
            else:
                chart_config['options'] = {'animation': False, 'responsive': False}

            payload = {
                "chart": chart_config,
                "width": width,
                "height": height,
                "backgroundColor": "white",
                "format": "png",
                "encoding": "base64"
            }

            response = requests.post(
                QUICKCHART_API,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                # Response is base64 encoded image
                return response.text
            else:
                logger.error(f"QuickChart API error: {response.status_code} - {response.text[:200]}")
                return None

        except Exception as e:
            logger.error(f"QuickChart request failed: {e}")
            return None

    def _replace_charts_with_images(self, html_content: str) -> str:
        """
        Replace Chart.js canvas elements with static images from QuickChart.io.
        """
        charts = self._extract_chartjs_configs(html_content)

        if not charts:
            logger.info("No Chart.js configurations found in HTML")
            return html_content

        soup = BeautifulSoup(html_content, 'html.parser')

        for chart in charts:
            canvas_id = chart['id']
            config = chart['config']

            # Find the canvas element
            canvas = soup.find('canvas', {'id': canvas_id})
            if not canvas:
                # Try finding by other attributes
                canvas = soup.find('canvas', id=re.compile(canvas_id, re.I))

            if canvas:
                # Generate chart image
                img_base64 = self._generate_quickchart_image(config, width=450, height=280)

                if img_base64:
                    # Create img element to replace canvas
                    img_tag = soup.new_tag('img')
                    img_tag['src'] = f"data:image/png;base64,{img_base64}"
                    img_tag['alt'] = f"Chart: {canvas_id}"
                    img_tag['style'] = "max-width: 100%; height: auto; display: block; margin: 5px auto;"
                    img_tag['class'] = "chart-image"

                    canvas.replace_with(img_tag)
                    logger.info(f"Replaced canvas '{canvas_id}' with static image")
                else:
                    logger.warning(f"Failed to generate image for chart '{canvas_id}'")

        # Remove Chart.js script tags (not needed anymore)
        for script in soup.find_all('script'):
            if script.string and 'new Chart' in script.string:
                script.decompose()

        return str(soup)

    def _inject_print_styles(self, html_content: str) -> str:
        """
        Inject print-optimized CSS for vertical A4, max 2 pages.
        """
        print_css = """
        <style type="text/css" media="all">
            /* Vertical A4 layout, compact for 2 pages max */
            @page {
                size: A4 portrait;
                margin: 8mm;
            }

            * {
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
                color-adjust: exact !important;
                box-sizing: border-box;
            }

            html, body {
                width: 210mm;
                margin: 0 !important;
                padding: 8px !important;
                font-size: 10px !important;
                line-height: 1.3 !important;
                font-family: Arial, sans-serif !important;
            }

            /* Header compact */
            .header, header, [class*="header"] {
                padding: 8px !important;
                margin-bottom: 8px !important;
            }

            h1 { font-size: 18px !important; margin: 5px 0 !important; }
            h2 { font-size: 14px !important; margin: 5px 0 !important; }
            h3 { font-size: 12px !important; margin: 4px 0 !important; }
            h4, h5, h6 { font-size: 11px !important; margin: 3px 0 !important; }

            /* KPI Cards - compact grid */
            .kpi-grid, .stats-grid, .metrics-grid,
            [class*="kpi"], [class*="stat"], [class*="metric"] {
                display: flex !important;
                flex-wrap: wrap !important;
                gap: 6px !important;
                margin: 6px 0 !important;
            }

            .kpi-card, .stat-card, .metric-card,
            [class*="kpi-card"], [class*="stat-card"] {
                flex: 1 1 calc(25% - 6px) !important;
                min-width: 100px !important;
                padding: 8px !important;
                margin: 0 !important;
                text-align: center;
            }

            .kpi-value, .stat-value, [class*="value"] {
                font-size: 16px !important;
                font-weight: bold !important;
            }

            .kpi-label, .stat-label, [class*="label"] {
                font-size: 9px !important;
            }

            /* Charts - fit nicely */
            .chart-image, .chart-container, [class*="chart"] {
                max-width: 100% !important;
                height: auto !important;
                margin: 8px auto !important;
            }

            img.chart-image {
                max-height: 200px !important;
                width: auto !important;
            }

            /* Grid layout for charts */
            .charts-grid, .dashboard-grid, [class*="grid"] {
                display: flex !important;
                flex-wrap: wrap !important;
                gap: 10px !important;
                justify-content: center !important;
            }

            .charts-grid > *, .dashboard-grid > * {
                flex: 1 1 calc(50% - 10px) !important;
                max-width: calc(50% - 10px) !important;
            }

            /* Tables - compact */
            table {
                width: 100% !important;
                border-collapse: collapse !important;
                font-size: 9px !important;
                margin: 8px 0 !important;
            }

            th, td {
                padding: 4px 6px !important;
                border: 1px solid #ddd !important;
                text-align: left !important;
            }

            th {
                background-color: #0076CE !important;
                color: white !important;
                font-weight: bold !important;
                font-size: 9px !important;
            }

            tr:nth-child(even) {
                background-color: #f9f9f9 !important;
            }

            /* Insights compact */
            .insight, .insight-card, [class*="insight"] {
                padding: 6px !important;
                margin: 4px 0 !important;
                font-size: 9px !important;
                background: #f5f5f5 !important;
                border-left: 3px solid #0076CE !important;
            }

            /* Hide non-essential */
            nav, footer, .chat-widget, .chat-fab, .chat-modal,
            button, .no-print, script, noscript, iframe,
            [class*="chat"], [class*="modal"] {
                display: none !important;
            }

            /* Page break control */
            .section, .card, .module, [class*="section"] {
                page-break-inside: avoid !important;
                break-inside: avoid !important;
            }

            /* Remove shadows/effects */
            * {
                box-shadow: none !important;
                text-shadow: none !important;
            }
        </style>
        """

        # Insert print CSS right before </head>
        if '</head>' in html_content:
            html_content = html_content.replace('</head>', print_css + '\n</head>')
        else:
            html_content = print_css + html_content

        return html_content

    def _html_to_pdf_playwright(self, html_content: str) -> Tuple[bool, bytes, str]:
        """
        Convert HTML to PDF using Playwright (headless Chromium).
        Charts are already converted to static images via QuickChart.io.
        """
        try:
            from playwright.sync_api import sync_playwright

            # First, replace Chart.js charts with static images
            html_content = self._replace_charts_with_images(html_content)

            # Inject print-optimized CSS
            html_content = self._inject_print_styles(html_content)

            # Write HTML to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                temp_html_path = f.name

            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()

                    # Load the HTML file
                    page.goto(f'file:///{temp_html_path.replace(os.sep, "/")}')

                    # Wait for images to load
                    page.wait_for_timeout(2000)

                    # Generate PDF - Vertical A4
                    pdf_bytes = page.pdf(
                        format='A4',
                        landscape=False,  # Portrait/Vertical
                        margin={
                            'top': '10mm',
                            'right': '10mm',
                            'bottom': '10mm',
                            'left': '10mm'
                        },
                        scale=0.9,
                        print_background=True,
                    )

                    browser.close()

                logger.info(f"PDF generated via Playwright: {len(pdf_bytes)} bytes")
                return True, pdf_bytes, ""

            finally:
                try:
                    os.unlink(temp_html_path)
                except:
                    pass

        except Exception as e:
            logger.error(f"Playwright PDF generation failed: {e}", exc_info=True)
            return False, b'', str(e)

    def html_to_pdf(self, html_content: str, options: dict = None) -> Tuple[bool, bytes, str]:
        """
        Convert HTML to PDF with charts rendered via QuickChart.io.

        - Vertical A4 portrait format
        - Charts converted to static images (no JS needed)
        - Compact layout for 1-2 pages max

        Args:
            html_content: HTML string
            options: PDF generation options

        Returns:
            Tuple of (success, pdf_bytes, error_message)
        """
        if not self.pdf_available:
            return False, b'', "PDF export not available. Install playwright."

        if self._playwright_installed:
            return self._html_to_pdf_playwright(html_content)

        return False, b'', "Playwright not installed"

    def _extract_kpi_data(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract KPI/metric data from dashboard HTML."""
        kpis = []

        kpi_selectors = [
            ('class', re.compile(r'kpi|metric|stat|card', re.I)),
            ('class', re.compile(r'summary|highlight|key-value', re.I)),
        ]

        for attr, pattern in kpi_selectors:
            cards = soup.find_all(attrs={attr: pattern})
            for card in cards:
                text = card.get_text(separator='|', strip=True)
                parts = [p.strip() for p in text.split('|') if p.strip()]

                if len(parts) >= 2:
                    label = None
                    value = None
                    for part in parts:
                        clean = part.replace(',', '').replace('%', '').replace('₹', '').strip()
                        if clean.replace('.', '').replace('-', '').isdigit() or '₹' in part:
                            if value is None:
                                value = part
                        else:
                            if label is None and len(part) < 100:
                                label = part

                    if label and value:
                        kpis.append({'label': label, 'value': value})
                elif len(parts) == 1 and len(parts[0]) < 200:
                    kpis.append({'label': 'Info', 'value': parts[0]})

        seen = set()
        unique_kpis = []
        for kpi in kpis:
            key = (kpi['label'], kpi['value'])
            if key not in seen:
                seen.add(key)
                unique_kpis.append(kpi)

        return unique_kpis[:30]

    def _extract_insights(self, soup: BeautifulSoup) -> List[str]:
        """Extract AI insights/analysis text from dashboard."""
        insights = []

        insight_selectors = [
            ('class', re.compile(r'insight|analysis|finding|recommendation', re.I)),
            ('class', re.compile(r'ai-|summary|observation', re.I)),
        ]

        for attr, pattern in insight_selectors:
            elements = soup.find_all(attrs={attr: pattern})
            for elem in elements:
                text = elem.get_text(separator=' ', strip=True)
                if text and 20 < len(text) < 1000:
                    insights.append(text)

        return insights[:10]

    def html_to_excel(self, html_content: str, title: str = "Dashboard") -> Tuple[bool, bytes, str]:
        """
        Convert HTML dashboard to Excel with proper data extraction.
        """
        if not self.excel_available:
            return False, b'', "Excel export not available. Install openpyxl."

        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
            from openpyxl.utils import get_column_letter

            soup = BeautifulSoup(html_content, 'html.parser')

            wb = Workbook()
            ws = wb.active
            ws.title = title[:31]

            # Styles
            title_font = Font(bold=True, size=16, color="FFFFFF")
            title_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
            header_font = Font(bold=True, size=11, color="FFFFFF")
            header_fill = PatternFill(start_color="0076CE", end_color="0076CE", fill_type="solid")
            section_font = Font(bold=True, size=12, color="2C3E50")
            cell_alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            center_alignment = Alignment(horizontal="center", vertical="center")
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )

            current_row = 1

            # Dashboard Title
            page_title = soup.find('title')
            title_text = page_title.get_text() if page_title else title
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=6)
            title_cell = ws.cell(row=current_row, column=1, value=title_text)
            title_cell.font = title_font
            title_cell.fill = title_fill
            title_cell.alignment = center_alignment
            ws.row_dimensions[current_row].height = 30
            current_row += 2

            # Date
            date_elem = soup.find(string=re.compile(r'\d{4}[-/]\d{2}[-/]\d{2}|\w+ \d{1,2}, \d{4}'))
            if date_elem:
                ws.cell(row=current_row, column=1, value="Report Date:")
                ws.cell(row=current_row, column=1).font = Font(bold=True)
                ws.cell(row=current_row, column=2, value=date_elem.strip()[:50])
                current_row += 2

            # KPIs
            kpis = self._extract_kpi_data(soup)
            if kpis:
                ws.cell(row=current_row, column=1, value="KEY METRICS SUMMARY")
                ws.cell(row=current_row, column=1).font = section_font
                current_row += 1

                ws.cell(row=current_row, column=1, value="Metric").font = header_font
                ws.cell(row=current_row, column=1).fill = header_fill
                ws.cell(row=current_row, column=1).border = thin_border
                ws.cell(row=current_row, column=2, value="Value").font = header_font
                ws.cell(row=current_row, column=2).fill = header_fill
                ws.cell(row=current_row, column=2).border = thin_border
                current_row += 1

                for kpi in kpis:
                    ws.cell(row=current_row, column=1, value=kpi['label']).border = thin_border
                    ws.cell(row=current_row, column=2, value=kpi['value']).border = thin_border
                    current_row += 1

                current_row += 1

            # Tables
            tables = soup.find_all('table')

            for table_idx, table in enumerate(tables):
                section_header = None
                prev = table.find_previous(['h2', 'h3', 'h4', 'div'])
                if prev:
                    header_text = prev.get_text(strip=True)
                    if header_text and len(header_text) < 100:
                        section_header = header_text

                if section_header:
                    ws.cell(row=current_row, column=1, value=section_header)
                    ws.cell(row=current_row, column=1).font = section_font
                    current_row += 1

                rows = table.find_all('tr')

                for row_idx, row in enumerate(rows):
                    cells = row.find_all(['th', 'td'])

                    for col_idx, cell in enumerate(cells):
                        cell_value = cell.get_text(separator=' ', strip=True)

                        try:
                            clean_value = cell_value.replace(',', '').replace('%', '').replace('₹', '').strip()
                            if clean_value.replace('.', '').replace('-', '').isdigit():
                                cell_value = float(clean_value) if '.' in clean_value else int(clean_value)
                        except:
                            pass

                        excel_cell = ws.cell(row=current_row, column=col_idx + 1, value=cell_value)
                        excel_cell.border = thin_border
                        excel_cell.alignment = cell_alignment

                        if cell.name == 'th' or row_idx == 0:
                            excel_cell.font = header_font
                            excel_cell.fill = header_fill
                            excel_cell.alignment = center_alignment

                    current_row += 1

                current_row += 2

            # Insights
            insights = self._extract_insights(soup)
            if insights:
                ws.cell(row=current_row, column=1, value="AI INSIGHTS & ANALYSIS")
                ws.cell(row=current_row, column=1).font = section_font
                current_row += 1

                for idx, insight in enumerate(insights, 1):
                    ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=6)
                    cell = ws.cell(row=current_row, column=1, value=f"{idx}. {insight}")
                    cell.alignment = Alignment(wrap_text=True, vertical="top")
                    ws.row_dimensions[current_row].height = max(15, len(insight) // 10)
                    current_row += 1

            # Auto-adjust column widths
            for col_num in range(1, 8):
                column_letter = get_column_letter(col_num)
                max_length = 0
                for row in ws.iter_rows(min_col=col_num, max_col=col_num):
                    for cell in row:
                        try:
                            if cell.value:
                                max_length = max(max_length, min(len(str(cell.value)), 50))
                        except:
                            pass
                ws.column_dimensions[column_letter].width = max(max_length + 2, 12)

            output = BytesIO()
            wb.save(output)
            output.seek(0)
            excel_bytes = output.read()

            logger.info(f"Excel generated: {len(excel_bytes)} bytes, {len(tables)} tables, {len(kpis)} KPIs")
            return True, excel_bytes, ""

        except Exception as e:
            logger.error(f"Excel generation failed: {e}", exc_info=True)
            return False, b'', str(e)

    def get_available_formats(self) -> dict:
        """Get list of available export formats."""
        return {
            "html": True,
            "pdf": self.pdf_available,
            "excel": self.excel_available,
        }


# Singleton instance
_export_service = None


def get_export_service() -> ExportService:
    """Get or create ExportService singleton."""
    global _export_service
    if _export_service is None:
        _export_service = ExportService()
    return _export_service
