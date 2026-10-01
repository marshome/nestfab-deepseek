# `..\multi\nesting_context.cpp` —— 排样上下文（模型 ↔ 引擎的桥）

目标轮次：goal round 6。只写**已证实**的；未转写的体在 §6 单列。

## 1. 规模与归属

* **135 个函数 / 114,670 字节**（本轮前已引用 17,849 = 15.6%）。
  * 注：TU 地图里本 TU 曾显示 270 函数 / 约 186 KB，那是**调用图传播**的结果；
    按 `direct` 证据（函数自身引用 `'..\multi\nesting_context.cpp'`）只有 **135 个**。
    差额属 §6 的"需复核"项，本档以 `direct` 数为准。
* `direct` 标签持有者：`0x41920`(5,640 B)、`0x69AA40`(4,801 B)、`0x3C9E0`(2,045 B)、
  `0x3DBE0`(2,033 B)、`0x3F070`(1,733 B)、`0x40070`(1,697 B)、`0x3E740`(1,547 B)、`0x3B2F0`、`0x3B5F0`、`0x3BCC0`、`0x3C3F0`、`0x434D0`。

## 2. API 面 **[已证实]**

| 地址 | 名字 | 角色 |
|---|---|---|
| `0x3B2F0` | **`ComputeRealNestingWindow`** | 真实可排样窗口（另有 `'y_valid'` 键） |
| `0x3B5F0` | **`GetTypicalLength`** | 典型长度（`'sheet'` 键） |
| `0x3BCC0` | **`NestedQuantities`** | 已排数量；断言 `'index <= quantities.size()'` |
| `0x3C3F0` | **`SetCommonCutParameters`** | 共边参数（`'biggest'`、`'context.GetPackerCache()'`） |
| `0x3C9E0` | **`ComputeSheetLayers`** | 板材分层；断言 `'!layers.front().empty()'` |
| `0x3DBE0` / `0x3F070` | **`ToNesting`** / **`GetNestingPart`** | 结果 → 嵌套对象；断言 `'nesting_part_index < m_parts.size()'` |
| `0x3E740` | **`SetMultiTorchParameters`** | 多火焰参数（`'packer_cache'`、`'biggest'`） |
| `0x40070` | **`ComputeGroups`** / **`FromNesting`** | 分组与反向构造；断言见 §3 |
| `0x40720` | **`RenestInHoles`** | 在孔洞中重排；`'part gap'` 与 `'Renested '` 计数打印 |
| `0x41920` | **`FillNestingAux`** | 填充辅助；断言 `'nesting.multiplicity() == 1u'` |
| `0x434D0` | **`FillNesting`** | 填充主体 |
| `0x69A720` | **`GetCluster`** | 取簇；断言见 §3（**簇的位置**） |
| `0x69AA40` | **`NestingPartModuleMapping`** | 零件↔模块映射；断言 `'m_parts.size() >= nb_parts'`、`'nb_modules > 0'` |
| `0x696C50` | `'Default'` / `'Implementation'` | 两个字符串常量（配置项） |
| `0x7D3E50` | **`GetStructureModule`** | 取结构模块；断言 `'!IsCluster(p)'`、`'index >= 0 && index < m_parts.size()'` |
| `0x7D4050` | **`IsCluster`** | 判簇 |
| `0x193420` | （12,805 B，最大） | 一致性核对（`'(assert_aux1 == assert_aux2)'`、§3 的两个坐标断言） |
| `0x191E80` | （5,521 B） | 同族核对 |

## 3. 断言即**布局 / 语义事实** **[已证实]**

| 断言文本 | 地址 | 事实 |
|---|---|---|
| `'index >= (m_parts.size() - m_clusters.size()) && index < m_parts.size()'` | `0x69A720` | **簇存放在 `m_parts` 的尾部**：`[0, size - n_clusters)` 是零件，末 `n_clusters` 个是簇 |
| `'(problem.part_gap() == 0.0) && "part gap not supported"'` | `0x69AA40` | **引擎不支持零件间隙**，必须为 0（间隙走别的机制） |
| `'nesting.multiplicity() == 1u'` | `0x41920` | `FillNestingAux` 只处理**单件**嵌套 |
| `'matrix_indices.size() == group_indices.size()'` | `0x40070` | `ComputeGroups` 的两个索引数组等长 |
| `'part_and_module.part()->module(part_and_module.module_index()).authori…'` | `0x40070` | 模块授权检查（与 `SetPartAuthorizations` 同族） |
| `'box.bottom_left().x() > -1e-6 && box.bottom_left().y() > -1e-6'` | `0x193420` | 包围盒左下角以 **`1e-6`** 容差非负 |
| `'Utils::eps_equals(res[0].x(), 0.0) && Utils::eps_equals(res[0].y(), 0.'` | `0x193420` | 结果首点须**落在原点**（`Utils::eps_equals`） |
| `'!box.empty()'`、`'!layers.front().empty()'`、`'!IsCluster(p)'`、`'m_parts.size() >= nb_parts'`、`'nb_modules > 0'` | 多处 | 非空/非簇/规模前置条件 |

选项键（本 TU 内出现）：`'biggest'`、`'packer_cache'`、`'sheet'`、`'y_valid'`、`'_mod'`、`'Default'`、`'Implementation'`。

## 4. 与 lcns 的**互证**（本轮唯一代码级落点）

lcns 里 `Part::gap` 由 `interpartGap` 赋值（`model.cpp:154`）但**源码中无人读取**；
实际间隙效果来自 `engine.cpp:157` 的 `prepareInflatedShapes(..., interpartGap * 0.5)`
（形状外扩半个间隙 ⇒ 相邻零件相距一个间隙）。

这与二进制里那条 `'(problem.part_gap() == 0.0) && "part gap not supported"'` **互相解释**：
**原库把零件间隙排除在 nesting context 之外，间隙只能通过板材/形状外扩走**。
⇒ lcns 的现有做法与之一致，但此前只是"碰巧一致"；现在有实证依据，已写进注释与登记表。
（`Part::gap` 在本工程里是死字段，已在 §6 记为待清理项。）

## 5. 落到工程与登记表

* `model.hpp` 的 `Part::gap` 处加注：**原库断言零件间隙为 0，lcns 的间隙走形状外扩**（附 RVA）；
* `engine.cpp` 的 `interpartGap` 处理处加注同源说明；
* 登记表新增 **`tu.nesting_context`**（`Structural`）。

## 6. **未转写 / 待复核**

| 范围 | 说明 |
|---|---|
| `0x193420`（12,805 B）一致性核对体 | 未转写（只读出其断言文本与两个容差） |
| `ComputeGroups` / `FillNesting` / `ComputeSheetLayers` 的体 | 未转写 |
| 模块授权（`authori…`）的判定逻辑 | 只知断言文本，**未读**（`SetPartAuthorizations` 同族） |
| 簇的构造与 `m_clusters` 的填充点 | 未读 |
| `'biggest'` / `'y_valid'` / `'_mod'` 三个选项键的语义 | 未读 |
| TU 地图中由**传播**归入本 TU 的另外约 135 个函数 | **需逐个复核**（本档只认 `direct` 的 135 个） |
| lcns 中 `Part::gap` 死字段 | 待清理或改为显式断言（保持与实证一致） |
