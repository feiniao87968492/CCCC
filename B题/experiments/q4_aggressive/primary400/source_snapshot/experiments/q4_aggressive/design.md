# Q4 aggressive local ablation, round 4

Target question: Q4. User authorizes additional aggressive offline experiments,
including adaptive C and two-step local L, prioritizing general-case efficiency
while retaining complete clearing. This is an isolated exploratory branch;
TRI25/V4 baseline and earlier experiment source/results remain immutable.
The user explicitly permits worse extreme-case efficiency. Completion is not
relaxed: every scene, including stress scenes, must clear and certify to rank.

## Objective and paired design

Primary ranking: mean(T/K) on the 350 general settings, conditional on all400
settings completing. Publish the all400 mean and the separate50 boundary
stress settings, with paired tails, failures, source counts and cost breakdown.
General means refer to this designed mixture, not a claimed real-world prior.
No subgroup non-regression requirement. Failed attempts and slow runs are kept.

Development: seeds60000-60019 mixed endpoint20, seeds60000-60009 mixed smooth10
and boundary/outward/minradius10 (40 settings,20 independent seed blocks).
Primary: fresh seeds70000-70199 mixed endpoint200; seeds70000-70049 each mixed
smooth50, omni endpoint50, directional endpoint50 and boundary endpoint50.
This yields400 settings and200 independent seed blocks; all same-seed settings
stay together in paired bootstrap. Seed sets differ from all earlier rounds.

Four controls: frozen baseline; prior local LC; prior local LPC; prior
JSO_compact_dopt (effective center/S/O/D-optimal/radius1900 configuration).
All12 initial candidates below share LC's L30+C15 unless expressly replacing
one component, and keep radius1950 and global route='tour'. Single-family
deltas use LC; frozen baseline is the primary historical anchor. LPC and prior
JSO remain simultaneous matched comparators.

## Six families, two parameters each

### E: expected-cost ordered complete optical clearing (E1, E2)

Replace C's full-route worst-case cost gate with a posterior-weighted expected
cost surrogate. Retain every point of the existing certified optical cover.
Order cells greedily by uncovered spatial mass / (3 + distance/5), adding a
small 0.05/n_cells floor to each candidate's mass benefit for unsampled areas.
Weights are RF spatial marginals; failed clear discs remove covered samples
for ordering only, never the positive polygon or certified cover. If all soft
weights vanish, use uniform weights. Estimate expected clear cost as sum of
each travel/clear increment times remaining sample mass, plus2 success.
Unsampled/no-hit mass is charged the full route. Actual clearing stops only
on success; otherwise visit every remaining original certified cell.

For early dispatch require rho<=160 and <=48 complete cells. Compare expected
optical cost with an actual legal RF candidate then center-clear travel/5+11.
E1/E2 use ratio1/2. The chosen cover and costs are recomputed from current
position, history and failed attempts. Order all eventual optical fallbacks
this way when <=256 cells; larger complete covers retain frozen NN execution.
No cap on complete fallback size or number of its attempts.

### B: short-approach candidates with a two-step local cost proxy (B20, B60)

Replace L's scalar non-completion penalty with a two-step cost proxy. Extend
the existing legal/fresh RF candidate list by points at20/60 m offsets around
the spatial weighted center and valid positive-bearing LS intersection.
For candidate q and each spatial hypothesis g, compute r1 using the existing
bounded-bearing parallax proxy. If r1<=20, continuation is q->g plus clear;
otherwise compare two virtual perpendicular second viewpoints at distance
clip(r1,20,120) from g, choosing the shorter q->viewpoint->g path, plus a
second measurement and clear. Score first travel/5+6, heard-weighted mean
continuation, and non-reception penalty78 s. These virtual future viewpoints
are scenario-dependent cost proxies, not executable rollout policies or proof
of post-observation accuracy. The selected current q is always legal/fresh.
Preserve the proven one-positive negative-RF bracket as an override. Actual
next decisions use only actual new observations and preserve the cap8 fallback.

### G: dynamic value-of-information stop probes (G075, G15)

