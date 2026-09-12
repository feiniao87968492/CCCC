## Reviewed scope

- `experiments/q4_aggressive/reviews/critique.md` (F1–F8, B1)
- `experiments/q4_aggressive/reviews/implementation-readiness.md`
- `experiments/q4_aggressive/design.md`
- `experiments/q4_aggressive/acceptance.md`
- `experiments/q4_local/primary400/report.md`
- `experiments/q4_local/reviews/primary-validation.md`
- `experiments/q4_local/q4_local_policies.py`
- `experiments/q4_transfer/q4_transfer_policies.py`
- `experiments/q4_ablation/q4_ablation_policies.py`
- `simulator_automation/q4_runner.py`
- `src/q4_adaptive.py`
- `src/q4_state.py`
- `memory.md`
- `claims/baseline-q4.md`
- `claims/baseline-snapshot.md`
- `claims/claim-registry.md`
- `decisions/decision-q4-aggressive-experiment.md`
- `improvements/improvement-frontier.md`
- `improvements/improvement-log.md`
- Required math-modeling-v4 protocol, reviewer-schema, and reviewer-discipline references.

## Findings

### F1 — E cost surrogate remains only partially tied to executable behavior

- Type: optical-cost/execution mismatch
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:34`, `experiments/q4_aggressive/design.md:153`, `simulator_automation/q4_runner.py:213`, `experiments/q4_local/primary400/report.md`
- Recommended action: Require an implementation-independent reconstruction of the executed permutation, failed-cell handling, first-hit indices, and charged route increments before accepting E evidence.

The critique correctly identified the original nearest-neighbor mismatch, but its clarification does not eliminate the risk. The all-zero case explicitly restores uniform weights over the original samples after failed-disc conditioning, so samples removed from the soft posterior can re-enter the ordering calculation. The first-hit formula also remains a planning quantity whose `j_i` mapping must be reconstructed from the actual cell sequence and physical clear outcomes. The prior local matrix provides no evidence that optical-cost proxies predict gains; C15 improved mean T/K by only 2.082%, while F and M produced no useful average gain.

### F2 — B is executable on paper but still vulnerable to proxy degeneracy

- Type: two-step proxy degeneracy
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:54`, `experiments/q4_aggressive/design.md:166`, `experiments/q4_aggressive/design.md:201`, `src/q4_adaptive.py:81`
- Recommended action: Add deterministic score fixtures for coincident `q=g`, duplicate candidates, zero heard mass, illegal virtual viewpoints, and recovery overrides, and preserve every score term in execution logs.

The clarification distinguishes virtual viewpoints from physical actions, but the coincident-point `(1,0)` convention and the `+78` fallback can create discontinuous rankings at exactly the cases likely to occur near a compact region. Candidate expansion and scoring are a combined intervention, so any paired improvement cannot establish that the continuation term caused the change. The existing `ranked_refinement_points` implementation still uses heuristic posterior weights and does not provide calibrated continuation probabilities.

### F3 — G’s stated endpoint coverage does not prove complete callback coverage

- Type: callback/budget accounting
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:70`, `experiments/q4_aggressive/design.md:175`, `simulator_automation/q4_runner.py:158`, `simulator_automation/q4_runner.py:606`, `experiments/q4_transfer/q4_transfer_policies.py:158`
- Recommended action: Require an event-level ledger showing every eligible endpoint, threshold rejection, accepted measurement, channel switch, and stop reset, including startup and source actions.

The design excludes action internals and optical tours, but the runner has separate cover-scan, detected-channel, source-action, and optical paths. A callback placed only around one parent hook can still miss a path or double-count a path. The `5 + (measure_channel != k)` expression must be reconstructed from physical measurement events, and every budget token must map to exactly one accepted measurement. Prior P evidence shows that fewer probes and lower time are distinct tradeoffs, so probe-count changes cannot serve as a proxy for G success.

### F4 — R precedence can suppress the mechanism it is meant to test

- Type: precedence/confounding
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:81`, `experiments/q4_aggressive/design.md:189`, `experiments/q4_ablation/q4_ablation_policies.py:181`
- Recommended action: Freeze and audit a precedence table at execution time, recording whether R was eligible, proposed, selected, or displaced by E, C, H, or B/L.

