from __future__ import annotations

from pathlib import Path

from common import (
    SKILL_TOKEN_RE,
    collect_bullet_block,
    collect_leading_bullets,
    dated_name_key,
    extract_h2_section,
    read_lines,
)


SKILL_HEADING_PREFIX = "### `"


def choose_plan_document(search_root: Path, override: Path | None) -> tuple[Path, str]:
    if override is not None:
        return Path(override), "explicit user override"

    candidates: dict[Path, None] = {}
    for pattern in ("*family-summary*.md", "*planning*.md"):
        for path in search_root.rglob(pattern):
            if path.is_file():
                candidates[path] = None

    if not candidates:
        raise FileNotFoundError(f"no planning document candidates found under {search_root}")

    chosen = max(candidates, key=dated_name_key)
    return chosen, "newest dated filename with filesystem recency tie-breaker"


def parse_skill_sections(lines: list[str]) -> tuple[dict[str, str], dict[str, list[str]]]:
    current_h2 = ""
    current_skill: str | None = None
    skill_roles: dict[str, str] = {}
    skill_sections: dict[str, list[str]] = {}

    for line in lines:
        if line.startswith("## "):
            current_h2 = line[3:].strip()
            current_skill = None
            continue

        if line.startswith(SKILL_HEADING_PREFIX) and line.endswith("`"):
            skill_name = line[len(SKILL_HEADING_PREFIX) : -1]
            current_skill = skill_name
            skill_sections.setdefault(skill_name, [])
            if current_h2 == "Role Of The Parent Skill":
                skill_roles[skill_name] = "parent"
            elif current_h2 == "Leaf Subskills":
                skill_roles.setdefault(skill_name, "leaf")
            elif current_h2 == "Shared Dependency Skills":
                skill_roles[skill_name] = "shared_dependency"
            else:
                skill_roles.setdefault(skill_name, "unknown")
            continue

        if current_skill is not None:
            skill_sections[current_skill].append(line)

    return skill_roles, skill_sections


def build_skill_contracts(skill_roles: dict[str, str], skill_sections: dict[str, list[str]]) -> dict[str, dict[str, list[str]]]:
    contracts: dict[str, dict[str, list[str]]] = {}
    for skill_name, section_lines in skill_sections.items():
        role = skill_roles.get(skill_name)
        owns_label = "It should own:" if role == "parent" else "Owns:"
        not_own_label = "It should not directly own:" if role == "parent" else "Should not own:"
        contracts[skill_name] = {
            "owns": collect_bullet_block(section_lines, owns_label),
            "should_not_own": collect_bullet_block(section_lines, not_own_label),
            "expected_inputs": collect_bullet_block(section_lines, "Expected inputs:"),
            "expected_outputs": collect_bullet_block(section_lines, "Expected outputs:"),
            "expected_dependencies": collect_bullet_block(section_lines, "Should depend on:"),
        }
    return contracts


def extract_relation_order(lines: list[str]) -> list[str]:
    section_lines = extract_h2_section(lines, "Relations Between Skills")
    relation_order: list[str] = []
    for line in section_lines:
        stripped = line.strip()
        if not stripped or not stripped[0].isdigit():
            continue
        match = SKILL_TOKEN_RE.search(stripped)
        if match:
            relation_order.append(match.group(1))
    return relation_order


def extract_skill_tokens(section_lines: list[str]) -> set[str]:
    return {match.group(1) for match in SKILL_TOKEN_RE.finditer("\n".join(section_lines))}


def build_family_manifest(plan_path: Path) -> dict[str, object]:
    text = plan_path.read_text(encoding="utf-8")
    lines = read_lines(plan_path)
    skill_roles, skill_sections = parse_skill_sections(lines)
    skill_contracts = build_skill_contracts(skill_roles, skill_sections)
    high_level_tree_tokens = extract_skill_tokens(extract_h2_section(lines, "High-Level Skill Tree"))
    relation_order = extract_relation_order(lines)

    planned_skill_names = set(skill_roles)
    planned_skill_names.update(high_level_tree_tokens)
    planned_skill_names.update(relation_order)
    planned_skills = sorted(planned_skill_names)
    shared_dependencies = {
        skill_name for skill_name, role in skill_roles.items() if role == "shared_dependency"
    }
    shared_dependencies.update(
        skill_name
        for skill_name in high_level_tree_tokens
        if skill_name in {"mineru-pdf-json", "mineru-pdf-markdown", "compress-png", "physics-lab-mathematica-modeling"}
    )

    return {
        "plan_path": str(plan_path),
        "planned_skills": planned_skills,
        "shared_dependencies": sorted(shared_dependencies),
        "skill_roles": skill_roles,
        "skill_contracts": skill_contracts,
        "relation_order": relation_order,
        "boundary_rules": collect_leading_bullets(extract_h2_section(lines, "Boundary Rules")),
        "raw_text": text,
    }
