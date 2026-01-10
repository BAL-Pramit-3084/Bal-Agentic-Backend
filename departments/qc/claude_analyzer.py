"""
qc_claude_analyzer.py
=====================
AI-powered insights from QC data.

This module:
1. Takes analysisData from QCDataProcessor
2. Builds a structured prompt for LLM
3. Calls Local LLM API (or Claude API as fallback)
4. Returns formatted HTML insights section

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
# QC CLAUDE INSIGHTS GENERATOR
# ============================================================================

class QCClaudeInsightsGenerator:
    """
    Generate executive insights from QC operations data using Local LLM.

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
        # logger.info(f"QC Claude Insights Generator initialized with model: {model}")

        # ====================================================================
        # NEW CODE - LOCAL LLM INTEGRATION
        # ====================================================================
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.base_url = base_url
        logger.info(f"QC Local LLM Insights Generator initialized")
        logger.info(f"Model: {model}")
        logger.info(f"Endpoint: {base_url}")
        logger.info(f"SSH Tunnel Required: ssh -L 11435:localhost:11434 pramit@107.170.2.49")

    def generate_insights(self, analysis_data: Dict[str, Any], date: str) -> str:
        """
        Generate insights HTML from analysis data.

        Args:
            analysis_data: The analysisData dict from QCDataProcessor
            date: Date string (YYYY-MM-DD)

        Returns:
            HTML string for the insights section
        """
        logger.info(f"Generating QC Claude insights for date: {date}")

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

            logger.info(f"QC Local LLM insights generated successfully ({len(insights_html)} characters)")
            return insights_html

        except Exception as e:
            logger.error(f"Error calling Local LLM API: {e}", exc_info=True)
            logger.error(f"Ensure SSH tunnel is active: ssh -L 11435:localhost:11434 pramit@107.170.2.49")
            return self._generate_fallback_insights(analysis_data)

    def _build_prompt(self, data: Dict[str, Any], date: str) -> str:
        """
        Build the prompt for Claude - QC specific.

        Structure:
        1. Context and role
        2. Data (as JSON)
        3. Output requirements
        4. Examples of CSS classes
        """
        # Convert data to clean JSON (handling None values)
        data_json = self._prepare_data_for_prompt(data)

        prompt = f"""You are an expert Quality Control engineer analyzing ferrochrome quality operations data for {date}.

**YOUR TASK:**
Generate an executive summary with insights and analysis. DO NOT include any "Recommended Actions" section.

**DATA:**
{data_json}

**OUTPUT REQUIREMENTS:**

Generate HTML with these THREE sections ONLY:

1. **Strong Performance Highlights** (green box) - IF despatch achieved 100% of plan AND quality rate ≥98%
   - Use CSS class: "success-highlight"
   - Title CSS: "success-title"
   - Items CSS: "success-item"
   - Include: Despatch achievement, quality rate, fastest turnaround time, best performing furnace

2. **Key Quality Insights** (yellow box) - ALWAYS include
   - Use CSS class: "insights-section"
   - Title CSS: "insights-title"
   - Items CSS: "insight-item"
   - Include 6 insights covering:
     * Despatch Performance (plan vs actual, variance analysis by customer)
     * Quality Testing Efficiency (total tests, pass rate, turnaround time analysis)
     * Product Quality Trends (Cr%, C%, deviation from specification)
     * Heat Analysis Performance (best vs worst furnace, grade consistency)
     * Material Testing Distribution (which materials tested most, results)
     * Stock & WIP Status (current stock levels, pending lots)

3. **Immediate Action Required** (red box) - ONLY if critical issues found
   - Use CSS class: "critical-alert"
   - Title CSS: "critical-title"
   - Items CSS: "critical-item"
   - Include ONLY if:
     * Any customer despatch variance > 5 MT
     * Any product shows Cr% or C% deviation > 2% from spec
     * Average turnaround time > 120 minutes
     * Any furnace grade shows significant composition variance

**IMPORTANT NOTES:**
- Handle NULL values gracefully (say "data not available" or omit that metric)
- Use actual numbers from the data
- Be specific about which customer/product/furnace has issues
- Use icons: 🎯✅⚡🔬📊🧪 for insight-item spans with class "insight-icon"
- Format numbers properly (1 decimal for percentages, 2 decimals for composition)
- DO NOT include any "Recommended Actions" or "📈 Recommended Actions" section
- DO NOT use markdown - output pure HTML only
- Use <strong> tags for emphasis, not bold

**EXAMPLE HTML STRUCTURE:**
```html
<div class="success-highlight">
    <div class="success-title">✅ Strong Performance Highlights</div>
    <div class="success-item">🎯 <strong>Perfect despatch performance achieved</strong> with 269 MT despatched vs 269 MT planned (100% achievement)</div>
    <div class="success-item">⚡ <strong>Excellent quality rate at 98.5%</strong>, with only 2 lots failing out of 87 total tests</div>
    <div class="success-item">🔬 <strong>Fastest turnaround: 45 minutes</strong> for Lot QC-2025-1234, demonstrating efficient testing process</div>
</div>

<div class="insights-section">
    <div class="insights-title">💡 Key Quality Insights</div>
    <div class="insight-item">
        <span class="insight-icon">📦</span>
        <div>
            <strong>Despatch Performance:</strong> Customer ABC received 50 MT (highest allocation) while Customer XYZ received 15 MT (lowest).
            All 8 customers received planned quantities with zero variance.
        </div>
    </div>
    <div class="insight-item">
        <span class="insight-icon">⚡</span>
        <div>
            <strong>Testing Efficiency:</strong> Average turnaround time of 67 minutes with 65 QC lots processed.
            Chemical tests (38 tests) dominate testing load, followed by mechanical tests (25 tests).
        </div>
    </div>
    <div class="insight-item">
        <span class="insight-icon">🔬</span>
        <div>
            <strong>Product Quality:</strong> FeCr-HC60 shows excellent Cr% at 62.5% (target: 60-65%).
            FeCr-LC shows C% at 0.08% (target: <0.10%), maintaining specification compliance.
        </div>
    </div>
    <!-- ... more insights ... -->
</div>

<div class="critical-alert">
    <div class="critical-title">🚨 Immediate Action Required</div>
    <div class="critical-item">• <strong>Customer DEF:</strong> Despatch variance of +8 MT detected - investigate order accuracy and material allocation</div>
    <div class="critical-item">• <strong>FeCr-MC Product:</strong> Cr% at 56.2% (below 58% minimum spec) - review furnace charging and raw material quality</div>
</div>
```

**NOW GENERATE THE HTML INSIGHTS (pure HTML only, no markdown, no code blocks):**"""

        return prompt

    def _prepare_data_for_prompt(self, data: Dict[str, Any]) -> str:
        """
        Convert analysis data to clean JSON string for prompt.
        Handles None values properly.
        """
        # Create a copy and convert None to "null" string for clarity
        def clean_data(obj):
            if isinstance(obj, dict):
                return {k: clean_data(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_data(item) for item in obj]
            elif obj is None:
                return "null"
            else:
                return obj

        cleaned_data = clean_data(data)
        return json.dumps(cleaned_data, indent=2)

    def _generate_fallback_insights(self, data: Dict[str, Any]) -> str:
        """
        Generate basic fallback insights if Claude API fails.
        """
        logger.warning("Generating fallback QC insights due to API failure")

        # Extract key metrics safely
        try:
            despatch = data.get('despatch', {})
            total_actual = despatch.get('total_actual', 0) or 0
            total_plan = despatch.get('total_plan', 1) or 1
            achievement_pct = (total_actual / total_plan * 100) if total_plan > 0 else 0

            qc_summary = data.get('qc_summary', {})
            total_lots = qc_summary.get('total_qc_lots', 0) or 0
            total_tests = qc_summary.get('total_tests', 0) or 0

            # Simple fallback HTML
            html = f"""
<div class="insights-section">
    <div class="insights-title">📊 Quality Control Summary</div>
    <div class="insight-item">
        <span class="insight-icon">📦</span>
        <div>
            <strong>Despatch Status:</strong> {total_actual:.1f} MT despatched against planned {total_plan:.1f} MT
            (Achievement: {achievement_pct:.1f}%)
        </div>
    </div>
    <div class="insight-item">
        <span class="insight-icon">🔬</span>
        <div>
            <strong>Testing Activity:</strong> {total_lots} QC lots processed with {total_tests} total tests conducted
        </div>
    </div>
    <div class="insight-item">
        <span class="insight-icon">⚠️</span>
        <div>
            <strong>Note:</strong> Detailed AI analysis temporarily unavailable.
            Please review the charts and tables above for complete quality metrics.
        </div>
    </div>
</div>
"""
            return html

        except Exception as e:
            logger.error(f"Error generating fallback: {e}")
            return """
<div class="insights-section">
    <div class="insights-title">⚠️ Analysis Unavailable</div>
    <div class="insight-item">
        <div>AI-powered insights are temporarily unavailable. Please review the dashboard metrics manually.</div>
    </div>
</div>
"""


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def generate_qc_insights(
    analysis_data: Dict[str, Any],
    date: str,
    api_key: str = "ollama",
    model: str = "qwen2.5:72b-instruct-q4_K_M",
    base_url: str = "http://localhost:11435/v1"
) -> str:
    """
    Convenience function to generate QC insights using local LLM.

    Args:
        analysis_data: Analysis data from QCDataProcessor
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
    # generator = QCClaudeInsightsGenerator(api_key, model)

    # ========================================================================
    # NEW CODE - LOCAL LLM
    # ========================================================================
    generator = QCClaudeInsightsGenerator(api_key, model, base_url)
    return generator.generate_insights(analysis_data, date)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['QCClaudeInsightsGenerator', 'generate_qc_insights']


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test with sample data"""
    import os

    # Sample minimal data for testing
    test_data = {
        "date": "2025-11-17",
        "despatch": {
            "total_plan": 269.0,
            "total_actual": 269.0,
            "total_variance": 0.0,
            "customers_served": 8,
            "by_customer": []
        },
        "qc_summary": {
            "total_qc_lots": 65,
            "total_tests": 87,
            "avg_turnaround_minutes": 67,
            "fastest_turnaround_minutes": 45
        },
        "tests": {
            "by_type": [],
            "by_plant": []
        }
    }

    # ========================================================================
    # LEGACY CODE - PRESERVED FOR ROLLBACK
    # ========================================================================
    # api_key = os.getenv("CLAUDE_API_KEY")
    # if not api_key:
    #     print("❌ CLAUDE_API_KEY not set in environment")

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
    else:
        print("Testing QC Local LLM Insights Generator...")
        print(f"Model: {model}")
        print(f"Endpoint: {base_url}")
        print(f"⚠️  Ensure SSH tunnel is active: ssh -L 11435:localhost:11434 pramit@107.170.2.49")
        generator = QCClaudeInsightsGenerator(api_key, model, base_url)
        insights = generator.generate_insights(test_data, "2025-11-17")
        print("\n" + "="*70)
        print("GENERATED QC INSIGHTS:")
        print("="*70)
        print(insights)