# `..\structure\border_property.hpp`（含 `internal.cpp` / `cns_no_fit.cpp`）—— 边界属性、皮料分层与无解上下文

目标轮次：goal round 6（第二次）。只写**已证实**的；未转写的体在 §7 单列。

## 1. 规模与归属

* **196 个函数 / 132,394 字节**（本轮前已引用 34,152 = 25.8%）。
* 该 TU 簇含**三个源文件**（由内联路径串确定）：
  | 文件 | 引用点 |
  |---|---|
  | `'../structure/border_property.hpp'` / `'..\structure\border_property.hpp'` | `0x1C980`、`0x1EE50`、`0x7BF0C0`、`0x7BC180` |
  | `'internal.cpp'` | `0x1E900`、`0x1EE50`、`0x22E40` |
  | `'cns_no_fit.cpp'` | `0x668F20` |
* `direct` 标签持有者：**`0x1EE50`（15,305 B，7 个调用者）**、`0x1C980`（2,347 B）；`graph-strict`：`0x22E40`(3,494, `internal.cpp`)、`0x668F20`(2,631, `cns_no_fit.cpp`)。

## 2. API 面 **[已证实]**

| 地址 | 名字（字符串） | 角色 |
|---|---|---|
| `0x1EE50` | **`CreateProblem`** / **`ComputeSheetGeometryRowMode`** / `GetCommonCutProperties` / `GetMultitorchProperties` / `GetLayerLeatherPart` / `GetLayerLeatherSheet` / `GetLayerRestrictedZonePart` / `GetLayerRestrictedZoneSheet` | 本 TU 主体（15.3 KB）：建问题 + 各分层几何 + 属性取出 |
| `0x1C980` | 同上族（`GetLayerLeather*` / `GetLayerRestrictedZone*`） | 分层取件/取板 |
| `0x22E40` | **`ArcToPoints`** / **`CheckAddElements invalid '`** | 圆弧离散成点；元素加入校验（`internal.cpp`） |
| `0x1E900` | **`ComputeNoHoleRings`** | 无孔环计算（`internal.cpp`） |
| `0x7BC180` | **`GetLeatherLayer`** / **`IsLeather(p)`** | 皮料分层与判据 |
| `0x668F20` | **`CNS_NoFitContext`** | 无解/放不下上下文（`cns_no_fit.cpp`） |
| `0x9CC0` | **`DeleteNoFitContext`** | 其析构 |
| `0x7BB430` | `'CNS informations'` | 信息打印 |

## 3. 断言即**精确硬事实** **[已证实]**

| 断言文本 | 地址 | 事实 |
|---|---|---|
| `'quality >= 0 && quality < 100'` | `0x1C980`、`0x1EE50` | **零件侧 quality 值域 = `[0,100)`** |
| `'quality >= 0 && quality < 9'` | `0x1C980`、`0x1EE50`、`0x7BF0C0` | **皮料层侧 quality 值域 = `[0,9)`**（两处同族函数分别断言 ⇒ 同一模型里的**两个不同值域**） |
| `'external_rings.size() == 1u'` | `0x1EE50` | 外环恰有 1 个 |
| `'poly.inners().empty()'` | `0x1E900` | `ComputeNoHoleRings` 要求**无内环** |
| `'!elements.empty()'` | `0x22E40` | 元素非空 |
| `'all_settings.find(order.common_cut_safety_preference) != all_settings.end()'` | `0x1EE50` | **存在名为 `all_settings` 的映射**，以 order 的 `common_cut_safety_preference` 为键 |
| `'boost.find(order.multitorch_cutting_preference) != boost.end()'` | `0x1EE50` | **另有名为 `boost` 的映射**，以 `multitorch_cutting_preference` 为键 |
| `'m_equivalent_problem->GetNumberOfParts() == order->parts.size()'` | `0x668F20` | ★ 无解上下文持有**等价问题**，其零件数须等于订单零件数（**与 round 7 的 `..\verify\equivalent.cpp` 直接相连**） |
| `'m_equivalent_problem->GetNumberOfSheets() == order->sheets.size()'` | `0x668F20` | 同上，板材数一致 |

选项/配置键：`'structure_sheet'`、`'common_cut_safety_preference'`、`'multitorch_cutting_preference'`、`'quality'`。
其它：`'-> '`、`'VSH'`、`'CNS_NoFitContext'`、`'CNS informations'`。

## 4. **皮料（leather）分层模型** **[已证实为 API/值域；语义为推断]**

名字组合起来给出一个比"一个布尔"丰富得多的模型：

* `IsLeather(p)` —— 零件级判据；
* `GetLeatherLayer` —— 皮料**分层**（layer）；
* `GetLayerLeatherPart` / `GetLayerLeatherSheet` —— **按层**取皮料零件/板材；
* `GetLayerRestrictedZonePart` / `GetLayerRestrictedZoneSheet` —— **按层**取受限区；
* 层侧 quality 值域 `[0,9)`，零件侧 `[0,100)`。

**推断**（未证实）：`quality` 是"层内取样/品质档位"，`[0,9)` 是层的可枚举档位，`[0,100)` 是零件的品质百分比。
**未读**：层与零件的绑定规则、受限区的层内几何、`structure_sheet` 的含义。

