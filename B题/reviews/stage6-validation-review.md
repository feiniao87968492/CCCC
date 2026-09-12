# Stage 6 Validation Review — Q4 TRI25 + ROUTE_ADAPTIVE_V4

## Reviewed scope
- `data/validation/validation-report.md`
- `docs/Q4效率瓶颈与V4优化-20260912.md`
- `docs/Q4覆盖命题.md` (SQUARE81-era P4 statement; not the TRI25 certificate)
- `experiments/q4_efficiency/release_holdout100.json`
- `experiments/q4_efficiency/release_holdout100.meta.json`
- `experiments/q4_efficiency/release_holdout100.csv` (header, seeds 1000–1099, optical-fallback rows, worse seeds)
- `experiments/q4_efficiency/holdout100_paired.csv` (header; worse seeds 1065 / 1092 / 1093)
- `experiments/q4_efficiency/paired_summary.json`
- `experiments/q4_efficiency/practice_attempt.json`
- `experiments/q4_efficiency/baseline_holdout100.json`
- `experiments/q4_efficiency/baseline_holdout100.csv` (worse-seed rows)
- `experiments/q4_efficiency/baseline_holdout100.meta.json`
- `experiments/q4_efficiency/release30.json`
- `experiments/q4_efficiency/release30.meta.json`
- `experiments/q4_efficiency/release_directional30.json`
- `experiments/q4_efficiency/release_omni30.json`
- `experiments/q4_efficiency/release_boundary30.json`
- `experiments/q4_efficiency/bench.py`
- `_tmp_check_q4_baseline.py`
- `simulator_automation/q4_practice.py` (CLI defaults)
- `src/q4_cover.py` (TRI25 builder; `Q4_COVER_MODE` fallback)
- `src/q4_policy.py` (`Q4_ROUTE_MODE` fallback)
- `src/q4_certificate.py`
- `tests/test_q4_efficiency.py` (TRI25 certificate tests)
- `workflow.md`
- `memory.md`
- `findings.md` (HEX37-era notes; not V4 freeze evidence)
- Absence check: `claims/` does not exist; `reviews/` did not exist before this file; `gates/` does not exist

## Findings

### F1 — Holdout mean T/K 517.5842931731096 s is reproduced from the primary artifacts
- Type: independent-numeric-replay
- Severity: INFO
- Evidence reference: `experiments/q4_efficiency/release_holdout100.json` (`mean_T_over_K`: 517.5842931731096; `cover`: TRI25; `route`: ROUTE_ADAPTIVE_V4; `error_mode`: endpoint; `sources`: mixed; `cases`: 100; `full_success`: 100; `failed_seeds`: []); `experiments/q4_efficiency/release_holdout100.meta.json` (`seed_start`: 1000); `experiments/q4_efficiency/release_holdout100.csv` seeds 1000–1099; `data/validation/validation-report.md` Independent numeric replay table
- Recommended action: Freeze this JSON mean, not a rounded 517.58 s headline, as the Q4 primary metric.

The CSV is 101 lines (header + 100 rows), seeds 1000 through 1099 with no gap. No `all_certified=False` row was found. Failure cells are empty. Min T/K 258.13623777185825 s (seed 1058) and max T/K 766.7178646948478 s (seed 1070) match the validation-report CSV extrema. Four optical-fallback events (seeds 1027, 1043, 1044, 1076, each `n_optical_fallback=1`) sum to 4 and match `mean_n_optical_fallback=0.04`. JSON p95 T/K 677.2650412845248 s matches the report. The CSV-vs-JSON mean listed in the report (517.584293173110 vs 517.5842931731096) is a 4e-13 aggregation residual, not a contradiction.

### F2 — Offline 100/100 full-clear plus certificate supports feasible_baseline, not a higher claim
- Type: claim-level-support
- Severity: INFO
- Evidence reference: `experiments/q4_efficiency/release_holdout100.json` (`full_success`: 100); `src/q4_certificate.py` (`discovery_certificate`); `experiments/q4_efficiency/paired_summary.json` `tri25_certificate` (`valid`: true, `n_points`: 25, `max_distance_m`: 943.0121947375769, `hull_margin_m`: 17.74943008678929, `triangles_checked`: 36); `tests/test_q4_efficiency.py` `test_tri25_has_a_continuous_discovery_certificate`; `data/validation/validation-report.md` Supported claim level
- Recommended action: Keep the supported claim at `feasible_baseline`; do not write locally_optimal_solution, validated_optimum, or global_optimum into the freeze.

