from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
BUILD_JOB_PATH = SKILL_DIR / "scripts" / "build_plot_job.py"
RENDER_PATH = SKILL_DIR / "scripts" / "render_plot.py"
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "sample_series.csv"


def load_module(module_name: str, script_path: Path):
    assert script_path.exists(), f"missing script: {script_path}"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RenderPlotTests(unittest.TestCase):
    def test_render_creates_png_and_manifest(self) -> None:
        build_module = load_module("course_lab_plotting_build_plot_job", BUILD_JOB_PATH)
        render_module = load_module("course_lab_plotting_render_plot", RENDER_PATH)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir)
            job = build_module.build_plot_job(
                source_path=FIXTURE_PATH,
                x_field="x",
                y_field="y",
                output_root=output_root,
                plot_id="plot-01",
            )

            result = render_module.render_plot_job(job)

            image_path = Path(result["output_png"])
            manifest_path = output_root / "plot_manifest.json"

            self.assertTrue(image_path.exists())
            self.assertTrue(manifest_path.exists())

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "ok")
            self.assertEqual(manifest["renderer"], "matplotlib")
            kinds = {item["kind"] for item in manifest["annotations"]}
            self.assertIn("max", kinds)
            self.assertIn("zero", kinds)

    def test_render_writes_unresolved_output_for_missing_column(self) -> None:
        build_module = load_module("course_lab_plotting_build_plot_job", BUILD_JOB_PATH)
        render_module = load_module("course_lab_plotting_render_plot", RENDER_PATH)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir)
            job = build_module.build_plot_job(
                source_path=FIXTURE_PATH,
                x_field="x",
                y_field="missing",
                output_root=output_root,
                plot_id="plot-01",
            )

            result = render_module.render_plot_job(job)

            unresolved_path = output_root / "plot_unresolved.md"

            self.assertEqual(result["status"], "unresolved")
            self.assertTrue(unresolved_path.exists())
            self.assertIn("missing", unresolved_path.read_text(encoding="utf-8").lower())


if __name__ == "__main__":
    unittest.main()
