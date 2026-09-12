## Status
ADOPTION NOT REQUESTED — exploratory results are complete; no candidate is adopted.
This is an optional future adoption record, not a pending blocker for the user's
already-authorized experiment request.

## Why this blocks progress
The route, probe policy and cover geometry are confirmed Q4 method components. The
v4.1 improvement protocol requires Critique and Skepticism reviews plus explicit
decision before replacing them. Critique exists; Skepticism failed with provider
403 insufficient balance. Offline experiments therefore cannot raise claims or
change the frozen baseline.

## Decision needed
Choose whether to adopt a candidate after independent Skepticism review and a
new Stage 6 validation, or retain the frozen TRI25/V4 baseline.

## Options
- A: Retain frozen TRI25/V4; keep all ablations exploratory.
- B: After independent review, validate the best complete arm
  (`proxy_reuse_early_compact`) through rollback and Stage 6 before adoption.
- C: Validate only one-factor arms (compact, reuse, early160) to isolate causality.

## Recommended option
A now, followed by C if an independent reviewer becomes available. The primary
matrix has no failures, but several aggressive arms regress and the best result
is tied to a new scenario distribution.

## Impact scope
Q4 route, refinement scheduling, opportunistic probes and optional outer witness
radius. Q1–Q3 are unchanged. Claim ceiling remains `feasible_baseline`.

## What will happen after confirmation
If B or C is selected, create a rollback record, rerun Stage 6 on the frozen
1000–1099 endpoint/mixed holdout plus stress strata, and update claims only after
the evidence gate. If A is selected, archive the ablation as exploratory.

## Confirmation record
- Experimental authorization: user requested large Q4 ablation and then said “继续”.
- Adoption authorization: none requested or inferred; frozen baseline retained.
- Decision summary: deliver exploratory results now; only reopen adoption if the user requests it.
