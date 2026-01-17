# CRM (Customer Relationship Management) Department Dashboard

## Overview

This module generates comprehensive dashboards for the **CRM/Sales & Distribution Department** at Balasore Alloys Limited. It tracks customer orders, sales performance, dispatch operations, billing, customer inquiries, contracts, and customer satisfaction metrics across **7 database tables**.

## File Structure

```
departments/crm/
├── __init__.py           # Module exports (CRMDataProcessor, CRMTemplateEngine, CRMClaudeInsightsGenerator)
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
GET /api/v1/dashboard/crm?date=2026-01-15

# Date range dashboard:
GET /api/v1/dashboard/crm?start_date=2026-01-01&end_date=2026-01-15
```

### Template Location
`templates/sd_dashboard.html` (Sales & Distribution)

---

## Database Tables Overview

| # | Table Name | Description | Row Count |
|---|------------|-------------|-----------|
| 1 | `sd_sales_order` | Sales orders by date | ~1,820 |
| 2 | `sd_sales_status` | Billing/invoice records | ~8,525 |
| 3 | `sd_outbound_delivery` | Delivery/dispatch records | ~20,648 |
| 4 | `sd_inquiry` | Customer inquiries | ~860 |
| 5 | `sd_contract` | Customer contracts | ~851 |
| 6 | `kpi_marketing_business_plan` | Monthly targets | ~80 |
| 7 | `kpi_marketing_customer_survey_report` | Customer satisfaction | ~17 |

---

## Database Table Schemas

### Table 1: `sd_sales_order`

**Description:** Sales order records with customer, material, and pricing details.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `SO_NO` | varchar(10) | PRI | NO | Sales order number |
| `SO_ITEM` | varchar(6) | PRI | NO | Line item number |
| `SO_DATE` | date | - | NO | Order date |
| `SD_TYPE` | varchar(4) | - | YES | Sales document type code |
| `SD_TYPE_DESC` | varchar(40) | - | YES | Sales document type description |
| `SIPPING_PLANT` | varchar(4) | - | YES | Shipping plant code |
| `SIPPING_PLANT_NAME` | varchar(40) | - | YES | Shipping plant name |
| `SOLD_TO_PARTY` | varchar(10) | - | YES | Customer code |
| `SOLD_TO_PARTY_NAME` | varchar(40) | - | YES | Customer name |
| `SHIP_TO_PARTY` | varchar(10) | - | YES | Ship-to party code |
| `SHIP_TO_PARTY_NAME` | varchar(40) | - | YES | Ship-to party name |
| `REGION` | varchar(20) | - | YES | Region |
| `COUNTRY` | varchar(15) | - | YES | Country |
| `ZONE` | varchar(40) | - | YES | Zone |
| `MATERIAL` | varchar(40) | - | YES | Material code |
| `MATERIAL_DESC` | varchar(40) | - | YES | Material description |
| `ORDER_QUANTITY` | decimal(15,3) | - | YES | Order quantity |
| `SALES_UNIT` | varchar(4) | - | YES | Unit of measure |
| `NET_VALUE` | decimal(15,2) | - | YES | Net value (document currency) |
| `DOCUMENT_CURRENCY` | varchar(5) | - | YES | Document currency (USD/INR) |
| `NET_PRICE` | decimal(11,2) | - | YES | Net price per unit |
| `NET_PRICE_INR` | decimal(11,2) | - | YES | Net price in INR |
| `NET_VALUE_INR` | decimal(15,2) | - | YES | Net value in INR |
| `DIST_CHANNEL` | varchar(2) | - | YES | Distribution channel code |
| `DIST_CHANNEL_NAME` | varchar(40) | - | YES | Distribution channel name |
| `DIVISION` | varchar(2) | - | YES | Division code |
| `DIVISION_NAME` | varchar(40) | - | YES | Division name |
| `CONFIRMED_QUANTITY` | decimal(15,3) | - | YES | Confirmed quantity |
| `EXCHANGE_RATE` | decimal(9,5) | - | YES | Exchange rate |
| ... | ... | ... | ... | *(38 columns total)* |

