#!/usr/bin/env python3
"""Create or reuse a Modern Physics report workspace for an experiment."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path

from common import BUILD_TEMPLATE, RESULTS_ROOT, copy_if_needed, ensure_executable, safe_experiment_dirname, write_json


STANDARD_DIRS = (
    "analysis",
    "appendix",
    "notes",
    "pictures-generated",
    "review",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--results-root", default=str(RESULTS_ROOT))
    parser.add_argument("--template", help="Chosen template .tex path.")
    parser.add_argument("--mode", choices=("new", "modify", "rewrite"), default="new")
    parser.add_argument("--canonical-tex", help="Explicit canonical .tex path when modifying.")
    parser.add_argument("--handout", action="append", default=[])
    parser.add_argument("--reference-report", action="append", default=[])
    parser.add_argument("--data-file", action="append", default=[])
    parser.add_argument("--signatory-file", action="append", default=[])
    parser.add_argument("--refresh-build-script", action="store_true")
    parser.add_argument("--output-json", help="Optional manifest output path.")
    return parser.parse_args()


def choose_canonical_tex(outdir: Path, explicit: str | None) -> Path:
    if explicit:
        candidate = Path(explicit)
        if not candidate.is_absolute():
            candidate = outdir / candidate
        return candidate

    main_tex = outdir / "main.tex"
    if main_tex.exists():
        return main_tex

    tex_files = sorted(outdir.glob("*.tex"))
    if len(tex_files) == 1:
        return tex_files[0]
    if len(tex_files) > 1:
        raise SystemExit(
            f"Multiple .tex files exist in {outdir}. Confirm the canonical file first and rerun with --canonical-tex."
        )
    return main_tex


def maybe_copy_template(template_path: Path, destination: Path, mode: str) -> dict[str, str] | None:
    if mode == "modify":
        return None

    if not template_path.is_file():
        raise SystemExit(f"Missing template file: {template_path}")

    backup_info: dict[str, str] | None = None
    if destination.exists() and mode == "rewrite":
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = destination.with_name(f"{destination.stem}.pre-rewrite-{stamp}{destination.suffix}")
        shutil.copy2(destination, backup_path)
        backup_info = {"backup_path": str(backup_path)}

    copy_if_needed(template_path, destination)
    return backup_info


def main() -> int:
    args = parse_args()

    results_root = Path(args.results_root)
    results_root.mkdir(parents=True, exist_ok=True)
    outdir = results_root / safe_experiment_dirname(args.experiment)
    existed_before = outdir.exists()
    outdir.mkdir(parents=True, exist_ok=True)

    for rel in STANDARD_DIRS:
        (outdir / rel).mkdir(parents=True, exist_ok=True)

    canonical_tex = choose_canonical_tex(outdir, args.canonical_tex)
    template_info = None
    if args.mode == "new" and canonical_tex.exists():
        raise SystemExit(
            f"Canonical TeX file already exists for new mode: {canonical_tex}. Use --mode modify or --mode rewrite."
        )
    if args.mode in {"new", "rewrite"}:
        template_path = Path(args.template) if args.template else None
        if template_path is None:
            raise SystemExit("--template is required for --mode new or --mode rewrite")
        template_info = maybe_copy_template(template_path, canonical_tex, args.mode)
    elif args.mode == "modify" and not canonical_tex.exists():
        raise SystemExit(f"Canonical TeX file does not exist for modify mode: {canonical_tex}")

    procedures_path = outdir / f"{safe_experiment_dirname(args.experiment)}_procedures.md"
    if not procedures_path.exists():
        procedures_path.write_text(
            "# Procedures\n\n"
            "<!-- Keep stable IDs like P01, P02, ... and mirror them in TeX comments as % procedure:P01 -->\n",
            encoding="utf-8",
        )

    build_dst = outdir / "build.sh"
    if args.refresh_build_script or not build_dst.exists():
        copy_if_needed(BUILD_TEMPLATE, build_dst)
        ensure_executable(build_dst)

    manifest = {
        "experiment": args.experiment,
        "workspace": str(outdir),
        "existed_before": existed_before,
        "mode": args.mode,
        "canonical_tex": str(canonical_tex),
        "procedures_markdown": str(procedures_path),
        "standard_dirs": [str(outdir / rel) for rel in STANDARD_DIRS],
        "template": args.template,
        "handouts": args.handout,
        "reference_reports": args.reference_report,
        "data_files": args.data_file,
        "signatory_files": args.signatory_file,
        "build_script": str(build_dst),
    }
    if template_info:
        manifest.update(template_info)

    manifest_path = outdir / "notes" / "workspace_manifest.json"
    write_json(manifest_path, manifest)

    if args.output_json:
        write_json(Path(args.output_json), manifest)

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
