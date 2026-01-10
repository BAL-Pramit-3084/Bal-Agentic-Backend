"""
jwt_validator.py
================
JWT token validation for API authentication.

This module provides:
- JWT token validation (shared secret with Node.js backend)
- User information extraction from tokens
- Permission checking
- Flask route decorators for protected endpoints

SECURITY MODEL:
- Node.js backend creates JWT tokens after user login
- Python backend validates tokens on each API request
- Shared secret (JWT_SECRET_KEY) must match between both backends
"""

import logging
import jwt
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from functools import wraps

from flask import request, jsonify, g

from config_modules.config import JWTConfig

# ============================================================================
# LOGGING SETUP
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# JWT TOKEN VALIDATOR
# ============================================================================

class JWTValidator:
    """
    JWT token validator for authentication.

    Validates tokens created by Node.js backend and extracts user information.
    """

    def __init__(self):
        """Initialize validator with config"""
        self.secret_key = JWTConfig.JWT_SECRET_KEY
        self.algorithm = JWTConfig.JWT_ALGORITHM
        self.required_claims = JWTConfig.REQUIRED_CLAIMS

        # Warn if using placeholder secret
        if JWTConfig.is_placeholder():
            logger.warning(
                "⚠️  JWT_SECRET_KEY is placeholder! "
                "Update in .env file with actual secret from Node.js team"
            )

    def extract_token_from_header(self, auth_header: Optional[str]) -> Optional[str]:
        """
        Extract JWT token from Authorization header.

        Expected format: "Bearer <token>"

        Args:
            auth_header: Authorization header value

        Returns:
            Token string if valid format, None otherwise
        """
        if not auth_header:
            return None

        parts = auth_header.split()

        if len(parts) != 2:
            logger.warning("Invalid Authorization header format")
            return None

        if parts[0].lower() != JWTConfig.TOKEN_PREFIX.lower():
            logger.warning(f"Invalid token prefix: {parts[0]}")
            return None

        return parts[1]

    def validate_token(self, token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Validate JWT token and extract payload.

        Args:
            token: JWT token string

        Returns:
            Tuple of (is_valid, payload_dict, error_message)
        """
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            # Check required claims
            missing_claims = [
                claim for claim in self.required_claims
                if claim not in payload
            ]

            if missing_claims:
                error_msg = f"Token missing required claims: {', '.join(missing_claims)}"
                logger.warning(error_msg)
                return False, None, error_msg

            # Check expiration (jwt.decode already checks 'exp', but let's be explicit)
            if 'exp' in payload:
                exp_timestamp = payload['exp']
                if datetime.utcnow().timestamp() > exp_timestamp:
                    return False, None, "Token has expired"

            logger.info(
                f"✅ Token validated successfully for user: {payload.get('username')}"
            )
            return True, payload, None

        except jwt.ExpiredSignatureError:
            logger.warning("Token validation failed: Expired signature")
            return False, None, "Token has expired"

        except jwt.InvalidTokenError as e:
            logger.warning(f"Token validation failed: {str(e)}")
            return False, None, f"Invalid token: {str(e)}"

        except Exception as e:
            logger.error(f"Unexpected error during token validation: {e}")
            return False, None, f"Token validation error: {str(e)}"

    def validate_request(self) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Validate JWT token from current Flask request.

        Extracts token from Authorization header and validates it.

        Returns:
            Tuple of (is_valid, payload_dict, error_message)
        """
        # Get Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return False, None, "No Authorization header provided"

        # Extract token
        token = self.extract_token_from_header(auth_header)

        if not token:
            return False, None, "Invalid Authorization header format"

        # Validate token
        return self.validate_token(token)


# ============================================================================
# USER INFORMATION EXTRACTION
# ============================================================================

class UserInfo:
    """
    Container for user information extracted from JWT token.
    Handles merged payloads from both Node.js (permissions) and Python (roles).
    """

    def __init__(self, payload: Dict[str, Any]):
        """
        Initialize user info from JWT payload.

        Args:
            payload: Decoded JWT payload dictionary
        """
        # --- Standard Claims (from Node.js or Python) ---
        self.user_id = payload.get('user_id') or payload.get('employee_id')
        self.username = payload.get('username')

        # --- Python Admin System Claims ---
        self.role = payload.get('role', 'user') # Default to 'user' if not present
        self.full_name = payload.get('full_name', self.username or "Unknown")

        # --- Node.js Frontend Claims ---
        self.department = payload.get('department')
        self.permissions = payload.get('permissions', {})
        self.raw_payload = payload

    def has_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission (from Node.js token).

        Args:
            permission: Permission name (e.g., 'data_entry', 'report', 'data_query')

        Returns:
            True if user has permission, False otherwise
        """
        if isinstance(self.permissions, dict):
            return self.permissions.get(permission, False)
        return False

    def is_admin(self) -> bool:
        """
        Check if user has the admin role (from Python token).
        """
        return self.role == 'admin'

    def can_access_department(self, dept_id: str) -> bool:
        """
        Check if user can access a specific department.

        Users can access:
        1. Their own department
        2. Any department if they have admin permissions (from Node.js)
        3. Any department if they have the admin role (from Python)

        Args:
            dept_id: Department ID to check

        Returns:
            True if user can access department, False otherwise
        """
        # Check if user's department matches
        if self.department == dept_id:
            return True

        # Check if user has admin permissions (can access all departments)
        if self.has_permission('admin') or self.has_permission('view_all_departments'):
            return True

        # Check if user has admin role
        if self.is_admin():
            return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert user info to dictionary.

        Returns:
            Dictionary with user information
        """
        return {
            'user_id': self.user_id,
            'username': self.username,
            'full_name': self.full_name,
            'role': self.role,
            'department': self.department,
            'permissions': self.permissions
        }

    def __repr__(self):
        return f"UserInfo(user_id={self.user_id}, full_name={self.full_name}, role={self.role}, department={self.department})"


# ============================================================================
# FLASK ROUTE DECORATORS
# ============================================================================

# Create singleton validator instance
validator = JWTValidator()


def require_auth(f):
    """
    Decorator to require JWT authentication for a Flask route.

    Usage:
        @app.route('/api/v1/protected')
        @require_auth
        def protected_endpoint():
            user = g.user  # Access user info
            return {"message": f"Hello {user.username}"}

    If authentication fails, returns 401 response.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Validate token
        is_valid, payload, error = validator.validate_request()

        if not is_valid:
            logger.warning(f"Authentication failed: {error}")
            return jsonify({
                "success": False,
                "error": "Authentication required",
                "message": error
            }), 401

        # Store user info in Flask's g object (request context)
        g.user = UserInfo(payload)
        g.token_payload = payload

        # Call the actual route function
        return f(*args, **kwargs)

    return decorated_function


def require_permission(permission: str):
    """
    Decorator to require a specific permission for a Flask route.

    Usage:
        @app.route('/api/v1/admin')
        @require_permission('admin')
        def admin_endpoint():
            return {"message": "Admin access granted"}

    If user lacks permission, returns 403 response.

    Args:
        permission: Permission name to check
    """
    def decorator(f):
        @wraps(f)
        @require_auth  # Also require authentication
        def decorated_function(*args, **kwargs):
            user = g.user

            if not user.has_permission(permission):
                logger.warning(
                    f"Permission denied: User {user.username} lacks '{permission}' permission"
                )
                return jsonify({
                    "success": False,
                    "error": "Permission denied",
                    "message": f"You do not have '{permission}' permission"
                }), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_department_access(dept_param_name: str = 'dept_id'):
    """
    Decorator to require access to a specific department.

    Usage:
        @app.route('/api/v1/dashboard/<dept_id>')
        @require_department_access('dept_id')
        def get_dashboard(dept_id):
            # User has access to this department
            return {"department": dept_id}

    Checks if user can access the department specified in the route parameter.

    Args:
        dept_param_name: Name of the route parameter containing department ID
    """
    def decorator(f):
        @wraps(f)
        @require_auth  # Also require authentication
        def decorated_function(*args, **kwargs):
            user = g.user

            # Get department ID from route parameters
            dept_id = kwargs.get(dept_param_name)

            if not dept_id:
                logger.error(f"Department parameter '{dept_param_name}' not found in route")
                return jsonify({
                    "success": False,
                    "error": "Invalid request",
                    "message": "Department parameter missing"
                }), 400

            # Check if user can access this department
            if not user.can_access_department(dept_id):
                logger.warning(
                    f"Department access denied: User {user.username} "
                    f"(dept: {user.department}) cannot access {dept_id}"
                )
                return jsonify({
                    "success": False,
                    "error": "Access denied",
                    "message": f"You do not have access to {dept_id} department"
                }), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_admin(f):
    """
    Decorator to require 'admin' role for a Flask route.
    This decorator MUST be used after @require_auth.

    Usage:
        @app.route('/api/v1/admin_stuff')
        @require_auth
        @require_admin
        def admin_endpoint():
            return {"message": "Admin access granted"}

    If user is not admin, returns 403 response.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # g.user is expected to be populated by @require_auth
        if not g.user:
            return jsonify({
                "success": False,
                "error": "Authentication required",
                "message": "g.user not found. @require_admin must be used after @require_auth."
            }), 500

        if not g.user.is_admin():
            logger.warning(
                f"Permission denied: User {g.user.full_name} (ID: {g.user.user_id}) "
                f"attempted to access admin route."
            )
            return jsonify({
                "success": False,
                "error": "Permission denied",
                "message": "You do not have 'admin' privileges"
            }), 403

        # User is an admin, proceed
        return f(*args, **kwargs)

    return decorated_function


# ============================================================================
# OPTIONAL: ALLOW UNAUTHENTICATED (FOR TESTING)
# ============================================================================

def optional_auth(f):
    """
    Decorator that allows both authenticated and unauthenticated access.

    If a valid token is provided, user info is available in g.user.
    If no token or invalid token, g.user is None.

    Useful for endpoints that have different behavior for logged-in vs guest users.

    Usage:
        @app.route('/api/v1/optional')
        @optional_auth
        def optional_endpoint():
            if g.user:
                return {"message": f"Hello {g.user.username}"}
            else:
                return {"message": "Hello guest"}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Try to validate token
        is_valid, payload, error = validator.validate_request()

        if is_valid:
            g.user = UserInfo(payload)
            g.token_payload = payload
        else:
            g.user = None
            g.token_payload = None

        return f(*args, **kwargs)

    return decorated_function


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "JWTValidator",
    "UserInfo",
    "validator",
    "require_auth",
    "require_permission",
    "require_department_access",
    "optional_auth"
]


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test JWT validation with sample tokens"""
    print("=" * 70)
    print("JWT VALIDATOR TEST")
    print("=" * 70)

    # Check configuration
    print("\n1. Configuration Check:")
    print(f"   Secret Key: {'*' * 20} (hidden)")
    print(f"   Algorithm: {JWTConfig.JWT_ALGORITHM}")
    print(f"   Is Placeholder: {JWTConfig.is_placeholder()}")

    if JWTConfig.is_placeholder():
        print("\n   ⚠️  WARNING: Using placeholder JWT secret!")
        print("   Real validation requires actual secret from Node.js team")

    # Create a test token (this would normally come from Node.js)
    print("\n2. Creating Test Token...")

    import jwt
    from datetime import datetime, timedelta

    test_payload = {
        'user_id': 2470,
        'username': 'test_manager',
        'department': 'env',
        'permissions': {
            'data_entry': True,
            'data_query': True,
            'report': True
        },
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=8)
    }

    test_token = jwt.encode(
        test_payload,
        JWTConfig.JWT_SECRET_KEY,
        algorithm=JWTConfig.JWT_ALGORITHM
    )

    print(f"   Token created: {test_token[:50]}...")

    # Test validation
    print("\n3. Testing Token Validation...")

    val = JWTValidator()
    is_valid, payload, error = val.validate_token(test_token)

    if is_valid:
        print("   ✅ Token validation successful!")
        print(f"   User ID: {payload['user_id']}")
        print(f"   Username: {payload['username']}")
        print(f"   Department: {payload['department']}")
        print(f"   Permissions: {payload['permissions']}")

        # Test UserInfo
        print("\n4. Testing UserInfo...")
        user = UserInfo(payload)
        print(f"   {user}")
        print(f"   Has 'report' permission: {user.has_permission('report')}")
        print(f"   Has 'admin' permission: {user.has_permission('admin')}")
        print(f"   Can access 'env' dept: {user.can_access_department('env')}")
        print(f"   Can access 'hr' dept: {user.can_access_department('hr')}")
    else:
        print(f"   ❌ Token validation failed: {error}")

    # Test expired token
    print("\n5. Testing Expired Token...")

    expired_payload = test_payload.copy()
    expired_payload['exp'] = datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago

    expired_token = jwt.encode(
        expired_payload,
        JWTConfig.JWT_SECRET_KEY,
        algorithm=JWTConfig.JWT_ALGORITHM
    )

    is_valid, payload, error = val.validate_token(expired_token)

    if not is_valid:
        print(f"   ✅ Correctly rejected expired token: {error}")
    else:
        print("   ❌ Failed to reject expired token")

    # Test invalid token
    print("\n6. Testing Invalid Token...")

    is_valid, payload, error = val.validate_token("invalid.token.here")

    if not is_valid:
        print(f"   ✅ Correctly rejected invalid token: {error}")
    else:
        print("   ❌ Failed to reject invalid token")

    print("\n" + "=" * 70)
    print("✅ JWT validator test complete!")
    print("\n📝 NEXT STEPS:")
    print("   1. Get actual JWT_SECRET_KEY from Node.js team")
    print("   2. Update .env file with the shared secret")
    print("   3. Test with real tokens from Node.js backend")