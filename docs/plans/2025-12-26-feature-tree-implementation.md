# Feature Tree Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an MCP-based feature management system with SQLite backend, fuzzy search, and auto-generated markdown reports.

**Architecture:** SQLite stores features with FTS5 for fuzzy search. MCP server exposes 4 tools (search/add/update/delete). SessionStart hook injects context. /commit command bundles git + feature updates.

**Tech Stack:** Python 3.11+, SQLite with FTS5, MCP SDK (mcp package), uv for dependencies

---

## Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `feature_tree/__init__.py`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "feature-tree"
version = "0.1.0"
description = "AI-driven feature management for Claude Code"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
]
```

**Step 2: Create package directory**

```bash
mkdir -p feature_tree
touch feature_tree/__init__.py
```

**Step 3: Install dependencies**

Run: `uv sync`
Expected: Dependencies installed successfully

**Step 4: Commit**

```bash
git add pyproject.toml feature_tree/__init__.py uv.lock
git commit -m "chore: initialize project with uv and mcp dependency"
```

---

## Task 2: SQLite Database Layer

**Files:**
- Create: `feature_tree/db.py`
- Create: `tests/test_db.py`

**Step 1: Write failing test for database initialization**

```python
# tests/test_db.py
import os
import tempfile
import pytest
from feature_tree.db import FeatureDB


def test_init_creates_tables():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "features.db")
        db = FeatureDB(db_path)

        # Check tables exist
        tables = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        assert "features" in table_names
        assert "features_fts" in table_names
        db.close()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_db.py::test_init_creates_tables -v`
Expected: FAIL with "No module named 'feature_tree.db'"

**Step 3: Write minimal implementation**

```python
# feature_tree/db.py
import sqlite3
import json
from datetime import datetime
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
                created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at    TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS features_fts USING fts5(
                id, name, description, technical_notes,
                content='features',
                content_rowid='rowid'
            );

            CREATE TRIGGER IF NOT EXISTS features_ai AFTER INSERT ON features BEGIN
                INSERT INTO features_fts(id, name, description, technical_notes)
                VALUES (new.id, new.name, new.description, new.technical_notes);
            END;

            CREATE TRIGGER IF NOT EXISTS features_ad AFTER DELETE ON features BEGIN
                INSERT INTO features_fts(features_fts, id, name, description, technical_notes)
                VALUES ('delete', old.id, old.name, old.description, old.technical_notes);
            END;

            CREATE TRIGGER IF NOT EXISTS features_au AFTER UPDATE ON features BEGIN
                INSERT INTO features_fts(features_fts, id, name, description, technical_notes)
                VALUES ('delete', old.id, old.name, old.description, old.technical_notes);
                INSERT INTO features_fts(id, name, description, technical_notes)
                VALUES (new.id, new.name, new.description, new.technical_notes);
            END;
        """)
        self.conn.commit()

    def execute(self, sql: str, params: tuple = ()):
        return self.conn.execute(sql, params)

    def close(self):
        self.conn.close()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_db.py::test_init_creates_tables -v`
Expected: PASS

**Step 5: Commit**

```bash
git add feature_tree/db.py tests/test_db.py
git commit -m "feat: add SQLite database layer with FTS5 support"
```

---

## Task 3: Add Feature CRUD Operations

**Files:**
- Modify: `feature_tree/db.py`
- Modify: `tests/test_db.py`

**Step 1: Write failing test for add_feature**

```python
# tests/test_db.py (append)

def test_add_feature():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "features.db")
        db = FeatureDB(db_path)

        feature = db.add_feature(
            id="auth-login",
            name="User Login",
            description="Login with email/password"
        )

        assert feature["id"] == "auth-login"
        assert feature["name"] == "User Login"
        assert feature["status"] == "planned"
        db.close()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_db.py::test_add_feature -v`
Expected: FAIL with "FeatureDB has no attribute 'add_feature'"

**Step 3: Write implementation for add_feature**

```python
# feature_tree/db.py (add to FeatureDB class)

    def add_feature(
        self,
        id: str,
        name: str,
        parent_id: Optional[str] = None,
        description: Optional[str] = None,
        status: str = "planned"
    ) -> dict:
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            """INSERT INTO features (id, parent_id, name, description, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (id, parent_id, name, description, status, now, now)
        )
        self.conn.commit()
        return self.get_feature(id)

    def get_feature(self, id: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM features WHERE id = ?", (id,)
        ).fetchone()
        return dict(row) if row else None
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_db.py::test_add_feature -v`
Expected: PASS

**Step 5: Write failing test for update_feature**

```python
# tests/test_db.py (append)

