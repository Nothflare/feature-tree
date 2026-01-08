# Feature Tree v3 Design

> **For Claude:** REQUIRED SUB-SKILL: Use feature-tree:executing-plans to implement this design.

## Context

Feature Tree v2.2.7 is stable. v3 introduces:
- Clean state model (lifecycle vs activity separation)
- JIT reminder hooks (Claude gets context on Read/Edit)
- Richer data structures (structured symbols, important messages)
- Semantic search (embeddings)
- Global awareness skill

**Philosophy:** Hooks = JIT reminders, not automation. Claude (complex system) makes decisions; FT provides data; hooks nudge.

---

## Discovery Summary

### First Principle
- **Surface request:** "Auto context injection", "better subagent utilization"
- **Actual intention:** Claude should agentically USE Feature Tree with minimal friction
- **Approach:** JIT reminders surface context; Claude decides what to do with it

### Crux
- **Core assumption:** JIT reminders will influence Claude's behavior
- **Test:** Observe if Claude references reminders in reasoning
- **Status:** Partially validated (SessionStart works, PreToolUse untested)

### Scope Fence
- **This IS:** Semantic data layer + JIT reminders for agentic Claude
- **This is NOT:** Automation bypassing Claude's judgment, visual UI (v4), multi-user sync

### Pre-Mortem Mitigations
1. Reminders must be <50ms (SQLite reads, no LLM)
2. Reminders must be actionable ("5 dependents, run get_feature()")
3. Reminders must be sparse (only on significant context)

---

## Data Model Changes

### Status Enum (v2 → v3)

| v2 | v3 | Migration |
|----|----|-----------|
| `planned` | `planned` | No change |
| `in_progress` | `active` | + `being_modified=building` |
| `done` | `active` | + `being_modified=none` |
| `deleted` | `archived` | No change |

### New Fields

```sql
ALTER TABLE features ADD COLUMN being_modified TEXT DEFAULT 'none';
-- Values: none, building, refactoring, fixing, extending

ALTER TABLE features ADD COLUMN important_message TEXT;
-- Claude-to-Claude sticky note

ALTER TABLE features ADD COLUMN archived_at TEXT;
-- Timestamp when status became 'archived'
```

### `being_modified` Values

| Value | Meaning | Valid with status |
|-------|---------|-------------------|
| `none` | Idle, no active work | any |
| `building` | First-time implementation | `planned` |
| `refactoring` | Changing implementation | `active` |
| `fixing` | Addressing a bug | `active` |
| `extending` | Adding capabilities | `active` |

### State Combinations

| Scenario | status | being_modified |
|----------|--------|----------------|
| Feature designed, not built | `planned` | `none` |
| Claude building new feature | `planned` | `building` |
| Feature complete, idle | `active` | `none` |
| Claude refactoring | `active` | `refactoring` |
| Claude fixing bug | `active` | `fixing` |
| Feature removed | `archived` | `none` |

### Structured `code_symbols`

```python
# v2: Array of strings
["handleLogin", "validateCredentials"]

# v3: Array of objects (location = file path only, NO line numbers - they go stale)
[
  {"name": "handleLogin", "location": "src/auth/login.ts", "valid": True},
  {"name": "validateCredentials", "location": "src/auth/login.ts", "valid": True}
]
```

**Note:** Line numbers are NOT stored because they become stale immediately as code changes. Claude should use its search tools (Grep) to find current line numbers when needed.

### Migration Logic

```python
def migrate_v2_to_v3(db):
    # Status migration
    db.execute("UPDATE features SET status = 'active' WHERE status = 'done'")
    db.execute("""
        UPDATE features
        SET status = 'active', being_modified = 'building'
        WHERE status = 'in_progress'
    """)
    db.execute("UPDATE features SET status = 'archived' WHERE status = 'deleted'")

    # code_symbols migration (strings → objects)
    for feature in db.execute("SELECT id, code_symbols FROM features"):
        if feature.code_symbols:
            symbols = json.loads(feature.code_symbols)
            if symbols and isinstance(symbols[0], str):
                # Old format, migrate
                new_symbols = [
                    {"name": s, "location": None, "valid": True}
                    for s in symbols
                ]
                db.execute(
                    "UPDATE features SET code_symbols = ? WHERE id = ?",
                    [json.dumps(new_symbols), feature.id]
                )
```

---

## MCP Tool Changes

### `update_feature()` — New Parameters

```python
def update_feature(
    id: str,
    name: str = None,
    description: str = None,
    technical_notes: str = None,
    status: Literal["planned", "active", "archived"] = None,
    being_modified: Literal["none", "building", "refactoring", "fixing", "extending"] = None,
    important_message: str = None,
    files: List[str] = None,
    code_symbols: List[dict] = None,  # [{name, location, valid}]
    uses: List[str] = None,
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = None,
    commit_ids: List[str] = None,
    s: int = None
):
```

