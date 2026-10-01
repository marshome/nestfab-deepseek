// lcns/boolean.cpp -- polygon boolean operations.
#include "lcns/boolean.hpp"
#include "lcns/recovery.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <map>
#include <unordered_map>

LCNS_STRUCTURAL(geom.boolean_kernel);
namespace lcns {
namespace geom {
namespace {

// ---------------------------------------------------------------------------
// snapping: all split points are quantised so that stitching matches exactly
// ---------------------------------------------------------------------------
struct QPoint {
    std::int64_t x = 0;
    std::int64_t y = 0;
    bool operator==(const QPoint& o) const { return x == o.x && y == o.y; }
    bool operator<(const QPoint& o) const { return x != o.x ? x < o.x : y < o.y; }
};

QPoint quantise(FPoint p) {
    const auto q = [](fixed_t v) -> std::int64_t {
        if (v >= 0) return (v + kSnapTolerance / 2) / kSnapTolerance;
        return -((-v + kSnapTolerance / 2) / kSnapTolerance);
    };
    return QPoint{q(p.x), q(p.y)};
}

struct QPointHash {
    std::size_t operator()(const QPoint& q) const noexcept {
        std::size_t h = 1469598103934665603ull;
        h ^= static_cast<std::size_t>(q.x);
        h *= 1099511628211ull;
        h ^= static_cast<std::size_t>(q.y);
        return h;
    }
};

// representative exact point per quantised cell so every node has one coordinate
class NodeTable {
public:
    FPoint add(FPoint p) {
        const QPoint q = quantise(p);
        auto it = rep_.find(q);
        if (it != rep_.end()) return it->second;
        rep_.emplace(q, p);
        return p;
    }
    FPoint representative(FPoint p) const {
        auto it = rep_.find(quantise(p));
        return it == rep_.end() ? p : it->second;
    }
    QPoint key(FPoint p) const { return quantise(p); }

private:
    std::unordered_map<QPoint, FPoint, QPointHash> rep_;
};

// ---------------------------------------------------------------------------
// segment intersection (0, 1 or 2 points; collinear overlap yields its endpoints)
// ---------------------------------------------------------------------------
long double crossL(FPoint a, FPoint b) {
    return static_cast<long double>(a.x) * static_cast<long double>(b.y) -
           static_cast<long double>(a.y) * static_cast<long double>(b.x);
}
FPoint sub(FPoint a, FPoint b) { return FPoint{a.x - b.x, a.y - b.y}; }
long double dotL(FPoint a, FPoint b) {
    return static_cast<long double>(a.x) * b.x + static_cast<long double>(a.y) * b.y;
}

void segIntersect(const FPoint& p1, const FPoint& p2, const FPoint& q1, const FPoint& q2,
                  std::vector<FPoint>& out) {
    const FPoint d1 = sub(p2, p1);
    const FPoint d2 = sub(q2, q1);
    const long double den = crossL(d1, d2);
    const FPoint r = sub(q1, p1);
    if (den != 0.0L) {
        const long double t = crossL(r, d2) / den;
        const long double u = crossL(r, d1) / den;
        if (t >= 0.0L && t <= 1.0L && u >= 0.0L && u <= 1.0L) {
            out.push_back(FPoint{
                static_cast<fixed_t>(std::llround(static_cast<long double>(p1.x) + t * d1.x)),
                static_cast<fixed_t>(std::llround(static_cast<long double>(p1.y) + t * d1.y))});
        }
        return;
    }
    if (crossL(r, d1) != 0.0L) return;  // parallel, not collinear
    // collinear: overlap interval in units of d1
    const long double L2 = dotL(d1, d1);
    if (L2 == 0.0L) return;
    const long double t0 = dotL(sub(q1, p1), d1) / L2;
    const long double t1 = dotL(sub(q2, p1), d1) / L2;
    const long double lo = std::min(t0, t1), hi = std::max(t0, t1);
    const long double a = std::max(0.0L, lo), b = std::min(1.0L, hi);
    if (a > b) return;
    const auto at = [&](long double t) {
        return FPoint{static_cast<fixed_t>(std::llround(static_cast<long double>(p1.x) + t * d1.x)),
                      static_cast<fixed_t>(std::llround(static_cast<long double>(p1.y) + t * d1.y))};
    };
    out.push_back(at(a));
    if (b > a) out.push_back(at(b));
}

// ---------------------------------------------------------------------------
// rings of a multi polygon, flattened
// ---------------------------------------------------------------------------
std::vector<Ring> allRings(const MultiPolygon& mp) {
    std::vector<Ring> out;
    for (const auto& p : mp) {
        if (p.external.size() >= 3) out.push_back(p.external);
        for (const auto& h : p.inners) {
            if (h.size() >= 3) out.push_back(h);
        }
    }
    return out;
}

int evenOdd(const std::vector<Ring>& rings, FPoint p) {
    int parity = 0;
    for (const auto& r : rings) {
        const std::size_t n = r.size();
        for (std::size_t i = 0, j = n - 1; i < n; j = i++) {
            const FPoint& A = r[j];
            const FPoint& B = r[i];
            if ((A.y > p.y) != (B.y > p.y)) {
                const int side = orient2d(A, B, p);
                if ((B.y > A.y) ? (side > 0) : (side < 0)) parity ^= 1;
            }
        }
    }
    return parity;
}

int evenOdd(const MultiPolygon& mp, FPoint p) { return evenOdd(allRings(mp), p); }

// split one ring's edges at every intersection with the other side's rings
struct SubEdge {
    FPoint a, b;
    bool fromB = false;
};

void splitRing(const Ring& r, const std::vector<Ring>& other, bool fromB,
               std::vector<SubEdge>& out) {
    const std::size_t n = r.size();
    for (std::size_t i = 0; i < n; ++i) {
        const FPoint p1 = r[i];
        const FPoint p2 = r[(i + 1) % n];
        if (p1 == p2) continue;
        std::vector<FPoint> cuts;
        cuts.push_back(p1);
        cuts.push_back(p2);
        for (const auto& o : other) {
            const std::size_t m = o.size();
            for (std::size_t k = 0; k < m; ++k) {
                std::vector<FPoint> hits;
                segIntersect(p1, p2, o[k], o[(k + 1) % m], hits);
                for (const auto& h : hits) cuts.push_back(h);
            }
        }
        // order the cuts along the edge
        const FPoint d = sub(p2, p1);
        const long double L2 = dotL(d, d);
        std::sort(cuts.begin(), cuts.end(), [&](const FPoint& u, const FPoint& v) {
            const long double tu = L2 > 0 ? dotL(sub(u, p1), d) / L2 : 0.0L;
            const long double tv = L2 > 0 ? dotL(sub(v, p1), d) / L2 : 0.0L;
            return tu < tv;
        });
        for (std::size_t k = 0; k + 1 < cuts.size(); ++k) {
            if (cuts[k] == cuts[k + 1]) continue;
            out.push_back(SubEdge{cuts[k], cuts[k + 1], fromB});
        }
    }
}

// ---------------------------------------------------------------------------
// interior membership of a probe point for the requested operation
// ---------------------------------------------------------------------------
struct Predicate {
    BoolOp op;
    const std::vector<Ring>* ra;
    const std::vector<Ring>* rb;

