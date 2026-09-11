#!/usr/bin/env python3
"""Cross-platform preflight for modeling-competition paper sources.

The checker is read-only except for an optional JSON report. It validates source
structure and provenance signals; it does not replace mathematical review or
rendered-page inspection.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from xml.etree import ElementTree


PLACEHOLDER_RE = re.compile(
    r"PLACEHOLDER|TODO|TBD|FIXME|XXX|待补充|待填写|待续写|待完善|这里补|示例数据|"
    r"\[论文标题\]|中文摘要内容|关键词[1-9]",
    re.IGNORECASE,
)
INTERNAL_TERMS = (
    "ANALYSIS_MODELING_REPORT",
    "RESULTS_REPORT",
    "CUMCM_Workspace",
    "review_request.md",
    "prompt inject",
    "由 AI 生成",
)
# Result IDs are internal provenance labels. Only an explicit double-bracket
# marker is treated as a citation; ordinary notation such as R1 must not create
# false positives in a mathematical paper. Final papers should normally use
# registry ``paper_checks`` instead of exposing these markers.
RESULT_MARKER_RE = re.compile(r"\[\[(R\d+[A-Za-z0-9_-]*)\]\]")
LATEX_IN_TYPST_RE = re.compile(
    r"\\(?:begin|end|frac|sum|prod|alpha|beta|theta|lambda|text|cite|ref|label|includegraphics)\b"
)
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
TEX_INPUT_RE = re.compile(r"\\(?:input|include)\s*\{([^}]+)\}")
TEX_IMAGE_RE = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")
TYPST_INCLUDE_RE = re.compile(r'#include\(\s*"([^"]+)"\s*\)')
TYPST_IMAGE_RE = re.compile(r'image\(\s*"([^"]+)"')
GENERIC_HEADING_RE = re.compile(
    r"(?:问题|第)[一二三四五六七八九十0-9]+.{0,10}(?:模型建立与求解|分析与求解)"
)
SOFTWARE_ONLY_RESULT_RE = re.compile(
    r"(?:利用|使用|通过).{0,24}(?:MATLAB|Matlab|Python|LINGO|Lingo|SPSS|软件|程序)"
    r".{0,24}(?:计算|求解).{0,16}(?:得到|得出).{0,8}(?:结果如下|如下结果)",
    re.IGNORECASE,
)
VALIDATION_RE = re.compile(r"验证|检验|敏感性|稳健性|误差分析|残差|收敛|不确定性")
METHOD_NAMES = (
    "AHP", "层次分析", "熵权", "TOPSIS", "灰色预测", "遗传算法", "神经网络",
    "模拟退火", "粒子群", "随机森林", "支持向量机", "博弈论",
)


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    file: str


class Audit:
    def __init__(self, project: Path):
        self.project = project.resolve()
        self.findings: list[Finding] = []
        self.references: set[Path] = set()
        self.paper_text_parts: list[str] = []

    def add(self, severity: str, code: str, message: str, path: Path) -> None:
        try:
            label = path.resolve().relative_to(self.project).as_posix()
        except (OSError, ValueError):
            label = str(path)
        self.findings.append(Finding(severity, code, message, label))

    def hard(self, code: str, message: str, path: Path) -> None:
        self.add("HARD", code, message, path)

    def warn(self, code: str, message: str, path: Path) -> None:
        self.add("WARN", code, message, path)

    def scan_text(self, path: Path, text: str, *, appendix: bool = False) -> None:
        self.paper_text_parts.append(text)
        match = PLACEHOLDER_RE.search(text)
        if match:
            self.hard("placeholder", f"placeholder remains: {match.group(0)}", path)
        lowered = text.lower()
        for term in INTERNAL_TERMS:
            if term.lower() in lowered:
                level = "appendix_internal_term" if appendix else "internal_term"
                self.warn(level, f"internal workflow term appears in paper: {term}", path)
        if not appendix:
            generic = GENERIC_HEADING_RE.search(text)
            if generic:
                self.warn(
                    "generic_heading",
                    f"generic fill-in-the-blank heading needs review: {generic.group(0)}",
                    path,
                )
            if SOFTWARE_ONLY_RESULT_RE.search(text):
                self.warn(
                    "software_only_result",
                    "a result appears to be introduced only as software output; add correctness and practical interpretation",
                    path,
                )
            methods = sorted({name for name in METHOD_NAMES if name.lower() in lowered})
            if len(methods) >= 4:
                self.warn(
                    "method_catalog_review",
                    f"many named methods appear ({', '.join(methods[:6])}); verify a problem-specific fit certificate for each",
                    path,
                )
            if len(text) >= 1500 and not VALIDATION_RE.search(text):
                self.warn(
                    "missing_validation_language",
                    "no validation, sensitivity, error, convergence, residual, robustness, or uncertainty discussion was detected",
                    path,
                )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def resolve_reference(source: Path, raw: str, suffixes: tuple[str, ...]) -> Path | None:
    raw = raw.strip().split("#", 1)[0].split("?", 1)[0]
    if not raw or re.match(r"^[a-z][a-z0-9+.-]*://", raw, re.IGNORECASE):
        return None
    candidate = (source.parent / raw).resolve()
    if candidate.exists():
        return candidate
    if not candidate.suffix:
        for suffix in suffixes:
            alternate = candidate.with_suffix(suffix)
            if alternate.exists():
                return alternate
    return candidate


def balanced_calls(text: str, marker: str) -> list[str]:
    calls: list[str] = []
    for match in re.finditer(re.escape(marker) + r"\s*\(", text):
        start = text.find("(", match.start())
        depth = 0
        quote = False
        escape = False
        for index in range(start, len(text)):
            char = text[index]
            if quote:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    quote = False
            elif char == '"':
                quote = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    calls.append(text[start + 1 : index])
                    break
    return calls


def scan_tex(audit: Audit, main: Path) -> None:
    visited: set[Path] = set()

    def visit(path: Path, *, appendix: bool = False) -> None:
        resolved = path.resolve()
        if resolved in visited:
            return
        visited.add(resolved)
        if not path.exists():
            audit.hard("missing_include", "included LaTeX file does not exist", path)
            return
        text = read_text(path)
        audit.scan_text(path, text, appendix=appendix)
        for raw in TEX_INPUT_RE.findall(text):
            target = resolve_reference(path, raw, (".tex",))
            if target is not None:
                visit(target, appendix=appendix or target.name.lower().startswith(("a_", "appendix")))
        for raw in TEX_IMAGE_RE.findall(text):
            target = resolve_reference(path, raw, (".pdf", ".png", ".jpg", ".jpeg", ".svg"))
            if target is None or not target.exists():
                audit.hard("missing_image", f"LaTeX image does not exist: {raw}", path)
            else:
                audit.references.add(target.resolve())
        for block in re.findall(r"\\begin\{figure\}.*?\\end\{figure\}", text, re.DOTALL):
            if not re.search(r"\\caption\s*\{", block):
                audit.hard("missing_caption", "LaTeX figure has no caption", path)

    visit(main)


def scan_typst(audit: Audit, main: Path) -> None:
    visited: set[Path] = set()

    def visit(path: Path, *, appendix: bool = False) -> None:
        resolved = path.resolve()
        if resolved in visited:
            return
        visited.add(resolved)
        if not path.exists():
            audit.hard("missing_include", "included Typst file does not exist", path)
            return
        text = read_text(path)
        audit.scan_text(path, text, appendix=appendix)
        residue = LATEX_IN_TYPST_RE.search(text)
        if residue:
            audit.hard("mixed_syntax", f"LaTeX command remains in Typst: {residue.group(0)}", path)
        for raw in TYPST_INCLUDE_RE.findall(text):
            target = resolve_reference(path, raw, (".typ",))
            if target is not None:
                visit(target, appendix=appendix or target.name.lower().startswith(("a_", "appendix")))
        for raw in TYPST_IMAGE_RE.findall(text):
            target = resolve_reference(path, raw, (".pdf", ".png", ".jpg", ".jpeg", ".svg"))
            if target is None or not target.exists():
                audit.hard("missing_image", f"Typst image does not exist: {raw}", path)
            else:
                audit.references.add(target.resolve())
        for body in balanced_calls(text, "#figure"):
            if "caption:" not in body:
                audit.hard("missing_caption", "Typst figure has no caption", path)

    visit(main)


def scan_markdown(audit: Audit, path: Path) -> None:
    text = read_text(path)
    audit.scan_text(path, text)
    for raw in MARKDOWN_IMAGE_RE.findall(text):
        target = resolve_reference(path, raw, (".pdf", ".png", ".jpg", ".jpeg", ".svg"))
        if target is None:
            continue
        if not target.exists():
            audit.hard("missing_image", f"Markdown image does not exist: {raw}", path)
        else:
            audit.references.add(target.resolve())


def scan_docx(audit: Audit, path: Path) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            try:
                document_xml = archive.read("word/document.xml")
            except KeyError:
                audit.hard("invalid_docx", "DOCX has no word/document.xml", path)
                return
            root = ElementTree.fromstring(document_xml)
            paragraph_texts = []
            for paragraph in root.iter():
                if not paragraph.tag.endswith("}p"):
                    continue
                paragraph_texts.append(
                    "".join(node.text or "" for node in paragraph.iter() if node.tag.endswith("}t"))
                )
            text = "\n".join(paragraph_texts)
            audit.scan_text(path, text)
            if not text.strip():
                audit.hard("empty_paper", "DOCX body contains no text", path)
            try:
                core = ElementTree.fromstring(archive.read("docProps/core.xml"))
                metadata = {
                    node.tag.rsplit("}", 1)[-1]: (node.text or "").strip()
                    for node in core.iter()
                }
                for key in ("creator", "lastModifiedBy"):
                    value = metadata.get(key, "")
                    if value and value.lower() not in {"参赛队", "team", "anonymous", "匿名"}:
                        audit.warn("identity_metadata", f"review possible identity metadata {key}={value!r}", path)
            except (KeyError, ElementTree.ParseError):
                audit.warn("missing_metadata", "DOCX core metadata could not be inspected", path)
    except (OSError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        audit.hard("invalid_docx", f"cannot parse DOCX: {exc}", path)


def scan_pdf(audit: Audit, path: Path) -> None:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        audit.warn("pdf_text_unchecked", "pypdf unavailable; run the PDF skill for page and visual QA", path)
        return
    try:
        reader = PdfReader(str(path))
        if not reader.pages:
            audit.hard("empty_paper", "PDF has no pages", path)
            return
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if text.strip():
            audit.scan_text(path, text)
        else:
            audit.warn("pdf_text_unchecked", "PDF has no extractable text; OCR or visual QA is required", path)
        metadata = reader.metadata or {}
        author = str(metadata.get("/Author", "")).strip()
        if author and author.lower() not in {"参赛队", "team", "anonymous", "匿名"}:
            audit.warn("identity_metadata", f"review possible PDF author metadata: {author!r}", path)
    except Exception as exc:  # pypdf exposes several parser-specific exceptions
        audit.hard("invalid_pdf", f"cannot parse PDF: {exc}", path)


def scan_registry(audit: Audit, registry_path: Path) -> None:
    try:
        payload = json.loads(read_text(registry_path))
    except (OSError, json.JSONDecodeError) as exc:
        audit.hard("invalid_registry", f"cannot parse result registry: {exc}", registry_path)
        return
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        audit.hard("invalid_registry", "registry must contain a results list", registry_path)
        return
    ids: set[str] = set()
    approved: set[str] = set()
    paper_text = "\n".join(audit.paper_text_parts)
    for index, result in enumerate(results, 1):
        if not isinstance(result, dict):
            audit.hard("invalid_registry", f"result #{index} is not an object", registry_path)
            continue
        result_id = result.get("id")
        if not isinstance(result_id, str) or not result_id:
            audit.hard("invalid_registry", f"result #{index} has no string id", registry_path)
            continue
        if result_id in ids:
            audit.hard("duplicate_result", f"duplicate result id: {result_id}", registry_path)
        ids.add(result_id)
        is_approved = result.get("approved_for_paper") is True and result.get("verification_status") == "PASS"
        if result.get("approved_for_paper") is True and not is_approved:
            audit.hard("unverified_result", f"paper-approved result is not verified PASS: {result_id}", registry_path)
        if is_approved:
            approved.add(result_id)
        if result.get("paper_required") is True:
            checks = result.get("paper_checks", [])
            if not isinstance(checks, list) or not all(isinstance(item, str) and item for item in checks):
                audit.hard(
                    "invalid_registry",
                    f"paper-required result needs a non-empty string list paper_checks: {result_id}",
                    registry_path,
                )
            elif not checks:
                audit.hard(
                    "invalid_registry",
                    f"paper-required result needs paper_checks: {result_id}",
                    registry_path,
                )
            elif not all(item in paper_text for item in checks) and f"[[{result_id}]]" not in paper_text:
                audit.hard(
                    "missing_required_result",
                    f"paper-required result is not evidenced by all paper_checks: {result_id}",
                    registry_path,
                )
        for key in ("source_script", "verification_report"):
            raw = result.get(key)
            if isinstance(raw, str) and raw:
                target = Path(raw)
                if not target.is_absolute():
                    target = audit.project / target
                if not target.exists():
                    audit.hard("missing_result_evidence", f"{result_id} missing {key}: {raw}", registry_path)
    for result_id in sorted(set(RESULT_MARKER_RE.findall(paper_text))):
        if result_id not in ids:
            audit.hard("unknown_result", f"paper cites unknown result id: {result_id}", registry_path)
        elif result_id not in approved:
            audit.hard("unapproved_result", f"paper cites unapproved result id: {result_id}", registry_path)


def scan_figures(audit: Audit, figures_dir: Path) -> None:
    if not figures_dir.exists():
        audit.warn("missing_figures_dir", "figures directory does not exist", figures_dir)
        return
    for path in figures_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".svg"}:
            if path.resolve() not in audit.references:
                audit.warn("unreferenced_figure", "figure asset is not referenced by the inspected source", path)


def scan_support_archive(audit: Audit, archive_path: Path) -> None:
    if not archive_path.is_file():
        audit.hard("missing_support_archive", "supporting-material archive does not exist", archive_path)
        return
    if archive_path.stat().st_size > 20 * 1024 * 1024:
        audit.hard("support_archive_size", "supporting-material archive exceeds 20 MB", archive_path)
    suffix = archive_path.suffix.lower()
    if suffix not in {".zip", ".rar"}:
        audit.hard("support_archive_format", "supporting materials must be one ZIP or RAR archive", archive_path)
        return
    if suffix == ".rar":
        audit.warn(
            "support_archive_manual",
            "RAR contents were not inspected; open it on a clean machine and verify files, identity, and runnable code",
            archive_path,
        )
        return
    try:
        with zipfile.ZipFile(archive_path) as archive:
            members = [item for item in archive.infolist() if not item.is_dir()]
            if not members:
                audit.hard("empty_support_archive", "supporting-material ZIP contains no files", archive_path)
            for item in members:
                normalized = item.filename.replace("\\", "/")
                if normalized.startswith("/") or ".." in normalized.split("/"):
                    audit.hard("unsafe_support_path", f"unsafe path in support archive: {item.filename}", archive_path)
    except (OSError, zipfile.BadZipFile) as exc:
        audit.hard("invalid_support_archive", f"cannot inspect supporting-material ZIP: {exc}", archive_path)
    audit.warn(
        "support_identity_manual",
        "manually verify that archive contents and metadata contain no team, school, region, instructor, or private information",
        archive_path,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", required=True, type=Path, help="Paper source or final PDF to inspect.")
    parser.add_argument("--project", type=Path, help="Project root; defaults to the paper's parent.")
    parser.add_argument("--registry", type=Path, help="Optional result registry JSON.")
    parser.add_argument("--figures-dir", type=Path, help="Optional figure asset directory.")
    parser.add_argument("--forbidden-term", action="append", default=[], help="Project-specific identity or leak term.")
    parser.add_argument("--max-size-mb", type=float, help="Official maximum paper file size, when applicable.")
    parser.add_argument("--support-archive", type=Path, help="Optional CUMCM ZIP/RAR supporting-material archive.")
    parser.add_argument("--output", type=Path, help="Optional JSON report path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    paper = args.paper.expanduser().resolve()
    project = (args.project or paper.parent).expanduser().resolve()
    audit = Audit(project)
    if not paper.exists():
        audit.hard("missing_paper", "paper file does not exist", paper)
    elif not paper.is_file() or paper.stat().st_size == 0:
        audit.hard("empty_paper", "paper file is empty or not a regular file", paper)
    else:
        if args.max_size_mb is not None and paper.stat().st_size > args.max_size_mb * 1024 * 1024:
            audit.hard("file_size", f"paper exceeds {args.max_size_mb:g} MB", paper)
        suffix = paper.suffix.lower()
        if suffix == ".tex":
            scan_tex(audit, paper)
        elif suffix == ".typ":
            scan_typst(audit, paper)
        elif suffix in {".md", ".markdown"}:
            scan_markdown(audit, paper)
        elif suffix == ".docx":
            scan_docx(audit, paper)
        elif suffix == ".pdf":
            scan_pdf(audit, paper)
        else:
            audit.hard("unsupported_format", f"unsupported paper format: {suffix or '<none>'}", paper)
    paper_text = "\n".join(audit.paper_text_parts)
    for term in args.forbidden_term:
        if term and term.lower() in paper_text.lower():
            audit.hard("forbidden_term", f"forbidden term appears in paper: {term}", paper)
    if args.registry:
        scan_registry(audit, args.registry.expanduser().resolve())
    if args.figures_dir:
        scan_figures(audit, args.figures_dir.expanduser().resolve())
    if args.support_archive:
        scan_support_archive(audit, args.support_archive.expanduser().resolve())
    hard_count = sum(item.severity == "HARD" for item in audit.findings)
    warn_count = sum(item.severity == "WARN" for item in audit.findings)
    report = {
        "status": "FAIL" if hard_count else "PASS",
        "paper": str(paper),
        "project": str(project),
        "support_archive": str(args.support_archive.expanduser().resolve()) if args.support_archive else None,
        "hard_failures": hard_count,
        "warnings": warn_count,
        "findings": [asdict(item) for item in audit.findings],
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 1 if hard_count else 0


if __name__ == "__main__":
    raise SystemExit(main())




