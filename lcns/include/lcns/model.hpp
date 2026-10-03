// lcns/model.hpp -- problem / solution model.
//
// Field names and ORDER mirror what the reverse engineering recovered:
//   * `CommonCutProperties`  : field order read straight off SaveProblem (0x5070E0)
//   * `MultitorchProperties` : same
//   * `CommonCutSegment`     : LoadSegment's field list
//   * `MultitorchInfo`       : the record returned per part by CNS_GetPartTorchInfos (0xD870)
//   * `Objective` / `NestingOrigin` : enums decoded from the dump fn at RVA 0x511080
// The `Order` comments give the LaunchingOrder byte offset each option was written to by
// the corresponding Set* export, as established in re/REPORT.md section 7.4.
#pragma once

#include <cstdint>
#include <string>
#include <vector>

#include "lcns/enums.hpp"   // Objective / NestingOrigin (recovered enums)
#include "lcns/geom.hpp"

namespace lcns {

// --------------------------------------------------------------------------
// properties (field order == the original serialiser's order)
// --------------------------------------------------------------------------
// RE ..\structure\border_property.hpp -- the two quality domains the original asserts, at 0x1C980 /
// 0x1EE50 / 0x7BF0C0:
//     'quality >= 0 && quality < 100'   parts
//     'quality >= 0 && quality < 9'     leather layers
// They are different sets in the same model, which is why they are two constants and not one.
inline constexpr int kQualityLevelsPart = 100;          // RE 0x1EE50 assertion text
inline constexpr int kQualityLevelsLeatherLayer = 9;    // RE 0x1EE50 / 0x7BF0C0 assertion text

struct CommonCutProperties {    int allowed = 0;                        // +0x00
    double gap = 0.0;                       // +0x08
    double originalPartGap = 0.0;           // +0x10
    double cuttingCostPerUnit = 0.0;        // +0x18
    double minLength = 0.0;                 // +0x20
    double maxRegardingRatio = 0.0;         // +0x28
    int leadinType = 0;                     // +0x30
    int noHoles = 0;                        // +0x34
    int onlyBiModules = 0;                  // +0x35
};

struct MultitorchProperties {
    int nbTorches = 0;                      // +0x00
    double cuttingCostPerUnit = 0.0;        // +0x08
    double reconfigurationCost = 0.0;       // +0x10
    double minTorchDistance = 0.0;          // +0x18
    double maxTorchDistance = 0.0;          // +0x20
    int verticalTorches = 0;                // +0x28
    double userRealMaterialCostPerUnit = 0.0;  // +0x30
};

// RE 0x68A1A0 (1334 B / 319 instructions): its own identifier strings are
//     'raw_evaluation_ratio_100'  and  'raw_evaluation_ratio_10'
// and its body loads the double 10.0. A ratio paired with a scale in the name, plus a 10.0 constant,
// means the same quantity is reported as hundredths and as tenths.
// RECOVERED: the two identifier strings and the 10.0 constant.
// INFERRED:  that 100 and 10 are the scales those names refer to (the names say so; the 100 never
//            appears as a constant in the body).
inline constexpr int kCommonCutRatioScale100 = 100;   // RE the identifier 'raw_evaluation_ratio_100'
inline constexpr int kCommonCutRatioScale10 = 10;     // RE the identifier and the 10.0 constant loaded

struct CommonCutSegment {
    bool commonCut = false;
    double left = 0.0;
    double right = 0.0;
    int leftIndex = -1;
    int rightIndex = -1;
    bool valid = false;
    bool linked = false;
    double length = 0.0;   // derived
};

struct MultitorchInfo {
    double torchDistance = 0.0;
    int groupNumber = 0;
    int torchNumber = 0;
    int nbActiveTorches = 0;
    int configIndex = 0;
    int infoNbTorches = 0;
};

struct CommonCutEvaluation {
    std::vector<CommonCutSegment> commonCutSegments;
    double number = 0.0;              // RE stats key: number_of_common_cut
    double commonCutLength = 0.0;     // RE stats key: common_cut_length
    double regardingLength = 0.0;     // RE stats key: regarding_length
};

// --------------------------------------------------------------------------
// geometry carriers
// --------------------------------------------------------------------------
struct Part {
    int id = 0;
    std::string userString;
    int multiplicity = 1;
    int priority = 0;

