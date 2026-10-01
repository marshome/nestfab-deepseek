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
