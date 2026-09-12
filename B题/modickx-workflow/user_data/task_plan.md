# Task Plan — Q4 HEX37 cover challenger

## Goal

Keep `cumulative-optical-v2` localization/optical fallback unchanged. Replace only the P4 discovery cover and its route with a switchable `SQUARE81` / `HEX37` layer. HEX37 may become the practice challenger only after the continuous cover proof, unit tests, and 30/30 paired offline correctness all hold.

## Status

- Phase 1: Independent HEX37 proof check — complete
- Phase 2: Cover abstraction + HEX37 points/path — complete
- Phase 3: Tests (existing + HEX37) — complete, 168 passed
- Phase 4: Paired SQUARE81 vs HEX37 offline experiment — complete, 30/30
- Phase 5: Audit detected-channel extra measures and N=16 stop rule — complete, no code change
- Phase 6: Official 问题4演练, HEX37, 1–2 games — complete, 12/12 and 16/16

## Constraints

- Do not delete SQUARE81; it remains regression baseline and fallback.
- Do not change `history_region`, cumulative bearings, 1.005° envelope, rho<=20 certified clear, optical fallback, or 28 m optical cover.
- Q4 `no_signal` still must not be read as `d>1000`.
- Detected/cleared channels cannot be rewritten to `certified_absent` by later `no_signal`.
- Official 问题4正式测试 is forbidden.

## Done when

1. Proof constants and finite-set membership are independently verified.
2. Existing tests still pass with default `SQUARE81`.
3. New HEX37 tests 1–15 pass.
4. Paired 30-seed comparison is recorded.
5. HEX37 is used in practice only if 30/30 full clear + certificate hold; otherwise revert to SQUARE81.

All items met. HEX37 did not miss a source in offline 30/30 or 2 official practice games.
