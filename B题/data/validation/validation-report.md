# Validation Report — Q4 TRI25 + ROUTE_ADAPTIVE_V4 (517 s T/K)

Date: 2026-09-12  
Question: Q4 only  
Scheme: `TRI25` discovery cover + `ROUTE_ADAPTIVE_V4` joint routing (`adaptive-reception-v4`)  
Primary evidence: `experiments/q4_efficiency/release_holdout100.*`

## Scheme identity

| Field | Value |
|---|---|
| Cover | `TRI25` (19-site 920 m lattice + 6 boundary witnesses at 1950 m) |
| Route | `ROUTE_ADAPTIVE_V4` |
| Practice default | `simulator_automation/q4_practice.py` defaults to TRI25 + ROUTE_ADAPTIVE_V4 |
| Module env default | `Q4_COVER_MODE` still falls back to `SQUARE81`; `Q4_ROUTE_MODE` falls back to `OLD_HEX37` if unset |
| Localization / optical fallback | Unchanged cumulative-optical path; `no_signal` is not treated as `d>1000` |
| N=16 counting certificate | Retained independently of geometric cover |
| Error model (primary holdout) | `endpoint` (±1° endpoint, two-decimal quantization) |
| Source mix (primary holdout) | `mixed`, seeds 1000–1099 |
| Official simulator | Not obtained this round (`experiments/q4_efficiency/practice_attempt.json`) |

## Independent numeric replay (2026-09-12)

Recomputed from `release_holdout100.csv` against `release_holdout100.json`. Current working-tree SHA256 of all files listed in `release_holdout100.meta.json` matched with 0 mismatches.

| Metric | CSV replay | JSON | Source artifact |
|---|---:|---:|---|
| cases | 100 | 100 | experiments/q4_efficiency/release_holdout100.csv |
| full_success / all_certified | 100 | 100 | same |
| failed_seeds | 0 | [] | same |
| mean T/K (s) | 517.584293173110 | 517.5842931731096 | same |
| mean T (s) | 6682.781249650516 | 6682.781249650514 | same |
| mean K | 13.24 | 13.24 | same |
| mean move (m) | 24742.356248252570 | 24742.356248252563 | same |
| mean refine_no_signal | 3.58 | 3.58 | same |
| mean discovery_no_signal | 230.54 | 230.54 | same |
| mean n_clear | 18.25 | 18.25 | same |
| mean n_optical_fallback | 0.04 | 0.04 | same |
| p95 T/K (s) | 677.2650412845248 | 677.2650412845248 | same |
| min T/K (s) | 258.13623777185825 | — | CSV |
| max T/K (s) | 766.7178646948478 | — | CSV |
| optical fallback events (sum) | 4 | — | CSV |

Paired against frozen pre-change snapshot `HEX37 + ROUTE_INSERT_V3` on the same 100 seeds (`holdout100_paired.csv`, `paired_summary.json`):

| Paired fact | Value |
|---|---|
| Improved (lower T/K) | 97 / 100 |
| Worse | 3 / 100 |
| Worst Δ T/K | +48.260035145791505 s (seed 1092, N=16) |
| Other worse seeds | 1065 (+6.26 s), 1093 (+19.52 s) |
| Mean T/K drop | 735.3565026536246 → 517.5842931731096 (−29.6145%) |

The three worse holdout seeds all have N=16. This is an average-efficiency improvement, not a per-scene path-optimum guarantee.

## Supporting groups (not primary freeze metrics)

| Group | Artifact | n | full clear | mean T/K (s) | error | sources |
|---|---|---:|---:|---:|---|---|
| Dev 0–29 | release30.json | 30 | 30/30 | 489.792867 | smooth | mixed |
| Holdout 1000–1099 | release_holdout100.json | 100 | 100/100 | 517.584293 | endpoint | mixed |
| Directional 2000–2029 | release_directional30.json | 30 | 30/30 | 550.406956 | endpoint | directional |
| Omni 4000–4029 | release_omni30.json | 30 | 30/30 | 475.140908 | endpoint | omni |
| Boundary outward 3000–3029 | release_boundary30.json | 30 | 30/30 | 583.861023 | endpoint | boundary |
| Old HEX37/V3 holdout | baseline_holdout100.json | 100 | 100/100 | 735.356503 | endpoint | mixed |

Aggregate offline correctness cited in `docs/Q4效率瓶颈与V4优化-20260912.md`: 220/220 full clear + certificate (30+100+30+30+30). Dev 30 uses `smooth` error and is not the freeze metric.

## Certificate constants (from paired_summary.json)

| Constant | Value |
|---|---|
| TRI25 points | 25 |
| Outer polygon | 128-gon of Ω (radius 1800 m) |
| Hull margin | 17.74943008678929 m |
| Max continuous cover distance | 943.0121947375769 m < R_min=1000 m |
| Nonempty triangle intersections checked | 36 |
| Certificate valid | true |
| Fixed reference route length | 19032.38903596451 m |

These constants prove a sufficient continuous discovery cover. They do not claim 25 is the minimal point count.

## Tests

`python -m pytest tests -q` in `B题/` on 2026-09-12: **225 passed** in 33.47 s.

## Official practice

`experiments/q4_efficiency/practice_attempt.json`: login timed out waiting for team label; server disconnected; no robot actions sent; `official_results: null`. Offline T/K must not be written as official simulator T/K.

## Reproducibility

- Git HEAD at check time: `3c144685832cc1df2ef6c84e581094bdd054c417`
- This HEAD does **not** contain the frozen V4 tree: `src/q4_cover.py`, `src/q4_policy.py`, `simulator_automation/q4_runner.py` are modified; `src/q4_adaptive.py`, `src/q4_certificate.py`, and `experiments/q4_efficiency/release_holdout100.json` are untracked.
- Working-tree SHA256 (authoritative for this freeze) is in `experiments/q4_efficiency/release_holdout100.meta.json`.
- Replay command:

```powershell
python experiments/q4_efficiency/bench.py --cover TRI25 --route ROUTE_ADAPTIVE_V4 --error-mode endpoint --seed-start 1000 --cases 100 --output experiments/q4_efficiency/recheck_v4.csv
```

## Supported claim level (main-agent recommendation, not a gate)

- Intended: freeze this scheme as the Q4 improvement-loop baseline.
- Supported: `feasible_baseline`.
- Not supported: `locally_optimal_solution`, `validated_optimum`, `global_optimum`, or any official-simulator performance claim.

## Memory check
Updated `memory.md` (git SHA pitfall, default-identity pitfall, three worse N=16 seeds, user freeze preference).