The sequential rule “base action, then E/C, then R” permits E to convert the action to optical before R is considered, making R inactive in precisely the compact cases where its effect is expected. Dedicated-measurement counters must be distinguished from discovery and supplemental probes, and scheduler proposals must not be counted as executions. Without those records, a null R result cannot distinguish ineffective logic from unreachable dispatch.

### F5 — H retry identity is still exposed to inherited optimistic state

- Type: speculative-retry accounting
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:89`, `experiments/q4_aggressive/design.md:178`, `experiments/q4_transfer/q4_transfer_policies.py:105`, `experiments/q4_transfer/q4_transfer_policies.py:129`, `memory.md`
- Recommended action: Use a dedicated H ledger keyed by source, positive-observation version, attempted coordinate, and outcome, and prove that inherited O counters cannot consume or renew H attempts.

The readiness review assumes explicit H registration is sufficient, but the inherited runner classifies generic `aggr_clear` actions through optimistic machinery. H’s two-attempt limit, one attempt per positive version, and failed-point exclusion therefore remain integration-sensitive. A negative observation must never renew permission, and a near result followed by a clear must have one unambiguous H identity. The prior local validation shows wider speculative mechanisms can be active without improving mean efficiency.

### F6 — N/B1 remains a concrete state-corruption blocker

- Type: reentrant clear/state resurrection
- Severity: BLOCKING
- Evidence reference: critique `F6` and `B1`; `experiments/q4_aggressive/design.md:197`; `simulator_automation/q4_runner.py:180`; `simulator_automation/q4_runner.py:213`; `src/q4_state.py:152`; `tests/test_q4_geomsim.py:67`
- Recommended action: Require a state-safe N implementation that rejects already-cleared targets inside `clear`/`_try_clear_at`, cancels stale enclosing actions after nested success, and proves no failed duplicate clear can restore `detected`.

The endpoint-only clarification narrows callback placement but does not itself change the inherited state transition. `Q4State.apply_clear(..., success=False)` sets a channel back to `detected` and `cleared=False`; `_try_clear_at` checks failed coordinates but not already-cleared status. Thus a nested N success followed by an enclosing stale clear can still issue a second physical clear and resurrect state after failure. No implementation or adversarial execution evidence exists. This is the same failure mode identified by critique F6/B1 and remains unresolved at the implementation boundary.

### F7 — General350 selection still needs an explicit certification/K rule

- Type: estimand/eligibility ambiguity
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:10`, `experiments/q4_aggressive/design.md:108`, `experiments/q4_aggressive/acceptance.md`, `claims/baseline-q4.md`, `experiments/q4_local/primary400/report.md`
- Recommended action: Define one machine-checkable all400 eligibility predicate covering failures, `all_certified`, source-clear counts, absence/counting certificates, and the denominator used for T/K before development selection.

The critique’s general350-after-all400 rule is directionally correct, but “complete clearing,” `K=N`, and counting-certificate eligibility are not stated as one consistent predicate. The frozen baseline reports 5,208 cleared sources across 400 settings while also treating the N=16 counting certificate as independent of geometric clearing. If certified-absent channels are included in eligibility but excluded from K, or if K=N is interpreted literally, rankings and denominators change. The 350-setting mixture must use setting-weighted sums and counts, with stress results retained regardless of ranking.

### F8 — Control and provenance risks remain operational

