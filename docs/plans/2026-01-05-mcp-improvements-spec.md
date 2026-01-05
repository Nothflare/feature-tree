# MCP Improvements Spec

> **For Next Session:** Implement these fixes in order of priority.

## Priority 1: Add `confidence` Param to MCP Tools

### Problem
The DB layer supports `confidence` field, but MCP tools don't expose it.

### Files to Modify
- `feature-tree/feature_tree/mcp_server.py`

### Changes

#### 1.1 add_feature()
```python
# Current (line ~203)
def add_feature(
    id: str,
    name: str,
    parent_id: str | None = None,
    description: str | None = None,
    uses: list[str] | None = None
) -> str:

# Fix: Add confidence param
def add_feature(
    id: str,
    name: str,
    parent_id: str | None = None,
    description: str | None = None,
    uses: list[str] | None = None,
    confidence: str | None = None  # ADD THIS
) -> str:

# Also update the db.add_feature call to pass confidence
db.add_feature(id=id, name=name, parent_id=parent_id,
               description=description, uses=uses, confidence=confidence)
```

#### 1.2 update_feature()
```python
# Current (line ~221)
def update_feature(
    id: str,
    status: str | None = None,
    code_symbols: list[str] | None = None,
    files: list[str] | None = None,
    commit_ids: list[str] | None = None,
    technical_notes: str | None = None,
    description: str | None = None,
    uses: list[str] | None = None
) -> str:

# Fix: Add confidence param and handling
def update_feature(
    id: str,
    status: str | None = None,
    code_symbols: list[str] | None = None,
    files: list[str] | None = None,
    commit_ids: list[str] | None = None,
    technical_notes: str | None = None,
    description: str | None = None,
    uses: list[str] | None = None,
    confidence: str | None = None  # ADD THIS
) -> str:

# Add to fields dict:
if confidence is not None:
    fields["confidence"] = confidence
```

#### 1.3 add_workflow()
```python
# Current (line ~325)
def add_workflow(
    id: str,
    name: str,
    parent_id: str | None = None,
    description: str | None = None,
    purpose: str | None = None,
    depends_on: list[str] | None = None,
    mermaid: str | None = None
) -> str:

# Fix: Add confidence param
def add_workflow(
    id: str,
    name: str,
    parent_id: str | None = None,
    description: str | None = None,
    purpose: str | None = None,
    depends_on: list[str] | None = None,
    mermaid: str | None = None,
    confidence: str | None = None  # ADD THIS
) -> str:

# Update db.add_workflow call to pass confidence
```

#### 1.4 update_workflow()
```python
# Current (line ~368)
def update_workflow(
    id: str,
    status: str | None = None,
    depends_on: list[str] | None = None,
    mermaid: str | None = None,
    description: str | None = None,
    purpose: str | None = None
) -> str:

# Fix: Add confidence param
def update_workflow(
    id: str,
    status: str | None = None,
    depends_on: list[str] | None = None,
    mermaid: str | None = None,
    description: str | None = None,
    purpose: str | None = None,
    confidence: str | None = None  # ADD THIS
) -> str:

# Add to fields dict
```

#### 1.5 search_features() - Show confidence in results
```python
# Current (line ~182-197)
trimmed = []
for r in results:
    item = {"id": r["id"], "name": r["name"], "status": r["status"], "parent_id": r.get("parent_id")}
    if r.get("uses"):
        uses_list = json.loads(r["uses"])
        if uses_list:
            item["uses_count"] = len(uses_list)
    trimmed.append(item)

# Fix: Add confidence to output
    if r.get("confidence"):
        item["confidence"] = r["confidence"]
```

#### 1.6 search_workflows() - Show confidence in results
```python
# Current (line ~315-320)
trimmed = [
    {"id": r["id"], "name": r["name"], "status": r["status"], "parent_id": r.get("parent_id")}
    for r in results
]

# Fix: Change to loop and add confidence
trimmed = []
for r in results:
    item = {"id": r["id"], "name": r["name"], "status": r["status"], "parent_id": r.get("parent_id")}
    if r.get("confidence"):
        item["confidence"] = r["confidence"]
    trimmed.append(item)
```

---

## Priority 2: FTS Index for files/code_symbols

### Problem
`files` and `code_symbols` are NOT in FTS5 index. Cannot search "which feature owns this file" or "which feature has this function".

### Files to Modify
- `feature-tree/feature_tree/db.py`

### Option A: Add to FTS Index (Recommended)

```python
# Current FTS table (line ~35)
CREATE VIRTUAL TABLE IF NOT EXISTS features_fts USING fts5(
    id, name, description, technical_notes
);

# Fix: Add files and code_symbols
CREATE VIRTUAL TABLE IF NOT EXISTS features_fts USING fts5(
    id, name, description, technical_notes, files, code_symbols
);
```

Also update `_sync_fts()` method to include these fields.

**Note:** This requires recreating the FTS table for existing databases. Add migration:
```python
def _migrate_fts_add_columns(self):
    # Drop and recreate FTS table with new columns
    # Re-sync all features
```

### Option B: Add find_feature_by_file() Tool

```python
@mcp.tool()
def find_feature_by_file(file_path: str) -> str:
    """Find which feature owns a specific file."""
    db = get_db()
    try:
        # Query features table where files JSON contains file_path
        results = db.execute("""
            SELECT id, name, status, files
            FROM features
            WHERE files LIKE ?
        """, (f'%{file_path}%',)).fetchall()
        # Return matching features
    finally:
        db.close()
```

---

## Priority 3: Validate References

### Problem
`uses` and `depends_on` accept non-existent feature IDs without warning.

### Files to Modify
- `feature-tree/feature_tree/mcp_server.py`

### Changes

```python
def add_feature(..., uses: list[str] | None = None, ...):
    db = get_db()
    try:
        # Validate uses references
        warnings = []
        if uses:
            for ref_id in uses:
                if not db.get_feature(ref_id):
                    warnings.append(f"Warning: uses references non-existent feature '{ref_id}'")

        db.add_feature(...)
        regenerate_markdown()

        result = {"ok": True}
        if warnings:
            result["warnings"] = warnings
        return json.dumps(result)
    finally:
        db.close()
```

Same pattern for `add_workflow` with `depends_on`.

---

## Priority 4: Complete Handoff Templates

### Problem
DEBUGGING and BLOCKED templates in handoff.md missing "Continue Protocol" section.

### Files to Modify
- `ft-mem/commands/handoff.md`

### Changes
Add this section to both DEBUGGING and BLOCKED templates:

```markdown
## Continue Protocol for Next Session

**Before any implementation, trace the data flow:**

1. For each feature below, run `get_feature(id)` to see current state
2. Check `linked_workflows` to find related workflows
3. For each workflow, run `get_workflow(id)` to understand the data flow
4. Trace: where does data come from → how it transforms → where it goes

**DO NOT speculate about data structures or DB schema. Trace the actual flow.**
```

---

## Testing

After implementing:

1. **Confidence params:**
   ```python
   add_feature(id="TEST.conf", name="Test", confidence="HIGH")
   search_features("TEST")  # Should show confidence
   update_feature(id="TEST.conf", confidence="LOW")
   ```

2. **FTS search:**
   ```python
   update_feature(id="TEST.conf", files=["src/test.py"])
   search_features("src/test.py")  # Should find TEST.conf
   ```

3. **Validation:**
   ```python
   add_feature(id="TEST.bad", name="Bad", uses=["NONEXISTENT.thing"])
   # Should return warning about non-existent reference
   ```

---

## Version Bump

After all fixes: bump to **feature-tree v2.0.3**
