# Q4 Aggressive Local Experiments — Independent Improvement-Critique Review

## Reviewed scope

- `experiments/q4_aggressive/design.md`.
- `experiments/q4_local/primary400/report.md`, `completion.json`, and `experiments/q4_local/reviews/primary-validation.md`.
- `memory.md`, `workflow.md`, `claims/baseline-q4.md`, `claims/baseline-snapshot.md`, and `claims/claim-registry.md`.
- `improvements/improvement-frontier.md`, `data/sensitivity/sensitivity-report.md`, `decisions/decision-improvement-round-1.md`, `gates/stage6-q4-validation.md`, and `reviews/stage6-validation-review.md`.
- `experiments/q4_local/q4_local_policies.py`, `experiments/q4_transfer/q4_transfer_policies.py`, and `experiments/q4_ablation/q4_ablation_policies.py`.
- `src/q4_adaptive.py`; relevant geometry and state-transition hooks in `src/q4_localize.py` and `src/q4_state.py`.
- `simulator_automation/q4_runner.py`: action accounting, scans, caches, refinement, optical execution, stopping, and failure handling.
- `experiments/q4_local/run_local.py`; aggregation/comparison hooks in `summary_local.py` and `experiments/q4_ablation/summarize.py`; scenario, execution, and manifest hooks in `experiments/q4_ablation/run_ablation.py`.
- `experiments/q4_efficiency/release_holdout100.meta.json`; accounting/summary search excerpts in `bench.py`; static simulator definitions in `tests/test_q4_geomsim.py` and `tests/test_q4_regressions.py`.
- Reviewer guidance listed under Required reads referenced.

All requested files were readable, including the optional frontier. Repository-wide discovery encountered access denial for `modickx_legacy`, outside the requested scope.

This is a design and integration review. Earlier numerical results are reported evidence from the inspected artifacts; I did not independently recompute them, verify their hashes, or execute aggressive candidates.

The frozen reference remains TRI25/V4, with historical holdout mean **517.5842931731096 s/source** and claim level `feasible_baseline`. The prior local cohort reports matched V4 **537.376003**, LC approximately **519.897**, and LPC **515.618001 s/source**. These are different cohorts, not interchangeable comparison denominators.

Below, **ΔG(X)** means candidate minus matched comparator X in setting-weighted mean(T/K) over the prescribed 350 general settings. Negative values favor the candidate. Every efficiency hypothesis requires complete clearing and certification on **all 400 settings**. All expected deltas are prospective criteria, not observed results or promised gains.

## Findings

### F1 — E: Separate the ordering score, expected-cost surrogate, and executed complete cover

- Type: optical-ordering-and-cost-definition
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:34`; `experiments/q4_local/q4_local_policies.py:157`; `simulator_automation/q4_runner.py:213`; `src/q4_localize.py:76`; `src/q4_adaptive.py:34`.
- Recommended action: Specify E’s normalized residual-mass calculation and execution contract in `experiments/q4_aggressive/design.md`, including complete-cover identity, failed-disc conditioning, and fallback behavior.
- Hypothesis: E’s reordered complete clearing reduces general-setting mean(T/K) relative to LC and matched frozen V4 without losing completion.
- Expected metric delta: ΔG(LC)<0 and ΔG(V4)<0; RF probes may decrease while failed clears and stress costs increase; no numerical gain estimate is supported.
- Implementation cost: Medium—an isolated optical executor/orderer, explicit cost bookkeeping, and independent order/cost reconstruction.
- Required new data or solver: No external data or new solver; prescribed synthetic batches and new mechanism traces suffice.
- Touches confirmed method or model structure: Yes—experimental optical scheduling/execution; Method revision if adopted into the confirmed method, with rollback handling required before such adoption.
- Suggested claim level after success: `exploratory_analysis`; retain the frozen baseline and its existing claim level.

The inherited executor repeatedly selects the nearest remaining cell. Merely sorting `optical_cover_points()` will therefore **not execute E’s order**. An isolated executor must preserve every certified cell while honoring the selected order.

The `0.05/n_cells` ordering bonus does not itself define “unsampled/no-hit mass” for the expected-cost calculation. Specify whether that mass is explicit or merely a conservative surcharge, how overlapping clear discs avoid double-counting, and what happens when failed discs eliminate every sampled point. Uniform recovery must not silently restore eliminated samples as calibrated probabilities.

Audit the first increment with remaining mass one, subsequent increments after preceding failures, and the success surcharge convention. Preserve the complete cover when soft mass reaches zero; the 48/256 thresholds must affect dispatch/order selection only. Cached geometry may use positive versions, but order and costs must reflect current position, full RF history, and failed attempts.

### F2 — B: The two-step proxy needs an executable mathematical definition

- Type: underspecified-local-score
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:54`; `experiments/q4_local/q4_local_policies.py:86`; `experiments/q4_transfer/q4_transfer_policies.py:227`; `src/q4_adaptive.py:81`.
- Recommended action: Freeze B’s candidate directions, continuation formula, weighting convention, degeneracy handling, and deterministic ties before development.
- Hypothesis: B’s short-approach candidates and two-step score jointly reduce general-setting mean(T/K) relative to LC and matched frozen V4.
- Expected metric delta: ΔG(LC)<0 and ΔG(V4)<0, with lower walking time as the intended mechanism; total probes may increase.
- Implementation cost: Medium—candidate generation, scoring, numerical safeguards, and independent selected-action reconstruction.
- Required new data or solver: No external data or new solver; use existing observations, geometry, and prescribed scenes.
- Touches confirmed method or model structure: Yes—experimental refinement selection; Method revision on adoption.
- Suggested claim level after success: `exploratory_analysis`.

