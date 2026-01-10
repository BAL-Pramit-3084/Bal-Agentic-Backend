"""
app_frontend.py - BAL Agentic AI Portal Frontend
============================================
Clean, modern frontend for BAL Dashboard System.
Uses SHA-1 authentication from intranet_user_login table.

Design:
- White/grey monochrome background
- BAL logo and colors
- Inline dashboard preview (no popup modal)
- Clean dashboard generation interface
"""

import hashlib
import logging
from datetime import datetime
from functools import wraps

from flask import Blueprint, request, session, redirect, url_for
import mysql.connector

from config_modules.config import DatabaseConfig

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint("frontend", __name__, url_prefix="/dashboard")


# ============================================================================
# AUTHENTICATION
# ============================================================================

def verify_user_credentials(empid: str, password: str) -> tuple[bool, dict]:
    """Verify user against intranet_user_login with SHA-1 password."""
    try:
        password_hash = hashlib.sha1(password.encode()).hexdigest().upper()

        conn = mysql.connector.connect(
            host=DatabaseConfig.MYSQL_HOST,
            port=DatabaseConfig.MYSQL_PORT,
            user=DatabaseConfig.MYSQL_USER,
            password=DatabaseConfig.MYSQL_PASSWORD,
            database=DatabaseConfig.MYSQL_DATABASE
        )
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT EMPID, STATUS, TOTALVISIT
            FROM intranet_user_login
            WHERE EMPID = %s AND USER_PWD = %s
        """
        cursor.execute(query, (empid, password_hash))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and user['STATUS'] == 'A':  # A = Active
            logger.info(f"Login successful: {empid}")
            return True, {"empid": user['EMPID'], "visits": user['TOTALVISIT']}
        else:
            logger.warning(f"Login failed: {empid}")
            return False, {"error": "Invalid credentials or inactive account"}

    except Exception as e:
        logger.error(f"Auth error: {e}", exc_info=True)
        return False, {"error": str(e)}


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('frontend.index'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# ROUTES
# ============================================================================

@bp.route("/")
def index():
    """Main page - Login or Dashboard selector"""
    # If already logged in, go to main page
    if 'user' in session:
        return redirect(url_for('frontend.main_page'))

    # Otherwise show login
    error = request.args.get('error')

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <script src="https://t.contentsquare.net/uxa/20c879254b465.js"></script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BAL Agentic AI Portal - Login</title>
    <style>
        :root {{
            --bal-blue: #0076ce;
            --bal-blue-100: #e5f2fc;
            --bal-red: #d62828;
            --bg-soft: #f5f6f7;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f5f6f7 0%, #e8eaed 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .login-container {{
            background: white;
            padding: 50px 40px;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.08);
            width: 100%;
            max-width: 440px;
        }}

        .logo-section {{
            text-align: center;
            margin-bottom: 40px;
        }}

        .logo-section img {{
            width: 180px;
            height: auto;
            margin-bottom: 20px;
        }}

        .logo-section h1 {{
            color: #1a1a1a;
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
        }}

        .logo-section p {{
            color: #666;
            font-size: 15px;
            font-weight: 400;
        }}

        .error-message {{
            background: #fff5f5;
            border-left: 4px solid var(--bal-red);
            color: var(--bal-red);
            padding: 14px 16px;
            border-radius: 8px;
            margin-bottom: 24px;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .form-group {{
            margin-bottom: 24px;
        }}

        .form-group label {{
            display: block;
            color: #333;
            font-weight: 500;
            margin-bottom: 8px;
            font-size: 14px;
        }}

        .form-group input {{
            width: 100%;
            padding: 14px 16px;
            border: 1.5px solid #e0e0e0;
            border-radius: 10px;
            font-size: 15px;
            transition: all 0.2s;
            background: white;
        }}

        .form-group input:focus {{
            outline: none;
            border-color: var(--bal-blue);
            background: var(--bal-blue-100);
        }}

        .submit-btn {{
            width: 100%;
            padding: 16px;
            background: var(--bal-blue);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }}

        .submit-btn:hover {{
            background: #005fa3;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 118, 206, 0.3);
        }}

        .footer {{
            text-align: center;
            margin-top: 32px;
            color: #999;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo-section">
            <img src="/static/images/bal_logo.png" alt="BAL Logo">
            <h1>Agentic AI Portal</h1>
            <p>Dashboard Intelligence System</p>
        </div>

        {'<div class="error-message">⚠️ ' + error + '</div>' if error else ''}

        <form method="POST" action="/dashboard/login">
            <div class="form-group">
                <label for="empid">Employee ID</label>
                <input type="text" id="empid" name="empid" required autofocus
                       placeholder="Enter your employee ID">
            </div>

            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required
                       placeholder="Enter your password">
            </div>

            <button type="submit" class="submit-btn">Sign In</button>
        </form>

        <div class="footer">
            Balasore Alloys Limited © 2025
        </div>
    </div>
</body>
</html>
"""


@bp.route("/login", methods=["POST"])
def login():
    """Handle login"""
    empid = request.form.get('empid', '').strip()
    password = request.form.get('password', '')

    if not empid or not password:
        return redirect(url_for('frontend.index', error='Please enter both fields'))

    success, user_data = verify_user_credentials(empid, password)

    if success:
        session['user'] = user_data
        return redirect(url_for('frontend.main_page'))
    else:
        error = user_data.get('error', 'Invalid credentials')
        return redirect(url_for('frontend.index', error=error))


@bp.route("/logout")
def logout():
    """Logout"""
    session.pop('user', None)
    return redirect(url_for('frontend.index'))


