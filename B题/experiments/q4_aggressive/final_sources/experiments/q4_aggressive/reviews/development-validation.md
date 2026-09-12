## Reviewed scope

Independent validation of corrected `dev_valid40` (16 arms x 40 settings) and `dev_combinations40` (10 arms x 40 settings), including the G075/R2/N20 selection and GR/GN/GRN configurations. Paths below are relative to `experiments/q4_aggressive/` unless qualified.

This review accepts development evidence only. It does not accept primary evidence, promote a baseline, change a claim ceiling, confirm a user decision, or mark a formal workflow stage complete. `dev40`, `dev40b`, `primary400` and invalid smoke batches supplied no efficiency or selection evidence.

Evidence bindings:

- `dev_valid40/results.csv`: `b3255e70367e52eff1bc497f068d0f364b220bf4f3ed894b999ea6f6f9064d0a`.
- `dev_combinations40/results.csv`: `1c334868baada358431153c99e4555c25de9153c00eac769b6e8c78c80c94c59`.
- Current policy: `c033a3dc8ee4c7024ae84b28a2cf78774cef2a9b946f5c663b94486feac4a47d`.
- Reviewer executable `reviews/reviewer_aggressive.py`: `a8ab0c92be82d4ea2be33c94852d23329179b9632181ac1d42f1b550d58cbbad`.

## Findings

**F1. Complete matrices, physical accounting and eligibility agree.**

- Type: evidence integrity; Severity: INFO.
- Evidence reference: both `completion.json` and `audit.json` files; `reviews/reviewer-matrix-development.json`; `experiments/q4_transfer/audit_transfer.py:89`.
- The complete scheduled matrices contain 640 and 400 rows. Every arm clears all 522 true sources over its 40 settings, with `full_success=True`, K=N, `all_certified=True` and empty failure. General ranking uses 30 settings and 20 seed blocks. Independent CSV reconstruction checks T/K and T = movement/5 + 5 measurements + receiver switches + 3 clear attempts + 2 successes. The full automated event/truth audit replays 326128 physical operations, checks absence certificates, rejects physical actions after clearing, and reports maximum timing residual 9.095e-13 s.
- Recommended action: Retain this same full-matrix and hash-bound eligibility gate for primary evidence.

**F2. E, B and G receive substantive independent reconstruction.**

- Type: model-to-implementation fidelity; Severity: INFO.
- Evidence reference: `reviews/reviewer_aggressive.py`; `reviews/reviewer-audit-dev_valid40.json`; `reviews/reviewer-audit-dev_combinations40.json`.
- Fixed first-two-seed samples cover every available stratum and new arm, augmented with every N activation trace: 80 initial and 46 combination traces. The reviewer reconstructs spatial samples/RF weights and uses explicit weighted first-hit cumulative costs for E. All 546 E decisions and 80 optical plans agree; 186 executed clear targets match the planned permutation after failed-cell skipping. B is checked against its entire legal/fresh expanded candidate set on 182 decisions, including 14 restored recovery choices. G admission, RF-weighted gain, actual-channel charge and full pending-channel choice are reconstructed for 399 actual selections across the two batches. Maximum E/G residuals are 3.411e-13/3.331e-16; B score residual is zero.
- Pure-function fixtures additionally cover E overlapping hits, failed-cell skips, all-weight reset, never-hit samples and empty cells; B coincident points, certified-radius continuation, both virtual viewpoints illegal and zero heard mass.
- Recommended action: Repeat a fixed-seed scoring sample on primary and retain complete automated replay. The underlying positive-region and optical-cell geometry is reused production geometry, so these are independent scoring checks rather than a second complete geometry implementation.

**F3. R/H gates and N/G integration have current evidence.**

- Type: local action control; Severity: INFO.
- Evidence reference: `test_aggressive.py`; `verification.md`; `audit_aggressive.py`; the two reviewer audit JSONs.
- The reviewer checks sampled R proposals against reconstructed dedicated counts, two bearings and rho <= 200; 20 H attempts satisfy reconstructed radius/conditioned feasible line-estimate gates. All 18 N activations across both batches are checked against reconstructed spatial mass, positive bearings and rho <= 320. Full automated audits bind tokens to physical actions, enforce G's three actual measurements per physical stop, and enforce N version/trial/failed-location rules.
- Current focused test source includes R2/R4 boundaries and precedence, H conditioning/version caps, and the intended N-after-new-G-bearing second callback without duplicate clearing. The caller reports 39 aggressive tests passing; that test execution was not rerun by the reviewer.
- Recommended action: Preserve these contracts and the two-callback interpretation in primary. R's threshold is a count of dedicated probes, which can include non-reception; label it accordingly.

**F4. Corrected selection and configuration provenance are reproducible.**

- Type: experiment selection/provenance; Severity: INFO.
- Evidence reference: `selection.json`; `select_combinations.py`; `reviews/reviewer-matrix-development.json`; both manifests and source snapshots.
- Independent selection recomputation yields G075 (-5.429715), R2 (-0.618118), N20 (-0.016437) s/source versus LC, satisfying the declared strict -1e-7 threshold. N20/N50 tie and the lexical rule selects N20. GR/GN/GRN exactly match the selected configurations. All 280 repeated control/component rows agree in physical metrics and event hashes; only measured Python wall times differ.
- All 27/29 starting dependency snapshots match their manifests and all 13 frozen baseline files match current hashes. The current policy AST equals initial development after removing exactly the three combination registry entries. Initial-to-current documentation/test/runner changes are disclosed in the matrix audit. After combination completion, the runner only added primary audit/summary files to dependency metadata; this does not alter policy behavior.
- Recommended action: Retain all 16 original arms plus the three locked combinations in the fresh primary cohort. Bind primary to the current policy and this review; do not tune from primary outcomes.

