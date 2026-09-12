# Q4 Aggressive Experiment — Independent Implementation-Readiness Review

## Reviewed scope

- `experiments/q4_aggressive/reviews/critique.md`, read first; all F1–F8 and B1 considered.
- `experiments/q4_aggressive/design.md`, including post-critique clarifications through line206; `acceptance.md`.
- `experiments/q4_local/reviews/primary-validation.md`.
- `memory.md`, `claims/baseline-q4.md`, `decisions/decision-improvement-round-1.md`.
- Relevant integration hooks in `experiments/q4_local/q4_local_policies.py`, `experiments/q4_transfer/q4_transfer_policies.py`, `experiments/q4_ablation/q4_ablation_policies.py`, `simulator_automation/q4_runner.py`, and `src/q4_adaptive.py`.
- Skill guidance listed under Required reads referenced.

All explicitly requested files were readable. Broader workflow/frontier/sensitivity documents, the general baseline snapshot, claim registry and historical raw results were not inspected. Prior numerical validation and the critique’s reported state-resurrection behavior were not independently reproduced.

## Findings

### F1 — E: Complete execution and survival-cost arithmetic are sufficiently specified

- Type: optical-execution-and-cost
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:153`; `experiments/q4_aggressive/acceptance.md:6`; `simulator_automation/q4_runner.py:213`.
- Recommended action: Independently reconstruct the executed permutation and first-hit cost, including overlaps, failed-cell skips and zero surviving weights.

The clarification correctly requires replacing the nearest-neighbor executor, makes E replace C15, and preserves complete fallback beyond the48/256 ordering thresholds. These address the original implementation ambiguity.

For two cells with first-hit masses \(a,b\) and never-hit mass \(u\), where \(a+b+u=1\), the declared surrogate is \(c_1+(b+u)c_2+2\). The first increment therefore carries mass one; overlapping discs contribute only at their first hit, and never-hit mass pays the entire route.

The `0.05/n_cells` bonus is an ordering incentive, not an additional probability reserve defined by this formula. Uniform restoration of eliminated samples is explicitly heuristic. Neither may prune the hard cover. Audit the scorer’s treatment of skipped failed cells against actual execution, and never broaden “exact failed cell” skipping to N’s1 m retry exclusion. These are future implementation checks, not an unresolved completeness-design blocker.

### F2 — B: The executable current action and virtual continuation are now distinguished

- Type: viewpoint-legality-and-score
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:166`; `experiments/q4_aggressive/design.md:201`; `experiments/q4_local/q4_local_policies.py:86`; `src/q4_adaptive.py:81`.
- Recommended action: Add independent score examples covering coincident points, zero reception mass, illegal virtual viewpoints, deterministic ties and recovery overrides.

The clarification supplies axial candidates, the perpendicular axis, a coincident-point convention, illegal-viewpoint exclusion and a finite fallback. Its continuation term is an **unnormalized heard-weighted sum** plus the78 s non-reception penalty; dividing by reception mass would implement another score.

Legal/fresh filtering must occur after candidate extension, followed by restoration of the proven one-bearing negative-RF bracket. Virtual viewpoints remain planning quantities. B’s comparison tests candidate expansion and scoring together; it cannot isolate the two-step term’s causal contribution. Remaining concerns are implementation/audit checks.

### F3 — G: Budget semantics are defined; callback coverage needs explicit verification

- Type: endpoint-budget-and-charging
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:175`; `experiments/q4_aggressive/design.md:203`; `experiments/q4_ablation/q4_ablation_policies.py:181`; `simulator_automation/q4_runner.py:112`; `src/q4_adaptive.py:60`.
- Recommended action: Audit every eligible endpoint and link each G token to exactly one accepted physical measurement.

The clarified scope is completed cover scans and completed scalar source actions, excluding optical tours and action internals. G replaces inherited detected-channel probes, shares three tokens across callbacks, and resets only after an accepted individual movement>1 m. Mandatory unknown-channel scans remain exempt.

The inherited startup scan has no following supplemental callback; include startup in the completed-cover-boundary acceptance check so it is not silently missed. Verify repeated callbacks and near-clear chains cannot duplicate supplementation.

Recompute switching cost from `measure_channel` after each probe; clearing does not switch that channel. `expected_gain()` already includes reception weighting. Additional multiplication by reception probability changes the specified score. Removal of inherited H-availability suppression addresses the critique’s interaction concern.

### F4 — R: Dedicated counters and bounded fallback are preserved

- Type: dispatch-precedence-and-progress
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:81`; `experiments/q4_aggressive/design.md:189`; `experiments/q4_aggressive/acceptance.md:20`; `simulator_automation/q4_runner.py:606`; `experiments/q4_ablation/q4_ablation_policies.py:213`.
- Recommended action: Verify a precedence matrix and execution-time records containing dedicated count, bearing count, radius and dispatch reason.

