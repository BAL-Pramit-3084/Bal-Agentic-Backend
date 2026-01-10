"""
permissions/department_access_dao.py

DAO for managing department_access table.

Provides:
- create_request
- approve_request
- reject_request
- activate_request (set active=1)
- revoke_request (set active=0)
- expire_guests (expire guest access based on guest_days + granted_at)
- get_request_by_id
- list_pending_requests
- list_active_requests_for_employee
- fetch_allowed_prefixes_for_employee
- fetch_active_department_rows_for_employee

NOTE: This module uses mysql.connector for write operations. It uses
      DatabaseConfig.get_connection_params() from config.py for connection params.
"""

import logging
from typing import Optional, List, Dict, Any
import mysql.connector
from datetime import datetime, timedelta

from config_modules.config import DatabaseConfig

logger = logging.getLogger(__name__)


class DepartmentAccessDAO:
    """
    Data Access Object for department_access table.
    """

    def __init__(self):
        self._conn_params = DatabaseConfig.get_connection_params()

    # ---------------------------
    # Internal helpers
    # ---------------------------
    def _get_connection(self):
        return mysql.connector.connect(
            host=self._conn_params.get("host"),
            port=self._conn_params.get("port"),
            user=self._conn_params.get("user"),
            password=self._conn_params.get("password"),
            database=self._conn_params.get("database"),
            charset=self._conn_params.get("charset", "utf8mb4"),
            use_unicode=self._conn_params.get("use_unicode", True),
            autocommit=False
        )

    # ---------------------------
    # CRUD / Business methods
    # ---------------------------
    def create_request(
        self,
        employee_id: str,
        requested_dept_access: str,
        access_type: str = "guest",
        guest_days: int = 2,
        dept_id: Optional[int] = None,
        designation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new access request row in department_access.

        Returns dict: {success: bool, request_id: int|None, error: str|None}
        """
        q = """
        INSERT INTO department_access
        (employee_id, dept_id, designation, requested_dept_access, access_type, guest_days, status, active, requested_at)
        VALUES (%s, %s, %s, %s, %s, %s, 'pending', 0, NOW())
        """
        params = (
            employee_id,
            dept_id,
            designation,
            requested_dept_access,
            access_type,
            guest_days
        )

        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(q, params)
            request_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Created department_access request_id={request_id} for employee={employee_id}")
            return {"success": True, "request_id": request_id, "error": None}
        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            logger.exception("DB error while creating department_access request")
            return {"success": False, "request_id": None, "error": str(err)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_request_by_id(self, request_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a single request row by request_id.
        Returns row dict or None.
        """
        q = "SELECT * FROM department_access WHERE request_id = %s"
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(q, (request_id,))
            row = cursor.fetchone()
            return row
        except mysql.connector.Error:
            logger.exception("DB error fetching department_access by id")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def list_pending_requests(self, limit: int = 200) -> List[Dict[str, Any]]:
        """
        Return pending requests for admin review.
        """
        q = "SELECT * FROM department_access WHERE status = 'pending' ORDER BY requested_at ASC LIMIT %s"
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(q, (limit,))
            rows = cursor.fetchall() or []
            return rows
        except mysql.connector.Error:
            logger.exception("DB error listing pending department_access requests")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def list_active_requests_for_employee(self, employee_id: str) -> List[Dict[str, Any]]:
        """
        Return active (active=1 and status=approved) requests for an employee.
        """
        q = "SELECT * FROM department_access WHERE employee_id = %s AND active = 1 AND status = 'approved' ORDER BY granted_at DESC"
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(q, (employee_id,))
            rows = cursor.fetchall() or []
            return rows
        except mysql.connector.Error:
            logger.exception("DB error listing active requests for employee")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def approve_request(self, request_id: int, reviewer_id: str) -> Dict[str, Any]:
        """
        Approve a pending request:
        - set status='approved', active=1, granted_at=NOW(), reviewed_by, reviewed_at=NOW()

        Returns dict with success and optionally error.
        """
        q = """
        UPDATE department_access
        SET status = 'approved',
            active = 1,
            granted_at = NOW(),
            reviewed_by = %s,
            reviewed_at = NOW()
        WHERE request_id = %s AND status = 'pending'
        """
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(q, (reviewer_id, request_id))
            if cursor.rowcount == 0:
                conn.rollback()
                return {"success": False, "error": "No matching pending request or already processed."}
            conn.commit()
            logger.info(f"Approved department_access request_id={request_id} by reviewer={reviewer_id}")
            return {"success": True, "error": None}
        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            logger.exception("DB error approving department_access request")
            return {"success": False, "error": str(err)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def reject_request(self, request_id: int, reviewer_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Reject a pending request:
        - set status='rejected', active=0, reviewed_by, reviewed_at=NOW()
        Optionally store reason in designation column or another column if you want to persist reason.
        """
        q = """
        UPDATE department_access
        SET status = 'rejected',
            active = 0,
            reviewed_by = %s,
            reviewed_at = NOW()
        WHERE request_id = %s AND status = 'pending'
        """
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(q, (reviewer_id, request_id))
            if cursor.rowcount == 0:
                conn.rollback()
                return {"success": False, "error": "No matching pending request or already processed."}
            conn.commit()
            logger.info(f"Rejected department_access request_id={request_id} by reviewer={reviewer_id}")
            # NOTE: if you want to persist 'reason', add a column (e.g., review_reason) and update above.
            return {"success": True, "error": None}
        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            logger.exception("DB error rejecting department_access request")
            return {"success": False, "error": str(err)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def revoke_request(self, request_id: int, reviewer_id: str) -> Dict[str, Any]:
        """
        Revoke an approved/active request (set active=0). Do not change status field here,
        but optionally set status='rejected' if you prefer. We update reviewed_by/reviewed_at.
        """
        q = """
        UPDATE department_access
        SET active = 0,
            reviewed_by = %s,
            reviewed_at = NOW()
        WHERE request_id = %s AND active = 1
        """
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(q, (reviewer_id, request_id))
            if cursor.rowcount == 0:
                conn.rollback()
                return {"success": False, "error": "No matching active request to revoke."}
            conn.commit()
            logger.info(f"Revoked department_access request_id={request_id} by reviewer={reviewer_id}")
            return {"success": True, "error": None}
        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            logger.exception("DB error revoking department_access request")
            return {"success": False, "error": str(err)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def activate_request(self, request_id: int, reviewer_id: str) -> Dict[str, Any]:
        """
        Force-activate a request regardless of its previous status (useful for admin override).
        Sets status='approved', active=1, granted_at, reviewed_by, reviewed_at.
        """
        q = """
        UPDATE department_access
        SET status = 'approved',
            active = 1,
            granted_at = NOW(),
            reviewed_by = %s,
            reviewed_at = NOW()
        WHERE request_id = %s
        """
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(q, (reviewer_id, request_id))
            if cursor.rowcount == 0:
                conn.rollback()
                return {"success": False, "error": "Request not found."}
            conn.commit()
            logger.info(f"Activated department_access request_id={request_id} by reviewer={reviewer_id}")
            return {"success": True, "error": None}
        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            logger.exception("DB error activating department_access request")
            return {"success": False, "error": str(err)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def expire_guests(self) -> Dict[str, Any]:
        """
        Expire guest access rows where guest_days elapsed since granted_at.
        - Only affects rows where access_type='guest', status='approved' and active=1.
        Returns summary dict: {success: bool, expired_count: int, error: str|None}
        """
        q = """
        UPDATE department_access
        SET active = 0
        WHERE access_type = 'guest'
          AND status = 'approved'
          AND active = 1
          AND (granted_at IS NOT NULL)
          AND (DATE_ADD(granted_at, INTERVAL COALESCE(guest_days,0) DAY) <= NOW())
        """
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(q)
            expired = cursor.rowcount
            conn.commit()
            logger.info(f"Expired {expired} guest department_access rows")
            return {"success": True, "expired_count": expired, "error": None}
        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            logger.exception("DB error expiring guest department_access rows")
            return {"success": False, "expired_count": 0, "error": str(err)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # ---------------------------
    # Helper fetches used by backend expansion logic
    # ---------------------------
    def fetch_active_department_rows_for_employee(self, employee_id: str) -> List[Dict[str, Any]]:
        """
        Returns all department_access rows (approved & active) for an employee.
        """
        q = "SELECT * FROM department_access WHERE employee_id = %s AND status = 'approved' AND active = 1"
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(q, (employee_id,))
            rows = cursor.fetchall() or []
            return rows
        except mysql.connector.Error:
            logger.exception("DB error fetching active department_access rows for employee")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def fetch_allowed_prefixes_for_employee(self, employee_id: str) -> List[str]:
        """
        Expand the employee's active department_access rows into a deduplicated
        list of requested_dept_access tokens (CSV may be present) or 'all'.

        NOTE: This returns raw tokens (e.g., ['env','mining','all']) which
              should be later expanded by reading department_master.table_prefixes.
        """
        rows = self.fetch_active_department_rows_for_employee(employee_id)
        prefixes = []
        for r in rows:
            token = r.get("requested_dept_access", "")
            if not token:
                continue
            # allow comma separated tokens in the requested_dept_access field
            for part in token.split(','):
                p = part.strip()
                if p:
                    prefixes.append(p)
        # deduplicate while preserving order
        seen = set()
        deduped = []
        for p in prefixes:
            if p not in seen:
                seen.add(p)
                deduped.append(p)
        return deduped


# Singleton instance for import convenience
department_access_dao = DepartmentAccessDAO()
