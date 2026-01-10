"""
config.py
=========
Central configuration file for the Balasore Alloys Dashboard System.

This file contains all configuration settings including:
- Database connection settings
- JWT authentication configuration
- CORS settings for frontend integration
- File storage paths
- API settings
- Claude API configuration (replacing Gemini)

IMPORTANT: Sensitive values should be stored in .env file!
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

class DatabaseConfig:
    """MySQL Database connection settings"""

    # Primary database connection
    MYSQL_HOST = os.getenv("MYSQL_HOST", "80.9.2.78")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER", "your_username")  # UPDATE IN .env
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "your_password")  # UPDATE IN .env
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "balcorpdb")

    # Connection pool settings
    MYSQL_POOL_SIZE = int(os.getenv("MYSQL_POOL_SIZE", 5))
    MYSQL_MAX_OVERFLOW = int(os.getenv("MYSQL_MAX_OVERFLOW", 10))
    MYSQL_POOL_TIMEOUT = int(os.getenv("MYSQL_POOL_TIMEOUT", 30))

    # Read-only mode (contractual requirement)
    READ_ONLY = True

    # Main transaction table for all departments
    MAIN_TABLE = "env_kpi_transaction"

    @classmethod
    def get_connection_string(cls) -> str:
        """Returns MySQL connection string for SQLAlchemy (if needed)"""
        return (
            f"mysql+mysqlconnector://{cls.MYSQL_USER}:{cls.MYSQL_PASSWORD}"
            f"@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DATABASE}"
        )

    @classmethod
    def get_connection_params(cls) -> Dict[str, Any]:
        """Returns connection parameters as dictionary for mysql.connector"""
        return {
            "host": cls.MYSQL_HOST,
            "port": cls.MYSQL_PORT,
            "user": cls.MYSQL_USER,
            "password": cls.MYSQL_PASSWORD,
            "database": cls.MYSQL_DATABASE,
            "charset": "utf8mb4",
            "use_unicode": True,
            "autocommit": False  # Read-only, but keep explicit
        }


# ============================================================================
# JWT AUTHENTICATION CONFIGURATION
# ============================================================================

class JWTConfig:
    """JWT token validation settings (shared with Node.js team)"""

    # CRITICAL: This secret MUST match the Node.js backend's JWT secret
    # Get this value from the Node.js team and store in .env file
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "PLACEHOLDER_CHANGE_THIS")

    # JWT algorithm (should match Node.js setup)
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

    # Token expiration settings
    JWT_TOKEN_EXPIRY_HOURS = int(os.getenv("JWT_TOKEN_EXPIRY_HOURS", 8))

    # Required claims in JWT token
    REQUIRED_CLAIMS = ["user_id", "username", "department", "permissions"]

    # Token prefix in Authorization header
    TOKEN_PREFIX = "Bearer"

    @classmethod
    def is_placeholder(cls) -> bool:
        """Check if JWT secret is still placeholder"""
        return cls.JWT_SECRET_KEY == "PLACEHOLDER_CHANGE_THIS"


# ============================================================================
# CORS CONFIGURATION (Frontend Integration)
# ============================================================================

class CORSConfig:
    """CORS settings for React frontend integration"""

    # Allowed origins (React app URLs)
    # UPDATE these with actual frontend URLs from React team
    ALLOWED_ORIGINS = [
        "http://80.9.2.78:5173",           # Default React dev server
        "http://localhost:3000",           # React dev server
        "http://localhost:5173",           # Vite dev server (alternative)
        "http://192.168.1.100:3000",      # PLACEHOLDER - Update with actual IP
        "http://192.168.1.100:80",        # PLACEHOLDER - Update with actual IP
        # Add production URLs here when available
    ]

    # CORS settings
    SUPPORTS_CREDENTIALS = True
    ALLOW_HEADERS = ["Content-Type", "Authorization", "X-Requested-With"]
    ALLOW_METHODS = ["GET", "POST", "OPTIONS"]
    MAX_AGE = 3600  # Preflight cache duration (1 hour)


# ============================================================================
# FLASK APPLICATION CONFIGURATION
# ============================================================================

class FlaskConfig:
    """Flask application settings"""

    # Server settings
    HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    PORT = int(os.getenv("FLASK_PORT", 5100))
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    # Secret key for Flask sessions
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", os.urandom(32).hex())

    # Request limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max request size

    # JSON settings
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True


# ============================================================================
# FILE STORAGE CONFIGURATION
# ============================================================================

class StorageConfig:
    """File storage paths and settings"""

    # Base directory for generated files
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Generated dashboards directory
    DASHBOARDS_DIR = os.path.join(BASE_DIR, "generated_dashboards")

    # Templates directory
    TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

    # Logs directory
    LOGS_DIR = os.path.join(BASE_DIR, "logs")

    # Dashboard file retention (hours)
    DASHBOARD_RETENTION_HOURS = 24

    # Maximum dashboard files to keep
    MAX_DASHBOARD_FILES = 1000

    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        for directory in [cls.DASHBOARDS_DIR, cls.TEMPLATES_DIR, cls.LOGS_DIR]:
            os.makedirs(directory, exist_ok=True)


# ============================================================================
# API CONFIGURATION
# ============================================================================

class APIConfig:
    """API endpoint settings"""

    # API version prefix
    API_VERSION = "v1"
    API_PREFIX = f"/api/{API_VERSION}"

    # Pagination defaults
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 1000

    # Rate limiting (future implementation)
    RATE_LIMIT_ENABLED = False
    RATE_LIMIT_PER_MINUTE = 100


# ============================================================================
# CLAUDE API CONFIGURATION (LEGACY - PRESERVED FOR ROLLBACK)
# ============================================================================
# DEPRECATED: Replaced with Local LLM on 2025-12-16
# To rollback: Set LOCAL_LLM_ENABLED=false in .env and uncomment CLAUDE_API_KEY

class ClaudeConfig:
    """Claude API settings for AI-powered features (LEGACY)"""

    # Claude API credentials (PRESERVED FOR ROLLBACK)
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "PLACEHOLDER_CHANGE_THIS")

    # Claude model to use
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

    # API endpoint
    CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

    # Request settings
    MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", 4096))
    TEMPERATURE = float(os.getenv("CLAUDE_TEMPERATURE", 0.7))

    # Timeout settings
    REQUEST_TIMEOUT = int(os.getenv("CLAUDE_REQUEST_TIMEOUT", 60))

    @classmethod
    def is_configured(cls) -> bool:
        """Check if Claude API is properly configured"""
        return cls.CLAUDE_API_KEY != "PLACEHOLDER_CHANGE_THIS"


# ============================================================================
# LOCAL LLM CONFIGURATION (ACTIVE)
# ============================================================================
# DigitalOcean H200 GPU - Qwen 2.5:72B via Ollama
# SSH Tunnel Required: ssh -L 11435:localhost:11434 pramit@107.170.2.49
# Migration Date: 2025-12-16

class LocalLLMConfig:
    """Local LLM settings for AI-powered features (OpenAI-compatible)"""

    # Local LLM enabled flag (SET TO FALSE TO USE CLAUDE API)
    ENABLED = os.getenv("LOCAL_LLM_ENABLED", "true").lower() == "true"

    # Local LLM API credentials (default "ollama" for local)
    API_KEY = os.getenv("LOCAL_LLM_API_KEY", "ollama")

    # Local LLM base URL (requires SSH tunnel on port 11435)
    BASE_URL = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11435/v1")

    # Local LLM model to use
    MODEL = os.getenv("LOCAL_LLM_MODEL", "qwen2.5:72b-instruct-q4_K_M")

    # Request settings
    MAX_TOKENS = int(os.getenv("LOCAL_LLM_MAX_TOKENS", 4096))
    TEMPERATURE = float(os.getenv("LOCAL_LLM_TEMPERATURE", 0.7))

    # Timeout settings
    REQUEST_TIMEOUT = int(os.getenv("LOCAL_LLM_REQUEST_TIMEOUT", 120))

    # SSH tunnel info (for documentation/logging)
    SSH_TUNNEL_COMMAND = "ssh -L 11435:localhost:11434 pramit@107.170.2.49"

    @classmethod
    def is_configured(cls) -> bool:
        """Check if Local LLM is enabled and configured"""
        return cls.ENABLED and cls.BASE_URL != ""

    @classmethod
    def get_config_info(cls) -> dict:
        """Get configuration info for logging"""
        return {
            "enabled": cls.ENABLED,
            "base_url": cls.BASE_URL,
            "model": cls.MODEL,
            "max_tokens": cls.MAX_TOKENS,
            "temperature": cls.TEMPERATURE,
            "ssh_tunnel": cls.SSH_TUNNEL_COMMAND
        }


# ============================================================================
# DEPARTMENT CONFIGURATION STRUCTURE
# ============================================================================

class DepartmentConfig:
    """Base structure for department configurations

    Each department will define:
    - ID: Unique identifier
    - Name: Display name
    - Table: Which table/data to query (all use env_kpi_transaction)
    - Template: Which HTML template to use
    - Enabled: Whether department is active
    - KPI Categories: Which KPI_DESC values to query
    """

    # Department status
    ENABLED_DEPARTMENTS = []  # Will be populated from departments_config.py

    # Template naming convention
    TEMPLATE_PATTERN = "{dept_id}_dashboard.html"

    @classmethod
    def get_template_path(cls, dept_id: str) -> str:
        """Get template file path for a department"""
        template_name = cls.TEMPLATE_PATTERN.format(dept_id=dept_id)
        return os.path.join(StorageConfig.TEMPLATES_DIR, template_name)


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

class LoggingConfig:
    """Logging settings"""

    # Log level
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Log format
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Log file settings
    LOG_FILE = os.path.join(StorageConfig.LOGS_DIR, "dashboard_system.log")
    MAX_LOG_SIZE_MB = 10
    BACKUP_COUNT = 5


# ============================================================================
# ENVIRONMENT VALIDATION
# ============================================================================

def validate_configuration():
    """Validate critical configuration values and warn about placeholders"""
    warnings = []
    info = []

    # Check JWT secret
    if JWTConfig.is_placeholder():
        warnings.append("⚠️  JWT_SECRET_KEY is still placeholder. Update in .env file!")

    # ========================================================================
    # LEGACY CODE - Claude API check (PRESERVED FOR ROLLBACK)
    # ========================================================================
    # if not ClaudeConfig.is_configured():
    #     warnings.append("⚠️  CLAUDE_API_KEY is not configured. Update in .env file!")

    # ========================================================================
    # NEW CODE - Local LLM check (ACTIVE)
    # ========================================================================
    if LocalLLMConfig.ENABLED:
        if LocalLLMConfig.is_configured():
            info.append(f"✅ Local LLM enabled: {LocalLLMConfig.MODEL}")
            info.append(f"   Endpoint: {LocalLLMConfig.BASE_URL}")
            info.append(f"   SSH Tunnel: {LocalLLMConfig.SSH_TUNNEL_COMMAND}")
        else:
            warnings.append("⚠️  LOCAL_LLM_ENABLED=true but configuration is incomplete!")
    else:
        # Fallback to Claude API check if Local LLM is disabled
        if not ClaudeConfig.is_configured():
            warnings.append("⚠️  Neither Local LLM nor Claude API is configured!")

    # Check database credentials
    if DatabaseConfig.MYSQL_USER == "your_username":
        warnings.append("⚠️  MYSQL_USER is still default. Update in .env file!")

    if DatabaseConfig.MYSQL_PASSWORD == "your_password":
        warnings.append("⚠️  MYSQL_PASSWORD is still default. Update in .env file!")

    # Print info messages (handle Unicode properly for Windows console)
    if info:
        for msg in info:
            try:
                print(msg)
            except UnicodeEncodeError:
                # Fallback for Windows console that can't handle emojis
                print(msg.encode('ascii', 'replace').decode('ascii'))

    return warnings


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize():
    """Initialize configuration and create necessary directories"""
    # Create directories
    StorageConfig.ensure_directories()

    # Validate configuration
    warnings = validate_configuration()

    if warnings:
        print("\n" + "="*70)
        print("⚠️  CONFIGURATION WARNINGS:")
        print("="*70)
        for warning in warnings:
            print(f"  {warning}")
        print("="*70 + "\n")

    return len(warnings) == 0


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "DatabaseConfig",
    "JWTConfig",
    "CORSConfig",
    "FlaskConfig",
    "StorageConfig",
    "APIConfig",
    "ClaudeConfig",
    "LocalLLMConfig",  # NEW: Local LLM configuration
    "DepartmentConfig",
    "LoggingConfig",
    "initialize",
    "validate_configuration"
]


# Initialize on import
if __name__ != "__main__":
    # Only show warnings if not running as main script
    pass
else:
    # If run as script, validate and show all settings
    print("Configuration Validation")
    print("=" * 70)
    initialize()
    print("\n✅ Configuration loaded successfully!")
    print(f"📊 Database: {DatabaseConfig.MYSQL_HOST}/{DatabaseConfig.MYSQL_DATABASE}")
    print(f"🌐 Flask: {FlaskConfig.HOST}:{FlaskConfig.PORT}")
    print(f"📁 Templates: {StorageConfig.TEMPLATES_DIR}")
    # ========================================================================
    # LEGACY CODE - PRESERVED FOR ROLLBACK
    # ========================================================================
    # print(f"🤖 Claude Model: {ClaudeConfig.CLAUDE_MODEL}")

    # ========================================================================
    # NEW CODE - Local LLM info
    # ========================================================================
    if LocalLLMConfig.ENABLED:
        print(f"🤖 Local LLM Model: {LocalLLMConfig.MODEL}")
        print(f"   Endpoint: {LocalLLMConfig.BASE_URL}")
        print(f"   SSH Tunnel: {LocalLLMConfig.SSH_TUNNEL_COMMAND}")
    else:
        print(f"🤖 Claude Model: {ClaudeConfig.CLAUDE_MODEL} (Local LLM disabled)")

# ============================================================================
# CONVENIENCE OBJECT FOR IMPORTS
# ============================================================================

class ConfigObject:
    """Convenience object for accessing all config classes"""

    # Database configuration
    MYSQL_HOST = DatabaseConfig.MYSQL_HOST
    MYSQL_PORT = DatabaseConfig.MYSQL_PORT
    MYSQL_USER = DatabaseConfig.MYSQL_USER
    MYSQL_PASSWORD = DatabaseConfig.MYSQL_PASSWORD
    MYSQL_DATABASE = DatabaseConfig.MYSQL_DATABASE

    # API configuration
    API_PORT = FlaskConfig.PORT
    API_HOST = FlaskConfig.HOST
    DEBUG = FlaskConfig.DEBUG

    # CORS
    ALLOWED_ORIGINS = CORSConfig.ALLOWED_ORIGINS

    # JWT
    JWT_SECRET_KEY = JWTConfig.JWT_SECRET_KEY
    JWT_ALGORITHM = JWTConfig.JWT_ALGORITHM

    # ========================================================================
    # LEGACY - Claude API (PRESERVED FOR ROLLBACK)
    # ========================================================================
    CLAUDE_API_KEY = ClaudeConfig.CLAUDE_API_KEY
    CLAUDE_MODEL = ClaudeConfig.CLAUDE_MODEL

    # ========================================================================
    # NEW - Local LLM
    # ========================================================================
    LOCAL_LLM_ENABLED = LocalLLMConfig.ENABLED
    LOCAL_LLM_API_KEY = LocalLLMConfig.API_KEY
    LOCAL_LLM_BASE_URL = LocalLLMConfig.BASE_URL
    LOCAL_LLM_MODEL = LocalLLMConfig.MODEL

    # Storage
    DASHBOARDS_DIR = StorageConfig.DASHBOARDS_DIR
    TEMPLATES_DIR = StorageConfig.TEMPLATES_DIR

    @classmethod
    def get_all(cls):
        """Get dictionary of all config values"""
        return {
            'database': {
                'host': cls.MYSQL_HOST,
                'port': cls.MYSQL_PORT,
                'database': cls.MYSQL_DATABASE
            },
            'api': {
                'host': cls.API_HOST,
                'port': cls.API_PORT,
                'debug': cls.DEBUG
            }
        }

# Create global config instance
config = ConfigObject()