“Offsets around” the center and “perpendicular second viewpoints” leave directions and reference axes unspecified. Define the `q=g` case and whether virtual viewpoints outside the legal region are retained as optimistic proxies or excluded.

Also distinguish an unnormalized heard-weighted continuation sum from a conditional mean given reception. They rank actions differently when combined with the 78 s non-reception penalty. Log reception mass, first-action cost, continuation cost, penalty, candidate provenance, and recovery override.

Apply legal/fresh filtering after extending the candidate list, then restore the proven one-bearing negative-RF bracket ahead of the score ranking. B changes both the candidate set and scoring; its paired result supports that combined intervention, not an isolated claim that the second-step term caused the gain.

### F3 — G: Define which probe paths share the three-probe budget

- Type: callback-coverage-and-budget-accounting
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:70`; `experiments/q4_local/q4_local_policies.py:80`; `experiments/q4_local/q4_local_policies.py:110`; `experiments/q4_transfer/q4_transfer_policies.py:158`; `experiments/q4_transfer/q4_transfer_policies.py:212`; `src/q4_adaptive.py:60`.
- Recommended action: Specify G’s callback coverage and replace every applicable detected-channel supplemental path with the same physical-stop budget, retaining mandatory unknown scans separately.
- Hypothesis: G’s dynamic selection saves enough later walking/refinement to reduce general-setting mean(T/K) relative to LC and matched frozen V4.
- Expected metric delta: ΔG(LC)<0 and ΔG(V4)<0; total probe count has no guaranteed negative delta; accepted G probes must remain ≤3 per defined stop.
- Implementation cost: Medium—callback integration, a distinct budget ledger, and one-to-one physical-event auditing.
- Required new data or solver: No external data or new solver; new opportunity, rejection, budget, and physical-action traces are required.
- Touches confirmed method or model structure: Yes—experimental supplemental-probe scheduling; Method revision on adoption.
- Suggested claim level after success: `exploratory_analysis`.

LC has `selective=False`. Existing post-source-action supplementation runs only when `selective=True`; cover-stop probing follows a separate dispatch path, and optical fallback does not invoke either hook. An override of `_supplement()` alone does not establish “at each actual stop.”

Define whether startup, dedicated measurements, speculative clears, and optical-cell visits are eligible, and prevent inherited V4/S probes from bypassing G’s cap. Recompute switching cost from `measure_channel`; a clear does not switch the RF measurement channel.

`expected_gain()` already includes reception-weighted gains. Additional multiplication by reception probability would change the declared score. Record admitted opportunities and threshold rejections so an inactive arm can be distinguished from a missing hook. Earlier LPC-versus-LC evidence already shows that lower time can coexist with more probes.

### F4 — R: Lock dedicated-count semantics and precedence with C/E/H

- Type: early-exit-dispatch-semantics
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:81`; `simulator_automation/q4_runner.py:606`; `experiments/q4_local/q4_local_policies.py:147`; `experiments/q4_ablation/q4_ablation_policies.py:181`.
- Recommended action: Define R using actual dedicated-measurement counters and an explicit precedence table, with execution records distinguished from scheduler proposals.
- Hypothesis: R’s earlier complete optical dispatch lowers general-setting mean(T/K) relative to LC and matched frozen V4 by avoiding costly later refinement.
- Expected metric delta: ΔG(LC)<0 and ΔG(V4)<0; dedicated RF decreases on activated exits, while optical attempts and stress costs may increase.
- Implementation cost: Low to medium—predicate/precedence integration and actual-dispatch auditing.
- Required new data or solver: No external data or new solver; existing histories and dedicated counters suffice.
- Touches confirmed method or model structure: Yes—experimental RF-to-optical transition; Method revision on adoption.
- Suggested claim level after success: `exploratory_analysis`.

