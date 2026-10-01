# `..\nesting\algos\bucket_manager.hpp` —— 束搜索的桶 / 节点树 TU

目标轮次：goal round 4。本档记录**已证实**的：TU 归属、词表（47 条）、**API 名与地址**、
数据模型线索与可判定的不变量。**未转写的**函数体在 §6 单独列出，不与结论混写。

## 1. TU 规模与归属

* 规模：**177 个函数 / 174,273 字节**（本轮开始前已引用 26,236 字节 = 15.1%）。
* 归属证据：`direct` —— `0x20FE90`、`0x212D30`、`0x215720` 自身引用
  `'..\nesting\algos\bucket_manager.hpp'`；另有 `0x23B420`（16,413 B）。
* 相关 TU（同批字符串）：`'../utils/evaluated_object.hpp'`、`'..\nesting\algos\algo_helpers.hpp'`。

## 2. 词表（47 条，节选按主题）

| 主题 | 字符串 | 引用者 |
|---|---|---|
| 束 / 桶 规模与统计 | `'Buckets : '`、`'Buckets : empty'`、`'nb_buckets='`、`'Beam width='`、`'Beam try nb : '`、`'Beam bucket comparisons mode='` | `0x7B3510`/`0x7B3D20`/`0x7B4880`、`0x655A30` |
| 树 / 访问 | `'Visited Nodes='`、`'calls='`、`'_beam_tree_'`、`'beam_try_'`、`'beam_slice_'`、`'BestNodes'`、`'InsertAllNext'`、`'Nodes introduced '`、`'degree='` | `0x1C7980`、`0x65DD20`、`0x215720`、`0x23B420`、`0x7B4000`/`0x7B4B60` |
| 等价 / 分桶原语 | `'EquivS'`、`'EquivV'`、`'EquivGV'`、`'EquivCloseV'`、`'AddOrReplaceEquiv'`、`'operator+'`、`'inserted'`、`'can not copy infos'`（`'Can not copy infos'`） | `0x7B30D0`/`0x7B38E0`/`0x7B4440`/`0x7B4FA0`、`0x6C7E80`、`0x235830` |
| 定价 / 评估不变量 | `'static_cast<long long>(pricer.m_prices[p]) >= 0'`、`'eval.m_c == 0'`、**`'eval.m_c >= 0 && eval.m_c <= max_surface * 1.05'`**、`'surface_step >= 0'`、`'ComputeNodeIndex'`、`'Grouper prices : '` | `0x222200`、**`0x81C370`/`0x81C690`/`0x81C9B0`**、`0x20FE90`/`0x212D30`/`0x215720` |
| 结构不变量 | `'first_index < static_cast< int >(m_best.size())'`、`'slices_width.size() > 0'`、`'n1.Valid()'`、`'n2.Valid()'`、`'!infos.state.m_nesting'` | `0x20FE90`/`0x212D30`/`0x215720`、`0x23B420`、`0x235830` |
| 其它 | `' / '`、`'%llu'`、`'none'`、`'global_pre_'`、`'WVSA'`、`'WVSH'`、`'vector::reserve'`、`'vector::_M_default_append'` | 反汇编 | 

## 3. **API 名与地址**（从 `0x215720` 的调用面 + 名字表读出）**[已证实]**

