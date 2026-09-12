# Q4 local decisions — independent primary validation

## Reviewed scope
- `experiments/q4_local/`: final design, policy, runner, audit, summary and test sources; `verification.json`; implementation-readiness and development reviews.
- `experiments/q4_local/dev40/` and `dev_combinations40/`: complete rows, source snapshots and automated audits, as reviewed in `reviews/development-validation.md`.
- `experiments/q4_local/primary400/`: completed 6,400 rows, manifest/scenarios, 22-file source snapshot, completion/audit JSON, mechanisms, summaries, local comparisons, source/error and N strata, and report.
- All primary P/F/M mechanism traces and all previous_best O/S traces; fixed mass and optical-cost samples described below.
- `experiments/q4_local/reviews/reviewer_audit.py`, `reviewer-audit.json`, and `reviewer-audit-dev40.json`.
- Inherited `experiments/q4_ablation/summarize.py`, Q4 source geometry/belief/executor and transfer audit interfaces inspected in preceding reviews.

Paths are relative to `B题/`. This review was finalized after primary completion and audit artifacts existed. The reviewer executed only read-only analyses and reviewer-owned event reconstruction, not a policy, simulator or pytest suite. Writes are confined to authorized `experiments/q4_local/reviews/` artifacts.

## Findings

### F1 — The local routing constraint and complete paired matrix are preserved
- Type: scope-and-reproducibility
- Severity: INFO
- Evidence reference: `primary400/manifest.json`, `source_snapshot/`, `completion.json`, `results.csv`, `scenarios.json`; `q4_local_policies.py::VARIANTS/make_runner`.
- Recommended action: Report the new local candidates separately from the additional previous-best control and preserve the frozen baseline anchor.

Independent checks confirm 16 arms × 400 settings = 6,400 unique pairs, with all 400 settings complete and 5,208 sources cleared per arm. The prescribed 200 mixed endpoint plus four 50-setting cohorts produce 200 seed blocks. All new local-arm configurations retain radius1950 and route='tour'; inherited global selection remains unchanged, although local actions alter realized trajectories. The previous_best factory explicitly executes JSO_compact_dopt with its different center/S/O/D-optimal/radius1900 settings, while S_all executes standalone S. All 22 source snapshots match their start hashes, including the local tests; completion/audit report no in-run source mutation, no post-run drift and no frozen-source mismatch. The 290-test verification record's source hash matches the pinned final test file; the reviewer did not rerun those tests.

### F2 — P, F and M contracts are supported by independent event parsing
- Type: local-mechanism-validation
- Severity: INFO
- Evidence reference: `q4_local_policies.py`; `audit_local.py::check_local`; `reviews/reviewer_audit.py` and `reviewer-audit.json`; `primary400/events/`.
- Recommended action: Retain the accepted-movement stop convention, outcome-based burst termination and positive-version clear cap as part of the result's algorithm definition.

Reviewer parsing covers all 3,200 P/F/M runs, plus 30 extra C sample traces. It links all 20,810 P budget tokens one-to-one to their selective-probe and physical-measure events, recomputes stop resets from actual movement, and finds no budget violation. All 5,605 burst steps obey the two-step limit, same-source/nonrecursive structure and radius bound; no burst continues after a negative measurement or failed clear. All 4,461 mass attempts obey threshold, per-source two-trial and new-positive-version rules. The final main-agent audit also contains the strengthened budget linkage and immediate failed-step stopping checks, closing the earlier audit-coverage gaps. The previous-best control independently passes 2,989 O version/cap checks and 5,716 S probability/prior-positive checks. L's RF-weighted completion score, P's dynamic switching denominator and C's explicit optical dispatch match the design on static inspection; no source-truth access was introduced.

### F3 — Mass scoring and optical route costs have a bounded independent reconstruction
- Type: geometry-and-planner-sample
- Severity: INFO
- Evidence reference: `reviews/reviewer_audit.py`; `reviews/reviewer-audit.json`; `src/q4_adaptive.py`; `q4_local_policies.py::mass_candidate/_adaptive_task`.
- Recommended action: Preserve the sample source and output, and describe its reused geometry and limited sampling accurately.

The fixed sample takes seeds50000/50001 in every source/error stratum. For M50/M75 this is 20 traces on 10 settings sharing two seed blocks; all 133 mass attempts are reconstructed with zero mass or chosen-coordinate discrepancy. RF spatial weights, positive-bearing least-squares estimates, mass ranking and candidate membership in separately constructed positive halfplanes are recomputed. The numerical positive polygon/center is reused to preserve deterministic sample ordering; this is independent mass/scoring verification, not a wholly independent polygon solver or statistical sample. The checker matches the declared batch matrix scoring arithmetic so floating-point ties are assessed consistently. In 50 C-family traces, all 2,061 logged optical proposals match independently recomputed NN route distance and charging, with zero cost discrepancy, using the production certified optical cells. The RF alternative cost and L/P score selection are inspected in code rather than independently reconstructed for every action. No policy or simulator is executed by these checks.

