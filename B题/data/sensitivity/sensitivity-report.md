# Q4 frozen baseline sensitivity, 2026-09-12

Target: Q4 TRI25 + ROUTE_ADAPTIVE_V4, frozen at feasible_baseline.
This report consolidates existing, completed offline experiments before the
user-authorized large ablation. No solver or frozen result is changed.

## Evidence and results

| Existing cohort | Cases | Full success | Mean T/K (s) | Mean movement (s) | Mean probes |
|---|---:|---:|---:|---:|---:|
| Mixed endpoint holdout | 100 | 100 | 517.5842931731096 | 4948.471249650514 | 279.73 |
| Mixed smooth development | 30 | 30 | 489.7928667317867 | 4967.4834140308 | 268.06666666666666 |
| Outward boundary, minimum RF radius, endpoint | 30 | 30 | 583.8610228024756 | 5291.001173331535 | 387.8666666666667 |
| Directional endpoint | 30 | 30 | 550.4069560674575 | 5193.812831663433 | 299.5 |
| Omnidirectional endpoint | 30 | 30 | 475.1409080301444 | 4603.272844601179 | 248.96666666666667 |

Sources: experiments/q4_efficiency/release_holdout100, release30,
release_boundary30, release_directional30, release_omni30, each with CSV,
summary JSON and manifest. These cohorts have different seeds and, in some
cases, multiple changed factors. Differences are descriptive stress sensitivity,
not causal paired effects of source type or error mode. The forthcoming ablation
must use the same seeds and latent scenes across every strategy and matched
source/error stress variants. The smooth development mean does not replace the
frozen endpoint holdout mean.

## Bottlenecks and scope

On the frozen holdout, movement takes 4948.471249650514 / 6682.781249650514
= approximately 74.05% of total virtual time; measurement takes 1653.08 s.
Discovery uses 243.78 probes, including 230.54 no_signal, versus 35.95 refinement
probes. Boundary tests increase probe count substantially. Completion remains
100% in these cohorts; this is finite offline evidence, not an official simulator
performance claim or a distribution-free performance guarantee.

The geometry certificate, positive-observation feasible region, optical fallback
and N=16 counting rule must remain authoritative. Soft RF beliefs may rank
actions but may not certify absence. The new experiment must report source
success, scene certification, movement, probe counts, failed clears, tail costs,
paired losses, and failures without success-only filtering.

## Memory check

Existing stress cohorts are not matched causal sensitivity experiments. New
comparisons will be paired; frozen baseline SHA256 entries were checked against
the working tree with no mismatches. Claim ceiling remains feasible_baseline.
