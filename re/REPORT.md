# `libcns_dump_64.dll` 逆向分析报告

> 目标文件：`D:\Nesting\nestfab\libcns_dump_64.dll`（11,808,768 字节）
> MD5 `01fea4b73a33dd233c66ca76235313fa` / SHA-256 `f63b98a94de4b2ca14785de207510ae13a570ca834bc505665bbce9e42efa847`
> 分析方式：纯静态（不执行样本）。所有地址为 **RVA**（相对镜像基址 `0x6B4C0000`）。

---

## 0. 结论速览

| 项目 | 结论 |
|---|---|
| 文件真实身份 | **Optalog CNS 排样/套料引擎核心库**，导出名为 `liblcns.dll`（"lib l C N S"） |
| 版本 | ProductVersion `5.0 - 68e2d90e72b4 5449`；构建时间 **Jun 28 2019 14:03:08**；git `68e2d90e72b4`，build `5449` |
| 版权 | `Authors Lionel and Lepere. All rights reserved.` |
| 编译工具链 | **MinGW-w64 GCC**（x86-64），静态链接 libstdc++ / libgcc / WinPthreads |
| 主要第三方库 | **Boost 1.63**（multiprecision、asio、uuid/sha1、filesystem）、**COIN-OR Clp 1.15.3 + CoinUtils**（LP）、**CryptoPP**（整库静态链接，但**授权路径上未见调用点**，见 §7.5c）、**JsonCpp**；授权校验实际委托给 **Sentinel HASP / Sentinel Admin API**（运行期 `LoadLibraryA`）。**几何内核完全自研**（`Geom::MultiPolygon`、`PartPolygon`、`RealPolygon`、`PolygonProxy`、`OffsetManager`、`NoFitMap`、`HullSurf`）；**未使用 Clipper / boost::geometry / CGAL / Eigen / 遗传算法**（均经全串扫描确认 0 命中，见 [`out_29.txt`](out_29.txt)） |
| 导出函数 | **168 个唯一函数 / 336 个导出项**（每个函数重复导出两次），**全部按序号导出，名字表被清空（`NumberOfNames = 0`）** |
| 函数名恢复率 | **162 / 168** 已恢复（方法见 §4），其余 6 个用行为反推 |
| 文件状态 | 这是 **UPX 加壳模块的内存 dump**：保留了 `BAB0`/`UPX1` 段名和伪造的 UPX 尾部，但**代码已解壳**，同时 IAT 中残留 dump 进程的绝对地址 → **该文件不能被 Windows 加载器正常加载**，只能用于静态分析 |
| 核心算法 | 多策略并行启发式套料（**beam search**：字面量 `Preparing tree for beam `、`beam_distinct_angle`；多个 Nester 策略竞争）+ **矩形对偶快速路径**（`nb_iterations_before_rectangle_dual`）+ **Clp 封装的 LP 与一套"pricing"评分层**（`Lp::LinearProgram`/`Coin::CoinLP`/`Prc::*PriceComputer`，**是否构成列生成尚未证实**，见 §7.3）+ **双自研几何内核**（`..\exact\*` int64 定点 + 128 位精确谓词，`..\geom\*` double；NFP = 边界 Convolution）+ 切割工艺约束（共边、多割炬、剪切、管材/行模式、皮革/纹理、缺陷区、余料）。**不含遗传算法，也不使用 Clipper** |

---

## 1. 文件结构鉴定

### 1.1 节区与熵

| 段名 | RVA | 虚拟大小 | 原始大小 | 属性 | 熵 | 内容 |
|---|---|---|---|---|---|---|
| `BAB0` | `0x1000` | `0x724000` | `0x724000` | X, R | 6.260 | CNS 应用层代码 + 只读数据（**file offset == RVA**） |
| `UPX1` | `0x725000` | `0x41D000` | `0x41D000` | X, R | 6.157 | CryptoPP / Boost / Clp / 其余应用代码与字符串表 |
| `.rsrc` | `0xB42000` | `0x1000` | `0x1000` | W, R | 3.215 | 版本资源、导入名字符串、**导出目录** |

- 熵 ≈ 6.2 是 x86-64 机器码的正常范围（压缩数据应在 7.8 以上）→ **代码已经是解壳状态**。
- 文件中唯一一处 `UPX!` 出现在文件偏移 **`0x205`**（节表之后、而非文件末尾），且后面紧跟 UPX 数据结构与解壳 stub 代码；UPX 4.2.4 尝试 `-d` 时报
  `CantUnpackException: file is possibly modified/hacked/protected`。说明壳头被人为搬迁/修补过。
- 只有一个内嵌 PE 头（文件自身），无 overlay。

### 1.2 版本资源（`.rsrc`）

```
StringFileInfo / 040904B0:
  ProductName     = "CNS - unknown"
  ProductVersion  = "5.0 - 68e2d90e72b4 5449"
  LegalCopyright  = "Authors Lionel and Lepere. All rights reserved."
  CompanyName     = (空)
```
其中 `68e2d90e72b4 5449` 与代码内字符串 `68e2d90e72b4 5449 default`、`Jun 28 2019`、`14:03:08` 互相印证，
分别由导出函数 `GetBuildVersion` / `GetBuildDate` / `GetMajorVersion` 返回。

### 1.3 导入表与"不可加载"结论

`IMAGE_DIRECTORY_ENTRY_IMPORT` 位于 RVA `0xB42274`，共 8 个 DLL、12 个函数：

| DLL | 函数 |
|---|---|
| KERNEL32.DLL | `LoadLibraryA` `GetProcAddress` `VirtualProtect` `VirtualAlloc` `VirtualFree` |
| ADVAPI32.dll | `CryptGenRandom` |
| IPHLPAPI.DLL | `GetAdaptersInfo` |
| libwinpthread-1.dll | `nanosleep` |
| msvcrt.dll | `acos` |
| PSAPI.DLL | `GetProcessMemoryInfo` |
| USER32.dll | `MessageBoxA` |
| WS2_32.dll | `bind` |

这 12 个函数就是**全库全部的导入**（8 个 DLL，每 DLL 1–5 个）：C++ 运行时（libstdc++、Boost、Clipper 等）
都是**静态链接**的，不产生导入。

**关键证据**：所有 `IMAGE_IMPORT_DESCRIPTOR` 的 `OriginalFirstThunk == 0`，而 `FirstThunk` 指向的 IAT 槽里存的是
**绝对运行期地址**（例如 `0x7FF99A5D0AF0`、`0x7FF998F97900`）。这些地址来自某次真实加载该 DLL 的进程。
Windows 加载器在 `OriginalFirstThunk == 0` 时会把 `FirstThunk` 当作"名字/序号数组"来解释，
而 `0x7FF9...` 远超镜像范围 → **按当前文件头加载会失败**。
不过这些槽对应的 **hint/name 名字表在 `.rsrc` 中完好保留**（`0xB42430` 起），
所以 12 个导入函数的**名字是可恢复的**（上表即由此得到）。

**另一个 dump 产物**：代码真正使用的"活 IAT"位于 **`0xB288FC`–`0xB2913C`**（8 字节步长，按 DLL 分 8 段，
共约 257 项），由链接器 thunk（`jmp qword ptr [rip+…]`，集中在 `0x60Axxx`/`0x63Fxxx`）转发。
已定位的 thunk：`GetAdaptersInfo = 0x61F000`、`GetProcessMemoryInfo = 0x61EFF0`、
`bind = 0x61F070`、`nanosleep = 0x63F728`、`acos = 0x63F418`、
`GetVolumeInformationA = 0xB28A84`、`LoadLibraryA = 0xB28AB4`、`GetProcAddress = 0xB28A5C`。

**活 IAT 的字节序异常（dump 产物，分析时需注意）**：`.rsrc` 里的 stub IAT（`0xB42328`）是正常的
小端 8 字节地址；但 `UPX1` 中的活 IAT 把 64 位地址的**两个 32 位半字写反了**
（高 32 位在前）。例如 `0xB28E00` 处字节为 `f9 7f 00 00 e0 1c b8 98`，
按常规小端读得 `0x98B81CE000007FF9`（非规范地址），
而按"半字交换"读得 **`0x00007FF998B81CE0`**（规范地址）。
在该区段 576 个条目中，按常规小端解释**规范地址数 = 0**，按半字交换解释 → 81 个规范地址。
这也是"该文件无法直接加载"的又一层原因。

> 结论：这是用"内存 dump + 回写段数据"方式获得的解壳样本（文件名中的 `_dump_` 也印证），
> 适合静态逆向；若要重新变成可加载 DLL，需要重建导入表（`OriginalFirstThunk`、按名 thunk 数组）与重定位。

---

## 2. 导出机制分析

| 项目 | 值 |
|---|---|
| 导出目录 RVA | `0xB424D8`（位于 `.rsrc`，大小 1424 字节） |
| `Name`（DLL 名） | `liblcns.dll` |
| `OrdinalBase` | 1 |
| `NumberOfFunctions` | **343** |
| `NumberOfNames` | **0** ← 名字表被完全清空（`AddressOfNames` 与 `AddressOfNameOrdinals` 都被改写成指向 DLL 名字符串） |
| 非零 RVA 项 | **336** |
| 唯一函数地址 | **168** —— 每个地址恰好出现 **2 次** |
| 序号空洞 | `63,64` / `75` / `106,107,108,109` 共 **7 个槽位 RVA = 0**（导出被抹掉） |

**为什么每个函数有两个导出项？**
这是 MinGW `ld`/`dlltool` 的经典现象：当符号同时被 `__declspec(dllexport)` 与
`--export-all-symbols`（或一份 `.def`）覆盖时，会生成两条指向同一 RVA 的导出项。此处两项**序号相邻**，
且序号空洞只出现在"对"的边界上，说明地址表是按对写入的。

**为什么是 C++ 重载？**
`dbg::symlog` 跟踪器写入的是**函数名标签**，不含命名空间与参数列表；
因此**原始导出名是 C++ mangled name，168 个函数是 168 个（重载）签名**。
恢复结果显示 168 个导出中只有 **1 组同名重载**（`AddLeatherQualityZoneInPart` ×2，RVA `0x19DE0` / `0x19F40`，
两者函数体几乎相同、指向两处内容相同但地址不同的标签字符串），其余 166 个名字互不相同 ——
说明这套 API 的命名本身就把"圆形/矩形/多边形"等变体区分开来了（见 §4.4）。

同时，DLL 内还在断言/异常文本里使用 `CNS_` 前缀的"公开 C 别名"（见 §4.3），
所以同一个函数往往同时存在 `GetSheet`（C++ 实现名）与 `CNS_GetSheet`（C 别名）两个名字。

---

## 3. 全量函数目录

* 18,614 个函数边界来自 `.pdata`（`IMAGE_DIRECTORY_ENTRY_EXCEPTION` @ RVA `0xA60000`，223,368 字节 ÷ 12 = 18,614 条 `RUNTIME_FUNCTION`），
  覆盖代码区间 **`0x1000` – `0x9A0A3A`**。
* 168 个导出全部落在 **`0x2AB0` – `0x1AE40`**（即 `BAB0` 段前 ~99 KB），且**没有任何一个是虚函数表槽位** →
  对外是一套**扁平的 C/C++ 自由函数 API**，内部才是面向对象的引擎。

完整 168 行清单见同目录：

* [`exports_table.md`](exports_table.md) —— 按功能家族分组的 Markdown 表（含整数参/浮点参/栈参数目、返回是否用 `xmm0`、证据字符串）
* [`exports_table.csv`](exports_table.csv) —— 同样内容的 CSV（便于二次处理）

### 3.1 功能家族分布

| 家族 | 数量 | 说明 |
|---|---:|---|
| 0-lifecycle | 2 | `NewLaunchingOrder` / `DeleteLaunchingOrder` |
| 1-NoFit（NFP/几何） | 8 | `NewNoFitContext` `DeleteNoFitContext` `GetNoFitMap` `GetNoFitPlacementMap` `NoFitAddNestedPart` `NoFitGetNumberOfPoints` `NoFitSetMaximumComplexity` … |
| 2-setters（选项） | 53 | 目标函数、间距、共边、多割炬、剪切、管材、皮革、区域限制、许可 |
| 3-getters（结果查询） | 33 | `GetSolution` `GetNesting` `GetNestedPart` `GetSheet` `GetFillRatio` `GetMark` … |
| 4-add（建模） | 33 | `AddSheet` `AddPart` `AddCircularPart` `AddRectanglePart` `AddPolygonPart` `AddHoleToPart` `AddDefectToSheet` `AddToolPathToPart` … |
| 5-CNS_ API 扩展 | 8 | 装配组、变体授权、区域限制、开放切割路径 |
| 6-computation control | 15 | `LaunchComputation` `LaunchLocalComputation` `LaunchLimitedLocalComputation` `LaunchEstimateLocalComputation` `WaitNextSolution` `WaitComputationTermination` `GetComputationStatus` `CancelComputation` `TerminateComputation` … |
| 8-report/export | 2 | `GenerateDxfNesting` `GenerateHtmlSolutionReport`（另有 `GenerateHtmlLaunchingOrderReport`） |
| 9-misc | 8 | `GetPCId` `UnLockLaunchingOrder*` `ForcePartInsideHole` 等 |
| Z-unnamed | 6 | 无跟踪字面量，按行为反推（见 §3.3） |

### 3.2 句柄对象与结构布局（由成员偏移反推）

通过对"第一个参数指针"的成员访问做聚类，可以还原出各句柄的对象布局（均为逆向推断，非符号信息）：

| 句柄 | 关键偏移 | 含义 |
|---|---|---|
| `LaunchingOrder*`（建模上下文） | `+0x22` / `+0x23` | `SetReorganizeBiggestPartNearOrigin` / `…LongestPart…` 布尔标志 |
| | `+0x41` | `SetEvaluateIntermediateNestingsAsLast` 标志 |
| | `+0x44` | `SetShearMode` |
| | `+0x48` | **计算模式：0 = Local，非 0 = Cloud** |
| | `+0x50` / `+0x58` | 间距相关（`SetInterpartGap` / `SetShearGap`） |
| | `+0x5C`/`+0x60`、`+0x68`/`+0x6C`、`+0x88`/`+0x8C`/`+0x90`、`+0x84`/`+0x85` | 共边模式 / 安全偏好 / 切割偏好 / 目标 / 授权位 |
| | `+0x98`–`+0xD8` | 多割炬配置 |
| | `+0xF8` / `+0xF9` / `+0x100` | 两个布尔标志 + 一个 `double`（内部 setter，见 §3.3） |
| | `+0x118` | `SetDefectGap` |
| | `+0x120` | `SetSheetPriority` |
| | `+0x134` | `SetSheetGrainDirection` |
| | `+0x138` | `SetSheetPrice` |
| | `+0x140`/`+0x148` | Sheet 用户字符串（`std::string`，`+8` 为长度） |
| | `+0x160` | 板材缺陷 / 外部边界容器 |
| | `+0x1A0`/`+0x1A8`/`+0x1B0` | Part 授权 |
| | `+0x1B0`/`+0x1B8` | （内层 problem 的）**Sheet 指针向量 begin/end** → `GetSheet` 用它做 `(end-begin)/8` 计数 |
| | `+0x1B8`/`+0x1C0` | Part 用户字符串（`std::string`：`+0x1B8` 数据指针、`+0x1C0` 长度） |
| | `+0x1C8`/`+0x1D0`/`+0x1D8` | 求解/引擎句柄（`LaunchComputation`、`LaunchLocalComputation` 使用） |
| | `+0x1F0`/`+0x1F8`/`+0x200` | `SetIncompatibleSheet` |
| | `+0x1F8` | `SetLocalMaximumThreads` |
| | `+0x1FC` | `SetLocalMaximumIterations` |
| | `+0x200`/`+0x201` | `SetLocalEngine` |
| | `+0x208` | Part 的外部边界/变体容器 |
| | `+0x20A`/`+0x20B` | `ForcePartInsideHole` / `ForcePartOutsideHole` 标志 |
| | `+0x210`–`+0x238` | `SetExtraParameters`（6 个 double） |
| | `+0x240` | `SetAutomaticStop` |
| | `+0x244` | `UnLockLaunchingOrder` |
| | `+0x248`/`+0x250`、`+0x268`/`+0x270` | **License 字符串 ×2**（`UnLockLaunchingOrderSntl/PCId` 写入，见 §8.4） |
| | `+0x288` | `LaunchEstimateLocalComputation` 的时间预算 |
| `Part*` | `+0x8` | `GetMultiplicity` / `GetLength` / `GetHeight`（包围盒尺寸） |
| | `+0x50`、`+0x180`/`+0x188`/`+0x190` | 几何/计数 |
| `Sheet*` | `+0xF8`–`+0x110` | `SetSheetGaps`（4 个 double） |
| `Nesting*` | `+0x50`/`+0x58` | `GetNumberOfNestings` / `GetNumberOfNestedParts` / `GetFillRatio` |
| `NoFitContext*` | `+0x48`/`+0x58`/`+0x78`/`+0x88`/`+0xA8`/`+0xB8` | NFP 容器（外部环 / 内孔 / 映射） |

### 3.3 6 个未能靠跟踪字面量命名的导出

| 序号 | RVA | 大小 | 行为（反汇编证据） | 推断名 |
|---|---:|---:|---|---|
| 208,209 | `0x16CB0` | 57 | `strlen(rdx)` → `std::string::_M_replace`，目标是 `this+0x1B8`（`+0x1C0` 为长度） | `AddPartVariantUserString`（写 Part 变体用户字符串） |
| 210,211 | `0x16CF0` | 8 | `mov rax,[rcx+0x1B8]; ret` | 取上述 `std::string` 数据指针（`GetPartVariantUserString`） |
| 270,271 | `0xAFE0` | 13 | `test ecx,ecx; setne cl; movzx ecx,cl; jmp 0x1B270`，`0x1B270 → 0x60A610` 写全局字节 `0xB23350` | `SetXXX(int)` → 归一化为 bool 写入全局开关 |
| 286,287 | `0xB000` | 18 | `test edx,edx; movsd [rcx+0x100],xmm2; setne [rcx+0xF9]; ret` | `(Order*, int, double)` 设置双精度值 + 标志 |
| 288,289 | `0xAFF0` | 10 | `test edx,edx; setne [rcx+0xF8]; ret` | `(Order*, int)` 设置标志 |
| 282,283 | `0x1A7D0` | 286 | 从 `r8`/`r9` 各读一个二维点 → 在栈上组装 4 个角点 ×3 个 double（共 12 个 double = `0x60` 字节）→ `operator new(0x60)` → `r8d=4` → `call CNS_SheetAddRestrictedZone` → `operator delete` | **`CNS_SheetAddRectangularRestrictedZone`**（由两角点构造矩形禁布区） |

> 这 6 个函数的调用者列表为空（只经导出表可达），进一步说明它们是纯 API 入口而非内部工具。

---

## 4. 函数名恢复方法（本报告的关键技术）

### 4.1 原理：`dbg::symlog` 作用域跟踪器

二进制里静态链接了一套自制调试框架，其 RTTI 类名为 `N3dbg6symlogE`（`dbg::symlog`），
配套还有 `dbg::file_error`、`dbg::frame_sink`、`dbg::symsink`、`dbg::pe_sink`。
它在函数进入时打印 `"-> " + __func__`，在离开时打印 `"-> // " + __func__`。

跟踪器函数本体（可用作识别特征）：

| RVA | 作用 |
|---|---|
| `0x64ABF0` | 记录 `"-> "` + 名字（带 `double` 变体，`SetObjective`/`SetShearGap` 等使用） |
| `0x64AEA0` | 记录 `"-> "` + 名字（最常用，绝大多数导出使用） |
| `0x64D9C0` | 记录 `"-> "` + 名字（`UnLockLaunchingOrder*` 使用） |
| `0x978010` | 把字面量追加到日志字符串 |

因此**每个被插桩的函数体内一定有至少一个指向自己名字的 RIP 相对字面量**。

### 4.2 恢复规则

> **规则（最终采用）**：取函数体内**第一次调用跟踪器时**作为其参数传入的标签字面量，
> 去掉可能的前导 `//` 后即为函数名；若函数在很靠后的位置才调用跟踪器，则退化为
> "函数体内**最早出现**的标识符形态 RIP 相对字面量"。

* 执行结果：**162 / 168** 得到名字，其中 166 个名字唯一、1 组 2 个重载。
* 交叉验证（三路独立证据一致）：
  1. **标签字面量**本身；
  2. **断言字符串**：`cns.cpp` / `cns_no_fit.cpp` + 断言表达式
     （如 `number <= order->sheets.size()`、`common_cut_number < evaluation.common_cut_segments.size()`、
     `point_number < ring.size()`）与名字语义一致；
  3. **调用图**：例如 `AddCircularPart` / `AddRectanglePart` / `AddPolygonPart` 都调用 `AddPart`；
     `AddNonRectangularPolygonSheet` 调用 `AddNonRectangularSheet`；
     `CNS_*` 变体函数调用对应的基名函数。
* 例：`0xB600` 的处理是 `idx = …` → `if (rbx > (sheets_end - sheets_begin)/8) assert`，
  与名字 `GetSheet` 完全吻合。

18,614 个内部函数同样可以用这套规则命名（本报告只在需要处使用）。

### 4.3 关于 `CNS_` 前缀名

二进制中还有一组仅用于**断言/异常文本**的 `CNS_` 前缀名（如 `CNS_GetSheet`、`CNS_GetCommonCut`）。
以 `GetSheet`（`0xB600`）为例，实际代码是：

```asm
0000B60D  lea rcx,[rip+…]        ; "GetSheet"        ← 跟踪器用它作为入口标签
0000B614  call 0x64AEA0          ; 记录 "-> GetSheet"
…
0000B665  lea rdx,[rip+…]        ; "number <= order->sheets.size()"
0000B679  lea rdx,[rip+…]        ; "CNS_GetSheet"    ← 断言/异常消息里用公开 C 名
0000B68D  lea rdx,[rip+…]        ; "cns.cpp"
```

