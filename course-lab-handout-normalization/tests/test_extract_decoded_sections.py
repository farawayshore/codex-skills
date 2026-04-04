from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from extract_decoded_sections import build_summary


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class ExtractDecodedSectionsTests(unittest.TestCase):
    def test_sections_are_normalized(self) -> None:
        payload = json.loads((FIXTURES / "sample_mineru.json").read_text(encoding="utf-8"))
        summary = build_summary(payload)
        self.assertEqual(summary["title"], "原子力显微镜的原理与应用")
        self.assertIn("introduction", summary["sections"])
        self.assertIn("objectives", summary["sections"])
        self.assertIn("equipment", summary["sections"])
        self.assertIn("steps", summary["sections"])
        self.assertEqual(len(summary["sections"]["equipment"]["tables"]), 1)
        self.assertEqual(len(summary["sections"]["principle"]["images"]), 1)
        self.assertEqual(summary["sections"]["principle"]["subheadings"][0]["heading"], "4.1 力曲线示意图")
        self.assertEqual(summary["sections"]["principle"]["images"][0]["context_subheading"], "4.1 力曲线示意图")
        self.assertEqual(len(summary["sections"]["thinking_questions"]["list_items"]), 1)


if __name__ == "__main__":
    unittest.main()
