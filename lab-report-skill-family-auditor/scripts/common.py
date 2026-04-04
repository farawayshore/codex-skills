from __future__ import annotations

import re
from pathlib import Path


DATE_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-")
SKILL_TOKEN_RE = re.compile(
    r"`?(course-lab-[a-z0-9-]+|physics-lab-[a-z0-9-]+|mineru-pdf-json|mineru-pdf-markdown|compress-png)`?"
)


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_h2_section(lines: list[str], heading: str) -> list[str]:
    in_section = False
    collected: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if in_section:
                break
            in_section = line[3:].strip() == heading
            continue
        if in_section:
            collected.append(line)
    return collected


def collect_bullet_block(section_lines: list[str], label: str) -> list[str]:
    items: list[str] = []
    collecting = False
    for line in section_lines:
        stripped = line.strip()
        if not collecting:
            if stripped == label:
                collecting = True
            continue
        if stripped.startswith("- "):
            items.append(stripped[2:].strip().strip("`"))
            continue
        if not stripped:
            continue
        break
    return items


def collect_leading_bullets(section_lines: list[str]) -> list[str]:
    items: list[str] = []
    for line in section_lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip().strip("`"))
    return items


def dated_name_key(path: Path) -> tuple[int, str, float, str]:
    match = DATE_PREFIX_RE.match(path.name)
    if match:
        return (1, match.group(1), path.stat().st_mtime, path.name)
    return (0, "", path.stat().st_mtime, path.name)


def parse_skill_frontmatter_name(skill_md_path: Path) -> str | None:
    text = read_text(skill_md_path)
    if not text.startswith("---"):
        return None

    lines = text.splitlines()
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if stripped.startswith("name:"):
            return stripped.split(":", 1)[1].strip()
    return None


def relative_file_list(root: Path) -> list[str]:
    return sorted(
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file()
    )
