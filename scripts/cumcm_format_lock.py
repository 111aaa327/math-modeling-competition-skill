#!/usr/bin/env python3
"""Record and audit a CUMCM paper-format lock using only the standard library."""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import sys
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
W = f"{{{W_NS}}}"
R = f"{{{R_NS}}}"
PR = f"{{{PR_NS}}}"
A4_TWIPS = (11906, 16838)
MIN_MARGIN_TWIPS = 1417
BLACK_VALUES = {"000000", "auto"}
SUPPORTING_FILE_RE = re.compile(
    r"支撑材料|文件列表|本论文没有支撑材料|[A-Za-z0-9_.-]+\.(?:py|ipynb|r|m|jl|csv|xlsx?|json|txt|zip|rar)(?![A-Za-z0-9])",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def within(root: Path, path: Path) -> Path:
    root = root.resolve()
    path = path.resolve()
    try:
        return path.relative_to(root)
    except ValueError as exc:
        raise SystemExit(f"File must be inside workspace: {path}") from exc


def read_docx_parts(path: Path) -> dict[str, bytes]:
    try:
        with zipfile.ZipFile(path) as archive:
            return {name: archive.read(name) for name in archive.namelist()}
    except (OSError, zipfile.BadZipFile) as exc:
        raise ValueError(f"cannot read DOCX package: {exc}") from exc


def parse_xml(parts: dict[str, bytes], name: str) -> ET.Element | None:
    raw = parts.get(name)
    if raw is None:
        return None
    try:
        return ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError(f"invalid XML part {name}: {exc}") from exc


def style_package_hash(path: Path) -> str:
    parts = read_docx_parts(path)
    digest = hashlib.sha256()
    found = False
    for name in ("word/styles.xml", "word/numbering.xml", "word/theme/theme1.xml"):
        if name in parts:
            found = True
            digest.update(name.encode("utf-8"))
            digest.update(b"\0")
            digest.update(parts[name])
    if not found:
        raise ValueError("template has no Word style package")
    return digest.hexdigest()


def load_lock(workspace: Path, explicit: Path | None) -> tuple[Path, dict]:
    lock_path = (explicit or workspace / "FORMAT_LOCK.json").resolve()
    if not lock_path.is_file():
        raise ValueError(f"format lock is missing: {lock_path}")
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read format lock: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("status") != "LOCKED":
        raise ValueError("FORMAT_LOCK.json status must be LOCKED")
    return lock_path, payload


def cmd_lock(args: argparse.Namespace) -> int:
    workspace = args.workspace.expanduser().resolve()
    if not workspace.is_dir():
        raise SystemExit(f"Workspace does not exist: {workspace}")
    official = args.official_rules.expanduser().resolve()
    if not official.is_file():
        raise SystemExit(f"Official rules file does not exist: {official}")
    official_rel = within(workspace, official)
    template_payload = None
    if args.word_template:
        template = args.word_template.expanduser().resolve()
        if template.suffix.lower() not in {".docx", ".dotx"}:
            raise SystemExit("Locked Word templates must be .docx or .dotx; convert legacy .doc first")
        if not template.is_file():
            raise SystemExit(f"Word template does not exist: {template}")
        template_rel = within(workspace, template)
        template_payload = {
            "path": template_rel.as_posix(),
            "sha256": sha256(template),
            "style_package_sha256": style_package_hash(template),
        }
    lock_path = (args.output or workspace / "FORMAT_LOCK.json").expanduser().resolve()
    if lock_path.exists() and not args.force:
        try:
            existing = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"Cannot inspect existing lock; use --force only after review: {exc}") from exc
        if not isinstance(existing, dict) or existing.get("status") != "UNLOCKED":
            raise SystemExit(f"Refusing to overwrite an existing non-UNLOCKED lock without --force: {lock_path}")
    payload = {
        "schema_version": 1,
        "status": "LOCKED",
        "competition": args.competition,
        "edition": str(args.edition),
        "paper_mode": args.paper_mode,
        "style_profile": args.style_profile,
        "locked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "official_rules": {
            "path": official_rel.as_posix(),
            "sha256": sha256(official),
            "source_url": args.source_url or "",
        },
        "word_template": template_payload,
        "typography_note": (
            "A locked Word template controls typography. Otherwise classic-black is a team style, "
            "not an official typography requirement."
        ),
    }
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(lock_path)
    return 0


