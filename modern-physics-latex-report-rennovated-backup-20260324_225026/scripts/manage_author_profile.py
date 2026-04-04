#!/usr/bin/env python3
"""Create, read, and update a reusable author profile for lab-report metadata."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from common import AUTHOR_PROFILE_PATH, read_json, write_json


PROFILE_TEMPLATE = {
    "student": {
        "name_zh": "",
        "name_en": "",
        "affiliation_zh": "",
        "affiliation_en": "",
    },
    "collaborator": {
        "name_zh": "",
        "name_en": "",
        "affiliation_zh": "",
        "affiliation_en": "",
    },
    "updated_at": "",
}

REQUIRED_KEYS = [
    "student.name_zh",
    "student.name_en",
    "student.affiliation_zh",
    "student.affiliation_en",
    "collaborator.name_zh",
    "collaborator.name_en",
    "collaborator.affiliation_zh",
    "collaborator.affiliation_en",
]


def clone_template() -> dict[str, object]:
    return json.loads(json.dumps(PROFILE_TEMPLATE))


def normalize_profile(payload: object) -> dict[str, object]:
    profile = clone_template()
    if not isinstance(payload, dict):
        return profile

    for role in ("student", "collaborator"):
        section = payload.get(role)
        if not isinstance(section, dict):
            continue
        for key in ("name_zh", "name_en", "affiliation_zh", "affiliation_en"):
            value = section.get(key)
            if isinstance(value, str):
                profile[role][key] = value

    updated_at = payload.get("updated_at")
    if isinstance(updated_at, str):
        profile["updated_at"] = updated_at
    return profile


def set_dotted_value(profile: dict[str, object], dotted_key: str, value: str) -> None:
    parts = dotted_key.split(".")
    if len(parts) != 2 or parts[0] not in {"student", "collaborator"}:
        raise SystemExit(f"Unsupported profile key: {dotted_key}")
    role, field = parts
    if field not in {"name_zh", "name_en", "affiliation_zh", "affiliation_en"}:
        raise SystemExit(f"Unsupported profile field: {dotted_key}")
    profile[role][field] = value


def missing_fields(profile: dict[str, object]) -> list[str]:
    missing: list[str] = []
    for dotted_key in REQUIRED_KEYS:
        role, field = dotted_key.split(".")
        value = str(profile.get(role, {}).get(field, "")).strip()
        if not value:
            missing.append(dotted_key)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", help="Optional override path for the author profile JSON file.")
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        help="Update a dotted profile key, for example --set student.name_zh=张三",
    )
    args = parser.parse_args()

    profile_path = Path(args.profile).expanduser().resolve() if args.profile else AUTHOR_PROFILE_PATH
    created = not profile_path.exists()
    payload = read_json(profile_path) if profile_path.exists() else None
    profile = normalize_profile(payload)

    updated = created
    for item in args.set:
        if "=" not in item:
            raise SystemExit(f"Expected dotted_key=value syntax, got: {item}")
        dotted_key, value = item.split("=", 1)
        set_dotted_value(profile, dotted_key.strip(), value)
        updated = True

    if updated:
        profile["updated_at"] = datetime.now(timezone.utc).isoformat()
        write_json(profile_path, profile)

    print(
        json.dumps(
            {
                "path": str(profile_path),
                "created": created,
                "updated": updated,
                "missing_fields": missing_fields(profile),
                "profile": profile,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
