# Memory

## Rules

- Q4 improvement comparisons must use the frozen per-question baseline, not the previous round and not the 30-seed smooth-error training mean.
- Q4 `no_signal` must not be read as `d>1000`. Counting certificate (N=16) is independent of the geometric cover certificate.
- Q4 ablation ranking must include paired per-scene deltas, subgroup results, p95 and worst regression; success-only averages are insufficient.
- Unknown-channel TRI25 scans remain mandatory even when detected-channel probes are suppressed.

## Pitfalls

- Git HEAD is not a reproducibility anchor while TRI25/V4 files are uncommitted. Freeze working-tree SHA256 from `experiments/q4_efficiency/release_holdout100.meta.json`.
- Practice entry defaults to TRI25 + ROUTE_ADAPTIVE_V4, but module env fallbacks remain `SQUARE81` / `OLD_HEX37`. Offline benches must pass `--cover` / `--route` explicitly.
- Holdout mean T/K is an average: 3/100 paired scenes are slower (worst +48.26 s/source). Do not claim per-scene path optimality.
- A generic experiment module named `policies.py` collides with Q3 ablation imports; use a Q4-specific module name.

## Counterexamples

- Holdout seeds 1065, 1092, 1093 (all N=16) have higher T/K under TRI25/V4 than HEX37/V3.

## Q3 ablation rules

- Rank only complete scenes; failed clears and all measurement charges remain in T.
- Compact seven-station covers require separate station identity and per-channel no-signal evidence.
- Screenshot aggregates do not identify reproducible scenes and cannot be claimed as reproduced.

## Q3 ablation counterexample

- In the synthetic 420-scene matrix, JSO_ALLSCAN reduced movement but increased probing to 353.25 measurements/run and had higher mean T/K than JSO.
- In the 8000-run primary Q4 matrix, nearest-only, finish-source and every-stop strategies increased mean T/K despite 100% completion.
- The best mean candidate in that matrix worsened boundary/outward minimum-radius T/K by 3.90%; aggregate gains do not imply stress robustness.

## User Preferences

- 2026-09-12: user asked to inspect the Q4 517 s T/K scheme and freeze it as the Q4 baseline.
- 2026-09-12: user requested aggressive Q3 ablations targeting walking time and probe count.
- 2026-09-12: user requested large matched Q4 ablations focused on walking time and probe count, including aggressive strategies and screenshot-style tables.
- 2026-09-12: user asked to organize latest unsubmitted Q3/Q4 results as supporting materials, not paper chapters; headline numbers are Q3 JSO ~254 s and Q4 ~529 s.
