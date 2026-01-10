"""
claude_analyzer.py
==================
AI-powered insights from furnace data.

This module:
1. Takes analysisData from FurnaceDataProcessor
2. Builds a structured prompt for LLM
3. Calls Local LLM API (or Claude API as fallback)
4. Returns formatted HTML insights section

Author: Senior ML Engineer
Date: November 2024

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
# CLAUDE INSIGHTS GENERATOR
# ============================================================================

class ClaudeInsightsGenerator:
    """
    Generate executive insights from furnace operations data using Local LLM.

    Migration Note (2025-12-16): Now uses OpenAI-compatible API for local Qwen 2.5:72B model.
    """

    def __init__(
        self,
        api_key: str = "ollama",
        model: str = "claude-3-5-sonnet-20241022",
        base_url: str = "http://localhost:11435/v1"
    ):
        """
        Initialize Claude API client.

        Args:
            api_key: Anthropic API key
            model: Model name (default Claude 3.5 Sonnet)
            base_url: Not used for Claude API (kept for compatibility)
        """
        # ====================================================================
        # CLAUDE API - COMMENTED OUT (NO CREDITS)
        # ====================================================================
        # import anthropic
        # self.client = anthropic.Anthropic(api_key=api_key)
        # self.model = model
        # logger.info(f"Claude Insights Generator initialized with model: {model}")

        # ====================================================================
        # LOCAL LLM INTEGRATION - ACTIVE
        # ====================================================================
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.base_url = base_url
        logger.info(f"Furnace Local LLM Insights Generator initialized")
        logger.info(f"Model: {model}")
        logger.info(f"Endpoint: {base_url}")
        logger.info(f"SSH Tunnel Required: ssh -L 11435:localhost:11434 pramit@107.170.2.49")

    def generate_insights(self, analysis_data: Dict[str, Any], date: str) -> str:
        """
        Generate insights HTML from analysis data.

        Args:
            analysis_data: The analysisData dict from FurnaceDataProcessor
            date: Date string (YYYY-MM-DD)

        Returns:
            HTML string for the insights section
        """
        logger.info(f"Generating Claude insights for date: {date}")

        # Build the prompt
        prompt = self._build_prompt(analysis_data, date)

        try:
            # ====================================================================
            # CLAUDE API - COMMENTED OUT (NO CREDITS)
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
            # LOCAL LLM API (OPENAI-COMPATIBLE) - ACTIVE
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

            # Clean up any markdown code fences that LLM might add
            insights_html = insights_html.strip()
            if insights_html.startswith('```html'):
                insights_html = insights_html[7:]  # Remove ```html
            if insights_html.startswith('```'):
                insights_html = insights_html[3:]  # Remove ```
            if insights_html.endswith('```'):
                insights_html = insights_html[:-3]  # Remove trailing ```
            insights_html = insights_html.strip()

            logger.info(f"Local LLM insights generated successfully ({len(insights_html)} characters)")
            return insights_html

        except Exception as e:
            logger.error(f"Error calling Local LLM: {e}", exc_info=True)
            return self._generate_fallback_insights(analysis_data)

    def _build_prompt(self, data: Dict[str, Any], date: str) -> str:
        """
        Build the prompt for Claude.

        Structure:
        1. Context and role
        2. Data (as JSON)
        3. Output requirements
        4. Examples of CSS classes
        """
        # Convert data to clean JSON (handling None values)
        data_json = self._prepare_data_for_prompt(data)

        prompt = f"""Analyze ferrochrome furnace data for {date} and generate 5-6 focused, actionable insights.

DATA:
{data_json}

CONTEXT - Normal Operating Ranges:
- Specific Power: 3500-3700 kWh/MT (lower is better)
- Cr Recovery: ≥85% (target)
- Plant OEE: ≥92% (target)
- Tapping Cycles: 8-12 per day per furnace
- Slag Generation: 1.2-1.5 MT per MT of FeCr

GENERATE 5-6 INSIGHTS covering Production, Power, Recovery, Operations, Tapping, and Slag. For each:
1. Compare actual vs target/norm with specific numbers
2. Identify best/worst performing furnaces
3. Flag any values outside normal ranges
4. Be specific and actionable (1-2 sentences per insight)

OUTPUT FORMAT (Pure HTML - NO markdown, NO code fences):

