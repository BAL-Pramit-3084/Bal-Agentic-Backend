"""
scm_claude_analyzer.py
======================
AI insights generator for SCM (Supply Chain Management) Dashboard.

Takes processed SCM data and generates intelligent analysis/insights
in HTML format for dashboard injection.

Author: Senior ML Engineer
Date: November 2025

Migration Notes (2025-12-16):
- Migrated from Claude API to Local LLM (Qwen 2.5:72B on DigitalOcean H200)
- All Claude API code preserved as comments for easy rollback
- SSH Tunnel Required: ssh -L 11435:localhost:11434 pramit@107.170.2.49
"""

import os
import json
import logging
from typing import Dict, Any, Optional

# ============================================================================
# LEGACY IMPORT - PRESERVED FOR ROLLBACK
# ============================================================================
# from anthropic import Anthropic  # Commented out 2025-12-16 - Replaced with OpenAI SDK

# ============================================================================
# NEW IMPORT - LOCAL LLM INTEGRATION
# ============================================================================
from openai import OpenAI  # OpenAI-compatible SDK for local LLM

logger = logging.getLogger(__name__)


# ============================================================================
# CLAUDE INSIGHTS GENERATOR
# ============================================================================

class SCMClaudeInsightsGenerator:
    """
    Generate AI-powered insights for SCM dashboard using Local LLM.

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
        # self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        # if not self.api_key:
        #     logger.warning("No Anthropic API key found - insights will be placeholder")
        #     self.client = None
        # else:
        #     self.client = Anthropic(api_key=self.api_key)
        #     logger.info("SCM Claude Insights Generator initialized")

        # ====================================================================
        # NEW CODE - LOCAL LLM INTEGRATION
        # ====================================================================
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.base_url = base_url
        logger.info(f"SCM Local LLM Insights Generator initialized")
        logger.info(f"Model: {model}")
        logger.info(f"Endpoint: {base_url}")
        logger.info(f"SSH Tunnel Required: ssh -L 11435:localhost:11434 pramit@107.170.2.49")

    def generate_insights(self, analysis_data: Dict[str, Any], date: str) -> str:
        """
        Generate HTML insights from SCM data.

        Args:
            analysis_data: Processed data from SCMDataProcessor
            date: Date string (YYYY-MM-DD)

        Returns:
            HTML string with insights cards
        """
        # ====================================================================
        # LEGACY CODE - PRESERVED FOR ROLLBACK
        # ====================================================================
        # if not self.client:
        #     return self._generate_placeholder_insights(analysis_data, date)

        try:
            # Build prompt with data summary
            prompt = self._build_prompt(analysis_data, date)

            # ====================================================================
            # LEGACY CODE - CLAUDE API (PRESERVED FOR ROLLBACK)
            # ====================================================================
            # response = self.client.messages.create(
            #     model="claude-sonnet-4-20250514",
            #     max_tokens=2000,
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
                max_tokens=2000,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract text from OpenAI-compatible response
            insights_html = response.choices[0].message.content

            # Clean up if needed (remove markdown code blocks if present)
            insights_html = self._clean_response(insights_html)

            logger.info(f"SCM Local LLM insights generated successfully ({len(insights_html)} characters)")
            return insights_html

        except Exception as e:
            logger.error(f"Error calling Local LLM API: {e}", exc_info=True)
            logger.error(f"Ensure SSH tunnel is active: ssh -L 11435:localhost:11434 pramit@107.170.2.49")
            return self._generate_placeholder_insights(analysis_data, date)

    def _build_prompt(self, data: Dict[str, Any], date: str) -> str:
        """Build the prompt for Claude."""

        # Extract key metrics
        metrics = data.get("summary_metrics", {})
        po = data.get("purchase_orders", {})
        pr = data.get("purchase_requisitions", {})
        charts = data.get("charts", {})

        # Build data summary
        data_summary = f"""
## SCM Daily Data for {data.get('formatted_date', date)}

