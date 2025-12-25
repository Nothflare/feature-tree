# Feature Tree

AI-driven feature management for Claude Code. Track what your project does, link features to code symbols and commits, and maintain a living documentation tree.

## What is Feature Tree?

Feature Tree is an MCP server that provides 4 tools for managing project features:

- **search_features** - Fuzzy search across feature names, descriptions, and technical notes
- **add_feature** - Create new features with hierarchical organization
- **update_feature** - Track code symbols, files, commits, and status changes
- **delete_feature** - Soft-delete features (recoverable via git history)

Features are stored in SQLite with FTS5 for fast fuzzy search, and automatically generate a `FEATURES.md` file documenting your project.

## Quick Start

### 1. Install

```bash
# Clone or copy to your project
git clone https://github.com/YOUR_USERNAME/feature-tree.git
cd feature-tree

# Install dependencies
uv sync
```

### 2. Configure Claude Code

Add to your project's `.claude/settings.json`:

```json
{
  "mcpServers": {
    "feature-tree": {
      "command": "uv",
      "args": ["run", "python", "-m", "feature_tree.mcp_server"]
    }
  }
}
```

### 3. Restart Claude Code

The Feature Tree tools will now be available in your Claude Code session.

## Usage

### Adding Features

When you describe a new feature, Claude will use `add_feature` to track it:

```
Human: I want to add user authentication with email/password login

Claude: I'll add this to the feature tree and start implementing...
[Uses add_feature with id="auth-login", name="User Login", description="..."]
```

### Tracking Implementation

As Claude implements features, it updates them with code symbols and files:

```
[Uses update_feature to add code_symbols=["AuthService", "loginUser"],
 files=["src/auth.py"], status="in-progress"]
```

### Committing with /commit

Use the `/commit` command to bundle git commits with feature updates:

```
Human: /commit

Claude: [Commits changes and updates feature tree with commit hashes]
```

### Searching Features

Before starting work, Claude searches existing features:

```
[Uses search_features("auth") to find related features]
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
├── feature_tree/
│   ├── __init__.py
│   ├── db.py              # SQLite + FTS5 database layer
│   ├── markdown.py        # FEATURES.md generator
│   ├── mcp_server.py      # FastMCP server with 4 tools
│   └── session_hook.py    # SessionStart context injection
├── tests/
│   ├── test_db.py
│   └── test_markdown.py
├── .claude/
│   ├── commands/
│   │   └── commit.md      # /commit slash command
│   └── settings.json      # MCP + hooks configuration
├── features.db            # SQLite database (auto-created)
├── FEATURES.md            # Auto-generated documentation
└── pyproject.toml
```

## Configuration

### Environment Variables

- `CLAUDE_PROJECT_DIR` - Project root directory (defaults to current working directory)

### Database Location

The `features.db` SQLite database is created in the project root. Add it to version control to share feature history across team members.

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest -v

# Test MCP server starts
uv run python -c "from feature_tree.mcp_server import mcp; print('OK')"
```

## How It Works

1. **SQLite + FTS5**: Features stored in SQLite with full-text search for fast fuzzy matching
2. **MCP Protocol**: Exposes tools via Model Context Protocol for Claude Code integration
3. **Auto-generated docs**: Every feature change regenerates `FEATURES.md`
4. **Hierarchical features**: Features can have parent-child relationships for organization

## License

MIT
