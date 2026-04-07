from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "render_symbolic_explanation.py"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class RenderSymbolicExplanationTests(unittest.TestCase):
    def build_fixture(self, root: Path) -> dict[str, Path]:
        handout = root / "decoded_handout.md"
        code = root / "analysis" / "process_data.py"
        processed = root / "analysis" / "derived_uncertainty.json"
        output_dir = root / "analysis" / "symbolic_expressing" / "tmp"
        response = output_dir / "wave_speed_symbolic_response.json"

        handout.write_text(
            "# Experiment Handout\n\n"
            "The linear density is $rho = m / L$ and the wave speed is $v = sqrt(T / rho)$.\n",
            encoding="utf-8",
        )
        code.parent.mkdir(parents=True, exist_ok=True)
        code.write_text(
            "rho = m / L\n"
            "wave_speed = sqrt(T / rho)\n",
            encoding="utf-8",
        )
        write_json(
            processed,
            {
                "coverage_k": 2.0,
                "inputs": {
                    "m": {"value": 0.01391, "unit": "kg", "symbol": "m"},
                    "L": {"value": 3.0, "unit": "m", "symbol": "L"},
                    "T": {"value": 4.9, "unit": "N", "symbol": "T"},
                },
                "derived": {
                    "rho": {"label": "linear density", "expression": "m / L", "unit": "kg/m", "value": 0.00464},
                    "wave_speed": {"label": "wave speed", "expression": "sqrt(T / rho)", "unit": "m/s", "value": 32.5},
                },
            },
        )
        return {"handout": handout, "code": code, "processed": processed, "output_dir": output_dir, "response": response}

    def run_renderer(self, fixture: dict[str, Path], result_key: str = "wave_speed") -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--handout",
                str(fixture["handout"]),
                "--calculation-code",
                str(fixture["code"]),
                "--processed-result",
                str(fixture["processed"]),
                "--result-key",
                result_key,
                "--output-dir",
                str(fixture["output_dir"]),
                "--output-response-json",
                str(fixture["response"]),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_cli_writes_response_json_with_temp_tex_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.build_fixture(Path(tmpdir))

            completed = self.run_renderer(fixture)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            response = json.loads(fixture["response"].read_text(encoding="utf-8"))
            self.assertEqual(response["result_key"], "wave_speed")
            self.assertEqual(response["unresolved"], [])
            tex_path = Path(response["tex_path"])
            self.assertTrue(tex_path.exists())
            self.assertTrue(str(tex_path).startswith(str(fixture["output_dir"])))

    def test_cli_renders_handout_code_and_processed_formula_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.build_fixture(Path(tmpdir))

            completed = self.run_renderer(fixture)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            response = json.loads(fixture["response"].read_text(encoding="utf-8"))
            tex = Path(response["tex_path"]).read_text(encoding="utf-8")
            self.assertIn(r"\paragraph{Calculation route for wave speed}", tex)
            self.assertIn("handout", tex.lower())
            self.assertIn("calculation code", tex.lower())
            self.assertIn("rho", tex)
            self.assertIn("sqrt", tex)
            self.assertIn(r"\sqrt{T / rho}", tex)
            self.assertIn(r"wave\_speed", tex)
            self.assertNotIn("Raw source table", tex)

    def test_cli_keeps_untraceable_result_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.build_fixture(Path(tmpdir))

            completed = self.run_renderer(fixture, result_key="missing_result")

            self.assertEqual(completed.returncode, 0, completed.stderr)
            response = json.loads(fixture["response"].read_text(encoding="utf-8"))
            self.assertTrue(response["unresolved"])
            tex = Path(response["tex_path"]).read_text(encoding="utf-8")
            self.assertIn(r"\NeedsInput", tex)
            self.assertIn(r"missing\_result", tex)


if __name__ == "__main__":
    unittest.main()
