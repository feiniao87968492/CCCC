# Model card: Bounded-bearing localization with certified coverage and optical fallback

Status: implementation_ready

## Task signature

Q1 geometric instance; Q2 one source and a legal observation prefix; Q3/Q4 whole case with unknown N. Domain: source disk radius1800m, robot legal coordinate box. Target: diameter/second-point policy and all-source clearance with minimum time. Consumers: online policy, case evaluator and competition paper.

## Evidence boundary

Official constants and API predicates are observed specifications. Existing two sessions are smoke evidence only. Coverage and optical-grid bounds are derived in MODELING_REPORT.md. Error probabilities and offline case generator are assumptions. True source state is unavailable online; incomplete completion time is right-censored. Model card readiness is a design state, not an executed validation verdict.

## Model role

GEO and SAFE are baseline designs with exact geometry and completeness responsibilities. ACTIVE is an audit-only extension to improve efficiency via robust/Pareto selection; its promotion requires case-paired validation. ORDER is optional and cannot alter coverage obligations. No neural or statistical surrogate is used.

## Variables and units

p,g in metres; a,eps,psi internal radians; r in metres; T and wall budget in seconds; c,k integer channels. Z is consistent hidden-state set, F its position projection, P a certified outer approximation, R pure wedge intersection. rho is minimum enclosing radius, distinct from diameter/2. Definitions and state ownership: SHARED_MODEL_BACKBONE.md.

## Mathematical specification

W_j is the intersection of cross(u(a-eps),x-s)>=0 and cross(u(a+eps),x-s)<=0. Classify A x<=b with LP; finite diameter is farthest vertex-pair distance. Q2 uses joint state Z1=(g,r) after the first direction, location set F1, MEC B(c1,rho1) with theoretical bound rho0=1500/(2 cos 1°)≈750.114m (a geometric scale, not a reception radius), core disk C_core=B(c1,1000-rho1) inside F_full_1000 inside C_guaranteed, and J(q)=sup over feasible near/direction(b)/no_signal of rho(F_y(q)); candidates are local A/B/C layers around c1, not a 20–3000m polar grid about s. Q3 uses the origin plus six equiangular sites on the1200m circle (seven sites); Q4 uses81 external lattice sites. A direction response implies the source lies in a1500m by60m bearing-aligned rectangle, covered by225 optical centres. Formal equations, constructive triangle counterexample and finite-time bounds: MODELING_REPORT.md sections2-6.

## Data requirements and identifiability

No training samples needed for baseline proofs. A single bearing does not identify range; absent feedback cannot identify existence at one point. Multiple near-parallel bearings may remain ill-conditioned. Online only uses accepted own commands; no hidden N or source truth. Same-site readings are dependent. Independent performance unit is a case, not a request.

## Estimation or solution

Planned scipy.optimize.linprog with free coordinate bounds for classification; pairwise boundary intersections plus convex hull for baseline geometry. Outer disk approximations use tangent half-planes and retain over-approximation. Q2 finite candidates and local refinement have no global-optimality claim; sampler scores are not certificates. ACTIVE adds at most6 measurements,2 extra clear actions and600 virtual seconds per source including return reserve, then falls back. SAFE uses sequential official API client, <=5238 core calls in Q4 including return actions. Wall-clock throughput remains to be tested; no network action in this stage.

## Comparison contract

Same case seeds, fixed spatial error field, legal information, metrics and runtime limits. Development20 cases per question, held-out100 per question after freeze. Compare full-clear outcomes first, then totalT and per-source time; do not omit failures. Case bootstrap2000 replications, separate deterministic adversarial geometries. Details in VALIDATION_PLAN.md.

## Validation and reality checks

Analytic empty/point/segment/unbounded/triangle geometry; independent solver comparison; field bounds and true-source inclusion; all orientations at source boundary; optical cell corners; action clocks and channel invariants. Units and original constraints checked before model promotion. Theoretical virtual bound does not establish wall-clock feasibility. Q2 sampling convergence and observed objective uncertainty constrain comparison claims.

## Failure triggers and fallback

Numerical ambiguity: higher precision or safe optical grid, never silent empty set. ACTIVE no_signal/stagnation/budget: return to discovery point and SAFE.225 failures: report model/protocol contradiction, not absent. API rejection/timeout: retain trace and explicit incomplete status. Wall-clock exhaustion: right-censored result; no all-clear certificate. Any certificate false positive blocks publication and formal testing.

## Outputs and downstream interface

Planned modules: geometry.py, localization.py, coverage.py, policy.py, offline_simulator.py, run_practice_strategy.py. Planned evidence: geometry_tests.json, coverage_audit.json, case_results.csv, action JSONL, channel_certificates.json, timing_audit.json. Each future figure exports PNG+CSV+meta.json. Existing robot_client.py is reused through a mode-checked budget adapter, not modified in this stage. Final official jlog is not replaceable by JSONL. Implementation checklist is the module and artifact list here plus VALIDATION_PLAN.md; all remain future outputs.

## Claim boundary

The design gives constructive completeness in the mathematical model provided accepted actions can finish. It does not yet establish actual official-simulator clearance, runtime, global optimality, or efficiency improvement. Formal results remain pending. Source literature motivates choices only; external citation verification remains incomplete.
