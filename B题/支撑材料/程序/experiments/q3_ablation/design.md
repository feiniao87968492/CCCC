# Q3 large paired ablation, 2026-09-12

## Scope and authorization

The user requested at least three aggressive algorithms reducing travel time and
measurement count, implemented and compared in a large ablation like the supplied
table. This authorizes this isolated offline experiment. It does not promote a
candidate to the official Q3 mainline. GREEDY_FAST with source_budget_s=0 remains
the mainline. Q4 files and its frozen baseline are outside this experiment.

This is exploratory Q3 experimental work, not a formal v4 improvement round:
there is no frozen Q3 per-question baseline or Stage 7 sensitivity report yet.
The screenshot's original nine scenes / raw observations were not found; its
numbers are context only and must not be presented as reproduced results.

## Model and accounting

- Sources lie in the radius-1800 disk; N is unknown online, 10 through 16.
- Each source uses a distinct one of 20 channels; reception radius 1000 to 1500.
- Omni reception, near <=5 m, clearing <=20 m, travel speed 5 m/s.
- T = distance/5 + 5*measurements + switches + 3*clear_attempts + 2*successes.
- Only measurement changes the receiver channel. Every failed clear is charged.
- Noise is a deterministic function of scene, source, and requested position,
  independent of policy action order. Test smooth, independent spatial noise,
  and endpoint-sign noise. Round bearings to two decimals while ensuring the
  returned direction remains within the stated one-degree error bound.
- Policy receives only API responses. Truth is held in the offline environment
  and used for post-run scoring. No official simulator or formal quota is used.
- Full completion must be certified by full discovery coverage or 16 detected
  sources, with every detected source cleared. N is never given to the policy.

## Algorithms

J: Joint action route. At every action compare remaining discovery stations,
useful second-view sites, and clear visits in travel-time units; include
continuation toward the remaining tour. Replan after each observation/clear.

S: Selective shared sensing. Reuse stops for several pending channels, but skip
measurements whose bounded posterior lies outside reception, whose parallax is
poor, or whose posterior is already small enough for a bounded clear attempt.
Unseen channels are scanned at mandatory coverage stations by default.

O: Optimistic two-bearing clearing. Once two directions give a finite, well
conditioned estimate and a moderately small outer posterior, allow a direct
clear without demanding a <=20 m certificate; after failure refine locally,
then retain the existing complete SAFE fallback. Never abandon a source.

Implementation parameters: O accepts a speculative least-squares clear only
with at least two bearings, normal-matrix condition number <=30 and posterior
MEC radius <=80 m. At most one speculative clear per observation state; failure
forces a fresh view, with at most four refinement rounds before SAFE. S skips
known-channel station scans when the posterior radius is <=40 m, center range
exceeds 1100 m, maximum possible reception fails, or parallax is <12 degrees
and the new stop does not halve range. These are heuristics, not absence
certificates. J uses the existing nearest-neighbor + 2-opt open-route helper
over coverage stations and posterior source centers, then replans after each
action. Source centers are observation-derived proxies, not known locations.

All factorial candidates use center + six radius-1130 stations. The maximum
distance to the nearest station is the greater of 1130/sqrt(3) and
sqrt(1800^2+1130^2-2*1800*1130*cos(pi/6)), both below 1000 m.
This is an analytic Voronoi-vertex/boundary coverage check, not a grid-only
check. The original radius-1200 runner is retained verbatim as a separate arm.

## Planned ablations

- Original GREEDY_FAST (1200 m).
- Eight combinations of J/S/O using a certified smaller ring radius, including
  all-off compact control, three individual algorithms, pairs, and all-on.
- All-on with unseen-channel scanning at every stop (negative control).

Keep complete fallback and action accounting identical across candidates.
Cache deterministic geometry only with exact input keys; no truth in caches.

## Experiment protocol

Pilot: N=10..16, three error modes, separate development seeds (21 scenes).
Lock policy parameters before evaluation. Evaluation: N=10..16 x four spatial
families x three error modes x five seeds = 420 paired scenes per arm.
Families: uniform disk, boundary/minimum-radius, clustered, radial spokes.
All arms use the same scene IDs and saved truth hashes. Never drop failures.

Report clearance K/N, certified full-scene rate, mean T, mean per-scene T/K,
pooled sum(T)/sum(K), walking time/distance, measurements, switch counts,
failed clears, p95 T/K, fallback use, paired deltas and bootstrap intervals.
Incomplete scenes must be flagged and cannot win on T/K. Provide subgroup
results, individual rows, action traces, manifests and a reproducible command.

## Verification and evidence

Before implementation: independent readiness review of this design and current
runner/API model. Test protocol accounting, coverage geometry, hidden-count
independence, deterministic paired noise, failure recovery and termination.
After results: independent validation review; evidence ceiling remains offline
exploratory analysis. No claim of official scores or universal improvement.

## Checklist

- [x] Inspect current Q3 code, parameters, memory and prior experiments.
- [x] State experiment design and user authorization.
- [ ] Readiness review and resolve findings.
- [ ] Implement isolated policy variants and paired environment.
- [ ] Pilot and freeze parameters.
- [ ] Run large paired experiment and replay accounting.
- [ ] Independent validation and result tables.

Memory check: screenshot aggregates alone cannot identify the original seeds.
