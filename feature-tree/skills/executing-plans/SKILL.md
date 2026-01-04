---
name: executing-plans
description: "Execute implementation plans feature-by-feature with commits and tests between batches. Use after brainstorming produces a design."
---

# Executing Plans

Execute implementation plans by implementing features in batches, with commits and tests between each batch.

**Core principle:** Batch execution with verification checkpoints. Never one-shot an entire project.

**Announce at start:** "I'm using the feature-tree:executing-plans skill to implement this design."

---

## When to Use

```
Have a design doc from brainstorming?
    ↓
YES → Use this skill
NO  → Use feature-tree:brainstorm first
```

This skill expects a design doc with:
- Implementation tasks broken into features
- Feature Tree entries identified
- Dependencies between tasks

---

## The Process

### Step 1: Load and Review

1. Read the design doc
2. Review critically — identify any questions or concerns
3. If concerns: Raise them before starting
4. Create TodoWrite with all tasks

**Critical:** If the design feels wrong or incomplete, STOP. Go back to brainstorming. Don't proceed with a flawed design.

### Step 2: Identify Layers

**Before batching, categorize every task by layer.**

Projects have natural layers that build on each other:

```
Layer 0: Project Setup
├── Create project structure
├── Install dependencies
├── Configure build tools
├── Set up testing framework
├── Initialize git, linting, formatting

Layer 1: Infrastructure (INFRA.*)
├── Database connection/setup
├── Config management
├── Logging
├── Error handling
├── Shared utilities

Layer 2: Core Features
├── The main thing the app does
├── What makes this app unique
├── Primary user-facing capabilities

Layer 3: Supporting Features
├── User management
├── Settings
├── Admin tools
├── Secondary capabilities

Layer 4: Polish
├── Performance optimization
├── UI refinement
├── Edge case handling
├── Error messages
```

**Write out the layer assignment:**

```
Layer 0 (Setup):
- Create React project
- Install dependencies
- Configure TypeScript

Layer 1 (Infrastructure):
- INFRA.database
- INFRA.config
- INFRA.logger

Layer 2 (Core):
- AUTH.login
- AUTH.session
- PAYMENT.checkout

Layer 3 (Supporting):
- USER.profile
- USER.settings
```

### Step 3: Plan Batches

**CRITICAL RULE: Tasks from different layers should NEVER be in the same batch.**

Group tasks into batches following these rules:

1. **Same layer only** — All tasks in a batch must be from the same layer
2. **Similar scope** — Tasks should be roughly the same size
3. **Related functionality** — Tasks that share dependencies or concepts
4. **Independently testable** — After the batch, you can verify it works

**Good batches:**

| Batch | Tasks | Why It Works |
|-------|-------|--------------|
| Setup | Create project, install deps, configure build | All Layer 0, all setup |
| Infrastructure | Database, config, logger | All Layer 1 INFRA |
| Core Auth | Login, session, middleware | All Layer 2, all auth-related |
| User Features | Profile, settings | All Layer 3, all user-related |

**Bad batches (NEVER DO THIS):**

| Bad Batch | Why It's Wrong |
|-----------|---------------|
| "Set up project" + "Implement login handler" | Layer 0 + Layer 2 mixed |
| "Install React" + "Style the navbar" | Setup + Polish mixed |
| "Add database" + "Add checkout flow" | Infrastructure + Core feature mixed |
| "Login" + "Checkout" + "Profile" | Unrelated features, too scattered |

### Step 4: Execute Batch

For each task in the batch:

1. **Mark as in_progress** in TodoWrite
2. **Implement the feature**
   - Follow TDD: write test first, then implementation
   - Keep changes focused on this feature only
3. **Run tests** for this feature
4. **Mark as completed** in TodoWrite

### Step 5: Batch Checkpoint

After completing all tasks in a batch:

1. **Run all tests** (not just the batch)
   ```bash
   pytest  # or npm test, etc.
   ```

2. **Use /feature-tree:commit**

   **REQUIRED:** Use the `/feature-tree:commit` command to:
   - Commit all changes with descriptive message
   - Update Feature Tree entries (files, symbols, status → done)
   - Record commit hash in Feature Tree

   This handles both git commit AND Feature Tree updates in one step.

3. **Report to user**
   ```
   Batch 1 (Layer 0 - Setup) complete:
   - ✅ Create React project
   - ✅ Install dependencies
   - ✅ Configure TypeScript

   Tests: 3/3 passing
   Committed: abc1234
   Feature Tree updated.

   Ready for feedback before continuing to Batch 2 (Layer 1 - Infrastructure).
   ```

