# lcns -- C++ 工程（基于 `libcns_dump_64.dll` 的逆向结果）

这个工程把逆向分析的结论落成了可编译、可运行的 C++ 代码。它分成两个**互相独立**的层次：

| 层 | 目标 | 用途 |
|---|---|---|
| **`lcns_api`** | 序号级动态加载 + 类型化封装 | 驱动一个真实的 `liblcns.dll`（Optalog CNS 引擎）。因为原 DLL **只按序号导出、名字表被清空**，绑定必须走序号 |
| **`lcns_geom` / `lcns_model` / `lcns_nest`** | 算法核心的**独立复现** | 不依赖任何 DLL 就能跑：精确定点几何、布尔运算、Minkowski 卷积 / 非凸 NFP、增量偏移 + 自交清理、多策略 + beam 搜索、pricing 评分、图案平铺、压缩、BL 收尾、共边检测、JSON/DXF/余料、LP + 列生成、云端 HTTP、许可层 |

> **为什么需要第二层**：被分析的样本 `libcns_dump_64.dll` 是一个**内存 dump**——
> IAT 里残留的是 dump 进程的绝对地址、`OriginalFirstThunk == 0`、且 UPX 尾部被人为改动。
> 实测把它交给 `LoadLibraryA` 会在加载器内部触发访问违例（`lcns_probe` 因此默认不加载）。
> 所以「调用原 DLL」这条路只有在拿到真正的 `liblcns.dll` 时才可用，而算法本身必须能独立跑。

---

## 目录结构

```
lcns/
├─ CMakeLists.txt
├─ include/lcns/
│  ├─ enums.hpp          逆向得到的枚举（Objective 8 值 / NestingOrigin 4 值 / Confidence）
│  ├─ api.hpp            DLL 访问层：句柄、导出表、PE 诊断、序号加载器、类型化 Api
│  ├─ detail/
│  │  ├─ api_table.inc   ← 由 tools/gen_api.py 从 re/exports_table.json 生成（168 行）
│  │  └─ api_typed.inc   类型化子集（签名标注为 INFERRED）
│  ├─ geom.hpp           精确定点几何内核（int64 + 128 位谓词、三角剖分、卷积、偏移）
│  ├─ boolean.hpp        多边形布尔运算（union/intersection/difference/xor）、normalize、
│  │                     regularize、minkowskiMulti、nfpMulti、inflateCleaned
│  ├─ model.hpp          问题/解模型（字段顺序照抄逆向结果）
│  ├─ nfp.hpp            NoFitMap + 缓存（25000 / 19,999,999 阈值）+ 非凸 NFP
│  ├─ nester.hpp         Nester 接口、策略族、beam、pricing、压缩、收尾、共边
│  ├─ tiling.hpp         BiModulePattern / MultiOrientedPartPattern / 7 个 Evaluator / 2 个 Tiler
│  ├─ engine.hpp         Supervisor/Engine 调度、观察者、SVG/HTML 报表
│  ├─ io.hpp             自研 JSON（值/解析/写出）+ 问题与解序列化 + DXF 导出 + 余料
│  ├─ lp.hpp             忠实镜像：Clp 包装层（LinearProgram / SimplexLinearProgram）+
│  │                     BuildAndSolveLp 的板材选择覆盖装配（buildAndSolveLp）
│  ├─ lp_column_generation.hpp  **非原库**：本项目扩展（MasterProblem / 列生成 / 定价器），
│  │                     故意不被 lp.hpp 包含，以免污染忠实层
│  ├─ row.hpp            Row::Distancer / Squeezer：成本 0x1380D0 + 地址键记忆化 0x13A360
│  ├─ lp_nesting.hpp     用真实排样作为定价子问题
│  ├─ cloud.hpp          HTTP 客户端（Winsock/POSIX）+ CloudEngine 云端流程
│  └─ licensing.hpp      PCId 机器指纹 + HASP/Sentinel LDK 动态封装
├─ src/                  api geom boolean model nfp row nester engine tiling io lp
│                        lp_column_generation lp_nesting cloud licensing（共 15 个 .cpp）
├─ apps/
│  ├─ demo/main.cpp      nest_demo：跑真实排样，输出 SVG / HTML / DXF / JSON / 余料
│  └─ probe/main.cpp     lcns_probe：诊断 + 列出 168 个导出 + 可选动态加载
├─ tests/                15 个单元测试（见下）
├─ tools/
│  ├─ gen_api.py         从 re/exports_table.json 生成导出表（可重复）
│  ├─ gen_arch.py        生成 docs/ARCHITECTURE.svg 与 docs/ROW_PATH.svg
│  ├─ gen_flow.py        生成 7 张算法流程图 docs/FLOW_*.svg
│  ├─ check_arch.py      校验全部 SVG 布局（不越界/不重叠/连线不穿无关框）
│  ├─ check_recovery.py  强制「代码标记集合 == 登记表集合」并生成 RECOVERY_STATUS.md
│  └─ patch_ns.py        一次性命名空间迁移脚本
└─ docs/
   ├─ ARCHITECTURE.md   架构图与模块说明（分层/依赖/路径/布局/验证）
   ├─ ARCHITECTURE.svg  分层架构图（可直接打开）
   ├─ ROW_PATH.svg      逐零件路径的完整调用链
   ├─ ALGORITHMS.md     主要算法流程图（图索引 + Mermaid + 要点）
   ├─ RECOVERY_STATUS.md 逆向状态总表（**由 include/lcns/recovery.hpp 生成**）
   ├─ FLOW_MAIN.svg     主流程：建模→分派→求解→取解
   ├─ FLOW_SEARCH.svg   搜索：多策略并发 + 级联预算
   ├─ FLOW_NESTER.svg   Nester::Run 内部
   ├─ FLOW_NFP.svg      No-Fit Polygon（边界 Convolution）
   ├─ FLOW_ROW.svg      行排样：逐零件路径
   ├─ FLOW_POSTOP.svg   后优化：Compaction + 收尾三连
   ├─ FLOW_LP.svg       LP 与定价层
   └─ MAPPING.md        逆向结论 → 代码位置 的逐条映射
```

