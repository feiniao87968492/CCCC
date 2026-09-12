# Q4 local decisions — independent development validation

## Reviewed scope
- `experiments/q4_local/q4_local_policies.py`, `run_local.py`, `audit_local.py`, `summary_local.py`, `test_local.py`, `verification.json`, and final `design.md`.
- `experiments/q4_local/reviews/implementation-readiness.md`.
- `experiments/q4_local/dev40/` and `dev_combinations40/`: manifests, source hashes, scenarios, complete result rows, summaries and automated audit reports.
- Inherited Q4 adaptive executor, positive-region, RF belief and optical interfaces inspected in the preceding readiness review.

Paths are relative to `B题/`. This review concerns 520 initial development runs and 160 additional-combination runs, not the still-running primary experiment. No simulation or test suite was rerun by the reviewer.

## Findings

### F1 — Local implementation follows the principal readiness contracts
- Type: implementation-contract
- Severity: INFO
- Evidence reference: `q4_local_policies.py::_refinement_points/_supplement/_execute_one/_do_v3_action`; readiness F1–F5.
- Recommended action: Retain the declared meaning of each mechanism and verify its actual event execution separately from aggregate costs.

L uses spatial marginal weights for distance, heard-weighted completion mass and a separate reception penalty, then restores the one-positive shadow bracket. P maintains a single accepted-operation stop counter, resets only when the individual physical move exceeds 1 m, re-ranks after each probe, and uses expected_gain directly over 5+actual-switch cost. F captures only the target channel's newly executed physical events, rejects initial no-signal/failed-clear/no-op outcomes, uses an explicit two-step loop, and returns optical tasks to the scheduler. C obtains a real RF candidate for an aggressive proposal, recomputes position-dependent full optical route costs, and preserves the uncapped fallback. M uses spatial mass without RF reception masking, recomputes candidate scores from the full-history RF belief/current position/failed points, and maps its new action kind to the recognized aggressive-clear dispatcher. Mass retry versions depend only on positive history and persist across negative updates. The latest previous_best explicitly invokes the transfer JSO_compact_dopt arm, avoiding the older previous_best alias.

### F2 — Development rows, source snapshots and physical audits are complete
- Type: development-provenance
- Severity: INFO
- Evidence reference: `dev40/results.csv`, `dev_combinations40/results.csv`, their manifests, snapshots, completion and audit JSON.
- Recommended action: Preserve both run snapshots and report their role as development selection and execution checking.

Independent row/hash checks confirm 520 unique initial arm/setting pairs and 160 unique additional pairs, with all rows complete and no snapshot hash mismatch. Both cohorts use the declared 30 mixed endpoint plus 10 boundary settings. The main-agent audits report PASS over 167,162 and 51,564 physical operations, with no failed run, no frozen-file mismatch and event timing residual at most 1.82e-12 s. Those physical audits were inspected, not rerun independently here. Current primary results are not inferred from these development successes.

### F3 — Development supports selected combinations while retaining counterexamples
- Type: selection-and-counterevidence
- Severity: WARNING
- Evidence reference: complete development results and `design.md::Development-based combination lock`.
- Recommended action: Keep every initial family in primary and distinguish exploratory combination selection from validation on fresh scenes.

Independent development means agree with baseline 519.673049 s/source, L30 511.235235, C15 508.509945, P1 515.226280 and S_all 517.357699. P1 reduces probes relative to S_all (310.225 versus 312.25) but increases them relative to baseline (300.5). F60 executes bursts yet has baseline-identical physical cost statistics; M50/M75 and F120 worsen the combined mean. The extra development means are LC 504.9572, PC 505.9081 and LPC 495.4689 s/source. All three combinations remain in the fixed final 16-arm registry. These data motivate hypotheses; they do not establish the eventual primary winner or a generally beneficial F/M mechanism.

### F4 — The audit verifies declared counters but does not reconstruct every planner score
- Type: validation-coverage-limit
- Severity: WARNING
- Evidence reference: `audit_local.py::check_local`; `q4_local_policies.py::mass_candidate/_adaptive_task/_supplement`.
- Recommended action: Supplement the full physical audit with independent mass/positive-polygon sampling and explicit linkage checks for P budget events and F negative-stop behavior before final result acceptance.

The audit checks logged mass thresholds/version/caps, logged optical cost inequalities and counters, burst bounds, matching physical distance and complete physical feasibility. It does not independently recompute RF posterior mass, P's winning score, or C's NN/RF costs from history. It also does not directly forbid a second burst action after a negative step before the eventual burst-end event; actual code correctly breaks immediately, but that invariant benefits from a separate parser. Similarly, every P selective probe should be linked to exactly one budget token, rather than trusting budget-tag counts alone. These are limits of the audit's proof coverage, not observed implementation failures. The reviewer will make a bounded independent mass reconstruction for the primary review.