@bp.route("/main")
@login_required
def main_page():
    """Main dashboard page with inline dashboard preview"""
    user = session['user']
    today = datetime.now().strftime('%Y-%m-%d')

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <script src="https://t.contentsquare.net/uxa/20c879254b465.js"></script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agentic AI Portal</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        :root {{
            --bal-blue: #0076ce;
            --bal-blue-100: #e5f2fc;
            --bal-red: #d62828;
            --bg-soft: #f5f6f7;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-soft);
            color: #1a1a1a;
            min-height: 100vh;
        }}

        .header {{
            background: white;
            border-bottom: 1px solid #e0e0e0;
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }}

        .header-left {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}

        .header-left img {{
            width: 120px;
            height: auto;
        }}

        .header-title {{
            border-left: 2px solid var(--bal-blue);
            padding-left: 20px;
        }}

        .header-title h1 {{
            font-size: 24px;
            font-weight: 600;
            color: #1a1a1a;
        }}

        .header-title p {{
            font-size: 13px;
            color: #666;
            margin-top: 2px;
        }}

        .header-right {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}

        .user-info {{
            color: #666;
            font-size: 14px;
        }}

        .user-info strong {{
            color: var(--bal-blue);
        }}

        .logout-btn {{
            background: var(--bal-red);
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }}

        .logout-btn:hover {{
            background: #b91f1f;
            transform: translateY(-1px);
        }}

        main {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px;
        }}

        .page-title {{
            font-size: 32px;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 8px;
        }}

        .page-subtitle {{
            font-size: 16px;
            color: #666;
            margin-bottom: 32px;
        }}

        .controls-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 32px;
        }}

        .control-card {{
            background: white;
            border-radius: 16px;
            padding: 32px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
            border: 1px solid #e0e0e0;
        }}

        .card-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
        }}

        .card-icon {{
            width: 48px;
            height: 48px;
            background: var(--bal-blue-100);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--bal-blue);
        }}

        .card-header h3 {{
            font-size: 18px;
            font-weight: 600;
            color: #1a1a1a;
        }}

        .dept-option {{
            background: var(--bg-soft);
            border: 2px solid transparent;
            border-radius: 12px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 16px;
        }}

        .dept-option:hover {{
            background: var(--bal-blue-100);
            border-color: var(--bal-blue);
        }}

        .dept-option.selected {{
            background: var(--bal-blue);
            color: white;
            border-color: var(--bal-blue);
        }}

        .dept-option .icon {{
            font-size: 32px;
        }}

        .dept-option .info h4 {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 4px;
        }}

        .dept-option .info p {{
            font-size: 13px;
            opacity: 0.8;
        }}

        .form-group {{
            margin-bottom: 20px;
        }}

        .form-group:last-child {{
            margin-bottom: 0;
        }}

        .form-group label {{
            display: block;
            font-size: 14px;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
        }}

        .form-group select,
        .form-group input[type="date"] {{
            width: 100%;
            padding: 14px 16px;
            border: 1.5px solid #e0e0e0;
            border-radius: 10px;
            font-size: 15px;
            transition: all 0.2s;
            background: white;
        }}

        .form-group select:focus,
        .form-group input[type="date"]:focus {{
            outline: none;
            border-color: var(--bal-blue);
            background: var(--bal-blue-100);
        }}

        .generate-btn {{
            width: 100%;
            padding: 16px;
            background: var(--bal-blue);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            transition: all 0.3s;
        }}

        .generate-btn:hover {{
            background: #005fa3;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 118, 206, 0.3);
        }}

        .generate-btn:disabled {{
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }}

        .dashboard-preview {{
            background: white;
            border-radius: 16px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
            overflow: hidden;
            height: 950px;
            display: flex;
            flex-direction: column;
        }}

        .dashboard-preview-header {{
            padding: 20px 32px;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--bg-soft);
        }}

        .dashboard-preview-header h3 {{
            font-size: 18px;
            font-weight: 600;
            color: #1a1a1a;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        /* Download Dropdown */
        .download-dropdown {{
            position: relative;
            display: inline-block;
        }}

        .download-btn {{
            background: var(--bal-blue);
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            transition: all 0.2s;
            border: none;
        }}

        .download-btn:hover {{
            background: #005fa3;
        }}

        .download-btn.disabled {{
            opacity: 0.5;
            cursor: not-allowed;
            pointer-events: none;
            background: #ccc;
        }}

        .download-menu {{
            display: none;
            position: absolute;
            top: 100%;
            right: 0;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
            min-width: 160px;
            z-index: 100;
            margin-top: 4px;
            overflow: hidden;
        }}

        .download-menu.show {{
            display: block;
        }}

        .download-menu-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 16px;
            color: #333;
            text-decoration: none;
            font-size: 14px;
            transition: all 0.2s;
            cursor: pointer;
            border: none;
            background: none;
            width: 100%;
            text-align: left;
        }}

        .download-menu-item:hover {{
            background: var(--bal-blue-100);
            color: var(--bal-blue);
        }}

        .download-menu-item.disabled {{
            opacity: 0.5;
            cursor: not-allowed;
            color: #999;
        }}

        .download-menu-item.disabled:hover {{
            background: none;
            color: #999;
        }}

        .download-menu-item i {{
            width: 18px;
            height: 18px;
        }}

        .download-menu-item .format-badge {{
            margin-left: auto;
            font-size: 11px;
            padding: 2px 6px;
            background: #f0f0f0;
            border-radius: 4px;
            color: #666;
        }}

        .dashboard-preview-body {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #fafbfc;
            position: relative;
        }}

        .empty-state {{
            text-align: center;
            color: #999;
        }}

        .empty-state-icon {{
            font-size: 64px;
            margin-bottom: 16px;
            opacity: 0.3;
        }}

        .empty-state-text {{
            font-size: 18px;
            font-weight: 500;
            color: #666;
        }}

        .empty-state-subtext {{
            font-size: 14px;
            margin-top: 8px;
            color: #999;
        }}

        #dashboardFrame {{
            width: 100%;
            height: 100%;
            border: none;
            display: none;
        }}

        #dashboardFrame.visible {{
            display: block;
        }}

        .loading-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.95);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 10;
        }}

        .loading-overlay.visible {{
            display: flex;
        }}

        .loading-content {{
            text-align: center;
        }}

        .loading-spinner {{
            width: 60px;
            height: 60px;
            border: 4px solid var(--bal-blue-100);
            border-top-color: var(--bal-blue);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }}

        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}

        .loading-text {{
            font-size: 18px;
            font-weight: 500;
            color: #666;
            margin-bottom: 8px;
        }}

        .loading-subtext {{
            font-size: 14px;
            color: #999;
        }}

        /* Chat Button */
        .chat-fab {{
            position: fixed;
            bottom: 32px;
            right: 32px;
            width: 64px;
            height: 64px;
            border-radius: 50%;
            background: var(--bal-blue);
            color: white;
            border: none;
            box-shadow: 0 4px 16px rgba(0, 118, 206, 0.4);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 999;
            transition: all 0.3s;
        }}

        .chat-fab:hover {{
            transform: scale(1.1);
            box-shadow: 0 6px 24px rgba(0, 118, 206, 0.5);
        }}

        /* Chat Modal */
        .chat-modal {{
            display: none;
            position: fixed;
            bottom: 110px;
            right: 32px;
            width: 420px;
            height: 600px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            flex-direction: column;
            z-index: 1000;
        }}

        .chat-header {{
            padding: 20px 24px;
            background: var(--bal-blue);
            color: white;
            border-radius: 16px 16px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 600;
            font-size: 16px;
        }}

        .chat-header .close-btn {{
            color: white;
            font-size: 24px;
            cursor: pointer;
            line-height: 1;
        }}

        .chat-body {{
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
            background: var(--bg-soft);
        }}

        .chat-bubble {{
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 12px;
            line-height: 1.5;
            word-wrap: break-word;
        }}

        .chat-bubble.user {{
            align-self: flex-end;
            background: var(--bal-blue);
            color: white;
            border-bottom-right-radius: 4px;
        }}

        .chat-bubble.assistant {{
            align-self: flex-start;
            background: white;
            color: #1a1a1a;
            border-bottom-left-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}

        .chat-footer {{
            padding: 20px;
            border-top: 1px solid #e0e0e0;
            background: white;
            border-radius: 0 0 16px 16px;
        }}

        #chat-form {{
            display: flex;
            gap: 10px;
        }}

        #chat-prompt {{
            flex: 1;
            padding: 12px 16px;
            border: 1.5px solid #e0e0e0;
            border-radius: 10px;
            font-size: 14px;
            transition: all 0.2s;
        }}

        #chat-prompt:focus {{
            outline: none;
            border-color: var(--bal-blue);
            background: var(--bal-blue-100);
        }}

        #chat-send-btn {{
            background: var(--bal-blue);
            color: white;
            border: none;
            width: 44px;
            height: 44px;
            border-radius: 10px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }}

        #chat-send-btn:hover {{
            background: #005fa3;
        }}

        #chat-send-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}

        /* Voice Buttons */
        .voice-btn {{
            background: #f0f0f0;
            color: #666;
            border: none;
            width: 44px;
            height: 44px;
            border-radius: 10px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }}

        .voice-btn:hover {{
            background: #e0e0e0;
            color: #333;
        }}

        .voice-btn.recording {{
            background: var(--bal-red);
            color: white;
            animation: pulse 1s infinite;
        }}

        .voice-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}

        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
        }}

        /* Voice Level Visualizer */
        .voice-visualizer {{
            display: none;
            align-items: center;
            justify-content: center;
            gap: 3px;
            height: 24px;
            margin-bottom: 8px;
        }}

        .voice-visualizer.active {{
            display: flex;
        }}

        .voice-bar {{
            width: 4px;
            height: 8px;
            background: var(--bal-red);
            border-radius: 2px;
            transition: height 0.05s ease;
        }}

        @keyframes voice-wave {{
            0%, 100% {{ height: 8px; }}
            50% {{ height: 24px; }}
        }}

        /* Speaker button on chat bubbles */
        .chat-bubble.assistant {{
            position: relative;
        }}

        .chat-bubble .speak-btn {{
            position: absolute;
            bottom: -8px;
            right: -8px;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: white;
            border: 1px solid #e0e0e0;
            color: #666;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .chat-bubble .speak-btn:hover {{
            background: var(--bal-blue);
            color: white;
            border-color: var(--bal-blue);
        }}

        .chat-bubble .speak-btn.playing {{
            background: var(--bal-blue);
            color: white;
            border-color: var(--bal-blue);
        }}

        .chat-bubble .speak-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}

        /* Voice status indicator */
        .voice-status {{
            font-size: 12px;
            color: #999;
            text-align: center;
            padding: 4px 0;
            display: none;
        }}

        .voice-status.visible {{
            display: block;
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-left">
            <img src="/static/images/bal_logo.png" alt="BAL Logo">
            <div class="header-title">
                <h1>Agentic AI Portal</h1>
                <p>Dashboard Intelligence System</p>
            </div>
        </div>
        <div class="header-right">
            <div class="user-info">
                Welcome, <strong>{user['empid']}</strong>
            </div>
            <a href="/dashboard/logout" class="logout-btn">Logout</a>
        </div>
    </header>

    <main>
        <!-- Single Centered Control Card -->
        <div style="max-width: 1306px; margin: 0 auto;">
            <div class="control-card">
                <div class="card-header">
                    <div class="card-icon">
                        <i data-lucide="calendar"></i>
                    </div>
                    <h3>Generate Dashboard</h3>
                </div>

                <div style="display: grid; grid-template-columns: 1fr; gap: 20px; margin-bottom: 24px;">
                    <div class="form-group" style="margin-bottom: 0;">
                        <label for="dept-select">Department</label>
                        <select id="dept-select" onchange="selectDept(this.value)">
                            <option value="furnace" selected>Furnace Operations</option>
                            <option value="qc">Quality Control</option>
                            <option value="scm">Supply Chain Management</option>
                            <option value="crm">CRM Department</option>
                            <option value="env">Environment</option>
                            <option value="geology">Geology & Survey</option>
                            <option value="automobile">Automobile</option>
                        </select>
                    </div>

                    <div class="form-group" style="margin-bottom: 0;">
                        <label style="display: flex; align-items: center; gap: 8px;">
                            <input type="checkbox" id="range-mode-toggle" onchange="toggleRangeMode()" style="width: auto; cursor: pointer;">
                            <span>Date Range Mode</span>
                        </label>
                    </div>

                    <!-- Single Date Picker (default) -->
                    <div id="single-date-section" class="form-group" style="margin-bottom: 0;">
                        <label for="dashboard-date">Select Date</label>
                        <input type="date" id="dashboard-date" value="{today}">
                    </div>

                    <!-- Date Range Picker (hidden by default) -->
                    <div id="date-range-section" style="display: none; gap: 16px;">
                        <div class="form-group" style="margin-bottom: 0;">
                            <label for="start-date">Start Date</label>
                            <input type="date" id="start-date" value="{today}">
                        </div>
                        <div class="form-group" style="margin-bottom: 0;">
                            <label for="end-date">End Date</label>
                            <input type="date" id="end-date" value="{today}">
                        </div>
                    </div>
                </div>

                <button class="generate-btn" onclick="generateDashboard()" id="generate-btn">
                    <i data-lucide="layout-dashboard"></i>
                    Generate Dashboard
                </button>
            </div>
        </div>

        <!-- Inline Dashboard Preview -->
        <div class="dashboard-preview" style="margin-top: 32px;">
            <div class="dashboard-preview-header">
                <h3>
                    <i data-lucide="monitor"></i>
                    Dashboard Preview
                </h3>
                <div class="download-dropdown" id="downloadDropdown">
                    <button id="downloadBtn" class="download-btn disabled" onclick="toggleDownloadMenu()">
                        <i data-lucide="download"></i>
                        Download
                        <i data-lucide="chevron-down" style="width:16px;height:16px;margin-left:4px;"></i>
                    </button>
                    <div class="download-menu" id="downloadMenu">
                        <button class="download-menu-item" onclick="downloadDashboard('html')">
                            <i data-lucide="file-code"></i>
                            HTML
                            <span class="format-badge">.html</span>
                        </button>
                        <button class="download-menu-item" id="pdfDownloadBtn" onclick="downloadDashboard('pdf')">
                            <i data-lucide="file-text"></i>
                            PDF
                            <span class="format-badge">.pdf</span>
                        </button>
                        <button class="download-menu-item" id="excelDownloadBtn" onclick="downloadDashboard('excel')">
                            <i data-lucide="file-spreadsheet"></i>
                            Excel
                            <span class="format-badge">.xlsx</span>
                        </button>
                    </div>
                </div>
            </div>
            <div class="dashboard-preview-body">
                <div id="emptyState" class="empty-state">
                    <div class="empty-state-icon">
                        <i data-lucide="layout-dashboard"></i>
                    </div>
                    <div class="empty-state-text">Generated dashboard will appear here</div>
                    <div class="empty-state-subtext">Select a department and date, then click Generate Dashboard</div>
                </div>
                <div id="loadingOverlay" class="loading-overlay">
                    <div class="loading-content">
                        <div class="loading-spinner"></div>
                        <div class="loading-text">Generating Dashboard...</div>
                        <div class="loading-subtext">This may take a few seconds</div>
                    </div>
                </div>
                <iframe id="dashboardFrame" src="about:blank"></iframe>
            </div>
        </div>
    </main>

    <!-- Chat FAB Button -->
    <button class="chat-fab" onclick="toggleChat()" title="Ask AI">
        <i data-lucide="message-circle" size="28"></i>
    </button>

    <!-- Chat Modal -->
    <div id="chatModal" class="chat-modal">
        <div class="chat-header">
            <span>💬 AI Assistant</span>
            <span class="close-btn" onclick="toggleChat()">&times;</span>
        </div>
        <div class="chat-body" id="chat-modal-body">
             <div class="chat-bubble assistant">
                Hi! I'm your AI assistant. Ask me anything about the selected department's data.
             </div>
        </div>
        <div class="chat-footer">
            <div id="voice-visualizer" class="voice-visualizer">
                <div class="voice-bar"></div>
                <div class="voice-bar"></div>
                <div class="voice-bar"></div>
                <div class="voice-bar"></div>
                <div class="voice-bar"></div>
                <div class="voice-bar"></div>
                <div class="voice-bar"></div>
                <div class="voice-bar"></div>
                <div class="voice-bar"></div>
                <div class="voice-bar"></div>
                <div class="voice-bar"></div>
                <div class="voice-bar"></div>
            </div>
            <div id="voice-status" class="voice-status"></div>
            <form id="chat-form" onsubmit="sendChatMessage(event)">
                <button type="button" id="mic-btn" class="voice-btn" onclick="toggleRecording()" title="Voice input">
                    <i data-lucide="mic"></i>
                </button>
                <input type="text" id="chat-prompt" placeholder="Ask a question..." required>
                <button type="submit" id="chat-send-btn">
                    <i data-lucide="send"></i>
                </button>
            </form>
        </div>
    </div>

    <script>
        lucide.createIcons();

        let selectedDept = 'furnace';
        let isRangeMode = false;

        function toggleRangeMode() {{
            isRangeMode = document.getElementById('range-mode-toggle').checked;
            const singleDateSection = document.getElementById('single-date-section');
            const dateRangeSection = document.getElementById('date-range-section');

            if (isRangeMode) {{
                singleDateSection.style.display = 'none';
                dateRangeSection.style.display = 'grid';
                dateRangeSection.style.gridTemplateColumns = '1fr 1fr';
            }} else {{
                singleDateSection.style.display = 'block';
                dateRangeSection.style.display = 'none';
            }}
        }}

        function selectDept(dept) {{
            selectedDept = dept;
            document.querySelectorAll('.dept-option').forEach(el => el.classList.remove('selected'));
            const deptEl = document.querySelector(`[data-dept="${{dept}}"]`);
            if (deptEl) deptEl.classList.add('selected');
            document.getElementById('dept-select').value = dept;
            // Clear chat history when department changes (different context)
            if (typeof conversationHistory !== 'undefined') {{
                conversationHistory = [];
            }}
        }}

        // Dashboard Generation Logic
        const iframe = document.getElementById('dashboardFrame');
        const downloadBtn = document.getElementById('downloadBtn');
        const downloadMenu = document.getElementById('downloadMenu');
        const emptyState = document.getElementById('emptyState');
        const loadingOverlay = document.getElementById('loadingOverlay');
        const generateBtn = document.getElementById('generate-btn');

        // Store current dashboard info for downloads
        let currentDashboard = {{
            id: null,
            downloadUrl: null,
            dept: null,
            date: null
        }};

        // Export format availability
        let exportFormats = {{ html: true, pdf: false, excel: false }};

        // Check available export formats on page load
        fetch('/api/v1/export/formats')
            .then(res => res.json())
            .then(data => {{
                if (data.success) {{
                    data.formats.forEach(fmt => {{
                        exportFormats[fmt.id] = fmt.available;
                        const btn = document.getElementById(fmt.id + 'DownloadBtn');
                        if (btn && !fmt.available) {{
                            btn.classList.add('disabled');
                            btn.title = fmt.name + ' export not available (missing dependencies)';
                        }}
                    }});
                }}
            }})
            .catch(err => console.log('Could not fetch export formats:', err));

        function toggleDownloadMenu() {{
            if (downloadBtn.classList.contains('disabled')) return;
            downloadMenu.classList.toggle('show');
        }}

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {{
            if (!e.target.closest('.download-dropdown')) {{
                downloadMenu.classList.remove('show');
            }}
        }});

        function downloadDashboard(format) {{
            if (!currentDashboard.downloadUrl) {{
                alert('No dashboard generated yet');
                return;
            }}

            if (!exportFormats[format]) {{
                alert(format.toUpperCase() + ' export is not available. Please install required dependencies.');
                return;
            }}

            // Close the menu
            downloadMenu.classList.remove('show');

            // Build download URL with format parameter
            const downloadUrl = currentDashboard.downloadUrl + '?format=' + format;

            // For HTML, we can use direct download
            if (format === 'html') {{
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = `${{currentDashboard.dept}}_dashboard_${{currentDashboard.date}}.html`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }} else {{
                // For PDF/Excel, show loading and fetch
                const originalText = downloadBtn.innerHTML;
                downloadBtn.innerHTML = '<i data-lucide="loader-2" class="animate-spin"></i> Generating...';
                lucide.createIcons();

                fetch(downloadUrl)
                    .then(response => {{
                        if (!response.ok) {{
                            return response.json().then(err => {{
                                throw new Error(err.message || 'Export failed');
                            }});
                        }}
                        return response.blob();
                    }})
                    .then(blob => {{
                        const extension = format === 'excel' ? 'xlsx' : format;
                        const url = window.URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        link.href = url;
                        link.download = `${{currentDashboard.dept}}_dashboard_${{currentDashboard.date}}.${{extension}}`;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        window.URL.revokeObjectURL(url);
                    }})
                    .catch(err => {{
                        alert('Export failed: ' + err.message);
                        console.error('Export error:', err);
                    }})
                    .finally(() => {{
                        downloadBtn.innerHTML = originalText;
                        lucide.createIcons();
                    }});
            }}
        }}

        async function generateDashboard() {{
            const selectedDept = document.getElementById('dept-select').value;
            let apiUrl;
            let dateLabel;

            // Build API URL based on mode
            if (isRangeMode) {{
                const startDate = document.getElementById('start-date').value;
                const endDate = document.getElementById('end-date').value;

                if (!startDate || !endDate) {{
                    alert("Please select both start date and end date.");
                    return;
                }}

                if (new Date(startDate) > new Date(endDate)) {{
                    alert("Start date must be before or equal to end date.");
                    return;
                }}

                apiUrl = `/api/v1/dashboard/${{selectedDept}}?start_date=${{startDate}}&end_date=${{endDate}}`;
                dateLabel = `${{startDate}} to ${{endDate}}`;
            }} else {{
                const selectedDate = document.getElementById('dashboard-date').value;

                if (!selectedDate) {{
                    alert("Please select a date first.");
                    return;
                }}

                apiUrl = `/api/v1/dashboard/${{selectedDept}}?date=${{selectedDate}}`;
                dateLabel = selectedDate;
            }}

            // Show loading
            emptyState.style.display = 'none';
            loadingOverlay.classList.add('visible');
            iframe.classList.remove('visible');
            downloadBtn.classList.add('disabled');
            downloadMenu.classList.remove('show');
            generateBtn.disabled = true;
            currentDashboard = {{ id: null, downloadUrl: null, dept: null, date: null }};

            try {{
                const response = await fetch(apiUrl);

                if (!response.ok) {{
                    const errorData = await response.json();
                    throw new Error(errorData.message || response.statusText);
                }}

                const data = await response.json();

                if (data.success) {{
                    iframe.src = data.preview_url;

                    // Store dashboard info for downloads
                    currentDashboard = {{
                        id: data.dashboard_id,
                        downloadUrl: data.download_url,
                        dept: selectedDept,
                        date: dateLabel
                    }};

                    downloadBtn.classList.remove('disabled');

                    iframe.onload = () => {{
                        loadingOverlay.classList.remove('visible');
                        iframe.classList.add('visible');
                        generateBtn.disabled = false;
                    }}
                }} else {{
                    throw new Error(data.message || data.error || 'Unknown error');
                }}
            }} catch (err) {{
                loadingOverlay.classList.remove('visible');
                emptyState.style.display = 'block';
                emptyState.innerHTML = `
                    <div class="empty-state-icon" style="color: var(--bal-red);">
                        <i data-lucide="alert-circle"></i>
                    </div>
                    <div class="empty-state-text" style="color: var(--bal-red);">Error generating dashboard</div>
                    <div class="empty-state-subtext">${{err.message}}</div>
                `;
                lucide.createIcons();
                generateBtn.disabled = false;
                console.error('Dashboard generation error:', err);
            }}
        }}

        // Chat Modal Logic
        const chatModal = document.getElementById('chatModal');
        const chatBody = document.getElementById('chat-modal-body');
        const chatPrompt = document.getElementById('chat-prompt');
        const chatSendBtn = document.getElementById('chat-send-btn');
        let chatProcessing = false;
        let conversationHistory = [];  // Track conversation history for context

        function toggleChat() {{
            const isHidden = chatModal.style.display === "none" || chatModal.style.display === "";
            chatModal.style.display = isHidden ? "flex" : "none";
            if (isHidden) {{
                lucide.createIcons();
            }}
        }}

        async function sendChatMessage(e) {{
            e.preventDefault();
            if (chatProcessing || !chatPrompt.value.trim()) return;

            const msg = chatPrompt.value.trim();
            chatPrompt.value = '';
            addChatBubble('user', msg);
            setChatProcessing(true);

            try {{
                const response = await fetch('/api/v1/chat', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        message: msg,
                        department: selectedDept,
                        conversation_history: conversationHistory  // Send chat history for context
                    }})
                }});

                if (!response.ok) {{
                    throw new Error(`Server error: ${{response.statusText}}`);
                }}

                const data = await response.json();

                if (data.success) {{
                    // Add user message to history
                    conversationHistory.push({{ role: 'user', content: msg }});
                    // Add assistant response to history
                    conversationHistory.push({{ role: 'assistant', content: data.response }});
                    // Keep only last 10 messages (5 exchanges) to avoid token limits
                    if (conversationHistory.length > 10) {{
                        conversationHistory = conversationHistory.slice(-10);
                    }}
                    addChatBubble('assistant', data.response);
                }} else {{
                    addChatBubble('assistant', '❌ Error: ' + (data.message || data.error));
                }}
            }} catch(err) {{
                addChatBubble('assistant', '❌ Connection error: ' + err.message);
                console.error('Chat error:', err);
            }} finally {{
                setChatProcessing(false);
            }}
        }}

        function addChatBubble(role, content) {{
            const el = document.createElement('div');
            el.className = `chat-bubble ${{role}}`;
            el.innerHTML = marked.parse(content);

            // Add speaker button to assistant messages
            if (role === 'assistant' && !content.includes('Thinking...')) {{
                const speakBtn = document.createElement('button');
                speakBtn.className = 'speak-btn';
                speakBtn.innerHTML = '<i data-lucide="volume-2" style="width:14px;height:14px;"></i>';
                speakBtn.title = 'Read aloud';
                speakBtn.onclick = () => speakText(content, speakBtn);
                el.appendChild(speakBtn);
            }}

            chatBody.appendChild(el);
            chatBody.scrollTop = chatBody.scrollHeight;
            lucide.createIcons();
            return el;
        }}

        function setChatProcessing(isProcessing) {{
            chatProcessing = isProcessing;
            chatSendBtn.disabled = isProcessing;
            if (isProcessing) {{
                const thinkingBubble = addChatBubble('assistant', '🤔 Thinking...');
                thinkingBubble.id = 'thinking-bubble';
            }} else {{
                const thinkingBubble = document.getElementById('thinking-bubble');
                if (thinkingBubble) thinkingBubble.remove();
            }}
            lucide.createIcons();
        }}

        // =====================================================================
        // VOICE FEATURES (TTS & STT)
        // =====================================================================

        let mediaRecorder = null;
        let audioChunks = [];
        let isRecording = false;
        let currentAudio = null;
        let audioContext = null;
        let analyser = null;
        let animationId = null;

        const micBtn = document.getElementById('mic-btn');
        const voiceStatus = document.getElementById('voice-status');
        const voiceVisualizer = document.getElementById('voice-visualizer');
        const voiceBars = voiceVisualizer.querySelectorAll('.voice-bar');

        // Check if voice is enabled
        let voiceEnabled = false;
        fetch('/api/v1/voice/status')
            .then(res => res.json())
            .then(data => {{
                voiceEnabled = data.operational;
                if (!voiceEnabled) {{
                    micBtn.disabled = true;
                    micBtn.title = 'Voice feature not available';
                }}
            }})
            .catch(() => {{
                micBtn.disabled = true;
                micBtn.title = 'Voice feature not available';
            }});

        // STT - Speech to Text (Mic button)
        async function toggleRecording() {{
            if (!voiceEnabled) {{
                showVoiceStatus('Voice feature not enabled', 'error');
                return;
            }}

            if (isRecording) {{
                stopRecording();
            }} else {{
                startRecording();
            }}
        }}

        async function startRecording() {{
            // Check if we're on a secure context (HTTPS or localhost)
            if (!window.isSecureContext) {{
                showVoiceStatus('❌ Voice requires HTTPS or localhost', 'error');
                alert('Microphone access requires HTTPS connection or localhost.\\n\\nPlease access via:\\n- http://localhost:5100\\n- http://127.0.0.1:5100\\n- Or use HTTPS');
                return;
            }}

            // Check if getUserMedia is supported
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {{
                showVoiceStatus('❌ Browser does not support audio recording', 'error');
                return;
            }}

            try {{
                const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});

                // Set up audio visualization
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                analyser = audioContext.createAnalyser();
                const source = audioContext.createMediaStreamSource(stream);
                source.connect(analyser);
                analyser.fftSize = 32;
                startVisualization();

                // Check supported MIME types
                let mimeType = 'audio/webm';
                if (!MediaRecorder.isTypeSupported('audio/webm')) {{
                    if (MediaRecorder.isTypeSupported('audio/mp4')) {{
                        mimeType = 'audio/mp4';
                    }} else if (MediaRecorder.isTypeSupported('audio/ogg')) {{
                        mimeType = 'audio/ogg';
                    }}
                }}

                mediaRecorder = new MediaRecorder(stream, {{ mimeType: mimeType }});
                audioChunks = [];

                mediaRecorder.ondataavailable = (e) => {{
                    if (e.data.size > 0) {{
                        audioChunks.push(e.data);
                    }}
                }};

                mediaRecorder.onstop = async () => {{
                    const audioBlob = new Blob(audioChunks, {{ type: mimeType }});
                    stream.getTracks().forEach(track => track.stop());
                    stopVisualization();
                    // Extract format from mimeType (e.g., 'audio/webm' -> 'webm')
                    const format = mimeType.split('/')[1].split(';')[0];
                    await sendAudioForTranscription(audioBlob, format);
                }};

                mediaRecorder.start();
                isRecording = true;
                micBtn.classList.add('recording');
                micBtn.innerHTML = '<i data-lucide="mic-off"></i>';
                lucide.createIcons();
                showVoiceStatus('🎤 Recording... Click again to stop', 'recording');

            }} catch (err) {{
                console.error('Microphone access error:', err);

                let errorMsg = '❌ Microphone access denied';
                if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {{
                    errorMsg = '❌ Please allow microphone access in browser';
                    alert('Microphone Permission Denied\\n\\nTo enable:\\n1. Click the lock/info icon in the address bar\\n2. Find "Microphone" setting\\n3. Change to "Allow"\\n4. Refresh the page');
                }} else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {{
                    errorMsg = '❌ No microphone found';
                }} else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {{
                    errorMsg = '❌ Microphone is in use by another app';
                }}

                showVoiceStatus(errorMsg, 'error');
            }}
        }}

        // Voice level visualization
        function startVisualization() {{
            voiceVisualizer.classList.add('active');
            const dataArray = new Uint8Array(analyser.frequencyBinCount);

            function draw() {{
                animationId = requestAnimationFrame(draw);
                analyser.getByteFrequencyData(dataArray);

                // Update each bar based on frequency data
                voiceBars.forEach((bar, index) => {{
                    const value = dataArray[index % dataArray.length];
                    const height = Math.max(4, (value / 255) * 28);
                    bar.style.height = height + 'px';
                }});
            }}

            draw();
        }}

        function stopVisualization() {{
            if (animationId) {{
                cancelAnimationFrame(animationId);
                animationId = null;
            }}
            voiceVisualizer.classList.remove('active');
            voiceBars.forEach(bar => bar.style.height = '8px');
            if (audioContext) {{
                audioContext.close();
                audioContext = null;
            }}
        }}

        function stopRecording() {{
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {{
                mediaRecorder.stop();
            }}
            isRecording = false;
            micBtn.classList.remove('recording');
            micBtn.innerHTML = '<i data-lucide="mic"></i>';
            lucide.createIcons();
            showVoiceStatus('Processing audio...', 'processing');
        }}

        async function sendAudioForTranscription(audioBlob, format = 'webm') {{
            try {{
                // Convert blob to base64
                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);

                reader.onloadend = async () => {{
                    const base64Audio = reader.result;

                    const response = await fetch('/api/v1/voice/stt', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            audio_base64: base64Audio,
                            format: format
                        }})
                    }});

                    const data = await response.json();

                    if (data.success && data.transcript) {{
                        chatPrompt.value = data.transcript;
                        const langInfo = data.language_code ? ` (Detected: ${{data.language_code}})` : '';
                        showVoiceStatus('✅ Transcribed' + langInfo, 'success');
                        chatPrompt.focus();
                    }} else {{
                        showVoiceStatus('❌ ' + (data.error || 'Transcription failed'), 'error');
                    }}
                }};
            }} catch (err) {{
                console.error('STT error:', err);
                showVoiceStatus('❌ Transcription error', 'error');
            }}
        }}

        // Detect language from text using Unicode ranges (client-side)
        // Returns ISO-639-1 codes for OpenAI Whisper/TTS compatibility
        function detectTextLanguage(text) {{
            // Unicode ranges for various scripts -> ISO-639-1 codes
            const languageRanges = {{
                'hi': [0x0900, 0x097F],  // Devanagari (Hindi/Marathi)
                'bn': [0x0980, 0x09FF],  // Bengali
                'pa': [0x0A00, 0x0A7F],  // Gurmukhi (Punjabi)
                'gu': [0x0A80, 0x0AFF],  // Gujarati
                'or': [0x0B00, 0x0B7F],  // Oriya (Odia)
                'ta': [0x0B80, 0x0BFF],  // Tamil
                'te': [0x0C00, 0x0C7F],  // Telugu
                'kn': [0x0C80, 0x0CFF],  // Kannada
                'ml': [0x0D00, 0x0D7F],  // Malayalam
                'th': [0x0E00, 0x0E7F],  // Thai
                'ja': [0x3040, 0x30FF],  // Japanese (Hiragana + Katakana)
                'zh': [0x4E00, 0x9FFF],  // Chinese (CJK Unified Ideographs)
                'ko': [0xAC00, 0xD7AF],  // Korean (Hangul Syllables)
                'ar': [0x0600, 0x06FF],  // Arabic
                'he': [0x0590, 0x05FF],  // Hebrew
                'ru': [0x0400, 0x04FF],  // Russian (Cyrillic)
            }};

            const scriptCounts = {{}};
            let totalChars = 0;

            for (const char of text) {{
                const codePoint = char.charCodeAt(0);
                if (/\\s|[.,!?;:'"\\-()\\[\\]{{}}]/.test(char)) continue;
                totalChars++;

                // Check various scripts
                for (const [lang, [start, end]] of Object.entries(languageRanges)) {{
                    if (codePoint >= start && codePoint <= end) {{
                        scriptCounts[lang] = (scriptCounts[lang] || 0) + 1;
                        break;
                    }}
                }}

                // ASCII/Latin = English
                if (codePoint >= 0x0041 && codePoint <= 0x007A) {{
                    scriptCounts['en'] = (scriptCounts['en'] || 0) + 1;
                }}
            }}

            if (Object.keys(scriptCounts).length === 0) {{
                return 'en';
            }}

            // Find dominant language
            let maxLang = 'en';
            let maxCount = 0;
            for (const [lang, count] of Object.entries(scriptCounts)) {{
                if (count > maxCount) {{
                    maxCount = count;
                    maxLang = lang;
                }}
            }}

            return maxLang;
        }}

        // TTS - Text to Speech (Speaker button)
        async function speakText(text, btn) {{
            if (!voiceEnabled) {{
                showVoiceStatus('Voice feature not enabled', 'error');
                return;
            }}

            // Stop any currently playing audio
            if (currentAudio) {{
                currentAudio.pause();
                currentAudio = null;
                document.querySelectorAll('.speak-btn.playing').forEach(b => b.classList.remove('playing'));
            }}

            // Clean the text (remove markdown, emojis, etc.)
            const cleanText = text
                .replace(/[#*_`~]/g, '')
                .replace(/\\n/g, ' ')
                .replace(/\\[.*?\\]/g, '')
                .replace(/\\(.*?\\)/g, '')
                .trim();

            if (!cleanText.trim()) {{
                showVoiceStatus('No text to speak', 'error');
                return;
            }}

            // Auto-detect language from text
            const detectedLanguage = detectTextLanguage(cleanText);
            console.log('Detected language for TTS:', detectedLanguage);

            btn.disabled = true;
            btn.classList.add('playing');
            showVoiceStatus('🔊 Generating audio (' + detectedLanguage + ')...', 'processing');

            try {{
                const response = await fetch('/api/v1/voice/tts/base64', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        text: cleanText,
                        language: detectedLanguage
                    }})
                }});

                const data = await response.json();

                if (data.success && data.audio_base64) {{
                    const audio = new Audio('data:' + data.content_type + ';base64,' + data.audio_base64);
                    currentAudio = audio;

                    audio.onended = () => {{
                        btn.classList.remove('playing');
                        btn.disabled = false;
                        currentAudio = null;
                        hideVoiceStatus();
                    }};

                    audio.onerror = () => {{
                        btn.classList.remove('playing');
                        btn.disabled = false;
                        currentAudio = null;
                        showVoiceStatus('❌ Audio playback error', 'error');
                    }};

                    await audio.play();
                    showVoiceStatus('🔊 Playing (' + detectedLanguage + ')...', 'playing');
                }} else {{
                    btn.classList.remove('playing');
                    btn.disabled = false;
                    showVoiceStatus('❌ ' + (data.error || 'TTS failed'), 'error');
                }}
            }} catch (err) {{
                console.error('TTS error:', err);
                btn.classList.remove('playing');
                btn.disabled = false;
                showVoiceStatus('❌ TTS error', 'error');
            }}
        }}

        function showVoiceStatus(message, type) {{
            voiceStatus.textContent = message;
            voiceStatus.className = 'voice-status visible';

            // Auto-hide success/error messages after 3 seconds
            if (type === 'success' || type === 'error') {{
                setTimeout(hideVoiceStatus, 3000);
            }}
        }}

        function hideVoiceStatus() {{
            voiceStatus.classList.remove('visible');
        }}
    </script>
</body>
</html>
"""