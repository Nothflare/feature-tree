# feature_tree/markdown.py
import json
from typing import Optional
from feature_tree.db import FeatureDB


def generate_features_markdown(db: FeatureDB) -> str:
    """Generate FEATURES.md content."""
    features = db.execute(
        "SELECT * FROM features WHERE status != 'deleted' ORDER BY id"
    ).fetchall()
    features = [dict(f) for f in features]

    tree = build_tree(features)

    lines = [
        "# Features",
        "",
        "> Auto-generated. Do not edit. Use Claude Code to modify.",
        ""
    ]

    for root in tree:
        lines.extend(render_feature(root, level=2))

    return "\n".join(lines)


def generate_workflows_markdown(db: FeatureDB) -> str:
    """Generate WORKFLOWS.md content with mermaid diagrams."""
    workflows = db.execute(
        "SELECT * FROM workflows WHERE status != 'deleted' ORDER BY type, id"
    ).fetchall()
    workflows = [dict(w) for w in workflows]

    tree = build_tree(workflows)

    lines = [
        "# Workflows",
        "",
        "> Auto-generated. Do not edit. Use Claude Code to modify.",
        ""
    ]

    for root in tree:
        lines.extend(render_workflow(root, level=2, db=db))

    return "\n".join(lines)


# Backwards compat
def generate_markdown(db: FeatureDB) -> str:
    return generate_features_markdown(db)


def build_tree(features: list[dict]) -> list[dict]:
    by_id = {f["id"]: {**f, "children": []} for f in features}
    roots = []

    for f in features:
        node = by_id[f["id"]]
        parent_id = f["parent_id"]
        if parent_id and parent_id in by_id:
            by_id[parent_id]["children"].append(node)
        else:
            roots.append(node)

    return roots


def render_feature(feature: dict, level: int) -> list[str]:
    lines = []
    prefix = "#" * level

    # Header with id and name
    lines.append(f"{prefix} {feature['id']}")
    lines.append(f"**{feature['name']}**")
    if feature["description"]:
        lines.append(feature["description"])
    lines.append("")

    # Metadata
    lines.append(f"- **Status:** {feature['status']}")

    if feature.get("code_symbols"):
        symbols = json.loads(feature["code_symbols"])
        if symbols:
            lines.append(f"- **Symbols:** {', '.join(symbols)}")

    if feature.get("files"):
        files = json.loads(feature["files"])
        if files:
            lines.append(f"- **Files:** {', '.join(files)}")

    if feature.get("commit_ids"):
        commits = json.loads(feature["commit_ids"])
        if commits:
            lines.append(f"- **Commits:** {', '.join(commits)}")

    lines.append("")

    # Children
    for child in feature.get("children", []):
        lines.extend(render_feature(child, level + 1))

    return lines


def render_workflow(workflow: dict, level: int, db: FeatureDB) -> list[str]:
    lines = []
    prefix = "#" * level

    # Header with type badge
    type_badge = "🎯" if workflow["type"] == "journey" else "→"
    lines.append(f"{prefix} {type_badge} {workflow['id']}")
    lines.append(f"**{workflow['name']}**")

    if workflow.get("purpose"):
        lines.append(f"*{workflow['purpose']}*")
    if workflow.get("description"):
        lines.append(workflow["description"])
    lines.append("")

    # Metadata
    lines.append(f"- **Type:** {workflow['type']}")
    lines.append(f"- **Status:** {workflow['status']}")

    # Linked features
    if workflow.get("depends_on"):
        depends = json.loads(workflow["depends_on"])
        if depends:
            lines.append(f"- **Depends on:** {', '.join(depends)}")

    lines.append("")

    # Mermaid diagram
    if workflow.get("mermaid"):
        lines.append("```mermaid")
        lines.append(workflow["mermaid"])
        lines.append("```")
        lines.append("")

    # Children (flows under journey)
    for child in workflow.get("children", []):
        lines.extend(render_workflow(child, level + 1, db))

    return lines
