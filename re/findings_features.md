# 切割工艺特性集（cutting-technology feature set）逆向发现

对象：`D:\Nesting\nestfab\libcns_dump_64.dll`（Optalog CNS 排版引擎，MinGW-w64 静态链接，内存 dump，仅供静态分析）。
导出名以 `re\exports_table.json` 的 `name` 字段为准；函数名到 RVA 的完整表见 `re\feat\targets.tsv`。

标注约定：**【已证实】**= 直接读自反汇编/字符串；**【推断】**= 由多处证据合理外推；**【未确认】**= 本轮未查清。

---

## 0. 通用机制（所有组共用，先读这一节）

### 0.1 导出函数的形态与 ABI 【已证实】

168 个导出都是普通 x64 自由函数（rcx, rdx, r8, r9 + 栈；浮点用 xmm0..3）。
存在两种形态：

**(a) 带守卫的 API 函数**（大多数 `SetXxx`）：
```
mov rdi, rcx / mov rsi, rcx   ; this
mov ebp, edx / mov r12d, edx  ; int 参数
movapd xmm6, xmm2             ; double 参数
call 0xAB20                   ; 取 LaunchingOrder 锁/上下文
call 0x63F6C0                 ; 有效性检查，非 0 -> 抛异常
call 0x1BF40                  ; 取 dbg::symlog 输出流
... 一连串 0x978010/0x869D00/0x1C0C0 调用 = 只写日志（"-> " + 函数名 + 参数）
mov dword ptr [rdi+0xNN], ebp ; ★ 真正的效果
ret
```
`dbg::symlog` 会把 `__func__` 打进日志，因此每个函数都引用一条等于自己名字的 rodata 字面量
——这也是名字能被恢复的原因（见 BRIEF）。

**(b) structure 层小函数**（`rcx` 直接是结构体指针，无守卫）：
```
mov rsi, rcx ; mov ebx, edx
lea rcx, [rip+<自己的 __func__ 字面量>]
call 0x64E120 / 0x64ABF0 / 0x64CA50   ; dbg::symlog 构造
mov dword ptr [rsi+0xNN], ebx         ; ★ 效果
ret
```
典型：`SetShearMode` 0xDDC0（33 B）、`SetPartCommonCutMode` 0xDE50（36 B）、
`SetShearGap` 0xCEF0（45 B）、`SetObjective` 0xCEC0（45 B）、`ForcePartInsideHole` 0xC610（43 B）。

**结论：几乎所有导出的第一个参数都是某个"结构体对象"指针，函数只写它的一两个字段。**

### 0.2 两个并行的对象族 【已证实 + 部分未确认】

* **Order / problem 对象**（"order"，很大，≥0x2C0 字节）：承载全局工艺设置——
  objective、shear、common cut、multitorch、row、pipe、mark、leather、offcut、extra parameters、
  automatic stop、assembly group 等。`Structure::CreateProblem`(0x1EE50) 的第一个参数就是它
  （CreateProblem 内把该指针存在 `[rsp+0x9C8]`，全程从它读取工艺字段）。
* **Sheet 对象**（`AddSheet` 0x15BF0 里 `mov ecx,0x168; call 0x998500` → **大小 0x168 = 360 字节**）：
  承载每张板材的设置。其字段（来自 `AddSheet` 的初始化序列和序列化 getter）：

  | offset | 含义 | 证据 |
  |---|---|---|
  | +0x20 | quantity (int) | getter 0x4F8360 `mov eax,[rcx+0x20]`，JSON 键 `quantity` |
  | +0x28 | dimension_x (double) | getter 0x4F8370 `[rcx+0x28]` |
  | +0x30 | dimension_y (double) | getter 0x4F8380 `[rcx+0x30]` |
  | +0x38/+0x40/+0x48/+0x50/+0x58 | left/right/bottom/top gap + defect_gap (5 × double) | getter 0x4F8C80(+0x38)…0x4F9C30(+0x58)，JSON 键 `left_gap`…`defect_gap` |
  | +0x90 | 有 price 标志 (bool) | 0x4F8540 `movzx eax,byte[rcx+0x90]`，`SaveProblem` 0x50752A 用它决定是否写 `price` |
  | +0x98 | price (double) | 0x4F8550 `movsd xmm0,[rcx+0x98]` |
  | +0xF0 | 备用 price 标志 (bool) | 0x4F8580 `cmp byte[rcx+0xF0],0` |
  | +0xF8 | 备用 price (double) | 0x4F8589 `movsd xmm0,[rbx+0xF8]` |
  | +0xF8/+0x100/+0x108/+0x110 | 4 个 gap（`AddSheet` 初始化时为同一个值） | `AddSheet` 0x15E3C-0x15E54 `Q[rbx+0xF8..+0x110] <- xmm6` |
  | +0x118 | defect gap | `AddSheet` 0x15E5C `Q[rbx+0x118] <- xmm6` |
  | +0x120 | priority (int) | `AddSheet` 0x15E64 `D[rbx+0x120]<-0`，`SetSheetPriority` 0x13C90 |
  | +0x124 / +0x128 | 有 specific origin 标志 / nesting_origin 值 | `AddSheet` 0x15E6E/0x15E91，`SetSpecificSheetOrigin` 0x13E30 |
  | +0x12C / +0x130 | 有 specific objective 标志 / objective 值 | `AddSheet` 0x15E9B/0x15EA2，`SetSpecificSheetObjective` 0x13FE0 |
  | +0x134 / +0x148 / +0x150 / +0x160 | 其他 bool/指针 | `AddSheet` 0x15EAC/0x15EBB/0x15EC6/0x15ECD |

**【未确认】**：`SetSheetGaps`(0xCCB0) 写 `+0xF8..+0x110`（4 个 double，与 `AddSheet` 一致 ⇒ 该对象是 Sheet）；
但序列化器读 gap 用的是 `+0x38..+0x58`（getter `0x4F8C80…0x4F9C30`）。
两者不能是同一个类 ⇒ **Sheet 存在两套表示**（API 层 0x168 对象 vs structure 层对象），
本轮未能把两套表示一一对齐。凡涉及 Sheet 偏移的结论，请以"哪个 setter 写的"为准。

### 0.3 唯一的强制/落地中心：`Structure::CreateProblem` = RVA **0x1EE50**

* 大小 15305 字节，3076 条指令，RVA 区间 0x1EE50-0x22A39；调用者 0x2AB0、0x6100、0xB1D0、0xB8D0、
  0x22A20、0x668F20。它把 Order 结构翻译成内部问题（并在这里读取几乎每个工艺字段）。
* 关键读取点（`[rsp+0x9C8]` = Order*）：

  | 指令 | 读取 | 含义 |
  |---|---|---|
  | 0x20BC8 | `mov r8d,[rax+0x8]` | objective（枚举，见 G 组） |
  | 0x1F12D | `cmp byte[rdi+0x128],0` | row_enable |
  | 0x21488 | `movzx eax,byte[rax+0x5C]` | common cut mode |
  | 0x2149B/0x2149F | `cmp byte[rax+0x68],0` / `maxsd xmm0,[rax+0x60]` | common cut 安全预设标志 + 双精度参数 |
  | 0x21533 | `cmp byte[rax+0x98],0` | multitorch 模式标签（0=显式目标；1=预设表） |
  | 0x2154F-0x215D1 | `[rax+0xB0]…[rax+0xD8]` 6 个 double | 组装到局部 MultitorchProperties（rsp+0x8A8..0x8D0） |
  | 0x215EE | `movzx edx,byte[rax+0xE0]` | 另一个 multitorch bool |
  | 0x2166F/0x2167B | `movzx edx,byte[rax+0xF8]` / `+0xF9` | 两个 bool |
  | 0x216AF | `lea rdx,[rax+0x128]` | 把 row 块（0x128..0x150）传给 `ComputeSheetGeometryRowMode`（字面量@0x9AE000） |
  | 0x216E0 | `lea rdx,[rax+0x158]` | 把 pipe 块（0x158..0x178）传给 pipe 几何计算 |
  | 0x21EEE | `mov r12d,[rax+0xA8]` `movsd xmm7,[rax+0xC0]` `xmm8,[rax+0xC8]` `movzx ebp,byte[rax+0xD0]` `xmm9,[rax+0xD8]` | multitorch 参数 |
  | 0x21F36 | `mov ecx,[rdi+0x9C]` + std::map 查找 | `boost` 预设表（见 B 组） |
  | 0x22369 | `mov edx,[rdi+0x8C]` | common cut cutting preference |
  | 0x225BD/0x226AA | `mov ecx,[rax+0x6C]` + std::map 查找 | `all_settings` 预设表（见 A 组） |

### 0.4 权威字段名表 = JSON 序列化 schema 【已证实】

`..\structure\text_io.cpp`（字面量 0x9DA694；辅助函数 `SaveProblem`=**0x5070E0**、
`LoadProblem`=**0x50B1D0**、`SaveSheet`=0x5091B0、`LoadSheet`=0x5090A0、
`SaveSolution`=**0x50DB70**、`LoadSolution`=**0x50EE50**、`LoadMtInfos`=0x50A550/0x506350、
`LoadCommonCutEvaluation`/`LoadSegment`/`LoadClusteredPart`@0x9DB0A0-B0D0）
把整个问题写成 JSON（落盘路径 `c:\Temp\cns.pb.json`，0x9AC189）。
所有键名字符串集中在 **0x9DA300-0x9DB010**（用 `feat\rng.py 0x9DA300 0x9DB010` 可全量导出）。
按出现顺序可切分出对象块：

