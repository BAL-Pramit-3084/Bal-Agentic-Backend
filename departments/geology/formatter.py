"""
geology_survey_formatter.py
============================
Data processor for Mines Department - Geology & Survey Dashboard.

This processor:
1. Queries mines_day_wise_excavation (actual daily production)
2. Queries mines_geology_face_sample_analysis (quality/grade data)
3. Queries mines_monthly_excavation_plan (monthly targets)
4. Queries mines_daily_excavation_plan (daily targets - for grade breakdown)
5. Joins with master tables (location, variant, agency)
6. Calculates TD (Today) and MTD (Month-to-Date) metrics
7. Builds analysisData structure matching the template
8. Handles NULL values gracefully

Author: Senior ML Engineer
Date: December 2025
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

MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}

MONTH_ABBREV = {
    1: "JAN", 2: "FEB", 3: "MAR", 4: "APR",
    5: "MAY", 6: "JUN", 7: "JUL", 8: "AUG",
    9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC"
}

DAY_NAMES = {
    0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday",
    4: "Friday", 5: "Saturday", 6: "Sunday"
}

# Grade classification thresholds for Cr2O3
GRADE_HG_THRESHOLD = 52.0  # High Grade >= 52%
GRADE_MG_THRESHOLD = 40.0  # Medium Grade >= 40%
# Low Grade < 40%


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert value to float, handling NULL/None/Decimal and strings with units."""
    if value is None:
        return default
    try:
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
        # Handle strings with units like "108 CuM", "80 Mt", "318 CuM"
        if isinstance(value, str):
            value = value.strip()
            # Extract numeric portion from beginning of string
            import re as re_module
            match = re_module.match(r'^[\d,.]+', value)
            if match:
                # Remove commas and convert
                num_str = match.group().replace(',', '')
                return float(num_str)
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Convert value to int safely."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """Convert value to string safely."""
    if value is None:
        return default
    return str(value).strip()


def format_number(value: float, decimals: int = 0) -> str:
    """Format number with commas."""
    if decimals == 0:
        return f"{value:,.0f}"
    return f"{value:,.{decimals}f}"


def format_mt(value: float) -> str:
    """Format value as MT (Metric Tons)."""
    return f"{value:,.0f} MT"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format value as percentage."""
    return f"{value:.{decimals}f}%"


def classify_grade(cr2o3: float) -> str:
    """Classify ore grade based on Cr2O3 percentage."""
    if cr2o3 >= GRADE_HG_THRESHOLD:
        return "HG"
    elif cr2o3 >= GRADE_MG_THRESHOLD:
        return "MG"
    else:
        return "LG"


def get_grade_badge_class(grade: str) -> str:
    """Get CSS badge class for grade."""
    return f"badge-{grade.lower()}"


def get_shift_badge_class(shift: str) -> str:
    """Get CSS badge class for shift."""
    return f"badge-shift-{shift.lower()}"


def calculate_change_indicator(current: float, average: float) -> Dict[str, Any]:
    """Calculate change indicator (positive/negative/neutral)."""
    if average == 0:
        return {"type": "neutral", "text": "No baseline", "value": 0}

    pct_change = ((current - average) / average) * 100

    if pct_change > 5:
        return {"type": "positive", "text": f"▲ {abs(pct_change):.1f}% vs Avg", "value": pct_change}
    elif pct_change < -5:
        return {"type": "negative", "text": f"▼ {abs(pct_change):.1f}% vs Avg", "value": pct_change}
    else:
        return {"type": "neutral", "text": "Same as Avg", "value": pct_change}


# ============================================================================
# GEOLOGY SURVEY DATA PROCESSOR CLASS
# ============================================================================

