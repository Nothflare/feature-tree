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

Two parallel trees: Features (atomic code units) and Workflows (user-facing experiences).

## ATOMIC FEATURES

Features are small, implementable units. NOT categories.

BAD: "User Authentication" (category - can't implement in one task)
GOOD: "User Login", "Email Verification", "Password Reset" (atomic - one task each)

Rule: If you can't "implement this feature" and get a complete, testable unit - it's not atomic enough.

## WHY TRACK SYMBOLS, FILES, NOTES

Every 1x effort noting these = 10x saved later.

| Field | Purpose | Example |
|-------|---------|---------|
| Symbols | LSP-queryable identifiers | handleLogin, UserSession |
| Files | Paths involved | src/auth/login.ts |
| Notes | What code can't capture | "Uses Redis for rate limiting" |

Without tracking: You guess → inconsistent code → hours debugging.
With tracking: Query symbols → read only relevant files → precise edits.

DO NOT skip this. It's what keeps the codebase flexible as it grows.

## WORKFLOWS

Workflows = user-facing experiences, structured like features.

Use ID hierarchy: `USER_ONBOARDING.signup` (parent.child, like features)
- Parent = journey (category)
- Child = flow (atomic)

Example: `USER_ONBOARDING.signup` depends on [AUTH.register, AUTH.email_verify]

Why both trees?
- Features only → technically correct but UX is accidental
- Workflows only → clear intent but implementation gaps
- Both → modify a feature, see which workflows break. Design a workflow, see what features exist vs. need building.

## INFRASTRUCTURE

Use naming convention `INFRA.*` for shared utilities (rate limiter, cache, etc.)

Features can declare `uses` to link to other features they depend on:
- AUTH.login uses [INFRA.rate_limiter]
- get_feature shows both `uses_features` and `used_by_features`

No separate "infra type" - just features with INFRA.* IDs.

## Tools

Features: search_features, get_feature, add_feature, update_feature, delete_feature
Workflows: search_workflows, get_workflow, add_workflow, update_workflow, delete_workflow

## Protocol
1. Search before implementing
2. Features = atomic units, Workflows = compositions
3. ALWAYS update symbols/files/notes after implementing
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
        trimmed = []
        for r in results:
            item = {"id": r["id"], "name": r["name"], "status": r["status"], "parent_id": r.get("parent_id")}
            if r.get("uses"):
                uses_list = json.loads(r["uses"])
                if uses_list:
                    item["uses_count"] = len(uses_list)
            trimmed.append(item)
        return json.dumps(trimmed)
    finally:
        db.close()


@mcp.tool()
def add_feature(
    id: str,
    name: str,
    parent_id: str | None = None,
    description: str | None = None,
    uses: list[str] | None = None
) -> str:
    """Create a new feature. Use when human describes something new."""
    db = get_db()
    try:
        db.add_feature(id=id, name=name, parent_id=parent_id, description=description, uses=uses)
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
    description: str | None = None,
    uses: list[str] | None = None
) -> str:
    """Update a feature. ALWAYS record code_symbols + files after implementing. 1x effort now = 10x saved later."""
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
        if uses is not None:
            fields["uses"] = uses

        db.update_feature(id, **fields)
        regenerate_markdown()
        return '{"ok":true}'
    finally:
        db.close()


@mcp.tool()
def get_feature(id: str) -> str:
    """Get full details of a single feature by ID, including linked workflows and used features."""
    db = get_db()
    try:
        feature = db.get_feature(id)
        if feature:
            # Add linked workflows
            workflows = db.get_workflows_for_feature(id)
            feature["linked_workflows"] = [
                {"id": w["id"], "name": w["name"]}
                for w in workflows
            ]

            # Add features this feature uses (forward lookup)
            if feature.get("uses"):
                uses_ids = json.loads(feature["uses"])
                feature["uses_features"] = [
                    {"id": f["id"], "name": f["name"]}
                    for uid in uses_ids
                    if (f := db.get_feature(uid))
                ]

            # Add features that use this feature (reverse lookup)
            used_by = db.get_features_using(id)
            if used_by:
                feature["used_by_features"] = [
                    {"id": f["id"], "name": f["name"]}
                    for f in used_by
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
    """Fuzzy search workflows by name, description, or purpose."""
    db = get_db()
    try:
        results = db.search_workflows(query)
        trimmed = [
            {"id": r["id"], "name": r["name"], "status": r["status"], "parent_id": r.get("parent_id")}
            for r in results
        ]
        return json.dumps(trimmed)
    finally:
        db.close()


@mcp.tool()
def add_workflow(
    id: str,
    name: str,
    parent_id: str | None = None,
    description: str | None = None,
    purpose: str | None = None,
    depends_on: list[str] | None = None,
    mermaid: str | None = None
) -> str:
    """Create a workflow. Use ID hierarchy: JOURNEY.flow (like features). depends_on links to feature IDs."""
    db = get_db()
    try:
        result = db.add_workflow(
            id=id, name=name, parent_id=parent_id,
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


@mcp.tool()
def update_workflow(
    id: str,
    status: str | None = None,
    depends_on: list[str] | None = None,
    mermaid: str | None = None,
    description: str | None = None,
    purpose: str | None = None
) -> str:
    """Update a workflow's fields."""
    db = get_db()
    try:
        fields = {}
        if status is not None:
            fields["status"] = status
        if depends_on is not None:
            fields["depends_on"] = depends_on
        if mermaid is not None:
            fields["mermaid"] = mermaid
        if description is not None:
            fields["description"] = description
        if purpose is not None:
            fields["purpose"] = purpose

        db.update_workflow(id, **fields)
        regenerate_markdown()
        return '{"ok":true}'
    finally:
        db.close()


@mcp.tool()
def delete_workflow(id: str) -> str:
    """Delete a workflow. Hard if planned, soft if in-progress/done."""
    db = get_db()
    try:
        result = db.delete_workflow(id)
        if result.get("ok"):
            regenerate_markdown()
        return json.dumps(result)
    finally:
        db.close()


def main():
    mcp.run()


if __name__ == "__main__":
    main()
