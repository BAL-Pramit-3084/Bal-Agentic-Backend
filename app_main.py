"""
BALASORE ALLOYS DASHBOARD SYSTEM - MAIN APPLICATION
====================================================

Production-Ready Flask Application
Version: 2.0
Author: Senior ML Engineer Team
Date: November 2025

This is the MAIN APPLICATION FILE that replaces app_flask.py
Integrates all modular components for production deployment.

ENDPOINTS FOR FRONTEND TEAM:
-----------------------------
Authentication: JWT Bearer tokens (coordinated with Node.js team)

1. GET  /health                           - Health check
2. GET  /api/v1/departments               - List all departments
3. GET  /api/v1/dashboard/<dept_id>       - Generate dashboard (requires ?date=YYYY-MM-DD)
4. GET  /preview/<file_id>                - Preview dashboard in iframe
5. GET  /download/<file_id>               - Download dashboard HTML
6. POST /api/v1/chat                      - AI Chatbot (body: {message, department})

DEPLOYMENT:
-----------
Port: 5100 (configurable in .env)
CORS: Configured for React frontend
Auth: JWT validation with Node.js backend
"""
# Department-specific imports (organized by department)
from departments.furnace import FurnaceDataProcessor, FurnaceTemplateEngine, ClaudeInsightsGenerator
from departments.qc import QCDataProcessor, QCTemplateEngine, QCClaudeInsightsGenerator
from departments.scm import SCMDataProcessor, SCMTemplateEngine, SCMClaudeInsightsGenerator
from departments.crm import CRMDataProcessor, CRMTemplateEngine, CRMClaudeInsightsGenerator
from departments.env import ENVDataProcessor, ENVTemplateEngine, ENVClaudeInsightsGenerator
from departments.geology import GeologyDataProcessor, GeologyTemplateEngine, GeologyClaudeInsightsGenerator
from departments.automobile import AutomobileDataProcessor, AutomobileTemplateEngine, AutomobileInsightsGenerator


import os
import sys
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import mysql.connector
import jwt
from werkzeug.security import check_password_hash
from core.log_manager import log_activity
from config_modules.config import DatabaseConfig, JWTConfig
from admin.admin_page import admin_bp
from routes.app_frontend import bp as frontend_bp
from core.mcp_server import MCPServer

from flask import Flask, request, jsonify, send_file, Response, g, current_app
from flask_cors import CORS
from dotenv import load_dotenv

# Import modular components
from config_modules.config import config, FlaskConfig, StorageConfig, ClaudeConfig, LocalLLMConfig, initialize
from dashboards.departments_config import DEPARTMENTS, get_enabled_departments, get_departments_list, get_department
from core.database import DatabaseConnector
from dashboards.template_engine import TemplateEngine

# Utility imports
from utils.prefix_loader import prefix_loader
from utils.chat_schema_builder import chat_schema_builder
from core.export_service import get_export_service


from flask import send_from_directory, request
from core.jwt_validator import JWTValidator, require_auth, require_admin

from routes.admin_auth_routes import admin_auth_bp
from routes.admin_routes import admin_routes_bp


# ============================================================================
# LEGACY IMPORT - CLAUDE API (PRESERVED FOR ROLLBACK)
# ============================================================================
# import anthropic  # Commented out 2025-12-16 - Replaced with OpenAI SDK

# ============================================================================
# NEW IMPORT - LOCAL LLM INTEGRATION
# ============================================================================
from openai import OpenAI  # OpenAI-compatible SDK for local LLM

# ============================================================================
# INITIALIZATION
# ============================================================================

# Load environment variables
load_dotenv()

# Initialize configuration
config_valid = initialize()
if not config_valid:
    print("⚠️  WARNING: Some configuration values are placeholders!")
    print("   Update your .env file before production deployment.")

# Setup logging
logging.basicConfig(
    level=logging.INFO if not FlaskConfig.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


import logging

# ============================================================================
# 🔧 DEBUG MODE - TEMPORARY AUTH BYPASS (FOR TESTING ONLY!)
# ============================================================================
DEBUG_MODE_SKIP_AUTH = True  # <-- Change to False for production
# ============================================================================

from functools import wraps

def smart_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if DEBUG_MODE_SKIP_AUTH:
            from types import SimpleNamespace
            g.user = SimpleNamespace(
                user_id='DEBUG_USER',
                username='debug_user',
                full_name='Debug Test User',
                role='admin',
                department='env',
                permissions={'admin': True}
            )
            logger.warning("🔧 DEBUG MODE: Auth bypassed!")
            return f(*args, **kwargs)
        else:
            return require_auth(f)(*args, **kwargs)
    return decorated_function
# ============================================================================


# ============================================================================
# FLASK APP SETUP
# ============================================================================

app = Flask(__name__)
app.static_folder = "static"
app.secret_key = FlaskConfig.SECRET_KEY
app.register_blueprint(frontend_bp, url_prefix="/dashboard")
logger.info("✅ Frontend UI registered at /")
app.register_blueprint(admin_bp)
logger.info(f"✅ Secure Admin App registered at {admin_bp.url_prefix}")
app.register_blueprint(admin_auth_bp)
app.logger.info(f"[ADMIN AUTH] Internal admin authentication blueprint registered successfully")
app.register_blueprint(admin_routes_bp, url_prefix="/admin")
app.logger.info("[ADMIN ROUTES] Admin blueprint registered at /admin")

# Register Voice addon (if enabled)
try:
    from addons.voice import voice_bp, is_voice_enabled
    if is_voice_enabled():
        app.register_blueprint(voice_bp)
        logger.info("✅ Voice addon (TTS/STT) registered at /api/v1/voice")
    else:
        logger.info("ℹ️  Voice addon disabled or not configured")
except ImportError as e:
    logger.warning(f"⚠️  Voice addon not available: {e}")

'''# CORS Configuration
CORS(app, resources={
    r"/api/*": {
        "origins": config.ALLOWED_ORIGINS,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})'''

CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Access-Control-Request-Private-Network"],
        "supports_credentials": True
    },
    r"/preview/*": {
        "origins": "*",
        "methods": ["GET", "OPTIONS"]
    },
    r"/download/*": {
        "origins": "*",
        "methods": ["GET", "OPTIONS"]
    }
})

# ============================================================================
# PRIVATE NETWORK ACCESS (PNA) HEADERS - FOR CROSS-ORIGIN REQUESTS
# ============================================================================
# This handles Chrome's Private Network Access security feature
# Required when: public IP frontend (80.9.2.78) → private IP backend (192.168.x.x)

@app.after_request
def add_private_network_access_headers(response):
    """
    Add Private Network Access headers for Chrome 94+ compatibility.
    This allows requests from public/external origins to private network addresses.
    """
    # Handle preflight requests for Private Network Access
    if request.method == "OPTIONS":
        # Check if this is a PNA preflight request
        if request.headers.get("Access-Control-Request-Private-Network"):
            response.headers["Access-Control-Allow-Private-Network"] = "true"

    # Always add these headers for the actual response
    response.headers["Access-Control-Allow-Private-Network"] = "true"

    return response



# ============================================================================
# GLOBAL INSTANCES
# ============================================================================
mcp_server = MCPServer()
jwt_validator = JWTValidator()
db_connector = DatabaseConnector()

# ============================================================================
# AI CLIENT INITIALIZATION
# ============================================================================

# ============================================================================
# LEGACY CODE - CLAUDE API CLIENT (PRESERVED FOR ROLLBACK)
# ============================================================================
# if ClaudeConfig.is_configured():
#     try:
#         claude_client = anthropic.Anthropic(api_key=ClaudeConfig.CLAUDE_API_KEY)
#         logger.info(f"✅ Claude API initialized: {ClaudeConfig.CLAUDE_MODEL}")
#     except TypeError as e:
#         logger.warning(f"⚠️  Claude API initialization warning: {e}")
#         try:
#             import anthropic as anthropic_module
#             claude_client = anthropic_module.Client(api_key=ClaudeConfig.CLAUDE_API_KEY)
#             logger.info(f"✅ Claude API initialized (legacy mode): {ClaudeConfig.CLAUDE_MODEL}")
#         except:
#             claude_client = None
#             logger.error("❌ Could not initialize Claude API - chatbot disabled")
# else:
#     claude_client = None
#     logger.warning("⚠️  Claude API not configured - chatbot will be disabled")

# ============================================================================
# OPENAI API CLIENT (ACTIVE - For Chatbot)
# ============================================================================
llm_client = None  # Will be used for chatbot

openai_api_key = os.getenv("OPENAI_API_KEY", "")
openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
openai_max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "4096"))

if openai_api_key:
    try:
        llm_client = OpenAI(api_key=openai_api_key)
        logger.info("="*70)
        logger.info("✅ OPENAI API CLIENT INITIALIZED (For Chatbot)")
        logger.info(f"   Model: {openai_model}")
        logger.info(f"   Temperature: {openai_temperature}")
        logger.info(f"   Max Tokens: {openai_max_tokens}")
        logger.info("="*70)
    except Exception as e:
        llm_client = None
        logger.error(f"❌ Could not initialize OpenAI client: {e}")
else:
    logger.warning("⚠️  OpenAI API key not configured - Chatbot will be disabled")
    logger.warning("   Set OPENAI_API_KEY in .env to enable")

# ============================================================================
# LOCAL LLM CLIENT (COMMENTED OUT - Preserved for rollback)
# ============================================================================
# if LocalLLMConfig.is_configured():
#     try:
#         llm_client = OpenAI(
#             api_key=LocalLLMConfig.API_KEY,
#             base_url=LocalLLMConfig.BASE_URL
#         )
#         logger.info("="*70)
#         logger.info("✅ LOCAL LLM CLIENT INITIALIZED")
#         logger.info(f"   Model: {LocalLLMConfig.MODEL}")
#         logger.info(f"   Endpoint: {LocalLLMConfig.BASE_URL}")
#         logger.info(f"   SSH Tunnel Required: {LocalLLMConfig.SSH_TUNNEL_COMMAND}")
#         logger.info("="*70)
#     except Exception as e:
#         llm_client = None
#         logger.error(f"❌ Could not initialize Local LLM client: {e}")
#         logger.error(f"   Ensure SSH tunnel is active: {LocalLLMConfig.SSH_TUNNEL_COMMAND}")
# else:
#     logger.warning("⚠️  Local LLM not configured - AI features will be disabled")
#     logger.warning(f"   Set LOCAL_LLM_ENABLED=true in .env to enable")

