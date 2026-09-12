# Q4 local decisions — implementation readiness review

## Reviewed scope
- `experiments/q4_local/design.md`, all five local families, controls, experiment plan and invariants.
- `experiments/q4_transfer/reviews/primary-validation.md`, previously completed independent primary review.
- `experiments/q4_transfer/q4_transfer_policies.py`, especially estimation, supplementation, candidate selection and action dispatch.
- `src/q4_adaptive.py`, including spatial/RF weights, expected gain and the receiving bracket.
- `simulator_automation/q4_runner.py`, adaptive task/executor, measurement caps and optical dispatch.
- `experiments/q4_ablation/q4_ablation_policies.py`, inherited experiment executor and global task selection.
- `memory.md`; frozen positive-region, optical-cover, state and certificate APIs inspected in the previous reviews.

Paths are relative to `B题/`. This is a preimplementation review for the user-authorized isolated experiment. No local policy implementation, test execution, simulated result or baseline replacement was performed or approved by this reviewer. The main agent owns recording existing authorization and subsequent readiness/evidence decisions.

## Findings

### F1 — L's cost terms must use one consistent spatial/RF measure
- Type: local-cost-semantics
- Severity: WARNING
- Evidence reference: `experiments/q4_local/design.md`, L30/L90; `src/q4_adaptive.py::ReceptionBelief.expected_gain/_heard/ranked_refinement_points`.
- Recommended action: Freeze exact marginalization formulas and use the L score solely for legal unmeasured RF candidates, restoring the proven one-positive negative-RF bracket afterward.

The weight tensor has spatial, heading/type and radius dimensions. For the declared local completion proxy, spatial distance should use `w_i=sum_heading,radius(weights)`; completion should use `sum_i completion_i * sum_heading,radius(weights * heard_at_p)`, and reception should be the corresponding total heard mass. Otherwise an unconditional completion weight can count a precise bearing from a hypothesis that will not receive. The design's 6 s measurement term is a deliberate planning surrogate; actual first/same-channel measurement can cost 5 s and all physical operations must retain exact charging. This score omits subsequent global coverage continuation on purpose and therefore cannot establish minimum total time. All legal V4 candidates should remain eligible, including low-reception candidates when the proven bracket/fallback needs them. Reapplying a generic sort after restoring the bracket would silently remove its priority.

### F2 — P needs one stop-level budget shared by every callback
- Type: local-budget-state
- Severity: WARNING
- Evidence reference: `experiments/q4_local/design.md`, P1/P2; `experiments/q4_transfer/q4_transfer_policies.py::_supplement/_probe_detected_at_v4/_do_v3_action`; `src/q4_adaptive.py::ReceptionBelief.expected_gain`.
- Recommended action: Track accepted physical movement and a single stop identifier/budget, enforce it across cover/source/clear callbacks and re-rank admitted channels after each executed probe using the current receiver channel.

The inherited executor can call supplementation through several paths at the same coordinate. Resetting a local counter on entry to `_supplement` would violate P1/P2 even though each call appears bounded. A fresh budget should require actual movement over the declared 1 m threshold, with a documented stop-anchor convention; merely proposing a different coordinate, entering an optical callback or changing channels is not movement. Small moves within the tolerance must not each reset the budget. Unknown-channel certificate scans are exempt from this budget but still update the receiver channel used in scoring. `expected_gain` already includes the reception-weighted mass; multiplying it by reception probability again would implement a different gate. Recomputing the 5+actual-switch denominator after each P probe avoids using a stale switch cost. All admitted P probes must still use S's full Boolean, adequacy and repeated-site conditions.

### F3 — F continuation must follow actual outcomes, without recursive dispatch
- Type: bounded-continuation-and-progress
- Severity: WARNING
- Evidence reference: `experiments/q4_local/design.md`, F60/F120; `simulator_automation/q4_runner.py::_do_v3_action`; `experiments/q4_transfer/q4_transfer_policies.py::_do_v3_action`; inherited `_run_adaptive_v4`.
- Recommended action: Use an explicit nonrecursive two-action loop, record the target channel's executed response, and route optical tasks back to the ordinary scheduler before dispatch.

