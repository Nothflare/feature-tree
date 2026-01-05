# Suggested Commands

## Development
```bash
uv sync --extra dev    # Install with dev deps
uv run pytest -v       # Run tests
uv run feature-tree    # Test MCP server starts
```

## Plugin Testing
```bash
/plugin uninstall feature-tree@feature-tree
/plugin install feature-tree@feature-tree
# Restart Claude Code
```

## Clean Up
```bash
rm -rf ~/.claude/plugins/cache/feature-tree/
rm -rf .feat-tree/
```

## Git
```bash
git add -A && git commit -m "msg" && git push
```
