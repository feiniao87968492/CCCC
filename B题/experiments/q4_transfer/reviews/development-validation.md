# Q4 transfer — independent development validation

## Reviewed scope
- `B题/experiments/q4_transfer/reviews/implementation-readiness.md`, Findings F1–F6.
- `B题/experiments/q4_transfer/q4_transfer_policies.py`, `run_transfer.py`, `test_transfer.py`, and `design.md`.
- `B题/experiments/q4_transfer/dev40/manifest.json`, `completion.json`, `scenarios.json`, `results.csv`, `provenance-correction.json`, all 960 compressed event logs, and the 22-file `source_snapshot/` hash map.
- `B题/experiments/q4_ablation/q4_ablation_policies.py` and `run_ablation.py`; frozen Q4 runner/adaptive/localize/state/certificate code inspected in the preceding readiness review.
- `B题/tests/test_q4_regressions.py`, `B题/tests/test_q4_geomsim.py`, and `B题/experiments/q4_efficiency/bench.py::event_metrics`.
- `B题/memory.md` and previously inspected `B题/claims/baseline-q4.md`.

The reviewed result is the initial 24-arm development batch, with 30 mixed endpoint and 10 outward boundary endpoint settings, 30 seed blocks, and 494 sources per arm. Read-only computations independently checked row coverage, hashes, event charging, S probability gates and O version/cap events. No simulation batch or pytest run was started by this reviewer. The main agent's reported 268 passing tests are therefore not independently rerun evidence. New combinations and the 400-setting primary experiment are outside this result review.

## Findings

### F1 — S's Boolean gate and accounting match the declared transfer
- Type: readiness-F1-implementation-check
- Severity: INFO
- Evidence reference: `q4_transfer_policies.py::_useful/_supplement/_probe_detected_at_v4/_do_v3_action`; `dev40/events/`; `dev40/results.csv`.
- Recommended action: Retain the admission predicates and report S's measured walking/probing tradeoff rather than claiming that S necessarily reduces both components.

The implementation requires reception probability at least the configured gate and either 12-degree parallax or half the latest positive-bearing range; it additionally rejects repeated sites within 1 m, radius <=40 m, excessive distance, and available adequate O estimates. Supplementation is recursion guarded and limited to detected channels. The 4,776 logged S events have no probability-threshold violation; the lowest admitted probability is 0.5013393562 in the 0.5 arm. This check validates logged probabilities and static Boolean structure, not calibration of the approximate RF posterior. S also replaces V4's cover-stop expected-gain gate, so its effect is not solely adding sensing at new stops. S averages 316.15 measurements versus baseline 312.60, while mean walking time falls from 4943.30 to 4835.41 s.

### F2 — O's active execution respects positive versions and its two-trial cap
- Type: readiness-F2-implementation-check
- Severity: INFO
- Evidence reference: `q4_transfer_policies.py::line_estimate/_positive_version/_optimistic_available/_adaptive_task/_do_v3_action`; `dev40/events/`; `test_transfer.py::test_optimistic_clear_failure_forces_new_positive_before_retry`.
- Recommended action: Preserve this O-only speculative path in the adaptive executor and include positive-version/cap checks in the primary event audit.

The implemented criterion is `cond(A)<=30`, where A contains bearing normals, not the squared normal-equation matrix. Estimates require at least two positive directions, legal coordinates, and membership in the convex feasible polygon; the radius threshold remains heuristic. In O-enabled `_adaptive_task`, inherited noncertified center trials are replaced, not appended. Across all 2,479 optimistic-attempt events, the maximum is two per scene/channel; every logged version equals the number of prior positive direction/near observations, and no version is reused. `_try_localize` remains an inherited helper without the O override, but it is not invoked by the production adaptive loop used in this batch. The revised sparse-shadow test now exercises `_adaptive_task`/`_do_v3_action` and full optical fallback, addressing the initial helper-path test limitation. These observations do not authorize a future executor to call the unguarded helper while claiming the same O cap.

### F3 — Recovery and complete fallback remain available; optical2 was inactive
- Type: readiness-F3-completion-check
- Severity: WARNING
- Evidence reference: `q4_transfer_policies.py::_recovery_pair/_refinement_points/_adaptive_task`; inherited `q4_runner.py::_optical_fallback`; `dev40/results.csv`; `test_transfer.py`, boundary and sparse-shadow tests.
- Recommended action: Keep the optical fallback uncapped, distinguish a candidate proposal from an executed action in the report, and identify optical2 as an inactive development arm.