The existing `_do_v3_action` returns None, can perform a measure followed by a near clear, and may then supplement other channels. A truthy return check or the last global event cannot reliably determine whether the selected channel received no signal or suffered a failed clear. Capture the target's actual measure/clear outcome and stop after a negative or failed clear, including the initial action; stale histories must not start a burst. Distinguish two additional source decisions from their physical operations when a measure triggers an immediate near clear, and log both. Check distance from the actual current position before each action, recheck detected status and remaining dedicated budget, and re-evaluate the next task after each observation. Never recursively invoke the outer burst-enabled method. Inherited `_do_v3_action` interprets an unrecognized action kind as a measurement; passing `optical` or a novel mass-clear label into it would execute the wrong operation. Optical requires the existing full fallback dispatch, and mass clear requires an explicit mapped clear path. Returning to the ordinary scheduler after a burst does not prove that the next global decision cannot choose the same source again; the inherited finite measurement/clear budgets and complete fallback remain necessary.

### F4 — C compares a full-cover planning cost with a surrogate, not two proven expected completion costs
- Type: optical-rf-cost-comparison
- Severity: WARNING
- Evidence reference: `experiments/q4_local/design.md`, C1/C15; `src/q4_localize.py::optical_cover_points` and inherited `simulator_automation/q4_runner.py::_optical_fallback` as inspected in prior reviews.
- Recommended action: Specify how the RF candidate is obtained when the current proposal is aggressive clear, preserve certified-clear priority, and log both compared cost surrogates and actual executed outcomes.

The full optical NN tour cost includes the whole candidate cover, 3 s per trial and one 2 s successful-clear surcharge; actual execution can stop early. The one-probe-plus-center-clear comparator does not guarantee reception, localization to 20 m or successful clearing. Therefore C1/C15 tests a heuristic decision threshold and cannot be described as optimal optical-versus-RF selection. When the current action is aggressive clear, choose a real legal unmeasured RF candidate for the comparator; using the aggressive center as though it were the RF point is a different algorithm. If no RF candidate remains or the eight-measure budget is exhausted, full fallback must remain available without using an invalid cheap RF comparator. Cache polygon-derived cells by positive version, but recompute NN route and costs from the current position. The <=12-cell condition is an early-selection gate, never a truncation on required optical coverage. Combine C with F only through the normal explicit optical dispatch outside a burst.

### F5 — M requires spatial mass, full-history cache invalidation and persistent retry limits
- Type: posterior-mass-clear-safety
- Severity: WARNING
- Evidence reference: `experiments/q4_local/design.md`, M50/M75; `src/q4_adaptive.py::ReceptionBelief`; `experiments/q4_transfer/q4_transfer_policies.py::line_estimate/_positive_version/_optimistic_available`; previous `reviews/primary-validation.md`, O and geometry checks.
- Recommended action: Sum spatial posterior mass within 20 m without an RF-heard mask, verify candidate feasibility, and key mass calculations to all RF history while keying retry permission only to new positive observations.

Optical clearing depends on Euclidean distance, not the candidate point's RF reception. Use spatial marginal mass `sum_i w_i * I(distance(point_i,q)<=20)`; multiplying by `_heard(q)` would incorrectly penalize optical success in shadow. Region center, LS estimate and polygon samples must pass legality and polygon membership checks, with finite mass in [0,1]. If no acceptable point remains, select refinement/full fallback directly; inherited center optimism must not be appended. The two mass-attempt limit persists per source, while a negative observation may change RF weights and hence the best mass point without permitting a retry at the same positive version. Accordingly, caching mass by positive count alone is wrong even though that count is appropriate for the unchanged geometric polygon. Current robot position can also change a distance tie-break. Keep a separate mass-attempt event with actual candidate coordinates, mass, positive version and trial number, and use a recognized clear action path. Threshold .50/.75 is a finite discretized-posterior heuristic, not a calibrated success probability or certificate. Certified all-vertex clearing retains priority; failed mass attempts cannot clip the positive polygon.

### F6 — Controls and manifests must separate local mechanisms from the previous global candidate
- Type: factor-and-evidence-design
- Severity: WARNING
- Evidence reference: `experiments/q4_local/design.md`, Scope and controls/Evidence; `experiments/q4_transfer/reviews/primary-validation.md`, F4–F6; `memory.md`.
- Recommended action: Keep radius1950 and the identical global tour selector for each new local arm, report P1/P2 both versus baseline and S_all, and serialize every effective setting of the previous-best comparator.

The new local points and bursts will change realized paths despite an unchanged global optimizer, so the appropriate claim is unchanged routing rule, not unchanged trajectory. P1/P2 versus baseline combines adding S and restricting its budget; the S_all control is needed to attribute the budget effect. C's cost choice, L's ranking and M's candidate criterion should remain isolated in their single-family arms before combinations are selected. The latest previous-best is `JSO_compact_dopt` from the transfer run; reusing the old `previous_best` factory from q4_transfer would instead instantiate the earlier proxy/reuse/early160 scheme. The comparator therefore needs an explicit final effective configuration/factory, not a label alias. The proposed new 400-setting cohort and 200-block inference plan are suitable for another finite comparison; every initial arm must remain visible even if inactive or inefficient, and at most three development-selected combinations must be locked before primary. The prior leading candidates' small unresolved difference and boundary regressions preclude a promised performance gain here.

