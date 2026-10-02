// lcns/include/lcns/launching_order.hpp -- the launch order's layout, read out of its constructor and its setters.
//
// The size and every offset come from RE 0x14620 NewLaunchingOrder, which allocates 0x2C0 bytes through operator new at
// 0x998500 and then writes 96 fields, the largest at +0x2B8 and nothing above 0x2C0. The names come from the exports that
// set the fields and from the accessors that read them, each carrying the store address that establishes it.
//
// A field with a NAME here is one the module itself names, and the comment says where: eight exports set fields and their
// own names are the field names (SetAutomaticStop sets +0x240, SetMarkMode sets +0xE8 and +0xF0, and so on), GetPartUserStringEx
// reads +0x1B8, and an earlier round read the five common-cut parameters that Multi::RowNester's core reads.
//
// A field with an OFFSET-DERIVED name (unnamedXXX) is one the module never names anywhere this project can read. It is
// spelled that way on purpose: inventing a meaning for it would be the mistake this file exists to prevent, and the
// serialiser channel that could name more of them is located but not yet paired (see re/LAUNCH_LOCAL_COMPUTATION.md).
#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {
namespace dll {

/** The launch order, 0x2C0 bytes. RE 0x14636: mov ecx, 0x2C0 ; call operator new. */
struct LaunchingOrderLayout {
    /** The empty-slot marker the constructor writes to +0x110, +0x118 and +0x120: the low 30 bits set. */
    static constexpr std::uint32_t kEmptySlotMarker = 0x3FFFFFFFu;

