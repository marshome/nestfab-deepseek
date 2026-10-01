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
#include <cstdint>

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


// --- the scale the comparator's tolerance is relative to (round 176) ------------------------------
// RE 0x7043B0 (17 instructions, 6 callers), read whole:
//     7043B0  movsd xmm1,[0x7FFFFFFFFFFFFFFF]      ; the sign mask, i.e. fabs
//     7043C1  andpd xmm4,xmm1   ; |v1|      7043CA andpd xmm0,xmm1  ; |v0|
//     7043CE  maxsd xmm4,xmm0
//     7043D7  andpd xmm3,xmm1   ; |v2|      7043E3 andpd xmm2,xmm1  ; |v3|
//     7043DB  maxsd xmm3,xmm4   ; 7043EF maxsd xmm2,xmm3
//     7043E7  movsd xmm1,[1.0]  ; 7043F3 maxsd xmm1,xmm2           ; max(1, the four magnitudes)
//     7043F7  movsd [rcx],xmm1
// So the result is the largest magnitude of the four components, never below 1.0. The two helpers store it
// through their r9 argument, and the twins then compare a cross product against a constant times this scale:
// that is what makes their comparison scale-invariant.
inline constexpr std::uint64_t kSignMask = 0x7FFFFFFFFFFFFFFFULL;   // RE 0x7043B0

inline double relativeScale(double v0, double v1, double v2, double v3) {
    double m = 1.0;                                   // RE 0x7043E7: the floor
    m = (std::fabs(v0) > m) ? std::fabs(v0) : m;       // RE 0x7043CA/0x7043CE
    m = (std::fabs(v1) > m) ? std::fabs(v1) : m;       // RE 0x7043C1
    m = (std::fabs(v2) > m) ? std::fabs(v2) : m;       // RE 0x7043D7
    return (std::fabs(v3) > m) ? std::fabs(v3) : m;    // RE 0x7043E3/0x7043F3
}


// --- the four-field formulas of 0x5E6360 (round 177) ----------------------------------------------
// The object it works on has doubles at +8, +0x10, +0x18 and +0x20; read from the loads at
// 0x5E637F, 0x5E6385, 0x5E637A and 0x5E638F, and stored back through rax (0x5E63E1).
inline constexpr std::size_t kObjectFieldA = 0x08;    // RE 0x5E637F
inline constexpr std::size_t kObjectFieldB = 0x10;    // RE 0x5E6385
inline constexpr std::size_t kObjectFieldC = 0x18;    // RE 0x5E637A
inline constexpr std::size_t kObjectFieldD = 0x20;    // RE 0x5E638F

// RE 0x5E6394/0x5E639C/0x5E63A0: the product of the two differences.
inline double differenceProduct(double a, double b, double c, double d) {
    return (c - a) * (d - b);
}

// RE 0x5E63BD/0x5E63DD: the mean of two fields, computed as (x + y) * 0.5 with the 0.5 from the shared block
// at rva 0x9DFBD0.
inline double midpointOf(double x, double y) {
    return (x + y) * kSharedHalf;
}

// RE 0x5E63AA/0x5E63D5: doubling then halving, i.e. the value itself.
inline double doubledThenHalved(double x) { return (x + x) * kSharedHalf; }

// RE 0x5E63B6: the all-ones word stored at +0x28, which is -1 read as a signed integer.
inline constexpr std::int64_t kSentinelMinusOne = -1;

}  // namespace lcns