即：**C++ 实现名 = `GetSheet`，公开 C 别名 = `CNS_GetSheet`**，两者指向同一 RVA。
这也解释了 §2 中"每个函数两个导出项"的现象：导出表同时给出 C++ mangled 名与 C 别名。
本报告的 `exports_table.md` 在"C 别名"列给出了已确认的对应关系。

### 4.4 两种"入口标签"风格（重要细节）

跟踪器标签有两种写法，恢复时必须都识别：

| 风格 | 代码形态 | 出现位置 | 例子 |
|---|---|---|---|
| A | 入口用 `"Name"`，作用域退出用 `"// Name"` | 大多数 API | `GetSheet`、`LaunchLocalComputation`、`SetObjective` |
| B | **入口直接使用 `"// DetailName"`**，没有裸名版本 | 一批"形状变体"建模函数 | 见下表 |

风格 B 的函数（这类函数的名字**必须**按去掉 `//` 后的字符串解读，否则会误合并成同一个泛化名）：

| 序号 | RVA | 跟踪标签 | 说明 |
|---|---|---|---|
| 1,2 | `0x16420` | `// AddPolygonHoleToPart` | 给零件加**多边形孔** |
| 3,4 | `0x162B0` | `// AddPolygonPart` | 多边形零件 |
| 69,70 | `0x16B20` | `// AddNonRectangularPolygonSheet` | 多边形异形板 |
| 71,72 | `0x16970` | `// AddPolygonDefectToSheet` | 多边形缺陷区 |
| 102,103 | `0x16610` | `// AddExternalPolygonBoundaryToSheet` | 板的外轮廓多边形 |
| 104,105 | `0x167C0` | `// AddExternalPolygonBoundaryToPart` | 零件外轮廓多边形 |
| 130,131 | `0x15480` | `// AddCircularPart` | 圆形零件 |
| 132,133 | `0x13800` | `// AddCircularHoleToPart` | **圆孔**（参数为 x/y/d 三个 `double`） |
| 134,135 | `0x15620` | `// AddRectanglePart` | 矩形零件 |
| 136,137 | `0x13A50` | `// AddRectangularHoleToPart` | **矩形孔**（两角点 + 半径） |
| 196,197 | `0x16D00` | `// AddHoleToPartVariant` | 变体孔 |
| 198,199 | `0x16D40` | `// CNS_AddExternalBoundaryToPartVariant` | 变体外轮廓 |
| 200,201 | `0x16D80` | `// CNS_AddOpenCuttingPathToPartVariant` | 变体开放切割路径 |
| 202,203 | `0x16DE0` | `// CNS_SetPartVariantAuthorizations` | 变体授权 |
| 204,205 | `0x16E20` | `// CNS_AddPartVariantSpecificAuthorizations` | 变体专用授权 |
| 216,217 | `0x3360` | `// LaunchEstimateLocalComputation` | 估算式本地计算 |
| 260,261 | `0x13410` | `// AddCircularExternalBoundaryToPart` | 零件圆形外轮廓 |
| 262,263 | `0x13610` | `// AddRectangularExternalBoundaryToPart` | 零件矩形外轮廓 |
| 53,54 / 122,123 | `0x10880` / `0x10920` | `CancelComputation ` / `// CancelComputation` | 取消 / 终止计算 |

---

## 5. 典型调用流程（由导出层调用图与参数约定还原）

```
1) 建模
   order = NewLaunchingOrder(…)                        # 0x14620
   AddSheet(order, …)                                   # 0x15BF0   矩形板
   AddNonRectangularSheet(order, …)                     # 0x157A0   异形板
   AddNonRectangularPolygonSheet(order, …)              # 0x16B20   → AddNonRectangularSheet
   AddPart(order, …)                                    # 0x14D10   任意多边形零件
   AddCircularPart / AddRectanglePart / AddPolygonPart  # → AddPart
   AddHoleToPart(part,…) ×4 个重载                      # 0x16420 / 0x132E0 / 0x13800 / 0x13A50
   AddExternalBoundaryToPart / …ToSheet / AddDefectToSheet
   AddToolPathToPart / AddHoleInToolPath / AddOpenCuttingPathToPart / AddInflatedToolPathToPart
   SetPartUserString / SetSheetUserString / SetPartPriority / SetSheetPrice / SetSheetGaps …

2) 选项
   SetObjective / SetSheetPrice / SetOffcutEvaluation
   SetInterpartGap / SetExtraGapOnPart / SetDefectGap / SetShearGap
   SetCommonCut*（7 个）/ SetMultiTorch*（5 个）
   SetShear* / SetRowMode / SetPipeMode / SetMarkMode / SetLeatherMode
   SetLocalEngine / SetLocalMaximumThreads / SetLocalMaximumIterations

3) 求解
   LaunchLocalComputation(order, timeout, …)             # 0x2AB0（本地）
       └─ 若 cns_force_cloud 选项生效 → LaunchComputation(order,"cns1.optalog.com;cns2.optalog.com","cns_force_cloud",…)
   LaunchComputation(order, servers, option, timeout)    # 0x6100（云端 HTTP）
   LaunchLimitedLocalComputation / LaunchEstimateLocalComputation   # 限时/估算变体
   WaitNextSolution / WaitComputationTermination         # 阻塞取下一个解 / 等结束
   GetComputationStatus / CancelComputation / TerminateComputation

4) 取结果
   GetSolution / GetNumberOfNestings / GetNesting / GetNestedPart / GetNestedPartPartVariant
   GetSheet / GetNestingBoundingBox / GetNestingDimensions / GetFillRatio / GetNestingFillRatio
   GetCommonCut / GetNumberOfCommonCuts / GetPartTorchInfos / GetNumberOfRows / GetRow
   GetMark / GetNumberOfMarks / GetPartWithBadGeometry

5) 输出 / 释放
   GenerateDxfNesting / GenerateHtmlSolutionReport / GenerateHtmlLaunchingOrderReport
   GenerateLaunchingOrderProblem / AsyncCancelAllComputationsAndDeleteLaunchingOrder
   DeleteLaunchingOrder
```

调用图（导出 → 导出）实证：

```
AddPolygonPart                    -> AddPart
AddCircularPart                   -> AddPart
AddRectanglePart                  -> AddPart
CNS_AddAssemblyGroupPart          -> AddPart
AddNonRectangularPolygonSheet     -> AddNonRectangularSheet
AddHoleToPartVariant              -> AddHoleToPart
CNS_AddExternalBoundaryToPartVariant -> AddHoleToPart
CNS_AddOpenCuttingPathToPartVariant  -> AddOpenCuttingPathToPart
CNS_SetPartVariantAuthorizations     -> SetPartAuthorizations
CNS_AddPartVariantSpecificAuthorizations -> AddPartSpecificAuthorizations
LaunchLimitedLocalComputation     -> LaunchLocalComputation
LaunchEstimateLocalComputation    -> LaunchLocalComputation
LaunchLocalComputation            -> LaunchComputation        # 云端回退
LaunchComputation                 -> LaunchLocalComputation    # 本地回退
SetDetailedMultiTorchObjective    -> SetMultiTorchObjective
sub_1A7D0                         -> CNS_SheetAddRestrictedZone
```

注意 `LaunchComputation ⇄ LaunchLocalComputation` 互调：这是"云端不可用则本地算 / 强制云端"的双向回退。

---

## 6. 顶层算法（已验证部分）

### 6.1 `LaunchLocalComputation` @ `0x2AB0`（2134 字节）

1. `call 0x1BF00` 检查环境；返回真时跳到 `0x31C9`：
   ```asm
   000031C9  lea r8,[rip+…]   ; "cns_force_cloud"
   000031D8  lea rdx,[rip+…]  ; "cns1.optalog.com;cns2.optalog.com"
   000031DF  call 0x6100      ; LaunchComputation
   ```
   → **强制云端开关 `cns_force_cloud` 一旦置位，本地入口直接转发给云端入口。**
2. 否则在 `0x314A` 调用内部函数 **`0x1E70`** 真正启动本地计算；返回前记录 `"// LaunchLocalComputation"`（作用域退出）。
3. 全程使用 `std::shared_ptr`（可见 `mov rax,[rbx]; mov rax,[rax-0x18]` 取虚基址偏移、`0x1BF40` 读取 TLS 中的日志/异常上下文）。

### 6.2 `0x1E70`：本地引擎启动器（3135 字节）

顺序打印（由字面量位置确认）：

```
"Order valid"
"Start"
"-> Launching local engines "  <n> " threads for multi," <m> " threads for nesting, " <i> " max iterations."
"Keys: "  <licence/keys 列表>
```

即：先校验问题（Order）合法性 → 读许可证 Keys → 按 `SetLocalMaximumThreads` / `SetLocalMaximumIterations`
配置 **multi 阶段线程数**与 **nesting 阶段线程数** → 启动引擎。
两个阶段的名字与 RTTI 中的 `Multi::Supervisor`（策略调度）和 `Multi::Nester` 体系一致。

### 6.3 `LaunchComputation` @ `0x6100`（3894 字节）：统一启动入口

`LaunchComputation(order, servers, option_name, timeout)` 是对外的主入口，其被调用者中同时包含
**`0x1E70`（本地引擎启动器）**与 **`0x2AB0`（`LaunchLocalComputation`）**，即它按配置在"云端/本地"之间分派，
并实现了"云端失败回退本地"的路径（`LaunchComputation ⇄ LaunchLocalComputation` 互调）。

**真正的云端实体不在导出层**，而是内部虚函数：

| 目标 | RVA | 证据 |
|---|---|---|
| `Engine::CloudEngine::v2`（即 `Engine::CloudEngine::Run`） | **`0x26A60`** | 同时引用 `"CloudEngine::Run "`、`"Launching cloud engine "`、`"/pb/"`、`"PUT on "`、`"GET done (response size = "` |
| HTTP/1.1 请求构造 | `0x6DAB80`、`0x6DC480` | 引用 `"HTTP/"` |

* 使用 Boost.Asio 手写 HTTP 客户端（`HTTP/`、`GET `、`PUT `、`Host: `、`Accept: */*`、`Connection: close`、`Content-Length: `）。
* 路径：`/pb/`（提交问题 problem）、`/sol/`、`/best_sol/`（取解），载荷区分 `final` / `intermediate`。
* 服务器：`cns1.optalog.com;cns2.optalog.com`（分号分隔的主备列表）——注意该字符串
  **只在 `LaunchLocalComputation`（`0x2AB0`）里被引用**，作为参数传给 `LaunchComputation`。
* 序列化：JsonCpp；调试转储 `c:\Temp\cns.pb.json`，报告 `c:\Temp\computation_solution.html`。
* 异常体系：`Utils::ConnectException` / `ResolveException` / `TimeoutException` / `BadResponseException`
  （对应字符串 `can not connect` / `can not resolve` / `timeout error` / `response failure`）。
* `Utils::OstreamSink<NestingSinkModel>` 把中间解推送进观察者。

### 6.4 计算控制族的分派

`WaitNextSolution` / `WaitComputationTermination` / `GetComputationStatus` / `CancelComputation` / `TerminateComputation`
都以 `cmp byte ptr [rcx+0x48], 0` 起手，并在日志里用字面量 `"Local"` / `"Cloud"` 区分两条分支
（`Order+0x48` 即计算模式字段）。

### 6.5 引擎/观察者模型

RTTI 给出的完整骨架：

```
Engine::Engine (abstract)
 ├─ Engine::CompositeEngine     Engine::MultiEngine      Engine::NestingEngine
 ├─ Engine::CloudEngine         Engine::DelayedEngine    Engine::InfiniteEngine
 ├─ Engine::EquivalentEngine    (MakeMaxTimeEngine / MakeSkipSmallTimeEngine 工厂)
 └─ Observer: BestObserver  CompositeObserver  EquivalentObserver
Multi::Supervisor  ←→  Multi::Strategist / AdvancedStrategist / StrategyAdder / StrategyDescriber
                        Multi::SheetSelector (All/Largest/Random/NoMix)
                        Multi::Nester 派生族（见 §7.2）
Multi::Node / TerminalNode / SplitNode + Multi::BeamNesting   → beam search 状态树
```

`NewNestingFound` / `NewIntermediateSolutionFound` 是观察者回调点，`Utils::Canceller` 提供中止令牌。

---

## 7. 子系统算法

> 7.0 为本人独立验证的骨架证据（可复现）；7.1–7.5 为分项深挖，细节见对应
> `findings_*.md`。

### 7.0 算法骨架（已独立验证）

**(a) 几何内核是自研的，不是 Clipper**

全串扫描结果（[`out_29.txt`](out_29.txt)）：

| 特征串 | 命中 |
|---|---:|
| `Clipper` / `ClipperLib` / `ClipperOffset` / `PolyTree` / `IntPoint` / `SimplifyPolygon` | **0** |
| `boost::geometry` / `bg::` | **0** |
| `CGAL` / `Eigen` / `gmp` / `mpfr` | **0** |
| `genetic` / `chromosome` / `population` / `mutation` / `crossover` / `fitness` | **0** |
| `[Mm]inkowski` / `NFP` / `NoFit` / `no_fit` | **35** |
| `ClpSimplex` / `ClpModel` / `CoinLp` / `CoinPackedMatrix` / `OsiClp` | **37** |
| `beam` / `Beam` | **33** |

自研几何/引擎类（RTTI 与 shared_ptr 实例化串）：

```
Geom::MultiPolygon                 PartPolygon   RealPolygon   PolygonProxy
OffsetManager   OffsetEvaluator    OffsetMultiEvaluator        CheckOffset
NoFitStrips     NoFitMap           NoFitMultiThreadComputer::RunAllComputations
HullSurf        GetNestableOffset  GetInflatedModulesGeometries  GetRing
IsGeometryValid(inflated)          ComputeNoHoleRings
```

典型断言/参数串：`(polygons.size() == 1u) && "internal error: no outer boundary"`、
`part.geometric_infos().hull().size() == 1`、`external_rings.size() == 1u`、
`point_number < ring.size()`、`offset2 %g`、`Offsets computed `、`nesting_offset_ratio`、
`CheckOffset`、`!detect_correct_invalid || IsGeometryValid(inflated)`。
→ 几何模型为 `Geom::MultiPolygon`（外环 + 内孔），零件带 `geometric_infos().hull()`，
偏移量由 `OffsetManager` 统一管理（`parameters.m_offset_manager`、`nc.m_offset_manager`）。

**(b) 搜索是 beam search + 多策略竞争**

* `Preparing tree for beam ` + `Multi::Node` / `TerminalNode` / `SplitNode` → 显式搜索树；
* `beam_distinct_angle` → 对候选角度去重（旋转离散化）；
* `Multi::Supervisor` / `AdvancedStrategist` / `StrategyAdder` / `StrategyBasicAdder` /
  `StrategyDescriber` + `PartUpdaterLimiter` + `NestingContextPool` → 策略注册与并发调度；
* `Engine::` 家族 + `Observer`（`BestObserver` / `CompositeObserver` / `EquivalentObserver`）→ 多引擎竞争取最优；
* 取消/剪枝：`CompactCanceller` / `RCompactCanceller` / `NoFitMapCanceller` / `SupervisorCanceller` / `Tiling::WarpCanceller`。

**(c) 矩形快速路径 / 矩形对偶**

参数串：`enable_rectangle`、`force_rectangle`、`tooling_with_rectangle`、
`nb_iterations_before_rectangle_advance`、`nb_iterations_before_rectangle_dual`、
`nb_rectangle_advance_try`、`nb_rectangle_try`、`rectangle common cut`、`Multi::Rectangle`、`Multi::RectangleNester`、
`Tiling::BoxMultiTiler`。
→ 存在"把零件用矩形包围盒近似后先用对偶/LP 快速求解、再精化"的两阶段路径
（`rectangle_nester.cpp`、`tiling_nester.cpp` 为独立源码单元）。

**(d) 定价 / LP（"price" 层）**

存在一套完整的 **`Lp::LinearProgram` ← `Coin::CoinLP`（封装 COIN-OR Clp）**
与 **`Prc::PriceComputer`** 家族（`BoxPriceComputer` / `HullPriceComputer` / `AlphaPriceComputer` /
`LinearCombinationPricer`，各 5 个虚槽；`Prc::DimAlpha` / `SurfaceCoeffs` / `BoostAlpha` 只有 RTTI 名、无多态），
以及 `Row::Distancer` / `BasicDistancer` / `Squeezer`。
Clp 侧证据：`ClpSimplexDual.cpp`、`CoinLpIO.cpp`、`CoinLpIO: is_sense()`、
`** Objective offset is %g`、`inf obj %g, true %g - offsets %g %g`、`restoring objective of %g`。
**这些类是被真实构造并可从嵌套引擎到达的（见 §7.3），不是死代码。**
另有一段标准 **LSQR** 终止判据字符串块（RVA `0x9A74A0`），与本 LP 栈**无引用关系**（独立静态库残留）。

**(e) 角度优化与 WKT 输出**

`GetNestingAngle`、`NewLocalAngleOptimize`、`_angle`、`angle_st` → 旋转角搜索；
`POLYGON` / `MULTIPOLYGON` / `LINESTRING` / `RECTANGLE` + `boost::starts_with(sub_strings[0], std::string("ELEMENT_PATH"))`
→ 几何以 **WKT** 形式序列化（供 SVG/DXF/报告与云端传输）。

### 7.1 几何：自研精确内核 + No-Fit Polygon（边界 Convolution）

**几何是两套自研内核，没有任何第三方几何库：**

| 内核 | 源码目录 | 数值表示 |
|---|---|---|
| **精确内核** | `..\exact\*`（`convolution.cpp`、`boolean.cpp`、`path.cpp`、`geom.cpp`、`geom_conversion.inl`） | **int64 定点**，长度定标 `1e10`；叉积/行列式用 **128 位**（`imul/mul + adc/sbb`） |
| 浮点内核 | `..\geom\*`（`ring.cpp`、`element_path`、`layered_multi_polygon`、`convexifier`、`svg_io`） | `double` |

#### 数据结构（指令级证明）

```
Point        { double x, y }                       = 16 B
Ring         = std::vector<Point>                  = 24 B
Polygon      = 48 B { Ring  m_external_path   @+0x00
                      vector<Ring> m_internal_paths @+0x18 }   // 成员名来自断言行
NoFitGeometry(= NFPMap handle) = 24 B { vector<Polygon> result @+0x00 }
NoFitContext = 240 B (0xF0)
```

证据：`NoFitGetNumberOfExternalPolygons`（`0x89D0`）做 `长度 / 48`；
`DeleteNoFitGeometry`（`0x8A10`）按 `0x30` 步长递归释放；
`GetRing`（`0x7270`）断言 `external_number < map->result.size()`（`cns_no_fit.cpp:483`）
与 `(internal_number-1) < inners.size()`（`:490`）；
两个访问器 `0x5C5F50` = 恒等（外环）、`0x5C5F60` = `lea rax,[rcx+0x18]`（内孔）。

`NoFitContext` 布局：`+0x78` 与 `+0xA8` 是两个
`std::map<Key(4×int64), vector<Polygon>>`（**NFPMap 缓存**，value 在节点 `+0x40`）；
`+0xD8` = 已缓存多边形总数，**超过 `0x1312CFF`（19,999,999）就清缓存**；
`+0xE8` = `m_max_complexity`（由 `NoFitSetMaximumComplexity` 直接写，0 时取默认 **25000 = 0x61A8**）。

#### NFP 算法链路（证明）

```
GetNoFitMap 0x8AC0 / GetNoFitPlacementMap 0xA620
  └─ 0x665BF0  缓存"取或算"
       └─ 0x585CA0
            ├─ 0x6863C0  ToExactPerimeter(.., tol=1e-6)   ×2   → 定点化 (×1e10)
            └─ 0x5A2530 → 0x5A11B0 → 0x59E9D0 "NoFitMapWithoutHoles"
                                  → 0x59CD10 → 0x59C560
       └─ 0x687080  转回 double
卷积本体: ..\exact\convolution.cpp::ConvolutionRaw  0x596F20
          （断言 max_size >= union(size1,size2)，行 331）
   核心 0x596100 (3605 B):
      0x595A80  生成 40 B 有向边记录（用 128 位叉积 0x58E450 判凸/凹）
      0x596000  生成 64 B Edge 记录 {A@+0, B@+0x10, C@+0x20, bool, bool}
      主循环 0x596231–0x59631F：**仅用 (dx,dy) 的符号**把方向分到象限 1..4
        1=(dx>0,dy>0)  2=(dx>0,dy≤0)  3=(dx≤0,dy<0)  4=其余
      按该极角键输出 40 B 事件记录 {tag, quadrant, dy, dx, ±1, flags, index} 到 [out+0x48]
```

→ **极角归并完全不用 `atan2`**，全部是 **128 位精确谓词**（`0x58E450`）。
全库唯一的 `atan2` 是 `0x634C70`（41 字节，x87 `fpatan`），只被
`Geom::SignedAngleInRad`（`0x5C5280`，`atan2(cross, dot)`）使用。
`ConvolutionRaw` 对同一对多边形调用核心两次并交换两者（`r9d = 1` 再 `0`，返回值 `xor 1`），
即分别得到两个方向的 NFP。

> 说明：**算法结构（象限分类 + 事件归并 + 精确谓词）是证明**；
> "这等价于教科书式 edge-merge Minkowski 和"是**推断**。

#### 偏移（inflate / gap）（证明）

* `AddInflatedToolPathToPart`（`0x12C60`）：对 `[part+0x50..0x58]` 用 `+inflate` 调用 `0x128E0`，
  再对 `[part+0x60..0x70]` 用 **`btc` 取反符号位 = `-inflate`** 调同一函数
  ⇒ **外轮廓 `+gap`、内孔 `-gap`**（**没有** JoinType / MiterLimit 概念）。
* `0x128E0` → 精确偏移 `0x58A7E0`（3388 B）：`N = floor(dist/step + 0.5)`，`N ≤ 1` 直接返回，
  否则**分 N 步增量偏移**。`NewExternalOffset`（`0x58B520`）前置断言 `radius >= 0.0`。
