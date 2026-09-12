# Claim Registry

Claim ceiling is the supporting gate / review, not this file. Do not upgrade a row without a new gate.

| ID | Question | Claim | Level | Evidence | Gate / review |
|---|---|---|---|---|---|
| Q4-B1 | Q4 | Offline holdout mean T/K is 517.5842931731096 s for TRI25 + ROUTE_ADAPTIVE_V4 on seeds 1000–1099 (endpoint, mixed, 100/100 certified) | feasible_baseline | experiments/q4_efficiency/release_holdout100.json | reviews/stage6-validation-review.md |
| Q4-B2 | Q4 | Relative to HEX37 + ROUTE_INSERT_V3 on the same 100 seeds, mean T/K drops 29.6145%; 97/100 scenes are faster; 3/100 (seeds 1065, 1092, 1093, all N=16) are slower, worst +48.260035145791505 s | feasible_baseline | experiments/q4_efficiency/holdout100_paired.csv; paired_summary.json | reviews/stage6-validation-review.md |
| Q4-B3 | Q4 | TRI25 has a sufficient continuous discovery certificate (max distance 943.0121947375769 m, hull margin 17.74943008678929 m) | feasible_baseline | experiments/q4_efficiency/paired_summary.json `tri25_certificate` | reviews/stage6-validation-review.md |

Blocked until new evidence:
- official-simulator T/K
- per-scene path optimality
- claim levels above `feasible_baseline`