def test_update_feature():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "features.db")
        db = FeatureDB(db_path)

        db.add_feature(id="auth", name="Auth")
        updated = db.update_feature(
            id="auth",
            status="in-progress",
            code_symbols=["AuthService", "loginUser"]
        )

        assert updated["status"] == "in-progress"
        assert json.loads(updated["code_symbols"]) == ["AuthService", "loginUser"]
        db.close()
```

**Step 6: Run test to verify it fails**

Run: `uv run pytest tests/test_db.py::test_update_feature -v`
Expected: FAIL with "FeatureDB has no attribute 'update_feature'"

**Step 7: Write implementation for update_feature**

```python
# feature_tree/db.py (add to FeatureDB class)

    def update_feature(self, id: str, **fields) -> Optional[dict]:
        if not fields:
            return self.get_feature(id)

        # Convert lists to JSON
        for key in ["code_symbols", "files", "commit_ids"]:
            if key in fields and isinstance(fields[key], list):
                fields[key] = json.dumps(fields[key])

        fields["updated_at"] = datetime.utcnow().isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [id]

        self.conn.execute(
            f"UPDATE features SET {set_clause} WHERE id = ?",
            values
        )
        self.conn.commit()
        return self.get_feature(id)
```

**Step 8: Run test to verify it passes**

Run: `uv run pytest tests/test_db.py::test_update_feature -v`
Expected: PASS

**Step 9: Write failing test for delete_feature**

```python
# tests/test_db.py (append)

def test_delete_feature():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "features.db")
        db = FeatureDB(db_path)

        db.add_feature(id="temp", name="Temporary")
        deleted = db.delete_feature("temp")

        assert deleted["status"] == "deleted"
        db.close()
```

**Step 10: Run test to verify it fails**

Run: `uv run pytest tests/test_db.py::test_delete_feature -v`
Expected: FAIL with "FeatureDB has no attribute 'delete_feature'"

**Step 11: Write implementation for delete_feature**

```python
# feature_tree/db.py (add to FeatureDB class)

    def delete_feature(self, id: str) -> Optional[dict]:
        return self.update_feature(id, status="deleted")
```

**Step 12: Run all tests**

Run: `uv run pytest tests/test_db.py -v`
Expected: All PASS

**Step 13: Commit**

```bash
git add feature_tree/db.py tests/test_db.py
git commit -m "feat: add CRUD operations for features"
```

---

## Task 4: Fuzzy Search

**Files:**
- Modify: `feature_tree/db.py`
- Modify: `tests/test_db.py`

**Step 1: Write failing test for search_features**

```python
# tests/test_db.py (append)