* gap 落点：`SetExtraGapOnPart`（`0x14450`）→ `part[+0x10]`；
  `SetDefectGap`（`0x109C0`）→ `order[+0x118]`；
  `SetInterpartGap`（导出 RVA **`0xCF20`**，同池断言 `(gap >= 0.0) && "Negative part gap unsupported"`）。

#### 关键常量

| 值 | 地址 | 用途 |
|---|---|---|
| `1e10` | `0x9AD708` | 长度定点缩放因子；`round(v * 1e10)`（编译器写法 `v/360*3.6e12 + 0.5` 后取整） |
| `3.6e12` / `360.0` / `0.5` | `0x9AC838` / `0x9AC830` / `0x9AC840` | 同上（角度→定点） |
| `1e-6` | `0x9AC818`、`0x9DCB20` | NFP 容差 |
| `1.0` / `0.5` / `0.0` / `-0.0` | `0x9DCB10` / `0x9DCB18` / `0x9DCB28` | 偏移 |
| `25000 = 0x61A8` | 立即数 | `m_max_complexity` 默认值 |
| `19999999 = 0x1312CFF` | 立即数 | NFPMap 缓存清空阈值 |

#### 未确认

* ~~point-in-polygon / 绕数例程未定位~~ → **结案为结构性结论**（[`findings_geometry.md`](findings_geometry.md) 附录）：
  精确谓词 `0x58E450` 的**全部 13 个调用者已穷举**（均在 `..\exact\*`，都是线段/环的相对位置分类外壳，如 `0x58C0C0`/`0x58C110`/`0x58C170`/`0x595930`/`0x595990`）；
  旧候选 `0x576470`/`0x573CD0` **被否定**（前者是 `..\common_cut\matrix.cpp` 的 40 字节网格矩阵构造器，两者都不调用精确谓词）；
  `Verify::DetectOverlap 0x99EAC0` **零调用者** ⇒ 是断言消息构造器（立即数拼出 `"DetectOv"`+`"Verify::"`+`"erlap"`）即**死代码**；
  包含测试**以内联 + 断言形式存在**：`..\geom\ring.cpp`（`0x5C5896`）与 `..\nesting\nesting.c…`（`0x16C5EB`）两处串簇，断言表达式 `old.Contains(nnp.m_window)` 被 `0x1C1A60` 引用；
  判据已从其指令读出：**`+0x60`/`+0x68` 窗口对 + 容差 `0x9BFD30 = 0.001` + `ucomisd`**（工程侧 `geom::kWindowContainEpsilon`，并已在 `test_recovered` 中绑定）。
  候选：`0x576470 GetIntersectingIndex`、`0x573CD0 GetOffsetedGeometry`（均在 `..\common_cut\matrix.cpp`）。
  真正的几何谓词是 128 位行列式 `0x58E450` 与 `SignedAngleInRad` `0x5C5280`。
* `NoFitGenerateSvgNesting`（`0x9550`）/ `NoFitGenerateSvgGeometry`（`0x9790`）只确认"不做几何计算"。
* `NoFitMapCanceller`、`NoFitMultiThreadComputer::RunAllComputations`、`..\tiling\nofit_mapper.cpp`（`0x7E6010`）仅确认存在。

（完整细节与文件→函数映射见 [`findings_geometry.md`](findings_geometry.md) 与 `out_g_filemap2.txt`）

### 7.2 搜索：多策略并发 + 迭代改进 + 束/树搜索 + 后处理压缩

> 要点来自 `findings_engine.md`（逐条 RVA 与 `证实/强推断/未确认` 标注）。

#### 搜索范式的定性结论（已证实）

* **不是遗传算法**（无任何 GA 字符串）；
* **不是纯随机重启**：`Multi::NestingNester` 内部**自带 `std::mt19937`**
  （构造器 `0x342E0` 413 B 内 `imul eax,eax,0x6C078965` + `[+0x9F8] = 0x270 = 624`）
  ⇒ **带随机扰动的确定性局部搜索**；
* 本质是 **"多策略并发 + 迭代改进 + 束/树搜索 + 后处理压缩" 的混合**。

#### 引擎与调度

| 环节 | 实现 |
|---|---|
| 引擎接口 | `Engine::Engine` 只有 **1 个业务虚函数 `Run`**（vtable 3 槽：D1/D0 析构 + `Run`） |
| 时间闸门（总闸） | `Multi::SupervisorCanceller::ProbeCancel` @ `0x30030`：`elapsed / Problem[+0x408] > 1.0` → 置粘滞标志并用 `__gthread_cond_broadcast` 广播取消 |
| 其它取消器 | `Multi::CompactCanceller` `0x7D2610`（压缩阶段）、`Multi::NoFitMapCanceller` `0x7D29F0`（NFP 阶段）、`Tiling::WarpCanceller` `0x7D7940`、**`Multi::RCompactCanceller` `0x7D2CB0` = `xor eax,eax; ret`（旋转压缩阶段不可取消）** |
| `Utils::Canceller` 基类默认 | `0x7D7D20` = `xor eax,eax; ret`（永不取消） |
| 调度 | `MultiEngine::Run` 读 `Problem` 的 `seed` / `nb_max_threads` / 策略表 → 构造 `AlgoParameters`（`0x4EC00`）与 `Supervisor`（`0x2F860`/`0x2F2C0`）→ `Supervisor::Run`（`0x827F0`）按 `StrategyDescriber` **每策略一线程** |
| 级联预算 | `AdvancedStrategist::operator()` `0x2DF60` 选 4 条路（mode 2/3/4/默认），每条经 `0x2CCF0` 展开成 1–4 个**预算递减**的变体（`n → 2 → (n+1)/2 → n−1`） |
| 观察者 | `Observer` 6 虚槽；`NewIntermediateSolutionFound` 槽 = `0x755A80` / `0x75CDA0`；`BestObserver` 择优；`CompositeEngine` 用 `CompositeObserver`（`0x8D4500`）聚合子引擎 |

#### Nester 家族（每个类的放置启发式）

所有 Nester 的公共接口（6 虚槽）为
`v0 dtor / v1 deleting-dtor / v2 Name()（返回常量串）/ v3 Prepare() / v4 Estimate() / v5 Run()`，
其中 v5 永远是该类最大的函数。

| 类 | vtable | v5 主体 | 启发式 |
|---|---|---|---|
| `Multi::NestingNester` | `0xA3B690` | **`0x378E0`（14374 B，主打包器）** | 见下 |
| `Multi::TilingNester` | `0xA3B5A0` | `0x46940`（16258 B，最大） | 用 `Tiling::*` 把板材切成**重复图案**（`BiModulePattern` / `MultiOrientedPartPattern` + 各种 Evaluator）再打包 |
| `Multi::RowNester` | `0xA3BB30` | `0x913E0`（12380 B） | 按 **行/条带** 放置；字符串 `Row ` / `Pipe `，由 `0x8F210(..., r8d=1)` 的第二参数在 Row/Pipe 间切换 |
| `Multi::MultiTorchNester` | `0xA3B8A0` | `0x7BCC0`（12232 B） | 多割炬模式（配 `Tiling::MultitorchEvaluator`） |
| `Multi::CompactNester` | `0xA3B610` | `0xB13D0`（9393 B） | 在已有嵌套上先做 compaction 再评估 |
| `Multi::NoFillNester` | `0xA3B530` | `0x7F240`（8440 B） | **禁止"填空/补洞"**（字符串 `NoFill(`），只做整体排布 → 提升多解多样性 |
| `Multi::DatabaseNester` | `0xA3B740` | `0x5B250`（4495 B） | 用 `tree_db` + `bucket_manager` **缓存复用**历史 nesting |
| `Multi::RectangleNester` | `0xA3B800` | `0x75FB0`（5261 B） | **矩形快速路径**（`enable_rectangle` / `force_rectangle` / `nb_rectangle_try` / `nb_iterations_before_rectangle_dual`） |
| `Multi::FlipNester` | `0xA3B490` | `0x4B870`（3496 B） | **整题镜像翻转后再嵌套**（内联字符串 `"temporary_flipped"`，可配 `flip_parts_ratio`） |
| `Multi::FilterNester` | `0xA3B4F0` | `0xB3AE0`（2254 B） | 先用廉价过滤器/下界剪掉不可能改好的解 |
| `Multi::LimitedNester` | `0xA3B650` | `0x4AB40`（1650 B） | 限量包装器（前 N 个零件/角度），与 `FlipNester` 共享代码 |
| `Pack::BestNester` | `0xA3B400` | `0x15E410`（316 B） | 遍历子 nester（`0x15E447` 取 begin/end）逐个调用虚 `+0x10` 槽后择优 |
| `Pack::KnapsackNester` | `0xA3B430` | `0x15DD70`（59 B） | **背包式选件**（读 `[rdx+8]`、`[rdx+0x14]` 作容量/件数转调 `0x15D1F0`） |
| `Pack::RecursiveNester` | `0xA3B460` | `0x165680`（125 B） | **递归装箱**（主体 `0x164FE0`） |
| `Multi::CompositeNester` | `0xA3B790` | 未确认 | 跑一组子 nester 取最优 |

`Multi::NestingNester` 的构造器证实其对象布局：
`[+0x18]/[+0x20]` = `StrategyDescriber` 的 mode/flags 与 double 参数；
`[+0x28]` = 迭代/预算上限；`[+0x30]` = 一个比例（很可能是 `nesting_pow_boost`，有断言 `>= 1.0`）；
`[+0x38..+0x9F8]` = **MT19937 状态**；`[+0xA00]` = `Tiling::PackerCache` 之类。
`Run` 的主要被调用者包括 `0x3F070`/`0x434D0`（`nesting_context.cpp`）、
`0x344D0`(6748 B) / `0x35F30`(6436 B)（两段核心排布）、以及 `tiled_multipart.cpp` 区的
`0x185750`/`0x185A40`/`0x187020`/`0x189CA0`。

#### 束/树搜索（已证实）

* `Multi::TerminalNode`（vtable `0xA3B570`）的评分槽 = `0x974F0` = **`movsd xmm0,[rcx+0x48]; ret`**
  → 叶节点价值在 `+0x48`；`Multi::SplitNode`（`0xA3BB70`）评分槽 = `0x97510`，内部节点在 `+0x50`。
* 树数据库 `..\nesting\algos\tree_db.cpp`：`FindNode` = `0x1C12D0`（断言 `itr != m_nodes.rend()`），
  另有 `0x1C16E0`/`0x1C18A0`/`0x1C1A60`/`0x1C1F30`/`0x1C2110`/`0x1C37A0`/`0x1C4350`。
* **束搜索的树准备 = `0x22CCA0`（2916 B）**：打印 `Preparing tree for beam `、`Length reduced `、
  `Simplified `、`Offsets computed `、`Tree Logged `；调用 `0x1C1650`（tree_db）后在互斥锁
  （`0x63F6C0`/`0x63F6B8` = `pthread_mutex_lock/unlock`）保护下填充 beam 参数。
  **beam width 不是常量 —— 结案（附原因）**：它是选项表里的用户参数，三个键分别为
  `beam_width`（读取点 `0x4EECB`）、`beam_advanced_width`（`0x4F342`）、`beam_expert_width`（`0x4F365`），
  运行期打印点 `'Beam width='` 在 `0x655DC6`。
  逐键与读取点见 [`findings_engine.md`](findings_engine.md) 附录「完整选项键表」；
  ⇒ 早先"找不到魔数"是**预期结果**（值由参数表给出），不是信息缺失。

#### Compaction 后优化（已证实）

* `Compact::Compacter::Implementation`（vtable `0xA3D470`）的 v2 = `0x7F4140`（115 B）：
  取几何对象 → `operator new(0x1E8)` → 调 **`0x252B60`（1389 B，工作内核）**。
* `0x252B60` 的关键算式：
  ```
  [obj+0x10] = min(f1, f2) / 10.0        ; 常量 10.0 @ 0x9C2BB0
  构造区间 (-f1, 0, f1+f2) 的网格 → 0x5CA780 / 0x5C6BE0
  0x2664F0(obj+0x18, grid, 0, 1)         ; 枚举网格
  逐个候选做 move
  ```
  ⇒ **Compaction = 以 `min(宽,高)/10` 为网格步长的"滑动 + 旋转"局部搜索**，
  `[+0x10]` 就是位移步长（tolerance / mesh）。
* `compact.hpp` 的具名函数：`CompactAux` = `0x1DA0C0`（14251 B）、
  `RotateCompact` = `0x1F2D00` + `0x678230`、`NoOverlap` = `0x678630`。
  **`RotateCompact` @ `0x678230` 的接受测试**：`if (1e-6 > param) return 0;`
  （常量 `1e-6` @ `0x9BF5D0`）→ 改善阈值过小就直接放弃。
* 字符串：`compacting ...`、`before_shake`/`shaker_`/`after_shake`（**"shake" 抖动**）、
  `Compaction success :`、`Compact cancelled !`、`Swap Postop begin` / `Trying swap ` /
  `Swap 180 begin` / `Trying swap180 `（180° 交换）。
* `RCompact::RotateLogger`（vtable `0xA533D0`，8 槽）**全是 1–5 字节空函数**
  ⇒ 纯日志钩子，接受/拒绝判定在 `RotateCompact` 内部。
* 参数键：`enable_last_compaction`、`enable_rotate_compact_postop`、
  `nb_iterations_before_rotate_compact_postop`。

#### 收尾三连 pass（已证实）

核心 `0x1B33B0`（9910 B）同时引用 `Finalize : Parts renested in holes`、
`Finalize : Nesting packed bottom left`、`$$$$$$$$$$$$$ CLUSTERS $$$$$$$$$$$$$$$$$$$$$ `、
`USE_POSTOP => `、`postop_estimate`、`Using seed `，并按此顺序执行：

1. **`postop` 通用后处理**（`postop.cpp`，含 `USE_POSTOP` 开关与 `postop_estimate` 评分）；
2. **`Finalize : Parts renested in holes`** —— 把零件重新塞进已有 nesting 的孔洞：
   `RenestInHoles` = `0x40720`，`Multi::HoleRenester`（无 vtable）；
   相关几何断言都带 **`1e-6` 容差**；
3. **`Finalize : Nesting packed bottom left`** —— 经典 **BL/BLF 稳定化**：
   在不重叠前提下把所有零件尽量推向左下（`postop_move.cpp`，`0x1E1BF0` 等），
   使解规范化、便于去重与比较。

（完整细节、策略描述符结构与未确认项见 [`findings_engine.md`](findings_engine.md)）

### 7.3 数学规划/定价层（`Lp` / `Coin` / `Prc` / `Row`）

> 这一层最容易误判，因此下面明确区分"已证实"与"未确定"。
> 分项深挖见 [`findings_lp.md`](findings_lp.md)。

#### 类层次（已证实，RTTI typeinfo 在 `0xA17D40`–`0xA17EB8`）

```
Prc::PriceComputer  (0xA17D50)
 ├─ Lp::LinearProgram (0xA17D40)
 │    └─ Coin::CoinLP  (0xA17EA0)          // 封装 ClpSimplex
 ├─ Prc::BoxPriceComputer    (vtable 地址点 0xA3B0C0)
 ├─ Prc::HullPriceComputer   (0xA3B100)
 ├─ Prc::AlphaPriceComputer  (0xA3B140)
 └─ Prc::LinearCombinationPricer (0xA3B180)
Row::Distancer (0xA17E20)
 ├─ Row::BasicDistancer      (0xA3B1C0)
 └─ Row::Squeezer            (0xA3B1F0)
```

`Prc::BoostAlpha` / `SurfaceCoeffs` / `DimAlpha` **只有 RTTI 名字串、全库零指针引用**
⇒ 是非多态的数据结构（不是可实例化的策略类）。

#### 这一层是**活的**（已证实，且纠正了一个常见误判）

对全库代码段做**全量线性反汇编**，搜索 `lea reg,[rip+X]`，X 取各 vtable 的**地址点**（`vtable+16`）：

| 类 | 地址点 | 被 `lea` 引用的构造/装配点 |
|---|---|---|
| `Coin::CoinLP` | `0xA3B280` | `0x26777C`（在 `0x267760` 内） |
| `Prc::BoxPriceComputer` | `0xA3B0C0` | `0x4D9AE2`、`0x7CA0E2` |
| `Prc::HullPriceComputer` | `0xA3B100` | `0x4D9B12`、`0x7CA152` |
| `Prc::AlphaPriceComputer` | `0xA3B140` | `0x4D9B4E`、`0x7CA1DC` |
| `Prc::LinearCombinationPricer` | `0xA3B180` | `0x4D9D04`、`0x4D9E22`、`0x4D9FD9`、`0x7CA5E7` |
| `Row::BasicDistancer` | `0xA3B1C0` | `0x136AFE` |
| `Row::Squeezer` | `0xA3B1F0` | `0x138A34`、`0x138BE8`、`0x138CAA`、`0x138D74` |

> ⚠️ **方法学提醒**：如果按 vtable **头部**地址（`vtable+0`，即 `0xA3B270` / `0xA3ADA0` 之类）搜索，
> 会得到"0 引用"的结论并误判为死代码 —— 因为 C++ 的 vptr 指向的是**地址点**（`vtable+16`），
> 代码里只出现地址点。本报告使用地址点，故结论为"**被构造**"。

进一步用**全库 `call` 指令扫描**（145,081 条 `call`，8,066 个目标）建立调用图并向上爬升，
得到到达定价器的路径，例如：

```
Multi::CompactNester::Run (0xB13D0)
  -> 0xB0380 -> 0x67460 -> 0x1CD290 -> 0x1CB100        (postop.cpp 区)
     -> 0x1A6020 -> 0x1A5B20 -> 0x4D64C0                (+0x1A6320 → 0x1AEE00 等)
        └─ 0x4D64C0 = 定价器工厂：构造 Box / Hull / Alpha / LinearCombinationPricer
```

即：**定价器可达自嵌套引擎的压缩/后优化路径**（`Multi::CompactNester`），另有
`0x185EF0`、`0x4D84D0` 等入口。`Coin::CoinLP` 的构造器 `0x267760` 由 `0x267730` 调用，
上游可达 `0x59AC0`（含字符串 `"linear"`）与 `0x24E2D0` 链。

#### 定价器在算什么（已证实结构）

| 类 | 关键实现 | 含义 |
|---|---|---|
| `BoxPriceComputer` | 主算法 `0x7C9D90`，面积公式 `(y1-y0)*(x1-x0)` @ `0x7CB750` | 返回**最大候选包围盒的面积** |
| `HullPriceComputer` | slot2 = `0x7CA130` = `movsd xmm0,[rdx+0x48]` | 返回预置的**凸包面量系数** |
| `AlphaPriceComputer` | slot2 = `0x7CA1B0` = `movsd xmm0,[rdx+0x68]` | 返回预置的 **α-shape 面量系数** |
| `LinearCombinationPricer` | slot2 = `0x7CA370` = `Σwᵢ·priceᵢ / Σwᵢ`；slot3 `0x7CA6C0` 构造 `"Combined(a,b,…)"` | **加权平均组合**多个 price |
| `PriceComputer` 本体 | `0x7C4C70` / `0x7C4F90` 均 `[obj+0x10]` 尾调用内部实现的 `+0x28/+0x30/+0x38/+0x40` 槽 | **策略包装器** |

类名串是内联构造的：`"BoxSurface"`（`0x7CA100`）、`"HullSurface"`（`0x7CA170`）、
`"AlphaPrice "`（`0x7CA200`）；源码路径串 `..\rprice\price_computer.cpp`；
断言/日志 `pricer.m_prices[p] >= 0`（`0x9C1CC0`）、`AlphaSurfacePricer `、`DimPricer `、
`Pb pricing `、`..\nesting\algos\old_beam.cpp`、`bucket_manager.hpp`。

#### `Coin::CoinLP` 的结构（已证实结构，方法名推断）

* 布局：`vptr[+0]` + **`ClpSimplex* [+8]`**。
* 末 4 个虚槽是转发 thunk，与 `ClpSimplex` 的槽位吻合：
  `0x7CB700 → [rax+0x248]`、`0x7CB710 → [rax+0x228]`、`0x7CB740 → [rax+0x230]`、
  `0x7CB720 → jmp 0x7CA830(r8d=1)`。
* 全局构造器 `0x6792C0` 用 `±inf` / `±1.0` 常量（`0x9C2DF8`/`0x9C2E18`/`0x9C2E20`/`0x9C2E30`）设上下界与目标。
* `0x7CA830`（3778 B）对 16 字节 `{double,int,int}` 记录做有序插入/去重/扩容
  ⇒ **`addColumn` / `addRow` 装配**（哪一个未确认）。
* 注意：`ClpSimplex` / `ClpModel` **不在 RTTI 名表**中（COIN 的 70 个类名在 `0xA21120`–`0xA21ED0`，
  只有 `ClpMatrixBase`/`ClpPackedMatrix`/`ClpPresolve`/`ClpDualRow{Dantzig,Steepest}`/
  `ClpPrimalColumn{Dantzig,Steepest}`/`CoinModel` …），Clp 的静态链接由
  `0x9C9E1F`（`ClpSimplexDual.cpp`）、`0x9D2D30`（`CoinLpIO.cpp`）证实。

#### `Row::Squeezer`（已证实结构）

区间**记忆化缓存**：两棵 `map`（`[+0x240]` / `[+0x248]`，节点 `{key, lo, hi, value, height}`）；
查询区间 `[lo,hi]` 被已有节点包含则命中，否则算完后插回。`0x138BE0`/`0x138CA0` 是析构。
⇒ 行生成层的**去重/剪枝缓存**（成本函数 `0x1380D0` 的语义未确认）。

#### Clp 究竟在解什么（**已结案**，见 [`findings_lp_use.md`](findings_lp_use.md)）

对 `0x585CA0` 之外的 LP 侧重新做了调用点扫描 + `BuildAndSolveLp` 全反汇编，结论：

* **`Coin::CoinLP` 不是死代码，而且被使用。** 它由 `0x267760` 构造（实例 0xF0=240 B，
  `vptr[+0]` + 求解器对象 `[+8]`），由内部名已恢复的 **`BuildAndSolveLp`（`0x7D7200`，
  1520 B，源文件 `..\multi\database.cpp`，断言 `biggest_sheet->price()` 在第 450 行）** 驱动。
