# 逐 TU 档案（修订版）

> **修订说明（goal round 98）**：本文件曾列出 1,444 个“由调用图传播得到 TU 标签”的函数，而归属审计显示其中**只有 8 个有独立佐证**（该函数自己的文本里出现了所属 TU 种子串中的标识符）。因为**地址出现在文档里就会被计作“已引用”**，继续保留那些行等于**用未验证的推断冲高指标**。因此本文件只保留：① **种子函数**（自带 TU 路径 = 身份级证据）；② **8 个有佐证的传播标签**；③ 每个 TU 的**标识词与计数**（不含未验证函数的地址）。完整假设集保留在 `re/tu_propagation.json`（生成物，**不计入引用**），供后续验证。

## `..\nesting\algos\bucket_manager.hpp`

* 种子（身份级）**10** 个；本文件保留的函数 **10** 个
* 种子标识词：`surface_step`(4)、`max_surface`(4)、`ComputeNodeIndex`(4)、`Grouper`(3)、`prices`(3)、`Nodes`(3)、`introduced`(3)、`first_index`(3)
* 保留的函数：`0x215720`(种子)、`0x212d30`(种子)、`0x20fe90`(种子)、`0x7b4000`(种子)、`0x7b56c0`(种子)、`0x7b4b60`(种子)、`0x81c690`(种子)、`0x81ccd0`(种子)、`0x81c370`(种子)、`0x81c9b0`(种子)

## `..\multi\nesting_context.cpp`

* 种子（身份级）**17** 个；本文件保留的函数 **17** 个
* 种子标识词：`sheet`(7)、`index`(7)、`m_parts`(7)、`nesting`(3)、`biggest`(2)、`empty`(2)、`nesting_part_index`(2)、`GetNestingPart`(2)
* 保留的函数：`0x41920`(种子)、`0x69aa40`(种子)、`0x3c9e0`(种子)、`0x3dbe0`(种子)、`0x3f070`(种子)、`0x40070`(种子)、`0x3e740`(种子)、`0x3c3f0`(种子)、`0x40720`(种子)、`0x3bcc0`(种子)、`0x696c50`(种子)、`0x3b2f0`(种子)、`0x7d3e50`(种子)、`0x69a720`(种子)、`0x434d0`(种子)、`0x3b5f0`(种子)、`0x7d4050`(种子)

## `..\structure\problem.cpp`

* 种子（身份级）**9** 个；本文件保留的函数 **9** 个
* 种子标识词：`number`(3)、`GetPart`(3)、`m_implementation`(3)、`GetNumberOfParts`(2)、`GetSheet`(2)、`false`(2)、`adding`(2)、`sheet`(2)
* 保留的函数：`0x501b60`(种子)、`0x4fdfe0`(种子)、`0x500a90`(种子)、`0x4fc6f0`(种子)、`0x4fca80`(种子)、`0x4fcd80`(种子)、`0x4fcf90`(种子)、`0x4fc940`(种子)、`0x4fc5b0`(种子)

## `internal.cpp`

* 种子（身份级）**4** 个；本文件保留的函数 **5** 个
* 种子标识词：`quality`(4)、`empty`(2)、`all_settings`(2)、`order`(2)、`boost`(2)、`part_maping`(1)、`MakeClusterFromSuggestedPartsGrouping`(1)、`inners`(1)
* 保留的函数：`0x1ee50`(种子)、`0x22e40`(种子)、`0x1e900`(种子)、`0x6859f0`(有佐证)、`0x1c2a0`(种子)

## `..\tiling\packer_cache.cpp`

* 种子（身份级）**6** 个；本文件保留的函数 **6** 个
* 种子标识词：`part_number`(4)、`parameters`(2)、`m_common_cut_tiling_parts`(2)、`GetCommonCutPart`(2)、`m_tiling_parts`(2)、`GetPart`(2)、`basic_evaluators`(1)、`quantity_evaluators`(1)
* 保留的函数：`0x765460`(种子)、`0x769410`(种子)、`0x768b80`(种子)、`0x158810`(种子)、`0x76a010`(种子)、`0x764a80`(种子)

## `..\structure\svg_io.cpp`

* 种子（身份级）**5** 个；本文件保留的函数 **6** 个
* 种子标识词：`sheet`(6)、`DrawDxf`(2)、`black`(2)、`stroke`(2)、`multiplicity`(1)、`nested_parts`(1)、`nesting`(1)、`height`(1)
* 保留的函数：`0x516380`(种子)、`0x513880`(种子)、`0x515090`(有佐证)、`0x510560`(种子)、`0x5100d0`(种子)、`0x510a90`(种子)

## `..\nesting\algos\compact.hpp`

* 种子（身份级）**2** 个；本文件保留的函数 **3** 个
* 种子标识词：`begin`(2)、`computed`(2)、`Trying`(2)、`nestings`(2)、`CompactAux`(2)、`groups`(2)、`Postop`(1)、`eqparts`(1)
* 保留的函数：`0x1da0c0`(种子)、`0x7b8dc0`(有佐证)、`0x677cb0`(种子)

## `..\multi\database.cpp`

* 种子（身份级）**4** 个；本文件保留的函数 **4** 个
* 种子标识词：`nesting`(4)、`sheet`(3)、`multiplicity`(2)、`production_cost`(1)、`Evaluate`(1)、`Unbind`(1)、`GetLimitedNesting`(1)、`dimension_y`(1)
* 保留的函数：`0x6a7800`(种子)、`0x59d30`(种子)、`0x525e0`(种子)、`0x52c70`(种子)

## `..\multi\float_filler.cpp`

* 种子（身份级）**2** 个；本文件保留的函数 **2** 个
* 种子标识词：`m_reduced_problem`(3)、`GetNumberOfParts`(3)、`part_number`(2)、`RawFillNesting`(2)、`index`(1)、`nesting`(1)、`multiplicity`(1)、`nested_part`(1)
* 保留的函数：`0x68f750`(种子)、`0x693520`(种子)

## `..\verify\equivalent.cpp`

* 种子（身份级）**5** 个；本文件保留的函数 **5** 个
* 种子标识词：`false`(2)、`internal`(2)、`error`(2)、`EquivalentNestingOrigin`(1)、`supported`(1)、`grain`(1)、`EquivalentUsedSurfaceEvaluation`(1)、`multiplicity`(1)
* 保留的函数：`0x4bdb70`(种子)、`0x4bb040`(种子)、`0x4bc9e0`(种子)、`0x4ba110`(种子)、`0x4b9fa0`(种子)

## `..\engine\cloud_engine.cpp`

* 种子（身份级）**1** 个；本文件保留的函数 **1** 个
* 种子标识词：`problem`(2)、`solution`(2)、`best_sol`(1)、`final`(1)、`intermediate`(1)、`Launching`(1)、`cloud`(1)、`engine`(1)
* 保留的函数：`0x26a60`(种子)

## `..\multi\nesting_nester.cpp`

* 种子（身份级）**1** 个；本文件保留的函数 **1** 个
* 种子标识词：`parameters`(1)、`nesting_pow_boost`(1)、`sheet`(1)、`deg_steps`(1)、`try_parts_ratio`(1)、`packer_cache`(1)、`biggest`(1)、`strategy`(1)
* 保留的函数：`0x378e0`(种子)

## `..\nesting\structure_interface_private.hpp`

* 种子（身份级）**3** 个；本文件保留的函数 **3** 个
* 种子标识词：`params`(2)、`m_initial_solution`(2)、`Bindable`(2)、`SpecialMaxMonoPart`(1)、`RotateCompact`(1)、`plates`(1)、`m_nestings`(1)、`empty`(1)
* 保留的函数：`0x1f5c20`(种子)、`0x1f1c20`(种子)、`0x1f2d00`(种子)

## `..\nesting\algos\postop.cpp`

* 种子（身份级）**5** 个；本文件保留的函数 **5** 个
* 种子标识词：`m_logs`(2)、`empty`(2)、`m_nb_strips`(1)、`GetZf`(1)、`m_offset_manager`(1)、`Postop`(1)、`Beginning`(1)、`postop`(1)
* 保留的函数：`0x1cb100`(种子)、`0x7c5b70`(种子)、`0x1c9290`(种子)、`0x1c97a0`(种子)、`0x1c8d30`(种子)

## `..\nesting\algos\tree_db.cpp`

* 种子（身份级）**9** 个；本文件保留的函数 **9** 个
* 种子标识词：`NestedNode`(2)、`assert_aux1`(2)、`assert_aux2`(2)、`FieldComputer`(2)、`MaxRightLengthComputer`(2)、`father`(1)、`Contains`(1)、`m_window`(1)
* 保留的函数：`0x1c4350`(种子)、`0x65cc50`(种子)、`0x673c60`(种子)、`0x1c37a0`(种子)、`0x1c1a60`(种子)、`0x1c2110`(种子)、`0x1c1f30`(种子)、`0x1c16e0`(种子)、`0x1c18a0`(种子)

## `..\structure\text_io.cpp`

* 种子（身份级）**4** 个；本文件保留的函数 **9** 个
* 种子标识词：`isArray`(4)、`segments`(2)、`LoadSegment`(1)、`common_cut`(1)、`right`(1)、`left_index`(1)、`right_index`(1)、`valid`(1)
* 保留的函数：`0x600c40`(有佐证)、`0x50ee50`(种子)、`0x603010`(有佐证)、`0x5f6620`(有佐证)、`0x509a40`(种子)、`0x50a550`(种子)、`0x505ce0`(种子)、`0x604020`(有佐证)、`0x602f00`(有佐证)

## `..\structure\stats.cpp`

* 种子（身份级）**8** 个；本文件保留的函数 **8** 个
* 种子标识词：`sheet`(6)、`GetPartTypicalDimension`(3)、`biggest`(2)、`UsedSurfaceAux`(2)、`nesting`(1)、`FillRatio`(1)、`UsedSurfaceWithStairs`(1)
* 保留的函数：`0x528020`(种子)、`0x528d10`(种子)、`0x52aad0`(种子)、`0x520a30`(种子)、`0x520e30`(种子)、`0x521210`(种子)、`0x525ef0`(种子)、`0x527870`(种子)

## `..\multi\rectangle_nester.cpp`

* 种子（身份级）**1** 个；本文件保留的函数 **1** 个
* 种子标识词：`sheet`(2)、`is_rectangular`(1)、`availables`(1)、`nb_parts`(1)、`tool_boxes`(1)、`empty`(1)、`tool_box`(1)、`NestAllPartsAux`(1)
* 保留的函数：`0x6d470`(种子)

