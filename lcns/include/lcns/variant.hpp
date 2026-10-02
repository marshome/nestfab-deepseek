// lcns/include/lcns/variant.hpp -- the variant scale rule, RE 0x132E0, now with the extent step it was missing.
//
// RE 0x132E0 (176 bytes) is the target of TWO exports -- ordinal 196 AddHoleToPartVariant at 0x16D00 and ordinal 198
// CNS_AddExternalBoundaryToPartVariant at 0x16D40 -- so reading it once completes two entry points. Its caller list contains ITSELF as
// well, so it walks a recursive structure.
//
// THE WHOLE BODY, in order. A first version of this header recorded only the multiplication and left the extent computation as a
// comment; that was half a rule, and the half it omitted is the half that says WHICH number is scaled.
//
//     0x13310  lea  rcx, [rsp + 0x50]         ; the BOX, at rsp+0x50
//     0x13315  lea  rdx, [rbx + 0x50]         ; +0x50 of the order is where the ledger PROVED CommonCutProperties sits
//     0x13319  call 0x5CD5C0                  ; fill the box from that sub-object
//     0x1331E  cmp  byte ptr [rsp + 0x50], 0  ; the box's valid flag, the same one 0x5C8C50 tests
//     0x13327  jne  -> 0x1334F                ; invalid -> no scaling at all
//     0x13329  movsd xmm3, [rsp + 0x70]       ; box+0x20 = high1
//     0x1332F  movsd xmm0, [rsp + 0x68]       ; box+0x18 = high0
//     0x13335  subsd xmm3, [rsp + 0x60]       ; minus box+0x10 = low1   -> extent of the SECOND axis
//     0x1333B  subsd xmm0, [rsp + 0x58]       ; minus box+0x08 = low0   -> extent of the FIRST axis
//     0x13341  ucomisd xmm3, xmm0
//     0x13345  jbe  -> 0x13382                ; which extent is larger chooses the ARM
//     0x13347  mulsd xmm3, [rip + 0x99a679]   ; 0x9AD9C8 = 0.0001
//     0x13382  mulsd xmm0, [rip + 0x99a63e]   ; 0x9AD9C8 = THE SAME DOUBLE
//     0x1334F  mov dword ptr [rsp + 0x28], 1
//     0x1335F  lea  rax, [rbx + 0x208]
//     0x13366  add  rbx, 0x68
//     0x13374  call 0x23BF0                   ; the grow-and-append primitive
//
// so the rule is: fill a box from the sub-object at order+0x50, take the extent of each axis, and scale the LARGER one by 0.0001. The two
// `mulsd` instructions have different DISPLACEMENTS that resolve to the same ADDRESS, which is why an earlier record called them two
// constants and read the comparison as choosing a FACTOR -- it chooses an ARM, and both arms multiply by one double.
//
// The box offsets are StatBox's, which is the check that this routine and the stat accumulator use one representation:
//
//     box+0x00 valid   box+0x08 low0   box+0x10 low1   box+0x18 high0   box+0x20 high1
//
// and that is exactly lcns/stat.hpp's StatBox, so the structure is shared rather than similar.
#pragma once

#include <cstddef>
#include <cstdint>

#include "lcns/stat.hpp"

namespace lcns {

/** The three launch-order offsets this routine touches, each with the instruction that shows it. */
constexpr std::size_t kVariantSource = 0x50;    // RE 0x13315: lea rdx, [rbx+0x50]
constexpr std::size_t kVariantTargetA = 0x68;   // RE 0x13366: add rbx, 0x68
constexpr std::size_t kVariantTargetB = 0x208;  // RE 0x1335F: lea rax, [rbx+0x208]

/** RE 0x13347 and RE 0x13382: the scale, ONE double that both arms load. */
constexpr std::uintptr_t kVariantScaleConstant = 0x9AD9C8;
constexpr double kVariantScale = 0.0001;

/** The scaled extent given the two extents directly, kept because it is what the two arms compute.
 *
 * `extentA` is the SECOND axis and `extentB` the FIRST, in the order the instructions load them into xmm3 and xmm0 -- recorded that way
 * rather than renamed, because the arm taken decides which of the two is scaled and a caller that cares which axis won needs the
 * correspondence to the machine code.
 */
inline double variantScale(bool valid, double extentA, double extentB, double scale) {
    if (!valid) {                                     // RE 0x13327: jne past both multiplies
        return 0.0;
    }
    if (extentA > extentB) {                          // RE 0x13341 and 0x13345
        return extentA * scale;                       // RE 0x13347
    }
    return extentB * scale;                           // RE 0x13382
}

/** RE 0x132E0's rule COMPLETE: the larger extent of a box, times the scale, and nothing at all when the box is invalid.
 *
 * `box` is the value filled by RE 0x5CD5C0 from whatever sub-object the caller points at -- which for both exports is order+0x50. The
 * extents are `high - low` per axis, exactly as 0x13335 and 0x1333B compute them, and the comparison at 0x13341 chooses which of the
 * two is multiplied. Since both arms load the same double, the result is `max(extentA, extentB) * kVariantScale` and the branch exists
 * only in the machine code.
 *
 * The returned zero for an invalid box is the routine skipping both multiplies at 0x13327, not a sentinel chosen here.
 */
inline double variantScaleOfBox(const StatBox& box) {
    if (!box.valid) {                                   // RE 0x1331E and 0x13327
        return 0.0;
    }
    const double extentFirst = box.high0 - box.low0;     // RE 0x1333B: [rsp+0x68] - [rsp+0x58]
    const double extentSecond = box.high1 - box.low1;    // RE 0x13335: [rsp+0x70] - [rsp+0x60]
    return variantScale(true, extentSecond, extentFirst, kVariantScale);
}

/** The append the rule's result feeds: RE 0x13374 calls the grow-and-append primitive 0x23BF0 with [rbx+0x208] and [rbx+0x68]. */
constexpr std::uintptr_t kVariantAppend = 0x23BF0;

static_assert(offsetof(StatBox, low0) == 0x08, "RE 0x1333B subtracts from box+0x08");
static_assert(offsetof(StatBox, low1) == 0x10, "RE 0x13335 subtracts from box+0x10");
static_assert(offsetof(StatBox, high0) == 0x18, "RE 0x1332F loads box+0x18");
static_assert(offsetof(StatBox, high1) == 0x20, "RE 0x13329 loads box+0x20");
static_assert(kVariantSource == 0x50, "RE 0x13315");
static_assert(kVariantTargetA == 0x68, "RE 0x13366");
static_assert(kVariantTargetB == 0x208, "RE 0x1335F");
static_assert(kVariantTargetB < 0x2C0, "all three offsets are inside the 0x2C0 object its constructor allocates");

}  // namespace lcns