**Primary Key:** (`SO_NO`, `SO_ITEM`)

**Statistics:** ~1,820 rows, 1.52 MB

---

### Table 2: `sd_sales_status`

**Description:** Billing/invoice records with GST breakdown and delivery details.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `BILLING_DOC_NO` | varchar(10) | PRI | NO | Billing document number |
| `BILLING_ITEM` | varchar(6) | PRI | NO | Billing line item |
| `INV_CREATED_ON` | date | - | YES | Invoice creation date |
| `DIST_CHANNEL` | varchar(2) | - | NO | Distribution channel |
| `DIVISION` | varchar(2) | - | NO | Division |
| `ZGROUP` | varchar(20) | - | NO | Group code |
| `SOLD_TO_PARTY` | varchar(10) | - | YES | Customer code |
| `CUSTOMER_NAME` | varchar(40) | - | YES | Customer name |
| `CONTRACT_NO` | varchar(10) | - | NO | Contract reference |
| `ORDER_NO` | varchar(10) | - | NO | Sales order reference |
| `MATERIAL_NO` | varchar(40) | - | YES | Material code |
| `MATERIAL_DESC` | varchar(40) | - | YES | Material description |
| `DELIVERY_NO` | varchar(10) | - | YES | Delivery number |
| `DELIVERY_DATE` | date | - | YES | Delivery date |
| `VEHICLE_NO` | varchar(15) | - | YES | Vehicle number |
| `TRANSPORTER` | varchar(40) | - | YES | Transporter name |
| `RATE_MT` | decimal(15,2) | - | YES | Rate per MT |
| `NET_WEIGHT` | decimal(15,3) | - | YES | Net weight (MT) |
| `INV_AMT` | decimal(15,2) | - | YES | Invoice amount (INR) |
| `INV_USD` | decimal(15,2) | - | YES | Invoice amount (USD) |
| `CGST_AMT` | decimal(15,2) | - | YES | CGST amount |
| `SGST_AMT` | decimal(15,2) | - | YES | SGST amount |
| `IGST_AMT` | decimal(15,2) | - | YES | IGST amount |
| `DEST_COUNTRY` | varchar(132) | - | YES | Destination country |
| `EX_RATE` | decimal(15,5) | - | YES | Exchange rate |
| ... | ... | ... | ... | *(65 columns total)* |

**Primary Key:** (`BILLING_DOC_NO`, `BILLING_ITEM`)

**Statistics:** ~8,525 rows, 7.52 MB

---

### Table 3: `sd_outbound_delivery`

**Description:** Outbound delivery/dispatch records.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `DELIVERY_NO` | varchar(10) | PRI | NO | Delivery number |
| `DELIVERY_ITEM` | varchar(6) | PRI | NO | Delivery line item |
| `GOODS_ISSUE_DT` | date | - | YES | Goods issue date |
| `DELIVERY_DATE` | date | - | YES | Delivery date |
| `SHIP_PARTY` | varchar(10) | - | YES | Ship-to party code |
| `SHIP_PARTY_NAME` | varchar(35) | - | YES | Ship-to party name |
| `SOLD_PARTY` | varchar(10) | - | YES | Sold-to party code |
| `SOLD_PARTY_NAME` | varchar(35) | - | YES | Sold-to party name |
| `MATERIAL_NO` | varchar(40) | - | YES | Material code |
| `DELIVERY_TYPE` | varchar(4) | - | YES | Delivery type |
| `NET_WEIGHT` | decimal(15,3) | - | YES | Net weight (MT) |
| `TOTAL_WEIGHT` | decimal(13,3) | - | YES | Total weight (MT) |
| `SHIP_PARTY_LOCA` | varchar(35) | - | YES | Ship-to location |
| `SOLD_PARTY_LOCA` | varchar(35) | - | YES | Sold-to location |
| `GOODS_MNT_STATUS` | varchar(1) | - | YES | Goods movement status |
| `UOM` | varchar(3) | - | YES | Unit of measure |
| ... | ... | ... | ... | *(20 columns total)* |

