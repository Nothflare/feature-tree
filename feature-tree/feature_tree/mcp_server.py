# feature_tree/mcp_server.py
#!/usr/bin/env python
"""Feature Tree MCP Server"""

import json
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from feature_tree.db import FeatureDB
from feature_tree.markdown import generate_features_markdown, generate_workflows_markdown
from feature_tree import embeddings


SERVER_INSTRUCTIONS = """
# Feature Tree

Feature Tree connects human intent to code. Workflows are journeys (broad context). Features are atomic units (focused context). Start at the right zoom level for your task with the right context in hand.

Searchable, persist across sessions, and grow with the project.

## Semantic Search

Semantic search lets you jump straight to the right context without guessing or exploring. Prevents duplicates, prevents hallucination, prevents blind spots.

## Features

Atomic, implementable code units. NOT categories.

| Bad | Good |
|-----|------|
| "User Authentication" (category) | AUTH.login, AUTH.register, AUTH.password_reset |
| "Database" (too broad) | INFRA.database, INFRA.migrations |

Shared infrastructure uses `INFRA.*` naming. Features declare dependencies via `uses`:
```
add_feature(id="AUTH.login", uses=["INFRA.database", "INFRA.rate_limiter"])
```

## Workflows

User journeys that compose features. Format: `JOURNEY.flow` (e.g., USER_ONBOARDING.signup)

Workflows link to features via `depends_on`. Check workflow to see if all dependencies are `active` (ready) or some are `planned` (blocked).

## Field Definitions

**Features:**
- `description` — Explain to a YC partner (what it does, user-facing)
- `technical_notes` — Explain to a developer (how it works, gotchas)

**Workflows:**
- `description` — Explain to a YC partner (what the journey is)
- `purpose` — Technical goal (why it exists in the system)
- `steps` — The actual flow in plain language, like a walkthrough

## How Updates Work

**Updates OVERRIDE, not append.** To add a file to existing list:
1. `get_feature(id)` → see current files
2. `update_feature(id, files=[...all files including new one...])`

To remove something:
1. `get_feature(id)` → see current values
2. `update_feature(id, files=[...remaining files...])` — full list without removed item

## When to Update

- **Search BEFORE implementing** (always)
- **Create/update AFTER implementing** — when you know actual files, symbols, dependencies

`being_modified` is for **handoff only** — when handing off mid-task (usually context window limit). Set it and document progress in handoff file so next Claude can continue.

## Status

Status tells you what you CAN DO with something:

| Status | Meaning | Action |
|--------|---------|--------|
| `planned` | Designed, not in code | Don't depend on it yet. Implement first. |
| `active` | Implemented, working | Safe to use and depend on |
| `archived` | Deprecated/removed | Don't use. Update things depending on it. |

**Workflow readiness:**
- depends_on has `planned` → Blocked (implement features first)
- depends_on has `archived` → Broken (remove from depends_on)
- All depends_on `active` → Ready

## Session

If you see `FT_SESSION=N` in context, pass `s=N` to all Feature Tree tools to avoid file conflicts with concurrent projects.
"""

def get_project_root(session_id: int | None = None) -> Path:
    """Get project root from session ID or fallback chain."""
    feat_tree_home = Path.home() / ".feat-tree"

    # 1. Session ID lookup (supports concurrent sessions)
    if session_id is not None:
        sessions_file = feat_tree_home / "sessions.json"
        if sessions_file.exists():
            try:
                sessions = json.loads(sessions_file.read_text(encoding="utf-8"))
                # sessions is {project_path: session_id}, reverse lookup
                for project, sid in sessions.items():
                    if sid == session_id:
                        return Path(project)
            except Exception:
                pass

    # 2. Hook-written file (backwards compatibility)
    current_project_file = feat_tree_home / "current-project"
    if current_project_file.exists():
        try:
            return Path(current_project_file.read_text(encoding="utf-8").strip())
        except Exception:
            pass

    # 3. Fallback to cwd
    return Path(os.getcwd())

