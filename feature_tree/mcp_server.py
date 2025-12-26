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

Single source of truth for what this project does. Human specifies, you execute.

## Tools

- **search_features(query)**: Search before starting work
- **add_feature(id, name, parent_id?, description?)**: Create with status='planned'
- **update_feature(id, ...)**: Track code_symbols, files, commits, status
- **delete_feature(id)**: Soft-delete (status='deleted')

## Protocol

1. Search existing features before implementing
2. add_feature() when human describes something new
3. update_feature() as you work—track symbols, files, status
4. When uncertain: ASK. Don't guess at intent.
5. Use /commit to bundle git + feature updates

## Status: planned → in-progress → done (or deleted)
"""

mcp = FastMCP(
    "feature-tree",
    instructions=SERVER_INSTRUCTIONS
)


def get_project_root() -> Path:
    """Get the project root directory from various sources."""
    # Try environment variables Claude Code might set
    for env_var in ["CLAUDE_PROJECT_DIR", "PROJECT_DIR", "PWD"]:
        if path := os.environ.get(env_var):
            return Path(path)

    # Look for .feat-tree/.project_root marker (written by ft-mem hook)
    cwd = Path.cwd()
    for search_dir in [cwd] + list(cwd.parents):
        marker = search_dir / ".feat-tree" / ".project_root"
        if marker.exists():
            try:
                return Path(marker.read_text(encoding="utf-8").strip())
            except:
                pass

    # Fallback: look for .git directory going up from cwd
    for parent in [cwd] + list(cwd.parents):
        if (parent / ".git").exists():
            return parent

    # Last resort: use cwd (may be wrong in plugin context)
    return cwd


def get_feat_tree_dir() -> Path:
    """Get the .feat-tree directory, creating if needed."""
    project_root = get_project_root()
    feat_tree_dir = project_root / ".feat-tree"
    feat_tree_dir.mkdir(exist_ok=True)
    return feat_tree_dir


def get_db() -> FeatureDB:
    db_path = get_feat_tree_dir() / "features.db"
    return FeatureDB(str(db_path))


def regenerate_markdown():
    db = get_db()
    md = generate_markdown(db)
    md_path = get_feat_tree_dir() / "FEATURES.md"
    md_path.write_text(md, encoding="utf-8")
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
