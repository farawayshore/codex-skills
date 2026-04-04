from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "build_plot_job.py"
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "sample_series.csv"


def load_module():
    assert SCRIPT_PATH.exists(), f"missing script: {SCRIPT_PATH}"
    spec = importlib.util.spec_from_file_location("course_lab_plotting_build_plot_job", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BuildPlotJobTests(unittest.TestCase):
    def test_serial_id_takes_priority_for_output_stem(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            job = module.build_plot_job(
                source_path=FIXTURE_PATH,
                x_field="x",
                y_field="y",
                output_root=Path(tmpdir),
                plot_id="plot-01",
                parameter_values={"f": "6.3054kHz", "m": "5", "n": "5"},
            )

        self.assertEqual(job["output_stem"], "plot-01")
        self.assertTrue(str(job["output_png"]).endswith("plot-01.png"))

    def test_parameter_identity_becomes_fallback_stem(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            job = module.build_plot_job(
                source_path=FIXTURE_PATH,
                x_field="x",
                y_field="y",
                output_root=Path(tmpdir),
                parameter_values={"f": "6.3054kHz", "m": "5", "n": "5"},
            )

        self.assertEqual(job["output_stem"], "f6.3054kHz-m5-n5")
        self.assertTrue(str(job["output_png"]).endswith("f6.3054kHz-m5-n5.png"))


if __name__ == "__main__":
    unittest.main()