**Primary Key:** (`DELIVERY_NO`, `DELIVERY_ITEM`)

**Statistics:** ~20,648 rows, 4.52 MB

---

### Table 4: `sd_inquiry`

**Description:** Customer inquiries with quantity and pricing.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `INQUIRY_NO` | varchar(10) | PRI | NO | Inquiry number |
| `DOC_CATEGORY` | varchar(4) | PRI | NO | Document category |
| `ITEM_NO` | varchar(6) | PRI | NO | Line item |
| `DOCUMENT_DATE` | date | - | YES | Inquiry date |
| `CUSTOMER_NO` | varchar(10) | - | YES | Customer code |
| `CUSTOMER_NAME` | varchar(35) | - | YES | Customer name |
| `MATERIAL_NO` | varchar(20) | - | YES | Material code |
| `MATERIAL_DESC` | varchar(40) | - | YES | Material description |
| `SEGMENT` | varchar(40) | - | YES | Market segment |
| `INQ_QTY` | decimal(15,3) | - | YES | Inquiry quantity |
| `PRICE` | decimal(11,2) | - | YES | Quoted price |
| `PLANT` | varchar(4) | - | YES | Plant code |
| `PLANT_NAME` | varchar(30) | - | YES | Plant name |
| `DELIVER_QTY` | decimal(13,3) | - | YES | Delivered quantity |
| `PENDING_QTY` | decimal(13,3) | - | YES | Pending quantity |
| ... | ... | ... | ... | *(27 columns total)* |

**Primary Key:** (`INQUIRY_NO`, `DOC_CATEGORY`, `ITEM_NO`)

**Statistics:** ~860 rows, 0.25 MB

---

### Table 5: `sd_contract`

**Description:** Customer contracts with quantity and fulfillment tracking.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `CONTRACT_NO` | varchar(10) | PRI | NO | Contract number |
| `INQUIRY_NO` | varchar(10) | PRI | NO | Reference inquiry number |
| `DOC_CATEGORY` | varchar(4) | PRI | NO | Document category |
| `ITEM_NO` | varchar(6) | PRI | NO | Line item |
| `DOCUMENT_DATE` | date | - | YES | Contract date |
| `CUSTOMER_NO` | varchar(10) | - | YES | Customer code |
| `CUSTOMER_NAME` | varchar(35) | - | YES | Customer name |
| `MATERIAL_NO` | varchar(20) | - | YES | Material code |
| `MATERIAL_DESC` | varchar(40) | - | YES | Material description |
| `SEGMENT` | varchar(40) | - | YES | Market segment |
| `CON_QTY` | decimal(15,3) | - | YES | Contract quantity |
| `PRICE` | decimal(11,2) | - | YES | Contract price |
| `PLANT` | varchar(4) | - | YES | Plant code |
| `PLANT_NAME` | varchar(30) | - | YES | Plant name |
| `DELIVER_QTY` | decimal(13,3) | - | YES | Delivered quantity |
| `PENDING_QTY` | decimal(13,3) | - | YES | Pending quantity |
| ... | ... | ... | ... | *(28 columns total)* |

**Primary Key:** (`CONTRACT_NO`, `INQUIRY_NO`, `DOC_CATEGORY`, `ITEM_NO`)

**Statistics:** ~851 rows, 0.27 MB

---

### Table 6: `kpi_marketing_business_plan`

**Description:** Monthly sales targets by customer and channel.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `id` | int | PRI | NO | Auto-increment ID |
| `month_year` | varchar(20) | MUL | NO | Month-Year (e.g., "NOV-2025") |
| `customer` | varchar(100) | - | NO | Customer name |
| `plant` | varchar(50) | - | YES | Plant name |
| `channel` | varchar(50) | - | YES | Sales channel |
| `segment` | varchar(50) | - | YES | Market segment |
| `oem_trad` | varchar(50) | - | YES | OEM/Trader classification |
| `kam` | varchar(50) | - | YES | Key Account Manager |
| `contract_no` | varchar(100) | - | YES | Contract number |
| `order_qty_mt` | decimal(10,3) | - | YES | Order target (MT) |
| `target_price` | decimal(12,2) | - | YES | Target price |
| `dispatch_target_mt` | decimal(10,3) | - | YES | Dispatch target (MT) |
| ... | ... | ... | ... | *(20 columns total)* |

