# Handoff

## Session Summary

Major improvements to Feature Tree skill system. Version now at **feature-tree v2.0.3, ft-mem v2.0.1**.

**After implementing the pending fixes, bump to v2.1.0.**

## Completed This Session

### Skills Created/Overhauled
1. **brainstorm skill** - Complete rewrite
   - Three phases: Discovery → Design → Specification
   - Mind tools as checkpoints (must address each)
   - Full tech stack discussion with rationale
   - Design doc includes complete feature/workflow lists

2. **executing-plans skill** - New
   - Layer-based batching (Layer 0-4: Setup → Infra → Core → Support → Polish)
   - CRITICAL RULE: Never mix layers in same batch
   - Uses /feature-tree:commit after each batch

3. **bootstrap skill** - Rewritten
   - Two-phase: Feature Discovery → Workflow Identification
   - Confidence levels on output
   - bootstrap_log() for audit trail

4. **ft-mem:brainstorm-sync** - New
   - Post-brainstorm memory sync

### Schema/MCP Changes
- Added `confidence` field to features and workflows tables
- DB auto-migrates existing databases
- Updated SERVER_INSTRUCTIONS with tool usage guidance
- Updated session-start hook philosophy

## Changes Committed

All changes from this session have been committed.

---

## PENDING FIXES FOR NEXT SESSION

### Priority 1: MCP Tool Bugs (confidence param missing)

The DB layer supports `confidence` but MCP tools don't expose it!

| Tool | Fix Needed |
|------|------------|
| `add_feature()` | Add `confidence: str \| None = None` param |
| `update_feature()` | Add `confidence: str \| None = None` param |
| `add_workflow()` | Add `confidence: str \| None = None` param |
| `update_workflow()` | Add `confidence: str \| None = None` param |
| `search_features()` | Show `confidence` in results |
| `search_workflows()` | Show `confidence` in results |

Files: `feature-tree/feature_tree/mcp_server.py`

### Priority 2: FTS Index Gap (CRITICAL)

**Problem:** `files` and `code_symbols` are NOT in FTS index!

Cannot search "which feature owns this file" or "which feature has this function".

**Fix options:**
1. Add `files` and `code_symbols` to FTS5 index in `db.py`
2. Or add `find_feature_by_file(path)` convenience tool

Files: `feature-tree/feature_tree/db.py`

### Priority 3: Validation Missing

| Issue | Fix |
|-------|-----|
| `uses` field accepts non-existent feature IDs | Add warning (not error) if referenced feature doesn't exist |
| `depends_on` field same issue | Same fix |

### Priority 4: Complete Handoff Templates

The handoff.md templates for DEBUGGING and BLOCKED need the "Continue Protocol" section added (only DONE and IN-PROGRESS have it).

File: `ft-mem/commands/handoff.md`

---

## Continue Protocol for Next Session

**Before any implementation, trace the data flow:**

1. Read this handoff completely
2. Read `docs/plans/2026-01-05-mcp-improvements-spec.md` for implementation details
3. For MCP fixes: read `mcp_server.py` and `db.py` to understand current state
4. Check `linked_workflows` when modifying features to understand impact
5. Trace: where does data come from → how it transforms → where it goes

**DO NOT speculate about data structures. Trace the actual flow.**

## Key Design Decisions (Don't Revisit)

| Decision | Rationale |
|----------|-----------|
| Mind tools as checkpoints, not scripts | Give Claude flexibility, explain WHY not HOW |
| Layer-based batching | Prevents mixing setup with features |
| /feature-tree:commit after each batch | Ensures FT stays in sync |
| INFRA.* naming convention | No separate infra table, just features with prefix |
| Soft delete for in-progress/done | Allows recovery, only planned = hard delete |

## Files Changed This Session

- `feature-tree/skills/brainstorm/SKILL.md` - Complete rewrite
- `feature-tree/skills/executing-plans/SKILL.md` - New
- `feature-tree/skills/bootstrap/SKILL.md` - Rewrite
- `feature-tree/feature_tree/db.py` - confidence field
- `feature-tree/feature_tree/mcp_server.py` - SERVER_INSTRUCTIONS
- `ft-mem/skills/brainstorm-sync/SKILL.md` - New
- `ft-mem/commands/handoff.md` - Continue Protocol
- `ft-mem/hooks/session-start.py` - Philosophy update

## Read These Files

- `.feat-tree/memories/codebase_structure.md` - Updated with new skills
- `.feat-tree/CONTEXT.md` - Project context and assumptions
- `docs/plans/2026-01-05-mcp-improvements-spec.md` - **Detailed implementation spec for pending fixes**
