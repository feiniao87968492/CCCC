# Workflow

## Current focus
Q4 local exploratory ablation in `experiments/q4_local/`: 16 arms x 400 fresh paired settings, 6400/6400 complete; 5208 sources cleared per arm. Best new local mean is LPC 515.618001 s versus same-cohort frozen V4 537.376003 s; walking -5.343%, probes -3.231%, all five subgroup means improve with 92/400 paired losses. Prior JSO_compact_dopt reruns at 513.488873 s; the LPC-minus-prior interval crosses zero. New local arms retain the frozen global planning rule and radius1950. Prior supporting-material package contains the earlier Q3 254.05 / Q4 529.29 results, not this new cohort. Official-simulator T/K remains empty.

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
- [x] Second Q4 ablation: 960 initial + 200 combination development runs, all complete and event-audited
- [x] Final 28-arm registry tests: 272 passed; primary 11200 traces / 3438321 operations audited; no source drift or frozen hash mismatch
- [x] Independent transfer readiness and development validation: `experiments/q4_transfer/reviews/`, PASS_WITH_WARNINGS
- [x] Independent primary validation: `experiments/q4_transfer/reviews/primary-validation.md`, PASS_WITH_WARNINGS; 50 alternate-geometry trace samples also pass
- [x] Local development: 520 initial + 160 combination runs, all complete/audited; 40 repeated baseline event hashes identical
- [x] Locked local primary: 16 x 400 runs, 200 independent seed blocks; all 2,008,468 physical operations audited, 22 pinned dependencies and frozen hashes verified
- [x] Final local registry/regressions: 290 tests passed; no policy/source drift during primary execution
- [x] Independent local readiness, development and primary reviews: `experiments/q4_local/reviews/`, PASS_WITH_WARNINGS; P/F/M linkage plus bounded mass/optical/statistical reconstruction pass
- [x] Local report retains all 16 arms, 11 component comparisons, subgroups/tails, failed attempts and negative F/M results; final analysis sources and evidence hashes packaged
- Formal baseline adoption is a separate task; prior-round review provider errors are historical, new review service works

## Active blockers
None for delivery of the requested exploratory experiments. Adoption was not requested; if requested later, independent Skepticism and Stage 6 reviews are required. Official-simulator T/K remains claim-blocked.

## Claim ceiling
Q4 frozen baseline: `feasible_baseline` (offline bounded-error geometry). New local experiments: `exploratory_analysis`, no baseline adoption. Official-simulator T/K is blocked.

## Next safe action
Completed requested local ablation delivery in `experiments/q4_local/README.md` and primary400 report/tables, with independent review. Preserve the frozen baseline; any new experimental round should lock tuning on development settings and use fresh paired scenarios. Existing `支撑材料/` and `handoff/` refer to the earlier result package. Baseline adoption remains separate; do not fill 表1 with offline values.

## Memory check
Updated `memory.md`: user's local-strategy preference, persistent per-stop probe budgets, negative-RF retry constraints, LPC subgroup/individual tradeoffs, P attribution, C15 alternative and negative F/M results.

Q3 exploratory ablation completed in `experiments/q3_ablation/`: 4,200 paired
offline runs, 420/420 complete scenes per arm. Evidence ceiling is
`exploratory_analysis`; GREEDY_FAST remains the official mainline.
