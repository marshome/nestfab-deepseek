
## TU 档案：`..\structure\stats.cpp`（goal round 95）**[逐函数带证据]**

本 TU 在**未引用领域**里有 **5** 个函数 / **8586** 字节。下表每行是一个函数及它**自己的证据**（字节数、指令数、被调用者数、调用者数、它自带的断言文本）。

| 函数 | 字节 | 指令 | 被调用者 | 调用者 | 自带文本 |
|---|---:|---:|---:|---:|---|
| `0x528020` | 2621 | 500 | 33 | 4 | `biggest`、`UsedSurfaceAux` |
| `0x528d10` | 2493 | 477 | 30 | 5 | `biggest`、`UsedSurfaceAux` |
| `0x52aad0` | 2294 | 498 | 34 | 2 | `sheet` |
| `0x525ef0` | 617 | 132 | 15 | 4 | `nesting.sheet()`、`FillRatio` |
| `0x527870` | 561 | 128 | 14 | 2 | `sheet`、`UsedSurfaceWithStairs` |

**口径**：TU 归属依据是函数**自带的字符串**；每行的其余列是该函数自身的结构事实。

## 调用图传播 TU 标签（goal round 96）**[推论，三类证据分开计数]**

种子：**自带 TU 路径**的可达函数 **151** 个（涉 **36** 个 TU）—— 这是**身份级**证据。

传播结果：**474** 个未引用函数 / **558015** 字节获得了标签，按证据分：

| 证据 | 函数 | 字节 |
|---|---:|---:|
| a | 190 | 105318 |
| b | 246 | 425036 |
| c | 38 | 27661 |

到达最多的 TU：`..\multi\nesting_context.cpp`(54)、`..\verify\equivalent.cpp`(47)、`internal.cpp`(43)、`..\nesting\algos\bucket_manager.hpp`(42)、`..\structure\svg_io.cpp`(26)、`..\structure\automatic_cluster.cpp`(21)

**口径**：这些标签是**推论**（调用图证据），**不等同**于“自带 TU 路径”的身份级证据；每个标签都带它的证据类型，存在 `re/tu_propagation.json`（生成物，不计入引用）。

### `..\verify\equivalent.cpp`（goal round 97）**[逐函数证据]**

本 TU 的**种子**（自带 TU 路径，身份级）**5** 个；经**调用图传播**归入的**未引用**函数 **47** 个 / **74673** 字节。

种子函数携带的可读标识（前 10）：`false && "internal error"`、`EquivalentNestingOrigin`、`false && "internal error mode not yet supported with grain"`、`EquivalentUsedSurfaceEvaluation`、`multiplicity == 1`、`orig_id != ""`、`GetOriginalNesting`、`defect_reduction > 0.0`、`EquivalentSmallerDefects`、`max_price_per_area != 0.0`

出现最多的标识词：`false`(2)、`internal`(2)、`error`(2)、`EquivalentNestingOrigin`(1)、`mode`(1)、`supported`(1)、`with`(1)、`grain`(1)、`EquivalentUsedSurfaceEvaluation`(1)、`multiplicity`(1)

