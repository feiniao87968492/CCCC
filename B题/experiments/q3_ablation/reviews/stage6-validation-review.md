# Stage 6 Validation Review — Q3 paired ablation

## Reviewed scope

- `B题/experiments/q3_ablation/design.md`
- `B题/experiments/q3_ablation/data_validation_report.md`
- `B题/experiments/q3_ablation/evaluation/summary.csv`
- `B题/experiments/q3_ablation/evaluation/paired_deltas.csv` and `paired_deltas.json`
- `B题/experiments/q3_ablation/evaluation/manifest.json`, `rows.csv`, `scenes.json`, and compressed traces
- `B题/tests/test_q3_ablation.py` (17 tests)
- Existing Stage 5 readiness review for obligations carried into validation

The review checks trace and objective accounting, scene and arm completion,
paired identity, and the strength of claims supported by this offline matrix.

## Findings

### F1 — Complete, paired evaluation matrix

The evaluation contains 4,200 rows: 420 shared scene IDs × 10 variants. Each
scene has all ten variants and one source hash; the matrix is balanced across
N=10…16, four spatial families, and three error modes (50 rows per N/family
cell). All 4,200 rows have `full_success=True`, `all_certified=True`, `K=N`,
`detected=K`, no failure, and `truth_clear_match/action_count_match=True`.
Every scene has a compressed trace, and each trace contains ten variant runs.

### F2 — Independent accounting replay is consistent

Recomputing every row gives
`T = move_m/5 + 5*n_measure + n_switch + 3*n_clear + 2*K`, with maximum
absolute residual 5.5e-12 s. The serialized components also satisfy
`movement_s=move_m/5`, `measure_s=5*n_measure+n_switch`, and
`clear_s=3*n_clear+2*K`; `T_over_K=T/K` to 1.8e-13 s. Comparing all 4,200
trace summaries to their rows gives maximum T residual 9.1e-13 s. Recorded
action and total-time replay errors are at numerical roundoff (≤9.1e-13 s).
The focused protocol suite passes: `17 passed`.

### F3 — Main paired effects are internally reproducible

The same-scene paired file reproduces the reported deltas. JSO has mean
ΔT=-1612.91 s, Δ walking=-1321.62 s, and Δ measurements=-28.64, with T and
measurement win rates 99.52% and 97.14%; J and JS show the same direction.
The all-scan negative control saves walking (−1463.26 s) but adds 216.99
measurements and has p95 ΔT=+1133.42 s. This supports the intended separation
of route savings from probing cost. O primarily reduces failed clears
(−41.14) while its measurement win rate is only 50%.

### F4 — Hashes and provenance are coherent

Manifest hashes for environment, policies, runner, design, scenes, and rows
match the files on disk. The manifest records the exact command, Python 3.10.11,
NumPy 2.2.6, SciPy 1.15.3, 420 scenes, and `changed_inputs=[]`. This is a
reproducibility anchor for the saved offline run.

### F5 — Supported claim ceiling

The evidence supports a descriptive `exploratory_analysis` comparison within
the declared synthetic scene/error matrix. It does not support official
simulator equivalence, global or validated optimality, or universal
superiority. The screenshot's nine scenes/117 sources were not reconstructed.
The review therefore does not promote any arm to the official Q3 mainline.

## Blocking risks

No blocking accounting, completion, pairing, or trace-integrity defect was
found. The principal limitations are evidence-scope limitations and do not
invalidate the recorded offline comparison. A rollback is not indicated by
the current validation evidence.

## Non-blocking warnings

- The design requests bootstrap intervals and subgroup results, but no such
  artifacts are present beside the aggregate summary and paired deltas. Add
  stratified (whole-scene) bootstrap intervals and family/N/error-mode tables
  before using these results in a paper-facing claim.
- The independent check replays saved traces and recomputes accounting; it does
  not constitute a second policy implementation or an official simulator run.
  Keep wording at exploratory-analysis level and preserve all synthetic-noise
  assumptions.
- The 1,130 m compact-ring coverage margin is only about 3.05 m; coordinate or
  problem-parameter changes require rerunning coverage and completion checks.

## Required follow-up

- Main agent should retain the aggregate and paired tables, traces, manifest,
  and test output as the validation evidence bundle.
- Generate subgroup summaries and scene-level bootstrap intervals before any
  stronger comparative statement; do not rank incomplete runs (none are
  incomplete here).
- If this is the first Stage 6 PASS/PASS_WITH_WARNINGS for Q3, freeze the
  reported primary metrics and claim ceiling in `claims/baseline-q3.md` and
  update the multi-question `claims/baseline-snapshot.md` index, following the
  baseline-snapshot template. Later changes must be recorded as improvement
  rounds rather than overwriting the snapshot.

## Reviewer recommendation

PASS_WITH_WARNINGS for the isolated synthetic offline Q3 ablation. The complete
paired matrix, exact trace accounting, deterministic replay, and focused tests
support the reported within-matrix reductions in travel time and measurements.
Continue only with the `exploratory_analysis` claim ceiling; add subgroup and
bootstrap evidence before any paper-facing comparison. This recommendation
does not clear other workflow gates, confirm user decisions, mark a stage
complete, or authorize export.

## Required reads referenced

- `C:/Users/zty/.agents/skills/math-modeling-v4/references/subagent-validation-paper.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-subagent-delegation.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-rollback.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-readiness-gate.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/baseline-snapshot-template.md`
- `B题/experiments/q3_ablation/design.md`
- `B题/experiments/q3_ablation/data_validation_report.md`
- `B题/experiments/q3_ablation/evaluation/summary.csv`
- `B题/experiments/q3_ablation/evaluation/paired_deltas.csv`
- `B题/experiments/q3_ablation/evaluation/manifest.json`
- `B题/tests/test_q3_ablation.py`

## Confidence

High for trace accounting, completion, pairing, hash integrity, and the stated
exploratory claim ceiling; moderate for external generalization because the
evidence is synthetic and lacks subgroup/bootstrap artifacts.

## Forbidden-behavior self-check

- [OK] Did not confirm user decisions
- [OK] Did not clear blockers or mark a stage complete
- [OK] Did not increase the supported claim level
- [OK] Did not modify source files or result data
- [OK] Did not invoke another subagent
- [OK] Did not export or authorize export

## Decision / gate / branch / rollback recommendation

Decision: PASS_WITH_WARNINGS; gate: allow only `exploratory_analysis` reporting;
branch: add subgroup and scene-level bootstrap evidence before paper claims;
rollback: none indicated by current validation, but trigger method/structural
rollback if a fresh replay contradicts these results.
