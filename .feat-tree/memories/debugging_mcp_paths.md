# Debugging: MCP Server Path Issues

## The Problem
MCP server stores `.feat-tree/` in plugin cache instead of user's project.

## Root Cause
`uv run --directory X` changes cwd to X before running. So:
- `${CLAUDE_PLUGIN_ROOT}` → runs from plugin cache → files go there
- `Path.cwd()` in Python → returns plugin cache path

## Known Valid Variables
- `${CLAUDE_PLUGIN_ROOT}` - plugin directory (works but wrong location)

## Attempted Solutions

### 1. --project flag
```json
"args": ["run", "--directory", "${CLAUDE_PLUGIN_ROOT}", "feature-tree", "--project", "."]
```
**Failed**: "." resolves AFTER --directory changes cwd

### 2. Wrapper script
```cmd
set "PROJECT_DIR=%CD%"
uv run --directory "%~dp0.." feature-tree --project "%PROJECT_DIR%"
```
**Worked** but complex. Reverted.

### 3. ${PROJECT_ROOT}
```json
"args": ["run", "--directory", "${PROJECT_ROOT}", "feature-tree"]
```
**Unknown**: MCP won't start - may not be valid variable

## What to Check
1. Valid plugin.json mcpServers variables (check Claude Code docs)
2. Try `${PWD}` or other shell variables
3. Check MCP server logs for startup error
