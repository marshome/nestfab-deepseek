# The Order reconciliation's two lists

`model.hpp`'s `Order` has **47** offset-commented fields and `launching_order.hpp`'s `LaunchingOrderLayout` has **127**; they share **45**, which is **96%** of the smaller. **They are one module object described twice**, and these are the two things a merge has to take from the layout.


## 1. The 82 offsets the layout has and `Order` does not

| offset | type | name in the layout |
|---|---|---|
| +0x000 | `std::uint64_t` | `unnamed000` (8 B) |
| +0x010 | `double` | `multiplicityPreference` (8 B) |
| +0x01C | `std::uint32_t` | `unnamed01C` (4 B) |
| +0x021 | `std::uint8_t` | `unnamed021` (1 B) |
| +0x024 | `unsigned char [0x4]` | `unnamed024` (4 B) |
| +0x028 | `std::uint8_t` | `unnamed028` (1 B) |
| +0x029 | `unsigned char [0x7]` | `unnamed029` (7 B) |
| +0x030 | `std::uint64_t` | `unnamed030` (8 B) |
| +0x039 | `unsigned char [0x7]` | `unnamed039` (7 B) |
| +0x040 | `std::uint8_t` | `unnamed040` (1 B) |
| +0x042 | `unsigned char [0x2]` | `unnamed042` (2 B) |
| +0x04C | `unsigned char [0x4]` | `unnamed04C` (4 B) |
| +0x05D | `unsigned char [0x3]` | `unnamed05D` (3 B) |
| +0x069 | `unsigned char [0x3]` | `unnamed069` (3 B) |
| +0x078 | `std::uint64_t` | `unnamed078` (8 B) |
| +0x080 | `std::uint32_t` | `unnamed080` (4 B) |
| +0x086 | `unsigned char [0x2]` | `unnamed086` (2 B) |
| +0x089 | `unsigned char [0x3]` | `unnamed089` (3 B) |
| +0x099 | `unsigned char [0x3]` | `unnamed099` (3 B) |
| +0x0A0 | `std::uint8_t` | `multiTorchCuttingPreferencePositive` (1 B) |
| +0x0A1 | `unsigned char [0x7]` | `unnamed0A1` (7 B) |
| +0x0AC | `unsigned char [0x4]` | `unnamed0AC` (4 B) |
| +0x0D1 | `unsigned char [0x7]` | `unnamed0D1` (7 B) |
| +0x0E0 | `std::uint8_t` | `markModeGiven` (1 B) |
| +0x0E1 | `unsigned char [0x7]` | `unnamed0E1` (7 B) |
| +0x0F0 | `double` | `markModeSecond` (8 B) |
| +0x0F8 | `std::uint8_t` | `unnamed0F8` (1 B) |
| +0x0F9 | `std::uint8_t` | `unnamed0F9` (1 B) |
| +0x0FA | `unsigned char [0x6]` | `unnamed0FA` (6 B) |
| +0x100 | `std::uint64_t` | `unnamed100` (8 B) |
| +0x108 | `std::uint32_t` | `unnamed108` (4 B) |
| +0x10C | `unsigned char [0x4]` | `unnamed10C` (4 B) |
| +0x110 | `std::uint64_t` | `emptySlotMarker0` (8 B) |
| +0x120 | `std::uint32_t` | `emptySlotMarker2` (4 B) |
| +0x124 | `std::uint8_t` | `specificSheetOriginGiven` (1 B) |
| +0x125 | `unsigned char [0x3]` | `unnamed125` (3 B) |
| +0x128 | `std::uint8_t` | `specificSheetOrigin` (1 B) |
| +0x129 | `unsigned char [0x3]` | `unnamed129` (3 B) |
| +0x12C | `std::uint8_t` | `specificSheetObjectiveGiven` (1 B) |
| +0x12D | `unsigned char [0x3]` | `unnamed12D` (3 B) |
| +0x130 | `std::uint32_t` | `specificSheetObjective` (4 B) |
| +0x134 | `unsigned char [0x4]` | `unnamed134` (4 B) |
| +0x138 | `std::uint64_t` | `unnamed138` (8 B) |
| +0x140 | `std::uint64_t` | `unnamed140` (8 B) |
| +0x148 | `std::uint64_t` | `unnamed148` (8 B) |
| +0x150 | `std::uint8_t` | `unnamed150` (1 B) |
| +0x151 | `unsigned char [0x7]` | `unnamed151` (7 B) |
| +0x159 | `unsigned char [0x7]` | `unnamed159` (7 B) |
| +0x160 | `std::uint64_t` | `unnamed160` (8 B) |
| +0x168 | `std::uint64_t` | `unnamed168` (8 B) |
| +0x171 | `unsigned char [0x7]` | `unnamed171` (7 B) |
| +0x178 | `std::uint64_t` | `unnamed178` (8 B) |
| +0x180 | `std::uint64_t` | `unnamed180` (8 B) |
| +0x188 | `std::uint64_t` | `unnamed188` (8 B) |
| +0x190 | `std::uint64_t` | `unnamed190` (8 B) |
| +0x198 | `std::uint64_t` | `unnamed198` (8 B) |
| +0x1C8 | `std::uint64_t` | `unnamed1C8` (8 B) |
| +0x1D0 | `std::uint64_t` | `unnamed1D0` (8 B) |
| +0x1D8 | `std::uint64_t` | `unnamed1D8` (8 B) |
| +0x1E0 | `std::uint64_t` | `unnamed1E0` (8 B) |
| +0x1E8 | `std::uint64_t` | `unnamed1E8` (8 B) |
| +0x1F0 | `std::uint64_t` | `unnamed1F0` (8 B) |
| +0x218 | `std::uint32_t` | `unnamed218` (4 B) |
| +0x21C | `unsigned char [0x4]` | `unnamed21C` (4 B) |
| +0x220 | `std::uint64_t` | `unnamed220` (8 B) |
| +0x228 | `std::uint64_t` | `unnamed228` (8 B) |
| +0x230 | `std::uint64_t` | `unnamed230` (8 B) |
| +0x238 | `std::uint64_t` | `unnamed238` (8 B) |
| +0x250 | `std::uint64_t` | `unnamed250` (8 B) |
| +0x258 | `std::uint8_t` | `unnamed258` (1 B) |
| +0x259 | `unsigned char [0xF]` | `unnamed259` (15 B) |
| +0x270 | `std::uint64_t` | `unnamed270` (8 B) |
| +0x278 | `std::uint8_t` | `unnamed278` (1 B) |
| +0x279 | `unsigned char [0xF]` | `unnamed279` (15 B) |
| +0x288 | `std::uint8_t` | `estimateLocalComputation` (1 B) |
| +0x289 | `unsigned char [0x7]` | `unnamed289` (7 B) |
| +0x290 | `std::uint64_t` | `unnamed290` (8 B) |
| +0x298 | `std::uint64_t` | `unnamed298` (8 B) |
| +0x2A0 | `std::uint64_t` | `unnamed2A0` (8 B) |
| +0x2A8 | `std::uint64_t` | `nodeList` (8 B) |
| +0x2B0 | `std::uint64_t` | `unnamed2B0` (8 B) |
| +0x2B8 | `std::uint64_t` | `unnamed2B8` (8 B) |