TRI25 is constructed as a 19-site 920 m lattice plus six 1950 m boundary witnesses (`src/q4_cover.py` `_build_tri25`). The certificate is a sufficient continuous cover (`max_distance_m` 943.012 m < `R_min` 1000 m), not a minimal-point proof. Supporting groups in the validation-report (dev 30 + holdout 100 + directional 30 + omni 30 + boundary 30) are 220/220 full-clear in the cited offline geometry; those groups do not raise the claim ceiling.

### F3 — Paired comparison is an average improvement, with 3/100 slower N=16 scenes
- Type: per-scene-nonoptimality
- Severity: WARNING
- Evidence reference: `experiments/q4_efficiency/holdout100_paired.csv` rows 1065 / 1092 / 1093; `experiments/q4_efficiency/paired_summary.json` `holdout100` (`improved`: 97, `worst_delta_s`: 48.260035145791505); `experiments/q4_efficiency/release_holdout100.csv` and `baseline_holdout100.csv` same seeds; `memory.md` Counterexamples
- Recommended action: Record the three worse seeds and the “average, not per-scene optimum” bound in `claims/baseline-q4.md`; do not freeze a path-optimality claim.

Worse holdout rows, all N=16, match across paired CSV, release CSV, and baseline CSV:

| seed | N | HEX37/V3 T/K (s) | TRI25/V4 T/K (s) | Δ T/K (s) |
|---|---:|---:|---:|---:|
| 1065 | 16 | 430.74751880049797 | 437.0079521654748 | +6.260433364976848 |
| 1092 | 16 | 319.8855687264751 | 368.14560387226663 | +48.260035145791505 |
| 1093 | 16 | 396.2329035893946 | 415.7577328519105 | +19.52482926251588 |

Mean drop 735.3565026536246 → 517.5842931731096 (−29.6145%) is an average-efficiency fact. Seed 1000 after-T/K 635.948337693204 and seed 1099 after-T/K 640.5965560014506 also match the release CSV, so the paired file is the same holdout, not a relabeled set.

### F4 — Official simulator was not obtained; offline T/K is not official T/K
- Type: missing-official-path
- Severity: WARNING
- Evidence reference: `experiments/q4_efficiency/practice_attempt.json` (`started`: false, `robot_actions_sent`: false, `official_results`: null, `failure`: login timed out); `data/validation/validation-report.md` Official practice; `experiments/q4_efficiency/release_holdout100.meta.json` `source`: "offline bounded-error geometry; not official practice"
- Recommended action: Freeze the offline holdout only; keep official-simulator T/K blocked until a later evidence path exists.

This warning caps the claim at `feasible_baseline`. It does not contradict the offline 517.5842931731096 s result.

### F5 — Git HEAD 3c144685 is not the V4 reproducibility anchor
- Type: reproducibility-anchor-mismatch
- Severity: WARNING
- Evidence reference: `data/validation/validation-report.md` Reproducibility (HEAD `3c144685832cc1df2ef6c84e581094bdd054c417`; `src/q4_cover.py`, `src/q4_policy.py`, `simulator_automation/q4_runner.py` modified; `src/q4_adaptive.py`, `src/q4_certificate.py`, `experiments/q4_efficiency/release_holdout100.json` untracked); `experiments/q4_efficiency/release_holdout100.meta.json` `sha256`; `memory.md` Pitfalls
- Recommended action: Put the working-tree SHA256 map from `release_holdout100.meta.json` in `claims/baseline-q4.md` / the snapshot index; do not list git `3c144685` as the code commit that produced V4.

This reviewer did not re-hash the working tree. The validation-report states 0 SHA256 mismatches against that manifest. The freeze must treat the manifest as the anchor, not HEAD.

### F6 — Dev 30 mean T/K 489.79 s uses smooth error and must not be frozen
- Type: wrong-split-metric
- Severity: WARNING
- Evidence reference: `experiments/q4_efficiency/release30.json` (`error_mode`: "smooth", `mean_T_over_K`: 489.7928667317867, seeds implied 0–29); `experiments/q4_efficiency/release30.meta.json` `error_mode`: smooth; `data/validation/validation-report.md` Supporting groups; `memory.md` Rules
- Recommended action: Exclude `release30.json` from `claims/baseline-q4.md` primary metrics.

