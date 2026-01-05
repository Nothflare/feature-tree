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

Two parallel trees that enable impact analysis and context continuity:
- **Features** = atomic code units (what gets implemented)
- **Workflows** = user-facing experiences (how features compose)

## SESSION

If you see `FT_SESSION=N` in context, pass `_s=N` to all Feature Tree tools.
This ensures data goes to the correct project when multiple sessions run concurrently.

## KEY MANTRAS

1. **"Workflows are the source of truth for data flow"**
2. **"Query the entries, don't just read the text"**
3. **"Trace, don't speculate"**
4. **"Check impact before changing"**
5. **"Create entry before implementing"**

---

## BEFORE ANY IMPLEMENTATION (REQUIRED)

These steps are MANDATORY. Do not skip them.

1. **search_features("relevant terms")**
   - Does this feature already exist?
   - What related features exist?

2. **search_workflows("relevant terms")**
   - What user journeys touch this area?
   - What would break if I change this?

3. **If feature exists: get_feature(id)**
   - What files/symbols are involved?
   - What uses this? (used_by_features)
   - What workflows depend on it? (linked_workflows)

**If you skip these steps, you WILL:**
- Recreate features that exist
- Break workflows you didn't know about
- Miss important context

---

## DATA FLOW TRACING (MANDATORY)

Before implementing, trace the actual data flow:

1. Find the entry point (route, handler, command)
2. Trace what data comes in (request shape)
3. Trace what happens to the data (transformations)
4. Trace what data goes out (response shape)
5. Check linked_workflows for the full journey

**NEVER speculate about:**
- Database schema → read the actual schema
- Request/response shapes → read the actual types
- State structure → read the actual store
- API contracts → read the actual endpoints

**If you don't know, ASK or READ. Don't guess.**

---

## IMPACT ANALYSIS (BEFORE ANY CHANGE)

Before modifying existing code:

1. **get_feature(id)** for the feature you're changing
2. **Check used_by_features:**
   - What other features depend on this?
   - Will your change break them?
3. **Check linked_workflows:**
   - What user journeys use this?
   - Will your change break the flow?

**ESPECIALLY for INFRA.*:**
- Infrastructure is high-impact
- Many features depend on INFRA.*
- ALWAYS check used_by_features before changing

**If impact is unclear, ASK before changing.**

---

## FEATURE LIFECYCLE

Follow this exact sequence:

1. **CREATE** (before implementing)
   ```
   add_feature(id="AUTH.login", name="User Login", status="planned")
   ```

2. **START** (when beginning work)
   ```
   update_feature(id="AUTH.login", status="in-progress")
   ```

3. **TRACK** (during implementation)
   ```
   update_feature(id="AUTH.login",
                  files=["src/auth/login.ts"],
                  code_symbols=["handleLogin", "LoginRequest"])
   ```

4. **COMMIT** (after tests pass)
   ```
   /feature-tree:commit  # bundles git + FT update
   ```

5. **COMPLETE**
   ```
   update_feature(id="AUTH.login", status="done")
   ```

**NEVER:**
- Implement before creating the feature entry
- Use regular git commit instead of /feature-tree:commit
- Forget to update files/symbols after implementing

---

## WHEN TO USE EACH TOOL

### search_features(query)
Use BEFORE any implementation work:
- "Does this feature already exist?" → search before creating
- "What feature owns this code?" → search by file/symbol name
- "What shared utilities exist?" → search "INFRA"

Searches across: id, name, description, technical_notes, files, code_symbols

### search_workflows(query)
Use for understanding user impact:
- "What user journeys exist?" → search by domain
- "If I break this, what flows fail?" → search to find affected workflows

Searches across: id, name, description, purpose

### get_feature(id) — Full Context
Returns everything about a feature:
- **uses_features**: What this feature depends on (forward)
- **used_by_features**: What depends on this feature (reverse)
- **linked_workflows**: Which workflows use this feature

### get_workflow(id) — Workflow Readiness
Returns workflow details plus:
- **linked_features**: Features with their STATUS

Use to check if workflow is implementable:
- All features "done"? → workflow is ready
- Some features "planned"? → workflow is blocked, implement features first

---

## FEATURES

Atomic, implementable units. NOT categories.

| Bad | Good |
|-----|------|
| "User Authentication" (category) | AUTH.login, AUTH.register, AUTH.password_reset |
| "Database" (too broad) | INFRA.database, INFRA.migrations |

### Key Fields
| Field | Purpose | When to Use |
|-------|---------|-------------|
| `files` | Paths touched | After implementing |
| `code_symbols` | Functions, classes, exports | After implementing |
| `technical_notes` | Context code can't capture | "Uses Redis", "Rate limited to 100/min" |
| `uses` | Dependencies on other features | When feature needs INFRA.* or other features |
| `commit_ids` | Which commits implemented this | After /feature-tree:commit |
| `confidence` | How certain (bootstrap) | HIGH=obvious, MEDIUM=inferred, LOW=uncertain |

### Hierarchy
Use `parent_id` for grouping: AUTH is parent, AUTH.login is child.
But each child must still be atomic and independently implementable.

## WORKFLOWS

User-facing experiences that compose features.

