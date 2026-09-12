# Q4 aggressive local experimental scope

## Status
EXPERIMENT AUTHORIZED — preimplementation independent readiness pending.

## Why this blocks progress
No user authorization is missing. Independent critique identified B1/F6, an
N callback hazard that could clear an already-cleared source and corrupt state.
Implementation waits for independent review of the endpoint-only mitigation.

## Decision needed
Main-agent readiness determination after independent review. No baseline
adoption or claim upgrade is requested. No repeat user confirmation is required.

## Options
The user requested aggressive local experiments including adaptive C/two-step L.
The authorized experimental design tests all six families: critique F1 E, F2 B,
F3 G, F4 R, F5 H and F6 N, with F7 estimand and F8 evidence requirements.
Retain complete clearing and frozen baseline; allow stress-time regression.

## Recommended option
Execute the isolated design after addressing B1/F6 and obtaining readiness;
retain all candidate outcomes and the four matched controls.

## Impact scope
Q4 only, experiments/q4_aggressive/. Shared simulation sources, Q1-Q3 solvers,
frozen Q4 entrypoints and baseline claims remain unchanged.

## What will happen after confirmation
Existing user authorization covers the experiments. After readiness review,
write behavioral tests, implement isolated strategies, run development, lock
combinations, run fresh400-setting primary matrix, audit and review results.

## Confirmation record
User: “包括这个方向，再多投入几个方向，采取更激进的策略，在保证全清的基础上，可以少考虑极端情况，采取对于更一般的情况更高效的策略进行消融实验”.
Interpretation: general-case efficiency is primary; full clearing remains
mandatory, including stress; no baseline adoption inferred.

## Pre-load critique and skepticism risks
Critique reviews/critique.md B1/F6: nested N success followed by enclosing
duplicate clear can restore detected status. Mitigation: N only after completed
cover scans/source scalar actions, no callbacks inside action primitives or
optical tours, recheck detected status; acceptance includes adversarial checks.
Skepticism/readiness pending; no risk attributed to an unwritten review.
