"""
Automobile Claude Analyzer
==========================
AI-powered insights generator for Fleet Management Dashboard.

This module:
1. Takes analysis data from AutomobileDataProcessor
2. Builds a structured prompt for LLM
3. Calls Local LLM API (Qwen 2.5:72B on DigitalOcean H200)
4. Returns formatted HTML insights section

Insight Categories:
- Critical (danger): Extreme idle time, sensor failures, fuel theft
- Warning: Low fuel alerts, poor mileage, high idle trucks
- Positive (success): Zero theft, best performers, efficiency wins
- Info: Fleet utilization stats, MTD trends, recommendations

Output Format:
- HTML insight cards with appropriate CSS classes
- Structured for direct injection into dashboard template

Author: BAL-Agentic-Backend Team
Date: December 2025

LLM Configuration:
- Primary: Local Qwen 2.5:72B via SSH tunnel (localhost:11435)
- Fallback: Static insights if LLM unavailable
- SSH Tunnel: ssh -L 11435:localhost:11434 pramit@107.170.2.49
"""

import logging
import json
from typing import Dict, Any, Optional, List

# ============================================================================
# LLM CLIENT IMPORT
# ============================================================================
from openai import OpenAI  # OpenAI-compatible SDK for local LLM

logger = logging.getLogger(__name__)


# ============================================================================
# AUTOMOBILE INSIGHTS GENERATOR
# ============================================================================

class AutomobileInsightsGenerator:
    """
    Generate executive insights from Fleet Management data using Local LLM.
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
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.base_url = base_url
        logger.info(f"Automobile Insights Generator initialized")
        logger.info(f"Model: {model}")
        logger.info(f"Endpoint: {base_url}")

    def generate_insights(self, analysis_data: Dict[str, Any], date: str) -> str:
        """
        Generate insights HTML from analysis data.

        Args:
            analysis_data: The data dict from AutomobileDataProcessor
            date: Date string (YYYY-MM-DD)

        Returns:
            HTML string for the insights section
        """
        logger.info(f"Generating Automobile insights for date: {date}")

        # Build the prompt
        prompt = self._build_prompt(analysis_data, date)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract text from response
            insights_html = response.choices[0].message.content

            # Clean up any markdown artifacts
            insights_html = self._clean_response(insights_html)

            logger.info(f"Automobile insights generated successfully ({len(insights_html)} characters)")
            return insights_html

        except Exception as e:
            logger.error(f"Error calling Local LLM API: {e}", exc_info=True)
            logger.error(f"Ensure SSH tunnel is active: ssh -L 11435:localhost:11434 pramit@107.170.2.49")
            return self._generate_fallback_insights(analysis_data)

    def _build_prompt(self, data: Dict[str, Any], date: str) -> str:
        """
        Build the prompt for LLM - Fleet Management specific.
        """
        # Prepare data summary
        data_summary = self._prepare_data_summary(data)

        prompt = f"""You are an expert Fleet Operations Analyst reviewing daily telematics data for Balasore Alloys Limited's MAN truck fleet on {date}.

**YOUR TASK:**
Generate 8-10 executive insights analyzing fleet performance, fuel efficiency, idle time patterns, and operational issues. Include actionable recommendations.

**FLEET DATA SUMMARY:**
{data_summary}

**OUTPUT REQUIREMENTS:**

Generate HTML insight cards using these exact CSS classes. Each insight MUST follow this format:

For CRITICAL issues (immediate action required):
```html
<div class="insight-card danger">
    <div class="insight-title">🔴 [Short Title]</div>
    <div class="insight-text">
        <strong>[Key Issue]:</strong> [Specific observation with numbers]<br><br>
        [Impact and risk assessment]<br><br>
        <strong>Action Required:</strong> [Immediate steps to take]
    </div>
</div>
```

For WARNING issues (needs attention):
```html
<div class="insight-card warning">
    <div class="insight-title">⚠️ [Short Title]</div>
    <div class="insight-text">
        <strong>[Key Finding]:</strong> [Observation with specific data]<br><br>
        [Why this matters]<br><br>
        <strong>Recommendation:</strong> [Suggested action]
    </div>
</div>
```

For POSITIVE findings (achievements, good performance):
```html
<div class="insight-card success">
    <div class="insight-title">✅ [Short Title]</div>
    <div class="insight-text">
        <strong>[Achievement]:</strong> [Specific positive outcome]<br><br>
        [Context and significance]<br><br>
        <strong>Maintain by:</strong> [How to sustain this success]
    </div>
</div>
```

