"""
Environment Department Module
=============================
Data processing, template rendering, and AI insights for Environment Department dashboards.

Components:
- ENVDataProcessor: Extracts and processes data from 14 ENV tables
- ENVTemplateEngine: Injects data into env_dashboard.html template
- ENVClaudeInsightsGenerator: Generates AI-powered insights using Claude API

Tables covered:
- kpi_env_food_waste_data
- kpi_env_stp_water_data
- kpi_env_cbam_data_emission_factors
- kpi_env_compliance
- kpi_env_compliance_return
- kpi_env_slag_gcp_dust_data
- kpi_env_biomedical_waste_data
- kpi_env_incident_report
- kpi_env_monitoring_report
- kpi_env_training_records
- kpi_env_water_consumption_data
- kpi_env_horticulture_plantation
- kpi_env_used_oil_data
- kpi_env_observation_report
"""

from .formatter import ENVDataProcessor, process_env_data
from .template_engine import ENVTemplateEngine, generate_env_dashboard
from .claude_analyzer import ENVClaudeInsightsGenerator, generate_env_insights

__all__ = [
    'ENVDataProcessor',
    'process_env_data',
    'ENVTemplateEngine',
    'generate_env_dashboard',
    'ENVClaudeInsightsGenerator',
    'generate_env_insights'
]