`extra_measures` counts dedicated measurements; discovery and supplemental probes do not increment it. Using history length would test a different R2/R4 mechanism.

The scheduler proposes tasks for every pending source before selecting one. A logged proposal is not an executed early exit. Record the dedicated count, positive-bearing count, radius, and dispatch reason at execution.

Specify certified clear first, then R’s relationship to C/E and H. In R+H, eligible R exits can suppress H; in R+E, E should still govern optical ordering. Preserve ordinary cap8/fallback behavior when R is ineligible, including one-bearing and large-region cases.

### F5 — H: Wider least-squares commitment needs execution-specific retry accounting

- Type: optimistic-retry-and-component-interaction
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:89`; `experiments/q4_transfer/q4_transfer_policies.py:64`; `experiments/q4_transfer/q4_transfer_policies.py:120`; `experiments/q4_transfer/q4_transfer_policies.py:158`; `experiments/q4_transfer/q4_transfer_policies.py:170`; `memory.md:20`.
- Recommended action: Give H attempts an explicit identity and audit their actual eligibility, positive-version consumption, failed-point exclusion, and interaction with C/E/R/G/N.
- Hypothesis: H200/H400 replace enough approach/refinement work with successful LS clears to reduce general-setting mean(T/K) relative to LC and matched frozen V4.
- Expected metric delta: ΔG(LC)<0 and ΔG(V4)<0; speculative walking and failed clears may increase, bounded by two H attempts per source.
- Implementation cost: Low to medium using the existing LS helper, with combination-specific retry auditing.
- Required new data or solver: No external data or new solver.
- Touches confirmed method or model structure: Yes—experimental speculative-clear policy; Method revision on adoption.
- Suggested claim level after success: `exploratory_analysis`.

The LS helper already checks `cond(A)<=30`, legality, and polygon membership. Retain these checks; polygon membership is not a 20 m clearing certificate.

The inherited optimistic executor counts any `aggr_clear` as an O attempt when optimism is enabled. Routing N through that path could consume H’s budget or suppress N unintentionally. H counters should represent actual H trials, not proposals replaced by C/E/R or unrelated clears.

Also resolve G suppression: inherited `_useful()` suppresses probing when an optimistic estimate/version exists, without checking the same failed-point exclusion used by optimistic dispatch. Log this interaction rather than attributing inactivity solely to G’s threshold. Negative RF must never renew H permission.

### F6 — N: Callback ordering can resurrect a physically cleared source

- Type: reentrant-clear-and-state-consistency
- Severity: BLOCKING
- Evidence reference: `experiments/q4_aggressive/design.md:98`; `simulator_automation/q4_runner.py:112`; `simulator_automation/q4_runner.py:158`; `simulator_automation/q4_runner.py:180`; `simulator_automation/q4_runner.py:213`; `src/q4_state.py:152`; `tests/test_q4_geomsim.py:67`.
- Recommended action: Specify a post-observation, post-log N callback lifecycle that rechecks source status before every enclosing clear/fallback continuation and prevents duplicate physical clears.
- Hypothesis: N’s bounded clears at visited positions reduce general-setting mean(T/K) relative to LC and matched frozen V4 without introducing state inconsistency.
- Expected metric delta: ΔG(LC)<0 and ΔG(V4)<0; direct N movement is exactly zero; at most two failed N trials add up to 6 s/source before induced downstream effects.
- Implementation cost: Medium to high—safe integration across scans, source actions, and optical execution, plus adversarial lifecycle validation.
- Required new data or solver: No external data or new solver; constructed callback histories and immutable physical traces are required.
- Touches confirmed method or model structure: Yes—experimental action lifecycle; Method revision, with rollback handling required if confirmed shared code is changed.
- Suggested claim level after success: `exploratory_analysis`.

The design’s nested-callback guard does not specify what the original caller does after N succeeds. Existing callers can issue a clear after a `near` response, and optical execution continues until its own `_try_clear_at()` returns success. `_try_clear_at()` does not reject an already-cleared channel.

A second physical clear returns failure in the inspected simulator. `Q4State.apply_clear(..., success=False)` then sets that source back to `detected` and `cleared=False`. This is a concrete integration failure path capable of defeating complete clearing/certification; it is **not an observed aggressive-run failure**.

Do not attach N to `_move_to()`: that occurs before the current response has updated observation state and been logged. Define callback timing, active-source handling, stale-task cancellation, and behavior after nested success. Apply the two-trial/new-positive-version/failed-point rules to N’s own ledger. Validate N+G, N+H, and N+E as well as N alone.

### F7 — Ranking must use the general-setting estimand after all-setting eligibility

- Type: estimand-and-selection-control
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:10`; `experiments/q4_aggressive/design.md:108`; `experiments/q4_ablation/summarize.py:70`; `experiments/q4_ablation/summarize.py:94`; `experiments/q4_local/summary_local.py:59`; `claims/baseline-q4.md:13`.
- Recommended action: Freeze separate eligibility, general-setting ranking, stress reporting, and paired-inference calculations in the aggressive design and selection record.
- Hypothesis: A locked selected candidate achieves ΔG(V4)<0 on fresh primary settings; its incremental mechanism claim additionally requires ΔG(LC)<0.
- Expected metric delta: Negative paired general-setting mean delta is the efficiency criterion; positive boundary or all400 cost deltas are permitted and must remain visible.
- Implementation cost: Low to medium—aggregation changes, deterministic selection rules, and independent statistical reconstruction.
- Required new data or solver: No external data or new solver; use the prescribed development and primary matrices.
- Touches confirmed method or model structure: Yes—the experimental evaluation objective differs from earlier all400 ranking; record the evidence-method change without replacing the frozen assessment.
- Suggested claim level after success: `exploratory_analysis`.

