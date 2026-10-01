# 排料 / 切割下料（nesting, cutting & packing）数据集与对比结果

本目录是 `lcns` 逆向工程的**外部基准数据与结果对比**。所有数据均为下载所得，未做修改（除统一格式仓库本身的转换）；
来源、许可、出处引用逐条列在下面。

```
datasets/
├─ esicup/                    ESICUP 官方数据集（稀疏检出，CC0-1.0）
│  ├─ 2d_irregular/           2118 文件 · 74 MB · 21 个族（原始格式：txt / globalnest xml / xlsx / pdf）
│  ├─ 2d_rectangular/         1781 文件 · 9.2 MB · 24 个族
│  ├─ README.md  LICENSE  CITATION.cff
├─ or-datasets/               统一 JSON 格式（Oscar-Oliveira/OR-Datasets，MIT）
│  └─ Cutting-and-Packing/2D-Irregular/Datasets/   12 族 · 24 个 json · 6.2 MB
├─ refs/                      引用来源
│  ├─ sparrow_src/            arXiv:2509.13329v3 的 LaTeX 源码（含结果表 .tex）
│  └─ sparrow_src.tar.gz
├─ work/                      转换后的 lcns problem.json 与 .meta.json（由工具生成）
├─ results.csv                本次 lcns 运行的原始统计（每个实例一行）
├─ RESULTS.md                 与文献最优值的对比表（自动生成）
└─ bench_run.log              本次跑批的完整日志
```

---

## 1. 数据来源与许可

