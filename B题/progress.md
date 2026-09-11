# Progress

## 2026-09-11 HEX37 cover

- Independently checked HEX37 lattice, covering radius, half-plane slack, and ring-4 exclusion.
- Proof constants hold with a 9.4 m gap on the finite-set bound.
- Found an origin-starting 800 m Hamilton path of 37 vertices (28800 m).
- Cover layer `SQUARE81`/`HEX37` is in `q4_cover.py`; state/policy/runner no longer hardcode 81.
- `pytest tests` : 168 passed.
- Paired seeds 0–29: HEX37 30/30 full clear + certificate. Mean T/K 1313.16 → 836.91 (−36.3%).
- Official 问题4演练 HEX37: `215125` 12/12 T/K=899.04; `215159` 16/16 T/K=620.08. Both all_certified, failure=null, 37 cover visits. Formal test not started.
