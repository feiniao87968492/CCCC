# Baseline Snapshot Index

## Frozen at
- Stage: 6
- Date: 2026-09-12
- Validation review: reviews/stage6-validation-review.md
- Verdict: PASS_WITH_WARNINGS (Q4 only)

## Per-question baselines
| Question | Per-question file | Primary metric | Claim level |
|---|---|---|---|
| Q1 | not frozen | — | — |
| Q2 | not frozen | — | — |
| Q3 | not frozen | — | — |
| Q4 | claims/baseline-q4.md | mean T/K 517.5842931731096 s (holdout 1000–1099, endpoint, mixed) | feasible_baseline |

Do not duplicate Q4 metric rows here. Q1–Q3 have no Stage 6 PASS in this freeze; do not invent their metrics.

## Cross-question coupling
- Q4 `TRI25` / `ROUTE_ADAPTIVE_V4` does not consume Q3 greedy paths or Q1/Q2 localization outputs.
- Shared inputs that can move other questions if edited: `src/params.py`, `src/geometry.py`, `data_preparation/parameters.csv` (SHA256 frozen with Q4).

## Reproducibility anchor
- Code commit: not used (HEAD `3c144685` is not the V4 tree)
- Input / solver hashes: `experiments/q4_efficiency/release_holdout100.meta.json`
- Random seed: holdout `seed_start=1000`, `cases=100`
- Official simulator: blocked (`experiments/q4_efficiency/practice_attempt.json`)
