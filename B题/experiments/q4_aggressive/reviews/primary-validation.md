## Reviewed scope

Independent post-result review of corrected `primary_valid400`: all 19 locked arms, 400 fresh settings per arm, full clearing/certificate eligibility, scoring samples and primary statistical reporting. Paths below are relative to `experiments/q4_aggressive/` unless qualified. This is an offline result review, not baseline adoption, official-simulator validation, paper export approval or a formal stage-completion action.

Evidence bindings:

- `primary_valid400/results.csv`: `c9733c2eae447866917933ab439f89ee6e52f9084f9a32e7ed508ea233a0c4f1`.
- `primary_valid400/scenarios.json`: `13423a4c238e9a2c4d1947be4124410a39d9a277e33907d8743d2556def4c38d`.
- Policy: `c033a3dc8ee4c7024ae84b28a2cf78774cef2a9b946f5c663b94486feac4a47d`.
- Existing score reviewer: `a8ab0c92be82d4ea2be33c94852d23329179b9632181ac1d42f1b550d58cbbad`.
- New `reviews/reviewer_primary.py`: `cd724f61ef87de05301dc0bfaf39635a8cb15ea915c56ce4855e45d3e999cadc`.

## Findings

**F1. The primary matrix and all-setting eligibility pass independent reconstruction.**

- Type: cohort completeness/physical validity; Severity: INFO.
- Evidence reference: `primary_valid400/manifest.json`, `scenarios.json`, `completion.json`, `audit.json`; `reviews/reviewer-primary-matrix.json`.
- Exactly 7600 distinct arm-setting rows are present. The cohort contains mixed endpoint seeds 70000-70199 plus 50 settings each for directional endpoint, omni endpoint, boundary endpoint and mixed smooth, using seeds 70000-70049. The declared geometry/type constraints and scenario hashes are consistent. No development seed overlaps the primary cohort. Each arm clears 5275/5275 true sources, including 4611/4611 in the 350 general settings; every row has K=N, full success, all certified and empty failure.
- Independent CSV reconstruction checks setting T/K, travel cost and all physical charges. The completed automated event/truth audit replays 2334497 physical operations, validates measurement/clear outcomes and absence certificates, rejects actions after source clearing, and reports maximum timing residual 1.819e-12 s. Its results hash matches the reviewed CSV.
- Recommended action: Accept the completed matrix for bounded offline comparison; do not drop the 50 boundary settings from eligibility.

**F2. All locked configurations, selection and frozen baseline hashes are retained.**

- Type: provenance/freeze integrity; Severity: INFO.
- Evidence reference: primary manifest/source snapshots; `selection.json`; development manifests; `reviews/reviewer-primary-matrix.json`.
- All 32 starting dependency snapshots match their manifest hashes. The 16 initial configurations match corrected development; GR/GN/GRN match the development selection and combination manifest exactly. Selection file/hash and its development result/summary bindings are unchanged. All 13 frozen baseline dependencies retain their expected hashes. No dependency changed during primary execution.
- After the completed automated audit, `summary_aggressive.py` changed inside `render_table`: each figure now highlights its own displayed-cohort minimum and records that basis. Final reporting closure also replaced exactly `独立边界压力组` with `单列边界压力组` and inserted exactly `边界压力组与其他组共享部分种子；单列报告不表示与一般场景统计独立。`. The reviewer inspected the full diff. The executable normalizes each of those two named AST text edits exactly once, excludes the previously inspected rendering function, and requires all remaining AST content to equal the execution snapshot. Statistical computation and policy are unchanged.
- These post-audit reporting changes are disclosed in the reviewer matrix; the automated audit's earlier empty current-drift list is not treated as a current all-file hash assertion. Regenerated summary CSV values and all independently reconstructed statistics agree. Figure CSV copies, source hashes and current rendering-script hashes match for all three cohorts.
- Recommended action: Preserve original snapshots and record the reporting-only change; do not rewrite the manifest to conceal it.

**F3. Independent scoring reconstruction passes on fixed samples and every N activation.**

- Type: implementation/model fidelity; Severity: INFO.
- Evidence reference: `reviews/reviewer_aggressive.py`; `reviews/reviewer-audit-primary_valid400.json`; inherited full mechanism audits.
- The unchanged reviewer executable inspects 313 traces: first two seeds across all five strata and all new arms, plus every trace with an N activation. It reconstructs spatial RF weights and checks 1219 E choices, 147 E optical plans and 443 executed optical clear targets; 422 full B candidate selections including 36 recovery choices; and 1681 full G candidate selections from 5315 logged opportunities/selections. It also checks 53 R proposals, 45 H gates and all 186 N mass gates. Pure fixtures cover E overlaps/failed skips/reset/never-hit cases and B zero heard mass/coincident/illegal virtual points.
- Maximum E expected/full-cost discrepancy is 3.411e-13, G score discrepancy 4.441e-16 and B score discrepancy zero. The full automated mechanism audit additionally checks physical token matching, shared G stop budgets, N trial/version accounting and E execution. No sampled or full-audit violation is reported.
- Recommended action: Accept the score/dispatch evidence with the stated independence boundary: positive-region and optical-cell geometry is reused from production, while RF weights, scores and candidate choices are reconstructed separately.