## `..\nesting\algos\multinesting_optimizer.cpp`

* 种子（身份级）**5** 个；本文件保留的函数 **5** 个
* 种子标识词：`nestings`(3)、`before_size`(3)、`RecordAndReplaceIfBetter`(3)、`cparts`(2)、`parts`(2)、`m_user_id`(2)、`MakeOriginalPartsNesting`(1)、`nb_slices`(1)
* 保留的函数：`0x1b64e0`(种子)、`0x1aafe0`(种子)、`0x1acf30`(种子)、`0x1ad3a0`(种子)、`0x1ad7e0`(种子)

## `cns_no_fit.cpp`

* 种子（身份级）**7** 个；本文件保留的函数 **7** 个
* 种子标识词：`m_equivalent_problem`(4)、`GetNumberOfParts`(2)、`order`(2)、`GetNumberOfSheets`(2)、`external_number`(2)、`is_rectangular`(1)、`ComputeNoFitSheetMap`(1)、`parts`(1)
* 保留的函数：`0x665f40`(种子)、`0x668f20`(种子)、`0x7270`(种子)、`0x7c7e70`(种子)、`0x74c0`(种子)、`0x91c0`(种子)、`0x8e70`(种子)

## `..\tiling\packer.cpp`

* 种子（身份级）**1** 个；本文件保留的函数 **1** 个
* 种子标识词：`m_problem`(2)、`GetNumberOfParts`(2)、`prices`(1)、`availables`(1)
* 保留的函数：`0x770d10`(种子)

## `cns.cpp`

* 种子（身份级）**12** 个；本文件保留的函数 **12** 个
* 种子标识词：`nesting`(9)、`order`(3)、`nested_parts`(2)、`GetNumberOfCommonCuts`(2)、`part_index`(2)、`GetRow`(1)、`row_number`(1)、`row_intervals`(1)
* 保留的函数：`0xf7c0`(种子)、`0xd870`(种子)、`0xba50`(种子)、`0xd460`(种子)、`0x10f30`(种子)、`0x11640`(种子)、`0xbd90`(种子)、`0x10040`(种子)、`0xb750`(种子)、`0xd710`(种子)、`0xb600`(种子)、`0xcf20`(种子)

## `..\multi\tiling_nester.cpp`

* 种子（身份级）**2** 个；本文件保留的函数 **2** 个
* 种子标识词：`sheet`(2)、`RemoveNestedPartsOverlapingDefects`(1)、`GetPackerParameters`(1)
* 保留的函数：`0x693950`(种子)、`0x462d0`(种子)

## `..\nesting\algos\algo_helpers.hpp`

* 种子（身份级）**4** 个；本文件保留的函数 **4** 个
* 种子标识词：`Valid`(8)、`operator`(4)、`check_father`(3)
* 保留的函数：`0x20e200`(种子)、`0x20ee50`(种子)、`0x20e840`(种子)、`0x9985d0`(种子)

## `..\structure\automatic_cluster.cpp`

* 种子（身份级）**2** 个；本文件保留的函数 **2** 个
* 种子标识词：`empty`(2)、`nesteds`(1)、`ToCluster`(1)、`groups`(1)、`GetBestEraseAndUpdate`(1)
* 保留的函数：`0x5563c0`(种子)、`0x552e30`(种子)

## `..\nesting\algos\algo_parameters.cpp`

* 种子（身份级）**4** 个；本文件保留的函数 **4** 个
* 种子标识词：`parameters`(2)、`m_offset_manager`(2)、`GetNestableOffset`(2)、`geometric_infos`(1)、`AsPricerPart`(1)、`false`(1)、`field`(1)、`NextEffortLevelField`(1)
* 保留的函数：`0x1a66a0`(种子)、`0x1a3db0`(种子)、`0x1a8af0`(种子)、`0x1a89d0`(种子)

## `..\tiling\optimizer.cpp`

* 种子（身份级）**2** 个；本文件保留的函数 **2** 个
* 种子标识词：`GetOrientation`(1)、`minimal_box`(1)、`GetBiModules`(1)、`empty`(1)、`pattern`(1)、`NewLocalAngleOptimize`(1)
* 保留的函数：`0x4e9a10`(种子)、`0x7ee7b0`(种子)

## `..\multi\marker.cpp`

* 种子（身份级）**2** 个；本文件保留的函数 **2** 个
* 种子标识词：`FindAllWindows`(1)、`problem`(1)、`mark_properties`(1)、`FindAllMarks`(1)
* 保留的函数：`0x8b280`(种子)、`0x8ba70`(种子)

## `..\multi\supervisor.cpp`

* 种子（身份级）**4** 个；本文件保留的函数 **4** 个
* 种子标识词：`m_supervisor`(3)、`ProbeCancel`(3)、`Compact`(2)、`nesting`(1)、`Bindable`(1)、`m_problem`(1)、`cancelled`(1)
* 保留的函数：`0x68a6e0`(种子)、`0x7d2610`(种子)、`0x7d29f0`(种子)、`0x30030`(种子)

## `..\nesting\algos\sheet_optimizer.cpp`

* 种子（身份级）**3** 个；本文件保留的函数 **3** 个
* 种子标识词：`nesting`(2)、`m_matrixes`(2)、`m_father`(1)、`AddNodeClusterChain`(1)、`nesteds`(1)、`IntroduceNestingNodes`(1)、`nested_extractor`(1)、`CreateNestedChain`(1)
* 保留的函数：`0x20c880`(种子)、`0x20c440`(种子)、`0x20c2d0`(种子)

## `..\engine\engine.cpp`

* 种子（身份级）**2** 个；本文件保留的函数 **2** 个
* 种子标识词：`original`(1)、`empty`(1)、`NewNestingFound`(1)、`m_state`(1)、`m_problem`(1)、`m_observer`(1)、`CompositeObserver`(1)
* 保留的函数：`0x8d4500`(种子)、`0x75ddf0`(种子)

## `..\structure\multitorch_eval.cpp`

* 种子（身份级）**1** 个；本文件保留的函数 **1** 个
* 种子标识词：`torch_configs`(1)、`empty`(1)、`ComputeBestConfigSequence`(1)
* 保留的函数：`0x53cc30`(种子)

## `..\nesting\algos\tree_db.hpp`

* 种子（身份级）**1** 个；本文件保留的函数 **1** 个
* 种子标识词：`last_value`(1)、`IsCompatible`(1)、`offval`(1)、`CheckOffset`(1)
* 保留的函数：`0x1c2640`(种子)

## `..\nesting\ios\log_ios.cpp`

* 种子（身份级）**1** 个；本文件保留的函数 **1** 个
* 种子标识词：`m_all_tries`(1)、`empty`(1)、`LogNesting`(1)
* 保留的函数：`0x1fb810`(种子)

## `..\exact\relinker_internal.cpp`

* 种子（身份级）**1** 个；本文件保留的函数 **1** 个
* 种子标识词：`father`(2)、`m_father`(2)、`Exact`(1)、`strange`(1)、`invalid`(1)、`geometry`(1)、`MakeInclusion`(1)
* 保留的函数：`0x5b3bf0`(种子)

## `..\structure\border_property.hpp`

* 种子（身份级）**1** 个；本文件保留的函数 **1** 个
* 种子标识词：`IsLeather`(1)、`GetLeatherLayer`(1)
* 保留的函数：`0x7bc180`(种子)
# 逐 TU 档案：以“引用了该 TU 的特异字符串”为证据（goal round 98）

**证据形式**：每行给出该函数**实际引用的那个字符串**（及它被多少个函数引用，越少越有辨识度）。这与 round 97 失败的区别是：**证据随每个函数一起走**，而不是一个传播出来的标签。

**证据强度声明**：“引用了某 TU 的断言字符串”说明该函数**参与该 TU 的代码路径**，是**强推论**（但仍不是“身份级”：不排除跨 TU 使用同一断言）。

## `..\nesting\algos\compact.hpp`—6 个函数 / 16327 字节

| 函数 | 字节 | 指令 | 引用的字符串 | 该串被引用次数 |
|---|---:|---:|---|---:|
| `0x1b0f70` | 9274 | 1813 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 12 |
| `0x1b5a70` | 2660 | 548 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 12 |
| `0x1abb20` | 2149 | 420 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 12 |
| `0x1ae990` | 1136 | 236 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 12 |
| `0x6d5b30` | 583 | 158 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 10 |
| `0x6d5d80` | 525 | 145 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 10 |

## `..\structure\multitorch_eval.cpp`—4 个函数 / 12558 字节

| 函数 | 字节 | 指令 | 引用的字符串 | 该串被引用次数 |
|---|---:|---:|---|---:|
| `0x53f910` | 11110 | 2221 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 11 |
| `0x53a680` | 669 | 160 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 11 |
| `0x53a290` | 441 | 112 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 11 |
| `0x53a520` | 338 | 96 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 11 |

## `..\nesting\algos\tree_db.cpp`—10 个函数 / 4363 字节

| 函数 | 字节 | 指令 | 引用的字符串 | 该串被引用次数 |
|---|---:|---:|---|---:|
| `0x7ba1d0` | 590 | 154 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 12 |
| `0x7ba9a0` | 487 | 133 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 12 |
| `0x7b9690` | 464 | 130 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 12 |
| `0x7ba420` | 464 | 134 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 12 |
| `0x7bad20` | 423 | 121 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 12 |
| `0x81d260` | 423 | 121 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 12 |
| `0x7bab90` | 400 | 113 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 12 |
| `0x7ba050` | 375 | 109 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 12 |
| `0x7ba6b0` | 373 | 109 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 12 |
| `0x7ba830` | 364 | 107 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 12 |

## `..\structure\automatic_cluster.cpp`—1 个函数 / 3833 字节

| 函数 | 字节 | 指令 | 引用的字符串 | 该串被引用次数 |
|---|---:|---:|---|---:|
| `0x5584b0` | 3833 | 756 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 2 |

## `..\structure\problem.cpp`—3 个函数 / 2719 字节

| 函数 | 字节 | 指令 | 引用的字符串 | 该串被引用次数 |
|---|---:|---:|---|---:|
| `0x92af20` | 1056 | 264 | `basic_string::_M_construct null not valid` | 9 |
| `0x8ec3b0` | 1021 | 260 | `basic_string::_M_construct null not valid` | 9 |
| `0x4fd900` | 642 | 162 | `basic_string::_M_construct null not valid` | 9 |

## `..\multi\nesting_nester.cpp`—1 个函数 / 2240 字节

