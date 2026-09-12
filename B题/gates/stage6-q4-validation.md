# Gate — Stage 6 Q4 validation

## Gate result
PASS_WITH_WARNINGS

## Intended claim level
feasible_baseline (Q4 improvement-loop freeze)

## Supported claim level
feasible_baseline

## Checks
- Independent CSV/JSON replay of holdout mean T/K 517.5842931731096 s: pass (`data/validation/validation-report.md`)
- Validation Reviewer: PASS_WITH_WARNINGS (`reviews/stage6-validation-review.md`)
- Baseline freeze written: `claims/baseline-q4.md`, index `claims/baseline-snapshot.md`
- Official simulator: fail / blocked
- Git commit as V4 anchor: fail; SHA256 manifest used instead

## Allowed outputs
- Q4 offline holdout metrics at `feasible_baseline`
- Per-question baseline freeze for Q4
- Later improvement rounds comparing against `claims/baseline-q4.md`

## Blocked claims
- official-simulator T/K
- per-scene path optimality
- locally_optimal_solution / validated_optimum / global_optimum
- using Dev-30 smooth-error 489.7928667317867 s as the freeze metric

## Required branches
none for this freeze

## Required decision
none; user requested this Q4 scheme as baseline on 2026-09-12