The combination contract is implementable as sequential proposal transformations: certified clear retains priority; construct H/B/L’s base action; apply E or C; then apply eligible R. Eligible R can suppress H, while E still controls the resulting optical order.

R2/R4 must count actual dedicated measurements, excluding discovery and G probes. An optical task must reach `_optical_fallback`, never the scalar executor’s measurement branch. One-bearing, oversized and otherwise ineligible regions retain cap8 and complete fallback. These are future behavioral checks, not evidence that R already improves efficiency.

### F5 — H: Retry ownership must remain separate from N

- Type: speculative-retry-accounting
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:89`; `experiments/q4_aggressive/design.md:178`; `experiments/q4_transfer/q4_transfer_policies.py:64`; `experiments/q4_transfer/q4_transfer_policies.py:158`.
- Recommended action: Audit independent H/N ledgers against physical clears, including proposals displaced by C/E/R and failed-point no-ops.

The direct frozen scalar call with explicit H registration avoids inherited O accounting accidentally charging every `aggr_clear` to H. N must not enter that registration path.

Retain two direction bearings, `cond(A)<=30`, legal polygon membership and failed-point exclusion. H and N each require their own two-trial limit and positive-version restriction; negative RF cannot renew permission. Only actual trials consume tokens. Polygon membership remains insufficient for a certified20 m clear.

Shared failed-clear geometry can also change later LC center eligibility; report that interaction rather than attributing N’s entire effect to zero walking. No unresolved retry-design blocker remains, but combination acceptance is essential.

### F6 — N: Post-critique endpoint placement addresses upstream B1

- Type: callback-lifecycle-and-state-consistency
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/reviews/critique.md`, F6/B1; `experiments/q4_aggressive/design.md:175`; `experiments/q4_aggressive/design.md:197`; `simulator_automation/q4_runner.py:158`; `simulator_automation/q4_runner.py:180`.
- Recommended action: Add adversarial lifecycle acceptance for N alone and N+G/H/E, checking physical events and final source state.

The original hazard requires N to succeed while an enclosing scan/near-clear/fallback chain still has another clear pending. The revised contract places callbacks after the complete scalar action or scan, prohibits callbacks inside optical tours, and rechecks status before endpoint actions. That addresses the identified failure path at the design level.

The inherited `_try_clear_at()` still lacks an already-cleared guard. Consequently, implementation must honor the caller-status checks, recursion guard and stale-task prohibition. Acceptance should establish no duplicate clear, no source resurrection, no optical-tour callback, exact current-position execution, at most two N trials and no retry within1 m of a failed point. These remain future tests; this review does not close the parent’s B1 record.

### F7 — Ranking correctly separates all400 eligibility from general350 efficiency

- Type: estimand-and-selection
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:12`; `experiments/q4_aggressive/design.md:108`; `experiments/q4_aggressive/reviews/critique.md`, F7; `claims/baseline-q4.md:13`.
- Recommended action: Independently reconstruct eligibility, cohort summaries, paired comparisons and seed-block resampling.

Rank only arms with every setting completed, `K=N`, valid clearing/absence or counting certificates, and no unresolved failure. Rank eligible arms by the setting-weighted general350 mean(T/K); report stress50 and all400 metrics, failures, tails and costs. Stress cost regression is explicitly allowed.

Bootstrap whole seeds using general-setting sums divided by resampled general-setting counts. The first50 blocks contain four general settings each; the remaining150 contain one. Equal weighting of block means would change the declared estimand.

Development selection, ties and zero/one-improving-family behavior are specified. Preserve all16 initial arms and locked combinations. Compare against contemporaneous frozen V4 and LC separately; historical517.584293 s/source is the baseline anchor, not this batch’s improvement denominator.

### F8 — Effective controls and immutable evidence are specified

- Type: control-identity-and-provenance
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:25`; `experiments/q4_aggressive/acceptance.md:31`; `experiments/q4_local/q4_local_policies.py:64`; `experiments/q4_transfer/q4_transfer_policies.py:91`; `experiments/q4_ablation/q4_ablation_policies.py:71`.
- Recommended action: Verify expanded control configurations against pinned sources and preserve complete dependency, scenario, event and analysis manifests.