| 函数 | 字节 | 指令 | 引用的字符串 | 该串被引用次数 |
|---|---:|---:|---|---:|
| `0x33100` | 2240 | 459 | `basic_string::append` | 4 |

## `..\engine\cloud_engine.cpp`—1 个函数 / 437 字节

| 函数 | 字节 | 指令 | 引用的字符串 | 该串被引用次数 |
|---|---:|---:|---|---:|
| `0x268a0` | 437 | 116 | `basic_string::_M_construct null not valid` | 8 |

## `..\multi\nesting_context.cpp`—1 个函数 / 365 字节

| 函数 | 字节 | 指令 | 引用的字符串 | 该串被引用次数 |
|---|---:|---:|---|---:|
| `0x7d7a90` | 365 | 107 | `vector::_M_range_check: __n (which is %zu) >= this->size() (` | 3 |

## `..\structure\text_io.cpp`—1 个函数 / 107 字节

| 函数 | 字节 | 指令 | 引用的字符串 | 该串被引用次数 |
|---|---:|---:|---|---:|
| `0x5053c0` | 107 | 33 | `extra_infos` | 5 |

# 两条**证据随行**的归属通道（goal round 99）

* **A**：该函数引用了某 TU 的**特异字符串**（阈值 ≤25 个引用者，每行给出该串与它的被引用次数，可单条复核）；
* **B**：该函数的**每一个调用者都是种子**（种子自带 TU 路径 = 身份级）且它们指向同一 TU（每行列出调用者）。**不做链式传播**，所以不会漂移。

**两条都是推论（A 强推论 / B 较强），不等同于身份级证据。**

## `..\nesting\algos\bucket_manager.hpp`—31 个函数 / 17946 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x236bc0` | 3646 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x234c60` | 3014 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x224aa0` | 2082 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x21faf0` | 916 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x7b53e0` | 730 | B | callers: 0x20fe90 |
| `0x8d0840` | 581 | B | callers: 0x7b4000 |
| `0x8d0d30` | 581 | B | callers: 0x7b4b60 |
| `0x8d1220` | 581 | B | callers: 0x7b56c0 |
| `0x1c55f0` | 565 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x8d0a90` | 565 | B | callers: 0x7b4000 |
| `0x8d0f80` | 565 | B | callers: 0x7b4b60 |
| `0x8d1470` | 565 | B | callers: 0x7b56c0 |
| `0x6d5f90` | 364 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x900820` | 342 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x1c3f30` | 324 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x900c00` | 309 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x674360` | 287 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x653550` | 276 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x236ad0` | 230 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x656110` | 202 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x20cfe0` | 184 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x20bec0` | 172 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x6742b0` | 169 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x6ddec0` | 107 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x20c0c0` | 106 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x6de0f0` | 106 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x8d0cd0` | 89 | B | callers: 0x215720, 0x7b4000 |
| `0x8d11c0` | 89 | B | callers: 0x212d30, 0x7b4b60 |
| `0x8d16b0` | 89 | B | callers: 0x20fe90, 0x7b56c0 |
| `0x8fe5e0` | 88 | B | callers: 0x20fe90, 0x212d30, 0x215720 |
| `0x1c12b0` | 22 | B | callers: 0x20fe90, 0x212d30, 0x215720 |

## `..\multi\nesting_context.cpp`—24 个函数 / 15562 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x550a80` | 6056 | B | callers: 0x3c9e0, 0x69aa40 |
| `0x54f5d0` | 1516 | B | callers: 0x3c9e0 |
| `0x549650` | 1083 | B | callers: 0x40070 |
| `0x3fd40` | 805 | B | callers: 0x40070 |
| `0x669e60` | 749 | B | callers: 0x3e740 |
| `0x3d920` | 690 | B | callers: 0x40070 |
| `0x8b3d60` | 572 | B | callers: 0x3f070 |
| `0x902440` | 563 | B | callers: 0x69aa40 |
| `0x8b8250` | 458 | B | callers: 0x69aa40 |
| `0x8b8650` | 454 | B | callers: 0x69aa40 |
| `0x8bf4c0` | 438 | B | callers: 0x3c9e0 |
| `0x8f5fd0` | 418 | B | callers: 0x69aa40 |
| `0x17b740` | 352 | B | callers: 0x69aa40 |
| `0x16f1f0` | 347 | B | callers: 0x40070 |
| `0x8cee00` | 256 | B | callers: 0x69aa40 |
| `0x931ff0` | 169 | B | callers: 0x3f070 |
| `0x92efd0` | 129 | B | callers: 0x40720, 0x41920 |
| `0x52c4c0` | 118 | B | callers: 0x3b5f0 |
| `0x669df0` | 102 | B | callers: 0x3c3f0, 0x3e740, 0x41920 |
| `0x3c390` | 96 | B | callers: 0x3c3f0, 0x3e740 |
| `0x3b590` | 84 | B | callers: 0x69aa40 |
| `0x4f0c60` | 56 | B | callers: 0x3e740 |
| `0x54e1c0` | 26 | B | callers: 0x69aa40 |
| `0x54e1a0` | 25 | B | callers: 0x69aa40 |

## `..\tiling\packer.cpp`—6 个函数 / 10204 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x154df0` | 3045 | B | callers: 0x770d10 |
| `0x76fa20` | 3013 | B | callers: 0x770d10 |
| `0x15f100` | 2837 | B | callers: 0x770d10 |
| `0x15ddc0` | 956 | B | callers: 0x770d10 |
| `0x544790` | 195 | B | callers: 0x770d10 |
| `0x15ea80` | 158 | B | callers: 0x770d10 |

## `internal.cpp`—23 个函数 / 7845 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x93e2c0` | 1252 | B | callers: 0x1ee50 |
| `0x8c1920` | 754 | B | callers: 0x22e40 |
| `0x1ec80` | 457 | B | callers: 0x1ee50 |
| `0x923110` | 408 | B | callers: 0x1ee50 |
| `0x923480` | 408 | B | callers: 0x1ee50 |
| `0x9237f0` | 408 | B | callers: 0x1ee50 |
| `0x9314f0` | 408 | B | callers: 0x1ee50 |
| `0x932b80` | 408 | B | callers: 0x1ee50 |
| `0x64f850` | 350 | B | callers: 0x22e40 |
| `0x677af0` | 350 | B | callers: 0x1ee50 |
| `0x8c20a0` | 330 | B | callers: 0x22e40 |
| `0x897650` | 292 | B | callers: 0x22e40 |
| `0x922ff0` | 288 | B | callers: 0x1ee50 |
| `0x923360` | 288 | B | callers: 0x1ee50 |
| `0x9236d0` | 288 | B | callers: 0x1ee50 |
| `0x9313d0` | 288 | B | callers: 0x1ee50 |
| `0x932a60` | 288 | B | callers: 0x1ee50 |
| `0x1b840` | 203 | B | callers: 0x22e40 |
| `0x1bb10` | 150 | B | callers: 0x1ee50 |
| `0x1e0d0` | 104 | B | callers: 0x1ee50 |
| `0x4f7a50` | 66 | B | callers: 0x1ee50 |
| `0x899690` | 44 | B | callers: 0x1ee50 |
| `0x549ab0` | 13 | B | callers: 0x1ee50 |

## `..\verify\equivalent.cpp`—16 个函数 / 7710 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x4bd070` | 2816 | B | callers: 0x4bdb70 |
| `0x4bb9b0` | 1364 | B | callers: 0x4bdb70 |
| `0x8c0570` | 648 | B | callers: 0x4bdb70 |
| `0x4b99b0` | 460 | B | callers: 0x4bdb70 |
| `0x4f8a80` | 449 | B | callers: 0x4bdb70 |
| `0x4fd130` | 429 | B | callers: 0x4bdb70 |
| `0x874270` | 291 | B | callers: 0x4bdb70 |
| `0x533ea0` | 255 | B | callers: 0x4bdb70 |
| `0x4fcc90` | 239 | B | callers: 0x4bdb70 |
| `0x8f4e40` | 220 | B | callers: 0x4bdb70 |
| `0x4ba3e0` | 136 | B | callers: 0x4bdb70 |
| `0x4b9cf0` | 128 | B | callers: 0x4bc9e0 |
| `0x4bad90` | 114 | B | callers: 0x4bc9e0 |
| `0x8743a0` | 75 | B | callers: 0x4bdb70 |
| `0x679f40` | 43 | B | callers: 0x4bdb70 |
| `0x67d680` | 43 | B | callers: 0x4bdb70 |

## `..\nesting\algos\postop.cpp`—5 个函数 / 5813 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x8ffb20` | 3207 | B | callers: 0x1c9290, 0x1c97a0 |
| `0x1c8960` | 973 | B | callers: 0x1c8d30 |
| `0x65e530` | 673 | B | callers: 0x7c5b70 |
| `0x8ae730` | 630 | B | callers: 0x1cb100 |
| `0x1c8ec0` | 330 | B | callers: 0x1cb100 |

## `..\structure\problem.cpp`—5 个函数 / 4082 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x7bfea0` | 3031 | B | callers: 0x500a90 |
| `0x89e2b0` | 541 | B | callers: 0x500a90 |
| `0x8ff520` | 253 | B | callers: 0x500a90 |
| `0x8ff620` | 253 | B | callers: 0x4fdfe0 |
| `0x4f8c70` | 4 | B | callers: 0x4fdfe0 |

## `..\nesting\algos\compact.hpp`—6 个函数 / 3818 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x1dea50` | 1355 | B | callers: 0x1da0c0 |
| `0x1d7160` | 1348 | B | callers: 0x1da0c0 |
| `0x1de600` | 581 | B | callers: 0x1da0c0 |
| `0x1dd950` | 269 | B | callers: 0x1da0c0 |
| `0x1d70a0` | 177 | B | callers: 0x1da0c0 |
| `0x8f69f0` | 88 | B | callers: 0x1da0c0 |

## `..\structure\multitorch_eval.cpp`—3 个函数 / 3733 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x53c2c0` | 2414 | B | callers: 0x53cc30 |
| `0x8e9840` | 1138 | B | callers: 0x53cc30 |
| `0x538fd0` | 181 | B | callers: 0x53cc30 |

## `..\structure\svg_io.cpp`—7 个函数 / 3705 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x52b3d0` | 2198 | B | callers: 0x516380 |
| `0x516050` | 812 | B | callers: 0x516380 |
| `0x542f30` | 236 | B | callers: 0x516380 |
| `0x7c4ae0` | 168 | B | callers: 0x516380 |
| `0x520770` | 159 | B | callers: 0x516380 |
| `0x5d9350` | 105 | B | callers: 0x516380 |
| `0x5da140` | 27 | B | callers: 0x516380 |

