// tests/test_conv.cpp -- rings, areas and the boundary convolution (Minkowski / NFP).
#include "check.hpp"
#include "lcns/geom.hpp"
#include "lcns/model.hpp"

using namespace lcns;
using namespace lcns::geom;

namespace {
Ring square(double x, double y, double w, double h) {
    Ring r = toRing({{x, y}, {x + w, y}, {x + w, y + h}, {x, y + h}});
    if (!isCCW(r)) r = reverse(r);
    return r;
}
}  // namespace

int main() {
    // --- ring measures ---
    {
        const Ring s = square(0, 0, 10, 10);
        CHECK(isCCW(s));
        CHECK_NEAR(area(s), 100.0, 1e-6);
        CHECK_NEAR(perimeter(s), 40.0, 1e-6);
        const Box b = bounds(s);
        CHECK_NEAR(toDouble(b.max.x - b.min.x), 10.0, 1e-9);
        CHECK_NEAR(toDouble(b.max.y - b.min.y), 10.0, 1e-9);
        CHECK_NEAR(b.area(), 100.0, 1e-6);
    }
    {
        const Ring s = reverse(square(0, 0, 10, 10));
        CHECK(!isCCW(s));
        CHECK_NEAR(area(s), 100.0, 1e-6);  // area is unsigned
    }

    // --- point in ring (exact winding) ---
    {
        const Ring s = square(0, 0, 10, 10);
        CHECK(pointInRing(s, FPoint{toFixed(5), toFixed(5)}));
        CHECK(!pointInRing(s, FPoint{toFixed(15), toFixed(5)}));
        CHECK(!pointInRing(s, FPoint{toFixed(-0.5), toFixed(5)}));
        Polygon poly;
        poly.external = s;
        Ring hole = reverse(square(4, 4, 2, 2));
        poly.inners.push_back(hole);
        CHECK(pointInPolygon(poly, FPoint{toFixed(1), toFixed(1)}));
        CHECK(!pointInPolygon(poly, FPoint{toFixed(5), toFixed(5)}));  // inside the hole
    }

    // --- collinear cleanup (RE: ..\exact\path.cpp RemoveAlignedCollinearPoints) ---
    {
        Ring r = toRing({{0, 0}, {5, 0}, {10, 0}, {10, 10}, {0, 10}});
        const Ring c = removeAlignedCollinearPoints(r);
        CHECK(c.size() == 4);
        CHECK_NEAR(area(c), 100.0, 1e-6);
    }

    // --- convex hull ---
    {
        Ring pts = toRing({{0, 0}, {10, 0}, {10, 10}, {0, 10}, {5, 5}});
        const Ring h = convexHull(pts);
        CHECK(h.size() == 4);
        CHECK_NEAR(area(h), 100.0, 1e-6);
    }

    // --- convolution of two axis aligned squares: [0,10]^2 + [0,5]^2 = [0,15]^2 ---
    {
        const Ring a = square(0, 0, 10, 10);
        const Ring b = square(0, 0, 5, 5);
        const Ring s = minkowskiSum(a, b);
        CHECK(s.size() >= 4);
        const Box bb = bounds(s);
        CHECK_NEAR(toDouble(bb.min.x), 0.0, 1e-6);
        CHECK_NEAR(toDouble(bb.min.y), 0.0, 1e-6);
        CHECK_NEAR(toDouble(bb.max.x), 15.0, 1e-6);
        CHECK_NEAR(toDouble(bb.max.y), 15.0, 1e-6);
        CHECK_NEAR(area(s), 225.0, 1e-3);
    }

    // --- no-fit polygon: nfp(a,b) = a (+) -b   ->   [-5,10] x [-5,10] ---
    {
        const Ring a = square(0, 0, 10, 10);
        const Ring b = square(0, 0, 5, 5);
        const Ring n = nfp(a, b);
        const Box bb = bounds(n);
        CHECK_NEAR(toDouble(bb.min.x), -5.0, 1e-6);
        CHECK_NEAR(toDouble(bb.min.y), -5.0, 1e-6);
        CHECK_NEAR(toDouble(bb.max.x), 10.0, 1e-6);
        CHECK_NEAR(toDouble(bb.max.y), 10.0, 1e-6);
    }

    // --- edge records carry the RE quadrant tag ---
    {
        const auto e = buildEdges(square(0, 0, 10, 10), square(0, 0, 5, 5));
        CHECK(e.size() == 8);
        int q1 = 0, q2 = 0, q3 = 0, q4 = 0;
        for (const auto& x : e) {
            CHECK(x.quadrant >= 1 && x.quadrant <= 4);
            if (x.quadrant == 1) ++q1;
            if (x.quadrant == 2) ++q2;
            if (x.quadrant == 3) ++q3;
            if (x.quadrant == 4) ++q4;
        }
        CHECK(q1 + q2 + q3 + q4 == 8);
        // CCW traversal order of the geometric quadrants is 1 -> 4 -> 3 -> 2
        CHECK(quadrantRank(1) < quadrantRank(4));
        CHECK(quadrantRank(4) < quadrantRank(3));
        CHECK(quadrantRank(3) < quadrantRank(2));
    }

    // --- segment predicates used by common cut detection ---
    {
        const FPoint p1{0, 0}, p2{toFixed(10), 0};
        const FPoint q1{toFixed(3), 0}, q2{toFixed(7), 0};
        double len = 0.0;
        CHECK(segmentCollinearOverlap(p1, p2, q1, q2, &len));
        CHECK_NEAR(len, 4.0, 1e-9);
        CHECK(!segmentCollinearOverlap(p1, p2, FPoint{0, kScaleI}, FPoint{toFixed(10), kScaleI}, nullptr));
        CHECK(segmentsIntersect(p1, p2, FPoint{toFixed(5), toFixed(-1)}, FPoint{toFixed(5), toFixed(1)}));
        CHECK(!segmentsIntersect(p1, p2, FPoint{toFixed(5), toFixed(1)}, FPoint{toFixed(5), toFixed(2)}));
    }

    // --- WKT serialisation (the original emits POLYGON / MULTIPOLYGON / LINESTRING) ---
    {
        Polygon p;
        p.external = square(0, 0, 1, 1);
        const std::string w = toWkt(p);
        CHECK(w.rfind("POLYGON(", 0) == 0);
    }

    return check::finish("test_conv");
}
