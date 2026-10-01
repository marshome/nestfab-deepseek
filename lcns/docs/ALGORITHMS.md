# 主要算法流程图

配套的可渲染图（双击用浏览器打开）：

| 图 | 内容 | 出处 |
|---|---|---|
| [`FLOW_MAIN.svg`](FLOW_MAIN.svg) | **主流程**：建模 → 选项 → 云端/本地分派 → 求解 → 取解 → 输出 | §5 · §6 |
| [`FLOW_SEARCH.svg`](FLOW_SEARCH.svg) | **搜索**：多策略并发 + 级联预算 + 观察者择优 + 时间闸门 | §7.2 |
| [`FLOW_NESTER.svg`](FLOW_NESTER.svg) | **Nester 内部**（以 `NestingNester 0x378E0` 为例） | §7.2 |
| [`FLOW_NFP.svg`](FLOW_NFP.svg) | **几何**：No-Fit Polygon（边界 Convolution）计算链路 | §7.1 |
| [`FLOW_ROW.svg`](FLOW_ROW.svg) | **行排样**：逐零件路径（候选角度 → 分值 → 取最小） | §21–§38 |
| [`FLOW_POSTOP.svg`](FLOW_POSTOP.svg) | **后优化**：Compaction + 收尾三连 pass | §7.2 |
| [`FLOW_LP.svg`](FLOW_LP.svg) | **LP/定价层**：`Prc::*PriceComputer` + `Coin::CoinLP` | §7.3 |

另有 [`ARCHITECTURE.svg`](ARCHITECTURE.svg)（分层架构）与 [`ROW_PATH.svg`](ROW_PATH.svg)（逐零件调用链）。

> 生成与校验：`python tools/gen_flow.py`（画流程图 + 分层图）· `python tools/check_arch.py`
> 校验全部 SVG：**不越界、不重叠、连线不穿过无关框**（当前 **9/9 通过**）。

---

## 1. 主流程（`FLOW_MAIN.svg`）

```mermaid
flowchart TB
  A["建模：LaunchingOrder<br/>NewLaunchingOrder 0x14620"] --> B["AddSheet / AddPart /<br/>AddHole / AddToolPath"]
  B --> C["Set* 选项：共边 / 多割炬 / 剪切 /<br/>行-管材 / 间隙 / 线程（只写字段）"]
  C --> D["Structure::CreateProblem 0x1EE50<br/>唯一读取/生效点"]
  D --> E{"cns_force_cloud<br/>置位？"}
  E -- 是 --> G["LaunchComputation 0x6100<br/>PUT /pb/ · GET /sol/"]
  E -- 否 --> F["LaunchLocalComputation 0x2AB0"]
  G --> H{"云端失败？"}
  H -- 否 --> L["WaitNextSolution /<br/>GetSolution / GetNesting"]
  H -- 是：回退本地 --> F
  F --> I["0x1E70 本地启动器<br/>校验 Order → Keys → 线程/迭代"]
  I --> J["MultiEngine::Run<br/>seed / nb_max_threads / 策略表"]
  J --> K["Supervisor::Run 0x827F0"]
  K --> L
  L --> M["GenerateDxfNesting 0xBF70 /<br/>HtmlSolutionReport / DeleteLaunchingOrder"]
```

**要点**

* `Set*` 导出**只写 `LaunchingOrder` 字段**；唯一让它们生效的是 `Structure::CreateProblem 0x1EE50`（15305 B）。
* `LaunchComputation ⇄ LaunchLocalComputation` **互调** ⇒ "云端不可用则本地算 / 强制云端"双向回退（已证实）。
* 计算控制族（`Wait*`/`Cancel*`/`Terminate*`）都以 `cmp byte [rcx+0x48], 0` 起手分支（`Order+0x48` = 计算模式）。

---

## 2. 搜索：多策略并发（`FLOW_SEARCH.svg`）

