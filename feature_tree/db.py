# feature_tree/db.py
import sqlite3
import json
from datetime import datetime, UTC
from typing import Optional
from pathlib import Path


class FeatureDB:
    def __init__(self, db_path: str = "features.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
        self._ensure_fts_valid()

    def _init_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS features (
                id            TEXT PRIMARY KEY,
                parent_id     TEXT REFERENCES features(id),
                name          TEXT NOT NULL,
                description   TEXT,
                status        TEXT DEFAULT 'planned',
                code_symbols  TEXT,
                files         TEXT,
                technical_notes TEXT,
                commit_ids    TEXT,
                created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at    TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    def _ensure_fts_valid(self):
        """Ensure FTS table exists and is properly synced."""
        # Drop old triggers that cause issues
        for trigger in ['features_ai', 'features_ad', 'features_au']:
            self.conn.execute(f"DROP TRIGGER IF EXISTS {trigger}")

        # Check if FTS table exists and is standalone (not content-based)
        try:
            result = self.conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='features_fts'"
            ).fetchone()

            if result:
                sql = result[0] or ""
                # If it's an old content-based FTS, drop and recreate
                if "content=" in sql.lower():
                    self.conn.execute("DROP TABLE features_fts")
                    result = None

            if not result:
                # Create standalone FTS5 table
                self.conn.execute("""
                    CREATE VIRTUAL TABLE features_fts USING fts5(
                        id, name, description, technical_notes
                    )
                """)

            # Rebuild FTS index from features table
            self._rebuild_fts()
            self.conn.commit()

        except sqlite3.OperationalError:
            # Table doesn't exist, create it
            self.conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS features_fts USING fts5(
                    id, name, description, technical_notes
                )
            """)
            self._rebuild_fts()
            self.conn.commit()

    def _rebuild_fts(self):
        """Rebuild entire FTS index from features table."""
        self.conn.execute("DELETE FROM features_fts")
        self.conn.execute("""
            INSERT INTO features_fts (id, name, description, technical_notes)
            SELECT id, name, description, technical_notes FROM features
        """)

    def _sync_fts(self, feature_id: str, delete_only: bool = False):
        """Sync a single feature to FTS index."""
        self.conn.execute("DELETE FROM features_fts WHERE id = ?", (feature_id,))

        if not delete_only:
            row = self.conn.execute(
                "SELECT id, name, description, technical_notes FROM features WHERE id = ?",
                (feature_id,)
            ).fetchone()
            if row:
                self.conn.execute(
                    "INSERT INTO features_fts (id, name, description, technical_notes) VALUES (?, ?, ?, ?)",
                    (row["id"], row["name"], row["description"], row["technical_notes"])
                )

    def execute(self, sql: str, params: tuple = ()):
        return self.conn.execute(sql, params)

    def close(self):
        self.conn.close()

    def add_feature(
        self,
        id: str,
        name: str,
        parent_id: Optional[str] = None,
        description: Optional[str] = None,
        status: str = "planned"
    ) -> dict:
        now = datetime.now(UTC).isoformat()
        self.conn.execute(
            """INSERT INTO features (id, parent_id, name, description, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (id, parent_id, name, description, status, now, now)
        )
        self._sync_fts(id)
        self.conn.commit()
        return self.get_feature(id)

    def get_feature(self, id: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM features WHERE id = ?", (id,)
        ).fetchone()
        return dict(row) if row else None

    def update_feature(self, id: str, **fields) -> Optional[dict]:
        if not fields:
            return self.get_feature(id)

        for key in ["code_symbols", "files", "commit_ids"]:
            if key in fields and isinstance(fields[key], list):
                fields[key] = json.dumps(fields[key])

        fields["updated_at"] = datetime.now(UTC).isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [id]

        self.conn.execute(
            f"UPDATE features SET {set_clause} WHERE id = ?",
            values
        )
        self._sync_fts(id)
        self.conn.commit()
        return self.get_feature(id)

    def delete_feature(self, id: str) -> Optional[dict]:
        return self.update_feature(id, status="deleted")

    def search_features(self, query: str) -> list[dict]:
        """FTS5 search with fallback to LIKE."""
        try:
            rows = self.conn.execute(
                """SELECT f.* FROM features f
                   JOIN features_fts fts ON f.id = fts.id
                   WHERE features_fts MATCH ? AND f.status != 'deleted'
                   ORDER BY rank""",
                (query,)
            ).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.OperationalError:
            like_query = f"%{query}%"
            rows = self.conn.execute(
                """SELECT * FROM features
                   WHERE status != 'deleted'
                   AND (name LIKE ? OR description LIKE ? OR technical_notes LIKE ?)""",
                (like_query, like_query, like_query)
            ).fetchall()
            return [dict(row) for row in rows]
