# lcns on the ESICUP / OR-Datasets 2D irregular benchmarks

Published reference values are **quoted** from the LaTeX source of Gardeyn, Vanden Berghe & Wauters, *An open-source heuristic to reboot 2D nesting research*, European Journal of Operational Research (arXiv:2509.13329v3) -- downloaded to `refs/` -- which reports the current state of the art on exactly these instances.

`rho = sum(placed part areas) / (strip_height * achieved_length)`, the density definition used in that literature. The instances fix `strip_height` and leave the other axis unbounded; lcns is given an over-long sheet and the achieved length is measured from the bounding box of the placed parts.

| instance | part kinds | instances | total area | strip H | nested | lcns rho | previous best rho | sparrow rho | gap vs sparrow | secs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `ALBANO` | 8 | 24 | 42656785 | 4900 | 24/24 | **42.02%** | 89.58% | 89.82% | 47.80 pp | 29.4 |
| `SHAPES2` | 7 | 28 | 324 | 15 | 28/28 | **37.31%** | 84.84% | 86.23% | 48.92 pp | 30.0 |
| `DAGLI` | 10 | 30 | 3034 | 60 | 30/30 | **34.40%** | 89.51% | 90.17% | 55.77 pp | 30.1 |
| `FU` | 12 | 12 | 1083 | 38 | 12/12 | **33.71%** | 92.41% | 92.41% | 58.70 pp | 0.4 |
| `JAKOBS1` | 25 | 25 | 392 | 40 | 25/25 | **30.31%** | 89.09% | 89.26% | 58.95 pp | 16.1 |
| `JAKOBS2` | 25 | 25 | 1351 | 70 | 25/25 | **30.00%** | 87.73% | 87.73% | 57.73 pp | 10.7 |
| `MAO` | 9 | 20 | 3758617 | 2550 | 20/20 | **33.17%** | 86.05% | 86.87% | 53.70 pp | 31.0 |
| `MARQUES` | 8 | 24 | 7194 | 104 | 24/24 | **42.55%** | 91.02% | 92.02% | 49.47 pp | 21.8 |
| `SHAPES0` | 4 | 43 | 1596 | 40 | 43/43 | **37.23%** | 68.79% | 69.98% | 32.75 pp | 30.3 |
| `SHAPES1` | 4 | 43 | 1596 | 40 | 43/43 | **37.23%** | 76.73% | 76.73% | 39.50 pp | 30.2 |
| `SHIRTS` | 8 | 99 | 2160 | 40 | 92/99 | **38.75%** | 88.96% | 90.92% | 52.17 pp | 30.4 |
| `SWIM` | 10 | 48 | 25445024 | 5752 | 48/48 | **33.29%** | 75.94% | 79.83% | 46.54 pp | 51.8 |
| `TROUSERS` | 17 | 64 | 17206 | 79 | 64/64 | **38.49%** | 91.06% | 92.62% | 54.13 pp | 30.9 |

## Literature comparison on the same instances (published expected density, %)

| instance | sparrow | ROMA | GCS | FLD | ELS | PS | lcns |
|---|---:|---:|---:|---:|---:|---:|---:|
| `ALBANO` | 89.47 | 87.55 | 87.47 | 88.01 | 87.38 | 84.95 | **42.02** |
| `SHAPES2` | 84.68 | 83.02 | 82.40 | - | 82.55 | 85.49 | **37.31** |
| `DAGLI` | 89.26 | 87.50 | 87.06 | 87.14 | 86.27 | 84.17 | **34.40** |
| `FU` | 92.24 | 91.95 | 90.68 | 91.17 | 90.00 | 90.39 | **33.71** |
| `JAKOBS1` | 89.09 | 89.09 | 88.90 | 88.96 | 88.35 | 81.67 | **30.31** |
| `JAKOBS2` | 84.77 | 83.56 | 81.14 | 83.41 | 80.97 | 80.42 | **30.00** |
| `MAO` | 86.14 | 83.76 | 82.93 | 82.28 | 82.57 | 75.94 | **33.17** |
| `MARQUES` | 90.93 | 89.97 | 89.40 | 88.38 | 88.32 | 85.48 | **42.55** |
| `SHAPES0` | 68.60 | 68.73 | 67.26 | 67.39 | 66.85 | 66.50 | **37.23** |
| `SHAPES1` | 75.69 | 75.86 | 73.79 | 73.91 | 74.24 | 72.55 | **37.23** |
| `SHIRTS` | 89.66 | 87.62 | 87.59 | 88.21 | 87.20 | 85.99 | **38.75** |
| `SWIM` | 78.26 | 74.29 | 74.49 | 74.66 | 74.10 | 71.44 | **33.29** |
| `TROUSERS` | 91.73 | 90.48 | 89.02 | 89.17 | 88.29 | 89.30 | **38.49** |

Legend: ROMA = Sato et al. 2019 (raster), GCS = Elkeran 2013, FLD = Wang et al. 2017, ELS = Leung et al. 2012, PS = Fontan 2023 (open source, deterministic). All quoted from the same table.

## What this comparison does and does not say

* The published numbers come from **20-minute runs** (sparrow: 100 independent runs; the deterministic PS: one run). The lcns column here comes from a single short run per instance -- see `results.csv` for the exact budget (`seconds`) and seed. It is a **reproducible baseline**, not a claim of parity.
* `sparrow` searches **continuous rotations** and uses a dedicated collision detection engine (`jagua-rs`). lcns is a reverse-engineered reconstruction whose geometry kernel is a hand-written fixed-point reimplementation and whose LP backend is a zero-dependency simplex (the original statically links COIN-OR Clp 1.15.3) -- so a gap is expected and is documented rather than hidden.
* lcns does not honour the per-item `allowed_orientations` of the instances; it uses its own discrete angle ladder (`--angles`).
* `literature_implied_length` in `results.csv` is `total_area / (strip_height * published_rho)`: it is the length the published density implies, and is printed so the density convention can be sanity checked independently (it must exceed the largest part extent).
