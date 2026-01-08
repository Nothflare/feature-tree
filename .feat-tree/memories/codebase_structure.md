# Codebase Structure

## Current: v2.2.7

```
feature-tree/
├── .claude-plugin/
│   └── marketplace.json     # Lists both plugins
├── feature-tree/            # Main plugin (v2.2.7)
│   ├── .claude-plugin/plugin.json
│   ├── feature_tree/        # MCP server package
│   │   ├── db.py           # SQLite + FTS5
│   │   ├── markdown.py     # FEATURES.md/WORKFLOWS.md generator
│   │   └── mcp_server.py   # FastMCP server + SERVER_INSTRUCTIONS
│   ├── skills/
│   │   ├── bootstrap/SKILL.md
│   │   ├── brainstorm/SKILL.md
│   │   └── executing-plans/SKILL.md
│   ├── commands/commit.md
│   ├── hooks/
│   │   ├── hooks.json       # SessionStart only
│   │   └── session-start.py # Creates session, injects FT_SESSION=N
│   └── tests/
├── ft-mem/                  # Companion plugin (v2.1.0)
│   ├── .claude-plugin/plugin.json
│   ├── commands/handoff.md
│   ├── skills/
│   │   ├── onboarding/SKILL.md
│   │   └── brainstorm-sync/SKILL.md
│   └── hooks/session-start.py  # Injects CONTEXT.md + philosophy
└── docs/plans/
```

## v3 Planned Changes

```
feature-tree/
├── feature_tree/
│   ├── db.py              # + migration logic, new columns
│   └── mcp_server.py      # + compact get_feature(), new params
├── hooks/
│   ├── hooks.json         # + PreToolUse(Read|Edit) matcher
│   ├── session-start.py   # + Restore State parsing
│   └── jit-reminder.py    # NEW: JIT context injection
└── skills/
    └── understand/SKILL.md  # NEW: Global awareness
```

## Schema: v2 vs v3

### v2 Status Enum
`planned`, `in_progress`, `done`, `deleted`

### v3 Status + Activity
```
status: planned | active | archived
being_modified: none | building | refactoring | fixing | extending
```

### v3 New Columns
- `being_modified` TEXT DEFAULT 'none'
- `important_message` TEXT
- `archived_at` TEXT

### v3 Structured code_symbols
```json
// v2: ["handleLogin", "validateCredentials"]
// v3: [{"name": "handleLogin", "location": "src/auth/login.ts:45", "valid": true}]
```

## v3 Semantic Search

```
.feat-tree/
├── features.db        # SQLite (existing)
├── chroma/            # NEW: ChromaDB vector store
│   ├── features/      # Feature embeddings
│   └── workflows/     # Workflow embeddings
```

- Embedding model: `all-MiniLM-L6-v2` (80MB, offline)
- Vector store: ChromaDB (embedded, no server)
- Hybrid search: semantic + FTS fallback

## MCP Tools

**Features:**
- `search_features(query, s?)` - Hybrid: semantic + FTS (v3)
- `get_feature(id, s?)` - Compact 10-line format (v3)
- `add_feature(id, name, being_modified?, important_message?, ..., s?)`
- `update_feature(id, being_modified?, important_message?, ..., s?)`
- `delete_feature(id, s?)` - Hard if planned, soft otherwise

**Workflows:**
- `search_workflows(query, s?)` - FTS5 search
- `get_workflow(id, s?)` - Full details + linked_features with status
- `add_workflow(id, name, depends_on?, ..., s?)`
- `update_workflow(id, ..., s?)`
- `delete_workflow(id, s?)`

## Hooks

### v2 (Current)
- `SessionStart` → Inject FT_SESSION, CONTEXT.md, handoff.md

### v3 (Planned)
- `SessionStart` → + Restore State parsing
- `PreToolUse(Read|Edit)` → JIT reminder (rich if being_modified, brief otherwise)

## Key Design Principles

1. **Hooks = JIT reminders, not automation** (cybernetics)
2. **Claude decides, FT provides data**
3. **Previous Claude instructs next Claude** (via handoff)
4. **Lifecycle ≠ Activity** (orthogonal dimensions)
5. **Dense > verbose** (compact get_feature output)