class Audit:
    def __init__(self, strict_style: bool):
        self.strict_style = strict_style
        self.findings: list[Finding] = []

    def hard(self, code: str, message: str) -> None:
        self.findings.append(Finding("HARD", code, message))

    def warn(self, code: str, message: str) -> None:
        self.findings.append(Finding("WARN", code, message))

    def style(self, code: str, message: str) -> None:
        (self.hard if self.strict_style else self.warn)(code, message)


def attr_int(node: ET.Element | None, name: str) -> int | None:
    if node is None:
        return None
    raw = node.get(W + name)
    try:
        return int(raw) if raw is not None else None
    except ValueError:
        return None


def paragraphs(root: ET.Element) -> list[tuple[ET.Element, str]]:
    result = []
    for paragraph in root.iter(W + "p"):
        text = "".join(node.text or "" for node in paragraph.iter(W + "t")).strip()
        if text:
            result.append((paragraph, text))
    return result


def paragraph_style_id(paragraph: ET.Element) -> str:
    node = paragraph.find(f"{W}pPr/{W}pStyle")
    return node.get(W + "val", "") if node is not None else ""


def paragraph_alignment(paragraph: ET.Element, styles: dict[str, ET.Element]) -> str:
    node = paragraph.find(f"{W}pPr/{W}jc")
    if node is not None:
        return node.get(W + "val", "")
    style = styles.get(paragraph_style_id(paragraph))
    if style is not None:
        node = style.find(f"{W}pPr/{W}jc")
        if node is not None:
            return node.get(W + "val", "")
    return ""


def color_is_nonblack(node: ET.Element) -> bool:
    value = (node.get(W + "val") or "auto").lower()
    theme = node.get(W + "themeColor")
    return value not in BLACK_VALUES or (theme not in {None, "text1", "dark1"})


def paragraph_has_nonblack(paragraph: ET.Element, style: ET.Element | None) -> bool:
    colors = list(paragraph.iter(W + "color"))
    if not colors and style is not None:
        colors = list(style.iter(W + "color"))
    return any(color_is_nonblack(node) for node in colors)


def style_maps(styles_root: ET.Element | None) -> tuple[dict[str, ET.Element], dict[str, str]]:
    elements: dict[str, ET.Element] = {}
    names: dict[str, str] = {}
    if styles_root is None:
        return elements, names
    for style in styles_root.findall(W + "style"):
        style_id = style.get(W + "styleId", "")
        if not style_id:
            continue
        elements[style_id] = style
        name = style.find(W + "name")
        names[style_id] = name.get(W + "val", "") if name is not None else ""
    return elements, names


def validate_lock_files(audit: Audit, workspace: Path, payload: dict) -> None:
    official = payload.get("official_rules")
    if not isinstance(official, dict) or not official.get("path") or not official.get("sha256"):
        audit.hard("invalid_format_lock", "official rules path/hash are missing from format lock")
        return
    official_path = (workspace / str(official["path"])).resolve()
    try:
        within(workspace, official_path)
    except SystemExit:
        audit.hard("invalid_format_lock", "official rules path escapes workspace")
        return
    if not official_path.is_file():
        audit.hard("missing_official_rules", f"locked official rules file is missing: {official_path}")
    elif sha256(official_path) != official["sha256"]:
        audit.hard("official_rules_changed", "locked official rules hash does not match")
    template = payload.get("word_template")
    if isinstance(template, dict) and template.get("path"):
        template_path = (workspace / str(template["path"])).resolve()
        try:
            within(workspace, template_path)
        except SystemExit:
            audit.hard("invalid_format_lock", "Word template path escapes workspace")
            return
        if not template_path.is_file():
            audit.hard("missing_word_template", f"locked Word template is missing: {template_path}")
        elif sha256(template_path) != template.get("sha256"):
            audit.hard("word_template_changed", "locked Word template hash does not match")


