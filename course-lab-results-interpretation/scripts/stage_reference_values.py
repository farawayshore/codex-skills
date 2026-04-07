from __future__ import annotations

import argparse
import re
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import requests

from common import read_json, resolve_handout_sections, write_json, write_text


RESULT_LINK_RE = re.compile(
    r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
SNIPPET_RE = re.compile(
    r'<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(?P<snippet>.*?)</a>|'
    r'<div[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(?P<divsnippet>.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")
DUCKDUCKGO_HTML_URL = "https://html.duckduckgo.com/html/"
DEFAULT_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) CodexReferenceHelper/1.0"


def strip_tags(text: str) -> str:
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", unescape(text or ""))).strip()


def parse_duckduckgo_html(html: str, *, max_results: int) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    snippets = [
        strip_tags(match.group("snippet") or match.group("divsnippet") or "")
        for match in SNIPPET_RE.finditer(html)
    ]
    for index, match in enumerate(RESULT_LINK_RE.finditer(html)):
        href = unescape(match.group("href") or "").strip()
        title = strip_tags(match.group("title") or "")
        if not href or not title:
            continue
        if href.startswith("//"):
            href = f"https:{href}"
        duck_target = re.search(r"[?&]uddg=([^&]+)", href)
        if duck_target:
            href = unquote(duck_target.group(1))
        snippet = snippets[index] if index < len(snippets) else ""
        results.append({"url": href, "title": title, "snippet": snippet})
        if len(results) >= max_results:
            break
    return results


def live_search(query: str, *, max_results: int, timeout: float) -> list[dict[str, str]]:
    response = requests.get(
        DUCKDUCKGO_HTML_URL,
        params={"q": query},
        headers={"User-Agent": DEFAULT_USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    return parse_duckduckgo_html(response.text, max_results=max_results)


def fetch_page_text(url: str, *, timeout: float) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": DEFAULT_USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.text


def load_payload(path_value: str | None) -> dict[str, Any] | None:
    if not path_value:
        return None
    path = Path(path_value)
    if not path.exists():
        return None
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected JSON object at {path}")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--handout-sections-markdown")
    parser.add_argument("--handout-sections-json")
    parser.add_argument("--processed-data-json", required=True)
    parser.add_argument("--seed-references-json")
    parser.add_argument("--search-spec-json")
    parser.add_argument("--search-snapshot-json")
    parser.add_argument("--page-snapshot-json")
    parser.add_argument("--approved-literature-json")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-unresolved", required=True)
    parser.add_argument("--max-search-results", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=15.0)
    return parser.parse_args()


def build_inventory(processed_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    inventory: dict[str, dict[str, Any]] = {}
    for entry in processed_payload.get("results", []):
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not name:
            continue
        inventory[str(name)] = entry
    return inventory


def merge_requirements(
    seed_payload: dict[str, Any] | None,
    search_spec_payload: dict[str, Any] | None,
) -> dict[str, list[str]]:
    required: list[str] = []
    optional: list[str] = []
    for payload in [seed_payload, search_spec_payload]:
        if not isinstance(payload, dict):
            continue
        requirements = payload.get("comparison_requirements", {})
        if not isinstance(requirements, dict):
            continue
        for key, target in [("required_bases", required), ("optional_bases", optional)]:
            for value in requirements.get(key, []):
                if isinstance(value, str) and value and value not in target:
                    target.append(value)
    return {"required_bases": required, "optional_bases": optional}


def build_target_specs(
    inventory: dict[str, dict[str, Any]],
    search_spec_payload: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if isinstance(search_spec_payload, dict):
        targets = search_spec_payload.get("targets", [])
        if isinstance(targets, list) and targets:
            return [target for target in targets if isinstance(target, dict) and target.get("name")]

    specs: list[dict[str, Any]] = []
    for name, entry in inventory.items():
        label = str(entry.get("label") or name)
        unit = entry.get("unit")
        specs.append(
            {
                "name": name,
                "query": f"{label} {unit or ''} reference value physics".strip(),
                "comparison_basis": "internet_reference",
                "label": f"Internet reference for {label}",
                "unit": unit,
            }
        )
    return specs


def get_search_results(
    *,
    query: str,
    search_snapshot_payload: dict[str, Any] | None,
    max_results: int,
    timeout: float,
) -> list[dict[str, str]]:
    if isinstance(search_snapshot_payload, dict):
        query_map = search_snapshot_payload.get("queries", {})
        if isinstance(query_map, dict):
            snapshot_results = query_map.get(query)
            if isinstance(snapshot_results, list):
                return [
                    result
                    for result in snapshot_results
                    if isinstance(result, dict) and result.get("url")
                ]
    return live_search(query, max_results=max_results, timeout=timeout)


def get_page_content(
    *,
    url: str,
    page_snapshot_payload: dict[str, Any] | None,
    timeout: float,
) -> str:
    if isinstance(page_snapshot_payload, dict):
        page_map = page_snapshot_payload.get("pages", {})
        if isinstance(page_map, dict):
            snapshot_text = page_map.get(url)
            if isinstance(snapshot_text, str):
                return snapshot_text
    return fetch_page_text(url, timeout=timeout)


def try_extract_value(text: str, spec: dict[str, Any]) -> float | None:
    regex = spec.get("value_regex")
    if isinstance(regex, str) and regex.strip():
        match = re.search(regex, text, re.IGNORECASE)
        if not match:
            return None
        try:
            value = float(match.group(1))
        except (ValueError, TypeError):
            return None
        scale = spec.get("unit_scale", 1.0)
        if isinstance(scale, (int, float)):
            value *= float(scale)
        return value

    match = re.search(r"([-+]?\d+(?:\.\d+)?)", text)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def stage_internet_reference(
    *,
    spec: dict[str, Any],
    search_snapshot_payload: dict[str, Any] | None,
    page_snapshot_payload: dict[str, Any] | None,
    max_results: int,
    timeout: float,
) -> dict[str, Any] | None:
    query = str(spec.get("query") or "").strip()
    if not query:
        return None

    try:
        results = get_search_results(
            query=query,
            search_snapshot_payload=search_snapshot_payload,
            max_results=max_results,
            timeout=timeout,
        )
    except requests.RequestException:
        return None
    for result in results:
        title = str(result.get("title") or "")
        snippet = str(result.get("snippet") or "")
        url = str(result.get("url") or "")
        page_text = ""
        if url:
            try:
                page_text = get_page_content(
                    url=url,
                    page_snapshot_payload=page_snapshot_payload,
                    timeout=timeout,
                )
            except requests.RequestException:
                page_text = ""
        combined_text = "\n".join(part for part in [title, snippet, page_text] if part)
        value = try_extract_value(combined_text, spec)
        if value is None:
            continue
        return {
            "name": spec["name"],
            "label": spec.get("label") or title or f"Internet reference for {spec['name']}",
            "value": value,
            "unit": spec.get("unit"),
            "comparison_basis": spec.get("comparison_basis", "internet_reference"),
            "source": url or query,
        }
    return None


def unique_references(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        key = (
            str(entry.get("name") or ""),
            str(entry.get("comparison_basis") or ""),
            str(entry.get("source") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)
    return unique


def merge_approved_literature_entries(
    references: list[dict[str, Any]],
    approved_payload: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not isinstance(approved_payload, dict):
        return references

    approved_results = approved_payload.get("approved_results", [])
    if not isinstance(approved_results, list):
        return references

    merged = list(references)
    for entry in approved_results:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("comparison_basis") or "").strip() != "literature_report":
            continue
        if str(entry.get("confirmation_state") or "approved").strip() != "approved":
            continue
        if not str(entry.get("name") or "").strip():
            continue

        promoted = {
            "name": entry["name"],
            "comparison_basis": "literature_report",
            "lane": "literature_report_vs_data",
            "source": entry.get("source"),
        }
        for key in [
            "title",
            "authors",
            "year",
            "match_reason",
            "value",
            "unit",
            "qualitative_finding",
            "label",
        ]:
            if key in entry:
                promoted[key] = entry[key]
        merged.append(promoted)

    return merged


def main() -> int:
    args = parse_args()

    resolve_handout_sections(
        args.handout_sections_markdown,
        args.handout_sections_json,
    )

    processed_payload = read_json(Path(args.processed_data_json))
    if not isinstance(processed_payload, dict):
        raise SystemExit(f"Expected JSON object at {args.processed_data_json}")
    inventory = build_inventory(processed_payload)

    seed_payload = load_payload(args.seed_references_json)
    search_spec_payload = load_payload(args.search_spec_json)
    search_snapshot_payload = load_payload(args.search_snapshot_json)
    page_snapshot_payload = load_payload(args.page_snapshot_json)
    approved_literature_payload = load_payload(args.approved_literature_json)

    comparison_requirements = merge_requirements(seed_payload, search_spec_payload)
    references: list[dict[str, Any]] = []
    if isinstance(seed_payload, dict):
        seed_entries = seed_payload.get("references", [])
        if isinstance(seed_entries, list):
            references.extend(entry for entry in seed_entries if isinstance(entry, dict))

    unresolved: list[str] = []
    target_specs = build_target_specs(inventory, search_spec_payload)
    for spec in target_specs:
        name = str(spec.get("name") or "")
        if name not in inventory:
            unresolved.append(f"Search target {name} is not present in processed-data results")
            continue
        staged_entry = stage_internet_reference(
            spec=spec,
            search_snapshot_payload=search_snapshot_payload,
            page_snapshot_payload=page_snapshot_payload,
            max_results=args.max_search_results,
            timeout=args.timeout,
        )
        if staged_entry is not None:
            references.append(staged_entry)
        elif str(spec.get("comparison_basis") or "internet_reference") in comparison_requirements["required_bases"]:
            unresolved.append(f"Missing required internet reference comparison for {name}")

    references = merge_approved_literature_entries(references, approved_literature_payload)
    references = unique_references(references)

    bases_by_name: dict[str, set[str]] = {}
    for entry in references:
        name = str(entry.get("name") or "")
        basis = str(entry.get("comparison_basis") or "")
        if not name or not basis:
            continue
        bases_by_name.setdefault(name, set()).add(basis)

    for name in inventory:
        available_bases = bases_by_name.get(name, set())
        for basis in comparison_requirements["required_bases"]:
            if basis not in available_bases:
                message = f"Missing required {basis.replace('_', ' ')} comparison for {name}"
                if message not in unresolved:
                    unresolved.append(message)

    payload = {
        "comparison_requirements": comparison_requirements,
        "references": references,
    }
    write_json(Path(args.output_json), payload)
    if unresolved:
        write_text(Path(args.output_unresolved), "\n".join(f"- {entry}" for entry in unresolved) + "\n")
    else:
        write_text(Path(args.output_unresolved), "None.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
