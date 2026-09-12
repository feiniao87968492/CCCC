## Reviewed scope

Independent static review of the current corrected implementation against design and acceptance. References below are relative to `experiments/q4_aggressive/` unless qualified.

Reviewed policy SHA256: `50fcd77cfadcd1e63a98242f80798d03d02d1235faf44e4e392386fb3e7a84d5`.

The reported **22 passing behavioral tests** were accepted as caller-provided execution evidence; their source was inspected. Withdrawn runs and ER/EN/ERN selection supplied no performance or selection evidence.

## Findings

**F1 — E’s substantive corrections are present.**
- Type: optical execution/cost; Severity: INFO.
- Evidence reference: `q4_aggressive_policies.py:40`, `:133`, `:143`, `:165`; `design.md:169`.
- Spatial weights, failed-disc conditioning, first-hit survival costs and the success surcharge are implemented. E disables C15, compares against a legal RF continuation, executes the ordered complete permutation, and delegates covers above256 cells to the inherited complete executor.
- Recommended action: Retain independent reconstruction of sampled E costs, overlapping hits and failed-cell skips before accepting development evidence.

**F2 — B implements the declared parallax continuation.**
- Type: candidate selection/model fidelity; Severity: WARNING.
- Evidence reference: `q4_aggressive_policies.py:65`, `:97`, `:112`; `test_aggressive.py:60`.
- The score uses the bounded-bearing predicted radius, unnormalized heard-weighted continuation, legal virtual viewpoints and78 s non-reception penalty. Extended current candidates are legal/fresh, and the one-bearing negative-RF recovery override is restored after ranking.
- Recommended action: Add independent full-score and selected-candidate fixtures covering recovery, zero heard mass, duplicate candidates and illegal virtual viewpoints. The current continuation fixture does not cover those decisions.

**F3 — G’s formula and physical-stop budget are corrected.**
- Type: supplemental probing/accounting; Severity: WARNING.
- Evidence reference: `q4_aggressive_policies.py:93`, `:178`, `:211`; `test_aggressive.py:74`; `simulator_automation/q4_runner.py:112`.
- The denominator uses the actual receiver switch, reception weighting is not applied twice, and admission retains S geometry without H suppression. Three tokens persist across callbacks; resets occur through `_move_to`, which physical action methods invoke after acceptance.
- Recommended action: Verify endpoint coverage and N+G interactions before combination acceptance; retain token-to-measurement audit checks.

**F4 — R preserves dedicated-count semantics and optical dispatch.**
- Type: early-exit precedence; Severity: WARNING.
- Evidence reference: `q4_aggressive_policies.py:140`; `experiments/q4_local/q4_local_policies.py:141`; `experiments/q4_ablation/q4_ablation_policies.py:208`; `simulator_automation/q4_runner.py:606`.
- R requires the configured dedicated count, two direction bearings and rho≤200. Certified clear returns first; E/C can select optical before R. Optical tasks reach the fallback rather than the scalar measurement branch; cap8 remains unchanged.
- Recommended action: Add focused R2/R4 boundary and precedence fixtures. Whole-scene completion alone does not establish that each gate or dispatch path activated.

**F5 — H’s inherited gates and retry ownership are intact.**
- Type: optimistic clearing/priority; Severity: WARNING.
- Evidence reference: `q4_aggressive_policies.py:24`, `:226`; `experiments/q4_transfer/q4_transfer_policies.py:64`, `:120`, `:123`, `:158`.
- H retains two direction bearings, condition number≤30, legal polygon membership, failed-point exclusion, two attempts and one attempt per positive version. Certified clear precedes speculation. Actual H registration occurs in the inherited transfer executor; N bypasses that registration.
- Recommended action: Add targeted conditioning, certified-priority, negative-version and third-attempt fixtures; reconcile the integration wording described below.

**F6 — Prior B1’s duplicate-clear mechanism is mitigated in current code.**
- Type: state consistency; Severity: INFO.
- Evidence reference: `q4_aggressive_policies.py:83`, `:194`, `:226`, `:237`; `test_aggressive.py:66`, `:97`; `src/q4_state.py:152`.
- Both clear entry points reject another physical clear of a cleared target. Stale scalar targets return early. N runs after completed scalar actions/scans, outside near-clear internals and optical tours. Its separate ledger enforces two bearings, rho≤320, mass threshold, two trials, positive-version renewal and the1 m failed-point exclusion.
- Recommended action: Record this implementation evidence against prior B1. Retain adversarial N+G/H/E checks; the old review’s “no implementation exists” premise no longer applies.

**F7 — Prior B2’s predicate and ranking distinction are implemented.**
- Type: eligibility/estimand; Severity: WARNING.
- Evidence reference: `design.md:127`; `run_aggressive.py:100`; `experiments/q4_ablation/run_ablation.py:110`; `summary_aggressive.py:17`.
- The engine derives `full_success` from empty failure, K=N and certification. Therefore requiring every generated row’s `full_success` is equivalent to the declared predicate. Ranking then uses setting-weighted nonboundary means; absence certificates do not inflate K.
- Recommended action: Independently reconstruct this predicate and require complete scheduled-matrix verification before selection. The remaining summary-entry-point weakness is described below.

