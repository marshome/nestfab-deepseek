# 原工程 TU 地图（由断言路径 + 虚表类名 + 调用图传播重建）

二进制把 `..\dir\file.cpp` 烧进断言串；但断言串在**独立的消息构造器**里，
所以只有少数函数自带路径。本表用三级标注把它铺满可达集：

1. **direct** —— 函数自己引用了 `..\dir\file.cpp`
2. **vtable** —— 函数是某个 vtable 的 slot，而其 demangle 类名可映射到 TU
3. **graph** —— 调用图标签传播（多数已标注邻居一致时赋值）

- 可达 **6181** 个 / 4670042 字节；已归位 **4163** 个 / 69.5% 字节
- 自有 TU：**49** 个 / 2977830 字节，其中**已引用 561663 字节 = 18.9%**
- 第三方 TU：6 个 / 265935 字节（按已分类处理，不列入待逆向）
- 仍无标签：**2025** 个 / **1426277** 字节（需逐个按调用者/字符串反推）

## 自有 TU：待逆向字节降序

| 原 TU | 函数数 | 字节 | 已引用 | 未引用 | 进度 |
|---|---:|---:|---:|---:|---:|
| `..\tiling\packer_cache.cpp` | 273 | 274948 | 35982 | **238966** | 13% |
| `..\multi\nesting_context.cpp` | 270 | 205881 | 20248 | **185633** | 10% |
| `..\engine\cloud_engine.cpp` | 566 | 252728 | 82190 | **170538** | 33% |
| `..\structure\svg_io.cpp` | 236 | 239605 | 70927 | **168678** | 30% |
| `..\structure\border_property.hpp` | 332 | 199302 | 33203 | **166099** | 17% |
| `..\nesting\algos\bucket_manager.hpp` | 167 | 157150 | 26236 | **130914** | 17% |
| `..\tiling\packer.cpp` | 105 | 119483 | 8242 | **111241** | 7% |
| `..\verify\equivalent.cpp` | 177 | 140629 | 34795 | **105834** | 25% |
| `..\structure\problem.cpp` | 124 | 103521 | 10325 | **93196** | 10% |
| `..\multi\rectangle_nester.cpp` | 105 | 99266 | 9014 | **90252** | 9% |
| `..\exact\relinker_internal.cpp` | 65 | 82005 | 196 | **81809** | 0% |
| `..\nesting\algos\compact.hpp` | 87 | 96219 | 15993 | **80226** | 17% |
| `..\multi\row_nester.cpp` | 120 | 102779 | 25586 | **77193** | 25% |
| `..\nesting\algos\algo_parameters.cpp` | 102 | 75592 | 0 | **75592** | 0% |
| `..\structure\text_io.cpp` | 125 | 66361 | 6383 | **59978** | 10% |
| `..\tiling\optimizer.cpp` | 48 | 53229 | 0 | **53229** | 0% |
| `..\exact\geom_conversion.inl` | 72 | 69044 | 21970 | **47074** | 32% |
| `..\multi\tiling_nester.cpp` | 47 | 63011 | 16821 | **46190** | 27% |
| `..\nesting\algos\multinesting_optimizer.cpp` | 81 | 52533 | 7564 | **44969** | 14% |
| `..\multi\marker.cpp` | 28 | 42036 | 0 | **42036** | 0% |
| `..\structure\automatic_cluster.cpp` | 59 | 41447 | 0 | **41447** | 0% |
| `..\nesting\algos\tree_db.cpp` | 79 | 41745 | 7743 | **34002** | 19% |
| `..\multi\database.cpp` | 21 | 46244 | 13057 | **33187** | 28% |
| `..\nesting\algos\..\nesting.hpp` | 37 | 29134 | 33 | **29101** | 0% |
| `..\structure\stats.cpp` | 55 | 33364 | 6473 | **26891** | 19% |
| `..\nesting\structure_interface_private.hpp` | 47 | 28590 | 2167 | **26423** | 8% |
| `..\structure\multitorch_eval.cpp` | 36 | 26305 | 2048 | **24257** | 8% |
| `..\multi\float_filler.cpp` | 11 | 19904 | 0 | **19904** | 0% |
| `..\utils\evaluated_object.hpp` | 28 | 14927 | 0 | **14927** | 0% |
| `..\multi\multitorch_nester.cpp` | 16 | 26939 | 12514 | **14425** | 46% |
| `..\nesting\algos\postop.cpp` | 22 | 27302 | 13234 | **14068** | 48% |
| `..\engine\engine.cpp` | 18 | 37510 | 26241 | **11269** | 70% |
| `..\multi\pack_nester.cpp` | 12 | 11321 | 500 | **10821** | 4% |
| `..\nesting\ios\log_ios.cpp` | 10 | 5551 | 0 | **5551** | 0% |
| `..\nesting\algos\algo_helpers.hpp` | 5 | 5459 | 0 | **5459** | 0% |
| `..\structure\part.cpp` | 25 | 6683 | 1821 | **4862** | 27% |
| `..\multi\database_nester.cpp` | 22 | 9309 | 4532 | **4777** | 49% |
| `..\structure\sheet.cpp` | 16 | 4701 | 0 | **4701** | 0% |
| `..\utils\continuous_index_map.hpp` | 7 | 4657 | 0 | **4657** | 0% |
| `..\multi\nesting_nester.cpp` | 19 | 18848 | 14374 | **4474** | 76% |
| `..\multi\supervisor.cpp` | 13 | 7187 | 3299 | **3888** | 46% |
| `..\nesting\algos\sheet_optimizer.cpp` | 6 | 2903 | 0 | **2903** | 0% |
| `..\nesting\nesting.cpp` | 17 | 6172 | 4904 | **1268** | 79% |
| `..\nesting\algos\tree_db.hpp` | 3 | 1255 | 0 | **1255** | 0% |
| `..\multi\limited_nester.cpp` | 6 | 2773 | 2001 | **772** | 72% |
| `..\multi\compact_nester.cpp` | 11 | 14137 | 13560 | **577** | 96% |
| `..\multi\filter_nester.cpp` | 6 | 3638 | 3148 | **490** | 87% |
| `..\nesting\algos\no_fit.cpp` | 5 | 113 | 0 | **113** | 0% |
| `..\multi\flip_nester.cpp` | 7 | 4390 | 4339 | **51** | 99% |

