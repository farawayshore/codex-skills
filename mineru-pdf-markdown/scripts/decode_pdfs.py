#!/usr/bin/env python3
"""Batch-convert local PDFs into MinerU markdown outputs."""

from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_API_BASE = "https://mineru.net"
UPLOAD_ENDPOINT = "/api/v4/file-urls/batch"
RESULT_ENDPOINT = "/api/v4/extract-results/batch/{batch_id}"
TERMINAL_STATES = {"done", "failed"}
NON_TERMINAL_STATES = {"waiting-file", "pending", "running", "converting"}
DEFAULT_TOKEN_FILE = Path(__file__).resolve().parent.parent / ".mineru_api_token"
LEGACY_TOKEN_FILE = Path(__file__).resolve().parent.parent.parent / "mineru-pdf-json/.mineru_api_token"
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HTML_ASSET_RE = re.compile(r"<(?:img|source|a)\b[^>]+(?:src|href)=[\"']([^\"']+)[\"']", re.IGNORECASE)


class MineruError(RuntimeError):
    """Base exception for MinerU decoding failures."""


class MineruAPIError(MineruError):
    """Raised when the MinerU API returns an error."""


@dataclass
class PdfWorkItem:
    pdf_path: Path

    @property
    def name(self) -> str:
        return self.pdf_path.name

    @property
    def stem(self) -> str:
        return self.pdf_path.stem


@dataclass
class FileResult:
    file_name: str
    state: str
    err_msg: str = ""
    full_zip_url: str = ""
    extract_progress: dict[str, Any] | None = None


