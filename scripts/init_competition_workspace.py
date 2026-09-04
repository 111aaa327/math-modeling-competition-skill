#!/usr/bin/env python3
"""Create a non-destructive mathematical-modeling competition workspace."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


DIRECTORIES = (
    "00_rules/official",
    "00_rules/templates",
    "01_problem",
    "02_data/raw",
    "02_data/processed",
    "03_src",
    "04_results",
    "05_paper",
    "06_archive",
    "07_review",
    "08_external_skill_review",
    "knowledge",
)


def write_new(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite: {path}")
    path.write_text(content, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", required=True, type=Path)
    parser.add_argument("--competition", default="Modeling Competition")
    args = parser.parse_args()

    root = args.path.expanduser().resolve()
    if root.exists() and any(root.iterdir()):
        raise SystemExit(f"Target exists and is not empty: {root}")
    root.mkdir(parents=True, exist_ok=True)
    for relative in DIRECTORIES:
        (root / relative).mkdir(parents=True, exist_ok=True)

    now = datetime.now().astimezone().isoformat(timespec="seconds")
    write_new(root / "STATUS.md", f"# {args.competition} status\n\n- Workspace created: {now}\n- Phase: preparation\n- Next gate: verify official rules and select a problem.\n")
    write_new(root / "PLAN.md", f"# {args.competition} plan\n\n## Deliverables\n\n- Confirm from official rules.\n\n## Typesetting route\n\n- Word / LaTeX / Typst: undecided; official template takes precedence.\n\n## Workflow\n\n1. Rules and problem selection\n2. Problem map and assumption-sensitivity precheck\n3. Data audit\n4. Baseline and advanced modeling\n5. Reproducible experiments and figures\n6. Paper, preflight, visual QA, and independent review\n")
    write_new(root / "TODO.md", "# Task status\n\n- [ ] Verify official rules and deliverables\n- [ ] Select problem and freeze requirement matrix\n- [ ] Complete assumption-sensitivity precheck\n- [ ] Audit raw data\n- [ ] Approve modeling route and baseline\n- [ ] Run and log reproducible experiments\n- [ ] Register paper-ready results and figures\n- [ ] Draft paper from verified artifacts\n- [ ] Pass machine preflight and visual QA\n- [ ] Freeze package and complete independent review\n")
    write_new(root / "HANDOFFS.md", "# Stage handoffs\n\n| Time | From stage | To stage | Inputs/version | Outputs | Invariants/checks | Open risks | Next action |\n|---|---|---|---|---|---|---|---|\n")
    write_new(root / "DECISIONS.md", "# Decision log\n\nRecord date, decision, alternatives, evidence, owner, and reversal condition.\n")
    write_new(root / "AI_USAGE_LOG.md", "# AI usage log\n\nDo not guess tool/model versions. Log material adopted uses with verification evidence.\n\n| Time | Tool and exact version | Phase and purpose | Prompt/process | Adopted output | Manual changes | Verification evidence | Related files |\n|---|---|---|---|---|---|---|---|\n")
    write_new(root / "EXPERIMENTS.csv", "experiment_id,timestamp,question,objective,dataset_version,code_version,method,parameters,random_seed,metrics,result_artifacts,status,conclusion,verified_by\n")
    write_new(root / "RESULT_REGISTRY.json", json.dumps({"schema_version": 1, "results": []}, ensure_ascii=False, indent=2) + "\n")
    write_new(root / "SUBMISSION_MANIFEST.csv", "relative_path,deliverable_type,required,source_or_generator,sha256,size_bytes,verification_status,notes\n")
    write_new(root / ".gitignore", "__pycache__/\n*.py[cod]\n.venv/\n.env\n~$*\n02_data/processed/cache/\n04_results/tmp/\n")
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())




