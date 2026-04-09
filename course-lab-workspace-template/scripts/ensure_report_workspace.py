#!/usr/bin/env python3
"""Create or reuse a course lab-report workspace for an experiment."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
from pathlib import Path
from typing import Any

from common import BUILD_TEMPLATE, RESULTS_ROOT, copy_if_needed, ensure_executable, read_json, safe_experiment_dirname, write_json


STANDARD_DIRS = (
    "analysis",
    "appendix",
    "notes",
    "pictures-generated",
    "review",
)

NEEDS_INPUT_PACKAGE = r"\usepackage{xcolor}"
NEEDS_INPUT_COLOR = r"\definecolor{NeedsInputRed}{RGB}{220,110,110}"
NEEDS_INPUT_MACRO = r"\newcommand{\NeedsInput}[1]{\textcolor{NeedsInputRed}{#1}}"

XCOLOR_PACKAGE_RE = re.compile(
    r"\\(?:usepackage|RequirePackage)(?:\[[^\]]*\])?\{(?:[^{}]*,)?(?:xcolor|color)(?:,[^{}]*)?\}"
)
NEEDS_INPUT_COLOR_RE = re.compile(r"\\definecolor\s*\{NeedsInputRed\}")
NEEDS_INPUT_DEFINITION_RE = re.compile(r"\\(?:newcommand|renewcommand|providecommand)\s*\{\\NeedsInput\}")
BEGIN_DOCUMENT_RE = re.compile(r"(?m)^\\begin\{document\}")
SECTION_BLOCK_RE = re.compile(r"(?ms)^\\section\{(?P<heading>[^}]+)\}[ \t]*\n(?P<body>.*?)(?=^\\section\{|^\\appendix\b|\Z)")

STOCK_TAU_SCaffold_CUES = (
    "Briefly introduce the physical phenomenon, the scientific background, and the practical value of the experiment.",
    "State the main physical quantity or phenomenon to be measured or verified.",
    "Replace the example formulas below with the equations for your own experiment.",
    "Perform the safety check and instrument warm-up.",
    "Present the original measurements clearly.",
    "Interpret whether the results support the theory, whether the observed phenomena match expectations",
)

FINAL_STAGING_ALLOW_OVERWRITE = "% course-lab-final-staging:allow-overwrite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--discovery-json", help="Optional discovery-cache JSON path from course-lab-discovery.")
    parser.add_argument("--course", help="Course name for this report run.")
    parser.add_argument("--experiment", help="Experiment name for this report run.")
    parser.add_argument("--results-root", help="Override for the results root directory.")
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


def load_discovery_payload(path_text: str | None) -> tuple[Path | None, dict[str, object] | None]:
    if not path_text:
        return None, None

    path = Path(path_text)
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise SystemExit(f"Discovery cache is missing or not a JSON object: {path}")
    return path, payload


def discovery_paths(payload: dict[str, object] | None, key: str) -> list[str]:
    if not payload:
        return []

    values = payload.get(key)
    if not isinstance(values, list):
        return []

    paths: list[str] = []
    for item in values:
        if isinstance(item, dict):
            path_value = item.get("path")
            if isinstance(path_value, str) and path_value:
                paths.append(path_value)
        elif isinstance(item, str) and item:
            paths.append(item)
    return paths


def resolved_course(args: argparse.Namespace, discovery_payload: dict[str, object] | None) -> str | None:
    if args.course:
        return args.course
    if discovery_payload and isinstance(discovery_payload.get("course"), str):
        return str(discovery_payload["course"])
    return None


def resolved_experiment(args: argparse.Namespace, discovery_payload: dict[str, object] | None) -> str:
    if args.experiment:
        return args.experiment
    if discovery_payload and isinstance(discovery_payload.get("experiment_query"), str):
        return str(discovery_payload["experiment_query"])
    raise SystemExit("--experiment is required unless --discovery-json provides experiment_query")


def resolved_results_root(args: argparse.Namespace, discovery_payload: dict[str, object] | None) -> Path:
    if args.results_root:
        return Path(args.results_root)

    roots = discovery_payload.get("roots") if isinstance(discovery_payload, dict) else None
    if isinstance(roots, dict):
        discovery_results_root = roots.get("results_root")
        if isinstance(discovery_results_root, str) and discovery_results_root:
            return Path(discovery_results_root)

    return RESULTS_ROOT


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


def infer_template_language(template_path: Path) -> str | None:
    lowered_parts = [part.lower() for part in template_path.parts]
    for language in ("english", "chinese"):
        if language in lowered_parts:
            return language
    return None


def backup_existing_tex(destination: Path, mode: str) -> dict[str, str] | None:
    if mode != "rewrite" or not destination.exists():
        return None

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = destination.with_name(f"{destination.stem}.pre-rewrite-{stamp}{destination.suffix}")
    shutil.copy2(destination, backup_path)
    return {"backup_path": str(backup_path)}


def template_contract(template_path: Path | None) -> dict[str, Any]:
    if template_path is None:
        return {
            "template_kind": None,
            "template_language": None,
            "template_root": None,
            "template_entry": None,
            "copied_companion_assets": [],
        }

    if template_path.is_dir():
        entry = template_path / "main.tex"
        if not entry.is_file():
            raise SystemExit(f"Bundle template directory must contain main.tex: {template_path}")
        return {
            "template_kind": "bundle",
            "template_language": infer_template_language(template_path),
            "template_root": str(template_path),
            "template_entry": str(entry),
            "copied_companion_assets": [],
        }

    if template_path.is_file() and template_path.suffix.lower() == ".tex":
        return {
            "template_kind": "file",
            "template_language": infer_template_language(template_path),
            "template_root": str(template_path.parent),
            "template_entry": str(template_path),
            "copied_companion_assets": [],
        }

    raise SystemExit(f"Template must be a .tex file or a directory containing main.tex: {template_path}")


def copy_bundle_template(template_root: Path, outdir: Path) -> list[str]:
    copied_assets: list[str] = []
    for source_path in sorted(path for path in template_root.rglob("*") if path.is_file()):
        relative_path = source_path.relative_to(template_root)
        destination = outdir / relative_path
        copy_if_needed(source_path, destination)
        if relative_path.as_posix() != "main.tex":
            copied_assets.append(relative_path.as_posix())
    return copied_assets


def apply_template(
    template_path: Path,
    outdir: Path,
    canonical_tex: Path,
    mode: str,
) -> tuple[Path, dict[str, Any]]:
    metadata = template_contract(template_path)
    backup_info: dict[str, str] | None = None

    if metadata["template_kind"] == "file":
        backup_info = backup_existing_tex(canonical_tex, mode)
        copy_if_needed(template_path, canonical_tex)
        final_canonical_tex = canonical_tex
    else:
        bundle_main = outdir / "main.tex"
        if canonical_tex != bundle_main and canonical_tex.exists():
            backup_info = backup_existing_tex(canonical_tex, mode)
        else:
            backup_info = backup_existing_tex(bundle_main, mode)
        metadata["copied_companion_assets"] = copy_bundle_template(template_path, outdir)
        final_canonical_tex = bundle_main

    if backup_info:
        metadata.update(backup_info)
    return final_canonical_tex, metadata


def ensure_placeholder_macros(tex_path: Path) -> dict[str, bool]:
    text = tex_path.read_text(encoding="utf-8")

    if NEEDS_INPUT_DEFINITION_RE.search(text):
        return {
            "needs_input_macro_added": False,
            "needs_input_color_added": False,
            "needs_input_xcolor_added": False,
        }

    additions: list[str] = []
    needs_input_xcolor_added = False
    needs_input_color_added = False

    if not XCOLOR_PACKAGE_RE.search(text):
        additions.append(NEEDS_INPUT_PACKAGE)
        needs_input_xcolor_added = True
    if not NEEDS_INPUT_COLOR_RE.search(text):
        additions.append(NEEDS_INPUT_COLOR)
        needs_input_color_added = True
    additions.append(NEEDS_INPUT_MACRO)

    insertion = "\n".join(additions) + "\n"
    match = BEGIN_DOCUMENT_RE.search(text)
    if match:
        prefix = text[: match.start()]
        if prefix and not prefix.endswith("\n"):
            prefix += "\n"
        text = prefix + insertion + text[match.start() :]
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        text += insertion

    tex_path.write_text(text, encoding="utf-8")
    return {
        "needs_input_macro_added": True,
        "needs_input_color_added": needs_input_color_added,
        "needs_input_xcolor_added": needs_input_xcolor_added,
    }


def looks_like_stock_tau_template(text: str) -> bool:
    heading_hits = sum(
        1
        for heading in (
            r"\section{Experiment Purpose}",
            r"\section{Experiment Steps}",
            r"\section{Experiment Process and Results}",
            r"\section{Experiment Discussion}",
        )
        if heading in text
    )
    cue_hits = sum(1 for cue in STOCK_TAU_SCaffold_CUES if cue in text)
    return heading_hits >= 3 and cue_hits >= 3


def replace_section_block(
    text: str,
    *,
    source_heading: str,
    target_heading: str | None = None,
    new_body: str | None = None,
) -> tuple[str, bool]:
    target = target_heading or source_heading
    pattern = re.compile(
        rf"(?ms)^\\section\{{{re.escape(source_heading)}\}}[ \t]*\n(?P<body>.*?)(?=^\\section\{{|^\\appendix\b|\Z)"
    )
    match = pattern.search(text)
    if match is None:
        return text, False

    body = new_body if new_body is not None else match.group("body")
    replacement = f"\\section{{{target}}}\n{body.rstrip()}\n\n"
    return text[: match.start()] + replacement + text[match.end() :], True


def normalize_stock_tau_template_scaffold(tex_path: Path) -> dict[str, bool]:
    text = tex_path.read_text(encoding="utf-8")
    if not looks_like_stock_tau_template(text):
        return {"stock_scaffold_normalized": False}

    text, _ = replace_section_block(
        text,
        source_heading="Introduction",
        new_body=r"\NeedsInput{Draft the introduction from the normalized handout and experiment-specific context.}",
    )
    text, _ = replace_section_block(
        text,
        source_heading="Experiment Purpose",
        target_heading="Objectives",
        new_body=(
            "\\begin{itemize}\n"
            "    \\item \\NeedsInput{State the main experiment objective.}\n"
            "    \\item \\NeedsInput{State the main instrument or operational skill developed in the experiment.}\n"
            "    \\item \\NeedsInput{State the intended theory, literature, or reference comparison.}\n"
            "\\end{itemize}"
        ),
    )
    text, _ = replace_section_block(
        text,
        source_heading="Experiment Principle",
        new_body=r"\NeedsInput{Draft the experiment principle from the normalized handout and stage any theory figures inside this section.}",
    )
    text, _ = replace_section_block(
        text,
        source_heading="Experiment Steps",
        target_heading="Experimental Procedure and Observations",
        new_body=(
            f"{FINAL_STAGING_ALLOW_OVERWRITE}\n"
            r"\NeedsInput{Draft the experimental procedure and observations from the normalized handout and validated evidence.}"
        ),
    )
    text, _ = replace_section_block(
        text,
        source_heading="Experiment Process and Results",
        target_heading="Results and Analysis",
        new_body=(
            f"{FINAL_STAGING_ALLOW_OVERWRITE}\n"
            r"\NeedsInput{Draft the results and analysis section after processed data, interpretation, and discussion artifacts are stable.}"
        ),
    )
    text, _ = replace_section_block(
        text,
        source_heading="Experiment Discussion",
        new_body=(
            f"{FINAL_STAGING_ALLOW_OVERWRITE}\n"
            r"\NeedsInput{Draft the experiment discussion after the synthesized discussion artifacts are stable.}"
        ),
    )

    if r"\section{Appendix}" not in text:
        appendix_block = (
            "\\appendix\n"
            "\\section{Appendix}\n"
            f"{FINAL_STAGING_ALLOW_OVERWRITE}\n"
            r"\NeedsInput{Add appendix code, data files, or other late-stage artifacts when they are available.}"
            "\n\n"
        )
        comment_pattern = re.compile(
            r"(?ms)^% Uncomment the next lines if you need appendices\.\n"
            r"% \\appendix\n"
            r"% \\section\{Appendix\}\n"
            r"% Put supplementary derivations, extra tables, or code here\.\n?"
        )
        if comment_pattern.search(text):
            text = comment_pattern.sub(appendix_block, text)
        else:
            end_document = text.rfind(r"\end{document}")
            if end_document != -1:
                text = text[:end_document].rstrip() + "\n\n" + appendix_block + text[end_document:]
            else:
                text = text.rstrip() + "\n\n" + appendix_block

    tex_path.write_text(text, encoding="utf-8")
    return {"stock_scaffold_normalized": True}


def main() -> int:
    args = parse_args()
    discovery_json_path, discovery_payload = load_discovery_payload(args.discovery_json)
    course = resolved_course(args, discovery_payload)
    experiment = resolved_experiment(args, discovery_payload)
    handouts = args.handout or discovery_paths(discovery_payload, "handouts")
    reference_reports = args.reference_report or discovery_paths(discovery_payload, "reference_reports")
    data_files = args.data_file or discovery_paths(discovery_payload, "data_files")
    signatory_files = args.signatory_file or discovery_paths(discovery_payload, "signatory_files")

    results_root = resolved_results_root(args, discovery_payload)
    results_root.mkdir(parents=True, exist_ok=True)
    outdir = results_root / safe_experiment_dirname(experiment)
    existed_before = outdir.exists()
    outdir.mkdir(parents=True, exist_ok=True)

    for rel in STANDARD_DIRS:
        (outdir / rel).mkdir(parents=True, exist_ok=True)

    canonical_tex = choose_canonical_tex(outdir, args.canonical_tex)
    if args.mode == "new" and canonical_tex.exists():
        raise SystemExit(
            f"Canonical TeX file already exists for new mode: {canonical_tex}. Use --mode modify or --mode rewrite."
        )
    template_info: dict[str, Any] = template_contract(Path(args.template)) if args.template else template_contract(None)
    if args.mode in {"new", "rewrite"}:
        template_path = Path(args.template) if args.template else None
        if template_path is None:
            raise SystemExit("--template is required for --mode new or --mode rewrite")
        canonical_tex, template_info = apply_template(template_path, outdir, canonical_tex, args.mode)
    elif args.mode == "modify" and not canonical_tex.exists():
        raise SystemExit(f"Canonical TeX file does not exist for modify mode: {canonical_tex}")

    placeholder_info = ensure_placeholder_macros(canonical_tex)
    scaffold_info = normalize_stock_tau_template_scaffold(canonical_tex)

    procedures_path = outdir / f"{safe_experiment_dirname(experiment)}_procedures.md"
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
        "course": course,
        "experiment": experiment,
        "workspace": str(outdir),
        "existed_before": existed_before,
        "mode": args.mode,
        "canonical_tex": str(canonical_tex),
        "procedures_markdown": str(procedures_path),
        "standard_dirs": [str(outdir / rel) for rel in STANDARD_DIRS],
        "template": args.template,
        "handouts": handouts,
        "reference_reports": reference_reports,
        "data_files": data_files,
        "signatory_files": signatory_files,
        "build_script": str(build_dst),
        "needs_input_macro_ready": True,
        "discovery_cache_input": str(discovery_json_path) if discovery_json_path else None,
        "template_kind": template_info["template_kind"],
        "template_language": template_info["template_language"],
        "template_root": template_info["template_root"],
        "template_entry": template_info["template_entry"],
        "copied_companion_assets": template_info["copied_companion_assets"],
    }
    if "backup_path" in template_info:
        manifest["backup_path"] = template_info["backup_path"]
    manifest.update(placeholder_info)
    manifest.update(scaffold_info)

    manifest_path = outdir / "notes" / "workspace_manifest.json"
    write_json(manifest_path, manifest)

    if args.output_json:
        write_json(Path(args.output_json), manifest)

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