**Primary Key:** (`id`)

**Statistics:** ~80 rows, 0.03 MB

---

### Table 7: `kpi_marketing_customer_survey_report`

**Description:** Annual customer satisfaction survey results.

| Column | Type | Key | Nullable | Description |
|--------|------|-----|----------|-------------|
| `SR_NO` | int | PRI | NO | Serial number |
| `FIN_YEAR` | varchar(9) | MUL | YES | Financial year (e.g., "2024-2025") |
| `COMPANY_NAME` | varchar(200) | - | YES | Customer company name |
| `SEGMENT` | varchar(100) | - | YES | Market segment |
| `PRODUCT_QUALITY` | float | - | YES | Product quality rating (1-5) |
| `ORDER_EXECUTION` | float | - | YES | Order execution rating (1-5) |
| `SERVICE_ATTITUDE` | float | - | YES | Service attitude rating (1-5) |
| `PRODUCT_PRICE` | float | - | YES | Product pricing rating (1-5) |
| `RELATIONSHIP_COMPANY` | float | - | YES | Relationship rating (1-5) |
| `CUSTOMER_LOYALTY` | float | - | YES | Customer loyalty rating (1-5) |
| `BUSINESS_SYSTEM` | float | - | YES | Business system rating (1-5) |
| `COMPANY_REPUTATION` | float | - | YES | Company reputation rating (1-5) |
| `CUSTOMER_AVG_RATING` | float | - | YES | Overall average rating |

**Primary Key:** (`SR_NO`)

**Statistics:** ~17 rows, 0.03 MB

---

## Key Files Explained

### 1. `formatter.py` - CRMDataProcessor

The main data processor that queries all 7 tables and builds the analysis data structure (~1,180 lines).

#### Key Constants

```python
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
```

#### Helper Functions

```python
def format_currency_cr(value: float) -> str:
    """
    Format value in Crores/Lakhs.
    >= 1 Crore: ₹X.XX Cr
    >= 1 Lakh: ₹X.XX L
    < 1 Lakh: ₹X,XXX
    """

def get_financial_year(date_obj: datetime) -> str:
    """
    Get financial year string (April-March).
    Example: 2026-01-15 → "2025-2026"
    """

def get_month_year_abbrev(date_obj: datetime) -> str:
    """
    Get month-year string for business plan lookup.
    Example: 2026-01-15 → "JAN-2026"
    """
```

#### Key Methods

| Method | Source Table(s) | Description |
|--------|-----------------|-------------|
| `process_date(date)` | All 7 tables | Main entry point for single-date processing |
| `process_date_range(start_date, end_date)` | All 7 tables | Process date range with aggregations |
| `_query_sales_orders(start, end)` | `sd_sales_order` | Query orders by date range |
| `_query_billing(start, end)` | `sd_sales_status` | Query invoices by date range |
| `_query_deliveries(start, end)` | `sd_outbound_delivery` | Query deliveries by date range |
| `_query_inquiries(start, end)` | `sd_inquiry` | Query inquiries by date range |
| `_query_customer_survey()` | `kpi_marketing_customer_survey_report` | Query latest survey data |
| `_query_business_plan(month_year)` | `kpi_marketing_business_plan` | Query monthly targets |
| `_query_contracts()` | `sd_contract` | Query active contracts |
| `_build_sales_orders_section(td, mtd)` | - | Build sales orders with TD/MTD |
| `_build_billing_section(td, mtd)` | - | Build billing with TD/MTD |
| `_build_deliveries_section(td, mtd)` | - | Build deliveries with TD/MTD |
| `_build_inquiries_section(td)` | - | Build inquiries section |
| `_build_survey_section(data)` | - | Build customer satisfaction charts |
| `_build_business_plan_section(data)` | - | Build business plan targets |
| `_build_contracts_section(data)` | - | Build contracts tracking |
| `_build_highlights(orders, billing, deliveries)` | - | Build daily highlights |

