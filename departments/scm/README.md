# Supply Chain Management (SCM) Department Dashboard

## Overview

This module generates comprehensive dashboards for the **Supply Chain Management Department** at Balasore Alloys Limited. It tracks purchase orders, purchase requisitions, vendor performance, and procurement metrics.

## File Structure

```
departments/scm/
├── __init__.py           # Module exports (SCMDataProcessor, SCMTemplateEngine, SCMClaudeInsightsGenerator)
├── formatter.py          # Data processing and KPI calculations
├── template_engine.py    # HTML dashboard generation
├── claude_analyzer.py    # AI-powered insights generation
└── README.md             # This file
```

## How to Run

The dashboard is generated through the main Flask application:

```bash
# Start the Flask server
python app_main.py

# API Endpoints:
# Single date dashboard:
GET /api/v1/dashboard/scm?date=2026-01-15

# Date range dashboard:
GET /api/v1/dashboard/scm?start_date=2026-01-01&end_date=2026-01-15
```

### Template Location
`templates/scm_dashboard.html`

---

## Database Tables

### Table: `scm_purchase_order`

**Description:** Purchase Order line items with vendor, material, pricing, and delivery status.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `PO_NO` | varchar(10) | PRI | NO | Purchase order number |
| `ITEM_NO` | varchar(5) | PRI | NO | Line item number |
| `PR_NO` | varchar(10) | - | YES | Source purchase requisition |
| `PR_ITEM` | varchar(5) | - | YES | PR line item |
| `PURCHASING_GROUP` | varchar(3) | - | YES | Purchasing group code |
| `PURCH_GROUP_DESC` | varchar(40) | - | YES | Purchasing group description |
| `PO_DATE` | date | - | YES | PO creation date |
| `VENDOR` | varchar(10) | - | YES | Vendor code |
| `VENDOR_NAME` | varchar(40) | - | YES | Vendor name |
| `MATERIAL_NO` | varchar(20) | - | YES | Material number |
| `MATERIAL_DESC` | varchar(40) | - | YES | Material description |
| `PLANT` | varchar(4) | - | YES | Plant code |
| `PLANT_NAME` | varchar(30) | - | YES | Plant name |
| `QUANTITY` | decimal(13,3) | - | YES | Ordered quantity |
| `UNIT` | varchar(3) | - | YES | Unit of measure |
| `NET_PRICE` | decimal(11,2) | - | YES | Net price per unit |
| `NET_ORDER_VALUE` | decimal(15,2) | - | YES | Total line item value |
| `STILL_DEL_QTY` | decimal(13,3) | - | YES | Pending delivery quantity |
| `GR_QTY` | decimal(13,3) | - | YES | Goods received quantity |
| `MATERIAL_GROUP` | varchar(9) | - | YES | Material group code |
| `MAT_GROUP_DESC` | varchar(40) | - | YES | Material group description |
| `ORDER_TYPE` | varchar(4) | - | YES | Order type code |
| `ORDER_TYPE_DESC` | varchar(20) | - | YES | Order type description |
| `ITEM_DEL_DATE` | date | - | YES | Expected delivery date |
| `PO_RELEASE_DATE` | date | - | YES | PO release date |
| `GOODS_RECEIPT_DATE` | varchar(10) | - | YES | GR posting date |
| ... | ... | ... | ... | *(53 columns total)* |

**Primary Key:** (`PO_NO`, `ITEM_NO`)

**Statistics:** ~10,686 rows, 4.52 MB

---

### Table: `scm_purchase_requisition`

