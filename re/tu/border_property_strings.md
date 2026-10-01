# TU `border_property` -- vocabulary dossier

196 functions / 132394 bytes (cited 34152 = 25.8%)

## strings referenced

| string | referenced by |
|---|---|
| `!elements.empty()` | `0x22e40` |
| `%s: __pos (which is %zu) > this->size() (which is %zu)` | `0xb8210` |
| `-> ` | `0x64f850` |
| `../structure/border_property.hpp` | `0x1c980` `0x1ee50` `0x7bf0c0` |
| `..\structure\border_property.hpp` | `0x7bc180` |
| `ArcToPoints` | `0x22e40` |
| `CNS informations` | `0x7bb430` |
| `CNS_NoFitContext` | `0x668f20` |
| `CheckAddElements invalid ` | `0x22e40` |
| `ComputeNoHoleRings` | `0x1e900` |
| `ComputeSheetGeometryRowMode` | `0x1ee50` |
| `CreateProblem` | `0x1ee50` |
| `DeleteNoFitContext` | `0x9cc0` |
| `GetCommonCutProperties` | `0x1ee50` |
| `GetLayerLeatherPart` | `0x1c980` `0x7bf0c0` |
| `GetLayerLeatherSheet` | `0x1c980` `0x1ee50` |
| `GetLayerRestrictedZonePart` | `0x1c980` `0x1ee50` |
| `GetLayerRestrictedZoneSheet` | `0x1c980` `0x1ee50` |
| `GetLeatherLayer` | `0x7bc180` |
| `GetMultitorchProperties` | `0x1ee50` |
| `IsLeather(p)` | `0x7bc180` |
| `VSH` | `0x6eaf20` |
| `a2U0*` | `0x19fe90` |
| `all_settings.find(order.common_cut_safety_preference) != all_settings.end()` | `0x1ee50` |
| `basic_string::_M_construct null not valid` | `0x1b070` `0xb8210` |
| `basic_string::substr` | `0xb8210` |
| `boost.find(order.multitorch_cutting_preference) != boost.end()` | `0x1ee50` |
| `cns_no_fit.cpp` | `0x668f20` |
| `external_rings.size() == 1u` | `0x1ee50` |
| `internal.cpp` | `0x1e900` `0x1ee50` `0x22e40` |
| `m_equivalent_problem->GetNumberOfParts() == order->parts.size()` | `0x668f20` |
| `m_equivalent_problem->GetNumberOfSheets() == order->sheets.size()` | `0x668f20` |
| `poly.inners().empty()` | `0x1e900` |
| `quality >= 0 && quality < 100` | `0x1c980` `0x1ee50` |
| `quality >= 0 && quality < 9` | `0x1c980` `0x1ee50` `0x7bf0c0` |
| `structure_sheet` | `0x1ee50` |
| `vector::_M_default_append` | `0x8b7ba0` |
| `vector::_M_fill_insert` | `0x8b7700` |
| `vector::_M_range_check: __n (which is %zu) >= this->size() (which is %zu)` | `0x1ee50` |
| `vector::_M_range_insert` | `0x8c1920` `0x8c2e10` |
| `vector::reserve` | `0x174be0` `0x175fb0` `0x176a60` `0x19fe90` |

## functions (largest first)

