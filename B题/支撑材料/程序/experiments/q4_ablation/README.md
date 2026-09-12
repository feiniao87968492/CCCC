# Q4 large ablation

Completed: 20 configurations x 400 matched scenario settings, 8000 certified
successes. Each configuration clears 5133 sources across its 400 settings.
Frozen TRI25/V4 remains unchanged. Results are offline exploratory evidence.

- [Results and limitations](primary400/report.md)
- [Selected comparison table](primary400/ablation_table.png)
- [All 20 arms](primary400/ablation_table_all.png)
- [Numeric summary](primary400/summary.csv)
- [Every event audited](primary400/audit.json)
- [40-run exact event replay](primary400/harness_replay.json)
- [Design locked before primary results](design.md)

Best mean candidate: source-center route + station reuse + early160 + compact
outer witnesses. Mean T/K 543.540202 -> 529.289930 s (-2.62%), walking -3.14%,
measurements -1.84%. Boundary/outward stress T/K increases 3.90%, so this does
not establish uniform improvement and no baseline replacement was made.

## Reproduce from B题

```powershell
python experiments/q4_ablation/run_ablation.py --suite primary --output experiments/q4_ablation/reproduce400 --workers 8
python experiments/q4_ablation/audit_evidence.py experiments/q4_ablation/reproduce400
python experiments/q4_ablation/summarize.py experiments/q4_ablation/reproduce400
```

Output directories must be new. The primary400 experiment retains its original
start-time manifest. A module was renamed during execution to avoid a Q3 import
collision; its bytes did not change. The final manifest check therefore exited
with a missing-path error after emitting all 8000 results. Original source bytes
are archived in code_at_start/ and match start-time SHA256. audit.json and
completion.json record the complete event replay and path changes transparently.
The repaired harness reproduced every event hash in 40 runs across all 20 arms.

Validation: 252 tests passed, including Q3 and Q4 tests. Automatic audit replayed
2,680,254 actions, checked scenario truth, full absence certificates and cost
accounting; maximum time discrepancy 1.82e-12 s. These automated checks are not an
independent expert review. Reviewer subprocesses failed with provider 403
insufficient balance; formal adoption review remains incomplete.
