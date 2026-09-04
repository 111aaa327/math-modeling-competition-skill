#!/usr/bin/env python3
"""Index ZIP central directories without extracting large modeling archives."""

from __future__ import annotations

import argparse
import csv
import re
import zipfile
from pathlib import Path


TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".py", ".m", ".r", ".tex", ".json", ".xml"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def searchability(ext: str) -> str:
    if ext in TEXT_EXTENSIONS:
        return "direct-text"
    if ext in DOCUMENT_EXTENSIONS:
        return "extract-or-render"
    if ext in IMAGE_EXTENSIONS:
        return "ocr-needed"
    return "unknown-or-binary"


def decoded_name(info: zipfile.ZipInfo) -> str:
    """Repair common mainland-China ZIP names stored as GBK without UTF-8 flag."""
    name = info.filename
    if info.flag_bits & 0x800:
        return name
    try:
        return name.encode("cp437").decode("gbk")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    rows = []
    for archive in args.archives:
        archive = archive.expanduser().resolve()
        with zipfile.ZipFile(archive) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                name = decoded_name(info).replace("\\", "/")
                ext = Path(name).suffix.lower()
                match = re.search(r"(?:19|20)\d{2}", name)
                ratio = 0.0 if info.file_size == 0 else 1 - info.compress_size / info.file_size
                rows.append({
                    "archive": str(archive),
                    "entry": name,
                    "top_level": name.split("/", 1)[0],
                    "extension": ext,
                    "year_hint": match.group(0) if match else "",
                    "uncompressed_bytes": info.file_size,
                    "compressed_bytes": info.compress_size,
                    "compression_ratio": f"{ratio:.4f}",
                    "searchability_hint": searchability(ext),
                })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ["archive", "entry"]
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Indexed {len(rows)} files into {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())




