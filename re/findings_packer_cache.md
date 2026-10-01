# `..\tiling\packer_cache.cpp` —— 图案（tiling）计算与缓存 TU

目标轮次：goal round 5。本档只写**已证实**的；未转写的体在 §6 单列。

## 1. 规模与归属

* **276 个函数 / 278,386 字节**（本轮前已引用 35,982 = 12.9%）。
* 归属证据：`direct` —— `0x765460`(13,811 B)、`0x769410`(3,063 B)、`0x158810` 自身引用
  `'..\tiling\packer_cache.cpp'`；`0x764A80`、`0x768B80`、`0x76A010`、`0x763EE0` 等引用同批字符串。

## 2. **图案目录（16 个键）** **[已证实]**

同一批函数传递的字面量即图案的键名（引用点见括号）：

| 键 | 引用点 | 键 | 引用点 |
|---|---|---|---|
| `box` | `0x765460` | `box_min_dist` | `0x765460` |
| `cc_matrix` | `0x765460` | `cc_mono` | `0x765460` |
| `cc_specific` | `0x765460` | `composite_bi` | `0x765460` |
| `composite_box` | `0x765460` | `composite_dual_bi` | `0x765460` |
| `composite_mono` | `0x765460` | `min_box_bi` | `0x765460` |
| `mono` | `0x765460` | `oblique_bi` | `0x765460` |
| `oblique_pentagon` | `0x765460` | `part` | `0x765460` |
| `pentagon` | `0x765460` | `windmill` | `0x765460` |

与 §选项键表里的 `enable_composite_tiling` 同源 —— `composite_*` 四兄弟对应它的开关。
已落到 `lcns::tiling::kPatternKeys`（含 `kPatternKeyCount`）并由 `test_recovered` 断言。

## 3. API 面 **[已证实]**

| 地址 | 字节 | 名字 | 角色 |
|---|---:|---|---|
| `0x158810` | —— | **`ComputeMonoTilings`** | 单一（mono）图案计算；断言 `'!parameters.basic_evaluators && !parameters.quantity_evaluators'` |
| `0x765460` | 13,811 | **`ComputeMinBoxBiTilings`** / **`ComputePartTilings`** / **`OppositePattern`** | 本 TU 最大者；同时引用 `'part'`、`'!shear'`、`'it != mapping.end()'` |
| `0x769410` | 3,063 | **`ComputeCommonCutMonoTilings`** / `GetCommonCutPart` | 共边（common cut）图案；断言 `'part_number < m_common_cut_tiling_parts.size()'`、`'cc_properties.allowed'` |
| `0x768B80` / `0x76A010` | —— | **`GetPart`** | 取零件图案；断言 `'part_number < m_tiling_parts.size()'` |
| `0x764A80` | —— | **`GetCommonCutPart`** | 共边零件图案 |
| `0xC1A0` | —— | **`SetPartAuthorizations`** | 设置零件授权（与 row 路径的 `AuthRecord` 同族概念） |
| `0x763EE0` | 2,974 | —— | 线程池工作体：`'Thread <'`、`' updating part '`、`' tilings.'`、`'skiped.'`、`' in '`、`'level '` |
| `0x76A130` | 4,673 | —— | 线程池入口：打印 `'Packer Cache max threads: '` |

**内部数据**（由断言文本确定）：`m_tiling_parts`、`m_common_cut_tiling_parts` 两个按零件索引的图案数组，
`cc_properties.allowed` 一个共边可用性属性。

## 4. **`'!shear'` —— 与 round 3 的 shear 概念交叉印证** **[已证实]**

`0x765460` 里出现 `'!shear'` 断言；而 round 3 在 `0x2CE00`（mode 2）里发现了 `is_tooling` 与
`"Normal shear is incompatible with … contact …"`。两处独立出现 ⇒ **shear 是一个贯穿 tiling 与调度两层的真实特性**
（图案计算在此显式排除 shear 情形）。这条交叉印证也支持 round 3 对 mode 2 的判断。

## 5. 落到工程

* `tiling.hpp` 新增 **`kPatternKeys[16]` / `kPatternKeyCount`**（16 个键名逐条列出，注明引用点 `0x765460`），
  以及四个 `Compute*Tilings` 入口与 getter 的地址注释；
* `test_recovered.cpp` 断言 `kPatternKeyCount == 17` 且若干键名逐字相符；
* 登记表新增 **`tu.packer_cache`**（`Structural`）。

## 6. **未转写**（本档不声称已完成的部分）

| 范围 | 说明 |
|---|---|
| `0x765460`（13,811 B） | 图案计算主体未逐条转写 |
| `ComputeMonoTilings` / `ComputeCommonCutMonoTilings` 的体 | 未转写 |
| 图案键 → 具体图案几何的生成规则 | **未读**（只知道键名与哪个函数用它们） |
| 缓存键的构成、淘汰策略 | 未读 |
| 线程池的调度与结果合并 | 只知入口与日志格式 |
| 该 TU 中标为 `graph-*`（**假设**）的成员 | 如 `0x7BC340`、`0x5679F0`、`0x578100`、`0x56C9A0` 等（大量集中在 `data@0x88DC80`），**需逐个复核是否真属本 TU** |
