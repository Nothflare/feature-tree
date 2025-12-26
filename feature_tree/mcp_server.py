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

# Project root from env var (set by plugin.json: "env": {"PROJECT_ROOT": "${PWD}"})
PROJECT_ROOT: Path = Path(os.environ.get("PROJECT_ROOT", os.getcwd()))

mcp = FastMCP(
    "feature-tree",
    instructions=SERVER_INSTRUCTIONS
)


def get_feat_tree_dir() -> Path:
    """Get the .feat-tree directory, creating if needed."""
    feat_tree_dir = PROJECT_ROOT / ".feat-tree"
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