**F4. Summary means, uncertainty and comparisons reproduce independently.**

- Type: statistical reporting/estimand; Severity: INFO.
- Evidence reference: `reviews/reviewer_primary.py`; `reviews/reviewer-primary-statistics.json`; primary general/all/stress summaries, comparisons and interactions.
- Independently reconstructed all 57 arm-cohort summaries, including mean(T/K), travel/probe means, source totals, failure predicate, wins/losses, p95 and extreme paired deltas. All 168 control and interaction rows also agree. The reconstruction uses 5000 seed-block bootstrap draws, 10000 block sign flips and Holm adjustment over the 18 baseline contrasts; it does not import the production summary implementation.
- General and all-setting cohorts contain 200 independent seed blocks; boundary stress contains 50. The bootstrap preserves within-seed dependence and setting weights through sampled block sums divided by sampled setting counts. General ranking is performed only after eligibility on all 400 settings.
- Final reporting closure additionally reconstructs all 57 cost-decomposition rows from raw physical-result columns, all 57 activation-summary rows from the completed audit's per-trace mechanisms, and all 12 family-comparison rows. README interpretation matches the named controls and descriptive uncertainty. In particular, G1.5 versus LC saves 8.107309 walking seconds/source while other physical costs add 0.823773 seconds/source, net -7.283536; R4 actually dispatches early optical work in 23/350 general settings. G1.5 has a lower mean than LC within each of the five declared strata, without implying per-setting dominance. The explanatory tables and reviewed README hashes are recorded in `reviews/reviewer-primary-statistics.json`.
- Recommended action: Treat the general cohort as the declared primary ranking; preserve nominal/descriptive labeling for secondary control and interaction intervals, and distinguish settings from independent seed blocks.

**F5. General T/K ranking favors the previous control; G1.5 is the strongest new single arm observed.**

- Type: efficiency claim strength; Severity: WARNING.
- Evidence reference: `primary_valid400/summary_general.csv`, `comparisons.csv`, `report.md`; reviewer statistics.
- General mean(T/K): frozen baseline 513.190019; LC 496.926222; LPC 495.884668; previous JSO control 488.846688; G1.5 489.642686 s/source. The previous control is the lowest observed general mean. G1.5 is 0.795998 s/source slower on average than that control, with nominal paired interval [-2.825514, 4.395607]; superiority of either over the other is not established by that comparison.
- G1.5 versus the frozen baseline reduces general mean(T/K) by 4.5884%, mean walking time by 5.9535% and mean probes by 3.9429%. Its baseline time difference is -23.547333 s/source, interval [-27.517551, -19.591059], Holm p=0.00179982. Versus LC, G1.5 reduces mean(T/K) by 7.283536 s/source and walking by 105.701393 s/setting, while adding 0.162857 probes/setting. The nominal time interval versus LC is [-10.601256, -4.122192], and versus LPC is [-9.585686, -3.093633].
- Recommended action: State both the overall general winner and the best new arm. Do not call G1.5 a general T/K victory over JSO or a probe reduction versus LC; its probe reduction versus the frozen baseline is supported.

**F6. Cohort and ablation effects prohibit a universal winner or monotonic-module claim.**

- Type: robustness/mechanism attribution; Severity: WARNING.
- Evidence reference: primary stress/all summaries, interactions, paired rows and worst-case columns.
- G1.5 has the lowest all-setting mean, 496.695441 s/source. In boundary stress it averages 546.064724 versus baseline 589.335014 and previous JSO 590.043252. GRN has the lowest observed stress mean, 545.490856. These separate rankings do not replace the declared general ranking. The 50 boundary settings reuse base seeds from other strata and are not independent of the general cohort as a whole.
- G1.5 wins 260 and loses 90 of the 350 general settings versus baseline; the worst general paired loss is +102.274727 s/source. It wins all 50 observed boundary settings, which is finite evidence. E/B/H worsen general mean(T/K) versus LC; E2 lowers probes by 2.72/setting versus LC but increases mean(T/K) by 6.556874 s/source. R2 reduces LC probes by 0.96/setting with a small time reduction. N alone has a tiny mean benefit; adding N to G or GR increases general mean(T/K) by 0.019023/0.020234 s/source. GR versus G0.75 differs by only -0.014923 s/source with interval spanning zero.
- G1.5's lower observed general mean than G0.75 is -0.799061 s/source, with nominal interval [-2.476483, 0.803210]. It was retained before primary; selecting it as the observed best new arm is not evidence that its threshold is uniquely optimal or grounds for tuning additional primary-derived combinations.
- Recommended action: Report the failed ablations and tradeoffs alongside successes. Keep the full table, stress analysis and paired tails; do not promote the most complex combination merely because it contains more modules.