def test_search_features():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "features.db")
        db = FeatureDB(db_path)

        db.add_feature(id="auth-login", name="User Login", description="Login with email")
        db.add_feature(id="auth-signup", name="User Signup", description="Register new users")
        db.add_feature(id="payments", name="Payments", description="Stripe integration")

        results = db.search_features("user")

        assert len(results) == 2
        ids = [r["id"] for r in results]
        assert "auth-login" in ids
        assert "auth-signup" in ids
        db.close()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_db.py::test_search_features -v`
Expected: FAIL with "FeatureDB has no attribute 'search_features'"

**Step 3: Write implementation for search_features**

```python
# feature_tree/db.py (add to FeatureDB class)

    def search_features(self, query: str) -> list[dict]:
        # FTS5 search
        rows = self.conn.execute(
            """SELECT f.* FROM features f
               JOIN features_fts fts ON f.id = fts.id
               WHERE features_fts MATCH ? AND f.status != 'deleted'
               ORDER BY rank""",
            (query,)
        ).fetchall()
        return [dict(row) for row in rows]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_db.py::test_search_features -v`
Expected: PASS

**Step 5: Commit**

```bash
git add feature_tree/db.py tests/test_db.py
git commit -m "feat: add fuzzy search with FTS5"
```

---

## Task 5: Markdown Generation

**Files:**
- Create: `feature_tree/markdown.py`
- Create: `tests/test_markdown.py`

**Step 1: Write failing test for generate_markdown**

```python
# tests/test_markdown.py
import os
import tempfile
from feature_tree.db import FeatureDB
from feature_tree.markdown import generate_markdown


def test_generate_markdown():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "features.db")
        db = FeatureDB(db_path)

        db.add_feature(id="auth", name="Authentication", description="Auth system")
        db.add_feature(id="auth-login", name="Login", parent_id="auth", status="done")

        md = generate_markdown(db)

        assert "# Feature Tree" in md
        assert "## auth" in md
        assert "Authentication" in md
        assert "### auth-login" in md
        assert "**Status:** done" in md
        db.close()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_markdown.py::test_generate_markdown -v`
Expected: FAIL with "No module named 'feature_tree.markdown'"

**Step 3: Write implementation**

```python
# feature_tree/markdown.py
import json
from typing import Optional
from feature_tree.db import FeatureDB


def generate_markdown(db: FeatureDB) -> str:
    features = db.execute(
        "SELECT * FROM features WHERE status != 'deleted' ORDER BY id"
    ).fetchall()
    features = [dict(f) for f in features]

    # Build tree structure
    tree = build_tree(features)

    lines = [
        "# Feature Tree",
        "",
        "> Auto-generated. Do not edit. Use Claude Code to modify.",
        ""
    ]

    for root in tree:
        lines.extend(render_feature(root, level=2))

    return "\n".join(lines)


def build_tree(features: list[dict]) -> list[dict]:
    by_id = {f["id"]: {**f, "children": []} for f in features}
    roots = []

    for f in features:
        node = by_id[f["id"]]
        parent_id = f["parent_id"]
        if parent_id and parent_id in by_id:
            by_id[parent_id]["children"].append(node)
        else:
            roots.append(node)

    return roots


def render_feature(feature: dict, level: int) -> list[str]:
    lines = []
    prefix = "#" * level

    # Header with name
    lines.append(f"{prefix} {feature['id']}")
    if feature["description"]:
        lines.append(feature["description"])
    lines.append("")

    # Metadata
    lines.append(f"- **Status:** {feature['status']}")

    if feature.get("code_symbols"):
        symbols = json.loads(feature["code_symbols"])
        if symbols:
            lines.append(f"- **Symbols:** {', '.join(symbols)}")

    if feature.get("files"):
        files = json.loads(feature["files"])
        if files:
            lines.append(f"- **Files:** {', '.join(files)}")

    if feature.get("commit_ids"):
        commits = json.loads(feature["commit_ids"])
        if commits:
            lines.append(f"- **Commits:** {', '.join(commits)}")

    lines.append("")

    # Children
    for child in feature.get("children", []):
        lines.extend(render_feature(child, level + 1))

    return lines
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_markdown.py::test_generate_markdown -v`
Expected: PASS

**Step 5: Commit**

```bash
git add feature_tree/markdown.py tests/test_markdown.py
git commit -m "feat: add markdown report generation"
```

---

## Task 6: MCP Server

**Files:**
- Create: `feature_tree/mcp_server.py`

**Step 1: Write MCP server with instructions and 4 tools**

```python
# feature_tree/mcp_server.py
#!/usr/bin/env python
"""Feature Tree MCP Server"""

