"""
utils/chat_schema_builder.py

This module builds the SAFE SCHEMA for the God’s Eye Chat Proxy:
    - fetch all real tables via MCP server
    - filter by allowed prefixes
    - remove BLACKLIST_TABLES from .env
    - return final sanitized list

The Chat Proxy will pass this schema ahead to the chatbot endpoint.
"""

import os
import logging
from typing import List, Dict

from core.mcp_server import MCPServer
from utils.prefix_loader import prefix_loader

logger = logging.getLogger(__name__)


class ChatSchemaBuilder:
    def __init__(self):
        self.mcp = MCPServer()
        self.blacklist = self._load_blacklist()

    # ----------------------------------------------------
    # Load blacklist
    # ----------------------------------------------------
    def _load_blacklist(self) -> List[str]:
        """
        BLACKLIST_TABLES=table1,table2,table3
        (from .env)
        """
        csv = os.getenv("BLACKLIST_TABLES", "") or ""
        return [t.strip().lower() for t in csv.split(",") if t.strip()]

    # ----------------------------------------------------
    # Fetch all tables from DB via MCP server
    # ----------------------------------------------------
    def fetch_all_tables(self) -> List[str]:
        """
        Returns raw list of all table names.
        """
        try:
            result = self.mcp.search_tables("")  # empty = return all
            if not result or "tables" not in result:
                logger.warning("MCP returned no tables")
                return []
            return [t["name"] for t in result["tables"]]
        except Exception:
            logger.exception("Failed to fetch tables via MCP")
            return []

    # ----------------------------------------------------
    # Filter tables by allowed prefixes
    # ----------------------------------------------------
    def filter_by_prefixes(self, tables: List[str], prefixes: List[str]) -> List[str]:
        allowed = []
        for t in tables:
            t_lower = t.lower()
            for p in prefixes:
                if t_lower.startswith(p.lower()):
                    allowed.append(t)
                    break
        return allowed

    # ----------------------------------------------------
    # Remove blacklist tables
    # ----------------------------------------------------
    def apply_blacklist(self, tables: List[str]) -> List[str]:
        clean = []
        for t in tables:
            if t.lower() not in self.blacklist:
                clean.append(t)
        return clean

    # ----------------------------------------------------
    # Main entry: build safe schema
    # ----------------------------------------------------
    def build_schema_for_employee(self, employee_id: str) -> List[str]:
        """
        Returns the final filtered list of allowed TABLE NAMES for the employee.
        """
        # Step 1: allowed prefixes
        prefixes = prefix_loader.expand_employee_prefixes(employee_id)
        logger.info(f"[prefixes] {employee_id} → {prefixes}")

        # Step 2: fetch all tables
        all_tables = self.fetch_all_tables()

        # Step 3: apply prefix rules
        prefix_filtered = self.filter_by_prefixes(all_tables, prefixes)

        # Step 4: apply blacklist
        clean = self.apply_blacklist(prefix_filtered)

        logger.info(
            f"[schema] Employee {employee_id} → {len(clean)} tables after filter"
        )

        return clean


chat_schema_builder = ChatSchemaBuilder()
