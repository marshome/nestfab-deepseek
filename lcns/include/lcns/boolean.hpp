// lcns/boolean.hpp -- polygon boolean operations (union / intersection / difference).
//
// The reverse engineering showed the original has a real exact polygon boolean kernel in
// `..\exact\boolean.cpp` (entry point 0x597BD0) which we did NOT decompile, and which the
// no-fit pipeline needs (`..\exact\nofit_map.cpp` = "NoFitMapWithoutHoles"). This header
// supplies an equivalent, so that
//   * the forbidden region of a NoFitNesting becomes a true union rather than a polygon list,
//   * non-convex no-fit polygons can be assembled from ring-wise convolutions,
//   * polygon offsetting can remove self intersections.
//
// Method: split every edge of A at its intersections with B, then classify each sub-edge by
// probing the boolean predicate on BOTH sides of the edge (a tiny nudge along the edge normal).
// An edge is on the result boundary iff the two probes disagree; it is then oriented so that
// the result interior is on its left. This is uniform with respect to degeneracies (coincident
// edges, touching corners) and needs no special cases in the sweep.
#pragma once

#include <vector>

#include "lcns/geom.hpp"

namespace lcns {
namespace geom {

enum class BoolOp {
    Union,         // A | B
    Intersection,  // A & B
    Difference,    // A - B
    Xor,           // A ^ B
};

// Exact-integer predicates with a snapping grid for stitching (1e-6 in real units, which is
// the tolerance the original uses for its no-fit work: double 1e-6 @ 0x9AC818).
inline constexpr fixed_t kSnapTolerance = 10000;  // == 1e-6 real units

MultiPolygon booleanOp(const MultiPolygon& a, const MultiPolygon& b, BoolOp op);
MultiPolygon booleanOp(const Polygon& a, const Polygon& b, BoolOp op);

inline MultiPolygon unite(const MultiPolygon& a, const MultiPolygon& b) {
    return booleanOp(a, b, BoolOp::Union);
}
inline MultiPolygon intersect(const MultiPolygon& a, const MultiPolygon& b) {
    return booleanOp(a, b, BoolOp::Intersection);
}
inline MultiPolygon subtract(const MultiPolygon& a, const MultiPolygon& b) {
    return booleanOp(a, b, BoolOp::Difference);
}

// Union of a set with itself: merges overlapping rings, resolves self intersections.
MultiPolygon uniteSelf(const MultiPolygon& a);

// Even-odd regularisation: re-derives the boundary from the even-odd interior of `mp`.
// This removes self intersections (miter spikes produced by offsetting, bow ties) and
// duplicated rings. Implemented as booleanOp(mp, mp, Union).
MultiPolygon regularize(const MultiPolygon& mp);

// Minkowski sum of two polygons WITH HOLES.
// Inclusion-exclusion over ring pairs:
//     A (+) -B  =  (Ao (+) -Bo)  -  (Ao (+) -Bh)  -  (Ah (+) -Bo)  +  (Ah (+) -Bh)
// where the outer/hole roles are decided by the ring's nesting parity. This is the
// equivalent of the original's `..\exact\nofit_map.cpp` "NoFitMapWithoutHoles" plus the
// hole handling of `..\exact\convolution.cpp`.
MultiPolygon minkowskiMulti(const MultiPolygon& a, const MultiPolygon& b);

// No-fit polygon of `a` with respect to `b`: a (+) -b, holes included.
// The result is the locus of translations of `b` at which it touches `a`.
MultiPolygon nfpMulti(const MultiPolygon& a, const MultiPolygon& b);

// Same set, but computed by ear-clipping every non convex ring and unioning the convex pairwise
// sums instead of walking the merged convolution edges. Two independent implementations of the
// same thing are worth keeping: the tests assert that the loop-walk path and this decomposition
// path agree, which is a strong check on both. The loop-walk path is the primary one.
MultiPolygon minkowskiMultiDecomposed(const MultiPolygon& a, const MultiPolygon& b);

// Turns the raw loops of geom::convolveRingLoops into a region: a loop nested inside an odd
// number of other loops bounds a hole of the sum, everything else bounds a new outer boundary.
// Degenerate loops (fewer than three points, or zero area) are dropped.
MultiPolygon classifyConvolutionLoops(const std::vector<Ring>& loops);

// Offset + self-intersection removal. The naive miter offset of geom::inflatePolygon can
// overshoot on concave corners and produce loops; this regularises the result so the output
// is a simple, non self intersecting polygon (what the original's exact kernel guarantees).
Polygon inflateCleaned(const Polygon& p, double gap, const OffsetParams& op = {});
MultiPolygon inflateCleaned(const MultiPolygon& mp, double gap, const OffsetParams& op = {});

// Rebuild a well formed MultiPolygon (CCW outer rings, CW holes bound to the smallest
// containing outer ring, degenerate rings dropped). Uses the even-odd nesting rule, which is
// what the input geometry of a nesting job follows.
MultiPolygon normalize(const MultiPolygon& mp);

// Even-odd membership test over all rings of `mp`. Returns 1 when `p` is inside.
int pointInMultiPolygon(const MultiPolygon& mp, FPoint p);

double multiArea(const MultiPolygon& mp);

// Total signed area of one ring in scaled^2 units, sign included (helper for callers).
inline Int128 signedArea2Raw(const Ring& r) { return signedArea2(r); }

}  // namespace geom
}  // namespace lcns
