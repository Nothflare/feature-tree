# Feature Tree

AI-driven feature management for Claude Code. Track what your project does, link features to code symbols and commits, maintain living documentation.

## Why Feature Tree?

The bottleneck shifted from implementation to specification.

Most people think "AI does the coding, humans do the thinking." Too vague. The actual skill is **decomposing intent into structures AI can execute reliably**—and knowing when the AI is wrong.

Feature Tree makes this concrete:
- **Human** describes features in natural language
- **Claude** structures them into a hierarchical tree with IDs, status, code symbols
- **Both** maintain a shared source of truth that persists across sessions

## Installation

### From GitHub

```bash
# Add marketplace
/plugin marketplace add github:Nothflare/feature-tree

# Install both plugins
/plugin install feature-tree@feature-tree
/plugin install ft-mem@feature-tree

# Restart Claude Code
```

### From Local Path

```bash
/plugin marketplace add /path/to/feature-tree
/plugin install feature-tree@feature-tree-marketplace
/plugin install ft-mem@feature-tree-marketplace
```

## Plugins

| Plugin | Description |
|--------|-------------|
| **feature-tree** | MCP tools for feature management |
| **ft-mem** | Session continuity (handoff, memories) |

## feature-tree

### MCP Tools

| Tool | Description |
|------|-------------|
| `search_features(query)` | Fuzzy search across features |
| `add_feature(id, name, ...)` | Create with hierarchy |
| `update_feature(id, ...)` | Track symbols, files, commits, status |
| `delete_feature(id)` | Soft-delete (recoverable) |

### Commands

| Command | Description |
|---------|-------------|
| `/commit` | Bundle git commit with feature tree update |

### Feature Lifecycle

```
planned → in-progress → done
                ↓
            deleted (soft, reversible)
```

## ft-mem

Session continuity for Claude. See [ft-mem/README.md](ft-mem/README.md).

| Component | Description |
|-----------|-------------|
| `/handoff` | Save context before /clear |
| `onboarding` skill | First-time memory setup |

## Storage

All data lives in `.feat-tree/` in your project:

```
.feat-tree/
├── features.db          # SQLite with FTS5
├── FEATURES.md          # Auto-generated docs
└── memories/            # Session continuity
    ├── handoff.md       # Picked up on session start
    ├── project_overview.md
    └── [anything].md
```

## Usage

```
Human: I want to add user authentication

Claude: I'll track this in the feature tree.
        [add_feature(id="auth", name="Authentication", ...)]

        Now implementing...
        [update_feature(id="auth", status="in-progress", code_symbols=["AuthService"])]

        Done. Ready to commit?
```
```
Human: /commit

Claude: [Commits and updates feature status to done]
```

## Requirements

- Python 3.11+
- uv (for running the MCP server)

## License

MIT