| 来源 | 内容 | 许可 | 说明 |
|---|---|---|---|
| [ESICUP/datasets](https://github.com/ESICUP/datasets) | EURO 切割与下料特别兴趣组的官方数据集（原 hospedagem 站点已迁移到 GitHub） | **CC0-1.0** | `2d_irregular` 为二维异形下料的经典族：albano, blaz(=SHAPES2), dagli, dighe, fu, gardeyn, guillotine, han, jakobs, mao, marques, poly, shapes, shirts, swim, terashima1/2, three, trousers |
| [Oscar-Oliveira/OR-Datasets](https://github.com/Oscar-Oliveira/OR-Datasets) | 由 Jeroen Gardeyn 转换的**统一 JSON 格式**（+ 每个形状的 DXF） | **MIT** | `Cutting-and-Packing/2D-Irregular/Datasets`：ALBANO, BALDACCI, BLAZ, DAGLI, FU, JAKOBS, MAO, MARQUES, SHAPES, SHIRTS, SWIM, TROUSERS |
| [arXiv:2509.13329v3](https://arxiv.org/abs/2509.13329) | Gardeyn, Vanden Berghe, Wauters, *An open-source heuristic to reboot 2D nesting research*（EJOR） | CC BY 4.0 | **结果表的权威来源**：`refs/sparrow_src/best_known_table.tex`（sparrow 最优 vs 此前最优）与 `comparison_table.tex`（sparrow/ROMA/GCS/FLD/ELS/PS 的期望密度） |
| [JeroenGar/sparrow](https://github.com/JeroenGar/sparrow) · [jagua-rs](https://github.com/JeroenGar/jagua-rs) | SOTA 开源实现（Rust） | MPL-2.0 | 未克隆；仅用于确认实例格式与对比口径（`strip_height`、连续旋转、`min_item_separation`） |

**未做任何修改**：`esicup/` 与 `or-datasets/` 是原样检出；`work/` 里的文件是转换产物（可删除并重建）。

## 2. 各数据集的出处引用（摘自 `esicup/2d_irregular/README.md`）

| 族 | 出处 |
|---|---|
| `albano` | Albano & Sapuppo (1980), *Optimal allocation of two-dimensional irregular shapes using heuristic search methods*, IEEE Trans. SMC 10(5):242–248 |
| `blaz`（= SHAPES2） | Blazewicz, Hawryluk & Walkowiak (1993), *Using a tabu search approach for solving the two-dimensional irregular cutting problem*, Annals of OR 41:313–327 |
| `dagli` | Ratanapan & Dagli (1997), *An object-based evolutionary algorithm for solving irregular nesting problems*, ANNIE'97 |
| `dighe` | Dighe & Jakiela (1996), *Solving pattern nesting problems with genetic algorithms…*, Evolutionary Computation 3:239–266 |
| `fu` | Fujita, Akagi & Hirokawa (1993), *Hybrid approach for optimal nesting using a GA and a local minimisation algorithm*, ASME DAC |
| `gardeyn` | Gardeyn, Van den Berghe & Wauters (2025), arXiv:2509.13329 —— **10 个新的真实工业实例**（含 90° 与连续旋转两个版本） |
| `han` | Han & Na (1996), *Two-stage approach for nesting…*, Proc. IMechE Part B 210(B6):509–519 |
| `jakobs` | Jakobs (1996), *On genetic algorithms for the packing of polygons*, EJOR 88:165–181 |
| `mao` | Bounsaythip & Maouche (1997), *Irregular shape nesting and placing with evolutionary approach*, IEEE SMC |
| `marques` | Marques, Bispo & Sentieiro (1991), *A system for the compaction of two-dimensional irregular shapes based on simulated annealing*, IECON'91 |
| `poly` | Hopper (2000), PhD thesis, Cardiff University |
| `shapes` / `shirts` / `swim` / `trousers` | Oliveira, Gomes & Ferreira (2000), *A new constructive algorithm for nesting problems*, OR Spectrum 22(2):263–284 |
| `terashima1` / `terashima2` | Terashima-Marín et al. (2010) / López-Camacho (2012)，共 1020 个凸/非凸算例（bin packing） |

（完整清单与 `3d_*`、`1d`、`misc` 见 `esicup/README.md` 与 `esicup/2d_irregular/README.md`。）

## 3. 文献基准值与口径

对比使用的口径（与文献一致，这是对比有意义的前提）：

```
rho = Σ(已放置零件面积) / ( 固定的条带边 × 实际占用长度 )
```

实例文件里 `strip_height` 是**固定边**（y 方向），x 方向视为无限；lcns 给一张超长板，
实际占用长度取解中所有已放置零件包围盒的 x 跨度。因此 `rho` 与文献的密度定义**逐字相同**。

作为口径自检，`results.csv` 里还给出 `literature_implied_length = 总面积 / (strip_height × 文献 rho)`，
它必须大于该实例的最大零件尺寸（否则说明我的换算写错了）。

## 4. 如何复现

```powershell
# 1) 数据集（已包含在本目录；如需重新获取）
git clone --depth 1 --filter=blob:none --sparse https://github.com/ESICUP/datasets esicup
cd esicup; git sparse-checkout set 2d_irregular 2d_rectangular
git clone --depth 1 --filter=blob:none --sparse https://github.com/Oscar-Oliveira/OR-Datasets or
cd or; git sparse-checkout set Cutting-and-Packing/2D-Irregular

# 2) 转换 + 跑批（需要先构建 nest_eval；MinGW 运行时必须在 PATH 上）
$env:PATH = 'C:\Program Files\JetBrains\CLion 2025.3.3\bin\mingw\bin;' + $env:PATH
python tools\run_benchmarks.py --time 30 --seeds 1
# 单实例：
python tools\esicup_to_lcns.py --in ..\datasets\or-datasets\...\SWIM\json\swim.json `
       --out ..\datasets\work\swim.json --meta ..\datasets\work\swim.meta.json
build\nest_eval.exe ..\datasets\work\swim.json --time 30 --out ..\datasets\work
```

## 5. 结果

* 原始统计：[`results.csv`](results.csv)
* 对比表（含文献各算法）：[`RESULTS.md`](RESULTS.md)
* 跑批日志：[`bench_run.log`](bench_run.log)

**口径与限制（务必与结果一起阅读）**

1. 文献数字来自 **20 分钟**级别的运行（sparrow 为 100 次独立运行），本目录的 lcns 数字是
   **单次短时运行**，具体预算见 `results.csv` 的 `seconds` 与 `seed`。它是**可复现的基线**，不是性能对等声明。
2. `sparrow` 使用**连续旋转**与专用碰撞检测引擎（`jagua-rs`）；lcns 是逆向重建，
   几何内核为自研定点实现，LP 后端为零依赖自研单纯形（原库静态链接 COIN-OR Clp 1.15.3）
   ⇒ 差距是预期内的，**如实记录而非隐藏**。
3. lcns **不遵循**实例的逐件 `allowed_orientations`，它用自己的离散角度阶梯（`nest_eval --angles`）。
4. 若某实例未能在预算内放完所有零件，`results.csv` 的 `nested/total` 会显示出来 ——
   此时 `rho` 只对**已放置**部分有意义，不能与文献的完整解密度直接比较。

---

## 6. 建这套基准时**发现并修掉的两处真实缺陷**

跑基准的价值之一，就是它会立刻暴露"能跑但错"的地方。本次发现两处：

### 6.1 `TilingNester` 超放零件（已修）

**现象**：`ALBANO` 需求 24 个实例，解里却有 **28** 个；其中 `partIndex=2` 被放了 **8 次**（需求 4）。
三个种子结果完全一致 ⇒ 确定性缺陷，不是随机。

**定位**：`nester.cpp` 的 `TilingNester::run` 用图案单元（pattern cells）拼 seed 时，
只卡了**全局实例总数**（`order.totalPartInstances()`），**没有逐件检查该 kind 的 multiplicity** ——
图案里同一个 kind 的单元多于需求时就会全被放进去。

**修复**：按 `max(1, part.multiplicity)` 维护逐件余量，放一个减一个（与模型里
`totalPartInstances()` 的 `max(1, ·)` 约定一致）。

**回归测试**：`tests/test_nester.cpp` 新增一条不变量断言 —— 任何策略产出的解，
每个 kind 的放置数不得超过 `max(1, multiplicity)`，且总数不得超过 `totalPartInstances()`。

### 6.2 `placeShape` 的平移被复制了 5 处，其中一处漏掉（已修）

**现象**：评测器算出的已放置包围盒（1940×1577）与引擎自己报的 nesting 包围盒（12968×3756）
不一致 —— 面积却完全吻合（旋转/平移保持面积，所以面积对、位置错）。

**原因**：`placeShape()` 只做**旋转+翻转**，"再平移"这段代码在 `nester.cpp`、`engine.cpp`、
`io.cpp`（3 处）被**各抄了一遍**；新写的 `nest_eval` 少抄了一份。

**修复**：新增 `lcns::placedPolygon()`（旋转+翻转+平移，**唯一一处定义**），
5 个调用点全部改用它；`placedShape(Part, NestedPart)` 也改走这条路径。

> 这两处都不是逆向结论错误，而是工程实现缺陷；它们说明"外部基准"对本工程的价值 ——
> 单纯的单元测试没覆盖到它们。

## 7. 与文献差距的**性质**：不是时间预算问题（实验证据）

对比表里 lcns 的密度是 30.0–42.6%，文献是 68.6–92.6%，差 **33–59 个百分点**。
为了判断这是"跑得不够久"还是"启发式上限"，做了 4 倍预算的对照实验：

```
build\nest_eval.exe ..\datasets\work\<inst>.json --time 30  --seed 0 --iterations 100000 --quiet
build\nest_eval.exe ..\datasets\work\<inst>.json --time 120 --seed 0 --iterations 100000 --quiet
```

| 实例 | 30 s：rho / 长度 / 实际用时 | 120 s：rho / 长度 / 实际用时 |
|---|---|---|
| `SWIM` | 33.29% / 13288.1 / 51.8 s | **33.29% / 13288.1 / 141.4 s** |
| `JAKOBS1` | 30.31% / 32.3 / 13.9 s | **30.31% / 32.3 / 10.3 s** |
| `MARQUES` | 42.55% / 162.6 / 19.1 s | **42.55% / 162.6 / 19.2 s** |

**结论（如实说）**：4 倍预算下密度**逐位相同**，且实际用时常常远小于限额
（`FU` 甚至只用 **0.4 s**）⇒ 差距**不是**"没跑够时间"，而是当前重建版的搜索在**放完即止**：
原库文档中的"多策略并发 **+ 迭代改进** + 束/树搜索 + 后处理压缩"里，
**迭代改进这一环在本工程里明显弱于原库**（压缩/平移/旋转阶段存在，但缺乏持续降低条带长度的驱动）。
这属于**已知差距**，不作"接近 SOTA"的暗示。

## 8. 其他已核实的事实

* **`SHAPES0` 与 `SHAPES1` 的几何完全相同**（四个 item 的多边形逐点相同、需求相同、`strip_height` 都是 40），
  差别只在 `allowed_orientations`：`SHAPES0` 只允许 `0°`，`SHAPES1` 允许 `0°/180°`。
  lcns **不读逐件朝向**（用自己的角度阶梯），所以两行结果必然相同 —— 这是口径差异，不是数据问题。
* `BLAZ` 统一格式文件名是 **`blaz1.json`**（`blaz.json` 不存在），已修正映射。
* `GARDEYN0..9`（论文新增的 10 个真实工业实例）已随 ESICUP 数据集下载到
  `esicup/2d_irregular/gardeyn/`，但论文只给了它们的解图、**没有给出可比数值表**，
  故未纳入对比；如需使用可自行转换运行。
* 论文结果表所在文件：`refs/sparrow_src/best_known_table.tex`（最优值 vs 此前最优）
  与 `comparison_table.tex`（sparrow/ROMA/GCS/FLD/ELS/PS 期望密度）—— 引用时请以这两个文件为准。
