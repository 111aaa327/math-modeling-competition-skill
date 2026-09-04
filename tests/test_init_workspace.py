from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "init_competition_workspace.py"


class InitWorkspaceTests(unittest.TestCase):
    def test_initializes_contract_files_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            first = subprocess.run(
                [sys.executable, str(SCRIPT), "--path", str(root), "--competition", "Test Cup"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            for name in (
                "STATUS.md",
                "PLAN.md",
                "TODO.md",
                "HANDOFFS.md",
                "RESULT_REGISTRY.json",
                "SUBMISSION_MANIFEST.csv",
            ):
                self.assertTrue((root / name).is_file(), name)
            self.assertEqual(json.loads((root / "RESULT_REGISTRY.json").read_text(encoding="utf-8"))["results"], [])
            self.assertTrue((root / "07_review").is_dir())
            self.assertTrue((root / "08_external_skill_review").is_dir())

            second = subprocess.run(
                [sys.executable, str(SCRIPT), "--path", str(root)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("not empty", second.stderr + second.stdout)


if __name__ == "__main__":
    unittest.main()




