import os
import subprocess
import sys
import unittest
from pathlib import Path


SKILLS_ROOT = Path("/root/.codex/skills")
FAMILY_TEST_TARGETS = [
    SKILLS_ROOT / "course-lab-body-scaffold" / "tests",
    SKILLS_ROOT / "course-lab-data-transfer" / "tests",
    SKILLS_ROOT / "course-lab-finalize-qc" / "tests",
    SKILLS_ROOT / "course-lab-report" / "tests",
]


class TestCourseLabFamilyPytestContract(unittest.TestCase):
    def test_multi_package_pytest_run_is_import_isolated(self) -> None:
        env = os.environ.copy()
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                *[str(path) for path in FAMILY_TEST_TARGETS],
                "-q",
            ],
            cwd=SKILLS_ROOT,
            capture_output=True,
            text=True,
            env=env,
        )

        combined_output = "\n".join(
            part for part in (result.stdout, result.stderr) if part
        )

        self.assertEqual(
            result.returncode,
            0,
            f"multi-package pytest run must stay import-isolated\n{combined_output}",
        )
        self.assertNotIn("import file mismatch", combined_output)
        self.assertNotIn("cannot import name", combined_output)


if __name__ == "__main__":
    unittest.main()