Explicit LC/LPC and `JSO_compact_dopt` factories address the ambiguous `previous_best` name: the transfer factory’s same label selects a different older control. Record actual runner class, expanded configuration and source hashes.

Preserve radius1950/tour for new candidates and the declared radius1900/center/S/O/D-optimal prior control. Restore process-global cover context after every job and avoid conflicting concurrent contexts within one process. Retain failed/resource-limited outcomes, all physical charges and certificates, and separately hash final analysis/review artifacts. These are execution-acceptance requirements.

## Blocking risks

No unresolved design blocker identified within the inspected scope. Upstream F6/B1 has a concrete design mitigation; its implementation remains unverified and its formal disposition belongs to the parent.

The existing adoption decision explicitly excludes already-authorized experiments from its blocking scope. No renewed authorization or stress-cost non-regression requirement is warranted.

## Non-blocking warnings

### W1 — Efficiency gains remain hypotheses

- Type: heuristic-performance-uncertainty
- Severity: WARNING
- Evidence reference: `experiments/q4_local/reviews/primary-validation.md:74`; `memory.md:23`; Findings F1–F5.
- Recommended action: Preserve inactive and losing arms and distinguish predicted scores from measured outcomes.

Prior M trials did not improve mean efficiency, and O added little on JS. Wider thresholds or more elaborate scores therefore provide no established gain or calibrated success probability.

### W2 — Finite offline completion has a limited claim scope

- Type: resource-and-evidence-limit
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:132`; `experiments/q4_ablation/q4_ablation_policies.py:183`; `claims/baseline-q4.md:44`.
- Recommended action: Report planner wall time, resource failures and iteration limits alongside simulated action costs.

Complete geometric fallback and successful offline batches do not establish official deadline completion, an official score or optimality.

## Required follow-up

- Expand `experiments/q4_aggressive/acceptance.md` with the F1–F6 edge cases, startup callback coverage, duplicate-clear checks and selected-combination interactions.
- Carry F1–F8 dispositions and the B1 design mitigation into parent-owned `gates/` or scoped `decisions/` records without relabeling the critique.
- Under `experiments/q4_aggressive/`, preserve control/configuration locks and immutable manifests before batches; independently validate development before primary execution.
- In the eventual aggressive report and audits, reconstruct general350/stress50/all400 metrics, physical charges, completion certificates and mechanism activations; preserve `claims/baseline-q4.md`.

## Reviewer recommendation

The clarified design is sufficiently specified for the parent to consider isolated implementation. No unresolved design blocker is identified; the remaining warnings concern explicit acceptance checks and evidence interpretation. This recommendation does not certify execution, promise performance gains, change claims, authorize baseline adoption or clear any gate.

Verdict: PASS_WITH_WARNINGS

## Required reads referenced

- All project artifacts actually opened are listed under Reviewed scope.
- `C:/Users/zty/.agents/skills/math-modeling-v4/SKILL.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/subagent-improvement-skepticism.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-subagent-delegation.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/stage-5-solution-implementation.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-readiness-gate.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-output-schema.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-self-discipline-checklist.md`

## Confidence

medium — the requested design and integration hooks support this readiness assessment, but no aggressive implementation, execution evidence or historical raw-artifact reconstruction was reviewed.

## Forbidden-behavior self-check

- [OK] Read the upstream critique before reviewing.
- [OK] Did not confirm decisions or request reconfirmation.
- [OK] Did not clear blockers or gates.
- [OK] Did not mark stages or rounds complete.
- [OK] Did not increase claim levels or adopt a baseline.
- [OK] Did not spawn agents.
- [OK] Did not implement, run tests/simulations or modify files.
- [OK] Used the frozen per-question baseline as the anchor.
- [OK] Addressed every critique F-ID with evidence and explicit recommendations.
- [OK] Distinguished future verification from unresolved design blockers.
- [OK] Preserved full clearing while allowing authorized stress-cost regression.
- [OK] Left gate handling and continuation decisions to the parent.