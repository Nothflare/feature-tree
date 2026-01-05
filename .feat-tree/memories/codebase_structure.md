# Codebase Structure

## Marketplace (root)
```
feature-tree/
├── .claude-plugin/
│   └── marketplace.json     # Lists both plugins
├── feature-tree/            # Main plugin
│   ├── .claude-plugin/plugin.json
│   ├── feature_tree/        # MCP server package
│   │   ├── db.py           # SQLite + FTS5 + confidence + uses
│   │   ├── markdown.py     # FEATURES.md/WORKFLOWS.md generator
│   │   └── mcp_server.py   # FastMCP server
│   ├── skills/
│   │   ├── bootstrap/SKILL.md      # Two-phase codebase analysis
│   │   ├── brainstorm/SKILL.md     # Three-phase design (Discovery → Design → Spec)
│   │   └── executing-plans/SKILL.md # Layer-based batch implementation
│   ├── commands/
│   │   └── commit.md
│   └── tests/
├── ft-mem/                  # Companion plugin
│   ├── .claude-plugin/plugin.json
│   ├── commands/handoff.md
│   ├── skills/
│   │   ├── onboarding/SKILL.md
│   │   └── brainstorm-sync/SKILL.md  # Post-brainstorm memory sync
│   └── hooks/session-start.py
└── docs/plans/              # Design docs (gitignored)
```

## Storage (in user projects)
```
project/
└── .feat-tree/
    ├── features.db         # SQLite database
    ├── FEATURES.md         # Auto-generated
    ├── WORKFLOWS.md        # Auto-generated
    ├── CONTEXT.md          # Product context
    ├── bootstrap-log.md    # Bootstrap audit trail
    └── memories/           # Session continuity
```

## MCP Tools

**Features:**
- `search_features(query)` - FTS5 fuzzy search
- `get_feature(id)` - Full details + linked_workflows + uses_features + used_by_features
- `add_feature(id, name, parent_id?, description?, uses?)`
- `update_feature(id, status?, code_symbols?, files?, uses?, ...)`
- `delete_feature(id)` - Hard if planned, soft if in-progress/done

**Workflows:**
- `search_workflows(query)` - FTS5 fuzzy search
- `get_workflow(id)` - Full details + linked_features (with status)
- `add_workflow(id, name, depends_on?, mermaid?, ...)`
- `update_workflow(id, status?, depends_on?, mermaid?, ...)`
- `delete_workflow(id)`

**Bootstrap:**
- `bootstrap_log(message, category)` - Append to bootstrap-log.md

## Key Fields
- `confidence`: HIGH | MEDIUM | LOW | null (bootstrap-created vs manual)
- `uses`: JSON array of feature IDs (for INFRA.* dependencies)
- `linked_workflows`: Workflows that depend on this feature (impact analysis)
- `used_by_features`: Features that use this feature (reverse lookup)