| 函数 | 字节 | 指令 | 归属证据 | 自带文本 |
|---|---:|---:|---|---|
| `0x4c5450` | 12535 | 2759 | b: 57 distinctive callees | `basic_string::_M_construct null not vali`、`from_` |
| `0x535c60` | 9499 | 2159 | b: 14 distinctive callees | 无 |
| `0x54e270` | 4954 | 1150 | b: 7 distinctive callees | 无 |
| `0x56e6b0` | 4827 | 1039 | b: 2 distinctive callees | 无 |
| `0x4cf000` | 4021 | 839 | b: 13 distinctive callees | `basic_string::_M_construct null not vali` |
| `0x52c5e0` | 3177 | 740 | b: 7 distinctive callees | 无 |
| `0x4bd070` | 2816 | 668 | a: all callers agree | 无 |
| `0x54d760` | 2622 | 613 | b: 3 distinctive callees | 无 |
| `0x54ac00` | 2555 | 579 | b: 3 distinctive callees | 无 |
| `0x722a0` | 2528 | 553 | b: 6 distinctive callees | 无 |
| `0x548680` | 2413 | 569 | b: 4 distinctive callees | `vector::_M_range_check: __n (which is %z` |
| `0x5455a0` | 1863 | 392 | b: 4 distinctive callees | 无 |
| `0x83dc0` | 1842 | 375 | b: 4 distinctive callees | 无 |
| `0x55ed00` | 1579 | 381 | b: 2 distinctive callees | 无 |
| `0x1918d0` | 1448 | 349 | b: 3 distinctive callees | 无 |
| `0x54ba40` | 1425 | 306 | b: 2 distinctive callees | 无 |
| `0x4bb9b0` | 1364 | 283 | a: all callers agree | 无 |
| `0x7d36e0` | 1316 | 347 | b: 3 distinctive callees | `vector::_M_default_append` |
| `0x86160` | 1234 | 305 | b: 5 distinctive callees | `__small_mark__`、`__big_mark__` |
| `0x54b600` | 1081 | 257 | b: 2 distinctive callees | 无 |
| `0x51d4c0` | 1044 | 282 | b: 2 distinctive callees | `SHEET NOT FOUND: `、`PART NOT FOUND: ` |
| `0x4d03f0` | 742 | 192 | b: 5 distinctive callees | 无 |
| `0x4ba4d0` | 717 | 148 | b: 5 distinctive callees | 无 |
| `0x8c0570` | 648 | 181 | a: all callers agree | 无 |
| `0x24d6f0` | 607 | 152 | b: 2 distinctive callees | 无 |
| `0xadad0` | 579 | 139 | b: 3 distinctive callees | 无 |
| `0x1f0700` | 494 | 144 | b: 11 distinctive callees | 无 |
| `0x4b99b0` | 460 | 118 | a: all callers agree | 无 |

其余 19 个函数的归属证据在 `re/tu_propagation.json`。

### `..\multi\float_filler.cpp`（goal round 97）**[逐函数证据]**

本 TU 的**种子**（自带 TU 路径，身份级）**2** 个；经**调用图传播**归入的**未引用**函数 **11** 个 / **54813** 字节。

种子函数携带的可读标识（前 10）：`part_number < m_reduced_problem.GetNumberOfParts()`、`index < m_reduced_problem.GetNumberOfParts()`、`nesting.multiplicity() == 1u`、`nested_part.part()`、`RemoveNullPricesParts`、`GetCandidates`、`ReducedPartNumber`、`RawFillNesting`、`part_number < m_reduced_problem.GetNumberOfParts()`、`RawFillNesting`

出现最多的标识词：`m_reduced_problem`(3)、`GetNumberOfParts`(3)、`part_number`(2)、`RawFillNesting`(2)、`index`(1)、`nesting`(1)、`multiplicity`(1)、`nested_part`(1)、`part`(1)、`RemoveNullPricesParts`(1)

| 函数 | 字节 | 指令 | 归属证据 | 自带文本 |
|---|---:|---:|---|---|
| `0x243820` | 15524 | 2949 | b: 9 distinctive callees | `vector::_M_range_check: __n (which is %z`、`pv|` |
| `0xa6950` | 7292 | 1382 | b: 6 distinctive callees | `basic_string::_M_construct null not vali` |
| `0xa85d0` | 7292 | 1382 | b: 6 distinctive callees | `basic_string::_M_construct null not vali` |
| `0xa3e10` | 5521 | 1108 | b: 7 distinctive callees | `basic_string::_M_construct null not vali` |
| `0xa53b0` | 5521 | 1108 | b: 7 distinctive callees | `basic_string::_M_construct null not vali` |
| `0x5c830` | 3923 | 809 | b: 6 distinctive callees | 无 |
| `0x69be80` | 3226 | 668 | b: 5 distinctive callees | `m_base && "call SetActiveNesting first"`、`GetActiveParts` |
| `0x69cb20` | 2556 | 619 | b: 6 distinctive callees | 无 |
| `0x8ed190` | 1999 | 440 | b: 6 distinctive callees | `vector::_M_range_insert` |
| `0xa3900` | 1288 | 278 | b: 6 distinctive callees | 无 |
| `0x7c21c0` | 671 | 152 | b: 4 distinctive callees | 无 |