## 构建

已用 **CLion 2025.3.3 自带的 CMake 4.1.2 + Ninja 1.12.1 + MinGW GCC 13.1.0** 全新配置、编译并跑通全部测试：**0 warning / 0 error / 15 of 15 tests passed**。

### 方式一：CLion
`File → Open` 选择本目录（含 `CMakeLists.txt`），CLion 会自动识别自带的 MinGW 工具链并生成。

### 方式二：命令行（Windows + CLion 自带工具链）
```powershell
$c = 'C:\Program Files\JetBrains\CLion 2025.3.3'
$env:PATH = "$c\bin\mingw\bin;$env:PATH"
& "$c\bin\cmake\win\x64\bin\cmake.exe" -S . -B build -G Ninja `
    -DCMAKE_BUILD_TYPE=RelWithDebInfo `
    -DCMAKE_MAKE_PROGRAM="$c/bin/ninja/win/x64/ninja.exe" `
    -DCMAKE_CXX_COMPILER="$c/bin/mingw/bin/g++.exe"
& "$c\bin\cmake\win\x64\bin\cmake.exe" --build build
& "$c\bin\cmake\win\x64\bin\ctest.exe" --test-dir build --output-on-failure
```

### CMake 选项
| 选项 | 默认 | 说明 |
|---|---|---|
| `LCNS_BUILD_TESTS` | ON | 构建 15 个测试 |
| `LCNS_BUILD_APPS` | ON | 构建 `nest_demo` / `lcns_probe` |
| `LCNS_WERROR` | OFF | 警告视为错误 |

## 运行

```powershell
# 独立复现：排样 1 张 1000x500 板 + 11 个零件（矩形/圆/带孔框），
# 输出 solution.svg / solution.html / solution.dxf / problem.json / solution.json
.\build\nest_demo.exe .

# 诊断样本 + 列出逆向得到的 168 个导出（按序号）
.\build\lcns_probe.exe ..\libcns_dump_64.dll
.\build\lcns_probe.exe ..\libcns_dump_64.dll --all      # 显示全部
.\build\lcns_probe.exe path\to\real\liblcns.dll --load  # 真实 DLL 才建议加 --load
```

`nest_demo` 实测输出（MinGW GCC 13.1，Release + 调试信息）：

```
problem: 1 sheet(s), 4 part kind(s), 11 instances
total part area 140154.9, sheet area 500000.0 (lower bound fill 28.0 %)
engine: start
  observer v4 NewIntermediateSolutionFound: improved to 28.03 %
  observer v5 NewNestingFound: 11 parts