### 2. `template_engine.py` - CRMTemplateEngine

Injects processed data into the HTML template.

**Key Methods:**
- `generate_dashboard(analysis_data, claude_insights_html, date)` - Main entry point
- Replaces all KPI values, customer details, chart data
- Injects JavaScript data for Chart.js visualizations

### 3. `claude_analyzer.py` - CRMClaudeInsightsGenerator

Generates AI-powered sales insights using OpenAI GPT-4 (or local LLM).

**Key Methods:**
- `generate_insights(analysis_data, date)` - Generates 5-6 actionable insights
- Analyzes sales trends, customer concentration, channel performance
- Returns formatted HTML for dashboard injection

---

## KPIs and Calculations

### Sales Orders Section

| KPI | Source Table | Column(s) | Calculation |
|-----|--------------|-----------|-------------|
| TD Order Count | `sd_sales_order` | `SO_NO` | `COUNT(DISTINCT SO_NO)` for date |
| TD Order Quantity | `sd_sales_order` | `ORDER_QUANTITY` | `SUM(ORDER_QUANTITY)` for date |
| TD Order Value | `sd_sales_order` | `NET_VALUE_INR` | `SUM(NET_VALUE_INR)` for date |
| TD Unique Customers | `sd_sales_order` | `SOLD_TO_PARTY_NAME` | `COUNT(DISTINCT SOLD_TO_PARTY_NAME)` |
| TD Avg Price | Calculated | - | `TD Value / TD Quantity` |
| MTD Order Count | `sd_sales_order` | `SO_NO` | `COUNT(DISTINCT SO_NO)` for month |
| MTD Order Value | `sd_sales_order` | `NET_VALUE_INR` | `SUM(NET_VALUE_INR)` for month |
| TD % of MTD | Calculated | - | `(TD Value / MTD Value) * 100` |
| By Channel | `sd_sales_order` | `DIST_CHANNEL_NAME` | `GROUP BY DIST_CHANNEL_NAME` |
| Top Customers | `sd_sales_order` | `SOLD_TO_PARTY_NAME`, `NET_VALUE_INR` | Top 10 by value |

### Billing Section

| KPI | Source Table | Column(s) | Calculation |
|-----|--------------|-----------|-------------|
| TD Invoice Count | `sd_sales_status` | `BILLING_DOC_NO` | `COUNT(DISTINCT BILLING_DOC_NO)` |
| TD Line Items | `sd_sales_status` | `*` | `COUNT(*)` for date |
| TD Weight (MT) | `sd_sales_status` | `NET_WEIGHT` | `SUM(NET_WEIGHT)` for date |
| TD Invoice Value | `sd_sales_status` | `INV_AMT` | `SUM(INV_AMT)` for date |
| TD Avg Rate | `sd_sales_status` | `INV_AMT`, `NET_WEIGHT` | `TD Value / TD Weight` |
| TD IGST | `sd_sales_status` | `IGST_AMT` | `SUM(IGST_AMT)` for date |
| TD CGST | `sd_sales_status` | `CGST_AMT` | `SUM(CGST_AMT)` for date |
| TD SGST | `sd_sales_status` | `SGST_AMT` | `SUM(SGST_AMT)` for date |
| TD Total GST | Calculated | - | `IGST + CGST + SGST` |
| Export Value | `sd_sales_status` | `INV_AMT`, `DEST_COUNTRY` | `SUM(INV_AMT)` where DEST_COUNTRY is not empty |
| Export USD | `sd_sales_status` | `INV_USD` | `SUM(INV_USD)` for exports |
| Export % | Calculated | - | `(Export Value / TD Value) * 100` |
| MTD Invoice Count | `sd_sales_status` | `BILLING_DOC_NO` | `COUNT(DISTINCT BILLING_DOC_NO)` for month |
| MTD Invoice Value | `sd_sales_status` | `INV_AMT` | `SUM(INV_AMT)` for month |
| By Geography | `sd_sales_status` | `DEST_COUNTRY` | `GROUP BY DEST_COUNTRY` |
| Top Customers | `sd_sales_status` | `CUSTOMER_NAME`, `INV_AMT` | Top 10 by value |