import json
import os
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from feature_tree.db import FeatureDB
from feature_tree.markdown import generate_markdown


SERVER_INSTRUCTIONS = """
# Feature Tree

You are working in a project that uses Feature Tree for feature management.
Feature Tree is the single source of truth for what this project does.

## Philosophy

- **Human elaborates, AI implements.** The human describes features in natural language.
  You translate that into structured data and working code.
- **Every feature is tracked.** When you implement something, record it.
  When you modify something, update it. When you delete something, mark it deleted.
- **Code symbols matter.** Record function names, class names, variables -
  these help future sessions find relevant code via LSP.
- **Commits link to features.** Every commit should be associated with a feature.
  Use /commit to bundle git commit + feature tree update.

## When to use each tool

- **search_features(query):** Before starting any work, search to understand
  what exists. Before modifying code, search to find related features.
- **add_feature(...):** When the human describes something new. Create it
  with status='planned', then update to 'in-progress' when you start.
- **update_feature(...):** After implementing, add code_symbols, files,
  technical_notes. After committing, add commit_ids. Update status as work progresses.
- **delete_feature(...):** Only when human explicitly wants to remove a feature.
  This soft-deletes (status='deleted') so it can be reverted via commit history.

## Status lifecycle

planned → in-progress → done
                ↓
            deleted (soft, reversible)
"""

# Find project root (where features.db lives)
PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd()))
DB_PATH = PROJECT_ROOT / "features.db"
MD_PATH = PROJECT_ROOT / "FEATURES.md"

server = Server("feature-tree")


def get_db() -> FeatureDB:
    return FeatureDB(str(DB_PATH))


def regenerate_markdown():
    db = get_db()
    md = generate_markdown(db)
    MD_PATH.write_text(md, encoding="utf-8")
    db.close()


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="search_features",
            description="Fuzzy search features by name, description, or technical notes. Use before starting work to understand what exists.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (matches against name, description, technical_notes)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="add_feature",
            description="Create a new feature. Use when human describes something new.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Unique identifier (slug format, e.g., 'auth-login')"
                    },
                    "name": {
                        "type": "string",
                        "description": "Human-readable feature name"
                    },
                    "parent_id": {
                        "type": "string",
                        "description": "Parent feature ID for hierarchy (optional)"
                    },
                    "description": {
                        "type": "string",
                        "description": "What the feature does"
                    }
                },
                "required": ["id", "name"]
            }
        ),
        Tool(
            name="update_feature",
            description="Update a feature's fields. Use after implementing to record code_symbols, files, commit_ids, status changes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Feature ID to update"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["planned", "in-progress", "done", "deleted"],
                        "description": "Feature status"
                    },
                    "code_symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Function/class/variable names involved"
                    },
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "File paths touched by this feature"
                    },
                    "commit_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Git commit hashes for this feature"
                    },
                    "technical_notes": {
                        "type": "string",
                        "description": "Implementation notes for future reference"
                    },
                    "description": {
                        "type": "string",
                        "description": "Updated description"
                    }
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="delete_feature",
            description="Soft-delete a feature (sets status='deleted'). Feature can be reverted via commit history.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Feature ID to delete"
                    }
                },
                "required": ["id"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    db = get_db()

    try:
        if name == "search_features":
            results = db.search_features(arguments["query"])
            return [TextContent(
                type="text",
                text=json.dumps(results, indent=2, default=str)
            )]

        elif name == "add_feature":
            feature = db.add_feature(
                id=arguments["id"],
                name=arguments["name"],
                parent_id=arguments.get("parent_id"),
                description=arguments.get("description")
            )
            regenerate_markdown()
            return [TextContent(
                type="text",
                text=f"Created feature: {json.dumps(feature, indent=2, default=str)}"
            )]

        elif name == "update_feature":
            feature_id = arguments.pop("id")
            feature = db.update_feature(feature_id, **arguments)
            regenerate_markdown()
            return [TextContent(
                type="text",
                text=f"Updated feature: {json.dumps(feature, indent=2, default=str)}"
            )]

        elif name == "delete_feature":
            feature = db.delete_feature(arguments["id"])
            regenerate_markdown()
            return [TextContent(
                type="text",
                text=f"Deleted feature: {json.dumps(feature, indent=2, default=str)}"
            )]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    finally:
        db.close()


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options(
            instructions=SERVER_INSTRUCTIONS
        ))


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

