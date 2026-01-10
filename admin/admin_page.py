from flask import Blueprint, render_template, g, redirect, url_for
from core.jwt_validator import require_auth, require_admin
import os

# Point to the 'templates' folder
template_dir = os.path.join(os.path.dirname(__file__), 'templates')

admin_bp = Blueprint("admin_page", __name__,
                     template_folder=template_dir,
                     url_prefix='/admin')

@admin_bp.route("/login")
def login():
    """
    Serves the public admin login page.
    This route does NOT have auth decorators, so it's accessible.
    """
    return render_template("login.html")

@admin_bp.route("/")
# --- DECORATORS REMOVED FROM HERE ---
def index():
    """
    Serves the admin log viewer page.
    The page itself is not protected, but the JavaScript
    inside it will fetch data from the protected /api/logs endpoint.
    """
    # We pass a 'None' user name, the JavaScript will fetch the real one
    # after it authenticates with the /api/logs endpoint.
    return render_template("admin.html", user_name="Admin")