# Backward compatibility alias for existing code
claude_client = llm_client  # This ensures existing checks like "if claude_client:" still work

# Dashboard storage
DASHBOARD_STORAGE_DIR = StorageConfig.DASHBOARDS_DIR
os.makedirs(DASHBOARD_STORAGE_DIR, exist_ok=True)

# ============================================================================
# AUTHENTICATION DECORATOR
# ============================================================================


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.route('/', methods=['GET'])
def index():
    """Root endpoint - API information"""
    return jsonify({
        'success': True,
        'message': 'Balasore Alloys Dashboard API',
        'version': '2.0',
        'frontend': '/dashboard (Login to access the dashboard generation interface)',
        'endpoints': {
            'health': '/health',
            'departments': '/api/v1/departments',
            'dashboard_single_date': '/api/v1/dashboard/<dept_id>?date=YYYY-MM-DD',
            'dashboard_date_range': '/api/v1/dashboard/<dept_id>?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD',
            'preview': '/preview/<dashboard_id>',
            'download': '/download/<dashboard_id>',
            'chat': '/api/v1/chat'
        },
        'documentation': 'See API_DOCUMENTATION_FOR_FRONTEND.md',
        'note': 'All 7 departments support both single date and date range formats'
    })

# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring.

    Returns system status and component availability.
    """
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0',
        'components': {
            'database': 'connected',
            'claude_api': 'available' if claude_client else 'not_configured',
            'jwt_auth': 'enabled',
            'departments': len(get_enabled_departments())
        }
    })

# ============================================================================
# DEPARTMENTS ENDPOINT
# ============================================================================

@app.route('/api/v1/departments', methods=['GET'])
def list_departments():
    """
    List all available departments.

    Returns:
        {
            "success": true,
            "departments": [
                {
                    "id": "env",
                    "name": "Environment",
                    "icon": "🌿",
                    "description": "...",
                    "enabled": true,
                    "template_exists": true,
                    "kpi_count": 7
                }
            ]
        }
    """
    try:
        departments = get_departments_list()
        return jsonify({
            'success': True,
            'departments': departments,
            'count': len(departments)
        })
    except Exception as e:
        logger.error(f"Error listing departments: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': str(e)
        }), 500

# ============================================================================
# DASHBOARD GENERATION ENDPOINT
# ============================================================================

@app.route('/api/v1/dashboard/<dept_id>', methods=['GET'])
@smart_auth
def generate_dashboard(dept_id: str):
    """
    Generate dashboard for a specific department and date.
    Now requires authentication and logs activity.
    """
    # Get user info from the auth decorator
    # =============================================================
    #        comment below and uncomment below below
    # =============================================================
    user = type('obj', (object,), {'user_id': 'demo_user', 'full_name': 'Demo User'})()
    #user = g.user
    ip_address = request.remote_addr

    try:
        # NEW: Support BOTH date formats
        # OLD: ?date=YYYY-MM-DD (single date)
        # NEW: ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD (date range)

        date_str = request.args.get('date')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Validate parameters
        if not date_str and not (start_date and end_date):
            return jsonify({
                'success': False,
                'error': 'MISSING_PARAMETER',
                'message': 'Either "date" (single) or both "start_date" and "end_date" (range) are required (format: YYYY-MM-DD)'
            }), 400

        # Validate date formats
        try:
            if date_str:
                datetime.strptime(date_str, '%Y-%m-%d')
                logger.info(f"Dashboard request (SINGLE DATE): dept={dept_id}, date={date_str}, user={user.user_id}")
            else:
                datetime.strptime(start_date, '%Y-%m-%d')
                datetime.strptime(end_date, '%Y-%m-%d')
                # Validate range
                if datetime.strptime(start_date, '%Y-%m-%d') > datetime.strptime(end_date, '%Y-%m-%d'):
                    return jsonify({
                        'success': False,
                        'error': 'INVALID_RANGE',
                        'message': 'start_date must be before or equal to end_date'
                    }), 400
                logger.info(f"Dashboard request (DATE RANGE): dept={dept_id}, range={start_date} to {end_date}, user={user.user_id}")
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'INVALID_DATE',
                'message': 'Dates must be in YYYY-MM-DD format'
            }), 400


        # ============================================================
        # ROUTE TO SPECIALIZED HANDLERS (if needed)
        # ============================================================
        if dept_id.lower() == 'furnace':
            return _generate_furnace_dashboard_internal(user, ip_address, date_str, start_date, end_date)

        if dept_id.lower() == 'qc':
            return _generate_qc_dashboard_internal(user, ip_address, date_str, start_date, end_date)
        if dept_id.lower() == 'scm':
            return _generate_scm_dashboard_internal(user, ip_address, date_str, start_date, end_date)
        if dept_id.lower() == 'crm':
            return _generate_crm_dashboard_internal(user, ip_address, date_str, start_date, end_date)
        if dept_id.lower() == 'env':
            return _generate_env_dashboard_internal(user, ip_address, date_str, start_date, end_date)
        if dept_id.lower() == 'geology':
            return _generate_geology_dashboard_internal(user, ip_address, date_str, start_date, end_date)
        if dept_id.lower() == 'automobile':
            return _generate_automobile_dashboard_internal(user, ip_address, date_str, start_date, end_date)

        # ============================================================
        # Department not implemented - return helpful error
        # ============================================================
        dept = DEPARTMENTS.get(dept_id.lower())
        if not dept:
            return jsonify({
                'success': False,
                'error': 'DEPARTMENT_NOT_FOUND',
                'message': f'Department "{dept_id}" not found. Available: furnace, qc, scm, crm'
            }), 404

        if not dept.enabled:
            return jsonify({
                'success': False,
                'error': 'DEPARTMENT_DISABLED',
                'message': f'Department "{dept_id}" is not yet enabled. Contact admin to enable.'
            }), 403

        # Department exists but no handler implemented
        return jsonify({
            'success': False,
            'error': 'NOT_IMPLEMENTED',
            'message': f'Dashboard generation for "{dept.name}" is not yet implemented. Available departments: furnace, qc, scm, crm'
        }), 501

    except ImportError as e:
        logger.error(f"Import error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'CONFIGURATION_ERROR',
            'message': f'Missing module: {str(e)}. Check your file structure.'
        }), 500

    except Exception as e:
        logger.error(f"Dashboard generation error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'GENERATION_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# SPECIALIZED DASHBOARD HANDLERS
# ============================================================================

def _generate_furnace_dashboard_internal(user, ip_address: str, date_str: str = None, start_date: str = None, end_date: str = None):
    """Internal handler for Furnace dashboard generation. NEW: Supports date ranges."""
    try:
        is_range = start_date is not None and end_date is not None
        date_label = f"{start_date} to {end_date}" if is_range else date_str

        logger.info(f"Furnace: Step 1 - Processing data for {date_label}...")
        processor = FurnaceDataProcessor(mcp_server)

        if is_range:
            analysis_data = processor.process_date_range(start_date, end_date)
        else:
            analysis_data = processor.process_date(date_str)

        if not analysis_data.get('has_data'):
            log_activity(employee_id=user.user_id, action_type="DASHBOARD",
                        details=f"Furnace dashboard for {date_label}. Result: NO DATA.",
                        flagged=False, dashboard_path=None, ip_address=ip_address)
            return jsonify({'success': False, 'error': 'NO_DATA',
                          'message': f'No furnace data found for {date_label}'}), 404

        logger.info("Furnace: Step 2 - Generating AI insights...")
        # ====================================================================
        # LEGACY CODE - PRESERVED FOR ROLLBACK
        # ====================================================================
        # ====================================================================
        # CLAUDE API - COMMENTED OUT (NO CREDITS)
        # ====================================================================
        # insights_generator = ClaudeInsightsGenerator(
        #     api_key=ClaudeConfig.CLAUDE_API_KEY,
        #     model=ClaudeConfig.CLAUDE_MODEL
        # )

        # ====================================================================
        # LOCAL LLM - ACTIVE
        # ====================================================================
        insights_generator = ClaudeInsightsGenerator(
            api_key=LocalLLMConfig.API_KEY,
            model=LocalLLMConfig.MODEL,
            base_url=LocalLLMConfig.BASE_URL
        )
        claude_insights_html = insights_generator.generate_insights(analysis_data, date_label)

        logger.info("Furnace: Step 3 - Generating HTML...")
        template_engine = FurnaceTemplateEngine()
        html_content = template_engine.generate_dashboard(analysis_data, claude_insights_html, date_label)

        # Save file
        dashboard_id = str(uuid.uuid4())
        filename_date = f"{start_date}_to_{end_date}" if is_range else date_str
        filename = f"dashboard_furnace_{filename_date}_{dashboard_id}.html"
        filepath = os.path.join(DASHBOARD_STORAGE_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        log_activity(employee_id=user.user_id, action_type="DASHBOARD",
                    details=f"Furnace dashboard for {date_label}. Result: SUCCESS.",
                    flagged=False, dashboard_path=filepath, ip_address=ip_address)

        base_url = request.host_url.rstrip('/')
        response_data = {
            'success': True, 'dashboard_id': dashboard_id,
            'preview_url': f"{base_url}/preview/{dashboard_id}",
            'download_url': f"{base_url}/download/{dashboard_id}",
            'department': 'Furnace Operations', 'department_id': 'furnace',
            'generated_at': datetime.now().isoformat(),
            'has_ai_insights': True
        }

        if is_range:
            response_data['start_date'] = start_date
            response_data['end_date'] = end_date
            response_data['date_range'] = date_label
        else:
            response_data['date'] = date_str

        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Furnace dashboard error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'GENERATION_ERROR', 'message': str(e)}), 500


def _generate_qc_dashboard_internal(user, ip_address: str, date_str=None, start_date=None, end_date=None):
    """
    Internal helper for QC dashboard generation WITH Claude AI insights.
    NEW: Supports both single date and date range.
    """
    try:
        # Determine if this is a range or single date request
        is_range = start_date is not None and end_date is not None
        date_label = f"{start_date} to {end_date}" if is_range else date_str

        logger.info(f"QC dashboard request ({'DATE RANGE' if is_range else 'SINGLE DATE'}): {date_label}, user={user.user_id}")

        # STEP 1: Process data using QCDataProcessor
        logger.info("Step 1: Processing QC data from database...")
        processor = QCDataProcessor(mcp_server)

        if is_range:
            analysis_data = processor.process_date_range(start_date, end_date)
        else:
            analysis_data = processor.process_date(date_str)

        # Check if we have data
        if not analysis_data.get('has_data'):
            logger.warning(f"No QC data found for {date_label}")
            log_activity(
                employee_id=user.user_id,
                action_type="DASHBOARD",
                details=f"User {user.full_name} requested QC dashboard for {date_label}. Result: NO DATA.",
                flagged=False,
                dashboard_path=None,
                ip_address=ip_address
            )
            return jsonify({
                'success': False,
                'error': 'NO_DATA',
                'message': f'No QC operations data found for {date_label}'
            }), 404

        logger.info(f"✅ Data processing complete. Has data: True")

        # STEP 2: Generate AI insights using Claude
        logger.info("Step 2: Generating AI insights with Claude API...")

        # ====================================================================
        # LEGACY CODE - PRESERVED FOR ROLLBACK
        # ====================================================================
        # if not ClaudeConfig.is_configured():
        #     logger.error("Claude API not configured!")
        #     return jsonify({
        #         'success': False,
        #         'error': 'CONFIGURATION_ERROR',
        #         'message': 'Claude API is not configured. Check CLAUDE_API_KEY in .env'
        #     }), 500
        # insights_generator = QCClaudeInsightsGenerator(
        #     api_key=ClaudeConfig.CLAUDE_API_KEY,
        #     model=ClaudeConfig.CLAUDE_MODEL
        # )

        # ====================================================================
        # NEW CODE - LOCAL LLM
        # ====================================================================
        if not LocalLLMConfig.is_configured():
            logger.error("Local LLM not configured!")
            return jsonify({
                'success': False,
                'error': 'CONFIGURATION_ERROR',
                'message': 'Local LLM is not configured. Check LOCAL_LLM_ENABLED in .env'
            }), 500

        insights_generator = QCClaudeInsightsGenerator(
            api_key=LocalLLMConfig.API_KEY,
            model=LocalLLMConfig.MODEL,
            base_url=LocalLLMConfig.BASE_URL
        )
        claude_insights_html = insights_generator.generate_insights(analysis_data, date_label)
        logger.info(f"✅ Local LLM insights generated ({len(claude_insights_html)} chars)")

        # STEP 3: Generate HTML dashboard
        logger.info("Step 3: Generating dashboard HTML...")
        template_engine = QCTemplateEngine()
        html_content = template_engine.generate_dashboard(
            analysis_data,
            claude_insights_html,
            date_label
        )
        logger.info(f"✅ Dashboard HTML generated ({len(html_content)} chars)")

        # STEP 4: Save to file
        dashboard_id = str(uuid.uuid4())
        date_filename = date_label.replace(' to ', '_') if is_range else date_label
        filename = f"dashboard_qc_{date_filename}_{dashboard_id}.html"
        filepath = os.path.join(DASHBOARD_STORAGE_DIR, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"✅ Dashboard saved: {filename}")

        # Log successful generation
        log_activity(
            employee_id=user.user_id,
            action_type="DASHBOARD",
            details=f"User {user.full_name} generated QC dashboard for {date_label}. Result: SUCCESS.",
            flagged=False,
            dashboard_path=filepath,
            ip_address=ip_address
        )

        # STEP 5: Build response URLs
        base_url = request.host_url.rstrip('/')
        preview_url = f"{base_url}/preview/{dashboard_id}"
        download_url = f"{base_url}/download/{dashboard_id}"

        # Build response with appropriate date fields
        response_data = {
            'success': True,
            'dashboard_id': dashboard_id,
            'preview_url': preview_url,
            'download_url': download_url,
            'department': 'Quality Control',
            'department_id': 'qc',
            'generated_at': datetime.now().isoformat(),
            'has_ai_insights': True
        }

        if is_range:
            response_data.update({
                'start_date': start_date,
                'end_date': end_date,
                'date_range': date_label
            })
        else:
            response_data['date'] = date_str

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"QC dashboard generation error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'GENERATION_ERROR',
            'message': str(e)
        }), 500

def _generate_scm_dashboard_internal(user, ip_address: str, date_str=None, start_date=None, end_date=None):
    """
    Internal helper for SCM dashboard generation WITH Claude AI insights.
    NEW: Supports both single date and date range.
    """
    try:
        # Determine if this is a range or single date request
        is_range = start_date is not None and end_date is not None
        date_label = f"{start_date} to {end_date}" if is_range else date_str

        logger.info(f"SCM dashboard request ({'DATE RANGE' if is_range else 'SINGLE DATE'}): {date_label}, user={user.user_id}")

        # STEP 1: Process data using SCMDataProcessor
        logger.info("SCM: Step 1 - Processing PO and PR data from database...")
        processor = SCMDataProcessor(mcp_server)

        if is_range:
            analysis_data = processor.process_date_range(start_date, end_date)
        else:
            analysis_data = processor.process_date(date_str)

        # Check if we have data
        if not analysis_data.get('has_data'):
            logger.warning(f"SCM: No data found for {date_label}")
            log_activity(
                employee_id=user.user_id,
                action_type="DASHBOARD",
                details=f"User {user.full_name} requested SCM dashboard for {date_label}. Result: NO DATA.",
                flagged=False,
                dashboard_path=None,
                ip_address=ip_address
            )
            return jsonify({
                'success': False,
                'error': 'NO_DATA',
                'message': f'No SCM (Purchase Orders/Requisitions) data found for {date_label}'
            }), 404

        logger.info(f"SCM: ✅ Data processing complete. POs: {analysis_data.get('summary_metrics', {}).get('po_count', 0)}, PRs: {analysis_data.get('purchase_requisitions', {}).get('count', 0)}")

        # STEP 2: Generate AI insights using Local LLM
        logger.info("SCM: Step 2 - Generating AI insights with Local LLM...")

        # ====================================================================
        # LEGACY CODE - PRESERVED FOR ROLLBACK
        # ====================================================================
        # if not ClaudeConfig.is_configured():
        #     logger.error("SCM: Claude API not configured!")
        #     return jsonify({
        #         'success': False,
        #         'error': 'CONFIGURATION_ERROR',
        #         'message': 'Claude API is not configured. Check CLAUDE_API_KEY in .env'
        #     }), 500
        # insights_generator = SCMClaudeInsightsGenerator(
        #     api_key=ClaudeConfig.CLAUDE_API_KEY
        # )

        # ====================================================================
        # NEW CODE - LOCAL LLM
        # ====================================================================
        if not LocalLLMConfig.is_configured():
            logger.error("SCM: Local LLM not configured!")
            return jsonify({
                'success': False,
                'error': 'CONFIGURATION_ERROR',
                'message': 'Local LLM is not configured. Check LOCAL_LLM_ENABLED in .env'
            }), 500

        insights_generator = SCMClaudeInsightsGenerator(
            api_key=LocalLLMConfig.API_KEY,
            model=LocalLLMConfig.MODEL,
            base_url=LocalLLMConfig.BASE_URL
        )
        claude_insights_html = insights_generator.generate_insights(analysis_data, date_label)
        logger.info(f"SCM: ✅ Local LLM insights generated ({len(claude_insights_html)} chars)")

        # STEP 3: Generate HTML dashboard
        logger.info("SCM: Step 3 - Generating dashboard HTML...")
        template_engine = SCMTemplateEngine()
        html_content = template_engine.generate_dashboard(
            analysis_data,
            claude_insights_html,
            date_label
        )
        logger.info(f"SCM: ✅ Dashboard HTML generated ({len(html_content)} chars)")

        # STEP 4: Save to file
        dashboard_id = str(uuid.uuid4())
        date_filename = date_label.replace(' to ', '_') if is_range else date_label
        filename = f"dashboard_scm_{date_filename}_{dashboard_id}.html"
        filepath = os.path.join(DASHBOARD_STORAGE_DIR, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"SCM: ✅ Dashboard saved: {filename}")

        # Log successful generation
        log_activity(
            employee_id=user.user_id,
            action_type="DASHBOARD",
            details=f"User {user.full_name} generated SCM dashboard for {date_label}. Result: SUCCESS.",
            flagged=False,
            dashboard_path=filepath,
            ip_address=ip_address
        )

        # STEP 5: Build response URLs
        base_url = request.host_url.rstrip('/')
        preview_url = f"{base_url}/preview/{dashboard_id}"
        download_url = f"{base_url}/download/{dashboard_id}"

        # Build response with appropriate date fields
        response_data = {
            'success': True,
            'dashboard_id': dashboard_id,
            'preview_url': preview_url,
            'download_url': download_url,
            'department': 'Supply Chain Management',
            'department_id': 'scm',
            'generated_at': datetime.now().isoformat(),
            'has_ai_insights': True
        }

        if is_range:
            response_data.update({
                'start_date': start_date,
                'end_date': end_date,
                'date_range': date_label
            })
        else:
            response_data['date'] = date_str

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"SCM dashboard generation error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'GENERATION_ERROR',
            'message': str(e)
        }), 500

def _generate_crm_dashboard_internal(user, ip_address: str, date_str=None, start_date=None, end_date=None):
    """
    Internal helper for CRM/Sales & Distribution dashboard generation WITH Claude AI insights.
    NEW: Supports both single date and date range.
    """
    try:
        # Determine if this is a range or single date request
        is_range = start_date is not None and end_date is not None
        date_label = f"{start_date} to {end_date}" if is_range else date_str

        logger.info(f"CRM dashboard request ({'DATE RANGE' if is_range else 'SINGLE DATE'}): {date_label}, user={user.user_id}")

        # STEP 1: Process data using CRMDataProcessor
        logger.info("CRM: Step 1 - Processing sales/billing data from database...")
        processor = CRMDataProcessor(mcp_server)

        if is_range:
            analysis_data = processor.process_date_range(start_date, end_date)
        else:
            analysis_data = processor.process_date(date_str)

        # Check if we have data
        if not analysis_data.get('has_data'):
            logger.warning(f"CRM: No data found for {date_label}")
            log_activity(
                employee_id=user.user_id,
                action_type="DASHBOARD",
                details=f"User {user.full_name} requested CRM dashboard for {date_label}. Result: NO DATA.",
                flagged=False,
                dashboard_path=None,
                ip_address=ip_address
            )
            return jsonify({
                'success': False,
                'error': 'NO_DATA',
                'message': f'No CRM (Sales/Billing) data found for {date_label}'
            }), 404

        logger.info(f"CRM: ✅ Data processing complete. Orders: {analysis_data.get('sales_orders', {}).get('td', {}).get('count', 0)}, Invoices: {analysis_data.get('billing', {}).get('td', {}).get('invoice_count', 0)}")

        # STEP 2: Generate AI insights using Local LLM
        logger.info("CRM: Step 2 - Generating AI insights with Local LLM...")

        # ====================================================================
        # LEGACY CODE - PRESERVED FOR ROLLBACK
        # ====================================================================
        # if not ClaudeConfig.is_configured():
        #     logger.error("CRM: Claude API not configured!")
        #     return jsonify({
        #         'success': False,
        #         'error': 'CONFIGURATION_ERROR',
        #         'message': 'Claude API is not configured. Check CLAUDE_API_KEY in .env'
        #     }), 500
        # insights_generator = CRMClaudeInsightsGenerator(
        #     api_key=ClaudeConfig.CLAUDE_API_KEY
        # )

        # ====================================================================
        # NEW CODE - LOCAL LLM
        # ====================================================================
        if not LocalLLMConfig.is_configured():
            logger.error("CRM: Local LLM not configured!")
            return jsonify({
                'success': False,
                'error': 'CONFIGURATION_ERROR',
                'message': 'Local LLM is not configured. Check LOCAL_LLM_ENABLED in .env'
            }), 500

        insights_generator = CRMClaudeInsightsGenerator(
            api_key=LocalLLMConfig.API_KEY,
            model=LocalLLMConfig.MODEL,
            base_url=LocalLLMConfig.BASE_URL
        )
        claude_insights_html = insights_generator.generate_insights(analysis_data, date_label)
        logger.info(f"CRM: ✅ Local LLM insights generated ({len(claude_insights_html)} chars)")

        # STEP 3: Generate HTML dashboard
        logger.info("CRM: Step 3 - Generating dashboard HTML...")
        template_engine = CRMTemplateEngine()
        html_content = template_engine.generate_dashboard(
            analysis_data,
            claude_insights_html,
            date_label
        )
        logger.info(f"CRM: ✅ Dashboard HTML generated ({len(html_content)} chars)")

        # STEP 4: Save to file
        dashboard_id = str(uuid.uuid4())
        date_filename = date_label.replace(' to ', '_') if is_range else date_label
        filename = f"dashboard_crm_{date_filename}_{dashboard_id}.html"
        filepath = os.path.join(DASHBOARD_STORAGE_DIR, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"CRM: ✅ Dashboard saved: {filename}")

        # Log successful generation
        log_activity(
            employee_id=user.user_id,
            action_type="DASHBOARD",
            details=f"User {user.full_name} generated CRM dashboard for {date_label}. Result: SUCCESS.",
            flagged=False,
            dashboard_path=filepath,
            ip_address=ip_address
        )

        # STEP 5: Build response URLs
        base_url = request.host_url.rstrip('/')
        preview_url = f"{base_url}/preview/{dashboard_id}"
        download_url = f"{base_url}/download/{dashboard_id}"

        # Build response with appropriate date fields
        response_data = {
            'success': True,
            'dashboard_id': dashboard_id,
            'preview_url': preview_url,
            'download_url': download_url,
            'department': 'Sales & Distribution',
            'department_id': 'crm',
            'generated_at': datetime.now().isoformat(),
            'has_ai_insights': True
        }

        if is_range:
            response_data.update({
                'start_date': start_date,
                'end_date': end_date,
                'date_range': date_label
            })
        else:
            response_data['date'] = date_str

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"CRM dashboard generation error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'GENERATION_ERROR',
            'message': str(e)
        }), 500


# INSERT AFTER LINE 753 (after CRM function's except block ends):

def _generate_env_dashboard_internal(user, ip_address: str, date_str=None, start_date=None, end_date=None):
    """
    Internal helper for Environment Department dashboard generation WITH Claude AI insights.
    NEW: Supports both single date and date range.
    """
    try:
        # Determine if this is a range or single date request
        is_range = start_date is not None and end_date is not None
        date_label = f"{start_date} to {end_date}" if is_range else date_str

        logger.info(f"ENV dashboard request ({'DATE RANGE' if is_range else 'SINGLE DATE'}): {date_label}, user={user.user_id}")

        # STEP 1: Process data using ENVDataProcessor
        logger.info("ENV: Step 1 - Processing environment data from 14 tables...")
        processor = ENVDataProcessor(mcp_server)

        if is_range:
            analysis_data = processor.process_date_range(start_date, end_date)
        else:
            analysis_data = processor.process_date(date_str)

        # Check if we have data
        if not analysis_data.get('has_data'):
            logger.warning(f"ENV: No data found for {date_label}")
            log_activity(
                employee_id=user.user_id,
                action_type="DASHBOARD",
                details=f"User {user.full_name} requested ENV dashboard for {date_label}. Result: NO DATA.",
                flagged=False,
                dashboard_path=None,
                ip_address=ip_address
            )
            return jsonify({
                'success': False,
                'error': 'NO_DATA',
                'message': f'No Environment data found for {date_label}'
            }), 404

        logger.info(f"ENV: ✅ Data processing complete. Food waste: {analysis_data.get('food_waste', {}).get('td', {}).get('total_waste', 0)} kg")

        # STEP 2: Generate AI insights using Local LLM
        logger.info("ENV: Step 2 - Generating AI insights with Local LLM...")

        # ====================================================================
        # LEGACY CODE - PRESERVED FOR ROLLBACK
        # ====================================================================
        # if not ClaudeConfig.is_configured():
        #     logger.error("ENV: Claude API not configured!")
        #     return jsonify({
        #         'success': False,
        #         'error': 'CONFIGURATION_ERROR',
        #         'message': 'Claude API is not configured. Check CLAUDE_API_KEY in .env'
        #     }), 500
        # insights_generator = ENVClaudeInsightsGenerator(
        #     api_key=ClaudeConfig.CLAUDE_API_KEY
        # )

        # ====================================================================
        # NEW CODE - LOCAL LLM
        # ====================================================================
        if not LocalLLMConfig.is_configured():
            logger.error("ENV: Local LLM not configured!")
            return jsonify({
                'success': False,
                'error': 'CONFIGURATION_ERROR',
                'message': 'Local LLM is not configured. Check LOCAL_LLM_ENABLED in .env'
            }), 500

        insights_generator = ENVClaudeInsightsGenerator(
            api_key=LocalLLMConfig.API_KEY,
            model=LocalLLMConfig.MODEL,
            base_url=LocalLLMConfig.BASE_URL
        )
        claude_insights_html = insights_generator.generate_insights(analysis_data, date_label)
        logger.info(f"ENV: ✅ Local LLM insights generated ({len(claude_insights_html)} chars)")

        # STEP 3: Generate HTML dashboard
        logger.info("ENV: Step 3 - Generating dashboard HTML...")
        template_engine = ENVTemplateEngine()
        html_content = template_engine.generate_dashboard(
            analysis_data,
            claude_insights_html,
            date_label
        )
        logger.info(f"ENV: ✅ Dashboard HTML generated ({len(html_content)} chars)")

        # STEP 4: Save to file
        dashboard_id = str(uuid.uuid4())
        date_filename = date_label.replace(' to ', '_') if is_range else date_label
        filename = f"dashboard_env_{date_filename}_{dashboard_id}.html"
        filepath = os.path.join(DASHBOARD_STORAGE_DIR, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"ENV: ✅ Dashboard saved: {filename}")

        # Log successful generation
        log_activity(
            employee_id=user.user_id,
            action_type="DASHBOARD",
            details=f"User {user.full_name} generated ENV dashboard for {date_label}. Result: SUCCESS.",
            flagged=False,
            dashboard_path=filepath,
            ip_address=ip_address
        )

        # STEP 5: Build response URLs
        base_url = request.host_url.rstrip('/')
        preview_url = f"{base_url}/preview/{dashboard_id}"
        download_url = f"{base_url}/download/{dashboard_id}"

        # Build response with appropriate date fields
        response_data = {
            'success': True,
            'dashboard_id': dashboard_id,
            'preview_url': preview_url,
            'download_url': download_url,
            'department': 'Environment',
            'department_id': 'env',
            'generated_at': datetime.now().isoformat(),
            'has_ai_insights': True
        }

        if is_range:
            response_data.update({
                'start_date': start_date,
                'end_date': end_date,
                'date_range': date_label
            })
        else:
            response_data['date'] = date_str

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"ENV dashboard generation error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'GENERATION_ERROR',
            'message': str(e)
        }), 500


def _generate_geology_dashboard_internal(user, ip_address: str, date_str: str = None, start_date: str = None, end_date: str = None):
    """
    Internal helper for Geology & Survey dashboard generation WITH Claude AI insights.

    NEW: Supports both single date and date range.
    Args:
        user: User object
        ip_address: Client IP
        date_str: Single date (OLD format) - optional
        start_date: Range start date (NEW format) - optional
        end_date: Range end date (NEW format) - optional
    """
    try:
        # Determine which mode we're in
        is_range = start_date is not None and end_date is not None

        if is_range:
            date_label = f"{start_date} to {end_date}"
            logger.info(f"GEOLOGY dashboard request (RANGE): {date_label}, user={user.user_id}")
        else:
            date_label = date_str
            logger.info(f"GEOLOGY dashboard request (SINGLE): date={date_str}, user={user.user_id}")

        # STEP 1: Process data using GeologyDataProcessor
        logger.info("GEOLOGY: Step 1 - Processing mining/geology data from 7 tables...")
        processor = GeologyDataProcessor(mcp_server)

        if is_range:
            analysis_data = processor.process_date_range(start_date, end_date)
        else:
            analysis_data = processor.process_date(date_str)

        # Check if we have data
        if not analysis_data.get('has_data'):
            logger.warning(f"GEOLOGY: No data found for {date_label}")
            log_activity(
                employee_id=user.user_id,
                action_type="DASHBOARD",
                details=f"User {user.full_name} requested GEOLOGY dashboard for {date_label}. Result: NO DATA.",
                flagged=False,
                dashboard_path=None,
                ip_address=ip_address
            )
            return jsonify({
                'success': False,
                'error': 'NO_DATA',
                'message': f'No Geology & Survey data found for {date_label}'
            }), 404

        # Log success with appropriate KPI key
        kpi_key = 'period_kpis' if is_range else 'today_kpis'
        excavation_value = analysis_data.get(kpi_key, {}).get('excavation', {}).get('value', 0)
        logger.info(f"GEOLOGY: ✅ Data processing complete. Excavation: {excavation_value} MT")

        # STEP 2: Generate AI insights
        # =======================================================================
        # OPENAI API (ACTIVE)
        # =======================================================================
        logger.info("GEOLOGY: Step 2 - Generating AI insights with OpenAI...")

        openai_api_key = os.getenv("OPENAI_API_KEY", "")
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")  # Latest model from .env

        if not openai_api_key:
            logger.error("GEOLOGY: OpenAI API key not configured!")
            return jsonify({
                'success': False,
                'error': 'CONFIGURATION_ERROR',
                'message': 'OpenAI API key is not configured. Check OPENAI_API_KEY in .env'
            }), 500

        insights_generator = GeologyClaudeInsightsGenerator(
            api_key=openai_api_key,
            model=openai_model
        )
        claude_insights_html = insights_generator.generate_insights(analysis_data, date_label)
        logger.info(f"GEOLOGY: ✅ OpenAI insights generated ({len(claude_insights_html)} chars)")

        # =======================================================================
        # LOCAL LLM (COMMENTED OUT - UNCOMMENT TO USE INSTEAD OF OPENAI)
        # =======================================================================
        # To use Local LLM instead:
        # 1. Comment out the OpenAI section above
        # 2. Uncomment the code below
        # 3. Ensure LOCAL_LLM_ENABLED=true in .env
        #
        # logger.info("GEOLOGY: Step 2 - Generating AI insights with Local LLM...")
        #
        # if not LocalLLMConfig.is_configured():
        #     logger.error("GEOLOGY: Local LLM not configured!")
        #     return jsonify({
        #         'success': False,
        #         'error': 'CONFIGURATION_ERROR',
        #         'message': 'Local LLM is not configured. Check LOCAL_LLM_ENABLED in .env'
        #     }), 500
        #
        # insights_generator = GeologyClaudeInsightsGenerator(
        #     api_key=LocalLLMConfig.API_KEY,
        #     model=LocalLLMConfig.MODEL,
        #     base_url=LocalLLMConfig.BASE_URL
        # )
        # claude_insights_html = insights_generator.generate_insights(analysis_data, date_label)
        # logger.info(f"GEOLOGY: ✅ Local LLM insights generated ({len(claude_insights_html)} chars)")

        # Generate AI Executive Summary
        ai_summary_html = insights_generator.generate_ai_summary(analysis_data, date_label)
        logger.info(f"GEOLOGY: ✅ AI summary generated ({len(ai_summary_html)} chars)")

        # STEP 3: Generate HTML dashboard
        logger.info("GEOLOGY: Step 3 - Generating dashboard HTML...")
        template_engine = GeologyTemplateEngine()
        html_content = template_engine.generate_dashboard(
            analysis_data,
            claude_insights_html,
            date_label,
            ai_summary_html=ai_summary_html
        )
        logger.info(f"GEOLOGY: ✅ Dashboard HTML generated ({len(html_content)} chars)")

        # STEP 4: Save to file
        dashboard_id = str(uuid.uuid4())
        filename_date = f"{start_date}_to_{end_date}" if is_range else date_str
        filename = f"dashboard_geology_{filename_date}_{dashboard_id}.html"
        filepath = os.path.join(DASHBOARD_STORAGE_DIR, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"GEOLOGY: ✅ Dashboard saved: {filename}")

        # Log successful generation
        log_activity(
            employee_id=user.user_id,
            action_type="DASHBOARD",
            details=f"User {user.full_name} generated GEOLOGY dashboard for {date_label}. Result: SUCCESS.",
            flagged=False,
            dashboard_path=filepath,
            ip_address=ip_address
        )

        # STEP 5: Build response URLs
        base_url = request.host_url.rstrip('/')
        preview_url = f"{base_url}/preview/{dashboard_id}"
        download_url = f"{base_url}/download/{dashboard_id}"

        response_data = {
            'success': True,
            'dashboard_id': dashboard_id,
            'preview_url': preview_url,
            'download_url': download_url,
            'department': 'Geology & Survey',
            'department_id': 'geology',
            'generated_at': datetime.now().isoformat(),
            'has_ai_insights': True
        }

        # Add appropriate date fields based on mode
        if is_range:
            response_data['start_date'] = start_date
            response_data['end_date'] = end_date
            response_data['date_range'] = date_label
        else:
            response_data['date'] = date_str

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"GEOLOGY dashboard generation error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'GENERATION_ERROR',
            'message': str(e)
        }), 500


def _generate_automobile_dashboard_internal(user, ip_address: str, date_str=None, start_date=None, end_date=None):
    """
    Internal helper for Automobile/Fleet dashboard generation WITH AI insights.
    NEW: Supports both single date and date range.
    """
    try:
        # Determine if this is a range or single date request
        is_range = start_date is not None and end_date is not None
        date_label = f"{start_date} to {end_date}" if is_range else date_str

        logger.info(f"Automobile dashboard request ({'DATE RANGE' if is_range else 'SINGLE DATE'}): {date_label}, user={user.user_id}")

        # STEP 1: Process data using AutomobileDataProcessor
        logger.info("Automobile: Step 1 - Processing fleet telematics data...")
        processor = AutomobileDataProcessor(mcp_server)

        if is_range:
            analysis_data = processor.process_date_range(start_date, end_date)
        else:
            analysis_data = processor.process_date(date_str)

        # Check if we have data
        if not analysis_data.get('has_data'):
            logger.warning(f"Automobile: No data found for {date_label}")
            log_activity(
                employee_id=user.user_id,
                action_type="DASHBOARD",
                details=f"User {user.full_name} requested Automobile dashboard for {date_label}. Result: NO DATA.",
                flagged=False,
                dashboard_path=None,
                ip_address=ip_address
            )
            return jsonify({
                'success': False,
                'error': 'NO_DATA',
                'message': f'No truck fleet data found for {date_label}'
            }), 404

        logger.info(f"Automobile: ✅ Data processing complete. Active trucks: {analysis_data.get('kpis', {}).get('active_trucks', 0)}")

        # STEP 2: Generate AI insights using Local LLM
        logger.info("Automobile: Step 2 - Generating AI insights with Local LLM...")

        if not LocalLLMConfig.is_configured():
            logger.error("Automobile: Local LLM not configured!")
            return jsonify({
                'success': False,
                'error': 'CONFIGURATION_ERROR',
                'message': 'Local LLM is not configured. Check LOCAL_LLM_ENABLED in .env'
            }), 500

        insights_generator = AutomobileInsightsGenerator(
            api_key=LocalLLMConfig.API_KEY,
            model=LocalLLMConfig.MODEL,
            base_url=LocalLLMConfig.BASE_URL
        )
        claude_insights_html = insights_generator.generate_insights(analysis_data, date_label)
        logger.info(f"Automobile: ✅ AI insights generated ({len(claude_insights_html)} chars)")

        # STEP 3: Generate HTML dashboard
        logger.info("Automobile: Step 3 - Generating dashboard HTML...")
        template_engine = AutomobileTemplateEngine()
        html_content = template_engine.generate_dashboard(
            analysis_data,
            claude_insights_html,
            date_label
        )
        logger.info(f"Automobile: ✅ Dashboard HTML generated ({len(html_content)} chars)")

        # STEP 4: Save to file
        dashboard_id = str(uuid.uuid4())
        date_filename = date_label.replace(' to ', '_') if is_range else date_label
        filename = f"dashboard_automobile_{date_filename}_{dashboard_id}.html"
        filepath = os.path.join(DASHBOARD_STORAGE_DIR, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Automobile: ✅ Dashboard saved: {filename}")

        # Log successful generation
        log_activity(
            employee_id=user.user_id,
            action_type="DASHBOARD",
            details=f"User {user.full_name} generated Automobile dashboard for {date_label}. Result: SUCCESS.",
            flagged=False,
            dashboard_path=filepath,
            ip_address=ip_address
        )

        # STEP 5: Build response URLs
        base_url = request.host_url.rstrip('/')
        preview_url = f"{base_url}/preview/{dashboard_id}"
        download_url = f"{base_url}/download/{dashboard_id}"

        # Build response with appropriate date fields
        response_data = {
            'success': True,
            'dashboard_id': dashboard_id,
            'preview_url': preview_url,
            'download_url': download_url,
            'department': 'Fleet Management',
            'department_id': 'automobile',
            'generated_at': datetime.now().isoformat(),
            'has_ai_insights': True
        }

        if is_range:
            response_data.update({
                'start_date': start_date,
                'end_date': end_date,
                'date_range': date_label
            })
        else:
            response_data['date'] = date_str

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Automobile dashboard generation error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'GENERATION_ERROR',
            'message': str(e)
        }), 500

# ============================================================================
# PREVIEW ENDPOINT
# ============================================================================

@app.route('/preview/<dashboard_id>', methods=['GET'])
def preview_dashboard(dashboard_id: str):
    """
    Preview dashboard in browser (for iframe embedding).

    Path Parameters:
        dashboard_id: Dashboard UUID

    Returns:
        HTML file for display
    """
    try:
        # Find file by dashboard_id
        files = [f for f in os.listdir(DASHBOARD_STORAGE_DIR) if dashboard_id in f]

        if not files:
            return jsonify({
                'success': False,
                'error': 'NOT_FOUND',
                'message': 'Dashboard not found or expired'
            }), 404

        filepath = os.path.join(DASHBOARD_STORAGE_DIR, files[0])
        return send_file(filepath, mimetype='text/html')

    except Exception as e:
        logger.error(f"Error serving preview: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'PREVIEW_ERROR',
            'message': str(e)
        }), 500

# ============================================================================
# DOWNLOAD ENDPOINT
# ============================================================================

@app.route('/download/<dashboard_id>', methods=['GET'])
@smart_auth
def download_dashboard(dashboard_id: str):
    """
    Download dashboard in specified format.

    Path Parameters:
        dashboard_id: Dashboard UUID

    Query Parameters:
        format: Export format (html, pdf, excel) - default: html

    Returns:
        File in requested format for download
    """
    try:
        # Get requested format
        export_format = request.args.get('format', 'html').lower()

        # Find file
        files = [f for f in os.listdir(DASHBOARD_STORAGE_DIR) if dashboard_id in f]

        if not files:
            return jsonify({
                'success': False,
                'error': 'NOT_FOUND',
                'message': 'Dashboard not found or expired'
            }), 404

        filepath = os.path.join(DASHBOARD_STORAGE_DIR, files[0])
        base_filename = os.path.splitext(files[0])[0]

        # HTML format - direct download
        if export_format == 'html':
            return send_file(
                filepath,
                mimetype='text/html',
                as_attachment=True,
                download_name=files[0]
            )

        # Read HTML content for conversion
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()

        export_service = get_export_service()

        # PDF format
        if export_format == 'pdf':
            success, pdf_bytes, error = export_service.html_to_pdf(html_content)
            if success:
                from io import BytesIO
                return send_file(
                    BytesIO(pdf_bytes),
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f"{base_filename}.pdf"
                )
            else:
                return jsonify({
                    'success': False,
                    'error': 'PDF_GENERATION_ERROR',
                    'message': error
                }), 500

        # Excel format
        elif export_format == 'excel':
            success, excel_bytes, error = export_service.html_to_excel(html_content, title=base_filename)
            if success:
                from io import BytesIO
                return send_file(
                    BytesIO(excel_bytes),
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=f"{base_filename}.xlsx"
                )
            else:
                return jsonify({
                    'success': False,
                    'error': 'EXCEL_GENERATION_ERROR',
                    'message': error
                }), 500

        else:
            return jsonify({
                'success': False,
                'error': 'INVALID_FORMAT',
                'message': f"Unsupported format: {export_format}. Supported: html, pdf, excel"
            }), 400

    except Exception as e:
        logger.error(f"Error serving download: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'DOWNLOAD_ERROR',
            'message': str(e)
        }), 500


@app.route('/api/v1/export/formats', methods=['GET'])
def get_export_formats():
    """
    Get available export formats.

    Returns:
        List of available export formats and their status
    """
    export_service = get_export_service()
    formats = export_service.get_available_formats()

    return jsonify({
        'success': True,
        'formats': [
            {'id': 'html', 'name': 'HTML', 'extension': '.html', 'available': formats['html']},
            {'id': 'pdf', 'name': 'PDF', 'extension': '.pdf', 'available': formats['pdf']},
            {'id': 'excel', 'name': 'Excel', 'extension': '.xlsx', 'available': formats['excel']},
        ]
    })


# ============================================================================
# HELPER FUNCTIONS FOR CHATBOT
# ============================================================================

def get_allowed_tables_for_dept(dept_id: str) -> List[str]:
    """
    Get list of allowed table names for a specific department from departments_config.py.

    Args:
        dept_id: Department identifier (e.g., 'env', 'furnace', 'qc')

    Returns:
        List of table names that belong to this department
    """
    dept = DEPARTMENTS.get(dept_id.lower())
    if not dept:
        logger.warning(f"Unknown department: {dept_id}")
        return []
    return dept.table_names


def get_relevant_schema(dept_id: str) -> str:
    """
    Get database schema for relevant tables based on department.
    Uses department configuration from departments_config.py.
    """
    dept = DEPARTMENTS.get(dept_id.lower())
    if not dept:
        return f"[No schema available for department: {dept_id}]"

    schema_parts = []

    # For departments with normalized tables (furnace, qc, etc.)
    if dept.has_normalized_tables:
        logger.info(f"Loading schema for {dept_id} normalized tables...")
        for table_def in dept.tables:
            result = mcp_server.inspect(table_def.name, database="balcorpdb")

            if result["success"] and result["schema"]:
                schema = result["schema"]
                schema_parts.append(f"\nTable: {schema['table']}")
                schema_parts.append(f"Database: {schema['database']}")
                schema_parts.append(f"Row Count: {schema['row_count']}")
                schema_parts.append("Columns:")
                for col in schema["columns"]:
                    key_info = f" [{col['key']}]" if col['key'] else ""
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    schema_parts.append(f"  - {col['name']}: {col['type']} {nullable}{key_info}")
                schema_parts.append("")

    # For EAV departments (env, hr, etc.)
    elif dept.has_eav_tables:
        logger.info(f"Loading schema for {dept_id} EAV tables...")
        for category in dept.kpi_categories:
            # Construct table name based on department
            table_name = f"kpi_{dept_id}_{category.lower().replace(' ', '_')}_data"

            result = mcp_server.inspect(table_name, database="balcorpdb")

            if result["success"] and result["schema"]:
                schema = result["schema"]
                schema_parts.append(f"\nTable: {schema['table']}")
                schema_parts.append(f"Database: {schema['database']}")
                schema_parts.append(f"Row Count: {schema['row_count']}")
                schema_parts.append("Columns:")
                for col in schema["columns"]:
                    key_info = f" [{col['key']}]" if col['key'] else ""
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    schema_parts.append(f"  - {col['name']}: {col['type']} {nullable}{key_info}")
                schema_parts.append("")

    return "\n".join(schema_parts) if schema_parts else f"[No schema information available for {dept_id}]"


def validate_table_access(table_name: str, dept_id: str) -> tuple[bool, str]:
    """
    Validate if a table can be accessed by a specific department.

    Args:
        table_name: Name of the table being accessed
        dept_id: Department identifier

    Returns:
        Tuple of (is_allowed, error_message)
    """
    allowed_tables = get_allowed_tables_for_dept(dept_id)
    if not allowed_tables:
        return False, f"Unknown department: {dept_id}"

    if table_name.lower() not in [t.lower() for t in allowed_tables]:
        return False, f"Access denied: Table '{table_name}' is not accessible for department '{dept_id}'. Allowed tables: {', '.join(allowed_tables)}"

    return True, ""


def extract_tables_from_sql(sql: str) -> List[str]:
    """
    Extract table names from a SQL query.

    Args:
        sql: SQL query string

    Returns:
        List of table names found in the query
    """
    import re
    # Match table names after FROM, JOIN, INTO, UPDATE, and in subqueries
    # This handles common patterns like: FROM table, JOIN table, FROM schema.table
    patterns = [
        r'\bFROM\s+([`"\[]?[\w.]+[`"\]]?)',
        r'\bJOIN\s+([`"\[]?[\w.]+[`"\]]?)',
        r'\bINTO\s+([`"\[]?[\w.]+[`"\]]?)',
        r'\bUPDATE\s+([`"\[]?[\w.]+[`"\]]?)',
    ]

    tables = []
    sql_upper = sql.upper()

    for pattern in patterns:
        matches = re.findall(pattern, sql, re.IGNORECASE)
        for match in matches:
            # Remove quotes/brackets and get the table name (handle schema.table format)
            clean_name = match.strip('`"[]')
            if '.' in clean_name:
                clean_name = clean_name.split('.')[-1]  # Get table name after schema
            tables.append(clean_name)

    return list(set(tables))  # Remove duplicates


def validate_sql_tables(sql: str, dept_id: str) -> tuple[bool, str]:
    """
    Validate that all tables in a SQL query are accessible by the department.

    Args:
        sql: SQL query string
        dept_id: Department identifier

    Returns:
        Tuple of (is_allowed, error_message)
    """
    tables = extract_tables_from_sql(sql)
    allowed_tables = get_allowed_tables_for_dept(dept_id)
    allowed_tables_lower = [t.lower() for t in allowed_tables]

    logger.info(f"[TABLE VALIDATION] SQL: {sql[:100]}...")
    logger.info(f"[TABLE VALIDATION] Extracted tables: {tables}")
    logger.info(f"[TABLE VALIDATION] Allowed tables for '{dept_id}': {allowed_tables}")

    unauthorized_tables = []
    for table in tables:
        if table.lower() not in allowed_tables_lower:
            unauthorized_tables.append(table)

    if unauthorized_tables:
        logger.warning(f"[TABLE VALIDATION] BLOCKED! Unauthorized tables: {unauthorized_tables}")
        return False, f"Access denied: Query contains unauthorized table(s) for department '{dept_id}': {', '.join(unauthorized_tables)}. Allowed tables: {', '.join(allowed_tables)}"

    logger.info(f"[TABLE VALIDATION] ALLOWED - all tables valid for department '{dept_id}'")
    return True, ""


def execute_tool_call(tool_name: str, parameters: Dict[str, Any], dept_id: str = None) -> Dict[str, Any]:
    """
    Execute MCP tool and return result.

    Args:
        tool_name: Name of the tool to execute
        parameters: Tool parameters
        dept_id: Department ID for access control (optional, but recommended)

    Returns:
        Tool execution result
    """
    try:
        if tool_name == "discover":
            return mcp_server.discover()

        elif tool_name == "search_tables":
            search_term = parameters.get("search_term", "")
            database = parameters.get("database")
            result = mcp_server.search_tables(search_term, database)

            # Filter results to only show tables accessible by the department
            if dept_id and result.get("success") and result.get("tables"):
                allowed_tables = get_allowed_tables_for_dept(dept_id)
                allowed_tables_lower = [t.lower() for t in allowed_tables]
                result["tables"] = [t for t in result["tables"] if t.lower() in allowed_tables_lower]

            return result

        elif tool_name == "inspect":
            table = parameters.get("table")
            database = parameters.get("database")
            if not table:
                return {"success": False, "error": "Missing required parameter: table"}

            # Validate table access for department
            if dept_id:
                is_allowed, error_msg = validate_table_access(table, dept_id)
                if not is_allowed:
                    return {"success": False, "error": error_msg}

            return mcp_server.inspect(table, database)

        elif tool_name == "query":
            sql = parameters.get("sql")
            database = parameters.get("database")
            if not sql:
                return {"success": False, "error": "Missing required parameter: sql"}

            # Validate all tables in the query are accessible by the department
            if dept_id:
                is_allowed, error_msg = validate_sql_tables(sql, dept_id)
                if not is_allowed:
                    return {"success": False, "error": error_msg}

            return mcp_server.query(sql, database)

        elif tool_name == "sample":
            table = parameters.get("table")
            database = parameters.get("database")
            limit = parameters.get("limit", 10)
            if not table:
                return {"success": False, "error": "Missing required parameter: table"}

            # Validate table access for department
            if dept_id:
                is_allowed, error_msg = validate_table_access(table, dept_id)
                if not is_allowed:
                    return {"success": False, "error": error_msg}

            return mcp_server.sample(table, database, limit)

        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


# ============================================================================
# AI CHAT FLAGGING LOGIC
# ============================================================================

FORBIDDEN_TABLES = [
    'emp_data', 'furnace_tapping_data', 'sd_contract', 'users', 'app_users', 'admin'
]

SUSPICIOUS_KEYWORDS = [
    'delete', 'update', 'insert', 'drop', 'truncate', 'alter', 'grant', 'revoke',
    'password', 'salary', 'credentials', 'hash', 'ssn', 'user_id', 'employee_id'
]

def check_suspicious_chat(message: str) -> tuple[bool, str]:
    """
    Analyzes a chat message for suspicious keywords or forbidden table access.

    Returns:
        tuple[bool, str]: (is_suspicious, reason_message)
    """
    if not message:
        return False, "Empty message."

    msg_lower = message.lower()

    # 1. Check for forbidden table names
    for table in FORBIDDEN_TABLES:
        if table in msg_lower:
            reason = f"Attempted to query forbidden table: {table}"
            logger.warning(f"Suspicious chat detected: {reason} | Message: {message}")
            return True, reason

    # 2. Check for suspicious SQL keywords
    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword in msg_lower:
            reason = f"Message contained suspicious keyword: {keyword}"
            logger.warning(f"Suspicious chat detected: {reason} | Message: {message}")
            return True, reason

    # 3. Check for unauthorized tool call attempts (simple)
    if "tool_call" in msg_lower or "mcp.query" in msg_lower:
        reason = "Message contained suspicious tool call syntax."
        logger.warning(f"Suspicious chat detected: {reason} | Message: {message}")
        return True, reason

    return False, "Chat message appears safe."


# ============================================================================
# VISUALIZATION PARSER FOR CHATBOT
# ============================================================================

def parse_visualizations(response_text: str) -> tuple[str, list]:
    """
    Parse visualization blocks from Claude's response.

    Returns:
        tuple[str, list]: (cleaned_text, list_of_visualizations)
    """
    import re

    visualizations = []
    cleaned_text = response_text

    # Find all <visualization>...</visualization> blocks
    pattern = r'<visualization>\s*([\s\S]*?)\s*</visualization>'
    matches = re.findall(pattern, response_text, re.IGNORECASE)

    for match in matches:
        try:
            # Remove comments (// style) that Claude might include
            cleaned_json = re.sub(r'//.*$', '', match, flags=re.MULTILINE)
            # Parse JSON from the match
            viz_data = json.loads(cleaned_json)
            visualizations.append(viz_data)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse visualization JSON: {e}")
            logger.debug(f"Raw visualization block: {match[:200]}...")

    # Remove visualization blocks from text for cleaner display
    cleaned_text = re.sub(pattern, '', response_text, flags=re.IGNORECASE)
    # Clean up extra whitespace
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    cleaned_text = cleaned_text.strip()

    return cleaned_text, visualizations


# ============================================================================
# CHATBOT ENDPOINT (OpenAI API - ACTIVE)
# ============================================================================
# Migration Note (2026-01-15): Migrated from Local LLM to OpenAI API
# The chatbot now uses OpenAI API directly (gpt-4o model)
# Tool calling format uses OpenAI 'functions' format
# ============================================================================
# PREVIOUS: Local LLM (Ollama/Qwen) - Commented out for rollback if needed

@app.route('/api/v1/chat', methods=['POST'])
@smart_auth
def chat():
    """
    AI Chatbot powered by OpenAI API with MCP database tools.
    Now includes authentication, AI flagging, and activity logging.

    Migration Note: Uses OpenAI API (gpt-4o model).
    """
    logger.info("="*70)
    logger.info("CHAT ENDPOINT CALLED (OPENAI API WITH MCP TOOLS)")

# Get user info from the auth decorator
    # =============================================================
    #        comment below and uncomment below below
    # =============================================================
    user = type('obj', (object,), {'user_id': 'demo_user', 'full_name': 'Demo User'})()
    #user = g.user
    ip_address = request.remote_addr

    # ========================================================================
    # LEGACY CODE - PRESERVED FOR ROLLBACK
    # ========================================================================
    # if not claude_client:
    #     return jsonify({
    #         'success': False,
    #         'error': 'CHATBOT_DISABLED',
    #         'message': 'Claude API is not configured'
    #     }), 503

    # ========================================================================
    # OPENAI API CHECK (ACTIVE)
    # ========================================================================
    if not llm_client:
        return jsonify({
            'success': False,
            'error': 'CHATBOT_DISABLED',
            'message': 'OpenAI API is not configured. Set OPENAI_API_KEY in .env'
        }), 503

    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        dept_id = data.get('department', 'env')
        conversation_history = data.get('conversation_history', [])  # Accept chat history from frontend

        if not user_message:
            return jsonify({
                'success': False,
                'error': 'INVALID_REQUEST',
                'message': 'message field is required'
            }), 400

        logger.info(f"Chat request: user={user.user_id}, dept={dept_id}, message={user_message[:100]}...")

        # --- STEP 1: AI FLAGGING ---
        is_suspicious, flag_reason = check_suspicious_chat(user_message)

        # --- STEP 2: LOG THE CHAT QUERY ---
        log_activity(
            employee_id=user.user_id,
            action_type="CHATBOT",
            details=f"Query: \"{user_message}\" | Reason: \"{flag_reason}\"",
            flagged=is_suspicious,
            ip_address=ip_address
        )

        # Get relevant schema
        relevant_schema = get_relevant_schema(dept_id)

        # Get department name for the system prompt
        dept_config = get_department(dept_id)
        dept_name = dept_config.name if dept_config else dept_id.upper()

        # Get today's date for the system prompt
        today_date = datetime.now().strftime('%Y-%m-%d')

        # Load system prompt from file
        try:
            with open('systemprompt.txt', 'r') as f:
                system_prompt = f.read()
            system_prompt = system_prompt.replace("{{RELEVANT_SCHEMA}}", relevant_schema)
            system_prompt = system_prompt.replace("{{USER_PROMPT}}", user_message)
            system_prompt = system_prompt.replace("{{TODAY_DATE}}", today_date)
            system_prompt = system_prompt.replace("{{DEPARTMENT_NAME}}", dept_name)
        except FileNotFoundError:
            system_prompt = f"You are a database assistant for {dept_name}. Today's date is {today_date}. Schema:\n{relevant_schema}"

        # ====================================================================
        # LEGACY CODE - CLAUDE API TOOLS FORMAT (PRESERVED FOR ROLLBACK)
        # ====================================================================
        # tools = [
        #     {
        #         "name": "query",
        #         "description": "Execute a read-only SQL query (SELECT only)",
        #         "input_schema": {
        #             "type": "object",
        #             "properties": {
        #                 "sql": {"type": "string", "description": "SQL query to execute"},
        #                 "database": {"type": "string", "description": "Database name (optional)"}
        #             },
        #             "required": ["sql"]
        #         }
        #     },
        #     {
        #         "name": "inspect",
        #         "description": "Get schema for a table",
        #         "input_schema": {
        #             "type": "object",
        #             "properties": {
        #                 "table": {"type": "string", "description": "Table name"},
        #                 "database": {"type": "string", "description": "Database name (optional)"}
        #             },
        #             "required": ["table"]
        #         }
        #     }
        # ]
        #
        # # Initial API call (Claude format)
        # response = claude_client.messages.create(
        #     model=ClaudeConfig.CLAUDE_MODEL,
        #     max_tokens=ClaudeConfig.MAX_TOKENS,
        #     temperature=ClaudeConfig.TEMPERATURE,
        #     system=system_prompt,
        #     tools=tools,
        #     messages=[{"role": "user", "content": user_message}]
        # )
        #
        # # Handle tool use loop (Claude format)
        # ... (Claude-specific tool loop code)

        # ====================================================================
        # NEW CODE - OPENAI-COMPATIBLE API FORMAT (LOCAL LLM)
        # ====================================================================
        # Define tools in OpenAI format
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "query",
                    "description": "Execute a read-only SQL query (SELECT only)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql": {"type": "string", "description": "SQL query to execute"},
                            "database": {"type": "string", "description": "Database name (optional)"}
                        },
                        "required": ["sql"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "inspect",
                    "description": "Get schema for a table",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table": {"type": "string", "description": "Table name"},
                            "database": {"type": "string", "description": "Database name (optional)"}
                        },
                        "required": ["table"]
                    }
                }
            }
        ]

        # Initial API call (OpenAI format)
        # Build messages with conversation history for context
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history (previous messages for context)
        # Frontend should send: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
        if conversation_history:
            for msg in conversation_history:
                # Only include user and assistant messages (not system or tool messages)
                if msg.get('role') in ['user', 'assistant'] and msg.get('content'):
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        # Get OpenAI config from environment variables
        chat_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        chat_max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "4096"))
        chat_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))

        response = llm_client.chat.completions.create(
            model=chat_model,
            max_tokens=chat_max_tokens,
            temperature=chat_temperature,
            tools=tools,
            messages=messages
        )

        # Handle tool use loop (OpenAI format)
        tool_calls_made = []

        while response.choices[0].finish_reason == "tool_calls" or (
            response.choices[0].message.tool_calls and len(response.choices[0].message.tool_calls) > 0
        ):
            assistant_message = response.choices[0].message
            messages.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in assistant_message.tool_calls
                ] if assistant_message.tool_calls else None
            })

            # Process each tool call
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_input = json.loads(tool_call.function.arguments)

                logger.info(f"Tool: {tool_name}, Input: {tool_input}")

                # Execute tool
                tool_result = execute_tool_call(tool_name, tool_input, dept_id)
                logger.info(f"Result: {tool_result}")

                tool_calls_made.append({
                    "tool": tool_name,
                    "input": tool_input,
                    "result": tool_result
                })

                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result)
                })

            # Continue conversation
            response = llm_client.chat.completions.create(
                model=chat_model,
                max_tokens=chat_max_tokens,
                temperature=chat_temperature,
                tools=tools,
                messages=messages
            )

        # Extract final response (OpenAI format)
        final_response = response.choices[0].message.content or ""

        logger.info(f"✅ Response generated (length: {len(final_response)})")

        # Parse visualization data from response
        cleaned_response, visualizations = parse_visualizations(final_response)

        logger.info(f"✅ Parsed {len(visualizations)} visualization(s)")

        return jsonify({
            'success': True,
            'response': cleaned_response,
            'visualizations': visualizations if visualizations else None,
            'tool_calls': tool_calls_made if tool_calls_made else None,
            'department': dept_id,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ CHAT ERROR: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'CHAT_ERROR',
            'message': str(e)
        }), 500





# ============================================================================
# ADMIN LOGIN ENDPOINT
# ============================================================================

@app.route('/api/v1/login', methods=['POST'])
def login():
    """
    Admin login endpoint.
    Accepts employee_id and password, returns a JWT token.
    """
    ip_address = request.remote_addr
    employee_id = None
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        password = data.get('password')

        if not employee_id or not password:
            return jsonify({
                "success": False,
                "error": "BAD_REQUEST",
                "message": "Employee ID and password are required"
            }), 400

        # Direct DB connection
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(
                host=DatabaseConfig.MYSQL_HOST,
                port=DatabaseConfig.MYSQL_PORT,
                user=DatabaseConfig.MYSQL_USER,
                password=DatabaseConfig.MYSQL_PASSWORD,
                database=DatabaseConfig.MYSQL_DATABASE
            )
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM app_users WHERE employee_id = %s", (employee_id,))
            user = cursor.fetchone()

        except mysql.connector.Error as err:
            logger.error(f"Login database error: {err}")
            return jsonify({"success": False, "error": "DB_ERROR", "message": str(err)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        # Validate user and password
        if not user or not check_password_hash(user['hashed_password'], password):
            logger.warning(f"Failed login attempt for {employee_id}")
            log_activity(
                employee_id=employee_id or "unknown",
                action_type="LOGIN_FAIL",
                details="Invalid credentials provided.",
                ip_address=ip_address
            )
            return jsonify({
                "success": False,
                "error": "UNAUTHORIZED",
                "message": "Invalid credentials"
            }), 401

        # ===== FIXED JWT PAYLOAD (required for validator) =====
        now_ts = int(datetime.utcnow().timestamp())
        expiry_seconds = int(JWTConfig.JWT_TOKEN_EXPIRY_HOURS * 3600)

        department = (
            user.get("department")
            if isinstance(user, dict) and user.get("department")
            else ("admin" if user.get("role") == "admin" else "env")
        )

        permissions = (
            {"admin": True}
            if user.get("role") == "admin"
            else (user.get("permissions") if user.get("permissions") else {})
        )

        payload = {
            "user_id": user["employee_id"],
            "username": user["employee_id"],       # REQUIRED CLAIM
            "full_name": user["full_name"],
            "role": user["role"],
            "department": department,              # REQUIRED CLAIM
            "permissions": permissions,            # REQUIRED CLAIM
            "exp": now_ts + expiry_seconds,
            "iat": now_ts
        }
        # =====================================================

        token = jwt.encode(
            payload,
            JWTConfig.JWT_SECRET_KEY,
            algorithm=JWTConfig.JWT_ALGORITHM
        )

        logger.info(f"Successful login for {user['full_name']} (Role: {user['role']})")

        # Log success
        log_activity(
            employee_id=user["employee_id"],
            action_type="LOGIN_SUCCESS",
            details=f"User {user['full_name']} logged in with role {user['role']}.",
            ip_address=ip_address
        )

        return jsonify({
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": {
                "full_name": user["full_name"],
                "employee_id": user["employee_id"],
                "role": user["role"]
            }
        }), 200

    except Exception as e:
        logger.error(f"Login endpoint error: {e}", exc_info=True)
        log_activity(
            employee_id=employee_id or "unknown",
            action_type="LOGIN_FAIL",
            details=f"Internal server error during login: {str(e)}",
            ip_address=ip_address
        )
        return jsonify({
            "success": False,
            "error": "INTERNAL_ERROR",
            "message": str(e)
        }), 500


# ============================================================================
# ADMIN LOGS ENDPOINT
# ============================================================================

@app.route('/api/logs', methods=['GET'])
@smart_auth
@require_admin  # Secure this endpoint
def get_activity_logs():
    """
    Fetches all activity logs for the admin panel.
    Protected by @require_auth and @require_admin.
    """
    logger.info(f"Admin log request from {g.user.full_name}")
    conn = None
    cursor = None

    try:
        conn = mysql.connector.connect(
            host=DatabaseConfig.MYSQL_HOST,
            port=DatabaseConfig.MYSQL_PORT,
            user=DatabaseConfig.MYSQL_USER,
            password=DatabaseConfig.MYSQL_PASSWORD,
            database=DatabaseConfig.MYSQL_DATABASE
        )
        cursor = conn.cursor(dictionary=True)

        # Join with app_users to get the user's full name
        query = """
        SELECT
            log.log_id,
            log.timestamp,
            log.employee_id,
            COALESCE(usr.full_name, 'Unknown User') AS full_name,
            log.action_type,
            log.details,
            log.flagged_suspicious,
            log.generated_dashboard_path,
            log.ip_address
        FROM app_activity_log AS log
        LEFT JOIN app_users AS usr ON log.employee_id = usr.employee_id
        ORDER BY log.timestamp DESC
        LIMIT 500
        """

        cursor.execute(query)
        logs = cursor.fetchall()

        # Convert datetime objects to ISO format strings for JSON
        for log in logs:
            if isinstance(log['timestamp'], datetime):
                log['timestamp'] = log['timestamp'].isoformat()

        return jsonify({
            "success": True,
            "logs": logs
        })

    except mysql.connector.Error as err:
        logger.error(f"Admin log retrieval error: {err}")
        return jsonify({"success": False, "error": "DB_ERROR", "message": str(err)}), 500
    except Exception as e:
        logger.error(f"Admin log endpoint error: {e}", exc_info=True)
        return jsonify({"success": False, "error": "INTERNAL_ERROR", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'NOT_FOUND',
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'INTERNAL_ERROR',
        'message': 'An unexpected error occurred'
    }), 500


def list_routes():
    """List all registered routes for debugging"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': ','.join(rule.methods),
            'path': str(rule)
        })
    return routes