mcp = FastMCP(
    "feature-tree",
    instructions=SERVER_INSTRUCTIONS
)


def get_feat_tree_dir(session_id: int | None = None) -> Path:
    """Get the .feat-tree directory, creating if needed."""
    feat_tree_dir = get_project_root(session_id) / ".feat-tree"
    feat_tree_dir.mkdir(exist_ok=True)
    return feat_tree_dir


def get_db(session_id: int | None = None) -> FeatureDB:
    db_path = get_feat_tree_dir(session_id) / "features.db"
    return FeatureDB(str(db_path))


def regenerate_markdown(session_id: int | None = None):
    db = get_db(session_id)
    feat_tree_dir = get_feat_tree_dir(session_id)

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
def resync_fts(s: int | None = None) -> str:
    """Rebuild FTS search index. Use if file/symbol search returns empty results."""
    db = get_db(s)
    try:
        db._resync_all_fts()
        db.conn.commit()
        return '{"ok":true,"message":"FTS index rebuilt"}'
    finally:
        db.close()


@mcp.tool()
def search_features(query: str, s: int | None = None) -> str:
    """Semantic search for features. Use BEFORE implementing to find existing features and prevent duplicates.

    Returns: id, name, status, parent_id, uses_count, confidence."""
    db = get_db(s)
    try:
        db_path = get_feat_tree_dir(s)

        # Semantic search first (top 10) - wrapped in try/except for robustness
        try:
            semantic_ids = embeddings.search_features_semantic(query, db_path, n_results=10)
        except Exception:
            # ChromaDB or API failure - fallback to FTS only
            semantic_ids = []

        # FTS search (top 10)
        fts_results = db.search_features(query)
        fts_ids = [r["id"] for r in fts_results[:10]]

        # Merge: semantic first, then FTS additions (deduplicated)
        seen = set()
        merged_ids = []
        for fid in semantic_ids + fts_ids:
            if fid not in seen:
                seen.add(fid)
                merged_ids.append(fid)

        # Load features and trim to essential fields
        trimmed = []
        for fid in merged_ids[:10]:
            r = db.get_feature(fid)
            if r:
                item = {"id": r["id"], "name": r["name"], "status": r["status"], "parent_id": r.get("parent_id")}
                if r.get("uses"):
                    uses_list = json.loads(r["uses"])
                    if uses_list:
                        item["uses_count"] = len(uses_list)
                if r.get("confidence"):
                    item["confidence"] = r["confidence"]
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
    technical_notes: str | None = None,
    status: str = "planned",
    being_modified: str = "none",
    important_message: str | None = None,
    files: list[str] | None = None,
    code_symbols: list[dict] | None = None,
    uses: list[str] | None = None,
    confidence: str | None = None,
    s: int | None = None
) -> str:
    """Create a new feature. Use when human describes something new.

    status: planned | active | archived
    being_modified: none | building | refactoring | fixing | extending
    code_symbols: [{name, location, valid}] - location is file path (no line numbers)"""
    db = get_db(s)
    try:
        # Validate uses references
        warnings = []
        if uses:
            for ref_id in uses:
                if not db.get_feature(ref_id):
                    warnings.append(f"uses references non-existent feature '{ref_id}'")

        feature = db.add_feature(
            id=id, name=name, parent_id=parent_id, description=description,
            technical_notes=technical_notes, status=status, being_modified=being_modified,
            important_message=important_message, files=files, code_symbols=code_symbols,
            uses=uses, confidence=confidence
        )
        regenerate_markdown(s)

        # Embed for semantic search (async, non-blocking)
        embeddings.embed_feature(feature, get_feat_tree_dir(s))

        result = {"ok": True}
        if warnings:
            result["warnings"] = warnings
        return json.dumps(result)
    finally:
        db.close()


