# feature_tree/db.py
import sqlite3
import json
import re
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
                being_modified TEXT DEFAULT 'none',
                code_symbols  TEXT,
                files         TEXT,
                technical_notes TEXT,
                commit_ids    TEXT,
                uses          TEXT,
                confidence    TEXT,
                important_message TEXT,
                archived_at   TEXT,
                created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at    TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Standalone FTS5 table (no content sync issues)
            CREATE VIRTUAL TABLE IF NOT EXISTS features_fts USING fts5(
                id, name, description, technical_notes, files, code_symbols, commit_ids
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
                being_modified TEXT DEFAULT 'none',
                confidence    TEXT,
                important_message TEXT,
                embedding_status TEXT,
                archived_at   TEXT,
                steps         TEXT,
                created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at    TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS workflows_fts USING fts5(
                id, name, description, purpose, depends_on, steps
            );

            -- Embedding job queue (persistent, survives restarts)
            CREATE TABLE IF NOT EXISTS embedding_queue (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type     TEXT NOT NULL,  -- 'feature' or 'workflow'
                item_id       TEXT NOT NULL,
                attempt       INTEGER DEFAULT 1,
                next_retry_at TEXT,  -- ISO timestamp, NULL = ready now
                created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(item_type, item_id)  -- Only one job per item
            );
        """)
        self.conn.commit()
        
        # Migrate existing databases: add columns if missing
        self._migrate_add_column("features", "confidence", "TEXT")
        self._migrate_add_column("features", "being_modified", "TEXT", default="'none'")
        self._migrate_add_column("features", "important_message", "TEXT")
        self._migrate_add_column("features", "archived_at", "TEXT")
        self._migrate_add_column("features", "embedding_status", "TEXT")
        self._migrate_add_column("workflows", "confidence", "TEXT")
        self._migrate_add_column("workflows", "being_modified", "TEXT", default="'none'")
        self._migrate_add_column("workflows", "important_message", "TEXT")
        self._migrate_add_column("workflows", "embedding_status", "TEXT")
        self._migrate_add_column("workflows", "archived_at", "TEXT")
        self._migrate_add_column("workflows", "steps", "TEXT")

        # Migrate FTS tables
        self._migrate_fts_add_columns()
        self._migrate_workflow_fts_add_columns()

        # v2→v3 migration: status enum + code_symbols format
        self._migrate_v2_to_v3()

    def _migrate_add_column(self, table: str, column: str, col_type: str, default: str | None = None):
        """Add column to existing table if it doesn't exist."""
        cursor = self.conn.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        if column not in columns:
            default_clause = f" DEFAULT {default}" if default else ""
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}{default_clause}")
            self.conn.commit()

    def _migrate_v2_to_v3(self):
        """Migrate v2 data to v3 format (idempotent)."""
        # Check which columns exist
        cursor = self.conn.execute("PRAGMA table_info(features)")
        columns = {row[1] for row in cursor.fetchall()}

        # Status migration: in_progress → active + building, done → active, deleted → archived
        if 'status' in columns and 'being_modified' in columns:
            v2_statuses = self.conn.execute(
                "SELECT COUNT(*) FROM features WHERE status IN ('in_progress', 'done', 'deleted')"
            ).fetchone()[0]

            if v2_statuses > 0:
                # in_progress → active + being_modified=building
                self.conn.execute("""
                    UPDATE features
                    SET status = 'active', being_modified = 'building'
                    WHERE status = 'in_progress'
                """)
                # done → active (being_modified stays 'none')
                self.conn.execute("UPDATE features SET status = 'active' WHERE status = 'done'")
                # deleted → archived
                if 'archived_at' in columns:
                    self.conn.execute("""
                        UPDATE features
                        SET status = 'archived', archived_at = CURRENT_TIMESTAMP
                        WHERE status = 'deleted'
                    """)
                else:
                    self.conn.execute("UPDATE features SET status = 'archived' WHERE status = 'deleted'")
                self.conn.commit()

        # code_symbols migration: convert string arrays to structured objects
        if 'code_symbols' in columns:
            rows = self.conn.execute("SELECT id, code_symbols FROM features WHERE code_symbols IS NOT NULL").fetchall()
            for row in rows:
                try:
                    symbols = json.loads(row[1])
                    if symbols and isinstance(symbols[0], str):
                        # Old format (array of strings), migrate to new format
                        new_symbols = [
                            {"name": s, "location": None, "valid": True}
                            for s in symbols
                        ]
                        self.conn.execute(
                            "UPDATE features SET code_symbols = ? WHERE id = ?",
                            [json.dumps(new_symbols), row[0]]
                        )
                except (json.JSONDecodeError, TypeError, IndexError):
                    pass
            self.conn.commit()

    def _migrate_fts_add_columns(self):
        """Recreate FTS table if it doesn't have all required columns."""
        needs_rebuild = False

        # Check if FTS table has all columns (files, code_symbols, commit_ids)
        try:
            self.conn.execute("SELECT files, code_symbols, commit_ids FROM features_fts LIMIT 0")
        except Exception:
            needs_rebuild = True

        if needs_rebuild:
            self.conn.execute("DROP TABLE IF EXISTS features_fts")
            self.conn.execute("""
                CREATE VIRTUAL TABLE features_fts USING fts5(
                    id, name, description, technical_notes, files, code_symbols, commit_ids
                )
            """)
            self._resync_all_fts()
            self.conn.commit()

    def _resync_all_fts(self):
        """Re-sync all features to FTS index (used by migration and manual refresh)."""
        self.conn.execute("DELETE FROM features_fts")
        rows = self.conn.execute(
            "SELECT id, name, description, technical_notes, files, code_symbols, commit_ids FROM features"
        ).fetchall()
        for row in rows:
            files_text = self._json_to_text(row[4])
            symbols_text = self._json_to_text(row[5])
            commits_text = self._json_to_text(row[6])
            self.conn.execute(
                "INSERT INTO features_fts (id, name, description, technical_notes, files, code_symbols, commit_ids) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (row[0], row[1], row[2], row[3], files_text, symbols_text, commits_text)
            )

    def _migrate_workflow_fts_add_columns(self):
        """Recreate workflow FTS table if it doesn't have all required columns."""
        needs_rebuild = False
        try:
            self.conn.execute("SELECT depends_on, steps FROM workflows_fts LIMIT 0")
        except Exception:
            needs_rebuild = True

        if needs_rebuild:
            self.conn.execute("DROP TABLE IF EXISTS workflows_fts")
            self.conn.execute("""
                CREATE VIRTUAL TABLE workflows_fts USING fts5(
                    id, name, description, purpose, depends_on, steps
                )
            """)
            self._resync_all_workflow_fts()
            self.conn.commit()

    def _resync_all_workflow_fts(self):
        """Re-sync all workflows to FTS index."""
        self.conn.execute("DELETE FROM workflows_fts")
        rows = self.conn.execute(
            "SELECT id, name, description, purpose, depends_on, steps FROM workflows"
        ).fetchall()
        for row in rows:
            depends_text = self._json_to_text(row[4])
            steps_text = self._json_to_text(row[5])
            self.conn.execute(
                "INSERT INTO workflows_fts (id, name, description, purpose, depends_on, steps) VALUES (?, ?, ?, ?, ?, ?)",
                (row[0], row[1], row[2], row[3], depends_text, steps_text)
            )

    def _json_to_text(self, json_str: str | None) -> str | None:
        """Convert JSON array to space-separated text for FTS indexing.

        Handles both string arrays (files, commit_ids) and dict arrays (code_symbols).
        """
        if not json_str:
            return None
        try:
            items = json.loads(json_str)
            if not items:
                return None
            # Handle both string arrays and dict arrays (code_symbols)
            text_parts = []
            for item in items:
                if isinstance(item, dict):
                    # code_symbols format: {name, location, valid}
                    text_parts.append(item.get("name", ""))
                else:
                    text_parts.append(str(item))
            return " ".join(filter(None, text_parts))
        except (json.JSONDecodeError, TypeError):
            return json_str

    def _sync_fts(self, feature_id: str, delete_only: bool = False):
        """Sync a single feature to FTS index."""
        # Delete old entry
        self.conn.execute(
            "DELETE FROM features_fts WHERE id = ?", (feature_id,)
        )

        if not delete_only:
            # Insert current data
            row = self.conn.execute(
                "SELECT id, name, description, technical_notes, files, code_symbols, commit_ids FROM features WHERE id = ?",
                (feature_id,)
            ).fetchone()
            if row:
                # Convert JSON arrays to space-separated text for FTS
                files_text = self._json_to_text(row["files"])
                symbols_text = self._json_to_text(row["code_symbols"])
                commits_text = self._json_to_text(row["commit_ids"])
                self.conn.execute(
                    "INSERT INTO features_fts (id, name, description, technical_notes, files, code_symbols, commit_ids) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (row["id"], row["name"], row["description"], row["technical_notes"], files_text, symbols_text, commits_text)
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
        confidence: Optional[str] = None,
        status: str = "planned",
        being_modified: str = "none",
        important_message: Optional[str] = None,
        files: Optional[list[str]] = None,
        code_symbols: Optional[list[dict]] = None,
        technical_notes: Optional[str] = None
    ) -> dict:
        now = datetime.now(UTC).isoformat()
        uses_json = json.dumps(uses) if uses else None
        files_json = json.dumps(files) if files else None
        symbols_json = json.dumps(code_symbols) if code_symbols else None
        self.conn.execute(
            """INSERT INTO features (id, parent_id, name, description, uses, confidence, status,
               being_modified, important_message, files, code_symbols, technical_notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (id, parent_id, name, description, uses_json, confidence, status,
             being_modified, important_message, files_json, symbols_json, technical_notes, now, now)
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
            "SELECT * FROM features WHERE status != 'archived'"
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
        """Check if feature has children with status active."""
        row = self.conn.execute(
            "SELECT COUNT(*) FROM features WHERE parent_id = ? AND status = 'active'",
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
            return {"ok": False, "error": "has children with status active"}

        status = feature.get("status", "planned")

        if status == "planned":
            self.hard_delete_feature(id)
            return {"ok": True, "type": "hard"}
        else:
            # Soft delete: set status to archived with timestamp
            now = datetime.now(UTC).isoformat()
            self.conn.execute(
                "UPDATE features SET status = 'archived', archived_at = ?, updated_at = ? WHERE id = ?",
                (now, now, id)
            )
            self._sync_fts(id)
            self.conn.commit()
            return {"ok": True, "type": "soft"}

    def _normalize_query(self, query: str) -> str:
        """Normalize query for FTS5: replace ., -, / with spaces."""
        return re.sub(r'[.\-/\\]', ' ', query)

    def search_features(self, query: str) -> list[dict]:
        """FTS5 search with fallback to LIKE for simple queries."""
        # Normalize query: health.ts → "health ts", status-check → "status check"
        normalized = self._normalize_query(query)
        try:
            # Try FTS5 search
            rows = self.conn.execute(
                """SELECT f.* FROM features f
                   JOIN features_fts fts ON f.id = fts.id
                   WHERE features_fts MATCH ? AND f.status != 'archived'
                   ORDER BY rank""",
                (normalized,)
            ).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.OperationalError:
            # Fallback to LIKE search (use original query for LIKE)
            like_query = f"%{query}%"
            rows = self.conn.execute(
                """SELECT * FROM features
                   WHERE status != 'archived'
                   AND (name LIKE ? OR description LIKE ? OR technical_notes LIKE ? OR files LIKE ? OR code_symbols LIKE ? OR commit_ids LIKE ?)""",
                (like_query, like_query, like_query, like_query, like_query, like_query)
            ).fetchall()
            return [dict(row) for row in rows]

    # ==================== WORKFLOWS ====================

    def _sync_workflow_fts(self, workflow_id: str, delete_only: bool = False):
        """Sync a single workflow to FTS index."""
        self.conn.execute("DELETE FROM workflows_fts WHERE id = ?", (workflow_id,))
        if not delete_only:
            row = self.conn.execute(
                "SELECT id, name, description, purpose, depends_on, steps FROM workflows WHERE id = ?",
                (workflow_id,)
            ).fetchone()
            if row:
                depends_text = self._json_to_text(row["depends_on"])
                steps_text = self._json_to_text(row["steps"])
                self.conn.execute(
                    "INSERT INTO workflows_fts (id, name, description, purpose, depends_on, steps) VALUES (?, ?, ?, ?, ?, ?)",
                    (row["id"], row["name"], row["description"], row["purpose"], depends_text, steps_text)
                )

    def add_workflow(
        self,
        id: str,
        name: str,
        parent_id: Optional[str] = None,
        description: Optional[str] = None,
        purpose: Optional[str] = None,
        depends_on: Optional[list[str]] = None,
        mermaid: Optional[str] = None,
        confidence: Optional[str] = None,
        being_modified: str = "none",
        important_message: Optional[str] = None,
        steps: Optional[list[str]] = None
    ) -> dict:
        now = datetime.now(UTC).isoformat()
        depends_json = json.dumps(depends_on) if depends_on else None
        steps_json = json.dumps(steps) if steps else None
        self.conn.execute(
            """INSERT INTO workflows (id, parent_id, name, description, purpose, depends_on, mermaid, confidence,
               being_modified, important_message, steps, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (id, parent_id, name, description, purpose, depends_json, mermaid, confidence,
             being_modified, important_message, steps_json, now, now)
        )
        self._sync_workflow_fts(id)
        self.conn.commit()
        return {"ok": True}

    def get_workflow(self, id: str) -> Optional[dict]:
        row = self.conn.execute("SELECT * FROM workflows WHERE id = ?", (id,)).fetchone()
        return dict(row) if row else None

    def search_workflows(self, query: str) -> list[dict]:
        """FTS5 search with fallback to LIKE."""
        # Normalize query: AUTH.login → "AUTH login"
        normalized = self._normalize_query(query)
        try:
            rows = self.conn.execute(
                """SELECT w.* FROM workflows w
                   JOIN workflows_fts wfts ON w.id = wfts.id
                   WHERE workflows_fts MATCH ? AND w.status != 'archived'
                   ORDER BY rank""",
                (normalized,)
            ).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.OperationalError:
            like_query = f"%{query}%"
            rows = self.conn.execute(
                """SELECT * FROM workflows
                   WHERE status != 'archived'
                   AND (name LIKE ? OR description LIKE ? OR purpose LIKE ? OR depends_on LIKE ?)""",
                (like_query, like_query, like_query, like_query)
            ).fetchall()
            return [dict(row) for row in rows]

    def get_workflows_for_feature(self, feature_id: str) -> list[dict]:
        """Get workflows that depend on a feature."""
        rows = self.conn.execute(
            "SELECT * FROM workflows WHERE status != 'archived'"
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
        for key in ["depends_on", "steps"]:
            if key in fields and isinstance(fields[key], list):
                fields[key] = json.dumps(fields[key])

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
        """Check if workflow has children with status active."""
        row = self.conn.execute(
            "SELECT COUNT(*) FROM workflows WHERE parent_id = ? AND status = 'active'",
            (id,)
        ).fetchone()
        return row[0] > 0

    def hard_delete_workflow(self, id: str):
        """Permanently remove workflow from database."""
        self._sync_workflow_fts(id, delete_only=True)
        self.conn.execute("DELETE FROM workflows WHERE id = ?", (id,))
        self.conn.commit()

    def delete_workflow(self, id: str) -> dict:
        """Delete workflow. Hard if planned, soft (archived) if active."""
        workflow = self.get_workflow(id)
        if not workflow:
            return {"ok": False, "error": "workflow not found"}

        if self.has_protected_workflow_children(id):
            return {"ok": False, "error": "has children with status active"}

        status = workflow.get("status", "planned")

        if status == "planned":
            self.hard_delete_workflow(id)
            return {"ok": True, "type": "hard"}
        else:
            # Soft delete: set status to archived with timestamp
            now = datetime.now(UTC).isoformat()
            self.conn.execute(
                "UPDATE workflows SET status = 'archived', archived_at = ?, updated_at = ? WHERE id = ?",
                (now, now, id)
            )
            self._sync_workflow_fts(id)
            self.conn.commit()
            return {"ok": True, "type": "soft"}

    # ==================== EMBEDDING QUEUE ====================

    def queue_embed_job(self, item_type: str, item_id: str) -> bool:
        """Add embedding job to queue. Returns True if added, False if already queued."""
        try:
            self.conn.execute(
                "INSERT OR IGNORE INTO embedding_queue (item_type, item_id) VALUES (?, ?)",
                (item_type, item_id)
            )
            self.conn.commit()
            return self.conn.total_changes > 0
        except Exception:
            return False

    def get_next_embed_job(self) -> Optional[dict]:
        """Get next ready job (no next_retry_at or past due). Returns None if queue empty."""
        now = datetime.now(UTC).isoformat()
        row = self.conn.execute(
            """SELECT id, item_type, item_id, attempt FROM embedding_queue
               WHERE next_retry_at IS NULL OR next_retry_at <= ?
               ORDER BY id LIMIT 1""",
            (now,)
        ).fetchone()
        return dict(row) if row else None

    def update_embed_job_retry(self, item_type: str, item_id: str, attempt: int, next_retry_at: str):
        """Update job for retry with next attempt time."""
        self.conn.execute(
            "UPDATE embedding_queue SET attempt = ?, next_retry_at = ? WHERE item_type = ? AND item_id = ?",
            (attempt, next_retry_at, item_type, item_id)
        )
        self.conn.commit()

    def delete_embed_job(self, item_type: str, item_id: str):
        """Remove completed or failed job from queue."""
        self.conn.execute(
            "DELETE FROM embedding_queue WHERE item_type = ? AND item_id = ?",
            (item_type, item_id)
        )
        self.conn.commit()

    def get_embed_queue_count(self) -> int:
        """Get number of pending jobs in queue."""
        row = self.conn.execute("SELECT COUNT(*) FROM embedding_queue").fetchone()
        return row[0] if row else 0

    def reset_embed_queue_for_startup(self) -> int:
        """Reset all jobs for fresh retry on startup. Returns count of jobs reset."""
        result = self.conn.execute(
            "UPDATE embedding_queue SET attempt = 1, next_retry_at = NULL"
        )
        self.conn.commit()
        return result.rowcount