    geom::MultiPolygon rawShape;           // as supplied (origin at 0,0)
    geom::MultiPolygon shape;              // gap-inflated working shape used by the engine

    // RE offsets on the original Part object
    double extraGap = 0.0;                 // Part+0x10
    int commonCutMode = 0;                 // Part+0x1C
    int authorizations = 0;                // Part+0x188/0x190/0x198
    int specificAuthorizations = 0;        // Part+0x1A8
    int holeStatus = 0;                    // Part+0x20A (1 = must be inside a hole) / +0x20B
    std::string variantUserString;         // Part+0x1B8

    geom::Box bounds() const { return geom::bounds(rawShape); }
    double width() const { return bounds().width(); }
    double height() const { return bounds().height(); }
    double area() const;
};

struct Sheet {
    int id = 0;
    std::string userString;
    double width = 0.0;
    double height = 0.0;
    int quantity = 1;
    double price = 0.0;                    // Sheet+0x138
    int priority = 0;                      // Sheet+0x120
    int grainDirection = 0;                // Sheet+0x134
    int objectiveOverride = -1;            // Sheet+0x12C
    int originOverride = -1;               // Sheet+0x124
    double gaps[4] = {0, 0, 0, 0};         // Sheet+0xF8..0x110
    double defectGap = 0.0;
    bool nonRectangular = false;
    bool reusable = true;                  // offcut evaluation
    geom::MultiPolygon shape;
    std::vector<geom::Polygon> defects;            // Sheet+0x160 area
    std::vector<geom::Polygon> restrictedZones;    // CNS_SheetAddRestrictedZone

    geom::Polygon outline() const;         // the sheet itself as a polygon
    double area() const;
};

struct NestedPart {
    int partIndex = 0;
    int instance = 0;
    double x = 0.0;      // world translation applied after rotation/flip
    double y = 0.0;
    double angle = 0.0;  // radians
    bool flipped = false;
    int torchGroup = 0;
};

struct Nesting {
    int sheetIndex = 0;
    std::vector<NestedPart> parts;
    std::vector<MultitorchInfo> multitorchInfos;   // RE: nesting->multitorch_infos().m_infos
    double sheetArea = 0.0;
    double usedSurface = 0.0;
    geom::Box cachedBounds;

    bool empty() const { return parts.empty(); }
    geom::Box bounds() const { return cachedBounds; }
};

struct Solution {
    std::vector<Nesting> nestings;
    bool valid = false;
    double filterScore = 0.0;      // RE 0xB3B6A: the double 0x97A090 produces, which FilterNester's Run stores

    double usedSurface() const;
    double sheetArea() const;
    double fillRatio() const;        // RE stats.cpp FillRatio
    int totalNestedParts() const;
};

// --------------------------------------------------------------------------
// the LaunchingOrder
// --------------------------------------------------------------------------
struct Order {
    // --- objective / origin (enums proven) ---

    // **THE MODULE'S LAYOUT, PLACED AT THE OFFSETS THE FIELD COMMENTS GIVE.** Every field below carries the offset its own comment states, padding fills the gaps, and this section is what makes `offsetof` agree with those comments.

