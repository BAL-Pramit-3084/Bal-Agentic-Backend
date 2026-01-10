"""
crm_claude_analyzer.py
======================
AI-powered insights from CRM/Sales & Distribution data.

This module:
1. Takes analysisData from CRMDataProcessor
2. Builds a structured prompt for LLM
3. Calls Local LLM API (or Claude API as fallback)
4. Returns formatted HTML insights section

Insight Categories:
- Critical: Customer concentration, data quality issues
- Warning: Channel imbalance, pricing variance, pipeline concerns
- Success: Strong performance, premium pricing, market reach
- Info: Working capital, geographic distribution, trends

Author: Senior ML Engineer
Date: November 2025

Migration Notes (2025-12-16):
- Migrated from Claude API to Local LLM (Qwen 2.5:72B on DigitalOcean H200)
- All Claude API code preserved as comments for easy rollback
- SSH Tunnel Required: ssh -L 11435:localhost:11434 pramit@107.170.2.49
"""

import logging
import json
from typing import Dict, Any, Optional

# ============================================================================
# LEGACY IMPORT - PRESERVED FOR ROLLBACK
# ============================================================================
# import anthropic  # Commented out 2025-12-16 - Replaced with OpenAI SDK

# ============================================================================
# NEW IMPORT - LOCAL LLM INTEGRATION
# ============================================================================
from openai import OpenAI  # OpenAI-compatible SDK for local LLM

logger = logging.getLogger(__name__)


# ============================================================================
# CRM CLAUDE INSIGHTS GENERATOR
# ============================================================================

