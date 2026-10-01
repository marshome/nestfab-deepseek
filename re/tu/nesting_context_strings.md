# TU `nesting_context` -- vocabulary dossier

135 functions / 114670 bytes (cited 17849 = 15.6%)

## strings referenced

| string | referenced by |
|---|---|
| ` != ` | `0x191e80` `0x193420` |
| ` parts.` | `0x40720` |
| `!IsCluster(p)` | `0x7d3e50` |
| `!box.empty()` | `0x40720` |
| `!layers.front().empty()` | `0x3c9e0` |
| `(assert_aux1 == assert_aux2)` | `0x191e80` `0x193420` |
| `(problem.part_gap() == 0.0) && "part gap not supported"` | `0x69aa40` |
| `..\multi\nesting_context.cpp` | `0x3b2f0` `0x3b5f0` `0x3bcc0` `0x3c3f0` |
| `ComputeGroups` | `0x40070` |
| `ComputeRealNestingWindow` | `0x3b2f0` |
| `ComputeSheetLayers` | `0x3c9e0` |
| `Default` | `0x696c50` |
| `FillNesting` | `0x434d0` |
| `FillNestingAux` | `0x41920` |
| `FromNesting` | `0x40070` |
| `GetCluster` | `0x69a720` |
| `GetNestingPart` | `0x3dbe0` `0x3f070` |
| `GetStructureModule` | `0x7d3e50` |
| `GetTypicalLength` | `0x3b5f0` |
| `Implementation` | `0x696c50` |
| `IsCluster` | `0x7d4050` |
| `NestedQuantities` | `0x3bcc0` |
| `NestingPartModuleMapping` | `0x69aa40` |
| `RenestInHoles` | `0x40720` |
| `Renested ` | `0x40720` |
| `SetCommonCutParameters` | `0x3c3f0` |
| `SetMultiTorchParameters` | `0x3e740` |
| `ToNesting` | `0x3dbe0` |
| `Utils::eps_equals(res[0].x(), 0.0) && Utils::eps_equals(res[0].y(), 0.0)` | `0x193420` |
| `_mod` | `0x69aa40` |
| `basic_string::_M_construct null not valid` | `0x3b1f0` `0x191e80` `0x193420` `0x549270` |
| `biggest` | `0x3c3f0` `0x3e740` |
| `box.bottom_left().x() > -1e-6 && box.bottom_left().y() > -1e-6` | `0x193420` |
| `context.GetPackerCache()` | `0x3c3f0` |
| `index <= quantities.size()` | `0x3bcc0` |
| `index >= (m_parts.size() - m_clusters.size()) && index < m_parts.size()` | `0x69a720` |
| `index >= 0 && index < m_parts.size()` | `0x7d3e50` `0x7d4050` |
| `m_parts.size() >= nb_parts` | `0x69aa40` |
| `matrix_indices.size() == group_indices.size()` | `0x40070` |
| `nb_modules > 0` | `0x69aa40` |
| `nesting.multiplicity() == 1u` | `0x41920` |
| `nesting.sheet()` | `0x41920` `0x434d0` |
| `nesting_part_index < m_parts.size()` | `0x3dbe0` `0x3f070` |
| `packer_cache` | `0x3e740` |
| `part_and_module.part()->module(part_and_module.module_index()).authorizations().IsCompatible(popos.m_o)` | `0x40070` |
| `sheet` | `0x3b5f0` `0x3dbe0` `0x40720` `0x41920` |
| `vector::_M_range_check: __n (which is %zu) >= this->size() (which is %zu)` | `0x548680` `0x69a720` |
| `vector::_M_range_insert` | `0x8ec0a0` `0x8ed190` |
| `vector::reserve` | `0x3e3e0` |
| `y_valid` | `0x3b2f0` |

## functions (largest first)