class GeologySurveyDataProcessor:
    """
    Process Geology & Survey data for dashboard generation.
    """

    def __init__(self, mcp_client):
        """
        Initialize with MCP client for database queries.

        Args:
            mcp_client: MCP client instance with query() method
        """
        self.mcp = mcp_client
        self.database = "balcorpdb"
        logger.info("Geology Survey Data Processor initialized")

    def process_date(self, date: str) -> Dict[str, Any]:
        """
        Main entry point: Process all Geology & Survey data for a specific date.

        Args:
            date: Date string in YYYY-MM-DD format

        Returns:
            Dictionary matching template's analysisData structure
        """
        logger.info(f"Processing Geology Survey data for date: {date}")

        # Parse date
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        month_start = date_obj.replace(day=1).strftime('%Y-%m-%d')
        month_name = MONTH_NAMES[date_obj.month]
        day_name = DAY_NAMES[date_obj.weekday()]
        month_year = date_obj.strftime('%Y-%m')  # For monthly plan lookup

        # Calculate days in month and days elapsed
        if date_obj.month == 12:
            next_month = date_obj.replace(year=date_obj.year + 1, month=1, day=1)
        else:
            next_month = date_obj.replace(month=date_obj.month + 1, day=1)
        days_in_month = (next_month - date_obj.replace(day=1)).days
        days_elapsed = date_obj.day
        time_elapsed_pct = (days_elapsed / days_in_month) * 100

        # Load master data first
        locations = self._load_location_master()
        variants = self._load_variant_master()
        agencies = self._load_agency_master()

        # Query excavation data - Today
        excavation_td = self._query_excavation(date, date)

        # Query excavation data - MTD
        excavation_mtd = self._query_excavation(month_start, date)

        # Query sample analysis data - Today
        samples_td = self._query_sample_analysis(date, date)

        # Query sample analysis data - MTD
        samples_mtd = self._query_sample_analysis(month_start, date)

        # Query monthly plan
        monthly_plan = self._query_monthly_plan(month_year)

        # Query daily plan (for today)
        daily_plan = self._query_daily_plan(date)

        # Build analysisData structure
        analysis_data = {
            "date": date,
            "date_formatted": f"{day_name}, {month_name} {date_obj.day}, {date_obj.year}",
            "day": date_obj.day,
            "month": month_name,
            "month_num": date_obj.month,
            "year": date_obj.year,
            "day_name": day_name,
            "month_year": month_year,
            "days_in_month": days_in_month,
            "days_elapsed": days_elapsed,
            "days_remaining": days_in_month - days_elapsed,
            "time_elapsed_pct": round(time_elapsed_pct, 1),

            # Master data references
            "masters": {
                "locations": locations,
                "variants": variants,
                "agencies": agencies,
            },

            # Today's KPI Summary
            "today_kpis": self._build_today_kpis(excavation_td, samples_td, excavation_mtd),

            # MTD Summary KPIs
            "mtd_kpis": self._build_mtd_kpis(excavation_mtd, samples_mtd),

            # Shift-wise Plan vs Actual (Today) - Uses daily plan
            "shift_plan_vs_actual": self._build_shift_plan_vs_actual(daily_plan, excavation_td),

            # Shift-wise breakdown (Today) - For backwards compatibility
            "shift_breakdown": self._build_shift_breakdown(excavation_td, locations),

            # Location-wise breakdown (Today)
            "location_breakdown": self._build_location_breakdown(excavation_td, locations),

            # Agency performance (Today & MTD)
            "agency_performance": self._build_agency_performance(excavation_td, excavation_mtd, agencies),

            # Sample analysis (Today)
            "sample_analysis": self._build_sample_analysis(samples_td, locations),

            # Daily production trend (T-12 to selected date)
            "daily_trend": self._build_daily_trend(excavation_mtd, date),

            # Quality parameter trends (T-12 to selected date)
            "quality_trend": self._build_quality_trend(samples_mtd, date),

            # MTD Location performance
            "mtd_location_performance": self._build_mtd_location_performance(excavation_mtd, locations),

            # Monthly Plan vs Actual
            "plan_vs_actual": self._build_plan_vs_actual(monthly_plan, excavation_mtd, locations),

            # Daily Plan vs Actual (Today) - includes grade breakdown
            "daily_plan_summary": self._build_daily_plan_summary(daily_plan, excavation_td, locations),

            # Detailed excavation records (Today)
            "excavation_details": self._build_excavation_details(excavation_td, locations, variants, agencies),

            # MTD Quality Statistics
            "mtd_quality_stats": self._build_mtd_quality_stats(samples_mtd),

            # Gap Analysis metrics (for insights)
            "gap_analysis": self._build_gap_analysis(monthly_plan, excavation_mtd, days_elapsed, days_in_month),
        }

        # Check if we have any data
        has_data = self._check_has_data(analysis_data)
        analysis_data["has_data"] = has_data

        logger.info(f"Geology Survey data processing complete. Has data: {has_data}")
        return analysis_data

    def process_date_range(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        NEW: Process all Geology & Survey data for a DATE RANGE.

        Args:
            start_date: Start date string in YYYY-MM-DD format
            end_date: End date string in YYYY-MM-DD format

        Returns:
            Dictionary with period_kpis (aggregated metrics for the entire range)
        """
        logger.info(f"Processing Geology Survey data for range: {start_date} to {end_date}")

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

        # Load master data
        locations = self._load_location_master()
        variants = self._load_variant_master()
        agencies = self._load_agency_master()

        # Query all data for the entire range
        excavation_range = self._query_excavation(start_date, end_date)
        samples_range = self._query_sample_analysis(start_date, end_date)

        # Query monthly plan (use start date's month for reference)
        month_year = start_obj.strftime('%Y-%m')
        monthly_plan = self._query_monthly_plan(month_year)

        # Query daily plan for the range (for shift plan vs actual)
        daily_plan_range = self._query_daily_plan_range(start_date, end_date)

        # Build analysis data structure (RANGE version)
        analysis_data = {
            "start_date": start_date,
            "end_date": end_date,
            "date_range_formatted": date_range_formatted,
            "days_in_range": days_in_range,
            "year": start_obj.year,

            # Master data references
            "masters": {
                "locations": locations,
                "variants": variants,
                "agencies": agencies,
            },

            # PERIOD KPIs (aggregated across entire range)
            "period_kpis": self._build_period_kpis(excavation_range, samples_range),

            # Shift-wise Plan vs Actual (aggregated across range)
            "shift_plan_vs_actual": self._build_shift_plan_vs_actual_range(daily_plan_range, excavation_range),

            # Shift-wise breakdown (aggregated across range) - For backwards compatibility
            "shift_breakdown": self._build_shift_breakdown_range(excavation_range, locations),

            # Location-wise breakdown (aggregated across range)
            "location_breakdown": self._build_location_breakdown(excavation_range, locations),

            # Agency performance (aggregated across range)
            "agency_performance": self._build_agency_performance_range(excavation_range, agencies),

            # Sample analysis (all samples in range)
            "sample_analysis": self._build_sample_analysis(samples_range, locations),

            # Daily production trend (all days in range)
            "daily_trend": self._build_daily_trend_range(excavation_range, start_date, end_date),

            # Quality parameter trends (all days in range)
            "quality_trend": self._build_quality_trend_range(samples_range, start_date, end_date),

            # Location performance for range
            "location_performance": self._build_mtd_location_performance(excavation_range, locations),

            # Plan vs Actual (using DAILY PLAN data for accurate comparison)
            "plan_vs_actual": self._build_plan_vs_actual_from_daily(daily_plan_range, excavation_range, locations),

            # Detailed excavation records (all records in range)
            "excavation_details": self._build_excavation_details(excavation_range, locations, variants, agencies),

            # Quality Statistics for range
            "quality_stats": self._build_mtd_quality_stats(samples_range),

            # Daily breakdown (day-by-day within range)
            "daily_breakdown": self._build_daily_breakdown(excavation_range, samples_range, start_date, end_date),

            # Gap Analysis for range (period-based, not monthly)
            "gap_analysis": self._build_gap_analysis_range(monthly_plan, excavation_range, days_in_range),
        }

        # Check if we have any data
        has_data = len(excavation_range) > 0 or len(samples_range) > 0
        analysis_data["has_data"] = has_data

        logger.info(f"Geology Survey range processing complete. Has data: {has_data}, Days: {days_in_range}")
        return analysis_data

    # ========================================================================
    # MASTER DATA LOADERS
    # ========================================================================

    def _load_location_master(self) -> Dict[int, str]:
        """Load location master data into lookup dict."""
        query = "SELECT Loc_Id, Loc_Desc FROM mines_location_master WHERE Status = 'A'"
        try:
            result = self.mcp.query(sql=query, database=self.database)
            if result["success"]:
                return {safe_int(r['Loc_Id']): safe_str(r['Loc_Desc']) for r in result['data']}
            return {}
        except Exception as e:
            logger.error(f"Error loading location master: {e}")
            return {}

    def _load_variant_master(self) -> Dict[int, str]:
        """Load variant master data into lookup dict."""
        query = "SELECT Variant_Id, Variant_Desc FROM mines_variant_master WHERE Status = 'A'"
        try:
            result = self.mcp.query(sql=query, database=self.database)
            if result["success"]:
                return {safe_int(r['Variant_Id']): safe_str(r['Variant_Desc']) for r in result['data']}
            return {}
        except Exception as e:
            logger.error(f"Error loading variant master: {e}")
            return {}

    def _load_agency_master(self) -> Dict[int, str]:
        """Load agency master data into lookup dict."""
        query = "SELECT Agency_Id, Agency_Desc FROM mines_agency_master WHERE Status = 'A'"
        try:
            result = self.mcp.query(sql=query, database=self.database)
            if result["success"]:
                return {safe_int(r['Agency_Id']): safe_str(r['Agency_Desc']) for r in result['data']}
            return {}
        except Exception as e:
            logger.error(f"Error loading agency master: {e}")
            return {}

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def _query_excavation(self, start_date: str, end_date: str) -> List[Dict]:
        """Query mines_day_wise_excavation for date range."""
        query = f"""
            SELECT
                Prod_date, Shift, Loc_Id, Variant, Agency,
                No_Of_trips, Qty, Entry_Id, Entry_Date
            FROM mines_day_wise_excavation
            WHERE Prod_date >= '{start_date}' AND Prod_date <= '{end_date}'
            ORDER BY Prod_date, Shift, Qty DESC
        """
        try:
            result = self.mcp.query(sql=query, database=self.database)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} excavation records")
                return result["data"]
            else:
                logger.error(f"Excavation query failed: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error querying excavation: {e}", exc_info=True)
            return []

    def _query_sample_analysis(self, start_date: str, end_date: str) -> List[Dict]:
        """Query mines_geology_face_sample_analysis for date range."""
        query = f"""
            SELECT
                Prod_date, Shift, LAB_ID, Loc_Id, SAMPLE_ID,
                Cr2O3, FeO, Ratio, Analysis_Name, Entry_Id, Entry_Date
            FROM mines_geology_face_sample_analysis
            WHERE Prod_date >= '{start_date}' AND Prod_date <= '{end_date}'
            ORDER BY Prod_date, Shift
        """
        try:
            result = self.mcp.query(sql=query, database=self.database)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} sample analysis records")
                return result["data"]
            else:
                logger.error(f"Sample analysis query failed: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error querying sample analysis: {e}", exc_info=True)
            return []

    def _query_monthly_plan(self, month_year: str) -> List[Dict]:
        """Query mines_monthly_excavation_plan for a month."""
        query = f"""
            SELECT
                Prod_Month, Shift, Loc_Id, Mode, Z_Range, Grade,
                Tonnage, Cr2O3_Percentage, CrFe_Ratio, Remarks,
                Entry_Id, Entry_Date
            FROM mines_monthly_excavation_plan
            WHERE Prod_Month = '{month_year}'
            ORDER BY Loc_Id, Grade
        """
        try:
            result = self.mcp.query(sql=query, database=self.database)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} monthly plan records")
                return result["data"]
            else:
                logger.error(f"Monthly plan query failed: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error querying monthly plan: {e}", exc_info=True)
            return []

    def _query_daily_plan(self, date: str) -> List[Dict]:
        """Query mines_daily_excavation_plan for a date."""
        query = f"""
            SELECT
                Prod_date, Shift, Loc_Id, Face_Desc,
                OB_QTY_Cum, ORE_QTY, HG_QTY, MG_QTY, LG_QTY,
                Entry_Id, Entry_Date
            FROM mines_daily_excavation_plan
            WHERE Prod_date = '{date}'
            ORDER BY Shift, Loc_Id
        """
        try:
            result = self.mcp.query(sql=query, database=self.database)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} daily plan records")
                return result["data"]
            else:
                logger.error(f"Daily plan query failed: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error querying daily plan: {e}", exc_info=True)
            return []

    def _query_daily_plan_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Query mines_daily_excavation_plan for a date range."""
        query = f"""
            SELECT
                Prod_date, Shift, Loc_Id, Face_Desc,
                OB_QTY_Cum, ORE_QTY, HG_QTY, MG_QTY, LG_QTY,
                Entry_Id, Entry_Date
            FROM mines_daily_excavation_plan
            WHERE Prod_date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY Prod_date, Shift, Loc_Id
        """
        try:
            result = self.mcp.query(sql=query, database=self.database)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} daily plan records for range")
                return result["data"]
            else:
                logger.error(f"Daily plan range query failed: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error querying daily plan range: {e}", exc_info=True)
            return []

    # ========================================================================
    # BUILD SECTION METHODS
    # ========================================================================

    def _build_today_kpis(self, excavation_td: List[Dict], samples_td: List[Dict],
                          excavation_mtd: List[Dict]) -> Dict[str, Any]:
        """Build today's top KPI cards."""
        # Today's excavation totals
        td_qty = sum(safe_float(r.get('Qty')) for r in excavation_td)
        td_trips = sum(safe_int(r.get('No_Of_trips')) for r in excavation_td)
        td_avg_load = td_qty / td_trips if td_trips > 0 else 0
        td_active_locations = len(set(r.get('Loc_Id') for r in excavation_td))

        # Today's quality metrics
        td_cr2o3_values = [safe_float(r.get('Cr2O3')) for r in samples_td if r.get('Cr2O3')]
        td_ratio_values = [safe_float(r.get('Ratio')) for r in samples_td if r.get('Ratio')]
        td_avg_cr2o3 = sum(td_cr2o3_values) / len(td_cr2o3_values) if td_cr2o3_values else 0
        td_avg_ratio = sum(td_ratio_values) / len(td_ratio_values) if td_ratio_values else 0

        # MTD average for comparison
        mtd_qty = sum(safe_float(r.get('Qty')) for r in excavation_mtd)
        mtd_working_days = len(set(r.get('Prod_date') for r in excavation_mtd))
        mtd_avg_daily = mtd_qty / mtd_working_days if mtd_working_days > 0 else 0

        # Change indicators
        qty_change = calculate_change_indicator(td_qty, mtd_avg_daily)

        # Determine grade classification based on avg Cr2O3
        grade_class = classify_grade(td_avg_cr2o3) if td_avg_cr2o3 > 0 else "N/A"

        return {
            "excavation": {
                "value": td_qty,
                "formatted": format_number(td_qty),
                "unit": "MT",
                "change": qty_change,
            },
            "trips": {
                "value": td_trips,
                "formatted": format_number(td_trips),
                "change": {"type": "neutral", "text": "", "value": 0},
            },
            "avg_load": {
                "value": round(td_avg_load, 2),
                "formatted": f"{td_avg_load:.2f}",
                "unit": "MT/trip",
                "change": {"type": "negative" if td_avg_load < 15 else "positive",
                          "text": "Lower Load" if td_avg_load < 15 else "Good Load"},
            },
            "avg_cr2o3": {
                "value": round(td_avg_cr2o3, 1),
                "formatted": f"{td_avg_cr2o3:.1f}%",
                "change": {"type": "positive" if td_avg_cr2o3 >= 50 else "neutral",
                          "text": "High Grade" if td_avg_cr2o3 >= 52 else "Medium Grade" if td_avg_cr2o3 >= 40 else "Low Grade"},
            },
            "avg_ratio": {
                "value": round(td_avg_ratio, 2),
                "formatted": f"{td_avg_ratio:.2f}",
                "change": {"type": "positive" if td_avg_ratio >= 2.5 else "neutral",
                          "text": "Excellent" if td_avg_ratio >= 3 else "Good" if td_avg_ratio >= 2 else "Low"},
            },
            "active_locations": {
                "value": td_active_locations,
                "formatted": str(td_active_locations),
                "change": {"type": "neutral", "text": "Same as Avg"},
            },
            "grade_classification": grade_class,
            "samples_today": len(samples_td),
        }

    def _build_mtd_kpis(self, excavation_mtd: List[Dict], samples_mtd: List[Dict]) -> Dict[str, Any]:
        """Build MTD summary KPI cards with material type breakdown.

        Material Types (Variant_Id):
        - 1 = ORE (HG/MG/LG/LUMP)
        - 3 = OVERBURDEN (OB)
        - 4 = SILT
        """
        # MTD excavation totals
        mtd_qty = sum(safe_float(r.get('Qty')) for r in excavation_mtd)
        mtd_trips = sum(safe_int(r.get('No_Of_trips')) for r in excavation_mtd)
        mtd_working_days = len(set(r.get('Prod_date') for r in excavation_mtd))
        mtd_avg_daily = mtd_qty / mtd_working_days if mtd_working_days > 0 else 0

        # Material type breakdown (Variant: 1=ORE, 3=OB, 4=SILT)
        ore_qty = sum(safe_float(r.get('Qty')) for r in excavation_mtd if safe_int(r.get('Variant')) == 1)
        ob_qty = sum(safe_float(r.get('Qty')) for r in excavation_mtd if safe_int(r.get('Variant')) == 3)
        silt_qty = sum(safe_float(r.get('Qty')) for r in excavation_mtd if safe_int(r.get('Variant')) == 4)

        # MTD quality metrics
        mtd_cr2o3_values = [safe_float(r.get('Cr2O3')) for r in samples_mtd if r.get('Cr2O3')]
        mtd_avg_cr2o3 = sum(mtd_cr2o3_values) / len(mtd_cr2o3_values) if mtd_cr2o3_values else 0
        mtd_samples = len(samples_mtd)

        return {
            "total_excavation": {
                "value": mtd_qty,
                "formatted": format_number(mtd_qty),
                "unit": "MT",
            },
            "ore_qty": {
                "value": ore_qty,
                "formatted": format_number(ore_qty),
                "unit": "MT",
            },
            "ob_qty": {
                "value": ob_qty,
                "formatted": format_number(ob_qty),
                "unit": "MT",
            },
            "silt_qty": {
                "value": silt_qty,
                "formatted": format_number(silt_qty),
                "unit": "MT",
            },
            "total_trips": {
                "value": mtd_trips,
                "formatted": format_number(mtd_trips),
            },
            "working_days": {
                "value": mtd_working_days,
                "formatted": str(mtd_working_days),
            },
            "avg_daily_production": {
                "value": round(mtd_avg_daily),
                "formatted": format_number(mtd_avg_daily),
                "unit": "MT",
            },
            "avg_cr2o3": {
                "value": round(mtd_avg_cr2o3, 1),
                "formatted": f"{mtd_avg_cr2o3:.1f}%",
            },
            "samples_analyzed": {
                "value": mtd_samples,
                "formatted": str(mtd_samples),
            },
        }

    def _build_shift_breakdown(self, excavation_td: List[Dict], locations: Dict[int, str]) -> Dict[str, Any]:
        """Build shift-wise production breakdown for today."""
        shift_data = defaultdict(lambda: {"trips": 0, "qty": 0})

        for r in excavation_td:
            shift = safe_str(r.get('Shift', 'Unknown'))
            shift_data[shift]["trips"] += safe_int(r.get('No_Of_trips'))
            shift_data[shift]["qty"] += safe_float(r.get('Qty'))

        total_qty = sum(d["qty"] for d in shift_data.values())
        total_trips = sum(d["trips"] for d in shift_data.values())

        # Build table rows
        rows = []
        for shift in ['A', 'B', 'C']:
            if shift in shift_data:
                pct = (shift_data[shift]["qty"] / total_qty * 100) if total_qty > 0 else 0
                rows.append({
                    "shift": shift,
                    "badge_class": get_shift_badge_class(shift),
                    "trips": shift_data[shift]["trips"],
                    "qty": round(shift_data[shift]["qty"]),
                    "pct": round(pct, 1),
                })

        # Chart data
        chart_labels = [f"Shift {r['shift']}" for r in rows]
        chart_data = [r['qty'] for r in rows]

        return {
            "rows": rows,
            "total_trips": total_trips,
            "total_qty": round(total_qty),
            "chart": {
                "labels": chart_labels,
                "data": chart_data,
                "colors": ['#48bb78', '#4299e1', '#ed8936'],  # Green, Blue, Orange
            },
        }

    def _build_location_breakdown(self, excavation_td: List[Dict], locations: Dict[int, str]) -> Dict[str, Any]:
        """Build location-wise excavation breakdown for today."""
        location_data = defaultdict(lambda: {"trips": 0, "qty": 0})

        for r in excavation_td:
            loc_id = safe_int(r.get('Loc_Id'))
            loc_name = locations.get(loc_id, f"Location {loc_id}")
            location_data[loc_name]["trips"] += safe_int(r.get('No_Of_trips'))
            location_data[loc_name]["qty"] += safe_float(r.get('Qty'))

        total_qty = sum(d["qty"] for d in location_data.values())
        total_trips = sum(d["trips"] for d in location_data.values())

        # Build table rows sorted by qty descending
        rows = []
        for loc_name, data in sorted(location_data.items(), key=lambda x: x[1]["qty"], reverse=True):
            pct = (data["qty"] / total_qty * 100) if total_qty > 0 else 0
            rows.append({
                "location": loc_name,
                "trips": data["trips"],
                "qty": round(data["qty"]),
                "pct": round(pct, 1),
            })

        # Chart data (top 5 locations)
        chart_labels = [r['location'] for r in rows[:5]]
        chart_data = [r['qty'] for r in rows[:5]]

        return {
            "rows": rows,
            "total_trips": total_trips,
            "total_qty": round(total_qty),
            "chart": {
                "labels": chart_labels,
                "data": chart_data,
                "colors": ['#667eea', '#48bb78', '#ed8936', '#9f7aea', '#f56565'],
            },
        }

    def _build_agency_performance(self, excavation_td: List[Dict], excavation_mtd: List[Dict],
                                   agencies: Dict[int, str]) -> Dict[str, Any]:
        """Build agency performance for today and MTD."""
        # Today's agency breakdown
        td_agency_data = defaultdict(lambda: {"trips": 0, "qty": 0})
        for r in excavation_td:
            agency_id = safe_int(r.get('Agency'))
            agency_name = agencies.get(agency_id, f"Agency {agency_id}")
            td_agency_data[agency_name]["trips"] += safe_int(r.get('No_Of_trips'))
            td_agency_data[agency_name]["qty"] += safe_float(r.get('Qty'))

        td_total_qty = sum(d["qty"] for d in td_agency_data.values())

        # MTD agency breakdown
        mtd_agency_data = defaultdict(lambda: {"trips": 0, "qty": 0})
        for r in excavation_mtd:
            agency_id = safe_int(r.get('Agency'))
            agency_name = agencies.get(agency_id, f"Agency {agency_id}")
            mtd_agency_data[agency_name]["trips"] += safe_int(r.get('No_Of_trips'))
            mtd_agency_data[agency_name]["qty"] += safe_float(r.get('Qty'))

        mtd_total_qty = sum(d["qty"] for d in mtd_agency_data.values())

        # Build today's rows
        td_rows = []
        for name, data in sorted(td_agency_data.items(), key=lambda x: x[1]["qty"], reverse=True):
            pct = (data["qty"] / td_total_qty * 100) if td_total_qty > 0 else 0
            td_rows.append({
                "agency": name,
                "trips": data["trips"],
                "qty": round(data["qty"]),
                "pct": round(pct, 1),
            })

        # Build MTD rows
        mtd_rows = []
        for name, data in sorted(mtd_agency_data.items(), key=lambda x: x[1]["qty"], reverse=True):
            pct = (data["qty"] / mtd_total_qty * 100) if mtd_total_qty > 0 else 0
            mtd_rows.append({
                "agency": name,
                "trips": data["trips"],
                "qty": round(data["qty"]),
                "pct": round(pct, 1),
            })

        # Chart data for MTD
        chart_labels = [f"{r['agency']} ({r['pct']:.1f}%)" for r in mtd_rows[:5]]
        chart_data = [r['qty'] for r in mtd_rows[:5]]

        # Calculate totals for trips
        td_total_trips = sum(d["trips"] for d in td_agency_data.values())
        mtd_total_trips = sum(d["trips"] for d in mtd_agency_data.values())

        return {
            "today": {
                "rows": td_rows,
                "total_qty": round(td_total_qty),
                "total_trips": td_total_trips,
            },
            "mtd": {
                "rows": mtd_rows,
                "total_qty": round(mtd_total_qty),
                "total_trips": mtd_total_trips,
            },
            "chart": {
                "labels": chart_labels,
                "data": chart_data,
                "colors": ['#667eea', '#48bb78', '#ed8936', '#9f7aea', '#f56565'],
            },
        }

    def _build_sample_analysis(self, samples_td: List[Dict], locations: Dict[int, str]) -> Dict[str, Any]:
        """Build sample analysis section for today."""
        rows = []
        for s in samples_td:
            loc_id = safe_int(s.get('Loc_Id'))
            loc_name = locations.get(loc_id, f"Location {loc_id}")
            cr2o3 = safe_float(s.get('Cr2O3'))
            feo = safe_float(s.get('FeO'))
            ratio = safe_float(s.get('Ratio'))
            grade = classify_grade(cr2o3)

            rows.append({
                "shift": safe_str(s.get('Shift')),
                "shift_badge_class": get_shift_badge_class(safe_str(s.get('Shift'))),
                "location": loc_name,
                "sample_id": safe_str(s.get('SAMPLE_ID')),
                "cr2o3": round(cr2o3, 1),
                "feo": round(feo, 1),
                "ratio": round(ratio, 2),
                "grade": grade,
                "grade_badge_class": get_grade_badge_class(grade),
            })

        # Today's quality summary
        if rows:
            avg_cr2o3 = sum(r['cr2o3'] for r in rows) / len(rows)
            avg_feo = sum(r['feo'] for r in rows) / len(rows)
            avg_ratio = sum(r['ratio'] for r in rows) / len(rows)
            overall_grade = classify_grade(avg_cr2o3)
        else:
            avg_cr2o3 = avg_feo = avg_ratio = 0
            overall_grade = "N/A"

        return {
            "rows": rows,
            "sample_count": len(rows),
            "summary": {
                "avg_cr2o3": round(avg_cr2o3, 1),
                "avg_feo": round(avg_feo, 1),
                "avg_ratio": round(avg_ratio, 2),
                "grade": overall_grade,
            },
        }

    def _build_daily_trend(self, excavation_mtd: List[Dict], selected_date: str = None) -> Dict[str, Any]:
        """Build daily production trend chart data - T-12 to selected date.

        Always shows 13 days ending on selected date. Days with no data show 0.
        """
        # Build lookup of daily data
        daily_data = defaultdict(lambda: {"qty": 0, "trips": 0})

        for r in excavation_mtd:
            prod_date = r.get('Prod_date')
            if prod_date:
                if hasattr(prod_date, 'strftime'):
                    date_key = prod_date.strftime('%Y-%m-%d')
                else:
                    date_key = str(prod_date)
                daily_data[date_key]["qty"] += safe_float(r.get('Qty'))
                daily_data[date_key]["trips"] += safe_int(r.get('No_Of_trips'))

        # Generate fixed 13-day window (T-12 to T)
        if selected_date:
            try:
                end_date = datetime.strptime(selected_date, '%Y-%m-%d')
            except:
                end_date = datetime.now()
        else:
            end_date = datetime.now()

        # Generate 13 days: T-12, T-11, ..., T-1, T
        date_range = []
        for i in range(12, -1, -1):  # 12 down to 0
            d = end_date - timedelta(days=i)
            date_range.append(d.strftime('%Y-%m-%d'))

        # Build labels and data for the fixed window
        labels = []
        production_data = []

        for date_str in date_range:
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                labels.append(dt.strftime('%b %d'))
            except:
                labels.append(date_str)

            # Get data for this date, or 0 if no data
            qty = daily_data[date_str]["qty"] if date_str in daily_data else 0
            production_data.append(round(qty))

        # Calculate average (only from days with actual data)
        days_with_data = [d for d in production_data if d > 0]
        avg_daily = sum(days_with_data) / len(days_with_data) if days_with_data else 0
        total_qty = sum(production_data)

        return {
            "labels": labels,
            "production_data": production_data,
            "average_line": [round(avg_daily)] * len(labels),
            "average_value": round(avg_daily),
            "working_days": len(days_with_data),
            "total_production": round(total_qty),
        }

    def _build_quality_trend(self, samples_mtd: List[Dict], selected_date: str = None) -> Dict[str, Any]:
        """Build quality parameter trend chart data - T-12 to selected date.

        Always shows 13 days ending on selected date. Days with no data show 0.
        """
        # Build lookup of daily quality data
        daily_quality = defaultdict(lambda: {"cr2o3_sum": 0, "ratio_sum": 0, "count": 0})

        for s in samples_mtd:
            prod_date = s.get('Prod_date')
            if prod_date:
                if hasattr(prod_date, 'strftime'):
                    date_key = prod_date.strftime('%Y-%m-%d')
                else:
                    date_key = str(prod_date)
                cr2o3 = safe_float(s.get('Cr2O3'))
                ratio = safe_float(s.get('Ratio'))
                if cr2o3 > 0:
                    daily_quality[date_key]["cr2o3_sum"] += cr2o3
                    daily_quality[date_key]["ratio_sum"] += ratio
                    daily_quality[date_key]["count"] += 1

        # Generate fixed 13-day window (T-12 to T)
        if selected_date:
            try:
                end_date = datetime.strptime(selected_date, '%Y-%m-%d')
            except:
                end_date = datetime.now()
        else:
            end_date = datetime.now()

        # Generate 13 days: T-12, T-11, ..., T-1, T
        date_range = []
        for i in range(12, -1, -1):  # 12 down to 0
            d = end_date - timedelta(days=i)
            date_range.append(d.strftime('%Y-%m-%d'))

        # Build labels and data for the fixed window
        labels = []
        cr2o3_data = []
        ratio_data = []

        for date_str in date_range:
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                labels.append(dt.strftime('%b %d'))
            except:
                labels.append(date_str)

            # Get data for this date, or 0 if no data
            if date_str in daily_quality and daily_quality[date_str]["count"] > 0:
                count = daily_quality[date_str]["count"]
                cr2o3_data.append(round(daily_quality[date_str]["cr2o3_sum"] / count, 1))
                ratio_data.append(round(daily_quality[date_str]["ratio_sum"] / count, 2))
            else:
                cr2o3_data.append(0)
                ratio_data.append(0)

        return {
            "labels": labels,
            "cr2o3_data": cr2o3_data,
            "ratio_data": ratio_data,
        }

    def _build_mtd_location_performance(self, excavation_mtd: List[Dict],
                                         locations: Dict[int, str]) -> Dict[str, Any]:
        """Build MTD location performance table and chart."""
        location_data = defaultdict(lambda: {"trips": 0, "qty": 0})

        for r in excavation_mtd:
            loc_id = safe_int(r.get('Loc_Id'))
            loc_name = locations.get(loc_id, f"Location {loc_id}")
            location_data[loc_name]["trips"] += safe_int(r.get('No_Of_trips'))
            location_data[loc_name]["qty"] += safe_float(r.get('Qty'))

        total_qty = sum(d["qty"] for d in location_data.values())

        # Build rows sorted by qty
        rows = []
        for loc_name, data in sorted(location_data.items(), key=lambda x: x[1]["qty"], reverse=True):
            pct = (data["qty"] / total_qty * 100) if total_qty > 0 else 0
            rows.append({
                "location": loc_name,
                "trips": data["trips"],
                "qty": round(data["qty"]),
                "pct": round(pct, 1),
            })

        # Chart data
        chart_labels = [r['location'] for r in rows[:5]]
        chart_data = [r['qty'] for r in rows[:5]]

        return {
            "rows": rows,
            "total_qty": round(total_qty),
            "chart": {
                "labels": chart_labels,
                "data": chart_data,
            },
        }

    def _build_plan_vs_actual(self, monthly_plan: List[Dict], excavation_mtd: List[Dict],
                               locations: Dict[int, str]) -> Dict[str, Any]:
        """Build monthly plan vs actual progress table.

        IMPORTANT: Since actual excavation data doesn't have grade breakdown,
        we aggregate planned data by location to match. Each location appears
        once with total planned tonnage across all grades.
        """
        # Aggregate actual by location
        actual_by_loc = defaultdict(float)
        for r in excavation_mtd:
            loc_id = safe_int(r.get('Loc_Id'))
            actual_by_loc[loc_id] += safe_float(r.get('Qty'))

        # Aggregate planned by location (summing all grades for ORE mode)
        # Structure: {loc_id: {"planned": total, "grades": ["HG", "MG", "LG"]}}
        planned_by_loc = defaultdict(lambda: {"planned": 0, "grades": []})

        for p in monthly_plan:
            loc_id = safe_int(p.get('Loc_Id'))
            mode = safe_str(p.get('Mode'))
            grade = safe_str(p.get('Grade'))
            planned = safe_float(p.get('Tonnage'))

            # Only include ORE mode
            if mode.upper() != 'ORE':
                continue

            planned_by_loc[loc_id]["planned"] += planned
            if grade and grade != 'undefined' and grade not in planned_by_loc[loc_id]["grades"]:
                planned_by_loc[loc_id]["grades"].append(grade)

        # Build rows - one row per location
        rows = []
        total_planned = 0
        total_actual = 0

        for loc_id, plan_data in sorted(planned_by_loc.items(), key=lambda x: x[1]["planned"], reverse=True):
            loc_name = locations.get(loc_id, f"Location {loc_id}")
            planned = plan_data["planned"]
            grades = plan_data["grades"]

            # Skip locations with no planned tonnage
            if planned <= 0:
                continue

            actual = actual_by_loc.get(loc_id, 0)
            achievement_pct = (actual / planned * 100) if planned > 0 else 0
            remaining = max(0, planned - actual)

            # Status determination
            if achievement_pct >= 80:
                status = "On Track"
                status_class = "success"
            elif achievement_pct > 0:
                status = "Behind Plan"
                status_class = "warning"
            else:
                status = "Not Started"
                status_class = "danger"

            # Format grade display: show all grades or "Mixed" if multiple
            if len(grades) == 1:
                grade_display = grades[0]
                grade_badge_class = get_grade_badge_class(grades[0])
            elif len(grades) > 1:
                # Sort grades: HG, MG, LG
                grade_order = {"HG": 1, "MG": 2, "LG": 3}
                sorted_grades = sorted(grades, key=lambda g: grade_order.get(g, 99))
                grade_display = "/".join(sorted_grades)
                grade_badge_class = "badge-mixed"
            else:
                grade_display = "-"
                grade_badge_class = ""

            rows.append({
                "location": loc_name,
                "grade": grade_display,
                "grade_badge_class": grade_badge_class,
                "planned": round(planned),
                "actual": round(actual),
                "achievement_pct": round(achievement_pct, 1),
                "remaining": round(remaining),
                "status": status,
                "status_class": status_class,
            })

            total_planned += planned
            total_actual += actual

        total_achievement_pct = (total_actual / total_planned * 100) if total_planned > 0 else 0
        total_remaining = max(0, total_planned - total_actual)

        return {
            "rows": rows,
            "totals": {
                "planned": round(total_planned),
                "actual": round(total_actual),
                "achievement_pct": round(total_achievement_pct, 1),
                "remaining": round(total_remaining),
            },
        }

    def _build_plan_vs_actual_from_daily(self, daily_plan_range: List[Dict], excavation_range: List[Dict],
                                          locations: Dict[int, str]) -> Dict[str, Any]:
        """Build plan vs actual progress table using DAILY PLAN data.

        This aggregates the daily excavation plan (mines_daily_excavation_plan) over
        the date range and compares with actual excavation (mines_day_wise_excavation).

        The daily plan has: OB_QTY_Cum, ORE_QTY, HG_QTY, MG_QTY, LG_QTY per location per shift per day.
        We sum OB + ORE across all days/shifts in the range for planned values.

        Actual excavation includes ALL variants (ORE, OVERBURDEN, SILT, etc.) to match other KPIs.
        Variant codes: 1=ORE, 2=ROM, 3=OVERBURDEN, 4=SILT, 5=SLURY
        """
        # Aggregate actual by location - ALL variants
        actual_by_loc = defaultdict(float)
        for r in excavation_range:
            loc_id = safe_int(r.get('Loc_Id'))
            actual_by_loc[loc_id] += safe_float(r.get('Qty'))

        # Aggregate planned by location from daily plan
        # Structure: {loc_id: {"ob": total, "ore": total, "total": ob+ore, "hg": total, "mg": total, "lg": total}}
        planned_by_loc = defaultdict(lambda: {"ob": 0, "ore": 0, "total": 0, "hg": 0, "mg": 0, "lg": 0})

        for p in daily_plan_range:
            loc_id = safe_int(p.get('Loc_Id'))
            ob = safe_float(p.get('OB_QTY_Cum'))
            ore = safe_float(p.get('ORE_QTY'))
            planned_by_loc[loc_id]["ob"] += ob
            planned_by_loc[loc_id]["ore"] += ore
            planned_by_loc[loc_id]["total"] += ob + ore
            planned_by_loc[loc_id]["hg"] += safe_float(p.get('HG_QTY'))
            planned_by_loc[loc_id]["mg"] += safe_float(p.get('MG_QTY'))
            planned_by_loc[loc_id]["lg"] += safe_float(p.get('LG_QTY'))

        # Build rows - one row per location with planned total (OB + ORE) > 0
        rows = []
        total_planned = 0
        total_actual = 0

        for loc_id, plan_data in sorted(planned_by_loc.items(), key=lambda x: x[1]["total"], reverse=True):
            loc_name = locations.get(loc_id, f"Location {loc_id}")
            planned = plan_data["total"]

            # Skip locations with no planned total
            if planned <= 0:
                continue

            actual = actual_by_loc.get(loc_id, 0)
            achievement_pct = (actual / planned * 100) if planned > 0 else 0
            remaining = max(0, planned - actual)

            # Status determination
            if achievement_pct >= 80:
                status = "On Track"
                status_class = "success"
            elif achievement_pct > 0:
                status = "Behind Plan"
                status_class = "warning"
            else:
                status = "Not Started"
                status_class = "danger"

            # Determine grade based on what was planned
            grades = []
            if plan_data["hg"] > 0:
                grades.append("HG")
            if plan_data["mg"] > 0:
                grades.append("MG")
            if plan_data["lg"] > 0:
                grades.append("LG")

            # Format grade display
            if len(grades) == 1:
                grade_display = grades[0]
                grade_badge_class = get_grade_badge_class(grades[0])
            elif len(grades) > 1:
                grade_display = "/".join(grades)
                grade_badge_class = "badge-mixed"
            else:
                grade_display = "-"
                grade_badge_class = ""

            rows.append({
                "location": loc_name,
                "grade": grade_display,
                "grade_badge_class": grade_badge_class,
                "planned": round(planned),
                "actual": round(actual),
                "achievement_pct": round(achievement_pct, 1),
                "remaining": round(remaining),
                "status": status,
                "status_class": status_class,
            })

            total_planned += planned
            total_actual += actual

        total_achievement_pct = (total_actual / total_planned * 100) if total_planned > 0 else 0
        total_remaining = max(0, total_planned - total_actual)

        return {
            "rows": rows,
            "totals": {
                "planned": round(total_planned),
                "actual": round(total_actual),
                "achievement_pct": round(total_achievement_pct, 1),
                "remaining": round(total_remaining),
            },
        }

    def _build_daily_plan_summary(self, daily_plan: List[Dict], excavation_td: List[Dict],
                                   locations: Dict[int, str]) -> Dict[str, Any]:
        """Build daily plan vs actual comparison with grade breakdown.

        Handles string quantities like '146cum', '292 cum' via safe_float().
        """
        # Aggregate planned by location (sum across all shifts for the day)
        planned_by_loc = defaultdict(lambda: {
            "ob_qty": 0, "ore_qty": 0, "hg_qty": 0, "mg_qty": 0, "lg_qty": 0
        })

        for p in daily_plan:
            loc_id = safe_int(p.get('Loc_Id'))
            # OB_QTY_Cum is varchar - may contain "146cum", "292 cum", etc.
            planned_by_loc[loc_id]["ob_qty"] += safe_float(p.get('OB_QTY_Cum'))
            planned_by_loc[loc_id]["ore_qty"] += safe_float(p.get('ORE_QTY'))
            planned_by_loc[loc_id]["hg_qty"] += safe_float(p.get('HG_QTY'))
            planned_by_loc[loc_id]["mg_qty"] += safe_float(p.get('MG_QTY'))
            planned_by_loc[loc_id]["lg_qty"] += safe_float(p.get('LG_QTY'))

        # Aggregate actual by location from today's excavation
        actual_by_loc = defaultdict(float)
        for r in excavation_td:
            loc_id = safe_int(r.get('Loc_Id'))
            actual_by_loc[loc_id] += safe_float(r.get('Qty'))

        # Build rows
        rows = []
        total_ore_planned = 0
        total_actual = 0

        for loc_id, planned in planned_by_loc.items():
            loc_name = locations.get(loc_id, f"Location {loc_id}")
            actual = actual_by_loc.get(loc_id, 0)
            ore_planned = planned["ore_qty"]
            achievement_pct = (actual / ore_planned * 100) if ore_planned > 0 else 0

            rows.append({
                "location": loc_name,
                "ob_planned": round(planned["ob_qty"]),
                "ore_planned": round(ore_planned),
                "hg_planned": round(planned["hg_qty"]),
                "mg_planned": round(planned["mg_qty"]),
                "lg_planned": round(planned["lg_qty"]),
                "actual": round(actual),
                "achievement_pct": round(achievement_pct, 1),
                "variance": round(actual - ore_planned),
            })

            total_ore_planned += ore_planned
            total_actual += actual

        # Sort by actual descending
        rows.sort(key=lambda x: x['actual'], reverse=True)

        total_achievement = (total_actual / total_ore_planned * 100) if total_ore_planned > 0 else 0

        return {
            "rows": rows,
            "has_data": len(rows) > 0,
            "totals": {
                "ore_planned": round(total_ore_planned),
                "actual": round(total_actual),
                "achievement_pct": round(total_achievement, 1),
                "variance": round(total_actual - total_ore_planned),
            }
        }

    def _build_excavation_details(self, excavation_td: List[Dict], locations: Dict[int, str],
                                   variants: Dict[int, str], agencies: Dict[int, str]) -> List[Dict]:
        """Build detailed excavation records table for today."""
        rows = []
        for r in excavation_td:
            shift = safe_str(r.get('Shift'))
            loc_id = safe_int(r.get('Loc_Id'))
            variant_id = safe_int(r.get('Variant'))
            agency_id = safe_int(r.get('Agency'))
            trips = safe_int(r.get('No_Of_trips'))
            qty = safe_float(r.get('Qty'))
            avg_load = qty / trips if trips > 0 else 0

            rows.append({
                "shift": shift,
                "shift_badge_class": get_shift_badge_class(shift),
                "location": locations.get(loc_id, f"Loc {loc_id}"),
                "material": variants.get(variant_id, f"Variant {variant_id}"),
                "agency": agencies.get(agency_id, f"Agency {agency_id}"),
                "trips": trips,
                "qty": round(qty),
                "avg_load": round(avg_load, 2),
            })

        # Sort by shift then qty descending
        rows.sort(key=lambda x: (x['shift'], -x['qty']))
        return rows

    def _build_mtd_quality_stats(self, samples_mtd: List[Dict]) -> Dict[str, Any]:
        """Build MTD quality statistics."""
        if not samples_mtd:
            return {
                "has_data": False,
                "avg_cr2o3": 0,
                "min_cr2o3": 0,
                "max_cr2o3": 0,
                "avg_feo": 0,
                "min_feo": 0,
                "max_feo": 0,
                "avg_ratio": 0,
                "total_samples": 0,
            }

        cr2o3_values = [safe_float(s.get('Cr2O3')) for s in samples_mtd if s.get('Cr2O3')]
        feo_values = [safe_float(s.get('FeO')) for s in samples_mtd if s.get('FeO')]
        ratio_values = [safe_float(s.get('Ratio')) for s in samples_mtd if s.get('Ratio')]

        return {
            "has_data": True,
            "avg_cr2o3": round(sum(cr2o3_values) / len(cr2o3_values), 1) if cr2o3_values else 0,
            "min_cr2o3": round(min(cr2o3_values), 1) if cr2o3_values else 0,
            "max_cr2o3": round(max(cr2o3_values), 1) if cr2o3_values else 0,
            "avg_feo": round(sum(feo_values) / len(feo_values), 1) if feo_values else 0,
            "min_feo": round(min(feo_values), 1) if feo_values else 0,
            "max_feo": round(max(feo_values), 1) if feo_values else 0,
            "avg_ratio": round(sum(ratio_values) / len(ratio_values), 2) if ratio_values else 0,
            "total_samples": len(samples_mtd),
        }

    def _build_gap_analysis(self, monthly_plan: List[Dict], excavation_mtd: List[Dict],
                            days_elapsed: int, days_in_month: int) -> Dict[str, Any]:
        """Build gap analysis metrics for AI insights."""
        # Total planned ORE
        total_planned = sum(safe_float(p.get('Tonnage')) for p in monthly_plan
                           if safe_str(p.get('Mode')).upper() == 'ORE')

        # Total actual
        total_actual = sum(safe_float(r.get('Qty')) for r in excavation_mtd)

        # Working days from data
        working_days = len(set(r.get('Prod_date') for r in excavation_mtd))
        avg_daily = total_actual / working_days if working_days > 0 else 0

        # Days remaining
        days_remaining = days_in_month - days_elapsed

        # Required daily production to achieve target
        remaining_target = max(0, total_planned - total_actual)
        required_daily = remaining_target / days_remaining if days_remaining > 0 else 0

        # Increase needed percentage
        increase_needed_pct = ((required_daily - avg_daily) / avg_daily * 100) if avg_daily > 0 else 0

        # Expected month-end at current pace
        expected_month_end = avg_daily * days_in_month
        expected_achievement_pct = (expected_month_end / total_planned * 100) if total_planned > 0 else 0

        return {
            "total_planned": round(total_planned),
            "total_actual": round(total_actual),
            "achievement_pct": round((total_actual / total_planned * 100) if total_planned > 0 else 0, 1),
            "remaining_target": round(remaining_target),
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "working_days": working_days,
            "avg_daily_production": round(avg_daily),
            "required_daily_production": round(required_daily),
            "increase_needed_pct": round(increase_needed_pct, 1),
            "expected_month_end": round(expected_month_end),
            "expected_achievement_pct": round(expected_achievement_pct, 1),
        }

    def _build_gap_analysis_range(self, monthly_plan: List[Dict], excavation_range: List[Dict],
                                   days_in_range: int) -> Dict[str, Any]:
        """Build gap analysis metrics for date range mode.

        For date ranges, we compare actual production against monthly plan targets.
        """
        # Total planned ORE from monthly plan
        total_planned = sum(safe_float(p.get('Tonnage')) for p in monthly_plan
                           if safe_str(p.get('Mode')).upper() == 'ORE')

        # Total actual in range
        total_actual = sum(safe_float(r.get('Qty')) for r in excavation_range)

        # Working days from data
        working_days = len(set(r.get('Prod_date') for r in excavation_range if r.get('Prod_date')))
        avg_daily = total_actual / working_days if working_days > 0 else 0

        # Achievement against monthly plan
        achievement_pct = (total_actual / total_planned * 100) if total_planned > 0 else 0

        # Remaining to achieve monthly target
        remaining_target = max(0, total_planned - total_actual)

        # Estimate days remaining in month (approximate)
        days_in_month = 30  # Approximate
        days_remaining = max(0, days_in_month - working_days)

        # Required daily to complete monthly target
        required_daily = remaining_target / days_remaining if days_remaining > 0 else 0

        # Increase needed percentage
        increase_needed_pct = ((required_daily - avg_daily) / avg_daily * 100) if avg_daily > 0 else 0

        # Expected month-end at current pace
        expected_month_end = avg_daily * days_in_month
        expected_achievement_pct = (expected_month_end / total_planned * 100) if total_planned > 0 else 0

        return {
            "total_planned": round(total_planned),
            "total_actual": round(total_actual),
            "achievement_pct": round(achievement_pct, 1),
            "remaining_target": round(remaining_target),
            "days_elapsed": working_days,
            "days_remaining": days_remaining,
            "days_in_range": days_in_range,
            "working_days": working_days,
            "avg_daily_production": round(avg_daily),
            "required_daily_production": round(required_daily),
            "increase_needed_pct": round(increase_needed_pct, 1),
            "expected_month_end": round(expected_month_end),
            "expected_achievement_pct": round(expected_achievement_pct, 1),
            "is_range_mode": True,
        }

    def _check_has_data(self, analysis_data: Dict) -> bool:
        """Check if we have meaningful data."""
        td_qty = analysis_data.get('today_kpis', {}).get('excavation', {}).get('value', 0)
        mtd_qty = analysis_data.get('mtd_kpis', {}).get('total_excavation', {}).get('value', 0)
        return td_qty > 0 or mtd_qty > 0

    # ========================================================================
    # NEW RANGE-SPECIFIC HELPER METHODS
    # ========================================================================

    def _build_period_kpis(self, excavation_range: List[Dict], samples_range: List[Dict]) -> Dict[str, Any]:
        """Build PERIOD KPIs (aggregated across entire date range).

        Material Types (Variant_Id):
        - 1 = ORE (HG/MG/LG/LUMP)
        - 3 = OVERBURDEN (OB)
        - 4 = SILT
        """
        # Excavation totals
        total_qty = sum(safe_float(r.get('Qty')) for r in excavation_range)
        total_trips = sum(safe_int(r.get('No_Of_trips')) for r in excavation_range)
        total_avg_load = total_qty / total_trips if total_trips > 0 else 0

        # Material type breakdown (Variant: 1=ORE, 3=OB, 4=SILT)
        ore_qty = sum(safe_float(r.get('Qty')) for r in excavation_range if safe_int(r.get('Variant')) == 1)
        ob_qty = sum(safe_float(r.get('Qty')) for r in excavation_range if safe_int(r.get('Variant')) == 3)
        silt_qty = sum(safe_float(r.get('Qty')) for r in excavation_range if safe_int(r.get('Variant')) == 4)

        # Working days (unique dates in data)
        working_days = len(set(r.get('Prod_date') for r in excavation_range if r.get('Prod_date')))
        avg_daily_production = total_qty / working_days if working_days > 0 else 0

        # Active locations
        active_locations = len(set(r.get('Loc_Id') for r in excavation_range if r.get('Loc_Id')))

        # Quality metrics (averaged across all samples)
        cr2o3_values = [safe_float(r.get('Cr2O3')) for r in samples_range if r.get('Cr2O3')]
        feo_values = [safe_float(r.get('FeO')) for r in samples_range if r.get('FeO')]
        ratio_values = [safe_float(r.get('Ratio')) for r in samples_range if r.get('Ratio')]

        avg_cr2o3 = sum(cr2o3_values) / len(cr2o3_values) if cr2o3_values else 0
        avg_feo = sum(feo_values) / len(feo_values) if feo_values else 0
        avg_ratio = sum(ratio_values) / len(ratio_values) if ratio_values else 0

        # Grade classification
        grade_class = classify_grade(avg_cr2o3) if avg_cr2o3 > 0 else "N/A"

        return {
            "excavation": {
                "value": total_qty,
                "formatted": format_number(total_qty),
                "unit": "MT",
            },
            "ore_qty": {
                "value": ore_qty,
                "formatted": format_number(ore_qty),
                "unit": "MT",
            },
            "ob_qty": {
                "value": ob_qty,
                "formatted": format_number(ob_qty),
                "unit": "MT",
            },
            "silt_qty": {
                "value": silt_qty,
                "formatted": format_number(silt_qty),
                "unit": "MT",
            },
            "trips": {
                "value": total_trips,
                "formatted": format_number(total_trips),
            },
            "avg_load": {
                "value": round(total_avg_load, 2),
                "formatted": f"{total_avg_load:.2f}",
                "unit": "MT/trip",
            },
            "working_days": {
                "value": working_days,
                "formatted": str(working_days),
            },
            "avg_daily_production": {
                "value": round(avg_daily_production),
                "formatted": format_number(avg_daily_production),
                "unit": "MT",
            },
            "avg_cr2o3": {
                "value": round(avg_cr2o3, 1),
                "formatted": f"{avg_cr2o3:.1f}%",
            },
            "avg_feo": {
                "value": round(avg_feo, 1),
                "formatted": f"{avg_feo:.1f}%",
            },
            "avg_ratio": {
                "value": round(avg_ratio, 2),
                "formatted": f"{avg_ratio:.2f}",
            },
            "active_locations": {
                "value": active_locations,
                "formatted": str(active_locations),
            },
            "grade_classification": grade_class,
            "samples_total": {
                "value": len(samples_range),
                "formatted": str(len(samples_range)),
            },
        }

    def _build_shift_breakdown_range(self, excavation_range: List[Dict], locations: Dict[int, str]) -> Dict[str, Any]:
        """Build shift-wise production breakdown aggregated across entire range."""
        shift_data = defaultdict(lambda: {"trips": 0, "qty": 0})

        for r in excavation_range:
            shift = safe_str(r.get('Shift', 'Unknown'))
            shift_data[shift]["trips"] += safe_int(r.get('No_Of_trips'))
            shift_data[shift]["qty"] += safe_float(r.get('Qty'))

        total_qty = sum(d["qty"] for d in shift_data.values())
        total_trips = sum(d["trips"] for d in shift_data.values())

        # Build table rows
        rows = []
        for shift in ['A', 'B', 'C']:
            if shift in shift_data:
                pct = (shift_data[shift]["qty"] / total_qty * 100) if total_qty > 0 else 0
                rows.append({
                    "shift": shift,
                    "badge_class": get_shift_badge_class(shift),
                    "trips": shift_data[shift]["trips"],
                    "qty": round(shift_data[shift]["qty"]),
                    "pct": round(pct, 1),
                })

        # Chart data
        chart_labels = [f"Shift {r['shift']}" for r in rows]
        chart_data = [r['qty'] for r in rows]

        return {
            "rows": rows,
            "total_trips": total_trips,
            "total_qty": round(total_qty),
            "chart": {
                "labels": chart_labels,
                "data": chart_data,
                "colors": ['#48bb78', '#4299e1', '#ed8936'],
            },
        }

    def _build_agency_performance_range(self, excavation_range: List[Dict], agencies: Dict[int, str]) -> Dict[str, Any]:
        """Build agency performance aggregated across entire range."""
        agency_data = defaultdict(lambda: {"trips": 0, "qty": 0})

        for r in excavation_range:
            agency_id = safe_int(r.get('Agency'))
            agency_name = agencies.get(agency_id, f"Agency {agency_id}")
            agency_data[agency_name]["trips"] += safe_int(r.get('No_Of_trips'))
            agency_data[agency_name]["qty"] += safe_float(r.get('Qty'))

        total_qty = sum(d["qty"] for d in agency_data.values())

        # Build rows
        rows = []
        for name, data in sorted(agency_data.items(), key=lambda x: x[1]["qty"], reverse=True):
            pct = (data["qty"] / total_qty * 100) if total_qty > 0 else 0
            rows.append({
                "agency": name,
                "trips": data["trips"],
                "qty": round(data["qty"]),
                "pct": round(pct, 1),
            })

        # Chart data
        chart_labels = [f"{r['agency']} ({r['pct']:.1f}%)" for r in rows[:5]]
        chart_data = [r['qty'] for r in rows[:5]]

        return {
            "rows": rows,
            "total_qty": round(total_qty),
            "total_trips": sum(d["trips"] for d in agency_data.values()),
            "chart": {
                "labels": chart_labels,
                "data": chart_data,
                "colors": ['#667eea', '#48bb78', '#ed8936', '#9f7aea', '#f56565'],
            },
        }

    def _build_daily_trend_range(self, excavation_range: List[Dict], start_date: str, end_date: str) -> Dict[str, Any]:
        """Build daily production trend for the specified date range."""
        # Build lookup of daily data
        daily_data = defaultdict(lambda: {"qty": 0, "trips": 0})

        for r in excavation_range:
            prod_date = r.get('Prod_date')
            if prod_date:
                if hasattr(prod_date, 'strftime'):
                    date_key = prod_date.strftime('%Y-%m-%d')
                else:
                    date_key = str(prod_date)
                daily_data[date_key]["qty"] += safe_float(r.get('Qty'))
                daily_data[date_key]["trips"] += safe_int(r.get('No_Of_trips'))

        # Generate all days in range
        start_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_obj = datetime.strptime(end_date, '%Y-%m-%d')

        date_range = []
        current = start_obj
        while current <= end_obj:
            date_range.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)

        # Build labels and data
        labels = []
        production_data = []

        for date_str in date_range:
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                labels.append(dt.strftime('%b %d'))
            except:
                labels.append(date_str)

            qty = daily_data[date_str]["qty"] if date_str in daily_data else 0
            production_data.append(round(qty))

        # Calculate average
        days_with_data = [d for d in production_data if d > 0]
        avg_daily = sum(days_with_data) / len(days_with_data) if days_with_data else 0
        total_qty = sum(production_data)

        return {
            "labels": labels,
            "production_data": production_data,
            "average_line": [round(avg_daily)] * len(labels),
            "average_value": round(avg_daily),
            "working_days": len(days_with_data),
            "total_production": round(total_qty),
        }

    def _build_quality_trend_range(self, samples_range: List[Dict], start_date: str, end_date: str) -> Dict[str, Any]:
        """Build quality parameter trend for the specified date range."""
        # Build lookup of daily quality data
        daily_quality = defaultdict(lambda: {"cr2o3_sum": 0, "ratio_sum": 0, "count": 0})

        for s in samples_range:
            prod_date = s.get('Prod_date')
            if prod_date:
                if hasattr(prod_date, 'strftime'):
                    date_key = prod_date.strftime('%Y-%m-%d')
                else:
                    date_key = str(prod_date)
                cr2o3 = safe_float(s.get('Cr2O3'))
                ratio = safe_float(s.get('Ratio'))
                if cr2o3 > 0:
                    daily_quality[date_key]["cr2o3_sum"] += cr2o3
                    daily_quality[date_key]["ratio_sum"] += ratio
                    daily_quality[date_key]["count"] += 1

        # Generate all days in range
        start_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_obj = datetime.strptime(end_date, '%Y-%m-%d')

        date_range = []
        current = start_obj
        while current <= end_obj:
            date_range.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)

        # Build labels and data
        labels = []
        cr2o3_data = []
        ratio_data = []

        for date_str in date_range:
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                labels.append(dt.strftime('%b %d'))
            except:
                labels.append(date_str)

            if date_str in daily_quality and daily_quality[date_str]["count"] > 0:
                count = daily_quality[date_str]["count"]
                cr2o3_data.append(round(daily_quality[date_str]["cr2o3_sum"] / count, 1))
                ratio_data.append(round(daily_quality[date_str]["ratio_sum"] / count, 2))
            else:
                cr2o3_data.append(0)
                ratio_data.append(0)

        return {
            "labels": labels,
            "cr2o3_data": cr2o3_data,
            "ratio_data": ratio_data,
        }

    def _build_daily_breakdown(self, excavation_range: List[Dict], samples_range: List[Dict],
                               start_date: str, end_date: str) -> List[Dict]:
        """Build day-by-day breakdown for the range."""
        # Build lookup by date
        daily_excavation = defaultdict(lambda: {"qty": 0, "trips": 0})
        daily_samples = defaultdict(lambda: {"cr2o3_sum": 0, "count": 0})

        for r in excavation_range:
            prod_date = r.get('Prod_date')
            if prod_date:
                if hasattr(prod_date, 'strftime'):
                    date_key = prod_date.strftime('%Y-%m-%d')
                else:
                    date_key = str(prod_date)
                daily_excavation[date_key]["qty"] += safe_float(r.get('Qty'))
                daily_excavation[date_key]["trips"] += safe_int(r.get('No_Of_trips'))

        for s in samples_range:
            prod_date = s.get('Prod_date')
            if prod_date:
                if hasattr(prod_date, 'strftime'):
                    date_key = prod_date.strftime('%Y-%m-%d')
                else:
                    date_key = str(prod_date)
                cr2o3 = safe_float(s.get('Cr2O3'))
                if cr2o3 > 0:
                    daily_samples[date_key]["cr2o3_sum"] += cr2o3
                    daily_samples[date_key]["count"] += 1

        # Generate all days in range
        start_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_obj = datetime.strptime(end_date, '%Y-%m-%d')

        breakdown = []
        current = start_obj
        while current <= end_obj:
            date_str = current.strftime('%Y-%m-%d')
            date_formatted = current.strftime('%b %d, %Y')

            exc_data = daily_excavation[date_str]
            samp_data = daily_samples[date_str]

            avg_cr2o3 = (samp_data["cr2o3_sum"] / samp_data["count"]) if samp_data["count"] > 0 else 0

            breakdown.append({
                "date": date_str,
                "date_formatted": date_formatted,
                "excavation": round(exc_data["qty"]),
                "trips": exc_data["trips"],
                "avg_cr2o3": round(avg_cr2o3, 1),
                "samples": samp_data["count"],
            })

            current += timedelta(days=1)

        return breakdown

    def _build_shift_plan_vs_actual(self, daily_plan: List[Dict], excavation_td: List[Dict]) -> Dict[str, Any]:
        """Build shift-wise Plan vs Actual comparison.

        Uses mines_daily_excavation_plan (planned) and mines_day_wise_excavation (actual).
        The daily plan has OB_QTY_Cum, ORE_QTY, HG_QTY, MG_QTY, LG_QTY per shift.
        We sum ORE_QTY + OB_QTY_Cum for total planned per shift.
        Actual comes from mines_day_wise_excavation Qty field.
        """
        # Aggregate planned by shift
        planned_by_shift = defaultdict(lambda: {"ob": 0, "ore": 0, "total": 0})
        for p in daily_plan:
            shift = safe_str(p.get('Shift', 'Unknown')).upper()
            if shift in ['A', 'B', 'C']:
                ob = safe_float(p.get('OB_QTY_Cum'))  # Handles "146cum" format
                ore = safe_float(p.get('ORE_QTY'))
                planned_by_shift[shift]["ob"] += ob
                planned_by_shift[shift]["ore"] += ore
                planned_by_shift[shift]["total"] += ob + ore

        # Aggregate actual by shift
        actual_by_shift = defaultdict(float)
        for r in excavation_td:
            shift = safe_str(r.get('Shift', 'Unknown')).upper()
            if shift in ['A', 'B', 'C']:
                actual_by_shift[shift] += safe_float(r.get('Qty'))

        # Build rows
        rows = []
        total_planned = 0
        total_actual = 0

        for shift in ['A', 'B', 'C']:
            planned = round(planned_by_shift[shift]["total"])
            actual = round(actual_by_shift.get(shift, 0))
            variance = actual - planned
            achievement_pct = (actual / planned * 100) if planned > 0 else 0

            total_planned += planned
            total_actual += actual

            rows.append({
                "shift": shift,
                "badge_class": get_shift_badge_class(shift),
                "planned": planned,
                "actual": actual,
                "achievement_pct": round(achievement_pct, 1),
                "variance": variance,
                "variance_class": "text-success" if variance >= 0 else "text-danger",
                "variance_formatted": f"+{variance}" if variance >= 0 else str(variance),
            })

        # Total row
        total_achievement = (total_actual / total_planned * 100) if total_planned > 0 else 0
        total_variance = total_actual - total_planned

        # Chart data for donut
        chart_labels = [f"Shift {r['shift']}" for r in rows]
        chart_data = [r['actual'] for r in rows]

        return {
            "rows": rows,
            "total_planned": total_planned,
            "total_actual": total_actual,
            "total_achievement_pct": round(total_achievement, 1),
            "total_variance": total_variance,
            "total_variance_class": "text-success" if total_variance >= 0 else "text-danger",
            "total_variance_formatted": f"+{total_variance}" if total_variance >= 0 else str(total_variance),
            "chart": {
                "labels": chart_labels,
                "data": chart_data,
                "colors": ['#48bb78', '#4299e1', '#ed8936'],  # Green, Blue, Orange
            },
            "has_plan_data": total_planned > 0,
        }

    def _build_shift_plan_vs_actual_range(self, daily_plan_range: List[Dict], excavation_range: List[Dict]) -> Dict[str, Any]:
        """Build shift-wise Plan vs Actual comparison for a date range.

        Aggregates data across all days in the range.
        """
        # Aggregate planned by shift
        planned_by_shift = defaultdict(lambda: {"ob": 0, "ore": 0, "total": 0})
        for p in daily_plan_range:
            shift = safe_str(p.get('Shift', 'Unknown')).upper()
            if shift in ['A', 'B', 'C']:
                ob = safe_float(p.get('OB_QTY_Cum'))
                ore = safe_float(p.get('ORE_QTY'))
                planned_by_shift[shift]["ob"] += ob
                planned_by_shift[shift]["ore"] += ore
                planned_by_shift[shift]["total"] += ob + ore

        # Aggregate actual by shift - ALL variants
        actual_by_shift = defaultdict(float)
        for r in excavation_range:
            shift = safe_str(r.get('Shift', 'Unknown')).upper()
            if shift in ['A', 'B', 'C']:
                actual_by_shift[shift] += safe_float(r.get('Qty'))

        # Build rows
        rows = []
        total_planned = 0
        total_actual = 0

        for shift in ['A', 'B', 'C']:
            planned = round(planned_by_shift[shift]["total"])
            actual = round(actual_by_shift.get(shift, 0))
            variance = actual - planned
            achievement_pct = (actual / planned * 100) if planned > 0 else 0

            total_planned += planned
            total_actual += actual

            rows.append({
                "shift": shift,
                "badge_class": get_shift_badge_class(shift),
                "planned": planned,
                "actual": actual,
                "achievement_pct": round(achievement_pct, 1),
                "variance": variance,
                "variance_class": "text-success" if variance >= 0 else "text-danger",
                "variance_formatted": f"+{variance}" if variance >= 0 else str(variance),
            })

        # Total row
        total_achievement = (total_actual / total_planned * 100) if total_planned > 0 else 0
        total_variance = total_actual - total_planned

        # Chart data for donut
        chart_labels = [f"Shift {r['shift']}" for r in rows]
        chart_data = [r['actual'] for r in rows]

        return {
            "rows": rows,
            "total_planned": total_planned,
            "total_actual": total_actual,
            "total_achievement_pct": round(total_achievement, 1),
            "total_variance": total_variance,
            "total_variance_class": "text-success" if total_variance >= 0 else "text-danger",
            "total_variance_formatted": f"+{total_variance}" if total_variance >= 0 else str(total_variance),
            "chart": {
                "labels": chart_labels,
                "data": chart_data,
                "colors": ['#48bb78', '#4299e1', '#ed8936'],
            },
            "has_plan_data": total_planned > 0,
        }


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def process_geology_survey_data(mcp_client, date: str) -> Dict[str, Any]:
    """
    Convenience function to process Geology & Survey data for a date.

    Args:
        mcp_client: MCP client instance
        date: Date string (YYYY-MM-DD)

    Returns:
        Analysis data dictionary
    """
    processor = GeologySurveyDataProcessor(mcp_client)
    return processor.process_date(date)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['GeologySurveyDataProcessor', 'process_geology_survey_data']


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test with mock data"""
    print("Geology Survey Formatter module loaded successfully")
    print("Use GeologySurveyDataProcessor(mcp_client).process_date('YYYY-MM-DD') to process data")
    print("\nExpected output structure:")
    print("- date, date_formatted, day, month, year")
    print("- today_kpis: excavation, trips, avg_load, avg_cr2o3, avg_ratio, active_locations")
    print("- mtd_kpis: total_excavation, total_trips, working_days, avg_daily_production, avg_cr2o3, samples_analyzed")
    print("- shift_breakdown: rows[], chart{}")
    print("- location_breakdown: rows[], chart{}")
    print("- agency_performance: today{}, mtd{}, chart{}")
    print("- sample_analysis: rows[], summary{}")
    print("- daily_trend: labels[], production_data[], average_line[]")
    print("- quality_trend: labels[], cr2o3_data[], ratio_data[]")
    print("- mtd_location_performance: rows[], chart{}")
    print("- plan_vs_actual: rows[], totals{}")
    print("- excavation_details: list of detail rows")
    print("- mtd_quality_stats: avg/min/max for cr2o3, feo, ratio")
    print("- gap_analysis: planned, actual, required_daily, increase_needed_pct")