### `..\multi\nesting_context.cpp`（goal round 97）**[逐函数证据]**

本 TU 的**种子**（自带 TU 路径，身份级）**17** 个；经**调用图传播**归入的**未引用**函数 **54** 个 / **53554** 字节。

种子函数携带的可读标识（前 10）：`y_valid`、`ComputeRealNestingWindow`、`sheet`、`GetTypicalLength`、`index <= quantities.size()`、`NestedQuantities`、`biggest`、`context.GetPackerCache()`、`SetCommonCutParameters`、`!layers.front().empty()`

出现最多的标识词：`size`(11)、`sheet`(7)、`index`(7)、`m_parts`(7)、`nesting`(3)、`biggest`(2)、`empty`(2)、`nesting_part_index`(2)、`GetNestingPart`(2)、`part_and_module`(2)

| 函数 | 字节 | 指令 | 归属证据 | 自带文本 |
|---|---:|---:|---|---|
| `0x7d5790` | 6754 | 1311 | b: 4 distinctive callees | 无 |
| `0x550a80` | 6056 | 1279 | a: all callers agree | 无 |
| `0x1eec00` | 4688 | 813 | b: 3 distinctive callees | `vector::_M_range_check: __n (which is %z` |
| `0x181e80` | 3842 | 926 | c: one labelled caller + shared distinctive callee | 无 |
| `0x54fcb0` | 3523 | 837 | b: 2 distinctive callees | 无 |
| `0x772d40` | 2622 | 552 | b: 4 distinctive callees | 无 |
| `0x559430` | 2126 | 445 | b: 5 distinctive callees | 无 |
| `0x1efe50` | 1829 | 427 | b: 4 distinctive callees | 无 |
| `0x54f5d0` | 1516 | 353 | a: all callers agree | 无 |
| `0x52be50` | 1505 | 342 | b: 2 distinctive callees | 无 |
| `0x531f70` | 1281 | 335 | b: 4 distinctive callees | 无 |
| `0x5271a0` | 1102 | 253 | b: 3 distinctive callees | 无 |
| `0x549650` | 1083 | 248 | a: all callers agree | `basic_string::_M_construct null not vali` |
| `0x3d1e0` | 1071 | 248 | b: 5 distinctive callees | 无 |
| `0x934080` | 980 | 249 | c: one labelled caller + shared distinctive callee | 无 |
| `0x3fd40` | 805 | 192 | a: all callers agree | 无 |
| `0x154690` | 800 | 207 | b: 4 distinctive callees | 无 |
| `0x3fa50` | 752 | 176 | c: one labelled caller + shared distinctive callee | 无 |
| `0x669e60` | 749 | 136 | a: all callers agree | 无 |
| `0x3d920` | 690 | 175 | a: all callers agree | 无 |
| `0x16ef80` | 622 | 154 | c: one labelled caller + shared distinctive callee | 无 |
| `0x8b3d60` | 572 | 149 | a: all callers agree | 无 |
| `0x902440` | 563 | 139 | a: all callers agree | 无 |
| `0x92a6d0` | 519 | 132 | c: one labelled caller + shared distinctive callee | 无 |
| `0x896f30` | 460 | 125 | b: 2 distinctive callees | 无 |
| `0x8b8250` | 458 | 132 | a: all callers agree | 无 |
| `0x8b8650` | 454 | 127 | a: all callers agree | 无 |
| `0x8bf4c0` | 438 | 122 | a: all callers agree | 无 |

其余 26 个函数的归属证据在 `re/tu_propagation.json`。

**口径**：表中“归属证据”列写明是哪一类（a/b/c），这些标签是**推论**；种子函数那部分才是**身份**。