## Blocking risks

No unresolved blocker identified for accepting these primary offline ablation results at the stated scope.

- Type: primary evidence assessment; Severity: NONE identified within reviewed scope.
- Evidence reference: F1-F6, completed full automated audit and three primary reviewer audit artifacts.
- Recommended action: Main-agent gate bookkeeping, any baseline adoption and any paper-facing claim/export review remain separate responsibilities. This verdict does not perform those actions.

## Non-blocking warnings

- Offline sampled success does not establish an official-simulator score, a universal completion proof or a universal efficiency improvement. The frozen baseline claim ceiling is unchanged.
- Independent scoring reconstruction shares existing geometry; the full physical/certificate replay is a separate implemented audit, not a completely independent replacement simulator.
- Paired intervals against LC/LPC/JSO and among mechanisms are marginal descriptive intervals. Holm-adjusted baseline comparisons do not automatically adjust every secondary comparison or every cohort.
- Ranking the retained candidates on primary reveals observed performance; follow-on threshold tuning, dropping poor arms or constructing new combinations would need a fresh cohort.
- General and stress minima differ. Figure highlights identify the minimum within each displayed cohort; the general-cohort rule remains the primary rank.
- The post-audit rendering and two shared-seed wording changes are current and explicitly recorded. Primary policy, statistics, lock and all frozen dependencies remain bound to the original execution evidence.
- No additional simulator runs or test suites were executed by this reviewer. Earlier focused/broad test outcomes remain those documented in development validation and `verification.md`.

## Required follow-up

1. Preserve all primary/development snapshots, row/event/scenario hashes, reviewer scripts and paired tables with the final report.
2. Lead user-facing conclusions with the general T/K result and best new arm; show walking/probe changes against a clearly named control and disclose stress/tail tradeoffs.
3. Keep the baseline and official entrypoint unchanged in this ablation task. Any later adoption must receive its own applicable validation and authorization.
4. Before manuscript claims/export, apply the separate evidence/claim review and limit wording to these offline findings. No further experiment is required to report this completed ablation at its current scope.

## Reviewer recommendation

**Verdict: PASS_WITH_WARNINGS.**

The locked 19-arm primary experiment provides consistent, reproducible offline ablation evidence. The strongest new observed general strategy is G1.5; the previous JSO control remains the observed general T/K minimum. No baseline promotion, universal winner, official score or unique-optimality claim is approved.

## Required reads referenced

- `design.md`, corrected acceptance/invalid-run record, `selection.json`, primary runner/policy/summary/audit sources and relevant inherited physical/summary audits already read during development and refreshed as needed.
- Primary manifest, completion, scenarios, all results, 32 source snapshots and the 13-file frozen dependency record.
- All sampled primary event traces and every N activation trace through the unchanged reviewer executable; full automated primary audit.
- Primary general/all/stress summaries, comparisons, interactions, report and three figure metadata/CSV bindings.
- Final README, `analyze_results.py`, cost-decomposition, activation-summary and family-comparison tables, and the exact shared-seed report-text correction diff.
- `reviews/development-validation.md`, the existing score-review executable and generated development evidence; primary reviewer executable and its generated matrix/statistics records.
- math-modeling-v4 Stage 6 independent validation and reviewer schema/self-discipline guidance previously read in this review task.

## Confidence

**high** for integrity of this offline primary matrix, sampled score fidelity and reported estimates. Confidence does not extend to universal or official-simulator performance, unique optimality, or superiority where the stated paired interval spans zero.

## Forbidden-behavior self-check

Edited only files within `experiments/q4_aggressive/reviews/`: the primary reviewer executable, its generated records and this primary review, including the explicitly requested final reporting-closure amendment. Earlier development/history reviews and the existing score-review executable were not modified. No policy, runner, snapshots, source, analyses, baseline or official entrypoint was edited. No simulation batch, test suite, subagent, permission request, user decision, baseline adoption or formal stage/claim promotion was performed. Invalid runs did not contribute to selection or performance evidence.

Reproduce from the B project root:

```powershell
python experiments/q4_aggressive/reviews/reviewer_aggressive.py primary_valid400
python experiments/q4_aggressive/reviews/reviewer_primary.py
```
