# Q4 second exploratory ablation: Q3 JSO transfer and different solver families

Date: 2026-09-12. User explicitly requests more solution types and tuning,
using the newly improved Q3 J+S+O result as reference. This authorizes isolated
offline implementation and experiments, not adoption into the frozen baseline.
All prior Q3/Q4 source and result artifacts remain unchanged.

## Grounded Q3 reference

experiments/q3_ablation/evaluation/summary.csv: JSO 420/420 scenes, 5460/5460
sources, mean T/K 254.05321048920862 s, mean movement 2518.529530835219 s,
107.62380952380953 probes. Q3 is omnidirectional and has seven discovery sites.
Its numerical score is not a matched Q4 benchmark. Inspect policies.py methods
_estimate, _useful, _supplement, _viewpoint, _resolve, choose_greedy_action.

## Families to implement

1. J/S/O transfer, full 2^3 factorial on unchanged TRI25. J uses posterior
   source-center tour proxies. S senses other detected channels at localization
   and clearing stops when predicted reception is >=0.7 and parallax >=12 degrees
   or range halves; it skips already-adequate regions and already measured sites.
   O uses at least two nondegenerate positive bearings (normal matrix condition
   <=30) for least-squares line intersection, with enclosing radius <=80 m.
   Any estimate must be legal and inside the continuous positive feasible polygon.
   A failed estimate is not retried before a new positive observation; total
   speculative attempts are bounded. Certified and optical clears are preserved.
2. Certificate-route insertion: first plan the remaining mandatory coverage tour,
   then execute pending tasks only if incremental detour below 80/200/400 m or
   no unknown-channel coverage work remains. This differs from a global tour of
   transient refinement points and from completing each source greedily.
3. Action-aligned localization: score V4 candidate probes with the actual next
   cover nearest to the robot, rather than fixed stale route order. A separate
   D-optimal family scores reception-weighted angular information against travel
   plus continuation to the next coverage site. These change viewpoint design.
4. Directional reception recovery: after negative RF, try a short symmetric
   bracket before the nearest feasible source projection. Use the same affine
   vertex distance proof as frozen V4; negative RF never removes feasible points.
5. Geometry-driven clearing: when optical cover of a localized polygon has at
   most 2/4 cells, compare/use its finite certified clear tour before another RF
   refinement. A separate conservative micro-tuning moves certified clear points
   toward the incoming position by only the rigorously available radius slack.
6. Geometry/combination tuning: 1900/1920/1950/1980 m outer witnesses, optimistic
   radius 80/120/160, reception gate 0.5/0.7/0.85. Every geometry passes the
   continuous cover certificate, and heuristic parameters only schedule actions.

All variants cap dedicated refinement at eight attempts, retain the complete
optical fallback, never abandon a detected source, and retain all 25 unknown-
channel scans or the independent observed-16-channel counting certificate.
Do not use true source locations, type, headings, radius or N in policy code.
Failed clear operations, receiver switches and all movement are charged.

## Experiments and locking

Development: 30 matched mixed endpoint settings, seeds 20000-20029, plus 10
boundary outward endpoint settings on seeds 20000-20009. Publish all rows.
Initial parameters are the predeclared values above. Run family singles and
JSO factorial, then select a small number of combinations on development only.

Primary: after development, freeze exact variant registry/hash. Use a new
400-setting cohort: 200 mixed endpoint seeds 30000-30199 plus 50 each of
directional, omni, outward boundary endpoint and mixed smooth on 30000-30049.
All variants get all 400 identical settings. This has 200 independent seed blocks.
Frozen V4 is rerun for every scene and is always the paired comparison anchor.
The previous round champion is included as an additional comparator, never
as a substitute baseline. Avoid comparison against its old 529 s aggregate.

Report source and scene success, mean T, mean(T/K), pooled T/K, walking time,
probe counts, discovery/refinement split, failed clears, optical fallback,
paired wins/losses, p95, worst delta and every source/error/N subgroup. Keep
failed variants and rows visible. Winner eligibility requires no failed scenes.
Use paired seed-block bootstrap and state multiple-comparison/selection limits.
If a candidate improves overall but worsens the directional boundary group,
report the regression prominently. Never identify the hidden scene type online.

## Reproducibility and review

Separate code, manifests, raw event traces, scenario hashes and summaries live
under experiments/q4_transfer/. Reuse immutable first-round implementation by
imports, without editing it. Protect the original 13-entry frozen SHA256 map.
Store a source snapshot before any long run; no file rename or mutation during
the run. Independently validate time accounting, observation bounds, all clears
and per-channel absence certificates using the recorded events and environment.
Request an implementation review per math-modeling-v4. If provider access is
still unavailable, explicitly record pending independent review and deliver
user-authorized exploratory results without claiming formal adoption.

## Readiness clarifications before implementation

Independent review: reviews/implementation-readiness.md, PASS_WITH_WARNINGS.
O uses cond(A)<=30 on the bearing normal matrix itself, matching Q3 code.
In O-enabled adaptive execution, all noncertified center trials are replaced
by the O path (not appended to the inherited center trials). Total O trials
are capped at two per source and at one per distinct count of positive
direction/near observations. Negative-only history never resets this counter.
S requires probability >= threshold AND (parallax >=12 degrees OR range halves).
Its same-stop calls are guarded against recursion and remeasurement; it never
scans unseen channels. The D-optimal and aligned families keep the proven
baseline recovery pair ahead of any heuristic re-ranking after RF shadow.
Multi-process execution isolates cover-mode globals; threads are not used.
Q4 already has adaptive joint routing and speculative clearing. J/S/O are
incremental transfers within that existing algorithm, not switches proving
the absence of joint routing or optimistic clearing in the frozen baseline.
