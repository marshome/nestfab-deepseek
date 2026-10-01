# TU `bucket_manager` -- vocabulary dossier

177 functions / 174273 bytes (cited 26236 = 15.1%)

## strings referenced

| string | referenced by |
|---|---|
| ` / ` | `0x7b3510` `0x7b3d20` `0x7b4880` `0x7b53e0` |
| ` degree=` | `0x655a30` |
| ` nb_buckets=` | `0x655a30` |
| `!infos.state.m_nesting` | `0x235830` |
| `%llu` | `0x7b3510` `0x7b3d20` `0x7b4880` `0x7b53e0` |
| `../utils/evaluated_object.hpp` | `0x23b420` |
| `..\nesting\algos\algo_helpers.hpp` | `0x23b420` |
| `..\nesting\algos\bucket_manager.hpp` | `0x20fe90` `0x212d30` `0x215720` `0x23b420` |
| `AddOrReplaceEquiv` | `0x23b420` |
| `Beam bucket comparisons mode=` | `0x655a30` |
| `Beam try nb : ` | `0x655a30` |
| `Beam width=` | `0x655a30` |
| `BestNodes` | `0x23b420` `0x7b4000` `0x7b4b60` `0x7b56c0` |
| `Buckets : ` | `0x7b3510` `0x7b3d20` `0x7b4880` `0x7b53e0` |
| `Buckets : empty` | `0x7b3510` `0x7b3d20` `0x7b4880` `0x7b53e0` |
| `Can not copy infos` | `0x235830` |
| `ComputeNodeIndex` | `0x81c370` `0x81c690` `0x81c9b0` `0x81ccd0` |
| `EquivCloseV` | `0x7b4440` |
| `EquivGV` | `0x7b4fa0` |
| `EquivS` | `0x7b30d0` `0x7b38e0` `0x7b4440` `0x7b4fa0` |
| `EquivV` | `0x7b30d0` `0x7b38e0` |
| `Grouper prices : ` | `0x20fe90` `0x212d30` `0x215720` |
| `InsertAllNext` | `0x20fe90` `0x212d30` `0x215720` `0x23b420` |
| `Nodes introduced ` | `0x20fe90` `0x212d30` `0x215720` |
| `Visited Nodes=` | `0x1c7980` `0x65dd20` |
| `WVSA` | `0x21d040` |
| `WVSH` | `0x656110` |
| `_beam_tree_` | `0x215720` |
| `basic_string::_M_construct null not valid` | `0x222200` `0x234c60` `0x235830` `0x239910` |
| `basic_string::append` | `0x9926b0` |
| `beam_try_` | `0x655a30` |
| `calls=` | `0x1c7980` `0x65dd20` |
| `eval.m_c == 0` | `0x81c370` `0x81c690` `0x81c9b0` `0x81ccd0` |
| `eval.m_c >= 0 && eval.m_c <= max_surface * 1.05` | `0x81c370` `0x81c690` `0x81c9b0` `0x81ccd0` |
| `first_index < static_cast< int >(m_best.size())` | `0x20fe90` `0x212d30` `0x215720` `0x23b420` |
| `global_pre_` | `0x20fe90` `0x212d30` `0x215720` |
| `inserted` | `0x23b420` |
| `n1.Valid()` | `0x23b420` |
| `n2.Valid()` | `0x23b420` |
| `none` | `0x20fe90` `0x212d30` `0x215720` `0x23b420` |
| `operator+` | `0x23b420` |
| `slices_width.size() > 0` | `0x23b420` `0x7b4000` `0x7b4b60` `0x7b56c0` |
| `static_cast<long long>(pricer.m_prices[p]) >= 0` | `0x222200` |
| `surface_step >= 0` | `0x81c370` `0x81c690` `0x81c9b0` `0x81ccd0` |
| `vector::_M_default_append` | `0x8fc870` `0x8fcf80` `0x8fdb20` `0x8fe420` |
| `vector::_M_range_check: __n (which is %zu) >= this->size() (which is %zu)` | `0x1a6320` `0x20fe90` `0x212d30` `0x215720` |
| `vector::reserve` | `0x1c52d0` `0x8ae450` `0x900ae0` |

## functions (largest first)

