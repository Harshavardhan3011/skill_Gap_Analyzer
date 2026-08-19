"""
Database initialization and repository for Skill Gap Analyzer.

Uses SQLite with parameterized queries only (no raw string formatting).
AnalysisRepository provides a clean interface for CRUD operations.
"""

import sqlite3
import json
import logging
import os
from datetime import datetime
from typing import Optional

from config.settings import DATABASE_PATH

logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row_factory set for dict-like access."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # safer concurrent writes
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """
    Create the database schema if it does not already exist.
    Safe to call on every application start.
    """
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    create_sql = """
    CREATE TABLE IF NOT EXISTS analyses (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_name  TEXT    NOT NULL,
        target_role     TEXT    NOT NULL,
        created_at      TEXT    NOT NULL,
        match_score     REAL    NOT NULL,
        matched_count   INTEGER NOT NULL,
        partial_count   INTEGER NOT NULL,
        missing_count   INTEGER NOT NULL,
        total_required  INTEGER NOT NULL,
        result_json     TEXT    NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_analyses_created_at
        ON analyses (created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_analyses_candidate
        ON analyses (candidate_name);
    """

    try:
        with get_connection() as conn:
            conn.executescript(create_sql)
        logger.info("Database initialized at %s", DATABASE_PATH)
    except sqlite3.Error as exc:
        logger.error("Failed to initialize database: %s", exc)
        raise


class AnalysisRepository:
    """
    Repository class for analysis CRUD operations.

    All SQL uses parameterized queries to prevent injection.
    """

    # ── Create ────────────────────────────────────────────────────────────────
    def save(self, result: dict) -> int:
        """
        Persist an analysis result dict to SQLite.

        Args:
            result: The full analysis result dictionary produced by ReportGenerator.

        Returns:
            The new row's auto-generated ID.

        Raises:
            sqlite3.Error: On any database failure.
            ValueError: If required fields are missing from result.
        """
        required_fields = [
            "candidate_name", "target_role", "match_score",
            "matched_count", "partial_count", "missing_count", "total_required",
        ]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field in result: {field}")

        sql = """
        INSERT INTO analyses
            (candidate_name, target_role, created_at,
             match_score, matched_count, partial_count,
             missing_count, total_required, result_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            result["candidate_name"][:100],
            result["target_role"][:100],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            round(float(result["match_score"]), 2),
            int(result["matched_count"]),
            int(result["partial_count"]),
            int(result["missing_count"]),
            int(result["total_required"]),
            json.dumps(result, ensure_ascii=False),
        )

        try:
            with get_connection() as conn:
                cursor = conn.execute(sql, params)
                return cursor.lastrowid
        except sqlite3.Error as exc:
            logger.error("Failed to save analysis: %s", exc)
            raise

    # ── Read ──────────────────────────────────────────────────────────────────
    def get_by_id(self, analysis_id: int) -> Optional[dict]:
        """
        Retrieve a single analysis by primary key.

        Returns:
            The result dict (parsed from result_json) with top-level metadata,
            or None if not found.
        """
        sql = "SELECT * FROM analyses WHERE id = ?"
        try:
            with get_connection() as conn:
                row = conn.execute(sql, (analysis_id,)).fetchone()
        except sqlite3.Error as exc:
            logger.error("Failed to fetch analysis %s: %s", analysis_id, exc)
            raise

        if row is None:
            return None

        return self._row_to_dict(row)

    def get_all(
        self,
        search: str = "",
        sort_by: str = "created_at",
        order: str = "desc",
        page: int = 1,
        page_size: int = 10,
    ) -> dict:
        """
        Return paginated list of analyses with optional search/sort.

        Args:
            search:    Filter by candidate_name or target_role (case-insensitive).
            sort_by:   Column to sort by. Allowed: created_at, match_score,
                       candidate_name, target_role.
            order:     'asc' or 'desc'.
            page:      1-indexed page number.
            page_size: Results per page.

        Returns:
            dict with keys: items (list), total (int), page (int), pages (int).
        """
        allowed_sort = {
            "created_at", "match_score", "candidate_name",
            "target_role", "matched_count", "missing_count",
        }
        if sort_by not in allowed_sort:
            sort_by = "created_at"
        if order not in ("asc", "desc"):
            order = "desc"

        where_clause = ""
        params: list = []
        if search:
            where_clause = (
                "WHERE candidate_name LIKE ? OR target_role LIKE ?"
            )
            like = f"%{search}%"
            params = [like, like]

        count_sql = f"SELECT COUNT(*) FROM analyses {where_clause}"
        data_sql = (
            f"SELECT * FROM analyses {where_clause} "
            f"ORDER BY {sort_by} {order.upper()} "
            f"LIMIT ? OFFSET ?"
        )

        offset = (max(page, 1) - 1) * page_size

        try:
            with get_connection() as conn:
                total = conn.execute(count_sql, params).fetchone()[0]
                rows = conn.execute(
                    data_sql, params + [page_size, offset]
                ).fetchall()
        except sqlite3.Error as exc:
            logger.error("Failed to list analyses: %s", exc)
            raise

        items = [self._row_to_meta(row) for row in rows]
        total_pages = max(1, (total + page_size - 1) // page_size)

        return {
            "items": items,
            "total": total,
            "page": page,
            "pages": total_pages,
        }

    # ── Delete ────────────────────────────────────────────────────────────────
    def delete(self, analysis_id: int) -> bool:
        """
        Delete an analysis by ID.

        Returns:
            True if a row was deleted, False if the ID was not found.
        """
        sql = "DELETE FROM analyses WHERE id = ?"
        try:
            with get_connection() as conn:
                cursor = conn.execute(sql, (analysis_id,))
                return cursor.rowcount > 0
        except sqlite3.Error as exc:
            logger.error("Failed to delete analysis %s: %s", analysis_id, exc)
            raise

    # ── Helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _row_to_meta(row: sqlite3.Row) -> dict:
        """Return lightweight row dict (no result_json blob) for list views."""
        return {
            "id": row["id"],
            "candidate_name": row["candidate_name"],
            "target_role": row["target_role"],
            "created_at": row["created_at"],
            "match_score": row["match_score"],
            "matched_count": row["matched_count"],
            "partial_count": row["partial_count"],
            "missing_count": row["missing_count"],
            "total_required": row["total_required"],
        }

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Parse the stored JSON and merge DB metadata."""
        data = json.loads(row["result_json"])
        data["id"] = row["id"]
        data["created_at"] = row["created_at"]
        return data
