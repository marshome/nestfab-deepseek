// tests/test_nofit.cpp -- NoFitMap cache behaviour and NoFitNesting bookkeeping.
#include "check.hpp"
#include "lcns/model.hpp"
#include "lcns/nfp.hpp"

using namespace lcns;

namespace {
Order makeOrder() {
    Order o;
    Sheet s;
    s.id = 0;
    s.width = 100.0;
    s.height = 80.0;
    o.sheets.push_back(s);

    Part p;
    p.id = 0;
    p.rawShape = makeRectMulti(0, 0, 20, 10);
    p.shape = p.rawShape;
    p.multiplicity = 2;
    o.parts.push_back(p);

    Part q = p;
    q.id = 1;
    q.rawShape = makeRectMulti(0, 0, 15, 15);
    q.shape = q.rawShape;
    q.multiplicity = 1;
    o.parts.push_back(q);
    return o;
}
}  // namespace

int main() {
    const Order order = makeOrder();

    // RE defaults: m_max_complexity default 25000 (0x61A8), cache clear at 19,999,999
    {
        NoFitMap m;
        CHECK(m.maximumComplexity() == NoFitMap::kDefaultMaxComplexity);
        CHECK(NoFitMap::kDefaultMaxComplexity == 25000);
        CHECK(NoFitMap::kCacheClearThreshold == 19999999u);
        CHECK_NEAR(NoFitMap::kTolerance, 1e-6, 0.0);
        CHECK(m.entryCount() == 0);
        CHECK(m.cachedPolygons() == 0);
    }

    // building an entry and hitting the cache
    {
        NoFitMap m;
        const NFPEntry& e = m.get(order, 0, 0, false, 0, 0.0);
        CHECK(e.partIndex == 0);
        CHECK(e.sheetIndex == 0);
        CHECK(!e.flipped);
        CHECK_NEAR(e.angle, 0.0, 0.0);
        CHECK(!e.map.empty());                       // sheet/part convolution exists
        CHECK(e.polygonCount() == e.map.size());
        const std::size_t after = m.entryCount();
        CHECK(after == 1);
        const std::size_t polys = m.cachedPolygons();
        CHECK(polys >= 1);

        // same key -> cache hit, no growth
        const NFPEntry& e2 = m.get(order, 0, 0, false, 0, 0.0);
        CHECK(&e2 == &e);
        CHECK(m.entryCount() == after);
        CHECK(m.cachedPolygons() == polys);

        // different orientation / flip -> new key
        m.get(order, 0, 0, true, 0, 0.0);
        CHECK(m.entryCount() == 2);
        m.get(order, 1, 0, false, 0, 0.0);
        CHECK(m.entryCount() == 3);

        m.clear();
        CHECK(m.entryCount() == 0);
        CHECK(m.cachedPolygons() == 0);
    }

    // maximum complexity drives tooComplex() and the angle-step reduction in placePart
    {
        NoFitMap m;
        m.setMaximumComplexity(1);
        CHECK(m.maximumComplexity() == 1);
        m.get(order, 0, 0, false, 0, 0.0);
        m.get(order, 1, 0, false, 0, 0.0);
        CHECK(m.tooComplex() || m.cachedPolygons() <= 1);
        m.setMaximumComplexity(0);                    // 0 falls back to the default
        CHECK(m.maximumComplexity() == NoFitMap::kDefaultMaxComplexity);
    }

    // sheet keeps its own key: the entry records the outline actually used
    {
        NoFitMap m;
        const NFPEntry& e = m.get(order, 0, 0, false, 3, 1.5707963267948966);
        const geom::Box b = geom::bounds(e.sheetOutline.external);
        CHECK_NEAR(geom::toDouble(b.max.x - b.min.x), 100.0, 1e-6);
        CHECK_NEAR(geom::toDouble(b.max.y - b.min.y), 80.0, 1e-6);
        CHECK_NEAR(e.angle, 1.5707963267948966, 1e-12);
    }

    // NoFitNesting bookkeeping (RE 32-byte object, addNestedPart pushes a 40-byte record)
    {
        NoFitMap m;
        NoFitNesting n(m, 0);
        CHECK(n.sheetIndex() == 0);
        CHECK(n.placements().empty());
        NoFitPlacement p;
        p.partIndex = 0;
        p.x = 5.0;
        p.y = 7.0;
        p.angle = 0.0;
        n.addNestedPart(p);
        CHECK(n.placements().size() == 1);
        CHECK_NEAR(n.placements().front().x, 5.0, 0.0);

        const geom::MultiPolygon forb =
            n.forbiddenRegion(order, 1, false, 0.0, order.parts[1].shape);
        CHECK(!forb.empty());   // one placed part -> one NFP polygon

        // the forbidden list must contain the placed part's own reference area
        const bool hit = NoFitNesting::forbiddenContains(forb, geom::FPoint{geom::toFixed(5.0), geom::toFixed(7.0)});
        CHECK(hit);

        n.clear();
        CHECK(n.placements().empty());
    }

    return check::finish("test_nofit");
}