    bool inside(FPoint p) const {
        const bool inA = evenOdd(*ra, p) != 0;
        const bool inB = evenOdd(*rb, p) != 0;
        switch (op) {
            case BoolOp::Union: return inA || inB;
            case BoolOp::Intersection: return inA && inB;
            case BoolOp::Difference: return inA && !inB;
            case BoolOp::Xor: return inA != inB;
        }
        return false;
    }
};

// ---------------------------------------------------------------------------
// stitching
// ---------------------------------------------------------------------------
using NodeId = QPoint;

struct Directed {
    NodeId u, v;
    FPoint pu, pv;
};

// Walk directed edges into closed rings. At a node with several outgoing candidates pick the
// sharpest right turn first (standard planar-graph face traversal with CCW interior).
std::vector<Ring> stitch(const std::vector<Directed>& in, const std::vector<FPoint>& pool) {
    (void)pool;
    std::vector<Directed> edges = in;
    std::vector<char> used(edges.size(), 0);
    std::map<NodeId, std::vector<std::size_t>> out;
    for (std::size_t i = 0; i < edges.size(); ++i) out[edges[i].u].push_back(i);

    std::vector<Ring> rings;
    for (std::size_t start = 0; start < edges.size(); ++start) {
        if (used[start]) continue;
        Ring ring;
        std::size_t cur = start;
        NodeId startNode = edges[start].u;
        NodeId node = edges[start].u;
        std::size_t guard = 0;
        while (guard++ <= edges.size() + 2) {
            used[cur] = 1;
            ring.push_back(edges[cur].pu);
            node = edges[cur].v;
            if (node == startNode) break;
            auto it = out.find(node);
            if (it == out.end()) break;
            std::size_t next = edges.size();
            // prefer the most clockwise turn relative to the incoming direction so that the
            // interior stays on the left
            const FPoint inDir = sub(edges[cur].pv, edges[cur].pu);
            long double best = 0.0L;
            bool haveBest = false;
            for (std::size_t cand : it->second) {
                if (used[cand]) continue;
                const FPoint outDir = sub(edges[cand].pv, edges[cand].pu);
                const long double cr = crossL(inDir, outDir);
                const long double dt = dotL(inDir, outDir);
                long double ang = std::atan2(static_cast<double>(cr), static_cast<double>(dt));
                if (!haveBest || ang < best) {
                    best = ang;
                    next = cand;
                    haveBest = true;
                }
            }
            if (next >= edges.size()) break;
            cur = next;
        }
        if (ring.size() >= 3) {
            ring = removeAlignedCollinearPoints(ring);
            if (ring.size() >= 3) rings.push_back(std::move(ring));
        }
    }
    return rings;
}

// A stitched boundary may visit one node twice (a bow tie or two regions touching at a
// point). Split such a walk into simple rings at the repeated nodes.
void splitAtRepeatedNodes(const Ring& r, std::vector<Ring>& out) {
    std::map<QPoint, std::size_t> first;
    for (std::size_t i = 0; i < r.size(); ++i) {
        const QPoint k = quantise(r[i]);
        auto it = first.find(k);
        if (it == first.end()) {
            first.emplace(k, i);
            continue;
        }
        const std::size_t b = it->second;
        Ring cycle(r.begin() + static_cast<std::ptrdiff_t>(b),
                   r.begin() + static_cast<std::ptrdiff_t>(i));
        Ring remainder;
        remainder.insert(remainder.end(), r.begin(), r.begin() + static_cast<std::ptrdiff_t>(b));
        remainder.insert(remainder.end(), r.begin() + static_cast<std::ptrdiff_t>(i), r.end());
        if (cycle.size() >= 3) {
            const Ring cleaned = removeAlignedCollinearPoints(cycle);
            if (cleaned.size() >= 3) out.push_back(cleaned);
        }
        if (remainder.size() >= 3) {
            splitAtRepeatedNodes(remainder, out);
        }
        return;
    }
    const Ring cleaned = removeAlignedCollinearPoints(r);
    if (cleaned.size() >= 3) out.push_back(cleaned);
}

}  // namespace

// ---------------------------------------------------------------------------
int pointInMultiPolygon(const MultiPolygon& mp, FPoint p) { return evenOdd(mp, p); }

double multiArea(const MultiPolygon& mp) {
    double a = 0.0;
    for (const auto& poly : mp) {
        a += area(poly.external);
        for (const auto& h : poly.inners) a -= area(h);
    }
    return a;
}

MultiPolygon normalize(const MultiPolygon& mp) {
    std::vector<Ring> rings = allRings(mp);
    // drop degenerate rings and normalise orientation by nesting parity later
    std::vector<std::pair<double, Ring>> sorted;
    sorted.reserve(rings.size());
    for (auto& r : rings) {
        r = removeAlignedCollinearPoints(r);
        if (r.size() < 3) continue;
        const double a = std::fabs(area(r));
        if (a <= 0.0) continue;
        sorted.emplace_back(a, std::move(r));
    }
    std::sort(sorted.begin(), sorted.end(),
              [](const auto& x, const auto& y) { return x.first > y.first; });

    MultiPolygon out;
    std::vector<int> owner(sorted.size(), -1);  // index into out
    for (std::size_t i = 0; i < sorted.size(); ++i) {
        // containment depth = how many already accepted rings contain this one
        int depth = 0;
        int smallest = -1;
        double smallestArea = 0.0;
        for (std::size_t j = 0; j < i; ++j) {
            if (!sorted[j].second.empty() && pointInRing(sorted[j].second, sorted[i].second.front())) {
                ++depth;
                if (smallest < 0 || sorted[j].first < smallestArea) {
                    smallestArea = sorted[j].first;
                    smallest = static_cast<int>(j);
                }
            }
        }
        Ring r = sorted[i].second;
        if (depth % 2 == 0) {
            if (!isCCW(r)) r = reverse(r);
            Polygon p;
            p.external = r;
            out.push_back(std::move(p));
            owner[i] = static_cast<int>(out.size()) - 1;
        } else {
            if (isCCW(r)) r = reverse(r);
            int host = smallest >= 0 ? owner[static_cast<std::size_t>(smallest)] : -1;
            if (host < 0) host = static_cast<int>(out.size()) - 1;
            if (host >= 0) out[static_cast<std::size_t>(host)].inners.push_back(std::move(r));
        }
    }
    return out;
}

MultiPolygon booleanOp(const Polygon& a, const Polygon& b, BoolOp op) {
    MultiPolygon ma, mb;
    ma.push_back(a);
    mb.push_back(b);
    return booleanOp(ma, mb, op);
}

MultiPolygon booleanOp(const MultiPolygon& a, const MultiPolygon& b, BoolOp op) {
    const std::vector<Ring> ra = allRings(a);
    const std::vector<Ring> rb = allRings(b);
    MultiPolygon result;
    if (ra.empty()) {
        if (op == BoolOp::Union || op == BoolOp::Xor) return normalize(b);
        if (op == BoolOp::Intersection) return MultiPolygon{};
        return MultiPolygon{};  // difference with empty A
    }
    if (rb.empty()) {
        if (op == BoolOp::Union || op == BoolOp::Difference || op == BoolOp::Xor) return normalize(a);
        return MultiPolygon{};  // intersection with empty B
    }

    std::vector<SubEdge> subs;
    for (const auto& r : ra) splitRing(r, rb, false, subs);
    for (const auto& r : rb) splitRing(r, ra, true, subs);

    NodeTable nodes;
    for (auto& s : subs) {
        s.a = nodes.add(s.a);
        s.b = nodes.add(s.b);
    }

    const Predicate pred{op, &ra, &rb};

    // probe distance: a small fraction of the overall extent
    Box bb = bounds(a);
    const Box bbb = bounds(b);
    if (bbb.valid) {
        if (!bb.valid) {
            bb = bbb;
        } else {
            bb.min.x = std::min(bb.min.x, bbb.min.x);
            bb.min.y = std::min(bb.min.y, bbb.min.y);
            bb.max.x = std::max(bb.max.x, bbb.max.x);
            bb.max.y = std::max(bb.max.y, bbb.max.y);
        }
    }
    double diag = 1.0;
    if (bb.valid) diag = std::max(1.0, std::hypot(bb.width(), bb.height()));
    const double eps = std::max(1e-7, diag * 1e-7);

    std::map<std::pair<NodeId, NodeId>, Directed> keep;
    for (const auto& s : subs) {
        if (s.a == s.b) continue;
        const FPoint d = sub(s.b, s.a);
        const double L = std::hypot(static_cast<double>(d.x), static_cast<double>(d.y));
        if (L <= 0.0) continue;
        // left normal
        const double nx = -static_cast<double>(d.y) / L;
        const double ny = static_cast<double>(d.x) / L;
        const FPoint mid{static_cast<fixed_t>((static_cast<long double>(s.a.x) + s.b.x) / 2.0L),
                         static_cast<fixed_t>((static_cast<long double>(s.a.y) + s.b.y) / 2.0L)};
        const FPoint pl{static_cast<fixed_t>(static_cast<long double>(mid.x) + nx * eps * kScale),
                        static_cast<fixed_t>(static_cast<long double>(mid.y) + ny * eps * kScale)};
        const FPoint pr{static_cast<fixed_t>(static_cast<long double>(mid.x) - nx * eps * kScale),
                        static_cast<fixed_t>(static_cast<long double>(mid.y) - ny * eps * kScale)};
        const bool leftIn = pred.inside(pl);
        const bool rightIn = pred.inside(pr);
        if (leftIn == rightIn) continue;  // not on the result boundary
        Directed e;
        if (leftIn) {
            e.u = nodes.key(s.a);
            e.v = nodes.key(s.b);
            e.pu = s.a;
            e.pv = s.b;
        } else {
            e.u = nodes.key(s.b);
            e.v = nodes.key(s.a);
            e.pu = s.b;
            e.pv = s.a;
        }
        keep[{e.u, e.v}] = e;  // duplicates (same direction) collapse to one
    }

    // cancel exact reverse twins (slits produced by coincident boundaries)
    for (auto it = keep.begin(); it != keep.end();) {
        const auto rev = std::make_pair(it->second.v, it->second.u);
        if (keep.count(rev)) {
            keep.erase(rev);
            it = keep.erase(it);
        } else {
            ++it;
        }
    }

    std::vector<Directed> edges;
    edges.reserve(keep.size());
    for (auto& kv : keep) edges.push_back(kv.second);

    std::vector<FPoint> pool;
    const std::vector<Ring> rings = stitch(edges, pool);
    MultiPolygon raw;
    for (const auto& r : rings) {
        std::vector<Ring> simple;
        splitAtRepeatedNodes(r, simple);
        for (auto& s : simple) {
            Polygon p;
            p.external = std::move(s);
            raw.push_back(std::move(p));
        }
    }
    result = normalize(raw);
    return result;
}

MultiPolygon uniteSelf(const MultiPolygon& a) {
    MultiPolygon acc;
    for (const auto& p : a) {
        MultiPolygon one;
        one.push_back(p);
        acc = acc.empty() ? one : unite(acc, one);
    }
    if (acc.empty()) acc = normalize(a);
    return acc;
}

LCNS_NOT_REVERSED(geom.detect_overlap);
MultiPolygon regularize(const MultiPolygon& mp) {
    // Splitting every edge at its intersections with the very same set, then keeping the
    // boundary where the even-odd interior changes side, is exactly a self-union.
    return booleanOp(mp, mp, BoolOp::Union);
}

namespace {

// ring pairs with nesting parity: index 0 = outer rings, index 1 = hole rings
void ringRoles(const MultiPolygon& mp, std::vector<Ring>& outers, std::vector<Ring>& holes) {
    for (const auto& p : mp) {
        if (p.external.size() >= 3) outers.push_back(orientCCW(p.external));
        for (const auto& h : p.inners) {
            if (h.size() >= 3) holes.push_back(orientCCW(h));
        }
    }
}

}  // namespace

LCNS_NOT_REVERSED(geom.exact_records);
MultiPolygon classifyConvolutionLoops(const std::vector<Ring>& loops) {
    MultiPolygon raw;
    raw.reserve(loops.size());
    for (const auto& r : loops) {
        Ring cleaned = removeAlignedCollinearPoints(r);
        if (cleaned.size() < 3) continue;
        if (area(cleaned) == 0.0) continue;   // a collapsed loop bounds nothing
        Polygon p;
        p.external = std::move(cleaned);
        raw.push_back(std::move(p));
    }
    if (raw.empty()) return raw;
    // Winding / nesting classification: a loop inside an odd number of other loops is a hole of
    // the sum, an even number makes it a new outer boundary. normalize() is exactly that rule
    // and also fixes the ring orientations (CCW outers, CW holes).
    return normalize(raw);
}

namespace {

// Guard against a combinatorial explosion when both operands are finely triangulated.
constexpr std::size_t kMaxConvPairs = 256;

bool isConvexRing(const Ring& r) {
    const std::size_t n = r.size();
    if (n < 4) return true;
    int sign = 0;
    for (std::size_t i = 0; i < n; ++i) {
        const int s = orient2d(r[i], r[(i + 1) % n], r[(i + 2) % n]);
        if (s == 0) continue;
        if (sign == 0) {
            sign = s;
        } else if ((s > 0) != (sign > 0)) {
            return false;
        }
    }
    return true;
}

// Convolution of two rings via ear-clip decomposition (the general path).
// Convolution by edge merge is only exact for convex rings, so non convex operands are
// ear-clipped into triangles first and the pairwise sums are unioned.
MultiPolygon convRingDecomposed(const Ring& aIn, const Ring& bIn, bool reflect) {
    const Ring a = orientCCW(aIn);
    Ring b = orientCCW(bIn);
    if (reflect) b = orientCCW(negateRing(b));

    std::vector<Ring> pa = isConvexRing(a) ? std::vector<Ring>{a} : triangulate(a);
    std::vector<Ring> pb = isConvexRing(b) ? std::vector<Ring>{b} : triangulate(b);
    if (pa.empty()) pa.push_back(a);
    if (pb.empty()) pb.push_back(b);
    if (pa.size() * pb.size() > kMaxConvPairs) {
        pa.assign(1, convexHull(a));
        pb.assign(1, convexHull(b));
    }

    MultiPolygon pieces;
    for (const auto& x : pa) {
        for (const auto& y : pb) {
            Ring c = convolveBoundaries(x, y);
            if (c.size() < 3) continue;
            Polygon p;
            p.external = std::move(c);
            pieces.push_back(std::move(p));
        }
    }
    if (pieces.empty()) return pieces;
    return uniteSelf(pieces);
}

MultiPolygon convRingPair(const Ring& a, const Ring& b, bool reflect, bool useLoops) {
    const Ring aa = orientCCW(a);
    const Ring bb = reflect ? orientCCW(negateRing(b)) : orientCCW(b);
    // The merged-edge loop walk (the recovered ConvolutionRaw contract, see
    // geom::convolveRingLoops) is EXACT when both operands are convex: each edge list is then
    // cyclically sorted by angle and the walk traces the sum boundary, with
    // classifyConvolutionLoops resolving the loops it produces.
    //
    // A non convex operand's edge list is NOT angle monotone -- it turns back at every reflex
    // vertex -- so the angular merge assumption fails there. That general boundary convolution
    // is what `..\exact\nofit_map.cpp` implements in the 10 KB that the reverse engineering did
    // NOT recover (re/REPORT.md 7.1). For those operands the ring is ear-clipped and the convex
    // pairwise convolutions are unioned, which is the standard construction for a non convex
    // Minkowski sum; test_boolean verifies it against the bounding box identity
    // bbox(A+B) = [minA+minB, maxA+maxB] and against the loop walk on convex operands.
    if (useLoops && isConvexRing(aa) && isConvexRing(bb)) {
        MultiPolygon byLoops = classifyConvolutionLoops(convolveRingLoops(aa, bb));
        if (!byLoops.empty()) return byLoops;
    }
    return convRingDecomposed(a, b, reflect);
}

MultiPolygon sumImpl(const MultiPolygon& a, const MultiPolygon& b, bool reflect, bool useLoops) {
    std::vector<Ring> ao, ah, bo, bh;
    ringRoles(a, ao, ah);
    ringRoles(b, bo, bh);

    MultiPolygon pos, neg;
    auto addTo = [](MultiPolygon& dst, MultiPolygon&& src) {
        for (auto& p : src) dst.push_back(std::move(p));
    };
    for (const auto& x : ao) {
        for (const auto& y : bo) addTo(pos, convRingPair(x, y, reflect, useLoops));
        for (const auto& y : bh) addTo(neg, convRingPair(x, y, reflect, useLoops));
    }
    for (const auto& x : ah) {
        for (const auto& y : bo) addTo(neg, convRingPair(x, y, reflect, useLoops));
        for (const auto& y : bh) addTo(pos, convRingPair(x, y, reflect, useLoops));
    }
    if (pos.empty()) return MultiPolygon{};
    const MultiPolygon positives = uniteSelf(pos);
    if (neg.empty()) return positives;
    return subtract(positives, uniteSelf(neg));
}

}  // namespace

MultiPolygon minkowskiMulti(const MultiPolygon& a, const MultiPolygon& b) {
    return sumImpl(a, b, /*reflect=*/false, /*useLoops=*/true);
}

MultiPolygon nfpMulti(const MultiPolygon& a, const MultiPolygon& b) {
    return sumImpl(a, b, /*reflect=*/true, /*useLoops=*/true);
}

MultiPolygon minkowskiMultiDecomposed(const MultiPolygon& a, const MultiPolygon& b) {
    return sumImpl(a, b, /*reflect=*/false, /*useLoops=*/false);
}

Polygon inflateCleaned(const Polygon& p, double gap, const OffsetParams& op) {
    if (gap == 0.0) return p;
    const Polygon raw = inflatePolygon(p, gap, op);
    MultiPolygon one;
    one.push_back(raw);
    // regularise removes miter loops while keeping outer/hole roles
    const MultiPolygon clean = regularize(one);
    if (clean.empty()) return Polygon{};
    if (clean.size() == 1) return clean.front();
    // the offset of a simple polygon should stay one connected region; if not, return the
    // member with the largest area so callers always get a usable outer ring
    std::size_t best = 0;
    double bestArea = -1.0;
    for (std::size_t i = 0; i < clean.size(); ++i) {
        const double a = area(clean[i].external);
        if (a > bestArea) {
            bestArea = a;
            best = i;
        }
    }
    return clean[best];
}

MultiPolygon inflateCleaned(const MultiPolygon& mp, double gap, const OffsetParams& op) {
    if (gap == 0.0) return mp;
    MultiPolygon raw;
    raw.reserve(mp.size());
    for (const auto& p : mp) raw.push_back(inflatePolygon(p, gap, op));
    return regularize(raw);
}

}  // namespace geom
}  // namespace lcns