### Deliveries Section

| KPI | Source Table | Column(s) | Calculation |
|-----|--------------|-----------|-------------|
| TD Delivery Count | `sd_outbound_delivery` | `DELIVERY_NO` | `COUNT(DISTINCT DELIVERY_NO)` |
| TD Weight (MT) | `sd_outbound_delivery` | `NET_WEIGHT` | `SUM(NET_WEIGHT)` for date |
| TD Unique Customers | `sd_outbound_delivery` | `SOLD_PARTY_NAME` | `COUNT(DISTINCT SOLD_PARTY_NAME)` |
| TD Avg per Delivery | Calculated | - | `TD Weight / TD Delivery Count` |
| MTD Delivery Count | `sd_outbound_delivery` | `DELIVERY_NO` | `COUNT(DISTINCT DELIVERY_NO)` for month |
| MTD Weight | `sd_outbound_delivery` | `NET_WEIGHT` | `SUM(NET_WEIGHT)` for month |
| TD % of MTD | Calculated | - | `(TD Count / MTD Count) * 100` |
| By Customer | `sd_outbound_delivery` | `SOLD_PARTY_NAME` | `GROUP BY SOLD_PARTY_NAME` |

### Inquiries Section

| KPI | Source Table | Column(s) | Calculation |
|-----|--------------|-----------|-------------|
| Inquiry Count | `sd_inquiry` | `INQUIRY_NO` | `COUNT(DISTINCT INQUIRY_NO)` |
| Total Quantity | `sd_inquiry` | `INQ_QTY` | `SUM(INQ_QTY)` |
| Unique Customers | `sd_inquiry` | `CUSTOMER_NAME` | `COUNT(DISTINCT CUSTOMER_NAME)` |
| By Segment | `sd_inquiry` | `SEGMENT` | `GROUP BY SEGMENT` |

### Customer Survey Section

| KPI | Source Table | Column(s) | Calculation |
|-----|--------------|-----------|-------------|
| Avg Product Quality | `kpi_marketing_customer_survey_report` | `PRODUCT_QUALITY` | `AVG(PRODUCT_QUALITY)` |
| Avg Order Execution | `kpi_marketing_customer_survey_report` | `ORDER_EXECUTION` | `AVG(ORDER_EXECUTION)` |
| Avg Service Attitude | `kpi_marketing_customer_survey_report` | `SERVICE_ATTITUDE` | `AVG(SERVICE_ATTITUDE)` |
| Avg Product Price | `kpi_marketing_customer_survey_report` | `PRODUCT_PRICE` | `AVG(PRODUCT_PRICE)` |
| Avg Relationship | `kpi_marketing_customer_survey_report` | `RELATIONSHIP_COMPANY` | `AVG(RELATIONSHIP_COMPANY)` |
| Avg Loyalty | `kpi_marketing_customer_survey_report` | `CUSTOMER_LOYALTY` | `AVG(CUSTOMER_LOYALTY)` |
| Avg Business System | `kpi_marketing_customer_survey_report` | `BUSINESS_SYSTEM` | `AVG(BUSINESS_SYSTEM)` |
| Avg Reputation | `kpi_marketing_customer_survey_report` | `COMPANY_REPUTATION` | `AVG(COMPANY_REPUTATION)` |
| Overall Avg Rating | `kpi_marketing_customer_survey_report` | `CUSTOMER_AVG_RATING` | `AVG(CUSTOMER_AVG_RATING)` |
| Respondents | `kpi_marketing_customer_survey_report` | `*` | `COUNT(*)` |

### Business Plan Section

| KPI | Source Table | Column(s) | Calculation |
|-----|--------------|-----------|-------------|
| Total Order Target | `kpi_marketing_business_plan` | `order_qty_mt` | `SUM(order_qty_mt)` |
| Total Dispatch Target | `kpi_marketing_business_plan` | `dispatch_target_mt` | `SUM(dispatch_target_mt)` |
| Unique Customers | `kpi_marketing_business_plan` | `customer` | `COUNT(DISTINCT customer)` |
| By Channel | `kpi_marketing_business_plan` | `channel` | `GROUP BY channel` |

