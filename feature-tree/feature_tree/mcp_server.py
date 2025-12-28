# feature_tree/mcp_server.py
#!/usr/bin/env python
"""Feature Tree MCP Server"""

import json
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from feature_tree.db import FeatureDB
from feature_tree.markdown import generate_features_markdown, generate_workflows_markdown


SERVER_INSTRUCTIONS = """
# Feature Tree

Two parallel trees: Features (what exists) and Workflows (how it's used).

## Features (what exists)
- **search_features(query)**: Fuzzy search
- **get_feature(id)**: Full details + linked workflows
- **add_feature(id, name, parent_id?, description?)**
- **update_feature(id, ...)**: Track code_symbols, files, commits, status
- **delete_feature(id)**: Hard if planned, soft if in-progress/done

## Workflows (how features are used)
- **search_workflows(query)**: Fuzzy search journeys/flows
- **get_workflow(id)**: Full details + linked features
- **add_workflow(id, name, type, parent_id?, depends_on?, mermaid?, ...)**
  - type: "journey" (user goal) or "flow" (steps to achieve)
  - depends_on: list of feature IDs this flow uses

## Protocol
1. Search before implementing
2. Features = components, Workflows = how they compose
3. Flows reference features via depends_on
4. When uncertain: ASK

## Status: planned → in-progress → done (or deleted)
"""

def get_project_root() -> Path:
    """Get project root from hook-written file, fallback to cwd."""
    current_project_file = Path.home() / ".feat-tree" / "current-project"
    if current_project_file.exists():
        try:
            return Path(current_project_file.read_text(encoding="utf-8").strip())
        except Exception:
            pass
    return Path(os.getcwd())

mcp = FastMCP(
    "feature-tree",
    instructions=SERVER_INSTRUCTIONS
)


def get_feat_tree_dir() -> Path:
    """Get the .feat-tree directory, creating if needed."""
    feat_tree_dir = get_project_root() / ".feat-tree"
    feat_tree_dir.mkdir(exist_ok=True)
    return feat_tree_dir


def get_db() -> FeatureDB:
    db_path = get_feat_tree_dir() / "features.db"
    return FeatureDB(str(db_path))


def regenerate_markdown():
    db = get_db()
    feat_tree_dir = get_feat_tree_dir()

    # Generate FEATURES.md
    features_md = generate_features_markdown(db)
    (feat_tree_dir / "FEATURES.md").write_text(features_md, encoding="utf-8")

    # Generate WORKFLOWS.md
    workflows_md = generate_workflows_markdown(db)
    (feat_tree_dir / "WORKFLOWS.md").write_text(workflows_md, encoding="utf-8")

    db.close()


@mcp.tool()
def debug_cwd() -> str:
    """Returns path info for debugging."""
    current_project_file = Path.home() / ".feat-tree" / "current-project"
    hook_path = current_project_file.read_text(encoding="utf-8").strip() if current_project_file.exists() else "(not found)"
    return f"os.getcwd(): {os.getcwd()}\nhook file: {hook_path}\nget_project_root(): {get_project_root()}"


@mcp.tool()
def search_features(query: str) -> str:
    """Fuzzy search features by name, description, or technical notes. Use before starting work to understand what exists."""
    db = get_db()
    try:
        results = db.search_features(query)
        # Trim to essential fields only
        trimmed = [
            {"id": r["id"], "name": r["name"], "status": r["status"], "parent_id": r.get("parent_id")}
            for r in results
        ]
        return json.dumps(trimmed)
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
        db.add_feature(id=id, name=name, parent_id=parent_id, description=description)
        regenerate_markdown()
        return '{"ok":true}'
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

        db.update_feature(id, **fields)
        regenerate_markdown()
        return '{"ok":true}'
    finally:
        db.close()


@mcp.tool()
def get_feature(id: str) -> str:
    """Get full details of a single feature by ID, including linked workflows."""
    db = get_db()
    try:
        feature = db.get_feature(id)
        if feature:
            # Add linked workflows
            workflows = db.get_workflows_for_feature(id)
            feature["linked_workflows"] = [
                {"id": w["id"], "name": w["name"], "type": w["type"]}
                for w in workflows
            ]
            return json.dumps(feature, default=str)
        return '{"ok":false,"error":"not found"}'
    finally:
        db.close()


@mcp.tool()
def delete_feature(id: str) -> str:
    """Delete a feature. Hard-deletes if planned, soft-deletes if in-progress/done."""
    db = get_db()
    try:
        result = db.delete_feature(id)
        if result.get("ok"):
            regenerate_markdown()
        return json.dumps(result)
    finally:
        db.close()


# ==================== WORKFLOWS ====================

@mcp.tool()
def search_workflows(query: str) -> str:
    """Fuzzy search workflows (journeys/flows) by name, description, or purpose."""
    db = get_db()
    try:
        results = db.search_workflows(query)
        trimmed = [
            {"id": r["id"], "name": r["name"], "type": r["type"], "status": r["status"], "parent_id": r.get("parent_id")}
            for r in results
        ]
        return json.dumps(trimmed)
    finally:
        db.close()


@mcp.tool()
def add_workflow(
    id: str,
    name: str,
    type: str,
    parent_id: str | None = None,
    description: str | None = None,
    purpose: str | None = None,
    depends_on: list[str] | None = None,
    mermaid: str | None = None
) -> str:
    """Create a workflow. type='journey' for user goals, type='flow' for steps. depends_on links to feature IDs."""
    db = get_db()
    try:
        result = db.add_workflow(
            id=id, name=name, type=type, parent_id=parent_id,
            description=description, purpose=purpose,
            depends_on=depends_on, mermaid=mermaid
        )
        regenerate_markdown()
        return json.dumps(result)
    finally:
        db.close()


@mcp.tool()
def get_workflow(id: str) -> str:
    """Get full details of a workflow by ID, including linked features."""
    db = get_db()
    try:
        workflow = db.get_workflow(id)
        if workflow:
            # Add linked features
            features = db.get_features_for_workflow(id)
            workflow["linked_features"] = [
                {"id": f["id"], "name": f["name"], "status": f["status"]}
                for f in features
            ]
            return json.dumps(workflow, default=str)
        return '{"ok":false,"error":"not found"}'
    finally:
        db.close()


def main():
    mcp.run()


if __name__ == "__main__":
    main()
