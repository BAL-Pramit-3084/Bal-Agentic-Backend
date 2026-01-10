import sys
import mysql.connector
from getpass import getpass
from werkzeug.security import generate_password_hash
from config_modules.config import DatabaseConfig

def create_admin_user():
    print("--- Create Balasore Alloys Admin User ---")

    try:
        employee_id = input("Enter Employee ID for Admin: ").strip()
        full_name = input("Enter Full Name for Admin: ").strip()
        password = getpass("Enter Password for Admin: ")
        password_confirm = getpass("Confirm Password: ")

        if not employee_id or not full_name:
            print("\n❌ Error: Employee ID and Full Name cannot be empty.")
            return

        if password != password_confirm:
            print("\n❌ Error: Passwords do not match.")
            return

        if not password:
            print("\n❌ Error: Password cannot be empty.")
            return

        hashed_password = generate_password_hash(password)

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
            cursor = conn.cursor()

            query = """
            INSERT INTO app_users (employee_id, full_name, hashed_password, role)
            VALUES (%s, %s, %s, 'admin')
            ON DUPLICATE KEY UPDATE
                full_name = VALUES(full_name),
                hashed_password = VALUES(hashed_password),
                role = VALUES(role)
            """

            cursor.execute(query, (employee_id, full_name, hashed_password))
            conn.commit()

            if cursor.rowcount > 0:
                print(f"\n✅ Success! Admin user '{full_name}' ({employee_id}) was created or updated.")
            else:
                print("\n⚠️  No changes made to the database.")

        except mysql.connector.Error as err:
            print(f"\n❌ Database Error: {err}")
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    create_admin_user()