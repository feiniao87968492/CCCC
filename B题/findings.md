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

## Decision rule

If HEX37 misses a source, fails absence certification, or `K<N`, revert to SQUARE81 immediately.
