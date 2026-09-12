# Corrected aggressive experiment verification

## Valid development

- dev_valid40: 16 x 40 = 640 runs; all clear/certify; 200982 physical
  operations replayed; maximum timing residual 9.095e-13 seconds.
- dev_combinations40: 10 x 40 = 400 runs; all clear/certify; 125146 physical
  operations replayed; same timing residual bound.
- All 280 repeated control/component event hashes match exactly between
  development batches. No dependencies changed during either batch.
- Both audits verify all 13 frozen baseline source hashes, without mismatch.
- Current aggressive behavior tests: 39 passed, including R2/R4 boundary and
  priority rules, H conditioning/version caps, N+G two callbacks at one stop,
  and complete observation-only execution for all15 new single/combined arms.
- Broad command: `python -m pytest tests experiments/q4_ablation/test_ablation.py experiments/q4_transfer/test_transfer.py experiments/q4_local/test_local.py experiments/q4_aggressive/test_aggressive.py -q`
- Broad result: 328 passed, 1 failed in 53.02s. Existing Q3 documentation
  replay test `test_q3_greedy_fast_practice_341_10_of_10` still expects the old
  GREEDY_FAST 341 table row, removed by concurrent Q3 documentation updates.
  Q3 files were not reverted. This is not reported as an all-suite pass.

## Valid primary

- primary_valid400: 19 x 400 = 7600 runs; every arm clears5275/5275 sources
  and completes certification. 350 general settings /4611 sources and50
  boundary settings /664 sources,200 independent seed blocks.
- Full automated audit:2334497 physical operations, no failure, maximum timing
  residual1.819e-12 s;32 start dependencies intact and no in-run source drift.
- Frozen13 baseline files still match. Primary used20 workers and completed
  in1781.689 s; this computation time is separate from physical T/K.
- After primary completion final table rendering was adjusted to highlight
  each displayed cohort's minimum, with an explicit legend. Statistical values
  and policy/configuration remain unchanged. Original summary script is preserved
  in the run-start snapshot; final analysis sources are separately packaged.
- Final prose replaces "independent boundary group" with "separately reported
  boundary group" and explicitly states shared seeds; no statistical calculation
  changes. Independent review source records these exact reporting edits.
- Visual inspection: general/all/stress tables display all19 arms with legible
  headers and units; totals4611/5275/664 sources agree with their respective
  cohorts. Green selects the minimum within that table; primary ranking is
  still general. The displayed cohorts' CSV hashes match figure metadata.
- Independent reviewer scoring sample passes313 traces, including every186
  observed N activation; full B candidate selection checked422 times and G
  pending-channel selection1681 times. Independent primary matrix/statistical
  audit passes and reproduces168 control/interaction comparison rows.

## Evidence boundaries

The early invalid batches are preserved and excluded; see invalid-runs.md.
Tests validate behavior; source snapshots bind each actual batch. Added tests
and combination registrations after initial development do not modify its
immutable snapshots. Independent development and primary reviews are
PASS_WITH_WARNINGS; combined with full event replay they support the final
offline exploratory conclusions, without baseline adoption or official score.
