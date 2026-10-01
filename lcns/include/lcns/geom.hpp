// lcns/geom.hpp -- exact fixed-point geometry core.
//
// Mirrors the reverse-engineered geometry kernel of liblcns.dll:
//   * two kernels: `..\exact\*` (int64 fixed point, 128-bit determinants) and
//     `..\geom\*` (double).  This header implements the exact kernel plus the double
//     interchange layer.
//   * fixed-point scale = 1e10  (RE constant @ RVA 0x9AD708; the compiler emitted the
//     equivalent `v/360*3.6e12 + 0.5` then floor).
//   * `Polygon` layout matches the recovered member offsets exactly:
//         +0x00  Ring  external      (std::vector<Point>, 24 bytes)
//         +0x18  std::vector<Ring> inners
//     which is why NoFitGetNumberOfExternalPolygons (0x89D0) divides a vector by 48 and
//     DeleteNoFitGeometry (0x8A10) recurses with a 0x30 stride.
//   * Minkowski/No-Fit-Polygon is the boundary convolution performed by
//     `..\exact\convolution.cpp::ConvolutionRaw` (0x596F20 -> core 0x596100).
//     That code NEVER calls atan2: it buckets edge directions into 4 quadrants using
//     only the SIGNS of (dx,dy) and then merges by exact polar order:
//         q1 = (dx > 0, dy > 0)
//         q2 = (dx > 0, dy <= 0)
//         q3 = (dx <= 0, dy < 0)
//         q4 = otherwise
//     We reproduce that scheme verbatim.
//   * polygon offsetting is done in N incremental steps with
//     N = floor(dist / step + 0.5)  (RE 0x58A7E0), and outer rings get +gap while inner
//     rings get -gap (RE AddInflatedToolPathToPart 0x12C60 flips the sign with `btc`).
//     There is no JoinType/MiterLimit concept in the original.
#pragma once

#include <cstdint>
#include "lcns/recovery.hpp"
#include <cstddef>
#include <cmath>
#include <string>
#include <vector>

namespace lcns::geom {

// ---------------------------------------------------------------------------
// 128-bit signed integer, portable (the original used imul/mul + adc/sbb).
// ---------------------------------------------------------------------------
struct Int128 {
    std::uint64_t lo = 0;
    std::int64_t hi = 0;  // signed high part