* **它解的是一条"板材选择"集合覆盖 LP**：
  ```
  min  Σ_sheet  price(sheet) · x_sheet
  s.t. 对每个零件 p :  Σ_sheet count(sheet, p) · x_sheet ≥ demand(p)
       x_sheet ≥ 0
  ```
  装配方式：`slot 4`（`0x6792C0`）**每张板材加一列**（代价 = `sheet.price()`）；
  `slot 5`（`0x679670`）**每个零件加一行**（系数 = 该板材在该零件上的计数，右端 = 需求）；
  某零件在任何板材里都不出现时插入**单位系数松弛列**（常量 `0x9B08B0 = 1.0`）；
  `slot 8`（`0x679D00`）提交并求解。
* **解被消费**：Database 侧 `0x6A6AD0` 解完后 `call [vptr+0x50]`（slot 10 → 求解器 `vt+0x228`）
  取解向量，再回映到板材记录上。
* ⇒ **不是 Dantzig–Wolfe 主问题**，而是覆盖式选板 LP。`findings_lp.md` §6 的
  "整套 `Lp::`/`Coin`/`Prc::`/`Row::` 是未接线死代码"**结论作废**（它搜的是 vtable **头部**
  地址，而 vptr 指向**地址点** `vtable+16`）。
* 求解器是 **COIN-OR Clp 1.15.3**（静态链接，经 `OsiClpSolverInterface`）；
  全文件扫描 **OR-Tools 0 命中**（13 个标记）。

#### 仍未确定（已缩减）

1. `Row::Squeezer` 的成本函数 `0x1380D0`：**已全部译出并并入工程** —— 主表达式
   `cost = obj[+0x10] / sin(方向角) − max(|A.v0−A.v2|, |B.v0−B.v2|)`；两道前置闸
   （平行性 `1e-6` @`0x9BCFC0`，区间表逐元素对齐 `0.005` @`0x9BCFD8`）；
   组成原语 `0x5C22D0` 定点角度、`sin` 精确分支、`hypot`；
   工程对应 `row::squeezeCost` / `row::Squeezer`（`test_row`）。
   详见 [`findings_lp_use.md`](findings_lp_use.md) §8。
2. `Prc::BoostAlpha` / `SurfaceCoeffs` / `DimAlpha` 的**字段布局仍[未确认]**，但**原因已查清**：
   这三个名字串**并非无引用** —— 它们由反射式**名称注册表 `0x6CC9D0`**（18272 B）在
   `0x6CCB6E` / `0x6CD080` / `0x6CD631` 三处直接 `lea`（此前"零引用"的说法是搜"指向名字串的
   指针"，方向错了）。它们**没有 typeinfo 对象、没有 vtable、没有成员名字串**，注册调用传入的
   rodata 指针落在 `basic_string::substr` 断言串中间、不可读 ⇒ 布局无从反推。
   **[推断，依据充分]**：两个 Alpha 实例被传入的 rodata double **0.5**（`0x9D9C08`）与
   **0.1**（`0x9D9BE8`）就是 `BoostAlpha` / `DimAlpha`（哪个是哪个无直接证据）；5 个 double 的
   系数块最可能是 `SurfaceCoeffs`。详见 §11.2 / §11.3。
3. **定价变体没有"默认值"**：`0x4D64C0`（源文件 `..\pricer\prices_generator.cpp`）把
   Box + Hull + Alpha×2 **全部构造**后交给 `LinearCombinationPricer` 加权平均。
   六个内联构造点见 §7.3 上一版；**1 项结案**。
4. `Pack::KnapsackNester` 消费的 `prices`（断言 `prices.size() == m_problem.GetNumberOfParts()` @
   `..\tiling\packer.cpp:410`）**与 `Prc::m_prices` 不是同一物** —— 不要把两者混淆。
5. LSQR 消息块（`0x9A74A0`）：**归属已定** —— 全库只有 `0x3B84E0` 内的两处引用
   （`0x3BA0A4`/`0x3BA114`），即实现体在 `0x3B84E0`，与本栈无关。
6. `0x7CA830`：**已结案**（先就地 `std::sort` 自己的 `+0x90` 三元组累加器 —— 功能性副作用，
   产出列优先 COO；再渲染成 3 空格分隔文本）。求解在 `CoinLP` slot 8。
7. **新增**：`CoinLP` 内部成员布局与 `slot 5/6/7` 的关系 —— `slot 4` 写三个并行
   `vector<double>`（`+0x18/+0x30/+0x48`），`slot 5/6/7` 写 `+0x60/+0x78/+0x90` 且**是同一个
   "追加三元组"例程的三个变体**（`slot 7` 是无前导块、无间接调用的共享裸核心；
   `slot 6` 比 `slot 5` 多一条 `xorpd` 取负）。**5/6 的参数语义仍[推断]**。
8. **新增**：`Row::` 的接线 —— **`Row::Squeezer` 可达**（`AdvancedStrategist` `0x2DF60` →
   级联 `0x2CCF0` → `StrategyAdder::Add` `0x2C4D0` → `0x8F210` → `0x6AABC0` →
   `0x13C380`/`0x134470` → `0x136B80` → Squeezer 构造器），
   而 **`Row::BasicDistancer` 未构造**（`0x136AE0` 无调用者）。这与 §6 旧结论部分矛盾，
   按地址点重扫后必须分开说。
9. **新增并已并入工程**：`Row::Squeezer` 的**对象图与构造路径**（见
   [`findings_lp_use.md`](findings_lp_use.md) §12）——
   外层 `{vptr@0xA3B1F0, inner*@+8}`，**inner = 0x270 = 624 字节**，其中
   `inner[+8] = 1` 就是 `0x1380D0` 测的开关、`inner[+0x10] = xmm3` 就是成本公式的阈值；
   `0x13C380` 的循环里 `xmm6 = xmm1` 是**赋值而非取最大**、有效行的贡献被置 **0**、
   差值**不取绝对值**（带符号 max）—— 这三条都已按指令写进 `row::buildSqueezer` 并由
   `test_row` 各钉一条断言（我第一版把赋值写成了取最大，已纠正）。
   **仍未接线到 nester 的具体策略**：原库接线点在策略体 `0x6AABC0` 内部，
   其策略身份（对应哪个导出）**未确认**，故不猜。
10. **策略身份与接线点**（见 [`findings_lp_use.md`](findings_lp_use.md) §13）——
    内联串还原给出 `0x6AABC0` 所在 TU 为 **`..\multi\row_nester.cpp`**、
    `0x1380D0` 为 **`..\row\squeezer.cpp`**、`0x5CD800` 为 **`..\geom\properties.cpp`**；
    地址点 RTTI 解出 `0xA3BB40` = **`Multi::RowNester`**（`0x8F210` 是它的构造函数，
    `Run` 槽 5 = `0x913E0`）。
    **⚠️ 并更正一处**：`0x6AABC0` **不是**策略体，而是
    `Multi::RowNester` 构造函数里 `new(0xD0)` 出来的 **208 字节 core** 的初始化函数
    （`0x8F210` 是它的唯一调用者；`0x913E0` 不调它）。因此 `+0x18`(阈值)/`+0x20`(系数)/
    `+0x40`(mode)/`+0xC0`(Squeezer\*) 都是**那个 core 的字段**，`RowNester::+0x18` 存的是 core 指针。
    工程已据此改为 `RowNestCore` + `RowNester::core_`（对应 `this+0x18`），
    **构建时机有一处明示偏离**（原库在构造函数里建，本工程 `makeStrategy()` 尚无 `Order`，
    故首次 `run()` 建；结构不变）。
11. **新增并已结案**（见 [`findings_lp_use.md`](findings_lp_use.md) §14）：
    **core 两个 double 的来源**——默认值是 rodata 常量
    `0x9B1A48 = 4.0`（阈值）、`0x9B1A50 = 20.0`（系数）、`0x9B1A40 = 10.0`（`core+8`），
    且可被问题对象的 `+0x1B0` / `+0x1A8` 覆盖（`0x4FC3C0` 返回 `problem+0x1A0` 再取
    `+0x10`/`+8`），gate 是 `problem+0x170` 与 `problem+0x1A0` 两个字节。
    工程里两个默认值**已从 0.0 占位换成真常量** `kRowCoreAt0x18` / `kRowCoreAt0x20`。
    **同一轮又纠正一处**：`0x5CD800` 的产出是**包围盒**
    `{bool@+0, minX@+8, minY@+0x10, maxX@+0x18, maxY@+0x20}`（由 `0x5C8C50` 的逐项 min/max
    证实），元素步长 **0x30**，签名是 `(out, container)` 且**返回 out**；标志极性是
    "**非 0 即跳过**"，所以 `RowView::valid` 已改名为 **`skipExtent`**（我上轮把极性写反了）。
12. **新增并已结案**（见 [`findings_lp_use.md`](findings_lp_use.md) §15）：**配置字段的写入者**
    是两个**命名导出** —— `Pb+0x170` 由 **`SetPipeMode`**（`0xFCF0`）写、
    `Pb+0x1A0..+0x1C0` 由 **`SetCommonCutParameters`**（`0x3C3F0`）写（两者都是整块 qword 拷贝，
    所以"byte 读 / qword 写"相容）。
13. **新增并已结案**（见 §16）：**pipe 分支的实体** —— `0x6AC20A`（pipe 闸置位时跳去处）
    **本身就是另一条配置来源**：`0x4FC3A0 = [[arg]]+0x170` 之后把
    **`Pb+0x188` → `core+0x20`（系数）**、**`Pb+0x190` → `core+0x18`（阈值）**。
    ⇒ 两条互斥来源：**pipe 闸置位用 `Pb+0x190/0x188`；否则若共边闸置位用 `Pb+0x1B0/0x1A8`；
    两者都不满足才用 rodata `4.0/20.0`**。
    **⚠️ 并更正 §15.3 的实现**：上一轮我把 pipe 模式写成"保留默认值、跳过覆盖"（读反了），
    现已按真实次序改正并由 `test_nester` 断言两条来源各自的取值与优先级。
    同轮还确定：**那个"行容器"就是 core 自己的 `std::vector`（`core+0x48`，`begin/end/cap` 三连清零）**，
    元素步长 48 字节、元素首 qword 是一个指针（`0x133190 = lea rax,[rcx+8]`）；
    相邻的 `0x6AC250` 属 **`Multi::SplitNode`**（地址点 `0xA3BB80`），不是 core。
14. **新增并已结案，且更正 §16.3**（见 §17）：行容器是 **`std::vector<Item*>`（元素 8 字节指针）**，
    `Item` 是 `0x1333D0(...)` 造的 **0x90 = 144 字节**对象（`6AB777 [rax]=rdi ; 6AB77A add rax,8`）；
    **0x30 步长属于 `0x13C380` 的第二个循环**（`Item+8` 处的嵌套容器，
    `0x133190 = lea rax,[rcx+8]` 取的正是它），不是外层容器。
    同轮另得：`core+0x40` 的 mode 分派（`0x6AB6B5`）有一条分支以
    **`0x1A3185C5000 = 1.8e12`（180 度定点度）** 作角度参数 —— 与 `0x1380D0` sin 块里的
    180 度魔数**是同一个常量**；`0x134470` 是**逐零件**调用且 `r9 = core+8`（配置块）。
    **仍未确认**：`Item`(0x90 B) 的字段布局与其构造者 `0x1333D0`、嵌套容器元素型别、
    `0x4F7690`/`0x5C4C50`/`0x5C4950` 的作用、`0x134470` 的算法、`core+0x28`/`0x30`/`0x38` 的用途、
    两个 setter 参数块内 qword 与语义的逐一配对。
15. **新增并已结案**（见 §18）：**`Item` 的布局与三层容器结构** ——
    `Item`(0x90 = 144 B，构造者 `0x1333D0`) 的 `+0x00` 是 `partIndex`(dword)、
    `+0x08` 是嵌套 `vector<Elem48>`；`Elem48`(0x30 B) 内含 `vector<Elem16>`(16 B 元素)
    与 `vector<0x18 B 记录>`；外层是 `vector<Item*>`。这**印证**了
    `0x133190 = lea rax,[rcx+8]` 取的正是 `Item+8` 的嵌套容器。
    同轮另收：**`0x4F7690` = `mov rcx,[rcx+0x70] ; jmp 0x547670`**（元素容器入口是 `Part+0x70`）；
    以及 core 的 **`+0x28`/`+0x30`/`+0x38` 在已追踪路径上零读者**（`0x6AABC0` 内读计数 0，
    `0x13C380` 只读 `cfg[+0x10]`/`cfg[+0x18]` ⇒ 被消费的是 `core+0x18`/`+0x20`，链路闭合）。
    **仍未确认**：`Item` 的 `+0x20…+0x88` 字段语义、`Elem48`/`Elem16` 的几何含义、
    `0x547670`/`0x5C4C50`/`0x5C4950` 的作用、`0x134470` 的算法、
    `core+0x28`/`0x30`/`0x38` 是否被别处读取、两个 setter 参数块内 qword 与语义的逐一配对。
16. **新增并已结案**（见 §19）：**`0x134470` 的算法** —— 逐零件扫描 **16 字节条目**的容器，
    对每个通过谓词 `0x5C2E40` 的条目调用 **`0x133DE0(..., core+8)`** 求代价并**保留最小值**，
    把最优条目写进 `*out`；常量 `0x14 = 20`、`0x38 = 56`、
    **`0xD18C2E2800 = 9e11 = 90 度**（与 sin 块同一魔数）。
    由此还确定 **core 的 `+0x18`/`+0x20` 有第二个消费者**（`0x133DE0`），补完了 §18.3(b)。
17. **明确声明不可恢复**（见 §19.3）：**`core+0x28`/`+0x30`/`+0x38` 是否被别处读取，
    用本方法无法判定**。原因：数据库 TU 内 ≤40 B 的访问器里只有 `Pb+0x170`/`Pb+0x1A0`
    两个；全局按偏移扫描会与 130–220 个**无关类型**的同偏移访问混淆。
    已知确切事实仅两条：由两个配置块写入，且在 `0x6AABC0`/`0x13C380` 内**无读者**。
    工程里建模为字段但**未接算法** —— 这是**明说的缺口，不是近似**。

### 7.4 切割工艺特性

> 全部要点来自 `findings_features.md`（逐条 RVA + `已证实/推断/未确认` 标注）。
> **命令式的唯一"落点中心"是内部函数 `Structure::CreateProblem` = `0x1EE50`（15305 字节）**：
> 所有 `Set*` 导出只是写 `LaunchingOrder` 的字段，真正被读取/生效的地方都在这里。

#### 字段落点总表（`LaunchingOrder*`，均由 setter 反汇编证实）

| 偏移 | 含义 | 写入者 | 读取点（CreateProblem） |
|---|---|---|---|
| `+0x08` | 目标函数（枚举） | `SetObjective` `0xCEC0` | `0x20BC8` |
| `+0x0C` | origin | `SetOrigin` `0xD050` | — |
| `+0x28/+0x30/+0x38` | `used_surface_min_offcut_dimension` / `_min_offcut_area` / `_usable_offcut_ratio` | `SetOffcutEvaluation` `0xE2D0` | — |
| `+0x44` / `+0x48` | shear / shear_corner（partial） | `SetShearMode` `0xDDC0`、`SetPartialShearMode` `0xDDF0`（**同时写 0x48 与 0x44**） | — |
| `+0x50` / `+0x58` | `shear_gap` / `shear_repulse_from_borders` | `SetShearGap` `0xCEF0`、`SetShearRepulseFromBorders` `0xDE20` | — |
| `+0x5C` / `+0x60` | 共边模式 | `SetCommonCutMode` `0xE460` | `0x21488` |
| `+0x68` / `+0x6C` | 共边安全标志 / 预设 map 键 | `SetCommonCutSafetyPreference` `0xE940` | `0x2149B`/`0x2149F`、`0x225BD` |
| `+0x70/+0x78/+0x80` | 共边授权 | `SetCommonCutAuthorizations` `0xEAB0` | — |
| `+0x84/+0x85` | `no_holes` / `only_bi_modules` | 同上 | — |
| `+0x88` / `+0x8C` / `+0x90` | **模式标签**（1=用预设 `+0x8C`，0=显式目标 `+0x90`） | `SetCommonCutCuttingPreference` `0xEC90`（写 1/0x8C）、`SetCommonCutObjective` `0xEDF0`（写 0/0x90） | `0x22369` |
| `+0x98` / `+0x9C` | **多割炬模式标签**（1=预设 `+0x9C`） | `SetMultiTorchCuttingPreference` `0xF130` | `0x21533`、`0x21F36` |
| `+0xA8 / +0xC0 / +0xC8 / +0xD0` | 多割炬 allowed / nb_torches / min / max | `SetMultiTorchMode` `0xEF50` | `0x2154F`–`0x215D1` |
| `+0xB0` / `+0xB8` / `+0xD8` | 多割炬派生目标系数 | `SetMultiTorchObjective` `0xF2C0` | — |
| `+0x118` | `defect_gap` | `SetDefectGap` `0x109C0` | — |
| `+0x120` / `+0x124..0x130` | 优先级 / 指定板 origin & objective | `SetSheetPriority` `0x13C90`、`SetSpecificSheetOrigin` `0x13E30`、`SetSpecificSheetObjective` `0x13FE0` | — |
| `+0x128..0x150` | **行模式块**（enable / 3~4 个 gap / alternate） | `SetRowMode` `0xFBF0` | `0x216AF` |
| `+0x158..0x178` | **管材模式块** | `SetPipeMode` `0xFCF0` | `0x216E0` |
| `+0x1F8` | `incompatible_sheets` | `SetIncompatibleSheet` `0x11490` | — |
| `+0x209` | force-on-bottom-border | `CNS_ForcePartOnBottomBorder` `0x1A8F0` | — |
| `+0x220..0x238` | `SetExtraParameters` 6 个 double | `SetExtraParameters` `0x11120` | — |
| `+0x240` | 自动停止 | `SetAutomaticStop` `0xE010` | — |
| `+0x2B0` | 装配组容器 | `CNS_CreateAssemblyGroup` `0x10B50` | — |

#### (A) 共边切割（common cut）

* `0x88` 是**模式标签**而不是普通数值：`1` 表示"使用预设"（预设号在 `+0x8C`），`0` 表示"显式目标"（参数在 `+0x90`）。
  多割炬的 `+0x98` 用完全相同的模式。
* 段结构（`LoadSegment`）：`{ common_cut, left, right, left_index, right_index, valid, linked }`；
  统计项 `number_of_common_cut` / `common_cut_length` / `regarding_length`。
* 取结果：`GetNumberOfCommonCuts` `0xD710`、`GetCommonCut` `0xBA50`
  （断言 `common_cut_number < evaluation.common_cut_segments.size()` @ `0x9ACB10`）。
* 校验器 `0x1C7C0` 会报 `// BadCommonCutGaps`。

#### (B) 多割炬

* `SetMultiTorchObjective`（`0xF2C0`）的完整公式（`a,b,c,d` = 4 个参数）：
  ```
  +0xD8 = a
  t     = max(a/1000.0, b)
  +0xB0 = t / a
  +0xB8 = t > 0 ? (c ? d/t : 0.66) : 0.66
  +0x98 = 0                       // 切回"显式"模式
  常量: 1000.0@0x9AD710, 0.9@0x9AD700, 0.66@0x9AD708
  ```
* `CNS_GetPartTorchInfos`（`0xD870`）断言 `part_index < nested_parts().size()`
  且 `< multitorch_infos().m_infos.size()`，每零件返回
  `{torch_distance, group_number, torch_number, nb_active_torches, config_index, info_nb_torches}`。
* 类：`Multi::MultiTorchNester`（vtable `0xA3B8A0`）、`Tiling::MultitorchEvaluator`（`0xA3D310`）、
  `Tiling::OldMultitorchEvaluator`（`0xA3D340`）、`multitorch_eval.cpp`、`ComputeBestConfigSequence`。

#### (C) 剪切模式

`LoadShear`（`0x506C10`）给出结构 `{shear, shear_corner, shear_repulse_from_borders, shear_gap, shear_thickness}`。
**剪切与"多割炬/共边 tiling"互斥**：代码中有断言 `!shear` @ `0x765460`
以及 `part_number < m_common_cut_tiling_parts.size()` @ `0x764A80` / `0x769410`。

#### (D) 行模式 / 管材模式

`LoadRow`（`0x506D80`）→ `{row_enable, row_shear_gap, row_shear_common_cut_gap, row_punch_gap, row_punch_common_cut_gap, row_alternate}`。
`row_intervals` 是 `vector<pair<double,double>>` 形式的 **y 向条带**：
`GetRow`（`0x10040`，断言 `row_number < row_intervals.size()`）通过两个 `double*` 输出条带起止，
`GetNumberOfRows`（`0xFF30`）返回条带数。相关类：`Row::Squeezer`（`0xA3B1E0`）、
`Row::BasicDistancer`（`0xA3B1B0`）、`Multi::RowNester`（`0xA3BB30`）。

#### (E) 皮革/纹理/缺陷/禁布区/标记/开放路径

* **两个品质区间确实并存**（均已证实）：
  `quality >= 0 && quality < 9`（`0x9ADCAA`，出现在 `0x1C980` / `0x1EE50` / `0x7BF0C0`）
  与 `quality >= 0 && quality < 100`（`0x9ADDEA`，出现在 `0x1C980` / `0x1EE50`）。
  配套 `../structure/border_property.hpp`、`GetLayerLeatherPart/Sheet`（`0x9AE0B0`/`0x9AE0D0`）、
  `GetLayerRestrictedZonePart/Sheet`（`0x9AE070`/`0x9AE090`）。
* 纹理方向：`SetSheetGrainDirection` `0xC9A0`，JSON 键 `grain_direction`；
  另有断言 `false && "internal error mode not yet supported with grain"` @ `0x9D9400`
  → **行/管材等某些模式与纹理方向不能同时使用**。
