# Claim Registry

Claim ceiling is the supporting gate / review, not this file. Do not upgrade a row without a new gate.

| ID | Question | Claim | Level | Evidence | Gate / review |
|---|---|---|---|---|---|
| Q4-B1 | Q4 | Offline holdout mean T/K is 517.5842931731096 s for TRI25 + ROUTE_ADAPTIVE_V4 on seeds 1000–1099 (endpoint, mixed, 100/100 certified) | feasible_baseline | experiments/q4_efficiency/release_holdout100.json | reviews/stage6-validation-review.md |
| Q4-B2 | Q4 | Relative to HEX37 + ROUTE_INSERT_V3 on the same 100 seeds, mean T/K drops 29.6145%; 97/100 scenes are faster; 3/100 (seeds 1065, 1092, 1093, all N=16) are slower, worst +48.260035145791505 s | feasible_baseline | experiments/q4_efficiency/holdout100_paired.csv; paired_summary.json | reviews/stage6-validation-review.md |
| Q4-B3 | Q4 | TRI25 has a sufficient continuous discovery certificate (max distance 943.0121947375769 m, hull margin 17.74943008678929 m) | feasible_baseline | experiments/q4_efficiency/paired_summary.json `tri25_certificate` | reviews/stage6-validation-review.md |
| Q3-E1 | Q3 | Offline 420-scene JSO mean T/K is 254.05321048920862 s, 420/420 certified, paired vs GREEDY_FAST 379.60 s | exploratory_analysis | experiments/q3_ablation/evaluation/summary.csv | experiments/q3_ablation/design.md |
| Q3-E2 | Q3 | Official practice 20 JSO games: 20/20 certified, mean T/K 239.08 s (median 235.52, range 190.39–311.80), unpaired | exploratory_analysis | experiments/q3_simulator/practice_results.md | practice only |
| Q4-E1 | Q4 | Ablation 400: proxy_reuse_early_compact mean T/K 529.2899300477935 s vs same-matrix V4 543.54 s; boundary −3.90% | exploratory_analysis | experiments/q4_ablation/primary400/summary.csv | not adopted |
| Q4-E2 | Q4 | Transfer 400: JSO_compact_dopt mean T/K 513.958406 s vs same-matrix V4 532.172912 s; boundary −0.59% | exploratory_analysis | experiments/q4_transfer/primary400/summary.csv | experiments/q4_transfer/reviews/primary-validation.md |
| Q4-E3 | Q4 | Local 400: LPC mean T/K 515.618001 s vs same-matrix V4 537.376003 s; prior JSO_compact_dopt rerun 513.488873 s | exploratory_analysis | experiments/q4_local/primary400/summary.csv | experiments/q4_local/reviews/primary-validation.md |
| Q4-E4 | Q4 | Aggressive general-350: G15 mean T/K 489.642686 s vs LC 496.926222 and frozen V4 513.190019; previous JSO 488.846688, paired interval vs G15 spans zero | exploratory_analysis | experiments/q4_aggressive/primary_valid400/summary_general.csv | experiments/q4_aggressive/reviews/primary-validation.md |

Blocked until new evidence:
- official-simulator T/K
- per-scene path optimality
- claim levels above `feasible_baseline`
