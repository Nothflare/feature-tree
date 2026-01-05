# Prompt Improvements Spec

> **For Next Session:** Review and implement these prompt/instruction improvements.
> These are behavioral/mentality changes, not code changes.

## Overview

The MCP tools exist, but Claude doesn't use them effectively. The prompts need to be more forceful about:
1. When to use which tool
2. Data flow tracing (don't speculate)
3. Feature lifecycle
4. Cross-session continuity

---

## Priority 1: Workflow-First Thinking

### Problem
Claude often modifies features without understanding how they fit into user workflows. This leads to:
- Breaking workflows without realizing
- Missing context about data flow
- Speculating about data structures

### Direction
Update SERVER_INSTRUCTIONS and philosophy to emphasize:

```
Before modifying ANY feature:
1. get_feature(id) → check linked_workflows
2. For each linked workflow: get_workflow(id)
3. Trace the FULL data flow through the workflow
4. Understand: where data comes from, how it transforms, where it goes
5. ONLY THEN make changes
```

### Key Insight
**Workflows are the source of truth for data flow.** Features alone don't tell you how data moves through the system. Without tracing workflows, Claude will speculate about:
- Database schema
- Data structures
- API contracts
- State management

This causes misalignment and broken code.

---

## Priority 2: Data Flow Tracing Protocol

### Problem
Claude speculates about data structures instead of tracing actual flow. Example:
- User says "add validation to login"
- Claude guesses what the login request/response looks like
- Claude's guess doesn't match actual implementation
- Code breaks

### Direction
Add explicit protocol to prompts:

```
DATA FLOW TRACING (MANDATORY)

Before implementing:
1. Find the entry point (route, handler, command)
2. Trace what data comes in (request shape)
3. Trace what happens to the data (transformations)
4. Trace what data goes out (response shape)
5. Check linked_workflows for the full journey

NEVER speculate about:
- Database schema → read the actual schema
- Request/response shapes → read the actual types
- State structure → read the actual store
- API contracts → read the actual endpoints

If you don't know, ASK or READ. Don't guess.
```

---

## Priority 3: Feature Lifecycle Clarity

### Problem
Claude doesn't follow a consistent lifecycle:
- Sometimes creates feature entry after implementing
- Sometimes forgets to update with files/symbols
- Sometimes uses regular git commit instead of /feature-tree:commit

### Direction
Make lifecycle explicit in prompts:

```
FEATURE LIFECYCLE

1. CREATE (before implementing)
   add_feature(id="AUTH.login", name="User Login", status="planned")

2. START (when beginning work)
   update_feature(id="AUTH.login", status="in-progress")

3. TRACK (during implementation)
   update_feature(id="AUTH.login",
                  files=["src/auth/login.ts"],
                  code_symbols=["handleLogin", "LoginRequest"])

4. COMMIT (after tests pass)
   /feature-tree:commit  # bundles git + FT update

5. COMPLETE
   update_feature(id="AUTH.login", status="done")

NEVER:
- Implement before creating the feature entry
- Use regular git commit instead of /feature-tree:commit
- Forget to update files/symbols after implementing
```

---

## Priority 4: "Search Before Implementing" Enforcement

### Problem
"Search before implementing" is mentioned but not enforced. Claude often skips directly to coding.

### Direction
Make it a HARD REQUIREMENT:

```
BEFORE ANY IMPLEMENTATION

REQUIRED STEPS (cannot skip):
1. search_features("relevant terms")
   - Does this feature already exist?
   - What related features exist?

2. search_workflows("relevant terms")
   - What user journeys touch this area?
   - What would break if I change this?

3. If feature exists: get_feature(id)
   - What files/symbols are involved?
   - What uses this? (used_by_features)
   - What workflows depend on it? (linked_workflows)

ONLY THEN start implementing.

If you skip these steps, you WILL:
- Recreate features that exist
- Break workflows you didn't know about
- Miss important context
```

---

## Priority 5: Cross-Session Continuity

### Problem
New Claude sessions don't connect handoff text to actual FT entries. Handoff says "AUTH.login was created" but new Claude doesn't query it.

### Direction
Update handoff template and session-start philosophy:

```
CROSS-SESSION PROTOCOL

When starting a new session:

1. Read handoff.md for context

2. For each feature mentioned in handoff:
   get_feature("AUTH.login")  # NOT just reading the text

3. Check linked_workflows:
   "AUTH.login has linked_workflows: [AUTH.login_flow]"
   get_workflow("AUTH.login_flow")  # trace the data flow

4. ONLY THEN continue work

The handoff TEXT is a summary.
The FT ENTRIES are the source of truth.
ALWAYS query the entries, don't just read the text.
```

---

## Priority 6: Impact Analysis Before Changes

### Problem
Claude changes features without checking what depends on them.

### Direction
Add to prompts:

```
IMPACT ANALYSIS (before any change)

Before modifying existing code:

1. get_feature(id) for the feature you're changing
2. Check used_by_features:
   - What other features depend on this?
   - Will your change break them?
3. Check linked_workflows:
   - What user journeys use this?
   - Will your change break the flow?

ESPECIALLY for INFRA.*:
- Infrastructure is high-impact
- Many features depend on INFRA.*
- ALWAYS check used_by_features before changing

If impact is unclear, ASK before changing.
```

---

## Files to Update

### SERVER_INSTRUCTIONS (mcp_server.py)
- Add "DATA FLOW TRACING" section
- Add "IMPACT ANALYSIS" section
- Make "search before implementing" a hard requirement
- Add feature lifecycle diagram

### Philosophy (session-start.py)
- Add "Workflow-First Thinking" concept
- Add cross-session protocol
- Emphasize querying FT entries, not just reading handoff text

### Handoff Templates (handoff.md)
- Change "Features Created" to include explicit `get_feature()` instructions
- Add reminder to trace data flow before continuing

---

## Testing the Changes

After implementing, test with scenarios:

1. **New feature request**
   - Does Claude search before creating?
   - Does Claude create feature entry before implementing?
   - Does Claude use /feature-tree:commit?

2. **Modify existing feature**
   - Does Claude check used_by_features?
   - Does Claude check linked_workflows?
   - Does Claude trace data flow?

3. **New session continuing work**
   - Does Claude query FT entries from handoff?
   - Does Claude trace workflows before continuing?
   - Does Claude avoid recreating existing features?

---

## Key Mantras

For easy reference, these should appear prominently:

1. **"Workflows are the source of truth for data flow"**
2. **"Query the entries, don't just read the text"**
3. **"Trace, don't speculate"**
4. **"Check impact before changing"**
5. **"Create entry before implementing"**
