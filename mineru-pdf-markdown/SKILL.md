---
name: mineru-pdf-markdown
description: Use when Codex needs Markdown rather than JSON from MinerU, especially for local PDF directories that should become stable per-PDF `.md` artifacts with extracted linked assets, or for one-off small-PDF parsing through MinerU's lightweight Agent API.
---

# MinerU PDF to Markdown

Use this skill when the input is a local directory of PDFs and the goal is to turn each undecoded PDF into a stable, per-PDF Markdown artifact with any linked archive assets extracted alongside it.

Prefer the bundled script over writing one-off MinerU API code. The script is the stable contract for discovery, upload, polling, archive download, Markdown promotion, linked-asset extraction, and final verification.

## Required Environment

- Set `MINERU_API_TOKEN` before running the script, or store the token once in `/root/.codex/skills/mineru-pdf-markdown/.mineru_api_token`.
- The script also accepts the sibling JSON skill's token file at `/root/.codex/skills/mineru-pdf-json/.mineru_api_token` if it already exists.
- Run on one directory at a time; the scan is non-recursive.
- Expect outputs under a sibling directory named `pdf_markdown/`.

## Primary Command

```bash
python3 /root/.codex/skills/mineru-pdf-markdown/scripts/decode_pdfs.py --pdf-dir /path/to/pdfs
```

Useful options:

- `--batch-size 20` by default; maximum `200`
- `--model-version vlm` or `--model-version pipeline`
- `--poll-seconds 10` by default
- `--dry-run` to stop after discovery and `decode_lists.md` generation

## Output Contract

For a PDF directory like `/data/folder1`:

1. Create `/data/folder1/decode_lists.md`.
2. Ensure `/data/folder1/pdf_markdown/` exists.
3. Treat `/data/folder1/pdf_markdown/<stem>/<stem>.md` as the decoded marker.
4. Skip PDFs that already have that marker.
5. For each undecoded PDF, save:
   - Markdown: `/data/folder1/pdf_markdown/<stem>/<stem>.md`
   - Linked assets: `/data/folder1/pdf_markdown/<stem>/...` preserving MinerU's archive-relative paths such as `images/...`
6. If final verification succeeds, delete `decode_lists.md`.
7. If any file fails, keep `decode_lists.md` and surface the error instead of silently continuing.

The canonical Markdown artifact is MinerU's `full.md`. Do not save `*_content_list.json` as the primary result for this skill unless the user explicitly asks for both Markdown and JSON.

## Workflow

1. Run the decoder script.
2. Let it build `decode_lists.md` from PDFs missing the decoded marker.
3. Let it request upload URLs from MinerU, upload the local PDFs, and poll `extract-results/batch`.
4. Let it download each result archive, promote `full.md` to `<stem>.md`, and extract all non-JSON linked assets into the per-PDF output directory.
5. Read `references/mineru_api.md` only when you need the exact endpoint, archive layout, or lightweight-Agent fallback contract.

## Quick Reference

- Want repeatable local outputs for a whole PDF folder: use the bundled script.
- Want no-token parsing for a single small PDF or URL: use the lightweight Agent API in `references/mineru_api.md`.
- Want structured blocks or caption-renamed images instead of Markdown: switch to `$mineru-pdf-json`.
- Unsure whether asset links will survive: keep the default extraction behavior, which preserves MinerU archive-relative paths.

## Failure Handling

- Do not claim success if any pending PDF fails verification.
- Keep `decode_lists.md` on failure so the user can see which PDFs still need work.
- Report concise, actionable failures:
  - upload URL request rejected
  - file upload failed
  - MinerU returned `failed`
  - result archive missing `full.md`
  - saved Markdown is empty or cannot be decoded as UTF-8
  - Markdown references a local asset path that was not extracted

## Common Mistakes

- Do not flatten or rename extracted assets. `full.md` usually references archive-relative paths like `images/...`, so preserve them.
- Do not treat `*_content_list.json` as the final artifact for this skill. That belongs to `$mineru-pdf-json`.
- Do not reach for the lightweight Agent API when processing whole folders. It is single-file and meant for smaller no-token jobs.
- Do not silently skip verification just because `full.md` exists. Confirm the saved Markdown is non-empty and its local links resolve.

## Resources

- `scripts/decode_pdfs.py`: main workflow implementation for batch local PDF to Markdown conversion
- `references/mineru_api.md`: compact endpoint, archive-layout, and lightweight-Agent reference
