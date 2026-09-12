# Workflow

## Current focus
Latest unsubmitted Q3/Q4 results packaged as supporting materials: Q3 JSO mean T/K 254.05 s (420/420); Q4 `proxy_reuse_early_compact` 529.29 s (400/400). Paper chapters were not edited. Official-simulator T/K remains empty.

## Checklist
- [x] Q4 V4 offline holdout artifacts exist (`experiments/q4_efficiency/release_holdout100.*`)
- [x] Independent CSV/JSON/hash replay (2026-09-12): 0 hash mismatches, mean T/K 517.5842931731096 s, 100/100 certified
- [x] `pytest tests`: 225 passed
- [x] `data/validation/validation-report.md`
- [x] `reviews/stage6-validation-review.md` — Verdict: PASS_WITH_WARNINGS
- [x] `claims/baseline-q4.md` + index `claims/baseline-snapshot.md` (Q1–Q3 not frozen)
- [x] `gates/stage6-q4-validation.md`
- Q1 / Q2 / Q3 per-question baselines: not in this slice
- [x] Q4 descriptive sensitivity: `data/sensitivity/sensitivity-report.md`; matched stress results in `experiments/q4_ablation/primary400/strata.csv`
- [x] User-authorized exploratory ablation: 20 arms x 400 scenarios, 8000/8000 certified; 252 tests pass
- [x] All 8000 event traces audited; repaired harness reproduces 40 event hashes exactly
- Formal improvement review/adoption remains incomplete (provider 403 insufficient balance)

## Active blockers
None for delivery of the requested exploratory experiments. Adoption was not requested; if requested later, independent Skepticism and Stage 6 reviews are required. Official-simulator T/K remains claim-blocked.

## Claim ceiling
Q4: `feasible_baseline` (offline bounded-error geometry). Official-simulator T/K is blocked.

## Next safe action
Use `支撑材料/` or `handoff/CUMCM2026-B-Q3-Q4-支撑材料-20260912.zip` for code/result delivery. Do not fill 表1. Adopting the 529 s Q4 arm as frozen baseline still needs independent review.

## Memory check
Updated `memory.md`: user wants Q3 254 / Q4 529 organized as supporting materials, not paper-section edits.

Q3 exploratory ablation completed in `experiments/q3_ablation/`: 4,200 paired
offline runs, 420/420 complete scenes per arm. Evidence ceiling is
`exploratory_analysis`; GREEDY_FAST remains the official mainline.