* **problem/order 块**：`extra_infos authorizations clustered_parts intergap requested_time layout_cost
  max_active_parts max_different_sheets strict_part_priorities have_priority_interpenetration
  priority_interpenetration assembly_group modules parts clusters sheets`
  以及 `shear shear_corner shear_repulse_from_borders shear_gap shear_thickness
  mark_active mark_size mark_inter_distance floating origin_packing
  try_biggest_part_in_corner try_longest_part_in_corner
  row_enable row_shear_gap row_shear_common_cut_gap row_punch_gap row_punch_common_cut_gap row_alternate
  pipe_enable pipe_gap pipe_common_cut_gap pipe_border_common_cut pipe_border_gap
  multitorch_allowed multitorch_nb_torches multitorch_min_torch_distance multitorch_max_torch_distance
  multitorch_cutting_cost_per_unit multitorch_user_real_material_cost_per_unit
  multitorch_reconfiguration_cost multitorch_vertical_torches
  common_cut_allowed common_cut_gap common_cut_original_part_gap common_cut_cutting_cost_per_unit
  common_cut_min_length common_cut_max_regarding_ratio common_cut_leadin_type common_cut_no_holes
  common_cut_only_bi_modules quality_zone_enable quality_zone_interactions`
* **sheet 块**：`quantity dimension_x dimension_y left_gap right_gap bottom_gap top_gap defect_gap
  used_surface_evaluation used_surface_min_offcut_dimension used_surface_min_offcut_area
  used_surface_usable_offcut_ratio optional_fill_unlimited evaluate_intermediate_as_last
  nesting_origin grain_direction price priority sheet_quality_zones`
* **part 块**：`quantity max_quantity common_cutable extra_gap single_orientation
  single_orientation_rot180_allowed force_bottom hole_status incompatible_sheets`
* **solution/nesting 块**（SaveSolution 0x50DB70）：`version number_of_nested_parts nestings
  sheet_id multiplicity angle flip common_cut_evaluation multitorch_infos number_of_groups
  fill_ratio min_x min_y max_x max_y nested_parts evaluation_ratio used_surface nested_surface
  nested_string final`
* **common_cut 段**（`LoadSegment` 0x9DB0B8）：`common_cut left right left_index right_index
  valid linked number_of_common_cut common_cut_length regarding_length segments`
* **multitorch 段**：`multitorch_part_infos torch_distance group_number torch_number
  nb_active_torches config_index info_nb_torches`

### 0.5 枚举 → 字符串表 【已证实】

由 `0x511080`（1866 条指令的 dump/HTML 函数）构造字符串数组并按索引取值（带 `index < size` 断言）：

* **objective**（getter `0x52F920`；字符串 0x9DB606..0x9DB676）：
  `0 MinimizeX, 1 MinimizeY, 2 NoOffcut, 3 MinimizeArea, 4 MinimizeXThenY, 5 MinimizeYThenX,
   6 IntelligentMinimizeX, 7 IntelligentMinimizeY`（越界 → `ERROR` 0x9DB5EF）
* **nesting_origin**（getter `0x4F8F80`= `[rcx+0xA0]`；字符串 0x9DB5C7..0x9DB5E6）：
  `0 BottomLeft, 1 TopLeft, 2 BottomRight, 3 TopRight`（越界 → `ERROR`）

### 0.6 两个预设表：`all_settings` 与 `boost` 【已证实】

CreateProblem 0x1EE50 里有两处 `std::map<int, Properties>` 查找（node: left=+0x10, right=+0x18,
key=+0x20 —— 标准 `std::map` 树布局）：

1. `boost.find(order.multitorch_cutting_preference) != boost.end()`（断言串 0x9ADEE8，
   代码 0x21F26-0x21F5F，用 key = `Order+0x9C`），命中后调用 `GetMultitorchProperties`（字面量 0x9ADFA0）。
2. `all_settings.find(order.common_cut_safety_preference) != all_settings.end()`（断言串 0x9ADE98，
   代码 0x225A3-0x225F5，key = `Order+0x6C`），命中后调用 `GetCommonCutProperties`（字面量 0x9ADFC0）。

两表都在 CreateProblem 内部由**静态小表**填充（0x20/0x30 字节一条记录，逐条 `std::map::insert`）：
boost 表填充循环在 0x21E1C-0x21EEC（表地址 0x9AE13F..0x9AE16F，3 条 16 字节记录），
all_settings 表填充循环在 0x224D5-0x2259D（栈上 0x20 字节记录，key 1/2/3）。
**【推断】**记录布局 ≈ `{int key; double a; double b; int c; bool d; bool e}`（0x20 字节）。

`GetCommonCutProperties` / `GetMultitorchProperties` 返回的对象布局 【已证实，来自 SaveProblem】：

* **CommonCutProperties**（SaveProblem 0x50841F-0x50853E）：
  `+0x00 int allowed, +0x08 double gap, +0x10 double original_part_gap,
   +0x18 double cutting_cost_per_unit, +0x20 double min_length,
   +0x28 double max_regarding_ratio, +0x30 int leadin_type,
   +0x34 bool no_holes, +0x35 bool only_bi_modules`（≈0x38 字节）
* **MultitorchProperties**（SaveProblem 0x5088C8-0x5089BC）：
  `+0x00 int nb_torches, +0x08 double cutting_cost_per_unit, +0x10 double reconfiguration_cost,
   +0x18 double min_torch_distance, +0x20 double max_torch_distance,
   +0x28 bool vertical_torches, +0x30 double user_real_material_cost_per_unit`（≈0x38 字节）

### 0.7 `SetExtraParameters` 接受的键名 【已证实】

rodata 0x9B009C-0x9B02EF：`enable_common_cut_nesting`、`enable_common_cut_relax_objective`、
`enable_common_cut_repair`、`enable_common_cut_tiling`、`enable_common_cut_filling`、
`enable_beautifier_common_cut`、`enable_beautifier_improve_common_cut`、`use_multitorch_tiling`
（另有云引擎键 `cns_force_cloud` 0x9AC139）。
容器写在 **Order+0x220..0x238**（`SetExtraParameters` 0x11120 的 4 次 store）。

---

## A 组 —— 共边切割 / 链式切割（common cut）

### A.1 导出函数 【已证实】

| 函数 | RVA | 大小 | 参数与效果 |
|---|---|---|---|
| `SetCommonCutMode` | **0xE460** | 404 | `(Order*, int mode, double x)`：`[Order+0x5C] = (mode!=0)`（byte）、`[Order+0x60] = x`（double） |
| `SetCommonCutSafetyPreference` | **0xE940** | 354 | `(Order*, int pref)`：`[Order+0x68] = 1`、`[Order+0x6C] = pref` |
| `SetCommonCutAuthorizations` | **0xEAB0** | 468 | `(Order*, double, double, int r9d, int[栈], int[栈])`：`[Order+0x70]`、`[Order+0x78]`（double）、`[Order+0x68] = 0`、`[Order+0x80] = r9d` |
| `SetCommonCutCuttingPreference` | **0xEC90** | 340 | `(Order*, int)`：`[Order+0x88] = 1`、`[Order+0x8C] = int` |
| `SetCommonCutObjective` | **0xEDF0** | 337 | `(Order*, double a=xmm1, double b=xmm2)`：`[Order+0x88] = 0`；若 a≠0 则 `[Order+0x90] = b/a`（`divsd xmm6,xmm7`） |
| `SetPartCommonCutMode` | **0xDE50** | 36 | `(Part*, int mode)`：`[Part+0x1C] = (mode!=0)`（structure 层小函数） |
| `CNS_GetNumberOfCommonCuts` | **0xD710** | 346 | `(cns_nesting*)` → 返回 `nesting->evaluation().common_cut_segments.size()`（断言 `cns_nesting->nesting` 0x9ACDD1，日志 `// GetNumberOfCommonCuts ` 0x9ACDE6） |
| `CNS_GetCommonCut` | **0xBA50** | 825 | `(cns_nesting*, nesting_number, common_cut_number, out…)`；断言 `common_cut_number < evaluation.common_cut_segments.size()`（0x9ACB10）与 `nesting->nesting`（0x9ACAFB）；取第 common_cut_number 段并写出其数据 |

注意：`0x88` 是**标签**：`1` = 用"切割偏好预设"（`+0x8C` 为 int，索引 `all_settings`），
`0` = 用"显式目标"（`+0x90` 为 double）。multitorch 在 `+0x98` 有完全相同的模式（见 B 组）。

### A.2 算法与语义 【已证实 + 推断】

* **common cut segment 的数据模型**（solution JSON，SaveSolution 0x50DB70 + `LoadSegment` 0x9DB0B8）：
  一条段包含 `common_cut`（类型/标志）、`left`、`right`（两段几何/长度）、`left_index`、`right_index`
  （左右两侧的 nested part 索引或子段索引）、`valid`、`linked`。
  `EVALUATION(valid: linked: common_cut: quality:)`（0x9DC54F）是该结构的打印格式；
  `CommonCutLeadinType(`（0x9DC5B0）是引入方式枚举的打印。
* **一段共边切割 = 两个相邻排版的零件共用同一条切割线** 【推断】：
  `left_index`/`right_index` 指向共边的两个零件（或两个子段），`left`/`right` 是两段重合的线段；
  `linked` = 两侧已在几何上连成一条连续切割线（可一次穿孔/连续割），`valid` = 该段通过所有几何检查。
  上层统计量：`number_of_common_cut`（共边段数）、`common_cut_length`（共边总长）、
  `regarding_length`（用于目标函数的分母/权重长度）。