<div class="insights-section">
    <div class="insights-title">💡 Key Insights</div>

    <div class="insight-item">
        <span class="insight-icon">🏭</span>
        <div><strong>Production Performance:</strong> [Plant produced X MT vs target Y MT (Z% variance). Furnace [name] highest at X MT, Furnace [name] lowest at Y MT. Mention if any major variance from plan.]</div>
    </div>

    <div class="insight-item">
        <span class="insight-icon">⚡</span>
        <div><strong>Power Efficiency:</strong> [Plant avg specific power X kWh/MT (compare to 3500-3700 range). Furnace [name] most efficient at X kWh/MT, Furnace [name] highest at Y kWh/MT. Flag if any furnace >3700.]</div>
    </div>

    <div class="insight-item">
        <span class="insight-icon">🔬</span>
        <div><strong>Chromium Recovery:</strong> [Plant avg X% (target ≥85%). Furnace [name] best at X%, Furnace [name] at Y%. Flag any furnace below 85% as concern.]</div>
    </div>

    <div class="insight-item">
        <span class="insight-icon">🔥</span>
        <div><strong>Operational Efficiency:</strong> [Plant OEE X% (target ≥92%). Mention uptime hours, breakdown hours if any. Identify furnaces with low OEE or high downtime.]</div>
    </div>

    <div class="insight-item">
        <span class="insight-icon">⏱️</span>
        <div><strong>Tapping Performance:</strong> [Total X taps across plant (avg Y per furnace). Furnace [name] highest at X taps, [name] lowest at Y. Mention avg time between taps if notable.]</div>
    </div>

    <div class="insight-item">
        <span class="insight-icon">🪨</span>
        <div><strong>Slag Management:</strong> [Plant generated X MT slag (Y MT/MT FeCr ratio - compare to 1.2-1.5 norm). Mention any furnace with unusually high/low slag generation.]</div>
    </div>
</div>

If ANY critical issues (Cr recovery <85%, OEE <92%, specific power >3700), add:

<div class="critical-alert">
    <div class="critical-title">⚠️ Action Required</div>
    <div class="critical-item">• <strong>[Furnace X]:</strong> [specific metric] at [value] - [brief context on why this matters]</div>
</div>

RULES:
- Use actual numbers from the data provided
- Be specific about which furnaces have issues
- Keep each insight to 1-2 sentences max
- Pure HTML only - NO MARKDOWN, NO CODE FENCES, NO BACKTICKS
- Start output directly with <div>
- Make insights actionable with context"""

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
        logger.warning("Generating fallback insights due to API failure")

        # Extract key metrics safely
        try:
            plant_prod = data.get('production', {}).get('plant_total', {})
            td_actual = plant_prod.get('td_actual', 0) or 0
            td_plan = plant_prod.get('td_plan', 1) or 1
            achievement_pct = (td_actual / td_plan * 100) if td_plan > 0 else 0

            # Simple fallback HTML
            html = f"""
<div class="insights-section">
    <div class="insights-title">📊 Data Analysis Summary</div>
    <div class="insight-item">
        <span class="insight-icon">🏭</span>
        <div>
            <strong>Production Status:</strong> Plant produced {td_actual:.1f} MT against planned {td_plan:.1f} MT
            (Achievement: {achievement_pct:.1f}%)
        </div>
    </div>
    <div class="insight-item">
        <span class="insight-icon">⚠️</span>
        <div>
            <strong>Note:</strong> Detailed AI analysis temporarily unavailable.
            Please review the charts and tables above for complete operational metrics.
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

def generate_furnace_insights(
    analysis_data: Dict[str, Any],
    date: str,
    api_key: str = "ollama",
    model: str = "qwen2.5:72b-instruct-q4_K_M",
    base_url: str = "http://localhost:11435/v1"
) -> str:
    """
    Convenience function to generate furnace insights using local LLM.

    Args:
        analysis_data: Analysis data from FurnaceDataProcessor
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
    # generator = ClaudeInsightsGenerator(api_key, model)

    # ========================================================================
    # NEW CODE - LOCAL LLM
    # ========================================================================
    generator = ClaudeInsightsGenerator(api_key, model, base_url)
    return generator.generate_insights(analysis_data, date)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['ClaudeInsightsGenerator', 'generate_furnace_insights']


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test with sample data"""
    import os

    # Sample minimal data for testing
    test_data = {
        "date": "2025-11-17",
        "production": {
            "plant_total": {
                "td_plan": 350.0,
                "td_actual": 345.0,
                "mtd_plan": 5200.0,
                "mtd_actual": 5100.0,
                "td_variance": -5.0,
                "mtd_variance": -100.0
            },
            "individual_furnaces": [
                {"furnace": "I", "td_actual": 85.0, "td_plan": 87.0},
                {"furnace": "II", "td_actual": 90.0, "td_plan": 88.0},
            ]
        },
        "operational": {
            "plant_metrics": {
                "oee_pct": 95.0,
                "downtime_hours": 1.5
            }
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
        print("Testing Furnace Local LLM Insights Generator...")
        print(f"Model: {model}")
        print(f"Endpoint: {base_url}")
        print(f"⚠️  Ensure SSH tunnel is active: ssh -L 11435:localhost:11434 pramit@107.170.2.49")
        generator = ClaudeInsightsGenerator(api_key, model, base_url)
        insights = generator.generate_insights(test_data, "2025-11-17")
        print("\n" + "="*70)
        print("GENERATED INSIGHTS:")
        print("="*70)
        print(insights)