| 地址 | 字节 | 名字 | 角色 |
|---|---:|---|---|
| `0x20FE90` | 10,648 | **`InsertAllNext`** | 把"下一层"全部插入（模板实例化 1） |
| `0x212D30` | 10,728 | **`InsertAllNext`** | 同上（实例化 2，尺寸几乎相同 ⇒ 同一模板的另一组参数） |
| `0x215720` | 11,929 | （hub，8 个调用者） | 桶/树的推进主循环，调用表下半数 |
| `0x22CCA0` | 2,916 | —— | **`'Preparing tree for beam '`**（§7.2 已记录） |
| `0x20C440` | 1,030 | **`IntroduceNestingNodes`** | 引入排样节点 |
| `0x20C2D0` | 363 | **`AddNodeClusterChain`** | 加节点簇链 |
| `0x20C880` | 1,119 | **`CreateNestedChain`** | 造嵌套链 |
| `0x20EE50` | 1,600 | **`check_father`** | 父节点检查 |
| `0x20CCE0` | 761 | **`NestingWindow`** | 嵌套窗口 |
| `0x81C690` | 790 | **`ComputeNodeIndex`** | 节点索引（另有 `0x81C370`、`0x81C9B0` 两处同族） |
| `0x6C7E80` | 847 | **`AddOrReplaceEquiv`** | 等价桶的增/替 |
| `0x23B420` | 16,413 | （`AddOrReplaceEquiv` 的另一实现点，本 TU 最大） | 等价与 `BestNodes` 的合并 |
| `0x1C5970` | 2,278 | **`ROOT_collection`** | 根集合 |
| `0x6548D0` | 4,447 | **`beam_slice_`** | 束切片（带该前缀的统计/跟踪名） |
| `0x655A30` | 1,488 | **`beam_try_`** | 束尝试（`'Beam width='`/`'Beam try nb : '` 的打印点） |
| `0x7B4000` / `0x7B4B60` | 1,073 / —— | **`BestNodes`** | 最优节点集 |
| `0x7B3510`/`0x7B3D20`/`0x7B4880` | 730 … | —— | `'Buckets : '` / `'Buckets : empty'` 的报表 |
| `0x1A89D0` | 277 | **`GetNestableOffset`** | 可取放偏移 |
| `0x16E140` | 3,645 | **`NG3`** | （名字表给出的短名） |
| `0x1C1650` | 12 | —— | 节点打分访问器（§7.2 已记录） |

⇒ 这个 TU 就是**束搜索的树/桶内核**，也正是登记项 `engine.beam_tree`（`NotReversed`）所指的东西；
本轮把它的 **TU 归属、词表与 API 面**补齐。

## 4. 数据模型线索 **[已证实为"不变量文本"，语义为推断]**

* 断言里出现 `pricer.m_prices[p]`、`max_surface`、`eval.m_c`、`surface_step`、`m_best`、`slices_width`
  ⇒ 节点评估对象含 **`m_c`（面积/成本）** 与 **`surface_step`（表面步长）**，定价器结果以 `m_prices` 数组暴露，
  桶按 `slices_width` 切片。
* **可判定常量**：`eval.m_c >= 0 && eval.m_c <= max_surface * 1.05`
  ⇒ 评估值有一个 **`1.05` 的松弛上界**（三处 `ComputeNodeIndex` 断言一致：`0x81C370`/`0x81C690`/`0x81C9B0`）。
  这是本轮唯一可直接入库的数值常量，已落到 `lcns::kEvalSurfaceSlack`。
* `'!infos.state.m_nesting'`、`'Can not copy infos'` ⇒ 有一个 `infos` 状态对象，含 `state.m_nesting`。
* 等价家族 `EquivS / EquivV / EquivGV / EquivCloseV` 是**四个不同的等价判据**（名字即语义：
  S=shape? V=vertex? GV=global vertex? CloseV=close vertex?），**具体判据未读**（推断，未证实）。

## 5. 落到工程

* `engine.hpp` 新增 **`kEvalSurfaceSlack = 1.05`**（RE `0x81C690` 等三处断言文本），
  并在注释里列出该 TU 的 API 面；
* 登记表新增 **`tu.bucket_manager`**（`Structural`：TU/词表/API 面已恢复，函数体未转写），
  并把 `engine.beam_tree` 的注记更新为"API 面已恢复见 `tu.bucket_manager`，**树本身未重建**"。

## 6. **未转写**（本档不声称已完成的部分）

| 范围 | 说明 |
|---|---|
| `0x215720`（11,929 B / 2,221 条指令） | 主推进循环体未逐条转写 |
| `0x20FE90` / `0x212D30`（各约 10.7 KB） | `InsertAllNext` 两个实例化的体未转写 |
| `0x23B420`（16,413 B） | 等价合并体未转写 |
| 四个 `Equiv*` 判据的具体比较 | 未读（本档只给出名字） |
| 桶的哈希/排序规则、`degree` 的含义 | 未读 |
| 该 TU 中标为 `graph-*`（**假设**置信度）的成员 | 例如 `0x21D040`(`'WVSA'`)、`0x237A00`、`0x239E30`，需单独复核是否真属本 TU |
