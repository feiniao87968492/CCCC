# Memory

## Rules

- Q4 improvement comparisons must use the frozen per-question baseline, not the previous round and not the 30-seed smooth-error training mean.
- Q4 `no_signal` must not be read as `d>1000`. Counting certificate (N=16) is independent of the geometric cover certificate.
- Q4 ablation ranking must include paired per-scene deltas, subgroup results, p95 and worst regression; success-only averages are insufficient.
- Unknown-channel TRI25 scans remain mandatory even when detected-channel probes are suppressed.
- Local P probe budgets persist across callbacks at one stop; reset only on an accepted individual physical move >1 m. Negative RF may update soft weights, but cannot clip the positive polygon or renew a mass-clear retry version.

## Pitfalls

- Q3/Q4 algorithm status lives in `docs/当前算法与消融状态.md`. Historical SQUARE81/HEX37/GREEDY_FAST notes are not the live entry.
- Git HEAD is not a reproducibility anchor while TRI25/V4 files are uncommitted. Freeze working-tree SHA256 from `experiments/q4_efficiency/release_holdout100.meta.json`.
- Practice entry defaults to TRI25 + ROUTE_ADAPTIVE_V4, but module env fallbacks remain `SQUARE81` / `OLD_HEX37`. Offline benches must pass `--cover` / `--route` explicitly.
- Holdout mean T/K is an average: 3/100 paired scenes are slower (worst +48.26 s/source). Do not claim per-scene path optimality.
- A generic experiment module named `policies.py` collides with Q3 ablation imports; use a Q4-specific module name.

## Counterexamples

- Q3-to-Q4 O uses cond(A)<=30, not cond(A.T@A), with retry versions keyed to new positive observations; negatives never reset the two-trial cap.
- Snapshot all manifest dependencies before each batch; no runtime mutation or rename. Preserve manifests and correct incomplete metadata additively.
- Q4 transfer primary (28 x 400, seeds 30000+): JSO 523.327595 vs JS 523.332762 s/source; O adds almost no mean benefit on JS. Q3 254.05 s is not a matched Q4 comparator.
- Q4 transfer mean champion JSO_compact_dopt: frozen V4 532.172912 -> 513.958406 s/source; walking -4.402%, probes -1.301%, boundary T/K +0.586%, 114/400 paired losses. All 5187 sources per arm cleared; frozen baseline unchanged.
- S_dopt_short improves five tested subgroup means but adds 2.005% probes. short_clear/optical4 improve both cost components with smaller gains. Strict cover-route insertion worsens T/K 6.70%-9.30%.
- D-optimal added to JSO_compact changes mean T/K by -1.225 s/source with block CI [-3.591, +1.219]; the two leading arms are not clearly separated. optical2 never activated early coverage in development or primary.
- Q4 local primary (16 x 400, seeds 50000+): LPC improves frozen V4 537.376003 -> 515.618001 s/source, walking -5.343%, probes -3.231%; all five subgroup means improve, but 92/400 settings lose (worst +84.942 s/source). Global route/radius stay fixed for new local arms. Prior JSO_compact_dopt reruns at 513.488873; LPC-minus-prior block CI [-2.126, +6.661] does not establish superiority.
- Local P1/P2 reduce probes against unlimited S_all but increase them against frozen V4. P1-minus-S_all time CI [-3.603, +0.378] crosses zero. Adding P1 to LC saves 4.279 s/source while adding 0.898 probes/setting; do not attribute all LPC savings to its budget.
- Local C15 gives a smaller 2.082% mean time gain with 379/400 wins; F60/F120/M50/M75 give no mean time gain. M50 and M75 mass thresholds are not calibrated success rates (764/2428 and 702/2033 successful trials).
- Q4 aggressive primary_valid400 (19 x400, fresh70000+): every arm clears5275/5275 and certifies; general350 mean baseline513.190019, LC496.926222, LPC495.884668, previous JSO488.846688, new best G15=489.642686. G15-minus-LC=-7.283536 (block CI[-10.601256,-4.122192]); versus previous=+0.795998 (CI[-2.825514,+4.395607]). G15 does not establish superiority over previous on the user's primary general cohort. All400 G15=496.695441 vs previous501.496258, driven partly by boundary546.064724 vs590.043252.
- Aggressive G15 saves general walking105.701s/setting versus LC while adding0.162857 probes; T/K decomposes into -8.107309 walking +0.823773 other costs. General E1/B20/H200 mean deltas vs LC are +3.676558/+3.373128/+0.878256; gains vs frozen baseline alone are inherited LC gains, not positive mechanism evidence. R2=-0.727379; N50=-0.020912; GN and GRN are slightly worse than G and GR. No G15+R or G-on-previous-JSO combination was tested.
- Aggressive invalid trials dev_smoke/dev_smoke2/dev_smoke3/dev40/dev40b/primary400 used incorrect implementations/seeds; excluded permanently. Valid development640+400 runs,280 repeated event hashes match. Original ER/EN/ERN selection withdrawn; corrected G075/R2/N20 lock yields GR/GN/GRN.

- Holdout seeds 1065, 1092, 1093 (all N=16) have higher T/K under TRI25/V4 than HEX37/V3.

## Q3 ablation rules

- Rank only complete scenes; failed clears and all measurement charges remain in T.
- Compact seven-station covers require separate station identity and per-channel no-signal evidence.
- Screenshot aggregates do not identify reproducible scenes and cannot be claimed as reproduced.

## Q3 ablation counterexample

- In the synthetic 420-scene matrix, JSO_ALLSCAN reduced movement but increased probing to 353.25 measurements/run and had higher mean T/K than JSO.
- In the 8000-run primary Q4 matrix, nearest-only, finish-source and every-stop strategies increased mean T/K despite 100% completion.
- The best mean candidate in that matrix worsened boundary/outward minimum-radius T/K by 3.90%; aggregate gains do not imply stress robustness.

## User Preferences

- 2026-09-12: user explicitly clarified "T/K优先". Rank eligible arms by general-case mean(T/K); walking and probes explain the result and are not independent non-regression constraints.
- 2026-09-12: user explicitly permits aggressive Q4 strategies and extreme-case cost regression, prioritizing general-case efficiency while requiring complete clearing. New experiments rank the declared general cohort, report stress separately, and never omit stress failures or replace the frozen baseline automatically.
- 2026-09-12: user requested more Q4 ablations emphasizing local decisions and giving less weight to global-route optimization. Isolated local experiments are authorized; frozen-baseline adoption was not requested.
- 2026-09-12: user requested additional Q4 algorithm families and tuning, learning from Q3 J+S+O; isolated q4_transfer experiments are authorized without baseline adoption.

- 2026-09-12: user asked to inspect the Q4 517 s T/K scheme and freeze it as the Q4 baseline.
- 2026-09-12: user requested aggressive Q3 ablations targeting walking time and probe count.
- 2026-09-12: user requested large matched Q4 ablations focused on walking time and probe count, including aggressive strategies and screenshot-style tables.
- 2026-09-12: user asked to organize latest unsubmitted Q3/Q4 results as supporting materials, not paper chapters; headline numbers are Q3 JSO ~254 s and Q4 ~529 s.
- 2026-09-12: user asked to run Q3 JSO on official practice 20 times (practice only).