The subsequently completed reviewer-only development check (`reviews/reviewer-audit-dev40.json`) parses all 240 relevant P/F/M traces: 1,011 budget-token/selective/measurement links, 580 burst steps and 451 mass-attempt version/cap checks pass. A fixed eight-trace M50/M75 sample on two seeds reconstructs 40 mass decisions with zero mass or selected-coordinate discrepancy and verifies candidates against separately constructed positive halfplanes. Production polygon/center construction is reused only to preserve the deterministic discretization ordering; RF weights, LS and candidate scoring are reconstructed separately. An initial checker using individual dot products selected a different floating-point mass tie than the batch matrix product; matching the declared batch scoring arithmetic resolved that checker discrepancy without a policy change.

Eight additional C traces reconstruct the NN full-optical route/charging for 154 proposals with zero discrepancy, using the production certified optical cells. The RF alternative cost is still reviewed statically rather than independently reconstructed from the trace.

### F5 — Test provenance and safe execution paths are materially improved
- Type: verification-scope
- Severity: INFO
- Evidence reference: `test_local.py`, `verification.json`, run manifests.
- Recommended action: Retain the test source hash and use the complete primary event audit for mechanisms beyond the crafted cases.

The test file covers same-stop repeated callbacks, the actual adaptive executor for all 13 local arms, mass failure plus negative-history retry denial, initial negative/failed-clear burst stopping, and final optical completion. It is included in snapshots. The verification record reports 290 passing tests with source hash `bc955390d77f0c2394b0334e87d7a9523d43cf563f3dcbad12a333527f34ca92`; this reviewer inspected the code and record but did not rerun the suite. The mocked admission conditions in the P budget test intentionally isolate budget persistence and do not validate the RF ranking itself.

## Blocking risks
No unresolved blocker was identified for continuing the locked primary experiment. Independent final physical/mechanism/geometry and statistical validation is still required before reporting primary results. This review does not clear a gate or approve baseline replacement.

## Non-blocking warnings

### W1 — A burst changes execution grouping without necessarily changing cost
- Type: mechanism-effect
- Severity: WARNING
- Evidence reference: Findings F3–F4; F60 development results.
- Recommended action: Report F burst counts separately from physical movement/probe changes in `experiments/q4_local/` reports.

### W2 — Cost ratios and posterior mass remain decision proxies
- Type: claim-limit
- Severity: WARNING
- Evidence reference: Findings F1 and F4; `design.md`, C/M definitions.
- Recommended action: Avoid describing C as an optimal cost choice or M mass as calibrated clear probability in result reports.

## Required follow-up
- Complete the locked 16×400 primary matrix under `experiments/q4_local/primary400/` with full snapshots and no in-run mutations (F2–F3).
- Run the complete physical/local mechanism audit and retain its source hashes under `experiments/q4_local/`; supplement mass geometry and P/F linkage checks in `reviews/` (F4).
- In the primary report, include P versus S_all, combinations versus their components, all inactive/losing families, subgroup/tail losses and seed-block uncertainty (F3, W1).
- Obtain `experiments/q4_local/reviews/primary-validation.md` after completion and audit artifacts exist; keep `claims/baseline-q4.md` frozen (W2).
- Memory check: recommend noting the P-versus-S_all attribution distinction and F60's active-but-cost-identical development case in `B题/memory.md`; reviewer did not edit memory.

## Reviewer recommendation
The development implementation and evidence are sufficiently consistent to continue the locked primary experiment. The requested local families are actual executable changes and the selected combinations were chosen without primary outcomes. Development remains exploratory; final acceptance should use the full audit, independent mechanism/geometry checks and paired fresh-cohort results rather than development rankings.

Verdict: PASS_WITH_WARNINGS

## Required reads referenced
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/stage-6-independent-validation.md` (previously read).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/subagent-validation-paper.md` (previously read).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-markdown-audit.md`, `protocol-human-confirmation.md`, `protocol-memory-update.md`, `protocol-subagent-delegation.md`, `protocol-readiness-gate.md`, and `protocol-rollback.md` (all read in preceding reviews).
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-output-schema.md` and `reviewer-self-discipline-checklist.md` (previously read).
- All actual project reads are identified in Reviewed scope; prior source reads are explicitly identified as prior context.

## Confidence
medium — actual code and complete development provenance were checked, while physical auditing is a reviewed automated artifact and primary outcomes are pending.

## Forbidden-behavior self-check
- [OK] Did not confirm user decisions
- [OK] Did not clear blockers
- [OK] Did not mark stages or rounds complete
- [OK] Did not increase claim level on behalf of the main agent
- [OK] Did not invoke another subagent
- [OK] Did not write or edit project files outside authorized review outputs
- [OK] Did not write claims/baseline-snapshot.md
- [OK] Did not export when the final evidence gate has not passed
- [OK] Did not modify pinned implementation/data or run tests/simulations
