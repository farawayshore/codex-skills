from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_family_manifest import build_family_manifest, choose_plan_document
from discover_current_family import discover_current_family


def prepare_family_audit(
    plan_root: Path,
    override: Path | None,
    skills_root: Path,
    output_dir: Path,
) -> dict[str, str]:
    plan_path, selection_reason = choose_plan_document(plan_root, override)
    manifest = build_family_manifest(plan_path)
    target_names = set(manifest["planned_skills"]) | set(manifest["shared_dependencies"])
    snapshot = discover_current_family(skills_root, target_names)

    stem = plan_path.stem
    support_dir = output_dir / "audit_support" / stem
    support_dir.mkdir(parents=True, exist_ok=True)

    family_manifest_path = support_dir / "family_manifest.json"
    family_snapshot_path = support_dir / "current_family_snapshot.json"
    family_manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    family_snapshot_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "plan_path": str(plan_path),
        "selection_reason": selection_reason,
        "support_dir": str(support_dir),
        "family_manifest_path": str(family_manifest_path),
        "current_family_snapshot_path": str(family_snapshot_path),
        "report_path": str(output_dir / f"lab_report_skill_family_audit_{stem}.md"),
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare support artifacts for the lab-report skill family auditor.")
    parser.add_argument("--plan-root", type=Path, default=Path.cwd(), help="Root to search for planning documents.")
    parser.add_argument("--plan", type=Path, default=None, help="Explicit planning document path.")
    parser.add_argument("--skills-root", type=Path, required=True, help="Installed skills root to inspect.")
    parser.add_argument("--output-dir", type=Path, required=True, help="AI_construction output root.")
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    result = prepare_family_audit(
        plan_root=args.plan_root,
        override=args.plan,
        skills_root=args.skills_root,
        output_dir=args.output_dir,
    )

    print(f"Selected plan: {result['plan_path']}")
    print(f"Selection reason: {result['selection_reason']}")
    print(f"Support dir: {result['support_dir']}")
    print(f"Family manifest: {result['family_manifest_path']}")
    print(f"Current snapshot: {result['current_family_snapshot_path']}")
    print(f"Report target: {result['report_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
