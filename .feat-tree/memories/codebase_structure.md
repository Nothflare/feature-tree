# Codebase Structure

## Marketplace (root)
```
feature-tree/
├── .claude-plugin/
│   ├── plugin.json          # feature-tree plugin manifest + MCP config
│   └── marketplace.json     # Lists both plugins
├── feature_tree/            # MCP server package
│   ├── db.py               # SQLite + standalone FTS5
│   ├── markdown.py         # FEATURES.md generator
│   └── mcp_server.py       # FastMCP server, 4 tools
├── commands/
│   └── commit.md           # /commit command
├── ft-mem/                 # Companion plugin
│   ├── .claude-plugin/plugin.json
│   ├── commands/handoff.md
│   ├── skills/onboarding/SKILL.md
│   └── hooks/session-start.py
├── tests/
├── pyproject.toml
└── README.md
```

## Storage (in user projects)
```
project/
└── .feat-tree/
    ├── features.db         # SQLite database
    ├── FEATURES.md         # Auto-generated
    └── memories/           # Session continuity
```

## MCP Tools
- `search_features(query)` - FTS5 fuzzy search
- `add_feature(id, name, parent_id?, description?)`
- `update_feature(id, status?, code_symbols?, files?, ...)`
- `delete_feature(id)` - soft delete
