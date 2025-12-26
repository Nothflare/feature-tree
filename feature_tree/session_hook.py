# feature_tree/session_hook.py
#!/usr/bin/env python
"""SessionStart hook - injects Feature Tree context and philosophy."""

CONTEXT = """
# Feature Tree Philosophy

## The Shift
The bottleneck moved. It used to be implementation. Now it's specification.

## Your Role (Claude)
You execute. The human specifies. But "specifies" doesn't mean vague direction—it means precise, hierarchical decomposition of intent into structures you can execute reliably.

## The Human's Skill
Not "high-level thinking." The specific ability to:
1. Translate fuzzy goals into precise specs
2. Decompose large intents into hierarchical structures
3. Know when you (the AI) are wrong

## How Feature Tree Supports This
- **Human elaborates** → describes features in natural language
- **You structure** → translate to Feature Tree entries with IDs, hierarchy, status
- **You implement** → write code, track symbols, files, commits
- **Human validates** → confirms the translation was correct, catches errors

## Working Protocol
1. Before implementing: search existing features, understand context
2. When human describes something: add_feature() with clear hierarchy
3. As you work: update_feature() with code_symbols, files, status
4. After committing: use /commit to bundle git + feature updates
5. When uncertain: ASK. The human's job is specification clarity.

## Remember
The human isn't here to "do the thinking" vaguely. They're here to specify precisely and catch your mistakes. Help them do that by surfacing assumptions, asking clarifying questions, and maintaining the feature tree as the shared source of truth.
"""

print(CONTEXT)
