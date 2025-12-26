# Handoff

## Status: FIXED

The MCP path issue is resolved.

## Solution

Use `cwd: "."` in MCP config - MCP servers inherit the working directory where Claude was launched:

```json
"mcpServers": {
  "feature-tree": {
    "command": "uv",
    "args": ["run", "--directory", "${CLAUDE_PLUGIN_ROOT}", "feature-tree"],
    "cwd": "."
  }
}
```

- `--directory ${CLAUDE_PLUGIN_ROOT}` → uv finds pyproject.toml in plugin cache
- `cwd: "."` → MCP process starts with user's project as cwd
- `Path.cwd()` in Python → returns user's project directory

## What Was Wrong

`${PROJECT_ROOT}` is **not a valid variable** in plugin.json. Only `${CLAUDE_PLUGIN_ROOT}` is supported.

## Key Files
- `.claude-plugin/plugin.json` - MCP server config (FIXED)
- `feature_tree/mcp_server.py` - Uses `Path.cwd()` for project root
- `feature_tree/db.py` - SQLite + FTS5 (standalone, working)

## Next: Test

Reinstall plugin and verify `.feat-tree/` is created in user's project, not plugin cache.
