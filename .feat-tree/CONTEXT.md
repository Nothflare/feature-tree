# CONTEXT

## Problem
AI handles implementation. Humans move to abstract levels (product vision, taste, specification). But there's no unified protocol connecting them efficiently.

**The gap:**
- Context window limits what AI can hold
- Human mindset is "what should exist" / AI mindset is "what code to write"
- No shared language between product intent and code structure
- Sessions restart cold, losing accumulated understanding

Feature Tree bridges this: a semantic layer that speaks both human (features, workflows) and AI (symbols, files).

## Target Users
- Solo devs using Claude Code who want persistent project memory
- Teams wanting shared feature documentation that AI can read/write

## Success Criteria
- Claude correctly identifies which features to modify for a task
- Changes to one feature surface which workflows might break
- New sessions resume with full context (no re-explaining)

## Constraints
- Claude Code plugin system (MCP tools, hooks, skills)
- SQLite for storage (portable, no server)
- Must work offline

## Key Assumptions
- [validated] Two trees (features + workflows) better than one
- [validated] Atomic features more useful than categories
- [untested] Two-phase bootstrap (code→features, then features→workflows) produces better results
- [implemented] Confidence levels (HIGH/MEDIUM/LOW) on features/workflows
- [validated] INFRA.* naming convention for infrastructure (no separate table)
- [validated] `uses` field for feature dependencies works well
