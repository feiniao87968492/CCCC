# Q4 Improvement Round 1 Critique

## Reviewed scope
- `B题/claims/baseline-q4.md`
- `B题/claims/baseline-snapshot.md`
- `B题/claims/claim-registry.md`
- `B题/data/sensitivity/sensitivity-report.md`
- `B题/gates/stage6-q4-validation.md`
- `B题/improvements/improvement-frontier.md`
- `B题/src/q4_policy.py`
- `B题/src/q4_adaptive.py`
- `B题/src/q4_state.py`
- `B题/src/q4_cover.py`
- `B题/src/q4_certificate.py`
- `B题/simulator_automation/q4_runner.py`
- `B题/experiments/q4_efficiency/bench.py`
- `B题/experiments/q4_efficiency/release_holdout100.json`
- `B题/experiments/q4_hex37/grid_v3.json` (first three parameter rows only)
- `B题/tests/test_q4_regressions.py`
- `B题/reviews/stage6-validation-review.md`
- `B题/improvements/improvement-log.md` (read attempted; absent at review time)
- `B题/memory.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-improvement-loop.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-readiness-gate.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-rollback.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-subagent-delegation.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-output-schema.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-self-discipline-checklist.md`

The comparison anchor is the frozen endpoint/mixed holdout (seeds 1000–1099): mean T/K 517.5842931731096 s, mean T 6682.781249650514 s, mean movement 24742.356248252563 m (4948.471249650514 s), and mean probes 279.73 (243.78 discovery, 35.95 refinement), with 100/100 certified success. Existing sensitivity cohorts are descriptive; they are not causal evidence for any proposal below.

All numerical ranges below are preregistered hypotheses to falsify, not measured results or confidence intervals. The user has requested candidate experiments; the main agent owns recording that authorization and deciding its scope. This review neither confirms a decision nor requires the user to repeat authorization already provided. The frontier contains no prior F-ID or abandoned proposal; the improvement log is absent and needs initialization by the main agent.

## Findings

### F1 — Nearest-task insertion with bounded replanning
- Type: movement-route-ablation
- Severity: WARNING
- Evidence reference: `B题/simulator_automation/q4_runner.py` (`_run_adaptive_v4`, `pending_batch_order`); `B题/src/q4_policy.py` (`pending_batch_order`, `act_now_vs_lookahead`); `B题/data/sensitivity/sensitivity-report.md` (movement is 74.05% of T)
- Recommended action: Open `decisions/decision-improvement-round-1.md` for a paired route-policy branch that compares the current full-task replan, nearest task, and task-cost score with an identical certificate path.
- Hypothesis: Replacing full-task open-path replanning with nearest-task or service-time-adjusted selection will reduce movement while preserving 100/100 certification on the frozen holdout.
- Expected metric delta: Mean movement −5% to −12% (approximately −1,240 to −2,970 m), mean T/K −15 to −40 s, and probes no worse than +2%; reject the arm if full success is below 100/100 or p95 T/K rises by more than 5%.
- Implementation cost: roughly 50–100 experiment-only lines plus paired harness work; existing Python/NumPy and a runner subclass suffice.
- Required new data or solver: no; use existing `NoisyGeomSim`, cover certificate, and `pending_batch_order` footprint.
- Touches confirmed method or model structure: yes — method revision; prepare a rollback document under `rollbacks/` before adopting the arm.
- Suggested claim level after success: retain `feasible_baseline`; only an updated Stage 6 review may bind a new efficiency claim.

Candidate switches: `full_route`, `nearest`, and `task_cost`. For `task_cost`, score travel/5 plus observable service cost (required unseen-channel scans and channel-switch overhead for a cover task, 5–6 s for a measure, 3 s for a trial clear), with a fixed cover/progress weight reported in the manifest. The baseline DP is exact only for its current static task set at size <=10; larger sets use NN+2-opt. Neither is a global optimum for the adaptive problem. Observations replace source tasks and N=16 discovery can remove the entire remaining cover, so optimizing the current complete path can select a poor immediate action. Bounded lack-of-progress and fallback rules are required; planner CPU improvement is separate from virtual walking-time improvement.