engine: stop
nested parts   : 11 of 11 requested
fill ratio     : 28.03 %
  nesting 0: sheet 0, 11 parts, bbox 918.7 x 375.3
wrote ./solution.svg
wrote ./solution.html
wrote ./solution.dxf (R12, layers SHEET/PART/HOLES)
wrote ./problem.json and ./solution.json
problem round trip: 4 part kind(s), 1 sheet(s)
offcuts        : 3 remnant ring set(s), 359845.1 of recoverable surface
  offcut 0: 1000.0 x 500.0 envelope, net area 339845.1, 11 hole(s)
  offcut 1: 100.0 x 100.0 envelope, net area 10000.0, 0 hole(s)
  offcut 2: 100.0 x 100.0 envelope, net area 10000.0, 0 hole(s)
```

（余料面积自洽：`339845.1 + 10000 + 10000 = 359845.1 = 500000 − 140154.9`。
两个 100×100 的"岛"是框件内孔留下的可用余料 —— 框被切走后孔内材料仍留在板上。）

## 测试

`ctest` 全部通过（**15/15**）：

| 测试 | 覆盖内容 |
|---|---|
| `test_exact` | 128 位乘法的**符号/边界**、定点缩放 1e10、`orient2d`、象限分类与 CCW 遍历次序 |
| `test_conv` | 环的面积/周长/包围盒、点在环内（精确绕数）、共线点清理、凸包、**Minkowski 卷积**（两个正方形 → 精确包围盒与面积）、**NFP**、共线重叠谓词、WKT |
| `test_boolean` | **布尔并/交/差/异或**（重叠/相接/相同/相离）、包含、带孔差集、L 形 6 角、空操作数、`uniteSelf`、`normalize` 的奇偶嵌套、`regularize` 自交蝴蝶结（在**重复节点处拆成两个简单环**）、**带孔 Minkowski 和**（含容斥）、**非凸 NFP**（L 形，切口恰好被排除：171 = 196 − 25）、`inflateCleaned` 凹形偏移不自交、**回环分类**（`convolveRingLoops` 的凸情形与等价分解路径逐项对照、退化回环丢弃、`{}`/`[]` 空容器类型不变）、**Minkowski 和的包围盒恒等式** `bbox(A+B)=[minA+minB, maxA+maxB]`（凸/非凸/带孔/星形全过） |
| `test_offset` | 单步/多步增量偏移（`N = floor(dist/step+0.5)`）、负向收缩、三角形、**外轮廓 +gap / 内孔 −gap**、keep-out 距离 |
| `test_nofit` | `NoFitMap` 缓存命中/未命中、`maximumComplexity` 语义、缓存阈值常量、`NoFitNesting` 记录与禁止区（**真并集**） |
| `test_nester` | `mt19937` 确定性、`TimeCanceller` 的 `elapsed/limit > 1.0`、pricing 四种定价器、`cascade` 序列、`StrategyAdder` 映射、**端到端排样（无重叠）**、放置校验、压缩/BL 不破坏合法性、**共边检测**、观察者回调、SVG/HTML |
| `test_model` | 逆向枚举取值、**`Polygon` 布局断言（inners 必须在 +0x18）**、图元构造、旋转/镜像、属性表顺序与预设切换、汇总统计 |
| `test_tiling` | `BiModulePattern` 棋盘交错与间距/预算、`MultiOrientedPartPattern` 定向轮转、7 个 Evaluator 的数值语义、`BoxMultiTiler` 择优、`SqueezeMultiTiler` 边界收拢、`PackerCache`、**TilingNester 端到端** |
| `test_io` | JSON 写出（紧凑/美化）、转义与 `\uXXXX`、嵌套/负数/错误输入、**问题往返**（含逆向得到的全部键）、**解往返**、**DXF**（AC1009 / 图层 / POLYLINE-VERTEX-SEQEND 计数）、**余料**面积与阈值过滤 |
| `test_lp` | 单纯形：单行/两行/等式、负右端、`Infeasible`、`Unbounded`、**对偶价**、新列 reduced cost；列生成：切板下料 LP 界 4/3、启发式定价的改进、无初始列时**明确报错而不空转**、**以真实排样为定价子问题** |
| `test_cloud` | 服务器列表解析、GET/PUT 报文**逐字节**形状、UUIDv4 版本/变体位与唯一性、`/sol/` → `end` → `/best_sol/` 流程、中间解取最优、PUT 失败回退本地引擎、坏载荷拒绝 |
| `test_licensing` | **PCId 混合公式**（含手算值 `0xABADCAFD`）、机器指纹自洽、`pcidString` 缓存、无加密狗时 HASP/Sentinel 全部安全失败、许可门（9=通过 / 11=拒绝）、key 列表、vendor code 只给说明不外带 |
| `test_row` | `0x1380D0` 的成本公式（含"两行必须平行"与 `0.005` 逐元素对齐两道闸、零长度、各 bail 分支）、`0x5C22D0` 定点角度、`0x13C380` 的行集→挤压器构造（**赋值不是取最大**、标志置位归 0、差值不取绝对值） |
| `test_recovered` | **验收测试**：逐条断言工程常量 == 从二进制读出的数值，每行注明 RVA（`kScale@0x9AD708`、`kFullTurnFixedDegrees@0x34630B8A000`、90/180/270 度魔数、`kSqueezeAlignmentTolerance@0x9BCFD8`、`kSqueezeParallelTolerance@0x9BCFC0`、`kRowCoreAt0x08/0x18/0x20@0x9B1A40/48/50`、`kBoostAlpha@0x9D9C08`、`kDimAlpha@0x9D9BE8`、`kSnapTolerance`、`NoFitMap::kDefaultMaxComplexity@0x61A8`）——**改常量而不重读二进制即会失败** |

测试期间发现并修掉的**真实缺陷**（可作为"测试有效"的证据）：

1. `Int128::toDouble()` 在 `hi < 0` 且数值较小时发生**灾难性抵消**（`-35` 变成 `0`）→ 改为先取负再转换；
2. `area()` 忘记除以 `kScale²`，导致面积放大 1e20 倍；
3. 象限排序用了 `1,2,3,4`，而逆时针从 0° 出发的遍历次序是 **`1 → 4 → 3 → 2`** → 卷积结果被旋转到错误位置；
4. `NoFitNesting::forbiddenRegion` 用了 `reverse()` 而不是**取负**（`A ⊕ −B`），导致禁止区偏移错误；
5. 卷积的极角比较把**平行边按长度**排序，破坏了边合并的遍历次序 → 结果错位。改为相等方向视为相等（稳定排序保序），并把锚点从"最低顶点之和"改为**包围盒最小值之和** `minA + minB`（Minkowski 和的充要锚点）；
6. `minkowskiMulti` 与 `nfpMulti` 共用一个实现，导致"和"被算成了"差" → 拆成 `reflect` 参数；
7. 边合并只对**凸**输入精确 → 引入耳切三角剖分（`geom::triangulate`），非凸环先分解再逐对卷积求和；
8. 自交环的边界游走会在**夹点**处重复访问同一节点（蝴蝶结/点接触）→ 新增 `splitAtRepeatedNodes` 拆成多个简单环；
9. `Simplex` 的 `isArtificial` 只随 `pushColumn` 增长，没有为结构列预留 → 按列索引访问**越界**，整个两阶段逻辑失效（改 `reserve()` 语义 + 预置 `isArtificial`）；
10. 阶段二的 big-M 在退化行上数值不稳 → 改为**显式把零值人工变量转出基**，并在阶段二禁止人工变量再入基；
11. 卷积回环游走的**点积用 int64 直接相乘溢出**（定点坐标 ~1e10，乘积 ~1e20）→ 平行边判定失效、边序错乱。改用 128 位 `add128/mul64` 求符号（`dotSign`）；
12. JSON 解析 `{}` 返回 **null** 而不是空对象（`Value obj;` 默认是 Null）→ 引入 `Value::array()` / `Value::object()` 工厂并补回归测试。

## 逆向结论 → 代码 的对应关系

完整逐条映射见 [`docs/MAPPING.md`](docs/MAPPING.md)。要点：

| 逆向证据 | 代码位置 |
|---|---|
| 定点缩放 `1e10`（`0x9AD708`） | `geom::kScale` |
| 128 位叉积谓词（`0x58E450`） | `geom::Int128` / `mul64` / `orient2d` |
| 象限分类 `1=(dx>0,dy>0) 2=(dx>0,dy≤0) 3=(dx≤0,dy<0) 4=其余` | `geom::quadrantOf` + `quadrantRank` |
| `Polygon{external@+0, inners@+0x18}`，48 字节 | `geom::Polygon`（`test_model` 里断言偏移） |
| `NoFitGetNumberOfExternalPolygons` 做 `len/48` | `geom::Polygon` 尺寸 + `NFPEntry::polygonCount()` |
| `NoFitContext` = 240 B，缓存 `+0x78`/`+0xA8`，`+0xD8` 阈值 19,999,999，`+0xE8` 默认 25000 | `NoFitMap` |
| 卷积 `..\exact\convolution.cpp::ConvolutionRaw`（`0x596F20`）核心 `0x596100` | `geom::convolveBoundaries` / `minkowskiSum` / `nfp` |
| 偏移 `N = floor(dist/step+0.5)`，`×1e-6` 容差 | `geom::offsetRing` / `OffsetParams` |
| `AddInflatedToolPathToPart`（`0x12C60`）外环 `+gap`、内孔 `−gap`（`btc` 翻符号） | `geom::inflatePolygon` + `boolean::inflateCleaned` + `prepareInflatedShapes` |
| `Multi::Nester` 6 虚槽（dtor/dtor/Name/Prepare/Estimate/Run） | `lcns::Nester` |
| 策略族与 `StrategyAdder::Add`（`0x2C4D0`）的 mode→类 映射 | `makeStrategy()` / `FlipNester` … `MultiTorchNester` |
| `TerminalNode::eval()= [rcx+0x48]`、`SplitNode::eval()= [rcx+0x50]` | `BeamNode::value48` / `value50` / `eval()` |
| `"Preparing tree for beam "`（`0x22CCA0`） | `NestingNester::run` 写日志 |
| 级联 `n → 2 → (n+1)/2 → n−1`（`0x2CCF0`） | `StrategyDescriber::cascade()` |
| 总取消闸 `elapsed / Problem[+0x408] > 1.0`（`0x30030`） | `TimeCanceller::probeCancel()` |
| 压缩网格 `min(w,h)/10`（`10.0 @0x9C2BB0`）、`RotateCompact` 的 `1e-6` 早退 | `compactNesting` |
| `"Finalize : Parts renested in holes"` / `"… packed bottom left"` | `renestInHoles` / `packedBottomLeft` |
| `Prc::BoxSurface/HullSurface/AlphaSurface/LinearCombination` | `BoxSurfacePrice` 等 |
| `Tiling::BiModulePattern`（vtbl 0xA3D1C0）、`Tiling::MultiOrientedPartPattern`（0xA3D370） | `tiling::BiModulePattern` / `MultiOrientedPartPattern` |
| `Tiling::Density/UnlimitedDensity/UnlimitedXDensity/Quantity/Reusable/Oblique/Multitorch Evaluator` | `tiling::*Evaluator` |
| `Tiling::BoxMultiTiler` / `Tiling::SqueezeMultiTiler` / `Tiling::PackerCache` | `tiling::BoxMultiTiler` / `SqueezeMultiTiler` / `PackerCache` |
| `LoadSegment` 字段 + `number_of_common_cut` 等统计键 | `CommonCutSegment` / `CommonCutEvaluation` / `detectCommonCuts` |
| `Objective` / `NestingOrigin` 枚举（dump fn `0x511080`） | `lcns::Objective` / `lcns::NestingOrigin` |
| `CommonCutProperties` / `MultitorchProperties` / `MultitorchInfo` 字段序 | `model.hpp` 中同名结构 |
| `SaveProblem`（`0x5070E0`）的 JSON 键、`source_version` = `5.0 - 68e2d90e72b4 5449` | `saveProblem` / `loadProblem`（`kSourceVersion`） |
| `UnSerializeSolution`（`0x1C5F0`）、`CreateProblem`（`0x1EE50`） | `saveSolution` / `loadSolution` |
| `GenerateDxfNesting`（`0xBF70`）→ `DrawDxf` | `toDxf` / `writeDxf`（R12，SHEET/PART/HOLES 三层） |
| `SetOffcutEvaluation` + 余料 SVG 图层 | `offcuts` |
| `Lp::LinearProgram` ← `Coin::CoinLP`（ClpSimplex 1.15.3 静态链接） | `lp::LinearProgram` / `lp::SimplexLinearProgram` / `lp::buildAndSolveLp` |
| `BuildAndSolveLp`（`0x7D7200`，`..\multi\database.cpp`）—— Clp 实际在解**板材选择集合覆盖 LP**：`min Σ price(s)·x_s`，`s.t. 每个零件 Σ_s count(s,p)·x_s ≥ demand(p)` | `lp::buildAndSolveLp` + `lp::SheetContent`（逐句翻译，含单位系数松弛列） |
| `Coin::CoinLP` 13 个虚槽（重置 / 追加列 / 追加行 / 提交求解 / 转发取解） | `lp::LinearProgram` 的虚接口 |
| **OR-Tools 全文件 0 命中**（13 个标记）；求解器是 COIN-OR Clp | 文档记录于 `re/findings_lp_use.md` |
| `Prc::PriceComputer` 家族可从 `Multi::CompactNester::Run` 到达（`0x4D64C0`） | `lp::NestingPatternPricer`（以真实排样作定价） |
| `Engine::CloudEngine::Run`（`0x26A60`）、PUT `/pb/`、GET `/sol/`|`/best_sol/`、body == `"end"` 选 best | `cloud::CloudEngine` |
| 服务器 `cns1.optalog.com;cns2.optalog.com`、端口 `0x50`、选项 `cns_force_cloud` | `cloud::Config` 默认值 |
| 超时 `120.0`（`0x9AE9B0`）、总期限 `2t + 30`（`0x9AE9B8`）、轮询 20 s | `Config::putTimeoutSeconds` / `overallSlackSeconds` / `pollWindowSeconds` |
| 请求构造 `0x6DA1F0`(GET) / `0x6DBD40`(PUT)、响应解析 `0x6DAB80` / `0x6DC480` | `buildGetRequest` / `buildPutRequest` / `parseResponse` |
| `GetPCId`（`0xC010`）+ 混合式（`0x24290`）`((mac*vol)+(mac>>16)+mac+vol) ^ 0xABADCAFE` | `licensing::computePcid` |
| `IP_ADAPTER_INFO.Address @+0x198`、`GetAdaptersInfo` 对 `0x6F` 重试、`GetVolumeInformationA("c:\\")` | `licensing::computeMachineId` |
| `hasp_login/logout/read/write`、file id `0xFFF4`、128 字节空格填充 | `licensing::HasLayer` |
| `sntl_admin_context_new/get/delete` | `licensing::SentinelAdmin` |
| 许可门写 `context+0x4C`：9 = 通过，11/17 = 拒绝 | `licensing::checkKey` |
| `DrawSVG` 家族 + `cns_solution.css` + `__marks__` 图层 | `toSvg` / `toHtmlReport` |
| `GetMajorVersion` / `GetBuildVersion` / `GetBuildDate` / `GetPCId` | `dll::Api` 中的类型化条目 |

## 外部基准（ESICUP / OR-Datasets）

`lcns` 可以在公开的二维异形下料基准上跑，并与文献最优值对比：

```powershell
# MinGW 运行时必须在 PATH 上，否则 nest_eval.exe 会报 0xC0000135
$env:PATH = 'C:\Program Files\JetBrains\CLion 2025.3.3\bin\mingw\bin;' + $env:PATH