Recovery retains the nearest-positive-projection bound, a bracket wide enough for the bearing wedge, and affine vertex distance dominance relative to the last receiving site. After one negative endpoint, the other fresh endpoint is reconstructed at the front of the list. Aligned/D-optimal reordering restores the baseline one-bearing bracket after heuristic ranking. Dedicated actions increment the inherited eight-measure budget, then choose the entire finite optical cover. Insertions stop deferring coverage when no eligible detour exists, and pending tasks remain eligible after coverage is done. There is no observed completion failure, but the global 800-iteration guard remains a failure boundary rather than a universal termination proof. `optical2` recorded zero early-optical proposals and exactly the baseline development T/K; `optical4` recorded 43 proposals, which are generated during replanning and are not necessarily 43 executed optical actions.

### F4 — Provenance is reconstructible, with an explicit comparator metadata correction
- Type: readiness-F4-provenance-check
- Severity: WARNING
- Evidence reference: `dev40/manifest.json`, `completion.json`, `source_snapshot/`, `provenance-correction.json`; `run_transfer.py::main`; `q4_transfer_policies.py::make_runner`.
- Recommended action: Carry the corrected effective comparator configuration into all new manifests and audit the next source snapshot independently of this development snapshot.

All 22 snapshotted file hashes match the original manifest; all 960 event hashes match the CSV, and the completion record reports no source change during execution. Current policy/design files differ from the development snapshot because combinations and documentation were added after completion; the old snapshot must remain the anchor for these 960 rows. The original `previous_best` manifest incorrectly described tour/no-reuse/80 m settings, although the actual snapshotted factory delegated to `proxy_reuse_early_compact` (center/reuse/160 m, radius 1900). The additive correction states those effective settings without rewriting the original manifest. This is a metadata defect, not evidence of a wrong executed comparator. The exact baseline arm constructs `Q4Runner` with explicit V4 route and 1950 m TRI25 context. Multiprocessing isolates cover globals. Geometries are continuously certified by the inherited context before execution; failures cannot silently select another geometry.

### F5 — The development table contradicts a blanket JSO transfer benefit
- Type: readiness-F5-mechanism-evidence
- Severity: WARNING
- Evidence reference: `dev40/results.csv`, paired by `scene_id`; `q4_transfer_policies.py::VARIANTS`; `design.md`, Development selection and primary lock.
- Recommended action: Publish the complete development matrix and retain its losing arms in the primary experiment; describe subsequent combinations as development-selected hypotheses.

All 960 rows are unique arm/scene pairs; each arm has 40/40 complete scenes and 494/494 cleared sources. Independently recomputed examples are below. Deltas are mean(T/K) against the paired frozen-V4 rerun, in seconds per source.

| Arm | Mean T/K | Overall delta | Outward-boundary delta |
|---|---:|---:|---:|
| baseline | 567.771 | 0.000 | 0.000 |
| JSO_compact | 560.702 | -7.069 | +19.013 |
| S | 561.455 | -6.316 | -5.220 |
| SO | 563.253 | -4.518 | -9.710 |
| doptimal | 564.707 | -3.064 | -2.203 |
| previous_best | 565.452 | -2.319 | +37.209 |
| JSO | 568.655 | +0.884 | +17.172 |
| J | 573.689 | +5.918 | +29.071 |
| insert80 | 623.052 | +55.281 | +69.408 |

Q3's numerical score is not a Q4 comparator. In this development set, unmodified JSO is slightly slower overall, its compact variant's best combined mean hides a boundary regression, and all insertion caps lose. These counterexamples justify testing S/D-optimal combinations but do not establish that those combinations will improve.

### F6 — Timing reconciles; development selection is not primary validation
- Type: readiness-F6-accounting-and-selection
- Severity: WARNING
- Evidence reference: all `dev40/events/`, `results.csv`, `scenarios.json`; `tests/test_q4_regressions.py::NoisyGeomSim`; `run_transfer.py::settings`; `design.md`, Development selection and primary lock.
- Recommended action: Lock the new registry before primary evaluation and independently validate observation truth, clear certificates, per-channel absence and blocked bootstrap statistics on the primary data.

