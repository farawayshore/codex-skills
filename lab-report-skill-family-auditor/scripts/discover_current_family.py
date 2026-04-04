from __future__ import annotations

from pathlib import Path

from common import parse_skill_frontmatter_name, read_text, relative_file_list


def discover_current_family(skills_root: Path, planned_names: set[str]) -> dict[str, object]:
    snapshot: dict[str, object] = {"skills": {}}

    for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        canonical_name = parse_skill_frontmatter_name(skill_md) or skill_dir.name
        if canonical_name not in planned_names and skill_dir.name not in planned_names:
            continue

        agent_prompt_path = skill_dir / "agents" / "openai.yaml"
        files = relative_file_list(skill_dir)
        snapshot["skills"][canonical_name] = {
            "folder_name": skill_dir.name,
            "skill_path": str(skill_dir),
            "legacy_alias": skill_dir.name != canonical_name,
            "files": files,
            "skill_markdown": read_text(skill_md),
            "agent_prompt": read_text(agent_prompt_path) if agent_prompt_path.exists() else "",
        }

    return snapshot