## 5. 与 lcns 的关系（**记录一处真实分歧**）

lcns 现在只有：
* `Order::leatherMode`（**单个 bool**，来自 JSON `leather_mode`）；
* `Sheet::restrictedZones`（`std::vector<geom::Polygon>`，`nester.cpp` 与 `nfp.cpp` 已遵守）——与 `CNS_SheetAddRestrictedZone` 对应。

而实证显示原库是 **分层 + 每层 quality + 按层取皮料件/受限区** 的模型。
⇒ **lcns 的皮料模型是简化版**：单一开关、无层、无 quality。
这条分歧已写进登记表注记与 `model.hpp` 注释（避免把简化版当成等价）。

## 6. 落到工程

* `model.hpp` 新增两个值域常量并按实证断言：
  `kQualityLevelsPart = 100`（`quality >= 0 && quality < 100`，RE `0x1EE50`）、
  `kQualityLevelsLeatherLayer = 9`（`quality >= 0 && quality < 9`，RE `0x1EE50`/`0x7BF0C0`）；
  并在 `leatherMode` 处注明"原库为分层模型，此处为简化版"；
* `test_recovered.cpp` 断言这两个常量；
* 登记表新增 **`tu.border_property`**（`Structural`）。

## 7. **未转写 / 待复核**

| 范围 | 说明 |
|---|---|
| `0x1EE50`（15,305 B） | 主体未逐条转写 |
| `ComputeNoHoleRings` / `ArcToPoints` 的实现 | 未转写（只读出其断言） |
| 皮料分层的层结构、层↔零件绑定、quality 语义 | **未读**（只知 API 名与两个值域） |
| `all_settings` / `boost` 两个映射的完整键集 | 只知各一个键 |
| `CNS_NoFitContext` 的记录内容与用途 | 只知其持有等价问题 |
| 标为 `graph-*` 的成员（如 `0x676940`、`0x176A60`、`0x86D9E0`） | **需复核**是否真属本 TU |

## 补充（goal round 46）：`ReducedPartNumber` 是**诊断消息里的标签**，不是函数名

读 `0x68AB50`（13,071 B / 2,574 指令）的字符串引用点，形态是**连续三次"三参数格式化"调用**：

```
68D6EA  lea r8,[rip+..] ; 68D6F9 lea rdx,[rip+..] ; 68D700 call 0xAAA60   ; 输出在 [rsp+0x290]
68D714  lea r8,[rip+..] ; 68D723 lea rdx,[rip+..] ; 68D72A call 0xAAA60   ; 输出在 [rsp+0x270]
68D73E  lea r8,[rip+..] ; 68D74D lea rdx,[rip+..] ; 68D754 call 0xAAA60   ; 输出在 [rsp+0x250]
68D759  mov r9,rbx ; mov r8,rsi ; ...                                     ; 三条消息一起交给后续调用
```

⇒ **更正我 round 33 的措辞**：那里我把 `ReducedPartNumber` 说成"映射函数"。实际上它是
**被传进格式化器的字符串/标签**之一 —— 也就是**诊断消息的组成部分**，不是函数名。
`0x68AB50` 本身的形态是：**先构造三条格式化消息，然后在一个 16 字节步长的容器上循环**
（尾部 `add rsi,0x10`、`call 0x979E70`（删除器包装）⇒ 遍历并释放 16 字节记录），
属于**校验/诊断 + 容器拆除**，不是"编号映射"。

**新记录一个可复用的小发现**：**`0xAAA60` 是三参数格式化器**（`rcx`=输出、`rdx`=格式、`r8`=参数），
本库大量诊断消息由它产生 —— 以后凡见 `call 0xAAA60` 即可判定为"**构造一条消息**"，不必跟进。

## 孔的终点 `0x5CD5C0` 与外界边的终点 `0x1BA30` 并排（goal round 50）**[已证实为结构]

* **`0x5cd5c0`（Hole 终点）** 528 B / 125 指令；字符串 `无`；调用 0x5c5260, 0x5c8c50, 0x5cd360, 0x60a620, 0x62f280, 0x910ba0, 0x9984b0；浮点常量 `无`
* **`0x1ba30`（ExternalBoundary 终点）** 198 B / 50 指令；字符串 `无`；调用 0x1b910, 0x62f280, 0x63f2f8, 0x9984b0, 0x998500；浮点常量 `无`

**用途**：这两个是 round 49 里 "孔" 与 "外边界" 两条路径的**终点例程**，比较它们即可确定
两个入口在几何上的真正差别（绕向？包含判定？裁剪？）。**尚未定论**，本条只记录结构事实。

## 两条路径的专有例程：再往下一层（goal round 52）**[已证实为结构]

* **`0x5ed8c0`（外边界专有）** 757 B / 152 指令；调用 0x5c8a10, 0x5ed3d0；浮点常量 `[6.283185, 1.570796, 3.141593, 4.712389, 10.995574, 7.853982]`；字段偏移 18 个
* **`0x5c8a10`（孔专有）** 114 B / 31 指令；调用 无；浮点常量 `无`；字段偏移 4 个

**仍未定论**：这两层之下要么是容器/分配基建（`0x9984B0`/`0x62F280`/`0x910BA0` 一类），
要么要继续下钻。下一轮按调用面判据先归类（基建即停，几何继续）。
