# Feature Tree

The interface between human intent, AI agent, and code.

## Philosophy

### The Problem

AI agents are high-variance systems. They can reason, explore, and make decisions. But without context, they:
- Guess instead of knowing
- Duplicate instead of reusing
- Break things they didn't know existed
- Lose everything when sessions restart

Traditional solutions try to control agents with rigid rules. This doesn't work — you can't control a complex system with a simple one.

### The Solution

Feature Tree is a **semantic layer** that grows with your project. Not rules that constrain, but context that enables.

**Workflows** capture human intent — user journeys explained like you'd explain to a YC partner.

**Features** capture code reality — atomic units with technical notes for implementation.

**Semantic search** connects them — "auth" finds login, signin, credentials. Jump straight to context without guessing.

The agent starts at the right zoom level, with the right context in hand.

## How It Works

### Workflow-First Approach

```
Task arrives
    ↓
search_workflows("what user wants")  ← Start here (broad context)
    ↓
get_workflow(id) → steps, dependencies, purpose
    ↓
get_feature(id) → files, symbols, technical notes (focused context)
    ↓
Read actual code (only when needed)
```

One workflow often contains all context needed for a task. No need to grep the entire codebase.

### Two Trees, Connected

| Tree | What It Captures | Audience |
|------|------------------|----------|
| **Workflows** | User journeys, steps, why it exists | Human (YC partner level) |
| **Features** | Atomic code units, how it works | Developer (implementation level) |

The link is the power:
- `get_feature("AUTH.login")` → shows which workflows use it
- `get_workflow("USER.login_flow")` → shows which features are done vs planned

### Field Definitions

**Workflows:**
- `description` — Explain to a YC partner (what the journey IS)
- `purpose` — Technical goal (why it exists in the system)
- `steps` — Actual flow in plain language

**Features:**
- `description` — Explain to a YC partner (what it does, user-facing)
- `technical_notes` — Explain to a developer (how it works, gotchas)

Both self-contained. Enough detail that Claude can understand without asking questions.

### Semantic Search

Search finds related concepts, not just keywords.

```
search_features("auth")     → finds: login, signin, credentials, session
search_workflows("payment") → finds: checkout, subscription, refund
```

Jump straight to the right context. Prevents duplicates, prevents hallucination, prevents blind spots.

## Installation

```bash
/plugin marketplace add github:Nothflare/feature-tree
/plugin install feature-tree@feature-tree
/plugin install ft-mem@feature-tree
# Restart Claude Code
```

### Semantic Search Setup (Optional)

Without API key, falls back to keyword search. Still works, just less semantic.

```json
// ~/.claude/settings.json
{
  "env": {
    "FT_EMBEDDING_API_KEY": "sk-or-..."
  }
}
```

| Env Variable | Default | Description |
|--------------|---------|-------------|
| `FT_EMBEDDING_API_KEY` | (none) | OpenRouter API key |
| `FT_EMBEDDING_MODEL` | `openai/text-embedding-3-small` | Model |
| `FT_EMBEDDING_ENDPOINT` | `https://openrouter.ai/api/v1/embeddings` | Endpoint |

## MCP Tools

### Search (use BEFORE implementing)

| Tool | Purpose |
|------|---------|
| `search_features(query)` | Find existing features, prevent duplicates |
| `search_workflows(query)` | Find user journeys, understand broad context |

### Get (use AFTER search for full context)

| Tool | Purpose |
|------|---------|
| `get_feature(id)` | Files, symbols, dependencies, what depends on this |
| `get_workflow(id)` | Steps, purpose, which features are ready vs blocked |

### Create/Update (use AFTER implementing)

| Tool | Purpose |
|------|---------|
| `add_feature(...)` | Create new feature |
| `update_feature(...)` | Update files, symbols, notes after implementing |
| `add_workflow(...)` | Create new workflow |
| `update_workflow(...)` | Update steps, dependencies |
| `delete_feature(id)` | Archive (active) or delete (planned) |
| `delete_workflow(id)` | Archive (active) or delete (planned) |

**Note:** Updates OVERRIDE, not append. To add a file, get current list first, then update with full list.

## Usage

### Simple Rule

- **Search BEFORE implementing** (always)
- **Create/update AFTER implementing** (when you know actual files, symbols)

### Status

Status tells you what you CAN DO with something:

| Status | Meaning | Action |
|--------|---------|--------|
| `planned` | Designed, not in code | Don't depend on it yet |
| `active` | Implemented, working | Safe to use |
| `archived` | Deprecated/removed | Update things depending on it |

### being_modified (for handoff only)

Only set when handing off mid-task:

| Value | When |
|-------|------|
| `building` | First-time implementation, incomplete |
| `refactoring` | Changing approach, incomplete |
| `fixing` | Bug fix, incomplete |
| `extending` | Adding features, incomplete |

## Skills

| Skill | Purpose |
|-------|---------|
| `/feature-tree:brainstorm` | Design through Discovery → Product → Design → Specification |
| `/feature-tree:executing-plans` | Execute plans with commits between tasks |
| `/feature-tree:commit` | Commit with feature tree update |
| `/feature-tree:bootstrap` | Discover features from existing codebase |
| `/ft-mem:handoff` | Save context before /clear |
| `/ft-mem:brainstorm-sync` | Sync brainstorm discoveries to memory |

## Storage

```
.feat-tree/
├── features.db      # SQLite + FTS5
├── chroma/          # Vector store (semantic search)
├── FEATURES.md      # Auto-generated
├── WORKFLOWS.md     # Auto-generated
├── CONTEXT.md       # Product context
└── memories/        # Cross-session context
    ├── handoff.md
    ├── user.md
    ├── scope.md
    └── decisions.md
```

## Requirements

- Python 3.11+
- uv

## License

MIT
