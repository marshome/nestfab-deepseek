# `re/VTABLE_SLOTS.md` —— 虚表槽位身份档案（**按类分组**）

由 `re/g_vtable_slots.py` 生成（goal round 9）。

## 这份档案的**身份**来自哪里

虚表顺序是**已恢复的数据**（`re/vtables.json`，443 个类），因此
「**`类名` 的第 k 槽**」是一个**确定的身份**，不是猜测：
它是该类第 k 个虚函数，调用点由虚表分派决定。
本轮把这类函数（此前只有结构指纹）提升为**有身份记录**。

**不在此列的**：只知形态、不知所属类的函数仍留在 `re/IDENTIFIED.md`，本档**不认领**它们。

## 统计

| 项 | 数值 |
|---|---|
| 有槽位身份的函数 | **209** |
| 字节 | **31685** |
| 涉及类数 | **68** |

规模分布：tiny (<=32B) 90, small 77, medium 37, large 5

## 按类分组

| 类 | 槽位身份（未引用者） |
|---|---|
| **Pack::RecursiveNester** （3 槽中 2 个未引用） | #0 `0x683d80` (2119B), #1 `0x681fa0` (7633B) |
| **Tiling::MultiOrientedPartPattern** （8 槽中 8 个未引用） | #0 `0x76f9d0` (1B), #1 `0x76f9c0` (5B), #2 `0x7ebb90` (152B), #3 `0x7eb5e0` (939B), #4 `0x7ebc30` (349B), #5 `0x7eb990` (510B), #6 `0x7ebdb0` (525B), #7 `0x7ebd90` (18B) |
| **Tiling::BiModulePattern** （8 槽中 8 个未引用） | #0 `0x76db40` (1B), #1 `0x76db30` (5B), #2 `0x7e84f0` (34B), #3 `0x7e8100` (74B), #4 `0x7e8520` (757B), #5 `0x7e8150` (923B), #6 `0x7e8840` (205B), #7 `0x7e8820` (26B) |
| **Tiling::PackerCache** （2 槽中 2 个未引用） | #0 `0x158be0` (895B), #1 `0x158f60` (919B) |
| **Multi::NoMixSheetSelector** （4 槽中 4 个未引用） | #0 `0x69a5d0` (86B), #1 `0x69a580` (74B), #2 `0x7d2ed0` (1299B), #3 `0x7d33f0` (193B) |
| **<subst>::__cxx11::basic_stringbuf::<>** （14 槽中 9 个未引用） | #0 `0x915ec0` (68B), #1 `0x915e70` (72B), #3 `0x915040` (50B), #4 `0x915150` (444B), #5 `0x915310` (278B), #7 `0x9156e0` (44B), #9 `0x915710` (54B), #11 `0x915680` (91B), #13 `0x915480` (499B) |
| **Tiling::SqueezeMultiTiler** （5 槽中 4 个未引用） | #0 `0x76f0a0` (427B), #1 `0x76ef00` (416B), #3 `0x7e9190` (13B), #4 `0x7e9180` (13B) |
| **Tiling::UnlimitedXDensityEvaluator** （4 槽中 3 个未引用） | #0 `0x76fa10` (1B), #1 `0x76fa00` (5B), #2 `0x7ec210` (590B) |
| **Tiling::UnlimitedDensityEvaluator** （4 槽中 3 个未引用） | #0 `0x76f9f0` (1B), #1 `0x76f9e0` (5B), #2 `0x7ebfc0` (578B) |
| **Tiling::ReusableEvaluator** （4 槽中 3 个未引用） | #0 `0x76e430` (1B), #1 `0x76e420` (5B), #2 `0x7e8f60` (542B) |
| **Tiling::Part** （2 槽中 2 个未引用） | #0 `0x4dafc0` (258B), #1 `0x4daec0` (249B) |
| **Multi::FilterNester** （6 槽中 4 个未引用） | #0 `0x6937d0` (15B), #1 `0x6937a0` (36B), #2 `0xb43b0` (115B), #3 `0xb3920` (324B) |
| **Multi::CompactNester** （6 槽中 4 个未引用） | #0 `0x695e40` (15B), #1 `0x695e10` (36B), #2 `0xb3890` (115B), #3 `0xb0130` (309B) |
| **Structure::ClusterObserver** （6 槽中 3 个未引用） | #0 `0x7bc0c0` (191B), #1 `0x7bc000` (188B), #4 `0x5593f0` (63B) |
| **Tiling::QuantityEvaluator** （4 槽中 4 个未引用） | #0 `0x76e410` (1B), #1 `0x76e400` (5B), #2 `0x7e8dd0` (390B), #3 `0x7e8da0` (37B) |
| **Multi::NestingContextPool** （3 槽中 3 个未引用） | #0 `0x69a500` (115B), #1 `0x69a480` (123B), #2 `0x7d2e20` (176B) |
| **Structure::SizeDimensioner** （3 槽中 3 个未引用） | #0 `0x7bc330` (1B), #1 `0x7bc320` (5B), #2 `0x81df30` (381B) |
| **Multi::RectangleNester** （6 槽中 2 个未引用） | #0 `0x6d2e0` (185B), #1 `0x6d3a0` (193B) |
| **Multi::NestingNester** （6 槽中 4 个未引用） | #0 `0x32ee0` (65B), #1 `0x32f30` (73B), #2 `0x3b110` (115B), #4 `0x32d90` (97B) |
| **Tiling::BasicCandidater** （3 槽中 3 个未引用） | #0 `0x4f3600` (1B), #1 `0x4f3610` (5B), #2 `0x4f4600` (340B) |
| **Structure::BoxAreaDimensioner** （3 槽中 3 个未引用） | #0 `0x7bf060` (1B), #1 `0x7bf050` (5B), #2 `0x81e1e0` (333B) |
| **Multi::NoFillNester** （6 槽中 3 个未引用） | #0 `0x693830` (59B), #1 `0x6937e0` (67B), #3 `0x7eca0` (211B) |
| **<subst>::__cxx11::basic_stringstream::<>** （2 槽中 2 个未引用） | #0 `0x91a7c0` (160B), #1 `0x91a710` (168B) |
| **Multi::TilingNester** （6 槽中 4 个未引用） | #0 `0x456f0` (91B), #1 `0x45680` (99B), #3 `0x45750` (39B), #4 `0x45560` (82B) |
| **Multi::PartUpdaterLimiter** （4 槽中 4 个未引用） | #0 `0x69a640` (1B), #1 `0x69a630` (5B), #2 `0x7d3530` (201B), #3 `0x7d34c0` (104B) |
| **Pack::BestNester** （3 槽中 2 个未引用） | #0 `0x681ee0` (157B), #1 `0x681e40` (149B) |
| **Structure::WidthDimensioner** （3 槽中 3 个未引用） | #0 `0x7befb0` (1B), #1 `0x7befa0` (5B), #2 `0x81e0b0` (297B) |
| **<subst>::__cxx11::moneypunct::<>** （11 槽中 4 个未引用） | #0 `0x90e150` (72B), #0 `0x90e4d0` (72B), #0 `0x90e880` (72B), #0 `0x90ec30` (72B) |
| **<subst>::__cxx11::basic_ostringstream::<>** （2 槽中 2 个未引用） | #0 `0x91fd80` (121B), #1 `0x91fcf0` (129B) |
| **Multi::LargestSheetSelector** （4 槽中 4 个未引用） | #0 `0x69a710` (1B), #1 `0x69a700` (5B), #2 `0x7d3c50` (136B), #3 `0x7d3ce0` (44B) |
| **<subst>::thread::_State_impl::<<subst>::<subst>::<subst>::shared_ptr::<Engine::Engine>>::<subst>::<subst>** （3 槽中 3 个未引用） | #0 `0x8aad10` (76B), #1 `0x8aacb0` (91B), #2 `0x8aaca0` (15B) |
| **<subst>::__cxx11::messages::<>** （5 槽中 4 个未引用） | #0 `0x921a90` (40B), #0 `0x921c60` (40B), #1 `0x921a60` (48B), #1 `0x921c30` (48B) |
| **Engine::EquivalentObserver** （6 槽中 4 个未引用） | #0 `0x75e130` (71B), #1 `0x75e0e0` (76B), #2 `0x75ddd0` (11B), #3 `0x75dde0` (11B) |
| **Multi::DatabaseNester** （6 槽中 3 个未引用） | #0 `0x5b170` (77B), #1 `0x5b100` (85B), #4 `0x5b0f0` (6B) |
| **Engine::CompositeObserver** （6 槽中 3 个未引用） | #0 `0x75ddc0` (1B), #1 `0x75ddb0` (5B), #3 `0x75cc90` (152B) |
| **<subst>::__cxx11::numpunct::<>** （7 槽中 2 个未引用） | #0 `0x921fd0` (72B), #0 `0x922350` (72B) |
| **<subst>::ios_base::failure** （3 槽中 3 个未引用） | #0 `0x9444e0` (80B), #1 `0x9444c0` (26B), #2 `0x854020` (5B) |
| **<subst>::thread::_State_impl::<NoFitMultiThreadComputer::RunAllComputations>** （3 槽中 3 个未引用） | #0 `0x8aaea0` (15B), #1 `0x8aae70` (36B), #2 `0x8aae30` (56B) |
| **Tiling::CompositePart** （2 槽中 2 个未引用） | #0 `0x76b420` (45B), #1 `0x76b3e0` (53B) |
| **Tiling::DensityEvaluator** （4 槽中 3 个未引用） | #0 `0x76e390` (1B), #1 `0x76e380` (5B), #2 `0x7e8910` (90B) |
| **<subst>::thread::_State_impl::<Engine::Engine>::Structure::Problem** （3 槽中 3 个未引用） | #0 `0x8aadc0` (15B), #1 `0x8aad90` (36B), #2 `0x8aad60` (42B) |
| **<subst>::thread::_State_impl::<Tiling::PackerCache::Implementation::PreUpdateTilings>::<subst>::vector::<<subst>::PartUpdaterInformer>** （3 槽中 3 个未引用） | #0 `0x8aaf10` (15B), #1 `0x8aaee0` (36B), #2 `0x8aaeb0` (39B) |
| **Multi::LimitedNester** （6 槽中 2 个未引用） | #0 `0x695e80` (40B), #1 `0x695e50` (48B) |
| **Multi::SupervisorCanceller** （3 槽中 2 个未引用） | #0 `0x69a6d0` (33B), #1 `0x69a690` (49B) |
| **Tiling::BoxMultiTiler** （5 槽中 3 个未引用） | #0 `0x76b3b0` (33B), #1 `0x76b380` (45B), #4 `0x7e7e80` (3B) |
| **Utils::TimerWinImplementation** （3 槽中 3 个未引用） | #0 `0x6d5970` (1B), #1 `0x6d5960` (5B), #2 `0x6d5910` (67B) |
| **<subst>::thread::_State_impl::<Multi::Supervisor>** （3 槽中 3 个未引用） | #0 `0x8aae20` (15B), #1 `0x8aadf0` (36B), #2 `0x8aadd0` (21B) |
| **<subst>::thread::_State_impl::<<subst>>::<subst>** （3 槽中 3 个未引用） | #0 `0x8aac90` (15B), #1 `0x8aac60` (36B), #2 `0x8aac50` (11B) |
| **Multi::WrapObserver** （3 槽中 2 个未引用） | #0 `0x695df0` (19B), #1 `0x695dc0` (40B) |
| **Multi::CompactCanceller** （3 槽中 2 个未引用） | #0 `0x697130` (19B), #1 `0x697100` (40B) |
| **Structure::ParseSolutionException** （3 槽中 3 个未引用） | #0 `0x7bfe90` (15B), #1 `0x7bfe60` (36B), #2 `0x81ed20` (8B) |
| **Multi::RandomSheetSelector** （4 槽中 3 个未引用） | #0 `0x69a680` (1B), #1 `0x69a670` (5B), #3 `0x7d3c10` (50B) |
| **<subst>::__cxx11::messages_byname::<>** （5 槽中 5 个未引用） | #2 `0x82d120` (3B), #2 `0x82d250` (3B), #3 `0x82d220` (48B), #4 `0x82d130` (1B), #4 `0x82d260` (1B) |
| **Multi::FlipNester** （6 槽中 2 个未引用） | #0 `0x687e10` (15B), #1 `0x687de0` (36B) |
| **Utils::BadResponseException** （3 槽中 2 个未引用） | #0 `0x6d5900` (15B), #1 `0x6d58d0` (36B) |
| **dbg::file_error** （3 槽中 1 个未引用） | #1 `0x679220` (36B) |
| **Tiling::WarpCanceller** （3 槽中 3 个未引用） | #0 `0x76db20` (1B), #1 `0x76db10` (5B), #2 `0x7e80e0` (19B) |
| **Multi::TraceObserver** （6 槽中 3 个未引用） | #0 `0x696c40` (1B), #1 `0x696c30` (5B), #3 `0x7c2470` (3B) |
| **Multi::NestingObserver** （6 槽中 4 个未引用） | #0 `0x6970d0` (1B), #1 `0x6970c0` (5B), #4 `0x7c2490` (1B), #5 `0x7c2480` (1B) |
| **Pack::KnapsackNester** （3 槽中 2 个未引用） | #0 `0x681f90` (1B), #1 `0x681f80` (5B) |
| **Multi::NoFitMapCanceller** （3 槽中 2 个未引用） | #0 `0x69a410` (1B), #1 `0x69a400` (5B) |
| **Multi::RCompactCanceller** （3 槽中 2 个未引用） | #0 `0x69a430` (1B), #1 `0x69a420` (5B) |
| **Multi::AdvancedStrategist** （3 槽中 2 个未引用） | #0 `0x69a470` (1B), #1 `0x69a460` (5B) |
| **Utils::Canceller** （3 槽中 2 个未引用） | #0 `0x6da1e0` (1B), #1 `0x6da1d0` (5B) |
| **Structure::Observer** （6 槽中 2 个未引用） | #0 `0x7c24b0` (1B), #1 `0x7c24a0` (5B) |
| **dbg::symlog** （3 槽中 1 个未引用） | #1 `0x679260` (5B) |
| **RCompact::RotateLogger** （8 槽中 4 个未引用） | #3 `0x7b3060` (1B), #5 `0x7b3010` (1B), #6 `0x7b3050` (1B), #7 `0x7b3040` (1B) |
| **<subst>::locale::facet** （2 槽中 1 个未引用） | #0 `0x8aa8b0` (1B) |