    std::uint64_t        unnamed000;   // +0x000  written by RE 0x14620
    unsigned char unnamed008;   // +0x008
    unsigned char unnamed009;   // +0x009
    unsigned char unnamed00A;   // +0x00A
    unsigned char unnamed00B;   // +0x00B
    std::uint32_t        origin;   // +0x00C  RE 0xD119, SetOrigin (86)
    std::uint64_t        multiplicityPreference;   // +0x010  RE 0xD26A, CNS_SetMultiplicityPreference (128), a double
    std::uint32_t        unnamed018;   // +0x018  written by RE 0x14620
    std::uint32_t        unnamed01C;   // +0x01C  written by RE 0x14620
    std::uint8_t         unnamed020;   // +0x020  written by RE 0x14620
    std::uint8_t         unnamed021;   // +0x021  written by RE 0x14620
    std::uint8_t         unnamed022;   // +0x022  written by RE 0x14620
    std::uint8_t         unnamed023;   // +0x023  written by RE 0x14620
    unsigned char unnamed024;   // +0x024
    unsigned char unnamed025;   // +0x025
    unsigned char unnamed026;   // +0x026
    unsigned char unnamed027;   // +0x027
    std::uint64_t        unnamed028;   // +0x028  written by RE 0x14620
    std::uint64_t        unnamed030;   // +0x030  written by RE 0x14620
    std::uint64_t        unnamed038;   // +0x038  written by RE 0x14620
    std::uint8_t         unnamed040;   // +0x040  written by RE 0x14620
    std::uint8_t         unnamed041;   // +0x041  written by RE 0x14620
    unsigned char unnamed042;   // +0x042
    unsigned char unnamed043;   // +0x043
    std::uint32_t        unnamed044;   // +0x044  written by RE 0x14620
    std::uint32_t        unnamed048;   // +0x048  written by RE 0x14620
    unsigned char unnamed04C;   // +0x04C
    unsigned char unnamed04D;   // +0x04D
    unsigned char unnamed04E;   // +0x04E
    unsigned char unnamed04F;   // +0x04F
    std::uint64_t        unnamed050;   // +0x050  written by RE 0x14620
    std::uint32_t        unnamed058;   // +0x058  written by RE 0x14620
    std::uint8_t         unnamed05C;   // +0x05C  written by RE 0x14620
    unsigned char unnamed05D;   // +0x05D
    unsigned char unnamed05E;   // +0x05E
    unsigned char unnamed05F;   // +0x05F
    std::uint64_t        unnamed060;   // +0x060  written by RE 0x14620
    std::uint8_t         commonCutSafetyPreferenceGiven;   // +0x068  RE 0xEA09, SetCommonCutSafetyPreference (150), byte = 1
    unsigned char unnamed069;   // +0x069
    unsigned char unnamed06A;   // +0x06A
    unsigned char unnamed06B;   // +0x06B
    std::uint32_t        commonCutSafetyPreference;   // +0x06C  RE 0xEA0D, SetCommonCutSafetyPreference (150)
    std::uint64_t        unnamed070;   // +0x070  written by RE 0x14620
    std::uint64_t        unnamed078;   // +0x078  written by RE 0x14620
    std::uint32_t        unnamed080;   // +0x080  written by RE 0x14620
    std::uint8_t         unnamed084;   // +0x084  written by RE 0x14620
    std::uint8_t         unnamed085;   // +0x085  written by RE 0x14620
    unsigned char unnamed086;   // +0x086
    unsigned char unnamed087;   // +0x087
    std::uint8_t         commonCutCuttingPreferenceGiven;   // +0x088  RE 0xED59, SetCommonCutCuttingPreference (154), byte = 1
    unsigned char unnamed089;   // +0x089
    unsigned char unnamed08A;   // +0x08A
    unsigned char unnamed08B;   // +0x08B
    std::uint32_t        commonCutCuttingPreference;   // +0x08C  RE 0xED60, SetCommonCutCuttingPreference (154)
    std::uint64_t        unnamed090;   // +0x090  written by RE 0x14620
    std::uint8_t         multiTorchCuttingPreferenceGiven;   // +0x098  RE 0xF225, SetMultiTorchCuttingPreference (176), byte = 1
    unsigned char unnamed099;   // +0x099
    unsigned char unnamed09A;   // +0x09A
    unsigned char unnamed09B;   // +0x09B
    std::uint32_t        multiTorchCuttingPreference;   // +0x09C  RE 0xF233, SetMultiTorchCuttingPreference (176)
    std::uint8_t         multiTorchCuttingPreferencePositive;   // +0x0A0  RE 0xF22C, setg on the same argument
    unsigned char unnamed0A1;   // +0x0A1
    unsigned char unnamed0A2;   // +0x0A2
    unsigned char unnamed0A3;   // +0x0A3
    unsigned char unnamed0A4;   // +0x0A4
    unsigned char unnamed0A5;   // +0x0A5
    unsigned char unnamed0A6;   // +0x0A6
    unsigned char unnamed0A7;   // +0x0A7
    std::uint32_t        unnamed0A8;   // +0x0A8  written by RE 0x14620
    unsigned char unnamed0AC;   // +0x0AC
    unsigned char unnamed0AD;   // +0x0AD
    unsigned char unnamed0AE;   // +0x0AE
    unsigned char unnamed0AF;   // +0x0AF
    std::uint64_t        unnamed0B0;   // +0x0B0  written by RE 0x14620
    std::uint64_t        unnamed0B8;   // +0x0B8  written by RE 0x14620
    std::uint64_t        unnamed0C0;   // +0x0C0  written by RE 0x14620
    std::uint64_t        unnamed0C8;   // +0x0C8  written by RE 0x14620
    std::uint8_t         unnamed0D0;   // +0x0D0  written by RE 0x14620
    unsigned char unnamed0D1;   // +0x0D1
    unsigned char unnamed0D2;   // +0x0D2
    unsigned char unnamed0D3;   // +0x0D3
    unsigned char unnamed0D4;   // +0x0D4
    unsigned char unnamed0D5;   // +0x0D5
    unsigned char unnamed0D6;   // +0x0D6
    unsigned char unnamed0D7;   // +0x0D7
    std::uint64_t        unnamed0D8;   // +0x0D8  written by RE 0x14620
    std::uint8_t         markModeGiven;   // +0x0E0  RE 0x18A09, SetMarkMode (246), setne on the flag
    unsigned char unnamed0E1;   // +0x0E1
    unsigned char unnamed0E2;   // +0x0E2
    unsigned char unnamed0E3;   // +0x0E3
    unsigned char unnamed0E4;   // +0x0E4
    unsigned char unnamed0E5;   // +0x0E5
    unsigned char unnamed0E6;   // +0x0E6
    unsigned char unnamed0E7;   // +0x0E7
    std::uint64_t        markModeFirst;   // +0x0E8  RE 0x189FA, SetMarkMode (246), the double in xmm2
    std::uint64_t        markModeSecond;   // +0x0F0  RE 0x18A10, SetMarkMode (246), the double in xmm3
    std::uint8_t         unnamed0F8;   // +0x0F8  written by RE 0x14620
    std::uint8_t         unnamed0F9;   // +0x0F9  written by RE 0x14620
    unsigned char unnamed0FA;   // +0x0FA
    unsigned char unnamed0FB;   // +0x0FB
    unsigned char unnamed0FC;   // +0x0FC
    unsigned char unnamed0FD;   // +0x0FD
    unsigned char unnamed0FE;   // +0x0FE
    unsigned char unnamed0FF;   // +0x0FF
    std::uint64_t        unnamed100;   // +0x100  written by RE 0x14620
    std::uint32_t        unnamed108;   // +0x108  written by RE 0x14620
    unsigned char unnamed10C;   // +0x10C
    unsigned char unnamed10D;   // +0x10D
    unsigned char unnamed10E;   // +0x10E
    unsigned char unnamed10F;   // +0x10F
    std::uint64_t        emptySlotMarker0;   // +0x110  RE 0x14793, the constant 0x3FFFFFFF
    std::uint64_t        emptySlotMarker1;   // +0x118  RE 0x1479E, the constant 0x3FFFFFFF
    std::uint64_t        emptySlotMarker2;   // +0x120  RE 0x147A9, the constant 0x3FFFFFFF
    std::uint8_t         specificSheetOrigin;   // +0x128  RE 0x13F09, SetSpecificSheetOrigin (298)
    unsigned char unnamed129;   // +0x129
    unsigned char unnamed12A;   // +0x12A
    unsigned char unnamed12B;   // +0x12B
    unsigned char specificSheetObjectiveGiven;   // +0x12C  RE 0x140B2, SetSpecificSheetObjective (300), byte = 1
    unsigned char unnamed12D;   // +0x12D
    unsigned char unnamed12E;   // +0x12E
    unsigned char unnamed12F;   // +0x12F
    std::uint64_t        specificSheetObjective;   // +0x130  RE 0x140B9, SetSpecificSheetObjective (300)
    std::uint64_t        unnamed138;   // +0x138  written by RE 0x14620
    std::uint64_t        unnamed140;   // +0x140  written by RE 0x14620
    std::uint64_t        unnamed148;   // +0x148  written by RE 0x14620
    std::uint8_t         unnamed150;   // +0x150  written by RE 0x14620
    unsigned char unnamed151;   // +0x151
    unsigned char unnamed152;   // +0x152
    unsigned char unnamed153;   // +0x153
    unsigned char unnamed154;   // +0x154
    unsigned char unnamed155;   // +0x155
    unsigned char unnamed156;   // +0x156
    unsigned char unnamed157;   // +0x157
    std::uint8_t         unnamed158;   // +0x158  written by RE 0x14620
    unsigned char unnamed159;   // +0x159
    unsigned char unnamed15A;   // +0x15A
    unsigned char unnamed15B;   // +0x15B
    unsigned char unnamed15C;   // +0x15C
    unsigned char unnamed15D;   // +0x15D
    unsigned char unnamed15E;   // +0x15E
    unsigned char unnamed15F;   // +0x15F
    std::uint64_t        unnamed160;   // +0x160  written by RE 0x14620
    std::uint64_t        unnamed168;   // +0x168  written by RE 0x14620
    std::uint8_t         pipeMode;   // +0x170  RE 0xFCF0 SetPipeMode, read by 0x4FC2F0 / 0x4FC300
    unsigned char unnamed171;   // +0x171
    unsigned char unnamed172;   // +0x172
    unsigned char unnamed173;   // +0x173
    unsigned char unnamed174;   // +0x174
    unsigned char unnamed175;   // +0x175
    unsigned char unnamed176;   // +0x176
    unsigned char unnamed177;   // +0x177
    std::uint64_t        unnamed178;   // +0x178  written by RE 0x14620
    std::uint64_t        unnamed180;   // +0x180  written by RE 0x14620
    std::uint64_t        unnamed188;   // +0x188  written by RE 0x14620
    std::uint64_t        unnamed190;   // +0x190  written by RE 0x14620
    std::uint64_t        unnamed198;   // +0x198  written by RE 0x14620
    std::uint64_t        commonCutParameterA;   // +0x1A0  RE 0x3C3F0 SetCommonCutParameters, read by 0x4FC3C0
    std::uint64_t        commonCutParameterB;   // +0x1A8  RE 0x3C3F0
    std::uint64_t        commonCutParameterC;   // +0x1B0  RE 0x3C3F0
    std::uint64_t        userString;   // +0x1B8  RE 0x14855 and GetPartUserStringEx (55)
    std::uint64_t        commonCutParameterE;   // +0x1C0  RE 0x3C3F0
    std::uint64_t        unnamed1C8;   // +0x1C8  written by RE 0x14620
    std::uint64_t        unnamed1D0;   // +0x1D0  written by RE 0x14620
    std::uint64_t        unnamed1D8;   // +0x1D8  written by RE 0x14620
    std::uint64_t        unnamed1E0;   // +0x1E0  written by RE 0x14620
    std::uint64_t        unnamed1E8;   // +0x1E8  written by RE 0x14620
    std::uint64_t        unnamed1F0;   // +0x1F0  written by RE 0x14620
    unsigned char unnamed1F8;   // +0x1F8
    unsigned char unnamed1F9;   // +0x1F9
    unsigned char unnamed1FA;   // +0x1FA
    unsigned char unnamed1FB;   // +0x1FB
    unsigned char unnamed1FC;   // +0x1FC
    unsigned char unnamed1FD;   // +0x1FD
    unsigned char unnamed1FE;   // +0x1FE
    unsigned char unnamed1FF;   // +0x1FF
    unsigned char unnamed200;   // +0x200
    unsigned char unnamed201;   // +0x201
    unsigned char unnamed202;   // +0x202
    unsigned char unnamed203;   // +0x203
    unsigned char unnamed204;   // +0x204
    unsigned char unnamed205;   // +0x205
    unsigned char unnamed206;   // +0x206
    unsigned char unnamed207;   // +0x207
    unsigned char unnamed208;   // +0x208
    unsigned char unnamed209;   // +0x209
    unsigned char unnamed20A;   // +0x20A
    unsigned char unnamed20B;   // +0x20B
    unsigned char unnamed20C;   // +0x20C
    unsigned char unnamed20D;   // +0x20D
    unsigned char unnamed20E;   // +0x20E
    unsigned char unnamed20F;   // +0x20F
    unsigned char unnamed210;   // +0x210
    unsigned char unnamed211;   // +0x211
    unsigned char unnamed212;   // +0x212
    unsigned char unnamed213;   // +0x213
    unsigned char unnamed214;   // +0x214
    unsigned char unnamed215;   // +0x215
    unsigned char unnamed216;   // +0x216
    unsigned char unnamed217;   // +0x217
    std::uint32_t        unnamed218;   // +0x218  written by RE 0x14620
    unsigned char unnamed21C;   // +0x21C
    unsigned char unnamed21D;   // +0x21D
    unsigned char unnamed21E;   // +0x21E
    unsigned char unnamed21F;   // +0x21F
    std::uint64_t        unnamed220;   // +0x220  written by RE 0x14620
    std::uint64_t        unnamed228;   // +0x228  written by RE 0x14620
    std::uint64_t        unnamed230;   // +0x230  written by RE 0x14620
    std::uint64_t        unnamed238;   // +0x238  written by RE 0x14620
    std::uint32_t        automaticStop;   // +0x240  RE 0xE0D9, SetAutomaticStop (140); read by 0x22A20 at RE 0x22BC1
    std::uint32_t        unnamed244;   // +0x244  written by RE 0x14620
    std::uint64_t        unnamed248;   // +0x248  written by RE 0x14620
    std::uint64_t        unnamed250;   // +0x250  written by RE 0x14620
    std::uint8_t         unnamed258;   // +0x258  written by RE 0x14620
    unsigned char unnamed259;   // +0x259
    unsigned char unnamed25A;   // +0x25A
    unsigned char unnamed25B;   // +0x25B
    unsigned char unnamed25C;   // +0x25C
    unsigned char unnamed25D;   // +0x25D
    unsigned char unnamed25E;   // +0x25E
    unsigned char unnamed25F;   // +0x25F
    unsigned char unnamed260;   // +0x260
    unsigned char unnamed261;   // +0x261
    unsigned char unnamed262;   // +0x262
    unsigned char unnamed263;   // +0x263
    unsigned char unnamed264;   // +0x264
    unsigned char unnamed265;   // +0x265
    unsigned char unnamed266;   // +0x266
    unsigned char unnamed267;   // +0x267
    std::uint64_t        unnamed268;   // +0x268  written by RE 0x14620
    std::uint64_t        unnamed270;   // +0x270  written by RE 0x14620
    std::uint8_t         unnamed278;   // +0x278  written by RE 0x14620
    unsigned char unnamed279;   // +0x279
    unsigned char unnamed27A;   // +0x27A
    unsigned char unnamed27B;   // +0x27B
    unsigned char unnamed27C;   // +0x27C
    unsigned char unnamed27D;   // +0x27D
    unsigned char unnamed27E;   // +0x27E
    unsigned char unnamed27F;   // +0x27F
    unsigned char unnamed280;   // +0x280
    unsigned char unnamed281;   // +0x281
    unsigned char unnamed282;   // +0x282
    unsigned char unnamed283;   // +0x283
    unsigned char unnamed284;   // +0x284
    unsigned char unnamed285;   // +0x285
    unsigned char unnamed286;   // +0x286
    unsigned char unnamed287;   // +0x287
    std::uint8_t         estimateLocalComputation;   // +0x288  RE 0x3383, LaunchEstimateLocalComputation (216)
    unsigned char unnamed289;   // +0x289
    unsigned char unnamed28A;   // +0x28A
    unsigned char unnamed28B;   // +0x28B
    unsigned char unnamed28C;   // +0x28C
    unsigned char unnamed28D;   // +0x28D
    unsigned char unnamed28E;   // +0x28E
    unsigned char unnamed28F;   // +0x28F
    std::uint64_t        unnamed290;   // +0x290  written by RE 0x14620
    std::uint64_t        unnamed298;   // +0x298  written by RE 0x14620
    std::uint64_t        unnamed2A0;   // +0x2A0  written by RE 0x14620
    std::uint64_t        nodeList;   // +0x2A8  RE 0x5007C0 through the order dereference
    std::uint64_t        unnamed2B0;   // +0x2B0  written by RE 0x14620
    std::uint64_t        unnamed2B8;   // +0x2B8  written by RE 0x14620
};

static_assert(sizeof(LaunchingOrderLayout) == 0x2C0,
              "RE 0x14636: NewLaunchingOrder allocates 0x2C0 bytes and its field writes stop at +0x2B8");

// The offsets a reader of this objective needs, asserted so a later edit cannot move them silently.
static_assert(offsetof(LaunchingOrderLayout, userString) == 0x1B8, "RE 0x14855, GetPartUserStringEx reads it");
static_assert(offsetof(LaunchingOrderLayout, automaticStop) == 0x240, "RE 0xE0D9 and RE 0x22BC1");
static_assert(offsetof(LaunchingOrderLayout, estimateLocalComputation) == 0x288, "RE 0x3383");
static_assert(offsetof(LaunchingOrderLayout, emptySlotMarker0) == 0x110, "RE 0x14793");
static_assert(offsetof(LaunchingOrderLayout, markModeFirst) == 0x0E8, "RE 0x189FA");
static_assert(offsetof(LaunchingOrderLayout, nodeList) == 0x2A8, "RE 0x5007C0");

}  // namespace dll
}  // namespace lcns