    // **THE MODULE'S LAYOUT, PLACED AT THE OFFSETS THE FIELD COMMENTS GIVE.** Every field below carries the offset its own comment states, padding fills the gaps, and this section is what makes `offsetof` agree with those comments.
    std::byte padding00[0x8];   // +0x000..+0x007, no field here
    Objective objective = Objective::MinimizeArea;   // +0x008
    NestingOrigin origin = NestingOrigin::BottomLeft;   // +0x00C
    std::byte padding01a[0x8];   // +0x010..+0x017, no field here
    // **AN OFFSET COMMENT GOES INLINE, AND THAT IS NOT COSMETIC.** `re/g_measure_order_run.py` reads `// ... +0xNNN` from the SAME LINE as the declaration, so a
    // field whose offset lives in a doc block ABOVE it is unmeasured -- and worse, the block's first line is then matched as if it WERE a field, which shifts
    // every offset after it. **`reorganizeBiggestPartNearOrigin says +0x22 and measures +0x23` was this**: the +0x in the prose was read as a field.
    std::uint32_t field18 = 0;   // +0x018, RE 0xD327: the 33-byte setter at 0xD310 stores `ebx` here
    // **AND +0x1C HAS TWO VIEWS IN THE MODULE, WHICH IS A MEASUREMENT AND NOT A CHOICE.** RE 0xD357 writes a DWORD here (the 33-byte setter at 0xD340) and RE
    // 0xDE69 writes the low BYTE of the same address (`setne byte [rsi + 0x1c]`, SetPartCommonCutMode). **The two overlap**, so a byte field here would alias
    // this one; the dword is declared and the byte is reachable through it. `OptionFlagCarrier::flag1C` was that byte, and this is where it lands.
    std::uint32_t field1C = 0;   // +0x01C, RE 0xD357 (dword) and RE 0xDE69 (the low byte, SetPartCommonCutMode)
    bool floatingMode = false;   // +0x020, RE 0xDD49 `setne byte [rsi + 0x20]` in CNS_SetFloatingMode (ordinal 182)
    bool originPackingMode = false;   // +0x021, RE 0xDD79 `setne byte [rsi + 0x21]` in CNS_SetOriginPackingMode
    bool reorganizeBiggestPartNearOrigin = false;   // +0x022
    bool reorganizeLongestPartNearOrigin = false;   // +0x023
    // **SHRUNK FROM FOUR BYTES TO TWO BECAUSE THE NAMES ABOVE TOOK THE FIRST TWO.** A padding member is not decoration: it is what keeps every field after it at
    // the module's offset, so naming a byte INSIDE a gap has to take the byte OUT of the gap. **The layout check caught this when I forgot**: `sizeof(Order)` grew
    // by four, every later offset moved by four, and two byte-level assertions failed.
    std::byte padding02[0x2];   // +0x026..+0x027, no field here
    double usedSurfaceMinOffcutDimension = 0.0;   // +0x028
    double usedSurfaceMinOffcutArea = 0.0;   // +0x030
    double usedSurfaceUsableOffcutRatio = 0.0;   // +0x038
    /** +0x40, RE 0xDDA9: `setne byte [rsi + 0x40]` in SetFillLastNestingStrategy (ordinal 144). **The export's name is the oracle for the field**, and the byte was
     *  inside `padding03` before this -- a real flag the port had written off as a gap. */
    bool fillLastNestingStrategy = false;
    bool evaluateIntermediateNestingsAsLast = false;   // +0x041
    std::byte padding04[0x2];   // +0x042..+0x043, no field here
    // **THIRTY-TWO BITS AND NOT A `bool`, WHICH IS WHAT IT SAID BEFORE.** RE 0xDDD7 is `mov dword ptr [rsi + 0x44], ebx` in setShearMode (0xDDC0) and RE 0xDE0A is
    // the same in setPartialShearMode -- **a one-byte member here would let a four-byte store overwrite +0x45..+0x47.** The byte and word reads elsewhere are other
    // objects at the same displacement, not this field.
    std::uint32_t shear = 0;   // +0x044
    // and the same measurement one field later: RE 0xDE07 is `mov dword ptr [rsi + 0x48], ebx` in setPartialShearMode
    std::uint32_t shearCorner = 0;   // +0x048
    std::byte padding06[0x4];   // +0x04C..+0x04F, no field here
    double shearGap = 0.0;   // +0x050
    bool shearRepulseFromBorders = false;   // +0x058
    std::byte padding07[0x3];   // +0x059..+0x05B, no field here
    int commonCutModeA = 0;   // +0x05C
    int commonCutModeB = 0;   // +0x060
    std::byte padding08[0x4];   // +0x064..+0x067, no field here
    int commonCutSafetyFlag = 0;   // +0x068
    int commonCutPresetIndex = 0;   // +0x06C
    int commonCutAuthorizations[3] = {0, 0, 0};   // +0x070
    std::byte padding09[0x8];   // +0x07C..+0x083, no field here
    std::uint8_t commonCutNoHoles = 0;   // +0x084
    std::uint8_t commonCutOnlyBiModules = 0;   // +0x085
    std::byte padding10[0x2];   // +0x086..+0x087, no field here
    int commonCutModeTag = 0;   // +0x088
    int commonCutPresetIndex2 = 0;   // +0x08C
    double commonCutObjectiveNum = 1.0;   // +0x090
    int multitorchModeTag = 0;   // +0x098
    int multitorchPresetIndex = 0;   // +0x09C
    std::byte padding11[0x8];   // +0x0A0..+0x0A7, no field here
    bool multitorchAllowed = false;   // +0x0A8
    std::byte padding12[0x7];   // +0x0A9..+0x0AF, no field here
    double multitorchCostRatio = 0.0;   // +0x0B0
    double multitorchReconfig = 0.66;   // +0x0B8
    int multitorchNbTorches = 0;   // +0x0C0
    std::byte padding13[0x4];   // +0x0C4..+0x0C7, no field here
    double multitorchMinDistance = 0.0;   // +0x0C8
    double multitorchMaxDistance = 0.0;   // +0x0D0
    double multitorchA = 0.0;   // +0x0D8
    std::byte padding14[0x8];   // +0x0E0..+0x0E7, no field here
    bool markMode = false;   // +0x0E8
    std::byte padding15[0x2F];   // +0x0E9..+0x117, no field here
    double defectGap = 0.0;   // +0x118
    std::byte padding16[0x8];   // +0x120..+0x127, no field here
    bool rowMode = false;   // +0x128
    std::byte padding17[0x7];   // +0x129..+0x12F, no field here
    double rowShearGap = 0.0;   // +0x130
    double rowShearCommonCutGap = 0.0;   // +0x138
    double rowPunchGap = 0.0;   // +0x140
    double rowPunchCommonCutGap = 0.0;   // +0x148
    bool rowAlternate = false;   // +0x150
    std::byte padding18[0x27];   // +0x151..+0x177, no field here
    double cfgAt178 = 0.0;   // +0x178
    double cfgAt180 = 0.0;   // +0x180
    double cfgAt188 = 0.0;   // +0x188
    double cfgAt190 = 0.0;   // +0x190
    unsigned char cfgAt198 = 0;   // +0x198
    std::byte padding19[0x7];   // +0x199..+0x19F, no field here
    bool commonCutBlockSet = false;   // +0x1A0
    std::byte padding20[0x7];   // +0x1A1..+0x1A7, no field here
    double commonCutAt1A8 = 0.0;   // +0x1A8
    double commonCutAt1B0 = 0.0;   // +0x1B0
    unsigned char commonCutAt1B8 = 0;   // +0x1B8
    std::byte padding21[0x7];   // +0x1B9..+0x1BF, no field here
    double commonCutAt1C0 = 0.0;   // +0x1C0
    std::byte padding22[0x30];   // +0x1C8..+0x1F7, no field here
    std::uint32_t maxThreads = 1;   // +0x1F8
    std::uint32_t maxIterations = 1000;   // +0x1FC
    std::uint8_t engineLo = 0;   // +0x200
    std::uint8_t engineHi = 0;   // +0x201
    std::byte padding23[0x2];   // +0x202..+0x203, no field here
    std::uint32_t threadsA = 0;   // +0x204
    std::uint32_t threadsB = 0;   // +0x208
    std::byte padding24[0x34];   // +0x20C..+0x23F, no field here
    bool automaticStop = false;   // +0x240
    std::byte padding25[0x3];   // +0x241..+0x243, no field here
    int unlockMode = 0;   // +0x244
    std::string licenseKey1 ;   // +0x248
    std::string licenseKey2 ;   // +0x268
    std::byte padding26[0x38];   // +0x288..+0x2BF, no field here