### F2 — Coverage-station refinement reuse with high-gain deferral
- Type: probe-movement-joint-ablation
- Severity: WARNING
- Evidence reference: `B题/simulator_automation/q4_runner.py` (`_refinement_points`, `_probe_detected_at_v4`, `_adaptive_task`); `B题/src/q4_adaptive.py` (`ranked_refinement_points`, `ReceptionBelief`); `B题/data/sensitivity/sensitivity-report.md` (35.95 refinement probes and high boundary probe count)
- Recommended action: Open a decision branch that adds the already-needed cover stations to the refinement candidate set and defers a dedicated refinement only when a specific future station has high reception/gain and lower estimated added travel; log the promised station and defer reason.
- Hypothesis: Reusing mandatory TRI25 station visits for refinement and deferring low-gain points will reduce refinement probes and localization walking without reducing scene certification.
- Expected metric delta: Refinement probes −20% to −40% (about −7 to −14 probes per case), movement −3% to −8% (−740 to −1,980 m), mean T/K −10 to −30 s; no more than 1/100 paired regressions over +50 s is acceptable.
- Implementation cost: roughly 60–120 experiment-only lines; expose `gain_per_detour` and defer thresholds while using the existing positive-observation region and optical fallback.
- Required new data or solver: no; existing belief and certificate code are sufficient.
- Touches confirmed method or model structure: yes — method revision; rollback severity is method revision if refinement scheduling changes, while the certificate remains unchanged.
- Suggested claim level after success: `feasible_baseline` with a paired average-efficiency statement; do not claim per-scene optimality.

Evaluate candidate enrichment alone, enrichment plus deferral, and baseline. Require reception probability >=0.7 and expected log-radius gain >=0.3 at the promised cover station, then sweep stricter values independently; limit waiting to 1–3 scheduled cover visits and cancel a promise when the cover is no longer needed or its current gain drops. Never defer solely because the current dedicated point has low gain: both options can be bad. Returning a cover-coordinate source task must cause a real `scan_at` sweep for unseen channels before that site is considered globally visited; `measure` records only the measured channel's site, so an incorrect visited-set shortcut can invalidate discovery.

### F3 — Configurable opportunistic-probe gate, including an off arm
- Type: probe-suppression-ablation
- Severity: WARNING
- Evidence reference: `B题/simulator_automation/q4_runner.py` (`_probe_detected_at_v4`, reception probability and expected-gain thresholds); `B题/src/q4_adaptive.py`; `B题/data/sensitivity/sensitivity-report.md` (243.78 discovery probes and 230.54 discovery no-signal probes)
- Recommended action: Include in `decisions/decision-improvement-round-1.md` a gate matrix (`off`, baseline `.7/.3`, strict `.85/.5`, permissive `.55/.2`) only for detected channels, preserving required unseen-channel scans.
- Hypothesis: Turning off or tightening opportunistic probes for already-detected channels will cut probe count with at most a small movement penalty because required TRI25 scans already provide the absence certificate.
- Expected metric delta: Mean total probes −0% to −3% (0 to approximately 8.4 probes), movement between −1% and +3%, mean T/K −0 to −5 s; reject efficiency superiority if extra movement erases probe savings, and reject deployment eligibility for any certification/source-completion failure.
- Implementation cost: roughly 15–35 experiment-only lines to override `_probe_detected_at_v4`; retain deterministic latent scenes and report discovery/refinement probes separately.
- Required new data or solver: no; no new solver or source data is needed.
- Touches confirmed method or model structure: yes — method revision; record the experimental scheduling deviation under `rollbacks/`; changing unknown-channel certificate inputs would require a separate structural decision.
- Suggested claim level after success: retain `feasible_baseline`; report a probe-efficiency bound only after Stage 6 revalidation.

The baseline already scans unseen channels only at required cover stops. The screenshot's unknown-at-every-stop comparison must therefore be an explicitly separate negative control, not described as a new optimization of V4. All opportunistic probes belong to the 35.95 refinement-probe total; without indirect route changes, eliminating that entire category would save at most 12.85% of all probes, and the true opportunistic subset is smaller. Log `n_probe` independently from `n_measure`. Extra optical fallback or failed clears are cost diagnostics, not automatic correctness failures: the baseline itself averages 18.25 clear attempts for 13.24 sources.