Holdout 1000–1099 / endpoint / mixed is the freeze metric. Directional 550.4069560674575 s, omni 475.1409080301444 s, and boundary 583.8610228024756 s are supporting groups only.

### F7 — Practice CLI, module env fallbacks, and bench.py defaults are three different scheme identities
- Type: solver-identity-drift
- Severity: WARNING
- Evidence reference: `simulator_automation/q4_practice.py` lines 104–108 (defaults TRI25 + ROUTE_ADAPTIVE_V4); `src/q4_cover.py` `_initial_mode` (`Q4_COVER_MODE` falls back to SQUARE81); `src/q4_policy.py` `_initial_route_mode` (`Q4_ROUTE_MODE` falls back to OLD_HEX37); `experiments/q4_efficiency/bench.py` lines 50–54 (defaults HEX37, ROUTE_INSERT_V3, smooth)
- Recommended action: Freeze the explicit command `--cover TRI25 --route ROUTE_ADAPTIVE_V4 --error-mode endpoint --seed-start 1000 --cases 100`; do not rely on bench.py or env fallbacks to reconstruct the baseline.

The holdout that produced 517.5842931731096 s was the explicit-arg run recorded in `release_holdout100.meta.json`, not the bench.py default path.

### F8 — Validation path is same-solver artifact replay plus certificate tests, not a second solver
- Type: validation-path-strength
- Severity: WARNING
- Evidence reference: `experiments/q4_efficiency/bench.py` (primary generator: `Q4Runner(NoisyGeomSim(...))`); `_tmp_check_q4_baseline.py` (CSV/JSON/hash replay of the same artifacts); `tests/test_q4_efficiency.py`; `experiments/q4_efficiency/baseline_holdout100.meta.json` (paired path loads `experiments/q4_efficiency/baseline/*.py` with HEX37 + ROUTE_INSERT_V3)
- Recommended action: Treat the HEX37/V3 snapshot as a paired comparator, not as an independent V4 reproduction; do not upgrade claim level on the basis of this validation path.

Cross-path consistency that does hold: V4 holdout artifacts internally agree; the frozen V3 snapshot on the same 100 seeds is 735.356502653625 s mean T/K with 100/100 full-clear; TRI25 certificate tests exist. Cross-path that does not hold: no official-simulator replay, and no second independent V4 implementation. That gap is why `feasible_baseline` is the ceiling, not a reason to reject the freeze.

### F9 — Multi-question contest; only Q4 has freezeable evidence
- Type: per-question-freeze-scope
- Severity: INFO
- Evidence reference: `workflow.md` Checklist (“Q1 / Q2 / Q3 per-question baselines: not in this slice”); `data/validation/validation-report.md` (`Question: Q4 only`); absence of `claims/`; Q1–Q3 code/docs exist under `src/`, `tests/`, `docs/`, `experiments/q3_simulator/`
- Recommended action: Main agent writes `claims/baseline-q4.md` plus an index `claims/baseline-snapshot.md` that marks Q1–Q3 as not frozen; do not invent Q1–Q3 metric rows.

### F10 — No Stage 1–5 structural defect requiring rollback
- Type: rollback-trigger-check
- Severity: INFO
- Evidence reference: `references/protocol-rollback.md` severity table; holdout 100/100 certified; TRI25 certificate `valid: true`; paired 97/100 improved; no numeric contradiction of 517.5842931731096 s
- Recommended action: Do not open a Stage 1–5 rollback. Keep later paper/docs aligned to TRI25/V4 rather than silently patching `docs/Q4覆盖命题.md` into the freeze.

`docs/Q4覆盖命题.md` still states SQUARE81 as P4. That is a documentation lag for later writing, not a defect in the holdout solver under review.

### F11 — N=16 counting certificate is independent of TRI25 geometric cover
- Type: scheme-identity
- Severity: INFO
- Evidence reference: `src/q4_cover.py` `_build_tri25`; `experiments/q4_efficiency/release_holdout100.csv` (N=16 rows with `n_cover_visited` < 25, e.g. seed 1058 visited 6); `memory.md` Rules; `data/validation/validation-report.md` Scheme identity
- Recommended action: State in `claims/baseline-q4.md` that N=16 counting remains independent of the TRI25 hull certificate, and that `no_signal` is not `d>1000`.