For INFORMATIONAL insights (trends, patterns):
```html
<div class="insight-card">
    <div class="insight-title">📊 [Short Title]</div>
    <div class="insight-text">
        <strong>[Observation]:</strong> [Data point or trend]<br><br>
        [Analysis and context]<br><br>
        <strong>Consider:</strong> [Strategic recommendation]
    </div>
</div>
```

**ANALYSIS FOCUS AREAS:**

1. **Idle Time Analysis** - Quantify fuel waste from excessive idling (estimate ~4L/hour diesel waste per idling truck)
2. **Fuel Efficiency** - Identify best and worst performers, calculate potential savings
3. **Sensor Issues** - Flag trucks with impossible data (KMPL > 10, distance without fuel consumption)
4. **Low Fuel Alerts** - Prioritize trucks needing immediate refueling
5. **Fleet Utilization** - Analyze active vs idle truck ratio, right-sizing opportunities
6. **Fuel Security** - Comment on theft detection (drains)
7. **Driver Behavior** - Infer patterns from mileage variance between trucks
8. **MTD Trends** - Month-to-date patterns and concerns
9. **Cost Impact** - Translate inefficiencies to rupee amounts where possible
10. **Recommendations** - Prioritized action items with expected ROI

**IMPORTANT RULES:**
- Use ONLY the CSS classes shown above (danger, warning, success, or no class for info)
- Include specific numbers from the data - never generic statements
- Each insight should be actionable
- Calculate fuel waste in liters AND estimated cost (assume ₹90/liter diesel)
- Prioritize critical issues first
- Generate 8-10 insights covering different aspects
- Output ONLY the HTML cards, no markdown, no explanation, no code blocks

Generate the insights now:
"""
        return prompt

    def _prepare_data_summary(self, data: Dict[str, Any]) -> str:
        """Prepare structured data summary for the prompt."""
        kpis = data.get('kpis', {})
        mtd = data.get('mtd', {})
        idle_analysis = data.get('idle_analysis', {})
        alerts = data.get('alerts', {})
        idle_trucks = data.get('idle_trucks', {})
        top_performers = data.get('top_performers', [])

        # Format top performers
        top_perf_str = ""
        for p in top_performers[:5]:
            top_perf_str += f"  - {p.get('vehicle')}: {p.get('distance')}km, {p.get('fuel')}L, {p.get('kmpl')} KMPL\n"

        # Format low fuel trucks
        low_fuel = alerts.get('low_fuel', [])
        low_fuel_str = ", ".join([f"{t['vehicle']} ({t['fuel_level']}L)" for t in low_fuel[:5]]) if low_fuel else "None"

        # Format sensor issues
        sensor_issues = alerts.get('sensor_issues', [])
        sensor_str = ", ".join([f"{t['vehicle']}: {t['issue']}" for t in sensor_issues[:4]]) if sensor_issues else "None detected"

        # Format high idle trucks
        high_idle = alerts.get('high_idle', [])
        high_idle_str = ", ".join([f"{t['vehicle']} ({t['idle_pct']}%)" for t in high_idle[:4]]) if high_idle else "None"

        # Format poor mileage
        poor_mileage = alerts.get('poor_mileage', [])
        poor_mileage_str = ", ".join([f"{t['vehicle']} ({t['kmpl']} KMPL)" for t in poor_mileage[:4]]) if poor_mileage else "None"

        # Format idle trucks
        no_data_trucks = idle_trucks.get('no_data', [])
        no_data_str = ", ".join([t['vehicle'] for t in no_data_trucks[:10]]) if no_data_trucks else "None"
        if len(no_data_trucks) > 10:
            no_data_str += f" (+{len(no_data_trucks) - 10} more)"

        summary = f"""
=== DAILY METRICS ({data.get('date_formatted', 'Unknown')}) ===
Fleet Size: {kpis.get('total_trucks', 35)} trucks
Active Today: {kpis.get('active_trucks', 0)} trucks ({kpis.get('utilization_pct', 0)}% utilization)
Total Distance: {kpis.get('total_distance', 0)} km (Yesterday: {kpis.get('yesterday_distance', 0)} km)
Fuel Consumed: {kpis.get('fuel_consumed', 0)} L (Yesterday: {kpis.get('yesterday_fuel', 0)} L)
Fuel Filled: {kpis.get('fuel_filled', 0)} L ({kpis.get('fillings_count', 0)} fill events)
Fuel Drained: {kpis.get('fuel_drained', 0)} L (theft indicator)
Fleet Average Mileage: {kpis.get('avg_kmpl', 0)} KMPL
Max Speed Recorded: {kpis.get('max_speed', 0)} km/h

