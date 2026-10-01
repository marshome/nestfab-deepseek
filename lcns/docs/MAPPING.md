# 逆向结论 → 代码位置 映射表

本文件的每一条都来自 `../re/` 下的实测结论（`REPORT.md`、`exports_table.json`、
`findings_*.md`、`out_29.txt`）。**RVA 均指 `libcns_dump_64.dll` 文件内 RVA**。

---

## 1. 导出层（`lcns::dll`，`include/lcns/api.hpp` + `src/api.cpp`）

| 逆向结论 | 证据 | 代码 |
|---|---|---|
| 导出名 `liblcns.dll`，`NumberOfFunctions=343`、**`NumberOfNames=0`** | 导出目录 `0xB424D8` | `dll::diagnoseFile()` 报告 `numberOfNames`；绑定走序号 |
| 336 个非零项 → **168 个唯一函数**，每个占**两个相邻序号** | 地址表成对重复 | `ExportInfo::ordinal0/ordinal1`；`byName()` 先试 `ordinal0` 再试 `ordinal1` |
| 序号空洞 `63,64 / 75 / 106-109` | 地址表 RVA=0 | `ordinal1 == -1` 的分支 |
| 每个函数的名字 = **第一次调用 `dbg::symlog` 时传入的标签字面量** | `0x64AEA0` / `0x64ABF0` / `0x64D9C0` | `ExportInfo::label`（原样保留，含 `//` 前缀） |
| 两种标签风格：`"GetSheet"` 与 `"// AddCircularHoleToPart"` | `0x13800` 等 | `gen_api.py` 去掉前导 `//` 作为 `name`，`label` 保留原文 |
| `CNS_` 前缀名是**断言文本里的公开 C 别名** | `0xB600` 的 `"CNS_GetSheet"` + `"cns.cpp"` | `ExportInfo::cAlias` |
| 名字恢复率 162/168，另 6 个靠行为反推 | `re/exports_table.json` | `tools/gen_api.py` 的 `FALLBACK_NAMES`，`confidence = 1` |
| IAT 是 dump 进程的绝对地址、`OriginalFirstThunk == 0` | `0xB42328` 处的 `0x7FF9…` | `Library::load()` 失败时附带 `diagnoseFile()` 的结论 |
| 提交给 `LoadLibraryA` 会在加载器内崩 | 实测 `0xC0000005` | `lcns_probe` 默认不加载，需显式 `--load` |
| `Objective` 8 个取值、`NestingOrigin` 4 个取值 | dump 函数 `0x511080` | `lcns/enums.hpp` |

## 2. 几何内核（`lcns::geom`，`include/lcns/geom.hpp` + `src/geom.cpp`）

| 逆向结论 | 证据 | 代码 |
|---|---|---|
| **没有 Clipper / boost::geometry / CGAL / Eigen** | 全串扫描 0 命中（`out_29.txt`） | 全部自研，无第三方几何依赖 |
| 双内核：`..\exact\*`（int64 定点）+ `..\geom\*`（double） | 源码路径串 | `geom::fixed_t` / `geom::Point` 两套表示与互转 |
| 长度定标 **1e10** | double `@0x9AD708` | `geom::kScale` / `kScaleI` |
| `round(v*1e10)`（编译器写法 `v/360*3.6e12+0.5`） | `@0x9AC838` / `0x9AC830` | `geom::toFixed` |
| 叉积/行列式用 **128 位**（`imul/mul + adc/sbb`） | `0x58E450` | `geom::Int128` / `mul64` / `add128` / `sub128` |
| `Polygon` = 48 B：`external @+0x00`、`inners @+0x18` | `NoFitGetNumberOfExternalPolygons` 除 48；`GetRing` 的 `lea rax,[rcx+0x18]` | `geom::Polygon`（`test_model` 断言偏移 == 0x18） |
| 断言 `external_number < map->result.size()`、`(internal_number-1) < inners.size()` | `cns_no_fit.cpp:483/490` | `NFPEntry::polygonCount()` / `NoFitGetNumberOfInternalHoles` 的类型化声明 |
| `..\exact\path.cpp::RemoveAlignedCollinearPoints` | `0x57FDA0` | `geom::removeAlignedCollinearPoints` |
| 点在多边形内用精确谓词（**原库位置未定位**） | 报告 §7.1「未确认」 | `geom::pointInRing`（绕数 + `orient2d`），文档中标注为常规实现 |
| WKT 序列化 `POLYGON/MULTIPOLYGON/LINESTRING` | 字符串表 | `geom::toWkt` |

## 3. 卷积 / NFP（`src/geom.cpp` 的 `convolveBoundaries`，`lcns::NoFitMap`）

| 逆向结论 | 证据 | 代码 |
|---|---|---|
| `..\exact\convolution.cpp::ConvolutionRaw`（`0x596F20`）核心 `0x596100` | 断言 `max_size >= union(size1,size2)` 行 331；`__func__` | `geom::convolveBoundaries` |
| 边记录 40 B（有向边，128 位叉积判凸凹）与 64 B `Edge{A,B,C,bool,bool}` | `0x595A80` / `0x596000` | `geom::ConvEdge` + `geom::buildEdges` |
| 事件记录 40 B 输出到 `[out+0x48]` | `0x596231`–`0x59631F` | `convolveBoundaries` 的累积环 |
| **极角归并只用 `(dx,dy)` 的符号分象限，完全不用 `atan2`** | 象限分类指令序列 | `geom::quadrantOf`（照抄条件）+ `quadrantRank`（CCW 遍历序 `1→4→3→2`） |
| 全库唯一 `atan2` 在 `Geom::SignedAngleInRad`（`0x5C5280`） | `0x634C70` 的 x87 `fpatan` | 本工程不需要（角度离散化用 `2π·s/steps`），未复现 |
| `ConvolutionRaw` 对同一对多边形调用两次并交换、返回值 `xor 1` | `0x596F20` | `geom::nfp(a,b)`（等价于 `a ⊕ −b`） |
| NFP 容差 `1e-6` | `@0x9AC818` / `0x9DCB20` | `NoFitMap::kTolerance` |
| `NoFitContext` = 240 B（0xF0），缓存 `+0x78`/`+0xA8`，`+0xD8` 计数、阈值 `19999999`、`+0xE8` 默认 `25000` | `NewNoFitContext` `0x9AF0` = `new(0xF0)`；`DeleteNoFitContext` `0x9CC0`；`NoFitSetMaximumComplexity` `0x9930` | `NoFitMap`（`kDefaultMaxComplexity = 25000`、`kCacheClearThreshold = 19999999`） |
| `NoFitNesting` = 32 B `{void* ctx; vector<40B 记录>}`，记录 `{Part*, bool flip, double,double,double}` | `NoFitAddNestedPart` `0xA9D0` | `NoFitNesting` / `NoFitPlacement` |
| 布尔并（`..\exact\boolean.cpp` `0x597BD0`）未逐指令反编译 | 报告 §7.1 未确认 | `boolean::booleanOp`（自研等价实现：边相交分裂 + 双侧包含性 + 最顺时针缝合 + 偶奇归一化） |
| **回环分类**：`ConvolutionRaw` 把事件累积成环，非凸情形再对环分类 | 报告 §7.1（通用非凸路径未反编译） | `geom::convolveRingLoops`（两边列表各自从最低顶点进入、按角度循环归并、重复顶点处闭环/裂环、整套环按 `minA+minB` 锚定）+ `boolean::classifyConvolutionLoops`（嵌套奇偶 → 外环/孔） |
| 非凸 NFP 未反编译（`NoFitMapWithoutHoles` `0x59E9D0`，10198 B） | 报告 §7.1 未确认 | 两条路：回环游走（**两个操作数都凸时精确**）与 `boolean::minkowskiMultiDecomposed`（耳切三角剖分 + 逐对凸卷积求并，通用）。带孔用环角色容斥 `(Ao⊕Bo) − (Ao⊕Bh) − (Ah⊕Bo) + (Ah⊕Bh)` |

## 3b. 布尔运算与图案平铺（`src/boolean.cpp`、`src/tiling.cpp`）

| 逆向结论 | 证据 | 代码 |
|---|---|---|
| `Tiling::BiModulePattern`（vtable `0xA3D1C0`，8 槽） | RTTI + vtable | `tiling::BiModulePattern`（两模块棋盘交错） |
| `Tiling::MultiOrientedPartPattern`（vtable `0xA3D370`，8 槽） | RTTI + vtable | `tiling::MultiOrientedPartPattern`（单元内定向轮转） |
| `Tiling::DensityEvaluator` / `UnlimitedDensityEvaluator` / `UnlimitedXDensityEvaluator` | RTTI | `tiling::DensityEvaluator` 等 |
| `Tiling::QuantityEvaluator` / `ReusableEvaluator` / `ObliqueEvaluator` | RTTI | 同名类 |
| `Tiling::MultitorchEvaluator` / `OldMultitorchEvaluator` | RTTI | `tiling::MultitorchEvaluator`（割炬行数越少越好） |
| `Tiling::BoxMultiTiler` / `Tiling::SqueezeMultiTiler` | RTTI | 同名类（择优 / 边界收拢） |
| `Tiling::PackerCache` | RTTI | `tiling::PackerCache` |
| 重复图案 + 主打包器 = `TilingNester`（`0x46940`，最大的 nester） | 报告 §7.0 | `TilingNester::run`：铺图案 → 逐个 `checkPlacement` → 余量交给 `packAll(seed)` |

## 4. 偏移（`src/geom.cpp`）

| 逆向结论 | 证据 | 代码 |
|---|---|---|
| `N = floor(dist/step + 0.5)`，`N ≤ 1` 直接返回，否则**分 N 步增量偏移** | `0x58A7E0` | `geom::offsetRing` |
| `NewExternalOffset` 前置断言 `radius >= 0.0` | `0x58B520`，`@0x9DCB28` | `offsetOnce` 的注释与 `dist` 符号处理 |
| **外轮廓 `+gap`、内孔 `−gap`**（`btc` 取反符号位） | `AddInflatedToolPathToPart` `0x12C60` | `geom::inflatePolygon` |
| 无 `JoinType` / `MiterLimit` 概念 | 无相关字符串 | 采用"边法向 + 顶点斜接"，不暴露 join 选项 |
| 偏移常量 `1.0 / 0.5 / 0.0 / -0.0` | `0x9DCB10` / `0x9DCB18` / `0x9DCB28` | `OffsetParams` |

## 5. 搜索与策略（`src/nester.cpp`、`src/engine.cpp`）