Format: `JOURNEY.flow` (e.g., USER_ONBOARDING.signup)

### Key Fields
| Field | Purpose |
|-------|---------|
| `purpose` | WHY this workflow exists (user goal) |
| `description` | WHAT it does (steps involved) |
| `depends_on` | Feature IDs this workflow needs |
| `mermaid` | Visual flow diagram |

### Why Both Trees?
- Feature only → technically correct but UX is accidental
- Workflow only → clear intent but implementation gaps
- Both → change a feature, see which workflows break

## INFRASTRUCTURE (INFRA.*)

Shared utilities: INFRA.database, INFRA.logger, INFRA.rate_limiter, INFRA.config

Features declare dependencies via `uses`:
```
add_feature(id="AUTH.login", uses=["INFRA.rate_limiter", "INFRA.database"])
```

**INFRA.* is high-impact** — always check `used_by_features` before changing.

## DELETE BEHAVIOR

- Status = "planned" → **hard delete** (gone forever)
- Status = "in-progress" or "done" → **soft delete** (recoverable)

## STATUS LIFECYCLE

planned → in-progress → done (or deleted)
"""

def get_project_root(session_id: int | None = None) -> Path:
    """Get project root from session ID or fallback chain."""
    feat_tree_home = Path.home() / ".feat-tree"

    # 1. Session ID lookup (supports concurrent sessions)
    if session_id is not None:
        session_file = feat_tree_home / "sessions" / f"{session_id}.json"
        if session_file.exists():
            try:
                data = json.loads(session_file.read_text(encoding="utf-8"))
                return Path(data["project"])
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
def resync_fts(_s: int | None = None) -> str:
    """Rebuild FTS search index. Use if file/symbol search returns empty results."""
    db = get_db(_s)
    try:
        db._resync_all_fts()
        db.conn.commit()
        return '{"ok":true,"message":"FTS index rebuilt"}'
    finally:
        db.close()


@mcp.tool()
def search_features(query: str, _s: int | None = None) -> str:
    """Fuzzy search features by name, description, or technical notes. Use before starting work to understand what exists."""
    db = get_db(_s)
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
    uses: list[str] | None = None,
    confidence: str | None = None,
    _s: int | None = None
) -> str:
    """Create a new feature. Use when human describes something new."""
    db = get_db(_s)
    try:
        # Validate uses references
        warnings = []
        if uses:
            for ref_id in uses:
                if not db.get_feature(ref_id):
                    warnings.append(f"uses references non-existent feature '{ref_id}'")

        db.add_feature(id=id, name=name, parent_id=parent_id, description=description, uses=uses, confidence=confidence)
        regenerate_markdown(_s)

        result = {"ok": True}
        if warnings:
            result["warnings"] = warnings
        return json.dumps(result)
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
    uses: list[str] | None = None,
    confidence: str | None = None,
    _s: int | None = None
) -> str:
    """Update a feature. ALWAYS record code_symbols + files after implementing. 1x effort now = 10x saved later."""
    db = get_db(_s)
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
        if confidence is not None:
            fields["confidence"] = confidence

        db.update_feature(id, **fields)
        regenerate_markdown(_s)
        return '{"ok":true}'
    finally:
        db.close()


@mcp.tool()
def get_feature(id: str, _s: int | None = None) -> str:
    """Get full details of a single feature by ID, including linked workflows and used features."""
    db = get_db(_s)
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
def delete_feature(id: str, _s: int | None = None) -> str:
    """Delete a feature. Hard-deletes if planned, soft-deletes if in-progress/done."""
    db = get_db(_s)
    try:
        result = db.delete_feature(id)
        if result.get("ok"):
            regenerate_markdown(_s)
        return json.dumps(result)
    finally:
        db.close()


# ==================== WORKFLOWS ====================

@mcp.tool()
def search_workflows(query: str, _s: int | None = None) -> str:
    """Fuzzy search workflows by name, description, or purpose."""
    db = get_db(_s)
    try:
        results = db.search_workflows(query)
        trimmed = []
        for r in results:
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
    _s: int | None = None
) -> str:
    """Create a workflow. Use ID hierarchy: JOURNEY.flow (like features). depends_on links to feature IDs."""
    db = get_db(_s)
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
        regenerate_markdown(_s)

        result = {"ok": True}
        if warnings:
            result["warnings"] = warnings
        return json.dumps(result)
    finally:
        db.close()


@mcp.tool()
def get_workflow(id: str, _s: int | None = None) -> str:
    """Get full details of a workflow by ID, including linked features."""
    db = get_db(_s)
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
    _s: int | None = None
) -> str:
    """Update a workflow's fields."""
    db = get_db(_s)
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

        db.update_workflow(id, **fields)
        regenerate_markdown(_s)
        return '{"ok":true}'
    finally:
        db.close()


@mcp.tool()
def delete_workflow(id: str, _s: int | None = None) -> str:
    """Delete a workflow. Hard if planned, soft if in-progress/done."""
    db = get_db(_s)
    try:
        result = db.delete_workflow(id)
        if result.get("ok"):
            regenerate_markdown(_s)
        return json.dumps(result)
    finally:
        db.close()


def main():
    mcp.run()


if __name__ == "__main__":
    main()