| RVA | bytes | callers | confidence | cited | hint |
|---|---:|---:|---|---|---|
| `0x23b420` | 16413 | 2 | direct | yes | ..\nesting\algos\bucket_manager.hpp |
| `0x215720` | 11929 | 8 | direct | - | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x212d30` | 10728 | 2 | direct | - | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x20fe90` | 10648 | 2 | direct | - | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x21d040` | 8462 | 3 | graph-strict | - | WVSA |
| `0x222200` | 8173 | 2 | graph-strict | yes | basic_string::_M_construct null not valid |
| `0x237a00` | 6636 | 2 | graph | - | data@0x9c2200 |
| `0x239e30` | 4684 | 2 | graph-strict | - |  |
| `0x21b7c0` | 4008 | 5 | graph-strict | - | data@0x21b070 |
| `0x236bc0` | 3646 | 4 | graph-strict | - | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x234c60` | 3014 | 4 | graph-strict | - | basic_string::_M_construct null not valid |
| `0x671b60` | 2882 | 2 | graph-strict | - | data@0x9c1b78 |
| `0x182d90` | 2638 | 2 | graph-strict | - | data@0xa55d40 |
| `0x235830` | 2279 | 3 | graph-strict | - | basic_string::_M_construct null not valid |
| `0x963820` | 2222 | 2 | graph-strict | - |  |
| `0x224aa0` | 2082 | 4 | graph-strict | - | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x7b9860` | 2029 | 5 | graph-strict | - | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x1c7980` | 1942 | 5 | graph-strict | - | Visited Nodes= |
| `0x21ca20` | 1559 | 2 | graph-strict | - |  |
| `0x94ca90` | 1512 | 3 | graph-strict | - |  |
| `0x655a30` | 1488 | 5 | graph-strict | - | Beam width= |
| `0x233f50` | 1414 | 8 | graph-strict | - | data@0x9c20d8 |
| `0x22da70` | 1373 | 5 | graph-strict | - | data@0x9c20d0 |
| `0x986cc0` | 1371 | 11 | graph-strict | - |  |
| `0x2393f0` | 1275 | 5 | graph-strict | - |  |
| `0x8fc870` | 1257 | 3 | graph-strict | - | vector::_M_default_append |
| `0x1837e0` | 1130 | 4 | graph-strict | - |  |
| `0x7b30d0` | 1073 | 2 | graph-strict | - | EquivS |
| `0x7b38e0` | 1073 | 2 | graph-strict | - | EquivS |
| `0x7b4000` | 1073 | 2 | direct | - | ..\nesting\algos\bucket_manager.hpp |
| `0x7b4440` | 1073 | 2 | graph-strict | - | EquivS |
| `0x7b4b60` | 1073 | 2 | direct | - | ..\nesting\algos\bucket_manager.hpp |
| `0x7b4fa0` | 1073 | 2 | graph-strict | - | EquivS |
| `0x7b56c0` | 1073 | 2 | direct | - | ..\nesting\algos\bucket_manager.hpp |
| `0x66ffa0` | 996 | 2 | graph-strict | - | data@0xa08340 |
| `0x775fb0` | 994 | 3 | graph-strict | - |  |
| `0x7b3510` | 970 | 2 | graph-strict | - | Buckets : empty |
| `0x180100` | 962 | 11 | graph-strict | - |  |
| `0x21faf0` | 916 | 4 | graph-strict | - |  |
| `0x224560` | 880 | 5 | graph-strict | - | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x8d03e0` | 830 | 2 | graph-strict | - |  |
| `0x1a6320` | 815 | 5 | graph-strict | yes | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x8ae120` | 811 | 3 | graph-strict | - |  |
| `0x1c52d0` | 797 | 2 | graph-strict | - | vector::reserve |
| `0x81c370` | 790 | 2 | direct | - | ..\nesting\algos\bucket_manager.hpp |
| `0x81c690` | 790 | 3 | direct | yes | ..\nesting\algos\bucket_manager.hpp |
| `0x81c9b0` | 790 | 3 | direct | - | ..\nesting\algos\bucket_manager.hpp |
| `0x81ccd0` | 790 | 3 | direct | - | ..\nesting\algos\bucket_manager.hpp |
| `0x8aef00` | 785 | 4 | graph-strict | - |  |
| `0x7b3d20` | 730 | 2 | graph-strict | - | Buckets : empty |
| `0x7b4880` | 730 | 2 | graph-strict | - | Buckets : empty |
| `0x7b53e0` | 730 | 2 | graph-strict | - | Buckets : empty |
| `0x870680` | 727 | 7 | graph-strict | - |  |
| `0x946830` | 715 | 2 | graph-strict | - |  |
| `0x949480` | 691 | 2 | graph-strict | - |  |
| `0x8d0120` | 690 | 2 | graph-strict | - |  |
| `0x1c65b0` | 673 | 3 | graph-strict | - | data@0x7c2460 |
| `0x8b6ac0` | 661 | 3 | graph-strict | - |  |
| `0x8b7200` | 648 | 2 | graph-strict | - |  |
| `0x2209d0` | 630 | 2 | graph-strict | - | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x218810` | 620 | 2 | graph-strict | - |  |
| `0x8ae450` | 592 | 4 | graph-strict | - | vector::reserve |
| `0x7ba1d0` | 590 | 3 | graph-strict | - | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x8d0840` | 581 | 2 | graph-strict | - |  |
| `0x8d0d30` | 581 | 2 | graph-strict | - |  |
| `0x8d1220` | 581 | 2 | graph-strict | - |  |
| `0x1aaca0` | 577 | 4 | graph-strict | - | data@0x9bf538 |
| `0x8d0a90` | 565 | 2 | graph-strict | - |  |
| `0x8d0f80` | 565 | 2 | graph-strict | - |  |
| `0x8d1470` | 565 | 2 | graph-strict | - |  |
| `0x8f2d00` | 554 | 11 | graph-strict | - |  |
| `0x1fd180` | 551 | 6 | graph-strict | - | data@0x9c11e8 |
| `0x16c4c0` | 544 | 5 | graph-strict | - | data@0x9bdb18 |
| `0x1c7780` | 482 | 2 | graph-strict | - | data@0xa082c0 |
| `0x8fcf80` | 469 | 2 | graph-strict | - | vector::_M_default_append |
| `0x21c770` | 462 | 3 | graph-strict | - | data@0xa37490 |
| `0x183c50` | 452 | 2 | graph-strict | - | data@0xa205e0 |
| `0x2248d0` | 449 | 2 | graph-strict | - |  |
| `0x8fdb20` | 437 | 11 | graph-strict | - | vector::_M_default_append |
| `0x8fe420` | 437 | 3 | graph-strict | - | vector::_M_default_append |
| `0x8ff080` | 437 | 2 | graph-strict | - | vector::_M_default_append |
| `0x239c80` | 430 | 2 | graph-strict | - |  |
| `0x81d260` | 423 | 6 | graph-strict | - | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x202590` | 420 | 4 | graph-strict | - |  |
| `0x908200` | 418 | 3 | graph-strict | - |  |
| `0x8aeb30` | 416 | 3 | graph-strict | - |  |
| `0x8aecd0` | 416 | 3 | graph-strict | - |  |
| `0x8b93b0` | 413 | 2 | graph-strict | - |  |
| `0x938b20` | 404 | 2 | graph-strict | - |  |
| `0x95a210` | 404 | 2 | graph-strict | - |  |
| `0x942dd0` | 373 | 3 | graph-strict | - |  |
| `0x93d430` | 373 | 2 | graph-strict | - |  |
| `0x6d5f90` | 364 | 4 | graph-strict | - | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x95a7f0` | 360 | 2 | graph-strict | - |  |
| `0x65dd20` | 356 | 2 | graph-strict | - | Visited Nodes= |
| `0x220230` | 355 | 2 | graph-strict | - | data@0x9c1bf0 |
| `0x906670` | 354 | 2 | graph-strict | - |  |
| `0x1fd6c0` | 343 | 7 | graph-strict | - | data@0x9c11e8 |
| `0x900820` | 342 | 4 | graph-strict | - |  |
| `0x8f7a20` | 337 | 5 | graph-strict | - |  |
| `0x1c3f30` | 324 | 4 | graph-strict | - |  |
| `0x900c00` | 309 | 3 | graph-strict | - |  |
| `0x658250` | 306 | 2 | graph-strict | - |  |
| `0x1fc320` | 306 | 16 | graph-strict | - | data@0xa37220 |
| `0x8fde10` | 292 | 2 | graph-strict | - |  |
| `0x8fdce0` | 290 | 2 | graph-strict | - |  |
| `0x66e830` | 290 | 4 | graph-strict | - |  |
| `0x674360` | 287 | 3 | graph-strict | - |  |
| `0x97eba0` | 282 | 1 | graph-strict | - |  |
| `0x8d0720` | 280 | 2 | graph-strict | - |  |
| `0x900ae0` | 279 | 10 | graph-strict | - | vector::reserve |
| `0x653550` | 276 | 4 | graph-strict | - |  |
| `0x908f60` | 256 | 2 | graph-strict | - |  |
| `0x7bb330` | 251 | 2 | graph-strict | - | data@0xa3a920 |
| `0x8fd3c0` | 232 | 3 | graph-strict | - |  |
| `0x236ad0` | 230 | 4 | graph-strict | - |  |
| `0x938a40` | 224 | 1 | graph-strict | - |  |
| `0x8bb1a0` | 209 | 6 | graph-strict | - |  |
| `0x656110` | 202 | 3 | graph-strict | - | WVSH |
| `0x96d4b0` | 197 | 2 | graph-strict | - |  |
| `0x20cfe0` | 184 | 4 | graph-strict | - |  |
| `0x1c1d40` | 180 | 8 | graph-strict | - |  |
| `0x1c0f50` | 177 | 6 | graph-strict | - | data@0x9bf8f0 |
| `0x239910` | 177 | 4 | graph-strict | - | basic_string::_M_construct null not valid |
| `0x20bfc0` | 177 | 4 | graph-strict | - | data@0x9c13d0 |
| `0x20bec0` | 172 | 4 | graph-strict | - |  |
| `0x6742b0` | 169 | 3 | graph-strict | - |  |
| `0x9926b0` | 159 | 78 | graph | - | basic_string::append |
| `0x20e020` | 157 | 2 | graph-strict | - |  |
| `0x20e0c0` | 157 | 2 | graph-strict | - |  |
| `0x20e160` | 157 | 2 | graph-strict | - |  |
| `0x897100` | 154 | 3 | graph-strict | - |  |
| `0x1be470` | 141 | 7 | graph-strict | - | data@0x9bf8a8 |
| `0x9083b0` | 137 | 4 | graph-strict | - |  |
| `0x8b9550` | 137 | 2 | graph-strict | - |  |
| `0x8ae6a0` | 137 | 4 | graph-strict | - |  |
| `0x234840` | 133 | 3 | graph-strict | - |  |
| `0x992840` | 130 | 9 | graph-strict | - |  |
| `0x8964d0` | 130 | 3 | graph-strict | - |  |
| `0x7602b0` | 123 | 15 | graph-strict | - | data@0xa3aa60 |
| `0x6dd780` | 118 | 5 | graph-strict | - |  |
| `0x86e940` | 115 | 5 | graph-strict | - |  |
| `0x22da00` | 112 | 5 | graph-strict | - | data@0x7c2460 |
| `0x6ddf30` | 107 | 1 | graph-strict | - |  |
| `0x900d40` | 106 | 18 | graph-strict | - |  |
| `0x20c0c0` | 106 | 3 | graph-strict | - |  |
| `0x6de080` | 106 | 3 | graph-strict | - |  |
| `0x6de0f0` | 106 | 3 | graph-strict | - |  |
| `0x7c98a0` | 105 | 3 | graph-strict | - | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x203d40` | 97 | 10 | graph-strict | - |  |
| `0x239a10` | 90 | 3 | graph-strict | - |  |
| `0x20c130` | 90 | 8 | graph-strict | - |  |
| `0x8d0cd0` | 89 | 2 | graph-strict | - |  |
| `0x8d11c0` | 89 | 2 | graph-strict | - |  |
| `0x8d16b0` | 89 | 2 | graph-strict | - |  |
| `0x225a10` | 88 | 1 | graph-strict | - |  |
| `0x8fdf40` | 88 | 3 | graph-strict | - |  |
| `0x8fe5e0` | 88 | 3 | graph-strict | - |  |
| `0x906950` | 88 | 2 | graph-strict | - |  |
| `0x8ff240` | 88 | 5 | graph-strict | - |  |
| `0x65cac0` | 86 | 3 | graph-strict | - | data@0xa37290 |
| `0x1c10b0` | 84 | 2 | graph-strict | - | data@0x9bf91b |
| `0x21f9f0` | 80 | 3 | graph-strict | - | data@0x9c1bf0 |
| `0x1a6650` | 66 | 5 | graph-strict | - |  |
| `0x21fab0` | 59 | 2 | graph-strict | - | data@0x9c1bf0 |
| `0x219690` | 57 | 3 | graph-strict | - | data@0xa37290 |
| `0x8704d0` | 40 | 3 | graph-strict | - |  |
| `0x16c6e0` | 33 | 4 | graph-strict | yes | data@0x9a2470 |
| `0x170900` | 27 | 11 | graph-strict | - |  |
| `0x2348e0` | 27 | 1 | graph-strict | - |  |
| `0x1c12b0` | 22 | 3 | graph-strict | - |  |
| `0x200c90` | 21 | 2 | graph-strict | - |  |
| `0x22d9e0` | 19 | 4 | graph-strict | - |  |
| `0x21fa90` | 13 | 1 | graph-strict | - |  |
| `0x1c1650` | 12 | 6 | graph-strict | yes |  |
| `0x21f9d0` | 10 | 3 | graph-strict | - |  |
| `0x17ff30` | 4 | 5 | graph-strict | - |  |
