"""
MCP Server - Database operations
Simplified version of your existing MCP server, but as a regular Python module
"""

import os
import json
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class MCPServer:
    """Database service with all MCP functionality"""

    def __init__(self):
        self.db_config = {
            "host": os.getenv("MYSQL_HOST"),
            "port": int(os.getenv("MYSQL_PORT", 3306)),
            "user": os.getenv("MYSQL_USER"),
            "password": os.getenv("MYSQL_PASSWORD"),
            "database": os.getenv("MYSQL_DATABASE")
        }
        logger.info(f"MCP Server initialized for {self.db_config['host']}")

    def get_connection(self, database: Optional[str] = None):
        """Get MySQL connection"""
        config = self.db_config.copy()
        if database:
            config["database"] = database
        elif not config.get("database"):
            config.pop("database", None)
        return mysql.connector.connect(**config)

    def validate_select_query(self, query: str) -> tuple[bool, str]:
        """Validate that query is read-only"""
        q = query.strip().lower()
        allowed_starts = ["select", "show", "describe", "desc", "explain", "with"]
        if not any(q.startswith(start) for start in allowed_starts):
            return False, "Only SELECT, SHOW, DESCRIBE, and EXPLAIN queries are allowed"

        forbidden = ["update ", "delete ", "insert ", "drop ", "alter ", "truncate ",
                    "create ", "grant ", "revoke ", "exec ", "execute "]
        for kw in forbidden:
            if kw in q:
                return False, f"Query contains forbidden keyword: {kw.strip()}"

        return True, ""

    def serialize_value(self, value):
        """Convert MySQL values to JSON-serializable format"""
        if value is None:
            return None
        elif isinstance(value, (datetime, date)):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, bytes):
            return value.decode('utf-8', errors='replace')
        return value

    def discover(self) -> Dict[str, Any]:
        """Discover all databases"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("SHOW DATABASES")
            databases = [row[0] for row in cursor.fetchall()]

            database_info = []
            for db in databases:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '{db}'")
                    table_count = cursor.fetchone()[0]

                    cursor.execute(f"""
                        SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2)
                        FROM information_schema.tables WHERE table_schema = '{db}'
                    """)
                    size_mb = cursor.fetchone()[0] or 0

                    database_info.append({
                        "name": db,
                        "table_count": table_count,
                        "size_mb": float(size_mb)
                    })
                except Error as e:
                    logger.warning(f"Error accessing {db}: {e}")

            return {"success": True, "databases": database_info, "error": None}
        except Error as e:
            logger.error(f"Error discovering databases: {e}")
            return {"success": False, "databases": [], "error": str(e)}
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def search_tables(self, search_term: str = "", database: Optional[str] = None) -> Dict[str, Any]:
        """Search for tables"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)

            where_clauses = []
            if search_term:
                where_clauses.append(
                    f"(LOWER(t.table_name) LIKE LOWER('%{search_term}%'))"
                )

            if database:
                where_clauses.append(f"t.table_schema = '{database}'")
            elif self.db_config.get("database"):
                where_clauses.append(f"t.table_schema = '{self.db_config['database']}'")

            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

            query = f"""
                SELECT
                    t.table_schema as database_name,
                    t.table_name,
                    t.table_rows as estimated_rows,
                    ROUND((t.data_length + t.index_length) / 1024 / 1024, 2) as size_mb
                FROM information_schema.tables t
                WHERE {where_clause}
                ORDER BY t.table_schema, t.table_name
                LIMIT 100
            """

            cursor.execute(query)
            tables = cursor.fetchall()

            result_tables = []
            for table in tables:
                t = {k.lower(): v for k, v in table.items()}
                result_tables.append({
                    "database": t.get("database_name") or t.get("table_schema"),
                    "name": t.get("table_name"),
                    "rows": t.get("estimated_rows", 0) or 0,
                    "size_mb": float(t.get("size_mb", 0) or 0)
                })

            return {"success": True, "tables": result_tables, "error": None}
        except Error as e:
            logger.error(f"Error searching tables: {e}")
            return {"success": False, "tables": [], "error": str(e)}
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def inspect(self, table: str, database: Optional[str] = None) -> Dict[str, Any]:
        """Get table schema"""
        conn = None
        cursor = None
        try:
            db_to_use = database or self.db_config.get("database")
            if not db_to_use:
                return {"success": False, "error": "No database specified"}

            conn = self.get_connection(db_to_use)
            cursor = conn.cursor(dictionary=True)

            # Get columns
            cursor.execute(f"""
                SELECT
                    COLUMN_NAME as name,
                    COLUMN_TYPE as type,
                    IS_NULLABLE as nullable,
                    COLUMN_KEY as key_type
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = '{db_to_use}' AND TABLE_NAME = '{table}'
                ORDER BY ORDINAL_POSITION
            """)
            columns = cursor.fetchall()

            if not columns:
                return {"success": False, "error": f"Table '{table}' not found"}

            # Get row count
            cursor.execute(f"SELECT COUNT(*) as count FROM `{db_to_use}`.`{table}`")
            row_count = cursor.fetchone()['count']

            return {
                "success": True,
                "schema": {
                    "database": db_to_use,
                    "table": table,
                    "columns": [
                        {
                            "name": col["name"],
                            "type": col["type"],
                            "nullable": col["nullable"] == "YES",
                            "key": col["key_type"] if col["key_type"] else None
                        } for col in columns
                    ],
                    "row_count": row_count
                },
                "error": None
            }
        except Error as e:
            logger.error(f"Error inspecting table: {e}")
            return {"success": False, "schema": None, "error": str(e)}
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def sample(self, table: str, database: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Get sample data from table"""
        db_to_use = database or self.db_config.get("database")
        if not db_to_use:
            return {"success": False, "error": "No database specified"}

        conn = None
        cursor = None
        try:
            conn = self.get_connection(db_to_use)
            cursor = conn.cursor(dictionary=True)

            cursor.execute(f"SELECT * FROM `{db_to_use}`.`{table}` LIMIT {limit}")
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()

            converted_rows = [
                {key: self.serialize_value(value) for key, value in row.items()}
                for row in rows
            ]

            return {
                "success": True,
                "columns": columns,
                "data": converted_rows,
                "error": None
            }
        except Error as e:
            logger.error(f"Error sampling table: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def query(self, sql: str, database: Optional[str] = None) -> Dict[str, Any]:
        """Execute SQL query"""
        is_valid, error_msg = self.validate_select_query(sql)
        if not is_valid:
            return {"success": False, "error": error_msg, "data": [], "columns": []}

        db_to_use = database or self.db_config.get("database")
        conn = None
        cursor = None
        try:
            conn = self.get_connection(db_to_use)
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql)

            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()

            converted_rows = [
                {key: self.serialize_value(value) for key, value in row.items()}
                for row in rows
            ]

            return {
                "success": True,
                "data": converted_rows,
                "columns": columns,
                "count": len(converted_rows),
                "error": None
            }
        except Error as e:
            logger.error(f"Database error: {e}")
            return {"success": False, "error": str(e), "data": [], "columns": []}
        finally:
            if cursor: cursor.close()
            if conn: conn.close()