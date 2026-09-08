from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "cumcm_format_lock.py"


def make_docx(path: Path, *, margin: int = 1500, heading_color: str = "000000", footer: bool = True) -> None:
    document = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:t>测试论文题目</w:t></w:r></w:p>
    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>摘 要</w:t></w:r></w:p>
    <w:p><w:r><w:t>研究内容与主要结论。关键词：模型；验证</w:t></w:r></w:p>
    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>1 问题重述</w:t></w:r></w:p>
    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>附录</w:t></w:r></w:p>
    <w:p><w:r><w:t>附件：solve.py完整源程序代码如下：print(1)</w:t></w:r></w:p>
    <w:sectPr>
      {"<w:footerReference w:type=\"default\" r:id=\"rId1\"/>" if footer else ""}
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="{margin}" w:right="{margin}" w:bottom="{margin}" w:left="{margin}"/>
      <w:pgNumType w:start="1"/>
    </w:sectPr>
  </w:body>
</w:document>'''.replace(
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"',
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"',
    )
    styles = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/><w:pPr><w:jc w:val="center"/></w:pPr>
    <w:rPr><w:color w:val="{heading_color}"/></w:rPr>
  </w:style>
</w:styles>'''
    footer_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:instrText> PAGE </w:instrText></w:r></w:p>
</w:ftr>'''
    relationships = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
</Relationships>'''
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document)
        archive.writestr("word/styles.xml", styles)
        if footer:
            archive.writestr("word/footer1.xml", footer_xml)
            archive.writestr("word/_rels/document.xml.rels", relationships)


class CumcmFormatLockTests(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def prepare_lock(self, root: Path) -> None:
        official = root / "00_rules" / "official" / "format.pdf"
        official.parent.mkdir(parents=True)
        official.write_bytes(b"official-format-rules")
        result = self.run_script(
            "lock", "--workspace", str(root), "--official-rules", str(official),
            "--edition", "2026", "--style-profile", "classic-black",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_valid_classic_docx_passes_with_visual_warning(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.prepare_lock(root)
            paper = root / "paper.docx"
            make_docx(paper)
            result = self.run_script(
                "audit", "--workspace", str(root), "--paper", str(paper), "--strict-style",
            )
            report = json.loads(result.stdout)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(report["status"], "PASS")
            self.assertIn("visual_qa_required", {item["code"] for item in report["findings"]})

    def test_small_margins_and_blue_heading_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.prepare_lock(root)
            paper = root / "paper.docx"
            make_docx(paper, margin=1000, heading_color="2E74B5")
            result = self.run_script(
                "audit", "--workspace", str(root), "--paper", str(paper), "--strict-style",
            )
            report = json.loads(result.stdout)
            codes = {item["code"] for item in report["findings"]}
            self.assertEqual(result.returncode, 1)
            self.assertIn("page_margin", codes)
            self.assertIn("nonblack_heading", codes)

    def test_missing_page_number_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.prepare_lock(root)
            paper = root / "paper.docx"
            make_docx(paper, footer=False)
            result = self.run_script("audit", "--workspace", str(root), "--paper", str(paper))
            report = json.loads(result.stdout)
            self.assertEqual(result.returncode, 1)
            self.assertIn("page_number", {item["code"] for item in report["findings"]})


if __name__ == "__main__":
    unittest.main()
