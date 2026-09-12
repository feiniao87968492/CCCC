# Q4 local-decision ablation, round 3

User: “再来几组消融实验，建议重局部策略，轻全域路线进行优化”.
Authorization covers isolated implementation and matched offline experiments;
no frozen baseline replacement. Existing Q3/Q4 code and results stay immutable.

## Scope and controls

All new local arms keep TRI25 radius1950 and the frozen V4 global tour selection.
Local actions can change the resulting path but not the global route optimizer,
cover sites, mandatory absence scans or stopping certificate. Frozen baseline
is the paired anchor. Last-round JSO_compact_dopt is an additional comparator
with its effective center/S/O/D-optimal/radius1900 settings fully recorded.
S_all (the already-tested standalone S) is an additional probe-policy control.

The previous round showed reduced refinement but increased discovery costs;
O added almost no mean benefit on JS, route insertion lost, and low mean did
not imply boundary robustness. This round targets local RF/clear choices.

## Initial families and exact parameters

L30/L90: local completion-cost probe ranking. Reuse all legal unmeasured V4
candidates; rank by immediate travel to the probe plus expected probe-to-source
travel, measurement cost and an incomplete-localization penalty (30/90 s).
For each spatial RF hypothesis, predict next radius using the existing bounded-
bearing parallax proxy 2*tan(1.005deg)*distance/max(sine,.015). A smooth completion
weight clip((40-predicted_radius)/20,0,1) is RF-weighted. Score is
distance(pos,p)/5 + E[distance(p,g)]/5 + 6 + penalty*(1-p_finish)
+ 12*(1-p_heard). Negative observations update only soft weights. This is a
heuristic expected local cost, not a proof of next-observation precision.
Restore the certified one-positive negative-RF bracket before any ranking.

P1/P2: budgeted selective stop probes. Use S's admitted-channel criteria and
probability gate .7, then rank by reception-weighted expected log-radius gain
per 5 s measurement plus actual 0/1 s channel switch. Execute at most1/2 probes
at the SAME physical stop across repeated callbacks. Guard recursion and
repeated coordinates; reset stop budget only after real movement >1 m. Cover
scans of unknown channels are exempt and remain mandatory. S_all is the
matched reference for separating adding S from imposing its local budget.

F60/F120: bounded same-source continuation. After an executed source measure
or clear, allow at most two additional actions for that source, provided it is
still detected and the proposed action is <=60/120 m away. All dedicated
measurements count toward the original cap8. Stop continuation after a negative
measurement or failed clear. Never start a full optical tour inside this burst;
return to ordinary scheduler, which can execute the complete fallback. No
recursive burst or unbounded focus on one source. No global route change.

C1/C15: optical-vs-RF local cost choice. If the next task is measure or heuristic
aggressive clear, rho<=80 and the COMPLETE optical cover has <=12 cells,
compute the nearest-neighbor full-cover route and charge travel/5 +3 per cell
+2 success. Compare with one RF action and then center clear:
distance(pos,probe)/5 +6 +distance(probe,center)/5 +5.
Use optical when its full-cover cost<=1.0/1.5 times that RF surrogate. Both costs
are proxies for planning; every actual operation is charged. The full optical
cover is uncapped when eventually required. Cached cover depends on positive
history; dynamic route costs depend on current position.

M50/M75: posterior-mass clear point instead of bearing-line least-squares.
For rho<=160, score region center, positive LS intersection when available and
48 legal polygon samples by total RF spatial weight within20 m, then distance
as tie-break. If best mass >=.50/.75, propose that speculative clear. Otherwise
choose RF refinement or full optical fallback; replace inherited speculative
center trials, do not append more. Max2 mass attempts per source and one per
NEW positive-observation count; negatives never reset retries. A failed point
is not retried within1 m. The candidate is in the positive polygon. RF mass is
not a calibrated success probability and never becomes a clear certificate.
Log mass attempts separately from Q3 O, including mass, positive version and
trial. Certified clear retains all-vertex20 m proof and has priority.

Initial registry: baseline, previous_best, S_all, L30, L90, P1, P2,
F60, F120, C1, C15, M50, M75 (13 arms). Fourteen or more are not required;
after development add at most3 combinations using these declared mechanisms.
Every initial arm, including losing/inactive ones, stays in primary.

## Evidence and invariants

Development: seeds40000–40029 mixed endpoint30 plus40000–40009 boundary10.
Primary: seeds50000–50199 mixed endpoint200, plus50000–50049 for directional,
omni, boundary/outward/minradius and mixed smooth (400 settings,200 blocks).
All algorithms are rerun on all identical scenarios. Rank only complete arms
but publish all failures. Report T, mean(T/K), sum(T)/sum(K), walking, probes,
discovery/refinement, S budgets, burst actions/distances, mass trials/successes,
optical proposals/executions, switching, failed clears, tails and all strata.
Use seed-block bootstrap with setting-weighted estimand; report multiple-
comparison and selected-winner limits and boundary degradation prominently.

Preserve positive polygon and complete optical fallback. Never infer d>1000
from no_signal. All 25 station per-channel negatives or observed16 positive
channels are required for absence. Hidden N, truth positions, headings, type
and radius are unavailable to policy. Use process isolation for geometry.
Snapshot all dependencies before every batch; no in-run mutation or rename.
Final analysis/test/review sources get their own hashes after completion.

Readiness clarifications: L uses spatial marginal for distance, heard-weighted
mass for completion. P uses expected_gain directly (already reception weighted)
and re-ranks after each real probe. A stop budget resets only on an accepted
operation whose individual movement from the preceding physical position is
>1 m; smaller successive moves never each reset it. F reads target-channel
physical events created by that action, including near-clear outcomes. M uses
spatial mass without RF-heard masking; full-history belief, current-position
tie-break and failed points are recomputed, positive version only gates retries.
C obtains a real RF candidate even when the current task is aggressive clear;
optical tasks bypass the scalar executor. Reviewer: PASS_WITH_WARNINGS.

## Review and testing

Independent implementation-readiness review before policy code; independent
result review after primary. User request authorizes these experiments.
Test geometric admissibility, mass retry/version caps, actual same-stop probe
budget, bounded/nonrecursive continuation, optical completeness and no-signal
recovery through the actual adaptive executor with an observation-only API.
Audit all recorded physical actions and certificates; add local-mechanism
checks independent of aggregate means. No stronger baseline/official claim.

## Development-based combination lock

Initial13x40=520 runs: all complete; all167162 physical actions audited.
Frozen-V4 mean519.673049; C15=508.509945, L30=511.235235, P1=515.226280.
C15 improves walking and probes; L30 strongly improves the development boundary
mean, while P1 is slightly better than unrestricted S_all=517.357699 but still
uses more probes than frozen V4. F60 performs2.3 burst decisions per scene but
has identical physical cost statistics to baseline. M50/M75 and F120 do not
improve the combined development mean. Preserve all these arms in primary.

Add exactly3 combinations: LC=L30+C15; PC=P1+C15; LPC=L30+P1+C15.
No route or coverage geometry change in any new arm. Final registry16 arms;
primary16x400=6400 runs on the predeclared fresh50000+ seeds. All16 retained
regardless of extra development outcome; no tuning on primary. Additional
development is baseline+LC+PC+LPC on the same40 settings to check execution.
