"""
ENV Claude Analyzer
===================
AI-powered insights from Environment Department data.

This module:
1. Takes analysisData from ENVDataProcessor
2. Builds a structured prompt for LLM
3. Calls Local LLM API (or Claude API as fallback)
4. Returns formatted HTML insights section

Insight Categories:
- Positive: Zero waste achievements, air quality excellence, compliance success
- Warning: Data gaps, rising emissions, expiring licenses
- Critical: GCP dust spikes, missed compliance, threshold breaches
- Info: Training progress, trend analysis, upcoming deadlines
- Action: Recommended next steps

Author: BAL-Agentic-Backend Team
Date: December 2025

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
# ENV CLAUDE INSIGHTS GENERATOR
# ============================================================================

class ENVClaudeInsightsGenerator:
    """
    Generate executive insights from Environment Department data using Local LLM.

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
        # logger.info(f"ENV Claude Insights Generator initialized with model: {model}")

        # ====================================================================
        # NEW CODE - LOCAL LLM INTEGRATION
        # ====================================================================
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.base_url = base_url
        logger.info(f"ENV Local LLM Insights Generator initialized")
        logger.info(f"Model: {model}")
        logger.info(f"Endpoint: {base_url}")
        logger.info(f"SSH Tunnel Required: ssh -L 11435:localhost:11434 pramit@107.170.2.49")

    def generate_insights(self, analysis_data: Dict[str, Any], date: str) -> str:
        """
        Generate insights HTML from analysis data.

        Args:
            analysis_data: The analysisData dict from ENVDataProcessor
            date: Date string (YYYY-MM-DD)

        Returns:
            HTML string for the insights section
        """
        logger.info(f"Generating ENV Claude insights for date: {date}")

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

            logger.info(f"ENV Local LLM insights generated successfully ({len(insights_html)} characters)")
            return insights_html

        except Exception as e:
            logger.error(f"Error calling Local LLM API: {e}", exc_info=True)
            logger.error(f"Ensure SSH tunnel is active: ssh -L 11435:localhost:11434 pramit@107.170.2.49")
            return self._generate_fallback_insights(analysis_data)

    def _build_prompt(self, data: Dict[str, Any], date: str) -> str:
        """
        Build the prompt for Claude - Environment Department specific.
        """
        # Prepare data summary for prompt
        data_summary = self._prepare_data_summary(data)

        prompt = f"""You are an expert Environmental Compliance & Sustainability analyst reviewing daily environmental KPI data for Balasore Alloys Limited (ferrochrome manufacturer) on {date}.

**YOUR TASK:**
Generate 6-8 executive insights analyzing the environmental performance, compliance status, and sustainability metrics. Include actionable recommendations.

**DATA SUMMARY:**
{data_summary}

**OUTPUT REQUIREMENTS:**

Generate HTML insights using these CSS classes. Each insight MUST follow this EXACT format:

For POSITIVE findings (achievements, compliance success):
```html
<div class="insight-card positive">
    <div class="insight-title">🎯 [Short Title]</div>
    <div class="insight-text">
        <strong>[Key Achievement]:</strong> [Specific observation with numbers]<br><br>
        [Additional context and why this matters]<br><br>
        <strong>Recommendation:</strong> [How to maintain or improve]
    </div>
</div>
```

For WARNING issues (needs monitoring, data gaps):
```html
<div class="insight-card warning">
    <div class="insight-title">⚠️ [Short Title]</div>
    <div class="insight-text">
        <strong>[Key Finding]:</strong> [Observation with specific data]<br><br>
        [Risk or compliance concern]<br><br>
        <strong>Immediate Action Required:</strong> [What to do]
    </div>
</div>
```

For CRITICAL issues (immediate attention, threshold breaches):
```html
<div class="insight-card critical">
    <div class="insight-title">🔴 [Short Title]</div>
    <div class="insight-text">
        <strong>[Critical Finding]:</strong> [Specific issue with numbers]<br><br>
        [Compliance risk or regulatory concern]<br><br>
        <strong>Immediate Action:</strong> [Urgent steps required]
    </div>
</div>
```

For INFO/analysis (trends, patterns, observations):
```html
<div class="insight-card info">
    <div class="insight-title">💧 [Short Title]</div>
    <div class="insight-text">
        <strong>[Analysis]:</strong> [Key observation with data]<br><br>
        [Pattern or trend identified]<br><br>
        <strong>Observation:</strong> [What this indicates]
    </div>
</div>
```

For ACTION items (upcoming deadlines, recommended steps):
```html
<div class="insight-card action">
    <div class="insight-title">📅 [Short Title]</div>
    <div class="insight-text">
        Based on the data analysis, the following actions require attention:<br>
        • <strong>[Date/Timeline]:</strong> [Action item 1]<br>
        • <strong>[Date/Timeline]:</strong> [Action item 2]<br>
        • <strong>[Date/Timeline]:</strong> [Action item 3]<br><br>
        <strong>Note:</strong> [Any additional context]
    </div>
</div>
```

**INSIGHT GUIDELINES:**

Use insight-card positive for:
- Zero food waste days achieved
- Air quality within NAAQS limits (significantly below thresholds)
- 100% compliance returns filed
- Zero environmental incidents
- Training milestones reached
- CBAM emissions below threshold

Use insight-card warning for:
- Data recording gaps (missing entries)
- Rising emission trends (approaching thresholds)
- Licenses expiring within 90 days
- Anomalies in readings (>20% deviation from average)
- GCP dust or slag ratio anomalies

Use insight-card critical for:
- CBAM emissions exceeding transitional threshold
- Expired licenses not renewed
- Regulatory compliance missed
- Significant data quality issues affecting compliance

Use insight-card info for:
- STP water flow analysis and patterns
- Air quality station comparisons
- Training coverage and reach
- Month-over-month trends

Use insight-card action for:
- Upcoming compliance deadlines
- License renewal timelines
- Recommended verification actions

**IMPORTANT NOTES:**
- Use ACTUAL numbers from the data provided
- Be specific about dates, values, percentages
- Include both positive findings and areas of concern
- Reference specific monitoring stations, locations, or license types
- Output pure HTML only - no markdown, no code blocks
- DO NOT include ```html or ``` markers

**NOW GENERATE THE HTML INSIGHTS (6-8 insights, pure HTML only):**"""

        return prompt

    def _prepare_data_summary(self, data: Dict[str, Any]) -> str:
        """
        Prepare a concise data summary for the prompt.
        """
        # Executive Summary
        exec_sum = data.get('executive_summary', {})

        # Food Waste
        food = data.get('food_waste', {})
        food_td = food.get('td', {})
        food_mtd = food.get('mtd', {})

        # STP Water
        stp = data.get('stp_water', {})
        stp_td = stp.get('td', {})
        stp_mtd = stp.get('mtd', {})

        # CBAM
        cbam = data.get('cbam_emissions', {})
        cbam_current = cbam.get('current', {})
        cbam_trend = cbam.get('trend', {})

        # Licenses
        licenses = data.get('licenses', {})

        # Air Quality
        air = data.get('air_quality', {})

        # Industrial Waste
        industrial = data.get('industrial_waste', {})
        industrial_current = industrial.get('current', {})

        # Compliance
        compliance = data.get('compliance_returns', {})

        # Training
        training = data.get('training', {})

        # Data Gaps
        data_gaps = data.get('data_gaps', [])

        # Incidents
        incidents = data.get('incidents', {})

        # Biomedical
        biomedical = data.get('biomedical_waste', {})

        summary = f"""
=== EXECUTIVE SUMMARY ===
Report Date: {data.get('date_formatted', 'Unknown')}
Financial Year: {data.get('financial_year', 'Unknown')}

Today's Highlights:
- Food Waste: {exec_sum.get('food_waste', {}).get('value', 0)} kg ({exec_sum.get('food_waste', {}).get('subtext', '')})
- Persons Served: {exec_sum.get('persons_served', {}).get('value', 0)}
- STP Water Flow: {exec_sum.get('stp_water', {}).get('value', 0)} KL
- Compliance Score: {exec_sum.get('compliance_score', {}).get('value', '0%')}
- Environmental Incidents: {exec_sum.get('incidents', {}).get('value', 0)}
- CBAM Emissions: {exec_sum.get('cbam_emissions', {}).get('value', '0')} tCO₂e/MT

=== FOOD WASTE (Today) ===
Total Waste: {food_td.get('total_waste', 0)} kg
Total Persons: {food_td.get('total_persons', 0)}
Waste Per Person: {food_td.get('waste_per_person', 0):.1f} gm
Is Zero Waste Day: {food_td.get('is_zero_waste', False)}
By Location: {json.dumps(food_td.get('by_location', {}), indent=2)}

=== FOOD WASTE (MTD) ===
Zero Waste Days: {food_mtd.get('zero_waste_days', 0)} out of {food_mtd.get('total_days', 0)}
Zero Waste Percentage: {food_mtd.get('zero_waste_pct', 0):.1f}%

=== STP WATER (Today) ===
Initial Reading: {stp_td.get('initial_reading', 0)}
Final Reading: {stp_td.get('final_reading', 0)}
Daily Flow: {stp_td.get('daily_flow', 0)} KL
Is Anomaly: {stp_td.get('is_anomaly', False)} (deviation: {stp_td.get('anomaly_pct', 0):.1f}%)

=== STP WATER (MTD) ===
Average Flow: {stp_mtd.get('avg_flow', 0)} KL
Total Flow: {stp_mtd.get('total_flow', 0)} KL
Days Covered: {stp_mtd.get('days', 0)}

=== CBAM EMISSIONS ({cbam_current.get('month', 'Unknown')}) ===
Direct Emissions: {cbam_current.get('direct', 0):.3f} tCO₂e/MT
Indirect Emissions: {cbam_current.get('indirect', 0):.3f} tCO₂e/MT
Total Emissions: {cbam_current.get('total', 0):.3f} tCO₂e/MT
Transitional Threshold: {cbam_current.get('threshold', 5.45)} tCO₂e/MT
Gap to Threshold: {cbam_current.get('threshold_gap_pct', 0):.1f}% below

Trends vs Previous Day ({cbam_trend.get('prev_month', 'Prior')}):
- Direct: {cbam_trend.get('direct', {}).get('direction', 'stable')} {cbam_trend.get('direct', {}).get('pct', 0)}%
- Indirect: {cbam_trend.get('indirect', {}).get('direction', 'stable')} {cbam_trend.get('indirect', {}).get('pct', 0)}%
- Total: {cbam_trend.get('total', {}).get('direction', 'stable')} {cbam_trend.get('total', {}).get('pct', 0)}%

=== LICENSE STATUS ===
Total Licenses: {licenses.get('total', 0)}
Valid: {licenses.get('valid', 0)}
Expiring Soon (90 days): {licenses.get('expiring_soon', 0)}
Expired: {licenses.get('expired', 0)}

=== AIR QUALITY ===
All Within NAAQS Limits: {air.get('all_within_limits', False)}
Stations Monitored: {list(air.get('stations', {}).keys())}

=== INDUSTRIAL WASTE ({industrial_current.get('month', 'Unknown')}) ===
Production: {industrial_current.get('production_mt', 0):,.0f} MT
Slag Generated: {industrial_current.get('slag_mt', 0):,.0f} MT
GCP Dust: {industrial_current.get('gcp_dust_mt', 0):,.0f} MT
Slag Ratio: {industrial_current.get('slag_ratio_pct', 0):.1f}%

=== COMPLIANCE RETURNS ===
Total Returns: {compliance.get('total', 0)}
Complied: {compliance.get('complied', 0)}
Pending: {compliance.get('pending', 0)}
Compliance Rate: {compliance.get('compliance_rate', 0):.1f}%

=== TRAINING ===
Total Sessions (YTD): {training.get('total_sessions', 0)}
Total Attendees (YTD): {training.get('total_attendees', 0)}
Trainers: {', '.join(training.get('trainers', []))}

=== DATA GAPS ===
{self._format_data_gaps(data_gaps)}

=== ENVIRONMENTAL INCIDENTS ===
Count Today: {incidents.get('count', 0)}
{self._format_incidents(incidents.get('incidents', []))}

=== BIOMEDICAL WASTE ===
Has Data Today: {biomedical.get('has_data', False)}
Last Entry: {biomedical.get('last_entry', {}).get('date', 'Unknown')} - {biomedical.get('last_entry', {}).get('container', '')} ({biomedical.get('last_entry', {}).get('grams', 0)}g)
"""
        return summary

    def _format_data_gaps(self, gaps: list) -> str:
        """Format data gaps for the prompt."""
        if not gaps:
            return "No data gaps detected"

        lines = []
        for gap in gaps:
            lines.append(f"- {gap.get('title', 'Unknown')}: {gap.get('message', '')}")
        return '\n'.join(lines)

    def _format_incidents(self, incidents: list) -> str:
        """Format incidents for the prompt."""
        if not incidents:
            return "No incidents reported"

        lines = []
        for inc in incidents[:5]:
            lines.append(f"- {inc.get('date', '')}: {inc.get('name', '')} ({inc.get('department', '')}) - {inc.get('description', '')}")
        return '\n'.join(lines)

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
        logger.warning("Generating fallback ENV insights due to API failure")

        try:
            exec_sum = data.get('executive_summary', {})
            food = exec_sum.get('food_waste', {})
            stp = exec_sum.get('stp_water', {})
            compliance = exec_sum.get('compliance_score', {})
            incidents = exec_sum.get('incidents', {})
            cbam = exec_sum.get('cbam_emissions', {})

            food_value = food.get('value', 0)
            stp_value = stp.get('value', 0)
            compliance_value = compliance.get('value', '0%')
            incident_count = incidents.get('value', 0)
            cbam_value = cbam.get('value', '0')

            # Determine food waste insight type
            food_class = "positive" if food_value == 0 else "info"
            food_icon = "🎯" if food_value == 0 else "🍽️"
            food_title = "Zero Food Waste Achievement" if food_value == 0 else "Food Waste Summary"

            html = f"""
<div class="insight-card {food_class}">
    <div class="insight-title">{food_icon} {food_title}</div>
    <div class="insight-text">
        <strong>Today's Performance:</strong> {food_value} kg food waste recorded.<br><br>
        {'Excellent achievement! Zero waste day demonstrates strong food management practices.' if food_value == 0 else 'Review food preparation quantities to minimize waste.'}
    </div>
</div>

<div class="insight-card info">
    <div class="insight-title">💧 STP Water Treatment</div>
    <div class="insight-text">
        <strong>Daily Flow:</strong> {stp_value} KL processed through STP today.<br><br>
        Water treatment operations are functioning within normal parameters.
    </div>
</div>

<div class="insight-card {'positive' if compliance_value == '100%' else 'warning'}">
    <div class="insight-title">📋 Compliance Status</div>
    <div class="insight-text">
        <strong>Compliance Score:</strong> {compliance_value}<br><br>
        {'All regulatory returns have been filed on time.' if compliance_value == '100%' else 'Review pending compliance returns to maintain regulatory standing.'}
    </div>
</div>

<div class="insight-card {'positive' if incident_count == 0 else 'warning'}">
    <div class="insight-title">{'✅' if incident_count == 0 else '⚠️'} Environmental Incidents</div>
    <div class="insight-text">
        <strong>Incidents Today:</strong> {incident_count}<br><br>
        {'Zero environmental incidents reported. Maintain vigilance in all operations.' if incident_count == 0 else f'{incident_count} incident(s) recorded. Review incident reports for corrective actions.'}
    </div>
</div>

<div class="insight-card info">
    <div class="insight-title">🏭 CBAM Emissions</div>
    <div class="insight-text">
        <strong>Current Emissions:</strong> {cbam_value} tCO₂e/MT<br><br>
        Monitor emission trends to ensure continued EU CBAM compliance.
    </div>
</div>

<div class="insight-card warning">
    <div class="insight-title">⚠️ AI Analysis Limited</div>
    <div class="insight-text">
        <strong>Note:</strong> Detailed AI-powered analysis is temporarily unavailable.<br><br>
        Please review the charts and tables above for complete metrics. Contact IT if this persists.
    </div>
</div>
"""
            return html

        except Exception as e:
            logger.error(f"Error generating fallback insights: {e}")
            return """
<div class="insight-card warning">
    <div class="insight-title">⚠️ Analysis Unavailable</div>
    <div class="insight-text">
        <strong>Note:</strong> AI-powered insights are temporarily unavailable. Please review the dashboard metrics manually.
    </div>
</div>
"""


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def generate_env_insights(
    analysis_data: Dict[str, Any],
    date: str,
    api_key: str = "ollama",
    model: str = "qwen2.5:72b-instruct-q4_K_M",
    base_url: str = "http://localhost:11435/v1"
) -> str:
    """
    Convenience function to generate ENV insights using local LLM.

    Args:
        analysis_data: Analysis data from ENVDataProcessor
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
    # generator = ENVClaudeInsightsGenerator(api_key, model)

    # ========================================================================
    # NEW CODE - LOCAL LLM
    # ========================================================================
    generator = ENVClaudeInsightsGenerator(api_key, model, base_url)
    return generator.generate_insights(analysis_data, date)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['ENVClaudeInsightsGenerator', 'generate_env_insights']


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test with sample data"""
    import os

    # Sample minimal data for testing
    test_data = {
        "date": "2025-11-17",
        "date_formatted": "November 17, 2025",
        "financial_year": "2025-26",
        "executive_summary": {
            "food_waste": {"value": 0, "subtext": "Zero Waste Day! 🎉"},
            "persons_served": {"value": 359, "subtext": "Across all locations"},
            "stp_water": {"value": 41, "subtext": "Daily flow"},
            "compliance_score": {"value": "100%", "subtext": "All returns filed"},
            "incidents": {"value": 0, "subtext": "Zero incidents reported"},
            "cbam_emissions": {"value": "4.60", "subtext": "Oct trend"}
        },
        "food_waste": {
            "td": {
                "total_waste": 0,
                "total_persons": 359,
                "is_zero_waste": True,
                "by_location": {
                    "Plant Canteen": {"waste_kg": 0, "persons": 339},
                    "Bachelor Hostel": {"waste_kg": 0, "persons": 14},
                    "Rest House": {"waste_kg": 0, "persons": 6}
                }
            },
            "mtd": {"zero_waste_days": 9, "total_days": 27, "zero_waste_pct": 33.3}
        },
        "stp_water": {
            "td": {"initial_reading": 113787, "final_reading": 113828, "daily_flow": 41, "is_anomaly": True, "anomaly_pct": 22.8},
            "mtd": {"avg_flow": 33.4, "total_flow": 902, "days": 27}
        },
        "cbam_emissions": {
            "has_data": True,
            "current": {"month": "Oct", "direct": 1.752, "indirect": 2.848, "total": 4.60, "threshold": 5.45, "threshold_gap_pct": 15.6},
            "trend": {
                "direct": {"pct": 4.0, "direction": "up"},
                "indirect": {"pct": 0.6, "direction": "down"},
                "total": {"pct": 1.5, "direction": "up"},
                "prev_month": "Sep"
            }
        },
        "licenses": {"total": 15, "valid": 12, "expiring_soon": 2, "expired": 1},
        "air_quality": {"has_data": True, "all_within_limits": True, "stations": {"AAQ1": {}, "AAQ2": {}, "AAQ3": {}}},
        "industrial_waste": {"has_data": True, "current": {"month": "Oct", "production_mt": 17599, "slag_mt": 7798, "gcp_dust_mt": 11866, "slag_ratio_pct": 44.3}},
        "compliance_returns": {"total": 12, "complied": 12, "pending": 0, "compliance_rate": 100},
        "training": {"total_sessions": 6, "total_attendees": 114, "trainers": ["Dr. Sudam Charan Barik", "Prashant Bardhan"]},
        "data_gaps": [{"title": "Biomedical Waste Gap", "message": "No entries for November 2025", "icon": "⚠️"}],
        "incidents": {"count": 0, "incidents": []},
        "biomedical_waste": {"has_data": False, "last_entry": {"date": "2025-10-31", "container": "Yellow", "grams": 53}}
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
        generator = ENVClaudeInsightsGenerator.__new__(ENVClaudeInsightsGenerator)
        fallback = generator._generate_fallback_insights(test_data)
        print("\n" + "="*70)
        print("FALLBACK INSIGHTS:")
        print("="*70)
        print(fallback)
    else:
        print("Testing ENV Local LLM Insights Generator...")
        print(f"Model: {model}")
        print(f"Endpoint: {base_url}")
        print(f"⚠️  Ensure SSH tunnel is active: ssh -L 11435:localhost:11434 pramit@107.170.2.49")
        generator = ENVClaudeInsightsGenerator(api_key, model, base_url)
        insights = generator.generate_insights(test_data, "2025-11-17")
        print("\n" + "="*70)
        print("GENERATED ENV INSIGHTS:")
        print("="*70)
        print(insights)