# Q4 large paired ablation, 2026-09-12

## Authorization and status

The user requests at least three aggressive or tuned algorithms and large
ablations, and subsequently explicitly says to continue. This authorizes
reversible isolated experiments. The frozen TRI25/V4 files and default entry
are not edited. Experimental policies live only in this directory.

The frozen 100-case endpoint/mixed replay exactly reproduced mean T/K
517.5842931731096, mean T 6682.781249650514, movement 24742.356248252563 m,
and 279.73 measurements. All 13 frozen SHA256 entries match.

The Critique draft is available but its subprocess ended with provider 403
insufficient balance before final delivery. Skepticism also failed with this
provider error. The specialized readiness reviewer could not access filesystem
reads with its role restrictions. Therefore independent gates are incomplete.
User-authorized exploratory experiments continue, with independent review
pending; this is not a completed formal improvement round or baseline promotion.

## Algorithms and factor design

- F1 nearest-task scheduling: choose the nearest actual actionable cover,
  refinement, or clearing task; replan after each result. Additional route
  controls use source centers as tour proxies, or finish a selected source
  without interleaving other sources.
- F2 coverage-station refinement reuse: replace a dedicated refinement point
  with a still-needed certified coverage station only when its estimated
  reception and information gain pass explicit gates and added walking is
  bounded. Scan the unseen channels there and reuse that same stop for the
  target channel. No unknown channel is omitted from the station certificate.
- F3 opportunistic detected-channel sensing: off, strict (.85 probability,
  .5 gain), baseline (.7/.3), permissive (.55/.2). Discovery scans remain
  mandatory. The baseline's 35.95 refinement probes are only 12.85% of all
  probes, so suppression alone cannot promise a 20% direct total reduction.
- F4 early clearing: increase the posterior enclosing-radius trial threshold
  from 80 to 120, 160 or 220 m, retaining at most two failed trials per source,
  no duplicate target trials, and complete optical fallback. Every failed
  clearing operation and its travel are charged.
- F5 geometry: test radius-1900 outer witnesses (25 sites retained). A fresh
  continuous discovery certificate is required. All 25 one-point deletions
  failed the existing sufficient certificate, so reduced-point arms are excluded.

The full 2^3 factorial uses F1 nearest, F2 reuse and F4 radius 160. Controls
include the original baseline, route proxy, source completion, F3 gates,
F4 radii 120/220, compact geometry, full+compact and every-stop unknown scans.
The last is a cost tradeoff control analogous to the user's screenshot.

## Invariants

Only measure/clear API results enter the policy. Truth and actual N are held
by the environment and used only for scoring. Count-based absence requires
16 distinct observed channels. no_signal is never a d>1000 certificate.
Positive-observation polygons and optical fallback remain authoritative.
All times include movement/5, 5 s per measurement plus 1 s receiver switching,
3 s per clearing attempt plus 2 s per successful clear, matching frozen bench.
Coordinate-stable noise keeps common random numbers independent of action order.

## Evaluation and selection

Development: 30 mixed endpoint scenes, seeds 5000-5029, all variants. Used only
to diagnose implementation and behavior, not to claim final improvement.
Primary: 400 matched scenario settings per arm: 200 mixed endpoint seeds
10000-10199 and 50 each of directional endpoint, omni endpoint, outward boundary
endpoint, mixed smooth, all with seeds 10000-10049. There are 200 independent
latent seed blocks, with five paired perturbations on the first 50. Confidence
intervals must resample seed blocks, not pretend all 400 are independent.
No policy tuning after the primary run starts. All arms are reported.

Report mean T, mean(T/K), sum(T)/sum(K), movement time and distance, discovery
and refinement probes, switches, failed clears, optical fallbacks, p95 T/K,
per-seed deltas, certification, failure rows, stratum and N breakdowns. Failures
are never dropped. Arms with any incomplete scene are ineligible for a winner
recommendation. Rank eligible arms by mean(T/K); flag walking/probe and tail
tradeoffs separately. Inferential comparisons to frozen V4 are paired; new
cohort baseline means need not equal the old 517.58 s mean.

Store scenario manifests, input/code SHA256, CSV/JSON results, event traces,
paired tables and a reproducible figure resembling the user's table. Offline
results do not establish official simulator T/K or path optimality.

## Development completion, before primary evaluation

All 540 development runs (18 arms x 30) completed and certified. Nearest-only,
probe-off and every-stop arms were slower. Center proxy and compact outer
witnesses were individually modestly faster. Before opening primary results,
two additional combinations are locked: center proxy + compact; center proxy
+ reuse + early160 + compact. No primary results informed this addition.
The primary matrix is therefore 20 arms x 400 settings = 8000 runs.
