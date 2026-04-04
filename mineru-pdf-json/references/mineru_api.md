# MinerU API Notes

Use this file only when you need the exact MinerU contract while debugging or extending the decoder script.

## Authentication

- Base URL: `https://mineru.net`
- Header: `Authorization: Bearer <token>`
- Use `Content-Type: application/json` for API requests.
- Do not set `Content-Type` for the `PUT` file upload to the returned upload URL.

## Batch Upload Flow

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

- `*_content_list.json`: canonical flat content list; use this as the final saved per-PDF JSON
- `*_model.json`: raw model output
- `*_middle.json` or layout/intermediate output depending on backend/version
- `full.md`: markdown output

## `content_list.json` Fields Used By This Skill

The skill relies on these fields:

- `type`
- `page_idx`
- `bbox`
- `img_path`
- `image_caption`

For image blocks:

```json
{
  "type": "image",
  "img_path": "images/example.jpg",
  "image_caption": ["Fig. 1. Example caption"],
  "image_footnote": [],
  "page_idx": 1
}
```

`img_path` points to a file inside the downloaded archive. Extract that file locally and rename it from the first caption entry after filename sanitization.
