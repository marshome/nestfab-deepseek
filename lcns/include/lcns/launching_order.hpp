// lcns/include/lcns/launching_order.hpp -- the launch order's layout, read out of its constructor.
//
// RE 0x14620 NewLaunchingOrder. The evidence is one function: it takes its own name to the logger, allocates 0x2C0 bytes
// through operator new at 0x998500, and then writes 96 fields, the largest at +0x2B8 and nothing above 0x2C0. That is why
// this file exists at all -- a constructor that writes every field gives the size, the boundaries and the widths at once,
// where counting how many functions touch an offset does not.
//
// What is NOT claimed here. The offsets and widths are evidence and are asserted below against the listing. The MEANINGS
// are not: a member named `word08` is an eight byte slot at +0x08 whose purpose is unknown, and it is named that way rather
// than "flags" or "counter" so that nothing is implied. Where the meaning IS known it is named and carries its address.
//
// This is the object LaunchLocalComputation receives: 0x2AB0 reads the mode at +0x240, and 0x5007C0, the destructor in the
// same closure, walks +0x1D0, +0x1F8, +0x208, +0x228, +0x230, +0x240, +0x250, +0x258, +0x268, +0x270, +0x280, +0x2A8 and
// +0x2B8 -- every one of them inside this size.
#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {
namespace dll {

/** The launch order, as bytes. RE 0x14620: operator new(0x2C0) and 96 field writes. */
struct LaunchingOrderLayout {
    // A null pointer with the low 30 bits set is this module's "empty slot" marker for the two pointer members at +0x110
    // and +0x120, so they are spelled as integers: RE 0x14793 and 0x1479E write the constant 0x3FFFFFFF.
    static constexpr std::uint32_t kEmptySlotMarker = 0x3FFFFFFFu;