Add selective probing to LC. Retain S geometry admissibility, with reception
gate0.5. At each actual stop rank admitted detected channels by
rho*(1-exp(-expected_gain))/(5*(5+actual_switch)); this is a saved-local-travel
proxy per measurement cost, not a calibrated value of information. Only execute
when ratio>=0.75/1.5, re-evaluating after each actual probe. Max3 supplemental
probes per stop shared across callbacks; reset only after an accepted individual
move>1 m. Mandatory unknown-channel scans remain exempt. New event names keep
these dynamic budgets distinct from earlier P's fixed-budget audit contract.

### R: early exit from dedicated RF refinement (R2, R4)

After2/4 dedicated measurements, at least2 positive bearings and rho<=200,
propose complete optical clearing before further RF/aggressive center attempts.
Certified clear has priority. Larger/one-bearing regions retain the original
cap8 RF and full optical fallback. No reduction of the underlying cap or
artificially incremented measurement counters. Actual early exits logged.

### H: wider two-bearing optimistic commitment (H200, H400)

Replace inherited center speculation by the existing Q3-derived least-squares
O rule at rho<=200/400. Require cond(A)<=30 and a legal estimate within the
positive polygon; max2 attempts/source and1/new positive version. Negative RF
never renews retry permission. Retain LC's C15 gate and complete fallback.
This deliberately tests wider conditions than prior O; success is observational
and no stronger location certificate is asserted.

### N: no-extra-walking opportunistic clear (N20, N50)

At an actually visited stop, before detected-channel supplemental probes,
try clearing a detected source if at least2 positive bearings, rho<=320 and
spatial mass within20 m of the current legal position>=0.20/0.50. Max2 trials
per source and1/new positive version; guard nested callbacks. No movement is
introduced and no repeat of a failed point within1 m. This adds bounded trials
to LC's existing clear behavior. The mass is not calibrated success probability.
Unknown-channel cover scans still run normally, and full fallback is preserved.

## Development selection lock

Initial16 arms =4 controls +12 single-family candidates. All enter primary,
including losing/inactive arms. After development, rank the best parameter
per family by general-case paired mean, require complete40 settings, and take
up to3 improving families versus LC. Add up to3 combinations: top two,
top plus third, and all three (if only2 improve, add their pair only).
No new mechanism or tuning after primary starts. Record exact selected config
and source hashes before an additional matched combination development batch.
Primary includes every initial arm plus these locked combinations.

Locked development result: E1, R2 and N20 are the three improving family
representatives against LC on the general development settings. The primary
combination registry is therefore ER, EN and ERN, with exact parameters E ratio
1, R count2 and N mass0.20. These are locked before primary; no primary tuning
selects among them.
Exact ties use variant name lexicographic order. A family improves only if its
general development mean delta versus LC is < -1e-7 s/source and every dev
setting completes. Zero or one improving family yields no new combination.

Machine-checkable eligibility is `eligible_all400 = (failure is empty) AND
full_success == True AND K == N AND all_certified == True` for every one of the
400 settings in an arm. Certified-absent channels count toward all_certified and
are excluded from source K exactly as in the simulator; source-clear rows still
require `K == N` for a setting to be eligible. Only after every arm passes this
predicate is the general350 sum selected: 350 settings are mixed endpoint200,
mixed smooth50, omni endpoint50 and directional endpoint50; the boundary50
settings are stress-only. The primary mean is `sum(T_over_K)/350` with each
setting equal weight; block intervals use the same setting-level deltas and
retain the 200 seed blocks. A failing arm remains in raw tables and cannot rank.

## Safety of full clearing and evidence ceiling

No truth access: policy uses public observations, previous clear outcomes and
public problem bounds only. Hidden N, source positions/types/radii/headings
are absent from the policy API. Continuous positive geometry remains the
clearing authority. Negative RF does not mean distance>1000. No unknown channel
is omitted from mandatory coverage evidence; require25 station/channel
negatives or independently observed16-source counting certificate.

Changes affect only local scheduling/selection and bounded speculative work.
The executor retains cap8 dedicated RF, finite supplemental attempts, no
unbounded per-source loops, and a finite complete optical cover under the
bounded-error model. Retain numerical/resource/iteration limits in reporting;
all tested completion is finite offline evidence, not an official-score claim.