# 单个实例：ESICUP 统一 JSON -> problem.json -> 求解 -> 统计
python tools\esicup_to_lcns.py --in ..\datasets\or-datasets\or\Cutting-and-Packing\2D-Irregular\Datasets\SWIM\json\swim.json `
       --out ..\datasets\work\swim.json --meta ..\datasets\work\swim.meta.json
build\nest_eval.exe ..\datasets\work\swim.json --time 30 --seed 0 --out ..\datasets\work

# 全量 13 个经典实例 + 与文献对比表
python tools\run_benchmarks.py --time 30 --seeds 1
```

* 数据集与出处/许可：[`../datasets/README.md`](../datasets/README.md)
* 结果对比表：[`../datasets/RESULTS.md`](../datasets/RESULTS.md)（原始统计 `../datasets/results.csv`）
* `nest_eval` 开关：`--time/--seed/--iterations/--threads/--beam/--angles/--out/--csv/--quiet`，
  以及用于二分定位的 `--no-renest/--no-compact/--no-bl`。

**结论摘要**：密度定义与文献一致（`rho = Σ已放置面积 / (固定边 × 实际长度)`），
lcns 当前得 30.0–42.6%，文献 68.6–92.6%。4 倍预算对照实验显示密度**逐位不变**，
即差距来自"放完即止、缺乏迭代改进"，**不是**时间预算问题 —— 详见 datasets/README §7。

