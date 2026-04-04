from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "build_or_patch_workflow.py"


def load_module(module_path: Path, module_name: str):
    if not module_path.exists():
        raise AssertionError(f"missing module file: {module_path}")

    script_dir = str(module_path.parent)
    inserted = False
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
        inserted = True

    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise AssertionError(f"unable to load module spec: {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if inserted:
            sys.path.pop(0)


class BuildOrPatchWorkflowTests(unittest.TestCase):
    def test_patch_existing_writes_run_local_wolfram_copy_without_mutating_source(self) -> None:
        module = load_module(SCRIPT_PATH, "build_or_patch_workflow_mathematica")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source_path = tmp / "source.wl"
            source_text = 'Print["source workflow"];\n'
            source_path.write_text(source_text, encoding="utf-8")
            run_dir = tmp / "run"
            run_dir.mkdir()
            config = {
                "run_id": "case-demo",
                "workflow": {
                    "mode": "patch-existing",
                    "source_wl": str(source_path),
                    "source_py": "",
                    "template_id": "",
                },
            }
            attempt_context = {
                "case_id": "case-4-f6.3054khz-m5-n5",
                "attempt_number": 2,
                "strategy": "alternate-nearby-root",
            }

            generated_path = module.build_or_patch_workflow(
                config,
                run_dir,
                "mathematica",
                attempt_context=attempt_context,
            )

            self.assertEqual(generated_path, run_dir / "workflow.generated.wl")
            self.assertTrue(generated_path.exists())
            self.assertEqual(source_path.read_text(encoding="utf-8"), source_text)
            generated_text = generated_path.read_text(encoding="utf-8")
            self.assertIn("generated", generated_text.lower())
            self.assertIn("case-demo", generated_text)
            self.assertIn("alternate-nearby-root", generated_text)
            self.assertTrue(str(generated_path).startswith(str(run_dir)))

    def test_patch_existing_writes_run_local_python_copy_without_mutating_source(self) -> None:
        module = load_module(SCRIPT_PATH, "build_or_patch_workflow_python")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source_path = tmp / "source.py"
            source_text = 'print("source workflow")\n'
            source_path.write_text(source_text, encoding="utf-8")
            run_dir = tmp / "run"
            run_dir.mkdir()
            config = {
                "run_id": "case-demo",
                "workflow": {
                    "mode": "patch-existing",
                    "source_wl": "",
                    "source_py": str(source_path),
                    "template_id": "",
                },
            }
            attempt_context = {
                "case_id": "case-4-f6.3054khz-m5-n5",
                "attempt_number": 3,
                "strategy": "python-fallback-wide-scan",
            }

            generated_path = module.build_or_patch_workflow(
                config,
                run_dir,
                "python",
                attempt_context=attempt_context,
            )

            self.assertEqual(generated_path, run_dir / "workflow.generated.py")
            self.assertTrue(generated_path.exists())
            self.assertEqual(source_path.read_text(encoding="utf-8"), source_text)
            generated_text = generated_path.read_text(encoding="utf-8")
            self.assertIn("generated", generated_text.lower())
            self.assertIn("case-demo", generated_text)
            self.assertIn("python-fallback-wide-scan", generated_text)
            self.assertTrue(str(generated_path).startswith(str(run_dir)))


if __name__ == "__main__":
    unittest.main()
