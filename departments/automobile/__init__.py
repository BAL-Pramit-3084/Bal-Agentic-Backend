"""
Automobile Department Module
============================
Fleet Management Dashboard for MAN truck telematics.

Components:
- AutomobileDataProcessor: Queries truck_reports table
- AutomobileTemplateEngine: Generates HTML dashboard
- AutomobileInsightsGenerator: AI-powered fleet insights
"""

from .formatter import AutomobileDataProcessor, process_automobile_data
from .template_engine import AutomobileTemplateEngine, generate_automobile_dashboard
from .claude_analyzer import AutomobileInsightsGenerator, generate_automobile_insights

__all__ = [
    'AutomobileDataProcessor',
    'process_automobile_data',
    'AutomobileTemplateEngine',
    'generate_automobile_dashboard',
    'AutomobileInsightsGenerator',
    'generate_automobile_insights'
]