    // **THIS PROJECT'S OWN MEMBERS, NOT THE MODULE'S LAYOUT.** None of them carries an offset because no store establishes one, and they sat INTERLEAVED with the module's fields -- a model-only member between two module fields pushes every later module field off its offset. That is part of why the members landed nowhere near their comments.
    /** **THE +0x1F8..+0x208 RANGE, FROM THREE EXPORTS.** `SetLocalEngine` at 0xD370 is `mov byte [rsi + 0x200], al` and `mov byte [rsi + 0x201], bl`;
     *  `SetLocalEngineThreads` at 0xDE80 is `mov dword [rdi + 0x204], r12d` and `mov dword [rdi + 0x208], ebp`; and `exports_impl.cpp` already reads 0xD3D5,
     *  0xD3E7, 0xD390 and 0xD3A0 into a `LocalEngineCarrier` whose fields are `maxThreads` at +0x1F8, `engineLo` at +0x200 and `engineHi` at +0x201.
     *
     *  **SO THE WIDTHS ARE PINNED BY INSTRUCTIONS RATHER THAN BY THE DECLARATION**: four bytes at +0x1F8, one byte at +0x200, one at +0x201, **two bytes at
     *  +0x202 that NO export writes and that nothing therefore establishes**, and four bytes each at +0x204 and +0x208. */

