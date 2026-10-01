// include/lcns/compare.hpp -- the comparator of the 284-byte twins (goal round 174).
//
// 0x74B430 and 0x74B700 are 83 instructions each. Compared instruction by instruction they are identical
// except for (a) jump targets, (b) their own constant slots, and (c) one call each to their own 284-byte
// sibling -- 0x74B390 versus 0x74B660. That is one template instantiated twice, with its two helpers.
//
// The return value is built verbatim:
//     pxor xmm3,xmm3 ; ucomisd xmm0,xmm3 ; seta al ; lea eax,[rax+rax-1]
// and the guards above it take an absolute value (andpd against the sign mask) and compare it with a constant
// and with that constant multiplied by the parameter stored at [rsp+0x20] -- a tolerance.
#pragma once

#include <cmath>

namespace lcns {

// RE `seta al ; lea eax,[rax+rax-1]`: the code maps {0,1} onto {-1,+1}.
inline int signOf(double value) {
    return (value > 0.0) ? 1 : -1;          // RE 0x74B4C4..0x74B4D8 (and 0x74B794..0x74B7A8 in the twin)
}

// RE the `je` path the twins take when the value compares equal to zero: the result is then 0.
inline int compareToZero(double value) {
    if (value == 0.0) {                     // RE the `je 0x74B466` / `je 0x74B736` guard
        return 0;
    }
    return signOf(value);                   // RE the seta/lea pair
}

// RE 0x74B430/0x74B700 comparing |value| with a constant times the [rsp+0x20] parameter: a tolerance test.
// The absolute value is not an assumption -- the guards apply `andpd` with the sign-mask constant first, which
// is fabs -- so the comparison is on |value|.
// RECORDED but NOT implemented in full: the order of the two gates was not read far enough to transcribe.
inline bool withinTolerance(double value, double tolerance) {
    return std::fabs(value) <= tolerance;      // RE the andpd sign-mask read before the comparisons
}

}  // namespace lcns