* 标记：`SetMarkMode` `0x188D0` → `+0xE8`/`+0xF0`（`mark_size`、`mark_inter_distance`）；
  `GetNumberOfMarks` `0x18AF0`、`GetMark` `0x18E70`；SVG 图层名 `__marks__`。
* 缺陷：`AddDefectToSheet` `0x14190` → `AddPolygonDefectToSheet` `0x16970`；
  `CNS_AddDefectFromNestedPart` `0x12F40`；`SetDefectGap` `0x109C0` → `+0x118`（键 `defect_gap`）。
* 禁布区：`CNS_SheetAddRestrictedZone` `0x1A210`、`CreateRestrictedZoneConstraint` `0x1AA90`、
  `CNS_SetZoneRestrictedPart` `0x1AE40`、`CNS_ForcePartOnBottomBorder` `0x1A8F0`。
* 孔位强制：`ForcePartInsideHole` `0xC610` 写 `part+0x20A=1` / `+0x20B=0`（键 `hole_status`）；
  `ForcePartOutsideHole` 是**内部**函数 `0xC640`（**并未导出**）。
* 开放切割路径：`AddToolPathToPart` `0x101C0`、`AddHoleInToolPath` `0x10240`、
  `AddInflatedToolPathToPart` `0x12C60`、`CNS_AddOpenToolPathToPart` `0x12D10`、
  `AddOpenCuttingPathToPart` `0x14A60` —— 都追加到 `part+0x88`。
  注意 `CNS_AddToolPathDefectToSheet`（内部 `0x102C0`）与
  `CNS_AddExternalToolPathBoundaryToSheet`（内部 `0x10380`）**都不在导出目录里**。

#### (F) 装配组与建议分组

已证实的调用链：`CreateProblem`（`0x1EE50`）→ `0x1C540` →
`MakeClusterFromSuggestedPartsGrouping`（内部 `0x1C2A0`，断言 `it != part_maping.end()`）
⇒ **建议分组在"建模阶段"被转换成 `clusters` / `clustered_parts`**。
`SetIncompatibleSheet` `0x11490` → `+0x1F8`；`SetPartAuthorizations` `0xC1A0` → `part+0x188/0x190/0x198`；
`AddPartSpecificAuthorizations` `0x10CE0` → `part+0x1A8`。

#### (G) 目标函数、余料、板选择

* **目标函数枚举**（由 dump 函数 `0x511080` 解出）：
  `0 MinimizeX, 1 MinimizeY, 2 NoOffcut, 3 MinimizeArea, 4 MinimizeXThenY,
   5 MinimizeYThenX, 6 IntelligentMinimizeX, 7 IntelligentMinimizeY`。
* **`nesting_origin` 枚举**：`0 BottomLeft, 1 TopLeft, 2 BottomRight, 3 TopRight`。
* 余料评估三个量即上表 `+0x28/+0x30/+0x38`；填充率真正实现于 `stats.cpp`
  （`FillRatio` / `UsedSurfaceAux` / `UsedSurfaceWithStairs`）。
* 板选择策略类：`AllSheetSelector`（`0xA3B840`）、`LargestSheetSelector`（`0xA3BAC0`）、
  `RandomSheetSelector`（`0xA3BA60`）、`NoMixSheetSelector`（`0xA3B9D0`）。
* `SetExtraParameters` 接受的键（`0x9B009C`–`0x9B02EF`）：
  `enable_common_cut_nesting`、`relax_objective`、`repair`、`tiling`、`filling`、
  `enable_beautifier_common_cut`、`enable_beautifier_improve_common_cut`、
  `use_multitorch_tiling`，以及 `cns_force_cloud`。

#### (H) IO / 报表

* JSON 落盘/读入：`SaveProblem` `0x5070E0`、`LoadProblem` `0x50B1D0`、
  `SaveSolution` `0x50DB70`、`LoadSolution` `0x50EE50`、`UnSerializeSolution` `0x1C5F0`；
  权威字段名清单 = `..\structure\text_io.cpp` 里的 JSON schema（键字符串在 `0x9DA300`–`0x9DB010`）。
* `GenerateDxfNesting` `0xBF70` → `DrawDxf`；**DXF 的组码约定未恢复**（未找到组码字符串）→ 未确认。
* SVG/HTML 家族：`DrawSVG`、`DrawSVGAux`、`DrawSVGReusableOffcuts`、`DrawSVGMarks`、
  `GetLeatherLayer`、`DrawHtmlPartsTable`、`GetNestingInformation`；
  CSS 资源 `cns_solution.css`（带 `../`、`../../` 回退）。

#### 已知未解决

`AddSheet`（`0x15BF0`）分配 `0x168` 字节并初始化 `+0xF8/+0x100/+0x108/+0x110/+0x118`
（正是 `SetSheetGaps` `0xCCB0` / `SetDefectGap` `0x109C0` 的目标）、`+0x120` 优先级、
`+0x124/0x128` origin、`+0x12C/0x130` objective、`+0x138` 价格；
但 `SaveProblem` 读到的板数量在 `+0x20`、`dimension_x +0x28`、`dimension_y +0x30`、
gaps `+0x38..0x58`、价格 `+0x98`（受 `+0x90` 守卫）。
两套偏移不可能属于同一个类 ⇒ **板存在两种表示**，其对应关系未确认。
本报告以"各 setter 的落点"为权威，并标注此不一致。

### 7.5 云端与许可/机器绑定

> 本节由 `findings_cloud_lic.md` 深挖并已抽样复核。下面只列**已证实**的关键结论。

#### (a) `GetPCId`（`0xC010`）：MAC + C: 卷序列号

`GetPCId` 返回一个受 `__cxa_guard` 保护的**静态 `std::string`** 的 `c_str()`
（worker = `0x24290`，219 条指令）：

```asm
0002429D  malloc(0x2C0)                     ; IP_ADAPTER_INFO 缓冲
000242CE  call 0x61F000                     ; GetAdaptersInfo(buf,&cb)   cb 初值 = 8
000242D3  cmp  eax, 0x6f                    ; 0x6F = ERROR_NO_DATA → 扩容重试
000242EF  movzx … byte ptr [rsi+0x198..0x19D]; IP_ADAPTER_INFO.Address[0..5] = 首块网卡 MAC(48bit)
00024363  lea  rcx, "c:\\"
00024390  call [0xB28A84]                   ; GetVolumeInformationA("c:\\",…,&serial,…)
000243A4  eax ^= 0xABADCAFE                 ; 混淆常量
```

**PCId = ((mac48 × serial) + (mac48 >> 16) + mac48 + serial) ^ 0xABADCAFE**（全 32 位），
最后用 `"%ld"` 格式化。**不含 CPU id，也未使用 `CryptGenRandom`。**
首块网卡取不到时走 `..\utils\pcid_win.cpp` 里的断言路径。

#### (b) 三个 `UnLockLaunchingOrder*` 与真正的授权闸门

* `UnLockLaunchingOrder`（`0xD430`）：`lo->[0x244] = mode`（仅一个 int）。
* `UnLockLaunchingOrderSntl` / `Oxy` / `PCId`（`0xE180` / `0xE1F0` / `0xE260`）：
  **111 字节机器码逐字节相同**（只有日志字符串不同），各自执行
  `strlen(a)` + `std::string::_M_replace(lo+0x248, 0, len, a, n)`，
  再对 `lo+0x268` 做同样操作 → **写入两条授权 key 字符串**。
  因此 `LaunchingOrder` 布局：`+0x244 : int32`、`+0x248 / +0x268 : std::string`、`+0x1C8 : std::vector<Engine*>`。
* **真正的闸门在内部函数 `0x1E70`**（由 `0x2AB0` / `0x6100` 调用）：
  打印 `"Order valid"` → `"Start"` → `"Keys: " + mode + key1 + key2`，
  然后用 `0x12B580` / `0x12C980`（单键校验）与 `0x12B5F0` / `0x12CB40`（枚举加密狗 key 列表）
  配合 `0x9993B0` / `0x9993F2` / `0xB5EC0` 做**字符串比对**；
  **失败写 `ctx+0x4C = 11 (0x0B)` 或 `17 (0x11)` 并中止，成功写 `9`。**
  所有"版本/特性"判定都基于 `0xB81F0()`，而它是硬编码的 `mov eax,0x64; ret`（返回 100）
  → 这些分支在**本构建中全部为死代码**。
* `GetComputationStatus` / `CancelComputation` / `TerminateComputation` 读同一对象的
  `[+0x48]`（非 0 → `"Local"`，否则 `"Cloud"`）与状态码。

#### (c) 加密狗与"许可"的真实实现：Sentinel HASP / Sentinel Admin API

* `0x12BBA0`（写）/ `0x12BCC0`（读）：`LoadLibraryA(<dll>)` +
  `GetProcAddress(h,"hasp_login"/"hasp_logout"/"hasp_write"/"hasp_read")`；
  `hasp_login(featureId=0, <VendorCode>, &handle)`；
  写：128 字节空格填充缓冲写入 `file id 0xFFF4`；读：`hasp_read(h,0xFFF4,0x10,buf,0x80)`。
* 内联 `movabs` 拼出的 DLL 名：**`hasp_windows_x64.dll`**（`0x12ADB0` 内还内联了含 `OxySec` 的 `__FILE__` 路径）
  与长度 29 的 **`sntl_adminapi_windows_x64.dll`**（`sntl_admin_context_new` / `sntl_admin_get` / … @ `0x9BCB50`）。
* **RVA `0x9A2080` 的 base64 blob = HASP 的 Vendor Code**（厂商代码，**不是**证书/DER）：
  984 个 base64 字符 → 解码 736 字节，熵 7.688，首字节 `0xAF`；
  **恰好两处 `lea rdx,[rip+…]`** 引用它（`0x12BC04` 于 `0x12BBA0`、`0x12BD3F` 于 `0x12BCC0`），
  且紧接 `call hasp_login`。解码副本见 `blob_9a2080.bin`。
  *(本报告此前写的"无引用"是错的——原因是我的字符串索引做了 220 字符长度上限，已修正。)*
* **重要否定结论：CryptoPP 未在授权路径上被使用。**
  `0x24290` / `0x12BBA0` / `0x12BCC0` 的被调用集合里都没有 CryptoPP 符号；
  二进制中大量的 `CryptoPP::` RTTI 与算法名（RSA-PSS/PKCS1v15+SHA1、DSA、ECDSA+SHA-256、OAEP、
  DES/AES/SKIPJACK、HMAC、HexEncoder、Base64、PKCS#8/X509、BER/DER）只是
  **整个静态库被链接进来**，不能作为"被使用"的证据。验签被委托给 Sentinel 运行库。

#### (d) 云端协议要点

| 项目 | 结论 |
|---|---|
| 云端实体 | `Engine::CloudEngine::Run` = RVA `0x26A60`（vtable 地址点 `0xA3CEE0` 的第 3 槽，也是该类唯一业务虚函数） |
| 请求文本 | GET 构造 `0x6DA1F0`、PUT 构造 `0x6DBD40`；`GET/PUT <path> HTTP/1.1` + `Host:` + `Accept: */*` + `Connection: close`（PUT 另加 `Content-Length:` / `Content-Type: text/plain` + body） |
| 端口 | 常量 `0x50` = 80（包装层 `0x2B630` / `0x2BD20` → 实现 `0x2AF30` / `0x2B660`） |
| 路径 | `PUT /pb/<id>` 提交问题；`GET /sol/<id>` 或 `/best_sol/<id>` —— 由 `0x2893F` 比较响应体与 `"end"` 后 `cmove` 决定：body==`end` → `/sol/` + 标签 `intermediate`；否则 `/best_sol/` + `final` |
| `<id>` | **随机 UUIDv4**：`std::mt19937`（种子 5489）+ `CryptAcquireContextW`（`0x26BE4`）/`CryptGenRandom`，并置版本/variant 位 |
| 超时 | PUT 120.0 s（`0x9AE9B0`）；轮询总截止 `2t + 30.0`（`0x9AE9B8`）；GET 轮询窗口 20 s（`0x27F25`）；提交给引擎的时限 `max(t − 5.0, 1.0)`；读循环含 `nanosleep` 退避；**未找到重试计数** |
| 反序列化 | `UnSerializeSolution` = `0x1C5F0`（断言 `solution.Bindable(problem)`，调用点 `0x2918B` 包在 `0x60A620("..\engine\cloud_engine.cpp", 行 61, …)` 中）；`CreateProblem` = `0x1EE50` |
| 日志 | `0x1BF40` 惰性建立 `c:\Temp\debug_nest.txt` sink（`0x7BB430`，写入 `"CNS informations"` + 许可类型）；`0x65A530` 选择 `log_nest.txt` / `cloud_nest.txt` / `local_nest.txt`；`0x5190B0` 生成 HTML（`cns_solution.css`） |
| 例外 | 仅证实 `Utils::ConnectException` 的 `__cxa_throw`（`0x6DA3EE` / `0x6DBFB1`）；`Timeout/BadResponse` 抛出点未定位 |

（完整细节与证据索引见 [`findings_cloud_lic.md`](findings_cloud_lic.md)）

---

## 8. 第三方组件清单（自 RTTI + 源码路径字符串）

| 组件 | 版本/证据 | 用途 |
|---|---|---|
| Boost | `boost_1_63_0`（`C:\Users\renaud\nest\external\boost_1_63_0`） | multiprecision（`cpp_int`/`rational`）、asio、uuid/sha1、filesystem |
| Clipper | **不存在** —— `Clipper` / `ClipperLib` / `ClipperOffset` / `PolyTree` / `IntPoint` / `SimplifyPolygon` 全串扫描 **0 命中** | 几何为自研实现 |
| COIN-OR Clp | `clp-1.15.3\Clp\src\ClpSimplexDual.cpp`、`CoinUtils\src\CoinLpIO.cpp`；`Coin::CoinLP` 封装 `ClpSimplex*`（+8） | LP 求解。**具体解什么问题（是否为列生成主问题）未证实**，见 §7.3 |
| CryptoPP | 470+ 个 `CryptoPP::` RTTI 类（RSA-PSS/PKCS1v15+SHA1、DSA、ECDSA+SHA-256、OAEP、DES/AES/SKIPJACK、HMAC、HexEncoder、Base64、PKCS#8/X509、BER/DER） | **整库被静态链接，但在授权路径上未见调用点**（见 §7.5(c)）——不能因 RTTI 存在就认为被使用 |
| JsonCpp | `Json::Writer`、`Json::StyledWriter`、`Json::FastWriter`、`Json::ValueAllocator` | 云端/本地序列化 |
| **Sentinel HASP / Sentinel Admin API** | `hasp_windows_x64.dll`、`sntl_adminapi_windows_x64.dll`（运行期 `LoadLibraryA` + `GetProcAddress`）；`hasp_login/logout/read/write`、`sntl_admin_context_new/get/…` | **真正的许可校验**（加密狗 / 软授权） |
| libstdc++/libgcc | `basic_string::_M_replace`、`__cxxabiv1::*`、`std::thread` | 标准库 |
| WinPthreads | `libwinpthread-1.dll`、`nanosleep` | 线程 |
| 自制框架 | `dbg::symlog` 等 | 日志/跟踪（也是本次命名恢复的关键） |
| 自研几何/求解 | `Geom::MultiPolygon`、`PartPolygon`、`OffsetManager`、`NoFitMap`、`NoFitStrips`、`HullSurf`、`Lp::LinearProgram`、`Prc::*`、`Row::*` | 几何与套料核心 |

源码路径泄漏（对还原工程结构很有帮助）：

```
cns.cpp              cns_no_fit.cpp        internal.cpp
..\engine\engine.cpp ..\engine\cloud_engine.cpp
..\structure\border_property.hpp     structure_interface_private.hpp
..\nesting\algos\compact.hpp         ..\nesting\algos\algo_parameters.cpp
..\nesting\algos\algo_helpers.hpp    ..\nesting\algos\bucket_manager.hpp
..\nesting\algos\multinesting_optimizer.cpp   ..\nesting\algos\old_beam.cpp
..\nesting\algos\postop.cpp          ..\nesting\algos\postop_move.cpp
..\nesting\algos\sheet_optimizer.cpp ..\nesting\algos\tree_db.cpp / .hpp
..\nesting\ios\log_ios.cpp           ..\nesting\tiled_multipart.cpp
..\multi\nesting_context.cpp  ..\multi\nesting_nester.cpp
..\multi\rectangle_nester.cpp ..\multi\tiling_nester.cpp
c:\Temp\computation_solution.h
```

---

## 9. 结论与可用性评估

1. **该文件是 Optalog CNS 5.0 的核心套料引擎库 `liblcns.dll` 的解壳内存镜像**，属于闭源商业软件，
   公开网络上没有对应源码或文档（检索无结果）。
2. **导出层是 168 个 C++ 自由函数**，通过序号导出、名字被清空、并抹掉 7 个导出项；
   但作者自带的 `dbg::symlog` 跟踪器在函数体内留下了自己的 `__func__` 字面量，
   使 **162/168 的名字可以被自动、可复现地恢复**（本报告的方法与脚本已给出）。
3. **算法层面**：这不是"遗传算法套料"（全串扫描 `genetic/chromosome/population/mutation/fitness` **0 命中**），
   而是一套工业级求解栈 ——
   几何层是**两套自研内核**：`..\exact\*`（int64 定点，长度定标 `1e10`，叉积/行列式用 **128 位** 精确谓词）
   与 `..\geom\*`（double）；No-Fit-Polygon 通过
   `..\exact\convolution.cpp::ConvolutionRaw`（`0x596F20`，核心 `0x596100`）做**边界 Convolution**，
   极角归并**只用 (dx,dy) 的符号做象限分类，完全不用 `atan2`**；
   偏移是 `0x58A7E0` 的"分 N 步增量偏移"，且外轮廓 `+gap` / 内孔 `-gap`（无 MiterLimit 概念）；
   搜索层是引擎 + 观察者 + 多策略（beam / compact / tiling / row / multitorch / rectangle…）竞争，
   并用**矩形对偶**与角度优化（`beam_distinct_angle`、`NewLocalAngleOptimize`）做快速路径；
   数学层引入 **Clp 上的 LP 封装与一套 "pricing"（面量打分/优先级）层**
   （`Lp::LinearProgram`、`Coin::CoinLP`、`Prc::{Alpha,Box,Hull,LinearCombination}PriceComputer`、`Row::Distancer/Squeezer`）——
   这些类**确实被构造**，且可达自 `Multi::CompactNester::Run` 等后优化路径；
   但"它们构成 Dantzig–Wolfe 列生成主问题"**并未被证实**（见 §7.3），本报告不作此断言；
   工艺层覆盖共边切割、多割炬、剪切、管材行模式、皮革纹理/品质区、板材缺陷与禁布区、余料评估。
4. **不可直接加载**：IAT 残留 dump 进程的绝对地址且 `OriginalFirstThunk == 0`。
   若需要动态验证，必须重建导入表与重定位。

### 复现步骤

```powershell
# Python 3.14 + pefile + capstone
C:\Users\16479\AppData\Local\Python\bin\python.exe -m pip install pefile capstone
cd D:\Nesting\nestfab
& $py re\01_pe_info.py          # PE 头/节区/熵
& $py re\02_exports_imports.py  # 导出/导入/壳特征
& $py re\08_pdata_rtti.py       # .pdata 函数表 + RTTI 名字
& $py re\09_rtti_vtables.py     # vtable → 虚函数地址
& $py re\12_xref.py             # 全量反汇编交叉引用（耗时约 10 分钟）
& $py re\18_final_names.py      # 名字恢复
& $py re\22_emit_table.py       # 输出 exports_table.md / .csv
```

### 产物清单

| 文件 | 说明 |
|---|---|
| `REPORT.md` | 本报告 |
| `exports_table.md` / `exports_table.csv` | 168 个导出函数全表（名字、跟踪标签、C 别名、序号、RVA、大小、参数、证据） |
| `exports_table.json` | 同上，附加字面量序列、导出间调用边、跟踪标签 |
| `findings_geometry.md` | 几何子系统深挖（数据结构、NFP/Convolution、偏移、常量） |
| `findings_engine.md` | 搜索/引擎策略深挖 |
| `findings_lp.md` | 列生成/定价/Clp 深挖 |
| `findings_features.md` | 切割工艺特性深挖 |
| `findings_cloud_lic.md` | 云端协议 + 授权/机器绑定深挖 |
| `BRIEF.md` | 供后续分析使用的完整背景与工具说明 |
| `lib.py` | 共享分析库（RVA 转换、反汇编、字符串、函数表） |
| `funcs.json` | 18,614 个函数的 `[begin,end]` RVA |
| `vtables.json` / `vtable_methods.txt` | 474 个 vtable：类名 → vtable RVA → 虚函数槽 RVA |
| `xref.pkl` / `prof2.pkl` | 每函数的反汇编画像（大小、指令数、被调用者、调用者、引用字符串、名字） |
| `out_29.txt` | 库/几何指纹与全部自研类名清单 |
| `internal_names.txt` | 已解析的内部函数名 → RVA |
| `blob_9a2080.bin` | HASP Vendor Code 的 base64 解码结果（736 B） |
| `listing_*.txt` | 关键函数的带注释反汇编清单 |
| `01_*.py` … `33_*.py` | 全部分析脚本（可复现） |

---

---

## 10. 未恢复项总清单（含原因与影响评估）

本节是**唯一**的收尾清单：凡本报告任何位置出现过的"未确认 / 未译"，
都收敛到这里，逐条给出**状态**、**原因**与**对工程等价性的影响**。
所有条目都**没有用近似值顶替**；凡声明"不可恢复"的，都给出了可复核的原因。

### 10.1 已结案（原清单，全部关闭）

