from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "manage_author_profile.py"


class ManageAuthorProfileTests(unittest.TestCase):
    def test_profile_is_created_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            profile = Path(temp_name) / "report_author_profile.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--profile",
                    str(profile),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            self.assertTrue(payload["created"])
            self.assertTrue(profile.exists())
            self.assertIn("student.name_zh", payload["missing_fields"])

    def test_profile_updates_are_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            profile = Path(temp_name) / "report_author_profile.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--profile",
                    str(profile),
                    "--set",
                    "student.name_zh=张三",
                    "--set",
                    "student.name_en=San Zhang",
                    "--set",
                    "student.affiliation_zh=中山大学",
                    "--set",
                    "student.affiliation_en=Sun Yat-sen University",
                    "--set",
                    "collaborator.name_zh=李四",
                    "--set",
                    "collaborator.name_en=Si Li",
                    "--set",
                    "collaborator.affiliation_zh=中山大学",
                    "--set",
                    "collaborator.affiliation_en=Sun Yat-sen University",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            self.assertTrue(payload["updated"])
            self.assertEqual(payload["missing_fields"], [])

            stored = json.loads(profile.read_text(encoding="utf-8"))
            self.assertEqual(stored["student"]["name_zh"], "张三")
            self.assertEqual(stored["collaborator"]["name_en"], "Si Li")


if __name__ == "__main__":
    unittest.main()
