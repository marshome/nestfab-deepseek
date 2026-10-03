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
    unsigned char unnamed008[0x4];   // +0x008..+0x00B, not written by RE 0x14620
    std::uint32_t        origin;   // +0x00C  RE 0xD119, SetOrigin (86)
    double               multiplicityPreference;   // +0x010  RE 0xD26A, CNS_SetMultiplicityPreference (128), a double
    std::uint32_t        unnamed018;   // +0x018  written by RE 0x14620
    std::uint32_t        unnamed01C;   // +0x01C  written by RE 0x14620
    std::uint8_t         unnamed020;   // +0x020  written by RE 0x14620
    std::uint8_t         unnamed021;   // +0x021  written by RE 0x14620
    std::uint8_t         unnamed022;   // +0x022  written by RE 0x14620
    std::uint8_t         unnamed023;   // +0x023  written by RE 0x14620
    unsigned char unnamed024[0x4];   // +0x024..+0x027, not written by RE 0x14620
    // **THE WIDTH HERE WAS READ OFF A STACK STORE, AND THE SPAN IS EIGHT BYTES.** The annotation used to say "narrowest store is 1 byte(s) at RE 0xD062", and
    // **0xD062 is `mov byte ptr [rsp + 0x28], 0`** -- the SAME DISPLACEMENT on the STACK, inside the log object that function builds, **not a store into this
    // structure at all.** Measured through a register the prologue loaded from rcx, +0x28 takes **108 qword stores, 22 dword stores and 15 byte stores**, so eight
    // bytes is the span and one byte was the wrong reading. **Whether the eight bytes are a `double` or a union with byte flags is a separate question** --
    // `lcns/model.hpp`'s `usedSurfaceMinOffcutDimension` says `double` -- and it is recorded rather than resolved.
    unsigned char        unnamed028[0x8];   // +0x028..+0x02F, eight bytes by store width; formerly declared 1 byte
    std::uint64_t        unnamed030;   // +0x030  written by RE 0x14620
    std::uint8_t         unnamed038;   // +0x038  narrowest store is 1 byte(s) at RE 0xD0F8
    unsigned char unnamed039[0x7];   // +0x039..+0x03F, not written by RE 0x14620
    std::uint8_t         unnamed040;   // +0x040  written by RE 0x14620
    std::uint8_t         unnamed041;   // +0x041  written by RE 0x14620
    unsigned char unnamed042[0x2];   // +0x042..+0x043, not written by RE 0x14620
    std::uint32_t        unnamed044;   // +0x044  written by RE 0x14620
    std::uint32_t        unnamed048;   // +0x048  written by RE 0x14620
    unsigned char unnamed04C[0x4];   // +0x04C..+0x04F, not written by RE 0x14620
    std::uint64_t        unnamed050;   // +0x050  written by RE 0x14620
    std::uint32_t        unnamed058;   // +0x058  written by RE 0x14620
    std::uint8_t         unnamed05C;   // +0x05C  written by RE 0x14620
    unsigned char unnamed05D[0x3];   // +0x05D..+0x05F, not written by RE 0x14620
    std::uint64_t        unnamed060;   // +0x060  written by RE 0x14620
    std::uint8_t         commonCutSafetyPreferenceGiven;   // +0x068  RE 0xEA09, SetCommonCutSafetyPreference (150), byte = 1
    unsigned char unnamed069[0x3];   // +0x069..+0x06B, not written by RE 0x14620
    std::uint32_t        commonCutSafetyPreference;   // +0x06C  RE 0xEA0D, SetCommonCutSafetyPreference (150)
    std::uint64_t        unnamed070;   // +0x070  written by RE 0x14620
    std::uint64_t        unnamed078;   // +0x078  written by RE 0x14620
    std::uint32_t        unnamed080;   // +0x080  written by RE 0x14620
    std::uint8_t         unnamed084;   // +0x084  written by RE 0x14620
    std::uint8_t         unnamed085;   // +0x085  written by RE 0x14620
    unsigned char unnamed086[0x2];   // +0x086..+0x087, not written by RE 0x14620
    std::uint8_t         commonCutCuttingPreferenceGiven;   // +0x088  RE 0xED59, SetCommonCutCuttingPreference (154), byte = 1
    unsigned char unnamed089[0x3];   // +0x089..+0x08B, not written by RE 0x14620
    std::uint32_t        commonCutCuttingPreference;   // +0x08C  RE 0xED60, SetCommonCutCuttingPreference (154)
    std::uint64_t        unnamed090;   // +0x090  written by RE 0x14620
    std::uint8_t         multiTorchCuttingPreferenceGiven;   // +0x098  RE 0xF225, SetMultiTorchCuttingPreference (176), byte = 1
    unsigned char unnamed099[0x3];   // +0x099..+0x09B, not written by RE 0x14620
    std::uint32_t        multiTorchCuttingPreference;   // +0x09C  RE 0xF233, SetMultiTorchCuttingPreference (176)
    std::uint8_t         multiTorchCuttingPreferencePositive;   // +0x0A0  RE 0xF22C, setg on the same argument
    unsigned char unnamed0A1[0x7];   // +0x0A1..+0x0A7, not written by RE 0x14620
    std::uint32_t        unnamed0A8;   // +0x0A8  written by RE 0x14620
    unsigned char unnamed0AC[0x4];   // +0x0AC..+0x0AF, not written by RE 0x14620
    std::uint64_t        unnamed0B0;   // +0x0B0  written by RE 0x14620
    std::uint64_t        unnamed0B8;   // +0x0B8  written by RE 0x14620
    std::uint64_t        unnamed0C0;   // +0x0C0  written by RE 0x14620
    std::uint64_t        unnamed0C8;   // +0x0C8  written by RE 0x14620
    std::uint8_t         unnamed0D0;   // +0x0D0  written by RE 0x14620
    unsigned char unnamed0D1[0x7];   // +0x0D1..+0x0D7, not written by RE 0x14620
    std::uint64_t        unnamed0D8;   // +0x0D8  written by RE 0x14620
    std::uint8_t         markModeGiven;   // +0x0E0  RE 0x18A09, SetMarkMode (246), setne on the flag
    unsigned char unnamed0E1[0x7];   // +0x0E1..+0x0E7, not written by RE 0x14620
    double               markModeFirst;   // +0x0E8  RE 0x189FA, SetMarkMode (246), the double in xmm2
    double               markModeSecond;   // +0x0F0  RE 0x18A10, SetMarkMode (246), the double in xmm3
    std::uint8_t         unnamed0F8;   // +0x0F8  written by RE 0x14620
    std::uint8_t         unnamed0F9;   // +0x0F9  written by RE 0x14620
    unsigned char unnamed0FA[0x6];   // +0x0FA..+0x0FF, not written by RE 0x14620
    std::uint64_t        unnamed100;   // +0x100  written by RE 0x14620
    std::uint32_t        unnamed108;   // +0x108  written by RE 0x14620
    unsigned char unnamed10C[0x4];   // +0x10C..+0x10F, not written by RE 0x14620
    std::uint64_t        emptySlotMarker0;   // +0x110  RE 0x14793, the constant 0x3FFFFFFF
    std::uint64_t        emptySlotMarker1;   // +0x118  RE 0x1479E, the constant 0x3FFFFFFF
    std::uint32_t        emptySlotMarker2;   // +0x120  RE 0x147A9, the constant 0x3FFFFFFF
    std::uint8_t         specificSheetOriginGiven;   // +0x124  RE 0x13F02, SetSpecificSheetOrigin (298), byte = 1
    unsigned char unnamed125[0x3];   // +0x125..+0x127, not written by RE 0x14620
    std::uint8_t         specificSheetOrigin;   // +0x128  RE 0x13F09, SetSpecificSheetOrigin (298)
    unsigned char unnamed129[0x3];   // +0x129..+0x12B, not written by RE 0x14620
    std::uint8_t         specificSheetObjectiveGiven;   // +0x12C  RE 0x140B2, SetSpecificSheetObjective (300), byte = 1
    unsigned char unnamed12D[0x3];   // +0x12D..+0x12F, not written by RE 0x14620
    std::uint32_t        specificSheetObjective;   // +0x130  RE 0x140B9, SetSpecificSheetObjective (300)
    unsigned char unnamed134[0x4];   // +0x134..+0x137, not written by RE 0x14620
    std::uint64_t        unnamed138;   // +0x138  written by RE 0x14620
    std::uint64_t        unnamed140;   // +0x140  written by RE 0x14620
    std::uint64_t        unnamed148;   // +0x148  written by RE 0x14620
    std::uint8_t         unnamed150;   // +0x150  written by RE 0x14620
    unsigned char unnamed151[0x7];   // +0x151..+0x157, not written by RE 0x14620
    std::uint8_t         unnamed158;   // +0x158  written by RE 0x14620
    unsigned char unnamed159[0x7];   // +0x159..+0x15F, not written by RE 0x14620
    std::uint64_t        unnamed160;   // +0x160  written by RE 0x14620
    std::uint64_t        unnamed168;   // +0x168  written by RE 0x14620
    std::uint8_t         pipeMode;   // +0x170  RE 0xFCF0 SetPipeMode, read by 0x4FC2F0 / 0x4FC300
    unsigned char unnamed171[0x7];   // +0x171..+0x177, not written by RE 0x14620
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
    unsigned char unnamed1F8[0x20];   // +0x1F8..+0x217, not written by RE 0x14620
    std::uint32_t        unnamed218;   // +0x218  written by RE 0x14620
    unsigned char unnamed21C[0x4];   // +0x21C..+0x21F, not written by RE 0x14620
    std::uint64_t        unnamed220;   // +0x220  written by RE 0x14620
    std::uint64_t        unnamed228;   // +0x228  written by RE 0x14620
    std::uint64_t        unnamed230;   // +0x230  written by RE 0x14620
    std::uint64_t        unnamed238;   // +0x238  written by RE 0x14620
    std::uint32_t        automaticStop;   // +0x240  RE 0xE0D9, SetAutomaticStop (140); read by 0x22A20 at RE 0x22BC1
    std::uint32_t        unnamed244;   // +0x244  written by RE 0x14620
    std::uint64_t        unnamed248;   // +0x248  written by RE 0x14620
    std::uint64_t        unnamed250;   // +0x250  written by RE 0x14620
    std::uint8_t         unnamed258;   // +0x258  written by RE 0x14620
    unsigned char unnamed259[0xF];   // +0x259..+0x267, not written by RE 0x14620
    std::uint64_t        unnamed268;   // +0x268  written by RE 0x14620
    std::uint64_t        unnamed270;   // +0x270  written by RE 0x14620
    std::uint8_t         unnamed278;   // +0x278  written by RE 0x14620
    unsigned char unnamed279[0xF];   // +0x279..+0x287, not written by RE 0x14620
    std::uint8_t         estimateLocalComputation;   // +0x288  RE 0x3383, LaunchEstimateLocalComputation (216)
    unsigned char unnamed289[0x7];   // +0x289..+0x28F, not written by RE 0x14620
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