| 原未确定项 | 结论 | 证据位置 |
|---|---|---|
| `Row::Squeezer` 成本函数 `0x1380D0` | **结案**：`cost = obj[+0x10] / sin(方向角) − max(\|A.v0−A.v2\|,\|B.v0−B.v2\|)`；仅当两行平行（`1e-6`）时适用；另有 `0.005` 逐元素对齐闸 | §8.5 / §8.5b，已并入 `row::squeezeCost` |
| `Prc::BoostAlpha` / `SurfaceCoeffs` / `DimAlpha` 布局 | **布局不可恢复（已明说原因）**；但**名字非零引用**（反射注册表 `0x6CC9D0`），两个 alpha 值 **0.5 / 0.1** 已读出并入库 | §11.2 / §11.3 / §20.3 |
| `0x7CA830` / `0x267A30` 的装配分支 | **结案**：`0x267A30` = `std::sort` 实例；`0x7CA830` = **先就地排序**自己的 `+0x90` 三元组累加器（功能性副作用，产出列优先 COO），**再**渲染成 3 空格分隔文本 | §8.1 / §10.2 |
| 四个定价变体默认为哪一个 | **结案：没有"默认变体"**——`0x4D64C0` 把 Box + Hull + Alpha×2 **全部构造**，交给 `LinearCombinationPricer` 按 5 个权重加权平均 | §9.1 / §9.2 |
| `CoinLP` slot 6/7 语义 | **结案（结构）**：`slot 5/6/7` 是同一个"追加三元组"例程的三个变体（`slot 7` 为无前导块、无间接调用的共享裸核心；`slot 6` 比 `slot 5` 多一条 `xorpd` 取负）；成员布局为 3 个并行 `vector<double>` + COO 三元组累加器 | §10.1 / §10.3，已并入 `SimplexLinearProgram` |

### 10.2 后续深挖并已结案

| 项 | 结论 | 证据 |
|---|---|---|
| `Row::Squeezer` 对象图与构造路径 | 外层 `{vptr@0xA3B1F0, inner*}`；inner 624 B；`inner[+8]`=开关、`inner[+0x10]`=阈值 | §12 |
| 策略身份与接线点 | `0x6AABC0` 在 `..\multi\row_nester.cpp`；core 存于 `RowNester+0x18`，Squeezer 存于 `core+0xC0` | §13 / §13.5 |
| core 配置默认值 | rodata `0x9B1A48 = 4.0`（阈值）、`0x9B1A50 = 20.0`（系数）、`0x9B1A40 = 10.0` | §14.1 |
| `0x5CD800` 产出结构 | 包围盒 `{bool@+0, minX@+8, minY@+0x10, maxX@+0x18, maxY@+0x20}`；标志极性"非 0 即跳过" | §14.2 |
| 两个配置来源 | pipe 闸（`Pb+0x170`，`SetPipeMode`）→ `Pb+0x190/0x188`；否则共边闸（`Pb+0x1A0`，`SetCommonCutParameters`）→ `Pb+0x1B0/0x1A8`；都不满足用 rodata | §15 / §16.1 |
| 行容器的三层结构 | `vector<Item*>`(8B) → `Item`(0x90B) → `Elem48`(0x30B) → `Elem16`(16B)；`0x4F7690` 入口是 `Part+0x70` | §17 / §18 |
| `0x134470` 的算法 | 逐零件扫描 16 字节条目容器，谓词 `0x5C2E40` 过滤，`0x133DE0(..., core+8)` 算价，**保留最小** | §19.1 |
| 配置参数块的边界 | `Pb+0x188..+0x1C8` 是 `SetCommonCutParameters` 的 `arg2` **原样结构拷贝**（`0x185A40` 逐个 qword 搬） | §20.1 / §20.2 |

### 10.3 明确声明**不可恢复**的项（附原因）

| 项 | 原因（可复核） | 对等价性的影响 |
|---|---|---|
| `Prc::BoostAlpha` / `SurfaceCoeffs` / `DimAlpha` 的**字段布局** | 三个名字串虽被反射注册表 `0x6CC9D0` 引用，但**无 typeinfo 对象、无 vtable、无成员名字串**；注册调用传入的 rodata 指针落在 `basic_string::substr` 断言串中间、不可读 | 无：三者在本栈中**不参与任何已追踪的算法**；两个 alpha **数值**（0.5/0.1）已入库 |
| 上述配置参数块各字段的**语义名** | 已化简为"`SetCommonCutParameters` 调用方结构体在偏移 k 处是什么"；该结构体由调用者分配、由导出签名约定，二进制中**无定义、无 typeinfo、无成员名** | 无：**偏移对应**与**写入者**均已确定，工程按偏移建模并已接入真实优先级 |
| `core+0x28` / `+0x30` / `+0x38` 是否被别处读取 | 数据库 TU 内 ≤40 B 的访问器里只有 `Pb+0x170`/`Pb+0x1A0` 两个；全局按偏移扫描会与 130–220 个**无关类型**的同偏移访问混淆，无法判归属 | 极小：三者**已建模为字段**（`commonCutAt1B8`/`commonCutAt1C0`/`cfgAt198`）但未接算法；已追踪路径（`0x6AABC0`、`0x13C380`）内确认无读者 |
| `Item` 的 `+0x20…+0x88` 字段语义 | **部分结案**（后续轮次）：`+0x08`=几何容器（`0x133190`=`lea rax,[rcx+8]`）、`+0x20`=子对象（`0x1333C0`）、`+0x58`/`+0x70`=两个 216 字节元素容器（`0x1331A0`）、`+0x88` u8；`+0x20…+0x50` 之间诸字段**仍未逐个定名**（原因是缺少每一格的写入者/读取者配对） | 小：本工程不建这两层容器 |
| ~~`0x133DE0`（逐零件代价）、`0x5C2E40`（谓词）、`0x547670`、`0x5C4C50`、`0x5C4950`~~ | ✅ **全部结案**（后续轮次）：`0x5C2E40` 谓词与 `0x5C4C50`（4 条指令）见 [`findings_lp_use.md`](findings_lp_use.md) §25–§26；`0x5C4950` 记录表构造见 §36；`0x133DE0` 全链见 §27；`0x547670`=`lea rax,[rcx+0x90]`（§39） | **算法已并入工程**（`row::authorized`/`bestCandidate`/`drainSources`/… 共 15 项，见 §30.1） |

### 10.6 后续轮次的结案（逐零件路径之外的补充）

| 项 | 结论 | 证据 |
|---|---|---|
| 束搜索宽度的"常量" | ✅ **它是选项表的用户参数**，三个键 + 全部束统计键与打印点已列出 | [`findings_engine.md`](findings_engine.md) 附录；读取点 `0x4EECB` / `0x4F342` / `0x4F365` |
| **完整选项键表**（≈80 个用户旋钮） | ✅ 已逐键取出并标注读取点；束族 8 键**各有且仅有一条 `lea`**，落在同一注册区 `0x4EE5A`–`0x4F411` | 同上 |
| `0x4F7600` / `0x4F7690`（Item 访问器）与其第二跳 | ✅ `0x4F7600`→`*(Part+0x70)`（`0x547610` 是恒等转发）；`0x4F7690`→`*(Part+0x70)+0x90`（`0x547670`=`lea rax,[rcx+0x90]`） | [`findings_lp_use.md`](findings_lp_use.md) §39 |
| `0x1368A9`（元素 `+0x98` 的另一分支） | ✅ `+0x98` = `第二槽 present 且 \|v[2]−v[0]\| <= 1e-06`（`0x1368B1`/`0x1368B9`/`0x1368C6 setae`），与 `+0x99` **完全对称**；工程里原先只实现了 presence 判定，**已更正** | 同上 |

> 方法说明：本节与 §10.3 的区别在于——§10.3 是"**不可恢复 + 原因**"，
> 本节是"**曾经标为未确认、现已结案**"。每次结案都会同时更新工程与 `test_row`/`test_recovered`。

### 10.7 覆盖率：**还远没有逆向完**（可复现的量化口径）

`python re/g_coverage.py` 会算出并打印以下数字，同时生成 [`UNCOVERED_RANKED.md`](UNCOVERED_RANKED.md)
（按体积排序的未覆盖函数清单）。当前结果：

| 口径 | 数值 |
|---|---|
| 全库函数（`.pdata` 扫描） | 18,614 个 / **9,928,180 字节** |
| 从 168 个导出出发**可达**（直接调用 + `vtables.json` 的 416 张虚表 slot 边） | 6,181 个 / 4,670,042 字节 = **47.0%** |
| 可达集中**入口地址被本文档或工程引用过**的 | **968 个 / 1,508,960 字节 = 32.3%** |
| 可达但**从未被引用**的 | 5,213 个 / 3,161,082 字节 = 67.7% |
| ├ **第三方**（boost / CryptoPP / COIN-OR / JsonCpp，**身份证据**） | 7 个 / 21,998 字节（0.5%）—— 无需逆向，已下载并链接 |
| ├ **工具链** libstdc++/MinGW（身份证据） | 288 个 / 365,589 字节（7.8%）—— 无需逆向 |
| └ **libcns 领域代码待逆向** | **4,918 个 / 2,773,495 字节 = 可达集的 59.4%** |
| &nbsp;&nbsp;&nbsp;├ **完全没有识别通道**（无名字、无字符串、无数据引用） | **4,531 个 / 2,308,205 字节 = 可达集的 49.4%** ← **真正的障碍** |
| &nbsp;&nbsp;&nbsp;└ 当前工具**可识别**（有名字或字符串） | 387 个 / 465,290 字节 |

**口径修正（goal round 7，重要）**：上表第三/四行的"领域"桶此前偏小 —— 旧规则只要函数**引用到的任一字符串**
匹配库符号就把它算作工具链，而"引用到的字符串"里包含**它调用的函数名**，于是**仅仅调用了
`std::vector::reserve` 的领域函数就被移出待做清单**。这是**乐观偏差**。现在排除必须满足**身份证据**：
函数**自身的名字**是库符号、或**全部**字符串都是库符号、或字符串显示它编译自**第三方源码路径**
（`external/boost_1_63_0`、`clp-`、`coinutils-`、`osi-`、`cryptopp/`、`jsoncpp/`）。
修正量：**117,692 字节**（旧规则报 4,859 个 / 2,655,803 B，新规则 4,918 个 / 2,773,495 B）。
`g_coverage.py` 仍同时计算旧规则，好让这个偏差的大小始终可见、可复核。

**新的主指标（本轮起）**：领域桶里**有名字或字符串**的只有 **387 个 / 465,290 字节**，
其余 **4,531 个 / 2,308,205 字节（可达集的 49.4%）连"识别通道"都没有** ——
没有名字、没有字符串、没有数据引用，现有工具**无法给出任何身份线索**。
⇒ 下一步不是再挑 TU 写档案（那只能覆盖那 387 个 + 已引用的部分），而是**新建识别通道**：
用**调用者/被调用者 + 虚表 slot 归属 + 结构指纹**（尺寸、指令数、是否 thunk、是否 getter）为这些函数建立
**可声明置信度**的识别记录，并把"已识别"作为独立于"已引用/已转写"的第二档指标。

**分母口径**：可达性只沿 `callees` 与 `vtables.json` 的虚表 slot；经函数指针的间接调用若不在虚表内
则**没有跟踪**，所以 47% 是**下界**。

**分子口径（重要）**：被"引用"只意味着该函数的入口地址**在我们的文档/源码里出现过**
（"看过并写下了它是什么"），**不等于**逐指令复现 —— 后者由
[`lcns/include/lcns/recovery.hpp`](../lcns/include/lcns/recovery.hpp) 的 58 条登记表跟踪。
该脚本会**排除自己生成的报告与原始数据表**（`UNCOVERED_RANKED.md`、`exports_table.*`、`vtables.json` 等），
否则"把某函数列为未覆盖"这件事本身就会把它算成已覆盖。

**结论：没有完成。** 已完成的：导出面（168/168 枚举、162 个名字恢复）、逐零件路径（指令级）、
引擎调度层的分派器/级联孪生体/描述符布局/默认调度表、LP 层结构、完整选项键表、JSON/DXF 格式与授权事实。
**未完成的是可达集里 66.6% 的领域代码**，其中体积最大且可识别的包括
`..\multi\database.cpp`（`0x6A7800`, 13,057 B）、SVG 写出器（`0x7CCDF0`, 16,831 B，含 `'<svg width="'`）、
`..\nesting\algos\bucket_manager.hpp`（`0x23B420`, 16,413 B）、
等价问题校验器（`0x4BDB70`, 11,150 B，`'..\verify\equivalent.cpp'`）、
float filler（`0x1E76C0`, 12,889 B，`'res.nb_fillers >= 0'`）等；
以及登记表里 27 条 `Substituted` —— **12 个策略的 `Run` 体与主放置器仍是本工程自己的搜索**，
这正是外部基准上密度约 35% 而文献约 90% 的原因。

### 10.8 原工程 TU 地图：把"可达 4.67 MB"变成**逐文件的可数工作清单**

`python re/g_tu_map.py` → [`TU_MAP.md`](TU_MAP.md)。二进制把 `..\dir\file.cpp` 烧进了断言串，
但断言串在**独立的消息构造器**里，所以只有少数函数自带路径。三级标注：

1. **direct**（156 个）—— 函数自己引用 `..\dir\file.cpp`；
2. **vtable**（140 个）—— 函数是 vtable slot，且 demangle 类名可映射到 TU；
3. **graph-strict**（3,766 个）—— **所有已标注邻居一致**才赋值（TU 私有助手与断言构造器由此绑定）；
   再用一条**强多数且禁止"超级 TU"吸收**的宽松规则补 101 个。

结果：**4,163 / 6,181 个函数（69.5% 字节）已归位到 49 个自有 TU + 6 个第三方 TU**；
仍无标签 2,025 个 / 1,426,277 字节。**置信度分级很重要**：`direct`/`vtable` 视为确证，
`graph-*` 是**假设**（严格规则下仍可能沿链漂移），所以在文档里分层列出、不作等同陈述。

重建出的原工程文件（按待逆向字节降序，前 15）：

| 原 TU | 函数数 | 字节 | 已引用 | 未引用 |
|---|---:|---:|---:|---:|
| `..\tiling\packer_cache.cpp` | 273 | 274,948 | 35,982 | **238,966** |
| `..\multi\nesting_context.cpp` | 270 | 205,881 | 20,248 | **185,633** |
| `..\engine\cloud_engine.cpp` | 566 | 252,728 | 82,190 | **170,538** |
| `..\structure\svg_io.cpp` | 236 | 239,605 | 70,927 | **168,678** |
| `..\structure\border_property.hpp` | 332 | 199,302 | 33,203 | **166,099** |
| `..\nesting\algos\bucket_manager.hpp` | 167 | 157,150 | 26,236 | **130,914** |
| `..\tiling\packer.cpp` | 105 | 119,483 | 8,242 | **111,241** |
| `..\verify\equivalent.cpp` | 177 | 140,629 | 34,795 | **105,834** |
| `..\structure\problem.cpp` | 124 | 103,521 | 10,325 | **93,196** |
| `..\multi\rectangle_nester.cpp` | 105 | 99,266 | 9,014 | **90,252** |
| `..\exact\relinker_internal.cpp` | 65 | 82,005 | 196 | **81,809** |
| `..\nesting\algos\compact.hpp` | 87 | 96,219 | 15,993 | **80,226** |
| `..\multi\row_nester.cpp` | 120 | 102,779 | 25,586 | **77,193** |
| `..\nesting\algos\algo_parameters.cpp` | 102 | 75,592 | 0 | **75,592** |
| `..\structure\text_io.cpp` | 125 | 66,361 | 6,383 | **59,978** |

⇒ "导出函数用到的都要逆向"由此有了**有限清单**：49 个自有 TU（其中 6 个已 100% 引用）。
推进方式：逐 TU 取该 TU 的函数列表 → 识别（入口/调用面/常量/字符串/虚表）→ 写档 → 落工程 → 复算覆盖率。

### 10.4 与目标条款的对照

| 目标条款 | 状态 |
|---|---|
| ① 清掉全部剩余未确定项 | **是**：原清单五项**全部结案**（§10.1）；后续深挖项 8 条亦结案（§10.2）；其余收敛为 §10.3 的"不可恢复 + 原因" |
| ② 用逆向结果替换自创替代 | **是**：LP 层按 `CoinLP` 的槽与成员布局重建（`SimplexLinearProgram` / `canonicalise` / `buildAndSolveLp`），列生成机具**隔离并标注为"非原库"**；`Row::`/`RowNestCore` 按逆出结构接线；配置默认值改用**真 rodata 常量** |
| ③ 每处给出地址级证据 | **是**：每个结论都附 RVA 与关键指令/常量；不可恢复项给出可复核原因（§10.3） |
| ④ 零警告构建 / 全部测试 / 文档同步 | **是**：33 TU、0 warning、`ctest` **15/15**；`REPORT.md` / `findings_*.md` / `lcns/README.md` / `MAPPING.md` 同步 |

### 10.5 验收机制：`test_recovered` 把文档与代码机械绑定
上述"常量与 DLL 一致"的说法**不是叙述性声明**，而是有一条可执行测试守着：
`lcns/tests/test_recovered.cpp` 逐条断言工程使用的常量等于本报告读出的数值，
并在每行注明 RVA（`geom::kScale@0x9AD708`、`kFullTurnFixedDegrees@0x34630B8A000`、
90/180/270 度魔数、`row::kSqueezeAlignmentTolerance@0x9BCFD8`、
`kSqueezeParallelTolerance@0x9BCFC0`、`kRowCoreAt0x08/0x18/0x20@0x9B1A40/48/50`、
`AlphaSurfacePrice::kBoostAlpha@0x9D9C08`、`kDimAlpha@0x9D9BE8`、
`geom::kSnapTolerance`、`NoFitMap::kDefaultMaxComplexity@0x61A8`）。
**任何人若在未重读二进制的情况下改动这些常量，该测试立即失败。**

另有一条**可追溯性检查脚本**（`re/g_acceptance.py`）：对 36 条结论逐条核对
"其依据的地址/常量是否确实出现在 `re/` 文档中，且工程中是否存在对应实现"。
当前结果 **108/108 全部满足**（检查项随后续轮次持续扩充）。

关于隔离：`lcns/include/lcns/lp_column_generation.hpp` 的文件头明确写着
**"NOT PART OF THE BINARY"**，且 `lp.hpp` 不包含它——即"自创替代"已被移出忠实层并就地声明。

---

---

---

## 11. 逐零件路径（承接 §10 之后的后续深挖）

本轮把行排样核心的**逐零件路径**又推进了一层（详见
[`findings_lp_use.md`](findings_lp_use.md) §21）：

1. **谓词 `0x5C2E40`（138 B）完全译出**：容器的记录是
   **24 字节 `{u8 tag@0, int64 lo@+8, int64 hi@+0x10}`**，函数判断
   "是否存在 tag 相符、且区间 `[lo,hi]`（或反向区间）包含给定整数的记录"。
   步长 `0x18` 与 §18.1 里 `Elem48+0x18` 那层容器**完全对上**。
2. **取价例程 `0x133DE0` 的入口译出**：`0x5CD800` 求候选包围盒 →
   **`20.0`（rodata `0x9BCEB0`）× 高** → `0x1333D0` 造 Item（`partIndex = 0`）→
   `0x136B80(&squeezer, xmm1 = 高×20, xmm2 = cfg[+0x18], xmm3 = cfg[+0x10])`。
   由此确定**同一个 `Row::Squeezer` 构造器的两个调用点第一实参含义不同**：
   `0x13C380` 传 `2×max(高,宽)`，`0x133DE0` 传 `20×高`。
   工程已并入 `row::kCandidateHeightScale = 20.0` 与 `row::candidateSqueezerArg()`，
   并由 `test_recovered` 断言。
3. **`0x136Cxx`/`0x137FE0` 家族不属于 Squeezer**：它们作用于 `rsp+0x110` 的另一个对象
   （Squeezer 的 out 槽是 `rsp+0x30`）。其中 `0x136CB0` 是**缓存于 `+0x50`、
   由常量 `0x9BCF48` 守门的惰性求值**（取容器末元素 `0x134F30(首 qword) + 次 qword`），
   `0x136CA0` 是容器计数，`0x136D30` 是 `+0x10`/`+0x11` 两级标志读取，
   `0x137FE0` 是 16 字节记录的合并循环。
   **`0x133DE0` 的返回值 = `0x136CB0` 留在 `xmm0` 的那个 double**（**[推断]**：
   已逐条核对 `0x134060`–`0x1342D4` 的清理路径全为整数/指针操作，不破坏 `xmm0`），
   `0x134470` 正是用它 `ucomisd … ; jbe` **取最小**。

**仍未确认**（详见 §21.4）：`rsp+0x110` 对象的类名与布局、其初始化函数 `0x136C00`、
`0x134F30` / `0x137A90` / `0x5CEE50` / `0x5D38C0` / `0x5C4CD0` / `0x5C4CE0` 的作用、
立即数 `0x271000000000` 的字段切分。

---

### 11.1 逐候选的分值公式（承接 §11）

在 §11 的基础上，本轮把**取价链闭合**了（详见
[`findings_lp_use.md`](findings_lp_use.md) §22）：

* **`0x136C00`（75 B）** 是 `0x133DE0` 在 `rsp+0x110` 建的那个对象的初始化器，
  它把**布局全给出**：`{double@0, double@8, u8@0x10, u8@0x11, vector<16B>@0x18/0x20/0x28,
  node*@0x30(=this+0x40), u64@0x38, u8@0x40, 分值缓存@0x50}`，且
  **缓存哨兵 `0x9BCF48` 是 `-1.0`（不是 NaN）** —— 这纠正了 §21.3 的一处猜测。
* **`0x134F30`（22 B）** = 节点贡献 `node[+0x18] ? 0 : (node[+0x30] − node[+0x20])`。
* **`0x136CB0`（78 B）** = 惰性分值：容器空 → 0，否则
  **`nodeLength(末元素.first) + 末元素.second`**（`0x136CDC` 取 `end[-1]`），
  记忆化于 `+0x50`，且**只在缓存恰为 `-1.0` 时才重算**（改数据不失效，须调用方重置）。

工程已并入 `row::kScoreUnset` / `ScoreNode` / `nodeLength` / `ScoreRecord` /
`candidateScore` / `LazyScorer`，并由 `test_row` 与 `test_recovered` 分别断言
（含"用末元素而非首元素"这一易错点：测试里首元素故意给 100 以区分）。