## 2. The 21 shared offsets where the two disagree on WIDTH

The module settles these: `re/g_adjudicate.py` compares each against the store it performs.

| offset | Order | layout | narrower |
|---|---|---|---|
| +0x018 | `double cfgAt190` (8B) | `std::uint32_t unnamed018` (4B) | **layout** |
| +0x020 | `double cfgAt188` (8B) | `std::uint8_t unnamed020` (1B) | **layout** |
| +0x044 | `bool shear` (1B) | `std::uint32_t unnamed044` (4B) | **Order** |
| +0x048 | `bool shearCorner` (1B) | `std::uint32_t unnamed048` (4B) | **Order** |
| +0x058 | `bool shearRepulseFromBorders` (1B) | `std::uint32_t unnamed058` (4B) | **Order** |
| +0x05C | `int commonCutModeA` (4B) | `std::uint8_t unnamed05C` (1B) | **layout** |
| +0x060 | `int commonCutModeB` (4B) | `std::uint64_t unnamed060` (8B) | **Order** |
| +0x068 | `int commonCutSafetyFlag` (4B) | `std::uint8_t commonCutSafetyPreferenceGiven` (1B) | **layout** |
| +0x070 | `int commonCutAuthorizations` (12B) | `std::uint64_t unnamed070` (8B) | **layout** |
| +0x084 | `int commonCutNoHoles` (4B) | `std::uint8_t unnamed084` (1B) | **layout** |
| +0x085 | `int commonCutOnlyBiModules` (4B) | `std::uint8_t unnamed085` (1B) | **layout** |
| +0x088 | `int commonCutModeTag` (4B) | `std::uint8_t commonCutCuttingPreferenceGiven` (1B) | **layout** |
| +0x098 | `int multitorchModeTag` (4B) | `std::uint8_t multiTorchCuttingPreferenceGiven` (1B) | **layout** |
| +0x0A8 | `bool multitorchAllowed` (1B) | `std::uint32_t unnamed0A8` (4B) | **Order** |
| +0x0C0 | `int multitorchNbTorches` (4B) | `std::uint64_t unnamed0C0` (8B) | **Order** |
| +0x0D0 | `double multitorchMaxDistance` (8B) | `std::uint8_t unnamed0D0` (1B) | **layout** |
| +0x0E8 | `bool markMode` (1B) | `double markModeFirst` (8B) | **Order** |
| +0x1A0 | `bool commonCutBlockSet` (1B) | `std::uint64_t commonCutParameterA` (8B) | **Order** |
| +0x1B8 | `unsigned char commonCutAt1B8` (1B) | `std::uint64_t userString` (8B) | **Order** |
| +0x1F8 | `int maxThreads` (4B) | `unsigned char unnamed1F8` (32B) | **Order** |
| +0x240 | `bool automaticStop` (1B) | `std::uint32_t automaticStop` (4B) | **Order** |

## 3. And 2 of `Order`'s fields whose width the table could not resolve

   +0x248  `std::string licenseKey1` -- add it to WIDTHS in re/g_order_reconcile.py
   +0x268  `std::string licenseKey2` -- add it to WIDTHS in re/g_order_reconcile.py

## 4. A convention the conflicts show

**Where the two disagree on a NAME, the layout's is usually the module's and `Order`'s is a description**: `commonCutSafetyFlag` against
`commonCutSafetyPreferenceGiven`, the latter being the export `SetCommonCutSafetyPreference` that writes the field. **So a merge keeps
`Order`'s callers, the layout's widths, and per field whichever NAME the module itself supplies.**