## `..\multi\tiling_nester.cpp`—3 个函数 / 3301 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x6bbf20` | 1561 | B | callers: 0x462d0 |
| `0x8721a0` | 1423 | B | callers: 0x462d0 |
| `0x46190` | 317 | B | callers: 0x462d0 |

## `..\nesting\algos\tree_db.cpp`—12 个函数 / 3229 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x8f74a0` | 913 | B | callers: 0x65cc50 |
| `0x972ec0` | 701 | B | callers: 0x65cc50 |
| `0x96b260` | 327 | B | callers: 0x65cc50 |
| `0x65dbf0` | 304 | B | callers: 0x1c4350 |
| `0x98d960` | 266 | B | callers: 0x65cc50 |
| `0x1c3420` | 239 | B | callers: 0x1c37a0 |
| `0x7ba5f0` | 185 | B | callers: 0x65cc50 |
| `0x8fcf20` | 88 | B | callers: 0x1c4350 |
| `0x8febe0` | 88 | B | callers: 0x1c4350, 0x673c60 |
| `0x8f7ce0` | 57 | B | callers: 0x1c4350 |
| `0x1c0f10` | 50 | B | callers: 0x65cc50 |
| `0x16c260` | 11 | B | callers: 0x1c4350 |

## `..\nesting\algos\multinesting_optimizer.cpp`—4 个函数 / 2672 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x8b9620` | 1768 | B | callers: 0x1acf30, 0x1ad3a0, 0x1ad7e0 |
| `0x931e50` | 408 | B | callers: 0x1aafe0 |
| `0x1aaa20` | 376 | B | callers: 0x1aafe0 |
| `0x8ba380` | 120 | B | callers: 0x1acf30, 0x1ad3a0, 0x1ad7e0 |

## `..\structure\automatic_cluster.cpp`—6 个函数 / 2244 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x8f5530` | 776 | B | callers: 0x5563c0 |
| `0x8e77c0` | 588 | B | callers: 0x5563c0 |
| `0x98ef50` | 344 | B | callers: 0x5563c0 |
| `0x8f5840` | 321 | B | callers: 0x5563c0 |
| `0x8f5990` | 155 | B | callers: 0x5563c0 |
| `0x552470` | 60 | B | callers: 0x552e30 |

## `..\multi\marker.cpp`—3 个函数 / 2012 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x871b20` | 1649 | B | callers: 0x8ba70 |
| `0x8cf220` | 358 | B | callers: 0x8b280 |
| `0x51d0e0` | 5 | B | callers: 0x8ba70 |

## `..\multi\database.cpp`—5 个函数 / 1552 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x597a0` | 448 | B | callers: 0x6a7800 |
| `0x544600` | 362 | B | callers: 0x525e0 |
| `0x523d0` | 324 | B | callers: 0x6a7800 |
| `0x56ab0` | 237 | B | callers: 0x6a7800 |
| `0x52520` | 181 | B | callers: 0x525e0 |

## `..\structure\stats.cpp`—1 个函数 / 1072 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x527bf0` | 1072 | B | callers: 0x528020, 0x528d10 |

## `..\tiling\optimizer.cpp`—2 个函数 / 1060 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x76db50` | 879 | B | callers: 0x7ee7b0 |
| `0x4e8870` | 181 | B | callers: 0x4e9a10, 0x7ee7b0 |

## `cns_no_fit.cpp`—2 个函数 / 1030 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x64c480` | 547 | B | callers: 0x91c0 |
| `0x64c290` | 483 | B | callers: 0x8e70 |

## `..\structure\text_io.cpp`—3 个函数 / 970 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x8e1bd0` | 501 | B | callers: 0x509a40 |
| `0x8ea5e0` | 305 | B | callers: 0x50a550 |
| `0x51f6a0` | 164 | B | callers: 0x50ee50 |

## `cns.cpp`—3 个函数 / 865 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x8f9dc0` | 322 | B | callers: 0x11640 |
| `0x8f90f0` | 292 | B | callers: 0x10f30 |
| `0x64b1c0` | 251 | B | callers: 0x10040 |

## `..\nesting\ios\log_ios.cpp`—1 个函数 / 751 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x9098e0` | 751 | B | callers: 0x1fb810 |

## `..\tiling\packer_cache.cpp`—5 个函数 / 674 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x768a60` | 275 | B | callers: 0x768b80 |
| `0x56f990` | 260 | B | callers: 0x768b80 |
| `0x4ba470` | 94 | B | callers: 0x769410 |
| `0x4e83e0` | 40 | B | callers: 0x158810 |
| `0x56a280` | 5 | B | callers: 0x768b80 |

## `..\nesting\algos\algo_parameters.cpp`—2 个函数 / 597 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x1a8780` | 592 | B | callers: 0x1a89d0, 0x1a8af0 |
| `0x17b9c0` | 5 | B | callers: 0x1a3db0 |

## `..\nesting\algos\tree_db.hpp`—2 个函数 / 452 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x8f7b80` | 338 | B | callers: 0x1c2640 |
| `0x1c1660` | 114 | B | callers: 0x1c2640 |

## `..\exact\relinker_internal.cpp`—1 个函数 / 253 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x5b3500` | 253 | B | callers: 0x5b3bf0 |

## `..\engine\cloud_engine.cpp`—2 个函数 / 237 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x8642d0` | 153 | B | callers: 0x26a60 |
| `0x999af0` | 84 | B | callers: 0x26a60 |

## `..\nesting\algos\algo_helpers.hpp`—1 个函数 / 50 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x20bf80` | 50 | B | callers: 0x20e840 |

## `..\multi\supervisor.cpp`—1 个函数 / 29 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x53a100` | 29 | B | callers: 0x68a6e0 |

## `..\nesting\structure_interface_private.hpp`—1 个函数 / 4 字节

| 函数 | 字节 | 通道 | 证据 |
|---|---:|---|---|
| `0x178560` | 4 | B | callers: 0x1f1c20 |

# channel B：深度 1 与深度 2（goal round 101）**[每行写出完整依据]**

**可入档规则**：一行只有在**它的全部依据都写在该行里、且从身份级证据出发不超过两跳**时才进入计入引用的档案；**深度 ≥ 3 永不入档**（这正是 round 97 犯的错）。

* 深度 1：**0** 个函数 / 0 字节（调用者**全是种子**）
* 深度 2：**0** 个函数 / 0 字节（调用者为种子或深度 1），其中**有独立标识符佐证者：0（0.0%）**

# 放宽调用者规则的归档（goal round 103）**[每行列出种子调用者]**

**规则**：至少**两个种子**（自带 TU 路径 = 身份级）调用它且指向同一 TU，且**没有**任何种子调用者属于别的 TU。每行给出那几个种子调用者，可逐行复核。

**证据强度**：比 channel B 略弱（它忽略了无标签的调用者），但依然**从身份级证据出发一跳**，且每行自带依据。

## `..\nesting\algos\bucket_manager.hpp`—18 个函数 / 6994 字节

| 函数 | 字节 | 种子调用者 |
|---|---:|---|
| `0x22da70` | 1373 | `0x20fe90`, `0x212d30`, `0x215720` |
| `0x2393f0` | 1275 | `0x20fe90`, `0x212d30`, `0x215720` |
| `0x180100` | 962 | `0x20fe90`, `0x212d30`, `0x215720` |
| `0x224560` | 880 | `0x20fe90`, `0x212d30`, `0x215720` |
| `0x16c4c0` | 544 | `0x20fe90`, `0x212d30`, `0x215720` |
| `0x1c0bf0` | 425 | `0x20fe90`, `0x212d30`, `0x215720` |
| `0x900ae0` | 279 | `0x20fe90`, `0x212d30`, `0x215720`, `0x7b4000` |
| `0x1c1d40` | 180 | `0x20fe90`, `0x212d30`, `0x215720` |
| `0x8f7d20` | 172 | `0x20fe90`, `0x212d30`, `0x215720` |
| `0x1be470` | 141 | `0x20fe90`, `0x212d30`, `0x215720` |
| `0x7602b0` | 123 | `0x20fe90`, `0x212d30`, `0x215720` |
| `0x6dd780` | 118 | `0x20fe90`, `0x212d30`, `0x215720` |
| `0x22da00` | 112 | `0x20fe90`, `0x212d30`, `0x215720` |
| `0x6dde50` | 111 | `0x20fe90`, `0x212d30`, `0x215720` |
| `0x6de010` | 108 | `0x20fe90`, `0x212d30`, `0x215720` |
| `0x900d40` | 106 | `0x20fe90`, `0x212d30`, `0x215720`, `0x7b4000` |
| `0x1a6650` | 66 | `0x20fe90`, `0x212d30`, `0x215720` |
| `0x22d9e0` | 19 | `0x20fe90`, `0x212d30`, `0x215720` |

## `..\structure\text_io.cpp`—10 个函数 / 2885 字节

| 函数 | 字节 | 种子调用者 |
|---|---:|---|
| `0x5feb70` | 950 | `0x509a40`, `0x50a550`, `0x50ee50` |
| `0x5ffad0` | 852 | `0x509a40`, `0x50a550`, `0x50ee50` |
| `0x5fe060` | 409 | `0x509a40`, `0x50a550`, `0x50ee50` |
| `0x5fc960` | 273 | `0x509a40`, `0x50a550`, `0x50ee50` |
| `0x5fcb90` | 178 | `0x505ce0`, `0x50a550`, `0x50ee50` |
| `0x5fcea0` | 80 | `0x505ce0`, `0x509a40`, `0x50a550`, `0x50ee50` |
| `0x5050a0` | 60 | `0x505ce0`, `0x509a40`, `0x50a550` |
| `0x505280` | 57 | `0x509a40`, `0x50ee50` |
| `0x5fd640` | 18 | `0x505ce0`, `0x509a40`, `0x50a550`, `0x50ee50` |
| `0x600680` | 8 | `0x509a40`, `0x50a550`, `0x50ee50` |

## `internal.cpp`—7 个函数 / 2257 字节