## Blocking risks
No unresolved design-level blocker was identified for implementing the user-authorized isolated experiment. The warnings above are concrete implementation acceptance conditions; their presence does not establish that the future code satisfies them. This review neither clears a gate nor authorizes adoption. Any actual loss of the positive feasible polygon, mandatory per-channel absence evidence, persistent clear/measurement limits, or complete optical dispatch would require a blocking finding before accepting the experiment's results.

## Non-blocking warnings

### W1 — Scalar action helpers need outcome instrumentation
- Type: audit-observability
- Severity: WARNING
- Evidence reference: Findings F2–F5; `simulator_automation/q4_runner.py::_do_v3_action`; `experiments/q4_local/design.md`, Review and testing.
- Recommended action: Record stop IDs/budget usage, burst parent/index/start/end reason, mass candidate/version/cap and optical proposal/execution separately in `experiments/q4_local/` traces and audit outputs.

These records allow an independent audit to distinguish a proposed action from a real action, a no-op from progress, and an immediate near clear from an additional planned burst step.

### W2 — Soft RF changes require different cache keys from hard geometry
- Type: cache-validity
- Severity: WARNING
- Evidence reference: Findings F1, F4–F5; `src/q4_adaptive.py::ReceptionBelief`; current runner `_region/_reception_belief` cache split.
- Recommended action: Document cache keys in the local implementation: positive version for geometry, full observation history for RF scores/mass, and actual position/channel for travel and switching costs.

## Required follow-up
- Before the first run, record L marginalization, P stop reset/ranking, F physical-outcome/burst semantics, C RF comparator selection and M mass-cache/retry rules in `experiments/q4_local/design.md` or the locked registry (F1–F5).
- Build executor-level checks in `experiments/q4_local/` for repeated same-stop callbacks, actual initial negative/failed-clear burst termination, optical dispatch, mass no-signal retry denial, and certified candidate geometry (F2–F5).
- Store all effective settings for baseline, S_all and the latest `JSO_compact_dopt` comparator in each `experiments/q4_local/` manifest and snapshot; verify the frozen 13-file map remains unchanged (F6).
- Add independent mechanism checks plus the full physical cost/reception/absence replay to `experiments/q4_local/` audit artifacts; require a new result review after the complete primary matrix (W1).
- Keep all development and primary rows, setting-weighted seed-block uncertainty, failures, inactive arms and boundary/tail results in `experiments/q4_local/` reports; do not change `claims/baseline-q4.md` (F6).
- Memory check: recommend documenting full-history mass cache versus positive-version retry permission and the explicit optical-dispatch requirement in `B题/memory.md`; this reviewer did not edit memory.

## Reviewer recommendation
The five local families are concrete, bounded changes aligned with the requested emphasis on local decisions while retaining the existing global route rule. The supplied design includes the necessary geometric fallback and matched controls, and the existing source APIs can support isolated implementation with the integration cautions above. Proceeding to implementation and development verification is reasonable within the existing authorization, while performance, actual mechanism compliance and any future baseline adoption remain separate evidence decisions.

Verdict: PASS_WITH_WARNINGS

## Required reads referenced
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/stage-5-solution-implementation.md` (read in the preceding readiness work).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/subagent-model-building.md` (preceding work).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/subagent-specialists.md` (preceding work).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-markdown-audit.md` (preceding work).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-human-confirmation.md` (preceding work).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-memory-update.md` (preceding work).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-subagent-delegation.md` (preceding work).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-readiness-gate.md` (preceding work).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-rollback.md` (preceding work).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-fallback-and-deviation.md` (preceding work).
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-output-schema.md` (preceding work).
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-self-discipline-checklist.md` (preceding work).
- Every project artifact actually inspected is listed in Reviewed scope; prior review references explicitly identify source inspected earlier rather than newly read files.

## Confidence
medium — the design is precise and the inherited executor interfaces are available, but new policy code and mechanism traces do not yet exist.

## Forbidden-behavior self-check
- [OK] Did not confirm user decisions
- [OK] Did not clear blockers
- [OK] Did not mark stages or rounds complete
- [OK] Did not increase claim level on behalf of the main agent
- [OK] Did not invoke another subagent
- [OK] Did not write or edit project files outside the review output
- [OK] Did not implement policies or run tests/simulations