**Description:** Purchase Requisition line items with status tracking and conversion to PO.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `PR_NUMBER` | varchar(10) | PRI | NO | Purchase requisition number |
| `PR_ITEM` | varchar(5) | PRI | NO | Line item number |
| `REQUISITION_DATE` | date | - | YES | Requisition date |
| `CREATED_ON` | date | - | YES | Creation date |
| `STATU` | varchar(10) | - | YES | Status code (N=New, B=Blocked/Converted, A=Approved) |
| `PO_NO` | varchar(10) | - | YES | Converted PO number (if converted) |
| `PO_ITEM` | varchar(5) | - | YES | PO line item |
| `PO_DATE` | date | - | YES | PO date (if converted) |
| `MATERIAL_NO` | varchar(20) | - | YES | Material number |
| `SHORT_TEXT` | varchar(40) | - | YES | Material description |
| `BASE_UNIT` | varchar(3) | - | YES | Unit of measure |
| `QUANTITY` | decimal(13,3) | - | YES | Requested quantity |
| `REQUISITIONER` | varchar(12) | - | YES | Requisitioner ID |
| `MATERIAL_GROUP` | varchar(9) | - | YES | Material group code |
| `MATERIAL_GROUP_DESC` | varchar(40) | - | YES | Material group description |
| `PLANT` | varchar(4) | - | YES | Plant code |
| `PURCHASING_GROUP` | varchar(3) | - | YES | Purchasing group |
| `NET_VALUE` | decimal(15,2) | - | YES | Estimated value |
| `PR_RELEASE_DATE` | date | - | YES | Release date |
| `PR_OVERALL_RELEASE` | varchar(1) | - | YES | Overall release status |
| `DELIVERY_DATE` | date | - | YES | Required delivery date |
| ... | ... | ... | ... | *(49 columns total)* |

**Primary Key:** (`PR_NUMBER`, `PR_ITEM`)

**Statistics:** ~15,809 rows, 5.52 MB

---

## Key Files Explained

### 1. `formatter.py` - SCMDataProcessor

The main data processor that queries the database and builds the analysis data structure.

#### Helper Functions

```python
def format_currency_lakhs(value: float) -> str:
    """
    Format value in Indian Lakhs/Crores.
    < 1 Lakh: ₹X,XXX
    1-99 Lakhs: ₹X.XX L
    >= 1 Crore: ₹X.XX Cr
    """
    lakhs = value / 100000
    if lakhs >= 100:
        return f"₹{lakhs/100:.2f} Cr"
    elif lakhs >= 1:
        return f"₹{lakhs:.2f} L"
    else:
        return f"₹{value:,.0f}"

def format_currency_display(value: float) -> Dict[str, Any]:
    """Return value formatted with unit for JS display."""
    if value >= 10000000:  # >= 1 Crore
        return {"value": round(value / 10000000, 2), "unit": "Cr", "prefix": "₹"}
    elif value >= 100000:  # >= 1 Lakh
        return {"value": round(value / 100000, 2), "unit": "L", "prefix": "₹"}
    else:
        return {"value": round(value, 0), "unit": "", "prefix": "₹"}
```

#### Key Methods

| Method | Description |
|--------|-------------|
| `process_date(date)` | Main entry point for single-date processing |
| `process_date_range(start_date, end_date)` | Processes date range with aggregations |
| `_query_po_summary(date)` | Aggregates PO metrics for a date |
| `_query_po_by_vendor(date)` | Top 10 vendors by PO value |
| `_query_po_by_plant(date)` | POs grouped by plant |
| `_query_po_by_category(date)` | POs grouped by material category |
| `_query_po_details(date)` | Top 20 PO line items by value |
| `_query_pr_summary(date)` | Aggregates PR metrics for a date |
| `_query_pr_by_status(date)` | PRs grouped by status |
| `_query_pr_details(date)` | Top 20 PR line items by value |
| `_build_po_section(...)` | Builds purchase order section with vendors, plants, categories |
| `_build_pr_section(...)` | Builds purchase requisition section with status tracking |
| `_build_summary_metrics(...)` | Builds executive summary metrics |
| `_build_chart_data(...)` | Builds Chart.js data structures |
| `_build_daily_highlights(...)` | Generates alert banner highlights |

#### Status Code Mapping

```python
status_map = {
    "N": "New/Pending",      # PR not yet converted
    "B": "Blocked/Converted", # PR converted to PO
    "A": "Approved"          # PR approved
}
```

### 2. `template_engine.py` - SCMTemplateEngine