@mcp.tool()
def update_feature(
    id: str,
    name: str | None = None,
    description: str | None = None,
    technical_notes: str | None = None,
    status: str | None = None,
    being_modified: str | None = None,
    important_message: str | None = None,
    files: list[str] | None = None,
    code_symbols: list[dict] | None = None,
    uses: list[str] | None = None,
    confidence: str | None = None,
    commit_ids: list[str] | None = None,
    s: int | None = None
) -> str:
    """Update a feature. ALWAYS record code_symbols + files after implementing.

    status: planned | active | archived
    being_modified: none | building | refactoring | fixing | extending
    code_symbols: [{name, location, valid}] - location is file path (no line numbers)
    important_message: Claude-to-Claude sticky note (persists across sessions)"""
    db = get_db(s)
    try:
        fields = {}
        if name is not None:
            fields["name"] = name
        if description is not None:
            fields["description"] = description
        if technical_notes is not None:
            fields["technical_notes"] = technical_notes
        if status is not None:
            fields["status"] = status
        if being_modified is not None:
            fields["being_modified"] = being_modified
        if important_message is not None:
            fields["important_message"] = important_message
        if files is not None:
            fields["files"] = files
        if code_symbols is not None:
            fields["code_symbols"] = code_symbols
        if uses is not None:
            fields["uses"] = uses
        if confidence is not None:
            fields["confidence"] = confidence
        if commit_ids is not None:
            fields["commit_ids"] = commit_ids

        updated = db.update_feature(id, **fields)
        regenerate_markdown(s)

        # Re-embed if any searchable text changed
        text_fields = {"name", "description", "technical_notes", "files", "code_symbols"}
        if updated and fields.keys() & text_fields:
            embeddings.embed_feature(updated, get_feat_tree_dir(s))

        return '{"ok":true}'
    finally:
        db.close()


@mcp.tool()
def get_feature(id: str, s: int | None = None) -> str:
    """Get full feature context. Use AFTER search to see files, symbols, dependencies, and what depends on this.

    Returns: status, files, symbols, uses, used_by, linked_workflows, important_message."""
    db = get_db(s)
    try:
        f = db.get_feature(id)
        if not f:
            return '{"ok":false,"error":"not found"}'

        # Get relationships
        used_by = db.get_features_using(id)
        workflows = db.get_workflows_for_feature(id)
        uses_ids = json.loads(f.get("uses") or "[]")

        # Build compact output
        lines = [f"{f['id']} [{f.get('status', 'planned')}] [{f.get('being_modified', 'none')}]"]

        if f.get("important_message"):
            lines.append(f"⚠️ {f['important_message']}")

        lines.append("")

        # Files (first 5)
        files = json.loads(f.get("files") or "[]")
        files_str = ", ".join(files[:5]) if files else "none"
        if len(files) > 5:
            files_str += f" (+{len(files) - 5} more)"
        lines.append(f"Files: {files_str}")

        # Symbols (first 5) - names only, use search to find actual locations
        symbols = json.loads(f.get("code_symbols") or "[]")
        if symbols:
            symbol_strs = []
            for sym in symbols[:5]:
                if isinstance(sym, dict):
                    symbol_strs.append(sym.get("name", "?"))
                else:
                    symbol_strs.append(str(sym))
            symbols_str = ", ".join(symbol_strs)
            if len(symbols) > 5:
                symbols_str += f" (+{len(symbols) - 5} more)"
            lines.append(f"Symbols: {symbols_str}")
        else:
            lines.append("Symbols: none")

        lines.append("")

        # Dependencies
        uses_str = ", ".join(uses_ids[:5]) if uses_ids else "none"
        lines.append(f"Uses: {uses_str}")
        used_by_ids = [ub["id"] for ub in used_by]
        lines.append(f"Used by ({len(used_by_ids)}): {', '.join(used_by_ids[:5])}")
        workflow_ids = [w["id"] for w in workflows]
        lines.append(f"Workflows ({len(workflow_ids)}): {', '.join(workflow_ids[:5])}")

        lines.append("")

        # Summaries
        if f.get("description"):
            lines.append(f"Desc: {f['description'][:100]}")
        if f.get("technical_notes"):
            lines.append(f"Tech: {f['technical_notes'][:100]}")

        return "\n".join(lines)
    finally:
        db.close()


