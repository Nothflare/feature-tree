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

### Step 2: Plan Batches

Group tasks into batches of 2-4 related features:

```
Batch 1: Foundation
- Task 1: INFRA.database setup
- Task 2: INFRA.config management

Batch 2: Core Feature
- Task 3: AUTH.login
- Task 4: AUTH.session

Batch 3: Secondary Features
- Task 5: USER.profile
- Task 6: USER.settings
```

**Batch rules:**
- Features in a batch should be related or have shared dependencies
- Each batch should be independently testable
- Later batches can depend on earlier batches, never reverse

### Step 3: Execute Batch

For each task in the batch:

1. **Mark as in_progress** in TodoWrite
2. **Implement the feature**
   - Follow TDD: write test first, then implementation
   - Keep changes focused on this feature only
3. **Update Feature Tree**
   ```
   update_feature(
       id="AUTH.login",
       status="in-progress",
       files=["src/auth/login.ts"],
       code_symbols=["handleLogin", "validateCredentials"]
   )
   ```
4. **Run tests** for this feature
5. **Mark as completed** in TodoWrite

### Step 4: Batch Checkpoint

After completing a batch:

1. **Run all tests** (not just the batch)
   ```bash
   # Run full test suite
   pytest  # or npm test, etc.
   ```

2. **Commit the batch**
   ```bash
   git add -A
   git commit -m "feat: implement [batch description]

   Features:
   - AUTH.login
   - AUTH.session

   Tests: all passing"
   ```

3. **Update Feature Tree status**
   ```
   update_feature(id="AUTH.login", status="done")
   update_feature(id="AUTH.session", status="done")
   ```

4. **Report to user**
   ```
   Batch 1 complete:
   - ✅ INFRA.database setup
   - ✅ INFRA.config management

   Tests: 12/12 passing
   Committed: abc1234

   Ready for feedback before continuing to Batch 2.
   ```

5. **Wait for user feedback** before proceeding

### Step 5: Continue or Adjust

Based on user feedback:
- **Continue:** Proceed to next batch
- **Adjust:** Modify implementation based on feedback, re-test, re-commit
- **Pause:** User wants to review more, wait for them

### Step 6: Complete

After all batches:

1. **Run full test suite** one final time
2. **Verify all Feature Tree entries** are updated to "done"
3. **Report completion**
   ```
   Implementation complete:

   Features implemented:
   - AUTH.login (done)
   - AUTH.session (done)
   - USER.profile (done)
   - USER.settings (done)

   All tests passing: 47/47
   Commits: 4 (one per batch)

   Ready for code review or deployment.
   ```

---

## Feature Tree Integration

### During Implementation

Update Feature Tree entries as you work:

```python
# Starting a feature
update_feature(id="AUTH.login", status="in-progress")

# As you implement
update_feature(
    id="AUTH.login",
    files=["src/auth/login.ts", "src/auth/validators.ts"],
    code_symbols=["handleLogin", "validateCredentials", "LoginRequest"]
)

# After tests pass
update_feature(id="AUTH.login", status="done")
```

### After Each Batch

Verify Feature Tree state matches reality:
- All implemented features marked "done"
- Files and symbols recorded
- Dependencies (uses) properly linked

---

## Commit Strategy

### One Commit Per Batch

Each batch gets one commit containing:
- All feature implementations in the batch
- All tests for those features
- Feature Tree updates happen via MCP tools (not in commit)

### Commit Message Format

```
feat: [batch description]

Features:
- FEATURE.one - [brief description]
- FEATURE.two - [brief description]

Tests: [X] passing
```

### When to NOT Commit

- Tests are failing
- Implementation is incomplete
- User hasn't approved the batch

---

## When to Stop and Ask

**STOP immediately when:**
- Tests fail and you can't figure out why
- A dependency is missing or unclear
- The design doc is ambiguous
- You realize the design is flawed
- User feedback indicates a problem

**Don't:**
- Push through blockers
- Guess when uncertain
- Skip tests to "fix later"
- Implement features not in the plan

---

## Red Flags

**Never:**
- One-shot the entire project (always batch)
- Skip the commit between batches
- Continue after test failures
- Implement without updating Feature Tree
- Skip user checkpoints between batches
- Commit without running tests

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
[Create TodoWrite with 6 tasks]

I've organized this into 3 batches:

Batch 1: Foundation (Tasks 1-2)
- INFRA.database
- INFRA.config

Batch 2: Core Auth (Tasks 3-4)
- AUTH.login
- AUTH.session

Batch 3: User Management (Tasks 5-6)
- USER.profile
- USER.settings

Starting Batch 1...

[Implement INFRA.database]
[Write tests]
[update_feature(id="INFRA.database", status="in-progress", files=[...])]
[Run tests - passing]
[Mark task complete]

[Implement INFRA.config]
[Write tests]
[update_feature(id="INFRA.config", status="in-progress", files=[...])]
[Run tests - passing]
[Mark task complete]

Batch 1 checkpoint:
[Run full test suite - 8/8 passing]
[git commit -m "feat: implement foundation (database, config)"]
[update_feature(id="INFRA.database", status="done")]
[update_feature(id="INFRA.config", status="done")]

---

Batch 1 complete:
- ✅ INFRA.database
- ✅ INFRA.config

Tests: 8/8 passing
Committed: abc1234

Ready for feedback before continuing to Batch 2.

User: "Looks good, continue"

Claude: Starting Batch 2...

[Continue with same pattern]
```

---

## Integration with Other Skills

**Preceded by:**
- `feature-tree:brainstorm` — Creates the design this skill executes

**During execution:**
- Update Feature Tree via MCP tools
- Use TDD principles for each feature

**After completion:**
- Consider `ft-mem:handoff` if ending session
- Code review if significant changes

---

## Key Principles

1. **Batch, don't one-shot** — Group related features, checkpoint between batches

2. **Test before commit** — Never commit with failing tests

3. **Update Feature Tree** — Track progress in the system of record

4. **User checkpoints** — Get feedback between batches

5. **Stop when blocked** — Don't push through problems

6. **Design is upstream** — If design is wrong, go back to brainstorming