## 逆向状态标记：**没逆向出来的地方，代码里都有标记**

本工程混着四种不同性质的代码，光看源码分不出来，所以每处都打上**可 grep 的 C++ 标记**，
并与一张机器可读的登记表 [`include/lcns/recovery.hpp`](include/lcns/recovery.hpp) 逐条对应：

| 状态宏 | 含义 |
|---|---|
| `LCNS_RECOVERED(id)` | **逐指令忠实**：每个常量/字段偏移都能追到 RVA，且被 `test_recovered` 与 `re/g_acceptance.py` 检查 |
| `LCNS_STRUCTURAL(id)` | **结构已恢复**：类、调用图、算法骨架与关键常量都逆出来了，但这里的实现是**重写** |
| `LCNS_SUBSTITUTED(id)` | **替代实现**：原库用的东西在本环境不可用（如 COIN-OR Clp），或启发式的**常数没有逆出来** |
| `LCNS_NOT_REVERSED(id)` | **未逆向**：DLL 里确实有这个功能，但我们**没有译出**；这里要么是壳、要么缺失 |
| `LCNS_NOT_IN_BINARY(id)` | **非原库**：本工程自己的扩展（如列生成机具） |

宏展开为 `static_assert(true, "...")`：**零开销**、在文件作用域/类体/函数体内都合法、
`grep -rn "LCNS_NOT_REVERSED" src include` 可枚举，也在编译器诊断里可见。

