# routes/admin_routes.py
# Full admin routes: manage department_access (CRUD, approve, reject, revoke, extend, convert, delete, list)
# Logs actions to app_activity_log.
# Assumes this blueprint is registered as: app.register_blueprint(admin_bp, url_prefix="/admin")
# and that admin authentication blueprint (/auth/admin_login) already exists.

from flask import Blueprint, request, jsonify, send_from_directory, current_app
import mysql.connector
from config_modules.config import DatabaseConfig
import jwt
from functools import wraps
import datetime

admin_routes_bp = Blueprint("admin_routes", __name__)

# Use same secret as admin_auth
JWT_SECRET = "YOUR_JWT_SECRET"


# -------------------------
# Auth decorator (internal admin)
# -------------------------
def require_admin_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
        if not token:
            current_app.logger.warning("[ADMIN AUTH] Missing token")
            return jsonify({"error": "Missing token"}), 401

        try:
            user = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except Exception as e:
            current_app.logger.warning(f"[ADMIN AUTH] Invalid token: {e}")
            return jsonify({"error": "Invalid or expired token"}), 401

        if user.get("access") != "internal_admin":
            current_app.logger.warning(f"[ADMIN AUTH] Unauthorized access attempt employee_id={user.get('employee_id')}")
            return jsonify({"error": "Unauthorized"}), 403

        # Attach user to request for downstream handlers
        request.user = user
        current_app.logger.info(f"[ADMIN AUTH] Authenticated admin employee_id={user.get('employee_id')}")
        return f(*args, **kwargs)
    return wrapper