### `get_feature()` — Compact Output

```python
def get_feature(id: str, s: int = None) -> str:
    """Returns compact 10-line feature summary."""
    f = load_feature(id)
    used_by = get_used_by_features(f.id)
    workflows = get_linked_workflows(f.id)

    lines = [
        f"{f.id} [{f.status}] [{f.being_modified}]"
    ]

    if f.important_message:
        lines.append(f"⚠️ {f.important_message}")

    lines.append("")

    # Files
    files_str = ", ".join(f.files[:5]) if f.files else "none"
    lines.append(f"Files: {files_str}")

    # Symbols with line numbers
    if f.code_symbols:
        symbol_strs = []
        for sym in f.code_symbols[:5]:
            if isinstance(sym, dict):
                loc = sym.get("location", "").split(":")[-1] if sym.get("location") else "?"
                symbol_strs.append(f"{sym['name']}:{loc}")
            else:
                symbol_strs.append(sym)
        lines.append(f"Symbols: {', '.join(symbol_strs)}")
    else:
        lines.append("Symbols: none")

    lines.append("")

    # Dependencies
    uses_str = ", ".join(f.uses[:5]) if f.uses else "none"
    lines.append(f"Uses: {uses_str}")
    lines.append(f"Used by ({len(used_by)}): {', '.join(used_by[:5])}")
    lines.append(f"Workflows ({len(workflows)}): {', '.join(workflows[:5])}")

    lines.append("")

    # Summaries
    if f.description:
        lines.append(f"Desc: {f.description[:100]}")
    if f.technical_notes:
        lines.append(f"Tech: {f.technical_notes[:100]}")

    return "\n".join(lines)
```

**Example output:**
```
AUTH.login [active] [refactoring]
⚠️ Rate limiter was causing 500s. Don't remove the 100ms delay.

Files: src/auth/login.ts, src/auth/helpers.ts
Symbols: handleLogin, validateCredentials, createSession

Uses: INFRA.session, INFRA.rate_limiter
Used by (3): AUTH.logout, AUTH.session, AUTH.password_reset
Workflows (2): USER.login_flow, USER.password_reset_flow

Desc: Validates credentials, creates session, handles rate limiting.
Tech: bcrypt cost 12, JWT RS256, Redis sessions
```

### `add_feature()` — New Parameters

```python
def add_feature(
    id: str,
    name: str,
    description: str = None,
    technical_notes: str = None,
    status: Literal["planned", "active", "archived"] = "planned",
    being_modified: Literal["none", "building", "refactoring", "fixing", "extending"] = "none",
    important_message: str = None,
    parent_id: str = None,
    files: List[str] = None,
    code_symbols: List[dict] = None,
    uses: List[str] = None,
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = None,
    s: int = None
):
```

---

## JIT Reminder Hooks

### Hook Configuration

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear",
        "hooks": [{
          "type": "command",
          "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run-python-hook.cmd\" session-start.py"
        }]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Read|Edit",
        "hooks": [{
          "type": "command",
          "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run-python-hook.cmd\" jit-reminder.py"
        }]
      }
    ]
  }
}
```

### `jit-reminder.py`

```python
#!/usr/bin/env python3
"""JIT reminder for PreToolUse(Read|Edit)."""
import json
import sys
import sqlite3
from pathlib import Path

def main():
    try:
        input_data = json.load(sys.stdin)
    except:
        print(json.dumps({}))
        return

    tool_input = input_data.get("input", {})
    file_path = tool_input.get("file_path") or tool_input.get("path")

    if not file_path:
        print(json.dumps({}))
        return

    # Find feature by file
    feature = find_feature_by_file(file_path)
    if not feature:
        print(json.dumps({}))
        return

    # Build reminder
    if feature["being_modified"] != "none":
        reminder = build_rich_reminder(feature)
    else:
        used_by_count = count_used_by(feature["id"])
        reminder = f"📍 {feature['id']} ({used_by_count} dependents)"

    print(json.dumps({
        "hookSpecificOutput": {
            "additionalContext": reminder
        }
    }))

def find_feature_by_file(file_path):
    """Query features.db for feature containing this file."""
    cwd = get_cwd()
    db_path = Path(cwd) / ".feat-tree" / "features.db"
    if not db_path.exists():
        return None

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Normalize path for matching
    normalized = file_path.replace("\\", "/")

    # Search features with this file
    cursor = conn.execute(
        "SELECT * FROM features WHERE files LIKE ? AND status != 'archived'",
        [f'%{normalized}%']
    )
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None