## 第三方 TU（已分类）

| TU | 函数数 | 字节 |
|---|---:|---:|
| `Users\renaud\nest\external\boost_1_63_0\boost\uuid\sha1.hpp` | 304 | 106830 |
| `Users\renaud\nest\external\boost_1_63_0\boost\multiprecision\rational_adaptor.hpp` | 61 | 98554 |
| `Users\renaud\nest\external\boost_1_63_0\boost\rational.hpp` | 24 | 52305 |
| `Users\renaud\nest\external\boost_1_63_0\boost\multiprecision\cpp_int\divide.hpp` | 8 | 6038 |
| `Users\renaud\nest\external\boost_1_63_0\boost\multiprecision\cpp_int\checked.hpp` | 9 | 1555 |
| `..\nesting\algos\..\strips\strip_position.hpp` | 1 | 653 |

## 仍无标签的最大 80 个（优先处理，逐个反推）

| RVA | 字节 | 调用者 | 线索 |
|---|---:|---:|---|
| `0x243820` | 15524 | 4 | vector::_M_range_check: __n (which is %zu) >= this->size() (whic |
| `0x1e3aa0` | 15380 | 2 | data@0x88dc80 |
| `0x9ed20` | 13360 | 2 | basic_string::_M_construct null not valid |
| `0x94d080` | 12939 | 3 | data@0x88dc80 |
| `0x1e76c0` | 12889 | 2 | res.nb_fillers >= 0 |
| `0x2306c0` | 12553 | 4 | vector::_M_range_check: __n (which is %zu) >= this->size() (whic |
| `0x4c5450` | 12535 | 4 | basic_string::_M_construct null not valid |
| `0x73280` | 11567 | 5 | vector::_M_range_check: __n (which is %zu) >= this->size() (whic |
| `0x1ce1c0` | 11183 | 2 | data@0x9c0238 |
| `0x53f910` | 11110 | 2 | vector::_M_range_check: __n (which is %zu) >= this->size() (whic |
| `0x59e9d0` | 10198 | 2 | data@0x9ddb10 |
| `0x1b33b0` | 9910 | 4 | vector::_M_range_check: __n (which is %zu) >= this->size() (whic |
| `0x535c60` | 9499 | 4 | data@0x9dbcb0 |
| `0x1b0f70` | 9274 | 2 | vector::_M_range_check: __n (which is %zu) >= this->size() (whic |
| `0x946b00` | 9029 | 2 | data@0x88dc80 |
| `0x9640d0` | 9021 | 3 | data@0x88dc80 |
| `0x67460` | 8995 | 3 | basic_string::_M_construct null not valid |
| `0x983e30` | 8990 | 4 | data@0x88dc80 |
| `0x674680` | 8881 | 2 | data@0x9ac818 |
| `0x987c50` | 8874 | 2 | data@0x88dc80 |
| `0x511080` | 8750 | 3 | &nbsp;&nbsp;&nbsp;&nbsp; |
| `0x7f240` | 8440 | 1 | basic_string::append |
| `0x6e6120` | 8168 | 18 | data@0xa57e80 |
| `0x74d8a0` | 8056 | 5 |  |
| `0x7e6010` | 7777 | 2 | Px\| |
| `0x5070e0` | 7663 | 7 | geometry |
| `0x7e9580` | 7580 | 3 | data@0x9da280 |
| `0x2403a0` | 7543 | 3 | vector::_M_range_check: __n (which is %zu) >= this->size() (whic |
| `0x8a2c90` | 7436 | 2 |  |
| `0x1d53a0` | 7403 | 3 | basic_string::_M_construct null not valid |
| `0xa85d0` | 7292 | 2 | basic_string::_M_construct null not valid |
| `0xa6950` | 7292 | 2 | basic_string::_M_construct null not valid |
| `0x248550` | 7274 | 2 | data@0x7b3020 |
| `0x760d90` | 7023 | 2 | data@0x9da2d0 |
| `0x6673f0` | 6952 | 2 | data@0x9ac818 |
| `0x7d5790` | 6754 | 3 | data@0x88dc80 |
| `0x344d0` | 6748 | 3 | data@0x88dc80 |
| `0x237a00` | 6636 | 2 | data@0x9c2200 |
| `0x17c790` | 6634 | 3 | AVAUATUWVSH |
| `0x8a5980` | 6582 | 2 |  |
| `0x35f30` | 6436 | 3 | vector::_M_range_check: __n (which is %zu) >= this->size() (whic |
| `0x982410` | 6194 | 2 |  |
| `0x976800` | 6159 | 2 |  |
| `0x550a80` | 6056 | 3 |  |
| `0x949740` | 5930 | 2 | data@0x88dc80 |
| `0x50c60` | 5785 | 6 | data@0x88dc80 |
| `0x6aabc0` | 5763 | 2 | data@0x9b1a40 |
| `0x1ec0b0` | 5758 | 4 | basic_string::_M_construct null not valid |
| `0x4ec00` | 5633 | 3 | nb_strips_first |
| `0x827f0` | 5274 | 4 | data@0x88dc80 |
| `0x1c9c80` | 5243 | 2 | basic_string::_M_construct null not valid |
| `0x5d830` | 5167 | 3 | data@0x9b0900 |
| `0x4e5d30` | 5147 | 3 | data@0x9d9e38 |
| `0x5a11b0` | 4990 | 3 |  |
| `0x54e270` | 4954 | 4 | data@0x9dc0a0 |
| `0x56e6b0` | 4827 | 2 | data@0x88dc80 |
| `0x97c670` | 4801 | 2 |  |
| `0x653670` | 4698 | 2 | basic_string::append |
| `0x1eec00` | 4688 | 3 | vector::_M_range_check: __n (which is %zu) >= this->size() (whic |
| `0x76c8d0` | 4669 | 3 | basic_string::_M_construct null not valid |
| `0xcca70` | 4614 | 1 |  |
| `0x688fa0` | 4604 | 2 | %lld |
| `0x698f10` | 4599 | 3 | data@0x9b1df0 |
| `0x96e520` | 4578 | 3 | data@0x88dc80 |
| `0x676940` | 4527 | 2 | data@0x9ae228 |
| `0x687e20` | 4478 | 2 | AUATUWVSH |
| `0x6548d0` | 4447 | 4 | %llu |
| `0x5f2790` | 4440 | 2 | data@0x9dfe60 |
| `0x98a7d0` | 4430 | 2 |  |
| `0x25b040` | 4303 | 5 | data@0x9c2bf0 |
| `0x1f0b80` | 4253 | 2 | /home/nicolas/tmp/bug |
| `0x67dc00` | 4249 | 8 | data@0x9dfbd8 |
| `0x726550` | 4232 | 2 | data@0x9dfbd8 |
| `0x1f4ba0` | 4221 | 5 | vector::_M_range_check: __n (which is %zu) >= this->size() (whic |
| `0x52e7e0` | 4135 | 6 | basic_string::_M_construct null not valid |
| `0x170bb0` | 4119 | 3 | VSH |
| `0x773eb0` | 4081 | 2 | data@0x9c2dc0 |
| `0x5ee1a0` | 4039 | 3 | data@0x9dfdc8 |
| `0x730300` | 4025 | 5 |  |
| `0x21b7c0` | 4008 | 5 | data@0x21b070 |