| 逆向结论 | 证据 | 代码 |
|---|---|---|
| `Multi::Nester` 6 虚槽：dtor / deleting dtor / `Name()` / `Prepare()` / `Estimate()` / `Run()` | 各 `Multi::*Nester` vtable 槽布局；`Name()` 在多个类里是同一个 4 字节 `mov eax,imm; ret` | `lcns::Nester` |
| `Multi::NestingNester` 自带 `std::mt19937`（种子常数 `0x6C078965`，`[+0x9F8] = 0x270 = 624`） | 构造器 `0x342E0` | `Random`（`std::mt19937`，默认种子 5489 = `0x1571`） |
| `TerminalNode::eval()` = `movsd xmm0,[rcx+0x48]`；`SplitNode::eval()` = `[rcx+0x50]` | `0x974F0` / `0x97510` | `BeamNode::value48` / `value50` / `eval()` |
| 树准备函数 `0x22CCA0` 打印 `"Preparing tree for beam "` | 字符串 `@0x9C1E94` | `NestingNester::run` 里的 `addLog(ctx, "Preparing tree for beam ")` |
| `tree_db.cpp::FindNode` `0x1C12D0` | 断言 `itr != m_nodes.rend()` | `DatabaseNester::hashNesting` / `remember` / `db_` |
| **beam width 常量未恢复** | 报告 §7.2 未确认 | `BeamParams::width`（默认 8，可配） |
| `beam_distinct_angle` / `beam_frequency_ratio` / `enable_beam` 参数键 | `@0x9AFE2D` / `@0x9AFB6E` / `@0x9AFB62` | `BeamParams::distinctAngle` / `frequencyRatio` |
| `StrategyAdder::Add` `0x2C4D0`：`2→Rectangle`、`3→Row`、`4→Row(pipe)`、`1→Nesting`、另加 Compact/Filter/NoFill/Limited | 分配大小 + 构造器装载的 vtable | `makeStrategy(int mode)` |
| `AdvancedStrategist::operator()` `0x2DF60` 选 4 条路，常量 `1.0 @0x9AEC90` | 三处 `movsd` | `Engine::run` 的策略表 + `StrategyDescriber` |
| `0x2CCF0` 级联 `n → 2 → (n+1)/2 → n−1` | 反汇编 | `StrategyDescriber::cascade()` |
| `Multi::Supervisor::Run` `0x827F0` 签名 `(Supervisor*, uint strategy_id, uint rank)`，**每策略一线程** | 线程绑定 RTTI `…IFPFvPN5Multi10SupervisorEjjE…` | `Supervisor::run`（+ `EngineParams::threads`） |
| `SupervisorCanceller::ProbeCancel` `0x30030`：`elapsed / Problem[+0x408] > 1.0` 是**唯一总闸** | double `1.0 @0x9AEE88` | `TimeCanceller::probeCancel()` |
| `Utils::Canceller` 基类 `probeCancel` = `xor eax,eax; ret`（`0x7D7D20`） | vtable `0xA3BD70` | `Canceller::probeCancel()` |
| `RCompactCanceller` `0x7D2CB0` **不可取消** | 9 字节空函数 | `NeverCanceller` |
| Observer 6 槽：v4 = `NewIntermediateSolutionFound`、v5 = `NewNestingFound` | `0x755A80` / `0x755A60`；字面量 `@0x9AE400` | `Observers::newIntermediateSolutionFound` / `newNestingFound` |
| `Engine::BestObserver` / `CompositeObserver` 择优 | `0x755A80` / `0x75CDA0` | `BestObserver` |
| `Engine::Run` 签名 `(const Problem&, double, Observer&, Result&)` | 调用点 `0x2516E` | `Engine::run(order, params, obs)` |
| 引擎族 Run 槽 RVA：`MultiEngine 0x755050`、`InfiniteEngine 0x759A80`（`-1.0 @0x9AE740` = 无限时间哨兵）等 | vtable 槽 | `EngineParams::timeLimitSeconds` 的注释 |
| 收尾三 pass：postop → `"Finalize : Parts renested in holes"` → `"Finalize : Nesting packed bottom left"` | `0x1B33B0`；`RenestInHoles` `0x40720` | `Supervisor::run` 末尾 + `renestInHoles` / `packedBottomLeft` |

## 6. 压缩（`src/nester.cpp::compactNesting`）

| 逆向结论 | 证据 | 代码 |
|---|---|---|
| 网格步长 = `min(宽,高) / 10.0` | `0x252B60` 的 `[obj+0x10] = min(f1,f2)/10.0`，`10.0 @0x9C2BB0` | `compactNesting` 的 `step` |
| `RotateCompact @0x678230` 开头 `if (1e-6 > param) return 0;` | `1e-6 @0x9BF5D0` | `compactNesting(..., acceptThreshold = 1e-6)` |
| `CompactAux` `0x1DA0C0` 的 `"Swap 180 begin"` / `"Trying swap180 "` | 字符串 | 180° 交换候选 |
| `RCompact::RotateLogger` 8 槽全是空函数 ⇒ 纯日志钩子 | vtable `0xA533D0` | 未建模（无行为） |
| `"Compaction success : "` / `"Compact cancelled !"` | `0x9C0B0E` / `0x9AECFF` | `addLog(ctx, "Compaction success : ")` |

## 7. 工艺特性（`src/model.cpp`、`src/nester.cpp`）

| 逆向结论 | 证据（setter → 偏移） | 代码 |
|---|---|---|
| `SetObjective → +0x08`，`SetOrigin → +0x0C` | `0xCEC0` / `0xD050` | `Order::objective` / `origin` |
| 余料三 double `+0x28/+0x30/+0x38` | `SetOffcutEvaluation` `0xE2D0` | `Order::usedSurfaceMinOffcutDimension` 等 |
| 剪切块 `+0x44/+0x48/+0x50/+0x58`，断言 `!shear` 与共边 tiling 互斥 | `0xDDC0` / `0xDDF0` / `0xCEF0` / `0xDE20`；`0x765460` | `Order::shear` / `shearCorner` / `shearGap` / `shearRepulseFromBorders` |
| 共边 `+0x5C..0x90`，**`+0x88` 是模式标签**（1=预设 `+0x8C`，0=目标 `+0x90`） | `0xE460` / `0xE940` / `0xEC90` / `0xEDF0` | `Order::commonCutModeTag` / `commonCutPresetIndex2` / `commonCutObjectiveNum/Den` |
| 多割炬 `+0x98..0xD8`，`+0x98` 同为模式标签；`SetMultiTorchObjective` 的完整算式 | `0xEF50` / `0xF130` / `0xF2C0`；`1000.0@0x9AD710`、`0.66@0x9AD708` | `Order::multitorch*`；算式作为注释保留 |
| 行块 `+0x128..0x150`、管材块 `+0x158..0x178` | `LoadRow 0x506D80` / `LoadPipe 0x506E10` / `0xFBF0` / `0xFCF0` | `Order::rowMode` / `rowShearGap` / `pipeMode` … |
| `row_intervals` 是 y 向条带，`GetRow` 输出两个 double | `0x10040`；`row_number < row_intervals.size()` | `dll::Api::GetRow` 的类型化签名 |
| 品质区两套区间 `<9` 与 `<100`；`grain` 断言 | `0x9ADCAA` / `0x9ADDEA` / `0x9D9400` | `Order::leatherMode` / `Sheet::grainDirection` |
| marks `+0xE8/+0xF0`，SVG 图层 `__marks__` | `0x188D0`；`0x9DB968` | `Order::markMode/markSize`；`toSvg` 里的 `__marks__` |
| 缺陷 `+0x118`、禁布区、`ForcePartInsideHole` 写 `+0x20A/+0x20B` | `0x109C0` / `0x1A210` / `0xC610` | `Order::defectGap`、`Sheet::restrictedZones`、`Part::holeStatus` |
| 装配组 `+0x2B0`；建议分组在建模期转成 clusters | `0x10B50` / `0x11640`；`CreateProblem → 0x1C540 → MakeClusterFromSuggestedPartsGrouping 0x1C2A0` | `Order` 的注释；`renestInHoles` 处理孔 |
| `CommonCutProperties` / `MultitorchProperties` 字段序 | `SaveProblem 0x5070E0` | `model.hpp` 同名结构 |
| `CommonCutSegment{common_cut,left,right,left_index,right_index,valid,linked}`、统计键 `number_of_common_cut` / `common_cut_length` / `regarding_length` | `LoadSegment`；`0x9ACB10` | `CommonCutSegment` / `CommonCutEvaluation` / `detectCommonCuts` |
| `CNS_GetPartTorchInfos` 逐零件返回 6 元组 | `0xD870`；断言 `part_index < nested_parts().size()` | `MultitorchInfo`；`evaluateMultitorch` |

## 8. 授权与云端（`src/licensing.cpp`、`src/cloud.cpp`）

| 逆向结论 | 证据 | 代码 |
|---|---|---|
| `PCId = ((mac×vol) + (mac>>16) + mac + vol) ^ 0xABADCAFE` | `GetPCId` `0xC010` + 混合式 `0x24290` | `licensing::computePcid`（`test_licensing` 手算校验） |
| `"%ld"` 格式化 + 函数内静态缓存 | `0xC010` | `licensing::pcidString()` |
| MAC 取第一个适配器 `IP_ADAPTER_INFO.Address`（`+0x198`，6 字节，**大端**） | `0x24290` | `licensing::computeMachineId()` |
| `GetAdaptersInfo` 返回 `0x6F`（`ERROR_BUFFER_OVERFLOW`）时按新长度重试 | `0x24290` | 同上 |
| 卷序列号来自 `GetVolumeInformationA("c:\\", …, &serial, …)` | `0x24290` | 同上 |
| 三个 `UnLockLaunchingOrder*`（`0xE180`/`0xE1F0`/`0xE260`）机器码相同，各写两个 key 字符串（`+0x248`/`+0x268`） | 反汇编 | `licensing::LicenseKind`（Sntl/PcId/Oxy）+ `Order::licenseKey1/2` |
| 许可门把状态码写进 `context+0x4C`：**9 = 通过**，11 / 17 = 拒绝 | `0x1E70` | `licensing::checkKey` 的 `contextCode` |
| 校验委托 Sentinel LDK：`hasp_login` / `hasp_logout` / `hasp_read` / `hasp_write` | `hasp_windows_x64.dll` 导入名 | `licensing::HasLayer`（`LoadLibraryA` + `GetProcAddress`） |
| 许可文件 id `0xFFF4`、写入 128 字节**空格填充**；读 `offset 0x10, length 0x80` | `0x12BBA0` / `0x12BCC0` | `HasLayer::kLicenseFileId` / `kWriteSize` / `readFile` |
| `sntl_admin_context_new` / `sntl_admin_get` / `_delete` / `_free` | `sntl_adminapi_windows_x64.dll` | `licensing::SentinelAdmin` |
| 984 字符 base64 厂商码在 `0x9A2080`（解码 736 B，熵 7.688），被 `0x12BC04` / `0x12BD3F` 引用 | 报告 §6 | **故意不外带**；`licensing::vendorCodeHint()` 说明来源与用法 |
| 授权路径**不用 CryptoPP** | 该路径 0 调用点 | 未引入任何加密库 |
| 云端 `Engine::CloudEngine::Run` `0x26A60` | 唯一的业务虚函数 | `cloud::CloudEngine::run` |
| HTTP PUT `/pb/<id>` 提交，GET `/sol/<id>` 轮询，body == `"end"` 时改取 `/best_sol/<id>` | `0x2893F` 处与 `"end"` 的比较 | 同上的轮询分支（label = `intermediate` / `final`） |
| 服务器 `cns1.optalog.com;cns2.optalog.com`（分号分隔）、端口常量 `0x50` | `LaunchComputation` `0x6100` | `cloud::Config::servers` / `port` |
| 选项名 `cns_force_cloud` | `LaunchLocalComputation` `0x2AB0` | `cloud::Config::optionName` |
| 超时：PUT `120.0`、总期限 `2t + 30`、GET 轮询窗口 20 s、引擎预算 `max(t − 5, 1)` | `0x9AE9B0` / `0x9AE9B8` / `0x4A817C800` ns | `Config::putTimeoutSeconds` / `overallSlackSeconds` / `pollWindowSeconds` / `submitTimeReduction` |
| 请求构造 `0x6DA1F0`(GET) / `0x6DBD40`(PUT)，响应解析 `0x6DAB80` / `0x6DC480` | 反汇编 | `buildGetRequest` / `buildPutRequest` / `parseResponse`（含 chunked 解码） |
| 请求 id = `std::mt19937`(5489) + `CryptGenRandom` 生成的 UUIDv4 | 构造器 | `cloud::makeRequestId`（`random_device` 顶替 `CryptGenRandom`） |
| `LaunchComputation` 与 `LaunchLocalComputation` 互相调用（可回退本地） | `0x6100` / `0x2AB0` | `CloudEngine::runWithFallback` |

## 9. 线性规划与列生成（`src/lp.cpp`、`src/lp_nesting.cpp`、`src/io.cpp`）