### Contracts Section

| KPI | Source Table | Column(s) | Calculation |
|-----|--------------|-----------|-------------|
| Total Contracts | `sd_contract` | `CONTRACT_NO` | `COUNT(DISTINCT CONTRACT_NO)` |
| Total Quantity | `sd_contract` | `CON_QTY` | `SUM(CON_QTY)` |
| Delivered Quantity | `sd_contract` | `DELIVER_QTY` | `SUM(DELIVER_QTY)` |
| Pending Quantity | `sd_contract` | `PENDING_QTY` | `SUM(PENDING_QTY)` |
| Fulfillment Rate | Calculated | - | `(Delivered / Total) * 100` |

---

## Data Flow

```
1. API Request (/api/v1/dashboard/crm?date=YYYY-MM-DD)
        ↓
2. CRMDataProcessor.process_date(date)
   - Queries:
     • sd_sales_order (TD + MTD)
     • sd_sales_status (TD + MTD)
     • sd_outbound_delivery (TD + MTD)
     • sd_inquiry (TD)
     • kpi_marketing_customer_survey_report (Latest FY)
     • kpi_marketing_business_plan (Current month)
     • sd_contract (All active)
   - Builds sections:
     • sales_orders: TD/MTD metrics, by channel, top customers
     • billing: TD/MTD metrics, GST breakdown, export/domestic
     • deliveries: TD/MTD metrics, by customer
     • inquiries: Count, quantity, by segment
     • customer_survey: Ratings, chart data
     • business_plan: Targets by channel
     • contracts: Fulfillment tracking
     • highlights: Daily summary
        ↓
3. CRMClaudeInsightsGenerator.generate_insights(analysis_data, date)
   - Builds data context with sales metrics
   - Calls OpenAI GPT-4 API
   - Returns AI-generated insights HTML
        ↓
4. CRMTemplateEngine.generate_dashboard(...)
   - Loads sd_dashboard.html
   - Replaces all KPI placeholders
   - Injects customer detail rows
   - Injects chart data into JavaScript
   - Injects AI insights HTML
        ↓
5. Returns complete HTML dashboard
```

---

## Sample SQL Queries Used

### Sales Orders Query
```sql
SELECT
    SO_NO, SO_DATE, SOLD_TO_PARTY, SOLD_TO_PARTY_NAME,
    MATERIAL, MATERIAL_DESC, ORDER_QUANTITY, SALES_UNIT,
    NET_PRICE, NET_VALUE, NET_VALUE_INR, DOCUMENT_CURRENCY,
    SIPPING_PLANT, SIPPING_PLANT_NAME, DIST_CHANNEL, DIST_CHANNEL_NAME,
    REGION, COUNTRY, ZONE, DIVISION_NAME
FROM sd_sales_order
WHERE SO_DATE >= '2026-01-01' AND SO_DATE <= '2026-01-15'
ORDER BY NET_VALUE_INR DESC
```

### Billing Query
```sql
SELECT
    BILLING_DOC_NO, BILLING_ITEM, INV_CREATED_ON,
    CUSTOMER_NAME, SOLD_TO_PARTY, CONTRACT_NO, ORDER_NO,
    MATERIAL_NO, MATERIAL_DESC, DELIVERY_NO, DELIVERY_DATE,
    NET_WEIGHT, INV_AMT, INV_USD, RATE_MT,
    DEST_COUNTRY, DIST_CHANNEL, ZGROUP,
    IGST_AMT, CGST_AMT, SGST_AMT, VEHICLE_NO, TRANSPORTER
FROM sd_sales_status
WHERE INV_CREATED_ON >= '2026-01-01' AND INV_CREATED_ON <= '2026-01-15'
ORDER BY INV_AMT DESC
```

