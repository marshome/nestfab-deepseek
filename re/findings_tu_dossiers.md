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