    bool isZero() const { return lo == 0 && hi == 0; }
    bool isNegative() const { return hi < 0; }
    int sign() const { return isZero() ? 0 : (isNegative() ? -1 : 1); }
    // Note: the naive `hi * 2^64 + lo` loses all precision when hi < 0 and |value| is small
    // (catastrophic cancellation). Negate first so both magnitudes stay small.
    double toDouble() const {
        if (hi >= 0) {
            return static_cast<double>(hi) * 18446744073709551616.0 + static_cast<double>(lo);
        }
        const std::uint64_t mlo = ~lo + 1;
        const std::int64_t mhi = ~hi + (mlo == 0 ? 1 : 0);
        return -(static_cast<double>(mhi) * 18446744073709551616.0 + static_cast<double>(mlo));
    }
};

inline Int128 mul64(std::int64_t a, std::int64_t b) {
    const bool neg = (a < 0) != (b < 0);
    const std::uint64_t ua = a < 0 ? (~static_cast<std::uint64_t>(a) + 1) : static_cast<std::uint64_t>(a);
    const std::uint64_t ub = b < 0 ? (~static_cast<std::uint64_t>(b) + 1) : static_cast<std::uint64_t>(b);
    const std::uint64_t a0 = ua & 0xFFFFFFFFull, a1 = ua >> 32;
    const std::uint64_t b0 = ub & 0xFFFFFFFFull, b1 = ub >> 32;
    const std::uint64_t p00 = a0 * b0;
    const std::uint64_t p01 = a0 * b1;
    const std::uint64_t p10 = a1 * b0;
    const std::uint64_t p11 = a1 * b1;
    const std::uint64_t mid = (p00 >> 32) + (p01 & 0xFFFFFFFFull) + (p10 & 0xFFFFFFFFull);
    Int128 r;
    r.lo = (mid << 32) | (p00 & 0xFFFFFFFFull);
    r.hi = static_cast<std::int64_t>(p11 + (p01 >> 32) + (p10 >> 32) + (mid >> 32));
    if (neg) {  // two's complement negation
        r.lo = ~r.lo + 1;
        r.hi = ~r.hi + (r.lo == 0 ? 1 : 0);
    }
    return r;
}

inline Int128 add128(const Int128& a, const Int128& b) {
    Int128 r;
    r.lo = a.lo + b.lo;
    r.hi = a.hi + b.hi + (r.lo < a.lo ? 1 : 0);
    return r;
}
inline Int128 sub128(const Int128& a, const Int128& b) {
    Int128 r;
    r.lo = a.lo - b.lo;
    r.hi = a.hi - b.hi - (a.lo < b.lo ? 1 : 0);
    return r;
}

// ---------------------------------------------------------------------------
// fixed point
// ---------------------------------------------------------------------------
using fixed_t = std::int64_t;
inline constexpr double kScale = 1e10;                 // RE: 1e10 @ 0x9AD708

// RE: the tolerance of the `Contains(window)` test. The check itself is INLINED at its assertion
// sites (there is no separate callee), and its shape was read out of 0x1C1A60, the builder of the
// assertion message "old.Contains(nnp.m_window)":
//     1C1AC2  xmm1 = [rbx+0x60] ; 1C1ABA xmm0 = [0x9BFD30] ; 1C1ACC xmm1 += xmm0
//     1C1AC7  xmm6 = [rax+0x60] ; 1C1AD5 ucomisd xmm1, xmm6 ; jae -> the failure path
// i.e. a window-containment test over the object's +0x60/+0x68 pair with this epsilon.
// See findings_geometry.md, appendix "点在多边形内 / 绕数例程的定位结果".
inline constexpr double kWindowContainEpsilon = 0.001;  // RE: 0.001 @ 0x9BFD30
inline constexpr fixed_t kScaleI = 10000000000ll;

// RE: round(v * 1e10) implemented as floor(v/360*3.6e12 + 0.5)
inline fixed_t toFixed(double v) { return static_cast<fixed_t>(std::floor(v * kScale + 0.5)); }
inline double toDouble(fixed_t v) { return static_cast<double>(v) / kScale; }

struct FPoint {
    fixed_t x = 0, y = 0;
    bool operator==(const FPoint& o) const { return x == o.x && y == o.y; }
    bool operator!=(const FPoint& o) const { return !(*this == o); }
};

struct Point {
    double x = 0, y = 0;
};

// ---------------------------------------------------------------------------
// exact predicates (RE: 128-bit cross product at 0x58E450)
// ---------------------------------------------------------------------------
// sign of (b-a) x (c-a); > 0 => counter clockwise
LCNS_RECOVERED(geom.orient128);
inline int orient2d(const FPoint& a, const FPoint& b, const FPoint& c) {
    const Int128 ab = mul64(b.x - a.x, c.y - a.y);
    const Int128 ac = mul64(b.y - a.y, c.x - a.x);
    return sub128(ab, ac).sign();
}
// squared-ish comparison of |v| and |w| in the same quadrant: sign of cross(v,w)
inline int crossSign(const FPoint& v, const FPoint& w) {
    const Int128 a = mul64(v.x, w.y);
    const Int128 b = mul64(v.y, w.x);
    return sub128(a, b).sign();
}

// ---------------------------------------------------------------------------
// rings / polygons  (layout deliberately matches the recovered offsets)
// ---------------------------------------------------------------------------
using Ring = std::vector<FPoint>;

struct Polygon {
    Ring external;                 // +0x00  m_external_path
    std::vector<Ring> inners;      // +0x18  m_internal_paths
};

using MultiPolygon = std::vector<Polygon>;  // Geom::MultiPolygon

Ring toRing(const std::vector<Point>& pts);
std::vector<Point> toPoints(const Ring& r);

// exact doubled signed area of a ring
Int128 signedArea2(const Ring& r);
bool isCCW(const Ring& r);
double area(const Ring& r);
double perimeter(const Ring& r);

struct Box {
    FPoint min{}, max{};
    bool valid = false;
    double width() const { return toDouble(max.x - min.x); }
    double height() const { return toDouble(max.y - min.y); }
    double area() const { return width() * height(); }
};
Box bounds(const Ring& r);
Box bounds(const Polygon& p);
Box bounds(const MultiPolygon& mp);

// remove duplicate and collinear points (RE: ..\exact\path.cpp RemoveAlignedCollinearPoints)
Ring removeAlignedCollinearPoints(const Ring& r, fixed_t tolerance = 0);

Ring reverse(const Ring& r);
Ring translate(const Ring& r, FPoint d);
// reflect about the origin (negation of the point set); orientation is not preserved
Ring negateRing(const Ring& r);
// same point set, traversed counter clockwise
Ring orientCCW(const Ring& r);
// true when no two non adjacent edges intersect (used to validate offset results)
bool isSimple(const Ring& r);

// winding-number point in polygon using the exact predicate
bool pointInRing(const Ring& r, FPoint p);
bool pointInPolygon(const Polygon& p, FPoint q);

// convex hull (monotone chain, exact predicate)
Ring convexHull(Ring pts);

// Ear clipping triangulation of a simple ring (exact orientation tests).
// Triangles are returned counter clockwise. Minkowski convolution is only exact for convex
// operands, so the boolean layer uses this to decompose non convex rings.
std::vector<Ring> triangulate(const Ring& r);

// ---------------------------------------------------------------------------
// fixed point angle  (RE: 0x5C22D0, 157 B, in the Geom/ring translation unit)
// ---------------------------------------------------------------------------
// Converts a direction vector into a fixed point angle in DEGREES scaled by 1e10, wrapped into
// [0, 360 * 1e10). Recovered instruction for instruction:
//
//     if (dx == 0 && dy == 0) return 0;
//     a = atan2(dy, dx);              // 0x634C70 is the only atan2 in the image (x87 fpatan)
//     a = a / 6.283185307179586;      // 0x9DE758 = 2*pi
//     a = a * 3600000000000.0;        // 0x9DE740 = 360 * 1e10
//     a = a + 0.5;                    // 0x9DE750
//     r = (fixed_t)round(a);          // 0x62FA20
//     while (r < 0) r += 3600000000000;            // 0x5C231F wrap
//     while (r > 3600000000000) r -= 3600000000000;  // 0x5C2360 wrap
//     return r;
inline constexpr fixed_t kFullTurnFixedDegrees = 3600000000000ll;  // 360 * 1e10

fixed_t angleToFixedDegrees(double dx, double dy);
fixed_t angleToFixedDegrees(fixed_t dx, fixed_t dy);

// ---------------------------------------------------------------------------
// Minkowski convolution  (RE: ..\exact\convolution.cpp::ConvolutionRaw)
// ---------------------------------------------------------------------------
// quadrant bucket, exactly the RE classification
inline int quadrantOf(fixed_t dx, fixed_t dy) {
    if (dx > 0 && dy > 0) return 1;
    if (dx > 0 && dy <= 0) return 2;
    if (dx <= 0 && dy < 0) return 3;
    return 4;
}

// The RE buckets are geometric quadrants, but a counter-clockwise sweep from angle 0
// visits them in the order 1 -> 4 -> 3 -> 2. Sorting needs that traversal rank.
inline int quadrantRank(int q) {
    switch (q) {
        case 1: return 0;
        case 4: return 1;
        case 3: return 2;
        case 2: return 3;
        default: return 0;
    }
}

struct ConvEdge {
    fixed_t dx = 0, dy = 0;
    int quadrant = 1;
    int ring = 0;   // 0 = first operand, 1 = second
    std::size_t index = 0;
    FPoint origin{};
};

// build the directed edge records (RE 0x595A80 / 0x596000)
std::vector<ConvEdge> buildEdges(const Ring& a, const Ring& b);

// merge two edge sequences by exact polar order (no atan2 anywhere)
// Raw boundary convolution, faithful to `..\exact\convolution.cpp::ConvolutionRaw` (0x596F20):
// both edge lists are entered at their lowest vertex and merged cyclically by angle, and every
// revisit of an already visited point closes a loop (or splits a pinched one). For convex
// operands this yields a single loop; non convex operands are not angle monotone, so the caller
// must decompose them first (see boolean::minkowskiMulti). The whole loop set is anchored so
// that its bounding box minima equal (minA + minB).
std::vector<Ring> convolveRingLoops(const Ring& a, const Ring& b);

Ring convolveBoundaries(const Ring& a, const Ring& b);

// Minkowski sum of two rings (boundary convolution + closing)
Ring minkowskiSum(const Ring& a, const Ring& b);

// No-Fit Polygon of `a` w.r.t. `b`: the locus of translations of `b` that touch `a`.
// Convention: nfp(a, b) = minkowskiSum(a, reverse(b)).
Ring nfp(const Ring& a, const Ring& b);

// ---------------------------------------------------------------------------
// offsetting  (RE 0x58A7E0 / NewExternalOffset 0x58B520)
// ---------------------------------------------------------------------------
struct OffsetParams {
    double step = 0.01;    // chosen so that N = floor(dist/step + 0.5) stays small
    bool clean = true;     // removeAlignedCollinearPoints at the end
};

// one offset pass by `dist` (>0 grows a CCW ring, shrinks a CW ring)
Ring offsetOnce(const Ring& r, double dist);

// N incremental passes, exactly the RE scheme
Ring offsetRing(const Ring& r, double dist, const OffsetParams& p = {});

// polygon level helper: outer ring gets +gap, inner rings get -gap
// (RE: AddInflatedToolPathToPart 0x12C60 flips the sign for inners)
Polygon inflatePolygon(const Polygon& p, double gap, const OffsetParams& op = {});
MultiPolygon inflatePolygon(const MultiPolygon& mp, double gap, const OffsetParams& op = {});

// ---------------------------------------------------------------------------
// misc predicates used by validity checks / common cut detection
// ---------------------------------------------------------------------------
bool segmentsIntersect(const FPoint& p1, const FPoint& p2, const FPoint& q1, const FPoint& q2);
bool segmentCollinearOverlap(const FPoint& p1, const FPoint& p2, const FPoint& q1, const FPoint& q2,
                            double* overlapLength = nullptr);
bool ringsOverlap(const Ring& a, const Ring& b);  // boundaries intersect or one inside other
double distancePointSegment(const Point& p, const Point& a, const Point& b);

std::string toWkt(const Ring& r);
std::string toWkt(const Polygon& p);
std::string toWkt(const MultiPolygon& mp);

// RE 0x15620 `AddRectanglePart` (374 B / 79 instructions), transcribed because the CORNER ORDER is
// part of the algorithm: the original lays a 12 double (0x60 byte) record on the stack as
//     { x0, y0, 0,  x1, y0, 0,  x1, y1, 0,  x0, y1, 0 }
// built from the two opposite corners (xmm2,xmm3) and (xmm7,xmm6), zero filling every third slot,
// then allocates 96 bytes with operator new (0x998500) and hands the consumer r8d = 4. Nothing else
// is computed here -- no area, no bounds -- so this is the whole of what the routine decides.
struct RectCorner {
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;   // the third slot of every triple is zero in the original
};

// RE the same three Add* entries (0x15620 AddRectanglePart, 0x13800 AddHoleToPart,
// 0x13410 AddExternalBoundaryToPart) all build the same thing: a stack record of 12 doubles
// (0x60 bytes), the count 4 written to a field, then operator new(0x60) at 0x998500 and a call into
// the shared "attach geometry to part" routine. The two numbers below are therefore not guesses:
// they are the allocation size and the point count those routines use.
inline constexpr int kRectangleCornerCount = 4;        // RE 0x156D1 r8d = 4, 0x138DE [rsp+0x40] = 4
inline constexpr std::size_t kRectangleRecordBytes = 0x60;   // RE 0x1566F / 0x138xx ecx = 0x60

// RE the three Add* entries compared side by side (goal round 49). They differ ONLY in data:
//   0x15620 AddRectanglePart          -> final call 0x14d10                       no constants
//   0x13410 AddExternalBoundaryToPart -> 0x64c940 then 0x1ba30, 0.292893 + 0.0001
//   0x13800 AddHoleToPart             -> 0x64c940 then 0x5cd5c0, 0.292893 + 0.0001, and one extra
//                                        flag store [rsp+0x28] = 1 that the other two do not have
// All three build the same 0x60 byte four corner record and all three call operator new(0x60).
enum class PartGeometryKind {
    Rectangle = 0,          // RE 0x15620, final step 0x14d10
    ExternalBoundary = 1,   // RE 0x13410, 0.292893 / 0.0001, no hole flag
    Hole = 2,               // RE 0x13800, 0.292893 / 0.0001, plus the flag [rsp+0x28] = 1
};

// RE 0x9AD9D0, loaded by both the boundary and the hole path. The VALUE is recovered; reading it as
// 1 - 1/sqrt(2) is an inference (it fits to all six digits), and no symbol states it.
inline constexpr double kCornerOffset = 0.292893;
// RE 0x9AD9C8, an epsilon both paths use (hole: twice, boundary: once).
inline constexpr double kGeometryEpsilon = 0.0001;

// RE the final call each Add* entry makes, read from the call sites in round 49:
//   0x15620 AddRectanglePart          -> 0x14D10 last
//   0x13410 AddExternalBoundaryToPart -> 0x64C940 then 0x1BA30
//   0x13800 AddHoleToPart             -> 0x64C940 then 0x5CD5C0, plus one extra flag store
// Kept as data so a port can name the step it reproduces instead of guessing which routine it is.
inline constexpr unsigned long kRectangleFinalStep = 0x14D10;   // RE 0x15620
inline constexpr unsigned long kBoundaryPrepStep = 0x64C940;    // RE 0x13410 and 0x13800
inline constexpr unsigned long kBoundaryFinalStep = 0x1BA30;    // RE 0x13410
inline constexpr unsigned long kHoleFinalStep = 0x5CD5C0;       // RE 0x13800

// RE 0x5ED8C0 (757 B), the routine only the EXTERNAL BOUNDARY path uses. It loads exactly six
// doubles, and all six are quadrant angles:
//     1.570796 = pi/2      3.141593 = pi        4.712389 = 3pi/2      6.283185 = 2pi
//     7.853982 = 2pi + pi/2                    10.995574 = 2pi + 3pi/2
// The last two are the first two shifted by a full turn, so the routine walks directions in 90 degree
// steps and WRAPS PAST A FULL TURN -- which is what a corner arc needs, and it agrees with the
// 0.292893 = 1 - 1/sqrt(2) corner offset that both the boundary and the hole path load (round 49).
// The VALUES are recovered; "these are quadrant angles" is the reading, and it fits exactly.
inline constexpr double kQuarterTurnHalfPi = 1.570796;          // RE 0x5ED8C0
inline constexpr double kQuarterTurnPi = 3.141593;              // RE 0x5ED8C0
inline constexpr double kQuarterTurn3HalfPi = 4.712389;         // RE 0x5ED8C0
inline constexpr double kQuarterTurn2Pi = 6.283185;             // RE 0x5ED8C0
inline constexpr double kQuarterTurn2PiPlusHalfPi = 7.853982;   // RE 0x5ED8C0
inline constexpr double kQuarterTurn2PiPlus3HalfPi = 10.995574; // RE 0x5ED8C0

// The four quadrant directions the routine steps through, in the order the constants suggest.
inline void quarterTurnDirections(double out[4]) {
    out[0] = kQuarterTurnHalfPi;
    out[1] = kQuarterTurnPi;
    out[2] = kQuarterTurn3HalfPi;
    out[3] = kQuarterTurn2Pi;
}

// RE the call graph, rounds 51-52: only the EXTERNAL BOUNDARY route reaches the quadrant-angle
// routine. The chain is 0x13410 AddExternalBoundaryToPart -> 0x1BA30 (boundary only) -> 0x1B910
// (boundary only) -> 0x5ED8C0 (757 B, the six quadrant angles and the wrap past a full turn), and the
// hole route (0x13800 -> 0x5CD5C0 -> 0x5CD360 / 0x5C8A10) never touches it, while the plain
// rectangle route (0x15620 -> 0x14D10) does not either. So "this kind gets corner arcs" is a fact
// about the call graph, not a guess about geometry.
inline bool usesCornerArcs(PartGeometryKind kind) {
    return kind == PartGeometryKind::ExternalBoundary;
}

// RE 0x13800 AddHoleToPart, the store at 0x1399C: `mov dword ptr [rsp + 0x28], 1`. It is the ONE
// thing the hole route does that the external-boundary route (0x13410) does not -- the two otherwise
// load the same constants and call the same prep routine. So the hole is marked by a flag, and what
// the flag is read for is not recovered yet; the offset and the value are.
inline constexpr std::size_t kHoleExtraFlagOffset = 0x28;   // RE 0x1399C
inline constexpr int kHoleExtraFlagValue = 1;               // RE 0x1399C

// RE the external-boundary call chain, walked step by step in rounds 50-54. Kept as named data so the
// port can say which routine of the chain it reproduces:
//   0x13410 AddExternalBoundaryToPart
//     -> 0x1BA30 (boundary only, 198 B)
//       -> 0x1B910 (boundary only, 278 B)
//         -> 0x5ED8C0 (757 B, the six quadrant angles and the wrap past a full turn)
//           -> 0x5CB400 (45 B leaf, one 0.5) and 0x5ED3D0 (1183 B) and 0x634C70 (41 B leaf)
// The hole route and the plain rectangle route never enter this chain (see usesCornerArcs).
inline constexpr unsigned long kBoundaryChainStep1 = 0x1BA30;   // RE 0x13410
inline constexpr unsigned long kBoundaryChainStep2 = 0x1B910;   // RE 0x1BA30
inline constexpr unsigned long kBoundaryChainStep3 = 0x5ED8C0;  // RE 0x1B910
inline constexpr unsigned long kBoundaryChainStep4 = 0x5ED3D0;  // RE 0x5ED8C0, the 1183 B body

// RE 0x5ED3D0, the two uses of 2pi (goal round 55), which CONFIRM the wrap that round 52 only read
// off the constant list:
//     5ED828  subsd xmm0, [2pi]   ; angle -= 2pi
//     5ED830  movsd [rax], xmm0   ; store it back
//     5ED85E  addsd xmm0, [2pi]   ; angle += 2pi
//     5ED866  movsd [rax], xmm0   ; store it back
// Each site is a SINGLE adjustment, not an unbounded loop, and the two are separate branches (the
// jump into 5ED828 comes from a comparison, the one into 5ED85E from another). So the recovered
// behaviour is: bring the angle back into the turn by one full turn in whichever direction it left.
inline double normaliseAngle(double angle) {
    if (angle < 0.0) {
        return angle + kQuarterTurn2Pi;        // RE 0x5ED85E
    }
    if (angle >= kQuarterTurn2Pi) {
        return angle - kQuarterTurn2Pi;        // RE 0x5ED828
    }
    return angle;
}

// RE 0x5ED3D0, the primitive the corner geometry is built from (goal round 57 data-flow trace):
//     5ED453  movsd xmm11, [rbx]        ; a.x      (point A lives at offset +0 of its object)
//     5ED458  movsd xmm6,  [rbx + 8]    ; a.y
//     5ED45D  subsd xmm11, [rsi]        ; a.x - b.x
//     5ED462  subsd xmm6,  [rsi + 8]    ; a.y - b.y
//     5ED476  mulsd xmm8, xmm6          ; dy * dy
//     5ED47B  addsd xmm8, xmm0          ; + dx * dx  -> a squared length
// Two adjacent edges are formed this way per corner, which is why the same function also needs the
// quadrant angles and the +-2pi normalisation (round 55): it is the corner-arc kernel.
struct Vec2d {
    double x = 0.0;
    double y = 0.0;
};

// RE the two differences above: a and b are 2 double points laid out as {x, y}.
inline Vec2d subtractPoints2d(const double* a, const double* b) {
    return Vec2d{a[0] - b[0], a[1] - b[1]};
}

// RE 0x5ED476 / 0x5ED47B: dy*dy + dx*dx, i.e. the squared length, with no square root at this site.
inline double lengthSquared2d(const Vec2d& v) {
    return v.y * v.y + v.x * v.x;
}

// RE the same kernel, one step on (goal round 58):
//     5ED4B1  movsd xmm8, [1.0]      ; the factor starts at 1.0 -- the DEGENERATE case
//     5ED7DB  divsd xmm8, xmm14      ; ... and is replaced by 1/length when the edge is usable
//     5ED7E0  mulsd xmm6,  xmm8      ; each edge component is scaled by that one factor
//     5ED7E5  mulsd xmm13, xmm8      ; (and the other edge by the same factor, 5ED802/5ED807)
// So the routine normalises an edge by dividing by its length, and a zero length does not divide:
// the factor stays 1.0, which leaves the vector as it was. The 1.0 load is the evidence for the
// guard; that it exists to avoid dividing by zero is the reading of it.
inline Vec2d normaliseEdge2d(const Vec2d& v) {
    const double len2 = lengthSquared2d(v);
    if (len2 == 0.0) {
        return v;                       // RE 0x5ED4B1: the factor is 1.0, nothing is divided
    }
    const double f = 1.0 / std::sqrt(len2);   // RE 0x5ED7DB: divsd by the length
    return Vec2d{v.x * f, v.y * f};           // RE 0x5ED7E0 / 0x5ED7E5
}

// RE the three points of a corner, resolved in round 59 from the data-flow trace:
//     5ED45D  subsd xmm11, [rsi]      ; [rbx]     - [rsi]        -> one edge
//     5ED462  subsd xmm6,  [rsi + 8]  ; [rbx + 8] - [rsi + 8]
//     5ED58A  subsd xmm13, xmm3       ; [rbx]     - xmm3         -> the other edge
//     5ED58F  subsd xmm6,  xmm2       ; [rbx + 8] - xmm2
// [rbx] is the corner itself, [rsi] is one neighbour and (xmm2, xmm3) is the other, so the routine
// holds the two ADJACENT EDGES of a corner -- which is why it also normalises angles and wraps by
// +-2pi (round 55) and why the corner offset 1 - 1/sqrt(2) shows up (round 49).
struct CornerEdges {
    Vec2d incoming;   // corner - previous, unit length
    Vec2d outgoing;   // corner - next, unit length
};

// NOT RECOVERED: how the corner is then distributed between those edges. The proportional split at
// 0x5ED7DB..0x5ED807 has its inputs' meaning unread (findings_border_property.md rounds 56/58), so
// only the two unit edges are reproduced -- the part the instructions state plainly.
inline CornerEdges cornerEdges(const double* previous, const double* corner, const double* next) {
    return CornerEdges{normaliseEdge2d(subtractPoints2d(corner, previous)),
                       normaliseEdge2d(subtractPoints2d(corner, next))};
}

// RE order: (x0,y0) -> (x1,y0) -> (x1,y1) -> (x0,y1).
void rectangleCorners(double x0, double y0, double x1, double y1, RectCorner out[4]);

}  // namespace lcns::geom