=== IDLE TIME ANALYSIS ===
Total Idle Hours Today: ~{idle_analysis.get('total_idle_hours', 0)} hours
Average Idle Ratio: {idle_analysis.get('avg_idle_pct', 0)}% of engine time
Best Performer: {idle_analysis.get('best_performer', {}).get('vehicle', 'N/A')} ({idle_analysis.get('best_performer', {}).get('idle_pct', 0)}% idle)
Highest Idle Trucks: {high_idle_str}

=== MTD SUMMARY (Month-to-Date) ===
MTD Distance: {mtd.get('distance', 0)} km
MTD Fuel Consumed: {mtd.get('fuel_consumed', 0)} L
MTD Fuel Filled: {mtd.get('fuel_filled', 0)} L
MTD Fuel Balance: {mtd.get('fuel_balance', 0)} L (negative = deficit)
MTD Fuel Drained: {mtd.get('fuel_drained', 0)} L
MTD Average Mileage: {mtd.get('avg_kmpl', 0)} KMPL
Trucks Active This Month: {mtd.get('trucks_active', 0)}

=== TOP PERFORMERS TODAY ===
{top_perf_str}

=== ALERTS & ISSUES ===
Low Fuel Trucks (< 50L): {low_fuel_str}
Sensor Issues: {sensor_str}
Poor Mileage (< 0.5 KMPL): {poor_mileage_str}

=== IDLE/UNUSED TRUCKS ===
Zero Activity: {no_data_str}
Total Idle Trucks: {idle_trucks.get('total_idle', 0)}
"""
        return summary

    def _clean_response(self, response: str) -> str:
        """Clean LLM response of markdown artifacts."""
        if not response:
            return ""

        # Remove markdown code blocks
        response = response.replace("```html", "").replace("```", "")

        # Remove any leading/trailing whitespace
        response = response.strip()

        # Ensure it starts with a div (insight card)
        if not response.startswith("<div"):
            # Try to find the first div
            div_start = response.find("<div")
            if div_start > 0:
                response = response[div_start:]

        return response

    def _generate_fallback_insights(self, data: Dict[str, Any]) -> str:
        """Generate fallback insights when LLM is unavailable."""
        logger.warning("Generating fallback insights (LLM unavailable)")

        try:
            kpis = data.get('kpis', {})
            mtd = data.get('mtd', {})
            idle_analysis = data.get('idle_analysis', {})
            alerts = data.get('alerts', {})

            # Extract key metrics
            active_trucks = kpis.get('active_trucks', 0)
            total_trucks = kpis.get('total_trucks', 35)
            utilization = kpis.get('utilization_pct', 0)
            total_distance = kpis.get('total_distance', 0)
            fuel_consumed = kpis.get('fuel_consumed', 0)
            fuel_drained = kpis.get('fuel_drained', 0)
            avg_kmpl = kpis.get('avg_kmpl', 0)

            total_idle_hours = idle_analysis.get('total_idle_hours', 0)
            avg_idle_pct = idle_analysis.get('avg_idle_pct', 0)

            low_fuel_count = alerts.get('low_fuel_count', 0)
            sensor_count = alerts.get('sensor_issues_count', 0)
            high_idle_count = alerts.get('high_idle_count', 0)

            # Build fallback HTML
            html = ""

            # Fleet utilization insight
            util_class = "danger" if utilization < 50 else "warning" if utilization < 70 else "success"
            util_icon = "🔴" if utilization < 50 else "⚠️" if utilization < 70 else "✅"
            html += f"""
<div class="insight-card {util_class}">
    <div class="insight-title">{util_icon} Fleet Utilization: {utilization}%</div>
    <div class="insight-text">
        <strong>Active Trucks:</strong> {active_trucks} of {total_trucks} trucks operational today.<br><br>
        {'Low utilization indicates potential for fleet right-sizing or redeployment.' if utilization < 60 else 'Fleet utilization is within acceptable range.'}<br><br>
        <strong>Recommendation:</strong> {'Review idle truck status and maintenance schedules.' if utilization < 60 else 'Maintain current operational efficiency.'}
    </div>
