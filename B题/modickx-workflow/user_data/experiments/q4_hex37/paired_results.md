# SQUARE81 vs HEX37 paired offline comparison

Date: 2026-09-11. Same runner `cumulative-optical-v2`, same seeds 0–29, same bounded deterministic bearing error. Only the discovery cover changes.

Command:

```powershell
python experiments/q4_revision/compare.py --cover-mode SQUARE81 --output experiments/q4_hex37/square81.csv --cases 30
python experiments/q4_revision/compare.py --cover-mode HEX37 --output experiments/q4_hex37/hex37.csv --cases 30
```

These are local geometry-model results, not official practice.

## Route insert v1 (same seeds 0–29, HEX37 cover)

`INSERT_MAX_M = 400`. Hamilton order is fixed; pending sources are inserted only when the detour extra is at most 400 m.

```powershell
python experiments/q4_revision/compare.py --cover-mode HEX37 --route-mode OLD_HEX37 --output experiments/q4_hex37/old_hex37_route.csv --cases 30
python experiments/q4_revision/compare.py --cover-mode HEX37 --route-mode ROUTE_INSERT_V1 --output experiments/q4_hex37/route_insert_v1.csv --cases 30
```

| metric | OLD_HEX37 | ROUTE_INSERT_V1 | change |
|---|---:|---:|---:|
| full clear | 30/30 | 30/30 | same |
| all_certified | 30/30 | 30/30 | same |
| mean T/K (s) | 836.91 | 774.06 | −7.5% |
| mean T (s) | 11417 | 10533 | −7.7% |
| mean move_m | 46196 | 36121 | −21.8% |
| mean localization_move | — | 12839 | — |
| mean n_measure | 337 | 545 | +62% |
| mean n_clear | 58.5 | 15.1 | −74% |
| mean optical fallback | 1.17 | 0.00 | — |
| mean n_insert | 0 | 18.8 | — |
| mean n_defer | 0 | 36.0 | — |
| mean pending_max | 0 | 8.5 | — |

Mean travel is inside the 35–38 km band. Extra measures come from still scanning detected channels at later HEX points; that is left for the next phase.

## Route insert v2 (same seeds 0–29, HEX37 cover)

Pending sources on the current edge are batched (enumerate if ≤7, else NN+2-opt) and localized before returning to the Hamilton skeleton. Detected channels are probed at a HEX site only when the site adds a ≥200 m baseline inside the current region.

```powershell
python experiments/q4_revision/compare.py --cover-mode HEX37 --route-mode ROUTE_INSERT_V2 --output experiments/q4_hex37/route_insert_v2.csv --cases 30
```

| metric | V1 | V2 | change |
|---|---:|---:|---:|
| full clear | 30/30 | 30/30 | same |
| all_certified | 30/30 | 30/30 | same |
| mean T/K (s) | 774.06 | **735.31** | −5.0% |
| mean T (s) | 10533 | **9985** | −5.2% |
| mean move_m | 36121 | 38342 | +6.1% |
| mean n_measure | 545 | **375** | −31% |
| mean n_clear | 15.1 | 22.4 | +48% |
| mean n_probe | — | 24.8 | — |
| mean n_batch | — | 10.3 | — |

V2 trades a little travel for fewer RF measures; T/K is the contest metric after full clear.

## Route insert v3 (same seeds 0–29, HEX37 cover)

Frozen params after a 10-seed grid: `CLEAR_INSERT_MAX=600`, `MEASURE_INSERT_MAX=250`, `AGGRESSIVE_CLEAR_RHO=80`. Clear is allowed with a larger detour than measure. A 3-step HEX lookahead defers tasks that will be cheaper later.

| metric | V2 | V3 | change |
|---|---:|---:|---:|
| full clear | 30/30 | 30/30 | same |
| all_certified | 30/30 | 30/30 | same |
| mean T/K (s) | 735.31 | **711.20** | −3.3% |
| mean T (s) | 9985 | **9646** | −3.4% |
| mean move_m | 38342 | **36870** | −3.8% |
| mean n_measure | 375 | **367** | −2.1% |
| mean n_clear | 22.4 | 22.4 | ~0 |
| mean n_probe | 24.8 | 19.6 | −21% |
| mean aggressive_clear | — | 11.3 | — |
| aggressive_clear success | — | 5.87 / 11.3 = 52% | — |

V3 beats V2 on T/K and travel, with 30/30 certificates. The gain is under 5%, so further threshold search is not the next lever; a later HEX37 prefix-route stage is reserved and not implemented here.

## HEX37 PREFIX_A vs CURRENT (V3 frozen, seeds 0–29)

Equal-length 800 m Hamilton paths. PREFIX_A is the best offline-scored DFS path (mean first-detect index 5.54 vs 8.98 on synthetic sources).

| metric | CURRENT | PREFIX_A | change |
|---|---:|---:|---:|
| full clear | 30/30 | 30/30 | same |
| all_certified | 30/30 | 30/30 | same |
| mean T/K (s) | 711.20 | **683.09** | −4.0% |
| mean T (s) | 9646 | **9277** | −3.8% |
| mean move_m | 36870 | **36103** | −2.1% |
| mean first detect index | 6.85 | **4.20** | −38.7% |
| mean P95 first detect | 20.26 | **16.19** | −20.1% |
| mean n_measure | 367 | **332** | −9.6% |

PREFIX_A replaces CURRENT as the practice default visit order. CURRENT remains selectable. Dynamic origin-based route choice is not enabled.

| metric | SQUARE81 | HEX37 | change |
|---|---:|---:|---:|
| full clear | 30/30 | 30/30 | same |
| all_certified | 30/30 | 30/30 | same |
| mean T/K (s) | 1313.16 | 836.91 | −36.27% |
| mean T (s) | 17844.98 | 11417.36 | −36.02% |
| mean move_m | 68250.75 | 46196.45 | −32.31% |
| mean n_measure | 679.73 | 337.10 | −50.41% |
| mean n_clear | 60.57 | 58.50 | −3.41% |
| mean optical fallback | 1.07 | 1.17 | +9.4% |
| cover points visited | 81 | 37 | −54.32% |

HEX37 kept 30/30 full clear and certificates. Efficiency is therefore comparable. Optical fallback count is not a localization change; first-detect geometry differs with the coarser lattice.

Ideal HEX37 Hamilton path: 36 × 800 = 28800 m vs SQUARE81 snake 48000 m.