- Type: control identity/evidence provenance
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/design.md:25`, `experiments/q4_aggressive/design.md:134`, `experiments/q4_local/q4_local_policies.py:64`, `experiments/q4_transfer/q4_transfer_policies.py:91`, `experiments/q4_ablation/q4_ablation_policies.py:71`, `improvements/improvement-frontier.md`
- Recommended action: Capture expanded factory configuration, effective runner class, radius context, dependency hashes, scenario hashes, event hashes, and complete failed outcomes for every arm.

The same label can resolve to different factories: `previous_best` in local and transfer code is not inherently the same effective control. Process-global cover context and shared module imports also make configuration identity runtime-sensitive. The prior local report shows LPC at 515.618001 s/source while the prior JSO control rerun is lower at 513.488873, so control identity materially affects interpretation. Packaging metadata alone cannot establish matched execution.

## Blocking risks

### B1 — N endpoint lifecycle

- Target proposal: Critique F6 / B1, N20/N50.
- Failure mode: A nested N clear succeeds, the enclosing caller continues with a stale clear or fallback, the second physical clear fails, and `apply_clear(success=False)` restores the source to `detected`.
- Required mitigation: Before implementation or execution, add an explicit state-transition contract and implementation check covering already-cleared rejection, stale-task cancellation, post-nested-success return, duplicate-clear prevention, and N+G/H/E combinations. Carry this risk into the scoped decision and readiness artifacts; do not treat endpoint placement alone as clearance.

### B2 — Ambiguous all400 eligibility can change the selected estimand

- Target proposal: Critique F7.
- Failure mode: Arms are ranked using inconsistent treatment of certified absence, `K`, failed scenes, or stress settings, producing a selected candidate whose reported general350 mean is not the declared conditional estimand.
- Required mitigation: Freeze a machine-readable eligibility and denominator schema in `experiments/q4_aggressive/design.md` and each batch manifest, then independently reconstruct ranking from raw rows before any selection decision.

## Non-blocking warnings

### W1 — No aggressive performance result exists

- Type: evidence ceiling
- Severity: WARNING
- Evidence reference: `experiments/q4_aggressive/acceptance.md`, `decisions/decision-q4-aggressive-experiment.md`, `memory.md`
- Recommended action: Treat all E/B/G/R/H/N deltas as prospective hypotheses and retain the frozen `feasible_baseline` claim unchanged.

### W2 — Prior evidence argues against automatic optimism

- Type: prior-sensitivity warning
- Severity: WARNING
- Evidence reference: `experiments/q4_local/primary400/report.md`, `experiments/q4_local/reviews/primary-validation.md`, `improvements/improvement-frontier.md`
- Recommended action: Preserve losing and inactive arms, 92 LPC losses, stress tails, and the lower observed prior-JSO mean in all later reports.

## Required follow-up

- Resolve B1/F6 in `experiments/q4_aggressive/design.md` and the isolated implementation contract.
- Freeze E/B formulas, degeneracy fixtures, and executed-route reconstruction under `experiments/q4_aggressive/acceptance.md`.
- Add G endpoint coverage and physical charge ledgers under `experiments/q4_aggressive/`.
- Add R precedence and H/N retry ledgers keyed to actual executions and positive versions.
- Define all400 eligibility, certified-absence treatment, K denominator, and general350 aggregation in `experiments/q4_aggressive/design.md` and batch manifests.
- Record expanded control factories, runtime cover context, dependency snapshots, and immutable event/output hashes under `experiments/q4_aggressive/`.
- Preserve `claims/baseline-q4.md`, `claims/baseline-snapshot.md`, and `claims/claim-registry.md`; any later method adoption requires the rollback and evidence gates.

## Reviewer recommendation

The critique identifies useful local hypotheses and the readiness review improves their textual specification, but the N callback state transition remains capable of corrupting completion, and the all400 eligibility denominator is still insufficiently explicit for a defensible selection rule. Existing local results provide no observed evidence for aggressive gains, and prior controls materially affect interpretation. Do not clear B1/F6 or proceed as though the design has passed implementation readiness.

Verdict: BLOCKED

## Required reads referenced

- `C:/Users/zty/.agents/skills/math-modeling-v4/references/subagent-improvement-skepticism.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/subagent-improvement-critique.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-improvement-loop.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-subagent-delegation.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-readiness-gate.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-rollback.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-output-schema.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-self-discipline-checklist.md`
- Project artifacts listed under Reviewed scope.

## Confidence

medium — static inspection and prior validated local results support the integration and estimand risks, but no aggressive implementation or execution evidence was available.

## Forbidden-behavior self-check

- [OK] Did not confirm user decisions
- [OK] Did not clear blockers
- [OK] Did not mark stages or rounds complete
- [OK] Did not increase claim level on behalf of the main agent
- [OK] Did not invoke another subagent
- [OK] Did not write or edit project files
- [OK] Compared against the frozen baseline snapshot, not the previous round
- [OK] Did not silently approve proposals
- [OK] Did not propose bypasses to readiness or rollback protocols
- [OK] Did not run without an upstream Critique review file
- [OK] Every Blocking risk includes an evidence reference and required mitigation
- [OK] Did not reject proposals without evidence references