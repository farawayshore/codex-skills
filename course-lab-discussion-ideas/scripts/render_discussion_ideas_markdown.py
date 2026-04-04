from __future__ import annotations


def render_discussion_ideas_markdown(payload: dict[str, object]) -> str:
    candidate_count = payload.get("candidate_count", 0)
    lines = [
        "# Discussion Ideas",
        "",
        f"- Candidate count: {candidate_count}",
        f"- Broad first-pass search used: {str(bool(payload.get('broad_first_pass_search_used'))).lower()}",
        "",
    ]
    for item in payload.get("discussion_ideas", []):
        if not isinstance(item, dict):
            continue
        lines.append(f"## {item.get('idea_id', 'idea')}")
        lines.append("")
        lines.append(f"- Title: {item.get('title', '')}")
        lines.append(f"- Category: {item.get('category', '')}")
        lines.append(f"- Confidence: {item.get('confidence_level', '')}")
        lines.append(f"- Targeted web rounds: {item.get('targeted_web_round_count', 0)}")
        lines.append(f"- Reuse status: {item.get('reuse_status', '')}")
        lines.append(f"- Broad web seeded: {str(bool(item.get('broad_web_seeded'))).lower()}")
        lines.append(f"- Reusable snippet: {item.get('reusable_snippet', '')}")
        lines.append(f"- Approval status: {item.get('approval_status', '')}")
        lines.append(f"- Approval basis: {item.get('approval_basis', '')}")
        lines.append("")
    return "\n".join(lines) + "\n"


def render_unresolved_markdown(lines: list[str]) -> str:
    output = ["# Discussion Ideas Unresolved", ""]
    for line in lines:
        output.append(f"- {line}")
    output.append("")
    return "\n".join(output) + "\n"


def render_synthesis_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Discussion Synthesis Input",
        "",
        f"- Candidate count: {payload.get('candidate_count', 0)}",
        f"- Approval mode: {payload.get('approval_mode', '')}",
        "",
    ]
    for item in payload.get("discussion_ideas", []):
        if not isinstance(item, dict):
            continue
        lines.append(f"## {item.get('idea_id', 'idea')}")
        lines.append("")
        lines.append(f"- Approval status: {item.get('approval_status', '')}")
        lines.append(f"- Approval basis: {item.get('approval_basis', '')}")
        lines.append(f"- Suggested position: {item.get('suggested_synthesis_position', '')}")
        lines.append(f"- Wording posture: {item.get('wording_posture', '')}")
        lines.append(f"- Reusable snippet: {item.get('reusable_snippet', '')}")
        lines.append("")
    return "\n".join(lines) + "\n"
