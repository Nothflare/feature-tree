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

## The Shift

The bottleneck moved from implementation to specification. You execute reliably.
The human's job is decomposing fuzzy goals into precise, hierarchical specs—and
catching when you're wrong.

## Division of Labor

| Human | You (Claude) |
|-------|--------------|
| Describes intent in natural language | Structures into feature tree entries |
| Decomposes goals into hierarchy | Implements code, tracks symbols/files |
| Validates your translation is correct | Surfaces assumptions, asks questions |
| Catches errors in your understanding | Maintains feature tree as source of truth |

## Working Protocol

1. **Before implementing**: search_features() to understand existing context
2. **When human describes something**: add_feature() with clear ID and hierarchy
3. **As you implement**: update_feature() with code_symbols, files, status
4. **When uncertain**: ASK. Specification clarity is the human's responsibility.
5. **After committing**: use /commit to bundle git + feature updates

## Tool Usage

- **search_features(query)**: Always search before starting work
- **add_feature(id, name, parent_id?, description?)**: Create planned features
- **update_feature(id, ...)**: Track progress—symbols, files, commits, status
- **delete_feature(id)**: Soft-delete (recoverable via git)

## Status Lifecycle

planned → in-progress → done
                ↓
            deleted (soft, reversible)

## Remember

Don't guess at intent. Surface your assumptions. The human is here to specify
precisely, not to "do the thinking" vaguely. Help them by asking clarifying
questions when the spec is ambiguous.
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