### F4 — Aggressive bounded center-clear radius and retry schedule
- Type: clearance-policy-ablation
- Severity: WARNING
- Evidence reference: `B题/simulator_automation/q4_runner.py` (`_adaptive_task`, `_do_v3_action`); `B题/src/q4_policy.py` (`V3Params.aggressive_clear_rho`, `aggressive_clear_max`); `B题/data/sensitivity/sensitivity-report.md` (35.95 refinement probes and 0.04 optical fallback mean)
- Recommended action: Include a grid of experiment-only center-clear thresholds `{80,120,160,220}` m and attempt caps `{1,2,3}` in the decision document, with an explicit failed-clear budget and unchanged optical coverage.
- Hypothesis: Clearing near the posterior center earlier, with at most three bounded retries, will replace some refinement measurements and reduce travel on small regions.
- Expected metric delta: Mean refinement probes −5% to −15% (−2 to −5 probes), movement −2% to −6% (−500 to −1,500 m), mean T/K −5 to −20 s; failed clears may increase by up to 0.5 per case but full certification must remain 100/100 and p95 T/K must not increase over 5%.
- Implementation cost: roughly 25–50 experiment-only lines overriding `_adaptive_task`; V4 hard-codes 80 m/two failed trials, so changing `V3Params` alone would be a no-op for this baseline.
- Required new data or solver: no; existing bounded-error simulator is sufficient.
- Touches confirmed method or model structure: yes — method revision; prepare `rollbacks/` because an over-aggressive radius can increase tail cost and optical fallback.
- Suggested claim level after success: `feasible_baseline`, with only an average paired efficiency claim.

Use one shared experiment setting across every V4 path that can attempt a heuristic center clear; audit `_try_localize` if the subclass invokes it. Never classify a trial at rho >20 m as a certified clear and never shrink the positive-observation polygon from failure. Counterevidence: the first three historical HEX37 grid rows at fixed insertion settings show rho 80 to 100/120 slightly worsened T/K (682.993 to 683.478) while reducing only 0.4 probes. This different route/cohort is not a baseline comparison, but it makes benefit at 160/220 m a low-confidence hypothesis worth exposing rather than assuming.

### F5 — Leaner certified cover geometry (separate structural branch)
- Type: cover-geometry-ablation
- Severity: WARNING
- Evidence reference: `B题/src/q4_cover.py` TRI25 construction; `B题/src/q4_certificate.py` `discovery_certificate`; `B题/claims/baseline-q4.md` certificate (`max_distance_m` 943.0121947375769 m, margin 17.74943008678929 m)
- Recommended action: Create `branches/q4-lean-cover-readiness.md` and test a reduced-point cover only after recomputing the continuous certificate, hull margin, and directional witness property; do not modify TRI25 in place.
- Hypothesis: Removing redundant interior or boundary stations while maintaining the certificate will reduce mandatory scan walking and discovery probes.
- Expected metric delta: If a valid certificate survives, target movement −8% to −18% (−1,980 to −4,450 m), probes −5% to −15% (−14 to −42), and T/K −20 to −60 s; any certificate invalidity or success loss is an immediate rejection.
- Implementation cost: several hours to days depending on search extent; first use a bounded deterministic subset/geometry search and the existing SciPy certificate, with strict wall-time/candidate limits.
- Required new data or solver: no for the first bounded search using existing SciPy; `branches/q4-lean-cover-readiness.md` is still required for fresh certificate evidence. Any later MILP/CP-SAT route is an additional solver branch and cannot be presumed available.
- Touches confirmed method or model structure: yes — structural revision; mandatory `rollbacks/` document and user decision before any baseline replacement.
- Suggested claim level after success: keep `feasible_baseline` until a new Stage 5 readiness and Stage 6 validation gate; no global/minimal-cover claim.

## Blocking risks

### B1 — Certificate and per-channel accounting must survive scheduling changes
- Type: certificate-accounting-risk
- Severity: BLOCKING
- Evidence reference: F2/F3/F5; `B题/src/q4_state.py` (`can_certify_absent`, `apply_measure`); `B题/simulator_automation/q4_runner.py` (`scan_at`, `_cover_need`)
- Recommended action: The main agent must record the certificate invariants in `gates/stage5-q4-ablation-readiness.md`, require actual full unseen-channel sweeps at reused cover stations, and keep F5 unavailable to performance ranking until its continuous certificate passes.

### B2 — Adaptive execution can invalidate a superficial paired comparison
- Type: paired-evidence-risk
- Severity: BLOCKING
- Evidence reference: F1–F4; `B题/tests/test_q4_regressions.py` (`NoisyGeomSim` coordinate-stable noise); `B题/experiments/q4_efficiency/bench.py` (`random_sources`, summary construction)
- Recommended action: Record identical latent-scene hashes, coordinate-stable error mode, full failure rows, original N and realized K in the experiment manifest/report; never calculate superiority from successful scenes alone or confuse mean(T/K) with sum(T)/sum(K).

These are conditions for valid experimental evidence and promotion, not statements that candidate exploration is unauthorized. The main agent owns confirming whether mitigation evidence satisfies them.

## Non-blocking warnings

### W1 — Average metrics can hide N=16 regressions
- Type: paired-tail-risk
- Severity: WARNING
- Evidence reference: `B题/claims/baseline-q4.md` (97/100 faster than HEX37/V3; slower seeds 1065, 1092, 1093; worst +48.260035145791505 s)
- Recommended action: Preserve per-seed deltas, p95, worst delta, and failed-clear/after-last-clear tails in `B题/experiments/q4_efficiency/` for every arm.

