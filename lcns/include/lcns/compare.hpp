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


// --- the quantity the twins compare (round 175) ---------------------------------------------------
// RE 0x74B390 and 0x74B660 (34 instructions each, instruction-for-instruction identical):
//     74B395 movsd xmm5,[rcx] ; 74B399 movsd xmm4,[rcx+8]     ; A
//     74B39E movsd xmm1,[r8]  ; 74B3A3 movsd xmm0,[r8+8]      ; C
//     74B3A9 movsd xmm3,[rdx] ; 74B3B9 movsd xmm2,[rdx+8]     ; B
//     74B3AD subsd xmm1,xmm5 ; 74B3BE subsd xmm0,xmm4         ; C - A
//     74B3CC subsd xmm3,xmm5 ; 74B3D5 subsd xmm2,xmm4         ; B - A
//     74B410 mulsd xmm1,[rsp+0x50] ; 74B41C mulsd xmm0,[rsp+0x58] ; 74B422 subsd xmm0,xmm1
// so the result is a 2D cross product: the signed area of the triangle ABC, i.e. the orientation test.
struct Point2dLike {
    double x;
    double y;
};

inline double crossProduct2d(const Point2dLike& a, const Point2dLike& b, const Point2dLike& c) {
    const double acx = c.x - a.x;      // RE 0x74B3AD
    const double acy = c.y - a.y;      // RE 0x74B3BE
    const double abx = b.x - a.x;      // RE 0x74B3CC
    const double aby = b.y - a.y;      // RE 0x74B3D5
    return abx * acy - acx * aby;      // RE 0x74B410/0x74B41C/0x74B422
}

// RE 0x74B40C: one component of the result is written through the fourth argument (r9), and the value stored
// is c.x - a.x (the [rsp+0x30] slot, i.e. AC.x). B takes no part in that component, so no function is written
// for it here -- a helper that ignored one of its own parameters would be a warning, not a recovery.

}  // namespace lcns