```mermaid
flowchart TB
  A["Supervisor::Run 0x827F0"] --> B["AdvancedStrategist::operator() 0x2DF60<br/>选 4 条路：mode 2/3/4/默认"]
  B --> C["0x2CCF0 展开成 1–4 个预算递减变体<br/>n → 2 → (n+1)/2 → n−1"]
  C --> D{"SupervisorCanceller::ProbeCancel 0x30030<br/>elapsed / Problem[+0x408] > 1.0 ？"}
  D -- 超时 --> E["置粘滞标志 + __gthread_cond_broadcast<br/>广播取消"]
  D -- 未超时 --> F["Nester::Prepare(v3) / Estimate(v4)"]
  F --> G["Nester::Run(v5)"]
  G --> H["Observer::NewNestingFound<br/>NewIntermediateSolutionFound 0x755A80"]
  H --> I["BestObserver 择优<br/>CompositeObserver 0x8D4500"]
  I --> K["返回最优解"]
  J["并行取消器：Compact 0x7D2610 · NoFitMap 0x7D29F0<br/>Warp 0x7D7940 · RCompact 0x7D2CB0（不可取消）"]
```

**要点**

* 两个阶段各自的多线程：`SetLocalMaximumThreads` / `SetLocalMaximumIterations` ⇒ multi 阶段与 nesting 阶段分开配线程。
* `Multi::NestingNester` 自带 `std::mt19937`（构造器 `0x342E0`：`imul eax,eax,0x6C078965`、`[+0x9F8] = 624`）
  ⇒ **带随机扰动的确定性局部搜索**；无任何 GA 字符串 ⇒ 不是遗传算法。
* 12 个策略的 `Run` 槽即各类的最大函数（Nesting `0x378E0` 14374 B、Tiling `0x46940` 16258 B、Row `0x913E0` 12380 B …）。

---

## 3. Nester 内部（`FLOW_NESTER.svg`）

```mermaid
flowchart TB
  A["NestingNester::Run 0x378E0"] --> B["对象布局（构造器证实）<br/>+0x18/+0x20 mode/flags · +0x28 预算<br/>+0x30 比例(≥1.0) · +0x38..+0x9F8 MT19937"]
  B --> C{"enable_rectangle /<br/>force_rectangle ？"}
  C -- 是 --> D["矩形快速路径 RectangleNester 0x75FB0<br/>nb_rectangle_try · ...before_rectangle_dual"]
  C -- 否 --> E["核心排布 A: 0x344D0（6748 B）"]
  D --> E
  E --> F["核心排布 B: 0x35F30（6436 B）"]
  F --> G["nesting_context.cpp: 0x3F070 / 0x434D0"]
  G --> H["tiled_multipart.cpp: 0x185750 / 0x185A40 / 0x187020 / 0x189CA0"]
  H --> I["beam 树准备 0x22CCA0（2916 B）<br/>tree_db 0x1C1650 + 互斥锁"]
  I --> J["节点评分：TerminalNode 0x974F0 → [+0x48]<br/>SplitNode 0x97510 → +0x50"]
  J --> K["产出 nesting 候选 → Observer"]
```

**未确认**：beam width 的具体常量未找到（切入口：`0x1C1650` 的实现与 `0x22CCA0` 中 `ebp` 的来源）。

---

## 4. 几何：NFP 链路（`FLOW_NFP.svg`）

```mermaid
flowchart TB
  A["GetNoFitMap 0x8AC0 / GetNoFitPlacementMap 0xA620"] --> B["0x665BF0 缓存「取或算」"]
  B --> C{"命中 NFPMap 缓存？<br/>+0x78 / +0xA8 两个 map"}
  C -- 是 --> D["直接返回缓存多边形"]
  C -- 否 --> E["0x585CA0 → ToExactPerimeter 0x6863C0（tol=1e-6）×2<br/>→ 定点化 ×1e10"]
  E --> F["0x5A2530 → 0x5A11B0 → 0x59E9D0 NoFitMapWithoutHoles<br/>→ 0x59CD10 → 0x59C560"]
  F --> G["ConvolutionRaw 0x596F20"]
  G --> H["核心 0x596100：0x595A80 生成 40 B 有向边<br/>用 128 位叉积 0x58E450 判凸/凹"]
  H --> I["0x596000 生成 64 B Edge 记录<br/>{A@+0x00, B@+0x10, C@+0x20, bool, bool}"]
  I --> J["主循环 0x596231：仅用 (dx,dy) 符号分象限 1..4"]
  J --> K["按极角键输出 40 B 事件记录并归并"]
  K --> L["对同一对多边形调用两次并交换（r9d=1 再 0）<br/>→ 两个方向的 NFP"]
  L --> M["0x687080 转回 double"]
  M --> N{"缓存总数 > 0x1312CFF（19,999,999）？"}
  N -- 是 --> O["清空 NFPMap 缓存"]
  N -- 否 --> P["返回 vector Polygon（NoFitGeometry 24 B）"]
  O --> P
```

