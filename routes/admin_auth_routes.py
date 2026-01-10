from flask import Blueprint, request, jsonify, current_app
import hashlib
import mysql.connector
from config_modules.config import DatabaseConfig
import jwt
import datetime

admin_auth_bp = Blueprint("admin_auth", __name__)

JWT_SECRET = "YOUR_JWT_SECRET"

@admin_auth_bp.route("/auth/admin_login", methods=["POST"])
def admin_login():
    data = request.json or {}
    emp = data.get("employee_id")
    pwd = data.get("password")

    current_app.logger.info(f"[ADMIN LOGIN] Attempt: employee_id={emp}")

    if not emp or not pwd:
        current_app.logger.warning("[ADMIN LOGIN] Missing credentials")
        return jsonify({"error": "Missing credentials"}), 400

    hashed_pwd = hashlib.sha1(pwd.encode()).hexdigest()

    # Connect
    conn = mysql.connector.connect(**DatabaseConfig.get_connection_params())
    cursor = conn.cursor(dictionary=True)

    # 1️⃣ Check intranet_user_login for ID + password
    cursor.execute("""
        SELECT employee_id, password
        FROM intranet_user_login
        WHERE employee_id = %s
    """, (emp,))
    row = cursor.fetchone()

    if not row:
        current_app.logger.warning(f"[ADMIN LOGIN] No such intranet user: {emp}")
        return jsonify({"error": "Invalid credentials"}), 401

    if row["password"] != hashed_pwd:
        current_app.logger.warning(f"[ADMIN LOGIN] Wrong password for employee_id={emp}")
        return jsonify({"error": "Invalid credentials"}), 401

    # 2️⃣ Check app_users for permission
    cursor.execute("""
        SELECT role, full_name
        FROM app_users
        WHERE employee_id = %s
    """, (emp,))
    access = cursor.fetchone()

    cursor.close()
    conn.close()

    if not access:
        current_app.logger.warning(f"[ADMIN LOGIN] ACCESS DENIED (not in app_users): {emp}")
        return jsonify({"error": "You are not authorized for the internal admin panel"}), 403

    # 3️⃣ Login success
    current_app.logger.info(f"[ADMIN LOGIN] SUCCESS internal admin: {emp}")

    payload = {
        "employee_id": emp,
        "role": access["role"],
        "full_name": access["full_name"],
        "access": "internal_admin",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    return jsonify({"token": token})