* **Safety preference 枚举（`all_settings` 的 key）** 【已证实 + 推断】：`Order+0x6C` 是一个**预设索引**，
  在 CreateProblem 里必须存在于 `all_settings` 表中，否则触发断言。
  每个预设给出一整套 `CommonCutProperties`：`allowed`、`gap`（共边间隙）、`original_part_gap`
  （零件原始间隙，断言 `m_implementation->common_cut_properties.original_part_gap == 0.0` 0x9DA3D0
  说明某些路径要求它为 0）、`cutting_cost_per_unit`、`min_length`（共边最小长度）、
  `max_regarding_ratio`（共边长 / 参照长度的最大比值）、`leadin_type`、`no_holes`（共边处不允许有孔）、
  `only_bi_modules`（只允许双模块共边）。
  ⇒ **"安全偏好"就是在"共边更省料但要求更苛刻"与"更保守"之间选一组阈值** 【推断】。
* **Objective 双参数**：`SetCommonCutObjective(Order*, a, b)` 存 `b/a`。
  结合 `common_cut_max_regarding_ratio` 与 `regarding_length` 推断：目标是共边收益与板材消耗的比值
  `regarding_ratio = 共边长度 / 参照长度`，参数 (a,b) 是两个权重/代价（例如"共边节省的切割长度"与
  "共边引起的最小间距损失"），取其比值作为代价系数。**【推断】**
* `SetCommonCutMode` 的第二参数 x（存 +0x60）在 CreateProblem 0x2149F 处参与
  `maxsd xmm0, [Order+0x60]` —— 说明它是共边间隙的下限（取 max），即 **共边间隙/容差**。**【已证实（指令）+ 推断（语义）】**
* **校验器** `0x1C7C0` 报告 `// BadPartGeometry`、`// BadSheetGeometry`、`// BadSheetPrices`、
  `// BadCommonCutGaps`（0x9ADDD6）——即共边间隙非法是 4 类"坏几何"之一。
* 其他相关断言/开关：`m_implementation->common_cut_computer.get()`（0x9DA4B8，problem.cpp）、
  `m_implementation->common_cut_properties.original_part_gap == 0.0`（0x9DA3D0）。

### A.3 未确认

* `CNS_GetCommonCut` 的每个出参具体含义（段结构字段如何映射到参数）——【未确认】。
* `SetCommonCutAuthorizations` 的 5 个参数语义（`+0x70/+0x78` 两个 double、`+0x80` 一个 int、
  两个栈上 int）——【未确认】；`+0x68=0` 说明它同时清掉 safety-preference 标志。
* `all_settings` 静态表里每个 key（1/2/3…）对应的具体阈值数值——【未确认】。

---

## B 组 —— 多割炬 / 多头火焰切割（multitorch）

### B.1 导出函数 【已证实】

| 函数 | RVA | 大小 | 参数与效果 |
|---|---|---|---|
| `SetMultiTorchMode` | **0xEF50** | 479 | `(Order*, int allowed=edx, int nb_torches=r8d, double min=xmm3, double max=[rsp+0xC0], int vertical=[rsp+0xC8])`；效果：`[+0xC0]=min`、`[+0xC8]=max`、`[+0xD0]=(vertical!=0)`、`[+0xA8] = allowed ? nb_torches : 0`（`cmove edi,eax` where eax=0） |
| `SetMultiTorchCuttingPreference` | **0xF130** | 388 | `(Order*, int)`：`[+0x98]=1`、`[+0x9C]=int` |
| `SetMultiTorchObjective` | **0xF2C0** | 633 | `(Order*, double a=xmm1, double b=xmm2, int c=r9d, double d=[rsp+0xD0])`；见下 |
| `SetDetailedMultiTorchObjective` | **0xF540** | 629 | 三个 double 参数（xmm1/xmm2/xmm3），尾部调用 `SetMultiTorchObjective`(0xF2C0) |
| `CNS_GetPartTorchInfos` | **0xD870** | 826 | `(cns_nesting*, part_index, out…)`；断言 `part_index < nesting->nesting->nested_parts().size()`(0x9ACE18) 与 `part_index < …multitorch_infos().m_infos.size()`(0x9ACE50)；返回该零件的割炬信息 |

`SetMultiTorchObjective` 的算法（0xF40E-0xF463，常量在 rodata 0x9AD700/0x9AD708/0x9AD710
= **0.9 / 0.66 / 1000.0**）：
```
xmm7 = a (参数1), xmm6 = b (参数2), edi = c, xmm8 = d (参数4)
[Order+0xD8] = a                                  // 原始值
if (a > 0) { t = a / 1000.0 ; t = max(t, b) ; xmm6 = t ; xmm1 = xmm6 / a }
else       { ... 均非正时 xmm1 = 0.9 }
[Order+0xB0] = xmm1
if (xmm6 > 0) { xmm8 = xmm8 / xmm6 ; [Order+0xB8] = (c != 0) ? xmm8 : 0.66 }
else            [Order+0xB8] = 0.66
[Order+0x98] = 0                                  // 关闭"预设"标签
```
⇒ `a` 是"每单位长度切割成本"（先 /1000 换算 mm→m），`b` 是"每单位切割长度的成本下限"，
`+0xB0 = max(a/1000,b)/a`（成本比），`+0xB8 = d/max(a/1000,b)`（材料成本相对切割成本之比），
`c` 是"是否启用用户材料成本"开关，`d` = 用户真实材料单价，`+0xD8 = a`。
映射到 `MultitorchProperties`：`+0x08 cutting_cost_per_unit`、`+0x30 user_real_material_cost_per_unit`、
`+0x10 reconfiguration_cost`、`+0x18/+0x20 min/max torch distance`。**【已证实（指令与偏移）+ 推断（命名对应）】**

### B.2 数据模型 【已证实 + 推断】

* `multitorch_infos()`（字面量 0x9DAF6E / 断言 0x9ACE50）返回一个对象，其成员是
  `vector<...> m_infos`（字面量 `m_infos` 出现在 `CNS_GetPartTorchInfos` 的断言里）；
  对应的输出 JSON 键是 `multitorch_infos` / `multitorch_part_infos`（0x9DA79E），
  每项字段：`torch_distance`、`group_number`、`torch_number`、`nb_active_torches`、
  `config_index`、`info_nb_torches`。⇒ **每个零件（或每组）记录它被安排在哪个割炬组、
  用哪个割炬配置、激活几个割炬、相邻割炬间距**。**【已证实（字段名）+ 推断（语义）】**
* `nb_torches_configs`（0x9DB76B）、`#torches`（0x9DB77E）、`mt_infos`（0x9DB78C）
  出现在绘制/统计代码里；`!torch_configs.empty()`（0x9DBE17）、
  `..\structure\multitorch_eval.cpp`（0x9DBE30）、`ComputeBestConfigSequence`（0x9DBE70）
  ⇒ 存在"从所有可用割炬配置中求最优配置序列"的算法。**【已证实（符号）+ 推断（算法）】**
* 打印格式（0x9DB435-0x9DB48D）：`torches: `、`min/max distance: `、`boost: `、`reconfig: `、
  `material cost: `、`cutting time cost: `、`cutting time speed: x` —— 与 MultitorchProperties 字段一一对应，
  其中 **`boost`** 就是 `SetMultiTorchCuttingPreference` 选出的预设。**【已证实】**
* 相关类（`re\vtables.json`，vtable RVA / 前几个虚槽 RVA）：
  * `N5Multi16MultiTorchNesterE` → vtable **0xA3B8A0**，槽 0x697260、0x697230、0xB4440、0x77C90、0x77C60、0x7BCC0
  * `N6Tiling19MultitorchEvaluatorE` → vtable **0xA3D310**，槽 0x76F260、0x76F250、0x7E9240、0x4E7E50
  * `N6Tiling22OldMultitorchEvaluatorE` → vtable **0xA3D340**，槽 0x76F9B0、0x76F9A0、0x7EB320、0x4E7E50
  * `N5Multi12TilingNesterE` → vtable 0xA3B5A0；`N5Multi9RowNesterE` → 0xA3BB30
* `use_multitorch_tiling`（0x9B02EF）是 `SetExtraParameters` 的开关之一 ⇒ 多割炬有两种实现路径
  （tiling 版 vs. old）。**【已证实（键名）+ 推断】**
* 断言 `part_number < m_common_cut_tiling_parts.size()`（0x9BD3D0）出现在 0x764A80、0x769410；
  `!shear`（0x9BD4D1）出现在 0x765460 —— 都在 UPX1 的 tiling/compact 代码区，说明
  **多割炬/共边 tiling 与 shear 模式互斥**。**【已证实（断言位置）+ 推断（互斥）】**

### B.3 约束与目标函数

* **割炬数与间距约束** 【已证实（字段读取）+ 推断（几何）】：
  `nb_torches`(Order+0xA8)、`min_torch_distance`(+0xC0)、`max_torch_distance`(+0xC8)、
  `vertical_torches`(+0xD0) 在 CreateProblem 0x21EEE-0x21F15 被取出后传入 multitorch 求值器。
  语义：一台多头切割机上 N 个割炬按固定间距排布，同一次走刀同时切出 N 条平行线。
  因此**零件必须能被"整组平移"到同一条走刀的割炬位置上**，相邻切割线的间距必须落在
  `[min_torch_distance, max_torch_distance]` 内；`vertical_torches` 表示割炬是竖直方向（横排）。
  ⇒ 这既是**间距约束**（相邻线间距范围）也是**数量约束**（一次最多 N 条线，多余部分需要重配置）。**【推断】**