**要点**

* **极角归并完全不用 `atan2`**：全库唯一的 `atan2` 是 `0x634C70`（41 B，x87 `fpatan`），只被 `Geom::SignedAngleInRad 0x5C5280` 使用；象限分类只用 `(dx,dy)` 的符号 ⇒ 全部是 **128 位精确谓词**。
* 复杂度上限 `m_max_complexity` 在 `NoFitContext+0xE8`，默认 **25000 = 0x61A8**；缓存清空阈值 **19,999,999 = 0x1312CFF**。
* 定位：**算法结构（象限分类 + 事件归并 + 精确谓词）已证明**；"等价于教科书式 edge-merge Minkowski 和"是**推断**。
* 偏移（inflate/gap）：`AddInflatedToolPathToPart 0x12C60` 对外轮廓 `+gap`、对内孔用 `btc` 取反符号位 ⇒ `−gap`（**没有** JoinType/MiterLimit 概念）；`0x58A7E0` 按 `N = floor(dist/step + 0.5)` 分 N 步增量偏移。

---

## 5. 行排样：逐零件路径（`FLOW_ROW.svg`）

```mermaid
flowchart TB
  A["0x134470 候选角度循环"] --> B["0x8BEFC0 + 0x5C4C50 构造候选集<br/>源自带元素 + 0° + 90°"]
  B --> C{"0x5C2E40 授权谓词通过？<br/>{tag, lo=角度, hi=角度}"}
  C -- 否 --> M["取下一个候选角度"]
  C -- 是 --> D["0x133DE0：0x5CEE50 角度→变换<br/>（tag≠0 → 镜像 {cos,+sin,sin,−cos}）"]
  D --> E["0x5D38C0 仿射变换 → 0x5CD800 包围盒<br/>0x133E67 取 20 × 高"]
  E --> F["Item 0x1333D0（0x90）→ 元素 0x136350（216 B）<br/>→ Squeezer 0x136B80 / 0x138A20"]
  F --> G["0x137FE0 排空（count=10000）<br/>→ 0x137A90 合并 → 0x13A360"]
  G --> H["0x13A360 / 0x1380D0 记忆化挤压代价<br/>阈值/sin − max(跨度)；1e-06 + 0.005 闸"]
  H --> I["0x137800 orderedAddElement（重置缓存）<br/>→ 0x136CB0 惰性分值"]
  I --> J{"分值 < 当前最优？"}
  J -- 是 --> K["记住该候选"]
  J -- 否 --> L{"还有候选？"}
  K --> L
  L -- 是 --> M
  M --> C
  L -- 否 --> N["返回最小分值的角度（全拒则 0）"]
```

**最终公式**（两端均已命名）：

```
score = Squeezer::cost(上一条记录的 node, 当前元素) − 环形面积 / cfg[+0x08]
```

细节见 [`../../re/findings_lp_use.md`](../../re/findings_lp_use.md) §21–§38：
元素（216 B）布局由 **15 条 `static_assert`** 锁进编译期；`0x5CC6A0` 是鞋带公式面积。

---

## 6. 后优化（`FLOW_POSTOP.svg`）

