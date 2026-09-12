# Q3 Offline Ablation Implementation Readiness Review

Review date: 2026-09-12. Independent Stage 5 review of the design and existing
Q3 runner interface. The experiment implementation is still in progress and is
outside this review's scope. This replaces the invalid earlier review artifact.

## Reviewed scope

- `B题/experiments/q3_ablation/design.md`
- `B题/memory.md`
- `B题/simulator_automation/q3_runner.py`
- `B题/simulator_automation/q3_fast_mode.py`
- `B题/simulator_automation/q3_state.py`
- `B题/src/params.py`
- `B题/data_preparation/parameters.csv` (the actual frozen CSV, rather than the dispatcher shorthand `params.csv`)
- `B题/experiments/q3_ablation/reviews/stage5-implementation-readiness-review.md` (superseded invalid review, inspected for context only)

## Findings

### F1 Coverage geometry is valid but station identity is part of the contract

- Type: coverage-and-state-contract
- Severity: WARNING
- Evidence reference: `B题/experiments/q3_ablation/design.md`, Algorithms; `B题/simulator_automation/q3_state.py`, P3_INDEX, cover_index and mark_cover_done; `B题/simulator_automation/q3_runner.py`, measure.
- Recommended action: implement and test all seven radius-1130 station identities, per-channel actual no-signal evidence, and completion bookkeeping together before batch execution.

For a radius-1800 source disk, center plus six radius-1130 stations gives a
maximum nearest-station distance of approximately 996.949676 m. The design's
Voronoi-intersection and boundary checks establish coverage within the minimum
1000 m reception radius, with approximately 3.05 m margin. Existing source
code separately stores remaining station coordinates and a global radius-1200
coordinate index. Replacing only remaining coordinates would break visitation
and absence accounting. Seven station visits are insufficient evidence unless
each still-unseen channel was actually measured there. Duplicate visits must
not count twice. The published upper bound of 16 detected sources is the only
count-based alternative to the complete discovery certificate.

### F2 Aggressive actions have implementable finite recovery requirements

- Type: termination-and-completeness
- Severity: WARNING
- Evidence reference: `B题/experiments/q3_ablation/design.md`, S/O parameters; `B题/simulator_automation/q3_fast_mode.py`, _resolve and _process_source; `B题/simulator_automation/q3_runner.py`, safe_channel; `B题/simulator_automation/q3_state.py`, done_all_channels.
- Recommended action: enforce the bounded refinement limits and retain the original complete SAFE recovery, reporting any unresolved channel or exhausted guard as a failed scene.

The current design specifies at least two bearings, normal-matrix condition
number at most 30, MEC radius at most 80 m, at most one speculative clear per
observation state, and at most four refinement rounds before SAFE. These are
sufficiently concrete to implement. S's 40 m, 1100 m and 12-degree thresholds
are heuristics and must not produce absence certificates. Pending-set removal
alone never proves clearing: the existing runner can remove a processed source
from P even after unsuccessful recovery. Final scoring must use channel status
and explicit certificates, and separately audit truth after the run. Guard
limits must also address repeated no-progress routing or skipped scans.

### F3 Baseline and factorial controls need distinct interpretation

- Type: experimental-identifiability
- Severity: WARNING
- Evidence reference: `B题/experiments/q3_ablation/design.md`, Planned ablations; `B题/simulator_automation/q3_fast_mode.py`, GreedyFastRunner.
- Recommended action: invoke the actual original GreedyFastRunner with source_budget_s=0 for the baseline and add an original-planner radius-only control, or explicitly limit what the baseline contrast identifies.

The eight compact-ring arms identify J/S/O effects when their common code,
recovery and accounting are identical. Comparing original GREEDY_FAST at 1200
with a newly implemented compact all-off arm can also include common changes
to scheduling and source resolution. A radius-only original-planner arm is the
clearest bridge and mirrors the supplied screenshot. An imitation of the
original algorithm does not establish the requested original-strategy baseline.
Main effects should average four matched contrasts across other factors;
all-on-minus-one contrasts are conditional effects and should be named as such.

### F4 Objective and synthetic noise match the intended evidence level

- Type: observation-and-accounting-contract
- Severity: INFO
- Evidence reference: `B题/data_preparation/parameters.csv`; `B题/experiments/q3_ablation/design.md`, Model and accounting.
- Recommended action: replay every action trace using the frozen parameter table and test deterministic paired noise and bearing error bounds after two-decimal rounding.

The objective distance/5 + 5*measurements + switches + 3*clear_attempts +
2*successes agrees with the frozen parameters. The initial receiver channel is
1; only measurements change it. Failed clears, no-signal measurements and
near measurements incur their specified costs. Noise fields that depend on
scene, channel and queried position permit paired comparisons without action
order determining the noise stream. Smooth, spatial and endpoint-sign regimes
are synthetic assumptions, because the contest specifies a bound rather than
a probability law. Exact repeated positions must return consistent errors;
the serialized coordinate key and rounding rule must be frozen. Source truth,
actual source count and hidden reception radius remain outside the policy API.

### F5 The paired experiment is sufficiently specified for implementation

- Type: evaluation-readiness
- Severity: INFO
- Evidence reference: `B题/experiments/q3_ablation/design.md`, Experiment protocol and Verification and evidence.
- Recommended action: freeze the scene generators, thresholds, seed manifests and source hashes after the 21-scene pilot, before evaluating all arms on the 420 shared scenes.