### F4 — The full physical audit supports source completion and exact charging
- Type: physical-evidence
- Severity: INFO
- Evidence reference: `primary400/audit.json`, `audit_local.py`, inherited `experiments/q4_transfer/audit_transfer.py`; `primary400/results.csv` and `mechanisms.csv`.
- Recommended action: Keep the all-operation audit alongside this independent review instead of describing the limited sample as covering every geometric case.

The main-agent automated audit covers all 2,008,468 physical operations: legal actions, scenario reception/bearing bounds, clear outcomes, source completion, per-channel absent-source cover evidence or observed-16 certificate, source/event hashes and movement/measurement/switch/clear costs. It reports PASS, no failure and a maximum timestamp residual of 1.82e-12 s. The result hash and both audit-source hashes match the inspected files. Certified clearing retains its existing positive-region proof; optical dispatch retains the full fallback. Negative RF changes soft belief without clipping the continuous feasible region. This reviewer inspected the audit and independently checked the mechanisms/statistics/samples above, but did not separately rerun the complete physical audit.

### F5 — LPC gives the best new-local mean and improves all tested subgroup means
- Type: paired-efficiency-and-tail
- Severity: WARNING
- Evidence reference: independently aggregated `primary400/results.csv`; `summary.csv`, `strata.csv`, `by_source_count.csv`, `report.md`.
- Recommended action: State the observed average improvements with the 92 losses and distinguish the new-local winner from the lower-mean previous-best control.

| Metric | Frozen V4 rerun | LPC |
|---|---:|---:|
| Mean T/K, s/source | 537.376003 | 515.618001 |
| Mean total time, s/setting | 6813.718983 | 6525.038865 |
| Mean walking time, s/setting | 4985.093983 | 4718.748865 |
| Mean probes/setting | 295.55 | 286.00 |
| Discovery/refinement probes | 260.2125 / 35.3375 | 260.0100 / 25.9900 |
| p95 T/K, s/source | 700.644623 | 687.684031 |

LPC reduces mean T/K by 4.048934%, walking by 5.342830% and total probes by 3.231264%. Most probe savings come from refinement. All five source/error subgroup means improve: boundary 5.338689%, directional 2.771606%, mixed endpoint 4.131572%, mixed smooth 3.720912% and omni 3.919772%; their probe means also improve. All N=10–16 mean T/K strata improve. Nevertheless, LPC wins308 settings and loses92, with worst regression +84.942112 s/source at directional_endpoint_50002. The prior global/compact control has a lower observed combined mean, 513.488873 s/source, but boundary mean worsens0.697261%. LPC should therefore be called the best *new local* observed mean, not the lowest mean across all16 arms or a universal per-setting improvement. The current report makes the new-local restriction explicit.

### F6 — Component evidence supports C and L combinations, with tradeoffs for P and the old control
- Type: component-comparison-and-selection
- Severity: WARNING
- Evidence reference: `primary400/local_comparisons.csv`, `summary.csv`; `summary_local.py`; independently recomputed seed-block arrays.
- Recommended action: Retain component comparisons and marginal-interval qualifications; avoid attributing the whole LPC gain to the P budget.

Independent calculations reproduce all primary paired deltas within2.67e-15 s, bootstrap endpoints within1.07e-14 s, Holm values exactly, and all11 local comparison point/interval values within4.00e-15 s. Whole seed blocks are resampled and divided by resampled setting counts, preserving the setting-weighted estimand. LPC's baseline delta is -21.758002 s/source, with marginal95% block interval[-26.137275,-17.519657] and Holm-adjusted block-sign-flip p approximately0.0015 under the stated symmetry assumption. Matrix winner selection is still not proof of unique/general superiority.

P1 versus S_all changes mean T/K by -1.601953 s/source, interval[-3.603106,+0.377722], while saving3.725 probes. P2 versus S_all has -1.911364, interval[-3.612112,-0.585142], and saves1.285 probes. Both P arms still use more probes than frozen V4. LC improves relative to both L30 and C15; PC improves relative to C15 and P1; LPC improves relative to LC and PC in these descriptive comparisons. Adding P1 to LC lowers mean T/K by4.278950 s/source but adds0.8975 probes, so its marginal value is primarily a travel/time tradeoff rather than further probe suppression. LPC versus the previous-best control is +2.129127 s/source with interval[-2.125772,+6.660902], crossing zero; a time superiority claim in either direction is unsupported by this comparison. LPC uses4.07 fewer probes than that control. C15 alone wins379/400 settings and has a smaller worst regression of26.940164 s/source, at a smaller2.081863% mean gain than LPC. These are useful alternative tradeoffs, not guarantees.