# -------------------------
# Helper: log_activity to app_activity_log
# -------------------------
def log_activity(employee_id, action_type, details=None, generated_dashboard_path=None, ip_address=None, flagged_suspicious=0):
    """
    Insert a row into app_activity_log.
    action_type should be one of your enum values: LOGIN_SUCCESS, LOGIN_FAIL, DASHBOARD, CHATBOT
    We use DASHBOARD for admin actions; 'details' provides exact action and affected request_id.
    """
    try:
        conn = mysql.connector.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()
        q = """
            INSERT INTO app_activity_log
            (employee_id, action_type, details, flagged_suspicious, generated_dashboard_path, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(q, (employee_id, action_type, details, int(flagged_suspicious), generated_dashboard_path, ip_address))
        conn.commit()
    except Exception as e:
        current_app.logger.error(f"[LOG] Failed to write activity log: {e} -- details: {details}")
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass


# -------------------------
# Serve admin root -> either login or admin.html depending on token
# -------------------------
@admin_routes_bp.route("/")
def admin_root():
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if token:
        try:
            user = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            if user.get("access") == "internal_admin":
                return send_from_directory("frontend/admin", "admin.html")
        except:
            pass
    return send_from_directory("frontend/admin", "login.html")


# -------------------------
# Serve admin login page (unprotected)
# -------------------------
@admin_routes_bp.route("/login")
def serve_admin_login():
    current_app.logger.info("[ADMIN] Serving admin login page")
    return send_from_directory("frontend/admin", "login.html")


# -------------------------
# Serve admin request form (unprotected - users can submit request)
# If you instead want the request form outside /admin, adjust path accordingly.
# -------------------------
@admin_routes_bp.route("/request", methods=["GET"])
def serve_admin_request_form():
    return send_from_directory("frontend/admin", "request.html")


# -------------------------
# Submit new department_access request (unprotected)
# This inserts a new row into department_access with status 'pending'
# -------------------------
@admin_routes_bp.route("/request", methods=["POST"])
def submit_department_request():
    data = request.json or {}
    employee_id = data.get("employee_id")
    designation = data.get("designation")
    requested_dept_access = data.get("requested_dept_access")
    access_type = data.get("access_type", "guest")
    guest_days = data.get("guest_days", 2)

    if not employee_id or not requested_dept_access:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        conn = mysql.connector.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()
        q = """
            INSERT INTO department_access
            (employee_id, designation, requested_dept_access, access_type, guest_days, status, active)
            VALUES (%s, %s, %s, %s, %s, 'pending', 0)
        """
        cursor.execute(q, (employee_id, designation, requested_dept_access, access_type, guest_days))
        conn.commit()
        request_id = cursor.lastrowid

        # Log the request creation into app_activity_log
        ip = request.remote_addr
        details = f"Created department_access request_id={request_id}, requested_dept_access={requested_dept_access}"
        log_activity(employee_id, "DASHBOARD", details=details, ip_address=ip)

    except Exception as e:
        current_app.logger.error(f"[ADMIN REQUEST] Insert failed: {e}")
        return jsonify({"error": "Failed to submit request"}), 500
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

    return jsonify({"message": "Request submitted", "request_id": request_id})


# -------------------------
# List pending requests (protected)
# -------------------------
@admin_routes_bp.route("/god-eye/requests/pending", methods=["GET"])
@require_admin_auth
def list_pending_requests():
    try:
        conn = mysql.connector.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM department_access WHERE status='pending' ORDER BY requested_at DESC")
        rows = cursor.fetchall()
    except Exception as e:
        current_app.logger.error(f"[LIST PENDING] DB error: {e}")
        return jsonify({"error": "DB error"}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"pending": rows})


# -------------------------
# List all requests (protected)
# -------------------------
@admin_routes_bp.route("/god-eye/requests/all", methods=["GET"])
@require_admin_auth
def list_all_requests():
    try:
        conn = mysql.connector.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM department_access ORDER BY requested_at DESC")
        rows = cursor.fetchall()
    except Exception as e:
        current_app.logger.error(f"[LIST ALL] DB error: {e}")
        return jsonify({"error": "DB error"}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"requests": rows})


# -------------------------
# Approve request (protected)
# Sets status=approved, active=1, granted_at, reviewed_by, reviewed_at
# -------------------------
@admin_routes_bp.route("/god-eye/requests/approve", methods=["POST"])
@require_admin_auth
def approve_request():
    data = request.json or {}
    req_id = data.get("request_id")
    reviewer = request.user.get("employee_id")

    if not req_id:
        return jsonify({"error": "Missing request_id"}), 400

    try:
        conn = mysql.connector.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM department_access WHERE request_id=%s", (req_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Request not found"}), 404

        # Update the request
        cursor.execute("""
            UPDATE department_access
            SET status='approved', active=1, granted_at=NOW(), reviewed_by=%s, reviewed_at=NOW()
            WHERE request_id=%s
        """, (reviewer, req_id))

        conn.commit()

        # Log activity
        details = f"Approved request_id={req_id} for employee_id={row['employee_id']} dept={row['requested_dept_access']}"
        log_activity(reviewer, "DASHBOARD", details=details, ip_address=request.remote_addr)

    except Exception as e:
        current_app.logger.error(f"[APPROVE] DB error: {e}")
        return jsonify({"error": "DB error"}), 500
    finally:
        cursor.close(); conn.close()

    return jsonify({"message": "Approved"})


# -------------------------
# Reject request (protected)
# Sets status='rejected', active=0, reviewed_by, reviewed_at
# -------------------------
@admin_routes_bp.route("/god-eye/requests/reject", methods=["POST"])
@require_admin_auth
def reject_request():
    data = request.json or {}
    req_id = data.get("request_id")
    reviewer = request.user.get("employee_id")

    if not req_id:
        return jsonify({"error": "Missing request_id"}), 400

    try:
        conn = mysql.connector.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM department_access WHERE request_id=%s", (req_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Request not found"}), 404

        cursor.execute("""
            UPDATE department_access
            SET status='rejected', active=0, reviewed_by=%s, reviewed_at=NOW()
            WHERE request_id=%s
        """, (reviewer, req_id))
        conn.commit()

        details = f"Rejected request_id={req_id} for employee_id={row['employee_id']}"
        log_activity(reviewer, "DASHBOARD", details=details, ip_address=request.remote_addr)

    except Exception as e:
        current_app.logger.error(f"[REJECT] DB error: {e}")
        return jsonify({"error": "DB error"}), 500
    finally:
        cursor.close(); conn.close()

    return jsonify({"message": "Rejected"})


# -------------------------
# Revoke access (protected)
# active -> 0, keep status as approved
# -------------------------
@admin_routes_bp.route("/god-eye/requests/revoke", methods=["POST"])
@require_admin_auth
def revoke_request():
    data = request.json or {}
    req_id = data.get("request_id")
    reviewer = request.user.get("employee_id")

    if not req_id:
        return jsonify({"error": "Missing request_id"}), 400

    try:
        conn = mysql.connector.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM department_access WHERE request_id=%s", (req_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Request not found"}), 404

        cursor.execute("UPDATE department_access SET active=0 WHERE request_id=%s", (req_id,))
        conn.commit()

        details = f"Revoked access request_id={req_id} for employee_id={row['employee_id']}"
        log_activity(reviewer, "DASHBOARD", details=details, ip_address=request.remote_addr)

    except Exception as e:
        current_app.logger.error(f"[REVOKE] DB error: {e}")
        return jsonify({"error": "DB error"}), 500
    finally:
        cursor.close(); conn.close()

    return jsonify({"message": "Revoked"})


# -------------------------
# Extend guest days (protected)
# -------------------------
@admin_routes_bp.route("/god-eye/requests/extend", methods=["POST"])
@require_admin_auth
def extend_guest_days():
    data = request.json or {}
    req_id = data.get("request_id")
    extra_days = int(data.get("extra_days", 0))
    reviewer = request.user.get("employee_id")

    if not req_id or extra_days <= 0:
        return jsonify({"error": "Invalid payload"}), 400

    try:
        conn = mysql.connector.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT guest_days FROM department_access WHERE request_id=%s", (req_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Request not found"}), 404

        new_days = row[0] + extra_days
        cursor.execute("UPDATE department_access SET guest_days=%s WHERE request_id=%s", (new_days, req_id))
        conn.commit()

        details = f"Extended guest_days for request_id={req_id} by {extra_days} days (new={new_days})"
        log_activity(reviewer, "DASHBOARD", details=details, ip_address=request.remote_addr)

    except Exception as e:
        current_app.logger.error(f"[EXTEND] DB error: {e}")
        return jsonify({"error": "DB error"}), 500
    finally:
        cursor.close(); conn.close()

    return jsonify({"message": "Extended", "new_guest_days": new_days})


# -------------------------
# Convert guest -> permanent (protected)
# -------------------------
@admin_routes_bp.route("/god-eye/requests/convert", methods=["POST"])
@require_admin_auth
def convert_guest_to_permanent():
    data = request.json or {}
    req_id = data.get("request_id")
    reviewer = request.user.get("employee_id")

    if not req_id:
        return jsonify({"error": "Missing request_id"}), 400

    try:
        conn = mysql.connector.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM department_access WHERE request_id=%s", (req_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Request not found"}), 404

        cursor.execute("""
            UPDATE department_access
            SET access_type='permanent', guest_days=NULL
            WHERE request_id=%s
        """, (req_id,))
        conn.commit()

        details = f"Converted request_id={req_id} to permanent access"
        log_activity(reviewer, "DASHBOARD", details=details, ip_address=request.remote_addr)

    except Exception as e:
        current_app.logger.error(f"[CONVERT] DB error: {e}")
        return jsonify({"error": "DB error"}), 500
    finally:
        cursor.close(); conn.close()

    return jsonify({"message": "Converted to permanent"})


# -------------------------
# Edit request (protected) - change requested_dept_access, designation, guest_days, access_type
# -------------------------
@admin_routes_bp.route("/god-eye/requests/edit", methods=["POST"])
@require_admin_auth
def edit_request():
    data = request.json or {}
    req_id = data.get("request_id")
    fields = {}
    allowed = ["requested_dept_access", "designation", "guest_days", "access_type"]

    if not req_id:
        return jsonify({"error": "Missing request_id"}), 400

    for k in allowed:
        if k in data:
            fields[k] = data[k]

    if not fields:
        return jsonify({"error": "No editable fields provided"}), 400

    set_clause = ", ".join([f"{k}=%s" for k in fields.keys()])
    params = list(fields.values()) + [req_id]
    reviewer = request.user.get("employee_id")

    try:
        conn = mysql.connector.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM department_access WHERE request_id=%s", (req_id,))
        old = cursor.fetchone()
        if not old:
            return jsonify({"error": "Request not found"}), 404

        q = f"UPDATE department_access SET {set_clause} WHERE request_id=%s"
        cursor.execute(q, params)
        conn.commit()

        details = f"Edited request_id={req_id} fields={list(fields.keys())}"
        log_activity(reviewer, "DASHBOARD", details=details, ip_address=request.remote_addr)

    except Exception as e:
        current_app.logger.error(f"[EDIT] DB error: {e}")
        return jsonify({"error": "DB error"}), 500
    finally:
        cursor.close(); conn.close()

    return jsonify({"message": "Edited"})


# -------------------------
# View active permissions (protected)
# -------------------------
@admin_routes_bp.route("/god-eye/requests/active", methods=["GET"])
@require_admin_auth
def list_active_requests():
    try:
        conn = mysql.connector.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM department_access WHERE active=1 ORDER BY granted_at DESC")
        rows = cursor.fetchall()
    except Exception as e:
        current_app.logger.error(f"[LIST ACTIVE] DB error: {e}")
        return jsonify({"error": "DB error"}), 500
    finally:
        cursor.close(); conn.close()

    return jsonify({"active": rows})


# -------------------------
# View expired guest access (protected)
# expired = active=0 AND status='approved' AND granted_at + INTERVAL guest_days DAY < NOW()
# -------------------------
@admin_routes_bp.route("/god-eye/requests/expired", methods=["GET"])
@require_admin_auth
def list_expired_guests():
    try:
        conn = mysql.connector.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM department_access
            WHERE status='approved' AND active=0
            ORDER BY granted_at DESC
        """)
        rows = cursor.fetchall()
    except Exception as e:
        current_app.logger.error(f"[LIST EXPIRED] DB error: {e}")
        return jsonify({"error": "DB error"}), 500
    finally:
        cursor.close(); conn.close()

    return jsonify({"expired": rows})


