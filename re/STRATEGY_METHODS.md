# `re/STRATEGY_METHODS.md` —— 策略类的**完整方法表**与 `Run` 工作量清单

由 `re/g_strategy_methods.py` 生成（goal round 10），数据来自 `re/vtables.json`（443 个类，**已恢复**）。

## 为什么这份表有用

虚表顺序是恢复出的数据，所以「**`类名` 的第 k 槽**」是**确定身份**（不是形状猜测）。
于是**行为保真最大的欠账 —— 15 个策略的 `Run` 体 —— 变成了带字节数的精确清单**：

| 类 | `Run` 槽 | 地址 | 字节 |
|---|---|---:|---:|
| `Multi::TilingNester` | #5 | `0x46940` | **16258** |
| `Multi::NestingNester` | #5 | `0x378e0` | **14374** |
| `Multi::RowNester` | #5 | `0x913e0` | **12380** |
| `Multi::MultiTorchNester` | #5 | `0x7bcc0` | **12232** |
| `Multi::CompactNester` | #5 | `0xb13d0` | **9393** |
| `Multi::NoFillNester` | #5 | `0x7f240` | **8440** |
| `Multi::RectangleNester` | #5 | `0x75fb0` | **5261** |
| `Multi::DatabaseNester` | #5 | `0x5b250` | **4495** |
| `Multi::FlipNester` | #5 | `0x4b870` | **3496** |
| `Multi::FilterNester` | #5 | `0xb3ae0` | **2254** |
| `Multi::LimitedNester` | #5 | `0x4ab40` | **1650** |

**合计 `Run` 体：90233 字节**（11 个类）。这些函数目前全部是 `Substituted`（跑的是本工程的替代搜索）。

`Pack::*Nester` 的 `Run` 不在槽 #5 而在**槽 #2**（它们的类更小，方法更少）。

## 各族的完整方法表

### 策略类（`Multi::*Nester`）

| 类 | 方法（槽: 地址(字节)） |
|---|---|
| **Multi::FlipNester** | #0 `0x687e10`(15B), #1 `0x687de0`(36B), #2 `0xb4440`(31B), #3 `0x4b1c0`(211B), #4 `0x4b2b0`(108B), #5 `0x4b870`(3496B) ←最大 |
| **Multi::FilterNester** | #0 `0x6937d0`(15B), #1 `0x6937a0`(36B), #2 `0xb43b0`(115B), #3 `0xb3920`(324B), #4 `0xb46f0`(894B), #5 `0xb3ae0`(2254B) ←最大 |
| **Multi::NoFillNester** | #0 `0x693830`(59B), #1 `0x6937e0`(67B), #2 `0xb4440`(31B), #3 `0x7eca0`(211B), #4 `0xb46f0`(894B), #5 `0x7f240`(8440B) ←最大 |
| **Multi::TilingNester** | #0 `0x456f0`(91B), #1 `0x45680`(99B), #2 `0xb4430`(4B), #3 `0x45750`(39B), #4 `0x45560`(82B), #5 `0x46940`(16258B) ←最大 |
| **Multi::CompactNester** | #0 `0x695e40`(15B), #1 `0x695e10`(36B), #2 `0xb3890`(115B), #3 `0xb0130`(309B), #4 `0xb46f0`(894B), #5 `0xb13d0`(9393B) ←最大 |
| **Multi::LimitedNester** | #0 `0x695e80`(40B), #1 `0x695e50`(48B), #2 `0xb4440`(31B), #3 `0x4a960`(211B), #4 `0x4a8d0`(140B), #5 `0x4ab40`(1650B) ←最大 |
| **Multi::NestingNester** | #0 `0x32ee0`(65B), #1 `0x32f30`(73B), #2 `0x3b110`(115B), #3 `0x33100`(2240B), #4 `0x32d90`(97B), #5 `0x378e0`(14374B) ←最大 |
| **Multi::DatabaseNester** | #0 `0x5b170`(77B), #1 `0x5b100`(85B), #2 `0xb4430`(4B), #3 `0x5b1c0`(37B), #4 `0x5b0f0`(6B), #5 `0x5b250`(4495B) ←最大 |
| **Multi::RectangleNester** | #0 `0x6d2e0`(185B), #1 `0x6d3a0`(193B), #2 `0xb4430`(4B), #3 `0x6c9b0`(41B), #4 `0x77780`(402B), #5 `0x75fb0`(5261B) ←最大 |
| **Multi::MultiTorchNester** | #0 `0x697260`(15B), #1 `0x697230`(36B), #2 `0xb4440`(31B), #3 `0x77c90`(211B), #4 `0x77c60`(20B), #5 `0x7bcc0`(12232B) ←最大 |
| **Multi::RowNester** | #0 `0x8eb40`(854B), #1 `0x8eea0`(865B), #2 `0xb4430`(4B), #3 `0x8cd20`(36B), #4 `0x8c010`(6B), #5 `0x913e0`(12380B) ←最大 |