class CRMClaudeInsightsGenerator:
    """
    Generate executive insights from CRM/Sales & Distribution data using Local LLM.

    Migration Note (2025-12-16): Now uses OpenAI-compatible API for local Qwen 2.5:72B model.
    """

    def __init__(
        self,
        api_key: str = "ollama",
        model: str = "qwen2.5:72b-instruct-q4_K_M",
        base_url: str = "http://localhost:11435/v1"
    ):
        """
        Initialize Local LLM client (OpenAI-compatible).

        Args:
            api_key: API key (default "ollama" for local LLM)
            model: Model name (default Qwen 2.5:72B)
            base_url: Local LLM endpoint (requires SSH tunnel)
        """
        # ====================================================================
        # LEGACY CODE - PRESERVED FOR ROLLBACK
        # ====================================================================
        # self.client = anthropic.Anthropic(api_key=api_key)
        # self.model = model
        # logger.info(f"CRM Claude Insights Generator initialized with model: {model}")

        # ====================================================================
        # NEW CODE - LOCAL LLM INTEGRATION
        # ====================================================================
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.base_url = base_url
        logger.info(f"CRM Local LLM Insights Generator initialized")
        logger.info(f"Model: {model}")
        logger.info(f"Endpoint: {base_url}")
        logger.info(f"SSH Tunnel Required: ssh -L 11435:localhost:11434 pramit@107.170.2.49")

    def generate_insights(self, analysis_data: Dict[str, Any], date: str) -> str:
        """
        Generate insights HTML from analysis data.

        Args:
            analysis_data: The analysisData dict from CRMDataProcessor
            date: Date string (YYYY-MM-DD)

        Returns:
            HTML string for the insights section
        """
        logger.info(f"Generating CRM Claude insights for date: {date}")

        # Build the prompt
        prompt = self._build_prompt(analysis_data, date)

        try:
            # ====================================================================
            # LEGACY CODE - CLAUDE API (PRESERVED FOR ROLLBACK)
            # ====================================================================
            # response = self.client.messages.create(
            #     model=self.model,
            #     max_tokens=4096,
            #     temperature=0.7,
            #     messages=[
            #         {"role": "user", "content": prompt}
            #     ]
            # )
            # insights_html = response.content[0].text

            # ====================================================================
            # NEW CODE - LOCAL LLM API (OPENAI-COMPATIBLE)
            # ====================================================================
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract text from OpenAI-compatible response
            insights_html = response.choices[0].message.content

            # Clean up any markdown artifacts
            insights_html = self._clean_response(insights_html)

            logger.info(f"CRM Local LLM insights generated successfully ({len(insights_html)} characters)")
            return insights_html

        except Exception as e:
            logger.error(f"Error calling Local LLM API: {e}", exc_info=True)
            logger.error(f"Ensure SSH tunnel is active: ssh -L 11435:localhost:11434 pramit@107.170.2.49")
            return self._generate_fallback_insights(analysis_data)

    def _build_prompt(self, data: Dict[str, Any], date: str) -> str:
        """
        Build the prompt for Claude - CRM/Sales & Distribution specific.
        """
        # Prepare data summary for prompt
        data_summary = self._prepare_data_summary(data)

        prompt = f"""You are an expert Sales & Marketing analyst reviewing daily CRM data for Balasore Alloys Limited (ferrochrome manufacturer) on {date}.

**YOUR TASK:**
Generate 6-8 executive insights analyzing the sales, billing, and delivery performance. Include actionable recommendations.

**DATA SUMMARY:**
{data_summary}

**OUTPUT REQUIREMENTS:**

Generate HTML insights using these CSS classes. Each insight MUST follow this EXACT format:

For CRITICAL issues (immediate attention needed):
```html
<div class="insight-item insight-critical">
    <h3 class="insight-title">[Number]. [Short Title]</h3>
    <p class="insight-content">
        <strong>Critical Finding:</strong> [Key observation with specific numbers]<br><br>
        <strong>Risk:</strong> [What could go wrong]<br><br>
        <strong>Recommendation:</strong> [Specific action to take]
    </p>
</div>
```

For WARNING issues (needs monitoring):
```html
<div class="insight-item insight-warning">
    <h3 class="insight-title">[Number]. [Short Title]</h3>
    <p class="insight-content">
        <strong>Finding:</strong> [Key observation with numbers]<br><br>
        <strong>Risk:</strong> [Potential impact]<br><br>
        <strong>Action:</strong> [What to do]
    </p>
</div>
```

For SUCCESS/positive findings:
```html
<div class="insight-item insight-success">
    <h3 class="insight-title">[Number]. [Short Title]</h3>
    <p class="insight-content">
        <strong>Strength:</strong> [Positive observation with numbers]<br><br>
        <strong>Insight:</strong> [Why this matters]<br><br>
        <strong>Strategy:</strong> [How to leverage this]
    </p>
</div>
```

For INFO/neutral observations:
```html
<div class="insight-item insight-info">
    <h3 class="insight-title">[Number]. [Short Title]</h3>
    <p class="insight-content">
        <strong>Analysis:</strong> [Key observation with numbers]<br><br>
        <strong>Impact:</strong> [Business implications]<br><br>
        <strong>Opportunity:</strong> [Potential actions]
    </p>
</div>
```

**INSIGHT GUIDELINES:**

Use insight-critical for:
- Customer concentration >40% from single customer
- Missing/NULL data in critical fields
- Zero orders or zero deliveries
- Billing delays >30 days

Use insight-warning for:
- Channel imbalance (>70% export or domestic)
- Price variance >15% for same product
- Low order velocity (below average)
- Geographic concentration

Use insight-success for:
- Premium pricing maintained
- 100% delivery completion
- Multi-market reach (exports to multiple countries)
- Strong order value

Use insight-info for:
- Working capital analysis
- Billing vs delivery ratio
- Customer satisfaction insights
- MTD progress tracking

**IMPORTANT NOTES:**
- Use ACTUAL numbers from the data provided
- Be specific about customer names, values, percentages
- Include both positive findings and areas of concern
- End with 2-3 actionable items for tomorrow
- Output pure HTML only - no markdown, no code blocks
- DO NOT include ```html or ``` markers

**NOW GENERATE THE HTML INSIGHTS (6-8 insights, pure HTML only):**"""

        return prompt

    def _prepare_data_summary(self, data: Dict[str, Any]) -> str:
        """
        Prepare a concise data summary for the prompt.
        """
        # Sales Orders
        so = data.get('sales_orders', {})
        so_td = so.get('td', {})
        so_mtd = so.get('mtd', {})
        so_pct = so.get('td_pct_of_mtd', {})
        top_order_customers = so.get('top_customers', [])[:5]

        # Billing
        bill = data.get('billing', {})
        bill_td = bill.get('td', {})
        bill_mtd = bill.get('mtd', {})
        bill_exp_dom = bill.get('export_domestic', {})
        top_billed = bill.get('top_customers', [])[:5]
        gst = bill.get('gst', {})

        # Deliveries
        del_data = data.get('deliveries', {})
        del_td = del_data.get('td', {})
        del_mtd = del_data.get('mtd', {})

        # Survey
        survey = data.get('customer_survey', {})

        # Contracts
        contracts = data.get('contracts', {})

        # Highlights
        highlights = data.get('highlights', {})
        concentration = highlights.get('concentration', {})
        channel_split = highlights.get('channel_split', {})

        summary = f"""
=== SALES ORDERS ===
Today (TD): {so_td.get('count', 0)} orders | {so_td.get('qty', 0):.0f} MT | {so_td.get('value_formatted', '₹0')} | {so_td.get('customers', 0)} customers
MTD: {so_mtd.get('count', 0)} orders | {so_mtd.get('qty', 0):.0f} MT | {so_mtd.get('value_formatted', '₹0')}
TD as % of MTD: {so_pct.get('count', 0):.1f}% (orders) | {so_pct.get('value', 0):.1f}% (value)
Avg Order Price: {so_td.get('avg_price_formatted', '₹0')}/MT

Top Order Customers Today:
{self._format_customer_list(top_order_customers, 'orders')}

Channel Split (Orders): Export {channel_split.get('export_pct', 0):.1f}% | Domestic {channel_split.get('domestic_pct', 0):.1f}%

=== BILLING/INVOICES ===
Today (TD): {bill_td.get('invoice_count', 0)} invoices | {bill_td.get('weight', 0):.0f} MT | {bill_td.get('value_formatted', '₹0')} | {bill_td.get('customers', 0)} customers
MTD: {bill_mtd.get('invoice_count', 0)} invoices | {bill_mtd.get('weight', 0):.0f} MT | {bill_mtd.get('value_formatted', '₹0')}
Avg Rate: {bill_td.get('avg_rate_formatted', '₹0')}/MT

Export vs Domestic (Billing):
- Export: {bill_exp_dom.get('export_pct', 0):.1f}% (${bill_exp_dom.get('export_usd', 0):,.0f} USD)
- Domestic: {bill_exp_dom.get('domestic_pct', 0):.1f}%

GST Collected: {gst.get('total_formatted', '₹0')} (IGST: ₹{gst.get('igst', 0)/100000:.2f}L | CGST+SGST: ₹{(gst.get('cgst', 0) + gst.get('sgst', 0))/100000:.2f}L)

Top Billed Customers Today:
{self._format_customer_list(top_billed, 'billing')}

Customer Concentration: {concentration.get('top_customer', 'N/A')} = {concentration.get('top_customer_pct', 0):.1f}% of revenue

=== DELIVERIES ===
Today (TD): {del_td.get('count', 0)} deliveries | {del_td.get('weight', 0):.0f} MT | {del_td.get('customers', 0)} customers
MTD: {del_mtd.get('count', 0)} deliveries | {del_mtd.get('weight', 0):.0f} MT
Avg per Delivery: {del_td.get('avg_per_delivery', 0):.1f} MT

Billing vs Delivery Ratio: {bill_td.get('invoice_count', 0)} invoices vs {del_td.get('count', 0)} deliveries

=== CUSTOMER SATISFACTION (FY {data.get('financial_year', '2024-2025')}) ===
Overall Rating: {survey.get('overall_avg', 0):.2f}/5 ({survey.get('respondents', 0)} respondents)
Ratings: Quality {survey.get('avg_ratings', {}).get('product_quality', 0):.2f} | Execution {survey.get('avg_ratings', {}).get('order_execution', 0):.2f} | Service {survey.get('avg_ratings', {}).get('service_attitude', 0):.2f} | Price {survey.get('avg_ratings', {}).get('product_price', 0):.2f}

=== CONTRACTS ===
Total Contracts: {contracts.get('total_contracts', 0)} | Total Qty: {contracts.get('total_qty', 0):,.0f} MT
Contracts with NULL delivery data: {contracts.get('null_delivery_count', 0)} (Data Quality Issue: {contracts.get('data_quality_issue', False)})

=== INQUIRIES ===
Today: {data.get('inquiries', {}).get('count', 0)} inquiries
"""

        return summary

    def _format_customer_list(self, customers: list, context: str) -> str:
        """Format customer list for prompt."""
        if not customers:
            return "  (No data)"

        lines = []
        for i, c in enumerate(customers[:5], 1):
            name = c.get('name', 'Unknown')[:25]
            if context == 'orders':
                value = c.get('value', 0)
                qty = c.get('qty', 0)
                lines.append(f"  {i}. {name}: {qty:.0f} MT, ₹{value/10000000:.2f} Cr")
            else:  # billing
                value = c.get('value', 0)
                pct = c.get('pct_revenue', 0)
                lines.append(f"  {i}. {name}: ₹{value/10000000:.2f} Cr ({pct:.1f}%)")

        return "\n".join(lines)

    def _clean_response(self, response: str) -> str:
        """Clean up Claude's response - remove markdown artifacts."""
        # Remove code block markers
        response = response.replace("```html", "").replace("```", "")
        # Remove leading/trailing whitespace
        response = response.strip()
        return response

    def _generate_fallback_insights(self, data: Dict[str, Any]) -> str:
        """
        Generate basic fallback insights if Claude API fails.
        """
        logger.warning("Generating fallback CRM insights due to API failure")

        try:
            so_td = data.get('sales_orders', {}).get('td', {})
            bill_td = data.get('billing', {}).get('td', {})
            del_td = data.get('deliveries', {}).get('td', {})
            highlights = data.get('highlights', {})
            concentration = highlights.get('concentration', {})

            order_count = so_td.get('count', 0)
            order_value = so_td.get('value_formatted', '₹0')
            invoice_count = bill_td.get('invoice_count', 0)
            invoice_value = bill_td.get('value_formatted', '₹0')
            delivery_count = del_td.get('count', 0)
            top_customer = concentration.get('top_customer', 'N/A')
            top_customer_pct = concentration.get('top_customer_pct', 0)

            html = f"""
<div class="insight-item insight-info">
    <h3 class="insight-title">1. Daily Sales Summary</h3>
    <p class="insight-content">
        <strong>Overview:</strong> Today's sales activity includes {order_count} orders worth {order_value}.<br><br>
        <strong>Details:</strong> {invoice_count} invoices processed with total billing of {invoice_value}. {delivery_count} deliveries executed.
    </p>
</div>

<div class="insight-item insight-warning">
    <h3 class="insight-title">2. Customer Concentration</h3>
    <p class="insight-content">
        <strong>Finding:</strong> {top_customer} represents {top_customer_pct:.1f}% of daily billing revenue.<br><br>
        <strong>Recommendation:</strong> Monitor customer concentration to ensure diversified revenue streams.
    </p>
</div>

<div class="insight-item insight-info">
    <h3 class="insight-title">3. Billing & Delivery Activity</h3>
    <p class="insight-content">
        <strong>Analysis:</strong> {invoice_count} invoices vs {delivery_count} deliveries processed today.<br><br>
        <strong>Note:</strong> Review billing-to-delivery ratio for working capital optimization.
    </p>
</div>

<div class="insight-item insight-warning">
    <h3 class="insight-title">4. AI Analysis Unavailable</h3>
    <p class="insight-content">
        <strong>Note:</strong> Detailed AI-powered analysis is temporarily unavailable.<br><br>
        <strong>Action:</strong> Please review the charts and tables above for complete metrics. Contact IT if this persists.
    </p>
</div>
"""
            return html

        except Exception as e:
            logger.error(f"Error generating fallback insights: {e}")
            return """
<div class="insight-item insight-warning">
    <h3 class="insight-title">Analysis Unavailable</h3>
    <p class="insight-content">
        <strong>Note:</strong> AI-powered insights are temporarily unavailable. Please review the dashboard metrics manually.
    </p>
</div>
"""


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def generate_crm_insights(
    analysis_data: Dict[str, Any],
    date: str,
    api_key: str = "ollama",
    model: str = "qwen2.5:72b-instruct-q4_K_M",
    base_url: str = "http://localhost:11435/v1"
) -> str:
    """
    Convenience function to generate CRM insights using local LLM.

    Args:
        analysis_data: Analysis data from CRMDataProcessor
        date: Date string
        api_key: API key (default "ollama" for local)
        model: Model name (default Qwen 2.5:72B)
        base_url: Local LLM endpoint

    Returns:
        HTML string with insights
    """
    # ========================================================================
    # LEGACY CODE - PRESERVED FOR ROLLBACK
    # ========================================================================
    # generator = CRMClaudeInsightsGenerator(api_key, model)

    # ========================================================================
    # NEW CODE - LOCAL LLM
    # ========================================================================
    generator = CRMClaudeInsightsGenerator(api_key, model, base_url)
    return generator.generate_insights(analysis_data, date)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['CRMClaudeInsightsGenerator', 'generate_crm_insights']


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test with sample data"""
    import os

    # Sample minimal data for testing
    test_data = {
        "date": "2025-11-17",
        "date_formatted": "Monday, November 17, 2025",
        "financial_year": "2025-2026",
        "sales_orders": {
            "td": {
                "count": 5,
                "qty": 495,
                "value": 53831250,
                "value_formatted": "₹5.38 Cr",
                "customers": 4,
                "avg_price_formatted": "₹1.09 L"
            },
            "mtd": {
                "count": 49,
                "value": 685133497,
                "value_formatted": "₹68.51 Cr"
            },
            "td_pct_of_mtd": {"count": 10.2, "value": 7.9},
            "top_customers": [
                {"name": "QUALITY CHROME", "qty": 150, "value": 17625000},
                {"name": "MORTEX INDIA", "qty": 200, "value": 19650000}
            ]
        },
        "billing": {
            "td": {
                "invoice_count": 75,
                "weight": 1446,
                "value": 72220091,
                "value_formatted": "₹7.22 Cr",
                "customers": 15,
                "avg_rate_formatted": "₹49,945"
            },
            "mtd": {"invoice_count": 689, "value_formatted": "₹66.32 Cr"},
            "export_domestic": {
                "export_pct": 55.4,
                "domestic_pct": 44.6,
                "export_usd": 452977
            },
            "gst": {"total_formatted": "₹23.30 L", "igst": 2236000, "cgst": 47000, "sgst": 47000},
            "top_customers": [
                {"name": "GLOBUS 8 ALLOYS", "value": 33581562, "pct_revenue": 46.5}
            ]
        },
        "deliveries": {
            "td": {"count": 19, "weight": 457, "customers": 3, "avg_per_delivery": 24},
            "mtd": {"count": 380, "weight": 9140}
        },
        "customer_survey": {
            "has_data": True,
            "overall_avg": 3.98,
            "respondents": 17,
            "avg_ratings": {
                "product_quality": 4.06,
                "order_execution": 4.00,
                "service_attitude": 3.94,
                "product_price": 3.47
            }
        },
        "contracts": {
            "total_contracts": 859,
            "total_qty": 142964,
            "null_delivery_count": 859,
            "data_quality_issue": True
        },
        "inquiries": {"count": 0},
        "highlights": {
            "concentration": {"top_customer": "GLOBUS 8 ALLOYS", "top_customer_pct": 46.5},
            "channel_split": {"export_pct": 73.8, "domestic_pct": 26.2}
        }
    }

    # ========================================================================
    # LEGACY CODE - PRESERVED FOR ROLLBACK
    # ========================================================================
    # api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
    # if not api_key:
    #     print("❌ ANTHROPIC_API_KEY or CLAUDE_API_KEY not set in environment")

    # ========================================================================
    # NEW CODE - LOCAL LLM CONFIGURATION
    # ========================================================================
    # Get Local LLM configuration from environment
    api_key = os.getenv("LOCAL_LLM_API_KEY", "ollama")
    model = os.getenv("LOCAL_LLM_MODEL", "qwen2.5:72b-instruct-q4_K_M")
    base_url = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11435/v1")

    # Check if local LLM is enabled
    local_llm_enabled = os.getenv("LOCAL_LLM_ENABLED", "true").lower() == "true"

    if not local_llm_enabled:
        print("❌ LOCAL_LLM_ENABLED is set to false")
        print("✅ Set LOCAL_LLM_ENABLED=true in .env to use local LLM")
        print("⚠️  Ensure SSH tunnel is active: ssh -L 11435:localhost:11434 pramit@107.170.2.49")
        print("\nTesting fallback insights generation...")
        generator = CRMClaudeInsightsGenerator.__new__(CRMClaudeInsightsGenerator)
        fallback = generator._generate_fallback_insights(test_data)
        print("\n" + "="*70)
        print("FALLBACK INSIGHTS:")
        print("="*70)
        print(fallback)
    else:
        print("Testing CRM Local LLM Insights Generator...")
        print(f"Model: {model}")
        print(f"Endpoint: {base_url}")
        print(f"⚠️  Ensure SSH tunnel is active: ssh -L 11435:localhost:11434 pramit@107.170.2.49")
        generator = CRMClaudeInsightsGenerator(api_key, model, base_url)
        insights = generator.generate_insights(test_data, "2025-11-17")
        print("\n" + "="*70)
        print("GENERATED CRM INSIGHTS:")
        print("="*70)
        print(insights)