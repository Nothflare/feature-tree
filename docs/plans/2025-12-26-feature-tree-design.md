# Feature Tree Design

> Date: 2025-12-26

## Overview

Feature Tree is a minimal system for AI-driven feature management. Humans elaborate on features via Claude Code, AI implements and tracks everything in a structured database.

**Core principle:** Human elaborates, AI implements.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Human Layer                         │
│  FEATURES.md (auto-generated, read-only report)         │
│  Claude Code chat (all interactions happen here)        │
└─────────────────────────────────────────────────────────┘
                          ↑↓
┌─────────────────────────────────────────────────────────┐
│                     Bridge Layer                        │
│  SessionStart hook → injects "we use Feature Tree"      │
│  /commit command → commit + update tree                 │
│  MCP Server → 4 tools for CRUD + search                 │
└─────────────────────────────────────────────────────────┘
                          ↑↓
┌─────────────────────────────────────────────────────────┐
│                     Data Layer                          │
│  features.db (SQLite - source of truth)                 │
│  Fuzzy search via SQLite FTS5                           │
└─────────────────────────────────────────────────────────┘
```

**Flow:**
1. Human talks to Claude about features
2. Claude uses MCP tools to query/update SQLite
3. Every update regenerates `FEATURES.md`
4. `/commit` bundles git commit + feature tree update

## File Structure

```
project/
├── .claude/
│   ├── settings.json      # MCP + hooks config
│   └── commands/
│       └── commit.md      # /commit command
├── feature_tree/
│   ├── mcp_server.py      # MCP server with 4 tools
│   ├── session_hook.py    # SessionStart hook
│   └── db.py              # SQLite helpers
├── features.db            # SQLite database
└── FEATURES.md            # Generated report
```

## Data Model (SQLite Schema)

```sql
CREATE TABLE features (
    id            TEXT PRIMARY KEY,  -- UUID or slug like "auth-login"
    parent_id     TEXT REFERENCES features(id),
    name          TEXT NOT NULL,
    description   TEXT,
    status        TEXT DEFAULT 'planned',  -- planned|in-progress|done|deleted
    code_symbols  TEXT,  -- JSON array: ["AuthService", "loginUser", "JWT_SECRET"]
    files         TEXT,  -- JSON array: ["src/auth/login.ts", "src/utils/jwt.ts"]
    technical_notes TEXT,
    commit_ids    TEXT,  -- JSON array: ["abc123", "def456"]
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at    TEXT DEFAULT CURRENT_TIMESTAMP
);

-- For fuzzy search
CREATE VIRTUAL TABLE features_fts USING fts5(
    name, description, technical_notes,
    content='features',
    content_rowid='rowid'
);
```

**Key decisions:**
- `id` as TEXT allows human-readable slugs ("auth-login") or UUIDs
- `parent_id` enables tree hierarchy (nullable for root features)
- JSON arrays for `code_symbols`, `files`, `commit_ids` - flexible, no extra tables
- FTS5 virtual table for fast fuzzy search across name/description/notes
- Soft delete via `status='deleted'` preserves history for reverting

## MCP Server

Single MCP server (`feature-tree`) exposes 4 tools:

| Tool | Purpose |
|------|---------|
| `search_features(query)` | Fuzzy search features by name/description/notes |
| `add_feature(name, parent_id?, description?)` | Create new feature |
| `update_feature(id, **fields)` | Update any field(s) |
| `delete_feature(id)` | Soft delete (status='deleted') |

Every mutating tool regenerates `FEATURES.md` after updating SQLite.

### MCP Server Instructions

Embedded philosophy that Claude receives:

```
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
```

## SessionStart Hook

Minimal context injection:

```python
#!/usr/bin/env python
print("This project uses Feature Tree for feature management.")
print("Use /commit after completing work to commit + update the tree.")
```

## /commit Slash Command

`.claude/commands/commit.md`:

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

## FEATURES.md Generation

Auto-generated markdown report format:

```markdown
# Feature Tree

> Auto-generated. Do not edit. Use Claude Code to modify.

## auth
Authentication system

- **Status:** done
- **Files:** src/auth/login.ts, src/auth/jwt.ts
- **Commits:** abc123, def456

### auth/login
User login with email/password

- **Status:** done
- **Symbols:** loginUser, validateCredentials, AuthService
- **Files:** src/auth/login.ts
- **Commits:** abc123

### auth/signup
User registration

- **Status:** in-progress
- **Symbols:** registerUser, sendVerificationEmail
- **Files:** src/auth/signup.ts
- **Commits:** def456

## payments
Payment processing (Stripe)

- **Status:** planned
```

**Format rules:**
- Tree structure via heading levels (`##` for root, `###` for children, etc.)
- Each feature shows: status, symbols, files, commits (if present)
- Deleted features omitted from report (but preserved in SQLite)

## Configuration

`.claude/settings.json` (project scope):

```json
{
  "mcpServers": {
    "feature-tree": {
      "command": "python",
      "args": ["feature_tree/mcp_server.py"]
    }
  },
  "hooks": {
    "SessionStart": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "python feature_tree/session_hook.py"
      }]
    }]
  }
}
```