```powershell
python tools\check_recovery.py     # 强制：代码标记集合 == 登记表集合；且带具体 RVA 的缺口必须在 re/ 文档中出现
python tools\check_recovery.py     # 同时生成 docs/RECOVERY_STATUS.md
```

**当前盘点（58 条）**：已恢复 6、结构已恢复 13、**替代实现 26**、**未逆向 12**、非原库 1。
登记表的条数被 `test_recovered.cpp` 断言住 —— 删掉一条缺口（= 悄悄假装它已恢复）会让测试失败。

## 已知限制（诚实说明）

1. **类型化 API 的签名是推断的**。二进制里没有符号与调试信息，`Api` 里每个函数的参数表来自
   调用点寄存器分析 + 语义证据，`include/lcns/detail/api_typed.inc` 中逐条标注 `// inferred`。
   真正权威的是 `Library::byName()` / `byOrdinal()` 的原始指针层。
2. **布尔运算与 NFP 是自研实现，不是原库的反编译**。原库的 `..\exact\boolean.cpp` 与
   `NoFitMapWithoutHoles` 的非凸路径没有被逐指令还原；本工程用"边相交分裂 + 双侧包含性判定 +
   最顺时针转向缝合 + 偶奇嵌套归一化"实现等价语义，并在测试里验证了面积/包围盒/切口等可判定量。
   卷积有**两条独立实现**，互相交叉验证：
   * `geom::convolveRingLoops` + `classifyConvolutionLoops`：**照搬逆向契约**（两边列表各自从最低
     顶点进入、按角度循环归并、重复顶点处闭环/裂环、再按嵌套奇偶分类）。它**在两个操作数都凸时精确**；
     非凸环的边序列不是角度单调的（每个凹顶点都会折返），此时归并假设不成立——原库那 10 KB 的通用
     非凸卷积正是逆向**没有**恢复的部分。
   * 凸分解路径（`minkowskiMultiDecomposed`）：耳切三角剖分后逐对凸卷积求并，是通用的非凸 Minkowski
     和标准做法，`test_boolean` 用**包围盒恒等式** `bbox(A+B)=[minA+minB, maxA+maxB]` 在凸/非凸/
     带孔/星形输入上验证它。
   仍需注意：
   * 组合爆炸有闸门：`boolean::kMaxConvPairs = 256`，超过则退化为凸包（有损，已在代码标注）；
   * 容差为量化吸附 `kSnapTolerance = 10000`（= 1e-6 定点单位）。
