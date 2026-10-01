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

#include "lcns/recovery.hpp"

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

// --- the 16-byte record IS this point (round 189) --------------------------------------------------
// Three independent facts agree:
//   (a) 0x6DE940 returns span >> 4 (round 180), the count for 16-byte records;
//   (b) 0x707FD0 calls that same accessor and then copies the element's `[rax]` and `[rax+8]` out as two
//       doubles (0x708020 and 0x70802A), so an element of that container IS two consecutive doubles;
//   (c) 0x70C810 also computes a 16-byte count (`sar r11,4`, 0x70C85D) and ALSO applies the 47-byte gate
//       (0x70C832, round 179) -- but that gate means "at least one 48-byte record", and for a 16-byte record it
//       would mean "at least three". So (c) does NOT show the same container as (a) and (b); that part of the
//       round-189 reading was withdrawn, and only (a) and (b) carry the point conclusion.
// The layout constants are therefore tied to this type rather than merely described next to it.
inline constexpr std::size_t kPoint2dSize = 2 * sizeof(double);   // 16
static_assert(sizeof(Point2dLike) == kPoint2dSize, "the 16-byte record is a 2D point");
static_assert(kPoint2dSize == 16, "0x6DE940 shifts the byte span by four");
static_assert(kPoint2dSize != 48, "the points are not the 48-byte records of the 47-byte gate");

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


// --- almostEqual, read whole from 0x5E6060 (round 185) --------------------------------------------
// 33 instructions, FORTY-NINE callers, no text of its own:
//     5E6068  ucomisd a,b ; 5E606C jp <general> ; 5E6073 je -> eax=1     ; equal short-circuit
//     5E6083  movsd xmm5,[0x7FEFFFFFFFFFFFFF]                            ; DBL_MAX, a finiteness guard
//     5E608F  ucomisd xmm5,|a| ; jb -> 0 ; 5E609D ucomisd xmm5,|b| ; jb -> 0
//     5E60A3  maxsd xmm1,xmm4                                            ; m = max(|a|,|b|)
//     5E60B3  ucomisd 1.0,m ; ja <small>                                 ; the switch at 1.0
//     5E60BD  mulsd xmm1,[2.22045e-16] ; 5E60C5 ucomisd xmm1,|a-b| ; setae al
//     5E60D1  (small) movsd xmm1,[2.22045e-16] ; ucomisd xmm1,|a-b| ; setae al
// The epsilon is the same 2.22045e-16 as the shared read-only slot at rva 0x9DFBA0 that round 172 recorded
// from nine independent functions, and round 172's test already confirmed that value equals
// std::numeric_limits<double>::epsilon() by computation.
inline constexpr double kAlmostEqualSwitch = 1.0;                       // RE 0x5E60B3
inline constexpr std::uint64_t kDoubleMaxBits = 0x7FEFFFFFFFFFFFFFULL;  // RE 0x5E6083

inline bool almostEqual(double a, double b) {
    if (a == b) {                                   // RE 0x5E606E/0x5E6073: the equality short-circuit
        return true;
    }
    if (!(std::fabs(a) <= kSharedEpsilon * 0.0 + 1.7976931348623157e308)) {   // RE 0x5E608F: above DBL_MAX
        return false;
    }
    if (!(std::fabs(b) <= 1.7976931348623157e308)) {                          // RE 0x5E609D
        return false;
    }
    const double m = (std::fabs(a) > std::fabs(b)) ? std::fabs(a) : std::fabs(b);   // RE 0x5E60A3
    const double diff = std::fabs(a - b);                                          // RE 0x5E60B7
    if (kAlmostEqualSwitch > m) {                   // RE 0x5E60B3: the small-magnitude branch
        return diff <= kSharedEpsilon;              // RE 0x5E60D1/0x5E60D9
    }
    return diff <= m * kSharedEpsilon;              // RE 0x5E60BD/0x5E60C5
}


