---
name: mineru-pdf-json
description: Convert a directory of local PDF files into per-PDF MinerU `content_list.json` outputs plus extracted caption-named images by using MinerU's official batch upload API flow. Use when Codex needs to batch-upload local PDFs to MinerU, skip already-decoded files, save canonical JSON artifacts under `pdf_decoded/pdf-stem/pdf-stem.json`, and extract image blocks into local files for downstream processing.
---

# MinerU PDF to JSON

Use this skill when the input is a local directory of PDFs and the goal is to turn each undecoded PDF into a stable, per-PDF JSON artifact plus extracted image files.

Prefer the bundled script over writing one-off MinerU API code. The script is the stable contract for discovery, upload, polling, archive download, JSON promotion, image extraction, and final verification.

## Required Environment

- Set `MINERU_API_TOKEN` before running the script, or store the token once in `/root/.codex/skills/mineru-pdf-json/.mineru_api_token`.
- Run on one directory at a time; the scan is non-recursive.
- Expect outputs under a sibling directory named `pdf_decoded/`.

## Primary Command

```bash
python3 /root/.codex/skills/mineru-pdf-json/scripts/decode_pdfs.py --pdf-dir /path/to/pdfs
```

Useful options:

- `--batch-size 20` by default; maximum `200`
- `--model-version vlm` or `--model-version pipeline`
- `--poll-seconds 10` by default
- `--dry-run` to stop after discovery and `decode_lists.md` generation

## Output Contract

For a PDF directory like `/data/folder1`:

1. Create `/data/folder1/decode_lists.md`.
2. Ensure `/data/folder1/pdf_decoded/` exists.
3. Treat `/data/folder1/pdf_decoded/<stem>/<stem>.json` as the decoded marker.
4. Skip PDFs that already have that marker.
5. For each undecoded PDF, save:
   - JSON: `/data/folder1/pdf_decoded/<stem>/<stem>.json`
   - Images: `/data/folder1/pdf_decoded/<stem>/images/<caption-or-fallback>.<ext>`
6. If final verification succeeds, delete `decode_lists.md`.
7. If any file fails, keep `decode_lists.md` and surface the error instead of silently continuing.

The canonical JSON artifact is MinerU's `*_content_list.json`. Do not save `model.json` or `middle.json` as the final per-PDF result unless the user explicitly asks for a different output.

## Workflow

1. Run the decoder script.
2. Let it build `decode_lists.md` from PDFs missing the decoded marker.
3. Let it request upload URLs from MinerU, upload the local PDFs, and poll `extract-results/batch`.
4. Let it download each result archive, promote `*_content_list.json` to `<stem>.json`, and extract image blocks through `img_path`.
5. Read `references/mineru_api.md` only when you need the exact endpoint or output-file mapping.

## Failure Handling

- Do not claim success if any pending PDF fails verification.
- Keep `decode_lists.md` on failure so the user can see which PDFs still need work.
- Report concise, actionable failures:
  - upload URL request rejected
  - file upload failed
  - MinerU returned `failed`
  - result archive missing `*_content_list.json`
  - image block references an archive path that does not exist
  - saved JSON cannot be parsed on the final verification pass

## Resources

- `scripts/decode_pdfs.py`: main workflow implementation
- `references/mineru_api.md`: compact endpoint and output-format reference
