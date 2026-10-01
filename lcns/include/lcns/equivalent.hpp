// lcns/equivalent.hpp -- the equivalent-problem reduction (..\verify\equivalent.cpp).
//
// RECOVERED, instruction level, from re/findings_equivalent.md sections 7-8:
//
//   EquivalentSmallerDefects 0x4BC9E0   1,677 B / 382 instructions, in ..\verify\equivalent.cpp
//     4BCA3C  call 0x4F9C30            ; X = obj[+0x58]
//     4BCA44  xmm9 = 0.5               ; the weight constant
//     4BCA51  call 0x5C6100            ; side effect: zeroes a 24 byte triple (a point)
//     4BCA56  mulsd xmm9, xmm8         ; 0.5 * xmm8 (xmm8 holds the third FP argument)
//     4BCA5B  subsd xmm6, xmm9         ; xmm6 = X - 0.5*p
//     4BCA60  ucomisd xmm6, xmm7       ; compared against 0
//   and the function's own assertion text says 'defect_reduction > 0.0'.
//
// The 6 byte getter at 0x4F9C30 is literally `movsd xmm0,[rcx+0x58]; ret`, so X is a field of the
// object the reduction runs on -- NOT a Part field: the reader's `rcx` comes from the equivalent
// problem side, and offset +0x58 belongs to a record of consecutive doubles (+0x48/+0x50/+0x58/
// +0x60) that the engine supervisor 0x827F0 copies wholesale (findings, section 12).
//
// WHAT IS RECOVERED vs INFERRED
//   recovered: the FORM (x - 0.5*p), the constant 0.5, the "> 0" assertion, and the getter shape
//   inferred : what x measures (a defect measure) and where p comes from
// lcns implements the FORM, which is what the instruction sequence states. The semantics are marked
// as inferred in the registry entry below.
#pragma once

#include "lcns/recovery.hpp"

namespace lcns {
namespace equivalent {

// RE 0x4BCA44 / 0x4BCA56: the weight applied to p.
inline constexpr double kDefectWeight = 0.5;

// RE 0x4F9C30: `movsd xmm0, qword ptr [rcx + 0x58]` -- the field the reduction starts from.
inline constexpr std::size_t kReductionSourceOffset = 0x58;

// RE 0x4BCA5B: reduction = x - kDefectWeight * p.
double reduce(double x, double p);

// RE 0x4BCA60 + the assertion text 'defect_reduction > 0.0': the reduction must be strictly positive.
bool isValidReduction(double reduction);

// The reduction as the recovered object would compute it: read +0x58 through the getter shape and
// apply the weight. Provided so callers can use the recovered shape rather than its parts.
double reduceFromSource(const double* object, double p);

// RE 0x5C6100 -- transcribed literally, it is four instructions:
//     mov qword ptr [rcx], 0
//     mov qword ptr [rcx + 8], 0
//     mov qword ptr [rcx + 0x10], 0
//     ret
// so it zeroes THREE consecutive doubles (24 bytes) and returns nothing. EquivalentSmallerDefects
// calls it at 0x4BCA51, right after saving x and before the subtraction, i.e. it clears the triple
// it is about to fill in. Nothing beyond the third double is touched.
void zeroTriple(double* triple);

}  // namespace equivalent
}  // namespace lcns
