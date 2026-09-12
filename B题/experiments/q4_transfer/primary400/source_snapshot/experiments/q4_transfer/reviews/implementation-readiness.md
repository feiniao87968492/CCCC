# Q4 transfer — implementation readiness review

## Reviewed scope
- `B题/experiments/q4_transfer/design.md` (six candidate families and development/primary lock).
- `B题/memory.md` and `B题/claims/baseline-q4.md`.
- `B题/experiments/q3_ablation/policies.py` and `evaluation/summary.csv`.
- `B题/experiments/q4_ablation/q4_ablation_policies.py`.
- `B题/simulator_automation/q4_runner.py` (measurement/clear accounting, scan bookkeeping, localization, V4 execution).
- `B题/src/q4_adaptive.py`, `q4_localize.py`, `q4_state.py`, and `q4_certificate.py`.

This is a review of a preimplementation design for isolated offline experiments. No new implementation, test execution, result verification, or baseline promotion was performed. The user authorization described in the invocation/design is for the main agent to record; this reviewer does not confirm decisions. No provider failure occurred in this review.

## Findings

### F1 — Q3 sensing rules do not provide a Q4 reception certificate
- Type: directional-transfer-risk
- Severity: WARNING
- Evidence reference: `B题/experiments/q3_ablation/policies.py::_useful/_viewpoint`; `B题/src/q4_adaptive.py::ReceptionBelief`; `B题/src/q4_localize.py::history_region`; `B题/experiments/q4_transfer/design.md`, family 1.
- Recommended action: Implement S as `reception >= gate AND (parallax >= 12 degrees OR range halves)`, preserve the continuous positive-observation polygon independently, and log why each supplemental probe was admitted.

Q3's distance/parallax conditions cannot rule out the Q4 directional shadow. The finite RF hypothesis weights are approximate, including a nonzero mismatch floor; even reception probability 1 is not a continuous guarantee. `no_signal` may update those weights but must not clip the feasible polygon. The design states this separation correctly. S should use a recursion guard around measure/clear supplementation and suppress repeated sites using the existing coordinate tolerance; otherwise repeated supplemental sensing can erase its intended savings.

### F2 — O needs a persistent positive-observation retry contract
- Type: optimistic-clear-accounting
- Severity: WARNING
- Evidence reference: `B题/experiments/q3_ablation/policies.py::_estimate/_resolve`; `B题/simulator_automation/q4_runner.py::_adaptive_task/_try_localize/_try_clear_at/_do_v3_action`; `B题/src/q4_state.py::apply_clear`; `B题/experiments/q4_transfer/design.md`, family 1.
- Recommended action: Freeze an explicit per-channel speculative-attempt cap and positive-observation version, applying them to every inherited and new speculative clear path; record conditioning convention and actual clear-point geometry.

Q3 checks `cond(normals) <= 30`; `cond(normals.T @ normals) <= 30` is materially stricter because the latter squares the condition number. The design's “normal matrix condition” must identify which matrix is used in the registry. On failure, gate the next O attempt on a new positive direction/near observation, not a larger history length: negative RF grows history without changing the location polygon. An inherited V4 center-clear fallback must not bypass that gate or reset the total cap. A legal least-squares point inside an 80 m enclosing region remains speculative. For a shifted *certified* point q, check `max(norm(vertex-q)) <= 20 - tolerance`; the old center's radius alone cannot certify q. Failed clears remain charged and must not shrink the positive polygon.

### F3 — Replanning and recovery must retain a finite completion path
- Type: progress-and-geometric-proof
- Severity: WARNING
- Evidence reference: `B题/src/q4_adaptive.py::ranked_refinement_points`; `B题/src/q4_localize.py::optical_cover_points`; `B题/simulator_automation/q4_runner.py::_run_adaptive_v4/_do_v3_action/_optical_fallback`; `B题/experiments/q4_transfer/design.md`, families 2–5.
- Recommended action: Log no-progress decisions, force eventual pending-source service after coverage work ends, and keep the uncapped complete optical cover reachable after the eight dedicated-refinement attempts.

