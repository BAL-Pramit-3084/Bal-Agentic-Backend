"""
Automobile Formatter
====================
Data processor for Automobile/Fleet Management Dashboard.

This processor queries the truck_reports table containing:
- Daily trip data for 35 MAN trucks
- Engine hours, motion hours, idle hours
- Fuel consumption, filling, draining
- Distance traveled, speed metrics
- Mileage (KMPL) calculations

Data Scope:
- Daily metrics (Today)
- Comparison metrics (Yesterday)
- Month-to-Date (MTD) aggregates
- Trend data (Last 16 days for charts)

Key Calculations:
- Idle percentage = idling_engine_hours / engine_hours * 100
- Fleet utilization = active_trucks / total_trucks * 100
- Fuel balance = filled - consumed
- Anomaly detection for impossible KMPL values

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

DAY_NAMES = {
    0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday",
    4: "Friday", 5: "Saturday", 6: "Sunday"
}

# Fleet configuration
TOTAL_FLEET_SIZE = 35  # Total MAN trucks in fleet
ASSUMED_TANK_CAPACITY = 170  # Liters - for fuel gauge percentage

# Thresholds for categorization
IDLE_THRESHOLDS = {
    "high": 50,      # >= 50% idle is HIGH
    "medium": 35,    # >= 35% idle is MEDIUM
    "low": 0         # < 35% idle is LOW
}

FUEL_LEVEL_THRESHOLDS = {
    "high": 100,     # > 100L is HIGH
    "medium": 50,    # 50-100L is MEDIUM
    "low": 0         # < 50L is LOW (critical)
}

MILEAGE_THRESHOLDS = {
    "excellent": 0.9,   # >= 0.9 KMPL
    "good": 0.7,        # >= 0.7 KMPL
    "poor": 0.5,        # >= 0.5 KMPL
    "critical": 0       # < 0.5 KMPL
}

# Anomaly detection
MAX_VALID_KMPL = 10  # Anything above this is sensor malfunction
MIN_VALID_FUEL_CONSUMED = 0.1  # Minimum to consider valid consumption


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


def time_to_hours(time_value: Any) -> float:
    """
    Convert TIME field (HH:MM:SS or timedelta) to decimal hours.

    Args:
        time_value: Can be string "HH:MM:SS", timedelta, or None

    Returns:
        Decimal hours (e.g., 2:30:00 -> 2.5)
    """
    if time_value is None:
        return 0.0

    try:
        # Handle timedelta objects (common from MySQL TIME fields)
        if hasattr(time_value, 'total_seconds'):
            return time_value.total_seconds() / 3600

        # Handle string format "HH:MM:SS"
        time_str = str(time_value)
        parts = time_str.split(':')

        if len(parts) >= 2:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2]) if len(parts) > 2 else 0
            return hours + minutes / 60 + seconds / 3600

        return 0.0
    except (ValueError, TypeError, AttributeError):
        return 0.0


def time_to_minutes(time_value: Any) -> float:
    """Convert TIME field to total minutes."""
    return time_to_hours(time_value) * 60


def format_time_display(time_value: Any) -> str:
    """
    Format TIME field for display as "H:MM" or "HH:MM".

    Args:
        time_value: TIME field value

    Returns:
        Formatted string like "14:43" or "0:37"
    """
    if time_value is None:
        return "0:00"

    try:
        # Handle timedelta
        if hasattr(time_value, 'total_seconds'):
            total_seconds = int(time_value.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}:{minutes:02d}"

        # Handle string format
        time_str = str(time_value)
        parts = time_str.split(':')

        if len(parts) >= 2:
            hours = int(parts[0])
            minutes = int(parts[1])
            return f"{hours}:{minutes:02d}"

        return "0:00"
    except (ValueError, TypeError):
        return "0:00"


def parse_max_speed(speed_value: Any) -> int:
    """
    Parse max_speed from various formats like "30 k", "30", "0".

    Args:
        speed_value: String like "30 k" or "0"

    Returns:
        Integer speed value
    """
    if speed_value is None:
        return 0

    try:
        # Extract digits only
        speed_str = str(speed_value)
        digits = ''.join(filter(str.isdigit, speed_str))
        return int(digits) if digits else 0
    except (ValueError, TypeError):
        return 0


def get_idle_category(idle_pct: float) -> Tuple[str, str]:
    """
    Get idle category and CSS class based on percentage.

    Returns:
        Tuple of (category_name, css_class)
    """
    if idle_pct >= IDLE_THRESHOLDS["high"]:
        return "High", "high"
    elif idle_pct >= IDLE_THRESHOLDS["medium"]:
        return "Med", "medium"
    else:
        return "Low", "low"


def get_fuel_status(fuel_level: float) -> Tuple[str, str, bool]:
    """
    Get fuel status category and CSS class.

    Returns:
        Tuple of (status_name, css_class, is_critical)
    """
    if fuel_level > FUEL_LEVEL_THRESHOLDS["high"]:
        return "high", "high", False
    elif fuel_level >= FUEL_LEVEL_THRESHOLDS["medium"]:
        return "medium", "medium", False
    else:
        return "low", "low", True


def get_mileage_badge(kmpl: float, fuel_consumed: float) -> Tuple[str, str, bool]:
    """
    Get mileage badge class and detect anomalies.

    Args:
        kmpl: Kilometers per liter
        fuel_consumed: Fuel consumed (to detect sensor issues)

    Returns:
        Tuple of (badge_class, display_value, is_anomaly)
    """
    # Check for sensor anomaly
    if kmpl > MAX_VALID_KMPL:
        return "badge-info", f"{kmpl:.1f}*", True

    # Check for no fuel data
    if fuel_consumed < MIN_VALID_FUEL_CONSUMED:
        return "badge-info", "Sensor?", True

    # Normal categorization
    if kmpl >= MILEAGE_THRESHOLDS["excellent"]:
        return "badge-success", f"{kmpl:.2f}", False
    elif kmpl >= MILEAGE_THRESHOLDS["good"]:
        return "badge-warning", f"{kmpl:.2f}", False
    elif kmpl >= MILEAGE_THRESHOLDS["poor"]:
        return "badge-warning", f"{kmpl:.2f}", False
    else:
        return "badge-danger", f"{kmpl:.2f}", False


def get_idle_badge(idle_pct: float) -> str:
    """Get badge class for idle percentage."""
    if idle_pct >= IDLE_THRESHOLDS["high"]:
        return "badge-danger"
    elif idle_pct >= IDLE_THRESHOLDS["medium"]:
        return "badge-warning"
    else:
        return "badge-success"


def calculate_idle_percentage(engine_hours: float, idle_hours: float) -> float:
    """Calculate idle percentage safely."""
    if engine_hours <= 0:
        return 0.0
    return (idle_hours / engine_hours) * 100


def get_fuel_gauge_percentage(fuel_level: float, tank_capacity: float = ASSUMED_TANK_CAPACITY) -> float:
    """Calculate fuel gauge percentage for visual display."""
    if tank_capacity <= 0:
        return 0
    pct = (fuel_level / tank_capacity) * 100
    return min(100, max(0, pct))  # Clamp between 0-100


def get_trend_direction(current: float, previous: float) -> Tuple[str, str]:
    """
    Get trend direction symbol and class.

    Returns:
        Tuple of (symbol, css_class)
    """
    if previous == 0:
        return "", "neutral"

    diff = current - previous
    pct_change = (diff / previous) * 100

    if pct_change > 1:
        return "▲", "negative" if diff > 0 else "positive"  # Up is bad for fuel, good for distance
    elif pct_change < -1:
        return "▼", "positive" if diff < 0 else "negative"
    else:
        return "", "neutral"


# ============================================================================
# AUTOMOBILE DATA PROCESSOR CLASS
# ============================================================================

class AutomobileDataProcessor:
    """
    Process Automobile/Fleet data for dashboard generation.
    """

    def __init__(self, mcp_client):
        """
        Initialize with MCP client for database queries.

        Args:
            mcp_client: MCP client instance with query() method
        """
        self.mcp = mcp_client
        self.database = "balcorpdb"
        self.table = "truck_reports"
        logger.info("Automobile Data Processor initialized")

    def process_date(self, date: str) -> Dict[str, Any]:
        """
        Main entry point: Process all automobile data for a specific date.

        Args:
            date: Date string in YYYY-MM-DD format

        Returns:
            Dictionary with all processed data for template engine
        """
        logger.info(f"Processing Automobile data for date: {date}")

        # Parse date
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        yesterday = (date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
        month_start = date_obj.replace(day=1).strftime('%Y-%m-%d')

        month_name = MONTH_NAMES[date_obj.month]
        month_abbrev = MONTH_ABBREV[date_obj.month]
        day_name = DAY_NAMES[date_obj.weekday()]

        # ====================================================================
        # QUERY ALL DATA SOURCES
        # ====================================================================

        today_data = self._query_day_data(date)
        yesterday_data = self._query_day_data(yesterday)
        mtd_data = self._query_mtd_data(month_start, date)
        trend_data = self._query_trend_data(date, days=16)
        mtd_by_truck = self._query_mtd_by_truck(month_start, date)

        # ====================================================================
        # BUILD ALL SECTIONS
        # ====================================================================

        # Basic metadata
        analysis_data = {
            "date": date,
            "date_formatted": f"{month_name} {date_obj.day}, {date_obj.year}",
            "month": month_name,
            "month_abbrev": month_abbrev,
            "day": date_obj.day,
            "year": date_obj.year,
            "day_name": day_name,
        }

        # Build each section
        analysis_data["kpis"] = self._build_kpis(today_data, yesterday_data)
        analysis_data["mtd"] = self._build_mtd_summary(mtd_data, mtd_by_truck)
        analysis_data["top_performers"] = self._build_top_performers(today_data)
        analysis_data["idle_analysis"] = self._build_idle_analysis(today_data)
        analysis_data["truck_details"] = self._build_truck_details(today_data)
        analysis_data["idle_trucks"] = self._build_idle_trucks_list(today_data)
        analysis_data["charts"] = self._build_chart_data(trend_data, mtd_by_truck, today_data)
        analysis_data["alerts"] = self._build_alerts(today_data)

        # Summary stats for template
        analysis_data["has_data"] = len(today_data) > 0

        logger.info(f"Automobile data processing complete. {len(today_data)} truck records for {date}")
        return analysis_data

    def process_date_range(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        NEW: Process automobile/fleet data for a DATE RANGE.

        Args:
            start_date: Start date string in YYYY-MM-DD format
            end_date: End date string in YYYY-MM-DD format

        Returns:
            Dictionary with period-aggregated metrics
        """
        logger.info(f"Processing Automobile data for range: {start_date} to {end_date}")

        # Parse and validate dates
        start_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_obj = datetime.strptime(end_date, '%Y-%m-%d')

        if start_obj > end_obj:
            raise ValueError("start_date must be before or equal to end_date")

        days_in_range = (end_obj - start_obj).days + 1

        # Format date range for display
        start_month_name = MONTH_NAMES[start_obj.month]
        end_month_name = MONTH_NAMES[end_obj.month]

        if start_obj.year == end_obj.year:
            if start_obj.month == end_obj.month:
                date_range_formatted = f"{start_month_name} {start_obj.day}-{end_obj.day}, {start_obj.year}"
            else:
                date_range_formatted = f"{start_month_name} {start_obj.day} - {end_month_name} {end_obj.day}, {start_obj.year}"
        else:
            date_range_formatted = f"{start_month_name} {start_obj.day}, {start_obj.year} - {end_month_name} {end_obj.day}, {end_obj.year}"

        # Query all data for the range
        range_data = self._query_range_data(start_date, end_date)

        # Build analysis data (aggregated for range)
        analysis_data = {
            "start_date": start_date,
            "end_date": end_date,
            "date_range_formatted": date_range_formatted,
            "days_in_range": days_in_range,
            "year": start_obj.year,
        }

        # Build sections with aggregated data
        analysis_data["period_kpis"] = self._build_period_kpis(range_data)
        analysis_data["period_summary"] = self._build_period_summary(range_data)
        analysis_data["top_performers"] = self._build_top_performers_range(range_data)
        analysis_data["idle_analysis"] = self._build_idle_analysis(range_data)
        analysis_data["truck_details"] = self._build_truck_details_range(range_data)
        analysis_data["charts"] = self._build_chart_data_range(range_data, start_date, end_date)
        analysis_data["alerts"] = self._build_alerts_range(range_data)

        # Has data check
        analysis_data["has_data"] = len(range_data) > 0

        logger.info(f"Automobile range processing complete. {len(range_data)} records, {days_in_range} days")
        return analysis_data

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def _query_day_data(self, date: str) -> List[Dict]:
        """Query all truck data for a specific date."""
        try:
            sql = f"""
                SELECT
                    slNo,
                    tripDate,
                    vehicle_desc,
                    engine_hours,
                    in_motion_engine_hours,
                    idling_engine_hours,
                    avg_speed,
                    max_speed,
                    distance,
                    fuel_consumed,
                    kmpl,
                    parkings_hours,
                    initial_fuel_level,
                    final_fuel_level,
                    total_fillings,
                    total_drains,
                    filled,
                    drained
                FROM {self.table}
                WHERE tripDate = '{date}'
                ORDER BY distance DESC
            """
            result = self.mcp.query(sql, database=self.database)

            if result.get("success") and result.get("data"):
                logger.info(f"Retrieved {len(result['data'])} records for {date}")
                return result["data"]
            return []
        except Exception as e:
            logger.error(f"Error querying day data for {date}: {e}")
            return []

    def _query_mtd_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Query aggregated MTD data."""
        try:
            sql = f"""
                SELECT
                    COUNT(DISTINCT vehicle_desc) as trucks_active,
                    SUM(distance) as total_distance,
                    SUM(fuel_consumed) as total_fuel_consumed,
                    SUM(filled) as total_filled,
                    SUM(drained) as total_drained,
                    SUM(total_fillings) as total_filling_events,
                    SUM(total_drains) as total_drain_events
                FROM {self.table}
                WHERE tripDate >= '{start_date}' AND tripDate <= '{end_date}'
                AND (distance > 0 OR fuel_consumed > 0)
            """
            result = self.mcp.query(sql, database=self.database)

            if result.get("success") and result.get("data"):
                return result["data"][0]
            return {}
        except Exception as e:
            logger.error(f"Error querying MTD data: {e}")
            return {}

    def _query_mtd_by_truck(self, start_date: str, end_date: str) -> List[Dict]:
        """Query MTD totals grouped by truck for top performers chart."""
        try:
            sql = f"""
                SELECT
                    vehicle_desc,
                    SUM(distance) as mtd_distance,
                    SUM(fuel_consumed) as mtd_fuel,
                    COUNT(*) as trip_days
                FROM {self.table}
                WHERE tripDate >= '{start_date}' AND tripDate <= '{end_date}'
                AND distance > 0
                GROUP BY vehicle_desc
                ORDER BY mtd_distance DESC
            """
            result = self.mcp.query(sql, database=self.database)

            if result.get("success") and result.get("data"):
                return result["data"]
            return []
        except Exception as e:
            logger.error(f"Error querying MTD by truck: {e}")
            return []

    def _query_trend_data(self, end_date: str, days: int = 16) -> List[Dict]:
        """Query daily aggregates for trend charts."""
        try:
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=days-1)).strftime('%Y-%m-%d')

            sql = f"""
                SELECT
                    tripDate,
                    SUM(distance) as total_distance,
                    SUM(fuel_consumed) as total_fuel_consumed,
                    SUM(filled) as total_filled,
                    SUM(drained) as total_drained,
                    COUNT(DISTINCT CASE WHEN distance > 0 THEN vehicle_desc END) as active_trucks
                FROM {self.table}
                WHERE tripDate >= '{start_date}' AND tripDate <= '{end_date}'
                GROUP BY tripDate
                ORDER BY tripDate ASC
            """
            result = self.mcp.query(sql, database=self.database)

            if result.get("success") and result.get("data"):
                return result["data"]
            return []
        except Exception as e:
            logger.error(f"Error querying trend data: {e}")
            return []

    # ========================================================================
    # BUILD METHODS
    # ========================================================================

    def _build_kpis(self, today_data: List[Dict], yesterday_data: List[Dict]) -> Dict[str, Any]:
        """Build daily KPI metrics."""

        # Today's calculations
        total_trucks = TOTAL_FLEET_SIZE
        active_trucks = len([t for t in today_data if safe_float(t.get('distance')) > 0 or time_to_hours(t.get('engine_hours')) > 0])
        utilization_pct = round((active_trucks / total_trucks) * 100) if total_trucks > 0 else 0

        total_distance = sum(safe_float(t.get('distance')) for t in today_data)
        fuel_consumed = sum(safe_float(t.get('fuel_consumed')) for t in today_data)
        fuel_filled = sum(safe_float(t.get('filled')) for t in today_data)
        fuel_drained = sum(safe_float(t.get('drained')) for t in today_data)
        fillings_count = sum(safe_int(t.get('total_fillings')) for t in today_data)

        # Calculate average KMPL (only for trucks with valid consumption)
        valid_trucks = [t for t in today_data if safe_float(t.get('fuel_consumed')) > MIN_VALID_FUEL_CONSUMED]
        if valid_trucks and fuel_consumed > 0:
            avg_kmpl = total_distance / fuel_consumed
        else:
            avg_kmpl = 0.0

        # Max speed today
        max_speed_today = max((parse_max_speed(t.get('max_speed')) for t in today_data), default=0)

        # Yesterday's calculations for comparison
        yesterday_distance = sum(safe_float(t.get('distance')) for t in yesterday_data)
        yesterday_fuel = sum(safe_float(t.get('fuel_consumed')) for t in yesterday_data)

        # Determine trend directions
        distance_trend, distance_class = get_trend_direction(total_distance, yesterday_distance)
        # For distance, down is negative (less work done)
        if total_distance < yesterday_distance:
            distance_class = "negative"
            distance_trend = "▼"
        elif total_distance > yesterday_distance:
            distance_class = "positive"
            distance_trend = "▲"

        fuel_trend, fuel_class = get_trend_direction(fuel_consumed, yesterday_fuel)
        # For fuel, up is negative (more consumption)
        if fuel_consumed > yesterday_fuel:
            fuel_class = "negative"
            fuel_trend = "▲"
        elif fuel_consumed < yesterday_fuel:
            fuel_class = "positive"
            fuel_trend = "▼"

        return {
            "total_trucks": total_trucks,
            "active_trucks": active_trucks,
            "utilization_pct": utilization_pct,
            "total_distance": round(total_distance, 1),
            "yesterday_distance": round(yesterday_distance, 1),
            "distance_trend": distance_trend,
            "distance_class": distance_class,
            "fuel_consumed": round(fuel_consumed, 1),
            "yesterday_fuel": round(yesterday_fuel, 1),
            "fuel_trend": fuel_trend,
            "fuel_class": fuel_class,
            "avg_kmpl": round(avg_kmpl, 2),
            "fuel_filled": round(fuel_filled, 1),
            "fillings_count": fillings_count,
            "max_speed": max_speed_today,
            "fuel_drained": round(fuel_drained, 1),
            "has_theft": fuel_drained > 0
        }

    def _build_mtd_summary(self, mtd_data: Dict, mtd_by_truck: List[Dict]) -> Dict[str, Any]:
        """Build MTD summary metrics."""

        total_distance = safe_float(mtd_data.get('total_distance'))
        total_fuel_consumed = safe_float(mtd_data.get('total_fuel_consumed'))
        total_filled = safe_float(mtd_data.get('total_filled'))
        total_drained = safe_float(mtd_data.get('total_drained'))
        trucks_active = safe_int(mtd_data.get('trucks_active'))

        # Calculate MTD average KMPL
        mtd_avg_kmpl = total_distance / total_fuel_consumed if total_fuel_consumed > 0 else 0

        # Fuel balance (deficit if negative)
        fuel_balance = total_filled - total_fuel_consumed

        return {
            "distance": round(total_distance, 1),
            "fuel_consumed": round(total_fuel_consumed, 1),
            "fuel_filled": round(total_filled, 1),
            "fuel_drained": round(total_drained, 1),
            "avg_kmpl": round(mtd_avg_kmpl, 2),
            "trucks_active": trucks_active,
            "fuel_balance": round(fuel_balance, 1),
            "filling_events": safe_int(mtd_data.get('total_filling_events')),
            "drain_events": safe_int(mtd_data.get('total_drain_events'))
        }

    def _build_top_performers(self, today_data: List[Dict], limit: int = 5) -> List[Dict]:
        """Build top performers list (by distance)."""

        # Filter active trucks and sort by distance
        active_trucks = [t for t in today_data if safe_float(t.get('distance')) > 0]
        sorted_trucks = sorted(active_trucks, key=lambda x: safe_float(x.get('distance')), reverse=True)

        top_performers = []
        for i, truck in enumerate(sorted_trucks[:limit]):
            distance = safe_float(truck.get('distance'))
            fuel = safe_float(truck.get('fuel_consumed'))
            kmpl = safe_float(truck.get('kmpl'))
            engine_hrs = time_to_hours(truck.get('engine_hours'))

            badge_class, kmpl_display, is_anomaly = get_mileage_badge(kmpl, fuel)

            rank_display = ["🥇 1", "🥈 2", "🥉 3", "4", "5"][i] if i < 5 else str(i + 1)

            top_performers.append({
                "rank": i + 1,
                "rank_display": rank_display,
                "vehicle": safe_str(truck.get('vehicle_desc')),
                "distance": round(distance, 2),
                "fuel": round(fuel, 1),
                "kmpl": kmpl,
                "kmpl_display": kmpl_display,
                "badge_class": badge_class,
                "engine_hours": format_time_display(truck.get('engine_hours')),
                "is_anomaly": is_anomaly,
                "is_top3": i < 3
            })

        return top_performers

    def _build_idle_analysis(self, today_data: List[Dict], limit: int = 5) -> Dict[str, Any]:
        """Build idle time analysis section."""

        idle_by_truck = []
        total_idle_hours = 0

        for truck in today_data:
            engine_hrs = time_to_hours(truck.get('engine_hours'))
            idle_hrs = time_to_hours(truck.get('idling_engine_hours'))

            if engine_hrs > 0:
                idle_pct = calculate_idle_percentage(engine_hrs, idle_hrs)
                category, css_class = get_idle_category(idle_pct)

                idle_by_truck.append({
                    "vehicle": safe_str(truck.get('vehicle_desc')),
                    "idle_hours": round(idle_hrs, 2),
                    "idle_hours_display": format_time_display(truck.get('idling_engine_hours')),
                    "engine_hours": round(engine_hrs, 2),
                    "idle_pct": round(idle_pct),
                    "category": category,
                    "css_class": css_class,
                    "progress_color": "red" if css_class == "high" else "orange" if css_class == "medium" else "green"
                })

                total_idle_hours += idle_hrs

        # Sort by idle percentage (highest first)
        idle_by_truck.sort(key=lambda x: x['idle_pct'], reverse=True)

        # Calculate fleet average idle percentage
        trucks_with_engine = [t for t in idle_by_truck if t['engine_hours'] > 0]
        avg_idle_pct = sum(t['idle_pct'] for t in trucks_with_engine) / len(trucks_with_engine) if trucks_with_engine else 0

        # Find best performer (lowest idle)
        best_performer = min(idle_by_truck, key=lambda x: x['idle_pct']) if idle_by_truck else None

        return {
            "total_idle_hours": round(total_idle_hours),
            "avg_idle_pct": round(avg_idle_pct),
            "by_truck": idle_by_truck[:limit],
            "all_trucks": idle_by_truck,
            "best_performer": best_performer
        }

    def _build_truck_details(self, today_data: List[Dict]) -> List[Dict]:
        """Build complete truck details for the main table."""

        truck_details = []

        for truck in today_data:
            distance = safe_float(truck.get('distance'))
            fuel_consumed = safe_float(truck.get('fuel_consumed'))
            kmpl = safe_float(truck.get('kmpl'))
            filled = safe_float(truck.get('filled'))
            final_fuel = safe_float(truck.get('final_fuel_level'))

            engine_hrs = time_to_hours(truck.get('engine_hours'))
            motion_hrs = time_to_hours(truck.get('in_motion_engine_hours'))
            idle_hrs = time_to_hours(truck.get('idling_engine_hours'))

            # Calculate idle percentage
            idle_pct = calculate_idle_percentage(engine_hrs, idle_hrs)

            # Get badges and statuses
            mileage_badge, mileage_display, is_mileage_anomaly = get_mileage_badge(kmpl, fuel_consumed)
            idle_badge = get_idle_badge(idle_pct)
            fuel_status, fuel_class, is_fuel_critical = get_fuel_status(final_fuel)
            fuel_gauge_pct = get_fuel_gauge_percentage(final_fuel)

            # Determine row class
            row_class = ""
            if distance > 60:  # Top performers
                row_class = "highlight"
            elif is_mileage_anomaly or (engine_hrs == 0 and distance > 0):
                row_class = "warning"
            elif idle_pct >= 80 or kmpl < 0.5:
                row_class = "danger"

            # Parse max speed
            max_speed = parse_max_speed(truck.get('max_speed'))

            truck_details.append({
                "vehicle": safe_str(truck.get('vehicle_desc')),
                "distance": round(distance, 2),
                "engine_hours": format_time_display(truck.get('engine_hours')),
                "motion_hours": format_time_display(truck.get('in_motion_engine_hours')),
                "idle_hours": format_time_display(truck.get('idling_engine_hours')),
                "idle_pct": round(idle_pct),
                "idle_badge": idle_badge,
                "fuel_consumed": round(fuel_consumed, 1),
                "kmpl": kmpl,
                "mileage_display": mileage_display,
                "mileage_badge": mileage_badge,
                "is_mileage_anomaly": is_mileage_anomaly,
                "max_speed": max_speed,
                "filled": round(filled, 1),
                "final_fuel_level": round(final_fuel, 1),
                "fuel_status": fuel_status,
                "fuel_class": fuel_class,
                "fuel_gauge_pct": round(fuel_gauge_pct),
                "is_fuel_critical": is_fuel_critical,
                "row_class": row_class,
                "has_data": engine_hrs > 0 or fuel_consumed > 0
            })

        return truck_details

    def _build_idle_trucks_list(self, today_data: List[Dict]) -> Dict[str, Any]:
        """Categorize idle/unused trucks."""

        no_data_trucks = []  # Zero engine hours, no telematics
        engine_only_trucks = []  # Engine ran but no movement
        with_fuel_trucks = []  # Parked but has fuel

        for truck in today_data:
            vehicle = safe_str(truck.get('vehicle_desc'))
            distance = safe_float(truck.get('distance'))
            engine_hrs = time_to_hours(truck.get('engine_hours'))
            fuel_consumed = safe_float(truck.get('fuel_consumed'))
            final_fuel = safe_float(truck.get('final_fuel_level'))

            if engine_hrs == 0 and distance == 0:
                no_data_trucks.append({
                    "vehicle": vehicle,
                    "final_fuel": round(final_fuel, 1)
                })
            elif distance == 0 and engine_hrs > 0:
                engine_only_trucks.append({
                    "vehicle": vehicle,
                    "engine_hours": format_time_display(truck.get('engine_hours')),
                    "fuel_consumed": round(fuel_consumed, 1)
                })

        # Find parked trucks with significant fuel
        all_vehicles = set(t.get('vehicle_desc') for t in today_data)
        idle_vehicles = set(t['vehicle'] for t in no_data_trucks)

        for truck in no_data_trucks:
            final_fuel = truck.get('final_fuel', 0)
            if final_fuel > 100:
                with_fuel_trucks.append(truck)

        return {
            "no_data": no_data_trucks,
            "no_data_count": len(no_data_trucks),
            "engine_only": engine_only_trucks,
            "engine_only_count": len(engine_only_trucks),
            "with_fuel": with_fuel_trucks,
            "total_idle": len(no_data_trucks) + len(engine_only_trucks)
        }

    def _build_chart_data(
        self,
        trend_data: List[Dict],
        mtd_by_truck: List[Dict],
        today_data: List[Dict]
    ) -> Dict[str, Any]:
        """Build all chart data structures."""

        # Distance trend chart (last 16 days)
        distance_trend = {
            "labels": [],
            "data": []
        }

        fuel_balance = {
            "labels": [],
            "consumed": [],
            "filled": []
        }

        for day in trend_data:
            trip_date = day.get('tripDate')
            if trip_date:
                if hasattr(trip_date, 'strftime'):
                    label = trip_date.strftime('%b %d')
                else:
                    label = str(trip_date)[-5:]  # Get MM-DD part

                distance_trend["labels"].append(label)
                distance_trend["data"].append(round(safe_float(day.get('total_distance'))))

                fuel_balance["labels"].append(label)
                fuel_balance["consumed"].append(round(safe_float(day.get('total_fuel_consumed'))))
                fuel_balance["filled"].append(round(safe_float(day.get('total_filled'))))

        # Top trucks MTD chart (horizontal bar)
        top_mtd = {
            "labels": [],
            "data": []
        }

        for truck in mtd_by_truck[:10]:  # Top 10
            top_mtd["labels"].append(safe_str(truck.get('vehicle_desc')))
            top_mtd["data"].append(round(safe_float(truck.get('mtd_distance'))))

        # Mileage performance chart (today's active trucks)
        mileage_chart = {
            "labels": [],
            "data": []
        }

        # Sort by mileage for the chart
        active_today = [t for t in today_data if safe_float(t.get('fuel_consumed')) > MIN_VALID_FUEL_CONSUMED]
        sorted_by_mileage = sorted(active_today, key=lambda x: safe_float(x.get('kmpl')), reverse=True)

        for truck in sorted_by_mileage[:15]:  # Top 15 for readability
            kmpl = safe_float(truck.get('kmpl'))
            if kmpl <= MAX_VALID_KMPL:  # Exclude anomalies
                mileage_chart["labels"].append(safe_str(truck.get('vehicle_desc')))
                mileage_chart["data"].append(round(kmpl, 2))

        return {
            "distance_trend": distance_trend,
            "fuel_balance": fuel_balance,
            "top_mtd": top_mtd,
            "mileage": mileage_chart
        }

    def _build_alerts(self, today_data: List[Dict]) -> Dict[str, Any]:
        """Build alerts for critical issues."""

        low_fuel_trucks = []
        sensor_issues = []
        high_idle_trucks = []
        poor_mileage = []

        for truck in today_data:
            vehicle = safe_str(truck.get('vehicle_desc'))
            final_fuel = safe_float(truck.get('final_fuel_level'))
            fuel_consumed = safe_float(truck.get('fuel_consumed'))
            kmpl = safe_float(truck.get('kmpl'))
            distance = safe_float(truck.get('distance'))
            engine_hrs = time_to_hours(truck.get('engine_hours'))
            idle_hrs = time_to_hours(truck.get('idling_engine_hours'))

            # Low fuel alert
            if 0 < final_fuel < FUEL_LEVEL_THRESHOLDS["medium"]:
                low_fuel_trucks.append({
                    "vehicle": vehicle,
                    "fuel_level": round(final_fuel, 1)
                })

            # Sensor issues
            if kmpl > MAX_VALID_KMPL:
                sensor_issues.append({
                    "vehicle": vehicle,
                    "issue": f"Impossible mileage: {kmpl:.1f} KMPL",
                    "type": "mileage_sensor"
                })
            elif distance > 0 and fuel_consumed == 0:
                sensor_issues.append({
                    "vehicle": vehicle,
                    "issue": "Movement without fuel consumption",
                    "type": "fuel_sensor"
                })
            elif engine_hrs == 0 and distance > 0:
                sensor_issues.append({
                    "vehicle": vehicle,
                    "issue": "Distance without engine hours",
                    "type": "engine_sensor"
                })

            # High idle
            if engine_hrs > 0:
                idle_pct = calculate_idle_percentage(engine_hrs, idle_hrs)
                if idle_pct >= 80:
                    high_idle_trucks.append({
                        "vehicle": vehicle,
                        "idle_pct": round(idle_pct),
                        "idle_hours": format_time_display(truck.get('idling_engine_hours'))
                    })

            # Poor mileage (but valid)
            if 0 < kmpl < MILEAGE_THRESHOLDS["poor"] and kmpl <= MAX_VALID_KMPL:
                poor_mileage.append({
                    "vehicle": vehicle,
                    "kmpl": round(kmpl, 2)
                })

        return {
            "low_fuel": sorted(low_fuel_trucks, key=lambda x: x['fuel_level']),
            "low_fuel_count": len(low_fuel_trucks),
            "sensor_issues": sensor_issues,
            "sensor_issues_count": len(sensor_issues),
            "high_idle": sorted(high_idle_trucks, key=lambda x: x['idle_pct'], reverse=True),
            "high_idle_count": len(high_idle_trucks),
            "poor_mileage": sorted(poor_mileage, key=lambda x: x['kmpl']),
            "poor_mileage_count": len(poor_mileage)
        }

    # ========================================================================
    # NEW RANGE-SPECIFIC HELPER METHODS
    # ========================================================================

    def _query_range_data(self, start_date: str, end_date: str) -> List[Dict]:
        """Query all truck data for date range."""
        try:
            sql = f"""
                SELECT
                    slNo, tripDate, vehicle_desc, engine_hours,
                    in_motion_engine_hours, idling_engine_hours,
                    avg_speed, max_speed, distance, fuel_consumed,
                    initial_fuel_level, final_fuel_level, kmpl
                FROM truck_reports
                WHERE tripDate BETWEEN '{start_date}' AND '{end_date}'
                ORDER BY tripDate, vehicle_desc
            """
            result = self.mcp.query(sql=sql)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} truck records for range")
                return result["data"]
            else:
                logger.error(f"Range query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying range data: {e}", exc_info=True)
            return []

    def _build_period_kpis(self, range_data: List[Dict]) -> Dict[str, Any]:
        """Build period KPIs (aggregated across range)."""
        if not range_data:
            return {}

        total_distance = sum(safe_float(t.get('distance')) for t in range_data)
        total_fuel = sum(safe_float(t.get('fuel_consumed')) for t in range_data)
        total_engine_hrs = sum(time_to_hours(t.get('engine_hours')) for t in range_data)
        total_idle_hrs = sum(time_to_hours(t.get('idling_engine_hours')) for t in range_data)

        avg_kmpl = total_distance / total_fuel if total_fuel > 0 else 0
        avg_idle_pct = (total_idle_hrs / total_engine_hrs * 100) if total_engine_hrs > 0 else 0
        active_trucks = len(set(t.get('vehicle_desc') for t in range_data if t.get('vehicle_desc')))

        return {
            "total_distance": {"value": round(total_distance), "unit": "KM"},
            "total_fuel": {"value": round(total_fuel, 1), "unit": "L"},
            "avg_kmpl": {"value": round(avg_kmpl, 2), "unit": "KMPL"},
            "total_engine_hours": {"value": round(total_engine_hrs), "unit": "Hrs"},
            "total_idle_hours": {"value": round(total_idle_hrs), "unit": "Hrs"},
            "avg_idle_pct": {"value": round(avg_idle_pct, 1), "unit": "%"},
            "active_trucks": {"value": active_trucks, "unit": "Trucks"},
        }

    def _build_period_summary(self, range_data: List[Dict]) -> Dict[str, Any]:
        """Build period summary (simplified)."""
        return self._build_period_kpis(range_data)

    def _build_top_performers_range(self, range_data: List[Dict]) -> List[Dict]:
        """Build top performers for range (aggregate by truck)."""
        from collections import defaultdict

        truck_totals = defaultdict(lambda: {"distance": 0, "fuel": 0})

        for record in range_data:
            vehicle = safe_str(record.get('vehicle_desc'))
            truck_totals[vehicle]["distance"] += safe_float(record.get('distance'))
            truck_totals[vehicle]["fuel"] += safe_float(record.get('fuel_consumed'))

        # Build list with KMPL
        trucks = []
        for vehicle, data in truck_totals.items():
            kmpl = data["distance"] / data["fuel"] if data["fuel"] > 0 else 0
            trucks.append({
                "vehicle": vehicle,
                "distance": round(data["distance"]),
                "fuel_consumed": round(data["fuel"], 1),
                "kmpl": round(kmpl, 2)
            })

        # Sort by distance and take top 5
        trucks.sort(key=lambda x: x["distance"], reverse=True)
        return trucks[:5]

    def _build_truck_details_range(self, range_data: List[Dict]) -> List[Dict]:
        """Build aggregated truck details for range."""
        from collections import defaultdict

        truck_data = defaultdict(lambda: {
            "distance": 0, "fuel": 0, "engine_hrs": 0, "idle_hrs": 0
        })

        for record in range_data:
            vehicle = safe_str(record.get('vehicle_desc'))
            truck_data[vehicle]["distance"] += safe_float(record.get('distance'))
            truck_data[vehicle]["fuel"] += safe_float(record.get('fuel_consumed'))
            truck_data[vehicle]["engine_hrs"] += time_to_hours(record.get('engine_hours'))
            truck_data[vehicle]["idle_hrs"] += time_to_hours(record.get('idling_engine_hours'))

        # Build output list
        result = []
        for vehicle, data in sorted(truck_data.items()):
            engine_hrs = data["engine_hrs"]
            idle_hrs = data["idle_hrs"]
            idle_pct = calculate_idle_percentage(engine_hrs, idle_hrs)
            kmpl = data["distance"] / data["fuel"] if data["fuel"] > 0 else 0

            result.append({
                "vehicle": vehicle,
                "distance": round(data["distance"]),
                "fuel_consumed": round(data["fuel"], 1),
                "kmpl": round(kmpl, 2),
                "engine_hours": hours_to_time_str(engine_hrs),
                "idle_hours": hours_to_time_str(idle_hrs),
                "idle_pct": round(idle_pct, 1),
            })

        return result

    def _build_chart_data_range(self, range_data: List[Dict], start_date: str, end_date: str) -> Dict[str, Any]:
        """Build chart data for range."""
        # Simplified - just return empty structure
        return {
            "daily_distance": {"labels": [], "data": []},
            "daily_fuel": {"labels": [], "data": []},
            "truck_comparison": {"labels": [], "data": []},
        }

    def _build_alerts_range(self, range_data: List[Dict]) -> Dict[str, Any]:
        """Build alerts for range (simplified)."""
        return {
            "low_fuel_trucks": [],
            "sensor_issues": [],
            "high_idle_trucks": [],
            "poor_mileage": [],
        }


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def process_automobile_data(mcp_client, date: str) -> Dict[str, Any]:
    """
    Convenience function to process automobile data for a date.

    Args:
        mcp_client: MCP client instance
        date: Date string (YYYY-MM-DD)

    Returns:
        Analysis data dictionary
    """
    processor = AutomobileDataProcessor(mcp_client)
    return processor.process_date(date)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['AutomobileDataProcessor', 'process_automobile_data']


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test module load"""
    print("Automobile Formatter module loaded successfully")
    print("=" * 60)
    print("Use AutomobileDataProcessor(mcp_client).process_date('YYYY-MM-DD')")
    print("=" * 60)
    print(f"Fleet Size: {TOTAL_FLEET_SIZE} trucks")
    print(f"Table: truck_reports")
    print(f"Database: balcorpdb")
    print()
    print("Sections produced:")
    print("  - kpis: Daily KPI metrics (8 cards)")
    print("  - mtd: Month-to-date summary (6 cards)")
    print("  - top_performers: Top 5 trucks by distance")
    print("  - idle_analysis: Idle time breakdown")
    print("  - truck_details: Complete truck table data")
    print("  - idle_trucks: Categorized idle trucks")
    print("  - charts: Data for 4 Chart.js charts")
    print("  - alerts: Critical alerts (low fuel, sensors, etc.)")