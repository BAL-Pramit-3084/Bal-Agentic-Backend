"""
claude_analyzer.py - Geology & Survey Department
=================================================
AI-powered insights for Geology & Survey Dashboard.

THIS IS AN AGENTIC DASHBOARD - LLM IS MANDATORY, NOT OPTIONAL.

Supports:
1. OpenAI API (GPT-4o, GPT-4o-mini) - DEFAULT
2. Local LLM (Ollama/Qwen) - COMMENTED OUT, can be re-enabled

Author: Senior ML Engineer
Date: January 2026
"""

import logging
import re
import os
from typing import Dict, Any, Optional, List
from openai import OpenAI

# Import configuration
try:
    from config_modules.config import LocalLLMConfig, ClaudeConfig
except ImportError:
    LocalLLMConfig = None
    ClaudeConfig = None

logger = logging.getLogger(__name__)


class ClaudeInsightsGenerator:
    """
    Generate executive insights from Geology & Survey operations data.

    Supports multiple LLM backends:
    - OpenAI API (default)
    - Local LLM via Ollama (commented out)
    """

    def __init__(self, api_key: str = None, model: str = None, base_url: str = None, **kwargs):
        """
        Initialize LLM client.

        Priority:
        1. OpenAI API (if OPENAI_API_KEY is set)
        2. Local LLM (if LOCAL_LLM_ENABLED=true) - currently commented out
        """

        # =======================================================================
        # OPENAI API CONFIGURATION (ACTIVE)
        # =======================================================================
        self.use_openai = True  # Set to False to use Local LLM instead

        if self.use_openai:
            self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
            self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")  # Latest model
            self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
            self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "4096"))

            if not self.api_key:
                raise ValueError("OPENAI_API_KEY is required for AI insights generation")

            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"Geology AI Generator initialized (OpenAI) - Model: {self.model}")

        # =======================================================================
        # LOCAL LLM CONFIGURATION (COMMENTED OUT - UNCOMMENT TO USE)
        # =======================================================================
        # To use Local LLM instead of OpenAI:
        # 1. Set self.use_openai = False above
        # 2. Uncomment the code below
        # 3. Ensure LOCAL_LLM_ENABLED=true in .env
        #
        # else:
        #     import httpx
        #
        #     # Determine if using local LLM
        #     if LocalLLMConfig is not None:
        #         self.use_local_llm = LocalLLMConfig.ENABLED
        #     else:
        #         self.use_local_llm = os.getenv("LOCAL_LLM_ENABLED", "false").lower() == "true"
        #
        #     if LocalLLMConfig is not None:
        #         self.base_url = base_url or LocalLLMConfig.BASE_URL
        #         self.api_key = api_key or LocalLLMConfig.API_KEY
        #         self.model = model or LocalLLMConfig.MODEL
        #         self.temperature = LocalLLMConfig.TEMPERATURE
        #         self.max_tokens = LocalLLMConfig.MAX_TOKENS
        #     else:
        #         self.base_url = base_url or os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1/")
        #         self.api_key = api_key or os.getenv("LOCAL_LLM_API_KEY", "ollama")
        #         self.model = model or os.getenv("LOCAL_LLM_MODEL", "qwen2.5:72b-instruct-q4_K_M")
        #         self.temperature = float(os.getenv("LOCAL_LLM_TEMPERATURE", "0.7"))
        #         self.max_tokens = int(os.getenv("LOCAL_LLM_MAX_TOKENS", "4096"))
        #
        #     # Set longer timeout for large models (72B needs more time)
        #     self.client = OpenAI(
        #         api_key=self.api_key,
        #         base_url=self.base_url,
        #         timeout=httpx.Timeout(300.0, connect=30.0)  # 5 min read, 30s connect
        #     )
        #     logger.info(f"Geology AI Generator initialized (Local LLM) - Model: {self.model}, URL: {self.base_url}")

    def _call_llm(self, prompt: str, max_retries: int = 3) -> str:
        """
        Call LLM API with retry logic.
        Works with both OpenAI API and Local LLM (Ollama).
        """
        import time

        last_error = None

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content

            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                logger.warning(f"LLM API attempt {attempt + 1}/{max_retries} failed: {error_type}: {e}")

                if attempt < max_retries - 1:
                    wait_time = 2 * (2 ** attempt)  # 2s, 4s, 8s
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

        logger.error(f"LLM API failed after {max_retries} attempts: {last_error}")
        raise last_error

    def _strip_markdown(self, text: str) -> str:
        """Remove markdown code blocks from LLM response."""
        if not text:
            return text
        text = re.sub(r'^```html\s*\n?', '', text.strip())
        text = re.sub(r'^```\s*\n?', '', text.strip())
        text = re.sub(r'\n?```\s*$', '', text.strip())
        text = re.sub(r'```html\s*\n?', '', text)
        text = re.sub(r'\n?```', '', text)
        return text.strip()

    def _build_data_context(self, data: Dict[str, Any], date: str) -> str:
        """Build structured data context for LLM analysis."""
        is_range = 'period_kpis' in data

        # Gap Analysis
        gap = data.get('gap_analysis', {})
        total_planned = gap.get('total_planned', 0)
        total_actual = gap.get('total_actual', 0)
        achievement_pct = gap.get('achievement_pct', 0)
        remaining_target = gap.get('remaining_target', 0)
        days_remaining = gap.get('days_remaining', 0)
        required_daily = gap.get('required_daily_production', 0)
        avg_daily = gap.get('avg_daily_production', 0)
        increase_needed = gap.get('increase_needed_pct', 0)

        # Quality Stats
        quality = data.get('mtd_quality_stats') or data.get('quality_stats', {})
        avg_cr2o3 = quality.get('avg_cr2o3', 0)
        min_cr2o3 = quality.get('min_cr2o3', 0)
        max_cr2o3 = quality.get('max_cr2o3', 0)
        avg_ratio = quality.get('avg_ratio', 0)
        total_samples = quality.get('total_samples', 0)

        # Shift Performance
        shift_data = data.get('shift_plan_vs_actual', {})
        shift_rows = shift_data.get('rows', [])
        if not shift_rows:
            shift_rows = data.get('shift_breakdown', {}).get('rows', [])

        shift_text = ""
        for r in shift_rows:
            shift = r.get('shift', '?')
            planned = r.get('planned', 0)
            actual = r.get('actual', r.get('qty', 0))
            pct = r.get('achievement_pct', r.get('pct', 0))
            shift_text += f"  - Shift {shift}: Actual={actual} MT"
            if planned > 0:
                shift_text += f", Planned={planned} MT, Achievement={pct:.1f}%"
            shift_text += "\n"

        # Location Performance
        loc_data = data.get('location_breakdown', {}).get('rows', [])
        if not loc_data:
            loc_data = data.get('location_performance', {}).get('rows', [])
            if not loc_data:
                loc_data = data.get('mtd_location_performance', {}).get('rows', [])

        loc_text = ""
        for r in loc_data[:5]:
            loc_text += f"  - {r.get('location', 'Unknown')}: {r.get('qty', 0):,.0f} MT ({r.get('pct', 0):.1f}%)\n"

        # Agency Performance
        agency_data = data.get('agency_performance', {})
        if is_range:
            agency_rows = agency_data.get('rows', [])
        else:
            agency_rows = agency_data.get('mtd', {}).get('rows', [])

        agency_text = ""
        for r in agency_rows[:3]:
            agency_text += f"  - {r.get('agency', 'Unknown')}: {r.get('qty', 0):,.0f} MT ({r.get('pct', 0):.1f}%)\n"

        # Zero Progress Locations
        plan_rows = data.get('plan_vs_actual', {}).get('rows', [])
        zero_locs = [r for r in plan_rows if r.get('planned', 0) > 0 and r.get('actual', 0) == 0]
        zero_text = ""
        if zero_locs:
            for r in zero_locs[:5]:
                zero_text += f"  - {r.get('location', 'Unknown')}: {r.get('planned', 0):,.0f} MT planned, 0 actual\n"

        # KPIs
        if is_range:
            kpis = data.get('period_kpis', {})
            working_days = kpis.get('working_days', {}).get('value', 0)
            total_trips = kpis.get('trips', {}).get('value', 0)
            avg_load = kpis.get('avg_load', {}).get('value', 0)
        else:
            kpis = data.get('today_kpis', {})
            mtd_kpis = data.get('mtd_kpis', {})
            working_days = mtd_kpis.get('working_days', {}).get('value', 0)
            total_trips = kpis.get('trips', {}).get('value', 0)
            avg_load = kpis.get('avg_load', {}).get('value', 0)

        time_elapsed = data.get('time_elapsed_pct', 0)

        context = f"""=== GEOLOGY & SURVEY OPERATIONS DATA FOR {date} ===

PRODUCTION METRICS:
- Total Planned (Monthly): {total_planned:,.0f} MT
- Total Actual: {total_actual:,.0f} MT
- Achievement: {achievement_pct:.1f}%
- Remaining to Target: {remaining_target:,.0f} MT
- Time Elapsed: {time_elapsed:.1f}% of month
- Days Remaining: {days_remaining}
- Average Daily Production: {avg_daily:,.0f} MT/day
- Required Daily to Hit Target: {required_daily:,.0f} MT/day
- Productivity Increase Needed: {increase_needed:.1f}%

QUALITY METRICS:
- Average Cr2O3: {avg_cr2o3:.1f}% (HG>=52%, MG 40-52%, LG<40%)
- Range: {min_cr2o3:.1f}% to {max_cr2o3:.1f}%
- Cr:Fe Ratio: {avg_ratio:.2f}
- Total Samples: {total_samples}
- Samples per Day: {total_samples/working_days if working_days > 0 else 0:.1f}

OPERATIONAL METRICS:
- Working Days: {working_days}
- Total Trips: {total_trips:,}
- Average Load per Trip: {avg_load:.1f} MT (Standard: 15 MT)

SHIFT PERFORMANCE:
{shift_text if shift_text else "  No shift data available"}

LOCATION PERFORMANCE (Top 5):
{loc_text if loc_text else "  No location data available"}

AGENCY PERFORMANCE:
{agency_text if agency_text else "  No agency data available"}

LOCATIONS WITH ZERO PROGRESS (Planned but 0 Actual):
{zero_text if zero_text else "  None - all planned locations have some production"}
"""
        return context

    def generate_insights(self, analysis_data: Dict[str, Any], date: str) -> str:
        """Generate 8 insight cards using LLM."""
        logger.info(f"Generating AI insights for: {date}")

        data_context = self._build_data_context(analysis_data, date)

        prompt = f"""{data_context}

=== YOUR TASK ===

You are an expert mining operations analyst. Analyze the data above and generate EXACTLY 8 insight cards.

Each insight MUST:
1. Reference SPECIFIC numbers from the data (not generic statements)
2. Identify the ROOT CAUSE or pattern
3. Provide ACTIONABLE recommendations
4. Be something a mine manager would find valuable

=== OUTPUT FORMAT ===

Output EXACTLY 8 HTML divs in this format:
<div class="insight-card [CLASS]"><div class="insight-title">[EMOJI] [SHORT TITLE]</div><div class="insight-text">[2-3 sentences with specific numbers and actionable insight]</div></div>

CLASS OPTIONS:
- "danger" = red (critical: achievement <50%, major gaps, safety issues)
- "warning" = orange (concern: behind plan, inefficiencies, risks)
- "success" = green (positive: on track, good quality, improvements)
- "" = blue (neutral observation or informational)

=== REQUIRED INSIGHTS (generate these 8) ===

1. PLAN ACHIEVEMENT STATUS - Are we on track? By how much are we ahead/behind?
2. SHIFT PERFORMANCE - Which shift is best/worst? What's the gap?
3. QUALITY ANALYSIS - What grade are we mining? Is quality consistent?
4. LOCATION PATTERNS - Where is production concentrated? Any risks?
5. ZERO PROGRESS ALERT - Any planned locations with zero output?
6. LOAD EFFICIENCY - Compare actual vs 15 MT standard
7. AGENCY ANALYSIS - Any over-dependency on contractors?
8. SAMPLING COVERAGE - Are we sampling enough?

=== RULES ===
- Output ONLY the 8 <div> elements
- NO markdown, NO code blocks, NO explanations
- Use actual numbers from the data
- Make insights specific and actionable

OUTPUT THE 8 HTML DIVS NOW:"""

        try:
            response = self._call_llm(prompt)
            insights_html = self._strip_markdown(response)

            if 'insight-card' not in insights_html:
                logger.error("LLM response missing insight-card structure")
                raise ValueError("Invalid LLM response format")

            logger.info(f"AI insights generated successfully: {len(insights_html)} chars")
            return insights_html

        except Exception as e:
            logger.error(f"AI insight generation failed: {e}", exc_info=True)
            raise

    def generate_ai_summary(self, analysis_data: Dict[str, Any], date: str) -> str:
        """Generate AI executive summary."""
        logger.info(f"Generating AI summary for: {date}")

        data_context = self._build_data_context(analysis_data, date)

        prompt = f"""{data_context}

=== YOUR TASK ===

You are a senior mining operations analyst presenting to executives. Write a concise executive summary.

Cover:
1. Overall production status vs target
2. Key operational highlights (positive and negative)
3. Quality performance
4. Top 2-3 immediate action items

=== FORMAT ===

Write 4-5 short paragraphs wrapped in <p> tags with <br> between them.
Use <strong> tags for key metrics and section headers.
Be specific with numbers. Be concise. Be actionable.

Example:
<p><strong>Production Status:</strong> [assessment with numbers]</p><br>
<p><strong>Operational Performance:</strong> [insights]</p><br>
<p><strong>Quality Indicators:</strong> [analysis]</p><br>
<p><strong>Immediate Actions:</strong> [2-3 specific actions]</p>

=== RULES ===
- Output ONLY the HTML paragraphs
- NO markdown
- Use actual numbers
- Keep it executive-friendly
- Total: 150-250 words

OUTPUT NOW:"""

        try:
            response = self._call_llm(prompt)
            summary_html = self._strip_markdown(response)

            if '<p>' not in summary_html:
                logger.error("LLM summary response missing paragraph structure")
                raise ValueError("Invalid LLM response format")

            logger.info(f"AI summary generated successfully: {len(summary_html)} chars")
            return summary_html

        except Exception as e:
            logger.error(f"AI summary generation failed: {e}", exc_info=True)
            raise


# Exports
__all__ = ['ClaudeInsightsGenerator']
