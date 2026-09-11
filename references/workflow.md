# Competition workflow

## 1. Intake and problem selection

Create a one-page comparison for each candidate problem: required outputs, data availability, dominant model families, implementation risk, validation path, writing burden, and team fit. Select by expected completion quality, not perceived sophistication.

For the chosen problem, write a requirement matrix mapping every sub-question to inputs, outputs, constraints, candidate methods, validation, figures/tables, and paper sections.

Before model selection, complete the operational-semantics audit, subproblem dependency graph, method-fit certificate, and assumption traceability defined in `reasoning-quality-gates.md`. The dependency graph must show which earlier definitions, indicators, states, parameters, and results are reused by later questions.

Before committing to one interpretation, run an assumption-sensitivity precheck for every ambiguity that could change the feasible set, objective, data horizon, or deliverable. Record the competing interpretations, a quick discriminating calculation or logic check, the chosen interpretation, and the condition that would reverse it. Use subproblem progression as evidence: added resources or relaxed constraints should normally have a plausible marginal effect; if they do not, re-check the interpretation and implementation.

## 2. Data and evidence

- Keep `raw/` immutable; create cleaned and derived data elsewhere.
- Create a data dictionary with field meaning, unit, type, source, and transformation.
- Detect missing values, duplicates, impossible ranges, inconsistent units, time leakage, sampling bias, and geographic/temporal mismatches.
- Preserve source URLs, access dates, checksums, and licenses where relevant.
- Synthetic or interpolated values must be labeled and justified; never present them as observed data.

## 3. Modeling

Start with a transparent baseline. For every candidate model state: objective, decision variables, assumptions, constraints, estimation procedure, computational cost, failure modes, and why it is suitable.

Reject keyword-triggered model selection. A method is not justified merely because the problem says evaluation, prediction, optimization, or competition. Check the mechanism, data resolution, identifiability, validation path, and simpler alternatives.

Use complexity only when it improves a relevant metric, robustness, interpretability, feasibility, or decision usefulness. Keep rejected models and reasons in the decision log.

## 4. Experiments

Make runs reproducible through scripts, fixed seeds where applicable, explicit parameters, environment information, and saved outputs. Separate exploratory notebooks from final runnable pipelines. Update the experiment log after each decision-changing run.

## 5. Stage handoff contracts

Do not hand off with prose such as "continue from here." Each completed stage records:

- exact input files and their versions or hashes;
- approved interpretation, assumptions, formulas, constraints, and units;
- output files and the command that regenerates them;
- invariants and acceptance checks;
- unresolved risks, rejected alternatives, and reversal conditions;
- the next stage's bounded task and forbidden changes.

Recommended artifact flow:

| From | Durable handoff | Required receiver check |
| --- | --- | --- |
| problem selection | problem map + requirement matrix | every requested deliverable is mapped |
| modeling design | model specification + implementation task table | formulas, units, constraints, baseline, and validation are implementable |
| coding and experiments | result registry + experiment log + figures/data | results rerun; constraints and claims verified |
| visualization | data-figure provenance + editable conceptual-diagram sources | every figure has a purpose, source, caption, and paper location |
| writing | paper source + citation list + result-to-claim map | no invented results; official structure retained |
| preflight | machine-readable findings + rendered PDF/DOCX | hard failures closed; warnings adjudicated |
| independent review | frozen manifest + hashes | reviewer sees only the submission package before benchmark comparison |

Human-only or externally verified actions use `HUMAN_TASKS.md`. The receiving stage must not treat `WAITING_FOR_HUMAN` as complete merely because code, instructions, or a plausible result exists.

## 6. Writing and audit

Draft from verified artifacts. Keep symbols and units consistent. Link every important number, table, and figure to its generating code/output. Run `scripts/paper_preflight.py` on Word, LaTeX, Typst, or Markdown source before visual QA. Complete the requirement matrix, compliance checklist, citation check, anonymity check, archive manifest, and clean-machine rerun before submission.




