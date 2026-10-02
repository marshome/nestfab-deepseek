// lcns/include/lcns/variant.hpp -- the shared variant scale rule, RE 0x132E0.
//
// RE 0x132E0 (176 bytes) is the target of TWO exports -- ordinal 196 AddHoleToPartVariant at 0x16D00 and ordinal 198
// CNS_AddExternalBoundaryToPartVariant at 0x16D40 -- so reading it once completes two entry points. Its caller list contains
// ITSELF as well, so it walks a recursive structure.
//
// The body, read in full:
//
//     0x132E9  mov  rbx, rcx                  ; the object, which the offsets below identify as the LAUNCH ORDER
//     0x13315  lea  rdx, [rbx + 0x50]         ; +0x50 is where the ledger PROVED CommonCutProperties is embedded
//     0x13319  call 0x5CD5C0                  ; fill a box from that sub-object
//     0x1331E  cmp  byte ptr [rsp + 0x50], 0  ; the box's valid flag, the same one 0x5C8C50 tests
//     0x13327  jne  -> 0x1334F                ; an INVALID box skips the scaling entirely
//     0x13335  subsd xmm3, [rsp + 0x60]       ; extent on one axis = max - min
//     0x1333B  subsd xmm0, [rsp + 0x58]       ; and on the other
//     0x13341  ucomisd xmm3, xmm0
//     0x13345  jbe  -> 0x13382                ; WHICH EXTENT IS LARGER CHOOSES THE SCALE FACTOR
//     0x13347  mulsd xmm3, [rip + 0x99a679]   ; one constant
//     0x13382  mulsd xmm0, [rip + 0x99a63e]   ; the other
//     0x1335F  lea  rax, [rbx + 0x208]
//     0x13366  add  rbx, 0x68
//     0x13374  call 0x23BF0                   ; with both sub-object addresses
//
// so the routine measures a sub-object's two extents, compares them, and multiplies by one of two constants depending on which is
// larger -- the shape a variant takes when it has to fit a part into an opening whose limiting dimension may be either one.
//
// The two offsets +0x68 and +0x208 are also fields of the 0x2C0 launch order, and all three are inside the size its constructor
// allocates, which is the containment argument this project uses to say that a routine operates on a given object.
//
// What is written here is the RULE and the two constants' addresses; the constants themselves and the 0x23BF0 call are left
// unread on purpose, because a value guessed at would be the failure the ledger exists to refuse. The rule is what a reader needs
// and it is fully determined by the instructions above.
#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {

/** The three launch-order offsets this routine touches, each with the instruction that shows it. */
constexpr std::size_t kVariantSource = 0x50;    // RE 0x13315: lea rdx, [rbx+0x50]
constexpr std::size_t kVariantTargetA = 0x68;   // RE 0x13366: add rbx, 0x68
constexpr std::size_t kVariantTargetB = 0x208;  // RE 0x1335F: lea rax, [rbx+0x208]

/** RE 0x13347 and RE 0x13382: the scale constant, and BOTH branches load the SAME one.
 *
 * The instructions are:
 *
 *     0x13347  f2 0f 59 1d 79 a6 99 00   mulsd xmm3, [rip + 0x99a679]   disp 10069625 -> 0x9AD9C8
 *     0x13382  f2 0f 59 05 3e a6 99 00   mulsd xmm0, [rip + 0x99a63e]   disp 10069566 -> 0x9AD9C8
 *
 * two different displacements that resolve to the SAME address, where the double is 0.0001. So the branch that compares the two
 * extents exists in the code and its two arms compute the same product: **the scale is `extent * 0.0001` on either path.**
 *
 * An earlier record of this called the two constants by their DISPLACEMENTS (0x99A679 and 0x99A63E) as if they were addresses, and
 * therefore reported them as two different factors. Two displacements are not two values, and the correction is here rather than
 * only in the ledger because a header with the wrong constants in it is worse than a header with none.
 */
constexpr std::uintptr_t kVariantScaleConstant = 0x9AD9C8;   // both mulsd instructions land here
constexpr double kVariantScale = 0.0001;                     // the double at 0x9AD9C8

/** RE 0x132E0's rule: multiply the extent by the scale, and scale nothing when the box is invalid.
 *
 * The extents are computed with `subsd` at 0x13335 and 0x1333B and compared at 0x13341; the comparison selects which arm runs, and
 * both arms multiply by kVariantScale, so the comparison does not change the RESULT. What it does change is which extent is
 * multiplied when they differ -- `extentA * scale` on one arm and `extentB * scale` on the other -- so a caller that cares which
 * dimension was the larger still gets that, and a caller that only wants the scaled value gets `max(extentA, extentB) * 0.0001`.
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

static_assert(kVariantSource == 0x50, "RE 0x13315");
static_assert(kVariantTargetA == 0x68, "RE 0x13366");
static_assert(kVariantTargetB == 0x208, "RE 0x1335F");
static_assert(kVariantTargetB < 0x2C0, "all three offsets are inside the 0x2C0 object its constructor allocates");

}  // namespace lcns