The row-level accounting residual is at most 5.46e-12 s. An independent event accumulator over all 362,863 logged events used movement/5, 5 s per measurement, 1 s per receiver-channel change, 3 s per clear and 2 s per successful clear. With the simulator's documented initial receiver channel 1, it matches every action timestamp and final row T within 1.82e-12 s. The initial audit assumption of an unset channel produced a constant 1 s offset; reading the simulator initialization resolved it, with no implementation change. Failed clears and receiver switches are therefore included in these development totals. Event hashes/charging and success flags alone do not independently prove that every observation and absence certificate is physically valid; the main agent's separate event audit must supply that evidence. Development has 40 settings but only 30 seed blocks; the planned primary has 400 settings and 200 seed blocks. The reviewed code constructs the declared fresh cohort. The four new combinations have no performance evidence in this review and must not be presented as established improvements.

## Blocking risks
No unresolved algorithm defect was identified that blocks running the additional user-authorized exploratory combinations or the locked primary experiment. This is a bounded development review, not a final result acceptance or gate clearance. Full physical-observation/absence verification, the additional-combination checks, and primary validation remain required before stronger result claims. A failed certificate or source-completion audit would become a blocking defect requiring a recorded method/evidence rollback.

## Non-blocking warnings

### W1 — The eight-way factorial has incremental, coupled meanings
- Type: causal-interpretation
- Severity: WARNING
- Evidence reference: Findings F1–F2 and F5; `implementation-readiness.md`, F5.
- Recommended action: Define J as center-proxy task ordering, S as changed cover-stop gating plus supplemental detected-channel sensing, and O as replacing center trials with bounded least-squares estimates.

### W2 — Verification commands must be linked to the code version they tested
- Type: test-provenance
- Severity: WARNING
- Evidence reference: `test_transfer.py`; `dev40/manifest.json::sha256`; Findings F2 and F4.
- Recommended action: Record the next test command/result and include `test_transfer.py` plus the final event-audit code in the next source snapshot or a separate verification manifest.

The original development snapshot does not include `test_transfer.py`; this review does not attribute the reported 268-test result to the later revised test or four new registry entries.

## Required follow-up
- Preserve `dev40/manifest.json`, `source_snapshot/`, and `provenance-correction.json`; use corrected effective configuration fields in the next `experiments/q4_transfer/` run manifest (F4).
- Complete and retain an independent physical event audit under `experiments/q4_transfer/`, covering source/observation validity, actual clear geometry, per-channel absence, total cost and O cap/version (F1–F3, F6).
- Record verification of the four new combinations and the revised adaptive fallback test under `experiments/q4_transfer/` before freezing the primary registry; include the verification sources in the provenance record (W2).
- Publish all initial development rows and subgroup deltas in the `experiments/q4_transfer/` report, including inactive optical2 and the boundary losses of JSO_compact/previous_best (F3, F5).
- For `experiments/q4_transfer/` primary summaries, preserve seed-block dependence, setting weights, N/source/error strata, failures, tails, and multiple-selection limits; request a separate final validation review (F6).
- Memory check: recommend recording the initial receiver channel 1, development-inactive optical2, and development JSO/compact boundary counterexamples in `B题/memory.md`; this reviewer did not edit it.

## Reviewer recommendation
The initial development evidence supports continued isolated experiments: the actual adaptive O/S mechanisms match their core contracts, traces are intact, time accounting independently reconciles, and all paired development runs report completion. The metadata correction is transparent and the observed losing/boundary arms must remain visible. No algorithm blocker was found for the planned next run. This verdict does not approve baseline replacement, certify every physical event, or substitute for the final 400-setting validation.

Verdict: PASS_WITH_WARNINGS

## Required reads referenced
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/stage-6-independent-validation.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/subagent-validation-paper.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-markdown-audit.md` (read in preceding readiness review)
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-human-confirmation.md` (preceding review)
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-memory-update.md` (preceding review)
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-subagent-delegation.md` (preceding review)
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-readiness-gate.md` (preceding review)
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-rollback.md` (preceding review)
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-output-schema.md` (preceding review)
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-self-discipline-checklist.md` (preceding review)
- All project artifacts listed in Reviewed scope.

## Confidence
medium — actual source, all development row/event hashes, O versions and timestamps were independently checked, while physical certificate auditing and fresh primary outcomes remain outside this completed slice.

## Forbidden-behavior self-check
- [OK] Did not confirm user decisions
- [OK] Did not clear blockers
- [OK] Did not mark stages or rounds complete
- [OK] Did not increase claim level on behalf of the main agent
- [OK] Did not invoke another subagent
- [OK] Did not write or edit project files outside the review output
- [OK] Did not write claims/baseline-snapshot.md
- [OK] Did not export when the final evidence gate has not passed
- [OK] Did not modify implementation/data or start simulation batches
