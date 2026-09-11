# Reasoning quality gates

Use these gates after the first problem map and before implementation. They prevent a fixed paper format from turning into fixed reasoning or a catalog of fashionable algorithms.

## Operational semantics

For every consequential noun, verb, comparison, and aggregation in the problem, record:

- the operational definition and unit;
- spatial, temporal, and population resolution;
- whether the quantity is observed, derived, assumed, or optimized;
- a competing interpretation and a discriminating check;
- the condition that would reverse the chosen interpretation.

Do not replace the requested object with an easier proxy unless the consequence is quantified.

## Subproblem dependency graph

Draw a directed graph or compact table showing which definitions, indicators, parameters, states, and outputs pass from each subproblem to the next. A later subproblem must reuse earlier artifacts or explicitly explain why the changed conditions invalidate them. Treat an unrelated stack of models as a design defect, not as breadth.

## Method-fit certificate

Before approving a method, state:

1. the problem mechanism and target claim;
2. the data and resolution the method requires;
3. identifiability and assumptions;
4. the baseline and simpler alternative;
5. the validation that can falsify the method;
6. the added value that justifies its complexity.

Do not select AHP, entropy weighting, TOPSIS, grey prediction, genetic algorithms, neural networks, game theory, or any other method merely because a prompt contains words such as evaluation, prediction, optimization, or competition. For game-theoretic models, identify actors, actions, information, incentives, and genuinely conflicting objectives first.

## Assumption traceability

Maintain a table with `assumption | necessity | evidence or rationale | affected equations and outputs | sensitivity or falsification | failure consequence`. Remove unused assumptions. Distinguish a simplifying approximation from a physical fact and an empirical formula from a derived law.

## Result interpretation

Every decisive table or figure must be introduced before it appears and followed by an interpretation that states what changed, compared with what, by how much, why it matters, and what uncertainty remains. A sentence such as "software calculation gives the following result" is not evidence by itself.

## Abstract coverage

For every requested subproblem, the abstract should contain the selected method, the main quantitative result, and the validation or practical meaning when space permits. Keep the abstract self-contained and consistent with the body and result files. Do not place complex formulas, tables, citations, or unsupported innovation claims in it.

## Source basis

These gates distill recurring lessons from CUMCM platform writing guidance and national review commentary. They are quality controls rather than official scoring rules. Current official rules and the exact problem statement remain authoritative.