### 打包类（`Pack::*Nester`）

| 类 | 方法（槽: 地址(字节)） |
|---|---|
| **Pack::BestNester** | #0 `0x681ee0`(157B), #1 `0x681e40`(149B), #2 `0x15e410`(316B) ←最大 |
| **Pack::KnapsackNester** | #0 `0x681f90`(1B), #1 `0x681f80`(5B), #2 `0x15dd70`(59B) ←最大 |
| **Pack::RecursiveNester** | #0 `0x683d80`(2119B), #1 `0x681fa0`(7633B) ←最大, #2 `0x165680`(125B) |

### 板材选择器（`Multi::*SheetSelector`）

| 类 | 方法（槽: 地址(字节)） |
|---|---|
| **Multi::AllSheetSelector** | #0 `0x6970f0`(1B), #1 `0x6970e0`(5B), #2 `0x7d2500`(217B) ←最大, #3 `0x7d25e0`(41B) |
| **Multi::NoMixSheetSelector** | #0 `0x69a5d0`(86B), #1 `0x69a580`(74B), #2 `0x7d2ed0`(1299B) ←最大, #3 `0x7d33f0`(193B) |
| **Multi::RandomSheetSelector** | #0 `0x69a680`(1B), #1 `0x69a670`(5B), #2 `0x7d36e0`(1316B) ←最大, #3 `0x7d3c10`(50B) |
| **Multi::LargestSheetSelector** | #0 `0x69a710`(1B), #1 `0x69a700`(5B), #2 `0x7d3c50`(136B) ←最大, #3 `0x7d3ce0`(44B) |

### 图案类（`Tiling::*`）

