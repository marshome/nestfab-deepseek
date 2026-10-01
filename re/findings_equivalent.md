# `..\verify\equivalent.cpp` —— 等价问题化简（校验/回算层）

目标轮次：goal round 7。只写**已证实**的；未转写的体在 §6 单列。

## 1. 规模与归属

* **190 个函数 / 163,972 字节**（本轮前已引用 47,023 = **28.7%**，是本 TU 已进入过文档的部分）。
* `direct` 标签持有者（函数自身引用 `'..\verify\equivalent.cpp'`）：
  `0x4B9FA0`、`0x4BA110`、`0x4BB040`、`0x4BC9E0`(1,677 B)、**`0x4BDB70`(11,150 B)**。
* 另有 `vtable:Equivalent` 证据：**`0x75BCC0`（3,569 B）** = `EquivalentEngine` 的实现点。

## 2. API 面 **[已证实]**

| 地址 | 字节 | 名字 | 角色 |
|---|---:|---|---|
| `0x4BDB70` | 11,150 | **`EquivalentProblemRaw`** / **`AddEquivalentPart`** / **`IsTooBigGeometry`** | 本 TU 主体：构造等价问题、加等价零件、判几何过大 |
| `0x4BC9E0` | 1,677 | **`EquivalentSmallerDefects`** | 缺陷缩减（断言 `'defect_reduction > 0.0'`） |
| `0x4BB040` | 2,101 | **`GetOriginalNesting`** | 取原排样（断言 `'multiplicity == 1'`、`'orig_id != ""'`） |
| `0x4B9FA0` | —— | **`EquivalentNestingOrigin`** | 等价排样原点（断言 `'false && "internal error"'`） |
| `0x4BA110` | —— | **`EquivalentUsedSurfaceEvaluation`** | 已用表面的等价评估 |
| `0x75BCC0` | 3,569 | （`vtable:Equivalent`） | `EquivalentEngine` 实现 |
| `0x12F40` | —— | **`CNS_AddDefectFromNestedPart`** | 从已排零件加缺陷（导出层可见的名字） |
| `0x4CC640` | 10,685 | —— | 同族核对（`'(assert_aux1 == assert_aux2)'`、`'point not found'`、`'property not found'`） |

## 3. 断言即**语义事实** **[已证实]**

| 断言文本 | 地址 | 事实 |
|---|---|---|
| `'false && "internal error mode not yet supported with grain"'` | `0x4BA110` | ★ **原库自己就不支持带 grain（材料纹理方向）的这种模式** |
| `'false && "internal error"'` | `0x4B9FA0` | 未支持路径的兜底 |
| `'defect_reduction > 0.0'` | `0x4BC9E0` | 缺陷缩减量**必须为正** |
| `'extra_equivalent_quantity >= 0'` | `0x4BDB70` | 额外等价数量非负 |
| `'max_price_per_area != 0.0'` | `0x4BDB70` | 单价/面积**不得为 0**（作分母） |
| `'modules_geometries.size() == nb_modules'` | `0x4BDB70` | 模块几何数组与模块数等长 |
| `'it != cache.end()'` | `0x4BDB70` | 存在**缓存**（等价问题按 id 缓存） |
| `'!geometries.empty()'` | `0x4BDB70` | 几何非空 |
| `'multiplicity == 1'` | `0x4BB040` | `GetOriginalNesting` **只处理单件** |
| `'orig_id != ""'` | `0x4BB040` | 原 id 必须存在 |
| `'point not found'` / `'property not found'` | `0x4CC640` | 两个查找失败分支 |

其它字符串：`'UWVSH'`(0x6D6100)、`'false'`、`' != '`。

## 4. 与 lcns 的关系（**诚实说明**）

`lcns` 里**没有任何等价问题化简的实现**（本轮已核对：登记表与源码中都无 `equivalent` 相关项）。
因此本 TU 的状态是 **`NotReversed`**（"二进制里有、我们没译出来"），
但它的**结构面**（API、调用关系、上述不变量）本轮已恢复 —— 按工程惯例，这类部分进展写在注记里，
不用 `Structural` 冒充（`Structural` 要求"已有重写实现"，而这里没有）。

⇒ 这同时说明：`EquivalentProblemRaw` 这一层（把问题化简成等价小问题以做校验/回算）
**尚未落到 lcns**，是"导出可达 → 但未实现"的真实缺口，已登记。

## 5. 落到工程与登记表

* 登记表新增 **`tu.equivalent`**（`NotReversed`，注记含全部 API 与不变量），属于**尚未逆向**类；
* 本档本身会把上述函数地址带入文档，因此覆盖率随之上升（这是"看过并写下它是什么"的引用，
  不等于复现 —— 见 `re/REPORT.md` 对覆盖率的口径说明）。

## 6. **未转写 / 待复核**

| 范围 | 说明 |
|---|---|
| `0x4BDB70`（11,150 B） | 等价问题构造主体未转写 |
| `EquivalentSmallerDefects` 的**缩减公式** | 只知"缩减量 > 0"，**公式未读** |
| `EquivalentUsedSurfaceEvaluation` 的评估公式 | 未读 |
| 缓存键与失效规则 | 只知存在缓存（`'it != cache.end()'`） |
| `grain`（纹理）在本库其它 TU 的处理 | 本 TU 明确不支持，**其它处是否有支持未查** |
| `0x4CC640`（10,685 B）与 `0x59E9D0` 等 `graph-*` 成员 | **需复核**是否真属本 TU |
