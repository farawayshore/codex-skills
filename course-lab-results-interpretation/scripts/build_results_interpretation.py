from __future__ import annotations

import argparse
import re
from pathlib import Path

from common import (
    extract_handout_expectations,
    maybe_read_json,
    read_json,
    resolve_handout_sections,
    write_json,
    write_text,
)


def build_result_inventory(processed_payload: dict) -> list[dict]:
    inventory = []
    for entry in processed_payload.get("results", []):
        inventory.append(
            {
                "name": entry["name"],
                "label": entry.get("label", entry["name"]),
                "value": entry.get("value"),
                "unit": entry.get("unit"),
                "kind": entry.get("kind", "reported"),
                "sources": entry.get("sources", ["processed-data"]),
            }
        )
    return inventory


def build_reference_index(reference_payload: dict | None) -> dict[str, dict]:
    if not reference_payload:
        return {}
    return {
        entry["name"]: entry
        for entry in reference_payload.get("references", [])
        if isinstance(entry, dict) and entry.get("name")
    }


def build_modeling_index(modeling_payload: dict | None) -> dict[str, dict]:
    if not modeling_payload:
        return {}
    return {
        entry["name"]: entry
        for entry in modeling_payload.get("outputs", [])
        if isinstance(entry, dict) and entry.get("name")
    }


def parse_markdown_results(text: str) -> dict[str, dict]:
    in_results = False
    parsed: dict[str, dict] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            in_results = line.lower() == "## results"
            continue
        if not in_results or not line.startswith("- "):
            continue

        body = line[2:]
        if ":" not in body:
            continue
        name, remainder = body.split(":", 1)
        name = name.strip()
        remainder = remainder.strip()
        match = re.match(r"^([-+]?\d+(?:\.\d+)?)\s*(.*)$", remainder)
        if match:
            value = float(match.group(1))
            unit = match.group(2).strip() or None
        else:
            value = remainder
            unit = None
        parsed[name] = {"value": value, "unit": unit, "raw": remainder}
    return parsed


def parse_required_result_families(text: str) -> list[str]:
    in_section = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            in_section = line.lower() == "## course-lab-results-interpretation"
            continue
        if not in_section:
            continue
        if line.lower().startswith("- required result families:"):
            _, value = line.split(":", 1)
            return [part.strip() for part in value.split(",") if part.strip()]
    return []


def enrich_inventory_with_optional_sources(
    inventory: list[dict],
    plots_payload: dict | None,
    modeling_payload: dict | None,
) -> None:
    by_name = {entry["name"]: entry for entry in inventory}

    for plot in (plots_payload or {}).get("plots", []):
        for result_name in plot.get("related_results", []):
            entry = by_name.get(result_name)
            if entry is not None and "plotted" not in entry["sources"]:
                entry["sources"].append("plotted")

    for output in (modeling_payload or {}).get("outputs", []):
        entry = by_name.get(output.get("name"))
        if entry is not None and "modeled" not in entry["sources"]:
            entry["sources"].append("modeled")


def build_comparison_records(
    inventory: list[dict],
    expectations: dict[str, object],
    modeling_index: dict[str, dict],
    reference_index: dict[str, dict],
    unresolved: list[str],
) -> list[dict]:
    records: list[dict] = []
    by_name = {entry["name"]: entry for entry in inventory}

    required_result_families = expectations.get("required_result_families", [])
    if isinstance(required_result_families, list):
        for name in required_result_families:
            if not isinstance(name, str):
                continue
            entry = by_name.get(name)
            if entry is not None:
                records.append(
                    {
                        "lane": "handout_expectation_vs_data",
                        "name": name,
                        "status": "covered",
                        "data_value": entry.get("value"),
                        "data_unit": entry.get("unit"),
                    }
                )
            else:
                records.append(
                    {
                        "lane": "handout_expectation_vs_data",
                        "name": name,
                        "status": "missing",
                    }
                )

    simulation_required = bool(expectations.get("simulation_required"))
    matched_simulation_names: list[str] = []
    if simulation_required:
        for entry in inventory:
            model = modeling_index.get(entry["name"])
            if model is None:
                continue
            matched_simulation_names.append(entry["name"])
            records.append(
                {
                    "lane": "simulation_vs_data",
                    "name": entry["name"],
                    "status": "compared",
                    "data_value": entry.get("value"),
                    "data_unit": entry.get("unit"),
                    "simulation_value": model.get("value"),
                    "simulation_unit": model.get("unit"),
                }
            )
        if not matched_simulation_names:
            target_names = [
                name
                for name in required_result_families
                if isinstance(name, str)
            ] or [entry["name"] for entry in inventory]
            for name in target_names:
                unresolved.append(
                    f"Handout expects simulation comparison for {name} but no modeling result was provided"
                )

    for entry in inventory:
        reference = reference_index.get(entry["name"])
        if reference is None:
            unresolved.append(f"No theory/reference value available for {entry['name']}")
            continue
        records.append(
            {
                "lane": "theory_reference_vs_data",
                "name": entry["name"],
                "status": "compared",
                "data_value": entry.get("value"),
                "data_unit": entry.get("unit"),
                "reference_value": reference.get("value"),
                "reference_unit": reference.get("unit"),
            }
        )

    if simulation_required and expectations.get("compare_simulation_to_theory"):
        for name, model in modeling_index.items():
            reference = reference_index.get(name)
            if reference is None:
                continue
            records.append(
                {
                    "lane": "simulation_vs_theory_reference",
                    "name": name,
                    "status": "compared",
                    "simulation_value": model.get("value"),
                    "simulation_unit": model.get("unit"),
                    "reference_value": reference.get("value"),
                    "reference_unit": reference.get("unit"),
                }
            )

    if simulation_required:
        inventory_names = {entry["name"] for entry in inventory}
        for name in modeling_index:
            if name not in inventory_names:
                unresolved.append(
                    f"Could not align simulation result {name} to any processed-data result"
                )

    return records


