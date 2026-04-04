from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILL_DIR / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_transfer_draft import build_transfer_draft, main


class BuildTransferDraftTests(unittest.TestCase):
    def test_build_transfer_draft_for_pdf_includes_three_way_review_structure(self) -> None:
        manifest = {
            "source_path": "/tmp/sample.pdf",
            "source_name": "sample.pdf",
            "source_type": "pdf",
            "review_dir": "/tmp/review",
            "page_images": [
                "/tmp/review/pages/page-001.png",
                "/tmp/review/pages/page-002.png",
            ],
            "pdf_text_path": "/tmp/review/sample.txt",
            "pdf_text_method": "pdftotext",
            "mineru_markdown_path": "/tmp/pdf_markdown/sample/sample.md",
            "preview_markdown_path": None,
            "picture_result_evidence": [
                {
                    "source_path": "/tmp/picture-results/sample-1.jpg",
                    "origin": "discovery",
                    "review_image_paths": ["/tmp/picture-results/sample-1.jpg"],
                    "notes": [],
                }
            ],
            "notes": [],
        }

        draft = build_transfer_draft(manifest, "crystal_optics")

        self.assertIn("# Crystal Optics Raw-Data Transfer", draft)
        self.assertIn("Read the rendered page images first", draft)
        self.assertIn("## Page 1", draft)
        self.assertIn("## Page 2", draft)
        self.assertIn("MinerU comparison", draft)
        self.assertIn("PDF-to-text comparison", draft)
        self.assertIn("## Picture-Result Cross-Check", draft)
        self.assertIn("Does the transferred phenomenon really appear in this picture?", draft)
        self.assertIn("Please proofread this transferred Markdown", draft)

    def test_cli_writes_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            manifest_path = root / "transfer_bundle.json"
            output_markdown = root / "transfer.md"
            manifest_path.write_text(
                json.dumps(
                    {
                        "source_path": "/tmp/sample.csv",
                        "source_name": "sample.csv",
                        "source_type": "csv",
                        "review_dir": "/tmp/review",
                        "page_images": [],
                        "pdf_text_path": None,
                        "pdf_text_method": None,
                        "mineru_markdown_path": None,
                        "preview_markdown_path": "/tmp/review/sample_preview.md",
                        "notes": [],
                    }
                ),
                encoding="utf-8",
            )

            exit_code = main(
                [
                    "--bundle-json",
                    str(manifest_path),
                    "--experiment-safe-name",
                    "mechanics_combined",
                    "--output-markdown",
                    str(output_markdown),
                ]
            )

            self.assertEqual(exit_code, 0)
            text = output_markdown.read_text(encoding="utf-8")
            self.assertIn("# Mechanics Combined Raw-Data Transfer", text)
            self.assertIn("## Direct Transfer", text)


if __name__ == "__main__":
    unittest.main()
