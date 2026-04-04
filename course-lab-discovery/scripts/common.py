#!/usr/bin/env python3
"""Shared helpers for the course-lab-discovery skill."""

from __future__ import annotations

import json
import os
import re
import unicodedata
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent


def detect_repo_root() -> Path:
    for env_name in ("COURSE_LAB_DISCOVERY_REPO_ROOT", "MODERN_PHYSICS_REPO_ROOT"):
        override = os.environ.get(env_name)
        if not override:
            continue
        candidate = Path(override).expanduser().resolve()
        if (candidate / "AI_works" / "resources").is_dir():
            return candidate

    candidates: list[Path] = []
    cwd = Path.cwd().resolve()
    candidates.append(cwd)
    candidates.extend(cwd.parents)
    candidates.append(SKILL_DIR)
    candidates.extend(SKILL_DIR.parents)
    candidates.append(Path("/root/grassman_projects"))

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "AI_works" / "resources").is_dir():
            return candidate
    return cwd


ROOT = detect_repo_root()
AI_WORKS_ROOT = ROOT / "AI_works"
RESOURCES_ROOT = AI_WORKS_ROOT / "resources"
RESULTS_ROOT = AI_WORKS_ROOT / "results"
HANDOUT_LIBRARY_ROOT = RESOURCES_ROOT / "experiment_handout"
REFERENCE_LIBRARY_ROOT = RESOURCES_ROOT / "lab_report_reference"
DATA_ROOT = RESOURCES_ROOT / "experiment_data"
PIC_RESULT_ROOT = RESOURCES_ROOT / "experiment_pic_results"
SIGNATORY_ROOT = RESOURCES_ROOT / "experiment_signatory"
TEMPLATE_ROOT = RESOURCES_ROOT / "latex_templet"
EXPERIMENT_SIMULATION_ROOT = RESOURCES_ROOT / "experiment_simulation"

STOPWORDS = {
    "and",
    "experiment",
    "experiments",
    "for",
    "lab",
    "modern",
    "of",
    "physics",
    "report",
    "the",
    "实验",
    "实验报告",
}

def char_ngrams(text: str, size: int = 2) -> set[str]:
    normalized = normalize_for_match(text).replace(" ", "")
    if len(normalized) < size:
        return {normalized} if normalized else set()
    return {normalized[idx : idx + size] for idx in range(0, len(normalized) - size + 1)}


@dataclass
class ScoredPath:
    path: str
    score: float
    label: str
    details: list[str]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["score"] = round(self.score, 3)
        return payload


def normalize_for_match(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.lower()
    text = text.replace("_", " ").replace("-", " ")
    text = re.sub(r"[^\w\u4e00-\u9fff]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def match_tokens(text: str) -> list[str]:
    normalized = normalize_for_match(text)
    if not normalized:
        return []
    return [token for token in normalized.split() if token and token not in STOPWORDS]


def score_text(query: str, candidate_texts: Iterable[str]) -> tuple[float, list[str]]:
    normalized_query = normalize_for_match(query)
    query_tokens = set(match_tokens(query))
    best_score = 0.0
    best_details: list[str] = []
    for raw_text in candidate_texts:
        normalized_text = normalize_for_match(raw_text)
        if not normalized_text:
            continue

        score = 0.0
        details: list[str] = []
        if normalized_query and normalized_query == normalized_text:
            score += 120.0
            details.append("exact-match")
        elif normalized_query and normalized_query in normalized_text:
            score += 90.0
            details.append("contains-query")
        elif normalized_query and normalized_text in normalized_query and len(normalized_text) > 4:
            score += 45.0
            details.append("query-contains-candidate")

        candidate_tokens = set(match_tokens(raw_text))
        overlap = query_tokens & candidate_tokens
        if overlap:
            score += 14.0 * len(overlap)
            details.append(f"token-overlap:{','.join(sorted(overlap))}")

        ngram_overlap = char_ngrams(query) & char_ngrams(raw_text)
        if ngram_overlap:
            score += 6.0 * len(ngram_overlap)
            details.append(f"ngram-overlap:{len(ngram_overlap)}")

        ratio = SequenceMatcher(None, normalized_query, normalized_text).ratio()
        if ratio > 0.28:
            score += ratio * 40.0
            details.append(f"ratio:{ratio:.2f}")

        if score > best_score:
            best_score = score
            best_details = details

    return best_score, best_details


def expand_query_variants(query: str) -> list[str]:
    return [query]


def score_query_variants(queries: Iterable[str], candidate_texts: Iterable[str]) -> tuple[float, list[str]]:
    candidate_texts = list(candidate_texts)
    best_score = 0.0
    best_details: list[str] = []
    best_query = ""
    for query in queries:
        score, details = score_text(query, candidate_texts)
        if score > best_score:
            best_score = score
            best_details = details
            best_query = normalize_for_match(query)
    if best_score > 0 and best_query:
        best_details = [f"query:{best_query}"] + best_details
    return best_score, best_details


def iter_files(root: Path, *, suffixes: set[str] | None = None, exclude_parts: set[str] | None = None) -> Iterable[Path]:
    if not root.exists():
        return []
    suffixes = {item.lower() for item in (suffixes or set())}
    exclude_parts = {item.lower() for item in (exclude_parts or set())}
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if exclude_parts and any(part.lower() in exclude_parts for part in path.parts):
            continue
        if suffixes and path.suffix.lower() not in suffixes:
            continue
        files.append(path)
    return files


def read_json(path: Path) -> dict[str, object] | list[object] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def path_match_texts(path: Path, *, library_root: Path | None = None) -> list[str]:
    texts = [path.stem, path.name]
    if library_root is not None:
        try:
            relative = path.resolve().relative_to(library_root.resolve())
        except Exception:
            relative = None
        if relative is not None:
            texts.append(str(relative))
            if len(relative.parts) > 1:
                texts.extend(part for part in relative.parts[1:] if part)
                trimmed_parent = Path(*relative.parts[1:]).parent
                if str(trimmed_parent) != ".":
                    texts.append(str(trimmed_parent))
    else:
        texts.append(str(path.parent))

    deduped: list[str] = []
    seen: set[str] = set()
    for item in texts:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def summarize_result_dir(path: Path) -> dict[str, object]:
    tex_files = sorted(item.name for item in path.glob("*.tex"))
    manifest_path = path / "notes" / "source_manifest.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else None
    details = [path.name]
    if isinstance(manifest, dict):
        topic = manifest.get("topic")
        if isinstance(topic, str) and topic:
            details.append(topic)
        for key in ("copied_handouts", "copied_reference_reports", "copied_resources"):
            values = manifest.get(key)
            if isinstance(values, list):
                details.extend(str(value) for value in values)
    return {
        "path": str(path),
        "label": path.name,
        "tex_files": tex_files,
        "manifest_topic": manifest.get("topic") if isinstance(manifest, dict) else None,
        "manifest_path": str(manifest_path) if manifest_path.exists() else None,
        "match_texts": details,
    }