| 逆向结论 | 证据 | 代码 |
|---|---|---|
| `Lp::LinearProgram` ← `Coin::CoinLP`（封装求解器），**COIN-OR Clp 1.15.3 静态链接、经 `OsiClpSolverInterface`** | RTTI + 构建路径串 `…\nest\external\Clp-1.15.3\Clp\src\ClpSimplexDual.cpp` / `CoinUtils\src\CoinLpIO.cpp`；全文件 **OR-Tools 0 命中** | `lp::LinearProgram`（抽象）+ `lp::SimplexLinearProgram`（零依赖后端；**非 Clp**） |
| `Coin::CoinLP`：实例 240 B，`vptr[+0]` + 求解器指针 `[+8]`；13 个虚槽（2 = 重置、3 = 4 B 标志设置器、4 = **追加一列**、5 = **追加一行**、8 = **提交+求解**、9/10/11/12 = 转发到求解器） | vtable 地址点 `0xA3B280`；构造器 `0x267760`（`operator new(0xF0)`、`operator new(0x418)`、`0x281BA0`、配置 `[vt+0xC0](0,10000)` / `0.5` / 模式 `3`） | `lp::LinearProgram` 的虚接口与之逐槽对应 |
| **`BuildAndSolveLp` = `0x7D7200`（1520 B），源文件 `..\multi\database.cpp`，断言 `biggest_sheet->price()` 在第 450 行** | 函数自带 symlog 标签 `BuildAndSolveLp`；字符串 `biggest_sheet->price()` / `..\multi\database.cpp` | `lp::buildAndSolveLp`（逐句翻译：一列/板材、一行/零件、单位系数松弛列、提交求解） |
| **Clp 实际在解**：`min Σ_sheet price(s)·x_s`，`s.t. 对每个零件 p：Σ_sheet count(s,p)·x_s ≥ demand(p)`，`x ≥ 0`（板材选择集合覆盖，**不是** Dantzig–Wolfe 主问题） | `BuildAndSolveLp` 的 slot 4/slot 5 装配循环；`sheet[+0x138]` 是按零件索引的计数数组；常量 `0x9B08B0 = 1.0` 是松弛列系数 | `lp::SheetContent` / `lp::SheetSelectionResult` / `lp::buildAndSolveLp` |
| 解被消费：`0x6A6AD0`（Database 族）解完 `call [vptr+0x50]`（slot 10 → 求解器 `vt+0x228`）取解向量并回映板材 | 反汇编 `0x6A6B7E` 起；调用者为 `0x59AC0`（含串 `linear`）与 `0x6A6AD0` | `SheetSelectionResult::values` / `duals` |
| ⚠️ 方法学：vptr 指向 **vtable 地址点（`vtable+16`）**，按 vtable **头部**地址搜索会得到"0 引用"并误判死代码 | `0xA3B270`（头）vs `0xA3B280`（地址点） | 文档记录于 `re/findings_lp_use.md` §4.1 |
| `Prc::PriceComputer` 家族可从 `Multi::CompactNester::Run` 到达 | 工厂 `0x4D64C0`（**地址点** `vtable+16` 命中，vtable 头部会误判为死代码） | `lcns::PriceComputer`（几何面量，`nester.hpp`）与 `lp::ColumnPricer`（列生成定价，`lp.hpp`）分开建模 |
| `Prc::BoxSurfacePrice` / `HullSurfacePrice` / `AlphaSurfacePrice` / `LinearCombinationPrice` | 构造器 + 系数表 | `BoxSurfacePrice` 等 |
| **是否存在 Dantzig–Wolfe 主问题无证据** | 报告 §7.3 | 本工程把这条链路显式写出来：`lp::MasterProblem`（集合覆盖）+ `lp::columnGeneration` + `lp::NestingPatternPricer`（以真实排样为定价子问题） |
| `SaveProblem` `0x5070E0` 的 JSON 键 | 字符串表 `0x9DA300`..`0x9DB010` | `saveProblem` / `loadProblem` |
| `source_version` = `"5.0 - 68e2d90e72b4 5449"` | `GetBuildVersion` | `kSourceVersion` |
| `UnSerializeSolution` `0x1C5F0`、`CreateProblem` `0x1EE50` | 反汇编 | `saveSolution` / `loadSolution` |
| `GenerateDxfNesting` `0xBF70` → `DrawDxf` | 反汇编 | `toDxf` / `writeDxf`（R12：HEADER + TABLES(SHEET/PART/HOLES) + ENTITIES 闭合 POLYLINE） |
| `SetOffcutEvaluation` `0xE2D0` 的三个 double | 反汇编 | `offcuts` 用 `usedSurfaceMinOffcutDimension` / `Area` 过滤余料 |
| **Clp 在解什么**：**已结案** | `BuildAndSolveLp` 全反汇编 + 4 处构造点 + 解消费点 | `lp::buildAndSolveLp` 按逆出的伪代码逐句实现（一列/板材、一行/零件、单位系数松弛列、`slot 8` 提交求解） |
| 定点角度原语 `0x5C22D0`（157 B）= `round(atan2(y,x)/2π · 360e10)` 回绕到 `[0,360e10)`；常量 `0x9DE758=2π`、`0x9DE740=3.6e12`、`0x9DE750=0.5`；边界 `0x34630B8A000=360e10` | `0x5C22D0` 逐指令；`0x634C70` = 全库唯一 `atan2`（x87 `fpatan`） | `geom::angleToFixedDegrees` / `geom::kFullTurnFixedDegrees`（`test_exact` 断言 0/90/180/270 的魔数 `0xD18C2E2800`/`0x1A3185C5000`/`0x274A48A7800`） |
| `0x1380D0` 中的 `sin` 块 = `sin(2π·angleIndex/3.6e12)`，0/90/180/270 走精确分支；`hypot` = `sqrt(a²+b²)`（`0x138210` 内联 `sqrtsd` + `0x62FE20` libm 兜底） | `0x1386FD`–`0x13878F` 的魔数除法与 `ucomisd` 分支 | 已并入 `row::directionSine`（见下行）；细节见 `re/findings_lp_use.md` §8.3–8.4 |
| `0x134FA0` = `optional<Interval>`（值类型 **4×double**，按 bool 选 `+0x48`/`+0x70`）；`0x134FF0` = 按 bool 在 `+0xA8`/`+0xC0` 间二选一 | `0x134FA0` / `0x134FF0` 全反汇编 | 记录于 `re/findings_lp_use.md` §8.4 |
| `0x7CA830` **先就地排序** `[this+0x90]` 的三元组（元素 16 字节 `{double@+0,int@+8,int@+0xc}`，键 `(int@+0xc,int@+8,double@+0)` ⇒ 列优先 COO），**再**把数值以 3 空格分隔格式化进调用者给的临时 `std::string` —— 两件事都做；求解在 slot 8（`call [solver_vt+0x00]` → `call [solver_vt+0x100]` → `xor 1`） | `0x7CA830` 开头 `mov r15,[rcx+0x98]` / `mov rdi,[rcx+0x90]` + `call 0x267A30`；`0x679D00` 的调用形态 | `SimplexLinearProgram::canonicalise()`（`solve()` 一开始调用，键 `(column,row,value)`） |
| `CoinLP` 成员布局：`slot 4` 写三个并行 `vector<double>` 的 end（`+0x20/+0x38/+0x50` ⇒ begin `+0x18/+0x30/+0x48`，每列 3 属性）；`slot 5/6/7` 写 `+0x68/+0x80/+0x98`（begin `+0x60/+0x78/+0x90`） | 各槽的写入偏移签名（`g_slot_offsets.py`） | `SimplexLinearProgram` 私有成员：`columnCost_/columnLower_/columnUpper_`、`rowRhs_`、`coefficients_`（`Triplet{value,row,column}`） |
| **`slot 5/6/7 是同一个"追加三元组"例程的三个变体**：`5 vs 6` 只差 4 处（两个 RIP 常量、一处指回 `slot 7` 的 `__func__` 名、slot 6 多一条 `xorpd` 取负）；`slot 7` 无前导块且无间接调用，是**被共享的裸核心** | 规范化指令流 diff（`g_slot_diff.py`） | 对应 `addRow` 的三元组追加；**5/6 的参数语义仍 [推断]**，不写死 |
| `Row::Distancer`（typeinfo `0xA17E20`）← `Row::BasicDistancer`（地址点 `0xA3B1C0`）/ `Row::Squeezer`（地址点 `0xA3B1F0`）；`Squeezer::slot2 = 0x13A360` | RTTI + 地址点 + `0x13A360` 反汇编 | `row::Squeezer`（`lcns/include/lcns/row.hpp`），按 (lo,hi) 地址键记忆化，命中判据 `lo<=keyLo && hi<=keyHi`，未命中才调成本例程并插回 |
| 成本 `0x1380D0`：`cost = obj[+0x10] / sin(方向角) − max(\|A.v0−A.v2\|, \|B.v0−B.v2\|)`；**仅当两行平行（\|cross(uA,uB)\| ≤ 1e-6，常量 `0x9BCFC0`）时适用**，否则落到 `*out = 0`；另有 `0.005`（`0x9BCFD8`）闸：`lo` 的 `+0xA8` 与 `hi` 的 `+0xC0` 两个 `vector<Interval>`（元素 32 字节）**长度须相等且逐元素 `v0`/`v2` 在 0.005 内** | `0x1380D0` 逐指令（`0x1385C9` 的 `ja` 方向、`0x13861C` 的 `sete`、`0x13863B`–`0x1386C3` 的两两比较） | `row::squeezeCost` + `row::SqueezeContext` / `Interval` / `Slot` / `IntervalList`（`test_row` 覆盖公式、两道闸、零长度与各 bail 分支） |
| `0x134FA0` = `optional<Interval>`（presence 字节 + 4 个 double；`bool!=0 → +0x48`，`bool==0 → +0x70`）；`0x134FF0` = `bool!=0 → +0xA8`，`bool==0 → +0xC0` | 两个小函数全反汇编 | `row::Slot` / `row::IntervalList` 的选取语义 |
| **定价变体无"默认"**：`0x4D64C0` 在 `0x4D6890` 起把 Box + Hull + Alpha×2 **四个子定价器全部构造**，交给 `0x4D9F80` 的 `Prc::LinearCombinationPricer` 按 **5 个权重**（`obj[+0x00/+0x08/+0x10/+0x18/+0x20]`）加权平均；六个内联构造点：`0x4D9AD0`(Box) / `0x4D9B00`(Hull) / `0x4D9B30`(Alpha) / `0x4D9F80`(LC)，另两个 LC 变体 `0x4D9CD0`/`0x4D9DE0` **无调用者** | 各构造点逐指令 + 调用者扫描（`0x4D9AE2` 等 6 处 `lea` 分属 6 个独立小函数，**不在** `0x4D64C0` 内） | 记录于 `re/findings_lp_use.md` §9；**未并入工程** |
| ⚠️ `MasterProblem` / `columnGeneration` / `GreedyPricer` / `NestingPatternPricer` **在 DLL 中没有对应物** | 原库只有板材选择覆盖 LP（见上），无 Dantzig–Wolfe 主问题 | 已隔离进 `lcns/include/lcns/lp_column_generation.hpp`（文件头标注 "NOT PART OF THE BINARY"），`lp.hpp` **不**包含它 |
| `Row::Squeezer` **在引擎策略分派链上可达**：`AdvancedStrategist 0x2DF60` → 级联 `0x2CCF0` → `StrategyAdder::Add 0x2C4D0` → `0x8F210` → `0x6AABC0` → `0x13C380`/`0x134470` → `0x136B80` → Squeezer 构造器（`0x138A20`/`0x138D60`）；而 `Row::BasicDistancer` 的构造器 `0x136AE0` **无调用者**（死代码） | 地址点引用 + 逐级调用图爬升（`g_row_wiring.py`） | `row::Squeezer` 已实现；**尚未接入 nester**（原库的接入点在策略体内 `0x6AABC0`，其调用参数未译） |
| 两个 `AlphaPriceComputer` 实例被传入 rodata double **0.5**（`0x9D9C08`）与 **0.1**（`0x9D9BE8`），存在对象 `+0x68`（slot2 `0x7CA1B0` 返回它）；日志短标签 `'AP '`（`0x9C1C92`，引用者 `0x220ED0`）/ `'DP '`（`0x9C1CAA`，引用者 `0x221110`） | `0x4D68D3`/`0x4D68F5` 的 `movsd`；rodata 引用扫描 | `AlphaSurfacePrice::kBoostAlpha = 0.5` / `kDimAlpha = 0.1`（注释说明**哪个名字对哪个值无证据**，不写死） |
| `Prc::BoostAlpha`/`SurfaceCoeffs`/`DimAlpha` 的名字串**由反射名称注册表 `0x6CC9D0`（18272 B）在 `0x6CCB6E`/`0x6CD080`/`0x6CD631` 直接 `lea`**（不是"零引用"） | rodata 引用扫描 + `0x6CC9D0` 的三处窗口 | 记录于 `re/findings_lp_use.md` §11.2；**布局仍 [未确认]**（无 typeinfo/vtable/成员名串） |
| ⚠️ 方法学：`.text` 段内的"字符串表命中"是**伪影**（断言串是内联构造的）；必须模拟 `movabs reg,imm` + `mov [mem],reg` 还原 | `0x4D64C0` 还原出 `..\pricer\prices_generator.cpp`、`0x7CA370` 还原出 `..\pricer\price_computer.cpp` | 脚本 `g_inline_strings2.py`；据此**撤销**了所有基于 `.text` 内字符串命中的结论 |
| `Row::Squeezer` 对象图：外层 `{vptr@0xA3B1F0, inner*@+8}`，inner **0x270 = 624 B**，`inner[+8]=1`（`0x1380D0` 的开关）、`inner[+0x10]=xmm3`（成本阈值）、`inner[+0]=xmm2`、`inner[+0x28]` 由 `0x2530D0(2*xmm1, xmm2)` 构造、两棵红黑树头在 `+0x210`/`+0x240`；构造器签名 `(out, xmm1, xmm2, xmm3)` | `0x138A20` 逐指令（97 条） | `row::Squeezer(twiceMaxExtent, coeffAt0x18, thresholdAt0x10)` + `enabled()/coeff()/threshold()` |
| `0x13C380` = 行集 → 挤压器：遍历行容器，对 `0x5CD800` 返回的「1 bool + 4 double」，**有效行的贡献被置 0**，否则取**带符号 max**（无 `fabs`）后 `addsd` 加倍；**`xmm6 = xmm1` 是赋值而非取最大**；最后 `call 0x136B80(&squeezer, xmm6, xmm8=cfg[+0x18], xmm9=cfg[+0x10])` | `0x13C380` 逐指令（101 条） | `row::buildSqueezer(rows, configAt0x10, configAt0x18)` + `row::RowView{valid, v[4]}`；`test_row` 三条断言分别钉住"赋值不是最大""有效行归 0""负值不取绝对值" |
| ✅ `Multi::RowNester`（**地址点 `0xA3BB40`**，typeinfo RVA `0xA18390`，名 `N5Multi9RowNesterE`；**构造函数 `0x8F210`**；`Run` = 槽 5 `0x913E0`）在构造函数里 `new(0xD0)` 造一个 **208 字节 core** 并调 `0x6AABC0` 填充，把 core 指针存到 **`this+0x18`**（`0x8F257`）。**`0x6AABC0` 是 core 的初始化函数，不是策略体**（`0x913E0` 不调它）。core 字段：`+0x18` 阈值（= `0x13C380` 的 `cfg[+0x10]`）、`+0x20` 系数（= `cfg[+0x18]`）、`+0x40` mode（0/1/3）、`+0xC0` `Row::Squeezer*`（`0x6AC118` 写入） | AP 的 RTTI 链（`AP-8` → typeinfo → `+8` 名字）；`0x8F210` 全反汇编；`0x913E0` 的直接被调表 | `RowNestCore`（`+0x18`/`+0x20`/`+0x40`/`+0xC0`）+ `RowNester::core_`（= `this+0x18`）；`test_nester` 断言 core 首次为 null、`run()` 后只建一次、四处映射 |
| ⚠️ **明示偏离**：原库在 `Multi::RowNester` **构造函数**里就建好 core（其构造函数已拿到问题对象），本工程 `makeStrategy()` 尚无 `Order`，故改在**首次 `run()`** 构建；结构（`RowNester` 持 `+0x18` 的 core、core 持 `+0xC0` 的挤压器）不变 | 同上 | 见 `nester.hpp` 中 `RowNestCore` 前的注释 |
| ⚠️ 仍未确认：core 两个 double 的**来源**（哪个配置项/`SetXxx` 写入）、`0x5CD800` 的 bool 标志含义与其内部算法、行容器元素型别、`0x134470` 那一路的用途 | 未译 `0x5CD800` 内部；配置写入点未追 | 两个标量作为参数暴露，默认 0，**不填造常量**；`RowView::valid` 统一置 false 并在注释中标明 |
| 旁证：`Multi::Nester` 的地址点 = `0xA3BB10`/`0xA3BB00`（名 `N5Multi6NesterE`）；四个定价器地址点 `0xA3B0C0`/`0xA3B100`/`0xA3B140`/`0xA3B180` 的 RTTI 名**独立印证** §9.1 | 同一条 RTTI 链 | 见 `re/findings_lp_use.md` §13.5(a) |
| ✅ core 两个配置 double 的来源：**默认 rodata 常量** `0x9B1A40 = 10.0`（`core+8`）、`0x9B1A48 = 4.0`（`core+0x18` 阈值）、`0x9B1A50 = 20.0`（`core+0x20` 系数）；**可被问题对象 `+0x1B0`/`+0x1A8` 覆盖**（`0x4FC3C0` = `problem+0x1A0`，再取 `+0x10`/`+8`），gate = `problem+0x170` / `problem+0x1A0` 两字节 | `0x6AABC0` 开头逐指令（`6AABDF`–`6AAC26` 写默认值，`6AAC42`–`6AAC7D` 覆盖）；`0x4FC2F0`/`0x4FC300`/`0x4FC3C0` 全反汇编 | `kRowCoreAt0x08/0x18/0x20` 真常量；`RowNester::cfg18_/cfg20_` 默认值改为它们（不再是 0.0 占位）；覆盖路径**未建模**（`Order` 无 `Pb+0x1A8/+0x1B0`）并在注释中明示 |
| ✅ `0x5CD800`（`..\geom\properties.cpp`）的产出是**包围盒** `{bool@+0, minX@+8, minY@+0x10, maxX@+0x18, maxY@+0x20}`（40 字节），签名 `(out, container)` 且 `ret` 回 out；容器元素步长 **0x30 = 48**；`0x133190 = lea rax,[rcx+8]`；标志极性"**非 0 即跳过**" | `0x5C8C50` 的逐项 min/max；`0x5CD800` 首尾；`0x13C380` 的 `[rsp+0x20..0x40]` 读取与 `r12` | `row::RowView` 字段语义按此校正，`valid` **改名 `skipExtent`**（上轮极性写反了）；`test_row` 用例已同步 |
| ⚠️ 仍未确认：容器元素型别（只知步长 0x30）、`0x5C61D0`/`0x5CD360` 内部、gate 置位时跳去的 `0x6AC20A` 路径、`0x134470` 那一路的用途 | 未译 | 不猜 |
| ✅ 配置字段的**写入者**：`Pb+0x170` ← 导出 **`SetPipeMode`**（`0xFCF0`，`[rsi+0x170] = qword`）；`Pb+0x1A0/+0x1A8/+0x1B0/+0x1B8/+0x1C0` ← 导出 **`SetCommonCutParameters`**（`0x3C3F0`）。两者都是**整块 qword 拷贝**，故"byte 读 / qword 写"相容 | 存储点扫描 + 两个导出的存储窗口；`0x4FC2F0/0x4FC300/0x4FC3C0` 各 3 条指令 | `Order` 补齐 `commonCutBlockSet/commonCutAt1A8/commonCutAt1B0/commonCutAt1B8/commonCutAt1C0`（`pipeMode` 原本已有，本轮补注 `Pb+0x170` 这条证据）；`RowNestCore` 按 `0x6AABC0` 的真实次序实现优先级（默认 → 共边块覆盖 → pipe 模式跳过覆盖），`test_nester` 三条用例钉住 |
| ⚠️ 仍未确认：两块参数内"哪个 qword 对哪个语义"的逐一配对、`core+0x28`(`Pb+0x1B8`)/`core+0x30`(`Pb+0x1C0`) 的用途（已建模未接算法）、gate 置位时跳去的 `0x6AC20A` 路径、容器元素型别、`0x5C61D0`/`0x5CD360` 内部、`0x134470` 那一路 | 未译 | 不猜 |
| ✅ **pipe 分支实体**：`0x6AC20A`（pipe 闸置位后跳去处）**本身就是另一条配置来源** —— `0x4FC3A0` = `[[arg]]+0x170`（已核实 3 条指令），随后 `Pb+0x188 → core+0x20`（系数）、`Pb+0x190 → core+0x18`（阈值）、`Pb+0x198 → core+0x38` | `0x6AC20A` 起 13 条指令（`6AC20A`–`6AC23E`）；`0x4FC3A0` 全反汇编 | `RowNestCore` 改为 `if (pipe) {pipeAt188/pipeAt190} else if (commonCutBlockSet) {commonCutAt1A8/commonCutAt1B0}`；`Order` 补 `pipeAt178/180/188/190/198`；`test_nester` 断言两条来源各自取值 + pipe 优先 |
| ⚠️ **更正**（上轮读反）：pipe 模式**不是**"保留默认值、跳过覆盖"；两条来源**互斥**：pipe 闸置位 → `Pb+0x190/0x188`；否则共边闸置位 → `Pb+0x1B0/0x1A8`；都不满足 → rodata `4.0/20.0` | `0x6AAC3A` 的 `jne 0x6AC20A` 与 `0x6AAC42` 的次序 | 同上 |
| ✅ 那个"行容器"= **core 自己的 `std::vector`（`core+0x48`）**：`6AAC95 [rsp+0x58] = rbp+0x48`，且 `6AACB3/BB/C3` 把 `begin/end/cap` 三连清零；元素步长 **48 字节**，元素首 qword 是 `void* p`，`0x133190 = lea rax,[rcx+8]` 取 `p+8` 交给 `0x5CD800` | `0x6AABC0` 的 `6AAC82`–`6AACC3` | 记录于 §16.3（工程不建该容器）；**仍未确认**：`p` 的型别、元素其余 40 字节、填充该 vector 的循环 |
| ✅ 相邻 `0x6AC250` 属 **`Multi::SplitNode`**（地址点 `0xA3BB80`，RTTI `N5Multi9SplitNodeE`），是引用计数释放循环；**208 字节的 core 自己没有 vtable** | 地址点 RTTI 链；`0x6AC250` 的 `lock sub dword [rbx+8],1` + 虚调用 | 与 `RowNestCore` 无关，仅记录以免误归属 |
| ⚠️ 仍未确认：`core+0x28`/`0x30`/`0x38` 的用途（已建模未接算法）、参数块内 qword 与语义的逐一配对、`0x5C61D0`/`0x5CD360` 内部、`0x134470` 那一路 | 未译 | 不猜 |
| ✅ **更正 §16.3**：行容器是 **`std::vector<Item*>`（元素 8 字节指针）**，`Item` = `0x1333D0(...)` 造的 **0x90 = 144 字节**对象（`6AB777 [rax]=rdi ; 6AB77A add rax,8`）。此前判定的"元素 48 字节"**是错的** —— 0x30 步长属于 `0x13C380` 的**第二个循环**（`Item+8` 处的嵌套容器；`0x133190 = lea rax,[rcx+8]` 正是取它） | `0x6AABC0` 的 `6AB6A0`–`6AB817`；`0x13C380` 的两个循环 | 记录于 §17；工程不建这两层容器，仅纠正文档 |
| ✅ `core+0x40` 的 mode 分派（`0x6AB6B5`）有一条分支以 **`0x1A3185C5000 = 1.8e12`（180 度定点度）** 作角度参数 —— 与 `0x1380D0` sin 块的 180 度魔数**同一常量**；`0x134470` 是**逐零件**调用且 `r9 = core+8`（配置块） | `0x6AB6CC` 的 `movabs`；`0x6AB72E` 的实参 | 记录于 §17（`0x134470` 的算法仍未译） |
| ✅ **`Item`(0x90 B) 布局**（构造者 `0x1333D0`，`r14 = this`）：`+0x00` = `partIndex`(dword)、`+0x08` = 嵌套 `vector<Elem48>`（begin/end/cap 在 +8/+0x10/+0x18）、`+0x20…+0x88` 多组字段。**三层**：`vector<Item*>`(8B) → `Item`(0x90B) → `Elem48`(0x30B，内含 `vector<Elem16>` 与 `vector<0x18B 记录>`) → `Elem16`(16B) | `0x1333D0` 的成员写入 + 三处尺寸魔数（÷48 的 `0xAAAAAAAAAAAAAAAB`+`sar 4`；16B 的 `sar 4`+`add 0x10`；`0x18` 的清理循环） | 记录于 §18.1；**印证** `0x133190 = lea rax,[rcx+8]` 取的正是 `Item+8` 的嵌套容器 |
| ✅ **`0x4F7690` = Part 的尾调访问器**：`mov rcx,[rcx+0x70] ; jmp 0x547670` ⇒ 元素容器入口是 **`Part+0x70`** | 该函数仅 2 条指令 | 记录于 §18.3(a) |
| ✅ core 的 **`+0x28`/`+0x30`/`+0x38` 在已追踪路径上零读者**（`0x6AABC0` 内读计数 0；`0x13C380` 只读 `cfg[+0x10]`/`cfg[+0x18]` ⇒ 被消费的是 `core+0x18`/`+0x20`）；链由此闭合 | `0x6AABC0` 内以 rbp 为基址的读写计数表 | 记录于 §18.3(b)；**不下"死字段"结论**，只写"已追踪范围内零读者" |
| ✅ **`0x134470` 的算法**：逐零件扫描 **16 字节条目**的容器，对每个通过谓词 `0x5C2E40` 的条目调用 **`0x133DE0(..., core+8)`** 求代价并**保留最小值**，把最优条目写进 `*out`。常量：`0x14 = 20`（初始容量）、`0x38 = 56`（内层元素步长）、**`0xD18C2E2800 = 9e11 = 90 度**（与 sin 块同一魔数） | `0x134470` 逐指令（`1345E9` 谓词、`134604` 代价调用、`13460E` 的 `jbe` 取小、`13450B` 的 `movabs`） | 记录于 §19.1；**未并入工程**（其依赖 `0x133DE0`/`0x5C2E40` 未译） |
| ✅ **core 的 `+0x18`/`+0x20` 有第二个消费者**：`0x134470` 把 `r9 = core+8` 交给 `0x133DE0`，故阈值/系数除 `0x13C380` 外还被这条逐零件路径消费 | 同上（`0x6AB716` 的 `r12 = rbp+8` 与 `0x134604` 的实参） | 补完 §18.3(b) |
| ⛔ **`core+0x28` / `+0x30` / `+0x38` 明确声明：用本方法不可恢复**（附原因）——数据库 TU 内 ≤40 B 的访问器里只有 `0x4FC2F0`(`+0x170`)/`0x4FC300`(`+0x1A0`)，**没有** `+0x198`/`+0x1B8`/`+0x1C0` 的 getter；全局按偏移扫描与 130–220 个**无关类型**的同偏移访问混淆，无法判归属。已知确切事实仅两条：**由两个配置块写入**，且**在 `0x6AABC0` 与 `0x13C380` 内都无读者** | `g_db_accessors.py` / `g_pb_readers.py` 两轮定向检索 | `Order` 里建模为 `pipeAt198`/`commonCutAt1B8`/`commonCutAt1C0` 但**未接算法**——**明说的缺口，不是近似** |
| ✅ **验收测试**：`tests/test_recovered.cpp` 逐条断言工程常量 == 从二进制读出的数值，每行注明 RVA（`kScale@0x9AD708`、`kFullTurnFixedDegrees@0x34630B8A000`、90/180/270 度魔数、`kSqueezeAlignmentTolerance@0x9BCFD8`、`kSqueezeParallelTolerance@0x9BCFC0`、`kRowCoreAt0x08/0x18/0x20@0x9B1A40/48/50`、`kBoostAlpha@0x9D9C08`、`kDimAlpha@0x9D9BE8`、`kSnapTolerance`、`NoFitMap::kDefaultMaxComplexity@0x61A8`） | 各常量在 `re/findings_*.md` 与 `re/REPORT.md` 中的 RVA | `ctest` 目标 `recovered`；**改常量而不重读二进制即会失败** |
| ✅ 隔离声明原文：`lcns/include/lcns/lp_column_generation.hpp` 文件头写着 **"NOT PART OF THE BINARY"**，且 `lp.hpp` **不**包含它 | 该文件头 | 即"自创替代"已移出忠实层并就地声明 |
| ✅ 可追溯性检查脚本 `re/g_acceptance.py`：对 36 条结论逐条核对"依据地址是否在文档中 + 工程是否有对应实现"，当前 **36/36** | 脚本自身 | 见 `re/REPORT.md` §10.5 |
| ✅ 谓词 `0x5C2E40`（138 B）**完全译出**：容器的**24 字节记录** `{u8 tag@0, int64 lo@+8, int64 hi@+0x10}`，判断"是否存在 tag 相符且 `[lo,hi]`（或反向区间）包含给定整数的记录"；步长 `0x18` 与 `Elem48+0x18` 那层**完全对上** | `0x5C2E40` 逐指令（`5C2E69` 的 tag 比较、`5C2E8A`/`5C2EA2` 的两向区间判断） | 记录于 `re/findings_lp_use.md` §21.1；其形状与 §18.1 的 `Elem48` 第二层一致 |
| ✅ 取价例程 `0x133DE0`（1458 B）入口：`0x5CD800` 求候选包围盒 → **`20.0`（`0x9BCEB0`）× 高** → `0x1333D0` 造 Item（`partIndex = 0`）→ `0x136B80(&squeezer, xmm1 = 高×20, xmm2 = cfg[+0x18], xmm3 = cfg[+0x10])`。**同一个 Squeezer 构造器两个调用点的第一实参含义不同**（`0x13C380` 是 `2×max(高,宽)`） | `0x133DE0` 的 `133E3E`–`133EF7`；常量 `0x9BCEB0` | 已并入：`row::kCandidateHeightScale = 20.0` + `row::candidateSqueezerArg(height)`，`test_recovered` 断言 `candidateSqueezerArg(3.0) == 60.0` |
| ✅ `0x136Cxx`/`0x137FE0` 家族作用于 **`rsp+0x110` 的另一个对象**（Squeezer 的 out 槽是 `rsp+0x30`）：`0x136CA0` = 容器计数 `([+0x20]−[+0x18])>>4`；`0x136CB0` = **缓存于 `+0x50`、由常量 `0x9BCF48` 守门的惰性求值**（取末元素 `0x134F30(首qword) + 次qword`）；`0x136D30` = `+0x10`/`+0x11` 两级标志；`0x137FE0` = 16 字节记录的合并循环（`0x137A90`） | 各函数逐指令 | 记录于 §21.3；`0x133DE0` 的返回值 = `0x136CB0` 留在 `xmm0` 的 double（**[推断]**，已逐条核对清理路径不碰 xmm0） |
| ⚠️ 仍未确认：`rsp+0x110` 对象的类名/布局与初始化函数 `0x136C00`、`0x134F30`/`0x137A90`/`0x5CEE50`/`0x5D38C0`/`0x5C4CD0`/`0x5C4CE0`、立即数 `0x271000000000` 的字段切分 | 未译 | 不猜 |
| ✅ `0x136C00`（75 B）= `rsp+0x110` 对象的初始化器，**布局全给出**：`{double@0, double@8, u8@0x10, u8@0x11, vector<16B>@0x18/0x20/0x28, node*@0x30(=this+0x40), u64@0x38, u8@0x40, 分值缓存@0x50}`；**缓存哨兵 `0x9BCF48 = -1.0`**（不是 NaN —— 纠正 §21.3 的猜测） | `0x136C00` 逐指令（14 条） | `row::kScoreUnset = -1.0`；`test_recovered` 断言其为 `-1.0` 且**非 NaN** |
| ✅ `0x134F30`（22 B）= 节点贡献：`node[+0x18] ? 0 : (node[+0x30] − node[+0x20])` | 该函数 7 条指令 | `row::ScoreNode{flag,a,b}` + `row::nodeLength()` |
| ✅ `0x136CB0`（78 B）= **惰性分值公式**：容器空 → 0，否则 **`nodeLength(末元素.first) + 末元素.second`**（`0x136CDC` 取 `end[-1]`），记忆化于 `+0x50`；**只在缓存恰为 `-1.0` 时重算**（改数据不失效） | `0x136CB0` 逐指令（21 条）；`0x136CDC`/`0x136CE0` 的取值 | `row::candidateScore()` + `row::LazyScorer`（`score/invalidate/cached/computed`）；`test_row` 断言"末元素而非首元素"（首元素故意给 100）、空容器、改数据不失效、`invalidate()` 后重算 |
| ⚠️ 仍未确认：**容器如何被填**（`0x137A90` 1175 B 的记录合并、`0x1331A0`、`0x1333C0`、`0x136C90`、`0x137FE0` 的合并循环），因而"节点从哪来、其 `+0x20`/`+0x30` 是什么"未定；`0x5CEE50`/`0x5D38C0`/`0x5C4CD0`/`0x5C4CE0`；`0x133DE0` 四实参含义；立即数 `0x271000000000` 的切分 | 未译 | 不猜 |
| ✅ **节点（Row node）布局齐全**（访问器族）：`+0x18` 退化标志、`+0x20/+0x28/+0x30/+0x38` **包围盒**、`+0x40/+0x41` 与 `+0x98/+0x99` 两组标志对、`+0x48/+0x70` 两个 `optional<4×double>`、`+0xa0` double、`+0xa8/+0xc0` 两个容器 | `0x134F30`(X 跨度) / `0x134F50`(Y 跨度) / `0x134F90` / `0x134FF0` / `0x135010` / `0x135030` 全反汇编 | `row::ScoreNode` 扩为完整布局 + `nodeLength()`/`nodeLengthY()`/`nodeFlag40()`/`nodeFlag98()`；`test_row` 断言 X/Y 跨度、退化归零、标志选择 |
| ✅ **`rsp+0x110` 对象布局齐全**：`+0x00`/`+0x08` double、`+0x10/+0x11` 标志对、`+0x18` `vector<16B>`、**`+0x30` `std::string`（SSO）**、`+0x50` 分值缓存 | `0x136D00`/`0x136D10`（两个 double）、`0x136D20`/`0x136D30`（标志）、**`0x136D40` = 在 `+0x30` 构造 `std::string`**、`0x136D50` = 字符串拷贝（读 `{ptr@+0x30, len@+0x38}`），与 `0x136C00` 的 SSO 写入（`[+0x30]=this+0x40, [+0x38]=0, byte[+0x40]=0`）互证 | 记录于 §23.2；`ScoreRecord` 仍是工程里的 16 字节元素模型 |
| ✅ 顺带记录两个 rodata 常量：`0x9BCF60 = 1e-06`、`0x9BCF70 = NaN`（出现在 `0x137A90` 内） | `0x137A90` 的 rodata 读取 | **语义未定，故不写入工程**（避免按猜测命名） |
| ⚠️ 仍未确认：**容器如何被填**（`0x137A90` 1175 B 主体、`0x137800` 636 B、`0x1331A0` 两个子对象的角色）、`0x5CEE50`/`0x5D38C0`/`0x5C4CD0`/`0x5C4CE0`、`0x133DE0` 四实参含义 | 未译 | ⇒ 候选集生成未确证，故"候选取最小"的完整实现仍不具备条件（不以假定输入凑版本） |
| ✅ `0x137800`（636 B）= **`orderedAddElement`**（方法名由它自己的内联断言串解出）：把 **16 字节 `{void*@0, double@8}`** 记录以 **步长 0x10** 追加到 `O+0x18/+0x20/+0x28`（`0x137854`/`0x137857`/`0x13785C`），需要时经 `0x137838`→`0x137A11` 扩容，**并在 `0x137877` 把分值缓存 `O+0x50` 重置为 `-1.0`** | `0x137800` 逐指令；内联串 `0x6465746e6569726f`+`0x656d656c45646441` = "orderedAddElement" | `row::orderedAddElement(records, scorer, node, value)`；`test_row` 断言"追加后 `computed()` 转 false 且分值由**新末元素**决定"。记录形状**印证**了 `row::ScoreRecord` |
| ✅ **缓存失效点确证**：就是 `orderedAddElement` 自己（`0x137877`），不是"调用方约定" —— §22.4 的注释**已修正** | 同上 | `row::LazyScorer` 的注释改为"由追加器在每次插入时重置" |
| ✅ **更正 §23.3**：`0x9BCF70` **不是 NaN 哨兵**，而是 `andpd` 的**取绝对值掩码**（位型 `0x7FFF…` 读作 NaN），与 `0x9BCF60 = 1e-06` 一起构成 epsilon 比较（`0x137E02`/`0x137F07` → `0x137E20`/`0x137F0F`） | `0x137A90` 的 `andpd` 与紧随的比较 | 记录于 §24.3（该常量入文档、**不入代码**） |
| ✅ `0x137A90`（1175 B）结构：按 tag 经 `0x1331A0` 选 `P+0x58`/`P+0x70` 子对象 → 以**步长 `0xd8` = 216 字节**遍历其容器 → 每元素对第 4 实参 `r12` 做**虚调用 `[vptr+0x10]`** + `0x136CB0` 惰性分值 + `0x134F30`/`0x134F50` 跨度 → 取优 → `0x137800` 追加 → 返回 1/0 | `0x137A90` 的头/尾/跳转表 | 记录于 §24.4 |
| ⚠️ 仍未确认：源容器元素**型别**（仅知步长 216）、`0x134F70`、虚调用目标 `r12` 的类、`0x1331A0` 两个子对象的角色、`0x133DE0` 四实参含义、`0x5CEE50`/`0x5D38C0`/`0x5C4CD0`/`0x5C4CE0` | 未译 | 候选集**骨架**已明，但元素型别与虚调用目标未定 ⇒ 仍不实现完整取最小算法 |
| ✅ `0x5CEE50`（527 B）= **角度索引 → `{cos, −sin, sin, cos, 0, 0}`**：取模魔数 `0x9C5FFF26ED75ED55`（与 `0x1380D0` 的 sin 块**同一个**）、`0x34630B8A000 = 360e10`、四个精确角分支（`0x5CEFE0`/`0x5CF000`/`0x5CF020`/`0x5CF040`）用 `1.0`/`-1.0`/**`-0.0`**（符号精确）；一般路径 `角度/3.6e12*2π` 后 `cos`/`sin`，`-sin` 由 `xorpd [0x9DE960] = -0.0` 取负。**tag ≠ 0 分支有额外缩放，未译** | `0x5CEE50` 逐指令 + 四个分支 | `row::AngleTransform` + `row::angleTransform()`（**仅 tag = 0 路径**）；`test_row` 断言四个精确角（含 `signbit(-0.0)`）、一般路径、`%360e10` 回绕 |
| ✅ `0x5D38C0`（1500 B）= 用该变换把 `0x4F7600(part)` 的 **48 字节元素容器**变换拷贝到 out（元素大小 `0x30` 由 `0x5D391E` 的 ÷48 魔数证明） | `0x5D38C0` 首 50 条 + 调用表 | **主体未译** ⇒ 它是 `bestCandidate` 里 `ScoreFn` 的注入点 |
| ✅ `0x134470`/`0x133DE0` 实参全部追清：`rcx=out`、`rdx=0x4F7600(part)` 的 48 字节缓冲、`r8=rsp+0x1d0`（**谓词用的记录表**）、`r9=core+8`；循环元素来自 `rsp+0x70` 的 16 字节向量（`0x8BEFC0` 填充），携带 `{tag, 角度}` | `0x6AABC0` 的调用点 + `0x134470`/`0x133DE0` 前导 | 记录于 §25.3 |
| ✅ **语义闭环**：`0x134470` = "在**被授权**的候选角度中挑出让分数最小的那个" —— 一个**最优旋转搜索** | 上述三者的合流 | `row::bestCandidate()`（控制流完全：谓词过滤、取最小、全拒返回 −1）；`test_row` 覆盖跳过被拒项/并列取先者/全拒 |
| ⚠️ 仍未确认：`0x5D38C0` 主体、`0x5CEE50` 的 tag ≠ 0 分支、`0x5C4CD0`/`0x5C4CE0`（tag/角度取值器，语义仅由用法推定）、`0x8BEFC0`、`0x133DE0` 的 arg2 角色 | 未译 | 注入点已明示（`ScoreFn`），译出后可直接替换而**无需改动循环** |
| ✅ 两个取值器坐实 ⇒ **16 字节元素的型别确定**：`0x5C4CD0(element)` = `movzx eax, byte [rcx]` ⇒ `tag@+0x00`；`0x5C4CE0(element)` = `mov rax, [rcx+8]` ⇒ `angle@+0x08`（定点度）。`0x5C5F50`/`0x5C61D0` 是恒等 | 两个函数各 2 条指令 | `row::CandidateElement{tag, angle}` 由"用法推定"升级为"取值器证实" |
| ✅ `0x5D38C0` 的**变换算术**译出（两处相同块 `0x5D3BA8`/`0x5D3C90`）：`x' = cos·x − sin·y + tx`、`y' = sin·x + cos·y + ty`，`tx`/`ty` = 变换记录的 `+0x20`/`+0x28`（tag = 0 时恒 0）；并用 `ucomisd 0, (cos²+sin²)` 校验行列式 | `0x5D3BFF` / `0x5D3BFA` / `0x5D3C09`–`0x5D3C17` | `row::transformX()` / `transformY()` / `transformDet()`；`test_row` 断言 90° 旋转两个基向量、四个分支行列式均为 1 |
| ✅ "高" = 变换后点的 **Y 跨度**（包围盒 min/max 由 `0x5C8C50` 完成，§14.2 已译），再 `20 × 高` 交给 `Squeezer` | `0x133DE0` 的 `0x133E3E`/`0x133E67` + `0x5C8C50` | `row::transformedHeight()` / `transformedWidth()`；`test_row` 断言 2×1 矩形未旋转高 2 宽 1、旋转 90° 后高 1 宽 2，且 `candidateSqueezerArg(...)` = 40 |
| ✅ **注入点收窄**：`Row::Squeezer` 的构造实参已**完全可算**（角度变换 + 高/宽 + `20×高` 三者都完全译出）；仍缺的是 `Squeezer` 之后的分值装配（`0x1333D0`→`0x136B80`→`0x136CB0`→`0x137A90`→`0x137800`） | 上述各节 | `bestCandidate` 的循环/谓词/取最小**无需改动**，只需替换 `ScoreFn` |
| ⚠️ 仍未确认：分值装配（见上）、`0x5CEE50` 的 tag ≠ 0 分支、`0x8BEFC0`、`0x133DE0` 的 arg2 角色、48 字节元素内点的确切偏移 | 未译 | 不猜 |
| ✅ **`0x271000000000` 解读完成**：`0x133DE0` 建的"容器"只有一个元素 `{[rax]=变换指针, [rax+8]=立即数}`；立即数按字节拆开是 `byte[+8]=0`、**`u32[+0xc] = 0x2710 = 10000`** ⇒ 源记录 = **16 字节 `{void* source@0, u8 tag@8, u32 count@0xc}`**，此处 count = **10000**（排空上限）。这**结清了 §21.4 的"立即数字段切分未定"** | `0x133EC9`/`0x133EDF`/`0x133EE9` 的写入 + 立即数字节分解 | `row::kSourceRecordCap = 10000` + `row::SourceRecord{source, tag, count}` |
| ✅ `0x137FE0`（177 B）**排空环**：先 `0x136C00` 初始化目标对象；逐记录（0x10 步长）：`esi = [rec+0xc]`，**count==0 整条跳过**（`0x138013`），否则取 `tag = byte[rec+8]`、`source = [rec]` 调 `0x137A90`，**返回 0 则下一条**（`0x13805A`），**`--esi` 到 0 也下一条**（`0x13805E`），否则**重试同一条**（`0x138063`）；最后返回目标对象 | `0x137FE0` 逐指令（53 条） | `row::drainSources(records, mergeFn)`；`test_row` 断言零 count 跳过、上限恰为 count、合并提前返回 false 即停、count=1 只调一次、source/tag 原样传递 |
| ✅ **`0x133DE0` 全链**（按地址拼装）：`0x5CEE50`(角度→变换) → `0x5D38C0`(变换拷贝) → `0x5CD800`(包围盒) → `20×高` → `0x1333D0`(Item) → `0x136B80`(Squeezer) → **`0x137FE0`(排空)** → `0x136D30` → `0x136CB0`(惰性分值) → `0x136CA0` → 返回 `xmm0` | §21/§25/§26/§27 各节 | 除 `0x137A90` 合并本体外，**全部已入工程** |
| ⚠️ **注入点只剩一个**：`0x137A90` 的合并本体 —— 缺源容器**元素型别（步长 216 字节已知）**与第 4 实参 `r12` 的**虚调用目标类**；另 `0x8BEFC0`、`0x133DE0` 的 arg1/arg2 分工、`0x5CEE50` 的 tag≠0 分支未译 | 未译 | `bestCandidate`/`drainSources`/`candidateScore`/`orderedAddElement` 届时**无需改动** |
| ✅ **ABI 纠正**：Windows x64 下 `rdi` 是 **callee-saved**，而 `0x5CD800` 的序/尾声是 `push rdi` … `pop rdi` ⇒ 它**保留 `rdi`**。所以 `0x133DE0` 里 `0x133EC9 [rax] = rdi` 存的是 `rsp+0x170`，`0x133E93 mov rcx, rdi` 把它当 `0x1333D0` 的 `this` ⇒ **同一段栈区先当"角度变换"、后被复用为 Item（0x90 字节）**，故 §27.2 的源记录 `source` = **那个 Item** | `0x5CD800` 的首 8 条与尾 14 条；`0x133EC9`/`0x133E93` | 记录于 §28.1（**纠正了 §27.1 的读法**） |
| ✅ **`Item+0x58` / `Item+0x70` = 两个 216 字节元素容器**：`0x1333D0` 把 `+0x58/+0x60/+0x68` 与 `+0x70/+0x78/+0x80` 六连清零（两组 begin/end/cap），随后反复写 `[r14+0x60]`/`[r14+0x78]` 提交 end；而 `0x1331A0(Item, dl)` = `dl ? +0x70 : +0x58` | `0x1336F8`/`0x133710`/`0x1339C1`/`0x133AA8` 等写入点 | `kItemSize = 0x90`、`kItemContainerA = 0x58`、`kItemContainerB = 0x70`、`kItemSubObject = 0x20`、`itemContainerOffset()`；`test_row` 断言 |
| ✅ **216 字节元素的构造器 `0x136350`（1920 B）证实了 `ScoreNode` 的布局**：`+0x00` 指针、`+0x08/+0x10` 源容器 begin/end、`+0x18` **退化标志初值 1**、`+0x20..+0x38` 包围盒（由 `0x5CD800` 的 5 个 qword 拷入）、`+0x40/+0x41` 两个标志（由 `0x134D70(容器, Item+0x20)` 得）、`+0x48/+0x70` 两个可选槽 presence、`+0xa8/+0xc0` 两个容器。另：`0x13645B` 用 **180 度**（`0x1A3185C5000`）建变换再 `0x5D38C0` 变换一次 ⇒ 元素里存着**镜像朝向**的容器 | `0x136350` 的前 70 条与调用表 | **15 条 `static_assert`**（`sizeof == 0xd8` + 逐 `offsetof`）把布局**锁进编译期**；`test_row` 另有运行时断言。**静态断言当场抓出 `ScoreNode` 缺 `+0x00/+0x08/+0x10` 三格**，已补 |
| ⚠️ 仍未确认：`0x137A90` 对第 4 实参 `r12` 的**虚调用 `[vptr+0x10]` 目标类**（源容器已知是 `Item+0x58`/`+0x70`、元素布局已证实）；`0x136350` 内部的 `0x1355C0`/`0x134D70`/`0x135040`/`0x135780`/`0x5CE7F0`/`0x5CF6B0`/`0x135C70`/`0x8C4FF0`；`0x8BEFC0`；`0x133DE0` 的 arg1/arg2 分工 | 未译 | 不猜 |
| ✅ **注入点闭合**：`0x137A90` 的 `call [rax+0x10]` 解析为 **`Row::Squeezer` 地址点 `0xA3B1F0` 的 slot 1 = `0x13A360`** = 记忆化挤压代价；实参 `rcx = r12(the Squeezer)`、`rdx = [rbp](已存最后一条记录的 node)`、`r8 = rbx(当前 216 字节元素)` ⇒ 它就是 **`Squeezer::cost(lo, hi)`**，即工程里已实现的 `row::Squeezer::cost` / `row::squeezeCost`。**槽位编号纠正**：`0x13A360` 是 slot **1**（`+0x10`，从地址点数），§12/§13 里按虚表基址数成了"slot 2" | `0xA3B1F0` 处的 8 项表 + `0x137BF5`–`0x137C0C` 的实参 | 记录于 §29.1/§29.2；`bestCandidate` 的 `ScoreFn` 从此**无需注入** |
| ✅ **最终算术** `0x137BF0..0x137C83`：`cost = 挤压代价`；`a = 记录值 + 该 node 的 X 跨度 + [P+0x38]`，`b = 惰性分值 + 代价`；`a > b` 则 `cost += a − b`（`jbe` 跳过，故 `a == b` 也跳过）；最后 **`score = cost − element[+0xa0] / obj[+0x08]`** | `0x137C0F`–`0x137C83` 逐指令 | `row::elementScore(...)`；`test_row` **两条分支都断言**（含 `a == b` 走 `jbe`），并做**端到端**：2×1 矩形 + 90° ⇒ `20/1 − 0 = 20` 且**被缓存** |
| ⚠️ 仍未确认：`0x134D70`（元素两个标志的计算）、`0x135030`/`0x136D10` 的用途命名（数值来源已知）、`0x136350` 内部的 `0x1355C0`/`0x135040`/`0x135780`/`0x5CE7F0`/`0x5CF6B0`/`0x135C70`/`0x8C4FF0`、`0x8BEFC0`、`0x133DE0` 的 arg1/arg2 分工 | 未译 | 数值与结构已知，仅"角色命名"未定 ⇒ 按目标 ④ 明说 |
| ✅ **候选角度的来源结案**：`0x5C4C50` 只有 **4 条指令** —— `mov rax,[r8] ; mov byte [rcx],dl ; mov [rcx+8],rax` ⇒ 它是**写一个 `{tag@+0x00, angle@+0x08}` 元素**（与 §26.1 由取值器确定的元素型别互为印证），不是"生成一组角度"。`0x8BEFC0`（308 B）则**拷贝源容器 + 追加这一个元素**（向量三字段写在 `0x8BF092`/`0x8BF098`/`0x8BF09C`）。而 `0x134470` 自己的准备段：空向量 → `0x8BEFC0(tag=0, angle=0)` → 再手工追加 **`{tag=0, angle=0xD18C2E2800 = 90°}`**（`0x13450B`/`0x134532`/`0x13453C`）⇒ **候选集 = 源自带元素 + 0° + 90°，tag 全 0** | `0x5C4C50` 全部 4 条；`0x8BEFC0` 首 60 条与尾部；`0x1344C5`–`0x134540` | `row::writeCandidateAngle` / `candidateAngles` / `kAxisAngle90` / `axisAlignedCandidates`；`test_row` 断言顺序、追加项、以及该 90° 条目走 `angleTransform` 的**精确 90° 分支** |
| ⏳ `0x134D70`（437 B）**部分证实**：`0x5CD800` 取包围盒 → 用 **`1e-06`（`0x9BCEE0`）与 fabs 掩码 `0x9BCED0`** 逐元素做容差比较（`0x134E40` `xmm0 = xmm7 − xmm10 + 1e-06` 后 `ucomisd`）→ 返回 bool，即元素 `+0x40`/`+0x41` 的来源。**完整表达式未逐条转写（101 条、多层分支），故不写入工程** | `0x134D70` 的前 46 条 + 调用表 | 仅记结构（§31.4） |
| ⏳ 仍未译：`0x135030`/`0x136D10` 的角色命名（数值来源已知）、`0x136350` 内部七个子调用、`0x133DE0` 的 arg1/arg2 构造者、`0x5CEE50` 的 tag≠0 分支 | 未译 | 不猜 |
| ✅ **纠正（本轮）**：元素 `+0x08`/`+0x10` **不是**"源容器 begin/end"（§28.3 的读法有误），而是**产生该元素的那条 16 字节候选记录 `{tag, angle}` 的副本**。三条证据：① 存储端 `0x136363`/`0x136374`/`0x13637B`/`0x136388` 从 `r8` 拷两个 qword；② 读取端 `0x1355C0` 的 `0x5CEE50(element+8)`，而 `0x5CEE50` 正是用 `0x5C4CD0(x)=byte[x]`（tag）与 `0x5C4CE0(x)=[x+8]`（角度）读它的；③ 调用端 `r8` 在各点都是遍历中的 **16 字节候选元素** | `0x136363`–`0x136388`、`0x1355DA`–`0x1355E1`、`0x5C4CD0`/`0x5C4CE0` | `ScoreNode` 字段改名 `sourceTagQword`/`sourceAngle`（**15 条 `static_assert` 偏移不变**，仅语义命名修正）+ `nodeSourceTag`/`nodeSourceAngle`/`nodeAngleTransform`；`test_row` 断言 tag/角度取值与 90° 精确分支 |
| ✅ `0x133190` = `lea rax,[rcx+8]` ⇒ 元素 `+0x00` 是 **Item 指针**，几何源是 **`Item+0x08`**（零件的 48 字节几何容器） | `0x133190` 两条指令 | `kItemGeometry = 0x08` |
| ✅ `0x1355C0`（438 B）= **元素自己的几何步**：`0x5CEE50(transform, element+8)`（用它自己的角度）→ `0x133190([element])` = `Item+0x08` → `0x5D38C0` 变换拷贝 → `0x5CD800` 包围盒 → `xorpd -0.0`（`0x9BCEF0`）→ `0x5D3430`（1156 B，未译）→ 整体替换 out 的 vector | `0x1355C0` 前 60 条 + 调用表 | 记录于 §32.3；工程侧只落到 `nodeAngleTransform` |
| ✅ 一批"访问器"实为**恒等转发**：`0x5C5F30`/`0x5C5260`/`0x5C61D0`/`0x5C5F50` 全是 `mov rax,rcx; ret` | 各自的 2 条指令 | 记录于 §32.4（修正此前把它们当作"做工作"的说法） |
| ⏳ 仍未译：`0x5D3430`(1156 B)、`0x135040`(1396 B)、`0x135780`(1250 B)、`0x135C70`(1748 B)、`0x5CE7F0`(381 B)、`0x5CF6B0`(235 B)、`0x8C4FF0`(147 B)；`0x134D70` 的完整表达式；`0x135030`/`0x136D10` 角色命名；`0x133DE0` 的 arg1/arg2 构造者；`0x5CEE50` 的 tag≠0 分支 | 未译 | 已按目标 ④ 明说；不猜 |
| ✅ `0x5CF6B0`（235 B）= **两点仿射变换**：算术与 `0x5D38C0` **完全一致**（`x' = cos·x − sin·y + tx`、`y' = sin·x + cos·y + ty`，对两个点各做一遍）⇒ 是 `transformX/transformY` 的**第二个独立代码证据** | `0x5CF70B`–`0x5CF791` 逐指令 | `row::transformPoint` + `row::FPoint2`；`test_row` 断言与 `transformX/Y` 一致 |
| ✅ `0x8C4FF0`（147 B）= **`Elem48` 容器析构函数**：内部 vector 元素步长 **0x18**（`0x8C502D add rbx,0x18`）、外层元素步长 **0x30**（`0x8C5054 add rdi,0x30`），最后 `jmp operator delete` ⇒ **从析构端证实 `Elem48`=48 字节、内含 24 字节记录 vector**（与 `0x5C2E40` 推出的记录步长吻合） | `0x8C4FF0` 全部 54 条 | `row::kElem48Stride = 0x30`、`row::kRecord18Stride = 0x18`；`test_row` 断言两者关系 |
| ✅ `0x5CE7F0`（381 B）= **角度→变换算法的第二个实例**：常量与 `0x5CEE50` **完全相同**（魔数 `0x9C5FFF26ED75ED55`、`0x34630B8A000`、`0xD18C2E2800`/`0x1A3185C5000`/`0x274A48A7800`）⇒ 印证 `angleTransform`；`0x136350` 在 `0x13645B` 以 **180°** 调它，把容器的**镜像副本**存进元素 | `0x5CE7F0` 前 25 条 + `0x13645B` | `row::kHalfTurn180 = 0x1A3185C5000ll` + `row::halfTurn()`；`test_row` 断言 `cos=−1`、`sin=0`、**`−sin = −0.0`（符号精确）**、`(3,4)→(−3,−4)` |
| ⏳ 仍未译的四个大函数：`0x5D3430`(1156 B)、`0x135040`(1396 B)、`0x135780`(1250 B)、`0x135C70`(1748 B)；另 `0x134D70` 的完整表达式、`0x135030`/`0x136D10` 角色命名、`0x133DE0` 的 arg1/arg2 构造者、`0x5CEE50` 的 tag≠0 分支 | 未译 | 已按目标 ④ 明说；不猜 |
| ✅ **`0x134D70` 完全译出**（437 B / 101 条）：对容器每个元素扫描其 `+0x00` 处的 **16 字节点链**（**按闭合链处理** —— `0x134E27` 从末点起算），用 `1e-06`（`0x9BCEE0`）与 fabs 掩码（`0x9BCED0`）判定；发现"y 在窗口内却严格倒退的 x 步"即 false（`0x134EDD`）。结果**粘滞**（`esi` 只清不置）⇒ 多元素 AND | `0x134D70` 全部 101 条 + 跳转表 | `row::chainMonotone(chain, node[3], bboxMaxX)`（**标签按地址命名** L40/L53/L57/L80/L95/Lb7，逐块对应、注释带 RVA）+ `chainFlags`；`test_row` **两条路径都断言**（含特意构造到 `0x134EDD` 的 false 用例） |
| ✅ **`Elem16` 语义确定 = 二维点 `{double x, double y}`**：`0x134E57` 的 `add rax,0x10` 给出 16 字节步长，循环只读 `[rax]`(x) 与 `[rax+8]`(y) ⇒ 补上目标 ② 中"`Elem16`(16B) 的字段语义"。至此三层为：`Item(0x90)` → `Elem48(0x30)` → `{+0x00 vector<Elem16> 二维点, +0x18 vector<Record18> 24 字节}` | `0x134E57`、`0x134E20`、`0x8C502D`（§33.2 的析构步长） | `row::Elem16` + `kElem16Stride = 0x10`、`kChainEpsilon = 1e-06`；`test_row` 断言尺寸与容差 |
| ⏳ 仍未译：`0x5D3430`(1156 B)、`0x135040`(1396 B)、`0x135780`(1250 B)、`0x135C70`(1748 B) 四个大函数；`0x135030`/`0x136D10` 角色命名；`0x133DE0` 的 arg1/arg2 构造者；`0x5CEE50` 的 tag≠0 分支 | 未译 | 已按目标 ④ 明说；不猜 |
| ✅ **⑥ 结案**：`0x5CEE50` 的 tag≠0 路径 = **反射 `{cos, +sin, sin, −cos, 0, 0}`**（行列式 −1）。前提是 `xmm6` 此时已为 0（一般路径 `0x5CEF1C` 与四个精确角分支各有 `pxor xmm6,xmm6`），故所有 `* xmm6` 项消失 ⇒ **tag 的语义 = "是否镜像"** | `0x5CEF62`–`0x5CEFB9` 逐指令 | `row::mirroredAngleTransform` + `row::nodeAngleTransform` **按 tag 分派**；`test_row` 断言六字段、`transformDet(mir) == −1`、tag 分派 |
| ✅ `element+0x98/+0x99/+0xa0` 的生产者（都在 `0x136350` 内）：`+0x99` = **第一槽存在且 `\|v[2]−v[0]\| ≤ 1e-06`**（`0x1366E0 setae`）；`+0x98` = **第二槽的 presence**（`0x1366F9`）；**`+0xa0` = `0x135C70(...)` 的返回值**（`0x13670F`） | `0x1366BE`–`0x13670F` 逐指令 | `row::nodeSlotFlag99` / `nodeSlotFlag98`；`test_row` 断言三种情形 |
| ✅ **③ 的答案**：分母 `0x136D10` = `obj[+0x08]` = `0x136C00` 的 `xmm2` = `0x133DE0` 的 **`cfg[+0x08]`（配置系数）** ⇒ **结案**；分子 `0x135030` = `element[+0xa0]` **数值通路结案（由 `0x13670F` 从 `0x135C70` 写入）**，**命名明确不可恢复**（取决于未译的 1748 B `0x135C70`；无类型/字符串/RTTI 可借） | `0x136D10`、`0x136C10`、`0x137FF8`、`0x133F2D`、`0x135030`、`0x13670F` | 记录于 §35.3（**不猜**） |
| ✅ **测试抓出的真实缺陷并已修正**：`0x5D38C0` 用的是 `[+0x00]cos`、`[+0x08]negSin`、`[+0x10]sin`、`[+0x18]cos2` ⇒ `x' = cos·x + negSin·y + tx`、`y' = sin·x + cos2·y + ty`、`det = cos·cos2 − sin·negSin`。我原先按 `−sin`/`cos` 写，**对旋转等价、对镜像错误**；`transformDet(mir) == −1` 的断言当场失败（得 1）并据此改正 | `0x5D3BDF`–`0x5D3C13` | `row::transformX/Y/Det` **修正**为按 `negSin`/`cos2`；旋转得 +1、镜像得 −1 |
| ⏳ 仍未译：`0x5D3430`(1156 B)、`0x135040`(1396 B)、`0x135780`(1250 B)、**`0x135C70`(1748 B，③ 的命名也依赖它)**；`0x1368A9`（`+0x98` 的另一分支）；`0x133DE0` 的 arg1/arg2 构造者 | 未译 | 已按目标 ④ 明说；不猜 |
| ✅ **⑤ 结案**：arg1（`rsp+0x1b0`）= `0x4F7600(part)` 的**拷贝**，而 `0x4F7600` 只有 **9 字节**（`mov rcx,[rcx+0x70] ; jmp 0x547610`）= 两步访问器返回零件内部容器引用（故必须拷贝）；arg2（`rsp+0x1d0`）= **授权记录表**，由 `0x5C4950`（730 B）逐元素（源步长 0x18）发出 24 字节 `{tag = 0x5C4CD0, lo = 0x5C4CE0, hi = 另一角度}`；两者都是**循环局部**（`0x6AB35A`/`0x6AB36C` 释放） | `0x4F7600` 全部 2 条；`0x5C4950` 的 `0x5C4A20`–`0x5C4AA8`；`0x6AB35A`–`0x6AB399` | `row::makeAuthRecord`、`kPartGeometryVia = 0x70`、`kAngleWrapMax = 0x34630B89FFF`；`test_row` 断言常量与角度区间用例 |
| ✅ **语义回溯**：`0x5C2E40` 的区间端点是**角度**（生产端 `0x5C4A45`/`0x5C4A4D` 取自 `0x5C4CE0`，被测值也是角度）⇒ **授权表 = "该 tag 下允许的角度范围"**，`0x134470` = "在被允许的角度范围内挑分数最小者" | `0x5C4A45`/`0x5C4A4D` + §21.1 的谓词 | `AuthRecord` 注释**升级为"lo/hi 是定点角度"**；`test_row` 用 `[0°,180°]` 测 `authorized`（90° 通过、270° 不通过、端点含） |
| ⏳ 只剩 ④：**四个大函数** `0x5D3430`(1156 B)、`0x135040`(1396 B)、`0x135780`(1250 B)、`0x135C70`(1748 B)；另 `0x1368A9`（`+0x98` 的另一分支） | 未译 | 已按目标 ④ 明说；不猜 |
| ✅ **`0x135C70`（1748 B）的返回值语义 = 鞋带公式面积**：整条函数**零 rodata 常量**、只有 8 条浮点指令；`0x135DB1` 的 `ucomisd`+`cmova` 在 16 字节元素上取 **`+0x08` 最小者**（最低点）；`0x135F90`–`0x135FBE` 原地**反转**一段（顶点顺序规范化）；最后 `0x135FCE` 调 `0x5C51A0`（容器拷贝）、`0x135FD6` 调 `0x5CC6A0`，其 xmm0 在 `0x135FE3` 成为返回值（`xmm6` 全程只写这一次；唯一 `ret` 在 `0x13609C`） | `0x135C70` 的入口/尾部/调用表/浮点表；`0x135DB1`–`0x135DC6`；`0x135F90`–`0x135FE3` | `row::nodeAreaValue`；`test_row` 断言正方形 ±1、三角形 6、退化 0 |
| ✅ **`0x5CC6A0`（135 B）= 鞋带公式求面积**：`0.5 · Σ(prev.x·cur.y − prev.y·cur.x)`，`prev` 从**末点**起算（闭合环）、**带符号不取绝对值**、空环返回 0；常量只有 **`0x9DE910 = 0.5`** | `0x5CC6B2`–`0x5CC726` 逐指令 | `row::dllArea` + `kAreaHalf = 0.5`；`test_row` 断言 CCW +1 / 反转 −1 / 空 0 / 退化 0 / 三角形 6 |
| ✅ **`0x5C51A0`（178 B）= 容器拷贝**（`operator new(end−begin)` → begin/end/cap → 逐个拷 16 字节元素） | `0x5C51E9`/`0x5C51F1`/`0x5C51F4`/`0x5C51F8`/`0x5C5215`–`0x5C522E` | `row::copyRing`；`test_row` 断言拷贝不改变值 |
| ✅ **③ 两端均已命名（更正 §35.3 的"命名不可恢复"）**：`0x137C76` 的比值 = **`ringArea / cfg[+0x08]`** ⇒ 最终 `score = cost − (环形面积 / 配置系数)`。仍严格区分：`0x135C70` 的**返回值语义**已完全确定，其**函数体其余部分**（断言串、临时对象）未逐条转写 | `0x13670F`/`0x135FD6`/`0x135FCE` + §37.1 | 记录于 §37.4 |
| ⏳ 仍未译：`0x5D3430`(1156 B)、`0x135040`(1396 B)、`0x135780`(1250 B)；`0x1368A9` | 未译 | 已按目标 ④ 明说 |
| ✅ **`0x5D3430`（1156 B）完全译出 = 按位移量平移的点链拷贝**：零 rodata 常量、只有 12 条浮点指令且是**两段相同**的 `xmm0=[rax] ; addsd [rbx] ; [rax-0x10]=xmm0`（`0x5D3700`/`0x5D3750`）；唯一 `ret` 在 `0x5D37A3` 返回 `rax=[rsp+0x90]`= arg1 ⇒ `(out, src, offset) -> out`；`0x1355C0` 在 `0x13562D` 用**取负的包围盒一角**（`0x135620 xorpd -0.0`）调用它 ⇒ **把环平移到原点** | `0x5D3430` 入口/返回/调用表/浮点表；`0x5D3700`–`0x5D371B`、`0x5D3750`–`0x5D376B` | `row::translatedCopy(src,dx,dy)`；`test_row` 断言平移正确、**源不被修改**、取负角点归零、**平移保持带符号面积** |
| ✅ **`0x135040`（1396 B）定量定性 = 0.005 容差的匹配例程**：常量 **`0x9BCEE8 = 0.005`**（**与挤压器的 `0x9BCFD8` 不是同一地址**）、fabs 掩码 `0x9BCED0`、`0x9BCEE0 = 1e-06`；FP 为 `addsd` 加 0.005 与成对的 `subsd`+`andpd`+`ucomisd`；调用含 **`0x8C4FF0`（`Elem48` 析构）**；唯一 `ret` 在 `0x135258` 不返回浮点 | `0x135129`–`0x13531C` 的常量与 FP；调用表 | `row::kMergeAlignTolerance = 0.005`（与 `kSqueezeAlignmentTolerance` **区分地址**）；`test_row` 断言两者数值相同 |
| ✅ **`0x135780`（1250 B）定量定性 = 拼 32 字节两点记录**：常量仅 fabs 掩码与 **`0x9BCEE0 = 1e-06`**；`0x135A37`/`0x135A3F`/`0x135A45`/`0x135A4B` **写出 4 个 double**；入口 `0x1357AF movapd xmm8, xmm2`（输入 double）；调用 **`0x134890`/`0x134C10`×2（row 单元内）** 与 `0x8C5D40`×2；唯一 `ret` 在 `0x135987` | `0x13580F`–`0x1358CA`、`0x135A37`–`0x135A4B`；调用表 | `row::kTwoPointRecord = 0x20`；`test_row` 断言该常量 |
| ⚠️ 明说未逐条转写：`0x135040` 与 `0x135780` 的**函数体**（常量、I/O 形状、调用面、返回均已确定）；`0x1368A9`（`+0x98` 的另一分支）**未译** | 未译 | 按目标 ④ 明说，不用近似顶替 |
| 原库用 JsonCpp | 导入/内联函数 | 本工程自研 JSON（值/解析/写出），无第三方依赖 |

## 10. 明确**没有**实现的部分

| 项 | 原因 |
|---|---|
| `..\exact\boolean.cpp` 的**逐指令**还原 | 未反编译（报告 §7.1 标为未确认）；`boolean::` 是语义等价的自研实现，并在 `test_boolean` 中验证可判定量 |
| `NoFitMapWithoutHoles` 的**逐指令**还原 | 同上；`nfpMulti` 用凸分解 + 并集达到等价效果 |
| Clp 求解器本身 | 本工程自带稠密单纯形；不引入 COIN-OR |
| `Tiling::*` 图案枚举的**原库精确顺序** | 原库图案枚举细节未恢复，只复现了类结构与评分语义 |
| DXF 的具体组码约定（原库未确认） | 采用 R12 最保守子集（AC1009 + POLYLINE/VERTEX/SEQEND），任何 CAD 均可读 |
| HASP Vendor Code 常量 | 属产品密钥材料，**故意不内置**（机制已完整提供） |
| 云端真实服务器交互的联网测试 | CI 不访问外网；用 `FakeHttpClient` 覆盖协议流程，真实 socket 实现参与编译 |
