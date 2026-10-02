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

// ---------------------------------------------------------------------------------------------------------------
// The field names, and how far they can honestly be pushed (rounds 534 and 535)
//
// The offsets and widths above are evidence: 0x14620 writes all 96 of them, which is what fixes the size at 0x2C0. The
// NAMES are a separate question and they are answered from three channels, of which only one is reliable today.
//
// 1. ACCESSORS. A function that is small and touches exactly ONE offset is an accessor, and its own name is the field's.
//    re/g_named_fields.py finds them. What it gives for this object:
//
//        +0x1B8  read by GetPartUserStringEx        (RE 0x0C5E0 is the recovered implementation of that getter)
//        +0x1F8  written by LaunchLimitedLocalComputation  (RE 0x332E, which saves it, sets it to 1 and calls 0x2AB0)
//        +0x240  the mode the candidate constructor reads (RE 0x22BC1) -- the setter is not a single-offset accessor, so
//                this one stays unnamed
//        +0x288  written by LaunchEstimateLocalComputation (RE 0x3383)
//
//    A big function is NOT an accessor even when it writes the field: SetCommonCutParameters writes twenty offsets, and
//    attributing all twenty to its name is how the first version of this tool labelled the whole object
//    'CommonCutParameters'. Size and single-mindedness are the filter, and a name from here is safe to use.
//
// 2. THE SERIALISERS. `..\structure\text_io.cpp` is where this module reads and writes its JSON, and its vocabulary is
//    exactly the field names of the objects it stores. Two functions carry most of it:
//
//        ToJson (0x50DB70, 4607 bytes, 217 calls) writes valid, version, number_of_nested_parts, nestings, sheet_id,
//            multiplicity, common_cut_evaluation, multitorch_infos, number_of_groups, fill_ratio, min_x, min_y
//        LoadSheet (0x5091B0) reads geometry, quantity, dimension_x, dimension_y, left_gap, right_gap, bottom_gap,
//            top_gap, defect_gap, used_surface_evaluation, used_surface_min_offcut_dimension, used_surface_min_offcut_area
//        LoadCommonCutEvaluation (0x509A40) reads common_cut, left, right, left_index, right_index, valid, linked,
//            number_of_common_cut, common_cut_length, regarding_length, segments
//
//    These are the names to use, but the PAIRING of a key to an offset is not reliable yet: each key is followed by several
//    accessor calls, and picking the wrong one is invisible in the output -- 'common_cut_length' came out attached to +0x10
//    that way. re/g_json_fields.py prints the pairings it completes; until one is confirmed by reading the two instructions
//    around it, it stays a lead and not a name.
//
// 3. THE KEY VOCABULARY of the settings: 555 lower_case_underscore literals across 288 functions, listed by
//    re/g_option_keys.py -- nb_strips_first, enable_database, beam_width, shear_corner, common_cut_allowed and the rest.
//    Note that most of these belong to SETTINGS objects, not to the launch order, which is why they are not used here.
//
// So: slot000 keeps its placeholder name and the reason is above, not an omission. The four names in channel 1 are used
// where the field is touched: see LaunchingOrderNames below.
// ---------------------------------------------------------------------------------------------------------------

// ---------------------------------------------------------------------------------------------------------------
// Each name's WITNESSES (round 536)
//
// A name is used here only when TWO INDEPENDENT single-offset accessors agree on the offset, which is the rule
// re/g_two_witnesses.py enforces. An accessor is a function of at most 0x100 bytes that touches exactly one offset through
// its first argument: one witness can be a function whose name describes something else, two independent ones cannot both
// be wrong the same way. The count is recorded next to each name because it is what tells a later reader how much weight to
// give it.
//
//   offset   witnesses  the accessors and what they do
//   +0x0010  2          GenerateDxfNesting reads it, GetNestingFillRatio reads it
//   +0x0050  2          GenerateHtmlSolutionReport reads it, GetFillRatio reads it
//   +0x0140  1          GetSheetUserStringEx reads it                                   (a lead)
//   +0x01B8  1          GetPartUserStringEx reads it                                    (a lead)
//   +0x01F8  1          LaunchLimitedLocalComputation writes it                         (a lead)
//   +0x0288  1          LaunchEstimateLocalComputation writes it                        (a lead)
//
// Two of the six are for the objects the EXPORTS take rather than for the launch order itself: GetFillRatio and
// GetNestingFillRatio are exports over a solution, and GenerateDxfNesting and GenerateHtmlSolutionReport read the same
// object to render it. They are listed because the offsets coincide, and that coincidence is itself a fact worth knowing --
// the solution and the launch order share a layout at +0x10 and +0x50 -- but it is not evidence that a launch order field at
// +0x10 is named FillRatio.
//
// The four remaining names have one witness each and are used with that stated. Everything else keeps slotXXX.
// ---------------------------------------------------------------------------------------------------------------

