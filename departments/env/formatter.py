"""
ENV Formatter
=============
Data processor for Environment Department Dashboard.

This processor queries 14 normalized tables:
1. kpi_env_food_waste_data - Daily food waste by location
2. kpi_env_stp_water_data - STP water treatment readings
3. env_cbam - CBAM emissions (daily SEE_DIRECT, SEE_INDIRECT, SEE_TOTAL)
4. kpi_env_compliance - License/clearance status
5. kpi_env_compliance_return - Regulatory return filings
6. kpi_env_slag_gcp_dust_data - Industrial waste (monthly)
7. kpi_env_biomedical_waste_data - Biomedical waste tracking
8. kpi_env_incident_report - Environmental incidents
9. kpi_env_monitoring_report - Air quality monitoring (monthly)
10. kpi_env_training_records - ESG/Environment training
11. kpi_env_water_consumption_data - Borewell consumption
12. kpi_env_horticulture_plantation - Plantation tracking
13. kpi_env_used_oil_data - Used oil management
14. kpi_env_observation_report - Environmental observations

Author: BAL-Agentic-Backend Team
Date: December 2025
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
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
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
}

MONTH_TO_NUM = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12
}

DAY_NAMES = {
    0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday",
    4: "Friday", 5: "Saturday", 6: "Sunday"
}

# Air quality limits (NAAQS standards)
AIR_QUALITY_LIMITS = {
    "PM10": 100,    # µg/m³
    "PM2.5": 60,    # µg/m³
    "SO2": 80,      # µg/m³
    "NO2": 80,      # µg/m³
    "CO": 4000,     # µg/m³
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert value to float, handling NULL/None/Decimal gracefully."""
    if value is None:
        return default
    try:
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Convert value to int safely."""
    if value is None:
        return default
    try:
        return int(float(value))
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


def get_financial_year(date_obj: datetime) -> str:
    """Get financial year string like '2025-26' from date."""
    if date_obj.month >= 4:
        return f"{date_obj.year}-{str(date_obj.year + 1)[2:]}"
    else:
        return f"{date_obj.year - 1}-{str(date_obj.year)[2:]}"


def calculate_trend_pct(current: float, previous: float) -> Tuple[float, str]:
    """Calculate trend percentage and direction."""
    if previous == 0:
        return 0.0, "stable"

    pct = ((current - previous) / previous) * 100

    if pct > 1:
        return round(pct, 1), "up"
    elif pct < -1:
        return round(abs(pct), 1), "down"
    else:
        return 0.0, "stable"


def get_license_status(valid_upto: Any, today: datetime) -> Tuple[str, str]:
    """
    Determine license status based on validity date.

    Returns:
        Tuple of (status_class, status_text)
    """
    if valid_upto is None:
        return "status-na", "Perpetual"

    try:
        if isinstance(valid_upto, str):
            valid_date = datetime.strptime(valid_upto, '%Y-%m-%d')
        else:
            valid_date = valid_upto

        days_remaining = (valid_date - today).days

        if days_remaining < 0:
            return "status-expired", f"Expired {abs(days_remaining)} days ago"
        elif days_remaining <= 90:
            return "status-expiring", f"Expires in {days_remaining} days"
        else:
            return "status-valid", f"Valid till {valid_date.strftime('%b %Y')}"
    except Exception:
        return "status-na", "N/A"


# ============================================================================
# ENV DATA PROCESSOR CLASS
# ============================================================================

class ENVDataProcessor:
    """
    Process Environment Department data for dashboard generation.
    """

    def __init__(self, mcp_client):
        """
        Initialize with MCP client for database queries.

        Args:
            mcp_client: MCP client instance with query() method
        """
        self.mcp = mcp_client
        self.database = "balcorpdb"
        logger.info("ENV Data Processor initialized")

    def process_date(self, date: str) -> Dict[str, Any]:
        """
        Main entry point: Process all ENV data for a specific date.

        Args:
            date: Date string in YYYY-MM-DD format

        Returns:
            Dictionary matching template's analysisData structure
        """
        logger.info(f"Processing ENV data for date: {date}")

        # Parse date
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        month_start = date_obj.replace(day=1).strftime('%Y-%m-%d')
        month_name = MONTH_NAMES[date_obj.month]
        month_abbrev = MONTH_ABBREV[date_obj.month]
        day_name = DAY_NAMES[date_obj.weekday()]
        financial_year = get_financial_year(date_obj)

        # ====================================================================
        # QUERY ALL DATA SOURCES
        # ====================================================================

        # Daily data (TD = Today)
        food_waste_td = self._query_food_waste(date, date)
        stp_water_td = self._query_stp_water(date, date)
        incidents_td = self._query_incidents(date, date)
        biomedical_td = self._query_biomedical_waste(date, date)

        # Monthly data (MTD = Month-to-Date)
        food_waste_mtd = self._query_food_waste(month_start, date)
        stp_water_mtd = self._query_stp_water(month_start, date)

        # Period/Static data
        cbam_data = self._query_cbam_emissions(month_start, date)
        compliance_licenses = self._query_compliance_licenses()
        compliance_returns = self._query_compliance_returns()
        slag_gcp_data = self._query_slag_gcp(financial_year, month_abbrev)
        air_quality_data = self._query_air_quality(date_obj.year, month_abbrev)
        training_data = self._query_training_records(date_obj.year)

        # Data gap detection
        biomedical_last_entry = self._get_last_biomedical_entry()

        # ====================================================================
        # BUILD ANALYSIS DATA STRUCTURE
        # ====================================================================

        # Calculate previous month for Air Quality display
        if date_obj.month == 1:
            prev_month_num = 12
            prev_year = date_obj.year - 1
        else:
            prev_month_num = date_obj.month - 1
            prev_year = date_obj.year
        prev_month_name = MONTH_NAMES[prev_month_num]
        prev_month_abbrev = MONTH_ABBREV[prev_month_num]

        analysis_data = {
            # Metadata
            "date": date,
            "date_formatted": f"{month_name} {date_obj.day}, {date_obj.year}",
            "day": date_obj.day,
            "month": month_name,
            "month_abbrev": month_abbrev,
            "year": date_obj.year,
            "day_name": day_name,
            "financial_year": financial_year,
            "prev_month": prev_month_name,
            "prev_month_abbrev": prev_month_abbrev,
            "prev_year": prev_year,

            # Executive Summary (6 cards)
            "executive_summary": self._build_executive_summary(
                food_waste_td, stp_water_td, incidents_td,
                compliance_returns, cbam_data, date_obj
            ),

            # Data Gap Alert
            "data_gaps": self._build_data_gaps(biomedical_last_entry, date_obj),

            # Food Waste Section
            "food_waste": self._build_food_waste_section(
                food_waste_td, food_waste_mtd, date_obj
            ),

            # STP Water Section
            "stp_water": self._build_stp_water_section(
                stp_water_td, stp_water_mtd, date_obj
            ),

            # CBAM Emissions Section
            "cbam_emissions": self._build_cbam_section(cbam_data, date_obj),

            # License Status Section
            "licenses": self._build_licenses_section(compliance_licenses, date_obj),

            # Air Quality Section
            "air_quality": self._build_air_quality_section(air_quality_data),

            # Industrial Waste Section
            "industrial_waste": self._build_industrial_waste_section(slag_gcp_data),

            # Compliance Returns Section
            "compliance_returns": self._build_compliance_returns_section(compliance_returns),

            # Training Section (for AI insights)
            "training": self._build_training_section(training_data),

            # Incidents (for AI insights)
            "incidents": self._build_incidents_section(incidents_td),

            # Biomedical waste (for AI insights)
            "biomedical_waste": self._build_biomedical_section(biomedical_td, biomedical_last_entry),
        }

        # Check if we have any data
        has_data = self._check_has_data(analysis_data)
        analysis_data["has_data"] = has_data

        logger.info(f"ENV data processing complete. Has data: {has_data}")
        return analysis_data

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def _query_food_waste(self, start_date: str, end_date: str) -> List[Dict]:
        """Query kpi_env_food_waste_data for date range."""
        query = f"""
            SELECT
                DATE, PLANT, LOCATION, WASTE_KG,
                PERSONS_COUNT, WASTE_PER_PERSON_GM
            FROM kpi_env_food_waste_data
            WHERE DATE >= '{start_date}' AND DATE <= '{end_date}'
            ORDER BY DATE, LOCATION
        """
        try:
            result = self.mcp.query(database=self.database, sql=query)
            if result.get("success"):
                logger.info(f"Retrieved {len(result['data'])} food waste records")
                return result["data"]
            else:
                logger.error(f"Food waste query failed: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error querying food waste: {e}", exc_info=True)
            return []

    def _query_stp_water(self, start_date: str, end_date: str) -> List[Dict]:
        """Query kpi_env_stp_water_data for date range."""
        query = f"""
            SELECT
                DATE, PLANT, INITIAL_READING, FINAL_READING, DIFFERENCE
            FROM kpi_env_stp_water_data
            WHERE DATE >= '{start_date}' AND DATE <= '{end_date}'
            ORDER BY DATE
        """
        try:
            result = self.mcp.query(database=self.database, sql=query)
            if result.get("success"):
                logger.info(f"Retrieved {len(result['data'])} STP water records")
                return result["data"]
            else:
                logger.error(f"STP water query failed: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error querying STP water: {e}", exc_info=True)
            return []

    def _query_cbam_emissions(self, start_date: str, end_date: str) -> List[Dict]:
        """Query env_cbam for CBAM emissions data (date-wise).

        New table: balcorpdb.env_cbam with daily POSTING_DATE and SEE_* fields.
        """
        query = f"""
            SELECT
                POSTING_DATE, SEE_DIRECT, SEE_INDIRECT, SEE_TOTAL
            FROM env_cbam
            WHERE POSTING_DATE >= '{start_date}' AND POSTING_DATE <= '{end_date}'
            ORDER BY POSTING_DATE
        """
        try:
            result = self.mcp.query(database=self.database, sql=query)
            if result.get("success"):
                logger.info(f"Retrieved {len(result['data'])} CBAM records from env_cbam")
                return result["data"]
            else:
                logger.error(f"CBAM query failed: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error querying CBAM: {e}", exc_info=True)
            return []

    def _query_compliance_licenses(self) -> List[Dict]:
        """Query kpi_env_compliance for license status."""
        query = """
            SELECT
                SL_NO, LOCATION, CLEARANCE_TYPE, LICENSE_NO,
                DESCRIPTION, LICENSING_AUTHORITY, VALID_UPTO,
                RENEWAL_DATE, PAYMENT_DUE, REMARKS
            FROM kpi_env_compliance
            ORDER BY LOCATION, CLEARANCE_TYPE
        """
        try:
            result = self.mcp.query(database=self.database, sql=query)
            if result.get("success"):
                logger.info(f"Retrieved {len(result['data'])} compliance license records")
                return result["data"]
            else:
                logger.error(f"Compliance licenses query failed: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error querying compliance licenses: {e}", exc_info=True)
            return []

    def _query_compliance_returns(self) -> List[Dict]:
        """Query kpi_env_compliance_return for regulatory returns."""
        query = """
            SELECT
                SL_NO, AREA, SUBJECT, ACT_RULE, FORMAT,
                SUBMISSION_PERIOD, SUBMISSION_DATE, COMPLIANCE_STATUS,
                COMPLIANCE_AUTHORITY, REMARKS
            FROM kpi_env_compliance_return
            ORDER BY AREA, SUBJECT
        """
        try:
            result = self.mcp.query(database=self.database, sql=query)
            if result.get("success"):
                logger.info(f"Retrieved {len(result['data'])} compliance return records")
                return result["data"]
            else:
                logger.error(f"Compliance returns query failed: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error querying compliance returns: {e}", exc_info=True)
            return []

    def _query_slag_gcp(self, financial_year: str, month: str) -> List[Dict]:
        """Query kpi_env_slag_gcp_dust_data for industrial waste."""
        query = f"""
            SELECT
                YEAR, MONTH, PRODUCTION_MT, SLAG_MT, GCP_DUST_MT
            FROM kpi_env_slag_gcp_dust_data
            WHERE YEAR = '{financial_year}'
            ORDER BY FIELD(MONTH, 'April', 'May', 'June', 'July', 'August', 'September',
                          'October', 'November', 'December', 'January', 'February', 'March')
        """
        try:
            result = self.mcp.query(database=self.database, sql=query)
            if result.get("success"):
                logger.info(f"Retrieved {len(result['data'])} slag/GCP records")
                return result["data"]
            else:
                logger.error(f"Slag/GCP query failed: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error querying slag/GCP: {e}", exc_info=True)
            return []

    def _query_biomedical_waste(self, start_date: str, end_date: str) -> List[Dict]:
        """Query kpi_env_biomedical_waste_data for date range."""
        query = f"""
            SELECT
                DATE, PLANT, CONTAINER_TYPE,
                GENERETED_GRAMS, DISPOSED_GRAMS, STOCK_GRAMS
            FROM kpi_env_biomedical_waste_data
            WHERE DATE >= '{start_date}' AND DATE <= '{end_date}'
            ORDER BY DATE, CONTAINER_TYPE
        """
        try:
            result = self.mcp.query(database=self.database, sql=query)
            if result.get("success"):
                logger.info(f"Retrieved {len(result['data'])} biomedical waste records")
                return result["data"]
            else:
                logger.error(f"Biomedical waste query failed: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error querying biomedical waste: {e}", exc_info=True)
            return []

    def _get_last_biomedical_entry(self) -> Optional[Dict]:
        """Get the most recent biomedical waste entry."""
        query = """
            SELECT DATE, CONTAINER_TYPE, GENERETED_GRAMS
            FROM kpi_env_biomedical_waste_data
            ORDER BY DATE DESC
            LIMIT 1
        """
        try:
            result = self.mcp.query(database=self.database, sql=query)
            if result.get("success") and result["data"]:
                return result["data"][0]
            return None
        except Exception as e:
            logger.error(f"Error getting last biomedical entry: {e}", exc_info=True)
            return None

    def _query_incidents(self, start_date: str, end_date: str) -> List[Dict]:
        """Query kpi_env_incident_report for date range."""
        query = f"""
            SELECT
                DATE, PLANT, NAME, DEPARTMENT, INCIDENT_DESCRIPTION
            FROM kpi_env_incident_report
            WHERE DATE >= '{start_date}' AND DATE <= '{end_date}'
            ORDER BY DATE DESC
        """
        try:
            result = self.mcp.query(database=self.database, sql=query)
            if result.get("success"):
                logger.info(f"Retrieved {len(result['data'])} incident records")
                return result["data"]
            else:
                logger.error(f"Incidents query failed: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error querying incidents: {e}", exc_info=True)
            return []

    def _query_air_quality(self, year: int, month: str) -> List[Dict]:
        """Query kpi_env_monitoring_report for air quality data.
        First tries current month, then falls back to previous months.
        """
        # First, find the latest month with data
        latest_query = f"""
            SELECT DISTINCT YEAR, MONTH
            FROM kpi_env_monitoring_report
            ORDER BY YEAR DESC, FIELD(MONTH, 'December', 'November', 'October', 'September',
                     'August', 'July', 'June', 'May', 'April', 'March', 'February', 'January') ASC
            LIMIT 1
        """
        try:
            latest_result = self.mcp.query(database=self.database, sql=latest_query)
            if latest_result.get("success") and latest_result["data"]:
                actual_year = latest_result["data"][0].get("YEAR", year)
                actual_month = latest_result["data"][0].get("MONTH", month)
            else:
                actual_year = year
                actual_month = month
        except Exception:
            actual_year = year
            actual_month = month

        # Now query for that month's data
        query = f"""
            SELECT
                YEAR, MONTH, POLLUTANT, STATION, VALUE
            FROM kpi_env_monitoring_report
            WHERE YEAR = '{actual_year}' AND MONTH = '{actual_month}'
            ORDER BY STATION, POLLUTANT
        """
        try:
            result = self.mcp.query(database=self.database, sql=query)
            if result.get("success"):
                logger.info(f"Retrieved {len(result['data'])} air quality records for {actual_month} {actual_year}")
                return result["data"]
            else:
                logger.error(f"Air quality query failed: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error querying air quality: {e}", exc_info=True)
            return []

    def _query_training_records(self, year: int) -> List[Dict]:
        """Query kpi_env_training_records for the year."""
        query = f"""
            SELECT
                DATE, PLANT, TRAINING_NAME, TRAINER_NAME, ATTENDEES_COUNT
            FROM kpi_env_training_records
            WHERE YEAR(DATE) = {year}
            ORDER BY DATE DESC
        """
        try:
            result = self.mcp.query(database=self.database, sql=query)
            if result.get("success"):
                logger.info(f"Retrieved {len(result['data'])} training records")
                return result["data"]
            else:
                logger.error(f"Training records query failed: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error querying training records: {e}", exc_info=True)
            return []

    # ========================================================================
    # BUILD SECTION METHODS
    # ========================================================================

    def _build_executive_summary(
        self,
        food_waste_td: List[Dict],
        stp_water_td: List[Dict],
        incidents_td: List[Dict],
        compliance_returns: List[Dict],
        cbam_data: List[Dict],
        date_obj: datetime
    ) -> Dict[str, Any]:
        """Build executive summary with 6 KPI cards."""

        # Food Waste (TD total)
        total_waste = sum(safe_float(r.get("WASTE_KG")) for r in food_waste_td)
        total_persons = sum(safe_int(r.get("PERSONS_COUNT")) for r in food_waste_td)
        is_zero_waste = total_waste == 0 and total_persons > 0

        # STP Water (TD flow)
        stp_flow = sum(safe_float(r.get("DIFFERENCE")) for r in stp_water_td)

        # Incidents count
        incident_count = len(incidents_td)

        # Compliance score - only count records with actual COMPLIANCE_STATUS
        total_returns = len(compliance_returns)
        complied_returns = sum(
            1 for r in compliance_returns
            if safe_str(r.get("COMPLIANCE_STATUS", "")).strip() != "" and
               ("submitted" in safe_str(r.get("COMPLIANCE_STATUS", "")).lower() or
                "complied" in safe_str(r.get("COMPLIANCE_STATUS", "")).lower())
        )
        compliance_score = (complied_returns / total_returns * 100) if total_returns > 0 else 0

        # CBAM latest (using new env_cbam table fields)
        latest_cbam = cbam_data[-1] if cbam_data else {}
        cbam_total = safe_float(latest_cbam.get("SEE_TOTAL"))

        # Format POSTING_DATE for display
        cbam_date_label = "N/A"
        if latest_cbam.get("POSTING_DATE"):
            try:
                posting_date = latest_cbam.get("POSTING_DATE")
                if isinstance(posting_date, str):
                    dt = datetime.strptime(posting_date, '%Y-%m-%d')
                else:
                    dt = posting_date
                cbam_date_label = dt.strftime('%b %d')
            except:
                cbam_date_label = str(latest_cbam.get("POSTING_DATE", "N/A"))

        return {
            "food_waste": {
                "value": total_waste,
                "unit": "kg",
                "subtext": "Zero Waste Day! 🎉" if is_zero_waste else f"{total_waste:.1f} kg waste",
                "color": "green" if is_zero_waste else "yellow"
            },
            "persons_served": {
                "value": total_persons,
                "unit": "",
                "subtext": "Across all locations",
                "color": "blue"
            },
            "stp_water": {
                "value": stp_flow,
                "unit": "KL",
                "subtext": "Daily flow",
                "color": "cyan"
            },
            "compliance_score": {
                "value": f"{compliance_score:.0f}%",
                "unit": "",
                "subtext": f"{complied_returns}/{total_returns} returns filed",
                "color": "purple" if compliance_score == 100 else "yellow"
            },
            "incidents": {
                "value": incident_count,
                "unit": "",
                "subtext": "Zero incidents reported" if incident_count == 0 else f"{incident_count} incident(s)",
                "color": "green" if incident_count == 0 else "red"
            },
            "cbam_emissions": {
                "value": f"{cbam_total:.2f}",
                "unit": "tCO₂e/MT",
                "subtext": f"{cbam_date_label} data",
                "color": "yellow"
            }
        }

    def _build_data_gaps(
        self,
        biomedical_last: Optional[Dict],
        date_obj: datetime
    ) -> List[Dict[str, Any]]:
        """Build data gap alerts."""
        gaps = []

        if biomedical_last:
            last_date = biomedical_last.get("DATE")
            if last_date:
                try:
                    if isinstance(last_date, str):
                        last_date_obj = datetime.strptime(last_date, '%Y-%m-%d')
                    else:
                        last_date_obj = last_date

                    days_since = (date_obj - last_date_obj).days

                    if days_since > 7:
                        container = safe_str(biomedical_last.get("CONTAINER_TYPE", ""))
                        grams = safe_float(biomedical_last.get("GENERETED_GRAMS"))

                        gaps.append({
                            "type": "warning",
                            "title": "Data Recording Gap Identified",
                            "message": f"Biomedical waste data not recorded for {days_since} days. "
                                      f"Last entry: {last_date_obj.strftime('%B %d, %Y')} "
                                      f"({container} container: {grams:.0f}g generated). "
                                      f"Recommend immediate data entry to maintain compliance records.",
                            "icon": "⚠️"
                        })
                except Exception as e:
                    logger.warning(f"Error calculating biomedical gap: {e}")

        return gaps

    def _build_food_waste_section(
        self,
        td_data: List[Dict],
        mtd_data: List[Dict],
        date_obj: datetime
    ) -> Dict[str, Any]:
        """Build food waste section data."""

        # Today's breakdown by location
        td_by_location = {}
        for r in td_data:
            loc = safe_str(r.get("LOCATION", "Unknown"))
            td_by_location[loc] = {
                "waste_kg": safe_float(r.get("WASTE_KG")),
                "persons": safe_int(r.get("PERSONS_COUNT")),
                "waste_per_person": safe_float(r.get("WASTE_PER_PERSON_GM"))
            }

        # MTD daily trend for chart
        daily_trend = defaultdict(lambda: {"waste": 0, "persons": 0})
        for r in mtd_data:
            date_str = safe_str(r.get("DATE", ""))
            if date_str:
                daily_trend[date_str]["waste"] += safe_float(r.get("WASTE_KG"))
                daily_trend[date_str]["persons"] += safe_int(r.get("PERSONS_COUNT"))

        # Sort by date
        sorted_dates = sorted(daily_trend.keys())
        chart_labels = [datetime.strptime(d, '%Y-%m-%d').strftime('%b %d') for d in sorted_dates]
        chart_waste = [daily_trend[d]["waste"] for d in sorted_dates]
        chart_persons = [daily_trend[d]["persons"] for d in sorted_dates]

        # Count zero waste days
        zero_waste_days = sum(1 for d in sorted_dates if daily_trend[d]["waste"] == 0)

        # Today's totals
        td_total_waste = sum(safe_float(r.get("WASTE_KG")) for r in td_data)
        td_total_persons = sum(safe_int(r.get("PERSONS_COUNT")) for r in td_data)
        td_waste_per_person = (td_total_waste * 1000 / td_total_persons) if td_total_persons > 0 else 0

        return {
            "td": {
                "total_waste": td_total_waste,
                "total_persons": td_total_persons,
                "waste_per_person": td_waste_per_person,
                "is_zero_waste": td_total_waste == 0,
                "by_location": td_by_location
            },
            "mtd": {
                "zero_waste_days": zero_waste_days,
                "total_days": len(sorted_dates),
                "zero_waste_pct": (zero_waste_days / len(sorted_dates) * 100) if sorted_dates else 0
            },
            "chart": {
                "labels": chart_labels,
                "waste_data": chart_waste,
                "persons_data": chart_persons
            }
        }

    def _build_stp_water_section(
        self,
        td_data: List[Dict],
        mtd_data: List[Dict],
        date_obj: datetime
    ) -> Dict[str, Any]:
        """Build STP water treatment section data."""

        # Today's data
        td_initial = safe_float(td_data[0].get("INITIAL_READING")) if td_data else 0
        td_final = safe_float(td_data[0].get("FINAL_READING")) if td_data else 0
        td_flow = safe_float(td_data[0].get("DIFFERENCE")) if td_data else 0

        # MTD calculations
        mtd_flows = [safe_float(r.get("DIFFERENCE")) for r in mtd_data]
        mtd_avg = sum(mtd_flows) / len(mtd_flows) if mtd_flows else 0
        mtd_total = sum(mtd_flows)

        # Chart data
        daily_trend = {}
        for r in mtd_data:
            date_str = safe_str(r.get("DATE", ""))
            if date_str:
                daily_trend[date_str] = safe_float(r.get("DIFFERENCE"))

        sorted_dates = sorted(daily_trend.keys())
        chart_labels = [datetime.strptime(d, '%Y-%m-%d').strftime('%b %d') for d in sorted_dates]
        chart_data = [daily_trend[d] for d in sorted_dates]

        # Anomaly detection
        anomaly_threshold = mtd_avg * 1.2  # 20% above average
        is_anomaly = td_flow > anomaly_threshold if mtd_avg > 0 else False
        anomaly_pct = ((td_flow - mtd_avg) / mtd_avg * 100) if mtd_avg > 0 else 0

        return {
            "td": {
                "initial_reading": td_initial,
                "final_reading": td_final,
                "daily_flow": td_flow,
                "is_anomaly": is_anomaly,
                "anomaly_pct": anomaly_pct
            },
            "mtd": {
                "avg_flow": round(mtd_avg, 1),
                "total_flow": mtd_total,
                "days": len(mtd_flows)
            },
            "chart": {
                "labels": chart_labels,
                "data": chart_data,
                "avg_line": mtd_avg
            }
        }

    def _build_cbam_section(
        self,
        cbam_data: List[Dict],
        date_obj: datetime
    ) -> Dict[str, Any]:
        """Build CBAM emissions section data.

        Updated to use env_cbam table with fields:
        - POSTING_DATE (date)
        - SEE_DIRECT, SEE_INDIRECT, SEE_TOTAL
        """

        if not cbam_data:
            return {
                "has_data": False,
                "current": {},
                "trend": {},
                "chart": {}
            }

        # Get latest (today or most recent) and previous day data
        latest = cbam_data[-1] if cbam_data else {}
        previous = cbam_data[-2] if len(cbam_data) >= 2 else {}

        # Current values (using SEE_* fields)
        direct = safe_float(latest.get("SEE_DIRECT"))
        indirect = safe_float(latest.get("SEE_INDIRECT"))
        total = safe_float(latest.get("SEE_TOTAL"))
        threshold = 5.45  # Default EU CBAM transitional threshold

        # Previous values for trend
        prev_direct = safe_float(previous.get("SEE_DIRECT"))
        prev_indirect = safe_float(previous.get("SEE_INDIRECT"))
        prev_total = safe_float(previous.get("SEE_TOTAL"))

        # Calculate trends
        direct_trend_pct, direct_trend_dir = calculate_trend_pct(direct, prev_direct)
        indirect_trend_pct, indirect_trend_dir = calculate_trend_pct(indirect, prev_indirect)
        total_trend_pct, total_trend_dir = calculate_trend_pct(total, prev_total)

        # Threshold gap
        threshold_gap_pct = ((threshold - total) / threshold * 100) if threshold > 0 else 0

        # Chart data - format POSTING_DATE as 'Oct 15' style labels
        chart_labels = []
        for r in cbam_data:
            posting_date = r.get("POSTING_DATE", "")
            if posting_date:
                try:
                    if isinstance(posting_date, str):
                        dt = datetime.strptime(posting_date, '%Y-%m-%d')
                    else:
                        dt = posting_date
                    chart_labels.append(dt.strftime('%b %d'))
                except:
                    chart_labels.append(str(posting_date))
            else:
                chart_labels.append("")

        chart_direct = [safe_float(r.get("SEE_DIRECT")) for r in cbam_data]
        chart_indirect = [safe_float(r.get("SEE_INDIRECT")) for r in cbam_data]
        chart_total = [safe_float(r.get("SEE_TOTAL")) for r in cbam_data]

        # Get current date label
        current_date_label = ""
        if latest.get("POSTING_DATE"):
            try:
                posting_date = latest.get("POSTING_DATE")
                if isinstance(posting_date, str):
                    dt = datetime.strptime(posting_date, '%Y-%m-%d')
                else:
                    dt = posting_date
                current_date_label = dt.strftime('%b %d')
            except:
                current_date_label = str(latest.get("POSTING_DATE", ""))

        return {
            "has_data": True,
            "current": {
                "date": current_date_label,
                "month": current_date_label,  # Keep for compatibility
                "direct": direct,
                "indirect": indirect,
                "total": total,
                "threshold": threshold,
                "threshold_gap_pct": round(threshold_gap_pct, 1)
            },
            "trend": {
                "direct": {"pct": direct_trend_pct, "direction": direct_trend_dir},
                "indirect": {"pct": indirect_trend_pct, "direction": indirect_trend_dir},
                "total": {"pct": total_trend_pct, "direction": total_trend_dir},
                "prev_month": ""  # Not applicable for daily data
            },
            "chart": {
                "labels": chart_labels,
                "direct": chart_direct,
                "indirect": chart_indirect,
                "total": chart_total,
                "threshold": [threshold] * len(chart_labels)
            }
        }

    def _build_licenses_section(
        self,
        licenses_data: List[Dict],
        date_obj: datetime
    ) -> Dict[str, Any]:
        """Build license status section data."""

        licenses_list = []
        expiring_soon = 0
        expired = 0

        for lic in licenses_data:
            status_class, status_text = get_license_status(
                lic.get("VALID_UPTO"), date_obj
            )

            if "expired" in status_class:
                expired += 1
            elif "expiring" in status_class:
                expiring_soon += 1

            licenses_list.append({
                "location": safe_str(lic.get("LOCATION", "")),
                "type": safe_str(lic.get("CLEARANCE_TYPE", "")),
                "license_no": safe_str(lic.get("LICENSE_NO", "")),
                "authority": safe_str(lic.get("LICENSING_AUTHORITY", "")),
                "valid_upto": safe_str(lic.get("VALID_UPTO", "")),
                "renewal_date": safe_str(lic.get("RENEWAL_DATE", "")),
                "payment_due": safe_str(lic.get("PAYMENT_DUE", "")),
                "status_class": status_class,
                "status_text": status_text
            })

        return {
            "total": len(licenses_list),
            "expiring_soon": expiring_soon,
            "expired": expired,
            "valid": len(licenses_list) - expiring_soon - expired,
            "licenses": licenses_list
        }

    def _build_air_quality_section(
        self,
        air_data: List[Dict]
    ) -> Dict[str, Any]:
        """Build air quality section data."""

        if not air_data:
            return {"has_data": False, "stations": {}, "chart": {}, "data_month": None, "data_year": None}

        # Get the actual month and year from the data
        data_month = safe_str(air_data[0].get("MONTH", ""))
        data_year = safe_str(air_data[0].get("YEAR", ""))

        # Pivot data by station and pollutant
        stations_data = defaultdict(dict)
        for r in air_data:
            station = safe_str(r.get("STATION", ""))
            pollutant = safe_str(r.get("POLLUTANT", ""))
            value = safe_float(r.get("VALUE"))

            if station and pollutant:
                limit = AIR_QUALITY_LIMITS.get(pollutant, 100)
                pct_of_limit = (value / limit * 100) if limit > 0 else 0

                stations_data[station][pollutant] = {
                    "value": value,
                    "limit": limit,
                    "pct_of_limit": round(pct_of_limit, 1),
                    "within_limit": value <= limit
                }

        # Get unique stations and pollutants for chart
        stations = sorted(stations_data.keys())
        pollutants = ["PM10", "PM2.5", "NO2", "SO2"]

        # Build chart datasets
        chart_data = {}
        for pollutant in pollutants:
            chart_data[pollutant] = [
                stations_data[s].get(pollutant, {}).get("value", 0)
                for s in stations
            ]

        # Check overall compliance
        all_within_limits = all(
            p_data.get("within_limit", True)
            for s_data in stations_data.values()
            for p_data in s_data.values()
        )

        return {
            "has_data": True,
            "all_within_limits": all_within_limits,
            "data_month": data_month,
            "data_year": data_year,
            "stations": dict(stations_data),
            "chart": {
                "labels": stations,
                "datasets": chart_data
            },
            "limits": AIR_QUALITY_LIMITS
        }

    def _build_industrial_waste_section(
        self,
        slag_data: List[Dict]
    ) -> Dict[str, Any]:
        """Build industrial waste (slag/GCP) section data."""

        if not slag_data:
            return {"has_data": False, "current": {}, "trend": []}

        # Get latest month
        latest = slag_data[-1] if slag_data else {}

        production = safe_float(latest.get("PRODUCTION_MT"))
        slag = safe_float(latest.get("SLAG_MT"))
        gcp_dust = safe_float(latest.get("GCP_DUST_MT"))
        slag_ratio = (slag / production * 100) if production > 0 else 0

        return {
            "has_data": True,
            "current": {
                "month": safe_str(latest.get("MONTH", "")),
                "production_mt": production,
                "slag_mt": slag,
                "gcp_dust_mt": gcp_dust,
                "slag_ratio_pct": round(slag_ratio, 1)
            },
            "trend": [
                {
                    "month": safe_str(r.get("MONTH", "")),
                    "production": safe_float(r.get("PRODUCTION_MT")),
                    "slag": safe_float(r.get("SLAG_MT")),
                    "gcp_dust": safe_float(r.get("GCP_DUST_MT"))
                }
                for r in slag_data
            ]
        }

    def _build_compliance_returns_section(
        self,
        returns_data: List[Dict]
    ) -> Dict[str, Any]:
        """Build compliance returns section data."""

        returns_list = []
        complied_count = 0

        for r in returns_data:
            status = safe_str(r.get("COMPLIANCE_STATUS", ""))
            remarks = safe_str(r.get("REMARKS", ""))

            # Only count as complied if COMPLIANCE_STATUS is not empty/NULL
            is_complied = (
                status.strip() != "" and
                ("submitted" in status.lower() or "complied" in status.lower())
            )

            if is_complied:
                complied_count += 1

            returns_list.append({
                "area": safe_str(r.get("AREA", "")),
                "subject": safe_str(r.get("SUBJECT", "")),
                "frequency": safe_str(r.get("SUBMISSION_PERIOD", "")),
                "authority": safe_str(r.get("COMPLIANCE_AUTHORITY", "")),
                "status": status,
                "remarks": remarks,
                "is_complied": is_complied
            })

        total = len(returns_list)
        compliance_rate = (complied_count / total * 100) if total > 0 else 0

        return {
            "total": total,
            "complied": complied_count,
            "pending": total - complied_count,
            "compliance_rate": round(compliance_rate, 1),
            "returns": returns_list
        }

    def _build_training_section(
        self,
        training_data: List[Dict]
    ) -> Dict[str, Any]:
        """Build training records section data."""

        total_sessions = len(training_data)
        total_attendees = sum(safe_int(r.get("ATTENDEES_COUNT")) for r in training_data)

        # Group by training type
        by_type = defaultdict(lambda: {"sessions": 0, "attendees": 0})
        trainers = set()

        for r in training_data:
            training_name = safe_str(r.get("TRAINING_NAME", "Other"))
            by_type[training_name]["sessions"] += 1
            by_type[training_name]["attendees"] += safe_int(r.get("ATTENDEES_COUNT"))

            trainer = safe_str(r.get("TRAINER_NAME", ""))
            if trainer:
                trainers.add(trainer)

        return {
            "total_sessions": total_sessions,
            "total_attendees": total_attendees,
            "by_type": dict(by_type),
            "trainers": list(trainers),
            "records": [
                {
                    "date": safe_str(r.get("DATE", "")),
                    "training": safe_str(r.get("TRAINING_NAME", "")),
                    "trainer": safe_str(r.get("TRAINER_NAME", "")),
                    "attendees": safe_int(r.get("ATTENDEES_COUNT"))
                }
                for r in training_data[:10]  # Last 10 records
            ]
        }

    def _build_incidents_section(
        self,
        incidents_data: List[Dict]
    ) -> Dict[str, Any]:
        """Build incidents section data."""

        return {
            "count": len(incidents_data),
            "incidents": [
                {
                    "date": safe_str(r.get("DATE", "")),
                    "name": safe_str(r.get("NAME", "")),
                    "department": safe_str(r.get("DEPARTMENT", "")),
                    "description": safe_str(r.get("INCIDENT_DESCRIPTION", ""))
                }
                for r in incidents_data
            ]
        }

    def _build_biomedical_section(
        self,
        td_data: List[Dict],
        last_entry: Optional[Dict]
    ) -> Dict[str, Any]:
        """Build biomedical waste section data."""

        # Today's data by container type
        by_container = {}
        for r in td_data:
            container = safe_str(r.get("CONTAINER_TYPE", "Unknown"))
            by_container[container] = {
                "generated": safe_float(r.get("GENERETED_GRAMS")),
                "disposed": safe_float(r.get("DISPOSED_GRAMS")),
                "stock": safe_float(r.get("STOCK_GRAMS"))
            }

        total_generated = sum(d["generated"] for d in by_container.values())
        total_disposed = sum(d["disposed"] for d in by_container.values())

        return {
            "has_data": len(td_data) > 0,
            "td": {
                "total_generated": total_generated,
                "total_disposed": total_disposed,
                "by_container": by_container
            },
            "last_entry": {
                "date": safe_str(last_entry.get("DATE", "")) if last_entry else "",
                "container": safe_str(last_entry.get("CONTAINER_TYPE", "")) if last_entry else "",
                "grams": safe_float(last_entry.get("GENERETED_GRAMS")) if last_entry else 0
            } if last_entry else None
        }

    def _check_has_data(self, analysis_data: Dict) -> bool:
        """Check if we have meaningful data."""
        # Check key sections
        food_waste = analysis_data.get("food_waste", {}).get("td", {})
        stp = analysis_data.get("stp_water", {}).get("td", {})

        has_food_waste = food_waste.get("total_persons", 0) > 0
        has_stp = stp.get("daily_flow", 0) > 0
        has_cbam = analysis_data.get("cbam_emissions", {}).get("has_data", False)

        return has_food_waste or has_stp or has_cbam

    # ========================================================================
    # NEW RANGE-SPECIFIC METHODS (SIMPLIFIED)
    # ========================================================================

    def process_date_range(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        NEW: Process ENV data for a DATE RANGE (simplified aggregation).

        Args:
            start_date: Start date string in YYYY-MM-DD format
            end_date: End date string in YYYY-MM-DD format

        Returns:
            Dictionary with period_kpis (aggregated metrics for the entire range)
        """
        logger.info(f"Processing ENV data for range: {start_date} to {end_date}")

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

        # Query key data for the range (using existing query methods with date range)
        food_waste_data = self._query_food_waste_range(start_date, end_date)
        stp_data = self._query_stp_water_range(start_date, end_date)
        cbam_data = self._query_cbam_range(start_date, end_date)
        water_consumption_data = self._query_water_consumption_range(start_date, end_date)
        incidents_data = self._query_incidents_range(start_date, end_date)

        # Build analysis data structure (RANGE version - simplified)
        analysis_data = {
            "start_date": start_date,
            "end_date": end_date,
            "date_range_formatted": date_range_formatted,
            "days_in_range": days_in_range,
            "year": start_obj.year,
            "month": start_month_name,

            # PERIOD KPIs (aggregated across range)
            "period_kpis": self._build_period_kpis_env_range(
                food_waste_data, stp_data, cbam_data, water_consumption_data, incidents_data
            ),

            # Simplified sections
            "food_waste": {"period": self._aggregate_food_waste(food_waste_data)},
            "stp_water": {"period": self._aggregate_stp_water(stp_data)},
            "cbam_emissions": {"period": self._aggregate_cbam(cbam_data)},
            "water_consumption": {"period": self._aggregate_water(water_consumption_data)},
            "incidents": {"period": self._aggregate_incidents(incidents_data)},
        }

        # Check if we have any data
        has_data = len(food_waste_data) > 0 or len(stp_data) > 0 or len(cbam_data) > 0
        analysis_data["has_data"] = has_data

        logger.info(f"ENV range processing complete. Has data: {has_data}, Days: {days_in_range}")
        return analysis_data

    # Simplified range query methods
    def _query_food_waste_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Query food waste for date range."""
        query = f"""
            SELECT * FROM kpi_env_food_waste_data
            WHERE DATE BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY DATE
        """
        try:
            result = self.mcp.query(sql=query)
            return result["data"] if result["success"] else []
        except Exception as e:
            logger.error(f"Error querying food waste range: {e}", exc_info=True)
            return []

    def _query_stp_water_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Query STP water for date range."""
        query = f"""
            SELECT * FROM kpi_env_stp_water_data
            WHERE DATE BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY DATE
        """
        try:
            result = self.mcp.query(sql=query)
            return result["data"] if result["success"] else []
        except Exception as e:
            logger.error(f"Error querying STP range: {e}", exc_info=True)
            return []

    def _query_cbam_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Query CBAM emissions for date range."""
        query = f"""
            SELECT * FROM env_cbam
            WHERE date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY date
        """
        try:
            result = self.mcp.query(sql=query)
            return result["data"] if result["success"] else []
        except Exception as e:
            logger.error(f"Error querying CBAM range: {e}", exc_info=True)
            return []

    def _query_water_consumption_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Query water consumption for date range."""
        query = f"""
            SELECT * FROM kpi_env_water_consumption_data
            WHERE DATE BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY DATE
        """
        try:
            result = self.mcp.query(sql=query)
            return result["data"] if result["success"] else []
        except Exception as e:
            logger.error(f"Error querying water range: {e}", exc_info=True)
            return []

    def _query_incidents_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Query incidents for date range."""
        query = f"""
            SELECT * FROM kpi_env_incident_report
            WHERE INCIDENT_DATE BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY INCIDENT_DATE
        """
        try:
            result = self.mcp.query(sql=query)
            return result["data"] if result["success"] else []
        except Exception as e:
            logger.error(f"Error querying incidents range: {e}", exc_info=True)
            return []

    # Simplified aggregation methods
    def _build_period_kpis_env_range(self, food_waste, stp, cbam, water, incidents) -> Dict[str, Any]:
        """Build period KPIs for ENV."""
        from .formatter import safe_float, safe_int

        total_food_waste = sum(safe_float(r.get('FOOD_WASTE_GENERATED')) for r in food_waste)
        total_stp_flow = sum(safe_float(r.get('DAILY_FLOW')) for r in stp)
        total_emissions = sum(safe_float(r.get('SEE_TOTAL')) for r in cbam)
        total_water = sum(safe_float(r.get('WATER_CONSUMED')) for r in water)
        incident_count = len(incidents)

        return {
            "food_waste_kg": round(total_food_waste, 2),
            "stp_water_kl": round(total_stp_flow, 2),
            "emissions_tonnes": round(total_emissions, 2),
            "water_consumed_kl": round(total_water, 2),
            "incidents": incident_count,
        }

    def _aggregate_food_waste(self, data: List[Dict]) -> Dict:
        """Aggregate food waste."""
        from .formatter import safe_float
        total = sum(safe_float(r.get('FOOD_WASTE_GENERATED')) for r in data)
        return {"total_kg": round(total, 2), "days": len(data)}

    def _aggregate_stp_water(self, data: List[Dict]) -> Dict:
        """Aggregate STP water."""
        from .formatter import safe_float
        total = sum(safe_float(r.get('DAILY_FLOW')) for r in data)
        return {"total_kl": round(total, 2), "days": len(data)}

    def _aggregate_cbam(self, data: List[Dict]) -> Dict:
        """Aggregate CBAM emissions."""
        from .formatter import safe_float
        total = sum(safe_float(r.get('SEE_TOTAL')) for r in data)
        return {"total_tonnes": round(total, 2), "days": len(data)}

    def _aggregate_water(self, data: List[Dict]) -> Dict:
        """Aggregate water consumption."""
        from .formatter import safe_float
        total = sum(safe_float(r.get('WATER_CONSUMED')) for r in data)
        return {"total_kl": round(total, 2), "days": len(data)}

    def _aggregate_incidents(self, data: List[Dict]) -> Dict:
        """Aggregate incidents."""
        return {"count": len(data)}


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def process_env_data(mcp_client, date: str) -> Dict[str, Any]:
    """
    Convenience function to process ENV data for a date.

    Args:
        mcp_client: MCP client instance
        date: Date string (YYYY-MM-DD)

    Returns:
        Analysis data dictionary
    """
    processor = ENVDataProcessor(mcp_client)
    return processor.process_date(date)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['ENVDataProcessor', 'process_env_data']


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test module load"""
    print("ENV Formatter module loaded successfully")
    print("Use ENVDataProcessor(mcp_client).process_date('YYYY-MM-DD') to process data")
    print(f"Tables covered: 14")
    print(f"Sections: executive_summary, food_waste, stp_water, cbam_emissions, ")
    print(f"          licenses, air_quality, industrial_waste, compliance_returns, ")
    print(f"          training, incidents, biomedical_waste, data_gaps")