| 函数 | 字节 | 种子调用者 |
|---|---:|---|
| `0x1e480` | 1007 | `0x1ee50`, `0x22e40` |
| `0x8c1e30` | 609 | `0x1e900`, `0x22e40` |
| `0x8c3730` | 178 | `0x1ee50`, `0x22e40` |
| `0x1b070` | 177 | `0x1e900`, `0x1ee50` |
| `0x1e870` | 138 | `0x1e900`, `0x1ee50` |
| `0x8c2320` | 88 | `0x1e900`, `0x1ee50`, `0x22e40` |
| `0x1b130` | 60 | `0x1c2a0`, `0x1ee50`, `0x22e40` |

## `..\structure\stats.cpp`—8 个函数 / 2257 字节

| 函数 | 字节 | 种子调用者 |
|---|---:|---|
| `0x5253e0` | 775 | `0x525ef0`, `0x527870`, `0x528020`, `0x528d10` |
| `0x5275f0` | 636 | `0x527870`, `0x528020`, `0x528d10` |
| `0x51c260` | 496 | `0x528020`, `0x528d10` |
| `0x520970` | 181 | `0x520a30`, `0x520e30`, `0x521210`, `0x525ef0` |
| `0x5eaff0` | 150 | `0x520a30`, `0x520e30`, `0x521210` |
| `0x51c250` | 9 | `0x528020`, `0x528d10` |
| `0x52f8f0` | 6 | `0x527870`, `0x528020`, `0x528d10` |
| `0x4fc1d0` | 4 | `0x520a30`, `0x520e30`, `0x521210` |

## `..\multi\nesting_context.cpp`—5 个函数 / 1650 字节

| 函数 | 字节 | 种子调用者 |
|---|---:|---|
| `0x7c1dc0` | 1012 | `0x40720`, `0x41920` |
| `0x9320a0` | 281 | `0x3f070`, `0x41920` |
| `0x3b1f0` | 177 | `0x3bcc0`, `0x3f070`, `0x41920` |
| `0x8ea1b0` | 120 | `0x3c9e0`, `0x69aa40` |
| `0x3b2b0` | 60 | `0x3b2f0`, `0x3b5f0`, `0x3bcc0`, `0x3c3f0` |

## `..\nesting\algos\multinesting_optimizer.cpp`—1 个函数 / 764 字节

| 函数 | 字节 | 种子调用者 |
|---|---:|---|
| `0x65b820` | 764 | `0x1acf30`, `0x1ad3a0`, `0x1ad7e0` |

## `..\verify\equivalent.cpp`—3 个函数 / 719 字节

| 函数 | 字节 | 种子调用者 |
|---|---:|---|
| `0x5d1360` | 531 | `0x4bc9e0`, `0x4bdb70` |
| `0x4b9d70` | 128 | `0x4bc9e0`, `0x4bdb70` |
| `0x4b9970` | 60 | `0x4b9fa0`, `0x4ba110`, `0x4bb040`, `0x4bc9e0` |

## `..\nesting\algos\compact.hpp`—5 个函数 / 468 字节

| 函数 | 字节 | 种子调用者 |
|---|---:|---|
| `0x25af80` | 185 | `0x1da0c0`, `0x677cb0` |
| `0x261e60` | 175 | `0x1da0c0`, `0x677cb0` |
| `0x259df0` | 53 | `0x1da0c0`, `0x677cb0` |
| `0x25c9e0` | 30 | `0x1da0c0`, `0x677cb0` |
| `0x2610c0` | 25 | `0x1da0c0`, `0x677cb0` |

## `..\nesting\algos\postop.cpp`—2 个函数 / 358 字节

| 函数 | 字节 | 种子调用者 |
|---|---:|---|
| `0x1c8210` | 181 | `0x1cb100`, `0x7c5b70` |
| `0x1c8150` | 177 | `0x1c8d30`, `0x1c9290`, `0x1c97a0` |

## `..\nesting\algos\tree_db.cpp`—3 个函数 / 250 字节

| 函数 | 字节 | 种子调用者 |
|---|---:|---|
| `0x8fee00` | 88 | `0x1c37a0`, `0x1c4350`, `0x673c60` |
| `0x16c140` | 81 | `0x1c37a0`, `0x1c4350`, `0x673c60` |
| `0x16c1a0` | 81 | `0x1c4350`, `0x673c60` |

## `..\nesting\algos\sheet_optimizer.cpp`—1 个函数 / 218 字节

| 函数 | 字节 | 种子调用者 |
|---|---:|---|
| `0x8ab880` | 218 | `0x20c440`, `0x20c880` |

## `..\multi\supervisor.cpp`—1 个函数 / 181 字节

| 函数 | 字节 | 种子调用者 |
|---|---:|---|
| `0x2fa90` | 181 | `0x30030`, `0x68a6e0`, `0x7d29f0` |

## `..\engine\engine.cpp`—1 个函数 / 177 字节

| 函数 | 字节 | 种子调用者 |
|---|---:|---|
| `0x24780` | 177 | `0x75ddf0`, `0x8d4500` |

## `..\multi\database.cpp`—1 个函数 / 177 字节

| 函数 | 字节 | 种子调用者 |
|---|---:|---|
| `0x52310` | 177 | `0x52c70`, `0x59d30`, `0x6a7800` |

## `..\multi\marker.cpp`—1 个函数 / 177 字节

| 函数 | 字节 | 种子调用者 |
|---|---:|---|
| `0x84ac0` | 177 | `0x8b280`, `0x8ba70` |

## `cns.cpp`—1 个函数 / 60 字节

| 函数 | 字节 | 种子调用者 |
|---|---:|---|
| `0xac50` | 60 | `0xb600`, `0xb750`, `0xba50`, `0xbd90` |

## `..\nesting\algos\algo_parameters.cpp`—1 个函数 / 60 字节

| 函数 | 字节 | 种子调用者 |
|---|---:|---|
| `0x1a2900` | 60 | `0x1a3db0`, `0x1a89d0`, `0x1a8af0` |

## `cns_no_fit.cpp`—1 个函数 / 4 字节

| 函数 | 字节 | 种子调用者 |
|---|---:|---|
| `0x5c61e0` | 4 | `0x7270`, `0x8e70` |

# 对偶批次规则：**唯一调用者是种子**（goal round 108）**[每行一个证据地址]**

**规则**：某未引用函数的**唯一**调用者是种子（自带 TU 路径 = 身份级）⇒ 它是该调用者的**私有辅助**，归入同一 TU。每行给出那个调用者，可单点复核。

本批：**0** 个函数 / 0 字节。（两跳变体另计 0 个，**本轮不入档**。）

# 剩余工作的**确切账目**（goal round 109）

按**每个函数身上到底有什么证据**分桶（互斥）：

| 桶 | 函数 | 字节 |
|---|---:|---:|
| A own text | 213 | 158508 |
| B identity neighbour | 380 | 226632 |
| C named class | 315 | 72905 |
| D nothing to anchor on | 3113 | 1823727 |

* **A**：自带可读文本（可逐个读通并归属）
* **B**：无文本，但**有身份级邻居**（调用者/被调用者是种子）
* **C**：无文本，但**引用了具名类**（RTTI/vtable 通道）
* **D**：三者皆无 —— **没有任何可锚定的证据**

**算术**：剩余轮数 393，若靠逐函数读，需 **10.2 个/轮**；而近几轮的实际产量是 4–8 个/轮**。

# 桶 B：有身份级邻居的函数（goal round 109）**[每行带证据与强度]**

* **B2**：至少一个调用者是种子，且没有种子调用者属于别的 TU（**允许存在无标签的调用者**，故比 channel B 弱）。
* **B1**：它**调用了**某 TU 的种子（更弱：调用进入某 TU 不等于属于该 TU）。

本批：B2 **233** 个 / 116691 字节；B1 **66** 个 / 82105 字节。

## `..\structure\problem.cpp`—39 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x773eb0` | 4081 | B1 调用种子 | `0x4fcd80` |
| `0x54fcb0` | 3523 | B1 调用种子 | `0x4fc940` |
| `0x559430` | 2126 | B1 调用种子 | `0x4fc5b0` |
| `0x83dc0` | 1842 | B1 调用种子 | `0x4fc6f0` |
| `0x52be50` | 1505 | B1 调用种子 | `0x4fc5b0` |
| `0xaf7d0` | 1413 | B1 调用种子 | `0x4fc940` |
| `0x4d0950` | 1370 | B1 调用种子 | `0x4fc6f0` |
| `0x7d36e0` | 1316 | B1 调用种子 | `0x4fc940` |
| `0x7d2ed0` | 1299 | B1 调用种子 | `0x4fc940` |
| `0x54d130` | 1297 | B1 调用种子 | `0x4fc5b0` |
| `0x81700` | 1071 | B1 调用种子 | `0x4fc5b0` |
| `0x4f1740` | 989 | B1 调用种子 | `0x4fc5b0` |
| `0x1880` | 985 | B1 调用种子 | `0x4fc5b0` |
| `0x81b30` | 828 | B1 调用种子 | `0x4fc5b0` |
| `0x824b0` | 827 | B1 调用种子 | `0x4fc5b0` |
| `0x154690` | 800 | B1 调用种子 | `0x4fc5b0` |
| `0x4ff920` | 752 | B1 调用种子 | `0x4fdfe0` |
| `0x4d03f0` | 742 | B1 调用种子 | `0x4fc6f0` |
| `0x54a930` | 705 | B1 调用种子 | `0x4fc940` |
| `0x524250` | 699 | B1 调用种子 | `0x4fc5b0` |
| `0x5232e0` | 669 | B1 调用种子 | `0x4fc5b0` |
| `0x5018c0` | 659 | B1 调用种子 | `0x500a90` |
| `0x4d06e0` | 624 | B1 调用种子 | `0x4fc5b0` |
| `0x814a0` | 596 | B1 调用种子 | `0x4fc5b0` |
| `0x501660` | 593 | B1 调用种子 | `0x500a90` |
| `0x4b320` | 589 | B1 调用种子 | `0x4fc5b0` |
| `0x266e00` | 492 | B1 调用种子 | `0x4fc940` |
| `0x4d9c0` | 438 | B1 调用种子 | `0x4fc5b0` |
| `0x81350` | 323 | B1 调用种子 | `0x4fc5b0` |
| `0x520840` | 294 | B1 调用种子 | `0x4fca80` |
| `0x54fbc0` | 239 | B1 调用种子 | `0x4fc940` |
| `0x546930` | 220 | B1 调用种子 | `0x4fc5b0` |
| `0x523100` | 218 | B1 调用种子 | `0x4fc940` |
| `0x523fe0` | 193 | B1 调用种子 | `0x4fc940` |
| `0x2e650` | 174 | B1 调用种子 | `0x4fc6f0` |
| `0x5240b0` | 95 | B1 调用种子 | `0x4fc940` |
| `0x523580` | 79 | B1 调用种子 | `0x4fc5b0` |
| `0x522540` | 62 | B1 调用种子 | `0x4fc940` |
| `0x4f76b0` | 4 | B2 种子调用者 | `0x500a90` |

