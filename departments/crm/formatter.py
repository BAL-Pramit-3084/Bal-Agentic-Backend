"""
crm_formatter.py
================
Data processor for CRM / Sales & Distribution Department.

This processor:
1. Queries sd_sales_order (sales orders by date)
2. Queries sd_sales_status (invoices/billing by date)
3. Queries sd_outbound_delivery (deliveries by date)
4. Queries sd_inquiry (customer inquiries by date)
5. Queries sd_contract (contracts - no date filter, check pending)
6. Queries kpi_marketing_business_plan (monthly targets)
7. Queries kpi_marketing_customer_survey_report (customer satisfaction)
8. Calculates TD (Today) and MTD (Month-to-Date) metrics
9. Builds analysisData structure matching the template
10. Handles NULL values gracefully

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
        return int(value)
    except (ValueError, TypeError):
        return default


def format_currency_cr(value: float) -> str:
    """Format value in Crores (₹X.XX Cr)."""
    if value >= 10000000:
        return f"₹{value/10000000:.2f} Cr"
    elif value >= 100000:
        return f"₹{value/100000:.2f} L"
    else:
        return f"₹{value:,.0f}"


def format_currency_lakhs(value: float) -> str:
    """Format value in Lakhs."""
    return f"₹{value/100000:.2f} L"


def format_number(value: float, decimals: int = 0) -> str:
    """Format number with commas."""
    if decimals == 0:
        return f"{value:,.0f}"
    return f"{value:,.{decimals}f}"


def get_financial_year(date_obj: datetime) -> str:
    """Get financial year string like '2024-2025' from date."""
    if date_obj.month >= 4:
        return f"{date_obj.year}-{date_obj.year + 1}"
    else:
        return f"{date_obj.year - 1}-{date_obj.year}"


def get_month_year_abbrev(date_obj: datetime) -> str:
    """Get month-year string like 'NOV-2025'."""
    return f"{MONTH_ABBREV[date_obj.month]}-{date_obj.year}"


# ============================================================================
# CRM DATA PROCESSOR CLASS
# ============================================================================

class CRMDataProcessor:
    """
    Process CRM/Sales & Distribution data for dashboard generation.
    """

    def __init__(self, mcp_client):
        """
        Initialize with MCP client for database queries.

        Args:
            mcp_client: MCP client instance with query() method
        """
        self.mcp = mcp_client
        logger.info("CRM Data Processor initialized")

    def process_date(self, date: str) -> Dict[str, Any]:
        """
        Main entry point: Process all CRM data for a specific date.

        Args:
            date: Date string in YYYY-MM-DD format

        Returns:
            Dictionary matching template's analysisData structure
        """
        logger.info(f"Processing CRM data for date: {date}")

        # Parse date
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        month_start = date_obj.replace(day=1).strftime('%Y-%m-%d')
        month_name = MONTH_NAMES[date_obj.month]
        day_name = DAY_NAMES[date_obj.weekday()]
        financial_year = get_financial_year(date_obj)
        month_year_abbrev = get_month_year_abbrev(date_obj)

        # Query all data sources
        # TD (Today) queries
        sales_orders_td = self._query_sales_orders(date, date)
        billing_td = self._query_billing(date, date)
        deliveries_td = self._query_deliveries(date, date)
        inquiries_td = self._query_inquiries(date, date)

        # MTD (Month-to-Date) queries
        sales_orders_mtd = self._query_sales_orders(month_start, date)
        billing_mtd = self._query_billing(month_start, date)
        deliveries_mtd = self._query_deliveries(month_start, date)

        # Static/Period queries
        customer_survey_data, survey_fy = self._query_customer_survey()
        business_plan = self._query_business_plan(month_year_abbrev)
        contracts = self._query_contracts()

        # Build analysisData structure
        analysis_data = {
            "date": date,
            "date_formatted": f"{day_name}, {month_name} {date_obj.day}, {date_obj.year}",
            "day": date_obj.day,
            "month": month_name,
            "year": date_obj.year,
            "day_name": day_name,
            "financial_year": financial_year,
            "survey_financial_year": survey_fy,  # FY of actual survey data

            # Sales Orders
            "sales_orders": self._build_sales_orders_section(sales_orders_td, sales_orders_mtd),

            # Billing/Invoices
            "billing": self._build_billing_section(billing_td, billing_mtd),

            # Deliveries
            "deliveries": self._build_deliveries_section(deliveries_td, deliveries_mtd),

            # Inquiries
            "inquiries": self._build_inquiries_section(inquiries_td),

            # Customer Survey
            "customer_survey": self._build_survey_section(customer_survey_data),

            # Business Plan
            "business_plan": self._build_business_plan_section(business_plan),

            # Contracts
            "contracts": self._build_contracts_section(contracts),

            # Daily Highlights (computed)
            "highlights": self._build_highlights(
                sales_orders_td, billing_td, deliveries_td
            )
        }

        # Check if we have any data
        has_data = self._check_has_data(analysis_data)
        analysis_data["has_data"] = has_data

        logger.info(f"CRM data processing complete. Has data: {has_data}")
        return analysis_data

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def _query_sales_orders(self, start_date: str, end_date: str) -> List[Dict]:
        """Query sd_sales_order table for date range."""
        query = f"""
            SELECT
                SO_NO, SO_DATE, SOLD_TO_PARTY, SOLD_TO_PARTY_NAME,
                MATERIAL, MATERIAL_DESC, ORDER_QUANTITY, SALES_UNIT,
                NET_PRICE, NET_VALUE, NET_VALUE_INR, DOCUMENT_CURRENCY,
                SIPPING_PLANT, SIPPING_PLANT_NAME, DIST_CHANNEL, DIST_CHANNEL_NAME,
                REGION, COUNTRY, ZONE, DIVISION_NAME
            FROM sd_sales_order
            WHERE SO_DATE >= '{start_date}' AND SO_DATE <= '{end_date}'
            ORDER BY NET_VALUE_INR DESC
        """
        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} sales order records")
                return result["data"]
            else:
                logger.error(f"Sales order query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying sales orders: {e}", exc_info=True)
            return []

    def _query_billing(self, start_date: str, end_date: str) -> List[Dict]:
        """Query sd_sales_status table for billing/invoice data."""
        query = f"""
            SELECT
                BILLING_DOC_NO, BILLING_ITEM, INV_CREATED_ON,
                CUSTOMER_NAME, SOLD_TO_PARTY, CONTRACT_NO, ORDER_NO,
                MATERIAL_NO, MATERIAL_DESC, DELIVERY_NO, DELIVERY_DATE,
                NET_WEIGHT, INV_AMT, INV_USD, RATE_MT,
                DEST_COUNTRY, DIST_CHANNEL, ZGROUP,
                IGST_AMT, CGST_AMT, SGST_AMT, VEHICLE_NO, TRANSPORTER
            FROM sd_sales_status
            WHERE INV_CREATED_ON >= '{start_date}' AND INV_CREATED_ON <= '{end_date}'
            ORDER BY INV_AMT DESC
        """
        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} billing records")
                return result["data"]
            else:
                logger.error(f"Billing query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying billing: {e}", exc_info=True)
            return []

    def _query_deliveries(self, start_date: str, end_date: str) -> List[Dict]:
        """Query sd_outbound_delivery table for delivery data."""
        query = f"""
            SELECT
                DELIVERY_NO, DELIVERY_ITEM, GOODS_ISSUE_DT, DELIVERY_DATE,
                SHIP_PARTY, SHIP_PARTY_NAME, SOLD_PARTY, SOLD_PARTY_NAME,
                MATERIAL_NO, DELIVERY_TYPE, NET_WEIGHT, TOTAL_WEIGHT,
                SHIP_PARTY_LOCA, SOLD_PARTY_LOCA, GOODS_MNT_STATUS
            FROM sd_outbound_delivery
            WHERE GOODS_ISSUE_DT >= '{start_date}' AND GOODS_ISSUE_DT <= '{end_date}'
            ORDER BY DELIVERY_NO
        """
        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} delivery records")
                return result["data"]
            else:
                logger.error(f"Delivery query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying deliveries: {e}", exc_info=True)
            return []

    def _query_inquiries(self, start_date: str, end_date: str) -> List[Dict]:
        """Query sd_inquiry table for customer inquiries."""
        query = f"""
            SELECT
                INQUIRY_NO, DOC_CATEGORY, DOCUMENT_DATE,
                CUSTOMER_NO, CUSTOMER_NAME, MATERIAL_NO, MATERIAL_DESC,
                SEGMENT, INQ_QTY, PRICE, PLANT, PLANT_NAME,
                DELIVER_QTY, PENDING_QTY
            FROM sd_inquiry
            WHERE DOCUMENT_DATE >= '{start_date}' AND DOCUMENT_DATE <= '{end_date}'
            ORDER BY DOCUMENT_DATE DESC
        """
        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} inquiry records")
                return result["data"]
            else:
                logger.error(f"Inquiry query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying inquiries: {e}", exc_info=True)
            return []

    def _query_customer_survey(self) -> tuple:
        """Query kpi_marketing_customer_survey_report for customer satisfaction.

        Returns the LATEST available survey data regardless of report date,
        since survey data is annual and may not match current FY.

        Returns:
            tuple: (data_list, financial_year_string)
        """
        # First, get the latest available FY
        fy_query = """
            SELECT DISTINCT FIN_YEAR
            FROM kpi_marketing_customer_survey_report
            ORDER BY FIN_YEAR DESC
            LIMIT 1
        """
        try:
            fy_result = self.mcp.query(sql=fy_query)
            if not fy_result["success"] or not fy_result["data"]:
                logger.warning("No survey data available in database")
                return [], "N/A"

            latest_fy = fy_result["data"][0]["FIN_YEAR"]
            logger.info(f"Using latest survey data from FY: {latest_fy}")

            # Now get the actual survey data
            query = f"""
                SELECT
                    COMPANY_NAME, SEGMENT,
                    PRODUCT_QUALITY, ORDER_EXECUTION, SERVICE_ATTITUDE,
                    PRODUCT_PRICE, RELATIONSHIP_COMPANY, CUSTOMER_LOYALTY,
                    BUSINESS_SYSTEM, COMPANY_REPUTATION, CUSTOMER_AVG_RATING
                FROM kpi_marketing_customer_survey_report
                WHERE FIN_YEAR = '{latest_fy}'
                ORDER BY CUSTOMER_AVG_RATING DESC
            """
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} survey records")
                return result["data"], latest_fy
            else:
                logger.error(f"Survey query failed: {result['error']}")
                return [], latest_fy
        except Exception as e:
            logger.error(f"Error querying survey: {e}", exc_info=True)
            return [], "N/A"

    def _query_business_plan(self, month_year: str) -> List[Dict]:
        """Query kpi_marketing_business_plan for monthly targets."""
        query = f"""
            SELECT
                customer, plant, channel, segment, oem_trad, kam,
                contract_no, order_qty_mt, target_price, dispatch_target_mt
            FROM kpi_marketing_business_plan
            WHERE month_year = '{month_year}'
            ORDER BY dispatch_target_mt DESC
        """
        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} business plan records")
                return result["data"]
            else:
                logger.error(f"Business plan query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying business plan: {e}", exc_info=True)
            return []

    def _query_contracts(self) -> List[Dict]:
        """Query sd_contract for active contracts."""
        query = """
            SELECT
                CONTRACT_NO, INQUIRY_NO, DOCUMENT_DATE,
                CUSTOMER_NO, CUSTOMER_NAME, MATERIAL_NO, MATERIAL_DESC,
                SEGMENT, CON_QTY, PRICE, PLANT, PLANT_NAME,
                DELIVER_QTY, PENDING_QTY
            FROM sd_contract
            ORDER BY DOCUMENT_DATE DESC
            LIMIT 100
        """
        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} contract records")
                return result["data"]
            else:
                logger.error(f"Contract query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying contracts: {e}", exc_info=True)
            return []

    # ========================================================================
    # BUILD SECTION METHODS
    # ========================================================================

    def _build_sales_orders_section(self, td_data: List[Dict], mtd_data: List[Dict]) -> Dict[str, Any]:
        """Build sales orders section with TD and MTD metrics."""
        # TD metrics
        td_count = len(td_data)
        td_qty = sum(safe_float(r.get('ORDER_QUANTITY')) for r in td_data)
        td_value = sum(safe_float(r.get('NET_VALUE_INR')) for r in td_data)
        td_customers = len(set(r.get('SOLD_TO_PARTY_NAME', '') for r in td_data if r.get('SOLD_TO_PARTY_NAME')))
        td_avg_price = td_value / td_qty if td_qty > 0 else 0

        # MTD metrics
        mtd_count = len(mtd_data)
        mtd_qty = sum(safe_float(r.get('ORDER_QUANTITY')) for r in mtd_data)
        mtd_value = sum(safe_float(r.get('NET_VALUE_INR')) for r in mtd_data)
        mtd_customers = len(set(r.get('SOLD_TO_PARTY_NAME', '') for r in mtd_data if r.get('SOLD_TO_PARTY_NAME')))

        # TD as % of MTD
        td_pct_of_mtd_count = (td_count / mtd_count * 100) if mtd_count > 0 else 0
        td_pct_of_mtd_value = (td_value / mtd_value * 100) if mtd_value > 0 else 0

        # Channel breakdown (TD)
        channel_breakdown = defaultdict(lambda: {"count": 0, "qty": 0, "value": 0})
        for r in td_data:
            channel = r.get('DIST_CHANNEL_NAME', 'Unknown') or 'Unknown'
            channel_breakdown[channel]["count"] += 1
            channel_breakdown[channel]["qty"] += safe_float(r.get('ORDER_QUANTITY'))
            channel_breakdown[channel]["value"] += safe_float(r.get('NET_VALUE_INR'))

        # Customer breakdown (TD)
        customer_breakdown = defaultdict(lambda: {"count": 0, "qty": 0, "value": 0})
        for r in td_data:
            customer = r.get('SOLD_TO_PARTY_NAME', 'Unknown') or 'Unknown'
            customer_breakdown[customer]["count"] += 1
            customer_breakdown[customer]["qty"] += safe_float(r.get('ORDER_QUANTITY'))
            customer_breakdown[customer]["value"] += safe_float(r.get('NET_VALUE_INR'))

        # Sort by value descending
        top_customers = sorted(
            [{"name": k, **v} for k, v in customer_breakdown.items()],
            key=lambda x: x["value"],
            reverse=True
        )[:10]

        # Order details for table
        order_details = []
        for r in td_data[:10]:  # Top 10 orders
            order_details.append({
                "so_no": r.get('SO_NO', ''),
                "customer": r.get('SOLD_TO_PARTY_NAME', '')[:25] if r.get('SOLD_TO_PARTY_NAME') else '',
                "material": r.get('MATERIAL_DESC', '')[:30] if r.get('MATERIAL_DESC') else '',
                "qty": safe_float(r.get('ORDER_QUANTITY')),
                "unit_price": safe_float(r.get('NET_PRICE')),
                "net_value": safe_float(r.get('NET_VALUE_INR')),
                "plant": r.get('SIPPING_PLANT_NAME', '')[:15] if r.get('SIPPING_PLANT_NAME') else '',
                "channel": r.get('DIST_CHANNEL_NAME', '') or 'Unknown',
                "region": r.get('REGION', '') or '',
            })

        return {
            "td": {
                "count": td_count,
                "qty": td_qty,
                "value": td_value,
                "value_formatted": format_currency_cr(td_value),
                "customers": td_customers,
                "avg_price": td_avg_price,
                "avg_price_formatted": format_currency_lakhs(td_avg_price) if td_avg_price > 0 else "₹0",
                "avg_order_value": td_value / td_count if td_count > 0 else 0,
            },
            "mtd": {
                "count": mtd_count,
                "qty": mtd_qty,
                "value": mtd_value,
                "value_formatted": format_currency_cr(mtd_value),
                "customers": mtd_customers,
            },
            "td_pct_of_mtd": {
                "count": td_pct_of_mtd_count,
                "value": td_pct_of_mtd_value,
            },
            "by_channel": dict(channel_breakdown),
            "top_customers": top_customers,
            "order_details": order_details,
        }

    def _build_billing_section(self, td_data: List[Dict], mtd_data: List[Dict]) -> Dict[str, Any]:
        """Build billing/invoice section with TD and MTD metrics."""
        # TD metrics
        td_invoice_count = len(set(r.get('BILLING_DOC_NO', '') for r in td_data if r.get('BILLING_DOC_NO')))
        td_line_items = len(td_data)
        td_weight = sum(safe_float(r.get('NET_WEIGHT')) for r in td_data)
        td_value = sum(safe_float(r.get('INV_AMT')) for r in td_data)
        td_customers = len(set(r.get('CUSTOMER_NAME', '') for r in td_data if r.get('CUSTOMER_NAME')))
        td_avg_rate = td_value / td_weight if td_weight > 0 else 0

        # GST breakdown
        td_igst = sum(safe_float(r.get('IGST_AMT')) for r in td_data)
        td_cgst = sum(safe_float(r.get('CGST_AMT')) for r in td_data)
        td_sgst = sum(safe_float(r.get('SGST_AMT')) for r in td_data)
        td_total_gst = td_igst + td_cgst + td_sgst

        # MTD metrics
        mtd_invoice_count = len(set(r.get('BILLING_DOC_NO', '') for r in mtd_data if r.get('BILLING_DOC_NO')))
        mtd_line_items = len(mtd_data)
        mtd_weight = sum(safe_float(r.get('NET_WEIGHT')) for r in mtd_data)
        mtd_value = sum(safe_float(r.get('INV_AMT')) for r in mtd_data)
        mtd_customers = len(set(r.get('CUSTOMER_NAME', '') for r in mtd_data if r.get('CUSTOMER_NAME')))

        # TD as % of MTD
        td_pct_of_mtd_invoices = (td_invoice_count / mtd_invoice_count * 100) if mtd_invoice_count > 0 else 0
        td_pct_of_mtd_value = (td_value / mtd_value * 100) if mtd_value > 0 else 0

        # Export vs Domestic (TD) - based on DEST_COUNTRY
        export_value = sum(safe_float(r.get('INV_AMT')) for r in td_data
                          if r.get('DEST_COUNTRY') and r.get('DEST_COUNTRY') != '')
        domestic_value = td_value - export_value
        export_pct = (export_value / td_value * 100) if td_value > 0 else 0
        domestic_pct = 100 - export_pct

        # Export USD value
        export_usd = sum(safe_float(r.get('INV_USD')) for r in td_data
                        if r.get('DEST_COUNTRY') and r.get('DEST_COUNTRY') != '')

        # Customer breakdown (TD)
        customer_billing = defaultdict(lambda: {"invoices": set(), "weight": 0, "value": 0})
        for r in td_data:
            customer = r.get('CUSTOMER_NAME', 'Unknown') or 'Unknown'
            customer_billing[customer]["invoices"].add(r.get('BILLING_DOC_NO', ''))
            customer_billing[customer]["weight"] += safe_float(r.get('NET_WEIGHT'))
            customer_billing[customer]["value"] += safe_float(r.get('INV_AMT'))

        # Convert sets to counts and calculate rate
        top_billed_customers = []
        for name, data in customer_billing.items():
            invoice_count = len(data["invoices"])
            weight = data["weight"]
            value = data["value"]
            rate = value / weight if weight > 0 else 0
            pct_revenue = (value / td_value * 100) if td_value > 0 else 0
            top_billed_customers.append({
                "name": name[:30],
                "invoices": invoice_count,
                "weight": weight,
                "value": value,
                "rate": rate,
                "pct_revenue": pct_revenue,
            })

        top_billed_customers.sort(key=lambda x: x["value"], reverse=True)
        top_billed_customers = top_billed_customers[:10]

        # Geographic breakdown
        geo_breakdown = defaultdict(lambda: {"invoices": 0, "value": 0, "weight": 0})
        for r in td_data:
            country = r.get('DEST_COUNTRY', '') or 'Domestic'
            if country == '':
                country = 'Domestic'
            geo_breakdown[country]["invoices"] += 1
            geo_breakdown[country]["value"] += safe_float(r.get('INV_AMT'))
            geo_breakdown[country]["weight"] += safe_float(r.get('NET_WEIGHT'))

        return {
            "td": {
                "invoice_count": td_invoice_count,
                "line_items": td_line_items,
                "weight": td_weight,
                "value": td_value,
                "value_formatted": format_currency_cr(td_value),
                "customers": td_customers,
                "avg_rate": td_avg_rate,
                "avg_rate_formatted": format_currency_lakhs(td_avg_rate) if td_avg_rate > 0 else "₹0",
            },
            "mtd": {
                "invoice_count": mtd_invoice_count,
                "line_items": mtd_line_items,
                "weight": mtd_weight,
                "value": mtd_value,
                "value_formatted": format_currency_cr(mtd_value),
                "customers": mtd_customers,
            },
            "td_pct_of_mtd": {
                "invoices": td_pct_of_mtd_invoices,
                "value": td_pct_of_mtd_value,
            },
            "gst": {
                "igst": td_igst,
                "cgst": td_cgst,
                "sgst": td_sgst,
                "total": td_total_gst,
                "total_formatted": format_currency_lakhs(td_total_gst),
            },
            "export_domestic": {
                "export_value": export_value,
                "export_pct": export_pct,
                "export_usd": export_usd,
                "domestic_value": domestic_value,
                "domestic_pct": domestic_pct,
            },
            "top_customers": top_billed_customers,
            "by_geography": dict(geo_breakdown),
        }

    def _build_deliveries_section(self, td_data: List[Dict], mtd_data: List[Dict]) -> Dict[str, Any]:
        """Build deliveries section with TD and MTD metrics."""
        # TD metrics
        td_delivery_count = len(set(r.get('DELIVERY_NO', '') for r in td_data if r.get('DELIVERY_NO')))
        td_weight = sum(safe_float(r.get('NET_WEIGHT')) for r in td_data)
        td_customers = len(set(r.get('SOLD_PARTY_NAME', '') for r in td_data if r.get('SOLD_PARTY_NAME')))
        td_avg_per_delivery = td_weight / td_delivery_count if td_delivery_count > 0 else 0

        # MTD metrics
        mtd_delivery_count = len(set(r.get('DELIVERY_NO', '') for r in mtd_data if r.get('DELIVERY_NO')))
        mtd_weight = sum(safe_float(r.get('NET_WEIGHT')) for r in mtd_data)

        # TD as % of MTD
        td_pct_of_mtd = (td_delivery_count / mtd_delivery_count * 100) if mtd_delivery_count > 0 else 0

        # Customer breakdown
        customer_deliveries = defaultdict(lambda: {"deliveries": set(), "weight": 0})
        for r in td_data:
            customer = r.get('SOLD_PARTY_NAME', 'Unknown') or 'Unknown'
            customer_deliveries[customer]["deliveries"].add(r.get('DELIVERY_NO', ''))
            customer_deliveries[customer]["weight"] += safe_float(r.get('NET_WEIGHT'))

        delivery_by_customer = [
            {"name": k[:30], "count": len(v["deliveries"]), "weight": v["weight"]}
            for k, v in customer_deliveries.items()
        ]
        delivery_by_customer.sort(key=lambda x: x["weight"], reverse=True)

        return {
            "td": {
                "count": td_delivery_count,
                "weight": td_weight,
                "customers": td_customers,
                "avg_per_delivery": td_avg_per_delivery,
            },
            "mtd": {
                "count": mtd_delivery_count,
                "weight": mtd_weight,
            },
            "td_pct_of_mtd": td_pct_of_mtd,
            "by_customer": delivery_by_customer[:10],
        }

    def _build_inquiries_section(self, td_data: List[Dict]) -> Dict[str, Any]:
        """Build inquiries section."""
        inquiry_count = len(td_data)
        total_qty = sum(safe_float(r.get('INQ_QTY')) for r in td_data)
        customers = len(set(r.get('CUSTOMER_NAME', '') for r in td_data if r.get('CUSTOMER_NAME')))

        inquiry_details = []
        for r in td_data[:10]:
            inquiry_details.append({
                "inquiry_no": r.get('INQUIRY_NO', ''),
                "customer": r.get('CUSTOMER_NAME', '')[:25] if r.get('CUSTOMER_NAME') else '',
                "material": r.get('MATERIAL_DESC', '')[:30] if r.get('MATERIAL_DESC') else '',
                "qty": safe_float(r.get('INQ_QTY')),
                "segment": r.get('SEGMENT', ''),
            })

        return {
            "count": inquiry_count,
            "total_qty": total_qty,
            "customers": customers,
            "details": inquiry_details,
        }

    def _build_survey_section(self, data: List[Dict]) -> Dict[str, Any]:
        """Build customer survey/satisfaction section."""
        if not data:
            return {
                "has_data": False,
                "avg_ratings": {},
                "overall_avg": 0,
                "respondents": 0,
            }

        respondents = len(data)

        # Calculate averages
        avg_product_quality = sum(safe_float(r.get('PRODUCT_QUALITY')) for r in data) / respondents
        avg_order_execution = sum(safe_float(r.get('ORDER_EXECUTION')) for r in data) / respondents
        avg_service_attitude = sum(safe_float(r.get('SERVICE_ATTITUDE')) for r in data) / respondents
        avg_product_price = sum(safe_float(r.get('PRODUCT_PRICE')) for r in data) / respondents
        avg_relationship = sum(safe_float(r.get('RELATIONSHIP_COMPANY')) for r in data) / respondents
        avg_loyalty = sum(safe_float(r.get('CUSTOMER_LOYALTY')) for r in data) / respondents
        avg_business_system = sum(safe_float(r.get('BUSINESS_SYSTEM')) for r in data) / respondents
        avg_reputation = sum(safe_float(r.get('COMPANY_REPUTATION')) for r in data) / respondents
        overall_avg = sum(safe_float(r.get('CUSTOMER_AVG_RATING')) for r in data) / respondents

        return {
            "has_data": True,
            "avg_ratings": {
                "product_quality": round(avg_product_quality, 2),
                "order_execution": round(avg_order_execution, 2),
                "service_attitude": round(avg_service_attitude, 2),
                "product_price": round(avg_product_price, 2),
                "relationship": round(avg_relationship, 2),
                "loyalty": round(avg_loyalty, 2),
                "business_system": round(avg_business_system, 2),
                "reputation": round(avg_reputation, 2),
            },
            "overall_avg": round(overall_avg, 2),
            "respondents": respondents,
            # For chart
            "chart_labels": ["Quality", "Execution", "Service", "Price", "Relationship", "Loyalty", "System", "Reputation"],
            "chart_data": [
                round(avg_product_quality, 2),
                round(avg_order_execution, 2),
                round(avg_service_attitude, 2),
                round(avg_product_price, 2),
                round(avg_relationship, 2),
                round(avg_loyalty, 2),
                round(avg_business_system, 2),
                round(avg_reputation, 2),
            ],
        }

    def _build_business_plan_section(self, data: List[Dict]) -> Dict[str, Any]:
        """Build business plan targets section."""
        if not data:
            return {
                "has_data": False,
                "total_target_qty": 0,
                "total_dispatch_target": 0,
                "customers": 0,
            }

        total_order_qty = sum(safe_float(r.get('order_qty_mt')) for r in data)
        total_dispatch_target = sum(safe_float(r.get('dispatch_target_mt')) for r in data)
        customers = len(set(r.get('customer', '') for r in data if r.get('customer')))

        # Channel breakdown
        channel_targets = defaultdict(lambda: {"order_qty": 0, "dispatch_target": 0})
        for r in data:
            channel = r.get('channel', 'Unknown') or 'Unknown'
            channel_targets[channel]["order_qty"] += safe_float(r.get('order_qty_mt'))
            channel_targets[channel]["dispatch_target"] += safe_float(r.get('dispatch_target_mt'))

        return {
            "has_data": True,
            "total_order_qty": total_order_qty,
            "total_dispatch_target": total_dispatch_target,
            "customers": customers,
            "by_channel": dict(channel_targets),
        }

    def _build_contracts_section(self, data: List[Dict]) -> Dict[str, Any]:
        """Build contracts section."""
        total_contracts = len(data)
        total_qty = sum(safe_float(r.get('CON_QTY')) for r in data)
        total_delivered = sum(safe_float(r.get('DELIVER_QTY')) for r in data)
        total_pending = sum(safe_float(r.get('PENDING_QTY')) for r in data)

        # Count contracts with NULL delivery data
        null_delivery_count = sum(1 for r in data if r.get('DELIVER_QTY') is None)

        return {
            "total_contracts": total_contracts,
            "total_qty": total_qty,
            "total_delivered": total_delivered,
            "total_pending": total_pending,
            "null_delivery_count": null_delivery_count,
            "data_quality_issue": null_delivery_count > 0,
        }

    def _build_highlights(self, orders_td: List[Dict], billing_td: List[Dict],
                          deliveries_td: List[Dict]) -> Dict[str, Any]:
        """Build daily highlights for alert banner."""
        # Orders summary
        order_count = len(orders_td)
        order_value = sum(safe_float(r.get('NET_VALUE_INR')) for r in orders_td)
        order_qty = sum(safe_float(r.get('ORDER_QUANTITY')) for r in orders_td)

        # Billing summary
        invoice_count = len(set(r.get('BILLING_DOC_NO', '') for r in billing_td))
        billing_value = sum(safe_float(r.get('INV_AMT')) for r in billing_td)
        billing_weight = sum(safe_float(r.get('NET_WEIGHT')) for r in billing_td)

        # Deliveries summary
        delivery_count = len(set(r.get('DELIVERY_NO', '') for r in deliveries_td))
        delivery_weight = sum(safe_float(r.get('NET_WEIGHT')) for r in deliveries_td)
        delivery_customers = len(set(r.get('SOLD_PARTY_NAME', '') for r in deliveries_td if r.get('SOLD_PARTY_NAME')))

        # Top customer concentration (billing)
        if billing_td:
            customer_values = defaultdict(float)
            for r in billing_td:
                customer = r.get('CUSTOMER_NAME', 'Unknown') or 'Unknown'
                customer_values[customer] += safe_float(r.get('INV_AMT'))

            top_customer = max(customer_values.items(), key=lambda x: x[1])
            top_customer_name = top_customer[0]
            top_customer_pct = (top_customer[1] / billing_value * 100) if billing_value > 0 else 0
        else:
            top_customer_name = "N/A"
            top_customer_pct = 0

        # Channel split (orders)
        export_value = sum(safe_float(r.get('NET_VALUE_INR')) for r in orders_td
                          if r.get('DIST_CHANNEL_NAME') and 'export' in r.get('DIST_CHANNEL_NAME', '').lower())
        export_pct = (export_value / order_value * 100) if order_value > 0 else 0

        return {
            "orders": {
                "count": order_count,
                "value": order_value,
                "value_formatted": format_currency_cr(order_value),
                "qty": order_qty,
            },
            "billing": {
                "count": invoice_count,
                "value": billing_value,
                "value_formatted": format_currency_cr(billing_value),
                "weight": billing_weight,
            },
            "deliveries": {
                "count": delivery_count,
                "weight": delivery_weight,
                "customers": delivery_customers,
            },
            "concentration": {
                "top_customer": top_customer_name[:25],
                "top_customer_pct": round(top_customer_pct, 1),
            },
            "channel_split": {
                "export_pct": round(export_pct, 1),
                "domestic_pct": round(100 - export_pct, 1),
            },
        }

    def _check_has_data(self, analysis_data: Dict) -> bool:
        """Check if we have meaningful data."""
        # Check if any key metrics have data
        has_orders = analysis_data.get('sales_orders', {}).get('td', {}).get('count', 0) > 0
        has_billing = analysis_data.get('billing', {}).get('td', {}).get('invoice_count', 0) > 0
        has_deliveries = analysis_data.get('deliveries', {}).get('td', {}).get('count', 0) > 0

        return has_orders or has_billing or has_deliveries

    # ========================================================================
    # NEW RANGE-SPECIFIC METHODS
    # ========================================================================

    def process_date_range(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        NEW: Process all CRM data for a DATE RANGE.

        Args:
            start_date: Start date string in YYYY-MM-DD format
            end_date: End date string in YYYY-MM-DD format

        Returns:
            Dictionary with period_kpis (aggregated metrics for the entire range)
        """
        logger.info(f"Processing CRM data for range: {start_date} to {end_date}")

        # Parse and validate dates
        start_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_obj = datetime.strptime(end_date, '%Y-%m-%d')

        if start_obj > end_obj:
            raise ValueError("start_date must be before or equal to end_date")

        # Calculate range metadata
        days_in_range = (end_obj - start_obj).days + 1
        start_month_name = MONTH_NAMES[start_obj.month]
        end_month_name = MONTH_NAMES[end_obj.month]
        financial_year = get_financial_year(start_obj)

        # Format date range for display
        if start_obj.year == end_obj.year:
            if start_obj.month == end_obj.month:
                date_range_formatted = f"{start_month_name} {start_obj.day}-{end_obj.day}, {start_obj.year}"
            else:
                date_range_formatted = f"{start_month_name} {start_obj.day} - {end_month_name} {end_obj.day}, {start_obj.year}"
        else:
            date_range_formatted = f"{start_month_name} {start_obj.day}, {start_obj.year} - {end_month_name} {end_obj.day}, {end_obj.year}"

        # Query all data for the range
        sales_orders_range = self._query_sales_orders(start_date, end_date)
        billing_range = self._query_billing(start_date, end_date)
        deliveries_range = self._query_deliveries(start_date, end_date)
        inquiries_range = self._query_inquiries(start_date, end_date)

        # Static/Period queries (same as single date)
        customer_survey_data, survey_fy = self._query_customer_survey()
        month_year_abbrev = get_month_year_abbrev(start_obj)
        business_plan = self._query_business_plan(month_year_abbrev)
        contracts = self._query_contracts()

        # Build analysis data structure (RANGE version)
        analysis_data = {
            "start_date": start_date,
            "end_date": end_date,
            "date_range_formatted": date_range_formatted,
            "days_in_range": days_in_range,
            "year": start_obj.year,
            "month": start_month_name,
            "financial_year": financial_year,
            "survey_financial_year": survey_fy,

            # PERIOD KPIs (aggregated across range)
            "period_kpis": self._build_period_kpis_range(
                sales_orders_range, billing_range, deliveries_range, inquiries_range
            ),

            # Detailed sections (aggregated)
            "sales_orders": self._build_sales_orders_section_range(sales_orders_range),
            "billing": self._build_billing_section_range(billing_range),
            "deliveries": self._build_deliveries_section_range(deliveries_range),
            "inquiries": self._build_inquiries_section_range(inquiries_range),
            "customer_survey": self._build_survey_section(customer_survey_data),
            "business_plan": self._build_business_plan_section(business_plan),
            "contracts": self._build_contracts_section(contracts),
            "highlights": self._build_highlights_range(
                sales_orders_range, billing_range, deliveries_range
            )
        }

        # Check if we have any data
        has_data = len(sales_orders_range) > 0 or len(billing_range) > 0 or len(deliveries_range) > 0
        analysis_data["has_data"] = has_data

        logger.info(f"CRM range processing complete. Has data: {has_data}, Days: {days_in_range}")
        return analysis_data

    # Range aggregation methods
    def _build_period_kpis_range(self, sales_orders: List[Dict], billing: List[Dict],
                                  deliveries: List[Dict], inquiries: List[Dict]) -> Dict[str, Any]:
        """Build period KPIs aggregated across range."""
        # Sales Orders metrics
        so_count = len(set(so.get('SALES_DOC') for so in sales_orders if so.get('SALES_DOC')))
        so_value = sum(safe_float(so.get('NET_VALUE')) for so in sales_orders)
        so_quantity = sum(safe_float(so.get('QUANTITY')) for so in sales_orders)

        # Billing metrics
        invoice_count = len(set(inv.get('BILLING_DOC') for inv in billing if inv.get('BILLING_DOC')))
        billing_value = sum(safe_float(inv.get('NET_VALUE')) for inv in billing)

        # Delivery metrics
        delivery_count = len(set(del_rec.get('DELIVERY') for del_rec in deliveries if del_rec.get('DELIVERY')))
        delivery_quantity = sum(safe_float(del_rec.get('DEL_QTY')) for del_rec in deliveries)

        # Inquiry metrics
        inquiry_count = len(set(inq.get('INQUIRY_NO') for inq in inquiries if inq.get('INQUIRY_NO')))

        return {
            "sales_orders": {
                "count": so_count,
                "value": so_value,
                "quantity": so_quantity,
            },
            "billing": {
                "invoice_count": invoice_count,
                "value": billing_value,
            },
            "deliveries": {
                "count": delivery_count,
                "quantity": delivery_quantity,
            },
            "inquiries": {
                "count": inquiry_count,
            }
        }

    def _build_sales_orders_section_range(self, sales_orders: List[Dict]) -> Dict[str, Any]:
        """Build sales orders section aggregated across range."""
        so_count = len(set(so.get('SALES_DOC') for so in sales_orders if so.get('SALES_DOC')))
        total_value = sum(safe_float(so.get('NET_VALUE')) for so in sales_orders)
        total_quantity = sum(safe_float(so.get('QUANTITY')) for so in sales_orders)

        # Aggregate by customer
        from collections import defaultdict
        customer_data = defaultdict(lambda: {"value": 0, "quantity": 0, "orders": set()})

        for so in sales_orders:
            customer = so.get('SOLD_TO', 'Unknown')
            customer_data[customer]["value"] += safe_float(so.get('NET_VALUE'))
            customer_data[customer]["quantity"] += safe_float(so.get('QUANTITY'))
            so_doc = so.get('SALES_DOC')
            if so_doc:
                customer_data[customer]["orders"].add(so_doc)

        # Build top customers
        top_customers = []
        for customer, data in sorted(customer_data.items(), key=lambda x: x[1]["value"], reverse=True)[:10]:
            top_customers.append({
                "customer": customer,
                "orders": len(data["orders"]),
                "value": data["value"],
                "quantity": round(data["quantity"], 2),
            })

        # Aggregate by product
        product_data = defaultdict(lambda: {"quantity": 0, "value": 0})
        for so in sales_orders:
            product = so.get('MATERIAL_DESC', 'Unknown')
            product_data[product]["quantity"] += safe_float(so.get('QUANTITY'))
            product_data[product]["value"] += safe_float(so.get('NET_VALUE'))

        top_products = []
        for product, data in sorted(product_data.items(), key=lambda x: x[1]["quantity"], reverse=True)[:5]:
            top_products.append({
                "product": product,
                "quantity": round(data["quantity"], 2),
                "value": data["value"],
            })

        return {
            "period": {
                "count": so_count,
                "total_value": total_value,
                "total_quantity": round(total_quantity, 2),
            },
            "top_customers": top_customers,
            "top_products": top_products,
        }

    def _build_billing_section_range(self, billing: List[Dict]) -> Dict[str, Any]:
        """Build billing section aggregated across range."""
        invoice_count = len(set(inv.get('BILLING_DOC') for inv in billing if inv.get('BILLING_DOC')))
        total_value = sum(safe_float(inv.get('NET_VALUE')) for inv in billing)

        # Aggregate by customer
        from collections import defaultdict
        customer_data = defaultdict(lambda: {"value": 0, "invoices": set()})

        for inv in billing:
            customer = inv.get('SOLD_TO', 'Unknown')
            customer_data[customer]["value"] += safe_float(inv.get('NET_VALUE'))
            inv_doc = inv.get('BILLING_DOC')
            if inv_doc:
                customer_data[customer]["invoices"].add(inv_doc)

        top_customers = []
        for customer, data in sorted(customer_data.items(), key=lambda x: x[1]["value"], reverse=True)[:10]:
            top_customers.append({
                "customer": customer,
                "invoices": len(data["invoices"]),
                "value": data["value"],
            })

        return {
            "period": {
                "invoice_count": invoice_count,
                "total_value": total_value,
            },
            "top_customers": top_customers,
        }

    def _build_deliveries_section_range(self, deliveries: List[Dict]) -> Dict[str, Any]:
        """Build deliveries section aggregated across range."""
        delivery_count = len(set(d.get('DELIVERY') for d in deliveries if d.get('DELIVERY')))
        total_quantity = sum(safe_float(d.get('DEL_QTY')) for d in deliveries)

        # Aggregate by customer
        from collections import defaultdict
        customer_data = defaultdict(lambda: {"quantity": 0, "deliveries": set()})

        for d in deliveries:
            customer = d.get('SHIP_TO', 'Unknown')
            customer_data[customer]["quantity"] += safe_float(d.get('DEL_QTY'))
            del_doc = d.get('DELIVERY')
            if del_doc:
                customer_data[customer]["deliveries"].add(del_doc)

        top_customers = []
        for customer, data in sorted(customer_data.items(), key=lambda x: x[1]["quantity"], reverse=True)[:10]:
            top_customers.append({
                "customer": customer,
                "deliveries": len(data["deliveries"]),
                "quantity": round(data["quantity"], 2),
            })

        return {
            "period": {
                "count": delivery_count,
                "total_quantity": round(total_quantity, 2),
            },
            "top_customers": top_customers,
        }

    def _build_inquiries_section_range(self, inquiries: List[Dict]) -> Dict[str, Any]:
        """Build inquiries section aggregated across range."""
        inquiry_count = len(set(inq.get('INQUIRY_NO') for inq in inquiries if inq.get('INQUIRY_NO')))

        # Aggregate by status
        from collections import defaultdict
        status_counts = defaultdict(int)
        for inq in inquiries:
            status = inq.get('STATUS', 'Unknown')
            status_counts[status] += 1

        by_status = []
        for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
            by_status.append({
                "status": status,
                "count": count,
            })

        return {
            "period": {
                "count": inquiry_count,
            },
            "by_status": by_status,
        }

    def _build_highlights_range(self, sales_orders: List[Dict], billing: List[Dict],
                                 deliveries: List[Dict]) -> List[str]:
        """Build highlights for range."""
        highlights = []

        so_count = len(set(so.get('SALES_DOC') for so in sales_orders if so.get('SALES_DOC')))
        so_value = sum(safe_float(so.get('NET_VALUE')) for so in sales_orders)

        if so_count > 0:
            highlights.append(f"{so_count} Sales Orders worth {format_currency_cr(so_value)}")

        invoice_count = len(set(inv.get('BILLING_DOC') for inv in billing if inv.get('BILLING_DOC')))
        billing_value = sum(safe_float(inv.get('NET_VALUE')) for inv in billing)

        if invoice_count > 0:
            highlights.append(f"{invoice_count} Invoices worth {format_currency_cr(billing_value)}")

        delivery_count = len(set(d.get('DELIVERY') for d in deliveries if d.get('DELIVERY')))
        if delivery_count > 0:
            highlights.append(f"{delivery_count} Deliveries completed")

        return highlights if highlights else ["No significant activity in this period"]


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def process_crm_data(mcp_client, date: str) -> Dict[str, Any]:
    """
    Convenience function to process CRM data for a date.

    Args:
        mcp_client: MCP client instance
        date: Date string (YYYY-MM-DD)

    Returns:
        Analysis data dictionary
    """
    processor = CRMDataProcessor(mcp_client)
    return processor.process_date(date)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['CRMDataProcessor', 'process_crm_data']


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test with mock data"""
    print("CRM Formatter module loaded successfully")
    print("Use CRMDataProcessor(mcp_client).process_date('YYYY-MM-DD') to process data")