**仍未确认**：容器**如何被填**（`0x137A90` 的记录合并等），因此"节点从哪来、
其 `+0x20`/`+0x30` 是什么"未定 ⇒ 分值**公式**已确证，但**输入的产生**未确证，
故"候选取最小"的**完整实现**仍不具备条件。

---

### 11.2 两套对象的完整布局（承接 §11.1）

本轮把 §11.1 里出现的两族访问器逐个读完，得到**两类对象的完整成员表**
（详见 [`findings_lp_use.md`](findings_lp_use.md) §23）：

* **节点（Row node）**：`+0x18` 退化标志；`+0x20/+0x28/+0x30/+0x38` = **包围盒**
  （`0x134F30` 取 X 跨度、`0x134F50` 取 Y 跨度，退化时都归 0）；
  `+0x40/+0x41` 与 `+0x98/+0x99` 两组标志对（`0x134F90`/`0x135010`）；
  `+0x48/+0x70` 两个 `optional<4×double>`（`0x134FA0`）；`+0xa0` 一个 double（`0x135030`）；
  `+0xa8/+0xc0` 两个容器（`0x134FF0`）。**这正是 §8.4/§12 里建模的那个 "Row"**，
  本轮把其余字段补齐，`nodeLength` 也因此有了明确语义：**盒的 X 跨度**。
* **`rsp+0x110` 的对象**：`+0x00`/`+0x08` 两个 double；`+0x10/+0x11` 标志对；
  `+0x18` 一个 `vector<16 字节元素>`；**`+0x30` 一个 `std::string`**；
  `+0x50` 分值缓存。字符串这一点由三条独立证据互证：`0x136C00` 的 SSO 写入
  （`[+0x30] = this+0x40`、`[+0x38] = 0`、`byte [+0x40] = 0`）、
  `0x136D40`（在 `+0x30` 处构造 `std::string`）、`0x136D50`（按 `{ptr, len}` 拷贝字符串）。

工程已把节点布局扩进 `row::ScoreNode`（含 `nodeLengthY`/`nodeFlag40`/`nodeFlag98`）并由
`test_row` 断言。另记录两个 rodata 常量 `0x9BCF60 = 1e-06`、`0x9BCF70 = NaN`——
它们出现在记录合并例程 `0x137A90` 内，但**角色未确定，故不入代码**。

**仍未确认**：**候选集如何生成**（`0x137A90` 1175 B 的主体、`0x137800` 636 B、
`0x1331A0` 选择的两个子对象的角色、`0x5CEE50`/`0x5D38C0`/`0x5C4CD0`/`0x5C4CE0`）。
因此 §19.1 那条"候选取最小"的**完整实现仍不具备条件**，本轮**没有**用假定输入去凑一个能跑的版本。

---

### 11.3 容器的生产者与缓存失效点（承接 §11.1/§11.2）

本轮把"记录从哪来"追到了底（详见 [`findings_lp_use.md`](findings_lp_use.md) §24）：

* **`0x137800`（636 B）** 的内联断言串解出方法名 **`orderedAddElement`**。逐指令显示它把
  **16 字节 `{void*@+0x00, double@+0x08}`** 记录以 **步长 `0x10`** 追加到
  `O+0x18/+0x20/+0x28`（`0x137854`/`0x137857`/`0x13785C`），需要时经 `0x137838`→`0x137A11`
  扩容，**并在 `0x137877` 把分值缓存 `O+0x50` 重置为 `-1.0`**。
  ⇒ 记录形状**印证**了 §11.1 的 `row::ScoreRecord` 建模；
  ⇒ **缓存失效点就是追加器自己**，§11.1 里"调用方须自己重置"的说法**已修正**。
* 名字 `orderedAddElement` 说明容器**有序**，而 `candidateScore` 取**末元素**
  ⇒ 分值等于容器的**极端元素**；`0x134470` 对它 `ucomisd … jbe` **取最小**
  ⇒ **语义是 minimax**（最小化最坏者）。**[推断]**：升序/降序无法仅由名字判定，故不写死。
* **更正 §11.2 的一处判断**：`0x9BCF70` **不是 NaN 哨兵**，而是 `andpd` 的**取绝对值掩码**
  （`0x7FFF…` 位型读作 NaN），与 `0x9BCF60 = 1e-06` 一起构成 epsilon 比较。
* **`0x137A90`（1175 B）的结构**：按 tag 经 `0x1331A0` 选 `P+0x58`/`P+0x70` 子对象 →
  以 **步长 `0xd8` = 216 字节**遍历其容器 → 每元素对第 4 实参 `r12` 做**虚调用 `[vptr+0x10]`**
  ＋ `0x136CB0` 惰性分值 ＋ `0x134F30`/`0x134F50` 跨度 → 取优 →
  `0x137800` 追加进 `O` → 返回 1/0。

工程已并入 `row::orderedAddElement` 并由 `test_row` 断言。
**仍未确认**：源容器元素的**型别**（仅知步长 216 字节）、虚调用目标 `r12` 的类、
`0x134F70`、`0x1331A0` 两个子对象的角色、`0x133DE0` 四实参含义。
⇒ 候选集生成的**骨架已明**，但**元素型别与虚调用目标未定**，
故 §19.1 的完整实现仍**不具备条件**（不以假定输入凑版本）。

---

---

## 12. 逐零件路径闭环：最优旋转搜索

本轮把 §11 的链路接到了底（详见 [`findings_lp_use.md`](findings_lp_use.md) §25）：

```
0x4F7600(part)            → 48 字节元素的几何容器
  → (拷贝到 rsp+0x1b0)
  → 0x134470 遍历"候选角度元素"（16 字节，含 {tag, 角度}）
       谓词 0x5C2E40      → 该角度是否被授权（记录表给出 [lo,hi] 区间）
       0x133DE0           → 变换(0x5CEE50) → 旋转拷贝(0x5D38C0) → 包围盒(0x5CD800)
                            → 20 × 高 → Item(0x1333D0) + Squeezer(0x136B80) → 惰性分值
       取最小             → 0x134470 结尾的 ucomisd / jbe
```

⇒ **`0x134470` = "在（被授权的）候选角度中，挑出让该零件分数最小的那个"**，即**最优旋转搜索**。

三个原语已**逐指令**并入工程（`lcns/include/lcns/row.hpp`）：

* **`0x5C2E40`** → `row::authorized(records, tag, value)`：**完全**（两种区间极性、tag 匹配、
  空容器返回 false）。
* **`0x5CEE50` 的 tag = 0 路径** → `row::angleTransform(fixedAngle)`：**完全**，
  含四个精确角（`1.0` / `-1.0` / **符号精确的 `-0.0`**）、一般路径 `角度/3.6e12*2π` 与
  `% 360e10` 回绕；取模魔数 `0x9C5FFF26ED75ED55` 与四个角常量均与二进制一致。
* **`0x134470` 的循环** → `row::bestCandidate(elements, records, scoreFn, &best)`：
  **控制流完全**（谓词过滤、取最小、全被拒时返回 −1）。

**唯一的注入点（明示）**：分值计算以 `ScoreFn` 注入，因为其几何步 `0x5D38C0`（1500 B）
**未译**。头文件注释写明这一原因——**没有**用工程自己的 `geom::` 旋转去冒充它；
`0x5D38C0` 一旦译出，替换 `ScoreFn` 即可，**无需改动循环**。

**仍未确认**：`0x5D38C0` 主体、`0x5CEE50` 的 tag ≠ 0 分支、`0x5C4CD0`/`0x5C4CE0`
（tag / 角度取值器，语义仅由用法推定）、`0x8BEFC0`、`0x133DE0` 的 arg2 角色。

---

### 12.1 注入点填空：元素型别坐实 + 变换算术译出

本轮把 §12 留下的**唯一注入点**填掉了大半（详见
[`findings_lp_use.md`](findings_lp_use.md) §26）：

* **元素型别坐实**：`0x5C4CD0(element)` = `movzx eax, byte [rcx]`（`tag@+0x00`）、
  `0x5C4CE0(element)` = `mov rax, [rcx+8]`（`angle@+0x08`，定点度）
  ⇒ `0x134470` 循环元素就是 **16 字节 `{u8 tag, …, int64 angle}`**，
  与 `row::CandidateElement` 完全一致（从"用法推定"升级为"取值器证实"）。
* **变换算术**：`0x5D38C0` 的两处相同块给出
  `x' = cos·x − sin·y + tx`、`y' = sin·x + cos·y + ty`（`tx`/`ty` 取变换记录的
  `+0x20`/`+0x28`，tag = 0 时恒为 0），并以 `ucomisd 0, (cos²+sin²)` 校验行列式。
  这与 `0x5CEE50` 产出的 `{cos, −sin, sin, cos, 0, 0}` **布局一致**。
* **"高"的定义**：变换后所有点的 `maxY − minY`（包围盒 min/max 由已译的 `0x5C8C50` 完成），
  再乘 `20.0` 交给 `Squeezer`。

工程已并入 `row::transformX/transformY/transformDet/transformedHeight/transformedWidth`
并由 `test_row` 断言（90° 旋转两个基向量、四个分支行列式均为 1、2×1 矩形旋转 90° 后
高宽互换、`candidateSqueezerArg(transformedHeight(...)) == 40`）。

**注入点已收窄**：`Row::Squeezer` 的构造实参现在**完全可算**；
仍缺的是 `Squeezer` **之后**的分值装配
（`0x1333D0` → `0x136B80` → `0x136CB0` → `0x137A90` → `0x137800`）。
`bestCandidate` 的循环、谓词与取最小**无需改动**，届时只需替换 `ScoreFn`。

---

### 12.2 分值装配链的控制流译出

本轮把 `0x133DE0` 的链条按地址拼齐，并解开了此前遗留的立即数（详见
[`findings_lp_use.md`](findings_lp_use.md) §27）：

```
0x5CEE50 角度→变换 → 0x5D38C0 变换拷贝 → 0x5CD800 包围盒 → 20×高
  → 0x1333D0 Item → 0x136B80 Squeezer → 0x137FE0 排空 → 0x136D30
  → 0x136CB0 惰性分值 → 返回值 = 它留在 xmm0 的 double
```

* **`0x271000000000` 解读完成**：按字节拆开是 `byte[+8] = 0`、**`u32[+0xc] = 10000`**
  ⇒ 源记录 = **16 字节 `{void* source@0, u8 tag@8, u32 count@0xc}`**，
  `0x133DE0` 传的 count = **10000**。这结清了 §21.4 的"立即数字段切分未定"。
* **`0x137FE0`（177 B）排空环**：初始化目标对象后逐记录（0x10 步长）反复调 `0x137A90`；
  **count == 0 的记录整条跳过**，合并返回 0 即提前结束，`--count` 到 0 也结束，
  否则**重试同一条**。

工程已并入 `row::kSourceRecordCap = 10000`、`row::SourceRecord`、`row::drainSources`
并由 `test_row` 断言（零 count 跳过、上限恰为 count、提前返回 false 即停、count = 1 只调一次、
source/tag 原样传递）。

**注入点只剩一个**：`0x137A90` 的**合并本体**——缺源容器**元素型别（步长 216 字节已知）**
与第 4 实参 `r12` 的**虚调用目标类**。
其余（`0x5CEE50`/`0x5D38C0`/`0x5C8C50`/`0x133E67`/`0x1333D0`/`0x136B80`/`0x137FE0`/
`0x136CB0`/`0x137800`）**全部已译并入工程**，届时替换 `ScoreFn` 即可，
`bestCandidate` / `drainSources` / `candidateScore` / `orderedAddElement` **无需改动**。

---

### 12.3 ABI 纠正、Item 的两个容器、216 字节元素经构造器证实

本轮（详见 [`findings_lp_use.md`](findings_lp_use.md) §28）：

* **ABI 纠正**：Windows x64 下 `rdi` 是 callee-saved，`0x5CD800` 序/尾声为 `push rdi` … `pop rdi`
  ⇒ 它**保留 `rdi`**。因此 `0x133DE0` 里 `rdi` 始终是 `rsp+0x170`：
  `0x133EC9 [rax] = rdi` 存的是它，`0x133E93 mov rcx, rdi` 又把它当 `0x1333D0` 的 `this`
  ⇒ **同一段栈区先当"角度变换"、后被复用为 Item（0x90 字节）**，
  故 §27.2 那条源记录的 `source` 是**那个 Item**（修正了我上一轮的一个读法）。
* **`Item+0x58` / `Item+0x70` = 两个 216 字节元素容器**：`0x1333D0` 把两组
  `begin/end/cap` 六连清零并反复提交 end；`0x1331A0(Item, dl)` = `dl ? +0x70 : +0x58`。
* **216 字节元素的构造器 `0x136350` 证实了 `ScoreNode` 的布局**：`+0x00` 指针、
  `+0x08/+0x10` 源容器 begin/end、`+0x18` 退化标志（**初值 1**）、`+0x20..+0x38` 包围盒、
  `+0x40/+0x41` 两个标志、`+0x48/+0x70` 两个可选槽、`+0xa8/+0xc0` 两个容器。
  另外它用 **180 度**（`0x1A3185C5000`）建变换再变换一次 ⇒ 元素里存着**镜像朝向**的容器。

工程侧最关键的收益是**编译期锁死布局**：`row.hpp` 里加了 **15 条 `static_assert`**
（`sizeof(ScoreNode) == 0xd8` 以及逐个 `offsetof`）。**这些断言当场抓出一个真实缺陷**——
我的 `ScoreNode` 缺了 `+0x00/+0x08/+0x10` 三格，导致其后所有偏移错位；补上后 15 条全部通过。
⇒ 从此"元素布局与二进制一致"不再靠注释，而是**编译期强制**。

**仍未确认**：`0x137A90` 对第 4 实参 `r12` 的**虚调用 `[vptr+0x10]` 目标类**
（源容器与元素布局均已证实）；`0x136350` 内部的 `0x1355C0`/`0x134D70`/`0x135040`/
`0x135780`/`0x5CE7F0`/`0x5CF6B0`/`0x135C70`/`0x8C4FF0`；`0x8BEFC0`；`0x133DE0` 的 arg1/arg2 分工。

---

### 12.4 注入点闭合：那个虚调用就是 `Squeezer::cost`

本轮把 §12.3 留下的**唯一注入点**关掉了（详见
[`findings_lp_use.md`](findings_lp_use.md) §29）：

* 读 `Row::Squeezer` 地址点 `0xA3B1F0` 处的虚表：`+0x10`（**slot 1**）的唯一非空目标是
  **`0x13A360`** —— 就是 §13 译出的**记忆化挤压代价**。
  （**纠正**：§12/§13 里按虚表基址数把它叫成"slot 2"；代码里的 `[vptr+0x10]` 是 **slot 1**。）
* `0x137A90` 的实参是 `rcx = r12`（那个 Squeezer）、`rdx = [rbp]`（对象里已存最后一条记录的
  **node 指针**）、`r8 = rbx`（当前 216 字节元素）⇒ 该调用就是
  **`Row::Squeezer::cost(lo = 上一条记录的 node, hi = 当前元素)`**，
  即工程里早已实现的 `row::Squeezer::cost` / `row::squeezeCost`。
* 其后 `0x137BF0..0x137C83` 的最终算术也已逐指令译出：
  `cost` 先按 `a = 记录值 + X 跨度 + [P+0x38]` 与 `b = 惰性分值 + cost` 的大小吸收超出
  （`jbe` 跳过，故 `a == b` 也跳过），最后 **`score = cost − element[+0xa0] / obj[+0x08]`**。

工程已并入 `row::elementScore(...)`，`test_row` **两条分支都断言**并做**端到端**验证：
2×1 矩形 + 90° 候选 ⇒ `angleTransform` → `transformedHeight = 1` → `candidateSqueezerArg = 20`
→ 用两个 `ScoreNode`（其 `+0x48`/`+0x70` 槽即 Squeezer 读的槽）建 `SqueezeContext`
⇒ `Squeezer::cost` 给出 `20/1 − 0 = 20` 且**被缓存**。

⇒ 目标的 ③ 由"控制流等价 + 单点注入"升级为"**整链条等价**"：
`0x134470` 的谓词、取最小、排空、记录追加、惰性分值、挤压代价与最终算术
**全部是逆出原语的组合**。
**仍未确认**（按目标 ④ 明说）：`0x134D70`（元素两个标志的计算）、
`0x135030`/`0x136D10` 的**角色命名**（数值来源已知：`node[+0xa0]` 与 `obj[+0x08]`）、
`0x136350` 内部的 `0x1355C0`/`0x135040`/`0x135780`/`0x5CE7F0`/`0x5CF6B0`/`0x135C70`/`0x8C4FF0`、
`0x8BEFC0`、`0x133DE0` 的 arg1/arg2 分工。

---

### 12.5 候选角度的来源结案（★ §12.4 残留清单第 ① 项）

本轮把"角度集合从哪来"追到了底（详见 [`findings_lp_use.md`](findings_lp_use.md) §31）：

* **`0x5C4C50` 只有 4 条指令**：`mov rax,[r8] ; mov byte [rcx],dl ; mov [rcx+8],rax`
  ⇒ 它是**写一个 `{tag@+0x00, angle@+0x08}` 元素**（与 §11.x 由取值器确定的元素型别互为印证），
  **不是**"生成一组角度"的黑箱。
* **`0x8BEFC0`（308 B）** = 拷贝源容器的元素 + **追加这一个元素**
  （向量三字段写在 `0x8BF092`/`0x8BF098`/`0x8BF09C`）。
* **`0x134470` 自己的准备段**：空向量 → `0x8BEFC0(tag=0, angle=0)` →
  再手工追加 `{tag=0, angle=0xD18C2E2800 = 90°}`（`0x13450B`/`0x134532`/`0x13453C`）。
  ⇒ **候选集 = 源容器自带的元素 + 0° + 90°，tag 全为 0**，
  即"先试零件自带角度，再试轴对齐的 0° 与 90°"。

工程已并入 `row::writeCandidateAngle` / `row::candidateAngles` / `row::kAxisAngle90` /
`row::axisAlignedCandidates` 并由 `test_row` 断言（顺序、追加项、以及该 90° 条目经
`angleTransform` 走**精确 90° 分支**）。

另：`0x134D70`（437 B）本轮**部分证实**——它是"取包围盒 → `1e-06` 容差 + fabs 掩码逐元素比较
→ 返回 bool"的几何谓词（元素 `+0x40`/`+0x41` 的来源）；**完整表达式未逐条转写，故不写入工程**。

---

### 12.6 纠正：元素的 `+0x08`/`+0x10` 是"产生它的候选记录"

本轮发现并纠正了 §12.3 里的一处**推断错误**（详见
[`findings_lp_use.md`](findings_lp_use.md) §32）：

* 我当时依据 `0x13637B`/`0x136388` 的两次存储，把元素的 `+0x08`/`+0x10` 记成
  **"源容器的 begin/end"**。**这是错的。**
* 三条独立证据表明它们是**产生该元素的那条 16 字节候选记录 `{tag, angle}` 的副本**：
  1. **存储端**：`0x136350` 从 `r8` 拷两个 qword 进来（`0x136363`/`0x136374`/`0x13637B`/`0x136388`）；
  2. **读取端**：`0x1355C0` 用 `0x5CEE50(element + 8)` 读它们，而 `0x5CEE50` 正是用
     `0x5C4CD0(x) = byte[x]`（tag）与 `0x5C4CE0(x) = [x+8]`（角度）来读的；
  3. **调用端**：`0x136350` 的 `r8` 在各调用点都是遍历中的**16 字节候选元素**。
* 顺带证实：`0x133190` = `lea rax,[rcx+8]` ⇒ 元素 `+0x00` 是 **Item 指针**，
  几何源是 **`Item+0x08`**（零件的 48 字节几何容器）；而 `0x1355C0`（438 B）就是
  **"用元素自己的角度把零件几何旋转、取包围盒"**的那一步。
* 另修正：`0x5C5F30`/`0x5C5260`/`0x5C61D0`/`0x5C5F50` **都是恒等转发**（`mov rax,rcx; ret`），
  它们本身不做工作。

工程侧：`ScoreNode` 的两个字段**改名**为 `sourceTagQword`/`sourceAngle` 并写明纠正原因，
**15 条 `static_assert` 的偏移全部不变**（布局未动、只是语义命名修正）；
新增 `kItemGeometry`/`nodeSourceTag`/`nodeSourceAngle`/`nodeAngleTransform`（仅 tag = 0 路径），
由 `test_row` 断言。

---

### 12.7 三个子调用结案：两点变换、`Elem48` 析构、角度→变换第二实例

本轮把 `0x136350` 内部规模较小的几个子调用读透（详见
[`findings_lp_use.md`](findings_lp_use.md) §33）：

* **`0x5CF6B0`（235 B）= 两点仿射变换**：其算术与 `0x5D38C0` **完全一致**
  （`x' = cos·x − sin·y + tx`、`y' = sin·x + cos·y + ty`，对两个点各做一遍）
  ⇒ 这是 `transformX/transformY` 的**第二个独立代码证据**。
* **`0x8C4FF0`（147 B）= `Elem48` 容器的析构函数**：内部 vector 元素步长 **0x18**、
  外层元素步长 **0x30** ⇒ **从析构端证实** `Elem48` = 48 字节、内含"24 字节记录"的 vector
  （与 §21 由谓词 `0x5C2E40` 推出的记录步长**吻合**）。目标 ② 又添一条独立证据。
* **`0x5CE7F0`（381 B）= 角度→变换算法的第二个实例**，常量与 `0x5CEE50` **完全相同**
  （取模魔数、`360e10`、90/180/270 三个常量）⇒ 印证 `angleTransform`；
  而 `0x136350` 在 `0x13645B` 以 **180°** 调它，把容器的**镜像副本**存进元素。

工程侧并入 `row::transformPoint`/`FPoint2`、`kElem48Stride`/`kRecord18Stride`、
`kHalfTurn180`/`halfTurn()`，`test_row` 断言两点变换与 `transformX/Y` 一致、
两个步长关系、以及 `halfTurn()` 的 `cos = −1`、`sin = 0`、**`−sin = −0.0`（符号精确）**
使得元素里存的是**关于原点的中心对称副本**。