## `..\tiling\optimizer.cpp`—15 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x7eedb0` | 8514 | B1 调用种子 | `0x7ee7b0` |
| `0x7f1b50` | 3983 | B1 调用种子 | `0x7ee7b0` |
| `0x7ec9a0` | 3602 | B1 调用种子 | `0x4e9a10` |
| `0x4ea310` | 1706 | B1 调用种子 | `0x4e9a10` |
| `0x7f2ae0` | 1445 | B2 种子调用者 | `0x7ee7b0` |
| `0x76df60` | 686 | B2 种子调用者 | `0x7ee7b0` |
| `0x8d4be0` | 432 | B2 种子调用者 | `0x7ee7b0` |
| `0x8d8a80` | 376 | B2 种子调用者 | `0x4e9a10` |
| `0x8c37f0` | 335 | B2 种子调用者 | `0x7ee7b0` |
| `0x4f3490` | 280 | B2 种子调用者 | `0x4e9a10` |
| `0x76dec0` | 160 | B2 种子调用者 | `0x7ee7b0` |
| `0x4f35d0` | 46 | B2 种子调用者 | `0x4e9a10` |
| `0x4daea0` | 5 | B2 种子调用者 | `0x4e9a10` |
| `0x4daeb0` | 5 | B2 种子调用者 | `0x4e9a10` |
| `0x4ddcc0` | 5 | B2 种子调用者 | `0x7ee7b0` |

## `..\multi\nesting_context.cpp`—32 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x181e80` | 3842 | B2 种子调用者 | `0x69aa40` |
| `0x786e0` | 3676 | B1 调用种子 | `0x434d0` |
| `0x5884d0` | 1419 | B2 种子调用者 | `0x3c9e0` |
| `0x3d1e0` | 1071 | B1 调用种子 | `0x3b2f0`, `0x3c9e0` |
| `0x549270` | 983 | B2 种子调用者 | `0x69aa40` |
| `0x934080` | 980 | B2 种子调用者 | `0x696c50` |
| `0x7d21a0` | 860 | B2 种子调用者 | `0x40720` |
| `0x3fa50` | 752 | B2 种子调用者 | `0x434d0` |
| `0x1d0d70` | 719 | B2 种子调用者 | `0x40720` |
| `0x16ef80` | 622 | B2 种子调用者 | `0x40070` |
| `0xaeaf0` | 552 | B2 种子调用者 | `0x41920` |
| `0x92a6d0` | 519 | B2 种子调用者 | `0x696c50` |
| `0x4f1bc0` | 512 | B2 种子调用者 | `0x3e740` |
| `0x4f1590` | 425 | B2 种子调用者 | `0x3e740` |
| `0x93fbb0` | 408 | B2 种子调用者 | `0x696c50` |
| `0x69bd10` | 354 | B2 种子调用者 | `0x696c50` |
| `0x69a8f0` | 334 | B2 种子调用者 | `0x69aa40` |
| `0x8e8690` | 330 | B2 种子调用者 | `0x69a720` |
| `0x531bd0` | 310 | B2 种子调用者 | `0x696c50` |
| `0x65e430` | 244 | B2 种子调用者 | `0x696c50` |
| `0x530010` | 242 | B2 种子调用者 | `0x696c50` |
| `0x40bf0` | 223 | B1 调用种子 | `0x40720` |
| `0x40cd0` | 223 | B1 调用种子 | `0x40720` |
| `0x8f3fa0` | 220 | B2 种子调用者 | `0x69aa40` |
| `0x90d790` | 209 | B2 种子调用者 | `0x69aa40` |
| `0x678f40` | 207 | B2 种子调用者 | `0x41920` |
| `0x51f970` | 185 | B2 种子调用者 | `0x40070` |
| `0x90d910` | 155 | B2 种子调用者 | `0x41920` |
| `0x42f30` | 112 | B1 调用种子 | `0x41920` |
| `0x6de240` | 97 | B2 种子调用者 | `0x41920` |
| `0x454e0` | 80 | B1 调用种子 | `0x696c50` |
| `0x5483c0` | 5 | B2 种子调用者 | `0x3bcc0` |

## `..\verify\equivalent.cpp`—29 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x535c60` | 9499 | B2 种子调用者 | `0x4bdb70` |
| `0x4f7aa0` | 2196 | B2 种子调用者 | `0x4bdb70` |
| `0x4f9fe0` | 1821 | B2 种子调用者 | `0x4bdb70` |
| `0x896720` | 737 | B2 种子调用者 | `0x4bdb70` |
| `0x8c49f0` | 621 | B2 种子调用者 | `0x4bdb70` |
| `0x67ef20` | 560 | B2 种子调用者 | `0x4bdb70` |
| `0x533fa0` | 551 | B2 种子调用者 | `0x4bdb70` |
| `0x4f7070` | 488 | B2 种子调用者 | `0x4bdb70` |
| `0x547dc0` | 447 | B2 种子调用者 | `0x4bdb70` |
| `0x5c90a0` | 357 | B2 种子调用者 | `0x4bdb70` |
| `0x4b9b80` | 354 | B2 种子调用者 | `0x4bdb70` |
| `0x4fb790` | 350 | B2 种子调用者 | `0x4bdb70` |
| `0x586300` | 349 | B2 种子调用者 | `0x4bc9e0` |
| `0x545370` | 272 | B2 种子调用者 | `0x4bdb70` |
| `0x5ccb10` | 254 | B2 种子调用者 | `0x4bdb70` |
| `0x8890e0` | 118 | B2 种子调用者 | `0x4bdb70` |
| `0x5ca7e0` | 96 | B2 种子调用者 | `0x4bc9e0` |
| `0x4fbe40` | 10 | B2 种子调用者 | `0x4bdb70` |
| `0x4fc240` | 10 | B2 种子调用者 | `0x4bdb70` |
| `0x4f77c0` | 8 | B2 种子调用者 | `0x4bdb70` |
| `0x4f73b0` | 7 | B2 种子调用者 | `0x4bdb70` |
| `0x4f8c90` | 6 | B2 种子调用者 | `0x4bdb70` |
| `0x4f8ca0` | 6 | B2 种子调用者 | `0x4bdb70` |
| `0x4f8cb0` | 6 | B2 种子调用者 | `0x4bdb70` |
| `0x4f7350` | 5 | B2 种子调用者 | `0x4bdb70` |
| `0x4f7360` | 5 | B2 种子调用者 | `0x4bdb70` |
| `0x52f8a0` | 5 | B2 种子调用者 | `0x4ba110` |
| `0x4f8cd0` | 4 | B2 种子调用者 | `0x4bdb70` |
| `0x548380` | 4 | B2 种子调用者 | `0x4bdb70` |

## `..\nesting\algos\tree_db.cpp`—12 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x1e3aa0` | 15380 | B1 调用种子 | `0x1c2110`, `0x1c4350` |
| `0x1c2310` | 674 | B2 种子调用者 | `0x65cc50` |
| `0x8fe860` | 437 | B2 种子调用者 | `0x65cc50` |
| `0x1c5830` | 309 | B1 调用种子 | `0x65cc50` |
| `0x1c1e00` | 289 | B2 种子调用者 | `0x1c1f30` |
| `0x775500` | 251 | B2 种子调用者 | `0x1c2110` |
| `0x986760` | 245 | B2 种子调用者 | `0x65cc50` |
| `0x62fbd0` | 224 | B2 种子调用者 | `0x65cc50` |
| `0x6dd800` | 118 | B2 种子调用者 | `0x673c60` |
| `0x1c25c0` | 86 | B2 种子调用者 | `0x673c60` |
| `0x89e5f0` | 35 | B2 种子调用者 | `0x65cc50` |
| `0x5c4cf0` | 28 | B2 种子调用者 | `0x65cc50` |

## `..\tiling\packer.cpp`—16 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x4e5d30` | 5147 | B2 种子调用者 | `0x770d10` |
| `0x15ae70` | 2429 | B2 种子调用者 | `0x770d10` |
| `0x15c560` | 849 | B2 种子调用者 | `0x770d10` |
| `0x8c6fc0` | 848 | B2 种子调用者 | `0x770d10` |
| `0x52fae0` | 622 | B2 种子调用者 | `0x770d10` |
| `0x8c8160` | 456 | B2 种子调用者 | `0x770d10` |
| `0x8c8450` | 442 | B2 种子调用者 | `0x770d10` |
| `0x6d2b10` | 398 | B2 种子调用者 | `0x770d10` |
| `0x15e5a0` | 255 | B2 种子调用者 | `0x770d10` |
| `0x15a410` | 184 | B2 种子调用者 | `0x770d10` |
| `0x15b800` | 145 | B2 种子调用者 | `0x770d10` |
| `0x4dddd0` | 124 | B2 种子调用者 | `0x770d10` |
| `0x4de020` | 42 | B2 种子调用者 | `0x770d10` |
| `0x531eb0` | 17 | B2 种子调用者 | `0x770d10` |
| `0x4dac80` | 4 | B2 种子调用者 | `0x770d10` |
| `0x4dc390` | 4 | B2 种子调用者 | `0x770d10` |

## `..\structure\svg_io.cpp`—24 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x5e1490` | 3026 | B2 种子调用者 | `0x516380` |
| `0x518910` | 1659 | B1 调用种子 | `0x5100d0`, `0x516380` |
| `0x54b600` | 1081 | B2 种子调用者 | `0x516380` |
| `0x5e0d90` | 918 | B2 种子调用者 | `0x516380` |
| `0x547730` | 633 | B2 种子调用者 | `0x516380` |
| `0x5d7070` | 507 | B2 种子调用者 | `0x510a90` |
| `0x5d7b90` | 340 | B2 种子调用者 | `0x510560` |
| `0x5d74f0` | 318 | B2 种子调用者 | `0x510560` |
| `0x5e0960` | 315 | B2 种子调用者 | `0x516380` |
| `0x5d9e90` | 259 | B2 种子调用者 | `0x516380` |
| `0x50ffd0` | 255 | B2 种子调用者 | `0x5100d0` |
| `0x5479d0` | 255 | B2 种子调用者 | `0x516380` |
| `0x5d9a10` | 240 | B2 种子调用者 | `0x516380` |
| `0x5d9da0` | 226 | B2 种子调用者 | `0x516380` |
| `0x911470` | 154 | B2 种子调用者 | `0x516380` |
| `0x5d8a70` | 120 | B2 种子调用者 | `0x510560` |
| `0x5185f0` | 97 | B1 调用种子 | `0x516380` |
| `0x5d19d0` | 91 | B2 种子调用者 | `0x516380` |
| `0x510a40` | 76 | B1 调用种子 | `0x510560` |
| `0x516020` | 45 | B1 调用种子 | `0x513880` |
| `0x5da250` | 17 | B2 种子调用者 | `0x516380` |
| `0x5da240` | 10 | B2 种子调用者 | `0x516380` |
| `0x51dd70` | 8 | B2 种子调用者 | `0x516380` |
| `0x5d74d0` | 7 | B2 种子调用者 | `0x510560` |

