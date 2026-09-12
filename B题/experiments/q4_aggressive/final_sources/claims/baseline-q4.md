# Baseline — Q4

## Frozen at
- Stage: 6
- Date: 2026-09-12
- Validation review: reviews/stage6-validation-review.md
- Verdict: PASS_WITH_WARNINGS
- Scheme: `TRI25` + `ROUTE_ADAPTIVE_V4` (`adaptive-reception-v4`)

## Primary metrics
| Metric | Value | Source artifact |
|---|---|---|
| mean T/K (s) | 517.5842931731096 | experiments/q4_efficiency/release_holdout100.json |
| cases / full_success | 100 / 100 | experiments/q4_efficiency/release_holdout100.json |
| failed_seeds | [] | experiments/q4_efficiency/release_holdout100.json |
| cover / route | TRI25 / ROUTE_ADAPTIVE_V4 | experiments/q4_efficiency/release_holdout100.json |
| error_mode / sources | endpoint / mixed | experiments/q4_efficiency/release_holdout100.json |
| seed range | 1000–1099 | experiments/q4_efficiency/release_holdout100.meta.json |
| mean T (s) | 6682.781249650514 | experiments/q4_efficiency/release_holdout100.json |
| mean K | 13.24 | experiments/q4_efficiency/release_holdout100.json |
| mean move (m) | 24742.356248252563 | experiments/q4_efficiency/release_holdout100.json |
| p95 T/K (s) | 677.2650412845248 | experiments/q4_efficiency/release_holdout100.json |
| min T/K (s) | 258.13623777185825 | experiments/q4_efficiency/release_holdout100.csv seed 1058 |
| max T/K (s) | 766.7178646948478 | experiments/q4_efficiency/release_holdout100.csv seed 1070 |
| mean n_optical_fallback | 0.04 (4 events) | experiments/q4_efficiency/release_holdout100.json |

Do not substitute the Dev-30 smooth-error mean 489.7928667317867 s (`release30.json`) for the freeze metric.

## Paired bound (not a path-optimum claim)
Against frozen pre-change `HEX37 + ROUTE_INSERT_V3` on the same 100 seeds (`holdout100_paired.csv`, `paired_summary.json`):

- 97/100 lower T/K; 3/100 higher T/K; 0 ties
- Mean T/K 735.3565026536246 → 517.5842931731096 (−29.6145%)
- Worse seeds, all N=16:

| seed | HEX37/V3 T/K (s) | TRI25/V4 T/K (s) | Δ T/K (s) |
|---|---:|---:|---:|
| 1065 | 430.74751880049797 | 437.0079521654748 | +6.260433364976848 |
| 1092 | 319.8855687264751 | 368.14560387226663 | +48.260035145791505 |
| 1093 | 396.2329035893946 | 415.7577328519105 | +19.52482926251588 |

This is an average-efficiency baseline, not a per-scene path-optimum guarantee.

## Claim level
- `feasible_baseline`
- Blocked: `locally_optimal_solution`, `validated_optimum`, `global_optimum`, and any official-simulator T/K

## Scheme constraints recorded at freeze
- N=16 counting certificate is independent of the TRI25 hull certificate.
- `no_signal` is not `d>1000`.
- Practice CLI defaults to TRI25 + ROUTE_ADAPTIVE_V4; module env fallbacks remain `SQUARE81` / `OLD_HEX37`; `bench.py` defaults remain HEX37 + ROUTE_INSERT_V3 + smooth. Reconstruct this baseline only with the explicit command below.
- Official practice did not start (`experiments/q4_efficiency/practice_attempt.json`: `started=false`, `official_results=null`).

## Replay command
```powershell
python experiments/q4_efficiency/bench.py --cover TRI25 --route ROUTE_ADAPTIVE_V4 --error-mode endpoint --seed-start 1000 --cases 100 --output experiments/q4_efficiency/recheck_v4.csv
```

## Cross-question impact (if any)
- Changing Q4 cover, route, or adaptive reception does not rewrite Q1/Q2/Q3 solvers.
- Shared files `src/params.py`, `src/geometry.py`, and `data_preparation/parameters.csv` are in the SHA256 map; editing them can couple Q1–Q3 and must not be treated as Q4-only.

## Reproducibility anchor
- Code commit: not used. Git HEAD `3c144685832cc1df2ef6c84e581094bdd054c417` does not contain the V4 tree.
- Working-tree SHA256: `experiments/q4_efficiency/release_holdout100.meta.json`
- Python: 3.10.11
- Source note: offline bounded-error geometry; not official practice
