# Handoff

## Completed

**Feature Tree v3.0.0** — Shipped and operational.

Previous session delivered:
- Clean state model (status × being_modified)
- JIT reminders on Read/Edit
- Semantic search (ChromaDB + OpenRouter)
- 23 tests passing

This session:
- Restored v3 files (user had accidentally reversed local changes)
- Added env var placeholders to plugin.json for model/endpoint customization

## Files Changed This Session

- `feature-tree/.claude-plugin/plugin.json` — Added `FT_EMBEDDING_MODEL` and `FT_EMBEDDING_ENDPOINT` env placeholders

## v3 Environment Variables

| Variable | Required | Default |
|----------|----------|---------|
| `OPENROUTER_API_KEY` | For semantic search | (none) |
| `FT_EMBEDDING_MODEL` | No | `openai/text-embedding-3-small` |
| `FT_EMBEDDING_ENDPOINT` | No | `https://openrouter.ai/api/v1/embeddings` |

Set via `~/.claude/settings.json` under `"env"` or system environment.

## Key v3 Architecture

| Component | Location |
|-----------|----------|
| Database schema | `feature_tree/db.py` |
| Embeddings/semantic search | `feature_tree/embeddings.py` |
| MCP tools | `feature_tree/mcp_server.py` |
| JIT reminder hook | `hooks/jit_reminder.py` |
| Tests | `tests/` (23 tests) |

## Status

**System is operational.** No pending work items.

## Read These Memories

Next session should read:
- `.feat-tree/memories/codebase_structure.md` — Architecture overview
- `README.md` — User-facing documentation

## Notes

- v3 uses OpenRouter for embeddings (not local sentence-transformers)
- Semantic search gracefully falls back to FTS if no API key configured
- JIT reminders fire on Read/Edit of tracked files
