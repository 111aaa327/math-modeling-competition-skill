# Validation and reproducibility

Choose checks that can falsify the actual model or claim.

## Interpretation and progression

- Test consequential wording ambiguity before model selection, not after results are polished.
- Compare alternative interpretations with a hand-checkable case or sensitivity run.
- Check expected progression across subproblems: added resources, information, or a relaxed feasible set should not worsen a maximization objective or improve a minimization objective unless another condition changes. An unexpected flat result is a diagnostic signal, not proof of correctness.
- Do not convert useful examples into universal numeric thresholds. Choose convergence tolerance, seed count, simulation budget, and sample size from the claim, variability, computational cost, and required confidence.

## Optimization

Verify feasibility and constraint residuals; compare with a simple heuristic/baseline; inspect bounds and optimality gaps when available; test parameter and scenario sensitivity; explain solver termination and infeasibility handling.

## Forecasting and time series

Use chronological splits or rolling-origin evaluation; prevent future leakage; compare against naive forecasts; report scale-appropriate errors and uncertainty; inspect residual structure and regime sensitivity.

## Classification or regression

Separate train/validation/test data correctly; use grouped or stratified splitting when required; compare baselines; report uncertainty and calibration where relevant; diagnose leakage, imbalance, multicollinearity, and extrapolation.

## Simulation and differential models

Check conservation laws, dimensions, boundary/initial conditions, numerical convergence, timestep/grid sensitivity, stochastic seed variability, and limiting cases with known behavior.

## Evaluation and ranking

Justify normalization, weights, and directionality; test weight sensitivity and rank stability; check redundancy/correlation among indicators; compare at least one defensible alternative when rankings drive decisions.

## Network, spatial, and clustering models

Validate graph construction or distance definitions; test resolution/parameter sensitivity; inspect stability across seeds/samples; use domain-grounded interpretation rather than relying on an internal score alone.

## Reproducibility gate

A final run must start from documented inputs and regenerate all submission-critical tables and figures. Record environment, dependencies, seeds, commands, elapsed time, and expected outputs. No manual spreadsheet edits may be the sole source of a reported result.

Classify audit findings as hard failures or warnings. Missing required deliverables, broken references, infeasible decisions, result contradictions, failed compilation when the compiler is available, identity leakage, and non-reproducible headline results are hard failures. Style preferences and unused backup artifacts are warnings unless official rules make them mandatory.




