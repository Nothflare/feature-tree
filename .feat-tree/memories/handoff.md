# Handoff

## Completed

**Feature Tree v3 Design** — Full specification written and ready for implementation.

## Artifacts Created

| File | Purpose |
|------|---------|
| `docs/plans/2026-01-08-feature-tree-v3-design.md` | Complete v3 specification |
| `.feat-tree/memories/codebase_structure.md` | Updated with v3 planned changes |

## Key v3 Decisions (Don't Revisit)

| Decision | Rationale |
|----------|-----------|
| `status`: planned/active/archived | Clean lifecycle (was: planned/in_progress/done/deleted) |
| `being_modified`: none/building/refactoring/fixing/extending | Activity is orthogonal to lifecycle |
| Hooks = JIT reminders, not automation | Cybernetics: complex system (Claude) shouldn't be controlled by simple system (hooks) |
| `get_feature()` returns compact 10-line format | Dense > verbose for daily use |
| Structured `code_symbols`: `{name, location, valid}` | Location + validity for better JIT reminders |
| `important_message` field | Claude-to-Claude sticky notes |
| Previous Claude decides which memories to inject | Via handoff, not automatic hook logic |
| Semantic search via embeddings | ChromaDB + sentence-transformers, hybrid with FTS fallback |

## Implementation Roadmap

### Layer 1 - Schema & Migration
- [ ] Add `being_modified`, `important_message`, `archived_at` columns to db.py
- [ ] Write v2→v3 migration logic
- [ ] Update `code_symbols` to structured format

### Layer 2 - MCP Tools & Embeddings
- [ ] Update `add_feature()` with new params + embed on create
- [ ] Update `update_feature()` with new params + re-embed on change
- [ ] Rewrite `get_feature()` for compact output
- [ ] Add ChromaDB + sentence-transformers for semantic search
- [ ] Implement hybrid search (semantic + FTS fallback)

### Layer 3 - Hooks
- [ ] Create `jit-reminder.py` hook
- [ ] Add PreToolUse matcher to `hooks.json`
- [ ] Update SessionStart to parse Restore State

### Layer 4 - Skills
- [ ] Create `/feature-tree:understand` skill
- [ ] Update `/ft-mem:handoff` with Restore State section

### Layer 5 - Testing
- [ ] Test migration on existing v2 databases
- [ ] Test semantic search quality (embeddings)
- [ ] Test JIT reminders on Read/Edit
- [ ] Test handoff restore state flow

## Read These Memories

Next session should read:
- `docs/plans/2026-01-08-feature-tree-v3-design.md` — Full implementation spec
- `.feat-tree/memories/codebase_structure.md` — Current vs v3 structure

## Notes for Future

- Design emerged from brainstorming session comparing Feature Tree with:
  - Official `feature-dev` plugin (parallel agents, code review)
  - Advent of Claude 31 days guide (Claude Code native features)
- Key insight: **Hooks should remind, not control** (cybernetics principle)
- v4 will add visualization (human-product-agent interface)