Seven source counts, four scene families, three noise regimes and five seeds
give 420 scenes per arm. The ten currently specified arms give 4200 paired
policy runs, or 4620 with the recommended radius-only control. The exact
generator definitions and baseline dependency hashes remain implementation
deliverables rather than prerequisites to writing that implementation. Pilot
and evaluation seeds must be disjoint. Retain failures, traceable scene IDs,
scene truth hashes and per-arm rows; do not replace failed scenes. Measure wall
runtime separately from virtual operational time. Bootstrap whole paired
scenes, ideally within the predeclared strata, rather than individual sources.

### F6 Reported conclusions must remain offline and exploratory

- Type: evidence-ceiling
- Severity: WARNING
- Evidence reference: `B题/experiments/q3_ablation/design.md`, Scope and authorization; `B题/memory.md`.
- Recommended action: label results as synthetic offline exploratory evidence and keep the screenshot aggregates, Q3 mainline promotion and Q4 frozen baseline outside the resulting performance claim.

Mean per-scene T/K and pooled sum(T)/sum(K) are different summaries and need
separate labels. Define K=0 handling explicitly. Clearance and certified full
scene completion precede time ranking; incomplete arms cannot win by doing
less work. A combined boundary/minimum-radius family is a joint stress test,
not an isolated causal test of either variable. Selecting a winner from this
evaluation supports a descriptive comparison within this matrix; stronger
generalization needs a later fresh holdout or official validation. The original
screenshot's nine scene identities were not supplied and cannot be reproduced
from aggregates alone.

## Blocking risks

No unresolved design-level blocking risk was identified for implementing this
isolated offline experiment. F1-F3 and F4-F5 specify checks required before a
benchmark may be treated as valid evidence. This review has not inspected or
approved the unfinished implementation, executed experiments, cleared a gate,
or determined whether those checks currently pass.

## Non-blocking warnings

### W1 Coverage and recovery implementation obligations

- Type: implementation-validation
- Severity: WARNING
- Evidence reference: F1-F2; `B题/experiments/q3_ablation/design.md`, Verification and evidence.
- Recommended action: demonstrate compact-station certificates, finite no-progress handling and full SAFE recovery in focused tests and pilot traces before the large run.

### W2 Attribution and evidence limits

- Type: comparison-interpretation
- Severity: WARNING
- Evidence reference: F3 and F6; `B题/experiments/q3_ablation/design.md`, Planned ablations and Scope and authorization.
- Recommended action: retain the real baseline, add or explain the radius-only control, and qualify every reported gain by completion, scene matrix and synthetic noise assumptions.

## Required follow-up

- Record this recommendation and allowed `exploratory_analysis` outputs in `B题/experiments/q3_ablation/gates/implementation-readiness.md`; the main agent owns the gate judgment.
- Update `B题/experiments/q3_ablation/design.md` with the final arm list and radius-only-control decision, generator definitions, K=0 treatment and finite no-progress rules.
- Add focused protocol and recovery checks under `B题/experiments/q3_ablation/` for all seven compact station identities, partial/duplicate coverage, per-channel observation certificates, hidden-count independence, deterministic bounded noise, failed-clear accounting and termination.
- Store the pilot results, locked thresholds, complete source and dependency hashes, CLI command, interpreter versions and 420-scene paired manifest under `B题/experiments/q3_ablation/` before evaluation.
- Store every arm's scene results and action traces under `B题/experiments/q3_ablation/`, including failures, and recompute time and completion independently before reporting the ranking.
- Request post-result independent validation in `B题/experiments/q3_ablation/reviews/stage6-validation-review.md`; use `B题/experiments/q3_ablation/rollbacks/` if later evidence exposes a model or implementation defect.

## Reviewer recommendation

The design is ready for implementation within the already specified isolated
offline scope. It defines at least three aggressive mechanisms, a paired
factorial experiment, a valid compact cover, finite speculative refinement and
an appropriate exploratory evidence ceiling. I recommend that the main agent
record a readiness gate with the F1-F6 obligations and require focused checks
and the pilot before accepting a large-run result. No additional user decision
is identified by this review for the requested implementation. This is an
expert recommendation, not a user confirmation, gate clearance, stage completion
or approval of any performance claim.

Verdict: PASS_WITH_WARNINGS

## Required reads referenced

- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-subagent-delegation.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-readiness-gate.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-human-confirmation.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/subagent-model-building.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-rollback.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/references/protocol-fallback-and-deviation.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-output-schema.md`
- `C:/Users/zty/.agents/skills/math-modeling-v4/schemas/reviewer-self-discipline-checklist.md`
- `B题/experiments/q3_ablation/design.md`
- `B题/memory.md`
- `B题/simulator_automation/q3_runner.py`
- `B题/simulator_automation/q3_fast_mode.py`
- `B题/simulator_automation/q3_state.py`
- `B题/src/params.py`
- `B题/data_preparation/parameters.csv`

## Confidence

high - Direct inspection of the current design, runner interfaces, frozen parameters and required protocols supports the scoped implementation-readiness assessment; unfinished code and future results are explicitly excluded.

## Forbidden-behavior self-check

- [OK] Did not confirm user decisions
- [OK] Did not clear blockers
- [OK] Did not mark stages or rounds complete
- [OK] Did not increase claim level on behalf of the main agent
- [OK] Did not invoke another subagent
- [OK] Did not write or edit project files outside the review output