@mcp.tool()
def delete_feature(id: str, s: int | None = None) -> str:
    """Delete a feature. Hard-deletes if planned, soft-deletes (archived) if active."""
    db = get_db(s)
    try:
        result = db.delete_feature(id)
        if result.get("ok"):
            regenerate_markdown(s)
            # Remove from embeddings index
            embeddings.delete_feature_embedding(id, get_feat_tree_dir(s))
        return json.dumps(result)
    finally:
        db.close()


# ==================== WORKFLOWS ====================

@mcp.tool()
def search_workflows(query: str, s: int | None = None) -> str:
    """Semantic search for workflows. Start here for broad context — one workflow often has all context needed for a task.

    Returns: id, name, status, parent_id, depends_on_count."""
    db = get_db(s)
    try:
        db_path = get_feat_tree_dir(s)

        # Semantic search first - wrapped in try/except for robustness
        try:
            semantic_ids = embeddings.search_workflows_semantic(query, db_path, n_results=10)
        except Exception:
            # ChromaDB or API failure - fallback to FTS only
            semantic_ids = []

        # FTS search
        fts_results = db.search_workflows(query)
        fts_ids = [r["id"] for r in fts_results[:10]]

        # Merge deduplicated
        seen = set()
        merged_ids = []
        for wid in semantic_ids + fts_ids:
            if wid not in seen:
                seen.add(wid)
                merged_ids.append(wid)

        trimmed = []
        for wid in merged_ids[:10]:
            r = db.get_workflow(wid)
            if r:
                item = {"id": r["id"], "name": r["name"], "status": r["status"], "parent_id": r.get("parent_id")}
                if r.get("confidence"):
                    item["confidence"] = r["confidence"]
                trimmed.append(item)

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
    mermaid: str | None = None,
    confidence: str | None = None,
    s: int | None = None
) -> str:
    """Create a workflow. Use ID hierarchy: JOURNEY.flow (like features). depends_on links to feature IDs."""
    db = get_db(s)
    try:
        # Validate depends_on references
        warnings = []
        if depends_on:
            for ref_id in depends_on:
                if not db.get_feature(ref_id):
                    warnings.append(f"depends_on references non-existent feature '{ref_id}'")

        db.add_workflow(
            id=id, name=name, parent_id=parent_id,
            description=description, purpose=purpose,
            depends_on=depends_on, mermaid=mermaid,
            confidence=confidence
        )
        regenerate_markdown(s)

        # Embed for semantic search
        workflow = db.get_workflow(id)
        if workflow:
            embeddings.embed_workflow(workflow, get_feat_tree_dir(s))

        result = {"ok": True}
        if warnings:
            result["warnings"] = warnings
        return json.dumps(result)
    finally:
        db.close()


@mcp.tool()
def get_workflow(id: str, s: int | None = None) -> str:
    """Get full workflow context. Atomic documentation for a user journey.

    Returns: description, purpose, steps, depends_on features with their status (ready/blocked)."""
    db = get_db(s)
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
    purpose: str | None = None,
    confidence: str | None = None,
    s: int | None = None
) -> str:
    """Update a workflow's fields."""
    db = get_db(s)
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
        if confidence is not None:
            fields["confidence"] = confidence

        updated = db.update_workflow(id, **fields)
        regenerate_markdown(s)

        # Re-embed if searchable text changed
        text_fields = {"name", "description", "purpose", "depends_on"}
        if updated and fields.keys() & text_fields:
            embeddings.embed_workflow(updated, get_feat_tree_dir(s))

        return '{"ok":true}'
    finally:
        db.close()


@mcp.tool()
def delete_workflow(id: str, s: int | None = None) -> str:
    """Delete a workflow. Hard if planned, soft (archived) if active."""
    db = get_db(s)
    try:
        result = db.delete_workflow(id)
        if result.get("ok"):
            regenerate_markdown(s)
            embeddings.delete_workflow_embedding(id, get_feat_tree_dir(s))
        return json.dumps(result)
    finally:
        db.close()


def main():
    mcp.run()


if __name__ == "__main__":
    main()
