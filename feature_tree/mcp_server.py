# feature_tree/mcp_server.py
#!/usr/bin/env python
"""Feature Tree MCP Server"""

import json
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

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

mcp = FastMCP(
    "feature-tree",
    instructions=SERVER_INSTRUCTIONS
)


def get_db() -> FeatureDB:
    return FeatureDB(str(DB_PATH))


def regenerate_markdown():
    db = get_db()
    md = generate_markdown(db)
    MD_PATH.write_text(md, encoding="utf-8")
    db.close()


@mcp.tool()
def search_features(query: str) -> str:
    """Fuzzy search features by name, description, or technical notes. Use before starting work to understand what exists."""
    db = get_db()
    try:
        results = db.search_features(query)
        return json.dumps(results, indent=2, default=str)
    finally:
        db.close()


@mcp.tool()
def add_feature(
    id: str,
    name: str,
    parent_id: str | None = None,
    description: str | None = None
) -> str:
    """Create a new feature. Use when human describes something new."""
    db = get_db()
    try:
        feature = db.add_feature(
            id=id,
            name=name,
            parent_id=parent_id,
            description=description
        )
        regenerate_markdown()
        return f"Created feature: {json.dumps(feature, indent=2, default=str)}"
    finally:
        db.close()


@mcp.tool()
def update_feature(
    id: str,
    status: str | None = None,
    code_symbols: list[str] | None = None,
    files: list[str] | None = None,
    commit_ids: list[str] | None = None,
    technical_notes: str | None = None,
    description: str | None = None
) -> str:
    """Update a feature's fields. Use after implementing to record code_symbols, files, commit_ids, status changes."""
    db = get_db()
    try:
        fields = {}
        if status is not None:
            fields["status"] = status
        if code_symbols is not None:
            fields["code_symbols"] = code_symbols
        if files is not None:
            fields["files"] = files
        if commit_ids is not None:
            fields["commit_ids"] = commit_ids
        if technical_notes is not None:
            fields["technical_notes"] = technical_notes
        if description is not None:
            fields["description"] = description

        feature = db.update_feature(id, **fields)
        regenerate_markdown()
        return f"Updated feature: {json.dumps(feature, indent=2, default=str)}"
    finally:
        db.close()


@mcp.tool()
def delete_feature(id: str) -> str:
    """Soft-delete a feature (sets status='deleted'). Feature can be reverted via commit history."""
    db = get_db()
    try:
        feature = db.delete_feature(id)
        regenerate_markdown()
        return f"Deleted feature: {json.dumps(feature, indent=2, default=str)}"
    finally:
        db.close()


def main():
    mcp.run()


if __name__ == "__main__":
    main()
