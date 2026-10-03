# The two placed layouts of the module's 0x2C0 object

| | Order (model.hpp) | LaunchingOrderLayout (launching_order.hpp) |
|---|---|---|
| fields with an offset | 59 | 127 |
| shared offsets | colspan=2 | **54** |
| only here | 5 | 73 |

**AND `LaunchingOrderLayout` HAS 73 OFFSETS `Order` DOES NOT, OF WHICH 62 CARRY AN `unnamedXXX` NAME** -- which that file's own header explains: "A field with an OFFSET-DERIVED name (unnamedXXX) is one the module never names anywhere this project [can see]". **So the merge takes those offsets and NOT their names**, and `Order`'s names stand where it has one.


## The 73 offsets only the layout has

| offset | the layout's type | its name | width |
|---|---|---|---|
| +0x000 | `std::uint64_t` | `unnamed000` | 8 B |
| +0x010 | `double` | `multiplicityPreference` | 8 B |
| +0x018 | `std::uint32_t` | `unnamed018` | 4 B |
| +0x01C | `std::uint32_t` | `unnamed01C` | 4 B |
| +0x020 | `std::uint8_t` | `unnamed020` | 1 B |
| +0x021 | `std::uint8_t` | `unnamed021` | 1 B |
| +0x024 | `unsigned char` | `unnamed024` | 4 B |
| +0x029 | `unsigned char` | `unnamed029` | 7 B |
| +0x039 | `unsigned char` | `unnamed039` | 7 B |
| +0x040 | `std::uint8_t` | `unnamed040` | 1 B |
| +0x042 | `unsigned char` | `unnamed042` | 2 B |
| +0x04C | `unsigned char` | `unnamed04C` | 4 B |
| +0x05D | `unsigned char` | `unnamed05D` | 3 B |
| +0x069 | `unsigned char` | `unnamed069` | 3 B |
| +0x078 | `std::uint64_t` | `unnamed078` | 8 B |
| +0x080 | `std::uint32_t` | `unnamed080` | 4 B |
| +0x086 | `unsigned char` | `unnamed086` | 2 B |
| +0x089 | `unsigned char` | `unnamed089` | 3 B |
| +0x099 | `unsigned char` | `unnamed099` | 3 B |
| +0x0A0 | `std::uint8_t` | `multiTorchCuttingPreferencePositive` | 1 B |
| +0x0A1 | `unsigned char` | `unnamed0A1` | 7 B |
| +0x0AC | `unsigned char` | `unnamed0AC` | 4 B |
| +0x0D1 | `unsigned char` | `unnamed0D1` | 7 B |
| +0x0E0 | `std::uint8_t` | `markModeGiven` | 1 B |
| +0x0E1 | `unsigned char` | `unnamed0E1` | 7 B |
| +0x0F0 | `double` | `markModeSecond` | 8 B |
| +0x0F8 | `std::uint8_t` | `unnamed0F8` | 1 B |
| +0x0F9 | `std::uint8_t` | `unnamed0F9` | 1 B |
| +0x0FA | `unsigned char` | `unnamed0FA` | 6 B |
| +0x100 | `std::uint64_t` | `unnamed100` | 8 B |
| +0x108 | `std::uint32_t` | `unnamed108` | 4 B |
| +0x10C | `unsigned char` | `unnamed10C` | 4 B |
| +0x110 | `std::uint64_t` | `emptySlotMarker0` | 8 B |
| +0x120 | `std::uint32_t` | `emptySlotMarker2` | 4 B |
| +0x124 | `std::uint8_t` | `specificSheetOriginGiven` | 1 B |
| +0x125 | `unsigned char` | `unnamed125` | 3 B |
| +0x129 | `unsigned char` | `unnamed129` | 3 B |
| +0x12C | `std::uint8_t` | `specificSheetObjectiveGiven` | 1 B |
| +0x12D | `unsigned char` | `unnamed12D` | 3 B |
| +0x134 | `unsigned char` | `unnamed134` | 4 B |
| +0x151 | `unsigned char` | `unnamed151` | 7 B |
| +0x158 | `std::uint8_t` | `unnamed158` | 1 B |
| +0x159 | `unsigned char` | `unnamed159` | 7 B |
| +0x160 | `std::uint64_t` | `unnamed160` | 8 B |
| +0x168 | `std::uint64_t` | `unnamed168` | 8 B |
| +0x170 | `std::uint8_t` | `pipeMode` | 1 B |
| +0x171 | `unsigned char` | `unnamed171` | 7 B |
| +0x1C8 | `std::uint64_t` | `unnamed1C8` | 8 B |
| +0x1D0 | `std::uint64_t` | `unnamed1D0` | 8 B |
| +0x1D8 | `std::uint64_t` | `unnamed1D8` | 8 B |
| +0x1E0 | `std::uint64_t` | `unnamed1E0` | 8 B |
| +0x1E8 | `std::uint64_t` | `unnamed1E8` | 8 B |
| +0x1F0 | `std::uint64_t` | `unnamed1F0` | 8 B |
| +0x218 | `std::uint32_t` | `unnamed218` | 4 B |
| +0x21C | `unsigned char` | `unnamed21C` | 4 B |
| +0x220 | `std::uint64_t` | `unnamed220` | 8 B |
| +0x228 | `std::uint64_t` | `unnamed228` | 8 B |
| +0x230 | `std::uint64_t` | `unnamed230` | 8 B |
| +0x238 | `std::uint64_t` | `unnamed238` | 8 B |
| +0x250 | `std::uint64_t` | `unnamed250` | 8 B |
| +0x258 | `std::uint8_t` | `unnamed258` | 1 B |
| +0x259 | `unsigned char` | `unnamed259` | 15 B |
| +0x270 | `std::uint64_t` | `unnamed270` | 8 B |
| +0x278 | `std::uint8_t` | `unnamed278` | 1 B |
| +0x279 | `unsigned char` | `unnamed279` | 15 B |
| +0x288 | `std::uint8_t` | `estimateLocalComputation` | 1 B |
| +0x289 | `unsigned char` | `unnamed289` | 7 B |
| +0x290 | `std::uint64_t` | `unnamed290` | 8 B |
| +0x298 | `std::uint64_t` | `unnamed298` | 8 B |
| +0x2A0 | `std::uint64_t` | `unnamed2A0` | 8 B |
| +0x2A8 | `std::uint64_t` | `nodeList` | 8 B |
| +0x2B0 | `std::uint64_t` | `unnamed2B0` | 8 B |
| +0x2B8 | `std::uint64_t` | `unnamed2B8` | 8 B |

## And the 5 offsets only `Order` has

| offset | Order's type | its name |
|---|---|---|
| +0x1FC | `std::uint32_t` | `maxIterations` |
| +0x200 | `std::uint8_t` | `engineLo` |
| +0x201 | `std::uint8_t` | `engineHi` |
| +0x204 | `std::uint32_t` | `threadsA` |
| +0x208 | `std::uint32_t` | `threadsB` |

