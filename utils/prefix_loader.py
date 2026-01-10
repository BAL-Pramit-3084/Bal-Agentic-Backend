"""
utils/prefix_loader.py

Prefix Loader for God’s Eye System
-----------------------------------

This module expands department access tokens (like "env", "mining", "security", "all")
into actual table prefixes defined in the department_master table.

Provides:
    - load_prefixes_for_department(token)
    - expand_employee_prefixes(employee_id)
    - expand_all_prefixes()

This connects directly to MySQL using DatabaseConfig, consistent with DAO behavior.
"""

import logging
import mysql.connector
from typing import List, Dict

from config_modules.config import DatabaseConfig
from permissions.department_access_dao import department_access_dao

logger = logging.getLogger(__name__)


class PrefixLoader:
    def __init__(self):
        self._conn_params = DatabaseConfig.get_connection_params()

    # -------------------------------------------------------
    # Internal MySQL connector (read-only operations)
    # -------------------------------------------------------
    def _get_connection(self):
        return mysql.connector.connect(
            host=self._conn_params.get("host"),
            port=self._conn_params.get("port"),
            user=self._conn_params.get("user"),
            password=self._conn_params.get("password"),
            database=self._conn_params.get("database"),
            charset=self._conn_params.get("charset", "utf8mb4"),
            use_unicode=self._conn_params.get("use_unicode", True),
        )

    # -------------------------------------------------------
    # Load all department master rows into a dict
    # -------------------------------------------------------
    def _load_department_map(self) -> Dict[str, List[str]]:
        """
        Returns dict:
            {
                "env": ["kpi_env_", "safety_"],
                "mining": ["mines_"],
                "furnace": ["furnace_", "furnace1_", ...]
            }
        """
        q = "SELECT dept_name, dept_short_name, table_prefixes FROM department_master"

        result = {}
        conn = None
        cursor = None

        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(q)

            for row in cursor.fetchall():
                # Token key must be dept_short_name
                key = row.get("dept_short_name")
                if not key:
                    continue

                prefixes_csv = row.get("table_prefixes") or ""
                prefixes_list = [
                    p.strip()
                    for p in prefixes_csv.split(",")
                    if p.strip()
                ]

                result[key] = prefixes_list

            return result

        except Exception:
            logger.exception("Failed loading department_master")
            return {}

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # -------------------------------------------------------
    # Expand single department token
    # -------------------------------------------------------
    def load_prefixes_for_department(self, token: str) -> List[str]:
        """
        Convert a single department token ("env") into prefix list ("kpi_env_", "safety_").
        """
        dept_map = self._load_department_map()
        return dept_map.get(token, [])

    # -------------------------------------------------------
    # Expand prefixes for employee
    # -------------------------------------------------------
    def expand_employee_prefixes(self, employee_id: str) -> List[str]:
        """
        Convert all allowed dept tokens for the employee into table prefixes.

        If "all" is present → expand all department prefixes.
        """
        tokens = department_access_dao.fetch_allowed_prefixes_for_employee(employee_id)

        # If MD/CEO
        if "all" in tokens:
            all_prefixes = self.expand_all_prefixes()
            return all_prefixes

        prefixes: List[str] = []
        dept_map = self._load_department_map()

        for token in tokens:
            if token in dept_map:
                prefixes.extend(dept_map[token])

        # Deduplicate
        seen = set()
        final = []
        for p in prefixes:
            if p not in seen:
                seen.add(p)
                final.append(p)

        return final

    # -------------------------------------------------------
    # Expand all prefixes (MD/CEO)
    # -------------------------------------------------------
    def expand_all_prefixes(self) -> List[str]:
        dept_map = self._load_department_map()
        combined = []

        for key, list_prefixes in dept_map.items():
            combined.extend(list_prefixes)

        # Deduplicate
        seen = set()
        final = []
        for p in combined:
            if p not in seen:
                seen.add(p)
                final.append(p)

        return final


# Singleton instance for imports
prefix_loader = PrefixLoader()