* **目标函数**：MultitorchProperties 的 `reconfiguration_cost`（换配置代价）、
  `cutting_cost_per_unit`（切割时间成本）、`user_real_material_cost_per_unit`（材料成本）、
  `boost`（偏好预设的加成系数）共同构成代价函数，与 `common_cut_cutting_cost_per_unit`
  的写法同构。**【已证实（字段）+ 推断（公式）】**
* **cutting preference 枚举** = `boost` 表的 key（`Order+0x9C`），CreateProblem 0x21F36 处必须命中，
  否则断言失败。⇒ 该枚举是"预置的 boost/间距/割炬数组合"。**【已证实】**

### B.4 未确认

* `boost` 表每个 key 的具体数值（0x9AE13F-0x9AE16F 的 3 条 16 字节记录未逐字节解码）——【未确认】。
* `SetMultiTorchMode` 的 5 个参数的**官方**参数名/顺序（据日志顺序与 JSON 键推断为
  allowed, nb_torches, min_dist, max_dist, vertical）——【推断】。
* `MultiTorchNester` / `MultitorchEvaluator` 虚槽内部的具体几何判定代码（只取到 vtable/槽 RVA，未逐槽展开）
  ——【未确认】。

---

## C 组 —— 剪切 / 闸刀模式（shear / guillotine）

### C.1 导出函数 【已证实】

| 函数 | RVA | 大小 | 效果 |
|---|---|---|---|
| `SetShearMode` | **0xDDC0** | 33 | `(Order*, int)` → `[Order+0x44] = int` |
| `SetPartialShearMode` | **0xDDF0** | 36 | `(Order*, int)` → `[Order+0x48] = int` **且** `[Order+0x44] = int` |
| `SetShearGap` | **0xCEF0** | 45 | `(Order*, double xmm1)` → `[Order+0x50] = double` |
| `SetShearRepulseFromBorders` | **0xDE20** | 33 | `(Order*, int)` → `[Order+0x58] = int` |
| `SetSheetGaps` | **0xCCB0** | 388 | `(Sheet*, double, double, double, double栈)` → `+0xF8 / +0x100 / +0x108 / +0x110` |

### C.2 shear 块的结构与落地位置 【已证实】

`LoadShear`（**0x506C10**，124 B）按 JSON 键顺序读入一个紧凑结构，证明 shear 逻辑块是：
```
+0x00 bool shear                       (键 "shear")
+0x01 bool shear_corner                (键 "shear_corner")
+0x02 bool shear_repulse_from_borders    (键 "shear_repulse_from_borders")
+0x08 double shear_gap                  (键 "shear_gap")
+0x10 double shear_thickness            (键 "shear_thickness")
```
（size 0x18）。对应到 Order 的字段：`0x44` shear、`0x48` shear_corner/partial、
`0x50` shear_gap、`0x58` shear_repulse_from_borders ⇒ 块占据 **0x44..0x5C**，
紧接着 `0x5C` 是 common cut mode（A 组），完全吻合。
`shear_thickness`（0x54 或 0x4C）没有对应导出 setter，只能从 JSON 读入——【未确认具体偏移】。

### C.3 约束与强制点 【已证实 + 推断】

* **条带/行结构** 【推断，证据充分】：闸刀（guillotine）只能整刀直切，所以排版必须能被
  一系列平行直线切分 ⇒ 零件被组织成**条带/行（strips/rows）**，条带边界是贯通的直线切割，
  条带之间用 `shear_gap` 作为间隙，`shear_repulse_from_borders` 让条带从板边回退。
  `shear_corner`（partial shear）表示允许在角部做部分剪切/两次半刀。
  `shear_thickness` 是材料厚度（影响闸刀能力/最小条带宽度）。
  支持证据：JSON 键把 shear 与 row/pipe **并列在行/条带一族**；row 模式带
  `row_shear_gap` / `row_shear_common_cut_gap`（见 D 组）；断言 `!shear` 出现在
  共边 tiling 代码（0x765460）中。
* **强制点**：
  * `Structure::CreateProblem` **0x1EE50**（读取 Order 工艺块并生成内部问题；shear 字段在 0x44-0x58）。
  * `N5Multi9RowNesterE`（vtable 0xA3BB30）与 `N5Multi12TilingNesterE`（0xA3B5A0）：
    条带/行式排版器。**【推断：它们是 shear/row 的执行者】**
  * `!shear` 断言 @ **0x765460**：共边 tiling 在 shear 模式下的非法组合检查。**【已证实（位置）】**
  * `part_number < m_common_cut_tiling_parts.size()` @ 0x764A80 / 0x769410。
* 统计/绘制：`shear`、`shear gap: `、`shear common cut gap: `、`punch gap: `、
  `punch common cut gap: `（0x9DB407、0x9DB502、0x9DB50E、0x9DB525、0x9DB531）——
  **剪切模式下还要区分 shear（剪切）与 punch（冲压）两套间隙**，各自有"普通间隙"与"共边间隙"。**【已证实】**

### C.4 未确认

* `SetShearMode` / `SetPartialShearMode` 的枚举取值（0/1/2…）——【未确认】。
* `shear_thickness` 在 Order 内的确切偏移——【未确认】。
* 条带划分算法本体（在 `Multi::RowNester`/`Tiling::*` 内）未展开——【未确认】。

---

## D 组 —— 管材模式与行模式（pipe / row）

### D.1 导出函数 【已证实】

| 函数 | RVA | 大小 | 效果 / 返回值 |
|---|---|---|---|
| `SetRowMode` | **0xFBF0** | 244 | `(Order*, int edx, double xmm2, double xmm3, …)`；小块函数，效果：`[Order+0x128]`、`[+0x130]`、`[+0x138]`、`[+0x140]`、`[+0x148]`（5 个槽，部分为 double）与 `[Order+0x150] = (al!=0)`；末尾调用内部 `0x54C400` |
| `SetPipeMode` | **0xFCF0** | 568 | 效果：`[Order+0x158]`、`[+0x160]`、`[+0x168]`、`[+0x170]`、`[+0x178]`（5 个值）；调用内部 `0x54C430` |
| `GetNumberOfRows` | **0xFF30** | 271 | `(cns_nesting*)` → 返回行数（= `row_intervals.size()`） |
| `CNS_GetRow` / `GetRow` | **0x10040** | 384 | `(cns_nesting*, nesting_number, row_number, double* a, double* b)`；断言 `row_number < row_intervals.size()`（0x9AD188）。函数尾部：`movsd xmm0,[rbx]; movsd [rdi],xmm0; movsd xmm0,[rbx+8]; movsd [rsi],xmm0` ⇒ **写出该行的两个 double（起点/终点）** |

关键点：`row_intervals` 是一个 `vector<pair<double,double>>`（每条 16 字节，
`sub_51E060` 做下标/边界检查），`GetRow` 通过它按 `row_number` 取出 (start,end)。

### D.2 row 块布局与 row-interval 构造 【已证实 + 推断】

`LoadRow`（**0x506D80**，144 B）读出：
```
+0x00 bool   row_enable                     (键 "row_enable")
+0x08 double row_shear_gap                  (键 "row_shear_gap")
+0x10 double row_shear_common_cut_gap       (键 "row_shear_common_cut_gap")
+0x18 double row_punch_gap                  (键 "row_punch_gap")
+0x20 double row_punch_common_cut_gap       (键 "row_punch_common_cut_gap")
+0x28 bool   row_alternate                  (键 "row_alternate")
```
（size 0x30）。对应 Order：**0x128 row_enable、0x130 row_shear_gap、0x138 row_shear_common_cut_gap、
0x140 row_punch_gap、0x148 row_punch_common_cut_gap、0x150 row_alternate** —— 与
`SetRowMode` 的写点完全一致，且 `CreateProblem` 在 **0x216AF** 处 `lea rdx,[rax+0x128]`
把这个块交给 `ComputeSheetGeometryRowMode`（字面量 0x9AE000）。**【已证实】**

* **row_interval 构造** 【推断】：在 `ComputeSheetGeometryRowMode` 内，用板材的
  `dimension_y` 与 `row_shear_gap`（以及 punch/shear 两套 gap、是否 alternate 交错）把板高切成
  一串 y 区间 `row_intervals = [(y0,y1), (y1,y2), …]`；每个区间即"一行"。
  所有属于同一行的零件共享同一对 y 边界 ⇒ `CNS_GetRow` 返回的就是这对边界。
  `row_alternate` 让相邻行的排版方向交替（常见于行式/条带式排版以减少浪费）。**【推断】**
* **零件分配到行** 【推断】：零件按其 y 跨度落在哪个区间即属于该行；行内沿 x 方向排布。
  `GetRow` 让调用方（上层 GUI/报表）能够把每个 nested part 归到某一行显示。

### D.3 pipe 块 【已证实 + 推断】

`LoadPipe`（**0x506E10**）按 JSON 键读 `pipe_enable`、`pipe_gap`、`pipe_common_cut_gap`、
`pipe_border_common_cut`、`pipe_border_gap`，对应 `SetPipeMode` 写入的
**Order+0x158 / 0x160 / 0x168 / 0x170 / 0x178**（`CreateProblem` 0x216E0 `lea rdx,[rax+0x158]`）。
管材模式 = 板料被弯成管/型材，排版沿管壁展开；`pipe_border_gap` / `pipe_border_common_cut`
处理管材边缘的间隙与共边。**【已证实（键与偏移）+ 推断（语义）】**
与 row 的差别：row 是**在板材平面内切行**，pipe 是**沿管材的轴向条带**；两者的参数结构同构
（1 个 enable + 4 个 double/bool）。**【推断】**

