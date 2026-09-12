# Findings — Q4 HEX37

## Independent proof check (2026-09-11)

Lattice: `e1=(800,0)`, `e2=(400, 400√3)`, `||e1||=||e2||=800`, angle `60°`.
Keep `max(|q|,|r|,|q+r|)<=3`: 1+6+12+18=37, origin included.

Covering radius of the infinite triangular lattice is the circumradius of an equilateral triangle of side 800:

`δ = 800/√3 ≈ 461.8802153517 m`.

Approach point `y=g+500d` satisfies `||y||<=2300`. Nearest lattice point `p` obeys `||p-y||<=δ`, hence

- `||p-g|| <= 500+δ ≈ 961.880 < 1000`
- `d·(p-g) >= 500-δ ≈ 38.120 > 0`

Finite-set claim: ring-4 (`max(|q|,|r|,|q+r|)=4`) minimum Euclidean origin distance is `800√12 ≈ 2771.281`. Algebra:

`2300 + 800/√3 < 800√12  ⇔  √3 < 40/23 ≈ 1.73913`.

`√3 ≈ 1.73205 < 1.73913`. Gap ≈ 9.401 m, strict.

Numerical spot checks: 720 headings on `|y|=2300` and 20000 random points in the disk of radius 2300 all had a HEX37 neighbor within `δ`. These checks do not replace the proof.

Hamilton path from origin along 800 m edges exists (37 unique vertices, 36×800=28800 m). Frozen offline; not searched online.

## Audit, not this round

### Detected channels on later cover points

`Q4Runner.run()` calls `scan_at(..., certificate_mode=True)`, so `_channels_to_scan` would measure a still-`detected` channel at later cover sites. In the current loop, `process_pending()` localizes and clears after every station, so this did not fire on sampled seeds (HEX37 seeds 0,1,7,10,27 and SQUARE81 0,7,10 all had 0 extra cover measures on already-detected channels). The wasted-measure path exists in code but is currently masked by immediate clearing. Do not mix a skip-detected-on-cover change into HEX37.

### N=16 counting certificate

Problem text (ATT2-03, Q4-01): `N∈{10,...,16}`, one source per channel. If 16 distinct channels have `direction`/`near`, then `N=16` and the other 4 channels cannot hide a source. Lower bound 10 is not a stop rule.

Observed leftover discovery after the 16th detection (still visiting remaining cover points to certify the 4 empty channels):

- HEX37 seed 7: 56 extra unseen-channel cover measures
- SQUARE81 seed 7: 104 extra unseen-channel cover measures

This is a counting certificate, not the geometric HEX37/SQUARE81 certificate. Do not change termination in this round.

## ROUTE_INSERT_V1 (2026-09-11)

Fixed HEX37 Hamilton order. Pending sources are one-step inserted only when
`ΔL = d(x,q)+d(q,u)-d(x,u) ≤ 400 m`. Optical fallback stays a drain-time SAFE
path. `INSERT_MAX_M=1000` still 30/30 but mean move stayed ~44.2 km because
inserts bounced off the skeleton; 400 m hit 36.1 km.

Detected channels are still measured at later HEX points (`certificate_mode=True`),
which raised n_measure 337→545. Next phase: opportunistic detected measure and
pending batching.

## ROUTE_INSERT_V2 (2026-09-11)

On-path pending (`ΔL≤400`) are batched: enumerate if ≤7 else NN+2-opt, then
localized before returning to the Hamilton point. Optical fallback remains
drain-only. Detected HEX probes require a new ≥200 m baseline inside the
current region and the forward half-plane.

Offline 30/30. Mean T/K 774→735, n_measure 545→375, mean move 36.1→38.3 km.
Contest metric is T/K after full clear, so V2 is the live scheduler.

## ROUTE_INSERT_V3 (2026-09-11)

Frozen after 18-cell 10-seed grid then two 30-seed finals:
`CLEAR_INSERT_MAX=600`, `MEASURE_INSERT_MAX=250`, `AGGRESSIVE_CLEAR_RHO=80`.
3-step HEX lookahead; rho>60 at most 2 heuristic clears per channel.
Offline 30/30. Mean T/K 735.31→711.20 (−3.3%). Gain <5%, so do not keep tuning thresholds.

## HEX37 PREFIX_A (2026-09-11)

Equal-length 800 m Hamilton path from origin, scored offline (mean first-detect
index 5.54 vs CURRENT 8.98; cov10 0.84 vs 0.56). Frozen as `PREFIX_A`.
Paired V3 seeds 0–29: T/K 711.20→683.09 (−4.0%), mean first-detect 6.85→4.20.
30/30 full clear. Practice default is PREFIX_A; CURRENT remains selectable.
Dynamic origin-based route choice is not enabled.

## Decision rule

If HEX37 misses a source, fails absence certification, or `K<N`, revert to SQUARE81 immediately.