    // **THIS PROJECT'S OWN MEMBERS, NOT THE MODULE'S LAYOUT.** None of them carries an offset because no store establishes one, and they sat INTERLEAVED with the module's fields -- a model-only member between two module fields pushes every later module field off its offset. That is part of why the members landed nowhere near their comments.

    // --- offcut evaluation: three doubles (RE +0x28/+0x30/+0x38) ---

    // --- shear block (+0x44..+0x5C) ---

    // --- common cut (+0x5C..+0x90) ---
    double commonCutObjectiveDen = 1.0;

    // --- multi torch (+0x98..+0xD8) ---

    // --- misc flags proven by offset ---
    double interpartGap = 0.0;
    double timeLimitSeconds = 10.0;     // consumed by the canceller
    bool incompatibleSheets = false;

    // --- pipe mode / late common-cut block (+0x170, +0x1A0..+0x1C0) ---
    // RE: written by two named exports, each by copying a whole qword block from a stack buffer:
    //   SetPipeMode (0xFCF0, 568 B)              -> [rsi+0x160], +0x168, +0x170, +0x178, ...
    //   SetCommonCutParameters (0x3C3F0, 1517 B) -> [rbx+0x190], +0x198, +0x1A0, +0x1A8, +0x1B0, ...
    // The bytes that Multi::RowNester's core reads as gates are the low bytes of those qwords:
    //   0x4FC2F0(arg) = byte [[arg]+0x170]      -- the pipe-mode gate
    //   0x4FC300(arg) = byte [[arg]+0x1A0]
    //   0x4FC3C0(arg) = [arg]+0x1A0, whose +8/+0x10/+0x18/+0x20 are Pb+0x1A8/+0x1B0/+0x1B8/+0x1C0
    // The byte the RowNester core reads through 0x4FC2F0 is Pb+0x170, i.e. inside this block:
    // 0x4FC2F0(arg) = byte [[arg]+0x170] gates the core's configuration path, and the export
    // SetPipeMode (0xFCF0) is what writes this block (by copying qwords to +0x160/+0x168/+0x170/
    // +0x178). So the gate is the pipe-mode flag; which qword of the block it is, is [推断].

    // --- row block (+0x128..+0x150) ---

    // --- pipe block (+0x158..+0x178) ---
    bool pipeMode = false;
    int pipeSides = 0;
    double pipeDiameter = 0.0;