### F7 — F and M do not produce an efficiency win in this matrix
- Type: negative-evidence
- Severity: WARNING
- Evidence reference: `primary400/summary.csv`, `mechanisms.csv`; `design.md` and development review.
- Recommended action: Keep F60/F120/M50/M75 in the final table and describe their active but ineffective primary behavior.

F60 has essentially unchanged mean T/K (+0.0085 s/source), F120 is worse by1.1634, M50 by0.2266 and M75 by0.0315. Their execution/certification can be correct without delivering the intended cost saving. L90's boundary mean worsens2.5159 s/source despite an overall benefit, whereas L30 improves that subgroup strongly. All losses and adverse subgroups remain visible. The completed experiment supports finite offline efficiency observations and retains the frozen baseline; it does not provide official-simulator scores or an optimal policy certificate.

Actual M trial successes are764/2428 for M50 and702/2033 for M75; their thresholds must not be read as achieved50%/75% success rates. All unsuccessful attempts remain in measured cost, and complete fallback preserves completion.

## Blocking risks
No unresolved blocker was identified for reporting these finite offline exploratory results with the stated qualifications. This review does not clear a main-agent gate, replace the baseline or approve stronger claims. Claims that LPC is best across all16 arms, that every setting improves, or that M's posterior mass is a calibrated success probability would exceed the inspected evidence.

## Non-blocking warnings

### W1 — Planner proxies are not validated physical forecasts
- Type: uncertainty-of-heuristics
- Severity: WARNING
- Evidence reference: Findings F3 and F7; L/C/M design definitions.
- Recommended action: Describe L/C as scheduling proxies and M as a discretized posterior heuristic; report observed outcomes rather than inferred probabilistic guarantees.

### W2 — Final reporting/audit sources must remain tied to their output hashes
- Type: evidence-packaging
- Severity: WARNING
- Evidence reference: primary audit JSON, reviewer audit JSON, manifest and verification record.
- Recommended action: Preserve final audit, summary, reviewer and test sources with hashes when packaging the experiment; distinguish immutable simulation snapshots from analysis files finalized afterward.

## Required follow-up
- Preserve the report's restriction to the best new-local mean and include previous-best's lower observed combined mean, LPC's92 losses and component tradeoffs in user-facing interpretation (`primary400/report.md`, F5–F6).
- Retain every initial arm, all eleven local comparisons, source/error/N strata and failures/tails under `primary400/` (F6–F7).
- Include `reviews/reviewer_audit.py`, both reviewer audit JSON files, this review and the full physical audit with source/result hashes in the local evidence package (F2–F4, W2).
- Keep `claims/baseline-q4.md` and frozen entrypoints unchanged; any later adoption/official claim requires separate evidence and decision handling (F7).
- Memory check: recommend adding LPC's all-subgroup mean benefit with92 losses, P1's unresolved time difference versus S_all, and F/M's inactive efficiency gains to `B题/memory.md`; reviewer did not edit memory.

## Reviewer recommendation
The completed local experiment is sufficiently grounded for its stated offline exploratory report. The locked global-route constraint is respected, full physical auditing passes, independent budget/burst/mass linkage and bounded scoring reconstruction pass, and all statistical summaries reproduce. LPC improves both requested costs against frozen V4 and all tested subgroup means, while the prior global/compact control retains a lower observed combined mean and LPC still loses individual settings. Report these tradeoffs without baseline promotion or a unique-optimum claim.

Verdict: PASS_WITH_WARNINGS

## Required reads referenced
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/stage-6-independent-validation.md` and `subagent-validation-paper.md` (previously read).
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-markdown-audit.md`, `protocol-human-confirmation.md`, `protocol-memory-update.md`, `protocol-subagent-delegation.md`, `protocol-readiness-gate.md`, and `protocol-rollback.md` (read in preceding reviews).
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-output-schema.md` and `reviewer-self-discipline-checklist.md` (previously read).
- All actual project reads are listed in Reviewed scope; reused source/reference knowledge is explicitly identified as prior review context.
- `data_preparation/parameters.csv`, coordinate bound, for independent mass-candidate legality checking.

## Confidence
high — the complete locked matrix, all local mechanism traces, selected mass/optical computations and uncertainty summaries were independently checked, with remaining physical-audit and sample limits explicitly stated.

## Forbidden-behavior self-check
- [OK] Did not confirm user decisions
- [OK] Did not clear blockers
- [OK] Did not mark stages or rounds complete
- [OK] Did not increase claim level on behalf of the main agent
- [OK] Did not invoke another subagent
- [OK] Did not write or edit project files outside authorized review outputs
- [OK] Did not write claims/baseline-snapshot.md
- [OK] Did not export when the final evidence gate has not passed
- [OK] Did not modify pinned implementation/data or run policies, simulators or tests