// --- the polygon area, read whole from 0x70C810 (round 190) ----------------------------------------
//     70C881  movsd xmm0,[r8-0x10]      ; the previous point's y
//     70C887  sub r8,0x10               ; a SIXTEEN-byte step: points
//     70C88B  movsd xmm1,[r8+8]         ; its x
//     70C894  addsd xmm0,[r9-0x10]      ; + the other point's y
//     70C89A  subsd xmm1,[r9-8]         ; (x_a - x_b)
//     70C8A0  mulsd xmm0,xmm1           ; (y_a + y_b) * (x_a - x_b)
//     70C8A4  addsd xmm0,xmm2           ; accumulate
//     70C8EE  mulsd xmm0,[0.5]          ; * 0.5 -> the area
// with 70C8D9/70C8DE (`idiv r11 ; shl rdx,4`) wrapping the index. That is the shoelace form of the area.
inline constexpr double kAreaHalf = 0.5;      // RE 0x70C8EE (the shared block's 0.5 slot)

// RE 70C8A0/70C8A4: one shoelace term, and the accumulation the loop performs.
inline double shoelaceTerm(const Point2dLike& a, const Point2dLike& b) {
    return (a.y + b.y) * (a.x - b.x);          // RE 0x70C894/0x70C89A/0x70C8A0
}

inline double polygonArea(const Point2dLike* points, std::size_t count) {
    if (points == nullptr || count < 3) {       // RE 0x70C832: the span > 47 gate means at least three points
        return 0.0;
    }
    double sum = 0.0;                           // RE 0x70C87D
    for (std::size_t i = 0; i < count; ++i) {
        sum += shoelaceTerm(points[i], points[(i + 1) % count]);   // RE 0x70C8D9: the wrap-around index
    }
    return kAreaHalf * sum;                     // RE 0x70C8EE
}


// --- the equal-or-sign test 0x5E78D0 applies three times (round 192) ------------------------------
//     5E79A7 call 0x5E6060                     ; almostEqual
//     5E79B7 ucomisd xmm6,xmm7 ; seta r14b ; lea r14d,[r14+r14-1]     ; equal -> 0, else +/-1
// and the same pair of instructions is repeated at 5E79F2, 5E7A26 and 5E7A57, with the results compared at
// 5E7A62. So the predicate's atom is "almost equal, otherwise sign", applied to a pair of coordinates.
inline int signCompare(double a, double b) {
    if (almostEqual(a, b)) {          // RE 0x5E79A7/0x5E79AC
        return 0;
    }
    return signOf(a - b);             // RE 0x5E79B7/0x5E79E2: seta then the {-1,+1} mapping
}

// RE the body applies that atom three times before combining the results (0x5E7A62).
inline constexpr int kPredicateSignCount = 3;


// --- the 2D midpoint of 0x707FD0 (round 193) -------------------------------------------------------
//     708083  movsd xmm0,[rbx-0x10] ; 70808A addsd xmm0,[rbx]     ; prev.x + cur.x
//     70808E  movsd xmm1,[0.5]      ; 708096 mulsd xmm0,xmm1      ; * 0.5
//     70809A  movsd [r12],xmm0
//     7080A0  movsd xmm0,[rbx-8] ; 7080A5 addsd xmm0,[rbx+8] ; 7080AA mulsd xmm0,xmm1 ; 7080AE [r12+8]
// So the routine picks a consecutive pair of points and writes the midpoint of that pair.
inline Point2dLike midpoint2d(const Point2dLike& a, const Point2dLike& b) {
    return Point2dLike{(a.x + b.x) * kSharedHalf, (a.y + b.y) * kSharedHalf};   // RE 708096/7080AA
}

// RE 0x70806C: the predicate that decides how far the walk advances. It is shared -- the twins of round 174
// call it too (0x74B430/0x74B700) -- so it is the next thing worth reading.
inline constexpr unsigned long kMidpointWalkPredicate = 0x72DAC0;


// --- the point comparison of 0x72DAC0, polarity settled in round 195 ---------------------------------
// Twelve callers, including the twins of round 174 and the midpoint walk of round 193. Read whole,
// INCLUDING the tail that round 194 had not reached:
//     72DAC8  ucomisd b.x,a.x ; jp <general> ; je 0x72DB39      ; x nearly equal -> go and look at y
//     72DB2F  ucomisd m*eps,|dx| ; jb 0x72DBCA                  ; dx EXCEEDS eps -> 72DBCA
//     72DBCA  mov eax,1 ; ret                                   ; -> TRUE
//     72DB49  y nearly equal -> mov eax,0 ; je 0x72DBB0          ; -> FALSE
//     72DBA7  setb al                                            ; dy EXCEEDS eps -> TRUE
// So the result is `!(x nearly equal) || !(y nearly equal)` -- the negation of "both coordinates nearly equal".
// The same machinery as almostEqual is applied to each coordinate (sign mask, DBL_MAX guard, the 1.0 switch and
// 2.22045e-16), which is why this composes with the rest of the chain.
inline constexpr unsigned long kPointComparePredicate = 0x72DAC0;   // RE the address itself