    // The pipe block's own configuration values, read by the row core's PIPE branch
    // (0x6AABC0 @0x6AC20A, reached when the gate at Pb+0x170 is set). The base there is
    // 0x4FC3A0 = `mov rax,[rcx] ; add rax,0x170`, so the sources are Pb+0x178 .. Pb+0x198:
    //     6AC20F  core[+0x08] = [rax+0x08]   == Pb+0x178
    //     6AC219  core[+0x10] = [rax+0x10]   == Pb+0x180
    //     6AC223  core[+0x20] = [rax+0x18]   == Pb+0x188   <- the coefficient
    //     6AC22D  core[+0x18] = [rax+0x20]   == Pb+0x190   <- the cost threshold
    //     6AC23B  core[+0x38] = (byte)[rax+0x28] == Pb+0x198
    // (pipeSides / pipeDiameter above were earlier, offset-unproven guesses at some of these
    // very slots.)
    //
    // NOTE -- the names below are OFFSET-KEYED on purpose, not role-keyed: these five do NOT all
    // come from SetPipeMode. By their store sites,
    //     0xFCF0 SetPipeMode              writes Pb+0x160, +0x168, +0x170, +0x178, ...
    //     0x3C3F0 SetCommonCutParameters  writes Pb+0x188, +0x190, +0x198, +0x1A0, +0x1A8,
    //                                     +0x1B0, +0x1B8, +0x1C0, +0x1C8, +0x1CC, ...
    // so +0x178/+0x180 come from SetPipeMode while +0x188/+0x190/+0x198 come from
    // SetCommonCutParameters (which copies its own argument struct verbatim through 0x185A40).

    // --- marks / leather ---
    double markSize = 0.0;
    double markInterDistance = 0.0;
    // RE ..\structure\border_property.hpp (re/findings_border_property.md): the original models
    // leather as LAYERS with a per-layer quality index -- IsLeather(p), GetLeatherLayer,
    // GetLayerLeatherPart/Sheet, GetLayerRestrictedZonePart/Sheet -- and it asserts TWO different
    // quality domains: [0,100) for parts and [0,9) for leather layers. lcns has only this single
    // flag plus Sheet::restrictedZones, so its leather support is a DOCUMENTED SIMPLIFICATION,
    // not an equivalent. The two recovered domains are kept below so the difference is visible.
    bool leatherMode = false;

    // --- data ---
    std::vector<Part> parts;
    std::vector<Sheet> sheets;

    // --- presets (RE: two std::map<int, Properties> filled in CreateProblem) ---
    std::vector<CommonCutProperties> commonCutPresets;
    std::vector<MultitorchProperties> multitorchPresets;

    CommonCutProperties commonCutProperties() const;
    MultitorchProperties multitorchProperties() const;

    int totalPartInstances() const;
    double totalPartArea() const;
    double totalSheetArea() const;
};

// ---------------------------------------------------------------------------
// helpers used all over the engine
// ---------------------------------------------------------------------------
geom::Polygon rectPolygon(double x, double y, double w, double h);
geom::Polygon circlePolygon(double cx, double cy, double r, int segments = 48);
geom::MultiPolygon makeRectMulti(double x, double y, double w, double h);

// rotate / flip / translate a shape into sheet space
// rotation + flip only (no translation) -- kept because several callers need the local frame
geom::MultiPolygon placeShape(const geom::MultiPolygon& shape, const NestedPart& np);
geom::Box placeBounds(const geom::MultiPolygon& shape, const NestedPart& np);
// the ACTUAL placed geometry: rotation + flip + the NestedPart translation. This is the one to
// use for reporting, overlap checks and every exporter -- the translation used to be duplicated
// at five call sites, which is exactly the kind of divergence a benchmark harness trips over.
geom::MultiPolygon placedPolygon(const geom::MultiPolygon& shape, const NestedPart& np);
geom::MultiPolygon placedShape(const Part& part, const NestedPart& np);
// the sheet region available for placement (outline minus restricted zones is handled
// by the placement validator, not by subtraction)
geom::Polygon sheetPolygon(const Sheet& s);

}  // namespace lcns
