from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path("/root/.codex/skills/course-lab-discussion-ideas")
SCRIPT_DIR = SKILL_DIR / "scripts"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class MergeIdeaMemoryTests(unittest.TestCase):
    def run_merge(
        self,
        *,
        existing_payload: dict[str, object] | None = None,
        new_payload: dict[str, object] | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], Path]:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        memory_dir = root / "experiment_discussion_ideas" / "fixture_experiment"
        new_ideas_json = root / "new_discussion_ideas.json"

        if existing_payload is not None:
            write_json(memory_dir / "idea_memory.json", existing_payload)

        write_json(
            new_ideas_json,
            new_payload
            or {
                "discussion_ideas": [
                    {
                        "idea_id": "wave-speed-comparison",
                        "title": "Wave-speed comparison",
                        "reuse_status": "new",
                        "reference_report_support": ["Reference Report A"],
                        "outside_lookup_summary": "Targeted lookup supports a damping-sensitive comparison.",
                    }
                ]
            },
        )

        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_DIR / "merge_idea_memory.py"),
                "--memory-dir",
                str(memory_dir),
                "--new-ideas-json",
                str(new_ideas_json),
            ],
            capture_output=True,
            text=True,
        )
        return completed, memory_dir

    def test_merge_creates_memory_files_when_absent(self) -> None:
        completed, memory_dir = self.run_merge()

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue((memory_dir / "idea_memory.json").exists())
        self.assertTrue((memory_dir / "idea_notes.md").exists())

        payload = json.loads((memory_dir / "idea_memory.json").read_text(encoding="utf-8"))
        self.assertEqual(len(payload["discussion_ideas"]), 1)

    def test_merge_deduplicates_repeated_ideas_by_stable_identifier(self) -> None:
        completed, memory_dir = self.run_merge(
            existing_payload={
                "discussion_ideas": [
                    {
                        "idea_id": "wave-speed-comparison",
                        "title": "Wave-speed comparison",
                        "reuse_status": "reused",
                        "reference_report_support": ["Reference Report A"],
                        "outside_lookup_summary": "Older run explored the same wave-speed comparison.",
                    }
                ]
            }
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads((memory_dir / "idea_memory.json").read_text(encoding="utf-8"))
        self.assertEqual(len(payload["discussion_ideas"]), 1)

    def test_merge_preserves_provenance_instead_of_overwriting_it(self) -> None:
        completed, memory_dir = self.run_merge(
            existing_payload={
                "discussion_ideas": [
                    {
                        "idea_id": "wave-speed-comparison",
                        "title": "Wave-speed comparison",
                        "reuse_status": "reused",
                        "reference_report_support": ["Reference Report A"],
                        "outside_lookup_summary": "Older run explored the same wave-speed comparison.",
                    }
                ]
            },
            new_payload={
                "discussion_ideas": [
                    {
                        "idea_id": "wave-speed-comparison",
                        "title": "Wave-speed comparison",
                        "reuse_status": "refined",
                        "reference_report_support": ["Reference Report B"],
                        "outside_lookup_summary": "New targeted lookup added damping-specific support.",
                    }
                ]
            },
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads((memory_dir / "idea_memory.json").read_text(encoding="utf-8"))
        merged = payload["discussion_ideas"][0]
        support = " ".join(merged.get("reference_report_support", []))
        provenance = json.dumps(merged, ensure_ascii=False)

        self.assertIn("Reference Report A", support)
        self.assertIn("Reference Report B", support)
        self.assertIn("Older run explored", provenance)
        self.assertIn("damping-specific support", provenance)


if __name__ == "__main__":
    unittest.main()