The frozen recovery proof uses both conditions: the short bracket crosses every feasible source ray *before* its nearest feasible projection, and both endpoints pass the affine squared-distance vertex test relative to a known receiving site. Distance dominance alone does not prove directional reception. Preserve the wedge/projection condition, endpoint legality and fresh-site rules when extending the trigger beyond the frozen one-bearing case. Replanning after the first negative must retain or reconstruct a valid second endpoint before claiming the pair's reception guarantee. The existing 800-iteration guard is a failure report, not a completeness proof. Early optical clearing must traverse the whole selected certified cell cover if necessary; reaching the 2/4-cell trigger must not impose a truncation on the final fallback.

### F4 — Cover geometry and its station identity are a single experiment state
- Type: certificate-and-isolation
- Severity: WARNING
- Evidence reference: `B题/experiments/q4_ablation/q4_ablation_policies.py::cover_context/_cover_model`; `B题/src/q4_certificate.py::discovery_certificate`; `B题/src/q4_state.py::can_certify_absent/maybe_count_certify_n_max`; `B题/simulator_automation/q4_runner.py::scan_at`.
- Recommended action: Record a successful continuous certificate for every actual geometry before running it, build channel/site indices under that geometry, and isolate global cover contexts by process or sequential execution.

The imported context manager mutates module-global TRI25 points/index maps and restores them later; concurrent threads running different geometries can corrupt absence bookkeeping without changing a file hash. A source task at a cover coordinate is not proof that every unknown channel was scanned there. Only actual per-channel readings populate absence evidence. Preserve the independent observed-16-channel certificate. The four radii in the design are candidate values, not prevalidated certificates; certificate rejection must appear in the manifest as an excluded geometry, never silently fall back to a different radius under the same label. Baseline source SHA checks do not replace these runtime-state checks.

### F5 — The Q3 factorial is an incremental transfer, with existing Q4 overlap
- Type: ablation-interpretation
- Severity: WARNING
- Evidence reference: `B题/experiments/q3_ablation/evaluation/summary.csv`; `B题/experiments/q4_ablation/q4_ablation_policies.py::_select/VARIANTS`; `B题/simulator_automation/q4_runner.py::_adaptive_task/_probe_detected_at_v4`; `B题/claims/baseline-q4.md`.
- Recommended action: Freeze all eight J/S/O arms relative to the same unmodified V4 control and describe each factor as the exact incremental change, including overlap with first-round center-route selection.

Q4 already has a joint adaptive tour, detected-channel opportunistic sensing, and bounded 80 m center trials. Thus O-off is not “no optimism”, S-off is not “no opportunistic probing”, and J's center proxy repeats the first-round `center_route` mechanism unless another declared change distinguishes it. This is useful reproducibility/interaction evidence, but not three wholly new mechanisms. Q3 JSO's 254.053 s/source and 107.624 probes come from 420 omnidirectional seven-site scenes; Q4's frozen 517.584 s/source comes from a different 100-scene mixed cohort. Neither cross-problem ratio nor the previous round's old aggregate is a paired transfer gain.

### F6 — Selection and stress regressions require separate reporting
- Type: paired-selection-evidence
- Severity: WARNING
- Evidence reference: `B题/experiments/q4_transfer/design.md`, Experiments and locking; `B题/memory.md`, Q3 ablation counterexample; `B题/claims/baseline-q4.md`, Paired bound.
- Recommended action: Lock the registry before primary evaluation, preserve the 400-setting mixture and within-seed dependence in bootstrap resampling, and report boundary/outward and N strata with failed rows visible.

The primary design has 200 seed blocks, not 400 independent draws: the first 50 seeds carry five settings each and the remaining 150 carry one. Cluster resampling should preserve every setting in a sampled block and recompute the intended setting-weighted mean; do not average seed means equally and accidentally change the estimand. Report 200 mixed endpoint settings as the primary natural mixture and the stress cohorts separately, alongside the declared 400-setting combined score. Development choice and primary ranking across many arms create selection effects; marginal intervals are not simultaneous winner guarantees. The previous Q4 champion worsened boundary/outward minimum-radius T/K by 3.90%, and the frozen baseline already has N=16 paired regressions. A fresh aggregate gain cannot be advertised as improvement in every environment. Failed scenes are ineligible for winner status but still require visible failure rows and denominators; an elapsed-until-failure T/K is not a completed-scene efficiency score.

## Blocking risks
No unresolved design-level blocker was identified for writing the user-authorized isolated experimental code. F1–F6 specify implementation and evidence acceptance conditions, not evidence that they are already satisfied. This review does not clear any main-agent gate. Any failure to retain the positive polygon, complete optical fallback, per-channel absence proof, immutable baseline, or primary registry lock would require a new blocking finding before results are accepted.