def build_interpretation_items(
    inventory: list[dict],
    comparison_records: list[dict],
) -> list[dict]:
    items = []
    comparison_names = {entry.get("name") for entry in comparison_records}
    for entry in inventory:
        item = {
            "name": entry["name"],
            "label": entry.get("label", entry["name"]),
            "summary": f"{entry.get('label', entry['name'])} was reported as {entry.get('value')} {entry.get('unit') or ''}".strip(),
            "evidence_sources": entry.get("sources", []),
        }
        if entry["name"] in comparison_names:
            item["comparison_summary"] = "Explicit comparison records were generated for this result."
        items.append(item)
    return items


def render_markdown(payload: dict) -> str:
    lines = [
        "# Results Interpretation",
        "",
        "## Result Inventory",
    ]
    for entry in payload["result_inventory"]:
        unit_suffix = f" {entry['unit']}" if entry.get("unit") else ""
        lines.append(f"- {entry['label']}: {entry.get('value')}{unit_suffix}")

    lines.extend(["", "## Comparison Records"])
    if payload["comparison_records"]:
        for entry in payload["comparison_records"]:
            lines.append(
                f"- {entry['lane']} / {entry['name']}: {entry['status']}"
            )
    else:
        lines.append("None.")

    lines.extend(["", "## Interpretation Notes"])
    for entry in payload["interpretation_items"]:
        lines.append(f"- {entry['summary']}")

    lines.extend(["", "## Anomalies"])
    if payload["anomalies"]:
        for entry in payload["anomalies"]:
            lines.append(f"- {entry}")
    else:
        lines.append("None.")

    lines.extend(["", "## Completeness Check"])
    if payload["completeness_checks"]:
        for entry in payload["completeness_checks"]:
            lines.append(f"- {entry['name']}: {entry['status']} ({entry['reason']})")
    else:
        lines.append("No explicit completeness expectations were provided.")

    lines.extend(["", "## Unresolved"])
    if payload["unresolved"]:
        for entry in payload["unresolved"]:
            lines.append(f"- {entry}")
    else:
        lines.append("None.")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--handout-sections-markdown")
    parser.add_argument("--handout-sections-json")
    parser.add_argument("--processed-data-json", required=True)
    parser.add_argument("--processed-data-markdown")
    parser.add_argument("--plots-manifest")
    parser.add_argument("--modeling-result")
    parser.add_argument("--references-json")
    parser.add_argument("--run-plan")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-markdown", required=True)
    parser.add_argument("--output-unresolved", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    handout_summary = resolve_handout_sections(
        args.handout_sections_markdown,
        args.handout_sections_json,
    )
    expectations = extract_handout_expectations(handout_summary)
    processed_payload = read_json(Path(args.processed_data_json))
    reference_payload = maybe_read_json(Path(args.references_json)) if args.references_json else None
    plots_payload = maybe_read_json(Path(args.plots_manifest)) if args.plots_manifest else None
    modeling_payload = maybe_read_json(Path(args.modeling_result)) if args.modeling_result else None
    unresolved: list[str] = []

    inventory = build_result_inventory(processed_payload)
    enrich_inventory_with_optional_sources(inventory, plots_payload, modeling_payload)
    reference_index = build_reference_index(reference_payload)
    modeling_index = build_modeling_index(modeling_payload)
    comparison_records = build_comparison_records(
        inventory,
        expectations,
        modeling_index,
        reference_index,
        unresolved,
    )
    interpretation_items = build_interpretation_items(inventory, comparison_records)

    if args.processed_data_markdown:
        markdown_path = Path(args.processed_data_markdown)
        if markdown_path.exists():
            parsed_markdown = parse_markdown_results(markdown_path.read_text(encoding="utf-8"))
            for entry in inventory:
                markdown_entry = parsed_markdown.get(entry["name"])
                if markdown_entry is None:
                    continue
                json_value = entry.get("value")
                markdown_value = markdown_entry.get("value")
                json_unit = (entry.get("unit") or "").strip()
                markdown_unit = (markdown_entry.get("unit") or "").strip()
                if isinstance(json_value, (int, float)) and isinstance(markdown_value, (int, float)):
                    values_match = abs(float(json_value) - float(markdown_value)) < 1e-9
                else:
                    values_match = str(json_value).strip() == str(markdown_value).strip()
                if not values_match or json_unit != markdown_unit:
                    unresolved.append(f"Processed-data JSON/Markdown conflict for {entry['name']}")

    completeness_checks: list[dict] = []
    if args.run_plan:
        run_plan_path = Path(args.run_plan)
        if run_plan_path.exists():
            required_families = parse_required_result_families(run_plan_path.read_text(encoding="utf-8"))
            present_names = {entry["name"] for entry in inventory}
            for name in required_families:
                if name not in present_names:
                    completeness_checks.append(
                        {
                            "name": name,
                            "status": "missing",
                            "reason": "Required by run plan but not present in processed-data results",
                        }
                    )

    payload = {
        "result_inventory": inventory,
        "comparison_records": comparison_records,
        "interpretation_items": interpretation_items,
        "anomalies": [],
        "completeness_checks": completeness_checks,
        "unresolved": unresolved,
    }

    write_json(Path(args.output_json), payload)
    write_text(Path(args.output_markdown), render_markdown(payload))
    if unresolved:
        unresolved_text = "\n".join(f"- {entry}" for entry in unresolved) + "\n"
    else:
        unresolved_text = "None.\n"
    write_text(Path(args.output_unresolved), unresolved_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
