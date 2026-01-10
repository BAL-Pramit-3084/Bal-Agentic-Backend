"""
furnace_formatter.py
====================
Data processor for Furnace Operations Department.

This processor:
1. Queries kpi_furnace_oper_summary (22 KPIs per furnace)
2. Queries kpi_furnace_tapping_clock (tap-by-tap data)
3. Builds analysisData structure matching the template
4. Handles NULL values gracefully
5. Calculates aggregations (plant totals, averages)

Author: Senior ML Engineer
Date: November 2024
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


# ============================================================================
# KPI MAPPING CONSTANTS
# ============================================================================

# Map KPI_NO to metric names used in analysisData
KPI_MAPPING = {
    1: "avg_load_mw",           # AVG. LOAD (On Time)
    2: "power_consumption_mwh",  # POWER CONSUMPTION - MWH
    3: "production_mt",          # PRODUCTION - MT
    4: "production_rate_pct",    # PRODUCTION RATE (%)
    5: "sp_power_kwh",           # SP.POWER (KwH)
    6: "sp_carbon_kg",           # SP.CARBON (Kg)
    7: "no_of_batch",            # No. of BATCH
    8: "carbon_per_batch",       # CARBON / BATCH
    9: "cr_recovery_pct",        # Cr. RECOVERY (%)
    10: "sp_cr_ore_kg",          # SP. CR. ORE (Kg)
    11: "sp_paste_kg",           # SP.PASTE (Kg)
    12: "sp_flux_kg",            # SP. FLUX (Kg)
    13: "slag_mt",               # SLAG (MT)
    14: "metal_slag_ratio",      # METAL SLAG RATIO
    15: "pct_sio2",              # % SiO2
    16: "pct_cr2o3",             # % Cr2O3
    17: "pct_feo",               # % FeO
    18: "cr_plus_fe",            # Cr+Fe
    19: "pct_cr2o3_in_slag",     # % Cr2O3 in SLAG
    20: "downtime_hours",        # DOWNTIME
    21: "oee_pct",               # OEE
    22: "ope_pct"                # OPE
}

# List of furnaces (excluding PLANT which is aggregated)
FURNACE_LIST = ["I", "II", "III", "IV", "V"]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def safe_float(value: Any, default: float = 0.0) -> Optional[float]:
    """
    Convert value to float, handling NULL/None/Decimal gracefully.

    Args:
        value: Value to convert
        default: Default value if conversion fails or value is NULL

    Returns:
        Float value or None if NULL
    """
    if value is None:
        return None

    if isinstance(value, str) and value.strip().upper() in ['NULL', 'NONE', '']:
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

    if isinstance(value, str) and value.strip().upper() in ['NULL', 'NONE', '']:
        return None

    try:
        if isinstance(value, Decimal):
            return int(value)
        return int(float(value))
    except (ValueError, TypeError):
        logger.warning(f"Could not convert value '{value}' to int, using default {default}")
        return default


# ============================================================================
# FURNACE DATA PROCESSOR CLASS
# ============================================================================

class FurnaceDataProcessor:
    """
    Process furnace operations data for dashboard generation.
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
        Main entry point: Process all furnace data for a specific date.

        Args:
            date: Date string in YYYY-MM-DD format

        Returns:
            Dictionary matching template's analysisData structure
        """
        logger.info(f"Processing furnace data for date: {date}")

        # Query both tables
        kpi_data = self._query_kpi_summary(date)
        tapping_data = self._query_tapping_clock(date)

        # Build analysisData structure
        analysis_data = {
            "date": date,
            "production": self._build_production_section(kpi_data),
            "power": self._build_power_section(kpi_data),
            "recovery": self._build_recovery_section(kpi_data),
            "operational": self._build_operational_section(kpi_data),
            "tapping": self._build_tapping_section(tapping_data),
            "slag": self._build_slag_section(kpi_data)
        }

        # Check if we have any data
        has_data = self._check_has_data(analysis_data)
        analysis_data["has_data"] = has_data

        logger.info(f"Furnace data processing complete. Has data: {has_data}")
        return analysis_data

    def process_date_range(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        NEW: Process furnace data for a DATE RANGE.

        Args:
            start_date: Start date string in YYYY-MM-DD format
            end_date: End date string in YYYY-MM-DD format

        Returns:
            Dictionary with period-aggregated metrics
        """
        from datetime import datetime

        logger.info(f"Processing furnace data for range: {start_date} to {end_date}")

        # Validate dates
        start_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_obj = datetime.strptime(end_date, '%Y-%m-%d')

        if start_obj > end_obj:
            raise ValueError("start_date must be before or equal to end_date")

        days_in_range = (end_obj - start_obj).days + 1

        # Format date range for display
        start_month_name = start_obj.strftime('%B')
        end_month_name = end_obj.strftime('%B')

        if start_obj.year == end_obj.year:
            if start_obj.month == end_obj.month:
                date_range_formatted = f"{start_month_name} {start_obj.day}-{end_obj.day}, {start_obj.year}"
            else:
                date_range_formatted = f"{start_month_name} {start_obj.day} - {end_month_name} {end_obj.day}, {start_obj.year}"
        else:
            date_range_formatted = f"{start_month_name} {start_obj.day}, {start_obj.year} - {end_month_name} {end_obj.day}, {end_obj.year}"

        # Query data for entire range
        kpi_data = self._query_kpi_summary_range(start_date, end_date)
        tapping_data = self._query_tapping_clock_range(start_date, end_date)

        # Build analysis data (aggregated for range)
        analysis_data = {
            "start_date": start_date,
            "end_date": end_date,
            "date_range_formatted": date_range_formatted,
            "days_in_range": days_in_range,
            "year": start_obj.year,
            "production": self._build_production_section_range(kpi_data),
            "power": self._build_power_section_range(kpi_data),
            "recovery": self._build_recovery_section_range(kpi_data),
            "operational": self._build_operational_section_range(kpi_data),
            "tapping": self._build_tapping_section_range(tapping_data),
            "slag": self._build_slag_section_range(kpi_data)
        }

        # Check if we have any data
        has_data = len(kpi_data) > 0 or len(tapping_data) > 0
        analysis_data["has_data"] = has_data

        logger.info(f"Furnace range processing complete. Has data: {has_data}, Days: {days_in_range}")
        return analysis_data

    def _query_kpi_summary(self, date: str) -> List[Dict]:
        """
        Query kpi_furnace_oper_summary table using MCP server.

        Returns list of dicts with keys:
        KPI_DATE, FCE_NO, KPI_NO, KPI_DESC, UOM, TD_PLAN, MTD_PLAN,
        TD_ACTUAL, MTD_ACTUAL, TD_VAR, MTD_VAR
        """
        query = """
            SELECT
                KPI_DATE, FCE_NO, KPI_NO, KPI_DESC, UOM,
                TD_PLAN, MTD_PLAN, TD_ACTUAL, MTD_ACTUAL,
                TD_VAR, MTD_VAR
            FROM kpi_furnace_oper_summary
            WHERE KPI_DATE = %s
            ORDER BY FCE_NO, KPI_NO
        """

        try:
            # Use MCP server's query method
            result = self.mcp.query(sql=query.replace('%s', f"'{date}'"))

            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} KPI records")
                return result["data"]
            else:
                logger.error(f"KPI query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying KPI summary: {e}", exc_info=True)
            return []

    def _query_tapping_clock(self, date: str) -> List[Dict]:
        """
        Query kpi_furnace_tapping_clock table using MCP server.

        Returns list of dicts with tapping data.
        """
        query = """
            SELECT
                KPI_DATE, FCE_NO, TAP_NO, ST_TIME, ED_TIME, DUR,
                TT_INTERVAL, TTI_MWH, SLAG_TEMP, MOULD_TEMP,
                METAL_OUT, SLAG_OUT, REMARKS
            FROM kpi_furnace_tapping_clock
            WHERE KPI_DATE = %s
            ORDER BY FCE_NO, TAP_NO
        """

        try:
            # Use MCP server's query method
            result = self.mcp.query(sql=query.replace('%s', f"'{date}'"))

            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} tapping records")
                return result["data"]
            else:
                logger.error(f"Tapping query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying tapping clock: {e}", exc_info=True)
            return []

    def _query_kpi_summary_range(self, start_date: str, end_date: str) -> List[Dict]:
        """
        NEW: Query kpi_furnace_oper_summary for date range.
        """
        query = f"""
            SELECT
                KPI_DATE, FCE_NO, KPI_NO, KPI_DESC, UOM,
                TD_PLAN, MTD_PLAN, TD_ACTUAL, MTD_ACTUAL,
                TD_VAR, MTD_VAR
            FROM kpi_furnace_oper_summary
            WHERE KPI_DATE BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY KPI_DATE, FCE_NO, KPI_NO
        """

        try:
            logger.info(f"[DEBUG] Querying KPI data: {start_date} to {end_date}")
            result = self.mcp.query(sql=query)

            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} KPI records for range")

                # DEBUG: Log sample of production data (KPI 3)
                prod_samples = [r for r in result['data'] if safe_int(r.get('KPI_NO')) == 3][:10]
                logger.info(f"[DEBUG] Sample production records (KPI 3):")
                for r in prod_samples:
                    logger.info(f"  {r.get('KPI_DATE')} | {r.get('FCE_NO')} | TD={r.get('TD_ACTUAL')} | MTD={r.get('MTD_ACTUAL')}")

                return result["data"]
            else:
                logger.error(f"KPI range query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying KPI summary range: {e}", exc_info=True)
            return []

    def _query_tapping_clock_range(self, start_date: str, end_date: str) -> List[Dict]:
        """
        NEW: Query kpi_furnace_tapping_clock for date range.
        """
        query = f"""
            SELECT
                KPI_DATE, FCE_NO, TAP_NO, ST_TIME, ED_TIME, DUR,
                TT_INTERVAL, TTI_MWH, SLAG_TEMP, MOULD_TEMP,
                METAL_OUT, SLAG_OUT, REMARKS
            FROM kpi_furnace_tapping_clock
            WHERE KPI_DATE BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY KPI_DATE, FCE_NO, TAP_NO
        """

        try:
            result = self.mcp.query(sql=query)

            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} tapping records for range")
                return result["data"]
            else:
                logger.error(f"Tapping range query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying tapping clock range: {e}", exc_info=True)
            return []

    def _get_kpi_value(self, kpi_data: List[Dict], furnace: str, kpi_no: int) -> Dict[str, Optional[float]]:
        """
        Extract a specific KPI value for a furnace.

        Returns:
            {
                'td_plan': float or None,
                'td_actual': float or None,
                'mtd_plan': float or None,
                'mtd_actual': float or None,
                'td_var': float or None,
                'mtd_var': float or None
            }
        """
        # Find matching row
        row = next((r for r in kpi_data if r['FCE_NO'] == furnace and r['KPI_NO'] == kpi_no), None)

        if not row:
            logger.warning(f"KPI {kpi_no} not found for furnace {furnace}")
            return {
                'td_plan': None, 'td_actual': None,
                'mtd_plan': None, 'mtd_actual': None,
                'td_var': None, 'mtd_var': None
            }

        return {
            'td_plan': safe_float(row.get('TD_PLAN')),
            'td_actual': safe_float(row.get('TD_ACTUAL')),
            'mtd_plan': safe_float(row.get('MTD_PLAN')),
            'mtd_actual': safe_float(row.get('MTD_ACTUAL')),
            'td_var': safe_float(row.get('TD_VAR')),
            'mtd_var': safe_float(row.get('MTD_VAR'))
        }

    def _build_production_section(self, kpi_data: List[Dict]) -> Dict[str, Any]:
        """Build production section of analysisData."""
        # Get PLANT totals (KPI 3 = PRODUCTION - MT)
        plant_prod = self._get_kpi_value(kpi_data, "PLANT", 3)

        # Get individual furnaces
        individual_furnaces = []
        for furnace in FURNACE_LIST:
            prod = self._get_kpi_value(kpi_data, furnace, 3)
            rate = self._get_kpi_value(kpi_data, furnace, 4)

            individual_furnaces.append({
                "furnace": furnace,
                "td_plan": prod['td_plan'],
                "td_actual": prod['td_actual'],
                "mtd_plan": prod['mtd_plan'],
                "mtd_actual": prod['mtd_actual'],
                "td_variance": prod['td_var'],
                "mtd_variance": prod['mtd_var'],
                "production_rate_pct": rate['td_actual']
            })

        return {
            "plant_total": {
                "td_plan": plant_prod['td_plan'],
                "td_actual": plant_prod['td_actual'],
                "mtd_plan": plant_prod['mtd_plan'],
                "mtd_actual": plant_prod['mtd_actual'],
                "td_variance": plant_prod['td_var'],
                "mtd_variance": plant_prod['mtd_var']
            },
            "individual_furnaces": individual_furnaces
        }

    def _build_power_section(self, kpi_data: List[Dict]) -> Dict[str, Any]:
        """Build power section of analysisData."""
        # Get PLANT totals (KPI 2 = POWER CONSUMPTION - MWH)
        plant_power = self._get_kpi_value(kpi_data, "PLANT", 2)
        plant_sp_power = self._get_kpi_value(kpi_data, "PLANT", 5)
        plant_load = self._get_kpi_value(kpi_data, "PLANT", 1)

        # Get individual furnaces
        individual_furnaces = []
        for furnace in FURNACE_LIST:
            power = self._get_kpi_value(kpi_data, furnace, 2)
            sp_power = self._get_kpi_value(kpi_data, furnace, 5)
            load = self._get_kpi_value(kpi_data, furnace, 1)

            individual_furnaces.append({
                "furnace": furnace,
                "td_plan": power['td_plan'],
                "td_actual": power['td_actual'],
                "mtd_plan": power['mtd_plan'],
                "mtd_actual": power['mtd_actual'],
                "sp_power_kwh": sp_power['td_actual'],
                "avg_load_mw": load['td_actual']
            })

        return {
            "plant_total": {
                "td_plan": plant_power['td_plan'],
                "td_actual": plant_power['td_actual'],
                "mtd_plan": plant_power['mtd_plan'],
                "mtd_actual": plant_power['mtd_actual'],
                "sp_power_kwh": plant_sp_power['td_actual'],
                "avg_load_mw": plant_load['td_actual']
            },
            "individual_furnaces": individual_furnaces
        }

    def _build_recovery_section(self, kpi_data: List[Dict]) -> Dict[str, Any]:
        """Build recovery section of analysisData."""
        # Calculate plant averages for all recovery metrics
        td_recoveries = []
        mtd_recoveries = []
        sp_cr_ore_values = []
        sp_carbon_values = []

        for furnace in FURNACE_LIST:
            # Get Cr Recovery (KPI 9)
            cr_rec = self._get_kpi_value(kpi_data, furnace, 9)
            if cr_rec['td_actual'] is not None:
                td_recoveries.append(cr_rec['td_actual'])
            if cr_rec['mtd_actual'] is not None:
                mtd_recoveries.append(cr_rec['mtd_actual'])

            # Get SP. CR. ORE (KPI 10)
            sp_cr_ore = self._get_kpi_value(kpi_data, furnace, 10)
            if sp_cr_ore['td_actual'] is not None:
                sp_cr_ore_values.append(sp_cr_ore['td_actual'])

            # Get SP.CARBON (KPI 6)
            sp_carbon = self._get_kpi_value(kpi_data, furnace, 6)
            if sp_carbon['td_actual'] is not None:
                sp_carbon_values.append(sp_carbon['td_actual'])

        # Calculate plant averages
        plant_avg_cr_recovery = sum(td_recoveries) / len(td_recoveries) if td_recoveries else 0
        plant_avg_mtd_cr_recovery = sum(mtd_recoveries) / len(mtd_recoveries) if mtd_recoveries else 0
        plant_avg_sp_cr_ore = sum(sp_cr_ore_values) / len(sp_cr_ore_values) if sp_cr_ore_values else 0
        plant_avg_sp_carbon = sum(sp_carbon_values) / len(sp_carbon_values) if sp_carbon_values else 0

        # Get individual furnaces data
        individual_furnaces = []
        for furnace in FURNACE_LIST:
            cr_rec = self._get_kpi_value(kpi_data, furnace, 9)
            sp_cr_ore = self._get_kpi_value(kpi_data, furnace, 10)
            sp_carbon = self._get_kpi_value(kpi_data, furnace, 6)

            individual_furnaces.append({
                "furnace": furnace,
                "cr_recovery_pct": cr_rec['td_actual'],
                "mtd_cr_recovery_pct": cr_rec['mtd_actual'],
                "sp_cr_ore_kg": sp_cr_ore['td_actual'],
                "sp_carbon_kg": sp_carbon['td_actual']
            })

        return {
            "plant_avg": {
                "cr_recovery_pct": plant_avg_cr_recovery,
                "mtd_cr_recovery_pct": plant_avg_mtd_cr_recovery,
                "sp_cr_ore_kg": plant_avg_sp_cr_ore,
                "sp_carbon_kg": plant_avg_sp_carbon
            },
            "individual_furnaces": individual_furnaces
        }

    def _build_operational_section(self, kpi_data: List[Dict]) -> Dict[str, Any]:
        """Build operational section of analysisData."""
        # Get PLANT metrics
        plant_oee = self._get_kpi_value(kpi_data, "PLANT", 21)
        plant_downtime = self._get_kpi_value(kpi_data, "PLANT", 20)

        # Calculate total batches (KPI 7) across all furnaces
        total_batches = 0
        for furnace in FURNACE_LIST:
            batches = self._get_kpi_value(kpi_data, furnace, 7)
            if batches['td_actual'] is not None:
                total_batches += batches['td_actual']

    # Get individual furnaces
        individual_furnaces = []
        for furnace in FURNACE_LIST:
            oee = self._get_kpi_value(kpi_data, furnace, 21)
            ope = self._get_kpi_value(kpi_data, furnace, 22)
            downtime = self._get_kpi_value(kpi_data, furnace, 20)
            batches = self._get_kpi_value(kpi_data, furnace, 7)  # ✅ NEW: Get batches per furnace

            individual_furnaces.append({
                "furnace": furnace,
                "oee_pct": oee['td_actual'],
                "mtd_oee_pct": oee['mtd_actual'],
                "ope_pct": ope['td_actual'],
                "downtime_hours": downtime['td_actual'],
                "batches": batches['td_actual'] or 0  # ✅ NEW: Added batches property
            })

        return {
            "plant_metrics": {
                "oee_pct": plant_oee['td_actual'],
                "mtd_oee_pct": plant_oee['mtd_actual'],
                "downtime_hours": plant_downtime['td_actual'] or 0,
                "mtd_downtime_hours": plant_downtime['mtd_actual'] or 0,
                "total_batches": total_batches
            },
            "individual_furnaces": individual_furnaces
        }

    def _build_tapping_section(self, tapping_data: List[Dict]) -> Dict[str, Any]:
        """Build tapping section from tapping_clock table."""
    # Group by furnace
        furnace_taps = {f: [] for f in FURNACE_LIST}

        for row in tapping_data:
            furnace = row['FCE_NO']
            if furnace in FURNACE_LIST:
                furnace_taps[furnace].append(row)

    # Calculate stats per furnace
        individual_furnaces = []
        total_taps = 0
        total_tti = 0
        total_metal = 0
        total_slag = 0

        for furnace in FURNACE_LIST:
            taps = furnace_taps[furnace]
            num_taps = len(taps)
            total_taps += num_taps

            if taps:
            # Calculate averages - FILTER OUT None values
                tti_values = [safe_float(t['TTI_MWH'], 0) for t in taps]
                tti_values = [v for v in tti_values if v is not None]  # Remove None values

                slag_temp_values = [safe_float(t['SLAG_TEMP'], 0) for t in taps]
                slag_temp_values = [v for v in slag_temp_values if v is not None]

                mould_temp_values = [safe_float(t['MOULD_TEMP'], 0) for t in taps]
                mould_temp_values = [v for v in mould_temp_values if v is not None]

            # Calculate averages only from actual values
                avg_tti = sum(tti_values) / len(tti_values) if tti_values else 0
                avg_slag_temp = sum(slag_temp_values) / len(slag_temp_values) if slag_temp_values else 0
                avg_mould_temp = sum(mould_temp_values) / len(mould_temp_values) if mould_temp_values else 0

            # Total metal and slag - use 'or 0' to handle None
                metal = sum(safe_float(t['METAL_OUT'], 0) or 0 for t in taps)
                slag = sum(safe_float(t['SLAG_OUT'], 0) or 0 for t in taps)

                total_metal += metal
                total_slag += slag

            # Metal-slag ratio
                metal_slag_ratio = metal / slag if slag > 0 else 0

                total_tti += avg_tti * num_taps

                individual_furnaces.append({
                    "furnace": furnace,
                    "total_taps": num_taps,
                    "avg_tti_mwh": avg_tti,
                    "avg_slag_temp": avg_slag_temp,
                    "avg_mould_temp": avg_mould_temp,
                    "total_metal_out": metal,
                    "total_slag_out": slag,
                    "metal_slag_ratio": metal_slag_ratio
                })
            else:
                individual_furnaces.append({
                    "furnace": furnace,
                    "total_taps": 0,
                    "avg_tti_mwh": 0,
                    "avg_slag_temp": 0,
                    "avg_mould_temp": 0,
                    "total_metal_out": 0,
                    "total_slag_out": 0,
                    "metal_slag_ratio": 0
                })

        avg_tti = total_tti / total_taps if total_taps > 0 else 0

        return {
            "overall_stats": {
                "total_taps": total_taps,
                "avg_tti_mwh": avg_tti,
                "total_metal_out": total_metal,
                "total_slag_out": total_slag
            },
            "individual_furnaces": individual_furnaces
        }

    def _build_slag_section(self, kpi_data: List[Dict]) -> Dict[str, Any]:
        """Build slag section of analysisData."""

    # Calculate plant totals from individual furnaces
        total_slag = 0          # TD total
        total_mtd_slag = 0      # MTD total (NEW)
        metal_slag_ratios = []
        cr2o3_in_slag_values = []

    # Get individual furnaces first
        individual_furnaces = []
        for furnace in FURNACE_LIST:
            slag = self._get_kpi_value(kpi_data, furnace, 13)
            metal_slag = self._get_kpi_value(kpi_data, furnace, 14)
            cr2o3 = self._get_kpi_value(kpi_data, furnace, 16)
            cr2o3_slag = self._get_kpi_value(kpi_data, furnace, 19)

        # Accumulate for plant totals
            if slag['td_actual'] is not None:
                total_slag += slag['td_actual']

        # ✅ NEW: Accumulate MTD slag
            if slag['mtd_actual'] is not None:
                total_mtd_slag += slag['mtd_actual']

            if metal_slag['td_actual'] is not None:
                metal_slag_ratios.append(metal_slag['td_actual'])
            if cr2o3_slag['td_actual'] is not None:
                cr2o3_in_slag_values.append(cr2o3_slag['td_actual'])

            individual_furnaces.append({
                "furnace": furnace,
                "slag_mt": slag['td_actual'],
                "metal_slag_ratio": metal_slag['td_actual'],
                "pct_cr2o3": cr2o3['td_actual'],
                "pct_cr2o3_in_slag": cr2o3_slag['td_actual']
            })

    # Calculate plant averages
        avg_metal_slag_ratio = (
            sum(metal_slag_ratios) / len(metal_slag_ratios)
            if metal_slag_ratios else 0
        )
        avg_cr2o3_in_slag = (
            sum(cr2o3_in_slag_values) / len(cr2o3_in_slag_values)
            if cr2o3_in_slag_values else 0
        )

        return {
            "plant_metrics": {
                "slag_mt": total_slag,                    # TD: Sum of all furnaces
                "metal_slag_ratio": avg_metal_slag_ratio,  # TD: Average across furnaces
                "cr2o3_in_slag_pct": avg_cr2o3_in_slag,   # TD: Average across furnaces
                "mtd_slag_mt": total_mtd_slag             # ✅ NEW: MTD sum
            },
            "individual_furnaces": individual_furnaces
        }

    # ========================================================================
    # NEW RANGE BUILDER METHODS (Aggregate TD_ACTUAL across days)
    # ========================================================================

    def _build_production_section_range(self, kpi_data: List[Dict]) -> Dict[str, Any]:
        """Build production section for date range by aggregating TD_ACTUAL."""
        # KPI 3 = Production (MT), KPI 4 = Production Rate (%)
        result = self._aggregate_section_by_td(kpi_data, [3])  # CORRECT: KPI 3 is production

        # Add production rate data
        for furn in result["individual_furnaces"]:
            furn["production_rate_pct"] = 100.0  # Placeholder

        return result

    def _build_power_section_range(self, kpi_data: List[Dict]) -> Dict[str, Any]:
        """Build power section for date range."""
        # KPI 2 = Power Consumption (MWH) - SUM
        # KPI 5 = Sp. Power (KWH) - AVERAGE (it's a rate)
        # KPI 1 = Avg Load (MW) - AVERAGE (it's already an average)

        result = self._aggregate_section_by_td(kpi_data, [2])  # Power MWH - SUM is correct

        # For Sp. Power and Avg Load, we need AVERAGE not SUM
        sp_power_avg = self._aggregate_averages(kpi_data, [5])
        avg_load_avg = self._aggregate_averages(kpi_data, [1])

        result["plant_total"]["sp_power_kwh"] = sp_power_avg["plant_total"]
        result["plant_total"]["avg_load_mw"] = avg_load_avg["plant_total"]

        for i, furn in enumerate(result["individual_furnaces"]):
            furnace_name = FURNACE_LIST[i]
            furn["sp_power_kwh"] = sp_power_avg["furnaces"].get(furnace_name, 0)
            furn["mtd_sp_power_kwh"] = sp_power_avg["furnaces"].get(furnace_name, 0)
            furn["avg_load_mw"] = avg_load_avg["furnaces"].get(furnace_name, 0)

        return result

    def _build_recovery_section_range(self, kpi_data: List[Dict]) -> Dict[str, Any]:
        """Build recovery section for date range."""
        # KPI 9 = Cr Recovery (%), KPI 10 = Sp Cr Ore (Kg), KPI 6 = Sp Carbon (Kg)
        # Recovery is a PERCENTAGE, so we need to average, not sum
        from collections import defaultdict

        recovery_values = defaultdict(list)
        sp_cr_ore_sum = defaultdict(float)
        sp_carbon_sum = defaultdict(float)

        for row in kpi_data:
            kpi_no = safe_int(row.get('KPI_NO'))
            furnace = row.get('FCE_NO', 'PLANT')
            td_actual = safe_float(row.get('TD_ACTUAL'))

            if kpi_no == 9 and td_actual is not None:  # Cr Recovery %
                recovery_values[furnace].append(td_actual)
            elif kpi_no == 10:  # Sp Cr Ore
                sp_cr_ore_sum[furnace] += td_actual if td_actual else 0
            elif kpi_no == 6:  # Sp Carbon
                sp_carbon_sum[furnace] += td_actual if td_actual else 0

        # Calculate averages
        plant_recovery = sum(recovery_values.get('PLANT', [])) / len(recovery_values.get('PLANT', [1])) if recovery_values.get('PLANT') else 0

        result = {
            "plant_avg": {
                "cr_recovery_pct": plant_recovery,
                "mtd_cr_recovery_pct": plant_recovery,
                "sp_cr_ore_kg": sp_cr_ore_sum.get('PLANT', 0),
                "sp_carbon_kg": sp_carbon_sum.get('PLANT', 0)
            },
            "individual_furnaces": []
        }

        for furnace in FURNACE_LIST:
            furn_recovery = sum(recovery_values.get(furnace, [])) / len(recovery_values.get(furnace, [1])) if recovery_values.get(furnace) else 0
            result["individual_furnaces"].append({
                "furnace": furnace,
                "cr_recovery_pct": furn_recovery,
                "mtd_cr_recovery_pct": furn_recovery,
                "sp_cr_ore_kg": sp_cr_ore_sum.get(furnace, 0),
                "sp_carbon_kg": sp_carbon_sum.get(furnace, 0)
            })

        return result

    def _build_operational_section_range(self, kpi_data: List[Dict]) -> Dict[str, Any]:
        """Build operational section for date range."""
        # KPI 21 = OEE (%), KPI 20 = Downtime (hours), KPI 7 = No of Batch
        downtime_agg = self._aggregate_section_by_td(kpi_data, [20])
        batch_agg = self._aggregate_section_by_td(kpi_data, [7])

        # OEE is percentage - calculate average not sum
        from collections import defaultdict
        oee_values = defaultdict(list)

        for row in kpi_data:
            kpi_no = safe_int(row.get('KPI_NO'))
            if kpi_no == 21:  # OEE %
                furnace = row.get('FCE_NO', 'PLANT')
                td_actual = safe_float(row.get('TD_ACTUAL'))
                if td_actual is not None:
                    oee_values[furnace].append(td_actual)

        plant_oee = sum(oee_values.get('PLANT', [])) / len(oee_values.get('PLANT', [1])) if oee_values.get('PLANT') else 0

        result = {
            "plant_metrics": {
                "oee_pct": plant_oee,
                "mtd_oee_pct": plant_oee,
                "downtime_hours": downtime_agg["plant_total"]["td_actual"],
                "mtd_downtime_hours": downtime_agg["plant_total"]["mtd_actual"],
                "total_batches": int(batch_agg["plant_total"]["td_actual"])
            },
            "individual_furnaces": []
        }

        for i, furnace in enumerate(FURNACE_LIST):
            furn_oee = sum(oee_values.get(furnace, [])) / len(oee_values.get(furnace, [1])) if oee_values.get(furnace) else 0
            result["individual_furnaces"].append({
                "furnace": furnace,
                "oee_pct": furn_oee,
                "mtd_oee_pct": furn_oee,
                "downtime_hours": downtime_agg["individual_furnaces"][i]["td_actual"],
                "mtd_downtime_hours": downtime_agg["individual_furnaces"][i]["mtd_actual"],
                "batches": int(batch_agg["individual_furnaces"][i]["td_actual"])
            })

        return result

    def _build_slag_section_range(self, kpi_data: List[Dict]) -> Dict[str, Any]:
        """Build slag section for date range."""
        # KPI 13 = Slag (MT) - SUM
        # KPI 14 = Metal-Slag Ratio - AVERAGE (it's a ratio)
        # KPI 19 = % Cr2O3 in Slag - AVERAGE (it's a percentage)

        slag_agg = self._aggregate_section_by_td(kpi_data, [13])  # SUM is correct
        ratio_avg = self._aggregate_averages(kpi_data, [14])  # AVERAGE for ratio
        cr2o3_avg = self._aggregate_averages(kpi_data, [19])  # AVERAGE for percentage

        result = {
            "plant_metrics": {
                "slag_mt": slag_agg["plant_total"]["td_actual"],
                "mtd_slag_mt": slag_agg["plant_total"]["mtd_actual"],
                "metal_slag_ratio": ratio_avg["plant_total"],
                "cr2o3_in_slag_pct": cr2o3_avg["plant_total"]
            },
            "individual_furnaces": []
        }

        for i, furnace in enumerate(FURNACE_LIST):
            result["individual_furnaces"].append({
                "furnace": furnace,
                "slag_mt": slag_agg["individual_furnaces"][i]["td_actual"],
                "mtd_slag_mt": slag_agg["individual_furnaces"][i]["mtd_actual"],
                "metal_slag_ratio": ratio_avg["furnaces"].get(furnace, 0),
                "cr2o3_in_slag_pct": cr2o3_avg["furnaces"].get(furnace, 0)
            })

        return result

    def _build_tapping_section_range(self, tapping_data: List[Dict]) -> Dict[str, Any]:
        """Build tapping section for date range."""
        if not tapping_data:
            return {"overall_stats": {}, "individual_furnaces": []}

        # Aggregate all tapping records - filter out None values
        total_taps = len(tapping_data)
        total_tti = sum(v for v in (safe_float(r.get('TTI_MWH')) for r in tapping_data) if v is not None)
        total_metal = sum(v for v in (safe_float(r.get('METAL_OUT')) for r in tapping_data) if v is not None)
        total_slag = sum(v for v in (safe_float(r.get('SLAG_OUT')) for r in tapping_data) if v is not None)

        return {
            "overall_stats": {
                "total_taps": total_taps,
                "avg_tti_mwh": total_tti / total_taps if total_taps > 0 else 0,
                "total_metal_out": total_metal,
                "total_slag_out": total_slag
            },
            "individual_furnaces": []  # Simplified for range
        }

    def _aggregate_averages(self, kpi_data: List[Dict], kpi_numbers: List[int]) -> Dict[str, Any]:
        """
        Helper: Calculate AVERAGE of TD_ACTUAL values across days for rate/percentage metrics.
        Use this for metrics like Sp. Power, Avg Load, Recovery %, OEE %, etc.
        """
        from collections import defaultdict

        values_by_furnace = defaultdict(list)

        for row in kpi_data:
            kpi_no = safe_int(row.get('KPI_NO'))
            if kpi_no not in kpi_numbers:
                continue

            furnace = row.get('FCE_NO', 'PLANT')
            td_actual = safe_float(row.get('TD_ACTUAL'))
            if td_actual is not None:
                values_by_furnace[furnace].append(td_actual)

        # Calculate averages
        plant_avg = (sum(values_by_furnace.get('PLANT', [])) / len(values_by_furnace.get('PLANT', [1]))) if values_by_furnace.get('PLANT') else 0

        furnace_avgs = {}
        for furnace in FURNACE_LIST:
            vals = values_by_furnace.get(furnace, [])
            furnace_avgs[furnace] = (sum(vals) / len(vals)) if vals else 0

        return {
            "plant_total": plant_avg,
            "furnaces": furnace_avgs
        }

    def _aggregate_section_by_td(self, kpi_data: List[Dict], kpi_numbers: List[int]) -> Dict[str, Any]:
        """
        Helper: Aggregate TD_ACTUAL values across all days for given KPI numbers.
        For date ranges, we sum TD_ACTUAL from each day (not MTD_ACTUAL which is cumulative).
        Returns same structure as single-date sections.
        """
        from collections import defaultdict

        # Aggregate by furnace and KPI - sum across all days
        aggregated = defaultdict(lambda: defaultdict(float))
        row_count = 0

        for row in kpi_data:
            kpi_no = safe_int(row.get('KPI_NO'))
            if kpi_no not in kpi_numbers:
                continue

            row_count += 1
            furnace = row.get('FCE_NO', 'PLANT')
            td_actual = safe_float(row.get('TD_ACTUAL'))

            # Debug logging for first few rows
            if row_count <= 10:
                logger.info(f"[AGG DEBUG] Row {row_count}: Date={row.get('KPI_DATE')}, Furnace={furnace}, KPI={kpi_no}, TD_ACTUAL={td_actual}")

            # Sum TD_ACTUAL across all days for this furnace+KPI
            aggregated[furnace][kpi_no] += td_actual

        logger.info(f"[AGG DEBUG] Processed {row_count} rows for KPIs {kpi_numbers}")

        # Build output structure - match single-date format for JS compatibility
        # For PLANT total, sum either the PLANT row OR sum all individual furnaces
        plant_from_plant_row = sum(aggregated.get('PLANT', {}).values())

        # Also calculate by summing all individual furnaces
        plant_from_furnaces = 0
        for furnace in FURNACE_LIST:
            furnace_sum = sum(aggregated.get(furnace, {}).values())
            if furnace_sum > 0:
                logger.info(f"[AGG DEBUG] {furnace}: {furnace_sum}")
            plant_from_furnaces += furnace_sum

        # Use whichever is greater (in case PLANT row doesn't exist or is incomplete)
        plant_total = max(plant_from_plant_row, plant_from_furnaces)

        logger.info(f"[AGG DEBUG] PLANT row sum: {plant_from_plant_row}, Furnaces sum: {plant_from_furnaces}, Final: {plant_total}")

        result = {
            "plant_total": {
                "td_plan": 0,  # Not available for range - use 0 to avoid JS errors
                "td_actual": plant_total,
                "mtd_plan": 0,  # Not available for range
                "mtd_actual": plant_total,  # Use same value for compatibility
                "td_variance": 0,
                "mtd_variance": 0
            },
            "individual_furnaces": []
        }

        for furnace in FURNACE_LIST:
            furnace_total = sum(aggregated.get(furnace, {}).values())
            result["individual_furnaces"].append({
                "furnace": furnace,
                "td_plan": 0,
                "td_actual": furnace_total,
                "mtd_plan": 0,
                "mtd_actual": furnace_total,
                "td_variance": 0,
                "mtd_variance": 0,
                "production_rate_pct": 100.0  # Not available for range - use 100 as placeholder
            })

        return result

    def _check_has_data(self, analysis_data: Dict) -> bool:
        """Check if we have any actual data (not all NULLs)."""
        # Check if plant production has actual value
        prod = analysis_data.get('production', {}).get('plant_total', {})
        if prod.get('td_actual') is not None:
            return True
        if prod.get('period_actual') is not None:  # NEW: For range data
            return True

        # Check if any individual furnace has production
        for f in analysis_data.get('production', {}).get('individual_furnaces', []):
            if f.get('td_actual') is not None:
                return True
            if f.get('period_actual') is not None:  # NEW: For range data
                return True

        return False


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['FurnaceDataProcessor', 'KPI_MAPPING', 'FURNACE_LIST']