### Deliveries Query
```sql
SELECT
    DELIVERY_NO, DELIVERY_ITEM, GOODS_ISSUE_DT, DELIVERY_DATE,
    SHIP_PARTY, SHIP_PARTY_NAME, SOLD_PARTY, SOLD_PARTY_NAME,
    MATERIAL_NO, DELIVERY_TYPE, NET_WEIGHT, TOTAL_WEIGHT,
    SHIP_PARTY_LOCA, SOLD_PARTY_LOCA, GOODS_MNT_STATUS
FROM sd_outbound_delivery
WHERE GOODS_ISSUE_DT >= '2026-01-01' AND GOODS_ISSUE_DT <= '2026-01-15'
ORDER BY DELIVERY_NO
```

### Inquiries Query
```sql
SELECT
    INQUIRY_NO, DOC_CATEGORY, DOCUMENT_DATE,
    CUSTOMER_NO, CUSTOMER_NAME, MATERIAL_NO, MATERIAL_DESC,
    SEGMENT, INQ_QTY, PRICE, PLANT, PLANT_NAME,
    DELIVER_QTY, PENDING_QTY
FROM sd_inquiry
WHERE DOCUMENT_DATE >= '2026-01-01' AND DOCUMENT_DATE <= '2026-01-15'
ORDER BY DOCUMENT_DATE DESC
```

### Customer Survey Query
```sql
SELECT DISTINCT FIN_YEAR
FROM kpi_marketing_customer_survey_report
ORDER BY FIN_YEAR DESC
LIMIT 1
-- Then:
SELECT
    COMPANY_NAME, SEGMENT,
    PRODUCT_QUALITY, ORDER_EXECUTION, SERVICE_ATTITUDE,
    PRODUCT_PRICE, RELATIONSHIP_COMPANY, CUSTOMER_LOYALTY,
    BUSINESS_SYSTEM, COMPANY_REPUTATION, CUSTOMER_AVG_RATING
FROM kpi_marketing_customer_survey_report
WHERE FIN_YEAR = '2024-2025'
ORDER BY CUSTOMER_AVG_RATING DESC
```

### Business Plan Query
```sql
SELECT
    customer, plant, channel, segment, oem_trad, kam,
    contract_no, order_qty_mt, target_price, dispatch_target_mt
FROM kpi_marketing_business_plan
WHERE month_year = 'JAN-2026'
ORDER BY dispatch_target_mt DESC
```

### Contracts Query
```sql
SELECT
    CONTRACT_NO, INQUIRY_NO, DOCUMENT_DATE,
    CUSTOMER_NO, CUSTOMER_NAME, MATERIAL_NO, MATERIAL_DESC,
    SEGMENT, CON_QTY, PRICE, PLANT, PLANT_NAME,
    DELIVER_QTY, PENDING_QTY
FROM sd_contract
ORDER BY DOCUMENT_DATE DESC
LIMIT 100
```

---

## Currency Display Format

| Value Range | Display Format | Example |
|-------------|----------------|---------|
| < ₹1 Lakh | ₹X,XXX | ₹50,000 |
| ₹1 L - ₹99 L | ₹X.XX L | ₹25.50 L |
| >= ₹1 Crore | ₹X.XX Cr | ₹1.25 Cr |

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

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No data displayed | Check if data exists for the requested date in SD tables |
| Customer count wrong | Check `SOLD_TO_PARTY_NAME` column for duplicates/NULL |
| Billing value mismatch | Verify `INV_AMT` column for NULL values |
| GST total wrong | Check `IGST_AMT`, `CGST_AMT`, `SGST_AMT` columns |
| Export % showing 100% | Verify `DEST_COUNTRY` column (empty = domestic) |
| Survey data old | Survey is annual; check `FIN_YEAR` in survey table |
| Business plan empty | Check if `month_year` format matches (e.g., "JAN-2026") |
| Contract pending wrong | Verify `DELIVER_QTY` and `PENDING_QTY` not NULL |

---

## Contact

**Department Lead**: @crm-lead
**Branch**: `dept/crm`

For questions or issues, contact the BAL-Agentic-Backend Team.