namespace names {

/** RE 0x0C5E0: the getter the export GetPartUserString(27/28) forwards to; it reads the pointer at +0x1B8. */
inline constexpr std::size_t kPartUserString = 0x1B8;

/** RE 0x332E: LaunchLimitedLocalComputation saves this field, sets it to 1, calls 0x2AB0 and restores it. */
inline constexpr std::size_t kLimitedLocalComputation = 0x1F8;

/** RE 0x3383: LaunchEstimateLocalComputation sets this one to 1 and tail calls 0x2AB0. */
inline constexpr std::size_t kEstimateLocalComputation = 0x288;

/** RE 0x22BC1: the mode the candidate constructor reads to choose its iteration cap and its two doubles. */
inline constexpr std::size_t kLocalComputationMode = 0x240;

}  // namespace names

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


/** The fields the EXPORTS name.
 *
 * An export that ends by writing a field of the order gives that field its name, and this table is read out of the nine
 * entries re/g_ready.py reports as needing no reading at all. Each line carries the export, its ordinal, the store address,
 * and the width, so the name can be checked against the instruction that produced it.
 *
 * This is a different kind of evidence from the accessor witnesses above: there, a function that touches one offset is
 * named; here, the entry point that a caller uses IS the name of the field it sets. Both are direct, and neither is a
 * guess about what a number means.
 */
namespace exported_fields {

inline constexpr std::size_t kOrigin = 0x00C;                    // RE 0xD119: SetOrigin (86) writes a dword
inline constexpr std::size_t kCommonCutCuttingPreference = 0x08C;   // RE 0xED60: SetCommonCutCuttingPreference (154)
inline constexpr std::size_t kMultiplicityPreference = 0x010;    // RE 0xD255: CNS_SetMultiplicityPreference (128), a double
inline constexpr std::size_t kAutomaticStop = 0x240;             // RE 0xE0D9: SetAutomaticStop (140)
inline constexpr std::size_t kCommonCutSafetyPreference = 0x06C; // RE 0xEA0D: SetCommonCutSafetyPreference (150)
inline constexpr std::size_t kMultiTorchCuttingPreference = 0x09C;   // RE 0xF233: SetMultiTorchCuttingPreference (176)
inline constexpr std::size_t kSpecificSheetOriginGiven = 0x124;  // RE 0x13F02: SetSpecificSheetOrigin (298), byte = 1
inline constexpr std::size_t kSpecificSheetOrigin = 0x128;       // RE 0x13F09: the value that flag qualifies
inline constexpr std::size_t kSpecificSheetObjectiveGiven = 0x12C;   // RE 0x140B2: SetSpecificSheetObjective (300)
inline constexpr std::size_t kSpecificSheetObjective = 0x130;    // RE 0x140B9
inline constexpr std::size_t kMarkModeFirst = 0x0E8;             // RE 0x189FA: SetMarkMode (246), a double from xmm2
inline constexpr std::size_t kMarkModeSecond = 0x0F0;            // RE 0x18A10: the second double, from xmm3

// Confirmed by hand in an earlier round and kept because it is the same kind of evidence:
//   SetPipeMode (0xFCF0) writes the gate byte at +0x170, and SetCommonCutParameters (0x3C3F0) writes +0x1A0, +0x1A8,
//   +0x1B0, +0x1B8 and +0x1C0 -- exactly the fields Multi::RowNester's core reads through 0x4FC2F0, 0x4FC300 and 0x4FC3C0.
inline constexpr std::size_t kPipeMode = 0x170;                  // RE round before 537
inline constexpr std::size_t kCommonCutParameterA = 0x1A0;
inline constexpr std::size_t kCommonCutParameterB = 0x1A8;
inline constexpr std::size_t kCommonCutParameterC = 0x1B0;
inline constexpr std::size_t kCommonCutParameterD = 0x1B8;
inline constexpr std::size_t kCommonCutParameterE = 0x1C0;

}  // namespace exported_fields

}  // namespace dll
}  // namespace lcns
