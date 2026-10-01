// lcns/geom.cpp -- implementation of the exact fixed-point geometry core.
#include "lcns/geom.hpp"
#include "lcns/recovery.hpp"

#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <sstream>

LCNS_STRUCTURAL(module.geom);
namespace lcns::geom {
namespace {

inline FPoint addP(const FPoint& a, const FPoint& b) { return FPoint{a.x + b.x, a.y + b.y}; }

inline double len(double dx, double dy) { return std::sqrt(dx * dx + dy * dy); }

// squared length comparison without floating point surprises for integer inputs
inline bool sameDirection(const ConvEdge& a, const ConvEdge& b) {
    return a.dx == b.dx && a.dy == b.dy;
}

// Exact polar comparison inside the RE quadrant scheme.
// Returns true if `a` comes strictly before `b` in CCW polar order.
// Equal directions compare equal (false both ways) so that a stable sort preserves the input
// order for parallel edges: reordering them by length breaks the merge traversal.
bool polarLess(const ConvEdge& a, const ConvEdge& b) {
    const int ra = quadrantRank(a.quadrant), rb = quadrantRank(b.quadrant);
    if (ra != rb) return ra < rb;
    return crossSign(FPoint{a.dx, a.dy}, FPoint{b.dx, b.dy}) > 0;
}

// index of the lowest (then leftmost) vertex; the classic convolution start point
std::size_t lowestIndex(const Ring& r) {
    std::size_t best = 0;
    for (std::size_t i = 1; i < r.size(); ++i) {
        if (r[i].y < r[best].y || (r[i].y == r[best].y && r[i].x < r[best].x)) best = i;
    }
    return best;
}

}  // namespace

// ---------------------------------------------------------------------------
// conversion
// ---------------------------------------------------------------------------
Ring toRing(const std::vector<Point>& pts) {
    Ring r;
    r.reserve(pts.size());
    for (const auto& p : pts) r.push_back(FPoint{toFixed(p.x), toFixed(p.y)});
    return r;
}

std::vector<Point> toPoints(const Ring& r) {
    std::vector<Point> out;
    out.reserve(r.size());
    for (const auto& p : r) out.push_back(Point{toDouble(p.x), toDouble(p.y)});
    return out;
}

// ---------------------------------------------------------------------------
// measures
// ---------------------------------------------------------------------------
Int128 signedArea2(const Ring& r) {
    Int128 acc;
    const std::size_t n = r.size();
    if (n < 3) return acc;
    for (std::size_t i = 0; i < n; ++i) {
        const FPoint& a = r[i];
        const FPoint& b = r[(i + 1) % n];
        acc = add128(acc, sub128(mul64(a.x, b.y), mul64(a.y, b.x)));
    }
    return acc;
}

bool isCCW(const Ring& r) { return signedArea2(r).sign() > 0; }

double area(const Ring& r) {
    // signedArea2 is in scaled units: divide by kScale^2 to get real area
    return std::fabs(signedArea2(r).toDouble()) * 0.5 / (kScale * kScale);
}

double perimeter(const Ring& r) {
    double s = 0.0;
    const std::size_t n = r.size();
    for (std::size_t i = 0; i < n; ++i) {
        const FPoint& a = r[i];
        const FPoint& b = r[(i + 1) % n];
        s += len(toDouble(b.x - a.x), toDouble(b.y - a.y));
    }
    return s;
}

Box bounds(const Ring& r) {
    Box b;
    if (r.empty()) return b;
    b.min = b.max = r.front();
    for (const auto& p : r) {
        b.min.x = std::min(b.min.x, p.x);
        b.min.y = std::min(b.min.y, p.y);
        b.max.x = std::max(b.max.x, p.x);
        b.max.y = std::max(b.max.y, p.y);
    }
    b.valid = true;
    return b;
}

Box bounds(const Polygon& p) { return bounds(p.external); }

Box bounds(const MultiPolygon& mp) {
    Box b;
    for (const auto& p : mp) {
        const Box q = bounds(p);
        if (!q.valid) continue;
        if (!b.valid) {
            b = q;
        } else {
            b.min.x = std::min(b.min.x, q.min.x);
            b.min.y = std::min(b.min.y, q.min.y);
            b.max.x = std::max(b.max.x, q.max.x);
            b.max.y = std::max(b.max.y, q.max.y);
        }
        b.valid = true;
    }
    return b;
}

// ---------------------------------------------------------------------------
// ring surgery
// ---------------------------------------------------------------------------
LCNS_STRUCTURAL(geom.offset);
Ring removeAlignedCollinearPoints(const Ring& r, fixed_t tolerance) {
    (void)tolerance;
    if (r.size() < 3) return r;
    Ring in;
    // drop exact duplicates first
    for (const auto& p : r) {
        if (in.empty() || in.back() != p) in.push_back(p);
    }
    if (in.size() > 1 && in.front() == in.back()) in.pop_back();
    if (in.size() < 3) return in;

    Ring out;
    const std::size_t n = in.size();
    for (std::size_t i = 0; i < n; ++i) {
        const FPoint& a = in[(i + n - 1) % n];
        const FPoint& b = in[i];
        const FPoint& c = in[(i + 1) % n];
        if (orient2d(a, b, c) == 0) {
            // keep only if b is a spike (outside the segment a..c)
            const bool between = (std::min(a.x, c.x) <= b.x && b.x <= std::max(a.x, c.x)) &&
                                 (std::min(a.y, c.y) <= b.y && b.y <= std::max(a.y, c.y));
            if (between) continue;
        }
        out.push_back(b);
    }
    return out;
}

Ring reverse(const Ring& r) {
    Ring o(r.rbegin(), r.rend());
    return o;
}

Ring negateRing(const Ring& r) {
    Ring o;
    o.reserve(r.size());
    for (const auto& p : r) o.push_back(FPoint{-p.x, -p.y});
    return o;
}

Ring orientCCW(const Ring& r) { return isCCW(r) ? r : reverse(r); }

bool isSimple(const Ring& r) {
    const std::size_t n = r.size();
    if (n < 3) return false;
    for (std::size_t i = 0; i < n; ++i) {
        const FPoint& a1 = r[i];
        const FPoint& a2 = r[(i + 1) % n];
        for (std::size_t j = i + 1; j < n; ++j) {
            // skip adjacent edges (they legitimately share a vertex)
            if (j == i || (j + 1) % n == i || (i + 1) % n == j) continue;
            const FPoint& b1 = r[j];
            const FPoint& b2 = r[(j + 1) % n];
            if (segmentsIntersect(a1, a2, b1, b2)) return false;
        }
    }
    return true;
}

Ring translate(const Ring& r, FPoint d) {
    Ring o = r;
    for (auto& p : o) {
        p.x += d.x;
        p.y += d.y;
    }
    return o;
}

// ---------------------------------------------------------------------------
// containment
// ---------------------------------------------------------------------------
LCNS_STRUCTURAL(geom.point_in_polygon);
bool pointInRing(const Ring& r, FPoint p) {
    const std::size_t n = r.size();
    if (n < 3) return false;
    bool inside = false;
    for (std::size_t i = 0, j = n - 1; i < n; j = i++) {
        const FPoint& a = r[j];
        const FPoint& b = r[i];
        // half open rule on y, then exact side test
        if ((a.y > p.y) != (b.y > p.y)) {
            const int side = orient2d(a, b, p);
            // a.y > b.y means the edge goes downward -> crossing when side < 0
            if ((b.y > a.y) ? (side > 0) : (side < 0)) inside = !inside;
        }
    }
    return inside;
}

bool pointInPolygon(const Polygon& p, FPoint q) {
    if (!pointInRing(p.external, q)) return false;
    for (const auto& h : p.inners) {
        if (pointInRing(h, q)) return false;
    }
    return true;
}

// ---------------------------------------------------------------------------
// fixed point angle (RE: 0x5C22D0)
// ---------------------------------------------------------------------------
fixed_t angleToFixedDegrees(double dx, double dy) {
    // the recovered code tests both components for an exact zero and returns 0
    if (dx == 0.0 && dy == 0.0) return 0;
    double a = std::atan2(dy, dx);
    a = a / 6.283185307179586;                 // 0x9DE758 = 2*pi
    a = a * static_cast<double>(kFullTurnFixedDegrees);   // 0x9DE740 = 360e10
    a = a + 0.5;                               // 0x9DE750
    // 0x62FA20 (424 B) is the libm rounding helper. The recovered code adds 0.5 and THEN calls
    // it, which is the half-up rounding idiom this compiler emits elsewhere (see kScale: the
    // recovered `round(v*1e10)` is written as `v/360*3.6e12 + 0.5`), so it is floor().
    fixed_t r = static_cast<fixed_t>(std::floor(a));
    // the original wraps with two compare/subtract loops (0x5C231F / 0x5C2360)
    while (r < 0) r += kFullTurnFixedDegrees;
    while (r > kFullTurnFixedDegrees) r -= kFullTurnFixedDegrees;
    return r;
}

fixed_t angleToFixedDegrees(fixed_t dx, fixed_t dy) {
    return angleToFixedDegrees(toDouble(dx), toDouble(dy));
}

// ---------------------------------------------------------------------------
// ear clipping triangulation (exact orientation tests)
// ---------------------------------------------------------------------------
std::vector<Ring> triangulate(const Ring& input) {
    std::vector<Ring> out;
    Ring r = removeAlignedCollinearPoints(input);
    if (r.size() < 3) return out;
    if (!isCCW(r)) r = reverse(r);
    if (r.size() == 3) {
        out.push_back(r);
        return out;
    }

    std::vector<std::size_t> idx(r.size());
    for (std::size_t i = 0; i < r.size(); ++i) idx[i] = i;
    int guard = 0;
    const int limit = static_cast<int>(r.size()) * static_cast<int>(r.size()) + 16;
    while (idx.size() > 3 && guard++ < limit) {
        bool clipped = false;
        const std::size_t n = idx.size();
        for (std::size_t i = 0; i < n; ++i) {
            const std::size_t ip = idx[(i + n - 1) % n];
            const std::size_t ic = idx[i];
            const std::size_t in = idx[(i + 1) % n];
            const FPoint& a = r[ip];
            const FPoint& b = r[ic];
            const FPoint& c = r[in];
            if (orient2d(a, b, c) <= 0) continue;  // reflex or collinear: not an ear
            // no other vertex may fall inside the candidate triangle
            bool clean = true;
            for (std::size_t k = 0; k < n; ++k) {
                const FPoint& p = r[idx[k]];
                if (p == a || p == b || p == c) continue;
                if (orient2d(a, b, p) >= 0 && orient2d(b, c, p) >= 0 && orient2d(c, a, p) >= 0) {
                    clean = false;
                    break;
                }
            }
            if (!clean) continue;
            out.push_back(Ring{a, b, c});
            idx.erase(idx.begin() + static_cast<std::ptrdiff_t>(i));
            clipped = true;
            break;
        }
        if (!clipped) break;  // degenerate / self intersecting input: stop early
    }
    if (idx.size() == 3) {
        out.push_back(Ring{r[idx[0]], r[idx[1]], r[idx[2]]});
    }
    return out;
}

// ---------------------------------------------------------------------------
// convex hull (monotone chain, exact orientation)
// ---------------------------------------------------------------------------
Ring convexHull(Ring pts) {
    if (pts.size() < 3) return pts;
    std::sort(pts.begin(), pts.end(), [](const FPoint& a, const FPoint& b) {
        return a.x < b.x || (a.x == b.x && a.y < b.y);
    });
    pts.erase(std::unique(pts.begin(), pts.end()), pts.end());
    if (pts.size() < 3) return pts;

    Ring hull(2 * pts.size());
    std::size_t k = 0;
    for (std::size_t i = 0; i < pts.size(); ++i) {
        while (k >= 2 && orient2d(hull[k - 2], hull[k - 1], pts[i]) <= 0) --k;
        hull[k++] = pts[i];
    }
    const std::size_t lower = k + 1;
    for (std::size_t i = pts.size() - 1; i-- > 0;) {
        while (k >= lower && orient2d(hull[k - 2], hull[k - 1], pts[i]) <= 0) --k;
        hull[k++] = pts[i];
    }
    hull.resize(k - 1);
    return hull;
}

// ---------------------------------------------------------------------------
// Minkowski convolution
// ---------------------------------------------------------------------------
std::vector<ConvEdge> buildEdges(const Ring& a, const Ring& b) {
    std::vector<ConvEdge> edges;
    edges.reserve(a.size() + b.size());
    auto emit = [&edges](const Ring& r, int which) {
        const std::size_t n = r.size();
        for (std::size_t i = 0; i < n; ++i) {
            const FPoint& p = r[i];
            const FPoint& q = r[(i + 1) % n];
            ConvEdge e;
            e.dx = q.x - p.x;
            e.dy = q.y - p.y;
            if (e.dx == 0 && e.dy == 0) continue;
            e.quadrant = quadrantOf(e.dx, e.dy);
            e.ring = which;
            e.index = i;
            e.origin = p;
            edges.push_back(e);
        }
    };
    emit(a, 0);
    emit(b, 1);
    return edges;
}

namespace {

// Rotate a ring's edges so the list starts at the edge leaving the ring's lowest vertex.
// Both operands must be entered at that vertex for the convolution walk to start on the
// boundary of the sum.
std::vector<ConvEdge> rotatedEdges(const Ring& r) {
    std::vector<ConvEdge> e;
    const std::size_t n = r.size();
    if (n < 3) return e;
    const std::size_t start = lowestIndex(r);
    for (std::size_t k = 0; k < n; ++k) {
        const std::size_t i = (start + k) % n;
        const FPoint& p = r[i];
        const FPoint& q = r[(i + 1) % n];
        ConvEdge ce;
        ce.dx = q.x - p.x;
        ce.dy = q.y - p.y;
        if (ce.dx == 0 && ce.dy == 0) continue;
        ce.quadrant = quadrantOf(ce.dx, ce.dy);
        ce.ring = 0;
        ce.index = i;
        ce.origin = p;
        e.push_back(ce);
    }
    return e;
}

// Sign of the dot product. Fixed point coordinates are ~1e10, so their products are ~1e20 and
// MUST go through the 128 bit helpers: a plain int64 product silently overflows here.
int dotSign(FPoint u, FPoint v) {
    return add128(mul64(u.x, v.x), mul64(u.y, v.y)).sign();
}

// Should edge `u` be walked before edge `v`, measured CCW from the direction `prev`?
// This is the local angular comparison the convolution walk needs: a global polar order is
// only correct for convex operands, because a non convex boundary doubles back.
bool angleFromLess(FPoint prev, FPoint u, FPoint v) {
    const auto half = [prev](FPoint e) -> int {
        const int cr = crossSign(prev, e);
        if (cr > 0) return 0;                       // within (0, pi) CCW of prev
        if (cr < 0) return 1;                       // within (pi, 2pi)
        return dotSign(prev, e) > 0 ? 0 : 1;         // parallel: same direction, or a full turn
    };
    const int hu = half(u);
    const int hv = half(v);
    if (hu != hv) return hu < hv;
    const int c = crossSign(u, v);
    if (c != 0) return c > 0;
    return false;   // equal direction
}

bool sameDirection(FPoint u, FPoint v) {
    return crossSign(u, v) == 0 && dotSign(u, v) > 0;
}

// Set LCNS_CONV_TRACE=1 to dump the convolution walk (development aid).
bool convTrace() {
    static const bool on = std::getenv("LCNS_CONV_TRACE") != nullptr;
    return on;
}

}  // namespace

std::vector<Ring> convolveRingLoops(const Ring& aIn, const Ring& bIn) {
    std::vector<Ring> loops;
    if (aIn.size() < 3 || bIn.size() < 3) return loops;
    const Ring a = orientCCW(aIn);
    const Ring b = orientCCW(bIn);
    const std::vector<ConvEdge> ea = rotatedEdges(a);
    const std::vector<ConvEdge> eb = rotatedEdges(b);
    if (ea.empty() || eb.empty()) return loops;

    // Walk the two edge lists cyclically, always taking the edge that comes first measured CCW
    // from the direction just walked. Exact integer accumulation means every revisit of a point
    // is detected exactly, and each revisit closes (or pinches) a loop.
    FPoint cur = addP(a[lowestIndex(a)], b[lowestIndex(b)]);
    Ring path;
    path.push_back(cur);
    FPoint prev{0, 0};
    bool havePrev = false;
    std::size_t i = 0, j = 0;

    // consume one edge: advance the walk, then split the path at a repeated vertex
    const auto consume = [&](const ConvEdge& e) {
        prev = FPoint{e.dx, e.dy};
        havePrev = true;
        cur.x += e.dx;
        cur.y += e.dy;
        std::size_t hit = path.size();
        for (std::size_t k = 0; k < path.size(); ++k) {
            if (path[k] == cur) {
                hit = k;
                break;
            }
        }
        if (hit == 0) {
            if (path.size() >= 3) {
                Ring loop = removeAlignedCollinearPoints(path);
                if (loop.size() >= 3) loops.push_back(std::move(loop));
            }
            path.clear();
        } else if (hit < path.size()) {
            Ring loop(path.begin() + static_cast<std::ptrdiff_t>(hit), path.end());
            loop = removeAlignedCollinearPoints(loop);
            if (loop.size() >= 3) loops.push_back(std::move(loop));
            path.resize(hit);
        }
        path.push_back(cur);
    };

    const std::size_t total = ea.size() + eb.size();
    std::size_t steps = 0;
    while ((i < ea.size() || j < eb.size()) && steps++ <= total) {
        const bool haveA = i < ea.size();
        const bool haveB = j < eb.size();
        if (haveA && haveB) {
            const FPoint u{ea[i].dx, ea[i].dy};
            const FPoint v{eb[j].dx, eb[j].dy};
            // Parallel edges of both operands bound the same stretch of the sum, so one edge
            // from each must be walked before moving on. Advancing only one of them (or
            // ordering all parallel edges of one operand first) breaks the trace.
            if (sameDirection(u, v)) {
                if (convTrace()) {
                    std::fprintf(stderr, "[conv] step %zu PARALLEL A(%.0f,%.0f) B(%.0f,%.0f)\n",
                                 steps, toDouble(u.x), toDouble(u.y), toDouble(v.x), toDouble(v.y));
                }
                consume(ea[i++]);
                consume(eb[j++]);
                continue;
            }
            const bool takeA = havePrev ? angleFromLess(prev, u, v) : polarLess(ea[i], eb[j]);
            if (convTrace()) {
                std::fprintf(stderr,
                             "[conv] step %zu prev(%.0f,%.0f) A(%.0f,%.0f) B(%.0f,%.0f) -> %s\n",
                             steps, toDouble(prev.x), toDouble(prev.y), toDouble(u.x),
                             toDouble(u.y), toDouble(v.x), toDouble(v.y), takeA ? "A" : "B");
            }
            if (takeA) {
                consume(ea[i++]);
            } else {
                consume(eb[j++]);
            }
        } else if (haveA) {
            consume(ea[i++]);
        } else {
            consume(eb[j++]);
        }
    }

    // A closed remainder means the walk ended exactly where a loop had started.
    if (path.size() >= 4 && path.front() == path.back()) {
        Ring loop(path.begin(), path.end() - 1);
        loop = removeAlignedCollinearPoints(loop);
        if (loop.size() >= 3) loops.push_back(std::move(loop));
    }
    if (loops.empty()) return loops;

    // Anchor the whole loop set: bbox(A+B) = [minA+minB, maxA+maxB], so shifting the set's
    // minimum onto (minA+minB) recovers the exact position of the sum.
    Box ob;
    for (const auto& loop : loops) {
        const Box lb = bounds(loop);
        if (!lb.valid) continue;
        if (!ob.valid) {
            ob = lb;
        } else {
            if (lb.min.x < ob.min.x) ob.min.x = lb.min.x;
            if (lb.min.y < ob.min.y) ob.min.y = lb.min.y;
            if (lb.max.x > ob.max.x) ob.max.x = lb.max.x;
            if (lb.max.y > ob.max.y) ob.max.y = lb.max.y;
        }
    }
    const Box ba = bounds(a);
    const Box bb = bounds(b);
    if (ob.valid && ba.valid && bb.valid) {
        const FPoint target{ba.min.x + bb.min.x, ba.min.y + bb.min.y};
        const FPoint shift{target.x - ob.min.x, target.y - ob.min.y};
        if (shift.x != 0 || shift.y != 0) {
            for (auto& loop : loops) loop = translate(loop, shift);
        }
    }
    return loops;
}

Ring convolveBoundaries(const Ring& a, const Ring& b) {
    if (a.size() < 3 || b.size() < 3) return Ring{};

    std::vector<ConvEdge> ea, eb;
    for (auto& e : buildEdges(a, b)) (e.ring == 0 ? ea : eb).push_back(e);

    std::stable_sort(ea.begin(), ea.end(), polarLess);
    std::stable_sort(eb.begin(), eb.end(), polarLess);

    // start point: sum of the lowest vertices
    FPoint cur = addP(a[lowestIndex(a)], b[lowestIndex(b)]);

    Ring out;
    out.push_back(cur);
    std::size_t i = 0, j = 0;
    const std::size_t total = ea.size() + eb.size();
    for (std::size_t k = 0; k < total; ++k) {
        const bool takeA = (j >= eb.size()) || (i < ea.size() && polarLess(ea[i], eb[j]));
        const bool takeB = !takeA;
        const ConvEdge& e = takeB ? eb[j] : ea[i];
        if (takeB) ++j; else ++i;
        cur.x += e.dx;
        cur.y += e.dy;
        if (cur != out.back()) out.push_back(cur);
    }
    // close the ring
    if (out.size() > 1 && out.front() == out.back()) out.pop_back();
    out = removeAlignedCollinearPoints(out);
    if (!isCCW(out)) out = reverse(out);

    // The edge order is cyclic, so the accumulated shape is a TRANSLATE of the true sum.
    // A Minkowski sum satisfies bbox(A+B) = [minA+minB, maxA+maxB], so anchoring the result's
    // bounding box minima at (minA+minB) recovers the exact position.
    if (!out.empty()) {
        const Box ba = bounds(a);
        const Box bb2 = bounds(b);
        const Box ob = bounds(out);
        if (ba.valid && bb2.valid && ob.valid) {
            const FPoint target{ba.min.x + bb2.min.x, ba.min.y + bb2.min.y};
            const FPoint shift{target.x - ob.min.x, target.y - ob.min.y};
            if (shift.x != 0 || shift.y != 0) out = translate(out, shift);
        }
    }
    return out;
}

Ring minkowskiSum(const Ring& a, const Ring& b) { return convolveBoundaries(a, b); }

Ring nfp(const Ring& a, const Ring& b) {
    // NFP(A,B) = A (+) -B : the locus of translations of B at which it touches A
    Ring nb;
    nb.reserve(b.size());
    for (const auto& p : b) nb.push_back(FPoint{-p.x, -p.y});
    return convolveBoundaries(a, nb);
}

// ---------------------------------------------------------------------------
// offsetting
// ---------------------------------------------------------------------------
Ring offsetOnce(const Ring& r, double dist) {
    Ring src = removeAlignedCollinearPoints(r);
    const std::size_t n = src.size();
    if (n < 3 || dist == 0.0) return src;

    const double s = isCCW(src) ? 1.0 : -1.0;
    const double d = dist * s;  // outward positive for CCW

    // offset lines: point + normal * d, normal = (dy, -dx)/|e|
    std::vector<Point> base(n), nrm(n);
    for (std::size_t i = 0; i < n; ++i) {
        const FPoint& p = src[i];
        const FPoint& q = src[(i + 1) % n];
        base[i] = Point{toDouble(p.x), toDouble(p.y)};
        const double dx = toDouble(q.x - p.x), dy = toDouble(q.y - p.y);
        const double L = len(dx, dy);
        if (L == 0.0) {
            nrm[i] = Point{0.0, 0.0};
            continue;
        }
        nrm[i] = Point{dy / L * d, -dx / L * d};
    }

    Ring out;
    out.reserve(n);
    for (std::size_t i = 0; i < n; ++i) {
        const std::size_t prev = (i + n - 1) % n;
        // line prev: through base[prev]+nrm[prev], direction dir_prev
        const FPoint& ap = src[prev];
        const FPoint& bp = src[i];
        const FPoint& bc = src[(i + 1) % n];
        const double dpx = toDouble(bp.x - ap.x), dpy = toDouble(bp.y - ap.y);
        const double dcx = toDouble(bc.x - bp.x), dcy = toDouble(bc.y - bp.y);
        const double det = dpx * dcy - dpy * dcx;  // cross of the two edge directions
        if (std::fabs(det) < 1e-12) {
            // nearly parallel: simply push the offset vertex
            out.push_back(FPoint{toFixed(base[i].x + nrm[prev].x), toFixed(base[i].y + nrm[prev].y)});
            continue;
        }
        const double px = base[prev].x + nrm[prev].x, py = base[prev].y + nrm[prev].y;
        const double qx = base[i].x + nrm[i].x, qy = base[i].y + nrm[i].y;
        // solve px + t*dpx = qx + u*dcx , py + t*dpy = qy + u*dcy
        const double rx = qx - px, ry = qy - py;
        const double t = (rx * dcy - ry * dcx) / det;
        out.push_back(FPoint{toFixed(px + t * dpx), toFixed(py + t * dpy)});
    }
    Ring cleaned = removeAlignedCollinearPoints(out);
    if (cleaned.size() < 3) return out;
    // keep the original orientation
    if (isCCW(cleaned) != isCCW(src)) cleaned = reverse(cleaned);
    return cleaned;
}

Ring offsetRing(const Ring& r, double dist, const OffsetParams& p) {
    if (dist == 0.0) return removeAlignedCollinearPoints(r);
    const double step = (p.step > 0.0) ? p.step : 0.01;
    const double ad = std::fabs(dist);
    const int n = static_cast<int>(std::floor(ad / step + 0.5));  // RE formula

    Ring cur = r;
    double sign = dist < 0.0 ? -1.0 : 1.0;
    if (n <= 1) {
        cur = offsetOnce(cur, sign * ad);
    } else {
        const double inc = sign * ad / n;
        for (int i = 0; i < n; ++i) cur = offsetOnce(cur, inc);
    }
    if (p.clean) cur = removeAlignedCollinearPoints(cur);
    return cur;
}

Polygon inflatePolygon(const Polygon& p, double gap, const OffsetParams& op) {
    Polygon out;
    out.external = offsetRing(p.external, gap, op);   // outer: +gap
    out.inners.reserve(p.inners.size());
    for (const auto& h : p.inners) {
        out.inners.push_back(offsetRing(h, -gap, op));  // inner: -gap (RE sign flip)
    }
    return out;
}

MultiPolygon inflatePolygon(const MultiPolygon& mp, double gap, const OffsetParams& op) {
    MultiPolygon out;
    out.reserve(mp.size());
    for (const auto& p : mp) out.push_back(inflatePolygon(p, gap, op));
    return out;
}

// ---------------------------------------------------------------------------
// misc
// ---------------------------------------------------------------------------
bool segmentsIntersect(const FPoint& p1, const FPoint& p2, const FPoint& q1, const FPoint& q2) {
    const int d1 = orient2d(q1, q2, p1);
    const int d2 = orient2d(q1, q2, p2);
    const int d3 = orient2d(p1, p2, q1);
    const int d4 = orient2d(p1, p2, q2);
    if (((d1 > 0 && d2 < 0) || (d1 < 0 && d2 > 0)) && ((d3 > 0 && d4 < 0) || (d3 < 0 && d4 > 0))) {
        return true;
    }
    auto onSeg = [](const FPoint& a, const FPoint& b, const FPoint& c) {
        return orient2d(a, b, c) == 0 && std::min(a.x, b.x) <= c.x && c.x <= std::max(a.x, b.x) &&
               std::min(a.y, b.y) <= c.y && c.y <= std::max(a.y, b.y);
    };
    return onSeg(q1, q2, p1) || onSeg(q1, q2, p2) || onSeg(p1, p2, q1) || onSeg(p1, p2, q2);
}

bool segmentCollinearOverlap(const FPoint& p1, const FPoint& p2, const FPoint& q1, const FPoint& q2,
                            double* overlapLength) {
    if (orient2d(p1, p2, q1) != 0 || orient2d(p1, p2, q2) != 0) return false;
    // project on the dominant axis
    const bool xAxis = std::llabs(p2.x - p1.x) >= std::llabs(p2.y - p1.y);
    auto lo = [xAxis](const FPoint& p) { return xAxis ? p.x : p.y; };
    fixed_t a0 = lo(p1), a1 = lo(p2);
    if (a0 > a1) std::swap(a0, a1);
    fixed_t b0 = lo(q1), b1 = lo(q2);
    if (b0 > b1) std::swap(b0, b1);
    const fixed_t s = std::max(a0, b0), e = std::min(a1, b1);
    if (s >= e) return false;
    if (overlapLength) *overlapLength = toDouble(e - s);
    return true;
}

bool ringsOverlap(const Ring& a, const Ring& b) {
    for (std::size_t i = 0; i < a.size(); ++i) {
        for (std::size_t j = 0; j < b.size(); ++j) {
            if (segmentsIntersect(a[i], a[(i + 1) % a.size()], b[j], b[(j + 1) % b.size()])) {
                return true;
            }
        }
    }
    if (!a.empty() && pointInRing(b, a.front())) return true;
    if (!b.empty() && pointInRing(a, b.front())) return true;
    return false;
}

double distancePointSegment(const Point& p, const Point& a, const Point& b) {
    const double vx = b.x - a.x, vy = b.y - a.y;
    const double wx = p.x - a.x, wy = p.y - a.y;
    const double vv = vx * vx + vy * vy;
    if (vv <= 0.0) return len(wx, wy);
    double t = (wx * vx + wy * vy) / vv;
    t = std::max(0.0, std::min(1.0, t));
    return len(p.x - (a.x + t * vx), p.y - (a.y + t * vy));
}

// ---------------------------------------------------------------------------
// WKT (the original serialises geometry as WKT: POLYGON / MULTIPOLYGON / LINESTRING)
// ---------------------------------------------------------------------------
namespace {
void writeRing(std::ostringstream& os, const Ring& r) {
    os << '(';
    for (std::size_t i = 0; i < r.size(); ++i) {
        if (i) os << ',';
        char buf[64];
        std::snprintf(buf, sizeof(buf), "%.10g %.10g", toDouble(r[i].x), toDouble(r[i].y));
        os << buf;
    }
    if (!r.empty()) {
        char buf[64];
        std::snprintf(buf, sizeof(buf), ",%.10g %.10g", toDouble(r[0].x), toDouble(r[0].y));
        os << buf;
    }
    os << ')';
}
}  // namespace

std::string toWkt(const Ring& r) {
    std::ostringstream os;
    os << "LINESTRING(";
    for (std::size_t i = 0; i < r.size(); ++i) {
        if (i) os << ',';
        char buf[64];
        std::snprintf(buf, sizeof(buf), "%.10g %.10g", toDouble(r[i].x), toDouble(r[i].y));
        os << buf;
    }
    os << ')';
    return os.str();
}

std::string toWkt(const Polygon& p) {
    std::ostringstream os;
    os << "POLYGON(";
    writeRing(os, p.external);
    for (const auto& h : p.inners) {
        os << ',';
        writeRing(os, h);
    }
    os << ')';
    return os.str();
}

std::string toWkt(const MultiPolygon& mp) {
    if (mp.size() == 1) return toWkt(mp.front());
    std::ostringstream os;
    os << "MULTIPOLYGON(";
    for (std::size_t i = 0; i < mp.size(); ++i) {
        if (i) os << ',';
        os << toWkt(mp[i]);
    }
    os << ')';
    return os.str();
}

}  // namespace lcns::geom
