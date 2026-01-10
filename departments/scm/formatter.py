"""
scm_formatter.py
================
Data processor for SCM (Supply Chain Management) Dashboard.

Queries two tables:
1. scm_purchase_order - Purchase Order data
2. scm_purchase_requisition - Purchase Requisition data

Produces analysis_data structure for template engine injection.

Author: Senior ML Engineer
Date: November 2025
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from decimal import Decimal
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def safe_float(value, default=0.0) -> float:
    """Safely convert value to float."""
    if value is None:
        return default
    try:
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0) -> int:
    """Safely convert value to int."""
    if value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def format_currency_lakhs(value: float) -> str:
    """Format value in Lakhs (₹ X.XX L)."""
    lakhs = value / 100000
    if lakhs >= 100:
        return f"₹{lakhs/100:.2f} Cr"
    elif lakhs >= 1:
        return f"₹{lakhs:.2f} L"
    else:
        return f"₹{value:,.0f}"


def format_currency_display(value: float) -> Dict[str, Any]:
    """Return value formatted for display with unit."""
    if value >= 10000000:  # >= 1 Crore
        return {"value": round(value / 10000000, 2), "unit": "Cr", "prefix": "₹"}
    elif value >= 100000:  # >= 1 Lakh
        return {"value": round(value / 100000, 2), "unit": "L", "prefix": "₹"}
    else:
        return {"value": round(value, 0), "unit": "", "prefix": "₹"}


# ============================================================================
# SCM DATA PROCESSOR
# ============================================================================

class SCMDataProcessor:
    """
    Process SCM data from Purchase Orders and Purchase Requisitions tables.
    """

    def __init__(self, mcp_server):
        """
        Initialize with MCP server instance.

        Args:
            mcp_server: MCP server instance for database queries
        """
        self.mcp = mcp_server
        logger.info("SCM Data Processor initialized")

    def process_date(self, date: str) -> Dict[str, Any]:
        """
        Process all SCM data for a given date.

        Args:
            date: Date string in YYYY-MM-DD format

        Returns:
            Dictionary with all analysis data for template injection
        """
        logger.info(f"Processing SCM data for date: {date}")

        # Parse date for display
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            month_name = date_obj.strftime('%B')
            year = date_obj.year
            formatted_date = date_obj.strftime('%B %d, %Y')
        except ValueError:
            month_name = "Unknown"
            year = 2025
            formatted_date = date

        # Query all data
        po_summary = self._query_po_summary(date)
        po_by_vendor = self._query_po_by_vendor(date)
        po_by_plant = self._query_po_by_plant(date)
        po_by_category = self._query_po_by_category(date)
        po_details = self._query_po_details(date)
        pr_summary = self._query_pr_summary(date)
        pr_by_status = self._query_pr_by_status(date)
        pr_details = self._query_pr_details(date)

        # Build analysis_data structure
        analysis_data = {
            "date": date,
            "formatted_date": formatted_date,
            "month": month_name,
            "year": year,
            "purchase_orders": self._build_po_section(po_summary, po_by_vendor, po_by_plant, po_by_category, po_details),
            "purchase_requisitions": self._build_pr_section(pr_summary, pr_by_status, pr_details),
            "summary_metrics": self._build_summary_metrics(po_summary, pr_summary),
            "charts": self._build_chart_data(po_by_vendor, po_by_plant, po_by_category),
            "daily_highlights": self._build_daily_highlights(po_summary, pr_summary, po_by_vendor, po_details)
        }

        # Check if we have any data
        has_data = self._check_has_data(analysis_data)
        analysis_data["has_data"] = has_data

        logger.info(f"SCM data processing complete. Has data: {has_data}")
        return analysis_data

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def _query_po_summary(self, date: str) -> Dict[str, Any]:
        """Query Purchase Order summary for the date."""
        query = f"""
            SELECT
                COUNT(DISTINCT PO_NO) as po_count,
                COUNT(*) as line_items,
                COALESCE(SUM(NET_ORDER_VALUE), 0) as total_value,
                COUNT(DISTINCT VENDOR) as vendor_count,
                COUNT(DISTINCT PURCH_GROUP_DESC) as purch_groups,
                COUNT(DISTINCT PLANT) as plant_count,
                COALESCE(SUM(STILL_DEL_QTY), 0) as pending_qty,
                COALESCE(SUM(GR_QTY), 0) as received_qty
            FROM scm_purchase_order
            WHERE PO_DATE = '{date}'
        """

        try:
            result = self.mcp.query(sql=query)
            if result["success"] and result["data"]:
                logger.info(f"PO Summary: {result['data'][0]}")
                return result["data"][0]
            else:
                logger.warning(f"PO summary query returned no data")
                return self._empty_po_summary()
        except Exception as e:
            logger.error(f"Error querying PO summary: {e}", exc_info=True)
            return self._empty_po_summary()

    def _empty_po_summary(self) -> Dict[str, Any]:
        """Return empty PO summary structure."""
        return {
            "po_count": 0,
            "line_items": 0,
            "total_value": 0,
            "vendor_count": 0,
            "purch_groups": 0,
            "plant_count": 0,
            "pending_qty": 0,
            "received_qty": 0
        }

    def _query_po_by_vendor(self, date: str) -> List[Dict]:
        """Query PO breakdown by vendor."""
        query = f"""
            SELECT
                VENDOR_NAME as vendor,
                COUNT(DISTINCT PO_NO) as po_count,
                COUNT(*) as line_items,
                SUM(NET_ORDER_VALUE) as total_value
            FROM scm_purchase_order
            WHERE PO_DATE = '{date}'
            GROUP BY VENDOR_NAME
            ORDER BY total_value DESC
            LIMIT 10
        """

        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} vendor records")
                return result["data"]
            return []
        except Exception as e:
            logger.error(f"Error querying PO by vendor: {e}", exc_info=True)
            return []

    def _query_po_by_plant(self, date: str) -> List[Dict]:
        """Query PO breakdown by plant."""
        query = f"""
            SELECT
                PLANT as plant_code,
                PLANT_NAME as plant,
                COUNT(DISTINCT PO_NO) as po_count,
                COUNT(*) as line_items,
                SUM(NET_ORDER_VALUE) as total_value
            FROM scm_purchase_order
            WHERE PO_DATE = '{date}'
            GROUP BY PLANT, PLANT_NAME
            ORDER BY total_value DESC
        """

        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} plant records")
                return result["data"]
            return []
        except Exception as e:
            logger.error(f"Error querying PO by plant: {e}", exc_info=True)
            return []

    def _query_po_by_category(self, date: str) -> List[Dict]:
        """Query PO breakdown by material category."""
        query = f"""
            SELECT
                MAT_GROUP_DESC as category,
                COUNT(*) as item_count,
                SUM(NET_ORDER_VALUE) as total_value
            FROM scm_purchase_order
            WHERE PO_DATE = '{date}'
            GROUP BY MAT_GROUP_DESC
            ORDER BY total_value DESC
            LIMIT 10
        """

        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} category records")
                return result["data"]
            return []
        except Exception as e:
            logger.error(f"Error querying PO by category: {e}", exc_info=True)
            return []

    def _query_po_details(self, date: str) -> List[Dict]:
        """Query detailed PO line items."""
        query = f"""
            SELECT
                PO_NO,
                ITEM_NO,
                VENDOR_NAME,
                MATERIAL_DESC,
                PLANT_NAME,
                QUANTITY,
                UNIT,
                NET_ORDER_VALUE,
                MAT_GROUP_DESC,
                ORDER_TYPE_DESC,
                STILL_DEL_QTY,
                GR_QTY,
                ITEM_DEL_DATE
            FROM scm_purchase_order
            WHERE PO_DATE = '{date}'
            ORDER BY NET_ORDER_VALUE DESC
            LIMIT 20
        """

        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} PO detail records")
                return result["data"]
            return []
        except Exception as e:
            logger.error(f"Error querying PO details: {e}", exc_info=True)
            return []

    def _query_pr_summary(self, date: str) -> Dict[str, Any]:
        """Query Purchase Requisition summary for the date."""
        query = f"""
            SELECT
                COUNT(DISTINCT PR_NUMBER) as pr_count,
                COUNT(*) as line_items,
                COALESCE(SUM(NET_VALUE), 0) as total_value,
                COUNT(DISTINCT REQUISITIONER) as requisitioner_count,
                COUNT(DISTINCT PLANT) as plant_count
            FROM scm_purchase_requisition
            WHERE REQUISITION_DATE = '{date}'
        """

        try:
            result = self.mcp.query(sql=query)
            if result["success"] and result["data"]:
                logger.info(f"PR Summary: {result['data'][0]}")
                return result["data"][0]
            else:
                return self._empty_pr_summary()
        except Exception as e:
            logger.error(f"Error querying PR summary: {e}", exc_info=True)
            return self._empty_pr_summary()

    def _empty_pr_summary(self) -> Dict[str, Any]:
        """Return empty PR summary structure."""
        return {
            "pr_count": 0,
            "line_items": 0,
            "total_value": 0,
            "requisitioner_count": 0,
            "plant_count": 0
        }

    def _query_pr_by_status(self, date: str) -> List[Dict]:
        """Query PR breakdown by status."""
        query = f"""
            SELECT
                STATU as status,
                COUNT(*) as count,
                SUM(NET_VALUE) as total_value
            FROM scm_purchase_requisition
            WHERE REQUISITION_DATE = '{date}'
            GROUP BY STATU
            ORDER BY count DESC
        """

        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} PR status records")
                return result["data"]
            return []
        except Exception as e:
            logger.error(f"Error querying PR by status: {e}", exc_info=True)
            return []

    def _query_pr_details(self, date: str) -> List[Dict]:
        """Query detailed PR line items."""
        query = f"""
            SELECT
                PR_NUMBER,
                PR_ITEM,
                SHORT_TEXT,
                NET_VALUE,
                STATU,
                PO_NO,
                REQUISITIONER,
                MATERIAL_GROUP_DESC,
                PLANT
            FROM scm_purchase_requisition
            WHERE REQUISITION_DATE = '{date}'
            ORDER BY NET_VALUE DESC
            LIMIT 20
        """

        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} PR detail records")
                return result["data"]
            return []
        except Exception as e:
            logger.error(f"Error querying PR details: {e}", exc_info=True)
            return []

    # ========================================================================
    # BUILD SECTION METHODS
    # ========================================================================

    def _build_po_section(self, summary: Dict, by_vendor: List, by_plant: List,
                          by_category: List, details: List) -> Dict[str, Any]:
        """Build Purchase Orders section."""
        po_count = safe_int(summary.get("po_count", 0))
        line_items = safe_int(summary.get("line_items", 0))
        total_value = safe_float(summary.get("total_value", 0))
        vendor_count = safe_int(summary.get("vendor_count", 0))
        purch_groups = safe_int(summary.get("purch_groups", 0))
        pending_qty = safe_float(summary.get("pending_qty", 0))
        received_qty = safe_float(summary.get("received_qty", 0))

        # Calculate delivery status
        total_qty = pending_qty + received_qty
        pending_pct = (pending_qty / total_qty * 100) if total_qty > 0 else 100
        received_pct = 100 - pending_pct

        # Calculate average value per item
        avg_value = total_value / line_items if line_items > 0 else 0

        # Format currency for display
        value_display = format_currency_display(total_value)
        avg_display = format_currency_display(avg_value)

        # Build vendor list
        vendors = []
        for v in by_vendor:
            vendors.append({
                "name": v.get("vendor", "Unknown"),
                "po_count": safe_int(v.get("po_count", 0)),
                "line_items": safe_int(v.get("line_items", 0)),
                "value": safe_float(v.get("total_value", 0)),
                "value_formatted": format_currency_lakhs(safe_float(v.get("total_value", 0)))
            })

        # Build plant list
        plants = []
        for p in by_plant:
            plants.append({
                "code": p.get("plant_code", ""),
                "name": p.get("plant", "Unknown"),
                "po_count": safe_int(p.get("po_count", 0)),
                "line_items": safe_int(p.get("line_items", 0)),
                "value": safe_float(p.get("total_value", 0)),
                "value_formatted": format_currency_lakhs(safe_float(p.get("total_value", 0)))
            })

        # Build category list
        categories = []
        for c in by_category:
            categories.append({
                "name": c.get("category", "Unknown"),
                "item_count": safe_int(c.get("item_count", 0)),
                "value": safe_float(c.get("total_value", 0)),
                "value_formatted": format_currency_lakhs(safe_float(c.get("total_value", 0)))
            })

        # Build details list
        po_items = []
        for d in details:
            po_items.append({
                "po_no": d.get("PO_NO", ""),
                "item_no": d.get("ITEM_NO", ""),
                "vendor": d.get("VENDOR_NAME", "Unknown"),
                "material": d.get("MATERIAL_DESC", "")[:50],  # Truncate long descriptions
                "plant": d.get("PLANT_NAME", ""),
                "quantity": safe_float(d.get("QUANTITY", 0)),
                "unit": d.get("UNIT", ""),
                "value": safe_float(d.get("NET_ORDER_VALUE", 0)),
                "value_formatted": format_currency_lakhs(safe_float(d.get("NET_ORDER_VALUE", 0))),
                "category": d.get("MAT_GROUP_DESC", ""),
                "order_type": d.get("ORDER_TYPE_DESC", ""),
                "pending_qty": safe_float(d.get("STILL_DEL_QTY", 0)),
                "received_qty": safe_float(d.get("GR_QTY", 0)),
                "delivery_date": str(d.get("ITEM_DEL_DATE", "")) if d.get("ITEM_DEL_DATE") else ""
            })

        return {
            "count": po_count,
            "line_items": line_items,
            "total_value": total_value,
            "total_value_display": value_display,
            "avg_value": avg_value,
            "avg_value_display": avg_display,
            "vendor_count": vendor_count,
            "purch_groups": purch_groups,
            "pending_pct": round(pending_pct, 1),
            "received_pct": round(received_pct, 1),
            "by_vendor": vendors,
            "by_plant": plants,
            "by_category": categories,
            "details": po_items
        }

    def _build_pr_section(self, summary: Dict, by_status: List, details: List) -> Dict[str, Any]:
        """Build Purchase Requisitions section."""
        pr_count = safe_int(summary.get("pr_count", 0))
        line_items = safe_int(summary.get("line_items", 0))
        total_value = safe_float(summary.get("total_value", 0))
        requisitioner_count = safe_int(summary.get("requisitioner_count", 0))

        # Status mapping
        status_map = {
            "N": "New/Pending",
            "B": "Blocked/Converted",
            "A": "Approved"
        }

        # Build status breakdown
        statuses = []
        converted_count = 0
        pending_count = 0
        for s in by_status:
            status_code = s.get("status", "")
            count = safe_int(s.get("count", 0))
            statuses.append({
                "code": status_code,
                "name": status_map.get(status_code, status_code),
                "count": count,
                "value": safe_float(s.get("total_value", 0))
            })
            if status_code == "B":
                converted_count = count
            elif status_code == "N":
                pending_count = count

        # Build PR details list
        pr_items = []
        for d in details:
            status_code = d.get("STATU", "N")
            po_no = d.get("PO_NO", "")
            is_converted = status_code == "B" and po_no

            pr_items.append({
                "pr_number": d.get("PR_NUMBER", ""),
                "pr_item": d.get("PR_ITEM", ""),
                "description": d.get("SHORT_TEXT", "")[:40],
                "value": safe_float(d.get("NET_VALUE", 0)),
                "value_formatted": format_currency_lakhs(safe_float(d.get("NET_VALUE", 0))),
                "status_code": status_code,
                "status": "✅ Converted" if is_converted else "⏳ Pending",
                "is_converted": is_converted,
                "po_no": po_no if is_converted else "-",
                "requisitioner": d.get("REQUISITIONER", ""),
                "category": d.get("MATERIAL_GROUP_DESC", "")[:20],
                "plant": d.get("PLANT", "")
            })

        # Calculate conversion rate
        total_prs = converted_count + pending_count
        conversion_rate = (converted_count / total_prs * 100) if total_prs > 0 else 0

        return {
            "count": pr_count,
            "line_items": line_items,
            "total_value": total_value,
            "total_value_formatted": format_currency_lakhs(total_value),
            "requisitioner_count": requisitioner_count,
            "by_status": statuses,
            "details": pr_items,
            "converted_count": converted_count,
            "pending_count": pending_count,
            "conversion_rate": round(conversion_rate, 1)
        }

    def _build_summary_metrics(self, po_summary: Dict, pr_summary: Dict) -> Dict[str, Any]:
        """Build executive summary metrics."""
        po_count = safe_int(po_summary.get("po_count", 0))
        po_items = safe_int(po_summary.get("line_items", 0))
        po_value = safe_float(po_summary.get("total_value", 0))
        vendor_count = safe_int(po_summary.get("vendor_count", 0))
        purch_groups = safe_int(po_summary.get("purch_groups", 0))

        pr_count = safe_int(pr_summary.get("pr_count", 0))
        pr_items = safe_int(pr_summary.get("line_items", 0))

        # Calculate average
        avg_per_item = po_value / po_items if po_items > 0 else 0

        return {
            "po_count": po_count,
            "po_line_items": po_items,
            "po_total_value": po_value,
            "po_value_display": format_currency_display(po_value),
            "avg_per_item": avg_per_item,
            "avg_per_item_display": format_currency_display(avg_per_item),
            "pr_count": pr_count,
            "pr_line_items": pr_items,
            "vendor_count": vendor_count,
            "purch_groups": purch_groups,
            "pending_delivery_pct": 100  # All pending for today's POs
        }

    def _build_chart_data(self, by_vendor: List, by_plant: List, by_category: List) -> Dict[str, Any]:
        """Build data structures for Chart.js."""
        # Vendor chart data (horizontal bar)
        vendor_labels = []
        vendor_values = []
        for v in by_vendor[:9]:  # Top 9 vendors
            name = v.get("vendor", "Unknown")
            # Truncate long names
            if len(name) > 15:
                name = name[:12] + "..."
            vendor_labels.append(name)
            vendor_values.append(safe_float(v.get("total_value", 0)))

        # Plant chart data (doughnut)
        plant_labels = []
        plant_values = []
        for p in by_plant:
            plant_labels.append(p.get("plant", "Unknown"))
            plant_values.append(safe_float(p.get("total_value", 0)))

        # Category chart data (pie)
        category_labels = []
        category_values = []
        for c in by_category[:8]:  # Top 8 categories
            category_labels.append(c.get("category", "Unknown"))
            category_values.append(safe_float(c.get("total_value", 0)))

        return {
            "vendor": {
                "labels": vendor_labels,
                "values": vendor_values
            },
            "plant": {
                "labels": plant_labels,
                "values": plant_values
            },
            "category": {
                "labels": category_labels,
                "values": category_values
            }
        }

    def _build_daily_highlights(self, po_summary: Dict, pr_summary: Dict,
                                  po_by_vendor: List, po_details: List) -> List[Dict]:
        """Build daily highlights for alert banner."""
        highlights = []

        po_count = safe_int(po_summary.get("po_count", 0))
        po_items = safe_int(po_summary.get("line_items", 0))
        po_value = safe_float(po_summary.get("total_value", 0))
        pr_count = safe_int(pr_summary.get("pr_count", 0))
        pr_items = safe_int(pr_summary.get("line_items", 0))
        pending_pct = 100  # Same-day POs are always pending

        # Highlight 1: PO summary
        value_formatted = format_currency_display(po_value)
        value_str = f"{value_formatted.get('prefix', '₹')}{value_formatted.get('value', 0)} {value_formatted.get('unit', '')}"
        highlights.append({
            "icon": "✓",
            "text": f"<strong>{po_count} Purchase Orders</strong> created totaling <strong>{value_str}</strong>",
            "type": "success"
        })

        # Highlight 2: Pending delivery warning
        if pending_pct == 100:
            highlights.append({
                "icon": "⚠️",
                "text": f"<strong>100% Pending Delivery:</strong> All orders from today are pending delivery",
                "type": "warning"
            })

        # Highlight 3: Top vendor concentration
        if po_by_vendor:
            top_vendor = po_by_vendor[0]
            top_value = safe_float(top_vendor.get("total_value", 0))
            if po_value > 0:
                concentration = (top_value / po_value) * 100
                if concentration > 50:
                    vendor_name = top_vendor.get("vendor", "Unknown")[:20]
                    highlights.append({
                        "icon": "📊",
                        "text": f"<strong>Vendor Concentration:</strong> {vendor_name} accounts for {concentration:.0f}% of total value",
                        "type": "info"
                    })

        # Highlight 4: Large order alert
        if po_details:
            top_order = po_details[0]
            top_order_value = safe_float(top_order.get("value", 0))
            if top_order_value > 1000000:  # > 10 Lakh
                material = top_order.get("material", "")[:30]
                highlights.append({
                    "icon": "💰",
                    "text": f"<strong>Large Order:</strong> {format_currency_lakhs(top_order_value)} for {material}",
                    "type": "info"
                })

        # Highlight 5: PR count
        if pr_count > 0:
            highlights.append({
                "icon": "📋",
                "text": f"<strong>{pr_count} Purchase Requisitions</strong> with {pr_items} line items created",
                "type": "info"
            })

        logger.info(f"Built {len(highlights)} daily highlights")
        return highlights

    def _check_has_data(self, analysis_data: Dict) -> bool:
        """Check if we have any meaningful data."""
        po = analysis_data.get("purchase_orders", {})
        pr = analysis_data.get("purchase_requisitions", {})

        has_po = po.get("count", 0) > 0
        has_pr = pr.get("count", 0) > 0

        return has_po or has_pr

    # ========================================================================
    # NEW RANGE-SPECIFIC METHODS
    # ========================================================================

    def process_date_range(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        NEW: Process all SCM data for a DATE RANGE.

        Args:
            start_date: Start date string in YYYY-MM-DD format
            end_date: End date string in YYYY-MM-DD format

        Returns:
            Dictionary with period_kpis (aggregated metrics for the entire range)
        """
        logger.info(f"Processing SCM data for range: {start_date} to {end_date}")

        # Parse and validate dates
        start_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_obj = datetime.strptime(end_date, '%Y-%m-%d')

        if start_obj > end_obj:
            raise ValueError("start_date must be before or equal to end_date")

        # Calculate range metadata
        days_in_range = (end_obj - start_obj).days + 1
        start_month_name = start_obj.strftime('%B')
        end_month_name = end_obj.strftime('%B')

        # Format date range for display
        if start_obj.year == end_obj.year:
            if start_obj.month == end_obj.month:
                date_range_formatted = f"{start_month_name} {start_obj.day}-{end_obj.day}, {start_obj.year}"
            else:
                date_range_formatted = f"{start_month_name} {start_obj.day} - {end_month_name} {end_obj.day}, {start_obj.year}"
        else:
            date_range_formatted = f"{start_month_name} {start_obj.day}, {start_obj.year} - {end_month_name} {end_obj.day}, {end_obj.year}"

        # Query all data for the range
        po_range = self._query_po_range(start_date, end_date)
        pr_range = self._query_pr_range(start_date, end_date)

        # Build analysis data structure (RANGE version)
        analysis_data = {
            "start_date": start_date,
            "end_date": end_date,
            "date_range_formatted": date_range_formatted,
            "days_in_range": days_in_range,
            "year": start_obj.year,
            "month": start_month_name,

            # PERIOD KPIs (aggregated across range)
            "period_kpis": self._build_period_kpis_range(po_range, pr_range),

            # Detailed sections (aggregated)
            "purchase_orders": self._build_po_section_range(po_range),
            "purchase_requisitions": self._build_pr_section_range(pr_range),
            "summary_metrics": self._build_summary_metrics_range(po_range, pr_range),
            "charts": self._build_chart_data_range(po_range),
            "daily_highlights": self._build_daily_highlights_range(po_range, pr_range)
        }

        # Check if we have any data
        has_data = len(po_range) > 0 or len(pr_range) > 0
        analysis_data["has_data"] = has_data

        logger.info(f"SCM range processing complete. Has data: {has_data}, Days: {days_in_range}")
        return analysis_data

    # Range query methods
    def _query_po_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Query Purchase Orders for date range."""
        query = f"""
            SELECT PO_NO, PO_DATE, VENDOR, PLANT, PURCH_GROUP_DESC,
                   MATERIAL_DESC, NET_ORDER_VALUE, STILL_DEL_QTY, GR_QTY,
                   ITEM_CAT
            FROM scm_purchase_order
            WHERE PO_DATE BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY PO_DATE, PO_NO
        """
        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} PO records for range")
                return result["data"]
            else:
                logger.error(f"PO range query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying PO range: {e}", exc_info=True)
            return []

    def _query_pr_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Query Purchase Requisitions for date range."""
        query = f"""
            SELECT PR_NO, PR_DATE, PLANT, PURCH_GROUP, MATERIAL_DESC,
                   QUANTITY, UNIT, REL_IND, STATUS, REQUISITIONER
            FROM scm_purchase_requisition
            WHERE PR_DATE BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY PR_DATE, PR_NO
        """
        try:
            result = self.mcp.query(sql=query)
            if result["success"]:
                logger.info(f"Retrieved {len(result['data'])} PR records for range")
                return result["data"]
            else:
                logger.error(f"PR range query failed: {result['error']}")
                return []
        except Exception as e:
            logger.error(f"Error querying PR range: {e}", exc_info=True)
            return []

    # Range aggregation methods
    def _build_period_kpis_range(self, po_range: List[Dict], pr_range: List[Dict]) -> Dict[str, Any]:
        """Build period KPIs aggregated across range."""
        # Aggregate PO metrics
        po_count = len(set(r.get('PO_NO') for r in po_range if r.get('PO_NO')))
        total_po_value = sum(safe_float(r.get('NET_ORDER_VALUE')) for r in po_range)
        vendor_count = len(set(r.get('VENDOR') for r in po_range if r.get('VENDOR')))
        plant_count = len(set(r.get('PLANT') for r in po_range if r.get('PLANT')))

        # Aggregate PR metrics
        pr_count = len(set(r.get('PR_NO') for r in pr_range if r.get('PR_NO')))
        pr_released = sum(1 for r in pr_range if r.get('REL_IND') == 'Y')
        pr_pending = pr_count - pr_released

        return {
            "purchase_orders": {
                "count": po_count,
                "total_value": format_currency_display(total_po_value),
                "vendors": vendor_count,
                "plants": plant_count,
            },
            "purchase_requisitions": {
                "count": pr_count,
                "released": pr_released,
                "pending": pr_pending,
            }
        }

    def _build_po_section_range(self, po_range: List[Dict]) -> Dict[str, Any]:
        """Build PO section aggregated."""
        # Count unique POs
        po_count = len(set(r.get('PO_NO') for r in po_range if r.get('PO_NO')))
        line_items = len(po_range)
        total_value = sum(safe_float(r.get('NET_ORDER_VALUE')) for r in po_range)
        vendor_count = len(set(r.get('VENDOR') for r in po_range if r.get('VENDOR')))

        # Aggregate by vendor
        from collections import defaultdict
        vendor_data = defaultdict(lambda: {"value": 0, "po_count": set()})

        for r in po_range:
            vendor = r.get('VENDOR', 'Unknown')
            po_no = r.get('PO_NO')
            vendor_data[vendor]["value"] += safe_float(r.get('NET_ORDER_VALUE'))
            if po_no:
                vendor_data[vendor]["po_count"].add(po_no)

        # Build top vendors
        top_vendors = []
        for vendor, data in sorted(vendor_data.items(), key=lambda x: x[1]["value"], reverse=True)[:10]:
            top_vendors.append({
                "vendor": vendor,
                "po_count": len(data["po_count"]),
                "value": format_currency_display(data["value"]),
            })

        # Aggregate by plant
        plant_data = defaultdict(lambda: {"value": 0, "po_count": set()})
        for r in po_range:
            plant = r.get('PLANT', 'Unknown')
            po_no = r.get('PO_NO')
            plant_data[plant]["value"] += safe_float(r.get('NET_ORDER_VALUE'))
            if po_no:
                plant_data[plant]["po_count"].add(po_no)

        by_plant = []
        for plant, data in sorted(plant_data.items()):
            by_plant.append({
                "plant": plant,
                "po_count": len(data["po_count"]),
                "value": format_currency_display(data["value"]),
            })

        # Aggregate by category
        category_data = defaultdict(float)
        for r in po_range:
            category = r.get('ITEM_CAT', 'Unknown')
            category_data[category] += safe_float(r.get('NET_ORDER_VALUE'))

        by_category = []
        for category, value in sorted(category_data.items(), key=lambda x: x[1], reverse=True):
            by_category.append({
                "category": category,
                "value": format_currency_display(value),
            })

        return {
            "count": po_count,
            "line_items": line_items,
            "total_value": format_currency_display(total_value),
            "vendors": vendor_count,
            "top_vendors": top_vendors,
            "by_plant": by_plant,
            "by_category": by_category[:5],  # Top 5
        }

    def _build_pr_section_range(self, pr_range: List[Dict]) -> Dict[str, Any]:
        """Build PR section aggregated."""
        # Count unique PRs
        pr_count = len(set(r.get('PR_NO') for r in pr_range if r.get('PR_NO')))

        # Aggregate by status
        status_counts = defaultdict(int)
        for r in pr_range:
            rel_ind = r.get('REL_IND', 'N')
            status = 'Released' if rel_ind == 'Y' else 'Pending'
            status_counts[status] += 1

        by_status = []
        for status, count in sorted(status_counts.items()):
            by_status.append({
                "status": status,
                "count": count,
            })

        # Aggregate by plant
        plant_counts = defaultdict(int)
        for r in pr_range:
            plant = r.get('PLANT', 'Unknown')
            plant_counts[plant] += 1

        by_plant = []
        for plant, count in sorted(plant_counts.items(), key=lambda x: x[1], reverse=True):
            by_plant.append({
                "plant": plant,
                "count": count,
            })

        return {
            "count": pr_count,
            "by_status": by_status,
            "by_plant": by_plant,
        }

    def _build_summary_metrics_range(self, po_range: List[Dict], pr_range: List[Dict]) -> Dict[str, Any]:
        """Build summary metrics for range."""
        po_count = len(set(r.get('PO_NO') for r in po_range if r.get('PO_NO')))
        total_po_value = sum(safe_float(r.get('NET_ORDER_VALUE')) for r in po_range)
        pr_count = len(set(r.get('PR_NO') for r in pr_range if r.get('PR_NO')))

        return {
            "po_count": po_count,
            "total_po_value": format_currency_display(total_po_value),
            "pr_count": pr_count,
        }

    def _build_chart_data_range(self, po_range: List[Dict]) -> Dict[str, Any]:
        """Build chart data for range."""
        # Simplified - daily trend
        from collections import defaultdict
        daily_data = defaultdict(lambda: {"value": 0, "count": 0})

        for r in po_range:
            date = r.get('PO_DATE', '')
            if date:
                daily_data[str(date)]["value"] += safe_float(r.get('NET_ORDER_VALUE'))
                daily_data[str(date)]["count"] += 1

        labels = []
        values = []
        for date in sorted(daily_data.keys()):
            labels.append(date)
            values.append(round(daily_data[date]["value"] / 100000, 2))  # Lakhs

        return {
            "daily_po_value": {
                "labels": labels,
                "values": values,
            }
        }

    def _build_daily_highlights_range(self, po_range: List[Dict], pr_range: List[Dict]) -> List[str]:
        """Build daily highlights for range."""
        highlights = []

        po_count = len(set(r.get('PO_NO') for r in po_range if r.get('PO_NO')))
        total_po_value = sum(safe_float(r.get('NET_ORDER_VALUE')) for r in po_range)
        pr_count = len(set(r.get('PR_NO') for r in pr_range if r.get('PR_NO')))

        if po_count > 0:
            highlights.append(f"{po_count} Purchase Orders processed with total value {format_currency_lakhs(total_po_value)}")

        if pr_count > 0:
            highlights.append(f"{pr_count} Purchase Requisitions raised")

        vendor_count = len(set(r.get('VENDOR') for r in po_range if r.get('VENDOR')))
        if vendor_count > 0:
            highlights.append(f"Engaged with {vendor_count} vendors")

        return highlights if highlights else ["No significant activity in this period"]


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def process_scm_data(mcp_server, date: str) -> Dict[str, Any]:
    """
    Convenience function to process SCM data.

    Args:
        mcp_server: MCP server instance
        date: Date string (YYYY-MM-DD)

    Returns:
        Analysis data dictionary
    """
    processor = SCMDataProcessor(mcp_server)
    return processor.process_date(date)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['SCMDataProcessor', 'process_scm_data']