| 类 | 方法（槽: 地址(字节)） |
|---|---|
| **Tiling::BiModulePattern** | #0 `0x76db40`(1B), #1 `0x76db30`(5B), #2 `0x7e84f0`(34B), #3 `0x7e8100`(74B), #4 `0x7e8520`(757B), #5 `0x7e8150`(923B) ←最大, #6 `0x7e8840`(205B), #7 `0x7e8820`(26B) |
| **Tiling::MultiOrientedPartPattern** | #0 `0x76f9d0`(1B), #1 `0x76f9c0`(5B), #2 `0x7ebb90`(152B), #3 `0x7eb5e0`(939B) ←最大, #4 `0x7ebc30`(349B), #5 `0x7eb990`(510B), #6 `0x7ebdb0`(525B), #7 `0x7ebd90`(18B) |
| **Tiling::BoxMultiTiler** | #0 `0x76b3b0`(33B), #1 `0x76b380`(45B), #2 `0x7e7fc0`(278B), #3 `0x7e7e90`(293B) ←最大, #4 `0x7e7e80`(3B) |
| **Tiling::SqueezeMultiTiler** | #0 `0x76f0a0`(427B) ←最大, #1 `0x76ef00`(416B), #2 `0x7e91a0`(157B), #3 `0x7e9190`(13B), #4 `0x7e9180`(13B) |
| **Tiling::DensityEvaluator** | #0 `0x76e390`(1B), #1 `0x76e380`(5B), #2 `0x7e8910`(90B), #3 `0x4e7e50`(539B) ←最大 |
| **Tiling::ObliqueEvaluator** | #0 `0x76e3d0`(33B), #1 `0x76e3a0`(46B), #2 `0x7e8b30`(619B) ←最大, #3 `0x7e8970`(434B) |
| **Tiling::QuantityEvaluator** | #0 `0x76e410`(1B), #1 `0x76e400`(5B), #2 `0x7e8dd0`(390B) ←最大, #3 `0x7e8da0`(37B) |
| **Tiling::ReusableEvaluator** | #0 `0x76e430`(1B), #1 `0x76e420`(5B), #2 `0x7e8f60`(542B) ←最大, #3 `0x4e7e50`(539B) |
| **Tiling::MultitorchEvaluator** | #0 `0x76f260`(1B), #1 `0x76f250`(5B), #2 `0x7e9240`(798B) ←最大, #3 `0x4e7e50`(539B) |
| **Tiling::OldMultitorchEvaluator** | #0 `0x76f9b0`(1B), #1 `0x76f9a0`(5B), #2 `0x7eb320`(699B) ←最大, #3 `0x4e7e50`(539B) |
| **Tiling::UnlimitedDensityEvaluator** | #0 `0x76f9f0`(1B), #1 `0x76f9e0`(5B), #2 `0x7ebfc0`(578B) ←最大, #3 `0x4e7e50`(539B) |
| **Tiling::UnlimitedXDensityEvaluator** | #0 `0x76fa10`(1B), #1 `0x76fa00`(5B), #2 `0x7ec210`(590B) ←最大, #3 `0x4e7e50`(539B) |
| **Tiling::WarpCanceller** | #0 `0x76db20`(1B), #1 `0x76db10`(5B), #2 `0x7e80e0`(19B) ←最大 |
| **Tiling::BasicCandidater** | #0 `0x4f3600`(1B), #1 `0x4f3610`(5B), #2 `0x4f4600`(340B) ←最大 |
| **Tiling::PackerCache** | #0 `0x158be0`(895B), #1 `0x158f60`(919B) ←最大 |
| **Tiling::CompositePart** | #0 `0x76b420`(45B), #1 `0x76b3e0`(53B) ←最大 |
| **Tiling::Part** | #0 `0x4dafc0`(258B) ←最大, #1 `0x4daec0`(249B) |

### 描述/添加器（`Multi::Strategy*`）

| 类 | 方法（槽: 地址(字节)） |
|---|---|
| **Multi::StrategyDescriber** | #0 `0x69a450`(1B), #1 `0x69a440`(5B), #2 `0x7d2cc0`(341B) ←最大 |
| **Multi::StrategyBasicAdder** | #0 `0x69a660`(1B), #1 `0x69a650`(5B), #2 `0x7d3600`(214B) ←最大 |

## 由方法表读出的结构

* `Multi::*Nester` 一律是 6 槽：`#0`/`#1` 极小（1–91 B，构造/探测），`#2` 是 4–31 B 的身份访问器，
  `#3`/`#4` 是参数读写（几十到 2,240 B），**`#5` 才是 `Run`**（1.6 KB–16.3 KB）。
* `Pack::*Nester` 只有 3 槽，`#0`/`#1` 极小，`#2` 是 `Run`。
* 板材选择器（`Multi::*SheetSelector`）是 4 槽：`#0`/`#1` 极小，`#2` 是选择逻辑（136–1,316 B），`#3` 是谓词。
* **`Multi::AllSheetSelector`**（`0x7D2500`）在本轮的表里首次出现 —— 此前报告只有 `Largest`/`Random`/`NoMix` 三个。
* `Tiling::*` 的槽数不固定（`BiModulePattern` 8 槽、`MultiOrientedPartPattern` 8 槽、
  `BoxMultiTiler`/`SqueezeMultiTiler` 5 槽），最大的槽是图案生成/评估体。

