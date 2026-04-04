# MinerU API Notes

Use this file only when you need the exact MinerU contract while debugging or extending the Markdown decoder workflow.

## Authentication

- Standard API base URL: `https://mineru.net`
- Standard API header: `Authorization: Bearer <token>`
- Use `Content-Type: application/json` for API requests.
- Do not set `Content-Type` for the `PUT` file upload to the returned upload URL.

## Standard Batch Upload Flow

### Request upload URLs

- Endpoint: `POST /api/v4/file-urls/batch`
- Minimal request body:

```json
{
  "files": [
    {"name": "demo.pdf", "data_id": "demo.pdf"}
  ],
  "model_version": "vlm"
}
```

- Constraints:
  - no more than 200 files per request
  - upload URLs are valid for 24 hours
  - after upload, MinerU auto-submits parsing tasks

### Poll batch results

- Endpoint: `GET /api/v4/extract-results/batch/{batch_id}`
- Result states:
  - `waiting-file`
  - `pending`
  - `running`
  - `converting`
  - `done`
  - `failed`

On success, each finished file includes `full_zip_url`.

## Output Archive Mapping

For non-HTML files, MinerU's zip archive includes:

- `full.md`: canonical Markdown artifact; save this as the final per-PDF Markdown file
- `*_content_list.json`: structured flat content list; useful only when the caller also wants JSON
- `*_model.json`: raw model output
- `*_middle.json` or other intermediate layout output depending on backend/version
- linked assets such as `images/...`

For this skill, preserve extracted asset paths relative to the Markdown file instead of renaming them. MinerU's Markdown usually references paths like `images/example.jpg`, so changing filenames will break local rendering unless the Markdown is also rewritten.

## Lightweight Agent API

Use this only when the job is a one-off URL or single local file and the user wants the quickest no-token Markdown path.

- URL parse endpoint: `POST /api/v1/agent/parse/url`
- File upload endpoint: `POST /api/v1/agent/parse/file`
- Result endpoint: `GET /api/v1/agent/parse/{task_id}`
- Authentication: none
- Output: `markdown_url` when `state=done`
- Call pattern:
  1. submit URL or request a signed upload URL
  2. upload the file with `PUT` if using file mode
  3. poll the task endpoint until `state=done` or `state=failed`
  4. download `markdown_url`

Published docs describe the lightweight API as a small-document path with a `10MB` file limit and a `20` page limit in the comparison table. A later failure example mentions `50` pages. Treat it as a small-document convenience API and fall back to the standard authenticated API whenever the limit matters.

## Parameters Worth Remembering

- Standard API:
  - `model_version`: `pipeline`, `vlm`, or `MinerU-HTML`
  - `page_ranges`: page selection for the standard API
  - `language`: OCR language hint
- Lightweight Agent API:
  - `page_range`: simple single-range page selection
  - `language`: OCR language hint for PDF parsing
