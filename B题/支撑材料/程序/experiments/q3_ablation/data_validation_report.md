# Q3 ablation independent result checks

## Data and replay

- Evaluation matrix: 420 scene groups = 7 values of N (10–16) × 4 spatial
  families × 5 repetitions × 3 deterministic error modes; 10 arms = 4,200 runs.
- `scenes.json` SHA256: `2cb2a009b2f00abad7fdcd5c38f27279ef4fe011f140997870391a44f701d114`.
- `rows.csv` SHA256: `f6dc70ff3dfb7840f82e718026ccf911960e7433a38d82afb518ca4fbcf60bce`.
- Manifest reports `changed_inputs=[]`; every run has a compressed action trace.
- Independent replay of each row's action trace reconstructs virtual T within the
  recorded audit tolerance (maximum action time error 0; total error 0).

## Completion and accounting

Every arm completed 420/420 scenes, with K=5,460 and N=5,460 source instances
(clearance rate 1.0). No source was removed after a failed clear; all failed
clears remain charged. `T/K` is reported only for complete rows, and pooled
`sum(T)/sum(K)` is kept separate from the mean of per-scene `T/K`.

The baseline is the actual repository `GreedyFastRunner(source_budget_s=0)`.
Compact arms use a separate radius-1130 station identity and per-channel V sets;
the original radius-1200 arm remains unchanged. Policies do not access the
environment's private source dictionary; the client exposes only enter, measure,
clear and exit. Source hashes and action traces permit exact replays.

## Main paired results

| 策略 | 完成率 | 平均总耗时 T (s) | 平均每源 T/K (s) | 平均行走时间 (s) | 平均探测次数 | 失败清除 |
|---|---:|---:|---:|---:|---:|---:|
| 原策略 GREEDY_FAST | 100% | 4850.96 | 379.60 | 3840.15 | 136.26 | 43.23 |
| 仅缩小外圈 COMPACT | 100% | 4642.35 | 362.70 | 3674.55 | 131.00 | 39.43 |
| 联合路线 J | 100% | 3571.50 | 279.28 | 2790.11 | 110.65 | 18.84 |
| 选择性探测 S | 100% | 3945.69 | 310.14 | 3127.91 | 116.55 | 19.66 |
| 两测向乐观清除 O | 100% | 4071.23 | 319.13 | 3202.49 | 133.50 | 2.09 |
| J+S | 100% | 3279.33 | 257.42 | 2499.47 | 108.27 | 23.45 |
| J+O | 100% | 3436.98 | 269.07 | 2681.63 | 114.12 | 4.14 |
| S+O | 100% | 3824.04 | 300.55 | 3075.33 | 113.36 | 2.13 |
| J+S+O | 100% | **3238.04** | **254.05** | **2518.53** | **107.62** | 4.39 |
| J+S+O 每站扫全频道 | 100% | 4574.24 | 360.37 | 2376.89 | 353.25 | 4.94 |

## Paired deltas against original

The paired file `evaluation/paired_deltas.csv` uses the same scene ID and error
field for every arm. The strongest complete arm JSO reduces mean T by 1,612.91
s, walking time by 1,321.62 s and measurements by 28.64 per scene; it wins on T
in 99.52% and on measurement count in 97.14% of paired scenes. J alone reduces
T by 1,279.46 s and measurements by 25.61. S alone reduces measurements by
19.71. O alone reduces failed clears by 41.14 while reducing T by 779.72 s but
does not materially reduce measurement count.

The all-scan negative control reduces walking by 1,463.26 s but adds 216.99
measurements and has a worse p95 T/K than JSO; this separates walking savings
from probing cost.

## Limitations and claim ceiling

These are synthetic offline scenes and deterministic bounded bearing-error
models, not official simulator results. The 1,130 m cover has a 3.05 m margin
below the 1,000 m minimum reception radius, so coordinate rounding or changed
problem assumptions would require revalidation. The data support an
`exploratory_analysis` comparison inside this declared matrix. They do not
support global optimality, official-simulator equivalence, or universal
superiority. The screenshot's nine original scenes and 117 sources were not
reconstructed.

Memory check: retaining failed clear attempts and ranking only complete scenes
is essential; a low T/K from incomplete runs is invalid.