## `internal.cpp`—24 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x587ec0` | 1552 | B2 种子调用者 | `0x1e900` |
| `0x8c2380` | 986 | B2 种子调用者 | `0x1ee50` |
| `0x93e7b0` | 975 | B2 种子调用者 | `0x1ee50` |
| `0x8c2e10` | 772 | B2 种子调用者 | `0x22e40` |
| `0x4ffc50` | 752 | B2 种子调用者 | `0x1ee50` |
| `0x54cea0` | 552 | B2 种子调用者 | `0x1ee50` |
| `0x1e140` | 408 | B2 种子调用者 | `0x1ee50` |
| `0x1e2e0` | 408 | B2 种子调用者 | `0x1ee50` |
| `0x8f8a80` | 401 | B2 种子调用者 | `0x1ee50` |
| `0x1b690` | 268 | B2 种子调用者 | `0x1ee50` |
| `0x5c5ff0` | 253 | B2 种子调用者 | `0x1ee50` |
| `0x23bf0` | 246 | B1 调用种子 | `0x22e40` |
| `0x523e60` | 193 | B2 种子调用者 | `0x1ee50` |
| `0x1e010` | 192 | B2 种子调用者 | `0x1ee50` |
| `0x932780` | 188 | B2 种子调用者 | `0x1ee50` |
| `0x9328f0` | 188 | B2 种子调用者 | `0x1ee50` |
| `0x1b170` | 80 | B2 种子调用者 | `0x1ee50` |
| `0x5ee110` | 62 | B2 种子调用者 | `0x22e40` |
| `0x5ee150` | 62 | B2 种子调用者 | `0x22e40` |
| `0x583810` | 32 | B2 种子调用者 | `0x22e40` |
| `0x4fbe60` | 12 | B2 种子调用者 | `0x1ee50` |
| `0x4f8d20` | 9 | B2 种子调用者 | `0x1ee50` |
| `0x4f7340` | 6 | B2 种子调用者 | `0x1ee50` |
| `0x4f9c20` | 6 | B2 种子调用者 | `0x1ee50` |

## `..\structure\automatic_cluster.cpp`—13 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x553230` | 2161 | B2 种子调用者 | `0x5563c0` |
| `0x1efe50` | 1829 | B1 调用种子 | `0x552e30`, `0x5563c0` |
| `0x997f90` | 1024 | B1 调用种子 | `0x5563c0` |
| `0x555d40` | 548 | B2 种子调用者 | `0x5563c0` |
| `0x7bbb30` | 406 | B2 种子调用者 | `0x5563c0` |
| `0x7bb9a0` | 326 | B2 种子调用者 | `0x5563c0` |
| `0x7bb850` | 321 | B2 种子调用者 | `0x5563c0` |
| `0x5523b0` | 177 | B2 种子调用者 | `0x5563c0` |
| `0x991f80` | 163 | B2 种子调用者 | `0x5563c0` |
| `0x90c000` | 155 | B2 种子调用者 | `0x5563c0` |
| `0x8e7760` | 88 | B2 种子调用者 | `0x5563c0` |
| `0x7bbaf0` | 49 | B2 种子调用者 | `0x5563c0` |
| `0x4f7670` | 9 | B2 种子调用者 | `0x5563c0` |

## `..\tiling\packer_cache.cpp`—13 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x560380` | 2212 | B2 种子调用者 | `0x768b80` |
| `0x5c3820` | 1295 | B2 种子调用者 | `0x768b80` |
| `0x763b10` | 975 | B1 调用种子 | `0x765460` |
| `0x4de560` | 814 | B2 种子调用者 | `0x769410` |
| `0x4dba70` | 626 | B2 种子调用者 | `0x768b80` |
| `0x8fc220` | 293 | B2 种子调用者 | `0x768b80` |
| `0x8fc3e0` | 293 | B2 种子调用者 | `0x158810` |
| `0x8e4460` | 264 | B2 种子调用者 | `0x768b80` |
| `0x4dda10` | 116 | B2 种子调用者 | `0x769410` |
| `0x52fd50` | 53 | B2 种子调用者 | `0x769410` |
| `0x5c4100` | 49 | B2 种子调用者 | `0x768b80` |
| `0x5ce2a0` | 45 | B2 种子调用者 | `0x768b80` |
| `0x4dc3b0` | 5 | B2 种子调用者 | `0x769410` |

## `..\nesting\algos\algo_parameters.cpp`—10 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x4d8dc0` | 1945 | B2 种子调用者 | `0x1a3db0` |
| `0x660010` | 1334 | B2 种子调用者 | `0x1a66a0` |
| `0x1a3900` | 1083 | B2 种子调用者 | `0x1a66a0` |
| `0x6451c0` | 433 | B2 种子调用者 | `0x1a66a0` |
| `0x90cc70` | 338 | B2 种子调用者 | `0x1a66a0` |
| `0x1a7580` | 189 | B1 调用种子 | `0x1a66a0` |
| `0x1a4920` | 183 | B2 种子调用者 | `0x1a66a0` |
| `0x1a2840` | 177 | B2 种子调用者 | `0x1a66a0` |
| `0x65e820` | 174 | B2 种子调用者 | `0x1a66a0` |
| `0x1a2940` | 86 | B2 种子调用者 | `0x1a66a0` |

## `..\nesting\algos\bucket_manager.hpp`—7 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x22e390` | 1478 | B2 种子调用者 | `0x215720` |
| `0x233f50` | 1414 | B2 种子调用者 | `0x215720` |
| `0x65bc00` | 960 | B2 种子调用者 | `0x215720` |
| `0x1aaca0` | 577 | B1 调用种子 | `0x215720` |
| `0x2337d0` | 447 | B2 种子调用者 | `0x215720` |
| `0x2203a0` | 244 | B2 种子调用者 | `0x215720` |
| `0x21fab0` | 59 | B2 种子调用者 | `0x215720` |

## `..\multi\marker.cpp`—4 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x69cb20` | 2556 | B2 种子调用者 | `0x8b280` |
| `0x6bd4a0` | 1839 | B2 种子调用者 | `0x8ba70` |
| `0x452f0` | 411 | B2 种子调用者 | `0x8ba70` |
| `0x45490` | 80 | B2 种子调用者 | `0x8ba70` |

## `..\multi\database.cpp`—8 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x5448c0` | 1350 | B2 种子调用者 | `0x59d30` |
| `0x54bfe0` | 1047 | B2 种子调用者 | `0x59d30` |
| `0x545e50` | 855 | B2 种子调用者 | `0x59d30` |
| `0x5cc8a0` | 461 | B2 种子调用者 | `0x59d30` |
| `0x6aab10` | 168 | B1 调用种子 | `0x6a7800` |
| `0x545220` | 107 | B2 种子调用者 | `0x525e0` |
| `0x5451d0` | 78 | B2 种子调用者 | `0x59d30` |
| `0x543670` | 72 | B2 种子调用者 | `0x525e0` |

## `..\nesting\structure_interface_private.hpp`—5 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x17abc0` | 2942 | B2 种子调用者 | `0x1f1c20` |
| `0x8b8420` | 456 | B2 种子调用者 | `0x1f1c20` |
| `0x5f3cb0` | 160 | B2 种子调用者 | `0x1f2d00` |
| `0x5f3bd0` | 73 | B2 种子调用者 | `0x1f2d00` |
| `0x5f3c70` | 59 | B2 种子调用者 | `0x1f2d00` |

## `..\nesting\algos\multinesting_optimizer.cpp`—7 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x8ba000` | 884 | B2 种子调用者 | `0x1aafe0` |
| `0x19da20` | 761 | B2 种子调用者 | `0x1b64e0` |
| `0x1a8cb0` | 177 | B2 种子调用者 | `0x1b64e0` |
| `0x8ba440` | 166 | B2 种子调用者 | `0x1b64e0` |
| `0x8d22f0` | 164 | B2 种子调用者 | `0x1b64e0` |
| `0x1f8350` | 132 | B2 种子调用者 | `0x1b64e0` |
| `0x1a8db0` | 90 | B2 种子调用者 | `0x1b64e0` |

## `..\structure\text_io.cpp`—12 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x5f8220` | 671 | B2 种子调用者 | `0x50ee50` |
| `0x681c60` | 468 | B2 种子调用者 | `0x50ee50` |
| `0x504fe0` | 177 | B2 种子调用者 | `0x50ee50` |
| `0x5fa940` | 176 | B2 种子调用者 | `0x50ee50` |
| `0x5fb860` | 173 | B2 种子调用者 | `0x50ee50` |
| `0x5fcf60` | 146 | B2 种子调用者 | `0x505ce0` |
| `0x5fcc50` | 108 | B2 种子调用者 | `0x50ee50` |
| `0x57a610` | 107 | B2 种子调用者 | `0x509a40` |
| `0x5052c0` | 57 | B2 种子调用者 | `0x509a40` |
| `0x5fd0a0` | 35 | B2 种子调用者 | `0x50ee50` |
| `0x5fd060` | 21 | B2 种子调用者 | `0x509a40` |
| `0x51cfe0` | 7 | B2 种子调用者 | `0x50ee50` |

## `..\nesting\algos\compact.hpp`—4 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x8b4bb0` | 1653 | B2 种子调用者 | `0x1da0c0` |
| `0x8bad20` | 368 | B2 种子调用者 | `0x1da0c0` |
| `0x17b9a0` | 5 | B2 种子调用者 | `0x1da0c0` |
| `0x17b9d0` | 5 | B2 种子调用者 | `0x1da0c0` |

## `..\multi\tiling_nester.cpp`—1 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x6bc540` | 1839 | B2 种子调用者 | `0x462d0` |

