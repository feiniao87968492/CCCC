# Q3 ablation implementation readiness

## Gate result

PASS_WITH_WARNINGS for the isolated offline exploratory experiment.

## Intended claim level

`exploratory_analysis`

## Supported claim level

`exploratory_analysis` after the pilot and focused tests. This gate does not
authorize official simulator testing or mainline promotion.

## Checks

- Compact radius-1130 coverage and station identity tests pass.
- 17 focused protocol/recovery tests pass; full repository suite is 242 passed.
- Pilot: 210/210 complete runs.
- Evaluation: 4,200/4,200 complete runs; 420 scenes per arm.
- Action traces, scene hash, source-code hashes and interpreter versions are
  recorded in `evaluation/manifest.json`.
- Original arm calls the existing `GreedyFastRunner`; no private environment
  state is exposed through its client.

## Allowed outputs

Synthetic offline result tables, paired deltas, action traces, manifests,
failure/recovery statistics and qualified exploratory comparisons.

## Blocked claims

Official simulator performance, reproduction of the supplied screenshot,
global/validated optimality, universal superiority and formal Q3 mainline
promotion remain blocked.

## Required branches

Keep `GREEDY_FAST` source-budget-zero as the official mainline. Any change to
official runtime, confirmed model or evidence path requires a separate decision
and rollback assessment.

## Required decision

No additional user decision is needed for this explicitly requested offline
experiment. A new decision is required before official simulator runs or
promoting JSO to the mainline.