inline bool pointAlmostEqual(const Point2dLike& a, const Point2dLike& b) {
    return almostEqual(a.x, b.x) && almostEqual(a.y, b.y);   // RE the branches above
}

inline bool pointsDiffer(const Point2dLike& a, const Point2dLike& b) {
    return !pointAlmostEqual(a, b);                          // RE 0x72DAC0's own polarity
}


// --- the bounding box of 0x72DBD0 (round 202) ------------------------------------------------------
//     72DBEE movsd xmm1,[0x7FEFFFFFFFFFFFFF]   ; +DBL_MAX     72DBF9 movsd xmm0,[0xFFEFFFFFFFFFFFFF]
//     72DC01 [rbx]=xmm1 (min x)  72DC05 [rbx+8]=xmm1 (min y)  72DC0A [rbx+0x10]=xmm0 (max x)
//     72DC12 [rbx+0x18]=xmm0 (max y)
//     per point: 72DC68 lowers min x, 72DC72 raises max x, 72DC82 lowers min y, 72DC8D raises max y
// so this computes the axis-aligned bounding box of a point list. Its result layout is the same four doubles that
// rounds 177/200 found at +8/+0x10/+0x18/+0x20, which settles that object as a box in two opposite corners.
inline constexpr std::uint64_t kBoundingMaxBits = 0x7FEFFFFFFFFFFFFFULL;   // RE 0x72DBEE
inline constexpr std::uint64_t kBoundingMinBits = 0xFFEFFFFFFFFFFFFFULL;   // RE 0x72DBF9

struct Box2d {
    double minX;    // RE +0x00
    double minY;    // RE +0x08
    double maxX;    // RE +0x10
    double maxY;    // RE +0x18
};

inline constexpr std::size_t kBoxMinXOffset = 0x00;   // RE 0x72DC01
inline constexpr std::size_t kBoxMinYOffset = 0x08;   // RE 0x72DC05
inline constexpr std::size_t kBoxMaxXOffset = 0x10;   // RE 0x72DC0A
inline constexpr std::size_t kBoxMaxYOffset = 0x18;   // RE 0x72DC12
inline constexpr std::size_t kBoxStride = 0x20;       // the four doubles
inline constexpr std::size_t kBoxPointStride = 0x10;  // RE 0x72DC96: the walk steps one point

inline Box2d boundingBox(const Point2dLike* points, std::size_t count) {
    Box2d b{1.7976931348623157e308, 1.7976931348623157e308,
            -1.7976931348623157e308, -1.7976931348623157e308};   // RE 0x72DC01..0x72DC12
    if (points == nullptr) {
        return b;
    }
    for (std::size_t i = 0; i < count; ++i) {
        const Point2dLike& p = points[i];
        if (b.minX > p.x) { b.minX = p.x; }     // RE 0x72DC62/0x72DC68
        if (p.x > b.maxX) { b.maxX = p.x; }     // RE 0x72DC6C/0x72DC72
        if (b.minY > p.y) { b.minY = p.y; }     // RE 0x72DC7C/0x72DC82
        if (p.y > b.maxY) { b.maxY = p.y; }     // RE 0x72DC87/0x72DC8D
    }
    return b;
}

// --- the tag dispatch of 0x5E7790 (round 202) ------------------------------------------------------
//     5E7798 cmp rax,1 ; 5E77A4 cmp rax,2 ; 5E77AA test rax,rax   on [rdx]   -- three cases
//     5E77D9 cmp eax,1 ; 5E77DC sete al                            -- the result is `eax == 1`
inline constexpr int kGeometryDispatchCases = 3;

}  // namespace lcns
LCNS_STRUCTURAL(geom.ratio_family);   // 50.0 margin then the almostEqual-guarded ratio
