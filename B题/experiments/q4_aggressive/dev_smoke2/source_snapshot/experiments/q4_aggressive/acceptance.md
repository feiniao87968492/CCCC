# Preimplementation acceptance cases

Readiness is pending independent review. These are specifications, not test
execution or evidence of correctness. No primary result exists yet.

- E: ordering is a permutation of the original certified cells; misleading
  mass at the wrong end still reaches a true source at the opposite end.
  Failed discs affect only soft mass; if all samples are eliminated, ordering
  still returns every cell. Expected cost equals explicit first-hit weighted
  path cost, charging the full route for samples never hit. Larger-than256-cell
  fallback remains complete and does not attempt a quadratic ordering matrix.
- B: illegal/freshness-violating current viewpoints are excluded, all scores
  are finite, actual negative-RF recovery priority is retained. Future virtual
  viewpoint costs must never be passed to the physical executor as observed
  positions or actual measurements.
- G: repeated callbacks at the same physical stop share3 tokens; single
  movements <=1 m do not reset them. Changing actual receiver channel changes
  the score denominator. Each token corresponds to exactly one actual measure.
  Cover scans remain outside the budget and still satisfy absent-channel proof.
- R: the early cap counts only actual dedicated measures, requires two bearing
  observations and rho<=200, and never returns an optical kind to the scalar
  measurement executor. One-bearing shadow still retains the original fallback.
- H: line-estimate conditioning and legality are retained, no third trial,
  and negative observations do not unlock another trial at one positive version.
- N: an opportunistic trial executes at the exact current physical position,
  is linked to one clear, requires two bearings, and cannot recur at the same
  positive version after a negative result. All trials retain their actual costs.
- Integration: all12 new arms finish an observation-only multi-source scene
  including outward directional boundary sources; preserve unknown channels,
  bounded speculative work, dedicated cap8 and complete optical fallback.
- Controls: factories explicitly instantiate old LC/LPC and JSO_compact_dopt;
  test them against previously pinned code and retain exact effective metadata.
- Evidence: preserve start snapshots and final source hashes, all dev/primary
  rows, exact cost reconstruction, scenario hashes and per-event hashes. Rank
  only arms clearing all settings, including the separate stress subset.
