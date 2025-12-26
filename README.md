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

| Command | Description |
|---------|-------------|
| **/commit** | Bundle git commits with feature tree updates |
| **/handoff** | Save session context before /clear for seamless continuation |

### Skills

| Skill | Description |
|-------|-------------|
| **onboarding** | First-time setup - creates memory files in `.feat-tree/memories/` |

### Hooks

- **SessionStart** - Injects philosophy, handoff context, and memory awareness

## Memory System

Feature Tree includes a memory system for session continuity:

```
.feat-tree/
├── memories/
│   ├── handoff.md           # Session handoff (auto-read on startup)
│   ├── project_overview.md  # Project context
│   ├── code_style.md        # Coding patterns
│   └── [anything].md        # Whatever helps
└── ...
```

### Session Handoff

Before `/clear`, run `/handoff` to save context:
- Captures work status (done, in-progress, debugging, blocked)
- Records decisions and their reasoning
- Documents what was tried and why it failed
- Next Claude continues without repeating work

### Memory Files

Create any `.md` files that help. Common ones:
- `project_overview.md` - Tech stack, entry points
- `suggested_commands.md` - Test, lint, build commands
- `code_style.md` - Naming conventions, patterns
- `api_patterns.md` - API conventions
- `known_issues.md` - Gotchas and quirks

## Usage

### First Time Setup

```
Human: [starts session in new project]
Claude: [sees "Onboarding Required"]
Claude: I'll run /onboarding to set up memories...
```

### Adding Features

```
Human: I want to add user authentication

Claude: I'll add this to the feature tree...
[Uses add_feature with id="auth", name="Authentication", ...]
```

### Session Continuity

```
Human: I need to stop, let's pick this up later
Human: /handoff

Claude: [Saves handoff.md with current state]
Claude: Memories updated. Safe to /clear

[Later, new session]
Claude: [Reads handoff automatically]
Claude: I see you were working on auth, with login done and signup next...
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
│   ├── commit.md            # /commit command
│   └── handoff.md           # /handoff command
├── skills/
│   └── onboarding/
│       └── SKILL.md         # First-time setup
├── hooks/
│   ├── hooks.json           # Hook configuration
│   ├── run-python-hook.cmd  # Cross-platform wrapper
│   └── session-start.py     # Philosophy + memory injection
├── feature_tree/
│   ├── db.py                # SQLite + FTS5
│   ├── markdown.py          # FEATURES.md generator
│   └── mcp_server.py        # FastMCP server
├── tests/
├── features.db              # Feature database
├── FEATURES.md              # Auto-generated docs
└── pyproject.toml
```

## Requirements

- Python 3.11+
- uv (for dependency management)

## License

MIT
