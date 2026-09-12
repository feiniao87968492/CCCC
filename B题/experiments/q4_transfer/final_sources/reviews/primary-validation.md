# Q4 transfer — independent primary validation

## Reviewed scope
- `experiments/q4_transfer/design.md`, `q4_transfer_policies.py`, `run_transfer.py`, `test_transfer.py`, `README.md`, and `verification.json`.
- `experiments/q4_transfer/reviews/implementation-readiness.md` and `development-validation.md`.
- `experiments/q4_transfer/dev_combinations40/`: manifest, completion, scenarios, all 200 result rows, source hashes, summary, strata and automated audit.
- `experiments/q4_transfer/primary400/`: manifest, completion, scenarios, all 11,200 result rows, 22-file source snapshot, summary, strata, source-count strata, report, automated audit and mechanism records.
- All primary logs for O-enabled or S-enabled arms, for independent positive-version/cap and reception-threshold checks; a fixed 50-trace geometry sample defined below.
- `experiments/q4_transfer/audit_transfer.py`, `summary_transfer.py`, and inherited `experiments/q4_ablation/summarize.py`.
- Frozen Q4 source, policy, simulator and evidence anchors inspected in the preceding reviews, including `claims/baseline-q4.md`, `memory.md`, and `experiments/q4_efficiency/release_holdout100.meta.json`.

All project-relative paths in this document are under `B题/`. This review was completed only after primary `completion.json` and `audit.json` existed. No policy/simulator or test suite was run by the reviewer. Reviewer writes are limited to this review, `reviews/sample_geometry_audit.py`, and `reviews/sample-geometry-audit.json`.

## Findings

### F1 — The full primary matrix and frozen comparator are reconstructible
- Type: reproducibility-and-pairing
- Severity: INFO
- Evidence reference: `primary400/manifest.json`, `completion.json`, `scenarios.json`, `results.csv`, `source_snapshot/`; `dev_combinations40/completion.json` and `audit.json`.
- Recommended action: Preserve these artifacts and use the new cohort's paired baseline for all reported primary deltas.

The final registry contains all 28 declared arms. Primary rows comprise 11,200 unique arm/setting pairs, 400 settings per arm, and 5,187 sources per arm; every row reports completed source clearing and certification. The setting composition is exactly 200 mixed endpoint plus 50 each of directional endpoint, omni endpoint, outward-boundary endpoint and mixed smooth, with 200 distinct seed blocks. Each of the 22 snapshot files matches its manifest hash, the frozen 13-file source map has no mismatch, and completion/audit report no source drift during or after the primary run. `baseline` constructs the frozen Q4Runner with explicit V4 route and radius-1950 TRI25. `previous_best` now correctly records center routing, reuse, 160 m early clearing and radius 1900, matching its actual delegated runner. The extra development run has 200 unique complete rows on the original 40 settings and an automated physical audit PASS; its four new combinations are all retained in primary regardless of development ranking.

### F2 — O/S action contracts survive the full primary execution
- Type: mechanism-validation
- Severity: INFO
- Evidence reference: `q4_transfer_policies.py`, `_adaptive_task`, `_do_v3_action`, `_useful`, `_supplement`; all relevant `primary400/events/`; `primary400/mechanisms.csv`.
- Recommended action: Keep the incremental factor definitions and explicitly distinguish dedicated refinement, S supplementation and optical clearing in explanations.

Independent event parsing found 35,408 O attempts and 78,317 S probes. No O channel exceeded two attempts, repeated a positive-observation version, or used a version inconsistent with prior positive direction/near readings; negative-only readings did not reset the counter. All logged S probabilities met their arm's gate, and every S-probed channel had prior positive evidence. Static code preserves `probability >= gate AND (parallax >=12 degrees OR range halves)`, repeated-site suppression and recursion guarding. The full audit additionally pairs mechanism records with subsequent actions. These checks do not interpret the approximate RF posterior as a reception guarantee. O-enabled adaptive execution replaces inherited noncertified center trials; the unoverridden legacy `_try_localize` helper is not the executed primary path. The finite full optical fallback remains reachable after the dedicated eight-measure cap, which does not count S supplemental measurements.

### F3 — Physical events and a separate geometric reconstruction support feasibility
- Type: geometry-and-cost-evidence
- Severity: INFO
- Evidence reference: `primary400/audit.json`; `audit_transfer.py`; `reviews/sample_geometry_audit.py`; `reviews/sample-geometry-audit.json`.
- Recommended action: Retain both the complete automated audit and the separately implemented geometry sample, with their distinct coverage limits.

The main-agent automated audit checks all 3,438,321 measure/clear operations against scenario truth, legal coordinates, bounded bearing error, reception and clear outcomes, costs, per-channel absent-source cover evidence or the observed-16 certificate, and scenario/event hashes. It reports PASS, no failed runs and maximum event-time residual 1.82e-12 s. Its script hash and result-file hash match the inspected code and data. This reviewer inspected that audit and independently checked mechanism events and result/statistic consistency; the all-operation physical replay was not rerun separately.

