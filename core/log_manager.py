import mysql.connector
import logging
from datetime import datetime
from config_modules.config import DatabaseConfig

logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Creates a new, write-enabled database connection.
    """
    try:
        conn = mysql.connector.connect(
            host=DatabaseConfig.MYSQL_HOST,
            port=DatabaseConfig.MYSQL_PORT,
            user=DatabaseConfig.MYSQL_USER,
            password=DatabaseConfig.MYSQL_PASSWORD,
            database=DatabaseConfig.MYSQL_DATABASE
        )
        return conn
    except mysql.connector.Error as err:
        logger.error(f"LogManager DB Connection Error: {err}")
        return None

def log_activity(
    employee_id: str,
    action_type: str,
    details: str = None,
    flagged: bool = False,
    dashboard_path: str = None,
    ip_address: str = None
):
    """
    Writes a new entry to the app_activity_log table.

    Args:
        employee_id (str): The ID of the user performing the action.
        action_type (str): One of 'LOGIN_SUCCESS', 'LOGIN_FAIL', 'DASHBOARD', 'CHATBOT'.
        details (str, optional): The chat query or dashboard info.
        flagged (bool, optional): Whether the AI flagged this as suspicious.
        dashboard_path (str, optional): The file path of the generated dashboard.
        ip_address (str, optional): The user's IP address.
    """

    # Ensure action_type is valid
    valid_actions = ['LOGIN_SUCCESS', 'LOGIN_FAIL', 'DASHBOARD', 'CHATBOT']
    if action_type not in valid_actions:
        logger.warning(f"Invalid log action_type: {action_type}")
        return

    conn = None
    cursor = None

    query = """
    INSERT INTO app_activity_log
    (timestamp, employee_id, action_type, details, flagged_suspicious, generated_dashboard_path, ip_address)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    try:
        conn = get_db_connection()
        if conn is None:
            raise Exception("Failed to get database connection for logging.")

        cursor = conn.cursor()

        cursor.execute(query, (
            datetime.now(),
            employee_id,
            action_type,
            details,
            flagged,
            dashboard_path,
            ip_address
        ))

        conn.commit()

    except Exception as e:
        logger.error(f"Failed to write to activity log: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()