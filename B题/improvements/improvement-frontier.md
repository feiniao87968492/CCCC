# Q4 improvement frontier

Target question: Q4. Frozen reference: claims/baseline-q4.md.
User requested at least three aggressive or tuned strategies and large paired
ablation experiments on 2026-09-12. Baseline remains frozen.

## Tried, experimental only

- F1 nearest-task insertion: tested; nearest-only mean T/K +4.51% on primary matrix.
- F2 coverage-station refinement reuse: tested; mean T/K -0.81%.
- F3 opportunistic-probe gates: tested; off +3.64%, strict +1.27%, loose approximately unchanged.
- F4 early center clear: tested at 120/160/220 m; mean gains below 0.6% individually.
- F5 leaner certified geometry: 25-site outer-radius micro-adjustment tested (-1.34% T/K); reduced-point branch excluded because one-point deletion certificates failed.
- Source-center route + F2 + F4 + outer-radius micro-adjustment: best matrix mean (-2.62%), but boundary stress mean +3.90%.

## Adoption status

No candidate adopted. Frozen TRI25/V4 unchanged. This is a completed user-authorized
exploratory experiment, not a closed formal improvement round. Critique artifact
exists; its final delivery and Skepticism failed with provider 403 insufficient
balance. Independent adoption reviews remain unavailable.

Evidence: experiments/q4_ablation/primary400/report.md, summary.csv, audit.json.
Stage 7 descriptive stress sensitivity: data/sensitivity/sensitivity-report.md.
