# Handoff

## Status
DONE (prompting/docs) → IN-PROGRESS (v3.1.0 implementation)

## What Was Done

### Bug Fixes (v3.0.1 → v3.0.3)
- v3.0.1: Handle dict code_symbols in FTS
- v3.0.2: Check API key BEFORE touching ChromaDB
- v3.0.3: Handle dict code_symbols in markdown, rename to FT_EMBEDDING_API_KEY

### Prompt/Docs Overhaul
- SERVER_INSTRUCTIONS: 6542 → 3368 chars (workflow-first, semantic search value, clear field definitions)
- Tool docstrings: Clean, with "When" guidance
- brainstorm skill: 500 → 200 lines (Discovery → Product → Design → Specification)
- executing-plans skill: 371 → 100 lines (follow order → implement → test REAL → commit)
- handoff command: Simplified structure
- session_start hook: Workflow-first reminder
- brainstorm-sync: Captures thinking NOT in plan
- README: v3 philosophy

### Deleted
- understand skill (integrated into workflow-first)
- onboarding skill (start with brainstorm)

## Next Session: v3.1.0 Implementation

**Plan:** `docs/plans/2026-01-08-v3.1.0-embedding-efficiency-design.md`

### Commit 1: Schema Changes
- [ ] Add to workflows table: being_modified, important_message, embedding_status, archived_at, steps
- [ ] Add to features table: embedding_status
- [ ] Migration logic in db.py

### Commit 2: Background Embedding Queue
- [ ] Single worker thread + queue in embeddings.py
- [ ] embed_feature/embed_workflow queue jobs instead of blocking
- [ ] Status tracking (pending → success/failed)

### Commit 3: Async Wiring in MCP
- [ ] add_feature/update_feature queue embed jobs
- [ ] add_workflow/update_workflow queue embed jobs
- [ ] update with no params = retry embedding

### Commit 4: get_workflow() Formatting
- [ ] Formatted output like get_feature()
- [ ] Show steps, status indicators for depends_on
- [ ] Embedding status line

### Commit 5: Embedded Text Updates
- [ ] Add `uses` to feature_to_text()
- [ ] Add `steps` to workflow_to_text()

## Decisions Made
- Fire-and-forget embedding with status tracking (not blocking)
- Single worker thread + queue (not thread pool)
- Status in DB column, not in-memory
- update_feature(id) with no params = retry embedding
- Removed Restore State (redundant with handoff)
- Effort-based commit grouping (big = own commit, small = batch)

## Files Changed This Session
- feature-tree/feature_tree/mcp_server.py (instructions, docstrings)
- feature-tree/feature_tree/embeddings.py (API key check order)
- feature-tree/feature_tree/db.py (dict code_symbols handling)
- feature-tree/feature_tree/markdown.py (dict code_symbols)
- feature-tree/hooks/session_start.py
- feature-tree/skills/brainstorm/SKILL.md
- feature-tree/skills/executing-plans/SKILL.md
- ft-mem/commands/handoff.md
- ft-mem/skills/brainstorm-sync/SKILL.md
- README.md
- docs/plans/2026-01-08-v3.1.0-embedding-efficiency-design.md

## Read These
- `docs/plans/2026-01-08-v3.1.0-embedding-efficiency-design.md` — Full v3.1.0 design
- `.feat-tree/CONTEXT.md` — Project context