### D.4 相关类与未确认

* `N3Row8SqueezerE`（vtable **0xA3B1E0**，槽 0x138BE0、0x138CA0、0x13A360）、
  `N3Row14BasicDistancerE`（vtable **0xA3B1B0**，槽 0x679060、0x679050、0x7CA810）。
  ⇒ `Row::Distancer`/`Row::Squeezer` 是行式排版的"距离度量/压缩"策略类。**【已证实（存在）+ 推断（作用）】**
* `Multi::RowNester` vtable **0xA3BB30**（槽 0x8EB40、0x8EEA0、0xB4430、0x8CD20、0x8C010、0x913E0）。
* 【未确认】`row_intervals` 具体生成代码（`ComputeSheetGeometryRowMode` 的宿主函数体未展开）；
  `SetRowMode`/`SetPipeMode` 的每个参数语义；`Row::Distancer`/`Squeezer` 槽的具体算法。

---

## E 组 —— 皮革 / 纹理 / 缺陷 / 限制区 / 标记 / 开放刀具路径

### E.1 函数清单 【已证实（RVA/大小来自 exports_table.json）】

| 函数 | RVA | 大小 | 备注 |
|---|---|---|---|
| `SetLeatherMode` | **0x19C40** | 411 | 效果 `[obj+0x108] = int`（out_fields） |
| `AddLeatherQualityZoneInPart` | **0x19F40**（另有 0x19DE0 一版） | 350/342 | 日志名 `AddLeatherQualityZoneInPart` |
| `AddLeatherQualityZoneInSheet` | **0x1A0A0** | 331 | |
| `SetMarkMode` | **0x188D0** | 529 | 效果 `[obj+0xE8]`、`[obj+0xF0]`（两个 double：mark_size / mark_inter_distance） |
| `GetNumberOfMarks` | **0x18AF0** | 889 | 返回标记数 |
| `GetMark` | **0x18E70** | 1312 | 返回第 n 个标记（几何，代码量大） |
| `AddNonRectangularSheet` | **0x157A0** | 1098 | 效果 `[obj+0x1B8]`（一个容器） |
| `AddDefectToSheet` | **0x14190** | 124 | 薄包装，转发到 `AddPolygonDefectToSheet` |
| `AddPolygonDefectToSheet` | **0x16970** | 426 | 日志 `// AddPolygonDefectToSheet` |
| `CNS_AddDefectFromNestedPart` | **0x12F40** | 894 | |
| `SetDefectGap` | **0x109C0** | 388 | 效果 `[obj+0x118] = double` |
| `AddToolPathToPart` | **0x101C0** | 127 | |
| `AddHoleInToolPath` | **0x10240** | 124 | |
| `AddInflatedToolPathToPart` | **0x12C60** | 169 | |
| `CNS_AddOpenToolPathToPart` | **0x12D10** | 552 | |
| `AddOpenCuttingPathToPart` | **0x14A60** | 678 | 效果 `[part+0x88] = rax`（刀具路径容器） |
| `CNS_AddToolPathDefectToSheet` | **0x102C0** | 190 | **不是导出**（内部函数，引用字面量 0x9AD1CE） |
| `CNS_AddExternalToolPathBoundaryToSheet` | **0x10380** | 178 | **不是导出**（内部，字面量 0x9AD1F0） |
| `CNS_SheetAddRestrictedZone` | **0x1A210** | 1468 | |
| `CreateRestrictedZoneConstraint` | **0x1AA90** | 944 | |
| `CNS_ForcePartOnBottomBorder` | **0x1A8F0** | 411 | 效果 `[obj+0x209] = 1` |
| `CNS_SetZoneRestrictedPart` | **0x1AE40** | 507 | 效果 `[obj+0x8]` |
| `ForcePartInsideHole` | **0xC610** | 43 | `[part+0x20A] = 1`、`[part+0x20B] = 0` |
| `ForcePartOutsideHole` | **0xC640** | 43 | **不是导出**（内部，字面量 0x9ACBDE），镜像上面 |
| `SetSheetGrainDirection` | **0xC9A0** | 372 | 见 E.3 |
| `SetExtraGapOnPart` | **0x14450** | 449 | 效果 `[part+0x10] = double`（键 `extra_gap`） |

### E.2 层 / 质量区模型 【已证实（证据）+ 推断（结构）】

* 断言 `quality >= 0 && quality < 9`（0x9ADCAA）出现在 **0x1C980**、**0x1EE50**、**0x7BF0C0**；
  断言 `quality >= 0 && quality < 100`（0x9ADDEA）出现在 **0x1C980** 与 **0x1EE50**。
  ⇒ **同时存在 9 档（0..8）与 100 档（0..99）两套质量等级**。
  9 档与 `../structure/border_property.hpp`（0x9ADCC8 / 0x9DB160）成对出现，
  且 `GetLayerLeatherPart`(0x9AE0B0) / `GetLayerLeatherSheet`(0x9AE0D0) 与
  `GetLayerRestrictedZonePart`(0x9AE070) / `GetLayerRestrictedZoneSheet`(0x9AE090)
  都在 **0x1C980** 与 **0x1EE50** 中被引用 ⇒ **"层（layer）"就是质量区在零件/板材上的分层表示，
  0..8 共 9 层是皮革/限制区的层数**。100 档更可能是细粒度质量（mark/quality zone interaction）。**【推断】**
* `IsLeather(p)`（0x9DB181，也在 `..\structure\border_property.hpp` 0x9DB160 旁边）用于判断零件是否走皮革逻辑。
* `AddLeatherQualityZoneInPart`（0x19F40 / 0x19DE0）与 `AddLeatherQualityZoneInSheet`（0x1A0A0）
  把一个多边形 + 质量值加到零件/板材的 `quality zones` 容器；
  JSON 键 `quality_zone_enable`(0x9DA7DE) 与 `quality_zone_interactions`(0x9DA7F2)、
  `sheet_quality_zones`(0x9DAC9D) 说明**板材也有质量区**，且区之间存在交互规则。
  **约束语义**：皮革零件带质量等级 q_part，板材区域带质量等级 q_zone；
  只有 `q_part <= q_zone`（或按 `quality_zone_interactions` 规则）的区域才允许放置该零件。**【推断】**
* `SetLeatherMode` 写 `obj+0x108`（int），是全局开关/模式。**【已证实（写点）】**

### E.3 纹理方向（grain） 【已证实 + 推断】

* `SetSheetGrainDirection` **0xC9A0**（372 B，带守卫、参数 `(Sheet*, int edx)`）。
  序列化侧：`SaveProblem` 0x5074E1 调 `0x4F8F90` 判断"是否有 grain"，再以 `grain_direction`
  键输出（值由 0x4F8FA0 一类的 getter 取）；`SetSheetGrainDirection` 自身未见直接 store
  ⇒ 通过内部 setter 写入，**偏移【未确认】**。
* 强制点：断言 `false && "internal error mode not yet supported with grain"`（0x9D9400）
  出现在 **0x4BA110** ⇒ 某条内部路径明确不支持 grain，即 grain 约束是在这一族代码里检查的。**【已证实（断言）+ 推断】**
* 语义：`grain_direction` 表示材料纹理方向（0 = 无/任意，1 = 水平，2 = 垂直之类），
  零件自身的纹理要求必须与板材一致才能放置；SVG 打印里有 ` vertical grain `（0x9DB39B）。**【推断】**

### E.4 标记（marks） 【已证实 + 推断】

* `SetMarkMode` 0x188D0 写两个 double 到 `obj+0xE8` / `obj+0xF0`，对应 JSON 键
  `mark_active` / `mark_size` / `mark_inter_distance`（0x9DA935-0x9DA94B）中的
  `mark_size`（标记尺寸）与 `mark_inter_distance`（标记间距）。**【已证实（键 + 写点）+ 推断（对应）】**
* `GetNumberOfMarks` 0x18AF0、`GetMark` 0x18E70：从解中枚举标记；标记在 SVG 图层 `__marks__`
  （0x9DB80B）、绘制函数 `DrawSVGMarks`（0x9DB968）、属性 `properties.active`（0x9DB815）中出现。
  ⇒ **mark 是排版完成后在板材上打的标记（如零件编号/基准点/纹理方向指示）**，输出为独立 SVG 层。**【推断】**
* `GetMark` 有 1312 字节代码 ⇒ 返回的是一小段几何（位置/尺寸/形状），不是一个标量。**【已证实（大小）+ 推断】**

### E.5 缺陷与限制区 【已证实（写点/键）+ 推断（语义）】

* 缺陷：`AddDefectToSheet`(0x14190) → `AddPolygonDefectToSheet`(0x16970)；
  `CNS_AddDefectFromNestedPart`(0x12F40) 把已排版零件的位置转成板材缺陷；
  `SetDefectGap`(0x109C0) 写 `obj+0x118`（键 `defect_gap`）。
  ⇒ 缺陷是多边形禁区，`defect_gap` 是零件与该区之间的最小间距。**【推断】**
* 限制区：`CNS_SheetAddRestrictedZone`(0x1A210) 加区域、`CreateRestrictedZoneConstraint`(0x1AA90)
  把区域转成约束、`CNS_SetZoneRestrictedPart`(0x1AE40) 写 `obj+0x8` 把"某零件只能/不能在该区"绑定。
  `CNS_ForcePartOnBottomBorder`(0x1A8F0) 写 `obj+0x209] = 1`（与 `ForcePartInsideHole` 的
  `+0x20A/+0x20B` 相邻，同属 "border/hole 强制" 字节族）。**【已证实（写点）】**