The independent geometric sample uses the first two seeds in each of five source/error strata and five preselected arms: O, JSO_r160, SO_doptimal, short_clear and S_dopt_short. These are 50 traces on 10 settings sharing two seed blocks, not a random statistical sample. It reconstructs positive halfplanes independently and uses a Chebyshev-center linear program plus SciPy HalfspaceIntersection instead of the production polygon clipper. All 2,567 positive-truth containment checks, 229 O least-squares/feasible-region checks and 634 certified-clear vertex checks pass. O coordinate discrepancy is zero; the largest reconstructed certified vertex distance is 19.99999000000038 m. This supports the actual sampled shifted-clear geometry and O estimates, while leaving unobserved numerical degeneracies outside the sample claim. The radius-1900 cover has valid continuous bounds but a smaller hull margin, 2.074857 m versus baseline 17.749430 m; further shrinking cannot be justified by this result alone.

### F4 — The best combined mean improves both requested costs, with a boundary loss
- Type: paired-result-and-subgroup
- Severity: WARNING
- Evidence reference: `primary400/results.csv`, `summary.csv`, `strata.csv`, `by_source_count.csv`, `report.md`.
- Recommended action: State the overall average gain with its boundary regression and per-scene losses, and show the alternative S/D-optimal/short-clear tradeoff when discussing robustness.

Independent aggregation agrees with the reported lowest combined mean, `JSO_compact_dopt`:

| Metric | Frozen V4 rerun | JSO_compact_dopt |
|---|---:|---:|
| Mean T/K, s/source | 532.172912 | 513.958406 |
| Mean total time, s/scene | 6679.620119 | 6447.019002 |
| Mean walking time, s/scene | 4890.420119 | 4675.126502 |
| Mean measurements/scene | 289.3425 | 285.5775 |
| Mean discovery/refinement measures | 254.6700 / 34.6725 | 256.2875 / 29.2900 |
| p95 T/K, s/source | 702.111577 | 681.684821 |

The measured reductions are 3.422667% in mean T/K, 4.402354% in walking and 1.301226% in total probes. Discovery probes increase while refinement probes fall, so the total reduction must not be attributed to fewer mandatory discovery scans. The arm wins 286 settings and loses 114, with worst regression +132.802307 s/source at `omni_endpoint_30035`. All N=10–16 aggregate strata improve, but boundary/outward settings worsen by +3.541421 s/source (+0.586305%). The 200 mixed-endpoint settings improve by 3.871950%; directional, omni and mixed-smooth means also improve. These are separate subgroup facts, not a per-scene guarantee. `S_dopt_short` improves all five subgroup means, including boundary by 3.104175%, but has a smaller combined T/K gain of 1.910223% and 2.004545% more probes. The existing report exposes the selected arm's boundary regression.

### F5 — The intervals support improvement over baseline, not superiority over every candidate
- Type: statistical-selection-limit
- Severity: WARNING
- Evidence reference: `experiments/q4_ablation/summarize.py::uncertainty`; `primary400/summary.csv`; `summary_transfer.py`; independently recomputed primary seed arrays.
- Recommended action: Describe JSO_compact_dopt as the lowest observed mean in this matrix; do not claim the D-optimal addition is established as better than JSO_compact.

The implementation resamples whole seed blocks, sums their setting deltas, and divides by resampled setting counts, preserving the setting-weighted estimand rather than giving seed means equal weight. Independent array calculations reproduce every point delta within 3.56e-15 s, every 5,000-resample interval endpoint within 2.14e-14 s, and Holm-adjusted p-values exactly. The selected arm's mean paired delta is -18.214506 s/source, with marginal 95% block-bootstrap interval [-21.964933, -14.503017]. Its Holm-adjusted block sign-flip p-value is approximately 0.0027, under the stated block sign-symmetry assumption. These marginal intervals do not constitute simultaneous uncertainty bands or a unique-winner proof.

In a separate descriptive comparison, adding D-optimal to JSO_compact changes mean T/K by only -1.224693 s/source; the same block resampling yields [-3.591462, +1.219008], crossing zero. Thus evidence for improvement against frozen V4 is stronger than evidence that the two leading combinations differ. The combination parameters were chosen on development and locked before primary, but identifying the lowest of 28 primary means still entails selection. D-optimal alone is nearly unchanged in mean T/K (-0.044719 s/source; interval includes zero) despite a small walking reduction and more probes. No optimization or universal generalization claim follows.

### F6 — Negative and inactive arms remain informative, within offline scope
- Type: counterevidence-and-claim-boundary
- Severity: WARNING
- Evidence reference: `primary400/summary.csv`, `mechanisms.csv`, `report.md`; `README.md`; `verification.json`; `claims/baseline-q4.md`.
- Recommended action: Keep the full 28-arm table, retain failing-efficiency/inactive findings, and label all achievements as finite offline exploratory comparisons.