### Purchase Orders Summary
- Total POs Created: {metrics.get('po_count', 0)}
- Total Line Items: {metrics.get('po_line_items', 0)}
- Total PO Value: ₹{metrics.get('po_total_value', 0):,.0f}
- Average per Item: ₹{metrics.get('avg_per_item', 0):,.0f}
- Unique Vendors: {metrics.get('vendor_count', 0)}
- Purchasing Groups Active: {metrics.get('purch_groups', 0)}
- Pending Delivery: {po.get('pending_pct', 100):.0f}%

### Top Vendors by Value
"""
        for v in po.get("by_vendor", [])[:5]:
            data_summary += f"- {v.get('name', 'Unknown')}: {v.get('value_formatted', '₹0')}\n"

        data_summary += f"""
### PO Distribution by Plant
"""
        for p in po.get("by_plant", []):
            data_summary += f"- {p.get('name', 'Unknown')}: {p.get('value_formatted', '₹0')} ({p.get('po_count', 0)} POs)\n"

        data_summary += f"""
### Top Material Categories
"""
        for c in po.get("by_category", [])[:5]:
            data_summary += f"- {c.get('name', 'Unknown')}: {c.get('value_formatted', '₹0')}\n"

        data_summary += f"""
### Purchase Requisitions Summary
- Total PRs Created: {pr.get('count', 0)}
- Total Line Items: {pr.get('line_items', 0)}
- Total PR Value: {pr.get('total_value_formatted', '₹0')}

### Top PO Details
"""
        for item in po.get("details", [])[:5]:
            data_summary += f"- {item.get('po_no', '')}: {item.get('material', '')[:40]} - {item.get('value_formatted', '₹0')} ({item.get('vendor', '')[:20]})\n"

        prompt = f"""You are an SCM (Supply Chain Management) analyst for Balasore Alloys Limited, a ferrochrome manufacturing company.

Analyze this daily procurement data and generate insightful observations in HTML format.

{data_summary}

Generate exactly 6 insight cards as HTML. Each card MUST follow this EXACT format with the correct CSS class based on severity:

For CRITICAL issues (high risk, immediate attention needed):
<div class="insight-item insight-critical">
    <h3>[Number]. [Short Title]</h3>
    <p><strong>Finding:</strong> [Key observation with specific numbers]</p>
    <p><strong>Risk:</strong> [What could go wrong]</p>
    <p><strong>Recommendation:</strong> [Action to take]</p>
</div>

For WARNING issues (needs monitoring):
<div class="insight-item insight-warning">
    <h3>[Number]. [Short Title]</h3>
    <p><strong>Finding:</strong> [Key observation]</p>
    <p><strong>Details:</strong> [Supporting data]</p>
    <p><strong>Recommendation:</strong> [Action to take]</p>
</div>

For INFO observations (neutral insights):
<div class="insight-item insight-info">
    <h3>[Number]. [Short Title]</h3>
    <p><strong>Observation:</strong> [Key insight with numbers]</p>
    <p><strong>Details:</strong> [Supporting information]</p>
</div>

For SUCCESS/positive findings:
<div class="insight-item insight-success">
    <h3>[Number]. [Short Title]</h3>
    <p><strong>Finding:</strong> [Positive observation]</p>
    <p><strong>Details:</strong> [Why this is good]</p>
</div>

Guidelines:
- Use insight-critical for: vendor concentration >80%, delivery risks, high-value single orders
- Use insight-warning for: pending deliveries, low conversion rates, budget concerns
- Use insight-info for: plant distribution, category breakdown, general patterns
- Use insight-success for: good diversity, positive trends, best practices