# Add debug route
@app.route('/debug/routes', methods=['GET'])
def debug_routes():
    """Debug endpoint to see all registered routes"""
    return jsonify({
        'success': True,
        'routes': list_routes()
    })


# ============================================================================
# STARTUP & MAIN
# ============================================================================

if __name__ == '__main__':
    try:
        print("=" * 70)
        print("🚀 BALASORE ALLOYS DASHBOARD SYSTEM")
        print("=" * 70)
        print(f"📊 Database: {config.MYSQL_HOST}/{config.MYSQL_DATABASE}")
        print(f"🌐 API Server: {config.API_HOST}:{config.API_PORT}")
        print(f"🔐 JWT Auth: {'Enabled' if jwt_validator else 'Disabled'}")
        print(f"🤖 Claude API: {'Configured' if claude_client else 'Not Configured'}")
        print(f"📁 Departments: {len(get_enabled_departments())} enabled")
        print("=" * 70)
        print("\n✅ Server starting...")
        print(f"\n📋 API Endpoints available at: http://{config.API_HOST}:{config.API_PORT}")
    except UnicodeEncodeError:
        # Fallback for Windows console
        print("=" * 70)
        print("BALASORE ALLOYS DASHBOARD SYSTEM")
        print("=" * 70)
        print(f"Database: {config.MYSQL_HOST}/{config.MYSQL_DATABASE}")
        print(f"API Server: {config.API_HOST}:{config.API_PORT}")
        print(f"JWT Auth: {'Enabled' if jwt_validator else 'Disabled'}")
        print(f"Claude API: {'Configured' if claude_client else 'Not Configured'}")
        print(f"Departments: {len(get_enabled_departments())} enabled")
        print("=" * 70)
        print("\nServer starting...")
        print(f"\nAPI Endpoints available at: http://{config.API_HOST}:{config.API_PORT}")

    print("   - GET  /health")
    print("   - GET  /api/v1/departments")
    print("   - GET  /api/v1/dashboard/<dept_id>?date=YYYY-MM-DD")
    print("   - GET  /preview/<dashboard_id>")
    print("   - GET  /download/<dashboard_id>")
    print("   - POST /api/v1/chat  {message, department}")
    print("\n")

    app.run(
        host=config.API_HOST,
        port=config.API_PORT,
        debug=config.DEBUG
    )