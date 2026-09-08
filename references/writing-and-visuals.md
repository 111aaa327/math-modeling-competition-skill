# Writing and visual evidence

- Organize the paper around the requested questions and decisions, not a catalog of algorithms.
- Make the abstract state the problem, main methods, quantitative findings, validation, and practical meaning within the official limit.
- Define symbols before use and keep notation, units, precision, and terminology consistent.
- State assumptions with consequences and validation, not arbitrary quantity targets.
- Every table and figure needs a purpose, readable labels/units, a data source, and an interpretation in the text.
- Prefer comparison, sensitivity, residual, uncertainty, and spatial/temporal evidence over decorative diagrams.
- Separate evidence-bearing data figures from conceptual diagrams. Data figures must be regenerated from recorded results; conceptual diagrams should have editable sources and may not imply numerical evidence.
- Do not force a roadmap or per-question flowchart. Create a conceptual diagram only when it explains a relationship that prose or a compact table cannot.
- Do not invent references, datasets, results, download links, or supplementary files.
- Do not force minimum page, equation, chart, model, or test counts unless official rules explicitly require them.
- Verify cross-references, captions, bibliography entries, anonymity, page limits, filenames, archive contents, and file sizes.
- Keep internal workflow terms, temporary paths, result-registry IDs, prompt text, and drafting notes out of the paper body. File names may appear in an appendix only when they are part of the reproducibility or submission inventory.

## Typesetting route

- CUMCM: read `cumcm-template-lock.md`, record `FORMAT_LOCK.json`, and block final authoring until the official-rule source hash is locked. A verified Word template controls the document; otherwise use the labeled `classic-black` team profile.
- Word: use when the official template or team workflow requires DOCX. Create the working paper from the locked template rather than a blank generic document. Render to PDF and visually compare against the template/reference.
- LaTeX: use when the template is verified and the environment can compile it deterministically. Run enough passes to resolve cross-references and inspect the log.
- Typst: use only after its template has been calibrated against official geometry and fonts. Scan for accidental LaTeX commands before compilation.
- Never treat successful compilation as visual correctness. Render every final page and inspect clipping, overflow, missing glyphs, blank pages, captions, formulas, tables, page numbers, and anonymity.

## Preflight

Run:

```text
python scripts/paper_preflight.py --paper <paper.docx|main.tex|main.typ|paper.md> --project <workspace> --registry <optional-result-registry.json> --output <report.json>
python scripts/cumcm_format_lock.py audit --workspace <workspace> --paper <paper.docx> --strict-style --output <format-report.json>
```

The preflight is deliberately conservative: it blocks missing/empty papers, placeholders, broken includes and image references, Typst/LaTeX syntax mixing, duplicate or explicitly marked unknown result IDs, and missing registry evidence. In `RESULT_REGISTRY.json`, a paper-required result should list stable `paper_checks` strings (for example the final displayed value with its unit). This checks expected claims without treating every number or ordinary notation such as `R1` as an internal result ID. The `[[R001]]` form is reserved for explicit source-stage tracing and should not remain visible in the submitted paper. The preflight warns about internal workflow terms, identity metadata, unreferenced figures, and other items that require human judgment. It does not replace mathematical validation, official-rule review, or rendered-page inspection.