| RVA | bytes | callers | confidence | cited | hint |
|---|---:|---:|---|---|---|
| `0x193420` | 12805 | 2 | graph-strict | yes | (assert_aux1 == assert_aux2) |
| `0x41920` | 5640 | 8 | direct | - | ..\multi\nesting_context.cpp |
| `0x191e80` | 5521 | 2 | graph | - | (assert_aux1 == assert_aux2) |
| `0x8afdb0` | 4805 | 2 | graph-strict | - |  |
| `0x69aa40` | 4801 | 2 | direct | - | ..\multi\nesting_context.cpp |
| `0x7f3090` | 4122 | 2 | graph-strict | - | data@0x9d9368 |
| `0x18f4b0` | 2705 | 3 | graph-strict | - |  |
| `0x18ff50` | 2705 | 3 | graph-strict | - |  |
| `0x8af220` | 2640 | 2 | graph-strict | - |  |
| `0x54d760` | 2622 | 3 | graph-strict | - |  |
| `0x548680` | 2413 | 3 | graph-strict | - | vector::_M_range_check: __n (which is %zu) >= this->size() (which is % |
| `0x155bb0` | 2294 | 3 | graph-strict | - | data@0x9bd370 |
| `0x3c9e0` | 2045 | 3 | direct | - | ..\multi\nesting_context.cpp |
| `0x3dbe0` | 2033 | 6 | direct | - | ..\multi\nesting_context.cpp |
| `0x1909f0` | 2011 | 2 | graph-strict | - |  |
| `0x8ed190` | 1999 | 3 | graph-strict | - | vector::_M_range_insert |
| `0x8eca70` | 1818 | 4 | graph-strict | - | basic_string::_M_construct null not valid |
| `0x3f070` | 1733 | 2 | direct | yes | ..\multi\nesting_context.cpp |
| `0x40070` | 1697 | 7 | direct | - | ..\multi\nesting_context.cpp |
| `0x3e740` | 1547 | 4 | direct | - | ..\multi\nesting_context.cpp |
| `0x3c3f0` | 1517 | 3 | direct | yes | ..\multi\nesting_context.cpp |
| `0x54f5d0` | 1516 | 2 | graph-strict | - | data@0x9dc0a0 |
| `0x937a70` | 1420 | 2 | graph-strict | - |  |
| `0x5884d0` | 1419 | 9 | graph-strict | - |  |
| `0x197090` | 1418 | 2 | graph-strict | - | data@0x9be3b0 |
| `0x18efc0` | 1261 | 2 | graph-strict | - | data@0x9be358 |
| `0x40720` | 1220 | 3 | direct | yes | ..\multi\nesting_context.cpp |
| `0x196c30` | 1111 | 3 | graph-strict | - |  |
| `0x5271a0` | 1102 | 2 | graph-strict | - |  |
| `0x3bcc0` | 1089 | 4 | direct | - | ..\multi\nesting_context.cpp |
| `0x549650` | 1083 | 2 | graph-strict | - | basic_string::_M_construct null not valid |
| `0x696c50` | 1030 | 3 | direct | - | ..\multi\nesting_context.cpp |
| `0x8ec3b0` | 1021 | 9 | graph-strict | - | basic_string::_M_construct null not valid |
| `0x7c1dc0` | 1012 | 3 | graph-strict | - |  |
| `0x549270` | 983 | 4 | graph-strict | - | basic_string::_M_construct null not valid |
| `0x934080` | 980 | 3 | graph-strict | - |  |
| `0x7d21a0` | 860 | 6 | graph-strict | - | data@0x9af7e8 |
| `0x3e3e0` | 854 | 7 | graph | - | vector::reserve |
| `0x1966a0` | 818 | 2 | graph-strict | - |  |
| `0x8ec0a0` | 776 | 2 | graph-strict | - | vector::_M_range_insert |
| `0x3fa50` | 752 | 3 | graph-strict | - | data@0x9af790 |
| `0x8e8840` | 749 | 3 | graph-strict | - |  |
| `0x669e60` | 749 | 1 | graph-strict | - |  |
| `0x598a30` | 745 | 2 | graph-strict | - |  |
| `0x1d0d70` | 719 | 4 | graph-strict | - |  |
| `0x18e020` | 629 | 3 | graph-strict | - | data@0x9be220 |
| `0x8d7260` | 626 | 2 | graph-strict | - |  |
| `0x16ef80` | 622 | 3 | graph-strict | - |  |
| `0x8cb6f0` | 609 | 9 | graph-strict | - |  |
| `0x8b3d60` | 572 | 2 | graph-strict | - |  |
| `0x902440` | 563 | 2 | graph-strict | - |  |
| `0x154bc0` | 554 | 3 | graph-strict | - |  |
| `0x5cf480` | 549 | 5 | graph-strict | - |  |
| `0x598760` | 544 | 6 | graph-strict | - |  |
| `0x3b2f0` | 524 | 3 | direct | - | y_valid |
| `0x92a6d0` | 519 | 3 | graph-strict | - |  |
| `0x7d3e50` | 504 | 5 | direct | - | ..\multi\nesting_context.cpp |
| `0xad630` | 478 | 6 | graph-strict | - |  |
| `0x896f30` | 460 | 3 | graph-strict | - |  |
| `0x8b8250` | 458 | 2 | graph-strict | - |  |
| `0x8b8650` | 454 | 2 | graph-strict | - |  |
| `0x69a720` | 454 | 4 | direct | - | ..\multi\nesting_context.cpp |
| `0x8bf4c0` | 438 | 2 | graph-strict | - |  |
| `0x4f1590` | 425 | 3 | graph-strict | - | data@0x9da1d8 |
| `0x8f5fd0` | 418 | 2 | graph-strict | - |  |
| `0x93fbb0` | 408 | 3 | graph-strict | - |  |
| `0x434d0` | 407 | 10 | direct | yes | ..\multi\nesting_context.cpp |
| `0x3b5f0` | 367 | 4 | direct | - | ..\multi\nesting_context.cpp |
| `0x7d4050` | 356 | 6 | direct | - | ..\multi\nesting_context.cpp |
| `0x69bd10` | 354 | 2 | graph-strict | - |  |
| `0x17b740` | 352 | 1 | graph-strict | - |  |
| `0x16f1f0` | 347 | 1 | graph-strict | - |  |
| `0x69a8f0` | 334 | 2 | graph-strict | - | data@0x9af820 |
| `0x8e8690` | 330 | 3 | graph-strict | - |  |
| `0x8afc70` | 313 | 4 | graph-strict | - |  |
| `0x9320a0` | 281 | 7 | graph-strict | - |  |
| `0x196b20` | 267 | 2 | graph-strict | - |  |
| `0x8cee00` | 256 | 2 | graph-strict | - |  |
| `0x896210` | 247 | 3 | graph-strict | - |  |
| `0x40bf0` | 223 | 2 | graph-strict | - |  |
| `0x40cd0` | 223 | 2 | graph-strict | - |  |
| `0x8f3010` | 220 | 2 | graph-strict | - |  |
| `0x8f30f0` | 220 | 3 | graph-strict | - |  |
| `0x8f3390` | 220 | 3 | graph-strict | - |  |
| `0x678f40` | 207 | 6 | graph-strict | - |  |
| `0x896e60` | 200 | 2 | graph-strict | - |  |
| `0x51f970` | 185 | 4 | graph-strict | - |  |
| `0x3b1f0` | 177 | 13 | graph | - | basic_string::_M_construct null not valid |
| `0x7d2e20` | 176 | 0 | vtable:NestingContext | - |  |
| `0x931ff0` | 169 | 2 | graph-strict | - |  |
| `0x93fb00` | 169 | 2 | graph-strict | - |  |
| `0x598980` | 167 | 6 | graph-strict | yes |  |
| `0x598d20` | 167 | 2 | graph-strict | - |  |
| `0x90d910` | 155 | 7 | graph-strict | - |  |
| `0x660550` | 149 | 4 | graph-strict | - |  |
| `0x6ef370` | 140 | 2 | graph-strict | - | data@0xb290ec |
| `0x6ef9a0` | 140 | 2 | graph-strict | - | data@0xb290ec |
| `0x897530` | 139 | 2 | graph-strict | - |  |
| `0x92efd0` | 129 | 3 | graph-strict | - |  |
| `0x8981a0` | 123 | 1 | graph-strict | - |  |
| `0x69a480` | 123 | 0 | vtable:NestingContext | - | data@0xa3bcf0 |
| `0x5ca6a0` | 123 | 3 | graph-strict | - |  |
| `0x8ea1b0` | 120 | 4 | graph-strict | - |  |
| `0x69a500` | 115 | 0 | vtable:NestingContext | - | data@0xa3bcf0 |
| `0x42f30` | 112 | 1 | graph-strict | - |  |
| `0x4f1dc0` | 108 | 1 | graph-strict | - |  |
| `0x669df0` | 102 | 3 | graph-strict | - |  |
| `0x6de240` | 97 | 7 | graph-strict | - |  |
| `0x3c390` | 96 | 2 | graph-strict | - |  |
| `0x6ec810` | 91 | 19 | graph-strict | - | data@0x9aa8f0 |
| `0x3b590` | 84 | 1 | graph-strict | - | data@0x9af1ef |
| `0x454e0` | 80 | 2 | graph-strict | - |  |
| `0x57d9e0` | 66 | 3 | graph-strict | - |  |
| `0x8ec9a0` | 61 | 2 | graph-strict | - |  |
| `0x3b2b0` | 60 | 23 | graph-strict | - |  |
| `0x6f0cb0` | 59 | 2 | graph-strict | - |  |
| `0x6f0df0` | 59 | 2 | graph-strict | - |  |
| `0x4f0c60` | 56 | 1 | graph-strict | - |  |
| `0x54e1c0` | 26 | 1 | graph-strict | - |  |
| `0x54e1a0` | 25 | 1 | graph-strict | - |  |
| `0x891b80` | 23 | 23 | graph-strict | - |  |
| `0x3b7a0` | 15 | 4 | graph-strict | - |  |
| `0x157dc0` | 15 | 1 | graph-strict | - |  |
| `0x45530` | 12 | 1 | graph-strict | - |  |
| `0x4f7610` | 9 | 3 | graph-strict | - |  |
| `0x178650` | 8 | 1 | graph-strict | - |  |
| `0x3f740` | 8 | 4 | graph-strict | - |  |
| `0x5433e0` | 7 | 4 | graph-strict | - |  |
| `0x5483a0` | 5 | 6 | graph-strict | - |  |
| `0x5483b0` | 5 | 7 | graph-strict | - |  |
| `0x5483c0` | 5 | 9 | graph-strict | - |  |
| `0x1804d0` | 5 | 2 | graph-strict | - |  |
| `0x547620` | 5 | 4 | graph-strict | - |  |
| `0x548390` | 4 | 4 | graph-strict | - |  |
| `0x548630` | 4 | 12 | graph | - |  |
