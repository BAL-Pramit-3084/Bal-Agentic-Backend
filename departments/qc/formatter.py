"""
qc_formatter.py
===============
Data processor for Quality Control Department.

This processor:
1. Queries kpi_qc_despatch_performance (customer despatch)
2. Queries kpi_qc_furnace_heat_composite_analysis (heat turnaround times)
3. Queries kpi_qc_product_deviation (monthly quality rates by furnace)
4. Queries kpi_qc_stock_summary (product stock movements)
5. Queries qm_quality_control (QC lots by material and plant)
6. Queries qm_quality_control_result (test results - moisture, over size)
7. Builds analysisData structure matching the template
8. Handles NULL values gracefully
9. Calculates turnaround times (REPORTING_TIME - RECEIVING_TIME)

Author: Senior ML Engineer
Date: November 2025
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

FURNACE_LIST = ["1", "2", "3", "4", "5"]

# Month name mapping for product deviation query
MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def safe_float(value: Any, default: float = 0.0) -> Optional[float]:
    """Convert value to float, handling NULL/None/Decimal gracefully."""
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if value.upper() in ['NULL', 'NONE', '']:
            return None

    try:
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"Could not convert value '{value}' to float, using default {default}")
        return default


def safe_int(value: Any, default: int = 0) -> Optional[int]:
    """Convert value to int, handling NULL gracefully."""
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if value.upper() in ['NULL', 'NONE', '']:
            return None

    try:
        if isinstance(value, Decimal):
            return int(value)
        return int(float(value))
    except (ValueError, TypeError):
        logger.warning(f"Could not convert value '{value}' to int, using default {default}")
        return default


def calculate_turnaround_minutes(receiving_time: str, reporting_time: str) -> Optional[int]:
    """
    Calculate turnaround time in minutes between two time strings.
    Handles midnight rollover (e.g., 22:30 to 01:45 next day).

    Args:
        receiving_time: Time string (HH:MM:SS or HH:MM)
        reporting_time: Time string (HH:MM:SS or HH:MM)

    Returns:
        Turnaround time in minutes, or None if calculation fails
    """
    try:
        # Parse time strings
        rec_time = datetime.strptime(receiving_time.strip(), "%H:%M:%S").time()
        rep_time = datetime.strptime(reporting_time.strip(), "%H:%M:%S").time()

        # Create datetime objects for today
        today = datetime.today().date()
        rec_dt = datetime.combine(today, rec_time)
        rep_dt = datetime.combine(today, rep_time)

        # If reporting time is earlier than receiving time, it crossed midnight
        if rep_dt < rec_dt:
            rep_dt += timedelta(days=1)

        # Calculate difference in minutes
        delta = rep_dt - rec_dt
        minutes = int(delta.total_seconds() / 60)

        return minutes
    except Exception as e:
        logger.warning(f"Error calculating turnaround time: {e}")
        return None


# ============================================================================
# QC DATA PROCESSOR CLASS
# ============================================================================

class QCDataProcessor:
    """
    Process QC data for dashboard generation.
    """

    def __init__(self, mcp_server):
        """
        Initialize processor.

        Args:
            mcp_server: MCP server instance (from mcp_server.py)
        """
        self.mcp = mcp_server

    def process_date(self, date: str) -> Dict[str, Any]:
        """
        Main entry point: Process all QC data for a specific date.

        Args:
            date: Date string in YYYY-MM-DD format

        Returns:
            Dictionary matching template's analysisData structure
        """
        logger.info(f"Processing QC data for date: {date}")

        # Parse date to get month, year, and day for product deviation query
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        month_name = MONTH_NAMES[date_obj.month]
        year = date_obj.year
        day_of_month = date_obj.day

        # Query all tables
        despatch_data = self._query_despatch_performance(date)
        heat_data = self._query_heat_analysis(date)
        product_quality_data = self._query_product_deviation(month_name, year)
        stock_data = self._query_stock_summary(date)
        qc_lots_data = self._query_qc_lots(date)
        test_results_data = self._query_test_results(date)

        # Build analysisData structure
        analysis_data = {
            "date": date,
            "month": month_name,
            "year": year,
            "despatch": self._build_despatch_section(despatch_data),
            "qc_lots": self._build_qc_lots_section(qc_lots_data),
            "tests": self._build_tests_section(test_results_data),
            "heat_analysis": self._build_heat_analysis_section(heat_data),
            "product_quality": self._build_product_quality_section(product_quality_data, day_of_month),
            "stock": self._build_stock_section(stock_data)
        }

        # Check if we have any data
        has_data = self._check_has_data(analysis_data)
        analysis_data["has_data"] = has_data

        logger.info(f"QC data processing complete. Has data: {has_data}")
        return analysis_data

    def _query_despatch_performance(self, date: str) -> List[Dict]:
        """Query kpi_qc_despatch_performance table."""
        query = f"""
            SELECT customer, planned_qty, actual_qty, variance, reason, dept_responsible
            FROM kpi_qc_despatch_performance
            WHERE report_date = '{date}'
            ORDER BY customer
        """

        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} despatch records")
                return result["data"]
            else:
                logger.error(f"Despatch query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying despatch performance: {e}", exc_info=True)
            return []

    def _query_heat_analysis(self, date: str) -> List[Dict]:
        """Query kpi_qc_furnace_heat_composite_analysis table."""
        query = f"""
            SELECT FURNACE, HEAT_NO, RECEIVING_TIME, REPORTING_TIME
            FROM kpi_qc_furnace_heat_composite_analysis
            WHERE DATE = '{date}'
            ORDER BY FURNACE, HEAT_NO
        """

        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} heat analysis records")
                return result["data"]
            else:
                logger.error(f"Heat analysis query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying heat analysis: {e}", exc_info=True)
            return []

    def _query_product_deviation(self, month_name: str, year: int) -> List[Dict]:
        """
        Query kpi_qc_product_deviation table for monthly data.
        Uses the widest week range that includes the selected date.
        """
        query = f"""
            SELECT FURNACE_NO, WEEK, PROD_QTY_MT, QUALITY_RATE_PERCENTAGE,
                   DEFECT_PERCENTAGE, TOTAL_DEVIATION_MT
            FROM kpi_qc_product_deviation
            WHERE MONTH = '{month_name}' AND YEAR = {year}
            ORDER BY FURNACE_NO, WEEK
        """

        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} product deviation records")
                return result["data"]
            else:
                logger.error(f"Product deviation query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying product deviation: {e}", exc_info=True)
            return []

    def _query_stock_summary(self, date: str) -> List[Dict]:
        """Query kpi_qc_stock_summary table."""
        query = f"""
            SELECT product, os_mt, td_mt, rec_qty_mtd, fines_add, fines_less,
                   returned, mtd_despatch, closing_stock
            FROM kpi_qc_stock_summary
            WHERE report_date = '{date}'
            ORDER BY product
        """

        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} stock records")
                return result["data"]
            else:
                logger.error(f"Stock query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying stock summary: {e}", exc_info=True)
            return []

    def _query_qc_lots(self, date: str) -> List[Dict]:
        """Query qm_quality_control table for QC lots."""
        query = f"""
            SELECT LOT_NUMBER, PLANT, MATERIAL_DESC, MATERIAL_TYPE, ACTUAL_LOT_QUANTITY
            FROM qm_quality_control
            WHERE QLT_START_DATE = '{date}'
            ORDER BY PLANT, MATERIAL_DESC
        """

        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} QC lot records")
                return result["data"]
            else:
                logger.error(f"QC lots query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying QC lots: {e}", exc_info=True)
            return []

    def _query_test_results(self, date: str) -> List[Dict]:
        """Query qm_quality_control_result joined with qm_quality_control."""
        query = f"""
            SELECT r.LOT_NUMBER, r.SHORT_TEXT_INS_CHAR, r.RESULTS, r.MATERIAL_DESC, r.PLANT
            FROM qm_quality_control_result r
            INNER JOIN qm_quality_control q ON r.LOT_NUMBER = q.LOT_NUMBER
            WHERE q.QLT_START_DATE = '{date}'
            ORDER BY r.SHORT_TEXT_INS_CHAR, r.LOT_NUMBER
        """

        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} test result records")
                return result["data"]
            else:
                logger.error(f"Test results query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying test results: {e}", exc_info=True)
            return []

    def _build_despatch_section(self, data: List[Dict]) -> Dict[str, Any]:
        """Build despatch performance section."""
        customers = []
        total_planned = 0.0
        total_actual = 0.0

        for row in data:
            customer = row.get('customer', 'Unknown')
            planned = safe_float(row.get('planned_qty'), 0) or 0
            actual = safe_float(row.get('actual_qty'), 0) or 0
            variance = safe_float(row.get('variance'), 0) or 0

            customers.append({
                "customer": customer,
                "planned_qty": planned,
                "actual_qty": actual,
                "variance": variance,
                "reason": row.get('reason', ''),
                "dept_responsible": row.get('dept_responsible', '')
            })

            total_planned += planned
            total_actual += actual

        achievement_pct = (total_actual / total_planned * 100) if total_planned > 0 else 0

        return {
            "customers": customers,
            "total_planned": total_planned,
            "total_actual": total_actual,
            "total_variance": total_actual - total_planned,
            "achievement_pct": achievement_pct
        }

    def _build_qc_lots_section(self, data: List[Dict]) -> Dict[str, Any]:
        """Build QC lots section with material and plant breakdown."""
        # Group by material
        material_counts = defaultdict(lambda: {"count": 0, "total_qty": 0.0})
        plant_counts = defaultdict(int)

        total_lots = len(data)

        for row in data:
            material = row.get('MATERIAL_DESC', 'Unknown')
            plant = row.get('PLANT', 'Unknown')
            qty = safe_float(row.get('ACTUAL_LOT_QUANTITY'), 0) or 0

            # Simplify material names for grouping
            material_key = material.split(':')[0].strip() if ':' in material else material

            material_counts[material_key]["count"] += 1
            material_counts[material_key]["total_qty"] += qty
            plant_counts[plant] += 1

        # Convert to lists
        by_material = [
            {
                "material": mat,
                "count": data["count"],
                "total_qty": data["total_qty"]
            }
            for mat, data in material_counts.items()
        ]

        by_plant = [
            {"plant": plant, "count": count}
            for plant, count in plant_counts.items()
        ]

        return {
            "total_lots": total_lots,
            "by_material": by_material,
            "by_plant": by_plant
        }

    def _build_tests_section(self, data: List[Dict]) -> Dict[str, Any]:
        """Build tests section with test type breakdown."""
        test_type_counts = defaultdict(int)
        total_tests = len(data)

        for row in data:
            test_type = row.get('SHORT_TEXT_INS_CHAR', 'Unknown').strip()
            test_type_counts[test_type] += 1

        by_type = [
            {"test_type": test, "count": count}
            for test, count in test_type_counts.items()
        ]

        return {
            "total_tests": total_tests,
            "by_type": by_type
        }

    def _build_heat_analysis_section(self, data: List[Dict]) -> Dict[str, Any]:
        """Build heat analysis section with turnaround times."""
        furnace_data = defaultdict(lambda: {"heats": [], "turnaround_times": []})

        for row in data:
            furnace = row.get('FURNACE', 'Unknown')
            receiving_time = row.get('RECEIVING_TIME', '')
            reporting_time = row.get('REPORTING_TIME', '')

            turnaround = calculate_turnaround_minutes(receiving_time, reporting_time)

            furnace_data[furnace]["heats"].append({
                "heat_no": row.get('HEAT_NO', ''),
                "receiving_time": receiving_time,
                "reporting_time": reporting_time,
                "turnaround_minutes": turnaround
            })

            if turnaround is not None:
                furnace_data[furnace]["turnaround_times"].append(turnaround)

        # Calculate averages
        by_furnace = []
        for furnace in FURNACE_LIST:
            heats = furnace_data[furnace]["heats"]
            turnaround_times = furnace_data[furnace]["turnaround_times"]

            avg_turnaround = (
                sum(turnaround_times) / len(turnaround_times)
                if turnaround_times else 0
            )

            by_furnace.append({
                "furnace": furnace,
                "num_heats": len(heats),
                "avg_turnaround_minutes": avg_turnaround,
                "heats": heats
            })

        return {
            "by_furnace": by_furnace,
            "total_heats": sum(len(f["heats"]) for f in by_furnace)
        }

    def _build_product_quality_section(self, data: List[Dict], day_of_month: int = 31) -> Dict[str, Any]:
        """
        Build product quality section from monthly data.
        Uses the week range that contains the selected day.

        Week ranges are cumulative:
        - 1-8: Week 1 (days 1-8)
        - 1-15: Week 1+2 (days 1-15)
        - 1-23: Week 1+2+3 (days 1-23)
        - 1-31: Full month (days 1-31)

        Args:
            data: List of product deviation records
            day_of_month: Day of month (1-31) to select appropriate week range
        """
        # Find all week ranges per furnace
        week_ranges = defaultdict(list)

        for row in data:
            furnace = row.get('FURNACE_NO', '')
            week = row.get('WEEK', '')
            if furnace and week:
                week_ranges[furnace].append(week)

        # Select appropriate week range per furnace based on day_of_month
        furnace_quality = []

        for furnace in FURNACE_LIST:
            weeks = week_ranges.get(furnace, [])
            if not weeks:
                furnace_quality.append({
                    "furnace": furnace,
                    "production_mt": 0,
                    "quality_rate_pct": 0,
                    "defect_pct": 0,
                    "deviation_mt": 0
                })
                continue

            # Find the smallest week range that includes the day_of_month
            # e.g., for day 5, use "1-8"; for day 12, use "1-15"
            valid_weeks = []
            for w in weeks:
                if '-' in w:
                    try:
                        end_day = int(w.split('-')[-1])
                        if end_day >= day_of_month:
                            valid_weeks.append((w, end_day))
                    except ValueError:
                        continue

            if valid_weeks:
                # Select smallest range that includes the day
                selected_week = min(valid_weeks, key=lambda x: x[1])[0]
            else:
                # Fallback to widest available if no valid range
                selected_week = max(weeks, key=lambda w: int(w.split('-')[-1]) if '-' in w else 0)

            logger.debug(f"Furnace {furnace}: day={day_of_month}, selected week={selected_week}")

            # Get data for this week range
            row = next(
                (r for r in data if r.get('FURNACE_NO') == furnace and r.get('WEEK') == selected_week),
                None
            )

            if row:
                furnace_quality.append({
                    "furnace": furnace,
                    "production_mt": safe_float(row.get('PROD_QTY_MT'), 0) or 0,
                    "quality_rate_pct": safe_float(row.get('QUALITY_RATE_PERCENTAGE'), 0) or 0,
                    "defect_pct": safe_float(row.get('DEFECT_PERCENTAGE'), 0) or 0,
                    "deviation_mt": safe_float(row.get('TOTAL_DEVIATION_MT'), 0) or 0,
                    "week_range": selected_week
                })

        return {
            "by_furnace": furnace_quality
        }

    def _build_stock_section(self, data: List[Dict]) -> Dict[str, Any]:
        """Build stock summary section."""
        products = []

        for row in data:
            products.append({
                "product": row.get('product', 'Unknown'),
                "opening_stock": safe_float(row.get('os_mt'), 0) or 0,
                "today_production": safe_float(row.get('td_mt'), 0) or 0,
                "mtd_received": safe_float(row.get('rec_qty_mtd'), 0) or 0,
                "fines_add": safe_float(row.get('fines_add'), 0) or 0,
                "fines_less": safe_float(row.get('fines_less'), 0) or 0,
                "returned": safe_float(row.get('returned'), 0) or 0,
                "mtd_despatch": safe_float(row.get('mtd_despatch'), 0) or 0,
                "closing_stock": safe_float(row.get('closing_stock'), 0) or 0
            })

        return {
            "products": products
        }

    def _check_has_data(self, analysis_data: Dict) -> bool:
        """Check if we have any actual data (not all empty)."""
        # Check despatch data
        if analysis_data.get('despatch', {}).get('total_planned', 0) > 0:
            return True

        # Check QC lots
        if analysis_data.get('qc_lots', {}).get('total_lots', 0) > 0:
            return True

        # Check tests
        if analysis_data.get('tests', {}).get('total_tests', 0) > 0:
            return True

        # Check heat analysis
        if analysis_data.get('heat_analysis', {}).get('total_heats', 0) > 0:
            return True

        return False

    # ========================================================================
    # NEW RANGE-SPECIFIC METHODS
    # ========================================================================

    def process_date_range(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        NEW: Process all QC data for a DATE RANGE.

        Args:
            start_date: Start date string in YYYY-MM-DD format
            end_date: End date string in YYYY-MM-DD format

        Returns:
            Dictionary with period_kpis (aggregated metrics for the entire range)
        """
        logger.info(f"Processing QC data for range: {start_date} to {end_date}")

        # Parse and validate dates
        start_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_obj = datetime.strptime(end_date, '%Y-%m-%d')

        if start_obj > end_obj:
            raise ValueError("start_date must be before or equal to end_date")

        # Calculate range metadata
        days_in_range = (end_obj - start_obj).days + 1
        start_month_name = MONTH_NAMES[start_obj.month]
        end_month_name = MONTH_NAMES[end_obj.month]

        # Format date range for display
        if start_obj.year == end_obj.year:
            if start_obj.month == end_obj.month:
                date_range_formatted = f"{start_month_name} {start_obj.day}-{end_obj.day}, {start_obj.year}"
            else:
                date_range_formatted = f"{start_month_name} {start_obj.day} - {end_month_name} {end_obj.day}, {start_obj.year}"
        else:
            date_range_formatted = f"{start_month_name} {start_obj.day}, {start_obj.year} - {end_month_name} {end_obj.day}, {end_obj.year}"

        # Query all data for the range
        despatch_range = self._query_despatch_range(start_date, end_date)
        heat_range = self._query_heat_range(start_date, end_date)
        stock_range = self._query_stock_range(start_date, end_date)
        qc_lots_range = self._query_qc_lots_range(start_date, end_date)
        test_results_range = self._query_test_results_range(start_date, end_date)

        # For product quality, use the start date's month
        month_name = MONTH_NAMES[start_obj.month]
        year = start_obj.year
        product_quality_data = self._query_product_deviation(month_name, year)

        # Build analysis data structure (RANGE version)
        analysis_data = {
            "start_date": start_date,
            "end_date": end_date,
            "date_range_formatted": date_range_formatted,
            "days_in_range": days_in_range,
            "year": start_obj.year,
            "month": start_month_name,

            # PERIOD KPIs (aggregated across range)
            "period_kpis": self._build_period_kpis_range(
                despatch_range, heat_range, stock_range, qc_lots_range, test_results_range
            ),

            # Detailed sections (aggregated)
            "despatch": self._build_despatch_section_range(despatch_range),
            "qc_lots": self._build_qc_lots_section_range(qc_lots_range),
            "tests": self._build_tests_section_range(test_results_range),
            "heat_analysis": self._build_heat_analysis_section_range(heat_range),
            "product_quality": self._build_product_quality_section(product_quality_data, start_obj.day),
            "stock": self._build_stock_section_range(stock_range)
        }

        # Check if we have any data
        has_data = len(despatch_range) > 0 or len(heat_range) > 0 or len(qc_lots_range) > 0
        analysis_data["has_data"] = has_data

        logger.info(f"QC range processing complete. Has data: {has_data}, Days: {days_in_range}")
        return analysis_data

    # Range query methods
    def _query_despatch_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Query despatch performance for date range."""
        query = f"""
            SELECT customer, planned_qty, actual_qty, variance, reason, dept_responsible, report_date
            FROM kpi_qc_despatch_performance
            WHERE report_date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY report_date, customer
        """
        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} despatch records for range")
                return result["data"]
            else:
                logger.error(f"Despatch range query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying despatch range: {e}", exc_info=True)
            return []

    def _query_heat_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Query heat analysis for date range."""
        query = f"""
            SELECT FURNACE, HEAT_NO, RECEIVING_TIME, REPORTING_TIME, DATE
            FROM kpi_qc_furnace_heat_composite_analysis
            WHERE DATE BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY DATE, FURNACE, HEAT_NO
        """
        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} heat records for range")
                return result["data"]
            else:
                logger.error(f"Heat range query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying heat range: {e}", exc_info=True)
            return []

    def _query_stock_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Query stock summary for date range."""
        query = f"""
            SELECT product, opening_stock, receipts, despatches, closing_stock, report_date
            FROM kpi_qc_stock_summary
            WHERE report_date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY report_date, product
        """
        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} stock records for range")
                return result["data"]
            else:
                logger.error(f"Stock range query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying stock range: {e}", exc_info=True)
            return []

    def _query_qc_lots_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Query QC lots for date range."""
        query = f"""
            SELECT material, plant, material_desc, inspection_lot, qty
            FROM qm_quality_control
            WHERE inspection_lot_created_on BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY inspection_lot_created_on, material
        """
        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} QC lot records for range")
                return result["data"]
            else:
                logger.error(f"QC lots range query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying QC lots range: {e}", exc_info=True)
            return []

    def _query_test_results_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Query test results for date range."""
        query = f"""
            SELECT inspection_lot, plant, material_desc, characteristic,
                   characteristic_desc, mean_value, lower_limit, upper_limit
            FROM qm_quality_control_result
            WHERE inspection_lot_created_on BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY inspection_lot_created_on, inspection_lot, characteristic
        """
        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} test result records for range")
                return result["data"]
            else:
                logger.error(f"Test results range query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying test results range: {e}", exc_info=True)
            return []

    # Range aggregation methods
    def _build_period_kpis_range(self, despatch_range, heat_range, stock_range, qc_lots_range, test_results_range) -> Dict[str, Any]:
        """Build period KPIs aggregated across range."""
        # Aggregate despatch metrics
        total_planned = sum(safe_float(r.get('planned_qty'), 0) for r in despatch_range)
        total_actual = sum(safe_float(r.get('actual_qty'), 0) for r in despatch_range)
        total_variance = total_actual - total_planned
        achievement_pct = (total_actual / total_planned * 100) if total_planned > 0 else 0

        # Count unique customers
        unique_customers = len(set(r.get('customer') for r in despatch_range if r.get('customer')))

        # Aggregate heat analysis
        total_heats = len(heat_range)
        turnaround_times = []
        for heat in heat_range:
            receiving = heat.get('RECEIVING_TIME')
            reporting = heat.get('REPORTING_TIME')
            if receiving and reporting:
                turnaround = calculate_turnaround_minutes(str(receiving), str(reporting))
                if turnaround is not None:
                    turnaround_times.append(turnaround)

        avg_turnaround = sum(turnaround_times) / len(turnaround_times) if turnaround_times else 0

        # Aggregate QC lots
        total_lots = len(qc_lots_range)
        total_qty_inspected = sum(safe_float(r.get('qty'), 0) for r in qc_lots_range)

        # Aggregate test results
        total_tests = len(test_results_range)

        return {
            "total_despatch": {
                "planned": round(total_planned, 2),
                "actual": round(total_actual, 2),
                "variance": round(total_variance, 2),
                "achievement_pct": round(achievement_pct, 1),
            },
            "customers_served": unique_customers,
            "heat_analysis": {
                "total_heats": total_heats,
                "avg_turnaround_minutes": round(avg_turnaround),
            },
            "qc_lots": {
                "total_lots": total_lots,
                "total_qty": round(total_qty_inspected, 2),
            },
            "tests": {
                "total_tests": total_tests,
            },
        }

    def _build_despatch_section_range(self, despatch_range: List[Dict]) -> Dict[str, Any]:
        """Build despatch section aggregated by customer."""
        from collections import defaultdict
        customer_data = defaultdict(lambda: {"planned": 0, "actual": 0, "variance": 0})

        for r in despatch_range:
            customer = r.get('customer', 'Unknown')
            customer_data[customer]["planned"] += safe_float(r.get('planned_qty'), 0)
            customer_data[customer]["actual"] += safe_float(r.get('actual_qty'), 0)

        # Build rows
        rows = []
        total_planned = 0
        total_actual = 0

        for customer, data in sorted(customer_data.items()):
            variance = data["actual"] - data["planned"]
            rows.append({
                "customer": customer,
                "planned_qty": round(data["planned"], 2),
                "actual_qty": round(data["actual"], 2),
                "variance": round(variance, 2),
                "status": "On Track" if variance >= 0 else "Below Plan"
            })
            total_planned += data["planned"]
            total_actual += data["actual"]

        return {
            "rows": rows,
            "total_planned": round(total_planned, 2),
            "total_actual": round(total_actual, 2),
            "total_variance": round(total_actual - total_planned, 2),
        }

    def _build_qc_lots_section_range(self, qc_lots_range: List[Dict]) -> Dict[str, Any]:
        """Build QC lots section aggregated by material."""
        from collections import defaultdict
        material_data = defaultdict(lambda: {"qty": 0, "lots": 0})

        for r in qc_lots_range:
            material = r.get('material_desc', 'Unknown')
            material_data[material]["qty"] += safe_float(r.get('qty'), 0)
            material_data[material]["lots"] += 1

        # Build rows
        rows = []
        for material, data in sorted(material_data.items()):
            rows.append({
                "material": material,
                "lots": data["lots"],
                "qty": round(data["qty"], 2),
            })

        return {
            "rows": rows,
            "total_lots": sum(d["lots"] for d in material_data.values()),
            "total_qty": round(sum(d["qty"] for d in material_data.values()), 2),
        }

    def _build_tests_section_range(self, test_results_range: List[Dict]) -> Dict[str, Any]:
        """Build tests section aggregated."""
        total_tests = len(test_results_range)

        # Group by characteristic
        from collections import defaultdict
        char_data = defaultdict(list)

        for r in test_results_range:
            char = r.get('characteristic_desc', 'Unknown')
            mean = safe_float(r.get('mean_value'))
            if mean is not None:
                char_data[char].append(mean)

        # Build summary
        rows = []
        for char, values in sorted(char_data.items()):
            avg_value = sum(values) / len(values) if values else 0
            rows.append({
                "characteristic": char,
                "samples": len(values),
                "avg_value": round(avg_value, 2),
            })

        return {
            "rows": rows,
            "total_tests": total_tests,
        }

    def _build_heat_analysis_section_range(self, heat_range: List[Dict]) -> Dict[str, Any]:
        """Build heat analysis section aggregated by furnace."""
        from collections import defaultdict
        furnace_data = defaultdict(lambda: {"heats": 0, "turnaround_times": []})

        for r in heat_range:
            furnace = str(r.get('FURNACE', 'Unknown'))
            furnace_data[furnace]["heats"] += 1

            receiving = r.get('RECEIVING_TIME')
            reporting = r.get('REPORTING_TIME')
            if receiving and reporting:
                turnaround = calculate_turnaround_minutes(str(receiving), str(reporting))
                if turnaround is not None:
                    furnace_data[furnace]["turnaround_times"].append(turnaround)

        # Build rows
        rows = []
        for furnace in FURNACE_LIST:
            data = furnace_data.get(furnace, {"heats": 0, "turnaround_times": []})
            avg_turnaround = sum(data["turnaround_times"]) / len(data["turnaround_times"]) if data["turnaround_times"] else 0

            rows.append({
                "furnace": furnace,
                "heats": data["heats"],
                "avg_turnaround_minutes": round(avg_turnaround),
            })

        return {
            "rows": rows,
            "total_heats": sum(d["heats"] for d in furnace_data.values()),
        }

    def _build_stock_section_range(self, stock_range: List[Dict]) -> Dict[str, Any]:
        """Build stock section - use last day's closing as current."""
        # Group by product and get latest closing stock
        from collections import defaultdict
        product_latest = {}

        for r in sorted(stock_range, key=lambda x: x.get('report_date', '')):
            product = r.get('product', 'Unknown')
            product_latest[product] = {
                "closing_stock": safe_float(r.get('closing_stock'), 0),
                "receipts": safe_float(r.get('receipts'), 0),
                "despatches": safe_float(r.get('despatches'), 0),
            }

        # Build rows
        rows = []
        for product, data in sorted(product_latest.items()):
            rows.append({
                "product": product,
                "closing_stock": round(data["closing_stock"], 2),
            })

        return {
            "rows": rows,
            "total_products": len(rows),
        }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['QCDataProcessor']