* 孔内/孔外：`ForcePartInsideHole` 0xC610 写 `part+0x20A=1, part+0x20B=0`；
  `ForcePartOutsideHole` 0xC640 镜像。JSON 键 `hole_status`(0x9DAD27) 即该标志。
  `force_bottom`(0x9DAD1A) 是零件级标志，由 `CNS_ForcePartOnBottomBorder` 设置。**【已证实】**

### E.6 开放 / 膨胀刀具路径 【已证实（结构）+ 推断（语义）】

* `AddToolPathToPart`(0x101C0)、`AddHoleInToolPath`(0x10240)、`AddInflatedToolPathToPart`(0x12C60)、
  `CNS_AddOpenToolPathToPart`(0x12D10)、`AddOpenCuttingPathToPart`(0x14A60) 都往
  **`part+0x88`** 的容器里加东西（`AddOpenCuttingPathToPart` 0x14C60 `Q[rsi+0x88] <- rax`）。
* **"开放刀具路径" = 非闭合切割轮廓**（例如坡口/刻线/起割引入段）：闭合轮廓是 part 的
  external boundary / hole，开放路径单独存在，可以在零件内也可以在板材上。
  `AddHoleInToolPath` 在一条开放路径内部再挖一个孔。
  `AddInflatedToolPathToPart` = 把该路径按一定量**外扩（inflate）**后加入（用于间隙/干涉检查），
  外扩量【未确认】。**【推断】**
* `CNS_AddToolPathDefectToSheet`(0x102C0) 把刀具路径当作缺陷加入板材；
  `CNS_AddExternalToolPathBoundaryToSheet`(0x10380) 把刀具路径当作板材外边界。
  两者**均不是导出函数**（EXPORS 表里没有这两个地址；它们只作为内部函数存在，
  但保留了 `CNS_` 前缀的 `__func__` 字面量）。**【已证实】**

### E.7 未确认

* 层（layer）的准确数据结构与 `GetLayer*` 的返回值（函数体 0x1C980 / 0x7BF0C0 未逐行展开）——【未确认】。
* `SetSheetGrainDirection` / `SetLeatherMode` 的对象类归属与 `grain_direction` 的存储偏移——【未确认】。
* `AddLeatherQualityZoneInPart` 两个重载的区别、区域多边形参数格式——【未确认】。
* 9 档 vs 100 档质量各自的 API 入口——【未确认】。

---

## F 组 —— 装配组与建议分组

### F.1 函数清单 【已证实】

| 函数 | RVA | 大小 | 效果要点 |
|---|---|---|---|
| `CNS_CreateAssemblyGroup` | **0x10B50** | 395 | `Q[rdx+0x0] <- rax`、`Q[rbx+0x2B0] <- rdx` ⇒ 在 **Order+0x2B0** 挂一个装配组对象 |
| `CNS_AddAssemblyGroupPart` | **0x11830** | 180 | `Q[rdx+0] <- rax`、`Q[rbx+0x18] <- rdx`、`Q[rbx+0x30] <- rax` ⇒ 组内零件容器在 `+0x18`/`+0x30` |
| `AddSuggestedPartsGrouping` | **0x11640** | 483 | 参数里出现 `order`（字面量 0x9AD477）；日志名 `AddSuggestedPartsGrouping` |
| `AddPartToSuggestedPartsGrouping` | **0xF7C0** | 1072 | 日志/断言含 `group`（0x9AD150） |
| `CNS_AddSuggestedPartsGrouping` | **0xF7C0 附近的 CNS 版本**（字面量 0x9AD5B0） | — | 与上面成对 |
| `CNS_AddPartToSuggestedPartsGrouping` | 字面量 0x9AD580 | — | 同上 |
| `MakeClusterFromSuggestedPartsGrouping` | **0x1C2A0** | 672 | **不是导出**；内部函数，断言 `it != part_maping.end()`（0x9AD059）、文件 `internal.cpp`（0x9AD071） |
| `SetIncompatibleSheet` | **0x11490** | 423 | `Q[rsi+0x1F8] <- rax`（容器） |
| `ForcePartInsideHole` | **0xC610** | 43 | `part+0x20A=1`、`part+0x20B=0` |
| `ForcePartOutsideHole` | **0xC640** | 43 | 内部函数，镜像 |
| `SetPartAuthorizations` | **0xC1A0** | — | `part+0x188`、`+0x190`、`+0x198` |
| `AddPartSpecificAuthorizations` | **0x10CE0** | — | `part+0x1A8` |

### F.2 从"分组"到"聚类约束"的路径 【已证实（调用链）+ 推断（语义）】

调用链（`re\prof2.pkl` 的 callers）：
```
Structure::CreateProblem (0x1EE50)
        └── 0x1C540  (168 B)
                └── MakeClusterFromSuggestedPartsGrouping (0x1C2A0, 672 B)
```
⇒ **建议分组（suggested grouping）在 CreateProblem 阶段被转成聚类（cluster）**。
其输入是 `part_maping`（零件映射表，断言 `it != part_maping.end()`），输出是 `clusters`
（JSON 键 `clusters` 0x9DAD55、`clustered_parts` 0x9DA678）。**【已证实（调用链/断言）+ 推断（输出）】**

* **assembly group（装配组）**：硬约束。挂在 `Order+0x2B0`，成员列表在组对象的 `+0x18`/`+0x30`；
  序列化为键 `assembly_group`（0x9DADF9，`agroup.isArray()` 0x9DAE25）。
  语义：同一装配组的零件必须**一起排在同一张板上并保持相对位置**（装配件）。
  `AssemblyGroup` 与 `clusters` 并列在 order 键表里，说明它是独立于聚类的结构。**【推断】**
* **suggested parts grouping（建议分组）**：软提示。`AddPartToSuggestedPartsGrouping`
  只是往 `order` 上的一个分组容器里登记"这些零件适合放一起"；随后
  `MakeClusterFromSuggestedPartsGrouping` 把它变成聚类候选，交给
  `Structure::automatic_cluster.cpp`（0x9DC118，符号 `GetBestEraseAndUpdate` 0x9DC200、
  `ToCluster` 0x9DC218、`[Cluster : time=… nb_parsed=… potential=…]` 0x9DC0DA）
  的自动聚类算法打分/合并。**【已证实（符号）+ 推断（机制）】**
* **incompatible_sheets**：`SetIncompatibleSheet`(0x11490) 往 `Order+0x1F8` 的容器里加；
  JSON 里它是 **part 级** 键（`incompatible_sheets` 0x9DAD33 位于 part 块）。
  语义：某零件不得放在某些板上（材质/厚度/纹理不兼容）。**【已证实（键位置）+ 推断】**
* **hole_status**：`ForcePartInsideHole`/`ForcePartOutsideHole` 写 `part+0x20A`/`+0x20B`，
  JSON 键 `hole_status`(0x9DAD27) 与 `force_bottom`(0x9DAD1A) 相邻。
  ⇒ 值域至少 {自由, 必须在孔内, 必须在孔外}，用于把零件塞进其他零件的孔里（套料）。**【已证实（写点/键）+ 推断（值域）】**

### F.3 未确认

* assembly group 与 suggested grouping 各自的具体容器类型与聚类打分公式——【未确认】。
* `CNS_AddSuggestedPartsGrouping` / `CNS_AddPartToSuggestedPartsGrouping` 的准确 RVA
  （只定位到字面量 0x9AD5B0 / 0x9AD580，未回连到函数体）——【未确认】。
* `SetIncompatibleSheet` 的参数（零件 + 板列表？）——【未确认】。

---

## G 组 —— 目标函数、余料评估、板材价格/优先级

### G.1 目标函数枚举 【已证实】

`SetObjective`（**0xCEC0**，45 B）：`(Sheet*/Order*, int edx)` → `[obj+0x08] = int`。
枚举值由 0x511080 的字符串数组确定（顺序即索引），并在 `CreateProblem` 0x20BC8 被读取
（`mov r8d, dword ptr [rax+8]`）：

| 值 | 名称 | 含义 |
|---|---|---|
| 0 | `MinimizeX` | 最小化排版在 X 方向的占用 |
| 1 | `MinimizeY` | 最小化 Y 方向占用 |
| 2 | `NoOffcut` | 不产生（不可用）余料 |
| 3 | `MinimizeArea` | 最小化占用面积 |
| 4 | `MinimizeXThenY` | 先 X 后 Y 字典序 |
| 5 | `MinimizeYThenX` | 先 Y 后 X 字典序 |
| 6 | `IntelligentMinimizeX` | 智能 X（按零件典型尺寸/形状决定） |
| 7 | `IntelligentMinimizeY` | 智能 Y |

（字符串 0x9DB606-0x9DB676；越界打印 `ERROR` 0x9DB5EF。）
`SetSpecificSheetObjective`（**0x13FE0**）写 `[sheet+0x12C] = 1`（有覆盖）+ `[sheet+0x130] = 枚举值`，
即**可以为单张板覆盖全局 objective**。`SetSpecificSheetOrigin`（**0x13E30**）同理写
`+0x124 = 1` + `+0x128 = nesting_origin`（枚举 `0 BottomLeft, 1 TopLeft, 2 BottomRight, 3 TopRight`）。
`SetOrigin`（**0xD050**）写 `[obj+0x0C] = int`。**【已证实】**