**F8 — Fresh cohorts and effective controls match the corrected plan.**
- Type: provenance/control identity; Severity: WARNING.
- Evidence reference: `run_aggressive.py:28`, `:85`, `:90`; `q4_aggressive_policies.py:30`, `:245`; `experiments/q4_local/q4_local_policies.py:64`; `invalid-runs.md:13`.
- Defaults contain four controls and twelve single-family candidates, with development60000+ and primary70000+ cohorts matching the declared mixtures. `previous_best` resolves to JSO_compact_dopt. No combination is registered or locked. Dependency snapshots and end-of-run drift checks are present.
- Recommended action: Bind future manifests to this correction review and the eventual corrected selection record; preserve all initial arms.

## Blocking risks

No unresolved blocker identified for **corrected initial16-arm development readiness**.

- Type: implementation-readiness assessment.
- Severity: NONE identified within this scope.
- Evidence reference: Findings F1–F8 and the current source references above.
- Recommended action: The caller should record formal dispositions of prior B1/B2 separately. This review does not mark a gate complete.

## Non-blocking warnings

**W1 — The documented scalar integration differs from the implementation.**  
`design.md:194` prescribes a direct frozen scalar call with explicit H registration; `q4_aggressive_policies.py:234` instead uses the Local→Transfer→Q4 chain. Current LC-derived configurations have `selective=False` and no burst, so the chain executes one scalar action and retains H accounting. Document that equivalence or implement the prescribed route before broadening configurations.

**W2 — Cover callbacks can invoke the endpoint handler twice.**  
`scan_at` invokes it, then the inherited scheduler invokes `_probe_detected_at_v4` (`q4_aggressive_policies.py:237`; `experiments/q4_ablation/q4_ablation_policies.py:204`). G’s shared budget prevents excess probes. In N+G, however, a G bearing from the first pass can enable N during the second pass at the same stop. Specify and verify whether that sequence is intended before locking such a combination.

**W3 — Standalone summarization does not establish cohort completeness.**  
`summary_aggressive.py:34` checks rectangularity against observed scene IDs; a common truncated subset can pass. The inherited audit correctly checks the full manifest matrix and completion record (`experiments/q4_transfer/audit_transfer.py:89`). Require that audit, bound to the same results hash, before ranking—or enforce equivalent checks in summarization.

**W4 — Mechanism audit and final reporting remain incomplete.**  
`audit_aggressive.py:37`, `:51`, `:57` checks E inequalities/permutations and B arithmetic identities, but does not independently reconstruct their underlying scores. `summary_aggressive.py` lacks separate stress summaries and seed-block intervals; its line43 incorrectly describes every arm as radius1950/tour despite the declared prior-control exception. These are follow-up requirements before result acceptance.

**W5 — Review metadata is stale.**  
`run_aggressive.py:97` hardcodes the earlier readiness verdict; `design.md:216` still says implementation has not started. Update current status and hash the correction review while retaining historical reviews unchanged. Residual ER/EN/ERN display labels are not a selection lock.

## Required follow-up

1. Reconcile callback/scalar contracts and add focused R/H, full B-score and selected-combination acceptance cases.
2. Validate corrected development using complete-matrix, physical-charge, certificate and mechanism audits, including independent scoring samples.
3. Select combinations solely from corrected development under the declared family, improvement and tie rules; freeze configurations and hashes before combination development and primary.
4. Complete stress/general/all-setting reporting, LC comparisons and seed-block inference before accepting efficiency conclusions.

## Reviewer recommendation

**Verdict: PASS_WITH_WARNINGS.**

The corrected implementation supports proceeding with the initial development matrix. Prior B1’s state-corruption path and B2’s predicate ambiguity have substantive current mitigations. Combination readiness, development-result acceptance and primary evidence acceptance remain separate follow-up assessments.

## Required reads referenced

- All requested current aggressive files: `q4_aggressive_policies.py`, `run_aggressive.py`, `test_aggressive.py`, `design.md`, `invalid-runs.md`, and the three reviews.
- `acceptance.md`, `summary_aggressive.py`, `audit_aggressive.py`.
- Inherited local/transfer policy and audit modules; ablation policy and execution engine.
- Q4 runner scalar/scan/fallback hooks; `src/q4_adaptive.py`, `src/q4_state.py`, relevant `src/q4_localize.py` geometry.
- Simulator/test-double definitions, frozen dependency manifest and scoped decision excerpts, inspected as text.

## Confidence

**medium** — high confidence in the traced mitigations; runtime activation, combination interactions and full-cohort evidence were not independently exercised.

## Forbidden-behavior self-check

Read-only inspection and hashing only. No file modifications, simulations, tests, agents, permission requests, baseline adoption, claim upgrades, official-score assertions or formal gate changes. Withdrawn runs did not inform selection or performance conclusions.