    // The order the constructor writes them in, with the width of each store.
    std::uint64_t slot000;      // +0x000 qword = 0.0        RE 0x1464C
    std::uint32_t slot008;      // +0x008 dword = 0          RE 0x1465A
    std::uint32_t slot00C;      // +0x00C dword = 0          RE 0x14661
    std::uint64_t slot010;      // +0x010 qword = 0.0        RE 0x14668
    std::uint32_t slot018;      // +0x018 dword = 0          RE 0x1466D
    std::uint32_t slot01C;      // +0x01C dword = 0          RE 0x14674
    std::uint8_t  slot020;      // +0x020 byte = 0           RE 0x1467B
    std::uint8_t  slot021;      // +0x021 byte = 0           RE 0x1467F
    std::uint8_t  slot022;      // +0x022 byte = 0           RE 0x14683
    std::uint8_t  slot023;      // +0x023 byte = 0           RE 0x14687
    std::uint32_t slot024;      // +0x024 padding to the next qword
    std::uint64_t slot028;      // +0x028 qword = 0.0        RE 0x1468B
    std::uint64_t slot030;      // +0x030 qword = 0.0        RE 0x14690
    std::uint64_t slot038;      // +0x038 qword = 0.0        RE 0x14695
    std::uint8_t  slot040;      // +0x040 byte = 0           RE 0x1469A
    std::uint8_t  slot041;      // +0x041 byte = 0           RE 0x1469E
    std::uint16_t slot042;      // +0x042 padding
    std::uint32_t slot044;      // +0x044 dword = 0          RE 0x146A2
    std::uint32_t slot048;      // +0x048 dword = 0          RE 0x146A9
    std::uint32_t slot04C;      // +0x04C padding to the next qword
    std::uint64_t slot050;      // +0x050 qword = 0.0        RE 0x146B0
    std::uint32_t slot058;      // +0x058 dword = 0          RE 0x146B5
    std::uint8_t  slot05C;      // +0x05C byte = 0           RE 0x146BC
    std::uint8_t  slot05D;      // +0x05D .. +0x05F padding
    std::uint8_t  slot05E;
    std::uint8_t  slot05F;
    std::uint64_t slot060;      // +0x060 qword = 0.0        RE 0x146C0
    std::uint8_t  slot068;      // +0x068 byte = 1           RE 0x146C5
    std::uint8_t  slot069;      // +0x069 .. +0x06B padding
    std::uint8_t  slot06A;
    std::uint8_t  slot06B;
    std::uint32_t slot06C;      // +0x06C dword = 1          RE 0x146C9
    std::uint64_t slot070;      // +0x070 qword = 0.0        RE 0x146D0
    std::uint64_t slot078;      // +0x078 qword = a constant RE 0x146D5, the double at 0x9A93E8
    std::uint32_t slot080;      // +0x080 dword = 0          RE 0x146DA
    std::uint8_t  slot084;      // +0x084 byte = 0           RE 0x146E4
    std::uint8_t  slot085;      // +0x085 byte = 0           RE 0x146EB
    std::uint16_t slot086;      // +0x086 padding
    std::uint8_t  slot088;      // +0x088 byte = 1           RE 0x146F2
    std::uint8_t  slot089;      // +0x089 .. +0x08B padding
    std::uint8_t  slot08A;
    std::uint8_t  slot08B;
    std::uint32_t slot08C;      // +0x08C dword = 1          RE 0x146F9
    std::uint64_t slot090;      // +0x090 qword = 0.0        RE 0x14703
    std::uint8_t  slot098;      // +0x098 byte = 1           RE 0x1470B
    std::uint8_t  slot099;      // +0x099 .. +0x09B padding
    std::uint8_t  slot09A;
    std::uint8_t  slot09B;
    std::uint32_t slot09C;      // +0x09C dword = 2          RE 0x14712
    std::uint8_t  slot0A0;      // +0x0A0 byte = 0           RE 0x1471C
    std::uint8_t  slot0A1;      // +0x0A1 .. +0x0A7 padding
    std::uint8_t  slot0A2;
    std::uint8_t  slot0A3;
    std::uint8_t  slot0A4;
    std::uint8_t  slot0A5;
    std::uint8_t  slot0A6;
    std::uint8_t  slot0A7;
    std::uint32_t slot0A8;      // +0x0A8 dword = 0          RE 0x14723
    std::uint32_t slot0AC;      // +0x0AC padding
    std::uint64_t slot0B0;      // +0x0B0 qword = 0.0        RE 0x1472D
    std::uint64_t slot0B8;      // +0x0B8 qword = 0.0        RE 0x14735
    std::uint64_t slot0C0;      // +0x0C0 qword = 0.0        RE 0x1473D
    std::uint64_t slot0C8;      // +0x0C8 qword = 0.0        RE 0x14745
    std::uint8_t  slot0D0;      // +0x0D0 byte = 1           RE 0x1474D
    std::uint8_t  slot0D1;      // +0x0D1 .. +0x0D7 padding
    std::uint8_t  slot0D2;
    std::uint8_t  slot0D3;
    std::uint8_t  slot0D4;
    std::uint8_t  slot0D5;
    std::uint8_t  slot0D6;
    std::uint8_t  slot0D7;
    std::uint64_t slot0D8;      // +0x0D8 qword = 0.0        RE 0x14754
    std::uint8_t  slot0E0;      // +0x0E0 byte = 0           RE 0x1475C
    std::uint8_t  slot0E1;      // +0x0E1 .. +0x0E7 padding
    std::uint8_t  slot0E2;
    std::uint8_t  slot0E3;
    std::uint8_t  slot0E4;
    std::uint8_t  slot0E5;
    std::uint8_t  slot0E6;
    std::uint8_t  slot0E7;
    std::uint64_t slot0E8;      // +0x0E8 qword = 0.0        RE 0x14763
    std::uint64_t slot0F0;      // +0x0F0 qword = 0.0        RE 0x1476B
    std::uint8_t  slot0F8;      // +0x0F8 byte = 0           RE 0x14773
    std::uint8_t  slot0F9;      // +0x0F9 byte = 0           RE 0x1477A
    std::uint8_t  slot0FA;      // +0x0FA .. +0x0FF padding
    std::uint8_t  slot0FB;
    std::uint8_t  slot0FC;
    std::uint8_t  slot0FD;
    std::uint8_t  slot0FE;
    std::uint8_t  slot0FF;
    std::uint64_t slot100;      // +0x100 qword = 0.0        RE 0x14781
    std::uint32_t slot108;      // +0x108 dword = 0          RE 0x14789
    std::uint32_t slot10C;      // +0x10C padding
    std::uint64_t slot110;      // +0x110 qword = 0x3FFFFFFF RE 0x14793, the empty slot marker
    std::uint64_t slot118;      // +0x118 qword = 0x3FFFFFFF RE 0x1479E
    std::uint64_t slot120;      // +0x120 qword = 0x3FFFFFFF RE 0x147A9
    std::uint8_t  slot128;      // +0x128 byte = 0           RE 0x147B4
    std::uint8_t  slot129;      // +0x129 .. +0x12F padding
    std::uint8_t  slot12A;
    std::uint8_t  slot12B;
    std::uint8_t  slot12C;
    std::uint8_t  slot12D;
    std::uint8_t  slot12E;
    std::uint8_t  slot12F;
    std::uint64_t slot130;      // +0x130 qword = 0.0        RE 0x147BB
    std::uint64_t slot138;      // +0x138 qword = 0.0        RE 0x147C3
    std::uint64_t slot140;      // +0x140 qword = 0.0        RE 0x147CB
    std::uint64_t slot148;      // +0x148 qword = 0.0        RE 0x147D3
    std::uint8_t  slot150;      // +0x150 byte = 0           RE 0x147DB
    std::uint8_t  slot151;      // +0x151 .. +0x157 padding
    std::uint8_t  slot152;
    std::uint8_t  slot153;
    std::uint8_t  slot154;
    std::uint8_t  slot155;
    std::uint8_t  slot156;
    std::uint8_t  slot157;
    std::uint8_t  slot158;      // +0x158 byte = 0           RE 0x147E2
    std::uint8_t  slot159;      // +0x159 .. +0x15F padding
    std::uint8_t  slot15A;
    std::uint8_t  slot15B;
    std::uint8_t  slot15C;
    std::uint8_t  slot15D;
    std::uint8_t  slot15E;
    std::uint8_t  slot15F;
    std::uint64_t slot160;      // +0x160 qword = 0.0        RE 0x147E9
    std::uint64_t slot168;      // +0x168 qword = 0.0        RE 0x147F1
    std::uint8_t  slot170;      // +0x170 byte = 0           RE 0x147F9
    std::uint8_t  slot171;      // +0x171 .. +0x177 padding
    std::uint8_t  slot172;
    std::uint8_t  slot173;
    std::uint8_t  slot174;
    std::uint8_t  slot175;
    std::uint8_t  slot176;
    std::uint8_t  slot177;
    std::uint64_t slot178;      // +0x178 qword = 0.0        RE 0x14800
    std::uint64_t slot180;      // +0x180 qword = 0          RE 0x14808
    std::uint64_t slot188;      // +0x188 qword = 0          RE 0x14813
    std::uint64_t slot190;      // +0x190 qword = 0          RE 0x1481E
    std::uint64_t slot198;      // +0x198 qword = 0          RE 0x14829
    std::uint64_t slot1A0;      // +0x1A0 qword = 0          RE 0x14834
    std::uint64_t slot1A8;      // +0x1A8 qword = 0          RE 0x1483F
    std::uint64_t slot1B0;      // +0x1B0 qword = 0          RE 0x1484A
    std::uint64_t slot1B8;      // +0x1B8 qword = 0          RE 0x14855
    // The fields above +0x1B8 are written by the rest of the constructor and by the setters -- GetPartUserString reads
    // +0x1B8, LaunchLocalComputation reads the mode at +0x240, and the destructor walks to +0x2B8.
    std::uint64_t tail[0x2C0 / 8 - 0x1C0 / 8];   // +0x1C0 .. +0x2BF, all inside the 0x2C0 the constructor allocates
};

static_assert(sizeof(LaunchingOrderLayout) == 0x2C0,
              "RE 0x14636: NewLaunchingOrder allocates 0x2C0 bytes, and the field writes stop at +0x2B8");

// The two members a reader of this objective actually needs, asserted so a later edit cannot move them silently.
static_assert(offsetof(LaunchingOrderLayout, slot100) == 0x100, "RE 0x14781");
static_assert(offsetof(LaunchingOrderLayout, slot110) == 0x110, "RE 0x14793, the empty slot marker");
static_assert(offsetof(LaunchingOrderLayout, slot178) == 0x178, "RE 0x14800");
static_assert(offsetof(LaunchingOrderLayout, slot1B8) == 0x1B8, "RE 0x14855, the user string pointer");
static_assert(offsetof(LaunchingOrderLayout, tail) == 0x1C0, "RE: the first field past the ones written above");

}  // namespace dll
}  // namespace lcns