All insertion caps worsen primary mean T/K: +49.496, +40.696 and +35.645 s/source for 80/200/400 m; bracket recovery worsens it by +13.374 s/source. Optical2 has zero early proposals and remains identical to baseline in the measured statistics, so it supplies no evidence of an active improvement. Optical4 has 476 early proposals but 490 total optical invocations; those counts represent different events and must not be equated. Its mean gain is small. Q3's 254.053 s/source and Q4's old frozen 517.584 s/source belong to different cohorts; the report uses the correct new 532.173 s/source paired baseline. The reviewed verification record reports 272 passing tests, zero failed, for the final registry and frozen tests, including the revised adaptive-path shadow test. The reviewer inspected the test implementation and record but did not rerun that suite. No frozen entrypoint or baseline artifact was replaced.

## Blocking risks
No unresolved blocking defect was identified for reporting this finite offline experiment at the stated exploratory level. This review does not clear a main-agent gate, authorize baseline replacement, or validate official-simulator/optimality claims. The boundary regression, marginal intervals, near-tie of the leading candidates and limited independent geometry sample are explicit limitations rather than omitted evidence. A claim of uniform improvement, a uniquely superior D-optimal combination, or a global/official optimum would exceed the reviewed evidence.

## Non-blocking warnings

### W1 — Verification sources are outside the simulation snapshot
- Type: provenance-scope
- Severity: WARNING
- Evidence reference: `primary400/manifest.json::sha256`; `verification.json`; `test_transfer.py`; `primary400/audit.json`.
- Recommended action: Preserve test/audit/summary files with final hashes when packaging the evidence, noting that the simulation manifest pins 22 dependencies rather than every subsequent reporting file.

The automated audit is already bound to its script hash and result hash; the reviewer geometry JSON is similarly bound. The final test record does not itself contain a source hash. At review time `test_transfer.py` SHA256 is `c8752ddfcd6a2aee99910dba7df5fd51529742a3fea2042e55c8eb04e0c3c268`.

### W2 — An overall benefit is not a probe benefit in every component
- Type: mechanism-attribution
- Severity: WARNING
- Evidence reference: Findings F4–F6; `primary400/summary.csv` and `strata.csv`.
- Recommended action: Explain movement, discovery, refinement, unsuccessful clearing and boundary behavior separately when comparing the leading candidates.

## Required follow-up
- Retain the boundary regression, 114 per-setting losses and offline scope in `primary400/report.md` and the user-facing result; use “lowest observed mean” for the matrix winner (F4–F5).
- If describing the D-optimal contribution in `README.md` or the report, distinguish the baseline gain from the unresolved small difference against JSO_compact (F5).
- Include `reviews/sample_geometry_audit.py`, `reviews/sample-geometry-audit.json`, this review, `audit.json`, result/scenario hashes and the final reporting/test sources in any evidence package under `experiments/q4_transfer/` (F3, W1).
- Keep `claims/baseline-q4.md` and formal entrypoints frozen; route any later adoption or stronger claim through a separate recorded readiness/rollback/evidence decision (F6).
- Memory check: recommend adding the primary boundary regression, the leading-candidate interval crossing zero, and inactive optical2 to `B题/memory.md`; reviewer did not edit memory.

## Reviewer recommendation
The completed 28×400 matrix supports reporting the observed paired efficiency gains and counterexamples as offline exploratory results. Full source/pairing records, an all-operation automated physical audit, independent mechanism/statistic checks and an alternate geometric reconstruction provide substantive validation for that scope. JSO_compact_dopt has the lowest combined mean and reduces both walking and total probing, while its boundary regression and uncertain margin over JSO_compact remain material. No baseline promotion, completed-stage declaration or stronger claim is made by this reviewer.

Verdict: PASS_WITH_WARNINGS

## Required reads referenced
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/stage-6-independent-validation.md` (read in preceding development review).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/subagent-validation-paper.md` (preceding review).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-markdown-audit.md` (preceding readiness review).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-human-confirmation.md` (preceding review).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-memory-update.md` (preceding review).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-subagent-delegation.md` (preceding review).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-readiness-gate.md` (preceding review).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-rollback.md` (preceding review).
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-output-schema.md` (preceding review).
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-self-discipline-checklist.md` (preceding review).
- All project artifacts explicitly listed in Reviewed scope; `src/geometry.py::wedge_halfplanes/disk_outer_halfplanes` for matching the declared envelope before independent reconstruction.

## Confidence
high — complete primary rows and provenance, all O/S mechanism events and uncertainty calculations were checked independently, supplemented by an alternative geometric sample and the reviewed full physical audit, with finite offline limits stated.

## Forbidden-behavior self-check
- [OK] Did not confirm user decisions
- [OK] Did not clear blockers
- [OK] Did not mark stages or rounds complete
- [OK] Did not increase claim level on behalf of the main agent
- [OK] Did not invoke another subagent
- [OK] Did not write or edit project files outside the authorized review outputs
- [OK] Did not write claims/baseline-snapshot.md
- [OK] Did not export when the final evidence gate has not passed
- [OK] Did not modify pinned implementation/data or rerun simulation/tests