```mermaid
flowchart TB
  A["得到候选 nesting"] --> B["Compacter::Implementation v2 = 0x7F4140<br/>new(0x1E8) → 内核 0x252B60"]
  B --> C["网格步长 = min(宽,高)/10.0（常量 @0x9C2BB0）<br/>区间 (-f1,0,f1+f2) → 0x5CA780 / 0x5C6BE0"]
  C --> D["0x2664F0 枚举网格 → 逐个 move"]
  D --> E{"RotateCompact 0x678230<br/>1e-6 > param ？"}
  E -- 是 --> F["放弃该次旋转"]
  E -- 否 --> G["接受/拒绝（RotateLogger 0xA533D0 只是日志钩子）"]
  F --> G
  G --> H["核心 0x1B33B0（9910 B）"]
  H --> I["① postop.cpp 通用后处理（USE_POSTOP / postop_estimate）"]
  I --> J["② RenestInHoles 0x40720<br/>把零件塞回孔洞（容差 1e-6）"]
  J --> K["③ BL/BLF 稳定化 0x1E1BF0（packed bottom left）"]
  K --> L["规范化后的解（便于去重/比较）"]
```

**要点**：`[obj+0x10] = min(f1,f2)/10.0` 就是位移步长（tolerance/mesh）；
字符串证据含 `before_shake`/`shaker_`/`after_shake`（shake 抖动）、`Swap 180 begin`（180° 交换）。

---

## 7. LP 与定价层（`FLOW_LP.svg`）

```mermaid
flowchart TB
  A["压缩/后优化路径进入定价器<br/>CompactNester::Run 0xB13D0"] --> B["0xB0380 → 0x67460 → 0x1CD290<br/>→ 0x1CB100 → 0x1A6020 → 0x1A5B20"]
  B --> C["定价器工厂 0x4D64C0<br/>构造四个定价器"]
  C --> D{"哪个定价器？"}
  D -- Box --> E["主算法 0x7C9D90<br/>面积 (y1−y0)*(x1−x0) @0x7CB750"]
  D -- Hull --> F["slot2 0x7CA130 = [rdx+0x48]"]
  D -- Alpha --> G["slot2 0x7CA1B0 = [rdx+0x68]"]
  D -- Linear --> H["slot2 0x7CA370 = Σwᵢ·priceᵢ / Σwᵢ"]
  E --> I["PriceComputer 本体 0x7C4C70 / 0x7C4F90<br/>[obj+0x10] 尾调用 +0x28/+0x30/+0x38/+0x40"]
  F --> I
  G --> I
  H --> I
  I --> J["Lp::LinearProgram ← Coin::CoinLP<br/>vptr + ClpSimplex* @+8；构造 0x267760"]
  J --> K["addColumn/addRow 装配 0x7CA830（3778 B）"]
  K --> L["转发 thunk → ClpSimplex<br/>0x7CB700→[+0x248] · 0x7CB710→[+0x228] · 0x7CB740→[+0x230]"]
  L --> M["取回原/对偶目标值"]
```

**要点与限定**

* 这一层是**活的**：`struct` 的 vtable **地址点**被真实 `lea` 引用（如 `Prc::BoxPriceComputer` 地址点 `0xA3B0C0` 被 `0x4D9AE2`/`0x7CA0E2` 引用）。
* ⚠️ 方法学：按 vtable **头部**（`vtable+0`）搜索会得到"0 引用"的假结论 —— vptr 指向 **地址点（`vtable+16`）**。
* **是否构成"列生成"尚未证实**（`findings_lp.md` §7.3）；`Prc::BoostAlpha`/`SurfaceCoeffs`/`DimAlpha` 只有 RTTI 名、零指针引用 ⇒ 非多态数据结构。
* 本机未安装 COIN-OR Clp，`lcns` 用零依赖自研 `Simplex` 作 LP 后端（**已知差异，已如实记录**）。

---

## 8. 已证实 / 推断 / 未确认 的标注约定

| 标注 | 含义 |
|---|---|
| 已证实 | 有指令级或数据级证据（本文件的 RVA 均可复核） |
| 推断 | 结构已证明，但"等价于某教科书算法"是解释性判断（如 NFP 与 Minkowski 和） |
| 未确认 | 明确列出缺口与切入口（如 beam width 常量、point-in-polygon 例程、列生成是否成立） |

完整的未恢复项总清单见 [`../../re/REPORT.md`](../../re/REPORT.md) §10 与 §11–§12。
