# Invalid pre-correction runs — excluded from evidence and selection

The initial implementation did not match the declared E/B/G mechanisms: E
ignored its ratio, used cells in place of spatial samples, reported a full-route
cost, and still executed nearest-neighbor order. B did not use the parallax
radius and changed legal candidate eligibility. G omitted the saved-travel
factor. N missed required two-bearing and retry-location conditions; H could
override certified clear. The copied runner reused40000/50000 seeds rather
than the declared fresh60000/70000 cohorts. Early tests did not exercise these
mechanisms deeply enough. These are implementation defects, not evidence that
the proposed mechanisms are ineffective. Main agent records the correction.

Affected directories: dev_smoke, dev_smoke2, dev_smoke3, dev40, dev40b and
primary400. Keep every existing file and original manifest; primary400 was
stopped before completion. Any in-run source drift in dev_smoke is retained.
All these runs are invalid for algorithm comparisons, tuning or final ranking.
Earlier user-facing development numbers and ER/EN/ERN selection are withdrawn.

The corrected implementation restores the design and uses dev_valid40 and
primary_valid400 (fresh60000/70000 seeds), with independently reviewed source,
behavioral execution tests and new mechanism auditing. Combination selection
is repeated solely on corrected development. The frozen baseline is unchanged.
