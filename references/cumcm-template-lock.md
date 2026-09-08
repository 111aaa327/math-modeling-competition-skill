# CUMCM format lock

Use this procedure whenever the deliverable is a CUMCM paper. It separates official rules from a team-selected visual style so that a third-party teaching template is never mislabeled as official.

## Authorities

1. The current CUMCM organizing committee's format specification and notices are the only source of hard format requirements.
2. A regional notice may add requirements when the official specification allows it.
3. A Word/LaTeX/Typst template, past winning paper, course handout, or prompt pack is a style reference unless its official provenance is verified.

The 2026 national specification explicitly leaves font size, font family, line spacing, and color unspecified. Therefore `classic-black` below is a conservative team style profile, not an official typography rule.

## Lock gate

Before drafting the final paper:

1. Put the verified official format document under `00_rules/official/`.
2. If the team adopts a Word template, put the approved `.docx` or `.dotx` under `00_rules/templates/`. Legacy `.doc` files must be converted and visually checked before they can be locked.
3. Record file hashes and the selected paper mode/style profile:

```text
python scripts/cumcm_format_lock.py lock --workspace <workspace> --official-rules <official-format.pdf> --competition "CUMCM 2026" --edition 2026 --paper-mode electronic --style-profile classic-black [--word-template <approved.docx>]
```

4. Do not generate the final paper from a blank generic document when a Word template is locked. Create a working copy from the locked template and preserve its page geometry and styles.
5. Run the audit before visual QA:

```text
python scripts/cumcm_format_lock.py audit --workspace <workspace> --paper <paper.docx> --strict-style --output <format-report.json>
```

Any `HARD` finding blocks delivery. Then render every page and manually verify the items that OOXML cannot prove: summary length, body page count, figure/caption duplication, page breaks, equation appearance, and appendix completeness.

## Built-in `classic-black` profile

Use this only when no official or regionally mandated typography template exists. It prevents the modern-report styling that commonly drifts away from CUMCM papers:

- all titles, headings, captions, and page headers are black;
- the paper title and `摘要` heading are centered;
- first-level headings are centered and lower-level headings are left aligned;
- no decorative accent colors, title rules, cover page, or table of contents;
- use a consistent Chinese academic font system and compact readable spacing chosen by the team;
- a figure has one external caption; do not repeat the same title inside the image and below it.

Do not claim that this profile is mandated by the national rules. If a verified template is locked, its styles override this fallback profile.

## Required 2026 hard checks

- A4 pages and margins of at least 2.5 cm on all four sides.
- Electronic paper starts with the summary page; pledge and number pages are excluded.
- Summary page contains title, abstract, and keywords; page numbering begins there at 1 in the centered footer.
- No table of contents; body begins after the summary and is at most 30 pages.
- Appendix lists supporting files and includes all complete runnable source code, or explicitly states that no program was used.
- Paper and supporting materials contain no identity or region clues.
- Electronic paper is one PDF or Word file no larger than 20 MB; supporting archive is ZIP/RAR no larger than 20 MB.
- Electronic and printed paper content and formatting, including appendices, are identical.

