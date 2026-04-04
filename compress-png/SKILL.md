---
name: compress-png
description: Compress oversized PNG images by auditing folders, quantizing colors, stripping metadata, and optionally resizing images while keeping PNG output. Use when Codex needs to shrink `.png` screenshots, microscope photos, lab-result figures, or LaTeX report assets, especially for batch folders with many large files or when a user asks to make PNGs smaller without switching to JPEG.
---

# Compress PNG

## Overview

Audit large PNGs and compress them with a reusable script instead of re-deriving one-off shell commands. Prefer this skill for report figures, experiment result folders, and screenshot-heavy assets where PNG is still the right format but the files are too large.

## Workflow

1. Audit the target folder before editing anything. Use `--audit-only` and a size threshold so you only touch the problem files.
2. Start with copy mode, not in-place replacement. The default script behavior writes sibling files with a suffix so you can compare quality first.
3. Use `256` colors first. This usually cuts screenshot-like or microscope-photo PNGs dramatically while keeping the image visually close.
4. Only get more aggressive if needed. Drop to `128` colors or set `--max-dimension` when the first pass is still too large.
5. Replace originals with `--in-place` only after checking a sample of the compressed outputs.

## Quick Start

Audit the largest PNGs in a result folder:

```bash
python3 /root/.codex/skills/compress-png/scripts/compress_png.py \
  AI_works/results/晶体光学性质/picture-results \
  --audit-only \
  --min-size-mb 1 \
  --top 20
```

Write compressed copies next to originals:

```bash
python3 /root/.codex/skills/compress-png/scripts/compress_png.py \
  AI_works/results/晶体光学性质/picture-results \
  --min-size-mb 1 \
  --colors 256
```

Replace the original files after checking quality:

```bash
python3 /root/.codex/skills/compress-png/scripts/compress_png.py \
  AI_works/results/晶体光学性质/picture-results \
  --min-size-mb 1 \
  --colors 256 \
  --in-place
```

Use a more aggressive pass when huge camera PNGs still need work:

```bash
python3 /root/.codex/skills/compress-png/scripts/compress_png.py \
  AI_works/results/晶体光学性质/picture-results/conoscopic-mode \
  --min-size-mb 2 \
  --colors 128 \
  --max-dimension 2400
```

## Script Notes

- The script prefers ImageMagick (`magick` or `convert`) because it is faster on very large images.
- The script falls back to Pillow if ImageMagick is unavailable.
- The script skips outputs that are not actually smaller unless `--keep-larger` is set.
- The default output is a sibling file named like `image-compressed.png`.
- Use `--output-dir DIR` when you want to keep the originals untouched and place all compressed outputs elsewhere.

## Quality Guardrails

- Prefer `256` colors first for lab screenshots, optical patterns, and report figures.
- Lower to `128` colors only when the first pass is still too large or the image is mostly smooth gradients with repeated colors.
- Use `--max-dimension` for oversized camera images. It is often the biggest win when a figure was captured at full sensor resolution but only displayed at report scale.
- Visually inspect a few representative samples before using `--in-place`.
- Do not switch to JPEG unless the user explicitly asks; this skill is for keeping PNG output.

## Files

- `scripts/compress_png.py`: audit and compress one file or whole directory trees