**仍未译**：`0x5D3430`(1156 B)、`0x135040`(1396 B)、`0x135780`(1250 B)、`0x135C70`(1748 B)
四个大函数，以及 `0x134D70` 的完整表达式、`0x135030`/`0x136D10` 的角色命名、
`0x133DE0` 的 arg1/arg2 构造者、`0x5CEE50` 的 tag ≠ 0 分支。

---

### 12.8 `0x134D70` 完全译出，并确定 `Elem16` = 二维点

本轮把 §12.5 里"只记结构、未转写"的 `0x134D70` **整条译出**（详见
[`findings_lp_use.md`](findings_lp_use.md) §34）：

* 它是 **`0x134D70(container, node) -> bool`**：对容器里每个元素，扫描其 `+0x00` 处的
  **16 字节点链**，并且**按闭合链处理**（`0x134E27` 从**末点**起算，首点与末点相比）；
  用 `1e-06`（`0x9BCEE0`）与 fabs 掩码（`0x9BCED0`）判定，一旦发现
  "**y 落在窗口内却出现严格倒退的 x 步**"（`0x134EDD`）即为 false。
  结果**粘滞**（`esi` 只在 `0x134EDD` 清零、从不置 1）⇒ 多元素之间是 **AND**。
* 顺带确定 **`Elem16` = 二维点 `{double x, double y}`**（`0x134E57` 的 `add rax,0x10`
  给出 16 字节步长，循环只读 `[rax]` 与 `[rax+8]`），**补上了"`Elem16`(16B) 的字段语义"**。

工程已并入 `row::Elem16`/`kElem16Stride`/`kChainEpsilon` 以及
`row::chainMonotone`（**标签按地址命名**、逐块对应、注释带 RVA）与 `row::chainFlags`。
`test_row` **两条路径都断言**：空链 ⇒ true、不回退的链 ⇒ true、
以及**特意构造到 `0x134EDD` 的 false 用例**（`node = {0,1,1}`、`bboxMaxX = 0`、
链 `{(0,5),(1,0),(2,0)}`）。

⇒ 目标 ② 项**结案**，**不再有"完整表达式未转写"的保留**。

---

### 12.9 tag≠0 = 镜像（⑥ 结案）、`+0x98/+0x99/+0xa0` 的生产者（③ 的答案），以及一处真实缺陷修复

本轮（详见 [`findings_lp_use.md`](findings_lp_use.md) §35）：

* **⑥ 结案**：`0x5CEE50` 的 tag≠0 路径是**反射 `{cos, +sin, sin, −cos, 0, 0}`**（行列式 −1）。
  前提是 `xmm6` 此时已为 0（一般路径与四个精确角分支各有 `pxor xmm6, xmm6`），
  故所有 `* xmm6` 项消失。⇒ **tag 的语义 = "是否镜像"**。
* **`+0x98`/`+0x99`/`+0xa0` 的生产者**（都在 `0x136350` 内）：
  `+0x99` = 第一槽存在且 `|v[2]−v[0]| ≤ 1e-06`（`0x1366E0 setae`）；
  `+0x98` = 第二槽的 presence（`0x1366F9`）；**`+0xa0` = `0x135C70(...)` 的返回值**（`0x13670F`）。
* **③ 的答案**（一半结案、一半明确不可恢复）：
  分母 `0x136D10` = `obj[+0x08]` = `0x136C00` 的 `xmm2` = `0x133DE0` 的 `cfg[+0x08]`
  ⇒ **配置系数**，**结案**；
  分子 `0x135030` = `element[+0xa0]`，**数值通路已完整追到 `0x135C70`（1748 B，未译）**，
  **命名不可恢复**（该函数无类型信息、无字符串、无 RTTI 可借）——按目标 ④ **不猜**。
* **测试抓出一处真实缺陷并修正**：`0x5D38C0` 用的是 `[+0x00]cos`/`[+0x08]negSin`/`[+0x10]sin`/
  `[+0x18]cos2`，我原先按 `−sin`/`cos` 写 —— **对旋转等价、对镜像错误**；
  新增的 `transformDet(mir) == −1` 断言当场失败（得 1），据此改为
  `x' = cos·x + negSin·y + tx`、`y' = sin·x + cos2·y + ty`、
  `det = cos·cos2 − sin·negSin`（与 `0x5D3C09`–`0x5D3C13` 完全一致）。

工程已并入 `row::mirroredAngleTransform`、按 tag 分派的 `nodeAngleTransform`、
`nodeSlotFlag99`/`nodeSlotFlag98`，并**修正**了 `transformX/Y/Det`。
**仍未译**：`0x5D3430`(1156 B)、`0x135040`(1396 B)、`0x135780`(1250 B)、
`0x135C70`(1748 B，③ 的命名也依赖它)、`0x1368A9`、`0x133DE0` 的 arg1/arg2 构造者。

---

### 12.10 ⑤ 结案：两个实参的构造者，以及"授权区间其实是角度区间"

本轮把 §12.4 残留的 ⑤ 追到了底（详见 [`findings_lp_use.md`](findings_lp_use.md) §36）：

* **arg1（`rsp+0x1b0`）**：`0x4F7600` 只有 **9 字节**（`mov rcx,[rcx+0x70] ; jmp 0x547610`），
  是**两步访问器**，返回零件内部的容器引用 —— 这就是为什么 `0x6AABC0` 必须先把它
  **拷贝**到循环局部的 `rsp+0x1b0` 再传给 `0x134470`。
* **arg2（`rsp+0x1d0`）**：由 `0x5C4950`（730 B）构造。它逐元素（源步长 `0x18`）发出
  **24 字节 `{tag = 0x5C4CD0(element), lo = 0x5C4CE0(element), hi = 另一角度}`**
  （`0x5C4A3E`/`0x5C4A45`/`0x5C4A4D`，追加于 `0x5C4A70`，步长 `0x18`）。
* **语义回溯**：既然两个端点取自 `0x5C4CE0`（角度）、被测值也是角度，
  那么 §21.1 的谓词 `0x5C2E40` 就是**角度区间的归属测试** ⇒
  **授权表的语义 = "该 tag 下允许的角度范围"**，
  `0x134470` = "**在被允许的角度范围内挑选分数最小的角度**"。
  这是从**生产端**反推出的语义闭环（此前只有消费端）。
* 两个缓冲都是**循环局部**的（`0x6AB35A`/`0x6AB36C` 在每轮迭代释放）。
* `0x5C3F00` 的角度回绕常量是 **`0x34630B89FFF = 360e10 − 1`**（`0x5C3F0A`/`0x5C3F66`）。

工程已并入 `row::makeAuthRecord`、`kPartGeometryVia = 0x70`、`kAngleWrapMax`，
并把 `AuthRecord` 的注释**升级为"lo/hi 是定点角度"**。

**至此残留只剩一项**：目标 ④ 的**四个大函数**
`0x5D3430`(1156 B)、`0x135040`(1396 B)、`0x135780`(1250 B)、`0x135C70`(1748 B)，
外加 `0x1368A9`（`+0x98` 的另一条分支）。

---

### 12.11 ③ 的分子已命名：它是鞋带公式的面积（更正 §12.9 的一处结论）

上一轮（§12.9）我把 `element+0xa0` 的语义判定为"**不可恢复**（取决于未译的 `0x135C70`）"。
本轮把那条链追到了底（详见 [`findings_lp_use.md`](findings_lp_use.md) §37），**该结论予以更正**：

* **`0x135C70`（1748 B）**：整条函数**零 rodata 常量**、只有 8 条浮点指令。
  其中 `0x135DB1`（`ucomisd` + `cmova`）在 16 字节元素上取 **`+0x08` 最小者**（最低点），
  `0x135F90`–`0x135FBE` 原地**反转**一段（顶点顺序规范化）；
  最后 `0x135FCE` 调 `0x5C51A0`（**容器拷贝**）、`0x135FD6` 调 **`0x5CC6A0`**，
  其 `xmm0` 在 `0x135FE3` 成为返回值（`xmm6` 全程只被写这一次；唯一 `ret` 在 `0x13609C`）。
* **`0x5CC6A0`（135 B）= 鞋带公式求面积**：
  `0.5 · Σ(prev.x·cur.y − prev.y·cur.x)`，`prev` 从**末点**起算（闭合环）、
  **带符号、不取绝对值**、空环返回 0；常量只有 **`0x9DE910 = 0.5`**。
* ⇒ **`element+0xa0` = 「按其最低点规范过顶点顺序的环」的带符号面积**，
  于是 `0x137C76` 的比值是 **`ringArea / cfg[+0x08]`**，
  最终 **`score = cost − (环形面积 / 配置系数)`**。

⇒ **③ 的两端（分子与分母）现在都已命名**。
工程已并入 `row::dllArea`/`copyRing`/`nodeAreaValue` 与 `kAreaHalf`，
`test_row` 断言单位正方形 CCW ⇒ +1、反转 ⇒ −1（带符号）、空环 ⇒ 0、退化环 ⇒ 0、
三角形 ⇒ 6，以及拷贝那一跳不改变值。

**仍未译**：`0x5D3430`(1156 B)、`0x135040`(1396 B)、`0x135780`(1250 B) 三个大函数，
外加 `0x1368A9`。另严格说明：`0x135C70` 的**返回值语义**已完全确定，
其**函数体其余部分**（断言串构造、临时对象管理）**未逐条转写**——但这不影响返回值语义。

---

### 12.12 ④ 结案：最后三个子调用

本轮把 §12.11 剩下的三个大函数处理完（详见
[`findings_lp_use.md`](findings_lp_use.md) §38）：

* **`0x5D3430`（1156 B）完全译出**：**零 rodata 常量**、只有 12 条浮点指令且是**两段相同**的
  `xmm0 = [rax] ; addsd [rbx] ; [rax-0x10] = xmm0`（`0x5D3700`/`0x5D3750`）
  ⇒ **把点链按位移量平移**；唯一 `ret` 在 `0x5D37A3` 返回 `rax = [rsp+0x90]`（= arg1）
  ⇒ `(out, src, offset) -> out`。而 `0x1355C0` 在 `0x13562D` 用**取负的包围盒一角**
  （`0x135620 xorpd -0.0`）调用它 ⇒ **把环平移到原点**（§12.6 里那一步的真实内容）。
* **`0x135040`（1396 B）定量定性**：常量 **`0x9BCEE8 = 0.005`**（**与挤压器的 `0x9BCFD8`
  不是同一个 rodata 地址**，数值相同）、fabs 掩码与 `1e-06`；FP 是 `addsd` 加 0.005 与成对的
  `subsd`+`andpd`+`ucomisd` 容差比较；调用含 `0x8C4FF0`（`Elem48` 析构）；
  唯一 `ret` 在 `0x135258` 且不返回浮点 ⇒ **0.005 容差下的几何匹配例程**。
* **`0x135780`（1250 B）定量定性**：常量仅 fabs 掩码与 `1e-06`；
  `0x135A37`/`0x135A3F`/`0x135A45`/`0x135A4B` **写出 4 个 double（32 字节 = 两点）**；
  调用 **`0x134890`/`0x134C10`（都在 row 单元内）** 与 `0x8C5D40`；入口取 `xmm2` 作输入
  ⇒ **在 `1e-06` 容差下把点链拼成一条 32 字节的两点记录**。

工程已并入 `row::translatedCopy`、`kMergeAlignTolerance = 0.005`（**与
`kSqueezeAlignmentTolerance` 区分地址**）、`kTwoPointRecord = 0x20`。
**明说**：`0x135040` 与 `0x135780` 的**函数体未逐条转写**（常量、I/O 形状、调用面、返回均已确定），
`0x1368A9`（`+0x98` 的另一条分支）**未译**。

⇒ 目标 ①–⑥ **全部结案**。

---

## 附录 A. 168 个导出函数（按序号顺序）

```
序号        RVA      字节      名称
--------------------------------------------------------------------------
1-2       0x016420 490     AddPolygonHoleToPart
3-4       0x0162B0 353     AddPolygonPart
5-6       0x015BF0 1717    AddSheet
7-8       0x0118F0 3660    DeleteLaunchingOrder
9-10      0x00B1D0 370     GenerateHtmlLaunchingOrderReport
11-12     0x00B350 247     GenerateHtmlSolutionReport
13-14     0x00B8D0 378     GenerateLaunchingOrderProblem
15-16     0x0107E0 155     GetComputationStatus
17-18     0x00B100 34      GetMultiplicity
19-20     0x00D460 688     GetNestedPart
21-22     0x010F30 490     GetNesting
23-24     0x00B190 63      GetNumberOfNestedParts
25-26     0x00B0C0 52      GetNumberOfNestings
27-28     0x00C5E0 36      GetPartUserString
29-30     0x00B510 43      GetPartWithBadGeometry
31-32     0x00B600 332     GetSheet
33-34     0x00B0A0 29      GetSolution
35-36     0x006100 3894    LaunchComputation
37-38     0x014620 1081    NewLaunchingOrder
39-40     0x00CF20 303     SetInterpartGap
41-42     0x00C1A0 241     SetPartAuthorizations
43-44     0x00C420 446     SetPartUserString
45-46     0x00CCB0 527     SetSheetGaps
47-48     0x0104D0 370     WaitComputationTermination
49-50     0x010650 386     WaitNextSolution
51-52     0x002AB0 2134    LaunchLocalComputation
53-54     0x010880 155     CancelComputation
55-56     0x00B020 52      GetPartUserStringEx
57-58     0x00C670 446     SetSheetUserString
59-60     0x00C830 353     GetSheetUserString
61-62     0x00B060 52      GetSheetUserStringEx
65-66     0x011120 868     SetExtraParameters
67-68     0x013C90 411     SetSheetPriority
69-70     0x016B20 353     AddNonRectangularPolygonSheet
71-72     0x016970 426     AddPolygonDefectToSheet
73-74     0x00D370 61      SetLocalEngine
76-77     0x00D430 36      UnLockLaunchingOrder
78-79     0x00CEC0 45      SetObjective
80-81     0x0109C0 388     SetDefectGap
82-83     0x00D3B0 68      SetLocalMaximumThreads
84-85     0x00D400 36      SetLocalMaximumIterations
86-87     0x00D050 334     SetOrigin
88-89     0x00B490 31      GetBuildVersion
90-91     0x00B470 31      GetBuildDate
92-93     0x00B450 31      GetMajorVersion
94-95     0x010CE0 584     AddPartSpecificAuthorizations
96-97     0x00B130 36      GetLength
98-99     0x00C9A0 372     SetSheetGrainDirection
100-101   0x00B160 36      GetHeight
102-103   0x016610 419     AddExternalPolygonBoundaryToSheet
104-105   0x0167C0 426     AddExternalPolygonBoundaryToPart
110-111   0x014D10 1891    AddPart
112-113   0x0132E0 176     AddHoleToPart
114-115   0x013390 124     AddExternalBoundaryToPart
116-117   0x0157A0 1098    AddNonRectangularSheet
118-119   0x014190 124     AddDefectToSheet
120-121   0x014210 117     AddExternalBoundaryToSheet
122-123   0x010920 155     TerminateComputation
124-125   0x014A60 678     AddOpenCuttingPathToPart
126-127   0x00C2A0 382     SetPartPriority
128-129   0x00D1A0 353     CNS_SetMultiplicityPreference
130-131   0x015480 404     AddCircularPart
132-133   0x013800 581     AddCircularHoleToPart
134-135   0x015620 374     AddRectanglePart
136-137   0x013A50 569     AddRectangularHoleToPart
138-139   0x014290 440     AddOptionalQuantityToPart
140-141   0x00E010 353     SetAutomaticStop
142-143   0x00E2D0 399     SetOffcutEvaluation
144-145   0x00DD90 36      SetFillLastNestingStrategy
146-147   0x00DDC0 33      SetShearMode
148-149   0x00E460 404     SetCommonCutMode
150-151   0x00E940 354     SetCommonCutSafetyPreference
152-153   0x00EAB0 468     SetCommonCutAuthorizations
154-155   0x00EC90 340     SetCommonCutCuttingPreference
156-157   0x00EDF0 337     SetCommonCutObjective
158-159   0x00D710 346     GetNumberOfCommonCuts
160-161   0x00BA50 825     GetCommonCut
162-163   0x00E180 111     UnLockLaunchingOrderSntl
164-165   0x003310 66      LaunchLimitedLocalComputation
166-167   0x00DE50 36      SetPartCommonCutMode
168-169   0x00B4B0 34      GetFillRatio
170-171   0x00BD90 470     GetNestingDimensions
172-173   0x00CB20 388     SetSheetPrice
174-175   0x00EF50 479     SetMultiTorchMode
176-177   0x00F130 388     SetMultiTorchCuttingPreference
178-179   0x00F2C0 633     SetMultiTorchObjective
180-181   0x014450 449     SetExtraGapOnPart
182-183   0x00DD30 36      CNS_SetFloatingMode
184-185   0x00D870 826     GetPartTorchInfos
186-187   0x00F540 629     SetDetailedMultiTorchObjective
188-189   0x00D310 33      CNS_SetNoMixPreference
190-191   0x00DBB0 382     CNS_SetNoOrientationMixOnPart
192-193   0x00B4E0 38      GetNestingFillRatio
194-195   0x018100 1955    AddPartVariantToPart
196-197   0x016D00 49      AddHoleToPartVariant
198-199   0x016D40 49      CNS_AddExternalBoundaryToPartVariant
200-201   0x016D80 96      CNS_AddOpenCuttingPathToPartVariant
202-203   0x016DE0 61      CNS_SetPartVariantAuthorizations
204-205   0x016E20 63      CNS_AddPartVariantSpecificAuthorizations
206-207   0x016E60 1727    GetNestedPartPartVariant
208-209   0x016CB0 57      <unnamed>
210-211   0x016CF0 8       <unnamed>
212-213   0x00CEF0 45      SetShearGap
214-215   0x011490 423     SetIncompatibleSheet
216-217   0x003360 52      LaunchEstimateLocalComputation
218-219   0x011640 483     AddSuggestedPartsGrouping
220-221   0x00F7C0 1072    AddPartToSuggestedPartsGrouping
222-223   0x00D340 33      CNS_SetNoSheetMixPreference
224-225   0x00BF70 148     GenerateDxfNesting
226-227   0x00C010 386     GetPCId
228-229   0x00E260 111     UnLockLaunchingOrderPCId
230-231   0x009AF0 452     NewNoFitContext
232-233   0x009CC0 568     DeleteNoFitContext
234-235   0x008AC0 939     GetNoFitMap
236-237   0x008A10 171     DeleteNoFitGeometry
238-239   0x0089D0 54      NoFitGetNumberOfExternalPolygons
240-241   0x008E70 335     NoFitGetNumberOfInternalHoles
242-243   0x008FC0 497     NoFitGetNumberOfPoints
244-245   0x0091C0 366     NoFitGetPoint
246-247   0x0188D0 529     SetMarkMode
248-249   0x018AF0 889     GetNumberOfMarks
250-251   0x018E70 1312    GetMark
252-253   0x00B540 177     AsyncCancelAllComputationsAndDeleteLaunchingOrder
254-255   0x017520 3027    AddRotatedPartVariantToPart
256-257   0x00FBF0 244     SetRowMode
258-259   0x00FCF0 568     SetPipeMode
260-261   0x013410 512     AddCircularExternalBoundaryToPart
262-263   0x013610 486     AddRectangularExternalBoundaryToPart
264-265   0x00FF30 271     GetNumberOfRows
266-267   0x010040 384     GetRow
268-269   0x00DE80 388     SetLocalEngineThreads
270-271   0x00AFE0 13      <unnamed>
272-273   0x019C40 411     SetLeatherMode
274-275   0x019DE0 350     AddLeatherQualityZoneInPart
276-277   0x01A0A0 331     AddLeatherQualityZoneInSheet
278-279   0x01AA90 944     CreateRestrictedZoneConstraint
280-281   0x01AE40 507     CNS_SetZoneRestrictedPart
282-283   0x01A7D0 286     <unnamed>
284-285   0x01A210 1468    CNS_SheetAddRestrictedZone
286-287   0x00B000 18      <unnamed>
288-289   0x00AFF0 10      <unnamed>
290-291   0x0101C0 127     AddToolPathToPart
292-293   0x019F40 342     AddLeatherQualityZoneInPart
294-295   0x012C60 169     AddInflatedToolPathToPart
296-297   0x010240 124     AddHoleInToolPath
298-299   0x013E30 417     SetSpecificSheetOrigin
300-301   0x013FE0 417     SetSpecificSheetObjective
302-303   0x01A8F0 411     CNS_ForcePartOnBottomBorder
304-305   0x00DE20 33      SetShearRepulseFromBorders
306-307   0x012F40 894     CNS_AddDefectFromNestedPart
308-309   0x010B50 395     CNS_CreateAssemblyGroup
310-311   0x011830 180     CNS_AddAssemblyGroupPart
312-313   0x00DD60 36      CNS_SetOriginPackingMode
314-315   0x012D10 552     CNS_AddOpenToolPathToPart
316-317   0x010440 42      CNS_SetEvaluateIntermediateNestingsAsLast
318-319   0x009330 449     NewNoFitNesting
320-321   0x00A9D0 240     NoFitAddNestedPart
322-323   0x009500 70      DeleteNoFitNesting
324-325   0x00A620 934     GetNoFitPlacementMap
326-327   0x009550 573     NoFitGenerateSvgNesting
328-329   0x009790 403     NoFitGenerateSvgGeometry
330-331   0x00DDF0 36      SetPartialShearMode
332-333   0x00B750 384     GetNestingBoundingBox
334-335   0x00C610 43      ForcePartInsideHole
336-337   0x010470 42      SetReorganizeBiggestPartNearOrigin
338-339   0x0104A0 42      SetReorganizeLongestPartNearOrigin
340-341   0x009930 443     NoFitSetMaximumComplexity
342-343   0x00E1F0 111     UnLockLaunchingOrderOxy
```

> 名称由 §4 的方法恢复；6 个 `<unnamed>` 见 §3.3。完整参数与证据见 `exports_table.md`。

---