【推断】各 objective 的实现位置：`Structure::stats.cpp`（0x9DBB50）里的
`FillRatio`(0x9DBBB8)、`UsedSurfaceAux`(0x9DBBA8)、`UsedSurfaceWithStairs`(0x9DBBD0)、
`Structure::Box`(0x9DBB7F)、`GetPartTypicalDimension`(0x9DBB90) 提供度量；
`Tiling::DensityEvaluator`/`UnlimitedDensityEvaluator`/`UnlimitedXDensityEvaluator`/`ObliqueEvaluator`/
`QuantityEvaluator`/`ReusableEvaluator`（vtable 表在 `re\vtables.json`）是取值器；
`Prc::PriceComputer`/`AlphaPriceComputer`/`BoxPriceComputer`/`HullPriceComputer` 与
`Lp::LinearProgram`/`Coin::CoinLP` 说明整体是**列生成（column generation）+ LP 主问题**，
objective 枚举决定主问题的目标列。

### G.2 余料 / 边角料评估 【已证实 + 推断】

`SetOffcutEvaluation`（**0xE2D0**，399 B）写三个 double：
`[obj+0x28]`、`[obj+0x30]`、`[obj+0x38]`。
对应 JSON 键（sheet 块）：`used_surface_min_offcut_dimension`、`used_surface_min_offcut_area`、
`used_surface_usable_offcut_ratio`（0x9DABD8/0x9DABFA/0x9DAC18），
由 `SaveProblem` 通过 getter `0x52F900`/`0x52F910`/`0x52F930` 输出（0x5073FA-0x507463）。
**推荐映射（按键顺序）**：`+0x28 = min_offcut_dimension`（余料最小边长）、
`+0x30 = min_offcut_area`（余料最小面积）、`+0x38 = usable_offcut_ratio`（余料可用率门槛）。
**【推断（一一对应关系）；三个 offset 的写点【已证实】】**

语义：排版结束后，把板材上剩余区域切成候选"余料块"，只有尺寸 ≥ min_offcut_dimension、
面积 ≥ min_offcut_area、可用率 ≥ usable_offcut_ratio 的块才被算作可回收余料（reusable offcut），
并参与 `used_surface_evaluation`（0x9DABB9）的利用率计算。绘制侧有
`DrawSVGReusableOffcuts`（0x9DB950）与打印 `offcut: `（0x9DB68D）、
`[min dimension: `（0x9DB696）、` min area: `（0x9DB6A7）、` lost value: `（0x9DB6B3）。
**【已证实（符号）+ 推断（语义）】**
`optional_fill_unlimited`（0x9DAC39）与 `evaluate_intermediate_as_last`（0x9DAC51）
是余料/填充相关的开关（对应 `CNS_SetEvaluateIntermediateNestingsAsLast`）。**【已证实（键）】**

### G.3 填充率 【已证实 + 推断】

* `GetFillRatio` **0xB4B0**（34 B）、`GetNestingFillRatio` **0xB4E0**（38 B）——极短的包装函数，
  直接返回一个 double（说明真正的计算在 `Structure::stats.cpp` 的 `FillRatio` 0x9DBBB8 一族）。
* JSON 中 `fill_ratio`（0x9DAF90）出现在 solution 块；`evaluation_ratio`（0x9DAFC0）、
  `used_surface`（0x9DAFD1）、`nested_surface`（0x9DAFDE）也在 solution 块。
  ⇒ 【推断】`fill_ratio = nested_surface / used_surface`（零件总面积 / 实际使用面积，
  与"是否回收余料"有关），`GetNestingFillRatio` 针对单个 nesting 而不是整个 solution。**【推断】**

### G.4 板材价格与优先级 【已证实】

* `SetSheetPrice` **0xCB20**（388 B）→ `[sheet+0x138] = xmm6`（double）。
  序列化侧 sheet 的 price 读的是 `+0x98`（`0x4F8550`，由 `+0x90` 标志保护）
  —— **两套表示的内部不一致（见 0.2 节，【未确认】）**。
* `SetSheetPriority` **0x13C90**（411 B）→ `[sheet+0x120] = edi`（int），键 `priority`（0x9DAC94）。
* `SetSheetGaps` **0xCCB0** → 4 个 gap（见 0.2/C 组）。
* 强制点【推断】：`Multi::AllSheetSelector`(vtable 0xA3B840)、`LargestSheetSelector`(0xA3BAC0)、
  `RandomSheetSelector`(0xA3BA60)、`NoMixSheetSelector`(0xA3B9D0) 是选板策略族；
  price 参与经济性目标（成本最小化），priority 决定板的优先使用顺序；
  `strict_part_priorities`(0x9DADA8) 与 `priority_interpenetration`(0x9DADDF)、
  `have_priority_interpenetration`(0x9DADC0) 控制"高优先级零件允许插入低优先级区域的深度"。
  相关打印：`priorities on parts`(0x9DB59E)、`priorities on sheets`(0x9DB5B2)、
  `&nbsp priority: `(0x9DB723)、`&nbsp per-sheet: `(0x9DB711)、`&nbsp contribution: `(0x9DB6FC)。

### G.5 原点 / 重组策略 【已证实（写点）+ 推断（语义）】

* `SetReorganizeBiggestPartNearOrigin` **0x10470**（42 B）、
  `SetReorganizeLongestPartNearOrigin` **0x104A0**（42 B）——极短布尔设置，
  对应 JSON 键 `try_biggest_part_in_corner`(0x9DA977)、`try_longest_part_in_corner`(0x9DA992)。
  语义：排版完成后把最大/最长的零件重排到靠近原点（板材角）的位置，便于下料。**【推断】**
* `CNS_SetOriginPackingMode`（字面量 0x9ACF14）、`origin_packing`(0x9DA968)、
  `floating`(0x9DA95F, 对应 `CNS_SetFloatingMode` 0x9ACF00)、
  `nesting_origin`（sheet 键，配 `SetSpecificSheetOrigin` / `SetOrigin`）
  ⇒ 原点/浮动/打包三组策略。**【已证实（键与 setter）+ 推断】**
* 代码里 `Sub_4F8F80`（读 `[rcx+0xA0]`）就是 nesting_origin 的 getter。

### G.6 自动停止、填充策略、额外参数 【已证实（写点/键）+ 推断】

* `SetAutomaticStop` **0xE010**（353 B）→ `[obj+0x240] = edi`（int）。语义【推断】：
  达到某个目标（时间/迭代/无改进次数）就自动停止计算；相关键 `requested_time`(0x9DAD67)、
  `layout_cost`(0x9DAD76)。
* `SetFillLastNestingStrategy` **0xDD90**（36 B，structure 层小函数）。语义【推断】：
  最后一个 nesting（最后一块板）的填充策略（例如"尽量填满"或"留余料"）。
* `SetExtraParameters` **0x11120**（868 B）→ `Order+0x220/0x228/0x230/0x238`（一个 map/容器）；
  接受的键见 0.7 节。这些键是**内部算法开关**：common cut 的四种附加策略
  （nesting/relax_objective/repair/tiling/filling）、beautifier 的两种共边优化、
  `use_multitorch_tiling`、`cns_force_cloud`。**【已证实（键与写点）】**
* 其他 order 级开关：`intergap`(0x9DAD5E)、`max_active_parts`(0x9DAD82)、
  `max_different_sheets`(0x9DAD93)；对应 `SetInterpartGap`（断言 `(gap >= 0.0) && "Negative part gap unsupported"` 0x9ACC78）、
  `CNS_SetMultiplicityPreference`(0xD1A0)、`CNS_SetNoMixPreference`(0xD310)、
  `CNS_SetNoSheetMixPreference`(0xD340)、`CNS_SetNoOrientationMixOnPart`(0xDBB0)。**【已证实】**

### G.7 未确认

* `SetOffcutEvaluation` 三个 double 与三个键的严格一一对应——【未确认】。
* `GetFillRatio` / `GetNestingFillRatio` 的具体公式——【未确认】。
* 各 objective 枚举值在主问题里的具体系数/惩罚项——【未确认】。
* `SetAutomaticStop` / `SetFillLastNestingStrategy` 的整数取值含义——【未确认】。

---

## H 组 —— IO / 查询 / 报表

### H.1 生命周期 【已证实 + 推断】

| 函数 | RVA | 大小 | 说明 |
|---|---|---|---|
| `NewLaunchingOrder` | **0x14620** | 1081 | 创建 launching order（问题容器），返回句柄 |
| `DeleteLaunchingOrder` | **0x118F0** | 3660 | 销毁；含 `*** ERROR unterminated/cancelled computation ***`(0x9AD4B0) 与 `ERROR unterminated/cancelled computation`(0x9AD4E8) 两条报错 ⇒ 若还有未终止/已取消的计算，必须报错并回收 |
| `UnLockLaunchingOrder` | 字面量 0x9ACD43 | — | 解锁（另有 `UnLockLaunchingOrderOxy` 0x9ACFD9 / `Sntl` 0x9ACFC0 / `PCId` 0x9ACFF1，分别对应氧燃料授权/加密狗/机器指纹） |
| `GetPCId` | 字面量 0x9ACB76 | — | 机器指纹（`getenv`+`GetAdaptersInfo`/`CryptGenRandom`，见 BRIEF） |

`ab20`（被几乎每个守卫型 setter 调用）= 取 LaunchingOrder 锁/上下文；
`63F6C0` = 校验；两条组合就是"必须先新建成一个未锁定的 launching order 才能设置工艺参数"。**【推断】**

### H.2 DXF 输出 【已证实（符号）+ 推断（细节）】

* `GenerateDxfNesting` **0xBF70**（148 B）——薄包装，转发到内部 DXF 绘制器
  （字面量 `DrawDxf` 0x9DB938 / 0x9DB940，源文件 `..\structure\svg_io.cpp` 0x9DB234 同族）。
