"""
database.py
===========
MySQL database query layer built on top of MCP Server.

This module provides:
- Convenient wrapper methods for EAV and normalized table queries
- Query execution delegated to MCPServer (read-only enforced there)
- Maintains consistency with existing chatbot architecture

CRITICAL: All queries go through MCPServer which enforces READ-ONLY mode
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

from core.mcp_server import MCPServer
from config_modules.config import DatabaseConfig

# ============================================================================
# LOGGING SETUP
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# CORE DATABASE CLASS (BUILT ON MCP SERVER)
# ============================================================================

class Database:
    """
    Main database interface for querying MySQL.

    This class wraps MCPServer and provides convenient methods for:
    - EAV table queries
    - Normalized table queries
    - Generic SQL execution

    All queries are executed through MCPServer which enforces:
    - Read-only mode (contractual requirement)
    - Query validation
    - Security checks
    """

    def __init__(self):
        """Initialize database interface with MCPServer"""
        # Use existing MCP Server (already has connection pooling and read-only validation)
        self.mcp = MCPServer()
        logger.info("✅ Database initialized using MCPServer")

    # ========================================================================
    # GENERIC QUERY EXECUTION (DELEGATES TO MCP)
    # ========================================================================

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch_one: bool = False,
        database: str = None
    ) -> Dict[str, Any]:
        """
        Execute a SQL query and return results.

        This method delegates to MCPServer.query() which handles:
        - Read-only validation
        - Query execution
        - Result serialization

        Args:
            query: SQL query string (can use %s placeholders)
            params: Query parameters (for prepared statements)
            fetch_one: If True, return only first row
            database: Database name (defaults to config database)

        Returns:
            Dictionary with:
                - success: bool
                - data: List of row dictionaries (or single dict if fetch_one)
                - columns: List of column names
                - count: Number of rows
                - error: Error message if failed
        """
        # Format query with parameters if provided
        if params:
            # MCPServer expects fully formatted SQL (doesn't use parameterized queries)
            # So we need to safely substitute parameters
            try:
                # Convert tuple to list for easier manipulation
                param_list = list(params)
                formatted_query = query

                # Replace %s placeholders with properly escaped values
                for param in param_list:
                    if param is None:
                        replacement = "NULL"
                    elif isinstance(param, str):
                        # Escape single quotes and wrap in quotes
                        replacement = f"'{param.replace(chr(39), chr(39)+chr(39))}'"
                    else:
                        replacement = str(param)

                    formatted_query = formatted_query.replace("%s", replacement, 1)

                query = formatted_query

            except Exception as e:
                logger.error(f"Error formatting query parameters: {e}")
                return {
                    "success": False,
                    "error": f"Parameter formatting error: {str(e)}",
                    "data": [],
                    "columns": [],
                    "count": 0
                }

        # Execute through MCP Server (which validates read-only)
        db_name = database or DatabaseConfig.MYSQL_DATABASE
        result = self.mcp.query(query, db_name)

        # MCP returns: {"success": bool, "data": [], "columns": [], "count": int, "error": str}
        # This matches our expected format!

        # Handle fetch_one
        if fetch_one and result.get("success") and result.get("data"):
            result["data"] = result["data"][0] if len(result["data"]) > 0 else None
            result["count"] = 1 if result["data"] else 0

        return result

    # ========================================================================
    # EAV TABLE QUERIES
    # ========================================================================

    def query_eav_table(
        self,
        table_name: str,
        date: str,
        kpi_category: str,
        func_plant: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query an EAV (Entity-Attribute-Value) table.

        EAV tables have structure:
        - DATE: Date column
        - FUNC_PLANT: Plant/location
        - KPI_DESC: KPI category
        - ATTRIBUTE_NAME: Attribute name
        - ATTRIBUTE_VALUE: Attribute value
        - UOM: Unit of measurement

        Args:
            table_name: Name of EAV table
            date: Date to query (YYYY-MM-DD format)
            kpi_category: Value of KPI_DESC to filter
            func_plant: Optional plant filter

        Returns:
            Query result dictionary
        """
        # Build query
        query = f"""
            SELECT
                DATE,
                FUNC_PLANT,
                KPI_DESC,
                ATTRIBUTE_NAME,
                ATTRIBUTE_VALUE,
                UOM,
                ENTRY_ID,
                ENTRY_DATE,
                UPDATED_DATE,
                STATUS
            FROM {table_name}
            WHERE DATE(DATE) = %s
            AND KPI_DESC = %s
        """

        params = [date, kpi_category]

        # Add plant filter if specified
        if func_plant:
            query += " AND FUNC_PLANT = %s"
            params.append(func_plant)

        # Order by attribute name for consistent results
        query += " ORDER BY ATTRIBUTE_NAME"

        logger.info(
            f"Querying EAV table: {table_name}, "
            f"Date: {date}, KPI: {kpi_category}, Plant: {func_plant}"
        )

        return self.execute_query(query, tuple(params))

    def get_all_kpi_categories(
        self,
        table_name: str,
        date: str,
        func_plant: Optional[str] = None
    ) -> List[str]:
        """
        Get all available KPI categories for a date in an EAV table.

        Args:
            table_name: Name of EAV table
            date: Date to query
            func_plant: Optional plant filter

        Returns:
            List of unique KPI_DESC values
        """
        query = f"""
            SELECT DISTINCT KPI_DESC
            FROM {table_name}
            WHERE DATE(DATE) = %s
        """

        params = [date]

        if func_plant:
            query += " AND FUNC_PLANT = %s"
            params.append(func_plant)

        query += " ORDER BY KPI_DESC"

        result = self.execute_query(query, tuple(params))

        if result["success"]:
            return [row["KPI_DESC"] for row in result["data"]]
        else:
            return []

    # ========================================================================
    # NORMALIZED TABLE QUERIES
    # ========================================================================

    def query_normalized_table(
        self,
        table_name: str,
        date: str,
        date_column: str = "DATE",
        columns: Optional[List[str]] = None,
        func_plant: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query a normalized (regular) table.

        Args:
            table_name: Name of table
            date: Date to query (YYYY-MM-DD format)
            date_column: Name of date column to filter on
            columns: Specific columns to select (None = all)
            func_plant: Optional plant filter

        Returns:
            Query result dictionary
        """
        # Build SELECT clause
        if columns:
            select_clause = ", ".join(columns)
        else:
            select_clause = "*"

        # Build query
        query = f"""
            SELECT {select_clause}
            FROM {table_name}
            WHERE DATE({date_column}) = %s
        """

        params = [date]

        # Add plant filter if table has FUNC_PLANT column
        if func_plant:
            query += " AND FUNC_PLANT = %s"
            params.append(func_plant)

        logger.info(
            f"Querying normalized table: {table_name}, "
            f"Date: {date}, Plant: {func_plant}"
        )

        return self.execute_query(query, tuple(params))

    # ========================================================================
    # EAV TABLE QUERIES (USING MCP)
    # ========================================================================

    def query_eav_table(
        self,
        table_name: str,
        date: str,
        kpi_category: str,
        func_plant: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query an EAV (Entity-Attribute-Value) table.

        EAV tables have structure:
        - DATE: Date column
        - FUNC_PLANT: Plant/location
        - KPI_DESC: KPI category
        - ATTRIBUTE_NAME: Attribute name
        - ATTRIBUTE_VALUE: Attribute value
        - UOM: Unit of measurement

        Args:
            table_name: Name of EAV table
            date: Date to query (YYYY-MM-DD format)
            kpi_category: Value of KPI_DESC to filter
            func_plant: Optional plant filter

        Returns:
            Query result dictionary (from MCPServer)
        """
        # Build query
        query = f"""
            SELECT
                DATE,
                FUNC_PLANT,
                KPI_DESC,
                ATTRIBUTE_NAME,
                ATTRIBUTE_VALUE,
                UOM,
                ENTRY_ID,
                ENTRY_DATE,
                UPDATED_DATE,
                STATUS
            FROM {table_name}
            WHERE DATE(DATE) = '{date}'
            AND KPI_DESC = '{kpi_category.replace("'", "''")}'
        """

        # Add plant filter if specified
        if func_plant:
            query += f" AND FUNC_PLANT = '{func_plant.replace(chr(39), chr(39)+chr(39))}'"

        # Order by attribute name for consistent results
        query += " ORDER BY ATTRIBUTE_NAME"

        logger.info(
            f"Querying EAV table via MCP: {table_name}, "
            f"Date: {date}, KPI: {kpi_category}, Plant: {func_plant}"
        )

        # Execute through MCP (read-only validation happens here)
        return self.execute_query(query)

    def get_all_kpi_categories(
        self,
        table_name: str,
        date: str,
        func_plant: Optional[str] = None
    ) -> List[str]:
        """
        Get all available KPI categories for a date in an EAV table.

        Args:
            table_name: Name of EAV table
            date: Date to query
            func_plant: Optional plant filter

        Returns:
            List of unique KPI_DESC values
        """
        query = f"""
            SELECT DISTINCT KPI_DESC
            FROM {table_name}
            WHERE DATE(DATE) = '{date}'
        """

        if func_plant:
            query += f" AND FUNC_PLANT = '{func_plant.replace(chr(39), chr(39)+chr(39))}'"

        query += " ORDER BY KPI_DESC"

        result = self.execute_query(query)

        if result["success"]:
            return [row["KPI_DESC"] for row in result["data"]]
        else:
            return []

    # ========================================================================
    # NORMALIZED TABLE QUERIES (USING MCP)
    # ========================================================================

    def query_normalized_table(
        self,
        table_name: str,
        date: str,
        date_column: str = "DATE",
        columns: Optional[List[str]] = None,
        func_plant: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query a normalized (regular) table.

        Args:
            table_name: Name of table
            date: Date to query (YYYY-MM-DD format)
            date_column: Name of date column to filter on
            columns: Specific columns to select (None = all)
            func_plant: Optional plant filter

        Returns:
            Query result dictionary (from MCPServer)
        """
        # Build SELECT clause
        if columns:
            select_clause = ", ".join(columns)
        else:
            select_clause = "*"

        # Build query
        query = f"""
            SELECT {select_clause}
            FROM {table_name}
            WHERE DATE({date_column}) = '{date}'
        """

        # Add plant filter if table has FUNC_PLANT column
        if func_plant:
            query += f" AND FUNC_PLANT = '{func_plant.replace(chr(39), chr(39)+chr(39))}'"

        logger.info(
            f"Querying normalized table via MCP: {table_name}, "
            f"Date: {date}, Plant: {func_plant}"
        )

        # Execute through MCP (read-only validation happens here)
        return self.execute_query(query)

    def check_table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of table to check

        Returns:
            True if table exists, False otherwise
        """
        # Use MCP's inspect method (it checks if table exists)
        result = self.mcp.inspect(table_name, DatabaseConfig.MYSQL_DATABASE)
        return result.get("success", False)

    def get_table_columns(self, table_name: str) -> List[str]:
        """
        Get list of columns in a table.

        Args:
            table_name: Name of table

        Returns:
            List of column names
        """
        # Use MCP's inspect method
        result = self.mcp.inspect(table_name, DatabaseConfig.MYSQL_DATABASE)

        if result.get("success") and result.get("schema"):
            columns = result["schema"].get("columns", [])
            return [col["name"] for col in columns]
        return []

    def test_connection(self) -> bool:
        """
        Test database connectivity.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Use MCP's discover method as a connection test
            result = self.mcp.discover()
            if result.get("success"):
                logger.info("✅ Database connection test successful (via MCP)")
                return True
            else:
                logger.error(f"❌ Database connection test failed: {result.get('error')}")
                return False
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

# Create a singleton instance for easy import
db = Database()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def execute_query(query: str, params: Optional[Tuple] = None) -> Dict[str, Any]:
    """Convenience function for executing queries"""
    return db.execute_query(query, params)


def query_eav(
    table: str,
    date: str,
    kpi: str,
    plant: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function for EAV queries"""
    return db.query_eav_table(table, date, kpi, plant)


def query_normalized(
    table: str,
    date: str,
    date_column: str = "DATE",
    plant: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function for normalized table queries"""
    return db.query_normalized_table(table, date, date_column, None, plant)


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

def initialize_database():
    """Initialize database interface (using MCPServer)"""
    database = Database()

    # Test connection
    if not database.test_connection():
        logger.warning("⚠️  Database connection test failed during initialization")

    return database


# ============================================================================
# CLEANUP
# ============================================================================

def cleanup():
    """Cleanup database connections (handled by MCPServer)"""
    # MCPServer manages its own connections
    logger.info("Database cleanup complete (MCPServer handles connection management)")


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "Database",
    "db",
    "execute_query",
    "query_eav",
    "query_normalized",
    "initialize_database",
    "cleanup"
]


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test database connectivity and basic queries using MCPServer"""
    print("=" * 70)
    print("DATABASE CONNECTION TEST (Using MCPServer)")
    print("=" * 70)

    # Initialize
    database = initialize_database()

    # Test connection
    print("\n1. Testing connection...")
    if database.test_connection():
        print("   ✅ Connection successful via MCPServer")
    else:
        print("   ❌ Connection failed")
        exit(1)

    # Test table existence
    print("\n2. Checking if env_kpi_transaction exists...")
    if database.check_table_exists("env_kpi_transaction"):
        print("   ✅ Table exists")

        # Get columns
        print("\n3. Getting table columns...")
        columns = database.get_table_columns("env_kpi_transaction")
        print(f"   Columns ({len(columns)}): {', '.join(columns)}")

        # Test query (get available KPI categories for a recent date)
        print("\n4. Testing EAV query...")
        categories = database.get_all_kpi_categories(
            "env_kpi_transaction",
            "2025-08-20",  # Use a date from your sample data
            "Balgopalpur"
        )
        print(f"   Found {len(categories)} KPI categories:")
        for cat in categories:
            print(f"     - {cat}")

        # Test specific KPI query
        if categories:
            print(f"\n5. Querying data for '{categories[0]}'...")
            result = database.query_eav_table(
                "env_kpi_transaction",
                "2025-08-20",
                categories[0],
                "Balgopalpur"
            )
            if result["success"]:
                print(f"   ✅ Found {result['count']} rows")
                if result["count"] > 0:
                    print(f"   Sample row: {result['data'][0]}")
            else:
                print(f"   ❌ Query failed: {result['error']}")
    else:
        print("   ❌ Table not found")

    # Verify read-only mode
    print("\n6. Testing read-only enforcement...")
    bad_query = "UPDATE env_kpi_transaction SET STATUS = '0'"
    result = database.execute_query(bad_query)
    if not result["success"] and "forbidden" in result.get("error", "").lower():
        print("   ✅ Read-only mode enforced by MCPServer")
    else:
        print("   ⚠️  Read-only check unexpected result")

    # Cleanup
    print("\n" + "=" * 70)
    cleanup()
    print("✅ Database test complete!")
    print("\n📝 NOTE: All queries executed through MCPServer")
    print("   - Read-only validation: ✅ Enforced by MCP")
    print("   - Connection pooling: ✅ Handled by MCP")
    print("   - Security checks: ✅ Handled by MCP")

# ============================================================================
# ALIAS FOR BACKWARD COMPATIBILITY
# ============================================================================

# Alias for dashboard_api.py imports
DatabaseConnector = Database