## `..\structure\stats.cpp`—5 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0xae040` | 767 | B1 调用种子 | `0x527870` |
| `0x521f90` | 589 | B2 种子调用者 | `0x525ef0` |
| `0x528ae0` | 257 | B1 调用种子 | `0x528020` |
| `0x52c540` | 118 | B1 调用种子 | `0x520e30` |
| `0x52fa40` | 37 | B2 种子调用者 | `0x525ef0` |

## `..\multi\supervisor.cpp`—2 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x51ecf0` | 893 | B2 种子调用者 | `0x68a6e0` |
| `0x2f9d0` | 177 | B2 种子调用者 | `0x7d2610` |

## `cns_no_fit.cpp`—2 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x4c0700` | 697 | B2 种子调用者 | `0x668f20` |
| `0x586460` | 349 | B2 种子调用者 | `0x665f40` |

## `..\engine\cloud_engine.cpp`—4 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x915080` | 202 | B2 种子调用者 | `0x26a60` |
| `0x51c6e0` | 173 | B2 种子调用者 | `0x26a60` |
| `0x6fc3b0` | 111 | B2 种子调用者 | `0x26a60` |
| `0x4fbe70` | 12 | B2 种子调用者 | `0x26a60` |

## `..\structure\multitorch_eval.cpp`—2 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x90dcc0` | 338 | B2 种子调用者 | `0x53cc30` |
| `0x7bbec0` | 104 | B2 种子调用者 | `0x53cc30` |

## `..\exact\relinker_internal.cpp`—1 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x5b3e20` | 428 | B1 调用种子 | `0x5b3bf0` |

## `cns.cpp`—2 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x51e060` | 329 | B2 种子调用者 | `0x10040` |
| `0x8761b0` | 48 | B2 种子调用者 | `0xf7c0` |

## `..\engine\engine.cpp`—1 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x4c1f30` | 346 | B2 种子调用者 | `0x75ddf0` |

## `..\nesting\algos\postop.cpp`—1 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x4d6110` | 261 | B2 种子调用者 | `0x1cb100` |

## `..\nesting\ios\log_ios.cpp`—2 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x1f84c0` | 177 | B2 种子调用者 | `0x1fb810` |
| `0x1f8580` | 60 | B2 种子调用者 | `0x1fb810` |

## `..\nesting\algos\sheet_optimizer.cpp`—2 个函数

| 函数 | 字节 | 强度 | 证据（相关种子） |
|---|---:|---|---|
| `0x1c1110` | 129 | B2 种子调用者 | `0x20c440` |
| `0x20c850` | 44 | B1 调用种子 | `0x20c440` |

# 桶 C 的**领域类行**（goal round 111）**[每行带类名]**

只列**引用领域类**的函数（共 **0** 个 / 0 字节）；已归为库代码的 **214** 个不在此表。

# 桶 C 的领域类行（恢复版，goal round 111b）**[每行带类名证据]**

上一轮重写时把本批误删了（那使 cited 降 38、领域升 33），现用**全可达集**重扫并只归档**当前仍未引用**者：**73** 个 / 28416 字节。

## `Tiling::Part`—4 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x4dafc0` | 258 | 86 | `Tiling::Part` |
| `0x4db0d0` | 254 | 71 | `Tiling::Part` |
| `0x4db1d0` | 254 | 71 | `Tiling::Part` |
| `0x4daec0` | 249 | 78 | `Tiling::Part` |

## `Multi::DatabaseNester`—3 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x5b100` | 85 | 27 | `Multi::DatabaseNester` |
| `0x5b1f0` | 83 | 23 | `Multi::DatabaseNester` |
| `0x5b170` | 77 | 25 | `Multi::DatabaseNester` |

## `Tiling::PackerCache`—3 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x158f60` | 919 | 238 | `Tiling::PackerCache` |
| `0x158be0` | 895 | 234 | `Tiling::PackerCache` |
| `0x159480` | 98 | 32 | `Tiling::PackerCache` |

## `Pack::BestNester`—3 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x681ee0` | 157 | 59 | `Pack::BestNester` |
| `0x681e40` | 149 | 52 | `Pack::BestNester` |
| `0x15e3b0` | 81 | 17 | `Pack::BestNester` |

## `Tiling::BoxMultiTiler`—3 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x4f4850` | 883 | 203 | `Tiling::BoxMultiTiler` |
| `0x76b380` | 45 | 13 | `Tiling::BoxMultiTiler` |
| `0x76b3b0` | 33 | 8 | `Tiling::BoxMultiTiler` |

## `Structure::ClusterObserver`—3 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x7bc0c0` | 191 | 64 | `Structure::ClusterObserver` |
| `0x7bc000` | 188 | 59 | `Structure::ClusterObserver` |
| `0x553100` | 75 | 17 | `Structure::ClusterObserver` |

## `Tiling::SqueezeMultiTiler`—3 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x76e440` | 2741 | 518 | `Tiling::SqueezeMultiTiler` |
| `0x76f0a0` | 427 | 129 | `Tiling::SqueezeMultiTiler` |
| `0x76ef00` | 416 | 123 | `Tiling::SqueezeMultiTiler` |

## `Engine::EquivalentEngine`—2 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x25a20` | 512 | 129 | `Engine::EquivalentEngine` |
| `0x24ab0` | 190 | 48 | `Engine::EquivalentEngine` |

## `Multi::NestingNester`—2 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x32f30` | 73 | 19 | `Multi::NestingNester` |
| `0x32ee0` | 65 | 17 | `Multi::NestingNester` |

## `Multi::TilingNester`—2 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x45680` | 99 | 31 | `Multi::TilingNester` |
| `0x456f0` | 91 | 29 | `Multi::TilingNester` |

## `Multi::RectangleNester`—2 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x6d3a0` | 193 | 63 | `Multi::RectangleNester` |
| `0x6d2e0` | 185 | 61 | `Multi::RectangleNester` |

## `N5Multi12TerminalNodeE`—2 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x9c280` | 2731 | 563 | `N5Multi12TerminalNodeE` |
| `0x9cd30` | 2604 | 546 | `N5Multi12TerminalNodeE` |

## `Utils::LogSink`—2 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x199570` | 2703 | 538 | `Utils::LogSink` |
| `0x19dd20` | 677 | 160 | `Utils::LogSink` |

## `Tiling::BiModulePattern`—2 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x7e8520` | 757 | 169 | `Tiling::BiModulePattern` |
| `0x4f2870` | 156 | 41 | `Tiling::BiModulePattern` |

## `Multi::FlipNester`—2 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x687de0` | 36 | 10 | `Multi::FlipNester` |
| `0x687e10` | 15 | 3 | `Multi::FlipNester` |

## `Multi::FilterNester`—2 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x6937a0` | 36 | 10 | `Multi::FilterNester` |
| `0x6937d0` | 15 | 3 | `Multi::FilterNester` |

## `Multi::NoFillNester`—2 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x6937e0` | 67 | 19 | `Multi::NoFillNester` |
| `0x693830` | 59 | 17 | `Multi::NoFillNester` |

## `Multi::WrapObserver`—2 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x695dc0` | 40 | 11 | `Multi::WrapObserver` |
| `0x695df0` | 19 | 4 | `Multi::WrapObserver` |

## `Multi::CompactNester`—2 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x695e10` | 36 | 10 | `Multi::CompactNester` |
| `0x695e40` | 15 | 3 | `Multi::CompactNester` |

## `Multi::LimitedNester`—2 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x695e50` | 48 | 13 | `Multi::LimitedNester` |
| `0x695e80` | 40 | 11 | `Multi::LimitedNester` |

## `Multi::NoMixSheetSelector`—2 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x69a5d0` | 86 | 25 | `Multi::NoMixSheetSelector` |
| `0x69a580` | 74 | 22 | `Multi::NoMixSheetSelector` |

## `Utils::BadResponseException`—2 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x6d58d0` | 36 | 10 | `Utils::BadResponseException` |
| `0x6d5900` | 15 | 3 | `Utils::BadResponseException` |

## `Engine::EquivalentObserver`—2 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x75e0e0` | 76 | 25 | `Engine::EquivalentObserver` |
| `0x75e130` | 71 | 23 | `Engine::EquivalentObserver` |

## `Tiling::CompositePart`—2 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x76b3e0` | 53 | 15 | `Tiling::CompositePart` |
| `0x76b420` | 45 | 13 | `Tiling::CompositePart` |

## `Structure::ParseSolutionException`—2 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x7bfe60` | 36 | 10 | `Structure::ParseSolutionException` |
| `0x7bfe90` | 15 | 3 | `Structure::ParseSolutionException` |

## `Engine::NestingEngine`—1 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x23e70` | 595 | 159 | `Engine::NestingEngine` |

## `Engine::MultiEngine`—1 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x240d0` | 431 | 118 | `Engine::MultiEngine` |

## `Engine::DelayedEngine`—1 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x24b80` | 192 | 50 | `Engine::DelayedEngine` |

## `Engine::CompositeEngine`—1 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x24c40` | 334 | 87 | `Engine::CompositeEngine` |

## `Engine::InfiniteEngine`—1 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x24fd0` | 209 | 53 | `Engine::InfiniteEngine` |

## `Multi::TraceObserver`—1 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x5f000` | 44 | 10 | `Multi::TraceObserver` |

## `Multi::TerminalNode`—1 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x99360` | 1449 | 328 | `Multi::TerminalNode` |

## `Multi::SplitNode`—1 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x99910` | 447 | 119 | `Multi::SplitNode` |

## `N5Multi4NodeE`—1 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x9c060` | 537 | 118 | `N5Multi4NodeE` |

## `Pack::KnapsackNester`—1 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x15d1d0` | 29 | 8 | `Pack::KnapsackNester` |

## `Pack::RecursiveNester`—1 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x162280` | 996 | 210 | `Pack::RecursiveNester` |

## `Tiling::QuantityEvaluator`—1 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x4e81b0` | 551 | 127 | `Tiling::QuantityEvaluator` |

## `Tiling::MultiOrientedPartPattern`—1 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x4f2a30` | 1944 | 409 | `Tiling::MultiOrientedPartPattern` |

## `Tiling::BasicCandidater`—1 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x4f3630` | 19 | 5 | `Tiling::BasicCandidater` |

## `Utils::TimerWinImplementation`—1 个函数

| 函数 | 字节 | 指令 | 证据（引用的类） |
|---|---:|---:|---|
| `0x5f47c0` | 112 | 29 | `Utils::TimerWinImplementation` |