* 相关符号：`_border_`(0x9DB7BA) ⇒ 板材边界用一个专门的图层/标记名；
  `fill:white`(0x9DB7C3)、`fill-opacity:0.8;fill:black;stroke:black;stroke-width:0.1%`(0x9DB7D0)
  是 SVG 的样式（DXF 部分未取到组码）**——【未确认】：本轮未找到 DXF 的组码字符串**（`0\nSECTION`
  之类的模式在全字符串表中不突出），因此**不能确认 DXF 的内部实体约定**；只确认了入口与转发目标。

### H.3 HTML / SVG 报表 【已证实】

* `GenerateHtmlLaunchingOrderReport` **0xB1D0**（370 B）：含
  `<h1> Problem contains invalid parts. </h1>`(0x9AC940) 与
  `<h1> Problem contains invalid sheets. </h1>`(0x9AC970) ⇒ 生成前先校验问题，非法则输出错误 HTML。
* `GenerateHtmlSolutionReport` **0xB350**（247 B）。
* `GenerateLaunchingOrderProblem` **0xB8D0**（378 B）：含 `source_version`(0x9ACADF)。
* 生成器主体：`0x511080`（1866 条指令）内建大量文本：
  `nesting evaluation: `(0x9DB678)、`offcut: `(0x9DB68D)、`# groups: `(0x9DB276)、
  `box area: `(0x9DB24C)、`fill-ratio: `(0x9DB269)、`nested parts: `(0x9DB30B)、
  `raw material: `(0x9DB331)、`number of sheets: `(0x9DB345)、`number of layouts: `(0x9DB358)、
  `sheet dimensions: `(0x9DB74E)、`cluster: `(0x9DB761)、`sheet: `(0x9DB387)、
  `time: `(0x9DB400)、`computation_time`(0x9DB3EA)。
* 资源/内嵌 CSS：`cns_solution.css`(0x9DB887) 以及向上查找的相对路径
  `../cns_solution.css`(0x9DB873)、`../../cns_solution.css`(0x9DB85C)；
  引用方式 `<LINK rel=stylesheet type="text/css" href="`(0x9DB1A8)；
  表格样式 `table { float:left } `(0x9DB846)、`table`(0x9DB2BB)、`style`(0x9DB840)。
* SVG 绘制族：`DrawSVG`(0x9DB948)、`DrawSVGAux`(0x9DB990)、
  `DrawSVGReusableOffcuts`(0x9DB950)、`DrawSVGMarks`(0x9DB968)、`GetLeatherLayer`(0x9DB980)、
  `DrawHtmlPartsTable`(0x9DB900)、`GetNestingInformation`(0x9DB920)；
  `__marks__`(0x9DB80B)、`properties.active`(0x9DB815)、`_border_`(0x9DB7BA) 是 SVG 图层/元素名；
  `SHEET NOT FOUND: `(0x9DBACB)、`PART NOT FOUND: `(0x9DBADD) 是查表失败的报错。
* 【推断】报表流程：校验问题 → 对每个 nesting 生成 SVG（板材轮廓 `_border_`、每个零件的多边形、
  余料层、标记层 `__marks__`、皮革/限制区层 `GetLeatherLayer`）→ 用 HTML 表格汇总
  （`DrawHtmlPartsTable`、`GetNestingInformation`）→ 链接 `/cns_solution.css`。

### H.4 查询接口 【已证实（断言）+ 推断】

| 函数 | RVA | 断言/行为 |
|---|---|---|
| `GetSolution` | **0xB0A0** | 29 B，返回当前 solution 指针 |
| `GetNesting` | **0x10F30** | 断言 `nesting_number < solution_aux.size()`(0x9AD410) ⇒ **求解结果保存在 `solution_aux` 向量里**，按 nesting_number 取 |
| `GetNestingDimensions` | **0xBD90** | 返回 nesting 的尺寸 |
| `GetNestingBoundingBox` | **0xB750** | 断言 `min_x && min_y && max_x && max_y`(0x9ACAA0) ⇒ 出参是 4 个 `double*` |
| `GetNestedPart` | **0xD460** | 断言 `nested_part_number <= nested_parts.size()`(0x9ACD68) 与 `part_number <= order->parts.size()`(0x9ACD98) |
| `GetNestedPartPartVariant` | **0x16E60** | 1727 B，取已排版零件实际使用的 PartVariant（朝向/变体） |
| `GetPartWithBadGeometry` | **0xB510** | 43 B，返回第一个几何非法的零件（配合 0x1C7C0 的 `// BadPartGeometry` 族） |
| `GetNumberOfNestings` | 字面量 0x9AC8C7 | |
| `GetFillRatio` / `GetNestingFillRatio` | 0xB4B0 / 0xB4E0 | 见 G 组 |

**多解模型** 【推断】：`solution_aux` 是"中间解 + 最佳解"的序列；
`WaitNextSolution`（0x9AD2FA）、`GetComputationStatus`（0x9AD31F）、
`CNS_SetEvaluateIntermediateNestingsAsLast`（0x9AD218）说明计算过程中会不断产出中间解，
并可用 `SetExtraParameters` 的 `evaluate_intermediate_as_last` 改变对中间解的评价方式。

### H.5 解序列化 【已证实】

* `Structure::UnSerializeSolution` = **0x1C5F0**（454 B，字面量 0x9AE120，另有 0x9AE900 同名字面量
  出现在 cloud_engine.cpp 附近 ⇒ 云端也复用同一反序列化）。
* 落盘/读取：`SaveSolution` **0x50DB70**、`LoadSolution` **0x50EE50**
  （`solution.Bindable(problem)` 0x9ADD7E / 0x9AE8A9；失败串 `Error while parsing solution` 0x9DA60C）。
* 解决 schema 键见 0.4 节；`final`(0x9DAFFB) 与 `intermediate`(0x9AE7F6) 是云端 PUT 的两种负载标记
  （`/pb/` 0x9AE837、`/sol/` 0x9AE7DF、`/best_sol/` 0x9AE7E5）；本地中间结果会写到
  `c:\Temp\computation_solution.html`(0x9AD2D8)。

### H.6 未确认

* DXF 的实体/图层约定（未找到组码字符串）——【未确认】。
* `GenerateHtmlSolutionReport` 与 `GenerateHtmlLaunchingOrderReport` 的完整差异——【未确认】。
* `GetMark` / `GetNestedPartPartVariant` 的出参结构——【未确认】。

---

## 附：本次使用/产出的工具与数据（都在 `re\feat\`）

| 文件 | 用途 |
|---|---|
| `d.py RVA [lo hi]` | 带注释反汇编（RIP 操作数解析为 `STR:"…"` / `FN:<导出名>`；call 目标解析为导出名） |
| `dmp.py RVA...` | 同上，输出到 `feat\out_dis.txt` 便于 grep |
| `xr.py 0xRVA \| 子串` | 谁引用了该字符串（基于 `prof2.pkl` 的 `data_refs`） |
| `rng.py lo hi` / `findstr.py 正则` | 字符串区间/正则检索 |
| `fields.py` → `out_fields.txt` | 每个导出的"this 指针写点"偏移表 |
| `sum.py` | 每个函数的紧凑摘要（参数寄存器、写点、字符串、callee、尾部指令） |
| `gkc.py` / `keymap.py` / `ctx.py` / `range_dis.py` / `gr.py` | 从序列化代码抽取"键→内部 getter/setter→偏移" |
| `tables.py` | 枚举指针表搜索（本例未命中：枚举用局部字符串数组实现） |
| `val.py` | 读某地址的 double/float/int 常量 |
| `map_targets.py` → `targets.tsv` | 名称→RVA/大小/序号/字符串 |
| `keys.py` / `out_keys.txt` | 键与后续调用的对照 |
| `NOTES.md` | 本次共享侦察笔记（ABI、偏移、schema、枚举表） |

## 总体的"已证实 vs 推断"小结

* **已证实**：所有函数的 RVA/参数寄存器/写点偏移；JSON schema 的完整字段名表；
  objective 与 nesting_origin 两个枚举的数值；`all_settings`/`boost` 两张预设表的存在与查找代码；
  `CommonCutProperties`/`MultitorchProperties` 的字段布局；shear/row/pipe 三个 JSON 子结构的
  精确布局与 Order 偏移；`CreateProblem`(0x1EE50) 是唯一的强制中心及其读取点；
  common cut segment 的字段（left/right/left_index/right_index/valid/linked）；
  multitorch 的 tag 语义（0x98：0=显式目标 1=预设）与 common cut 的同构 tag（0x88）；
  SetMultiTorchObjective 的完整算式与常量 1000.0/0.9/0.66；
  9 档与 100 档两套质量等级断言；`CNS_AddToolPathDefectToSheet` /
  `CNS_AddExternalToolPathBoundaryToSheet` / `ForcePartOutsideHole` /
  `MakeClusterFromSuggestedPartsGrouping` **不是导出函数**。
* **推断（有充分结构证据但未逐行验证算法）**：共边段检测的几何含义；
  多割炬的间距/数量约束与目标函数形式；shear 的条带结构；row interval 的构造；
  余料评估的三参数语义；聚类/建议分组/装配组的机制；报表流程。
* **未确认**：0.2 节 Sheet 双表示的偏移对齐；各 enum 的完整取值域（除 objective/nesting_origin）；
  预设表内的具体数值；DXF 实体约定；各内部算法（Row/Multitorch/Cluster/stats）的实现细节。