def audit_docx(audit: Audit, paper: Path, payload: dict) -> None:
    try:
        parts = read_docx_parts(paper)
        document = parse_xml(parts, "word/document.xml")
        styles_root = parse_xml(parts, "word/styles.xml")
    except ValueError as exc:
        audit.hard("invalid_docx", str(exc))
        return
    if document is None:
        audit.hard("invalid_docx", "word/document.xml is missing")
        return

    if paper.stat().st_size > 20 * 1024 * 1024:
        audit.hard("paper_size", "electronic paper exceeds 20 MB")

    sects = list(document.iter(W + "sectPr"))
    if not sects:
        audit.hard("missing_page_setup", "document has no section page setup")
    for index, sect in enumerate(sects, 1):
        size = sect.find(W + "pgSz")
        width, height = attr_int(size, "w"), attr_int(size, "h")
        if width is None or height is None or min(
            abs(width - A4_TWIPS[0]) + abs(height - A4_TWIPS[1]),
            abs(width - A4_TWIPS[1]) + abs(height - A4_TWIPS[0]),
        ) > 200:
            audit.hard("page_size", f"section {index} is not A4")
        margins = sect.find(W + "pgMar")
        for side in ("top", "right", "bottom", "left"):
            value = attr_int(margins, side)
            if value is None or value < MIN_MARGIN_TWIPS:
                audit.hard("page_margin", f"section {index} {side} margin is below 2.5 cm")

    paras = paragraphs(document)
    early_text = "\n".join(text for _, text in paras[:25])
    early_compact = re.sub(r"\s+", "", early_text)
    if payload.get("paper_mode") == "electronic" and re.search(r"承诺书|编号专用页", early_text):
        audit.hard("electronic_front_matter", "electronic paper contains pledge or number-page content")
    if "摘要" not in early_compact:
        audit.hard("missing_summary", "abstract heading is not near the beginning of the electronic paper")
    if "关键词" not in early_compact:
        audit.hard("missing_keywords", "keywords are not present near the abstract")
    if any(text.replace(" ", "") == "目录" for _, text in paras):
        audit.hard("table_of_contents", "CUMCM paper must not contain a table of contents")
    for node in document.iter(W + "instrText"):
        if re.search(r"\bTOC\b", node.text or "", re.IGNORECASE):
            audit.hard("table_of_contents", "TOC field is present")

    appendix_index = next((i for i, (_, text) in enumerate(paras) if re.match(r"^附录", text)), None)
    if appendix_index is None:
        audit.hard("missing_appendix", "paper has no appendix")
    else:
        appendix_text = "\n".join(text for _, text in paras[appendix_index:])
        if not re.search(r"源程序|程序代码|完整.{0,8}代码|代码如下|本论文没有用到程序", appendix_text):
            audit.hard("missing_source_code", "appendix does not contain or explicitly account for complete source code")
        if not SUPPORTING_FILE_RE.search(appendix_text):
            audit.hard("missing_supporting_file_list", "appendix does not list or explicitly disclaim supporting files")

    footer_ids = {
        node.get(R + "id")
        for sect in sects
        for node in sect.findall(W + "footerReference")
        if node.get(R + "id")
    }
    footer_names: set[str] = set()
    rels = parse_xml(parts, "word/_rels/document.xml.rels")
    if rels is not None:
        for relationship in rels.findall(PR + "Relationship"):
            if relationship.get("Id") in footer_ids:
                target = relationship.get("Target", "")
                footer_names.add(posixpath.normpath(posixpath.join("word", target.lstrip("/"))))
    footer_has_page = False
    footer_has_centered_page = False
    for name, raw in parts.items():
        if name not in footer_names:
            continue
        try:
            footer = ET.fromstring(raw)
        except ET.ParseError:
            continue
        for paragraph in footer.iter(W + "p"):
            instructions = "".join(node.text or "" for node in paragraph.iter(W + "instrText"))
            if re.search(r"\bPAGE\b", instructions, re.IGNORECASE):
                footer_has_page = True
                jc = paragraph.find(f"{W}pPr/{W}jc")
                footer_has_centered_page = footer_has_centered_page or (
                    jc is not None and jc.get(W + "val") == "center"
                )
    if not footer_has_page:
        audit.hard("page_number", "no PAGE field was found in a footer")
    elif not footer_has_centered_page:
        audit.hard("page_number_alignment", "page number is not centered in the footer")
    starts = [node.get(W + "start") for node in document.iter(W + "pgNumType") if node.get(W + "start")]
    if starts and starts[0] != "1":
        audit.hard("page_number_start", "first explicit page-number start is not 1")
    if len(starts) > 1:
        audit.hard("page_number_restart", "page numbering restarts in a later section")

    template = payload.get("word_template")
    if isinstance(template, dict) and template.get("style_package_sha256"):
        try:
            if style_package_hash(paper) != template["style_package_sha256"]:
                audit.hard("template_styles_changed", "paper style package differs from the locked Word template")
        except ValueError as exc:
            audit.hard("template_styles_unchecked", str(exc))

    if payload.get("style_profile") == "classic-black" and not template:
        style_elements, style_names = style_maps(styles_root)
        heading_tokens = ("heading", "title", "caption", "标题", "题注")
        first_paragraph = paras[0][0] if paras else None
        nonblack_headings: list[str] = []
        for paragraph, text in paras:
            style_id = paragraph_style_id(paragraph)
            style_name = style_names.get(style_id, "")
            heading_like = (
                paragraph is first_paragraph
                or text.replace(" ", "") == "摘要"
                or any(token in (style_id + " " + style_name).lower() for token in heading_tokens)
            )
            if not heading_like:
                continue
            if paragraph_has_nonblack(paragraph, style_elements.get(style_id)):
                nonblack_headings.append(text[:40])
            alignment = paragraph_alignment(paragraph, style_elements)
            if paragraph is first_paragraph and alignment != "center":
                audit.style("title_alignment", "paper title is not centered")
            if re.sub(r"\s+", "", text) == "摘要" and alignment != "center":
                audit.style("abstract_alignment", "abstract heading is not centered")
        if nonblack_headings:
            samples = "; ".join(nonblack_headings[:4])
            audit.style(
                "nonblack_heading",
                f"{len(nonblack_headings)} headings/titles use non-black color; examples: {samples}",
            )

    audit.warn(
        "visual_qa_required",
        "render every page to verify the one-page abstract, 30-page body limit, captions, equations, page breaks, and appendix completeness",
    )