## Review, tests and artifacts

Independent critique then skepticism/readiness before policy implementation;
independent development validation before primary and final result review.
User has authorized this experimental scope; no baseline adoption is requested.
Write behavioral tests for full optical cover under misleading soft weights,
failed clear conditioning, physical G stop budgets, bounded N retries, legal B
candidates, R fallback and H version caps, plus observation-only full execution.
Full event audit covers every action/charge and stopping certificate. Add
family-specific mechanism logs/audits and independent scoring samples.
Snapshot all simulation dependencies before each batch; never mutate or rename
in-run code. Final report sources/reviews get separate hashes. Preserve failed
and extreme results; publish screenshot-style full comparison PNG/PDF + CSV.

## Explicit integration contracts

E overrides the entire optical executor inside the isolated subclass: passing
an ordered list to the inherited nearest-neighbor executor is insufficient.
It logs optical_cover with the original cell count, then iterates the complete
ordered permutation until actual success; skipped exact already-failed cells
cannot cover the true source under the model. No other source callbacks occur
inside optical execution. E's early gate replaces C15 (does not cascade it).
For weights w_i summing1 and first-hit cell index j_i, expected cost is
sum_j c_j*sum_i[w_i*(j_i>=j)] +2, using j_i=n_cells for never-hit samples;
c_j=distance(previous,cell_j)/5+3. The success surcharge2 is a planning surrogate
for eventual success, and never-hit mass pays every increment. The all-zero
failed-disc-conditioned sample case resets to uniform weights over all original
samples; this is explicitly heuristic. Hard cover is never pruned by mass.

B's conditional hit continuation for g is distance(q,g)/5+5 if r1<=20;
otherwise min over its two virtual viewpoints of
[distance(q,v)+distance(v,g)]/5+11. Virtual illegal viewpoints are excluded;
if neither is legal, use distance(q,g)/5+11+78 as a fallback cost proxy.
Score=distance(current,q)/5+6+sum_i heard_weight_i*continuation_i
+78*(1-sum_i heard_weight_i). Virtual observations are never generated.
Candidates around weighted center/LS use four axial offsets of the declared
radius, plus weighted center/LS themselves when legal and fresh.

G/N endpoint hooks run ONLY at completed cover-scan boundaries and after the
selected source's scalar action (including any immediate near clear). They do
not run in measure(), clear(), _move_to(), scan_at() internals, region/task
proposal generation or optical tours. Override _do_v3_action using the frozen
Q4 scalar executor once, then run endpoint handling; replicate H's version
registration explicitly before that scalar action. This avoids inherited
selective callbacks followed by another endpoint callback. Endpoint handler
uses a recursion guard, runs N then G (or frozen cover-stop probes for N-only
cover callbacks), and rechecks detected status immediately before each action.
No remaining caller action targets a just-cleared source; completed targets
are not passed to the scalar executor again. N-only source callbacks add only
N, leaving LC's lack of source-stop supplemental RF unchanged. G replaces
frozen stop probes where enabled. All endpoint work remains finite.

Task precedence for combinations: certified clear; base H speculation or legal
B/L RF candidate; E's replacement optical gate (or unchanged C15); then R early
optical dispatch if eligible. G/N affect only physical endpoints. Each selected
combination is an overlay of distinct family config fields on LC; candidates
are always re-evaluated after actual observations and proposed events never
consume retry/budget tokens. Early optical proposal events are distinguished
from selected executions by the subsequent ablation_action and optical_cover.

Critique binding: reviews/critique.md F1-F8 remain unchanged identifiers. B1/F6
is addressed by endpoint-only N callbacks AFTER all enclosing scalar actions,
with no callbacks inside a near-clear chain or optical tour. The readiness
review must evaluate this clarification; no implementation has started yet.
For B, perpendicular axis is the90-degree rotation of (g-q)/norm(g-q), with
(1,0) for coincident points; ties preserve candidate insertion order. Log B's
selected score terms and recovery override at actual execution. G opportunities
and threshold skips are logged, and its admission check uses S geometry without
the inherited optimistic-available suppression: H availability is handled by
task precedence, not by blocking useful G opportunities at unrelated stops.
