# Feature Tree

A semantic layer connecting human intent and AI implementation.

## Why Use Feature Tree?

### The Problem You Have

Without Feature Tree, every session you:
- **Re-discover** which files implement which features
- **Break things** because you don't know what depends on what
- **Duplicate work** by recreating features that already exist
- **Lose context** when sessions restart

### What Feature Tree Gives You

| Before | After |
|--------|-------|
| "Which file handles login?" → grep, guess, hope | `search_features("login")` → AUTH.login → files: [src/auth/login.ts] |
| "What breaks if I change this?" → no idea | `get_feature("INFRA.database")` → used_by: [AUTH.login, CART.checkout, ...] |
| "Does this feature exist?" → search codebase | `search_features("password reset")` → shows if it exists with status |
| "What's the user flow?" → reverse-engineer from code | `get_workflow("USER_ONBOARDING.signup")` → full journey with dependencies |

### Concrete Benefits

1. **Instant Context**: `search_features("auth")` returns all auth features with their files, symbols, and status in one call
2. **Impact Analysis**: Before changing `INFRA.rate_limiter`, see exactly what depends on it
3. **No Duplicates**: Search before creating - know what exists
4. **Cross-Session Memory**: Features persist across sessions - no re-explaining

## Core Concepts

### Two Trees

| Tree | Purpose | Searchable Fields |
|------|---------|-------------------|
| **Features** | Code units (what to implement) | id, name, description, files, code_symbols, commit_ids |
| **Workflows** | User journeys (how features compose) | id, name, description, purpose, depends_on |

The link between them is the power:
- `get_feature("AUTH.login")` → shows `linked_workflows` (what user journeys use this)
- `get_workflow("USER_ONBOARDING.signup")` → shows `linked_features` with status (what's done vs planned)

### Atomic Features

Features are small, implementable units. NOT categories.

```
BAD:  "User Authentication" (too broad)
GOOD: AUTH.login, AUTH.register, AUTH.password_reset (atomic, implementable)
```

### Infrastructure (INFRA.*)

Shared utilities use the `INFRA.*` naming convention:

```
INFRA.rate_limiter     → shared infrastructure
AUTH.login             → uses: [INFRA.rate_limiter]
```

Call `get_feature("INFRA.rate_limiter")` → see `used_by_features` (everything that depends on it).

## Installation

```bash
/plugin marketplace add github:Nothflare/feature-tree
/plugin install feature-tree@feature-tree
/plugin install ft-mem@feature-tree
# Restart Claude Code
```

## Session Support

When multiple Claude sessions work on different projects simultaneously:

```
# Hook injects session ID into context:
FT_SESSION=1

# Pass to all tools:
search_features("auth", s=1)
add_feature(id="AUTH.login", name="Login", s=1)
```

This prevents cross-project data corruption.

## MCP Tools

### Features

| Tool | When to Use | Benefit |
|------|-------------|---------|
| `search_features(query)` | **BEFORE implementing anything** | Find existing features, avoid duplicates |
| `get_feature(id)` | **BEFORE modifying code** | See dependencies, linked workflows, impact |
| `add_feature(id, name, ...)` | When creating new functionality | Track from the start |
| `update_feature(id, files, code_symbols, ...)` | **AFTER implementing** | Future sessions find code instantly |
| `delete_feature(id)` | Removing functionality | Clean up (soft-delete if in-progress) |

**Search finds:** id, name, description, technical_notes, files, code_symbols, commit_ids

### Workflows

| Tool | When to Use | Benefit |
|------|-------------|---------|
| `search_workflows(query)` | Understanding user impact | Find journeys that touch an area |
| `get_workflow(id)` | Before implementing a flow | See what features exist vs need building |
| `add_workflow(id, name, depends_on, ...)` | Designing user journeys | Track the full experience |
| `update_workflow(id, ...)` | Refining flows | Keep journeys accurate |
| `delete_workflow(id)` | Removing flows | Clean up |

**Search finds:** id, name, description, purpose, depends_on (feature IDs)

### Utility

| Tool | When to Use |
|------|-------------|
| `resync_fts()` | If search returns empty but features exist |
| `debug_cwd()` | Debugging path/session issues |

## Skills

| Skill | Purpose |
|-------|---------|
| `/feature-tree:bootstrap` | Analyze codebase → discover features → trace workflows |
| `/feature-tree:brainstorm` | Design new features through structured discovery |
| `/feature-tree:executing-plans` | Execute implementation plans with commits |
| `/feature-tree:commit` | Commit with automatic feature tree update |
| `/ft-mem:onboarding` | First-time project setup |
| `/ft-mem:handoff` | Save context before /clear |

## Usage Protocol

### Before ANY Implementation

```python
# 1. Check if feature exists
search_features("login")

# 2. If modifying existing, check impact
get_feature("AUTH.login")
# → See used_by_features, linked_workflows

# 3. Check related workflows
search_workflows("login")
```

### During Implementation

```python
# Create feature BEFORE coding
add_feature(id="AUTH.login", name="User Login", status="planned")

# Start work
update_feature(id="AUTH.login", status="in-progress")

# Track as you go
update_feature(id="AUTH.login",
    files=["src/auth/login.ts"],
    code_symbols=["handleLogin", "LoginRequest"])
```

### After Implementation

```python
# Use the commit skill (bundles git + FT update)
/feature-tree:commit

# Or manually
update_feature(id="AUTH.login", status="done", commit_ids=["abc123"])
```

## Storage

```
.feat-tree/
├── features.db      # SQLite + FTS5
├── FEATURES.md      # Auto-generated
├── WORKFLOWS.md     # Auto-generated
├── CONTEXT.md       # Product context
└── memories/        # Session continuity
```

## Requirements

- Python 3.11+
- uv

## License

MIT