def cmd_audit(args: argparse.Namespace) -> int:
    workspace = args.workspace.expanduser().resolve()
    paper = args.paper.expanduser().resolve()
    audit = Audit(args.strict_style)
    try:
        _, payload = load_lock(workspace, args.lock)
    except ValueError as exc:
        audit.hard("format_lock", str(exc))
        payload = {}
    if payload:
        validate_lock_files(audit, workspace, payload)
    if not paper.is_file():
        audit.hard("missing_paper", f"paper does not exist: {paper}")
    elif paper.suffix.lower() != ".docx":
        audit.hard("unsupported_paper", "format lock audit currently requires a DOCX paper")
    else:
        audit_docx(audit, paper, payload)
    hard_count = sum(item.severity == "HARD" for item in audit.findings)
    warn_count = sum(item.severity == "WARN" for item in audit.findings)
    report = {
        "status": "FAIL" if hard_count else "PASS",
        "paper": str(paper),
        "workspace": str(workspace),
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    lock = subparsers.add_parser("lock", help="Record official rules and an optional Word template")
    lock.add_argument("--workspace", required=True, type=Path)
    lock.add_argument("--official-rules", required=True, type=Path)
    lock.add_argument("--competition", default="CUMCM")
    lock.add_argument("--edition", required=True)
    lock.add_argument("--paper-mode", choices=("electronic", "printed"), default="electronic")
    lock.add_argument("--style-profile", choices=("official-only", "classic-black"), default="classic-black")
    lock.add_argument("--word-template", type=Path)
    lock.add_argument("--source-url")
    lock.add_argument("--output", type=Path)
    lock.add_argument("--force", action="store_true")
    lock.set_defaults(func=cmd_lock)

    audit = subparsers.add_parser("audit", help="Audit a DOCX against the recorded format lock")
    audit.add_argument("--workspace", required=True, type=Path)
    audit.add_argument("--paper", required=True, type=Path)
    audit.add_argument("--lock", type=Path)
    audit.add_argument("--strict-style", action="store_true")
    audit.add_argument("--output", type=Path)
    audit.set_defaults(func=cmd_audit)
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
