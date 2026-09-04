from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "paper_preflight.py"


class PaperPreflightTests(unittest.TestCase):
    def run_check(self, root: Path, paper: Path, *extra: str) -> tuple[int, dict]:
        process = subprocess.run(
            [sys.executable, str(SCRIPT), "--paper", str(paper), "--project", str(root), *extra],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        return process.returncode, json.loads(process.stdout)

    def assert_code(self, report: dict, code: str) -> None:
        self.assertIn(code, {item["code"] for item in report["findings"]})

    def test_missing_and_empty_papers_are_hard_failures(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code, report = self.run_check(root, root / "missing.md")
            self.assertEqual(code, 1)
            self.assert_code(report, "missing_paper")

            empty = root / "empty.md"
            empty.touch()
            code, report = self.run_check(root, empty)
            self.assertEqual(code, 1)
            self.assert_code(report, "empty_paper")

    def test_valid_markdown_with_existing_image_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "figure.png").write_bytes(b"not-decoded-by-preflight")
            paper = root / "paper.md"
            paper.write_text("# 模型\n\n![敏感性分析](figure.png)\n", encoding="utf-8")
            code, report = self.run_check(root, paper, "--figures-dir", str(root))
            self.assertEqual(code, 0)
            self.assertEqual(report["status"], "PASS")

    def test_placeholder_and_missing_markdown_image_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paper = root / "paper.md"
            paper.write_text("TODO\n\n![结果](missing.png)\n", encoding="utf-8")
            code, report = self.run_check(root, paper)
            self.assertEqual(code, 1)
            self.assert_code(report, "placeholder")
            self.assert_code(report, "missing_image")

    def test_typst_latex_residue_and_caption_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "plot.png").write_bytes(b"asset")
            paper = root / "main.typ"
            paper.write_text('#figure(image("plot.png"))\n$\\frac{a}{b}$\n', encoding="utf-8")
            code, report = self.run_check(root, paper)
            self.assertEqual(code, 1)
            self.assert_code(report, "mixed_syntax")
            self.assert_code(report, "missing_caption")

    def test_latex_missing_image_and_caption_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paper = root / "main.tex"
            paper.write_text(
                "\\begin{figure}\\includegraphics{missing}\\end{figure}",
                encoding="utf-8",
            )
            code, report = self.run_check(root, paper)
            self.assertEqual(code, 1)
            self.assert_code(report, "missing_image")
            self.assert_code(report, "missing_caption")

    def test_docx_body_and_identity_metadata_are_inspected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paper = root / "paper.docx"
            with zipfile.ZipFile(paper, "w") as archive:
                archive.writestr(
                    "word/document.xml",
                    '<?xml version="1.0"?><w:document xmlns:w="urn:w"><w:body><w:p><w:r><w:t>待补充</w:t></w:r></w:p></w:body></w:document>',
                )
                archive.writestr(
                    "docProps/core.xml",
                    '<?xml version="1.0"?><cp:coreProperties xmlns:cp="urn:cp" xmlns:dc="urn:dc"><dc:creator>Alice</dc:creator></cp:coreProperties>',
                )
            code, report = self.run_check(root, paper)
            self.assertEqual(code, 1)
            self.assert_code(report, "placeholder")
            self.assert_code(report, "identity_metadata")

    def test_registry_uses_explicit_markers_or_paper_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "verify.txt"
            evidence.write_text("PASS", encoding="utf-8")
            source = root / "solve.py"
            source.write_text("print(1)", encoding="utf-8")
            registry = root / "registry.json"
            registry.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "id": "R001",
                                "approved_for_paper": True,
                                "verification_status": "PASS",
                                "paper_required": True,
                                "paper_checks": ["4.7734 s"],
                                "source_script": "solve.py",
                                "verification_report": "verify.txt",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            paper = root / "paper.md"
            paper.write_text("半径 R1 为变量，结果为 4.7734 s。", encoding="utf-8")
            code, report = self.run_check(root, paper, "--registry", str(registry))
            self.assertEqual(code, 0)
            self.assertNotIn("unknown_result", {item["code"] for item in report["findings"]})

            paper.write_text("显式引用未知结果 [[R999]]。", encoding="utf-8")
            code, report = self.run_check(root, paper, "--registry", str(registry))
            self.assertEqual(code, 1)
            self.assert_code(report, "unknown_result")
            self.assert_code(report, "missing_required_result")

    def test_registry_rejects_unverified_and_missing_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paper = root / "paper.md"
            paper.write_text("结果是 1.0。", encoding="utf-8")
            registry = root / "registry.json"
            registry.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "id": "R002",
                                "approved_for_paper": True,
                                "verification_status": "PENDING",
                                "paper_required": True,
                                "paper_checks": ["1.0"],
                                "source_script": "missing.py",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            code, report = self.run_check(root, paper, "--registry", str(registry))
            self.assertEqual(code, 1)
            self.assert_code(report, "unverified_result")
            self.assert_code(report, "missing_result_evidence")


if __name__ == "__main__":
    unittest.main()