## Blocking risks
None. No finding in this review has Severity BLOCKING. The offline holdout does not contradict the stated mean, and the intended freeze claim `feasible_baseline` is not stronger than the evidence.

## Non-blocking warnings

### W1 — Average improvement, three worse N=16 scenes
- Type: per-scene-nonoptimality
- Severity: WARNING
- Evidence reference: `experiments/q4_efficiency/holdout100_paired.csv` seeds 1065 / 1092 / 1093; `experiments/q4_efficiency/paired_summary.json` `holdout100`
- Recommended action: Write the 97/100 / 3/100 / +48.260035145791505 s bound into `claims/baseline-q4.md`.

### W2 — Official simulator missing
- Type: missing-official-path
- Severity: WARNING
- Evidence reference: `experiments/q4_efficiency/practice_attempt.json`
- Recommended action: Block any official-simulator T/K sentence in the freeze and in later paper drafts until new official evidence exists.

### W3 — Git HEAD is not the V4 tree
- Type: reproducibility-anchor-mismatch
- Severity: WARNING
- Evidence reference: `data/validation/validation-report.md` Reproducibility; `experiments/q4_efficiency/release_holdout100.meta.json`
- Recommended action: Freeze SHA256 from the meta manifest, not commit `3c144685`.

### W4 — Do not freeze the smooth-error Dev 30 mean
- Type: wrong-split-metric
- Severity: WARNING
- Evidence reference: `experiments/q4_efficiency/release30.json` (`error_mode`: smooth, `mean_T_over_K`: 489.7928667317867)
- Recommended action: Keep 489.79 s out of `claims/baseline-q4.md` primary metrics.

### W5 — Default scheme identity is not unique
- Type: solver-identity-drift
- Severity: WARNING
- Evidence reference: `simulator_automation/q4_practice.py`; `src/q4_cover.py`; `src/q4_policy.py`; `experiments/q4_efficiency/bench.py`
- Recommended action: Freeze explicit CLI flags; warn that env fallbacks remain SQUARE81 / OLD_HEX37.

### W6 — Validation is not a second V4 solver
- Type: validation-path-strength
- Severity: WARNING
- Evidence reference: `experiments/q4_efficiency/bench.py`; `_tmp_check_q4_baseline.py`; `experiments/q4_efficiency/baseline_holdout100.meta.json`
- Recommended action: Leave claim level at `feasible_baseline`; do not treat paired V3 or CSV replay as `validated_optimum`.

## Required follow-up
- Main agent: write `claims/baseline-q4.md` per `C:\Users\zty\.agents\skills\math-modeling-v4\references\baseline-snapshot-template.md`, primary metric mean T/K = 517.5842931731096 s from `experiments/q4_efficiency/release_holdout100.json`, claim level `feasible_baseline` only.
- Main agent: write index `claims/baseline-snapshot.md` listing Q4 → `claims/baseline-q4.md` and Q1–Q3 as not frozen; do not invent Q1–Q3 metric rows.
- Record reproducibility from `experiments/q4_efficiency/release_holdout100.meta.json` SHA256 (not git HEAD `3c144685832cc1df2ef6c84e581094bdd054c417`).
- Record the exact replay command in `claims/baseline-q4.md`: `python experiments/q4_efficiency/bench.py --cover TRI25 --route ROUTE_ADAPTIVE_V4 --error-mode endpoint --seed-start 1000 --cases 100 --output experiments/q4_efficiency/recheck_v4.csv`.
- Copy the paired bound from `experiments/q4_efficiency/holdout100_paired.csv` / `paired_summary.json` (97/100 faster; seeds 1065, 1092, 1093 slower; worst +48.260035145791505 s).
- Cite `experiments/q4_efficiency/practice_attempt.json` as the official-simulator blocker; do not write official T/K.
- Do not put `experiments/q4_efficiency/release30.json` 489.7928667317867 s into primary metrics.
- Do not raise claim level above `feasible_baseline` in `claims/baseline-q4.md` or `claims/baseline-snapshot.md`.
- Do not export; `reviews/stage10-evidence-claim-review.md` and `gates/final-evidence-gate.md` do not exist.
- Do not open `rollbacks/` for this result. Documentation lag in `docs/Q4覆盖命题.md` belongs to later writing, not a Stage 1–5 rollback.