</div>
"""

            # Idle time insight
            if avg_idle_pct > 40:
                idle_fuel_waste = total_idle_hours * 4  # ~4L per idle hour
                idle_cost = idle_fuel_waste * 90  # ₹90 per liter
                html += f"""
<div class="insight-card danger">
    <div class="insight-title">🔴 Excessive Idle Time: {avg_idle_pct}%</div>
    <div class="insight-text">
        <strong>Total Idle Hours:</strong> ~{total_idle_hours} hours across fleet today.<br><br>
        Estimated fuel waste: ~{idle_fuel_waste:.0f} liters (₹{idle_cost:,.0f} daily loss).<br><br>
        <strong>Action Required:</strong> Implement automatic engine shutoff policy after 5 minutes idle.
    </div>
</div>
"""

            # Fuel theft insight
            theft_class = "success" if fuel_drained == 0 else "danger"
            theft_icon = "✅" if fuel_drained == 0 else "🔴"
            html += f"""
<div class="insight-card {theft_class}">
    <div class="insight-title">{theft_icon} Fuel Security Status</div>
    <div class="insight-text">
        <strong>Fuel Drained Today:</strong> {fuel_drained} liters<br><br>
        {'No fuel theft detected. Security measures are effective.' if fuel_drained == 0 else f'Potential fuel theft detected. Investigate drain events immediately.'}<br><br>
        <strong>{'Maintain:' if fuel_drained == 0 else 'Action:'}</strong> {'Continue monitoring with telematics alerts.' if fuel_drained == 0 else 'Review GPS locations during drain events.'}
    </div>
</div>
"""

            # Low fuel alert
            if low_fuel_count > 0:
                low_fuel_trucks = alerts.get('low_fuel', [])
                trucks_str = ", ".join([f"{t['vehicle']} ({t['fuel_level']}L)" for t in low_fuel_trucks[:4]])
                html += f"""
<div class="insight-card warning">
    <div class="insight-title">⚠️ Low Fuel Alert: {low_fuel_count} Trucks</div>
    <div class="insight-text">
        <strong>Critical Fuel Levels:</strong> {trucks_str}<br><br>
        Risk of mid-shift breakdown if not refueled before next operation.<br><br>
        <strong>Recommendation:</strong> Prioritize refueling these trucks immediately.
    </div>
</div>
"""

            # Sensor issues
            if sensor_count > 0:
                html += f"""
<div class="insight-card warning">
    <div class="insight-title">⚠️ Sensor Malfunctions: {sensor_count} Trucks</div>
    <div class="insight-text">
        <strong>Issue:</strong> {sensor_count} trucks showing impossible data readings.<br><br>
        Faulty sensors prevent accurate fuel theft detection and efficiency monitoring.<br><br>
        <strong>Recommendation:</strong> Schedule sensor calibration/replacement within 48 hours.
    </div>
</div>
"""

            # Performance summary
            html += f"""
<div class="insight-card">
    <div class="insight-title">📊 Daily Performance Summary</div>
    <div class="insight-text">
        <strong>Distance:</strong> {total_distance} km | <strong>Fuel:</strong> {fuel_consumed} L | <strong>Mileage:</strong> {avg_kmpl} KMPL<br><br>
        Fleet is operating at {'below' if avg_kmpl < 0.8 else 'within'} expected efficiency benchmarks.<br><br>
        <strong>Consider:</strong> {'Driver training and vehicle maintenance review.' if avg_kmpl < 0.8 else 'Continue monitoring for consistency.'}
    </div>
</div>
"""

            # AI unavailable notice
            html += """
<div class="insight-card warning">
    <div class="insight-title">⚠️ Advanced AI Analysis Limited</div>
    <div class="insight-text">
        <strong>Note:</strong> Detailed AI-powered analysis is temporarily unavailable.<br><br>
        Basic metrics and alerts shown above. For deeper insights, ensure LLM service is running.<br><br>
        <strong>Contact:</strong> IT team if this persists beyond expected maintenance window.
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
        <strong>Note:</strong> AI-powered fleet insights are temporarily unavailable.<br><br>
        Please review the dashboard metrics and charts manually for operational decisions.
    </div>
