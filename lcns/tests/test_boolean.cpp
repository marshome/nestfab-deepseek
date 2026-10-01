// tests/test_boolean.cpp -- polygon boolean operations, the keystone of the no-fit pipeline.
#include "check.hpp"
#include "lcns/boolean.hpp"
#include "lcns/model.hpp"

using namespace lcns;
using namespace lcns::geom;

namespace {

MultiPolygon box(double x, double y, double w, double h) {
    return makeRectMulti(x, y, w, h);
}

double areaOf(const MultiPolygon& mp) { return multiArea(mp); }

const Ring* outerRing(const MultiPolygon& mp, std::size_t i = 0) {
    if (i >= mp.size()) return nullptr;
    return &mp[i].external;
}

// An L shaped polygon: 10x10 with the 5x5 top right corner removed.
MultiPolygon lShape() {
    Polygon p;
    p.external = orientCCW(toRing({{0, 0}, {10, 0}, {10, 5}, {5, 5}, {5, 10}, {0, 10}}));
    return MultiPolygon{p};
}

// A non convex 8 pointed star: alternating outer and inner radii.
MultiPolygon star(double outer, double inner, int points) {
    std::vector<Point> pts;
    const double twoPi = 6.283185307179586476925286766559;
    for (int i = 0; i < points * 2; ++i) {
        const double r = (i % 2 == 0) ? outer : inner;
        const double a = twoPi * i / (points * 2);
        pts.push_back(Point{r * std::cos(a), r * std::sin(a)});
    }
    Polygon p;
    p.external = orientCCW(toRing(pts));
    return MultiPolygon{p};
}

// A rectangle with a rectangular hole.
MultiPolygon frame(double w, double h, double wall) {
    Polygon p = rectPolygon(0, 0, w, h);
    p.inners.push_back(reverse(rectPolygon(wall, wall, w - 2 * wall, h - 2 * wall).external));
    return MultiPolygon{p};
}

// The two convolution implementations must describe the same set. The loop walk is only
// applicable when both operands are convex (a non convex edge list is not angle monotone), so
// this is used for convex pairs; for the general case see checkBBoxIdentity below.
void checkPathsAgree(const char* what, const MultiPolygon& a, const MultiPolygon& b) {
    const MultiPolygon byLoops = minkowskiMulti(a, b);
    const MultiPolygon byDecomp = minkowskiMultiDecomposed(a, b);
    CHECK_MSG(!byLoops.empty(), what);
    CHECK_MSG(!byDecomp.empty(), what);
    const double la = multiArea(byLoops);
    const double da = multiArea(byDecomp);
    CHECK_MSG(std::fabs(la - da) < 1e-6 * (1.0 + std::fabs(da)),
              std::string(what) + ": areas " + std::to_string(la) + " vs " + std::to_string(da));
    const Box lb = bounds(byLoops);
    const Box db = bounds(byDecomp);
    CHECK_NEAR(toDouble(lb.min.x), toDouble(db.min.x), 1e-4);
    CHECK_NEAR(toDouble(lb.min.y), toDouble(db.min.y), 1e-4);
    CHECK_NEAR(toDouble(lb.max.x), toDouble(db.max.x), 1e-4);
    CHECK_NEAR(toDouble(lb.max.y), toDouble(db.max.y), 1e-4);
    CHECK_MSG(byLoops.size() == byDecomp.size(),
              std::string(what) + ": component counts " + std::to_string(byLoops.size()) + " vs " +
                  std::to_string(byDecomp.size()));
}

// A Minkowski sum always satisfies bbox(A+B) = [minA+minB, maxA+maxB]. This holds for convex
// and non convex operands alike, so it is an independent check on the general path.
void checkBBoxIdentity(const char* what, const MultiPolygon& a, const MultiPolygon& b) {
    const MultiPolygon s = minkowskiMulti(a, b);
    CHECK_MSG(!s.empty(), what);
    const Box ba = bounds(a);
    const Box bb = bounds(b);
    const Box sb = bounds(s);
    CHECK_NEAR(toDouble(sb.min.x), toDouble(ba.min.x + bb.min.x), 1e-3);
    CHECK_NEAR(toDouble(sb.min.y), toDouble(ba.min.y + bb.min.y), 1e-3);
    CHECK_NEAR(toDouble(sb.max.x), toDouble(ba.max.x + bb.max.x), 1e-3);
    CHECK_NEAR(toDouble(sb.max.y), toDouble(ba.max.y + bb.max.y), 1e-3);
    // the sum of two non empty sets is never smaller than either operand
    CHECK(multiArea(s) >= multiArea(a) - 1e-6);
    CHECK(multiArea(s) >= multiArea(b) - 1e-6);
}

}  // namespace