## 每个类的完整方法表（含已引用的槽）

按类的槽序排列；`*` 表示该槽的函数尚未被引用。这也是**策略 `Run` 体所在的位置**（`Multi::NestingNester` / `TilingNester` / `FlipNester` … 的槽 0 即 `Run`）。

* **Pack::RecursiveNester**: #0 `0x683d80` *, #1 `0x681fa0` *, #2 `0x165680` ✓
* **Tiling::MultiOrientedPartPattern**: #0 `0x76f9d0` *, #1 `0x76f9c0` *, #2 `0x7ebb90` *, #3 `0x7eb5e0` *, #4 `0x7ebc30` *, #5 `0x7eb990` *, #6 `0x7ebdb0` *, #7 `0x7ebd90` *
* **Tiling::BiModulePattern**: #0 `0x76db40` *, #1 `0x76db30` *, #2 `0x7e84f0` *, #3 `0x7e8100` *, #4 `0x7e8520` *, #5 `0x7e8150` *, #6 `0x7e8840` *, #7 `0x7e8820` *
* **Tiling::PackerCache**: #0 `0x158be0` *, #1 `0x158f60` *
* **Multi::NoMixSheetSelector**: #0 `0x69a5d0` *, #1 `0x69a580` *, #2 `0x7d2ed0` *, #3 `0x7d33f0` *
* **<subst>::__cxx11::basic_stringbuf::<>**: #0 `0x915ec0` *, #1 `0x915e70` *, #2 `0x88f8c0` *, #3 `0x915040` *, #4 `0x915150` *, #5 `0x915310` *, #6 `0x88f8a0` *, #7 `0x9156e0` *, #8 `0x88fb80` *, #9 `0x915710` *, #10 `0x88f980` *, #11 `0x915680` *, #12 `0x88fc60` *, #13 `0x915480` *
* **Tiling::SqueezeMultiTiler**: #0 `0x76f0a0` *, #1 `0x76ef00` *, #2 `0x7e91a0` ✓, #3 `0x7e9190` *, #4 `0x7e9180` *
* **Tiling::UnlimitedXDensityEvaluator**: #0 `0x76fa10` *, #1 `0x76fa00` *, #2 `0x7ec210` *, #3 `0x4e7e50` ✓
* **Tiling::UnlimitedDensityEvaluator**: #0 `0x76f9f0` *, #1 `0x76f9e0` *, #2 `0x7ebfc0` *, #3 `0x4e7e50` ✓
* **Tiling::ReusableEvaluator**: #0 `0x76e430` *, #1 `0x76e420` *, #2 `0x7e8f60` *, #3 `0x4e7e50` ✓
* **Tiling::Part**: #0 `0x4dafc0` *, #1 `0x4daec0` *
* **Multi::FilterNester**: #0 `0x6937d0` *, #1 `0x6937a0` *, #2 `0xb43b0` *, #3 `0xb3920` *, #4 `0xb46f0` ✓, #5 `0xb3ae0` ✓
* **Multi::CompactNester**: #0 `0x695e40` *, #1 `0x695e10` *, #2 `0xb3890` *, #3 `0xb0130` *, #4 `0xb46f0` ✓, #5 `0xb13d0` ✓
* **Structure::ClusterObserver**: #0 `0x7bc0c0` *, #1 `0x7bc000` *, #2 `0x7c2460` ✓, #3 `0x7c2470` *, #4 `0x5593f0` *, #5 `0x7c2480` *
* **Tiling::QuantityEvaluator**: #0 `0x76e410` *, #1 `0x76e400` *, #2 `0x7e8dd0` *, #3 `0x7e8da0` *
* **Multi::NestingContextPool**: #0 `0x69a500` *, #1 `0x69a480` *, #2 `0x7d2e20` *
* **Structure::SizeDimensioner**: #0 `0x7bc330` *, #1 `0x7bc320` *, #2 `0x81df30` *
* **Multi::RectangleNester**: #0 `0x6d2e0` *, #1 `0x6d3a0` *, #2 `0xb4430` ✓, #3 `0x6c9b0` ✓, #4 `0x77780` ✓, #5 `0x75fb0` ✓
* **Multi::NestingNester**: #0 `0x32ee0` *, #1 `0x32f30` *, #2 `0x3b110` *, #3 `0x33100` *, #4 `0x32d90` *, #5 `0x378e0` ✓
* **Tiling::BasicCandidater**: #0 `0x4f3600` *, #1 `0x4f3610` *, #2 `0x4f4600` *
* **Structure::BoxAreaDimensioner**: #0 `0x7bf060` *, #1 `0x7bf050` *, #2 `0x81e1e0` *
* **Multi::NoFillNester**: #0 `0x693830` *, #1 `0x6937e0` *, #2 `0xb4440` ✓, #3 `0x7eca0` *, #4 `0xb46f0` ✓, #5 `0x7f240` ✓
* **<subst>::__cxx11::basic_stringstream::<>**: #0 `0x91a7c0` *, #1 `0x91a710` *
* **Multi::TilingNester**: #0 `0x456f0` *, #1 `0x45680` *, #2 `0xb4430` ✓, #3 `0x45750` *, #4 `0x45560` *, #5 `0x46940` ✓
* **Multi::PartUpdaterLimiter**: #0 `0x69a640` *, #1 `0x69a630` *, #2 `0x7d3530` *, #3 `0x7d34c0` *
* **Pack::BestNester**: #0 `0x681ee0` *, #1 `0x681e40` *, #2 `0x15e410` ✓
* **Structure::WidthDimensioner**: #0 `0x7befb0` *, #1 `0x7befa0` *, #2 `0x81e0b0` *
* **<subst>::__cxx11::moneypunct::<>**: #0 `0x90e150` *, #1 `0x90e130` *, #2 `0x828a90` *, #3 `0x828b40` *, #4 `0x828850` *, #5 `0x828a30` *, #6 `0x828af0` *, #7 `0x828aa0` *, #8 `0x828a80` *, #9 `0x828910` *, #10 `0x828900` *
* **<subst>::__cxx11::basic_ostringstream::<>**: #0 `0x91fd80` *, #1 `0x91fcf0` *
* **Multi::LargestSheetSelector**: #0 `0x69a710` *, #1 `0x69a700` *, #2 `0x7d3c50` *, #3 `0x7d3ce0` *
* **<subst>::thread::_State_impl::<<subst>::<subst>::<subst>::shared_ptr::<Engine::Engine>>::<subst>::<subst>**: #0 `0x8aad10` *, #1 `0x8aacb0` *, #2 `0x8aaca0` *
* **<subst>::__cxx11::messages::<>**: #0 `0x921a90` *, #1 `0x921a60` *, #2 `0x82d120` *, #3 `0x82d070` *, #4 `0x82d130` *
* **Engine::EquivalentObserver**: #0 `0x75e130` *, #1 `0x75e0e0` *, #2 `0x75ddd0` *, #3 `0x75dde0` *, #4 `0x75e060` ✓, #5 `0x75ddf0` ✓
* **Multi::DatabaseNester**: #0 `0x5b170` *, #1 `0x5b100` *, #2 `0xb4430` ✓, #3 `0x5b1c0` ✓, #4 `0x5b0f0` *, #5 `0x5b250` ✓
* **Engine::CompositeObserver**: #0 `0x75ddc0` *, #1 `0x75ddb0` *, #2 `0x75cbc0` ✓, #3 `0x75cc90` *, #4 `0x75cda0` ✓, #5 `0x75cd30` ✓
* **<subst>::__cxx11::numpunct::<>**: #0 `0x921fd0` *, #1 `0x921fb0` *, #2 `0x82d3c0` *, #3 `0x82d3d0` *, #4 `0x82d270` *, #5 `0x82d2c0` *, #6 `0x82d310` *
* **<subst>::ios_base::failure**: #0 `0x9444e0` *, #1 `0x9444c0` *, #2 `0x854020` *
* **<subst>::thread::_State_impl::<NoFitMultiThreadComputer::RunAllComputations>**: #0 `0x8aaea0` *, #1 `0x8aae70` *, #2 `0x8aae30` *
* **Tiling::CompositePart**: #0 `0x76b420` *, #1 `0x76b3e0` *
* **Tiling::DensityEvaluator**: #0 `0x76e390` *, #1 `0x76e380` *, #2 `0x7e8910` *, #3 `0x4e7e50` ✓