# -------------------------
# Delete request (protected)
# -------------------------
@admin_routes_bp.route("/god-eye/requests/delete", methods=["POST"])
@require_admin_auth
def delete_request():
    data = request.json or {}
    req_id = data.get("request_id")
    reviewer = request.user.get("employee_id")

    if not req_id:
        return jsonify({"error": "Missing request_id"}), 400

    try:
        conn = mysql.connector.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM department_access WHERE request_id=%s", (req_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Request not found"}), 404

        cursor.execute("DELETE FROM department_access WHERE request_id=%s", (req_id,))
        conn.commit()

        details = f"Deleted request_id={req_id} for employee_id={row[1] if len(row)>1 else 'unknown'}"
        log_activity(reviewer, "DASHBOARD", details=details, ip_address=request.remote_addr)

    except Exception as e:
        current_app.logger.error(f"[DELETE] DB error: {e}")
        return jsonify({"error": "DB error"}), 500
    finally:
        cursor.close(); conn.close()

    return jsonify({"message": "Deleted"})


# -------------------------
# Expire guest access job (protected)
# Finds active guest records where granted_at + guest_days < NOW() and deactivates them
# -------------------------
@admin_routes_bp.route("/god-eye/expire_guest", methods=["POST"])
@require_admin_auth
def expire_guest_access():
    reviewer = request.user.get("employee_id")
    try:
        conn = mysql.connector.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor(dictionary=True)

        # Select active guest rows that are past expiry
        cursor.execute("""
            SELECT request_id, employee_id, guest_days, granted_at
            FROM department_access
            WHERE active=1 AND access_type='guest' AND granted_at IS NOT NULL
        """)
        rows = cursor.fetchall()
        expired_ids = []
        for r in rows:
            request_id = r[0]
            emp = r[1]
            guest_days = r[2] or 0
            granted_at = r[3]
            if granted_at is None:
                continue
            expiry_date = granted_at + datetime.timedelta(days=guest_days)
            if datetime.datetime.utcnow() > expiry_date:
                cursor.execute("UPDATE department_access SET active=0 WHERE request_id=%s", (request_id,))
                expired_ids.append(request_id)

        conn.commit()

        details = f"Expired guest requests: {expired_ids}"
        log_activity(reviewer, "DASHBOARD", details=details, ip_address=request.remote_addr)

    except Exception as e:
        current_app.logger.error(f"[EXPIRE GUEST] DB error: {e}")
        return jsonify({"error": "DB error"}), 500
    finally:
        try:
            cursor.close(); conn.close()
        except:
            pass

    return jsonify({"expired_ids": expired_ids})


# -------------------------
# Simple health/test route
# -------------------------
@admin_routes_bp.route("/ping")
@require_admin_auth
def admin_ping():
    return jsonify({"message": "Admin authenticated!", "employee": request.user["employee_id"]})