**Step 2: Test MCP server starts**

Run: `uv run python -c "from feature_tree.mcp_server import server; print('OK')"`
Expected: "OK"

**Step 3: Commit**

```bash
git add feature_tree/mcp_server.py
git commit -m "feat: add MCP server with 4 tools"
```

---

## Task 7: SessionStart Hook

**Files:**
- Create: `feature_tree/session_hook.py`

**Step 1: Write hook script**

```python
# feature_tree/session_hook.py
#!/usr/bin/env python
"""SessionStart hook - injects Feature Tree context."""

print("This project uses Feature Tree for feature management.")
print("Use /commit after completing work to commit + update the tree.")
```

**Step 2: Test hook runs**

Run: `uv run python feature_tree/session_hook.py`
Expected: Two lines of output

**Step 3: Commit**

```bash
git add feature_tree/session_hook.py
git commit -m "feat: add SessionStart hook"
```

---

## Task 8: /commit Command

**Files:**
- Create: `.claude/commands/commit.md`

**Step 1: Create commands directory**

```bash
mkdir -p .claude/commands
```

**Step 2: Write commit command**

```markdown
---
description: "Commit changes and update the feature tree"
---

1. Stage and commit current changes with a descriptive message
2. Push to remote
3. Call update_feature() to record:
   - The commit hash(es) for the feature you worked on
   - Any new code_symbols discovered
   - Any new files touched
   - Update status if appropriate (e.g., planned → in-progress → done)
4. If this was a new feature, use add_feature() first
```

**Step 3: Commit**

```bash
git add .claude/commands/commit.md
git commit -m "feat: add /commit slash command"
```

---

## Task 9: Project Configuration

**Files:**
- Create: `.claude/settings.json`

**Step 1: Write settings**

```json
{
  "mcpServers": {
    "feature-tree": {
      "command": "uv",
      "args": ["run", "python", "feature_tree/mcp_server.py"]
    }
  },
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "uv run python feature_tree/session_hook.py"
          }
        ]
      }
    ]
  }
}
```

**Step 2: Commit**

```bash
git add .claude/settings.json
git commit -m "feat: add project configuration for MCP and hooks"
```

---

## Task 10: Integration Test

**Step 1: Initialize empty feature database**

Run: `uv run python -c "from feature_tree.db import FeatureDB; FeatureDB('features.db')"`
Expected: Creates `features.db`

**Step 2: Generate initial FEATURES.md**

Run: `uv run python -c "from feature_tree.db import FeatureDB; from feature_tree.markdown import generate_markdown; db = FeatureDB('features.db'); print(generate_markdown(db))"`
Expected: Empty feature tree markdown

**Step 3: Run all tests**

Run: `uv run pytest -v`
Expected: All tests pass

**Step 4: Final commit**

```bash
git add features.db FEATURES.md
git commit -m "feat: complete Feature Tree implementation"
```

---

## Summary

| Task | Component | Files |
|------|-----------|-------|
| 1 | Project Setup | pyproject.toml, feature_tree/__init__.py |
| 2 | Database Layer | feature_tree/db.py, tests/test_db.py |
| 3 | CRUD Operations | feature_tree/db.py |
| 4 | Fuzzy Search | feature_tree/db.py |
| 5 | Markdown Generation | feature_tree/markdown.py |
| 6 | MCP Server | feature_tree/mcp_server.py |
| 7 | SessionStart Hook | feature_tree/session_hook.py |
| 8 | /commit Command | .claude/commands/commit.md |
| 9 | Configuration | .claude/settings.json |
| 10 | Integration Test | features.db, FEATURES.md |
