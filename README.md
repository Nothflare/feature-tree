# Feature Tree

AI-driven feature management for Claude Code. Track what your project does, link features to code symbols and commits, maintain living documentation.

## Philosophy

The bottleneck shifted from implementation to specification.

**Human skill**: Decomposing fuzzy goals into precise, hierarchical specs—and catching when the AI is wrong.

**AI role**: Execute reliably, surface assumptions, ask clarifying questions, maintain the feature tree as source of truth.

## Installation

```bash
# Add marketplace
/plugin marketplace add /path/to/feature-tree

# Install feature-tree (and optionally ft-mem for session continuity)
/plugin install feature-tree@feature-tree-marketplace
/plugin install ft-mem@feature-tree-marketplace

# Restart Claude Code
```

## Plugins in This Marketplace

| Plugin | Description |
|--------|-------------|
| **feature-tree** | MCP tools for feature management |
| **ft-mem** | Session continuity (handoff, memories) |

## feature-tree

### MCP Tools

- **search_features(query)** - Fuzzy search features
- **add_feature(id, name, ...)** - Create features with hierarchy
- **update_feature(id, ...)** - Track code symbols, files, commits, status
- **delete_feature(id)** - Soft-delete (recoverable)

### Commands

- **/commit** - Bundle git commits with feature tree updates

### Usage

```
Human: I want to add user authentication

Claude: [Uses add_feature with id="auth", name="Authentication", ...]
Claude: [Implements, then uses update_feature to track symbols, files]
Claude: [Uses /commit to commit + update feature tree]
```

### Feature Lifecycle

```
planned → in-progress → done
                ↓
            deleted (soft, reversible)
```

## ft-mem (Companion Plugin)

Session continuity via handoff and memories. See [ft-mem/README.md](ft-mem/README.md).

- **/handoff** - Save session context before /clear
- **onboarding skill** - First-time memory setup
- Stores in `.feat-tree/memories/`

## Project Structure

```
feature-tree/                 # Marketplace
├── .claude-plugin/
│   ├── plugin.json          # feature-tree manifest
│   └── marketplace.json     # Lists both plugins
├── feature_tree/            # MCP server
│   ├── db.py
│   ├── markdown.py
│   └── mcp_server.py
├── commands/
│   └── commit.md
├── ft-mem/                  # Companion plugin
│   ├── .claude-plugin/
│   ├── commands/
│   ├── skills/
│   └── hooks/
├── features.db
├── FEATURES.md
└── pyproject.toml
```

## Requirements

- Python 3.11+
- uv

## License

MIT