## Non-blocking warnings

### W1 — Finite offline success does not upgrade the frozen claim
- Type: evidence-scope
- Severity: WARNING
- Evidence reference: `B题/claims/baseline-q4.md`, Claim level and Scheme constraints; Findings F5–F6.
- Recommended action: Label new results as offline exploratory comparisons against a `feasible_baseline`, obtain a separate Stage 6 event/result validation, and keep official-simulator and optimality claims blocked.

### W2 — Mechanism counters are needed to explain probe savings
- Type: cost-decomposition
- Severity: WARNING
- Evidence reference: `B题/simulator_automation/q4_runner.py::measure/clear/_probe_detected_at_v4/_do_v3_action`; Findings F1–F3.
- Recommended action: Add counters for S probes, dedicated refinement, O attempts/successes, optical cells and failed clears to the experiment outputs, while independently reconciling movement, measurements, switches and clears with total virtual time.

`n_probe` counts an opportunistic subset, whereas `n_measure` is total measurement count. Eight dedicated attempts do not cap supplemental S probes. A smaller walking component may still lose overall, as Q3 JSO_ALLSCAN's 353.252 measurements versus JSO's 107.624 illustrate.

## Required follow-up
- In `B题/experiments/q4_transfer/design.md` or its locked registry, state O's exact condition matrix, persistent positive-version retry rule, total cap, and explicit S Boolean expression (F1–F2).
- In `B题/experiments/q4_transfer/`, save source snapshots, exact factor/config registry hashes, scene-setting hashes, successful geometry certificates and rejected-candidate reasons before primary execution (F4–F5).
- In the experiment validation artifact under `B题/experiments/q4_transfer/reviews/`, independently check per-channel absence, valid positive regions, clear classifications, progress/fallback and total time accounting using raw events (F1–F4, W2).
- In the final report under `B题/experiments/q4_transfer/`, publish all development and primary rows, frozen-V4 paired comparisons, seed-block uncertainty, subgroup/tail regressions and selection limitations (F5–F6).
- In the applicable `gates/` or experiment readiness record, document the existing authorization for isolated experiments and the unchanged frozen baseline claim ceiling; route any future adoption through a separate rollback/readiness and Stage 6 review (W1).
- Memory check: propose recording the `cond(A)` versus `cond(A.T @ A)` distinction and positive-observation-version retry rule in `B题/memory.md`; this reviewer did not edit that file.

## Reviewer recommendation
The design is sufficiently concrete for isolated implementation and matched exploration, with the warnings above carried into the registry and verification artifacts. The combination of a full J/S/O factorial, distinct localization/recovery families, new paired scenes and retained geometric safety mechanisms can answer the user's transfer question. This verdict evaluates readiness of the design only; it neither approves a candidate implementation nor confirms baseline replacement, a completed stage, or improved claim strength.

Verdict: PASS_WITH_WARNINGS

## Required reads referenced
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/stage-5-solution-implementation.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/subagent-model-building.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/subagent-specialists.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-markdown-audit.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-human-confirmation.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-memory-update.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-subagent-delegation.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-readiness-gate.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-rollback.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-fallback-and-deviation.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-improvement-loop.md` (opened during the earlier review invocation).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/subagent-improvement-critique.md` and `subagent-improvement-skepticism.md` (opened during the earlier invocation; latest assignment is Stage 5 readiness).
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-output-schema.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-self-discipline-checklist.md`
- All project artifacts listed in Reviewed scope.

The attempted path `references/subagent-implementation-readiness.md` does not exist in this installation; the existing Stage 5 contract and `subagent-model-building.md` explicitly cover implementation readiness and were used.

## Confidence
medium — the design and reused code expose the relevant interfaces and counterexamples, but the new implementation and primary event evidence do not yet exist.

## Forbidden-behavior self-check
- [OK] Did not confirm user decisions
- [OK] Did not clear blockers
- [OK] Did not mark stages or rounds complete
- [OK] Did not increase claim level on behalf of the main agent
- [OK] Did not invoke another subagent
- [OK] Did not write or edit project files outside the review output
- [OK] Did not implement experimental code or run tests
- [N/A] Did not run without upstream Critique — latest assignment is Stage 5 readiness, not Improvement-Skepticism