4. **Wait for user feedback** before proceeding

### Step 6: Continue or Adjust

Based on user feedback:
- **Continue:** Proceed to next batch
- **Adjust:** Modify implementation based on feedback, re-test, use /feature-tree:commit again
- **Pause:** User wants to review more, wait for them

### Step 7: Complete

After all batches:

1. **Run full test suite** one final time
2. **Report completion**
   ```
   Implementation complete:

   Layer 0 (Setup): ✅
   Layer 1 (Infrastructure): ✅
   Layer 2 (Core Features): ✅
   Layer 3 (Supporting Features): ✅

   All tests passing: 47/47
   Commits: 4 (one per batch)

   Ready for code review or deployment.
   ```

---

## Layer Execution Order

**Layers must be executed in order.** You cannot implement Layer 2 before Layer 1 is complete.

```
Layer 0 → Layer 1 → Layer 2 → Layer 3 → Layer 4
  ↓         ↓         ↓         ↓         ↓
Setup → Infra → Core → Support → Polish
```

If a task depends on something from a higher layer that doesn't exist yet, STOP and go back to design.

---

## When to Stop and Ask

**STOP immediately when:**
- Tests fail and you can't figure out why
- A dependency is missing or unclear
- The design doc is ambiguous
- You realize the design is flawed
- User feedback indicates a problem
- You're tempted to mix layers in a batch

**Don't:**
- Push through blockers
- Guess when uncertain
- Skip tests to "fix later"
- Implement features not in the plan
- Mix different layers in one batch

---

## Red Flags

**Never:**
- One-shot the entire project (always batch)
- Mix tasks from different layers in one batch
- Skip /feature-tree:commit between batches
- Continue after test failures
- Skip user checkpoints between batches
- Commit without running tests

**If you're tempted to batch "setup + feature":**
STOP. That's wrong. Setup is Layer 0, features are Layer 2+. They cannot be in the same batch.

**If tests fail:**
1. Stop and diagnose
2. Fix the issue
3. Re-run tests
4. Only then continue

**If design is wrong:**
1. Stop implementation
2. Report the issue to user
3. Go back to brainstorming if needed
4. Don't patch a bad design

---

## Example Workflow

```
User: "Implement the auth system from the design doc"

Claude: I'm using the feature-tree:executing-plans skill to implement this design.

[Read design doc]
[Create TodoWrite with 8 tasks]

First, let me categorize by layer:

Layer 0 (Setup):
- Initialize project structure
- Install dependencies

Layer 1 (Infrastructure):
- INFRA.database
- INFRA.config

Layer 2 (Core Features):
- AUTH.login
- AUTH.session
- AUTH.middleware

Layer 3 (Supporting):
- USER.profile

I've organized this into 4 batches (one per layer):

Batch 1: Layer 0 - Setup
- Initialize project structure
- Install dependencies

Batch 2: Layer 1 - Infrastructure
- INFRA.database
- INFRA.config

Batch 3: Layer 2 - Core Auth
- AUTH.login
- AUTH.session
- AUTH.middleware

Batch 4: Layer 3 - User Features
- USER.profile

Starting Batch 1 (Layer 0 - Setup)...

[Initialize project structure]
[Install dependencies]
[Run tests - passing]
[Use /feature-tree:commit]

---

Batch 1 (Layer 0 - Setup) complete:
- ✅ Initialize project structure
- ✅ Install dependencies

Tests: passing
Committed: abc1234

Ready for feedback before continuing to Batch 2 (Layer 1 - Infrastructure).

User: "Continue"

Claude: Starting Batch 2 (Layer 1 - Infrastructure)...

[Continue with same pattern]
```

---

## Integration with Other Skills

**Preceded by:**
- `feature-tree:brainstorm` — Creates the design this skill executes

**During execution:**
- `/feature-tree:commit` — **REQUIRED** after each batch (handles commit + FT updates)
- TDD principles for each feature

**After completion:**
- Consider `ft-mem:handoff` if ending session
- Code review if significant changes

---

## Key Principles

1. **Layer-based batching** — Categorize tasks by layer, never mix layers in a batch

2. **Layers execute in order** — Layer 0 → 1 → 2 → 3 → 4

3. **Test before commit** — Never commit with failing tests

4. **/feature-tree:commit after each batch** — This is how Feature Tree stays in sync

5. **User checkpoints** — Get feedback between batches

6. **Stop when blocked** — Don't push through problems

7. **Design is upstream** — If design is wrong, go back to brainstorming