@dataclass
class ProcessOutcome:
    work_item: PdfWorkItem
    markdown_path: Path | None = None
    asset_paths: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert local PDFs into per-PDF MinerU markdown outputs.",
    )
    parser.add_argument("--pdf-dir", required=True, help="Directory containing PDFs to decode")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Number of PDFs per MinerU upload batch (default: 20, max: 200)",
    )
    parser.add_argument(
        "--model-version",
        choices=["vlm", "pipeline"],
        default="vlm",
        help="MinerU model version to request (default: vlm)",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=10,
        help="Seconds to wait between batch result polls (default: 10)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only discover pending PDFs and write decode_lists.md",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return run(args)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


def run(args: argparse.Namespace) -> int:
    pdf_dir = Path(args.pdf_dir).expanduser().resolve()
    if not pdf_dir.is_dir():
        print(f"PDF directory not found: {pdf_dir}", file=sys.stderr)
        return 2

    if args.batch_size < 1 or args.batch_size > 200:
        print("--batch-size must be between 1 and 200.", file=sys.stderr)
        return 2
    if args.poll_seconds < 1:
        print("--poll-seconds must be at least 1.", file=sys.stderr)
        return 2

    decode_list_path = pdf_dir / "decode_lists.md"
    decoded_root = pdf_dir / "pdf_markdown"
    decoded_root.mkdir(exist_ok=True)

    work_items = discover_pdfs(pdf_dir)
    pending_items = [item for item in work_items if not decoded_marker_for(decoded_root, item).exists()]
    write_decode_list(decode_list_path, pending_items)

    if not pending_items:
        delete_if_exists(decode_list_path)
        print(f"No pending PDFs found in {pdf_dir}.")
        return 0

    if args.dry_run:
        print(f"Pending PDFs written to {decode_list_path}.")
        return 0

    token = load_token()
    if not token:
        print(
            "MINERU_API_TOKEN is required, or store the token in "
            f"{DEFAULT_TOKEN_FILE} (the script also accepts {LEGACY_TOKEN_FILE} if present).",
            file=sys.stderr,
        )
        return 2

    api_base = os.environ.get("MINERU_API_BASE_URL", DEFAULT_API_BASE).rstrip("/")
    outcomes = {item.name: ProcessOutcome(work_item=item) for item in pending_items}

    for batch in chunked(pending_items, args.batch_size):
        try:
            batch_id, upload_urls = request_upload_urls(api_base, token, batch, args.model_version)
        except MineruError as exc:
            for item in batch:
                outcomes[item.name].add_error(str(exc))
            continue

        print(f"Created MinerU batch {batch_id} for {len(batch)} PDF(s).")
        uploaded_items: list[PdfWorkItem] = []
        for item, upload_url in zip(batch, upload_urls):
            print(f"Uploading {item.name}...")
            try:
                upload_file(upload_url, item.pdf_path)
                uploaded_items.append(item)
            except MineruError as exc:
                outcomes[item.name].add_error(str(exc))

        if not uploaded_items:
            continue

        try:
            print(f"Polling batch {batch_id} until MinerU finishes...")
            batch_results = poll_batch_results(
                api_base=api_base,
                token=token,
                batch_id=batch_id,
                expected_names={item.name for item in uploaded_items},
                poll_seconds=args.poll_seconds,
            )
        except MineruError as exc:
            for item in uploaded_items:
                outcomes[item.name].add_error(str(exc))
            continue

        for item in uploaded_items:
            outcome = outcomes[item.name]
            result = batch_results.get(item.name)
            if result is None:
                outcome.add_error("MinerU did not return a batch result for this file.")
                continue
            if result.state == "failed":
                outcome.add_error(f"MinerU reported failed: {result.err_msg or 'no error message provided'}")
                continue
            if result.state != "done":
                outcome.add_error(f"MinerU returned unexpected terminal state: {result.state}")
                continue
            try:
                markdown_path, asset_paths = download_and_extract_result(
                    work_item=item,
                    full_zip_url=result.full_zip_url,
                    decoded_root=decoded_root,
                )
                outcome.markdown_path = markdown_path
                outcome.asset_paths = asset_paths
            except MineruError as exc:
                outcome.add_error(str(exc))

    verification_errors = verify_pending_outputs(decoded_root, pending_items)
    for file_name, error in verification_errors:
        outcomes[file_name].add_error(error)

    failures = [outcome for outcome in outcomes.values() if outcome.errors]
    if failures:
        print_failure_report(decode_list_path, failures)
        return 1

    delete_if_exists(decode_list_path)
    print(f"Saved {len(pending_items)} Markdown file(s) under {decoded_root}.")
    return 0


def discover_pdfs(pdf_dir: Path) -> list[PdfWorkItem]:
    return [
        PdfWorkItem(entry)
        for entry in sorted(pdf_dir.iterdir(), key=lambda path: path.name.lower())
        if entry.is_file() and entry.suffix.lower() == ".pdf"
    ]


def decoded_marker_for(decoded_root: Path, work_item: PdfWorkItem) -> Path:
    return decoded_root / work_item.stem / f"{work_item.stem}.md"


def write_decode_list(path: Path, pending_items: list[PdfWorkItem]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for item in pending_items:
            handle.write(f"{item.name}\n")


def delete_if_exists(path: Path) -> None:
    if path.exists():
        path.unlink()


def chunked(items: list[PdfWorkItem], size: int) -> list[list[PdfWorkItem]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def load_token() -> str:
    env_token = os.environ.get("MINERU_API_TOKEN", "").strip()
    if env_token:
        return env_token
    for candidate in (DEFAULT_TOKEN_FILE, LEGACY_TOKEN_FILE):
        if candidate.exists():
            token = candidate.read_text(encoding="utf-8").strip()
            if token:
                return token
    return ""


def request_upload_urls(
    api_base: str,
    token: str,
    batch: list[PdfWorkItem],
    model_version: str,
) -> tuple[str, list[str]]:
    payload = {
        "files": [{"name": item.name, "data_id": item.name} for item in batch],
        "model_version": model_version,
    }
    response = api_request(
        method="POST",
        url=f"{api_base}{UPLOAD_ENDPOINT}",
        token=token,
        payload=payload,
    )
    data = response.get("data")
    if not isinstance(data, dict):
        raise MineruAPIError("MinerU upload response did not include a data object.")
    batch_id = data.get("batch_id")
    file_urls = extract_upload_urls(data.get("file_urls") or data.get("files"))
    if not isinstance(batch_id, str) or not batch_id:
        raise MineruAPIError("MinerU upload response did not include batch_id.")
    if len(file_urls) != len(batch):
        raise MineruAPIError("MinerU upload response returned an unexpected number of file URLs.")
    return batch_id, file_urls


def upload_file(upload_url: str, file_path: Path) -> None:
    data = file_path.read_bytes()
    parsed = urllib.parse.urlsplit(upload_url)
    if parsed.scheme not in {"http", "https"}:
        raise MineruAPIError(f"Unsupported upload URL scheme for {file_path.name}: {parsed.scheme}")
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    connection_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    connection = connection_cls(parsed.netloc, timeout=300)
    try:
        connection.putrequest("PUT", path)
        connection.putheader("Content-Length", str(len(data)))
        connection.endheaders()
        connection.send(data)
        response = connection.getresponse()
        details = response.read().decode("utf-8", errors="replace").strip()
        if response.status not in (200, 201):
            suffix = f": {details}" if details else ""
            raise MineruAPIError(
                f"Upload failed for {file_path.name} with status {response.status}{suffix}"
            )
    except OSError as exc:
        raise MineruAPIError(f"Upload failed for {file_path.name}: {exc}") from exc
    finally:
        connection.close()


def poll_batch_results(
    api_base: str,
    token: str,
    batch_id: str,
    expected_names: set[str],
    poll_seconds: int,
) -> dict[str, FileResult]:
    url = f"{api_base}{RESULT_ENDPOINT.format(batch_id=urllib.parse.quote(batch_id, safe=''))}"
    while True:
        response = api_request(method="GET", url=url, token=token)
        data = response.get("data")
        if not isinstance(data, dict):
            raise MineruAPIError("MinerU batch result response did not include a data object.")
        result_rows = data.get("extract_result")
        if not isinstance(result_rows, list):
            raise MineruAPIError("MinerU batch result response did not include extract_result.")
        file_results = parse_file_results(result_rows)
        known_results = {name: result for name, result in file_results.items() if name in expected_names}
        if expected_names.issubset(known_results.keys()) and all(
            result.state in TERMINAL_STATES for result in known_results.values()
        ):
            return known_results
        print(format_progress_line(batch_id, known_results, expected_names))
        time.sleep(poll_seconds)


def parse_file_results(rows: list[Any]) -> dict[str, FileResult]:
    parsed: dict[str, FileResult] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        file_name = row.get("file_name") or row.get("name") or row.get("data_id")
        state = row.get("state")
        if not isinstance(file_name, str) or not isinstance(state, str):
            continue
        parsed[file_name] = FileResult(
            file_name=file_name,
            state=state,
            err_msg=str(row.get("err_msg") or ""),
            full_zip_url=str(row.get("full_zip_url") or ""),
            extract_progress=row.get("extract_progress") if isinstance(row.get("extract_progress"), dict) else None,
        )
    return parsed


def format_progress_line(batch_id: str, results: dict[str, FileResult], expected_names: set[str]) -> str:
    counts: dict[str, int] = {state: 0 for state in sorted(NON_TERMINAL_STATES | TERMINAL_STATES)}
    counts["missing"] = 0
    for name in expected_names:
        result = results.get(name)
        if result is None:
            counts["missing"] += 1
            continue
        counts[result.state] = counts.get(result.state, 0) + 1
    summary = ", ".join(f"{state}={count}" for state, count in counts.items() if count)
    return f"Batch {batch_id} progress: {summary or 'waiting for results'}"


def extract_upload_urls(raw_value: Any) -> list[str]:
    if not isinstance(raw_value, list):
        raise MineruAPIError("MinerU upload response did not include a list of upload URLs.")
    urls: list[str] = []
    for entry in raw_value:
        if isinstance(entry, str) and entry:
            urls.append(entry)
            continue
        if isinstance(entry, dict):
            for key in ("upload_url", "file_url", "url"):
                value = entry.get(key)
                if isinstance(value, str) and value:
                    urls.append(value)
                    break
            else:
                raise MineruAPIError("MinerU upload response included an upload entry without a URL.")
            continue
        raise MineruAPIError("MinerU upload response included an invalid upload URL entry.")
    return urls


def download_and_extract_result(
    work_item: PdfWorkItem,
    full_zip_url: str,
    decoded_root: Path,
) -> tuple[Path, list[Path]]:
    if not full_zip_url:
        raise MineruError("MinerU did not provide full_zip_url for a completed file.")

    target_dir = decoded_root / work_item.stem
    target_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="mineru-pdf-markdown-") as temp_dir:
        archive_path = Path(temp_dir) / f"{work_item.stem}.zip"
        download_file(full_zip_url, archive_path)
        with zipfile.ZipFile(archive_path) as archive:
            markdown_member = select_markdown_member(archive)
            try:
                markdown_text = archive.read(markdown_member).decode("utf-8")
            except UnicodeDecodeError as exc:
                raise MineruError(f"Downloaded full.md for {work_item.name} is not valid UTF-8.") from exc
            output_markdown_path = target_dir / f"{work_item.stem}.md"
            output_markdown_path.write_text(normalize_newlines(markdown_text), encoding="utf-8")
            asset_paths = extract_asset_files(archive, target_dir)
            return output_markdown_path, asset_paths


def download_file(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            with destination.open("wb") as handle:
                shutil.copyfileobj(response, handle)
    except urllib.error.HTTPError as exc:
        details = read_error_body(exc)
        raise MineruError(f"Failed to download MinerU result archive: {exc.code} {details}") from exc
    except urllib.error.URLError as exc:
        raise MineruError(f"Failed to download MinerU result archive: {exc.reason}") from exc


def select_markdown_member(archive: zipfile.ZipFile) -> str:
    candidates = [
        normalize_archive_path(name)
        for name in archive.namelist()
        if normalize_archive_path(name) and Path(normalize_archive_path(name)).name == "full.md"
    ]
    unique_candidates = list(dict.fromkeys(candidates))
    if len(unique_candidates) == 1:
        return unique_candidates[0]
    if not unique_candidates:
        raise MineruError("MinerU result archive did not contain full.md.")
    raise MineruError("MinerU result archive contained multiple full.md files.")


def extract_asset_files(archive: zipfile.ZipFile, target_dir: Path) -> list[Path]:
    extracted: list[Path] = []
    for member in archive.infolist():
        if member.is_dir():
            continue
        normalized = normalize_archive_path(member.filename)
        if not normalized:
            continue
        if Path(normalized).name == "full.md" or Path(normalized).suffix.lower() == ".json":
            continue
        destination = safe_extract_path(target_dir, normalized)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(member) as source, destination.open("wb") as target:
            shutil.copyfileobj(source, target)
        extracted.append(destination)
    return extracted


def safe_extract_path(base_dir: Path, member_name: str) -> Path:
    destination = (base_dir / member_name).resolve()
    base = base_dir.resolve()
    if destination != base and base not in destination.parents:
        raise MineruError(f"Archive member escaped the output directory: {member_name}")
    return destination


def normalize_archive_path(path_value: str) -> str:
    normalized = path_value.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if not normalized:
        return ""
    return normalized


def normalize_newlines(value: str) -> str:
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.endswith("\n"):
        normalized += "\n"
    return normalized


def verify_pending_outputs(
    decoded_root: Path,
    pending_items: list[PdfWorkItem],
) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    for item in pending_items:
        markdown_path = decoded_marker_for(decoded_root, item)
        if not markdown_path.exists():
            errors.append((item.name, "Expected decoded Markdown file is missing after processing."))
            continue
        try:
            markdown_text = markdown_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append((item.name, "Saved Markdown file cannot be decoded as UTF-8 during verification."))
            continue
        if not markdown_text.strip():
            errors.append((item.name, "Saved Markdown file is empty."))
            continue
        missing_paths: list[str] = []
        for rel_path in referenced_local_paths(markdown_text):
            try:
                if not safe_extract_path(markdown_path.parent, rel_path).exists():
                    missing_paths.append(rel_path)
            except MineruError:
                missing_paths.append(rel_path)
        if missing_paths:
            preview = ", ".join(missing_paths[:3])
            suffix = "..." if len(missing_paths) > 3 else ""
            errors.append(
                (
                    item.name,
                    f"Markdown references local asset(s) that were not extracted: {preview}{suffix}",
                )
            )
    return errors


def referenced_local_paths(markdown_text: str) -> list[str]:
    referenced: list[str] = []
    for raw_value in MARKDOWN_LINK_RE.findall(markdown_text):
        cleaned = clean_reference_target(raw_value)
        if cleaned:
            referenced.append(cleaned)
    for raw_value in HTML_ASSET_RE.findall(markdown_text):
        cleaned = clean_reference_target(raw_value)
        if cleaned:
            referenced.append(cleaned)
    return sorted(dict.fromkeys(referenced))


def clean_reference_target(raw_value: str) -> str:
    value = raw_value.strip()
    if value.startswith("<") and value.endswith(">"):
        value = value[1:-1].strip()
    if not value:
        return ""
    if value.startswith(("http://", "https://", "mailto:", "data:", "#")):
        return ""
    if value.startswith("/"):
        return ""
    value = value.split("#", 1)[0].split("?", 1)[0]
    if " " in value:
        value = value.split(" ", 1)[0]
    return value.replace("\\", "/").strip()


def print_failure_report(decode_list_path: Path, failures: list[ProcessOutcome]) -> None:
    print("Decoding completed with errors.", file=sys.stderr)
    print(f"Pending list kept at {decode_list_path}.", file=sys.stderr)
    for outcome in failures:
        print(f"- {outcome.work_item.name}", file=sys.stderr)
        for message in outcome.errors:
            print(f"  error: {message}", file=sys.stderr)
        print(f"  suggestion: {suggest_fix(outcome)}", file=sys.stderr)


def suggest_fix(outcome: ProcessOutcome) -> str:
    combined = " ".join(outcome.errors).lower()
    if "upload" in combined:
        return "Check token validity, network reachability, and retry the failed PDF."
    if "failed" in combined:
        return "Inspect MinerU's reported failure reason and retry later or switch model_version."
    if "archive" in combined or "full.md" in combined:
        return "Inspect the downloaded zip format; MinerU may have changed the output bundle."
    if "asset" in combined or "markdown references" in combined:
        return "Compare the saved Markdown links with the archive contents and preserve relative paths."
    return "Review the saved outputs, fix the reported issue, and rerun the script."


def api_request(
    method: str,
    url: str,
    token: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    data: bytes | None = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response_text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        details = read_error_body(exc)
        raise MineruAPIError(f"MinerU API request failed ({exc.code}): {details}") from exc
    except urllib.error.URLError as exc:
        raise MineruAPIError(f"MinerU API request failed: {exc.reason}") from exc

    try:
        body = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise MineruAPIError("MinerU API response was not valid JSON.") from exc
    if not isinstance(body, dict):
        raise MineruAPIError("MinerU API response was not a JSON object.")
    if body.get("code") != 0:
        trace = body.get("trace_id")
        msg = body.get("msg") or "unknown MinerU API error"
        trace_text = f" trace_id={trace}" if trace else ""
        raise MineruAPIError(f"{msg}.{trace_text}".strip())
    return body


def read_error_body(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8").strip()
    except Exception:  # pragma: no cover - defensive only
        return exc.reason if isinstance(exc.reason, str) else "request failed"
    return body or (exc.reason if isinstance(exc.reason, str) else "request failed")


if __name__ == "__main__":
    sys.exit(main())