3. **beam width 常量未从二进制中恢复**（报告 §7.2 已说明），因此它是 `BeamParams::width` 参数，
   默认 8。
4. **列生成仍是未证实；但 LP 的用途已经查清。** 原库确有 `Lp::LinearProgram ← Coin::CoinLP`
   （静态链接 **COIN-OR Clp 1.15.3**，经 `OsiClpSolverInterface`；**全文件 OR-Tools 0 命中**），
   且它**被真实使用**：驱动函数是 `BuildAndSolveLp`（`0x7D7200`，源文件 `..\multi\database.cpp`，
   断言 `biggest_sheet->price()` 在第 450 行），它解的是一条**板材选择集合覆盖 LP**
   ——`min Σ_sheet price(s)·x_s`，`s.t.` 每个零件一条 `Σ_sheet count(s,p)·x_s ≥ demand(p)`——
   **不是 Dantzig–Wolfe 主问题**；解出来后被 slot 10 取回并回映到板材上。
   原库的"定价"是 `Prc::LinearCombinationPricer` 对 **Box + Hull + Alpha×2 四个几何面量**
   按权重加权平均（**没有"默认变体"**，四个都被构造，权重取 5 个 double 的系数结构），
   由 `..\nesting\algos\old_beam.cpp` 的 beam 搜索调用。
   ⇒ 工程里 `MasterProblem` / `columnGeneration` / `GreedyPricer` / `NestingPatternPricer`
   **在 DLL 中没有对应物**，已全部隔离进
   [`lp_column_generation.hpp`](lcns/include/lcns/lp_column_generation.hpp)（文件头明确声明
   "NOT PART OF THE BINARY"），`lp.hpp` 不含它。仍需注意：`lp::GreedyPricer` 只是启发式，
   可能找不到存在的负 reduced cost 列而**提前报"最优"**（`test_lp` 只断言改进而不断言达到 LP 下界）。