Rules:
- Use specific numbers from the data (use Indian format: Lakhs/Crores)
- Keep each insight to 2-4 bullet points
- Be actionable and business-focused
- Output ONLY the 6 HTML divs, no other text or markdown
- Mix the severity types appropriately based on the data
"""

        return prompt

    def _clean_response(self, response: str) -> str:
        """Clean up Claude's response."""
        # Remove markdown code blocks if present
        response = response.strip()
        if response.startswith("```html"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        return response.strip()

    def _generate_placeholder_insights(self, data: Dict[str, Any], date: str) -> str:
        """Generate placeholder insights when Claude API is unavailable."""

        metrics = data.get("summary_metrics", {})
        po = data.get("purchase_orders", {})
        pr = data.get("purchase_requisitions", {})

        po_count = metrics.get("po_count", 0)
        po_value = metrics.get("po_total_value", 0)
        vendor_count = metrics.get("vendor_count", 0)
        pr_count = pr.get("count", 0)

        # Format value
        if po_value >= 10000000:
            value_str = f"₹{po_value/10000000:.2f} Cr"
        elif po_value >= 100000:
            value_str = f"₹{po_value/100000:.2f} L"
        else:
            value_str = f"₹{po_value:,.0f}"

        # Get top vendor
        top_vendor = po.get("by_vendor", [{}])[0] if po.get("by_vendor") else {}
        top_vendor_name = top_vendor.get("name", "N/A")
        top_vendor_value = top_vendor.get("value_formatted", "₹0")

        # Get top category
        top_category = po.get("by_category", [{}])[0] if po.get("by_category") else {}
        top_category_name = top_category.get("name", "N/A")

        return f"""
        <div class="insight-item insight-info">
            <h3>1. Daily Procurement Summary</h3>
            <p><strong>Overview:</strong> Today's procurement activity includes {po_count} Purchase Orders worth {value_str} across {vendor_count} vendors.</p>
            <p><strong>Details:</strong> This represents the day's total authorized purchasing activity for Balasore Alloys operations.</p>
        </div>
        <div class="insight-item insight-warning">
            <h3>2. Top Vendor Concentration</h3>
            <p><strong>Finding:</strong> The highest value PO today was placed with {top_vendor_name} for {top_vendor_value}.</p>
            <p><strong>Recommendation:</strong> Monitor vendor concentration to ensure supply chain diversification and reduce dependency risk.</p>
        </div>
        <div class="insight-item insight-info">
            <h3>3. Purchase Requisition Pipeline</h3>
            <p><strong>Status:</strong> {pr_count} new Purchase Requisitions were created today with {pr.get('line_items', 0)} line items.</p>
            <p><strong>Details:</strong> These represent future procurement needs awaiting PO conversion.</p>
        </div>
        <div class="insight-item insight-info">
            <h3>4. Material Category Focus</h3>
            <p><strong>Observation:</strong> The dominant material category today is {top_category_name}.</p>
            <p><strong>Recommendation:</strong> Categorize spend regularly to identify cost optimization opportunities.</p>
        </div>
        <div class="insight-item insight-critical">
            <h3>5. Delivery Status Alert</h3>
            <p><strong>Finding:</strong> All {po_count} POs created today are pending delivery.</p>
            <p><strong>Risk:</strong> Delayed deliveries could impact production schedules.</p>
            <p><strong>Recommendation:</strong> Set up delivery tracking and follow-up schedules with vendors.</p>
        </div>
        <div class="insight-item insight-success">
            <h3>6. Recommended Actions</h3>
            <p><strong>Priority Tasks:</strong> Review high-value orders for delivery timeline confirmation.</p>
            <p><strong>Follow-up:</strong> Ensure PR-to-PO conversion is timely for pending requisitions.</p>
        </div>
"""


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def generate_scm_insights(
    analysis_data: Dict[str, Any],
    date: str,
    api_key: str = "ollama",
    model: str = "qwen2.5:72b-instruct-q4_K_M",
    base_url: str = "http://localhost:11435/v1"
) -> str:
    """
    Convenience function to generate SCM insights using local LLM.

    Args:
        analysis_data: Data from SCMDataProcessor
        date: Date string (YYYY-MM-DD)
        api_key: API key (default "ollama" for local)
        model: Model name (default Qwen 2.5:72B)
        base_url: Local LLM endpoint

    Returns:
        HTML string with insights
    """
    # ========================================================================
    # LEGACY CODE - PRESERVED FOR ROLLBACK
    # ========================================================================
    # generator = SCMClaudeInsightsGenerator(api_key)

    # ========================================================================
    # NEW CODE - LOCAL LLM
    # ========================================================================
    generator = SCMClaudeInsightsGenerator(api_key, model, base_url)
    return generator.generate_insights(analysis_data, date)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['SCMClaudeInsightsGenerator', 'generate_scm_insights']