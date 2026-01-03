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
                uses          TEXT,
                created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at    TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Standalone FTS5 table (no content sync issues)
            CREATE VIRTUAL TABLE IF NOT EXISTS features_fts USING fts5(
                id, name, description, technical_notes
            );

            -- Workflows: user-facing experiences (same structure as features)
            CREATE TABLE IF NOT EXISTS workflows (
                id            TEXT PRIMARY KEY,
                parent_id     TEXT REFERENCES workflows(id),
                name          TEXT NOT NULL,
                description   TEXT,
                purpose       TEXT,
                depends_on    TEXT,
                mermaid       TEXT,
                status        TEXT DEFAULT 'planned',
                created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at    TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS workflows_fts USING fts5(
                id, name, description, purpose
            );
        """)
        self.conn.commit()

    def _sync_fts(self, feature_id: str, delete_only: bool = False):
        """Sync a single feature to FTS index."""
        # Delete old entry
        self.conn.execute(
            "DELETE FROM features_fts WHERE id = ?", (feature_id,)
        )

        if not delete_only:
            # Insert current data
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
        uses: Optional[list[str]] = None,
        status: str = "planned"
    ) -> dict:
        now = datetime.now(UTC).isoformat()
        uses_json = json.dumps(uses) if uses else None
        self.conn.execute(
            """INSERT INTO features (id, parent_id, name, description, uses, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (id, parent_id, name, description, uses_json, status, now, now)
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

        # Convert lists to JSON
        for key in ["code_symbols", "files", "commit_ids", "uses"]:
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

    def get_features_using(self, feature_id: str) -> list[dict]:
        """Get features that use this feature (reverse lookup)."""
        rows = self.conn.execute(
            "SELECT * FROM features WHERE status != 'deleted'"
        ).fetchall()
        result = []
        for row in rows:
            f = dict(row)
            uses = json.loads(f.get("uses") or "[]")
            if feature_id in uses:
                result.append(f)
        return result

    def get_children(self, id: str) -> list[dict]:
        """Get direct children of a feature."""
        rows = self.conn.execute(
            "SELECT * FROM features WHERE parent_id = ?", (id,)
        ).fetchall()
        return [dict(row) for row in rows]

    def has_protected_children(self, id: str) -> bool:
        """Check if feature has children with status in-progress or done."""
        row = self.conn.execute(
            "SELECT COUNT(*) FROM features WHERE parent_id = ? AND status IN ('in-progress', 'done')",
            (id,)
        ).fetchone()
        return row[0] > 0

    def hard_delete_feature(self, id: str):
        """Permanently remove feature from database."""
        self._sync_fts(id, delete_only=True)
        self.conn.execute("DELETE FROM features WHERE id = ?", (id,))
        self.conn.commit()

    def delete_feature(self, id: str) -> dict:
        """Delete feature. Returns {"type": "hard"/"soft", "error": ...}"""
        feature = self.get_feature(id)
        if not feature:
            return {"ok": False, "error": "feature not found"}

        # Check for protected children
        if self.has_protected_children(id):
            return {"ok": False, "error": "has children with status in-progress or done"}

        status = feature.get("status", "planned")

        if status == "planned":
            self.hard_delete_feature(id)
            return {"ok": True, "type": "hard"}
        else:
            self.update_feature(id, status="deleted")
            return {"ok": True, "type": "soft"}

    def search_features(self, query: str) -> list[dict]:
        """FTS5 search with fallback to LIKE for simple queries."""
        try:
            # Try FTS5 search
            rows = self.conn.execute(
                """SELECT f.* FROM features f
                   JOIN features_fts fts ON f.id = fts.id
                   WHERE features_fts MATCH ? AND f.status != 'deleted'
                   ORDER BY rank""",
                (query,)
            ).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.OperationalError:
            # Fallback to LIKE search
            like_query = f"%{query}%"
            rows = self.conn.execute(
                """SELECT * FROM features
                   WHERE status != 'deleted'
                   AND (name LIKE ? OR description LIKE ? OR technical_notes LIKE ?)""",
                (like_query, like_query, like_query)
            ).fetchall()
            return [dict(row) for row in rows]

    # ==================== WORKFLOWS ====================

    def _sync_workflow_fts(self, workflow_id: str, delete_only: bool = False):
        """Sync a single workflow to FTS index."""
        self.conn.execute("DELETE FROM workflows_fts WHERE id = ?", (workflow_id,))
        if not delete_only:
            row = self.conn.execute(
                "SELECT id, name, description, purpose FROM workflows WHERE id = ?",
                (workflow_id,)
            ).fetchone()
            if row:
                self.conn.execute(
                    "INSERT INTO workflows_fts (id, name, description, purpose) VALUES (?, ?, ?, ?)",
                    (row["id"], row["name"], row["description"], row["purpose"])
                )

    def add_workflow(
        self,
        id: str,
        name: str,
        parent_id: Optional[str] = None,
        description: Optional[str] = None,
        purpose: Optional[str] = None,
        depends_on: Optional[list[str]] = None,
        mermaid: Optional[str] = None
    ) -> dict:
        now = datetime.now(UTC).isoformat()
        depends_json = json.dumps(depends_on) if depends_on else None
        self.conn.execute(
            """INSERT INTO workflows (id, parent_id, name, description, purpose, depends_on, mermaid, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (id, parent_id, name, description, purpose, depends_json, mermaid, now, now)
        )
        self._sync_workflow_fts(id)
        self.conn.commit()
        return {"ok": True}

    def get_workflow(self, id: str) -> Optional[dict]:
        row = self.conn.execute("SELECT * FROM workflows WHERE id = ?", (id,)).fetchone()
        return dict(row) if row else None

    def search_workflows(self, query: str) -> list[dict]:
        """FTS5 search with fallback to LIKE."""
        try:
            rows = self.conn.execute(
                """SELECT w.* FROM workflows w
                   JOIN workflows_fts wfts ON w.id = wfts.id
                   WHERE workflows_fts MATCH ? AND w.status != 'deleted'
                   ORDER BY rank""",
                (query,)
            ).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.OperationalError:
            like_query = f"%{query}%"
            rows = self.conn.execute(
                """SELECT * FROM workflows
                   WHERE status != 'deleted'
                   AND (name LIKE ? OR description LIKE ? OR purpose LIKE ?)""",
                (like_query, like_query, like_query)
            ).fetchall()
            return [dict(row) for row in rows]

    def get_workflows_for_feature(self, feature_id: str) -> list[dict]:
        """Get workflows that depend on a feature."""
        rows = self.conn.execute(
            "SELECT * FROM workflows WHERE status != 'deleted'"
        ).fetchall()
        result = []
        for row in rows:
            w = dict(row)
            depends = json.loads(w.get("depends_on") or "[]")
            if feature_id in depends:
                result.append(w)
        return result

    def get_features_for_workflow(self, workflow_id: str) -> list[dict]:
        """Get features that a workflow depends on."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return []
        depends = json.loads(workflow.get("depends_on") or "[]")
        result = []
        for fid in depends:
            f = self.get_feature(fid)
            if f:
                result.append(f)
        return result

    def update_workflow(self, id: str, **fields) -> Optional[dict]:
        """Update a workflow's fields."""
        if not fields:
            return self.get_workflow(id)

        # Convert lists to JSON
        if "depends_on" in fields and isinstance(fields["depends_on"], list):
            fields["depends_on"] = json.dumps(fields["depends_on"])

        fields["updated_at"] = datetime.now(UTC).isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [id]

        self.conn.execute(
            f"UPDATE workflows SET {set_clause} WHERE id = ?",
            values
        )
        self._sync_workflow_fts(id)
        self.conn.commit()
        return self.get_workflow(id)

    def has_protected_workflow_children(self, id: str) -> bool:
        """Check if workflow has children with status in-progress or done."""
        row = self.conn.execute(
            "SELECT COUNT(*) FROM workflows WHERE parent_id = ? AND status IN ('in-progress', 'done')",
            (id,)
        ).fetchone()
        return row[0] > 0

    def hard_delete_workflow(self, id: str):
        """Permanently remove workflow from database."""
        self._sync_workflow_fts(id, delete_only=True)
        self.conn.execute("DELETE FROM workflows WHERE id = ?", (id,))
        self.conn.commit()

    def delete_workflow(self, id: str) -> dict:
        """Delete workflow. Hard if planned, soft if in-progress/done."""
        workflow = self.get_workflow(id)
        if not workflow:
            return {"ok": False, "error": "workflow not found"}

        if self.has_protected_workflow_children(id):
            return {"ok": False, "error": "has children with status in-progress or done"}

        status = workflow.get("status", "planned")

        if status == "planned":
            self.hard_delete_workflow(id)
            return {"ok": True, "type": "hard"}
        else:
            self.update_workflow(id, status="deleted")
            return {"ok": True, "type": "soft"}