### W2 — Offline evidence cannot support an official-simulator claim
- Type: evidence-path-limit
- Severity: WARNING
- Evidence reference: `B题/claims/baseline-q4.md`; `B题/gates/stage6-q4-validation.md` (official simulator blocked)
- Recommended action: Keep all improvement claims at offline feasible-baseline scope and rerun Stage 6 before updating `B题/claims/claim-registry.md`.

### W3 — Module defaults can silently select a different scheme
- Type: reproducibility-risk
- Severity: WARNING
- Evidence reference: `B题/claims/baseline-q4.md` (explicit replay command); `B题/src/q4_policy.py` and `B题/experiments/q4_efficiency/bench.py` defaults
- Recommended action: Pass explicit `--cover TRI25 --route ROUTE_ADAPTIVE_V4 --error-mode endpoint --seed-start 1000 --cases 100` for the baseline arm and record all strategy parameters in each manifest.

## Required follow-up
- Create `decisions/decision-improvement-round-1.md` covering F1–F5 and preloading the conditional certificate risk.
- Create `improvements/round-1.md` with `Target question: Q4` and `Cross-question impact expected: none`; compare every arm to `B题/claims/baseline-q4.md`.
- Add isolated strategy runners/flags under `B题/branches/` or `B题/experiments/q4_efficiency/` without editing frozen result artifacts.
- For F5, write `branches/q4-lean-cover-readiness.md`, then obtain readiness and rollback decisions before any code change.
- Run matched endpoint/mixed holdout seeds 1000–1099 and stress strata; report success, certification, T/K, T, movement, discovery/refinement probes, failed clears, optical fallback, p95, worst paired delta, and failure rows.
- After an accepted arm, write a new `reviews/stage6-validation-review.md` artifact or round-specific validation review and update claims only through the evidence gate.

## Reviewer recommendation
Proceed to adversarial Skepticism review and a user-confirmed decision document for F1–F4 as reversible method branches. F5 is a separate structural branch: its potential movement reduction is attractive, but the 17.75 m baseline hull margin leaves little room for removing witnesses without a fresh continuous certificate. No proposal should replace the frozen TRI25/V4 baseline or raise the `feasible_baseline` claim ceiling before readiness, rollback, and Stage 6 evidence are complete.

Verdict: PASS_WITH_WARNINGS

## Required reads referenced
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/subagent-improvement-critique.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-improvement-loop.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-readiness-gate.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-rollback.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-subagent-delegation.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-output-schema.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-self-discipline-checklist.md`
- `B题/claims/baseline-q4.md`
- `B题/claims/baseline-snapshot.md`
- `B题/claims/claim-registry.md`
- `B题/data/sensitivity/sensitivity-report.md`
- `B题/gates/stage6-q4-validation.md`
- `B题/improvements/improvement-frontier.md`
- `B题/src/q4_policy.py`
- `B题/src/q4_adaptive.py`
- `B题/src/q4_state.py`
- `B题/src/q4_cover.py`
- `B题/src/q4_certificate.py`
- `B题/simulator_automation/q4_runner.py`
- `B题/experiments/q4_efficiency/bench.py`
- `B题/experiments/q4_efficiency/release_holdout100.json`
- `B题/experiments/q4_hex37/grid_v3.json` (first three parameter rows only)
- `B题/tests/test_q4_regressions.py`
- `B题/reviews/stage6-validation-review.md`
- `B题/improvements/improvement-log.md` (read attempted; absent at review time)
- `B题/memory.md`

## Confidence
medium — the baseline bottlenecks and code controls are directly supported, but candidate gains have not been measured and the historical aggressive-clear grid contains counterevidence.

## Forbidden-behavior self-check
- [OK] Did not confirm user decisions
- [OK] Did not clear blockers
- [OK] Did not mark stages or rounds complete
- [OK] Did not increase claim level on behalf of the main agent
- [OK] Did not invoke another subagent
- [OK] Did not write or edit project files outside the review output
- [OK] Compared against baseline snapshot, not the previous round
- [OK] Did not silently approve proposals
- [OK] Did not propose changes that bypass v4 readiness gate or rollback protocols
- [OK] Did not invoke the Improvement-Skepticism Reviewer (main agent's responsibility)
- [OK] Every Finding includes Hypothesis + Expected metric delta + Implementation cost + Required new data or solver + Touches confirmed method or model structure + Suggested claim level after success