## Reviewer recommendation
The Q4 scheme `TRI25 + ROUTE_ADAPTIVE_V4` is internally consistent on the independent holdout seeds 1000–1099: endpoint mixed sources, 100/100 full-clear and certified, mean T/K 517.5842931731096 s in `release_holdout100.json`, matching CSV extrema, optical-fallback count, and paired after-values. The paired HEX37/V3 snapshot on the same seeds is an average-efficiency improvement (97/100 faster; 3/100 slower, all N=16, worst +48.26 s), not a per-scene path optimum. Official practice did not start. Git HEAD does not contain the V4 tree, so the freeze must use the meta.json SHA256 map. Dev 30 smooth-error 489.79 s is a different split and must stay out of the frozen primary metric. Those limits keep the supported claim at `feasible_baseline`. They do not contradict the main result and do not expose a Stage 1–5 structural defect. This is the first Stage 6 PASS_WITH_WARNINGS for Q4, so the **main agent** (not this reviewer) must freeze `claims/baseline-q4.md` and the multi-question index `claims/baseline-snapshot.md` (Q1–Q3 not frozen) per `references/baseline-snapshot-template.md`. Do not increase claim level.

Verdict: PASS_WITH_WARNINGS

## Decision / gate / branch / rollback recommendation
Allow the main agent to freeze Q4 only at `feasible_baseline`; no rollback; no method-revision branch; official-simulator T/K remains blocked.

## Required reads referenced
- `C:\Users\zty\.agents\skills\math-modeling-v4\references\subagent-validation-paper.md`
- `C:\Users\zty\.agents\skills\math-modeling-v4\references\protocol-subagent-delegation.md`
- `C:\Users\zty\.agents\skills\math-modeling-v4\references\protocol-rollback.md`
- `C:\Users\zty\.agents\skills\math-modeling-v4\references\protocol-readiness-gate.md`
- `C:\Users\zty\.agents\skills\math-modeling-v4\references\baseline-snapshot-template.md`
- `C:\Users\zty\.agents\skills\math-modeling-v4\schemas\reviewer-output-schema.md`
- `C:\Users\zty\.agents\skills\math-modeling-v4\schemas\reviewer-self-discipline-checklist.md`
- `data/validation/validation-report.md`
- `docs/Q4效率瓶颈与V4优化-20260912.md`
- `docs/Q4覆盖命题.md`
- `experiments/q4_efficiency/release_holdout100.json`
- `experiments/q4_efficiency/release_holdout100.meta.json`
- `experiments/q4_efficiency/release_holdout100.csv`
- `experiments/q4_efficiency/holdout100_paired.csv`
- `experiments/q4_efficiency/paired_summary.json`
- `experiments/q4_efficiency/practice_attempt.json`
- `experiments/q4_efficiency/baseline_holdout100.json`
- `experiments/q4_efficiency/baseline_holdout100.csv`
- `experiments/q4_efficiency/baseline_holdout100.meta.json`
- `experiments/q4_efficiency/release30.json`
- `experiments/q4_efficiency/release30.meta.json`
- `experiments/q4_efficiency/release_directional30.json`
- `experiments/q4_efficiency/release_omni30.json`
- `experiments/q4_efficiency/release_boundary30.json`
- `experiments/q4_efficiency/bench.py`
- `_tmp_check_q4_baseline.py`
- `simulator_automation/q4_practice.py`
- `src/q4_cover.py`
- `src/q4_policy.py`
- `src/q4_certificate.py`
- `tests/test_q4_efficiency.py`
- `workflow.md`
- `memory.md`
- `findings.md`

## Confidence
medium — artifact cross-checks confirm the holdout mean, 100/100 certificates, worse-seed rows, scheme identity, and official-sim gap, but this reviewer did not re-execute SHA256, pytest, or the 100-seed bench.

## Forbidden-behavior self-check
- [OK] Did not confirm user decisions
- [OK] Did not clear blockers
- [OK] Did not mark stages or rounds complete
- [OK] Did not increase claim level on behalf of the main agent
- [OK] Did not invoke another subagent
- [OK] Did not write or edit project files outside the review output
- [OK] Did not write claims/baseline-snapshot.md (only recommended freezing)
- [OK] Did not export when the final evidence gate has not passed