int main() {
    // --- union of two overlapping squares: [0,10]^2 | [5,15]x[0,10] = [0,15]x[0,10] ---
    {
        const MultiPolygon r = unite(box(0, 0, 10, 10), box(5, 0, 10, 10));
        CHECK(r.size() == 1);
        CHECK_NEAR(areaOf(r), 150.0, 1e-6);
        const Box b = bounds(r);
        CHECK_NEAR(toDouble(b.min.x), 0.0, 1e-6);
        CHECK_NEAR(toDouble(b.max.x), 15.0, 1e-6);
        CHECK_NEAR(toDouble(b.max.y), 10.0, 1e-6);
        CHECK(isCCW(r.front().external));
    }

    // --- union of two squares sharing an edge: the shared edge must vanish ---
    {
        const MultiPolygon r = unite(box(0, 0, 10, 10), box(10, 0, 10, 10));
        CHECK(r.size() == 1);
        CHECK_NEAR(areaOf(r), 200.0, 1e-6);
        const Box b = bounds(r);
        CHECK_NEAR(toDouble(b.max.x), 20.0, 1e-6);
        // collinear cleanup collapses the touching corners -> 4 corners
        CHECK_MSG(outerRing(r)->size() == 4, "merged ring should be the 4 corner rectangle");
    }

    // --- union of identical squares == the square itself (no doubled edges) ---
    {
        const MultiPolygon r = unite(box(0, 0, 10, 10), box(0, 0, 10, 10));
        CHECK(r.size() == 1);
        CHECK_NEAR(areaOf(r), 100.0, 1e-6);
        CHECK(outerRing(r)->size() == 4);
    }

    // --- union of disjoint squares stays two polygons ---
    {
        const MultiPolygon r = unite(box(0, 0, 10, 10), box(50, 0, 10, 10));
        CHECK(r.size() == 2);
        CHECK_NEAR(areaOf(r), 200.0, 1e-6);
    }

    // --- intersection ---
    {
        const MultiPolygon r = intersect(box(0, 0, 10, 10), box(5, 0, 10, 10));
        CHECK(r.size() == 1);
        CHECK_NEAR(areaOf(r), 50.0, 1e-6);
        const Box b = bounds(r);
        CHECK_NEAR(toDouble(b.min.x), 5.0, 1e-6);
        CHECK_NEAR(toDouble(b.max.x), 10.0, 1e-6);
    }
    {
        const MultiPolygon r = intersect(box(0, 0, 10, 10), box(50, 0, 10, 10));
        CHECK(r.empty());
        CHECK_NEAR(areaOf(r), 0.0, 1e-12);
    }
    {
        // one fully inside the other
        const MultiPolygon r = intersect(box(0, 0, 100, 100), box(10, 10, 20, 20));
        CHECK(r.size() == 1);
        CHECK_NEAR(areaOf(r), 400.0, 1e-6);
    }

    // --- difference producing a hole ---
    {
        const MultiPolygon r = subtract(box(0, 0, 10, 10), box(2, 2, 6, 6));
        CHECK(r.size() == 1);
        CHECK(r.front().inners.size() == 1);
        CHECK_NEAR(areaOf(r), 100.0 - 36.0, 1e-6);
        CHECK(isCCW(r.front().external));
        CHECK_MSG(!isCCW(r.front().inners.front()), "a hole must be wound clockwise");
        // a point inside the hole is outside the result
        CHECK(pointInMultiPolygon(r, FPoint{toFixed(5), toFixed(5)}) == 0);
        CHECK(pointInMultiPolygon(r, FPoint{toFixed(1), toFixed(1)}) == 1);
    }

    // --- difference of overlapping squares ---
    {
        const MultiPolygon r = subtract(box(0, 0, 10, 10), box(5, 0, 10, 10));
        CHECK(r.size() == 1);
        CHECK_NEAR(areaOf(r), 50.0, 1e-6);
        const Box b = bounds(r);
        CHECK_NEAR(toDouble(b.min.x), 0.0, 1e-6);
        CHECK_NEAR(toDouble(b.max.x), 5.0, 1e-6);
    }

    // --- L shape: corner notch ---
    {
        const MultiPolygon r = subtract(box(0, 0, 10, 10), box(5, 5, 5, 5));
        CHECK(r.size() == 1);
        CHECK(r.front().inners.empty());
        CHECK_NEAR(areaOf(r), 75.0, 1e-6);
        CHECK_MSG(outerRing(r)->size() == 6, "L shape must have 6 corners");
    }

    // --- xor ---
    {
        const MultiPolygon r = booleanOp(box(0, 0, 10, 10), box(5, 0, 10, 10), BoolOp::Xor);
        CHECK_NEAR(areaOf(r), 100.0, 1e-6);
        CHECK(r.size() == 2);
    }

    // --- empty operands ---
    {
        MultiPolygon empty;
        const MultiPolygon u = unite(empty, box(0, 0, 10, 10));
        CHECK_NEAR(areaOf(u), 100.0, 1e-6);
        const MultiPolygon i = intersect(empty, box(0, 0, 10, 10));
        CHECK(i.empty());
        const MultiPolygon d = subtract(box(0, 0, 10, 10), empty);
        CHECK_NEAR(areaOf(d), 100.0, 1e-6);
    }

    // --- overlapping instance of one notch: three squares in a row ---
    {
        MultiPolygon acc = unite(box(0, 0, 10, 10), box(10, 0, 10, 10));
        acc = unite(acc, box(20, 0, 10, 10));
        CHECK(acc.size() == 1);
        CHECK_NEAR(areaOf(acc), 300.0, 1e-6);
        CHECK_NEAR(toDouble(bounds(acc).max.x), 30.0, 1e-6);
    }

    // --- uniteSelf merges overlapping members of one set ---
    {
        MultiPolygon mp;
        mp.push_back(box(0, 0, 10, 10).front());
        mp.push_back(box(5, 0, 10, 10).front());
        const MultiPolygon r = uniteSelf(mp);
        CHECK(r.size() == 1);
        CHECK_NEAR(areaOf(r), 150.0, 1e-6);
    }

    // --- normalize: nesting parity decides outer vs hole ---
    {
        MultiPolygon mp;
        Polygon outer;
        outer.external = toRing({{0, 0}, {10, 0}, {10, 10}, {0, 10}});   // CCW
        if (!isCCW(outer.external)) outer.external = reverse(outer.external);
        mp.push_back(outer);
        Polygon mid;
        mid.external = toRing({{2, 2}, {8, 2}, {8, 8}, {2, 8}});         // also CCW: a hole
        mp.push_back(mid);
        Polygon inner;
        inner.external = toRing({{4, 4}, {6, 4}, {6, 6}, {4, 6}});       // island again
        mp.push_back(inner);
        const MultiPolygon r = normalize(mp);
        CHECK(r.size() == 2);                 // the outer (+hole) and the island
        CHECK(r[0].inners.size() == 1);
        CHECK_NEAR(multiArea(r), 100.0 - 36.0 + 4.0, 1e-6);
    }

    // --- normalize drops degenerate input ---
    {
        MultiPolygon mp;
        Polygon degen;
        degen.external = toRing({{0, 0}, {10, 0}, {20, 0}});  // zero area
        mp.push_back(degen);
        const MultiPolygon r = normalize(mp);
        CHECK(r.empty());
    }

    // --- area bookkeeping is consistent ---
    {
        const MultiPolygon a = box(0, 0, 10, 10);
        const MultiPolygon b = box(5, 0, 10, 10);
        const double au = areaOf(unite(a, b));
        const double ai = areaOf(intersect(a, b));
        const double ad = areaOf(subtract(a, b));
        CHECK_NEAR(au, areaOf(a) + areaOf(b) - ai, 1e-6);   // inclusion-exclusion
        CHECK_NEAR(ad, areaOf(a) - ai, 1e-6);
    }

    // --- the loop-walk convolution and the convex decomposition must agree ---
    {
        // convex (+) convex: both algorithms apply and must produce the same set
        checkPathsAgree("square(4) + square(2)", box(0, 0, 4, 4), box(0, 0, 2, 2));
        checkPathsAgree("square(10) + square(10)", box(0, 0, 10, 10), box(3, 3, 10, 10));
        checkPathsAgree("square + triangle", box(0, 0, 6, 4),
                        MultiPolygon{Polygon{orientCCW(toRing({{0, 0}, {5, 0}, {0, 5}})), {}}});
        checkPathsAgree("pentagon + square", MultiPolygon{Polygon{convexHull(toRing(
                                               {{0, 0}, {4, 0}, {6, 3}, {3, 6}, {-1, 4}})), {}}},
                        box(0, 0, 2, 2));
    }

    // --- bounding box identity holds for every operand shape (independent check) ---
    {
        checkBBoxIdentity("square + square", box(0, 0, 4, 4), box(0, 0, 2, 2));
        checkBBoxIdentity("square + L", box(0, 0, 4, 4), lShape());
        checkBBoxIdentity("L + square", lShape(), box(0, 0, 4, 4));
        checkBBoxIdentity("L + L", lShape(), lShape());
        checkBBoxIdentity("star + L", star(10.0, 4.0, 8), lShape());
        checkBBoxIdentity("star + star", star(10.0, 4.0, 8), star(6.0, 2.5, 5));
        checkBBoxIdentity("frame + square", frame(20.0, 20.0, 5.0), box(0, 0, 4, 4));
        checkBBoxIdentity("L + frame", lShape(), frame(8.0, 8.0, 2.0));
    }

    // --- the raw loop walk: shape of its output (exact for convex operands) ---
    {
        // convex operands give exactly one loop, and it is the sum boundary
        const std::vector<Ring> convexLoops = convolveRingLoops(
            orientCCW(rectPolygon(0, 0, 4, 4).external), orientCCW(rectPolygon(0, 0, 2, 2).external));
        CHECK(convexLoops.size() == 1);
        CHECK(isCCW(convexLoops.front()));
        CHECK_NEAR(area(convexLoops.front()), 36.0, 1e-6);

        // the loop walk is also the path that produces a non convex sum when one operand has a
        // single reflex-free complement: a square summed with the negated L gives the known 171
        const std::vector<Ring> mixedLoops =
            convolveRingLoops(orientCCW(rectPolygon(0, 0, 4, 4).external),
                              orientCCW(negateRing(lShape().front().external)));
        CHECK(!mixedLoops.empty());
        for (const auto& loop : mixedLoops) {
            CHECK(isSimple(loop));
            CHECK(area(loop) != 0.0);
        }
        CHECK_NEAR(multiArea(classifyConvolutionLoops(mixedLoops)), 171.0, 1e-3);

        // classifyConvolutionLoops drops degenerate loops and keeps real ones
        MultiPolygon classified = classifyConvolutionLoops(convexLoops);
        CHECK(classified.size() == 1);
        CHECK_NEAR(multiArea(classified), 36.0, 1e-6);
        std::vector<Ring> degenerate;
        degenerate.push_back(toRing({{0, 0}, {1, 1}}));                       // 2 points
        degenerate.push_back(toRing({{0, 0}, {1, 1}, {2, 2}}));               // zero area
        CHECK(classifyConvolutionLoops(degenerate).empty());
        CHECK(classifyConvolutionLoops({}).empty());
    }

    // --- a hole in the sum: the frame's bore is carried through ---
    {
        const MultiPolygon sum = minkowskiMulti(frame(20.0, 20.0, 5.0), box(0, 0, 4, 4));
        CHECK(sum.size() == 1);
        CHECK_MSG(sum.front().inners.size() == 1, "the bore must survive as an inner ring");
        // outer 20x20 grows to 24x24 = 576; the 10x10 bore grows to 14x14 = 196
        CHECK_NEAR(areaOf(sum), 576.0 - 196.0, 1e-3);
        CHECK(isCCW(sum.front().external));
        CHECK(!isCCW(sum.front().inners.front()));   // holes are clockwise
    }

    // --- regularize: a self intersecting bow tie is rebuilt from its even-odd interior ---
    {
        Ring bow = toRing({{0, 0}, {10, 10}, {10, 0}, {0, 10}});
        MultiPolygon mp;
        Polygon p;
        p.external = bow;
        mp.push_back(p);
        CHECK_MSG(!isSimple(bow), "the input really is self intersecting");
        const MultiPolygon r = regularize(mp);
        // even-odd interior = two triangles of 25 each, touching at (5,5), split into
        // two simple rings at the repeated node
        CHECK_NEAR(areaOf(r), 50.0, 1e-6);
        CHECK_MSG(r.size() == 2, "the pinch point must split the walk into two rings");
        for (const auto& poly : r) {
            CHECK_MSG(isSimple(poly.external), "regularised rings must be simple");
            CHECK_NEAR(area(poly.external), 25.0, 1e-6);
        }
    }

    // --- regularize on already valid input is a no-op in terms of area ---
    {
        const MultiPolygon a = box(0, 0, 10, 10);
        const MultiPolygon r = regularize(a);
        CHECK(r.size() == 1);
        CHECK_NEAR(areaOf(r), 100.0, 1e-6);
    }

    // --- Minkowski sum with holes (inclusion-exclusion) ---
    {
        // a frame (outer 10x10, hole 4x4 centred) plus -a 2x2 box
        MultiPolygon frame;
        Polygon f;
        f.external = orientCCW(toRing({{0, 0}, {10, 0}, {10, 10}, {0, 10}}));
        f.inners.push_back(reverse(orientCCW(toRing({{3, 3}, {7, 3}, {7, 7}, {3, 7}}))));
        frame.push_back(f);
        const MultiPolygon small = box(0, 0, 2, 2);
        const MultiPolygon sum = minkowskiMulti(frame, small);
        // The sum sweeps the small box around the frame: the outer 10x10 grows to 12x12 and
        // the 4x4 hole also grows (the hole boundary is swept too) to 6x6
        // => area 144 - 36 = 108
        CHECK_NEAR(areaOf(sum), 108.0, 1e-3);
        const Box b = bounds(sum);
        CHECK_NEAR(toDouble(b.max.x), 12.0, 1e-3);
        CHECK_NEAR(toDouble(b.min.x), 0.0, 1e-3);
        CHECK_MSG(sum.size() == 1 && sum.front().inners.size() == 1,
                  "the hole must survive as an inner ring");
    }

    // --- non convex NFP: L shaped part against a square ---
    {
        MultiPolygon lshape;  // 10x10 minus the 5x5 top right corner
        Polygon p;
        p.external = orientCCW(toRing({{0, 0}, {10, 0}, {10, 5}, {5, 5}, {5, 10}, {0, 10}}));
        lshape.push_back(p);
        const MultiPolygon obst = box(0, 0, 4, 4);
        const MultiPolygon n = nfpMulti(obst, lshape);
        CHECK(!n.empty());
        // NFP(obst, part) = obst (+) -part, so its extent is obst + reflected part extents
        const Box b = bounds(n);
        CHECK_NEAR(toDouble(b.min.x), -10.0, 1e-3);
        CHECK_NEAR(toDouble(b.max.x), 4.0, 1e-3);
        CHECK_NEAR(toDouble(b.min.y), -10.0, 1e-3);
        CHECK_NEAR(toDouble(b.max.y), 4.0, 1e-3);
        // the NFP of a non convex part is not simply a rectangle: its area is below the box
        CHECK(areaOf(n) < 14.0 * 14.0);
        for (const auto& poly : n) {
            CHECK(isSimple(poly.external));
        }
    }

    // --- inflateCleaned keeps concave offsets simple ---
    {
        Polygon l;
        l.external = orientCCW(toRing({{0, 0}, {20, 0}, {20, 5}, {5, 5}, {5, 20}, {0, 20}}));
        OffsetParams op;
        op.step = 0.5;
        const Polygon grown = inflateCleaned(l, 2.0, op);
        CHECK(grown.external.size() >= 3);
        CHECK_MSG(isSimple(grown.external), "cleaned offset must not self intersect");
        CHECK(area(grown.external) > area(l.external));
        // an aggressive inward offset collapses or stays simple, never self intersects
        const Polygon shrunk = inflateCleaned(l, -1.0, op);
        if (shrunk.external.size() >= 3) CHECK(isSimple(shrunk.external));
    }

    return check::finish("test_boolean");
}