5. **HASP Vendor Code 故意不外带**。`0x9A2080` 处那 984 字符的 base64（解码 736 字节，
   熵 7.688）是产品的厂商码，本工程只提供机制（`HasLayer::login(featureId, vendorCode)`），
   不内置该常量；`licensing::vendorCodeHint()` 说明了它的位置与用法。
6. **云端路径在测试里用 `FakeHttpClient`**。真实 socket 实现（Winsock / POSIX）已写出并参与编译，
   但 CI 不做外网访问；未联网或服务器不可达时 `CloudEngine::runWithFallback` 会回退本地引擎
   （对应原库 `LaunchComputation` / `LaunchLocalComputation` 互相调用的行为）。
7. 原库的一项行为无法对齐：板存在**两套字段表示**（报告 §7.4 末），本工程按各 `Set*` 的落点建模。
8. **行排样核心有三项明确声明为"用现有方法不可恢复"**（`re/REPORT.md` §10.3 是全报告的
   统一收尾清单，含**原因与影响评估**），它们**没有被近似值顶替**，只是留在缺口清单里：
   - `RowNestCore` 的 `+0x28`/`+0x30`/`+0x38`（来源字段 `Pb+0x198`/`+0x1B8`/`+0x1C0`）
     **是否被别处读取无法判定**：数据库翻译单元内 ≤40 字节的访问器里只有
     `Pb+0x170`/`Pb+0x1A0` 两个 getter；全局按偏移扫描会与 130–220 个**无关类型**的同偏移
     访问混淆。已知确切事实仅两条：它们由两个配置块写入，且在 `0x6AABC0` 与 `0x13C380`
     内都没有读者。工程里建模为 `pipeAt198` / `commonCutAt1B8` / `commonCutAt1C0`
     三个字段，**未接任何算法**。
   - `Item`（0x90 字节）的 `+0x20…+0x88` 字段语义、`Elem48`/`Elem16` 的几何含义未定
     （偏移、步长与三层嵌套关系已证实）。
   - `0x133DE0`（`0x134470` 的逐零件代价函数）与 `0x5C2E40`（谓词）未译，
     因此 §19.1 那条"候选取最小"的算法**未并入工程**。