Injects processed data into the HTML template.

**Key Methods:**
- `generate_dashboard(analysis_data, claude_insights_html, date)` - Main entry point
- Handles currency formatting for display
- Injects vendor, plant, and category chart data

### 3. `claude_analyzer.py` - SCMClaudeInsightsGenerator

Generates AI-powered procurement insights using OpenAI GPT-4.

**Key Methods:**
- `generate_insights(analysis_data, date)` - Generates 5-6 actionable insights
- Analyzes vendor concentration, PO values, PR conversion rates
- Returns formatted HTML for dashboard injection

---

## KPIs and Calculations

### Purchase Order KPIs

| KPI | Source Table | Column(s) | Calculation |
|-----|--------------|-----------|-------------|
| PO Count | `scm_purchase_order` | `PO_NO` | `COUNT(DISTINCT PO_NO)` |
| Line Items | `scm_purchase_order` | `*` | `COUNT(*)` |
| Total Value | `scm_purchase_order` | `NET_ORDER_VALUE` | `SUM(NET_ORDER_VALUE)` |
| Vendor Count | `scm_purchase_order` | `VENDOR` | `COUNT(DISTINCT VENDOR)` |
| Purchasing Groups | `scm_purchase_order` | `PURCH_GROUP_DESC` | `COUNT(DISTINCT PURCH_GROUP_DESC)` |
| Plant Count | `scm_purchase_order` | `PLANT` | `COUNT(DISTINCT PLANT)` |
| Pending Qty | `scm_purchase_order` | `STILL_DEL_QTY` | `SUM(STILL_DEL_QTY)` |
| Received Qty | `scm_purchase_order` | `GR_QTY` | `SUM(GR_QTY)` |
| Avg PO Value | Calculated | - | `Total Value / PO Count` |

### Purchase Requisition KPIs

| KPI | Source Table | Column(s) | Calculation |
|-----|--------------|-----------|-------------|
| PR Count | `scm_purchase_requisition` | `PR_NUMBER` | `COUNT(DISTINCT PR_NUMBER)` |
| Line Items | `scm_purchase_requisition` | `*` | `COUNT(*)` |
| Total Value | `scm_purchase_requisition` | `NET_VALUE` | `SUM(NET_VALUE)` |
| Requisitioner Count | `scm_purchase_requisition` | `REQUISITIONER` | `COUNT(DISTINCT REQUISITIONER)` |
| Converted Count | `scm_purchase_requisition` | `STATU` | `COUNT(*) WHERE STATU = 'B'` |
| Pending Count | `scm_purchase_requisition` | `STATU` | `COUNT(*) WHERE STATU = 'N'` |
| Conversion Rate | Calculated | - | `(Converted / Total) * 100` |

### Delivery Performance

| KPI | Source | Calculation |
|-----|--------|-------------|
| Pending Delivery % | `scm_purchase_order` | `STILL_DEL_QTY / (STILL_DEL_QTY + GR_QTY) * 100` |
| Received % | `scm_purchase_order` | `GR_QTY / (STILL_DEL_QTY + GR_QTY) * 100` |

### Vendor Analysis

| KPI | Calculation |
|-----|-------------|
| Top Vendors | `GROUP BY VENDOR_NAME ORDER BY SUM(NET_ORDER_VALUE) DESC LIMIT 10` |
| Vendor Concentration | `Top Vendor Value / Total Value * 100` |

### Plant-wise Distribution

| KPI | Calculation |
|-----|-------------|
| POs per Plant | `GROUP BY PLANT, PLANT_NAME` |
| Value per Plant | `SUM(NET_ORDER_VALUE) GROUP BY PLANT` |

---

## Data Flow