</div>
"""


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def generate_automobile_insights(
    analysis_data: Dict[str, Any],
    date: str,
    api_key: str = "ollama",
    model: str = "qwen2.5:72b-instruct-q4_K_M",
    base_url: str = "http://localhost:11435/v1"
) -> str:
    """
    Convenience function to generate automobile insights using local LLM.

    Args:
        analysis_data: Analysis data from AutomobileDataProcessor
        date: Date string
        api_key: API key (default "ollama" for local)
        model: Model name (default Qwen 2.5:72B)
        base_url: Local LLM endpoint

    Returns:
        HTML string with insights
    """
    generator = AutomobileInsightsGenerator(api_key, model, base_url)
    return generator.generate_insights(analysis_data, date)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['AutomobileInsightsGenerator', 'generate_automobile_insights']


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test with sample data"""
    import os

    print("Automobile Claude Analyzer module loaded successfully")
    print("=" * 60)

    # Sample minimal data for testing
    test_data = {
        "date": "2025-12-16",
        "date_formatted": "December 16, 2025",
        "kpis": {
            "total_trucks": 35,
            "active_trucks": 18,
            "utilization_pct": 51,
            "total_distance": 713.9,
            "yesterday_distance": 775.5,
            "fuel_consumed": 775.7,
            "yesterday_fuel": 748.8,
            "avg_kmpl": 0.92,
            "fuel_filled": 754.7,
            "fillings_count": 6,
            "max_speed": 50,
            "fuel_drained": 0
        },
        "mtd": {
            "distance": 13188.9,
            "fuel_consumed": 13626.0,
            "fuel_filled": 12625.5,
            "fuel_drained": 55.4,
            "avg_kmpl": 0.97,
            "trucks_active": 24,
            "fuel_balance": -1000.5
        },
        "idle_analysis": {
            "total_idle_hours": 56,
            "avg_idle_pct": 47,
            "best_performer": {"vehicle": "MAN66", "idle_pct": 24}
        },
        "alerts": {
            "low_fuel": [
                {"vehicle": "MAN69", "fuel_level": 17},
                {"vehicle": "MAN57", "fuel_level": 22},
                {"vehicle": "MAN71", "fuel_level": 26}
            ],
            "low_fuel_count": 3,
            "sensor_issues": [
                {"vehicle": "MAN71", "issue": "Impossible mileage: 84.9 KMPL"},
                {"vehicle": "MAN52", "issue": "Movement without fuel consumption"}
            ],
            "sensor_issues_count": 2,
            "high_idle": [
                {"vehicle": "MAN53", "idle_pct": 81},
                {"vehicle": "Diesel Tanker", "idle_pct": 90}
            ],
            "high_idle_count": 2,
            "poor_mileage": [
                {"vehicle": "MAN53", "kmpl": 0.16},
                {"vehicle": "Diesel Tanker", "kmpl": 0.37}
            ],
            "poor_mileage_count": 2
        },
        "idle_trucks": {
            "no_data": [{"vehicle": f"MAN{i}"} for i in [11, 12, 14, 20, 41, 47, 48, 51, 54, 68]],
            "total_idle": 17
        },
        "top_performers": [
            {"vehicle": "MAN77", "distance": 77.07, "fuel": 102.4, "kmpl": 0.75},
            {"vehicle": "MAN50", "distance": 75.92, "fuel": 71.2, "kmpl": 1.07},
            {"vehicle": "MAN69", "distance": 69.33, "fuel": 74.7, "kmpl": 0.93}
        ]
    }

    # Get configuration
    api_key = os.getenv("LOCAL_LLM_API_KEY", "ollama")
    model = os.getenv("LOCAL_LLM_MODEL", "qwen2.5:72b-instruct-q4_K_M")
    base_url = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11435/v1")
    local_llm_enabled = os.getenv("LOCAL_LLM_ENABLED", "false").lower() == "true"

    if not local_llm_enabled:
        print("LOCAL_LLM_ENABLED is false - testing fallback insights")
        print("=" * 60)
        generator = AutomobileInsightsGenerator.__new__(AutomobileInsightsGenerator)
        fallback = generator._generate_fallback_insights(test_data)
        print("FALLBACK INSIGHTS:")
        print(fallback)
    else:
        print(f"Model: {model}")
        print(f"Endpoint: {base_url}")
        print("⚠️  Ensure SSH tunnel is active: ssh -L 11435:localhost:11434 pramit@107.170.2.49")
        print("=" * 60)
        generator = AutomobileInsightsGenerator(api_key, model, base_url)
        insights = generator.generate_insights(test_data, "2025-12-16")
        print("GENERATED INSIGHTS:")
        print(insights)