| RVA | bytes | callers | confidence | cited | hint |
|---|---:|---:|---|---|---|
| `0x1ee50` | 15305 | 7 | direct | yes | quality >= 0 && quality < 9 |
| `0x676940` | 4527 | 2 | graph | - | data@0x9ae228 |
| `0x176a60` | 3764 | 2 | graph-strict | - | vector::reserve |
| `0x174be0` | 3710 | 3 | graph-strict | - | vector::reserve |
| `0x86d9e0` | 3624 | 2 | graph-strict | - | data@0xa08320 |
| `0x22e40` | 3494 | 2 | graph-strict | - | internal.cpp |
| `0x206690` | 3137 | 5 | graph-strict | - |  |
| `0x5873e0` | 2784 | 3 | graph-strict | yes |  |
| `0x8ac620` | 2756 | 2 | graph-strict | - |  |
| `0x175fb0` | 2734 | 2 | graph-strict | - | vector::reserve |
| `0x668f20` | 2631 | 2 | graph-strict | yes | cns_no_fit.cpp |
| `0x2098f0` | 2606 | 3 | graph-strict | - | vector::reserve |
| `0x19fe90` | 2374 | 3 | graph-strict | - | vector::reserve |
| `0x1c980` | 2347 | 2 | direct | yes | quality >= 0 && quality < 9 |
| `0x874490` | 2208 | 2 | graph-strict | - |  |
| `0x20b610` | 2059 | 3 | graph | - | data@0x9c13c0 |
| `0x135c70` | 1748 | 2 | graph-strict | yes |  |
| `0x76d0` | 1495 | 4 | graph-strict | yes |  |
| `0x8f9220` | 1462 | 3 | graph-strict | yes |  |
| `0x2072f0` | 1446 | 4 | graph-strict | - |  |
| `0x1fd820` | 1443 | 2 | graph-strict | - | data@0xa08320 |
| `0x5d2a60` | 1253 | 3 | graph-strict | - |  |
| `0x93e2c0` | 1252 | 2 | graph-strict | - |  |
| `0x57bd20` | 1217 | 2 | graph-strict | - |  |
| `0x19f1f0` | 1168 | 2 | graph-strict | - | data@0x9be4f0 |
| `0x870070` | 1106 | 2 | graph-strict | - |  |
| `0x19f8f0` | 1057 | 2 | graph-strict | - | data@0x9be4f0 |
| `0x22a20` | 1037 | 2 | graph-strict | yes | data@0x9adf72 |
| `0x202aa0` | 1017 | 3 | graph-strict | - | vector::reserve |
| `0x1e480` | 1007 | 4 | graph-strict | - | data@0x9ae228 |
| `0x8c2380` | 986 | 6 | graph-strict | - |  |
| `0x8b7700` | 974 | 7 | graph-strict | - | vector::_M_fill_insert |
| `0x57c540` | 970 | 3 | graph-strict | - |  |
| `0x205a30` | 938 | 3 | graph-strict | - | vector::reserve |
| `0x57b3d0` | 931 | 2 | graph-strict | - | data@0x9dc620 |
| `0x174860` | 888 | 2 | graph-strict | yes | data@0x9bdc70 |
| `0x1e900` | 887 | 2 | graph-strict | - | internal.cpp |
| `0x128e0` | 883 | 2 | graph-strict | yes | data@0x9ad6e0 |
| `0x57d3f0` | 869 | 2 | graph-strict | - |  |
| `0x57af60` | 841 | 3 | graph-strict | - | data@0x9dc620 |
| `0x8d1980` | 829 | 3 | graph-strict | - |  |
| `0x86cd60` | 779 | 2 | graph-strict | - |  |
| `0x8c2e10` | 772 | 6 | graph-strict | - | vector::_M_range_insert |
| `0x57c910` | 770 | 2 | graph-strict | - |  |
| `0x8c1920` | 754 | 2 | graph-strict | - | vector::_M_range_insert |
| `0x57ce80` | 728 | 3 | graph-strict | - | data@0x9dc650 |
| `0xb8210` | 727 | 3 | graph-strict | - | basic_string::substr |
| `0x8d1cc0` | 690 | 3 | graph-strict | - | data@0x9dc610 |
| `0x203ab0` | 656 | 8 | graph-strict | - |  |
| `0x20b390` | 637 | 2 | graph-strict | - | vector::reserve |
| `0x57c1f0` | 633 | 2 | graph-strict | - | vector::reserve |
| `0x19f680` | 620 | 2 | graph-strict | - |  |
| `0x19dfe0` | 613 | 2 | graph-strict | - |  |
| `0x8b8f30` | 609 | 2 | graph-strict | - |  |
| `0x8c1e30` | 609 | 10 | graph-strict | - |  |
| `0x86c740` | 603 | 2 | graph-strict | - |  |
| `0x1fe4e0` | 590 | 4 | graph-strict | - |  |
| `0x57cc20` | 588 | 3 | graph-strict | - |  |
| `0x5c5970` | 571 | 4 | graph-strict | yes |  |
| `0x9cc0` | 568 | 0 | graph-strict | yes | DeleteNoFitContext |
| `0x8ad9c0` | 563 | 6 | graph-strict | - |  |
| `0x54cc00` | 552 | 2 | graph-strict | - |  |
| `0x54cea0` | 552 | 3 | graph-strict | - |  |
| `0x202ea0` | 531 | 2 | graph-strict | - |  |
| `0x5d1f70` | 521 | 2 | graph-strict | - |  |
| `0x89ed70` | 510 | 5 | graph-strict | - |  |
| `0x7bb430` | 495 | 2 | graph-strict | yes | CNS informations |
| `0x89b5c0` | 491 | 2 | graph-strict | - |  |
| `0x96f710` | 478 | 8 | graph-strict | - |  |
| `0x86d430` | 473 | 2 | graph-strict | - |  |
| `0x6d3070` | 463 | 4 | graph-strict | - |  |
| `0x209610` | 457 | 2 | graph-strict | - |  |
| `0x1ec80` | 457 | 2 | graph-strict | - | data@0x9ae228 |
| `0x8adc00` | 448 | 8 | graph-strict | - | vector::reserve |
| `0x95b7a0` | 445 | 2 | graph-strict | - |  |
| `0x57bb00` | 443 | 2 | graph-strict | - | data@0x9dc640 |
| `0x57d160` | 442 | 2 | graph-strict | - |  |
| `0x4f3650` | 439 | 2 | graph-strict | - | data@0x9da258 |
| `0x86cad0` | 426 | 3 | graph-strict | - |  |
| `0x86d1a0` | 426 | 3 | graph-strict | - |  |
| `0x86d740` | 426 | 3 | graph-strict | - |  |
| `0x8b91a0` | 418 | 3 | graph-strict | - |  |
| `0x7bc180` | 413 | 2 | direct | - | ..\structure\border_property.hpp |
| `0x9314f0` | 408 | 2 | graph-strict | - |  |
| `0x931690` | 408 | 3 | graph-strict | yes |  |
| `0x931c00` | 408 | 3 | graph-strict | yes |  |
| `0x932b80` | 408 | 2 | graph-strict | - |  |
| `0x923110` | 408 | 2 | graph-strict | - |  |
| `0x923480` | 408 | 2 | graph-strict | - |  |
| `0x9237f0` | 408 | 2 | graph-strict | - |  |
| `0x1e140` | 408 | 3 | graph-strict | - |  |
| `0x1e2e0` | 408 | 3 | graph-strict | - |  |
| `0x89a740` | 405 | 1 | graph-strict | yes |  |
| `0x8f8a80` | 401 | 3 | graph-strict | - |  |
| `0x8e0b90` | 401 | 2 | graph-strict | - |  |
| `0x8e0e70` | 385 | 3 | graph-strict | - |  |
| `0x4f3de0` | 382 | 4 | graph-strict | - |  |
| `0x8b7ba0` | 378 | 8 | graph-strict | - | vector::_M_default_append |
| `0x1a07e0` | 350 | 2 | graph-strict | - | data@0xa07760 |
| `0x64f850` | 350 | 2 | graph-strict | - | ->  |
| `0x677af0` | 350 | 1 | graph-strict | - |  |
| `0x6f2e30` | 347 | 5 | graph-strict | - | data@0xb28994 |
| `0x8e6dd0` | 339 | 2 | graph-strict | - |  |
| `0x170760` | 338 | 3 | graph-strict | - |  |
| `0x19fd30` | 338 | 2 | graph-strict | - |  |
| `0x8c20a0` | 330 | 2 | graph-strict | - |  |
| `0x8b7f20` | 328 | 4 | graph-strict | - |  |
| `0x8e0d30` | 305 | 3 | graph-strict | - |  |
| `0x897400` | 301 | 2 | graph-strict | - |  |
| `0x8c21f0` | 300 | 5 | graph-strict | - |  |
| `0x951110` | 297 | 2 | graph-strict | - |  |
| `0x96d7f0` | 292 | 2 | graph-strict | - |  |
| `0x897650` | 292 | 1 | graph-strict | - |  |
| `0x9313d0` | 288 | 2 | graph-strict | - |  |
| `0x932a60` | 288 | 2 | graph-strict | - |  |
| `0x922ff0` | 288 | 2 | graph-strict | - |  |
| `0x923360` | 288 | 2 | graph-strict | - |  |
| `0x9236d0` | 288 | 2 | graph-strict | - |  |
| `0x93e1a0` | 288 | 3 | graph-strict | - |  |
| `0x1b690` | 268 | 4 | graph-strict | - |  |
| `0x1a3560` | 266 | 1 | graph-strict | - | data@0xa205e0 |
| `0x7bf0c0` | 266 | 2 | direct | yes | quality >= 0 && quality < 9 |
| `0x98e0a0` | 260 | 8 | graph-strict | - |  |
| `0x908e60` | 253 | 3 | graph-strict | - |  |
| `0x6eaf20` | 253 | 2 | graph-strict | - | VSH |
| `0x5c5ff0` | 253 | 11 | graph-strict | - |  |
| `0x8b7d20` | 253 | 10 | graph-strict | - |  |
| `0x8b7e20` | 253 | 5 | graph-strict | - |  |
| `0x90d790` | 209 | 25 | graph | - |  |
| `0x1b840` | 203 | 2 | graph-strict | - | data@0x9ae1d0 |
| `0x1e010` | 192 | 3 | graph-strict | - |  |
| `0x57c470` | 191 | 1 | graph-strict | - |  |
| `0x932780` | 188 | 4 | graph-strict | - |  |
| `0x9328f0` | 188 | 4 | graph-strict | - |  |
| `0x8c3730` | 178 | 12 | graph-strict | - |  |
| `0x1b070` | 177 | 9 | graph-strict | - | basic_string::_M_construct null not valid |
| `0x203db0` | 175 | 3 | graph-strict | - |  |
| `0x931320` | 169 | 2 | graph-strict | - |  |
| `0x9326d0` | 169 | 2 | graph-strict | - |  |
| `0x932840` | 169 | 2 | graph-strict | - |  |
| `0x9329b0` | 169 | 2 | graph-strict | - |  |
| `0x922f40` | 169 | 2 | graph-strict | - |  |
| `0x9232b0` | 169 | 2 | graph-strict | - |  |
| `0x923620` | 169 | 2 | graph-strict | - |  |
| `0x93e0f0` | 169 | 2 | graph-strict | - |  |
| `0x1c540` | 168 | 1 | graph-strict | yes |  |
| `0x870f70` | 155 | 5 | graph-strict | - |  |
| `0x1bb10` | 150 | 1 | graph-strict | - |  |
| `0x57b340` | 139 | 1 | graph-strict | - |  |
| `0x1e870` | 138 | 3 | graph-strict | - | data@0x9ae228 |
| `0x5cc6a0` | 135 | 8 | graph-strict | yes | data@0x9de910 |
| `0x54e1f0` | 123 | 2 | graph-strict | - |  |
| `0x897ff0` | 123 | 3 | graph-strict | - |  |
| `0x82a270` | 122 | 6 | graph-strict | - |  |
| `0x207930` | 118 | 1 | graph-strict | - |  |
| `0x1e0d0` | 104 | 2 | graph-strict | - |  |
| `0x873a50` | 93 | 3 | graph-strict | - |  |
| `0x8d1920` | 92 | 2 | graph-strict | - |  |
| `0x8d1f80` | 89 | 2 | graph-strict | - |  |
| `0x8b9350` | 88 | 6 | graph-strict | - |  |
| `0x8c2320` | 88 | 17 | graph-strict | - |  |
| `0x65deb0` | 86 | 3 | graph-strict | - |  |
| `0x1b170` | 80 | 2 | graph-strict | - |  |
| `0x20b2d0` | 79 | 1 | graph-strict | - |  |
| `0x861a30` | 74 | 105 | graph-strict | yes |  |
| `0x89f760` | 66 | 2 | graph-strict | - |  |
| `0x1a1e30` | 65 | 7 | graph-strict | yes | data@0x9a2480 |
| `0x5ee110` | 62 | 2 | graph-strict | - | data@0x9dfd30 |
| `0x5ee150` | 62 | 2 | graph-strict | - | data@0x9dfd30 |
| `0x1b130` | 60 | 7 | graph-strict | - |  |
| `0x6561e0` | 54 | 10 | graph-strict | - |  |
| `0x656220` | 54 | 3 | graph-strict | - |  |
| `0x898780` | 44 | 1 | graph-strict | - | data@0xa205e0 |
| `0x898a80` | 44 | 1 | graph-strict | - | data@0xa205e0 |
| `0x8991c0` | 44 | 1 | graph-strict | - | data@0xa205e0 |
| `0x899690` | 44 | 1 | graph-strict | - | data@0xa205e0 |
| `0x899710` | 44 | 1 | graph-strict | - | data@0xa205e0 |
| `0x8997d0` | 44 | 1 | graph-strict | - | data@0xa205e0 |
| `0x57d8f0` | 44 | 4 | graph-strict | - |  |
| `0x52f980` | 37 | 1 | graph-strict | - |  |
| `0x52f9e0` | 37 | 1 | graph-strict | - |  |
| `0x52fa10` | 37 | 1 | graph-strict | - |  |
| `0x52fa70` | 37 | 1 | graph-strict | - |  |
| `0x52faa0` | 37 | 1 | graph-strict | - |  |
| `0x57d760` | 18 | 2 | graph-strict | - |  |
| `0x549ab0` | 13 | 1 | graph-strict | - |  |
| `0x4fbe60` | 12 | 3 | graph-strict | - |  |
| `0x4f8d20` | 9 | 2 | graph-strict | - |  |
| `0x22e30` | 9 | 2 | graph-strict | yes |  |
| `0x895f80` | 8 | 1 | graph-strict | - |  |
| `0x4f9c20` | 6 | 2 | graph-strict | - |  |
| `0x4f7340` | 6 | 2 | graph-strict | - |  |
| `0x895f90` | 5 | 7 | graph-strict | - |  |
| `0x52f8d0` | 4 | 2 | graph-strict | - |  |
| `0x52f8e0` | 4 | 2 | graph-strict | - |  |
| `0x54d110` | 3 | 2 | graph-strict | - |  |
