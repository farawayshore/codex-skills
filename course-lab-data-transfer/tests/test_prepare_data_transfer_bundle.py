from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILL_DIR / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from prepare_data_transfer_bundle import main, prepare_bundle, resolve_mineru_markdown


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class PrepareDataTransferBundleTests(unittest.TestCase):
    def test_resolve_mineru_markdown_prefers_matching_pdf_markdown_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            source = root / "sample.pdf"
            source.write_text("placeholder", encoding="utf-8")
            expected = root / "pdf_markdown" / "sample" / "sample.md"
            expected.parent.mkdir(parents=True)
            expected.write_text("# sample", encoding="utf-8")

            resolved = resolve_mineru_markdown(source)

            self.assertEqual(resolved, expected.resolve())

    def test_prepare_bundle_creates_direct_preview_for_csv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            output_dir = root / "review"

            manifest = prepare_bundle(
                source=FIXTURES / "sample_table.csv",
                output_dir=output_dir,
                preview_rows=10,
            )

            self.assertEqual(manifest["source_type"], "csv")
            self.assertTrue(manifest["preview_markdown_path"])
            preview_text = Path(manifest["preview_markdown_path"]).read_text(encoding="utf-8")
            self.assertIn("| sample | angle_deg | retardation_nm |", preview_text)
            self.assertTrue((output_dir / "transfer_bundle.json").exists())

    def test_prepare_bundle_creates_pdf_review_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            source = root / "sample.pdf"
            source.write_text("placeholder pdf bytes", encoding="utf-8")
            mineru_path = root / "pdf_markdown" / "sample" / "sample.md"
            mineru_path.parent.mkdir(parents=True)
            mineru_path.write_text("# sample", encoding="utf-8")

            def fake_run(command: list[str], check: bool, stdout: int, stderr: int) -> subprocess.CompletedProcess[str]:
                if "pdftoppm" in command[0]:
                    prefix = Path(command[-1])
                    prefix.parent.mkdir(parents=True, exist_ok=True)
                    (prefix.parent / "page-1.png").write_bytes(b"png")
                    (prefix.parent / "page-2.png").write_bytes(b"png")
                elif "pdftotext" in command[0]:
                    Path(command[-1]).write_text("page one text", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0)

            with mock.patch("prepare_data_transfer_bundle.shutil.which", side_effect=lambda name: f"/usr/bin/{name}"):
                with mock.patch("prepare_data_transfer_bundle.subprocess.run", side_effect=fake_run):
                    manifest = prepare_bundle(
                        source=source,
                        output_dir=root / "review",
                    )

            self.assertEqual(manifest["source_type"], "pdf")
            self.assertEqual(manifest["pdf_text_method"], "pdftotext")
            self.assertEqual(len(manifest["page_images"]), 2)
            self.assertTrue(manifest["page_images"][0].endswith("page-001.png"))
            self.assertEqual(manifest["mineru_markdown_path"], str(mineru_path.resolve()))

    def test_prepare_bundle_collects_related_picture_results_from_discovery_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            source = root / "sample.pdf"
            source.write_text("placeholder pdf bytes", encoding="utf-8")

            picture_file = root / "matched_phenomenon.jpg"
            picture_file.write_bytes(b"jpg")
            discovery_json = root / "discovery.json"
            discovery_json.write_text(
                json.dumps(
                    {
                        "picture_result_files": [
                            {"path": str(picture_file)}
                        ]
                    }
                ),
                encoding="utf-8",
            )

            def fake_run(command: list[str], check: bool, stdout: int, stderr: int) -> subprocess.CompletedProcess[str]:
                if "pdftoppm" in command[0]:
                    prefix = Path(command[-1])
                    prefix.parent.mkdir(parents=True, exist_ok=True)
                    (prefix.parent / "page-1.png").write_bytes(b"png")
                elif "pdftotext" in command[0]:
                    Path(command[-1]).write_text("page one text", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0)

            with mock.patch("prepare_data_transfer_bundle.shutil.which", side_effect=lambda name: f"/usr/bin/{name}"):
                with mock.patch("prepare_data_transfer_bundle.subprocess.run", side_effect=fake_run):
                    manifest = prepare_bundle(
                        source=source,
                        output_dir=root / "review",
                        discovery_json=discovery_json,
                    )

            self.assertEqual(len(manifest["picture_result_evidence"]), 1)
            evidence = manifest["picture_result_evidence"][0]
            self.assertEqual(evidence["source_path"], str(picture_file.resolve()))
            self.assertEqual(evidence["origin"], "discovery")
            self.assertEqual(evidence["review_image_paths"], [str(picture_file.resolve())])

    def test_cli_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            output_dir = root / "review"

            exit_code = main(
                [
                    "--source",
                    str(FIXTURES / "sample_table.csv"),
                    "--output-dir",
                    str(output_dir),
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads((output_dir / "transfer_bundle.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["source_name"], "sample_table.csv")


if __name__ == "__main__":
    unittest.main()
