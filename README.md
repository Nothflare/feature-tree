# Feature Tree

AI-driven feature management for Claude Code. Track what your project does, link features to code symbols and commits, and maintain a living documentation tree.

## Philosophy

The bottleneck shifted. It used to be implementation. Now it's specification.

**Human skill**: Decomposing fuzzy goals into precise, hierarchical specs—and catching when the AI is wrong.

**AI role**: Execute reliably, surface assumptions, ask clarifying questions, maintain the feature tree as source of truth.

## Installation

### As a Plugin (Recommended)

```bash
# Add the marketplace
/plugin marketplace add /path/to/feature-tree

# Install the plugin
/plugin install feature-tree@feature-tree-dev

# Restart Claude Code
```

### From GitHub

```bash
# Add the repository as a marketplace
/plugin marketplace add github:your-org/feature-tree

# Install
/plugin install feature-tree@feature-tree

# Restart Claude Code
```

## What You Get

### MCP Tools

- **search_features(query)** - Fuzzy search across feature names, descriptions, and notes
- **add_feature(id, name, ...)** - Create new features with hierarchical organization
- **update_feature(id, ...)** - Track code symbols, files, commits, and status
- **delete_feature(id)** - Soft-delete features (recoverable via git)

### Commands

- **/commit** - Bundle git commits with feature tree updates

### Hooks

- **SessionStart** - Injects the Feature Tree philosophy and working protocol

## Usage

### Adding Features

When you describe a new feature, Claude will track it:

```
Human: I want to add user authentication with email/password login

Claude: I'll add this to the feature tree and start implementing...
[Uses add_feature with id="auth-login", name="User Login", ...]
```

### Tracking Implementation

As Claude implements, it updates features with code context:

```
[Uses update_feature to add code_symbols=["AuthService", "loginUser"],
 files=["src/auth.py"], status="in-progress"]
```

### Committing

Use `/commit` to bundle git commits with feature updates:

```
Human: /commit

Claude: [Commits changes and updates feature tree with commit hashes]
```

## Feature Lifecycle

```
planned → in-progress → done
                ↓
            deleted (soft, reversible)
```

## Project Structure

```
feature-tree/
├── .claude-plugin/
│   ├── plugin.json          # Plugin manifest
│   └── marketplace.json     # Dev marketplace
├── commands/
│   └── commit.md            # /commit command
├── hooks/
│   ├── hooks.json           # Hook configuration
│   ├── run-hook.cmd         # Cross-platform wrapper
│   └── session-start.sh     # Philosophy injection
├── feature_tree/
│   ├── __init__.py
│   ├── db.py                # SQLite + FTS5
│   ├── markdown.py          # FEATURES.md generator
│   └── mcp_server.py        # FastMCP server
├── tests/
├── features.db              # SQLite database (auto-created)
├── FEATURES.md              # Auto-generated documentation
├── LICENSE
├── pyproject.toml
└── README.md
```

## Development

```bash
# Install dependencies
uv sync --extra dev

# Run tests
uv run pytest -v

# Test MCP server
uv run feature-tree
```

## How It Works

1. **SQLite + FTS5**: Features stored with full-text search for fast fuzzy matching
2. **MCP Protocol**: Tools exposed via Model Context Protocol
3. **Auto-generated docs**: Every change regenerates `FEATURES.md`
4. **Hierarchical features**: Parent-child relationships for organization
5. **Cross-platform hooks**: Works on Windows, macOS, and Linux

## Requirements

- Python 3.11+
- uv (for dependency management)
- Git for Windows (on Windows, for hooks)

## License

MIT
