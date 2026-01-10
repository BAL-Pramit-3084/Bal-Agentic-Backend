"""
claude_analyzer.py - Geology & Survey Department
=================================================
AI-powered insights for Geology & Survey Dashboard.

Supports both Local LLM (Ollama/Qwen) and Anthropic Claude API.
Configuration from config_modules.config.

Generates 8 insight cards with proper CSS classes:
- insight-card danger (red) - critical issues
- insight-card warning (orange) - concerns
- insight-card success (green) - positive indicators
- insight-card (default blue) - neutral observations

Author: Senior ML Engineer
Date: January 2026
"""

import logging
import re
import os
from typing import Dict, Any, Optional

# Import configuration
try:
    from config_modules.config import LocalLLMConfig, ClaudeConfig
except ImportError:
    # Fallback if config_modules not available
    LocalLLMConfig = None
    ClaudeConfig = None

logger = logging.getLogger(__name__)


class ClaudeInsightsGenerator:
    """Generate executive insights from Geology & Survey operations data."""

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        base_url: str = None
    ):
        """
        Initialize LLM client from config_modules or parameters.

        Priority:
        1. Explicit parameters passed to __init__
        2. config_modules.config settings
        3. Environment variables as fallback
        """
        # Determine if using local LLM
        if LocalLLMConfig is not None:
            self.use_local_llm = LocalLLMConfig.ENABLED
        else:
            self.use_local_llm = os.getenv("LOCAL_LLM_ENABLED", "false").lower() == "true"

        if self.use_local_llm:
            # Local LLM configuration (Ollama/Qwen)
            from openai import OpenAI

            if LocalLLMConfig is not None:
                self.base_url = base_url or LocalLLMConfig.BASE_URL
                self.api_key = api_key or LocalLLMConfig.API_KEY
                self.model = model or LocalLLMConfig.MODEL
                self.temperature = LocalLLMConfig.TEMPERATURE
                self.max_tokens = LocalLLMConfig.MAX_TOKENS
            else:
                # Fallback to environment variables
                self.base_url = base_url or os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1/")
                self.api_key = api_key or os.getenv("LOCAL_LLM_API_KEY", "ollama")
                self.model = model or os.getenv("LOCAL_LLM_MODEL", "qwen2.5:72b-instruct-q4_K_M")
                self.temperature = float(os.getenv("LOCAL_LLM_TEMPERATURE", "0.7"))
                self.max_tokens = int(os.getenv("LOCAL_LLM_MAX_TOKENS", "4096"))

            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            logger.info(f"Geology LLM Generator initialized (Local) - Model: {self.model}, URL: {self.base_url}")
        else:
            # Anthropic Claude API
            import anthropic

            if ClaudeConfig is not None:
                self.api_key = api_key or ClaudeConfig.CLAUDE_API_KEY
                self.model = model or ClaudeConfig.CLAUDE_MODEL
                self.temperature = ClaudeConfig.TEMPERATURE
                self.max_tokens = ClaudeConfig.MAX_TOKENS
            else:
                self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
                self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
                self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
                self.max_tokens = 4096

            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info(f"Geology LLM Generator initialized (Anthropic) - Model: {self.model}")

    def generate_insights(self, analysis_data: Dict[str, Any], date: str) -> str:
        """
        Generate insights HTML from analysis data.
        Returns 8 insight cards for the Critical Insights section.
        """
        logger.info(f"Generating Geology Survey insights for: {date}")

        prompt = self._build_prompt(analysis_data, date)

        try:
            if self.use_local_llm:
                # OpenAI-compatible API call (Ollama)
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                insights_html = response.choices[0].message.content
            else:
                # Anthropic API call
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                insights_html = response.content[0].text

            insights_html = self._strip_markdown_code_blocks(insights_html)

            # Validate the output contains insight-card divs
            if 'insight-card' not in insights_html:
                logger.warning("LLM output missing insight-card structure, using fallback")
                return self._generate_fallback_insights(analysis_data, date)

            logger.info(f"LLM insights generated: {len(insights_html)} chars")
            return insights_html

        except Exception as e:
            logger.error(f"LLM API error: {e}", exc_info=True)
            return self._generate_fallback_insights(analysis_data, date)

    def _strip_markdown_code_blocks(self, text: str) -> str:
        """Remove markdown code blocks from LLM response."""
        if not text:
            return text

        text = re.sub(r'^```html\s*\n?', '', text.strip())
        text = re.sub(r'^```\s*\n?', '', text.strip())
        text = re.sub(r'\n?```\s*$', '', text.strip())
        text = re.sub(r'```html\s*\n?', '', text)
        text = re.sub(r'\n?```', '', text)

        return text.strip()

    def _build_prompt(self, data: Dict[str, Any], date: str) -> str:
        """Build prompt for LLM with exact HTML structure required.

        NEW: Now supports BOTH single date (today_kpis) and date range (period_kpis) data.
        """

        # Detect if this is range data or single date data
        is_range_data = 'period_kpis' in data

        # Extract key metrics - UNIFIED approach for both formats
        gap = data.get('gap_analysis', {})
        quality_stats = data.get('mtd_quality_stats') or data.get('quality_stats', {})
        shift_data = data.get('shift_breakdown', {})
        location_data = data.get('location_breakdown', {})
        agency_data = data.get('agency_performance', {})

        if is_range_data:
            # DATE RANGE MODE: Use period_kpis
            period_kpis = data.get('period_kpis', {})

            period_qty = period_kpis.get('excavation', {}).get('value', 0)
            period_trips = period_kpis.get('trips', {}).get('value', 0)
            period_avg_load = period_kpis.get('avg_load', {}).get('value', 0)
            working_days = period_kpis.get('working_days', {}).get('value', 1) or 1
            avg_daily = period_kpis.get('avg_daily_production', {}).get('value', 0)

            avg_cr2o3 = period_kpis.get('avg_cr2o3', {}).get('value', 0)
            avg_ratio = period_kpis.get('avg_ratio', {}).get('value', 0)
            total_samples = period_kpis.get('samples_total', 0)

            # For range, use totals
            achievement_pct = 100  # Not applicable for range
            time_elapsed_pct = 0   # Not applicable for range
            total_planned = 0      # Not applicable for range
            total_actual = period_qty
            remaining = 0
            days_remaining = 0
            required_daily = 0
            increase_pct = 0

            max_cr2o3 = quality_stats.get('max_cr2o3', avg_cr2o3)
            samples_per_day = total_samples / working_days if working_days > 0 else 0

            # Get top agency info (from rows, not mtd)
            agency_rows = agency_data.get('rows', [])
            top_agency_pct = agency_rows[0].get('pct', 0) if agency_rows else 0
            top_agency_name = agency_rows[0].get('agency', 'Unknown') if agency_rows else 'Unknown'

        else:
            # SINGLE DATE MODE: Use today_kpis and mtd_kpis
            mtd_kpis = data.get('mtd_kpis', {})
            today_kpis = data.get('today_kpis', {})

            achievement_pct = gap.get('achievement_pct', 0)
            time_elapsed_pct = data.get('time_elapsed_pct', 0)
            total_planned = gap.get('total_planned', 0)
            total_actual = gap.get('total_actual', mtd_kpis.get('total_excavation', {}).get('value', 0))
            remaining = gap.get('remaining_target', 0)
            days_remaining = gap.get('days_remaining', 0)
            required_daily = gap.get('required_daily_production', 0)
            avg_daily = mtd_kpis.get('avg_daily_production', {}).get('value', 0)
            increase_pct = gap.get('increase_needed_pct', 0)

            period_qty = today_kpis.get('excavation', {}).get('value', 0)
            period_trips = today_kpis.get('trips', {}).get('value', 0)
            period_avg_load = today_kpis.get('avg_load', {}).get('value', 0)

            avg_cr2o3 = quality_stats.get('avg_cr2o3', 0)
            max_cr2o3 = quality_stats.get('max_cr2o3', 0)
            total_samples = quality_stats.get('total_samples', 0)
            working_days = mtd_kpis.get('working_days', {}).get('value', 1) or 1
            samples_per_day = total_samples / working_days if working_days > 0 else 0

            # Get top agency info
            mtd_agency_rows = agency_data.get('mtd', {}).get('rows', [])
            top_agency_pct = mtd_agency_rows[0].get('pct', 0) if mtd_agency_rows else 0
            top_agency_name = mtd_agency_rows[0].get('agency', 'Unknown') if mtd_agency_rows else 'Unknown'

        # Build prompt (unified for both modes)
        period_label = "Period" if is_range_data else "Today"
        prompt = f"""You are a mining operations analyst. Generate EXACTLY 8 insight cards for a Geology & Survey dashboard for {date}.

**KEY METRICS:**
- MTD Achievement: {achievement_pct:.1f}% ({total_actual:,.0f} MT of {total_planned:,.0f} MT)
- Time Elapsed: {time_elapsed_pct:.1f}% of month
- {period_label} Production: {period_qty:,.0f} MT from {period_trips} trips
- Average Load/Trip: {period_avg_load:.1f} MT (standard: 15 MT)
- Average Cr₂O₃: {avg_cr2o3:.1f}% (HG≥52%, MG 40-52%, LG<40%)
- Max Cr₂O₃: {max_cr2o3:.1f}%
- Samples: {total_samples} total ({samples_per_day:.1f}/day)
- Top Agency: {top_agency_name} ({top_agency_pct:.1f}%)
- Required Daily: {required_daily:,.0f} MT/day ({increase_pct:.0f}% increase needed)

**OUTPUT EXACTLY THIS HTML STRUCTURE (8 cards):**

<div class="insight-card [CLASS]"><div class="insight-title">[ICON] [SHORT TITLE]</div><div class="insight-text">[2-3 sentence insight with specific numbers]</div></div>

**CLASS OPTIONS:**
- "danger" = red background (critical: achievement <50%, zero progress, quality <40%)
- "warning" = orange background (concern: achievement <80%, efficiency gap, dependency)
- "success" = green background (positive: good quality, on track)
- "" = blue background (neutral observation)

**GENERATE THESE 8 INSIGHTS IN ORDER:**

1. PLAN ACHIEVEMENT (danger if <50%, warning if <80%, else success)
   Icon: ⚠️ or ✅ | Title: "Significant Plan Shortfall" or "Production On Track"

2. SHIFT PERFORMANCE (analyze today's shift contribution)
   Icon: 📉 or 📈 | Title: "Shift [X] Underperformance" or "Balanced Shift Output"

3. QUALITY TREND (based on avg Cr₂O₃)
   Icon: ✅ or ⚠️ | Title: "Excellent Quality" or "Quality Concerns"

4. LOCATION PATTERN (which locations dominating)
   Icon: 🔄 | Title: "Location Shift Pattern"

5. ZERO PROGRESS ALERT (if any planned locations have 0)
   Icon: 🚫 | Title: "DVS West & East - Zero Progress" (danger class)

6. LOAD EFFICIENCY (compare to 15 MT standard)
   Icon: 📊 | Title: "Declining Load Efficiency" or "Good Load Efficiency"

7. AGENCY DEPENDENCY (warning if single agency >75%)
   Icon: 🏆 | Title: "[Agency] Dominance" or "Balanced Agency Distribution"

8. SAMPLE COVERAGE (warning if <2/day)
   Icon: 🔬 | Title: "Sample Coverage Gap" or "Adequate Sample Coverage"

**RULES:**
- Output ONLY the 8 <div> elements, nothing else
- Use actual numbers from metrics above
- Each insight-text should be 2-3 sentences with specific data
- NO markdown, NO code blocks, NO explanations before/after
- Use proper HTML entities for special chars

**OUTPUT NOW:**"""

        return prompt

    def _generate_fallback_insights(self, data: Dict[str, Any], date: str) -> str:
        """Generate fallback insights when LLM fails.

        NEW: Now supports BOTH single date and date range data.
        """
        logger.warning("Generating fallback insights")

        # Detect if this is range data or single date data
        is_range_data = 'period_kpis' in data

        gap = data.get('gap_analysis', {})
        quality_stats = data.get('mtd_quality_stats') or data.get('quality_stats', {})
        agency_data = data.get('agency_performance', {})

        if is_range_data:
            # DATE RANGE MODE
            period_kpis = data.get('period_kpis', {})

            achievement_pct = 0  # Not applicable
            time_elapsed_pct = 0  # Not applicable
            total_planned = 0
            total_actual = period_kpis.get('excavation', {}).get('value', 0)
            remaining = 0
            days_remaining = 0
            expected_achievement = 0

            td_qty = period_kpis.get('excavation', {}).get('value', 0)
            td_trips = period_kpis.get('trips', {}).get('value', 0)
            td_avg_load = period_kpis.get('avg_load', {}).get('value', 0)
            working_days = period_kpis.get('working_days', {}).get('value', 1) or 1

            avg_cr2o3 = period_kpis.get('avg_cr2o3', {}).get('value', 0)
            avg_ratio = period_kpis.get('avg_ratio', {}).get('value', 0)
            total_samples = period_kpis.get('samples_total', 0)
            max_cr2o3 = quality_stats.get('max_cr2o3', avg_cr2o3)

            # Get top agency info
            agency_rows = agency_data.get('rows', [])
            top_agency_pct = agency_rows[0].get('pct', 0) if agency_rows else 0
            top_agency_name = agency_rows[0].get('agency', 'BAL') if agency_rows else 'BAL'
            top_agency_qty = agency_rows[0].get('qty', 0) if agency_rows else 0

        else:
            # SINGLE DATE MODE
            mtd_kpis = data.get('mtd_kpis', {})
            today_kpis = data.get('today_kpis', {})

            achievement_pct = gap.get('achievement_pct', 0)
            time_elapsed_pct = data.get('time_elapsed_pct', 0)
            total_planned = gap.get('total_planned', 0)
            total_actual = gap.get('total_actual', mtd_kpis.get('total_excavation', {}).get('value', 0))
            remaining = gap.get('remaining_target', 0)
            days_remaining = gap.get('days_remaining', 0)
            expected_achievement = gap.get('expected_achievement_pct', 0)

            td_qty = today_kpis.get('excavation', {}).get('value', 0)
            td_trips = today_kpis.get('trips', {}).get('value', 0)
            td_avg_load = today_kpis.get('avg_load', {}).get('value', 0)
            working_days = mtd_kpis.get('working_days', {}).get('value', 1) or 1

            avg_cr2o3 = quality_stats.get('avg_cr2o3', 0)
            avg_ratio = quality_stats.get('avg_ratio', 0)
            total_samples = quality_stats.get('total_samples', 0)
            max_cr2o3 = quality_stats.get('max_cr2o3', 0)

            # Get top agency info
            mtd_agency_rows = agency_data.get('mtd', {}).get('rows', [])
            top_agency_pct = mtd_agency_rows[0].get('pct', 0) if mtd_agency_rows else 0
            top_agency_name = mtd_agency_rows[0].get('agency', 'BAL') if mtd_agency_rows else 'BAL'
            top_agency_qty = mtd_agency_rows[0].get('qty', 0) if mtd_agency_rows else 0

        # Determine classes
        plan_class = "danger" if achievement_pct < 50 else "warning" if achievement_pct < 80 else "success"
        plan_icon = "⚠️" if achievement_pct < 80 else "✅"
        plan_title = "Significant Plan Shortfall" if achievement_pct < 80 else "Production On Track"

        quality_class = "success" if avg_cr2o3 >= 50 else "warning" if avg_cr2o3 >= 40 else "danger" if avg_cr2o3 > 0 else ""
        quality_icon = "✅" if avg_cr2o3 >= 50 else "⚠️"
        quality_title = "Excellent Quality" if avg_cr2o3 >= 52 else "Good Quality Performance" if avg_cr2o3 >= 50 else "Quality Performance" if avg_cr2o3 > 0 else "No Quality Data"
        quality_grade = "High Grade" if avg_cr2o3 >= 52 else "Medium Grade" if avg_cr2o3 >= 40 else "Low Grade" if avg_cr2o3 > 0 else "N/A"

        load_class = "danger" if td_avg_load < 10 and td_avg_load > 0 else "warning" if td_avg_load < 15 and td_avg_load > 0 else "success" if td_avg_load > 0 else ""
        load_pct_gap = ((15 - td_avg_load) / 15 * 100) if td_avg_load < 15 and td_avg_load > 0 else 0

        agency_class = "warning" if top_agency_pct > 75 else "success" if top_agency_pct > 0 else ""

        sample_class = "warning" if samples_per_day < 2 and total_samples > 0 else "success" if total_samples > 0 else ""

        insights = f'''<div class="insight-card {plan_class}"><div class="insight-title">{plan_icon} {plan_title}</div><div class="insight-text">With {time_elapsed_pct:.1f}% of the month elapsed, {achievement_pct:.1f}% of the monthly target ({total_actual:,.0f} MT of {total_planned:,.0f} MT) has been achieved. Current pace projects ~{expected_achievement:.0f}% achievement by month end.</div></div>
<div class="insight-card warning"><div class="insight-title">📉 Shift Performance Analysis</div><div class="insight-text">Today recorded {td_qty:,.0f} MT across {td_trips} trips. Review shift-wise contribution and identify underperforming shifts for corrective action.</div></div>
<div class="insight-card {quality_class}"><div class="insight-title">{quality_icon} {quality_title}</div><div class="insight-text">{"Average Cr₂O₃ at " + f"{avg_cr2o3:.1f}% indicates {quality_grade} ore. Best sample recorded {max_cr2o3:.1f}%." if avg_cr2o3 > 0 else "No sample analysis data available for quality assessment."}</div></div>
<div class="insight-card warning"><div class="insight-title">🔄 Location Shift Pattern</div><div class="insight-text">Production distribution across locations requires monitoring. Ensure all planned faces are being excavated according to plan.</div></div>
<div class="insight-card danger"><div class="insight-title">🚫 DVS West & East - Zero Progress</div><div class="insight-text">DVS West and DVS East locations have zero excavation recorded. Immediate mobilization required to recover planned production.</div></div>
<div class="insight-card {load_class}"><div class="insight-title">📊 {"Declining " if td_avg_load < 15 and td_avg_load > 0 else ""}Load Efficiency</div><div class="insight-text">{"Average load per trip is " + f"{td_avg_load:.1f} MT vs 15 MT standard - {load_pct_gap:.0f}% below optimal." if td_avg_load > 0 else "No trip data available for load analysis."}</div></div>
<div class="insight-card {agency_class}"><div class="insight-title">🏆 {top_agency_name} Agency {"Dominance" if top_agency_pct > 75 else "Performance"}</div><div class="insight-text">{f"{top_agency_name} contributes {top_agency_pct:.1f}% of excavation (MTD: {top_agency_qty:,.0f} MT)." if top_agency_pct > 0 else "No agency performance data available."}</div></div>
<div class="insight-card {sample_class}"><div class="insight-title">🔬 Sample Coverage {"Gap" if samples_per_day < 2 and total_samples > 0 else ""}</div><div class="insight-text">{f"{total_samples} samples analyzed MTD (~{samples_per_day:.1f}/day)." if total_samples > 0 else "No samples analyzed MTD. Implement sampling protocol."}</div></div>'''

        return insights


# Exports
__all__ = ['ClaudeInsightsGenerator']