**F5. The ranking is valid development evidence, with limited mechanism gains.**

- Type: interpretation/estimand; Severity: WARNING.
- Evidence reference: both `summary_general.csv` files; `dev_combinations40/comparisons.csv`; `dev_combinations40/interactions.csv`.
- General mean(T/K) is baseline 515.839726, LC 498.078055, LPC 493.275557, G075/GN 492.648340 and GR/GRN 492.836545 s/source. Independent reconstruction agrees with general, stress and all-setting summaries. G075 improves T/K over LC while increasing mean probes by 1.4667 per setting. R2 reduces probes; N's incremental development benefit is very small. E/B/H best parameters worsen general mean T/K versus LC, so their improvements versus the frozen baseline cannot be attributed to those new mechanisms.
- G075-versus-LC paired interval is [-17.434079, 6.863310] and versus LPC is [-10.127150, 8.047113] s/source. GN has exactly the same general metrics as G075; GR adds 0.188205 s/source and 1.5 probes. Boundary settings remain in eligibility and receive separate stress reporting.
- Recommended action: Present development ranking as selection evidence. Do not claim unique optimality, statistically established superiority to LC/LPC, universal per-setting improvement, or monotonic benefits from adding modules.

## Blocking risks

No unresolved blocker identified for accepting these corrected development batches and proceeding to the locked 19-arm fresh primary experiment.

- Type: development evidence assessment; Severity: NONE identified within the reviewed scope.
- Evidence reference: F1-F5 and the three reviewer-generated audit JSONs.
- Recommended action: The main agent must record any formal gate disposition. This review does not itself clear historical workflow blockers or establish primary efficiency claims.

## Non-blocking warnings

- Development contains only 20 independent seed blocks; selection and confidence intervals on this same cohort are exploratory. Fresh primary evidence is still required.
- New-arm gains must be compared with LC as well as the frozen baseline; T/K improvements can trade additional probes for less travel. Report both components rather than calling G a probe-reduction method versus LC.
- N's effect is activation-limited; all observed activations were inspected, but the tiny mean improvement does not establish broad utility. General GN/G and GRN/GR ties should be reported as ties.
- The `eligible_all400` column name is inherited even for 40-setting development. Its evaluated predicate covers all settings in the current batch; it is not evidence of 400 completed settings.
- `verification.md` records 328 passing broad tests and one unrelated Q3 documentation replay failure. This review inspected that record and focused test source; it does not assert an all-suite pass or independently diagnose the Q3 change.
- Geometry/certification evidence relies partly on existing audited geometry and finite offline scenarios. No official-simulator score or universal bounded-error efficiency guarantee follows from these results.

## Required follow-up

1. Freeze the 19 effective configurations and run the fresh declared 70000+ primary cohort, preserving every arm and failed setting.
2. Require complete physical/certificate replay, immutable source/event/scenario hashes, all-setting eligibility and independent primary result review before making final efficiency claims.
3. Rank eligible arms by setting-weighted nonboundary mean(T/K), report separate boundary stress/tails and comparisons to LC/LPC/previous_best, and disclose travel/probe tradeoffs.
4. Keep invalid batches excluded, baseline files frozen and official entrypoints unchanged until any separately authorized promotion workflow is satisfied.

## Reviewer recommendation

**Verdict: PASS_WITH_WARNINGS.**

The corrected development evidence and locked combination choice are acceptable for advancing to primary evaluation. No primary verdict or baseline promotion is issued here.

## Required reads referenced

- Corrected design, acceptance, invalid-run record, current policy/runner/audit/summary/selection code and focused tests.
- Correction-readiness and prior review artifacts, treated according to their historical scope.
- Both complete manifests, scenario/results/completion/audit records, source snapshots and general/all/stress summaries; sampled events and every N activation trace.
- Inherited local/transfer policy and audit modules, ablation summary checks, Q4 region/cell geometry and frozen dependency manifest.
- math-modeling-v4 Stage 5/6 references, reviewer output/self-discipline schemas, relevant delegation/readiness/rollback guidance previously read in this review task.
- `verification.md`, comparisons and combination interaction tables.

## Confidence

**high for corrected development integrity and sampled scoring; medium for out-of-sample efficiency.** Full matrices and hashes were independently reconstructed. Mechanism traces include both fixed sampling and exhaustive observed N activation checks, supplemented by focused fixtures. Primary performance remains unobserved.

## Forbidden-behavior self-check

The reviewer edited only the reviewer executable, its generated audits and this review. No policy, runner, test, shared model, baseline or official entrypoint was edited; no simulator batch or broad test suite was rerun. No user decisions, formal stages or claim ceilings were changed. Invalid runs did not inform performance or selection. No subagent was spawned and no additional permission was requested.

Reproduce from the B project root:

```powershell
python experiments/q4_aggressive/reviews/reviewer_aggressive.py dev_valid40
python experiments/q4_aggressive/reviews/reviewer_aggressive.py dev_combinations40
python experiments/q4_aggressive/reviews/reviewer_aggressive.py --matrix
```