```
1. API Request (/api/v1/dashboard/scm?date=YYYY-MM-DD)
        ↓
2. SCMDataProcessor.process_date(date)
   - Queries scm_purchase_order (summary, by vendor, by plant, by category, details)
   - Queries scm_purchase_requisition (summary, by status, details)
   - Calculates delivery performance metrics
   - Calculates PR conversion rates
   - Builds sections: purchase_orders, purchase_requisitions, summary_metrics
   - Builds chart data for vendors, plants, categories
   - Generates daily highlights for alert banner
        ↓
3. SCMClaudeInsightsGenerator.generate_insights(analysis_data, date)
   - Builds data context with PO/PR metrics
   - Calls OpenAI GPT-4 API
   - Returns AI-generated insights HTML
        ↓
4. SCMTemplateEngine.generate_dashboard(...)
   - Loads scm_dashboard.html
   - Injects KPI values via regex replacement
   - Injects chart data into JavaScript
        ↓
5. Returns complete HTML dashboard
```

---

## Sample SQL Queries Used

### PO Summary
```sql
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
WHERE PO_DATE = '2026-01-15'
```

### PO by Vendor (Top 10)
```sql
SELECT
    VENDOR_NAME as vendor,
    COUNT(DISTINCT PO_NO) as po_count,
    COUNT(*) as line_items,
    SUM(NET_ORDER_VALUE) as total_value
FROM scm_purchase_order
WHERE PO_DATE = '2026-01-15'
GROUP BY VENDOR_NAME
ORDER BY total_value DESC
LIMIT 10
```

### PO by Plant
```sql
SELECT
    PLANT as plant_code,
    PLANT_NAME as plant,
    COUNT(DISTINCT PO_NO) as po_count,
    COUNT(*) as line_items,
    SUM(NET_ORDER_VALUE) as total_value
FROM scm_purchase_order
WHERE PO_DATE = '2026-01-15'
GROUP BY PLANT, PLANT_NAME
ORDER BY total_value DESC
```

### PR Summary
```sql
SELECT
    COUNT(DISTINCT PR_NUMBER) as pr_count,
    COUNT(*) as line_items,
    COALESCE(SUM(NET_VALUE), 0) as total_value,
    COUNT(DISTINCT REQUISITIONER) as requisitioner_count,
    COUNT(DISTINCT PLANT) as plant_count
FROM scm_purchase_requisition
WHERE REQUISITION_DATE = '2026-01-15'
```

### PR by Status
```sql
SELECT
    STATU as status,
    COUNT(*) as count,
    SUM(NET_VALUE) as total_value
FROM scm_purchase_requisition
WHERE REQUISITION_DATE = '2026-01-15'
GROUP BY STATU
ORDER BY count DESC
```

---

## Configuration

Environment variables required in `.env`:
```bash
# Database
DB_HOST=80.9.2.78
DB_PORT=3306
DB_NAME=balcorpdb
DB_USER=your_user
DB_PASSWORD=your_password

# AI (OpenAI - Default)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

---

## Currency Display Format

| Value Range | Display Format | Example |
|-------------|----------------|---------|
| < ₹1 Lakh | ₹X,XXX | ₹50,000 |
| ₹1 L - ₹99 L | ₹X.XX L | ₹25.50 L |
| >= ₹1 Crore | ₹X.XX Cr | ₹1.25 Cr |

---

## Daily Highlights Logic

The dashboard generates contextual alerts:

| Condition | Highlight |
|-----------|-----------|
| Always | PO count and total value summary |
| Same-day POs | "100% Pending Delivery" warning |
| Top vendor > 50% | Vendor concentration alert |
| Large order > ₹10 L | Large order highlight |
| PRs exist | PR count summary |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No data displayed | Check if data exists for the requested date in SCM tables |
| Values showing ₹0 | Verify `NET_ORDER_VALUE` column is not NULL |
| Vendor count wrong | Check `VENDOR_NAME` column for duplicates/variations |
| Conversion rate N/A | Ensure `PR_NUMBER` references in PO table via `PR_NO` |
| Plant data missing | Verify `PLANT` and `PLANT_NAME` columns have values |
| PR status wrong | Check `STATU` column values (N/B/A) |

---

## Contact

**Department Lead**: @scm-lead
**Branch**: `dept/scm`

For questions or issues, contact the BAL-Agentic-Backend Team.
