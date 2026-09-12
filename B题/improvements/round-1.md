# Improvement Round 1 — Q4 large ablation

## Round metadata
- Round number: 1
- Opened at: 2026-09-12
- Target question: Q4
- Cross-question impact expected: none
- Target metric: mean T/K, with movement and probe count as secondary metrics
- Exploratory ranking: complete certification first, then mean T/K; adoption would additionally require acceptable tail and subgroup behavior
- Target claim level ceiling: feasible_baseline

## Baseline reference
- Snapshot file: claims/baseline-snapshot.md
- Frozen metrics referenced: Q4 holdout mean T/K 517.5842931731096 s, mean movement 24742.356248252563 m, mean probes 279.73, 100/100 success

## Critique findings
- Source review: reviews/improvement-round-1-critique.md
- F1 nearest-task route; F2 coverage-station reuse; F3 detected-channel probe gate; F4 early center clear; F5 certified cover branch.

## Skepticism findings
- Source review: unavailable; provider returned 403 insufficient balance.
- This absence blocks formal adoption and claim update; results remain exploratory.

## Synthesized proposal
- Selected change: retain frozen V4 and evaluate reversible F1–F4 policy arms; keep F5 as certificate-gated geometry branch.
- Hypothesis: source-center route + coverage reuse + early160 + 1900 m outer witnesses reduces walking and probes while preserving certification.
- Required new data or solver: no for F1–F4; yes for any reduced-point F5 branch.
- Touches confirmed method or model structure: yes; no production replacement made.

## Risk assessment
- Worst-case observed development risk: every-stop unknown scan and source-continuation policies greatly increase total time; nearest-only also regresses.
- Per-question baseline comparison: Q4 only 517.5842931731096 s frozen holdout; Q1–Q3 unaffected and no cross-question impact expected.
- Primary matrix had 0/8000 failed scenes; aggregate gains can hide per-scene losses, so paired deltas and p95 are retained.

## Required readiness or rollback
- Readiness gate: branches/q4-lean-cover-readiness.md required before any point-set change (not opened because no point deletion was attempted).
- Rollback document: required before adopting any route/policy change; not needed for the isolated experiment itself.

## Claim level delta
- Before: feasible_baseline
- After (intended): feasible_baseline
- Gate justifying upgrade: none

## User decision link
- decisions/decision-improvement-round-1.md
- Status: adoption not requested; user authorization to continue experiments does not promote a candidate.

## Implementation summary
- Isolated code: experiments/q4_ablation/q4_ablation_policies.py and run_ablation.py.
- Safety tests: 10 passed; full project plus ablation tests: 252 passed.
- Primary data: experiments/q4_ablation/primary400/ (8000 runs, 20 arms, 0 failures).

## Before vs after metrics

See experiments/q4_ablation/primary400/summary.csv and report.md. Best eligible arm:
source-center route + coverage reuse + early160 + 1900 m outer witnesses, mean T/K
529.289930 s versus this matrix's paired baseline 543.540202 s; movement 4816.824399 s
and 292.49 probes versus 4972.874350 s and 297.985 probes. This is a new-scenario
paired result and cannot replace the frozen 517.584293 s holdout metric.
The best candidate is slower by 3.90% on boundary stress and loses 125/400 paired
cases (worst +113.37 s/source). This prevents claiming uniform improvement.

## Frontier update
- Experiments complete; adoption not requested, formal independent reviews unavailable.
- Results and review status recorded at experiments/q4_ablation/primary400/.