The inherited local summary aggregates all settings. Reusing it unchanged would rank the wrong objective. Compute eligibility from all400 first: no failure, `K=N`, and valid certification for every setting. Then rank eligible arms on general350; retain failed arms and partial costs without success-only ranking.

Bootstrap whole seed blocks but use **general-setting sums and counts** for the primary estimand. In this matrix, the first 50 blocks contain four general settings each and the other 150 contain one; averaging block means equally would change the estimand.

Lock tie-breaking and zero/one-improving-family behavior before development selection. Report paired comparisons against frozen V4 and LC separately, with LPC/prior JSO as additional controls. Historical 517.584293 and prior-cohort LC/LPC means cannot supply this batch’s improvement percentages. A lowest observed mean does not establish a unique winner.

### F8 — Preserve effective control identity and end-to-end immutable evidence

- Type: control-identity-and-evidence-provenance
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:25`; `experiments/q4_aggressive/design.md:134`; `experiments/q4_local/q4_local_policies.py:64`; `experiments/q4_transfer/q4_transfer_policies.py:91`; `experiments/q4_ablation/q4_ablation_policies.py:71`; `experiments/q4_local/run_local.py:86`; `experiments/q4_ablation/run_ablation.py:121`; `improvements/improvement-frontier.md:9`.
- Recommended action: Record effective runner/configuration identities, immutable dependency snapshots, complete outcome manifests, and separately hashed final analysis/review artifacts for each batch.
- Hypothesis: Matched controls execute their declared configurations, and independent artifact reconstruction reproduces every reported comparison without source or result substitution.
- Expected metric delta: Zero intended policy-cost delta from packaging; any deterministic control discrepancy must be explained before accepting efficiency comparisons.
- Implementation cost: Medium—dependency/configuration capture and full evidence-chain auditing.
- Required new data or solver: No external data or new solver; new manifests, event traces, audits, and final artifact hashes are required.
- Touches confirmed method or model structure: No for evidence preservation itself; silently changing control factories, shared modules, or frozen inputs would constitute Method revision.
- Suggested claim level after success: `exploratory_analysis`.

`previous_best` is factory-sensitive: the local factory selects `JSO_compact_dopt`, whereas the transfer factory’s same name selects an older ablation control. Record the **effective runner and expanded configuration**, not just the arm name. Radius changes occur through process-global cover state; preserve per-job restoration and avoid concurrent conflicting contexts within one process.

Retain all initial arms, failed/resource-limited outcomes, scenario hashes, physical charges, actual mechanism activations, and both source-clear and absence/counting certificates. Snapshot simulation dependencies before execution; do not overwrite earlier results or mutate in-run sources. Final analysis and review files need their own source/output hashes.

The 800-iteration executor limit and reported wall time remain relevant. The inspected geometric simulator does not enforce the advertised real-duration field, so offline completion cannot establish deadline completion in the official simulator.

The frontier’s existing F1–F5 describe an earlier review. Reference this review’s F1–F6 by review path and family; do not overwrite or relabel those historical findings.

## Blocking risks

### B1 — N’s enclosing caller may continue after a nested successful clear

- Type: reentrant-clear-and-state-consistency
- Severity: BLOCKING
- Evidence reference: F6; `simulator_automation/q4_runner.py:180`; `src/q4_state.py:152`; `tests/test_q4_geomsim.py:67`.
- Recommended action: Resolve the callback lifecycle in `experiments/q4_aggressive/design.md` and require independent readiness evidence for duplicate-clear prevention, active fallback termination, and stale-task handling.

This blocks an implementation-readiness recommendation for the current integration specification. It does not question the user’s authorization or impose a stress-cost non-regression requirement.

## Non-blocking warnings

### W1 — The proposed scores remain heuristics

- Type: uncalibrated-proxy-interpretation
- Severity: WARNING
- Evidence reference: F1–F5; `src/q4_adaptive.py:34`; `experiments/q4_local/reviews/primary-validation.md:74`.
- Recommended action: Report predicted scores and actual outcomes separately; retain inactive and losing arms without interpreting soft mass as success probability or virtual viewpoints as executable forecasts.

### W2 — Efficiency, completion, and provenance require separate checks

- Type: evaluation-and-reproducibility
- Severity: WARNING
- Evidence reference: F7–F8; `experiments/q4_aggressive/design.md:10`; `claims/claim-registry.md:11`.
- Recommended action: Keep general350 ranking conditional on all400 completion, disclose permitted stress regressions, and bind comparisons to immutable matched controls and events.

## Required follow-up

- Resolve F6 in `experiments/q4_aggressive/design.md`; specify callback placement, committed-state visibility, nested-success handling, and retry ownership.
- Add E/B scoring formulas, G callback/budget coverage, and C/E/R/H/N precedence to `experiments/q4_aggressive/design.md` before configuration lock.
- Record the already-authorized experimental scope and this review’s unchanged F-IDs in a scoped `decisions/` record; no renewed confirmation of the same authorization is requested.
- Have the caller obtain Skepticism and implementation-readiness reviews under `experiments/q4_aggressive/reviews/`, carrying B1 forward explicitly.
- In the aggressive validation artifacts, cover misleading/all-eliminated soft weights, complete fallback beyond ordering thresholds, B’s coincident/illegal candidates, G stop resets and switch accounting, R dedicated counts, H condition/version boundaries, and N duplicate-clear interactions.
- Freeze development selection, effective controls, general350 estimand, and all400 eligibility in the aggressive design and batch manifests; preserve every initial arm.
- Require immutable events, complete charging/certification audits, independent scoring samples, and separately hashed final report/review sources under `experiments/q4_aggressive/`.
- Preserve `claims/baseline-q4.md`, `claims/baseline-snapshot.md`, and `claims/claim-registry.md`; any later adoption remains separate and must follow applicable decision, rollback, and evidence-gate handling.

## Reviewer recommendation

The six families provide testable local efficiency hypotheses within the existing solver footprint, and the general-case objective is consistent with the user’s authorization. The current proposal nevertheless leaves a concrete clearing-state hazard unresolved in N’s callback integration. Resolve that lifecycle contract and carry the scoring, budget, precedence, ranking, and provenance requirements into independent Skepticism/readiness review. This recommendation neither authorizes implementation nor clears a gate; extreme-case cost regression alone is not grounds for rejection.

Verdict: BLOCKED

## Required reads referenced

- `C:/Users/zty/.agents/skills/math-modeling-v4/SKILL.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/subagent-improvement-critique.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-improvement-loop.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-subagent-delegation.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-readiness-gate.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-rollback.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-output-schema.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-self-discipline-checklist.md`
- All project artifacts actually inspected are listed under Reviewed scope; cited line references identify the relevant evidence.

## Confidence

medium — static inspection establishes the integration hazards and comparison requirements, but aggressive execution evidence was unavailable and earlier numerical/hash validation was not independently repeated.

## Forbidden-behavior self-check

- [OK] Did not confirm user decisions or request confirmation.
- [OK] Did not clear blockers, approve implementation, or mark stages or rounds complete.
- [OK] Did not change baseline or claim levels.
- [OK] Did not invoke another subagent, including the Improvement-Skepticism Reviewer.
- [OK] Did not write or edit any project file; the caller will save this response.
- [OK] Did not implement policies or run simulations/tests; simulator/test files were inspected only as text.
- [OK] Compared against the frozen baseline, with LC as an additional matched mechanism control.
- [OK] Did not silently approve proposals or bypass readiness/rollback protocols.
- [OK] Every finding includes all required schema and Critique fields.
- [OK] Did not describe expected gains as observed results or promise improvement.
- [OK] Retained full clearing/certification as mandatory while allowing extreme-case cost regression.