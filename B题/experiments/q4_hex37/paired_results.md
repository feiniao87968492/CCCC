# SQUARE81 vs HEX37 paired offline comparison

Date: 2026-09-11. Same runner `cumulative-optical-v2`, same seeds 0–29, same bounded deterministic bearing error. Only the discovery cover changes.

Command:

```powershell
python experiments/q4_revision/compare.py --cover-mode SQUARE81 --output experiments/q4_hex37/square81.csv --cases 30
python experiments/q4_revision/compare.py --cover-mode HEX37 --output experiments/q4_hex37/hex37.csv --cases 30
```

These are local geometry-model results, not official practice.

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
