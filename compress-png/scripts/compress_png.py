#!/usr/bin/env python3
"""
Audit and compress PNG files while keeping PNG output.

The default mode writes sibling files with a "-compressed" suffix so callers can
compare the result before replacing originals. Use --in-place to replace files.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    from PIL import Image
except ImportError:  # pragma: no cover - dependency check at runtime
    Image = None

if Image is not None:  # pragma: no branch - compatibility shim
    try:
        RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
    except AttributeError:  # pragma: no cover - older Pillow
        RESAMPLE_LANCZOS = Image.LANCZOS


@dataclass
class Result:
    source: Path
    destination: Path
    original_size: int
    new_size: int | None
    status: str
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit or compress PNG files by quantizing colors and optionally resizing.",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="PNG files or directories to scan recursively.",
    )
    parser.add_argument(
        "--audit-only",
        action="store_true",
        help="List matching PNG files without writing outputs.",
    )
    parser.add_argument(
        "--min-size-mb",
        type=float,
        default=0.0,
        help="Only process files at or above this size in MiB.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=0,
        help="When auditing, only show the largest N matches.",
    )
    parser.add_argument(
        "--colors",
        type=int,
        default=256,
        help="Target palette size from 2 to 256. Default: 256.",
    )
    parser.add_argument(
        "--max-dimension",
        type=int,
        default=0,
        help="Resize so the longer edge is at most this many pixels.",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Replace the original file when compression succeeds.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Write outputs under this directory while preserving input-relative paths.",
    )
    parser.add_argument(
        "--suffix",
        default="-compressed",
        help="Suffix to add before .png when not using --in-place or --output-dir.",
    )
    parser.add_argument(
        "--backend",
        choices=("auto", "imagemagick", "pillow"),
        default="auto",
        help="Compression backend. Default: auto.",
    )
    parser.add_argument(
        "--keep-larger",
        action="store_true",
        help="Keep outputs even if they are not smaller than the source.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files in copy mode.",
    )
    args = parser.parse_args()

    if not 2 <= args.colors <= 256:
        parser.error("--colors must be between 2 and 256.")
    if args.max_dimension < 0:
        parser.error("--max-dimension must be positive.")
    if args.min_size_mb < 0:
        parser.error("--min-size-mb must be non-negative.")
    if args.top < 0:
        parser.error("--top must be non-negative.")
    if args.in_place and args.output_dir:
        parser.error("--in-place and --output-dir cannot be used together.")

    return args


def iter_png_files(raw_paths: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()

    for raw_path in raw_paths:
        path = Path(raw_path).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")

        if path.is_file():
            candidates = [path]
        else:
            candidates = [child for child in path.rglob("*") if child.is_file()]

        for candidate in candidates:
            if candidate.suffix.lower() != ".png":
                continue
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(resolved)

    return sorted(files)


def choose_backend(name: str) -> tuple[str, list[str]]:
    if name in {"auto", "imagemagick"}:
        magick = shutil.which("magick")
        if magick:
            return "imagemagick", [magick]
        convert = shutil.which("convert")
        if convert:
            return "imagemagick", [convert]
        if name == "imagemagick":
            raise RuntimeError("ImageMagick was requested but neither 'magick' nor 'convert' was found.")

    if name in {"auto", "pillow"} and Image is not None:
        return "pillow", []

    raise RuntimeError("No supported PNG compression backend is available. Install ImageMagick or Pillow.")


def relative_output_path(source: Path, output_dir: Path, roots: list[Path]) -> Path:
    source = source.resolve()
    output_dir = output_dir.expanduser().resolve()

    for root in roots:
        root = root.expanduser().resolve()
        if root.is_file() and source == root:
            return output_dir / source.name
        if root.is_dir() and source.is_relative_to(root):
            return output_dir / source.relative_to(root)

    return output_dir / source.name


def destination_for(source: Path, args: argparse.Namespace, roots: list[Path]) -> Path:
    if args.in_place:
        return source
    if args.output_dir:
        return relative_output_path(source, args.output_dir, roots)
    return source.with_name(f"{source.stem}{args.suffix}{source.suffix}")


def format_mib(size_bytes: int) -> str:
    return f"{size_bytes / (1024 * 1024):.2f} MiB"


def image_dimensions(path: Path) -> str:
    if Image is None:
        return "?"
    with Image.open(path) as image:
        width, height = image.size
    return f"{width}x{height}"


def compress_with_imagemagick(command_prefix: list[str], source: Path, destination: Path, args: argparse.Namespace) -> None:
    command = list(command_prefix)
    command.append(str(source))
    command.extend(["-strip"])
    if args.max_dimension:
        command.extend(["-resize", f"{args.max_dimension}x{args.max_dimension}>"])
    command.extend(
        [
            "-dither",
            "FloydSteinberg",
            "-colors",
            str(args.colors),
            "-define",
            "png:compression-level=9",
            "-define",
            "png:compression-filter=5",
            f"PNG8:{destination}",
        ]
    )
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)


def compress_with_pillow(source: Path, destination: Path, args: argparse.Namespace) -> None:
    if Image is None:
        raise RuntimeError("Pillow is not installed.")

    with Image.open(source) as image:
        if args.max_dimension:
            image.thumbnail((args.max_dimension, args.max_dimension), RESAMPLE_LANCZOS)

        bands = image.getbands()
        if "A" in bands:
            working = image.convert("RGBA")
            quantized = working.quantize(
                colors=args.colors,
                method=Image.Quantize.FASTOCTREE,
                dither=Image.Dither.FLOYDSTEINBERG,
            )
        else:
            working = image.convert("RGB")
            quantized = working.quantize(
                colors=args.colors,
                method=Image.Quantize.MEDIANCUT,
                dither=Image.Dither.FLOYDSTEINBERG,
            )

        quantized.save(destination, optimize=True)


def compress_one(
    source: Path,
    destination: Path,
    args: argparse.Namespace,
    backend_name: str,
    backend_command: list[str],
) -> Result:
    original_size = source.stat().st_size
    destination.parent.mkdir(parents=True, exist_ok=True)

    if not args.in_place and destination.exists() and not args.overwrite:
        return Result(source, destination, original_size, None, "skipped", "output exists")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir=destination.parent) as tmp_file:
        temp_output = Path(tmp_file.name)

    try:
        if backend_name == "imagemagick":
            compress_with_imagemagick(backend_command, source, temp_output, args)
        else:
            compress_with_pillow(source, temp_output, args)

        new_size = temp_output.stat().st_size
        if new_size >= original_size and not args.keep_larger:
            temp_output.unlink(missing_ok=True)
            return Result(source, destination, original_size, new_size, "skipped", "not smaller")

        if args.in_place:
            temp_output.replace(source)
            return Result(source, source, original_size, new_size, "replaced", backend_name)

        temp_output.replace(destination)
        return Result(source, destination, original_size, new_size, "written", backend_name)
    except subprocess.CalledProcessError as exc:
        temp_output.unlink(missing_ok=True)
        message = exc.stderr.strip() if exc.stderr else str(exc)
        return Result(source, destination, original_size, None, "error", message)
    except Exception as exc:  # pragma: no cover - runtime safety
        temp_output.unlink(missing_ok=True)
        return Result(source, destination, original_size, None, "error", str(exc))


def print_audit(files: list[Path], top: int) -> None:
    rows = sorted(((path.stat().st_size, path) for path in files), reverse=True)
    total_all = sum(size for size, _ in rows)
    if top:
        rows = rows[:top]

    total_shown = 0
    for size, path in rows:
        total_shown += size
        print(f"{format_mib(size):>10}  {image_dimensions(path):>12}  {path}")

    print(f"\nMatched files: {len(files)}")
    print(f"Files shown: {len(rows)}")
    print(f"Total matched size: {format_mib(total_all)}")
    print(f"Total shown size: {format_mib(total_shown)}")


def main() -> int:
    try:
        args = parse_args()
        roots = [Path(raw).expanduser() for raw in args.paths]
        files = iter_png_files(args.paths)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    min_bytes = int(args.min_size_mb * 1024 * 1024)
    eligible = [path for path in files if path.stat().st_size >= min_bytes]

    if args.audit_only:
        print_audit(eligible, args.top)
        return 0

    try:
        backend_name, backend_command = choose_backend(args.backend)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Using backend: {backend_name}")
    print(f"Eligible files: {len(eligible)}")

    results: list[Result] = []
    for source in eligible:
        destination = destination_for(source, args, roots)
        result = compress_one(source, destination, args, backend_name, backend_command)
        results.append(result)

        if result.new_size is None:
            print(f"[{result.status}] {source} ({result.message})")
            continue

        if result.status == "skipped":
            print(
                f"[skipped] {source} | "
                f"{format_mib(result.original_size)} -> {format_mib(result.new_size)} "
                f"({result.message})"
            )
            continue

        delta = result.original_size - result.new_size
        delta_pct = (delta / result.original_size) * 100 if result.original_size else 0.0
        print(
            f"[{result.status}] {source} -> {result.destination} | "
            f"{format_mib(result.original_size)} -> {format_mib(result.new_size)} "
            f"({delta_pct:.1f}% smaller)"
        )

    written = sum(1 for result in results if result.status in {"written", "replaced"})
    skipped = sum(1 for result in results if result.status == "skipped")
    errored = sum(1 for result in results if result.status == "error")
    successful = [result for result in results if result.status in {"written", "replaced"} and result.new_size is not None]
    before = sum(result.original_size for result in successful)
    after = sum(result.new_size or 0 for result in successful)

    print("\nSummary")
    print(f"written/replaced: {written}")
    print(f"skipped: {skipped}")
    print(f"errors: {errored}")
    if after:
        print(f"aggregate size: {format_mib(before)} -> {format_mib(after)}")

    return 1 if errored else 0


if __name__ == "__main__":
    sys.exit(main())
