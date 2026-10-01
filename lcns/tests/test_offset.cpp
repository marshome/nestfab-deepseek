// tests/test_offset.cpp -- incremental polygon offsetting (RE 0x58A7E0) and inflation.
#include "check.hpp"
#include "lcns/geom.hpp"

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
    // --- single pass, step chosen so that N = floor(dist/step + 0.5) == 1 ---
    {
        OffsetParams p;
        p.step = 1.0;
        const Ring out = offsetRing(square(0, 0, 10, 10), 1.0, p);
        const Box b = bounds(out);
        CHECK_NEAR(toDouble(b.min.x), -1.0, 1e-6);
        CHECK_NEAR(toDouble(b.min.y), -1.0, 1e-6);
        CHECK_NEAR(toDouble(b.max.x), 11.0, 1e-6);
        CHECK_NEAR(toDouble(b.max.y), 11.0, 1e-6);
        CHECK_NEAR(area(out), 144.0, 1e-3);
        CHECK(isCCW(out));
    }

    // --- multi step: N = floor(1.0 / 0.1 + 0.5) = 10 incremental passes ---
    {
        OffsetParams p;
        p.step = 0.1;
        const Ring out = offsetRing(square(0, 0, 10, 10), 1.0, p);
        const Box b = bounds(out);
        CHECK_NEAR(toDouble(b.min.x), -1.0, 1e-3);
        CHECK_NEAR(toDouble(b.max.x), 11.0, 1e-3);
        CHECK_NEAR(area(out), 144.0, 0.5);
    }

    // --- shrinking (negative distance) ---
    {
        OffsetParams p;
        p.step = 1.0;
        const Ring out = offsetRing(square(0, 0, 10, 10), -2.0, p);
        const Box b = bounds(out);
        CHECK_NEAR(toDouble(b.min.x), 2.0, 1e-6);
        CHECK_NEAR(toDouble(b.max.x), 8.0, 1e-6);
        CHECK_NEAR(area(out), 36.0, 1e-3);
    }

    // --- zero distance is a no-op (after cleanup) ---
    {
        const Ring out = offsetRing(square(0, 0, 10, 10), 0.0);
        CHECK_NEAR(area(out), 100.0, 1e-6);
    }

    // --- a triangle keeps its orientation and grows ---
    {
        Ring tri = toRing({{0, 0}, {10, 0}, {0, 10}});
        if (!isCCW(tri)) tri = reverse(tri);
        CHECK(isCCW(tri));
        OffsetParams p;
        p.step = 1.0;
        const Ring out = offsetRing(tri, 1.0, p);
        CHECK(isCCW(out));
        CHECK(area(out) > area(tri));
    }

    // --- polygon inflation: outer +gap, inner -gap (RE AddInflatedToolPathToPart) ---
    {
        Polygon poly;
        poly.external = square(0, 0, 100, 100);
        poly.inners.push_back(reverse(square(40, 40, 20, 20)));
        const double outer0 = area(poly.external);
        const double hole0 = area(poly.inners.front());

        OffsetParams p;
        p.step = 0.5;
        const Polygon inf = inflatePolygon(poly, 2.0, p);
        CHECK(area(inf.external) > outer0);           // outer grew
        CHECK(area(inf.inners.front()) < hole0);      // hole shrank
        const Box hb = bounds(inf.inners.front());
        CHECK_NEAR(toDouble(hb.min.x), 42.0, 1e-3);   // 40 + 2
        CHECK_NEAR(toDouble(hb.max.x), 58.0, 1e-3);   // 60 - 2
    }

    // --- keep-out distance is honoured: a point 1.5 away from a 2.0 offset is inside ---
    {
        OffsetParams p;
        p.step = 0.5;
        const Ring out = offsetRing(square(0, 0, 10, 10), 2.0, p);
        CHECK(pointInRing(out, FPoint{toFixed(-1.5), toFixed(5)}));
        CHECK(!pointInRing(out, FPoint{toFixed(-2.5), toFixed(5)}));
    }

    return check::finish("test_offset");
}