def build_rich_reminder(feature):
    """Build rich context for active feature."""
    lines = [
        f"📍 {feature['id']} [{feature['status']}] [{feature['being_modified']}]"
    ]

    if feature.get("important_message"):
        lines.append(f"⚠️ {feature['important_message']}")

    uses = json.loads(feature.get("uses") or "[]")
    lines.append(f"Uses: {', '.join(uses) if uses else 'none'}")

    used_by = get_used_by(feature["id"])
    lines.append(f"Used by ({len(used_by)}): {', '.join(used_by[:3])}")

    workflows = get_linked_workflows(feature["id"])
    lines.append(f"Workflows: {', '.join(workflows[:3])}")

    lines.append(f"\nRun get_feature(\"{feature['id']}\") for full context.")

    return "\n".join(lines)

def count_used_by(feature_id):
    """Count features that use this feature."""
    # Implementation queries features where uses contains feature_id
    pass

def get_used_by(feature_id):
    """Get list of feature IDs that use this feature."""
    pass

def get_linked_workflows(feature_id):
    """Get workflows that depend on this feature."""
    pass

def get_cwd():
    """Get current working directory from session."""
    pass

if __name__ == "__main__":
    main()
```

---

## Semantic Search (Embeddings)

### Why Embeddings over FTS

| FTS (v2) | Embeddings (v3) |
|----------|-----------------|
| Keyword matching | Conceptual matching |
| "auth" doesn't find "login" | "auth" finds "login", "signin", "credentials" |
| Requires exact/similar words | Understands meaning |
| Fast but dumb | Slightly slower but smart |

### Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  add_feature()  │────▶│  Embed text      │────▶│  ChromaDB       │
│  update_feature │     │  (sentence-      │     │  (vector store) │
└─────────────────┘     │   transformers)  │     └─────────────────┘
                        └──────────────────┘              │
                                                          │
┌─────────────────┐     ┌──────────────────┐              │
│ search_features │────▶│  Embed query     │──────────────┘
│                 │◀────│  Vector search   │
└─────────────────┘     └──────────────────┘
```

### Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Embedding Model | `all-MiniLM-L6-v2` | Small (80MB), fast, good quality, offline |
| Vector Store | ChromaDB | Embedded, no server, handles embeddings, simple API |
| Fallback | FTS5 | If embeddings fail/slow, fall back to keyword search |

### Storage

```
.feat-tree/
├── features.db        # SQLite (existing)
├── chroma/            # NEW: ChromaDB vector store
│   ├── features/      # Feature embeddings
│   └── workflows/     # Workflow embeddings
```

### What Gets Embedded

**Features:** Concatenated text of searchable fields
```python
def feature_to_text(f):
    """Convert feature to embeddable text."""
    parts = [
        f.id,
        f.name,
        f.description or "",
        f.technical_notes or "",
        " ".join(f.files or []),
        " ".join(s["name"] for s in f.code_symbols or [])
    ]
    return " ".join(parts)
```

**Workflows:** Concatenated text
```python
def workflow_to_text(w):
    """Convert workflow to embeddable text."""
    parts = [
        w.id,
        w.name,
        w.description or "",
        w.purpose or "",
        " ".join(w.depends_on or [])
    ]
    return " ".join(parts)
```

### Implementation

```python
import chromadb
from sentence_transformers import SentenceTransformer

# Initialize once per session
_model = None
_chroma = None

def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def get_chroma_client(db_path):
    global _chroma
    if _chroma is None:
        _chroma = chromadb.PersistentClient(path=str(db_path / "chroma"))
    return _chroma

def embed_feature(feature, db_path):
    """Add/update feature embedding in ChromaDB."""
    client = get_chroma_client(db_path)
    collection = client.get_or_create_collection("features")

    text = feature_to_text(feature)

    collection.upsert(
        ids=[feature.id],
        documents=[text],
        metadatas=[{"status": feature.status, "being_modified": feature.being_modified}]
    )

def search_features_semantic(query: str, db_path, n_results=10):
    """Semantic search for features."""
    client = get_chroma_client(db_path)
    collection = client.get_or_create_collection("features")

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where={"status": {"$ne": "archived"}}  # Exclude archived
    )

    return results["ids"][0] if results["ids"] else []
```

### Hybrid Search (Semantic + FTS)

For best results, combine both:

```python
def search_features(query: str, s: int = None) -> List[dict]:
    """Hybrid search: semantic + FTS, deduplicated."""
    db_path = get_db_path(s)

    # Semantic search (top 10)
    semantic_ids = search_features_semantic(query, db_path, n_results=10)

    # FTS search (top 10)
    fts_ids = search_features_fts(query, db_path, n_results=10)

    # Merge, semantic results first, then FTS additions
    seen = set()
    merged = []
    for id in semantic_ids + fts_ids:
        if id not in seen:
            seen.add(id)
            merged.append(id)

    # Load full features
    return [load_feature(id, db_path) for id in merged[:10]]
```

### Migration: Embed Existing Features

```python
def migrate_embeddings(db_path):
    """Create embeddings for all existing features/workflows."""
    conn = sqlite3.connect(db_path / "features.db")

    # Embed features
    for row in conn.execute("SELECT * FROM features WHERE status != 'archived'"):
        feature = dict(row)
        embed_feature(feature, db_path)

    # Embed workflows
    for row in conn.execute("SELECT * FROM workflows"):
        workflow = dict(row)
        embed_workflow(workflow, db_path)

    conn.close()
```

### Performance Considerations

| Operation | Expected Time |
|-----------|---------------|
| Load model (first query) | ~2s |
| Embed query | ~50ms |
| Vector search | ~10ms |
| Total (warm) | ~60ms |
| Total (cold) | ~2s |

**Mitigation:**
- Lazy load model on first search
- Cache model in memory for session duration
- Fall back to FTS if embeddings take >500ms

### Dependencies

Add to `pyproject.toml`:
```toml
dependencies = [
    "sentence-transformers>=2.2.0",
    "chromadb>=0.4.0",
    # existing deps...
]
```

**Note:** First run will download the embedding model (~80MB). Subsequent runs use cached model.

---

## Handoff Enhancements

### New Section: `Restore State`

```markdown
## Restore State
```json
{"feature": "AUTH.login", "being_modified": "refactoring"}
```
```

### SessionStart Hook Reads Restore State

```python
# In session-start.py
def parse_restore_state(handoff_content):
    """Extract Restore State JSON from handoff."""
    import re
    match = re.search(r'## Restore State\s*```json\s*({.*?})\s*```', handoff_content, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    return None

# In main()
restore_state = parse_restore_state(handoff_content)
if restore_state:
    context_parts.append(f"""
⚠️ ACTIVE WORK FROM LAST SESSION:
Feature: {restore_state['feature']} is being_modified={restore_state['being_modified']}
Continue or run update_feature(..., being_modified="none") to close.
""")
```

### Handoff Skill Update

Add to `/ft-mem:handoff` skill:
- If any feature has `being_modified != none`, include Restore State section
- Ask Claude which memories next session should read

---

## New Skill: `/feature-tree:understand`

```markdown
---
name: understand
description: "Build global awareness of codebase via workflows and features"
---

# Understand Codebase

Build a mental model of the entire codebase through Feature Tree.

## Steps

### 1. Load All Workflows
```
search_workflows("*")
```

### 2. Rank by Importance
- Most features referenced (complex)
- Entry points (user-facing)
- Revenue-critical paths

### 3. Present Tree View
```
USER_ONBOARDING (4 features)
├── signup_flow → AUTH.register, EMAIL.verify, DB.user
└── login_flow → AUTH.login, AUTH.session

CHECKOUT (6 features)
├── cart_flow → CART.add, CART.update, CART.remove
└── payment_flow → PAYMENTS.process, PAYMENTS.refund
```

### 4. Ask User
"Which area should I explore deeper?"

### 5. Deep Dive
For selected area:
- `get_feature()` for each feature
- Build understanding of data flow
- Note dependencies and impact
```

---

## Implementation Tasks

### Layer 1 - Schema & Migration
1. Add `being_modified`, `important_message`, `archived_at` columns
2. Write v2→v3 migration logic
3. Update `code_symbols` to structured format

### Layer 2 - MCP Tools
4. Update `add_feature()` with new params + embed on create
5. Update `update_feature()` with new params + re-embed on text change
6. Rewrite `get_feature()` for compact output
7. Implement hybrid search (semantic + FTS) in `search_features()`
8. Add ChromaDB setup and embedding migration

### Layer 3 - Hooks
9. Create `jit-reminder.py` hook
10. Add PreToolUse matcher to `hooks.json`
11. Update SessionStart to parse Restore State

### Layer 4 - Skills
12. Create `/feature-tree:understand` skill
13. Update `/ft-mem:handoff` with Restore State section

### Layer 5 - Testing
14. Test migration on existing v2 databases
15. Test embedding search quality
16. Test JIT reminders on Read/Edit
17. Test handoff restore state flow

---

## Open Questions

- Should JIT reminder have a disable flag for performance-sensitive sessions?
- Should `being_modified` auto-reset after N hours of inactivity?
- Should archived features be queryable via search, or only via direct `get_feature()`?
