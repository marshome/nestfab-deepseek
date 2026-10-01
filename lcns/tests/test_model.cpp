// tests/test_model.cpp -- model helpers, recovered enums and property mapping.
#include "check.hpp"
#include "lcns/model.hpp"

#include <cstring>

using namespace lcns;

int main() {
    // --- enums decoded from the dump function at RVA 0x511080 ---
    CHECK(static_cast<int>(Objective::MinimizeX) == 0);
    CHECK(static_cast<int>(Objective::MinimizeY) == 1);
    CHECK(static_cast<int>(Objective::NoOffcut) == 2);
    CHECK(static_cast<int>(Objective::MinimizeArea) == 3);
    CHECK(static_cast<int>(Objective::MinimizeXThenY) == 4);
    CHECK(static_cast<int>(Objective::MinimizeYThenX) == 5);
    CHECK(static_cast<int>(Objective::IntelligentMinimizeX) == 6);
    CHECK(static_cast<int>(Objective::IntelligentMinimizeY) == 7);
    CHECK(static_cast<int>(NestingOrigin::BottomLeft) == 0);
    CHECK(static_cast<int>(NestingOrigin::TopLeft) == 1);
    CHECK(static_cast<int>(NestingOrigin::BottomRight) == 2);
    CHECK(static_cast<int>(NestingOrigin::TopRight) == 3);

    // --- confidence tags used by the generated export table ---
    CHECK(static_cast<int>(Confidence::Unknown) == 0);
    CHECK(static_cast<int>(Confidence::Inferred) == 1);
    CHECK(static_cast<int>(Confidence::Recovered) == 2);

    // --- Polygon layout matches the recovered member offsets: Ring at +0, inners at +0x18 ---
    {
        geom::Polygon p;
        const auto base = reinterpret_cast<const char*>(&p);
        const auto offInners = reinterpret_cast<const char*>(&p.inners) - base;
        CHECK_MSG(offInners == 0x18, "Polygon::inners must sit at +0x18 like the original");
        CHECK(sizeof(geom::Ring) == 24);   // std::vector<FPoint>
    }

    // --- primitive constructors ---
    {
        const geom::Polygon r = rectPolygon(1, 2, 10, 4);
        CHECK_NEAR(geom::area(r.external), 40.0, 1e-6);
        CHECK(geom::isCCW(r.external));
        const geom::Box b = geom::bounds(r.external);
        CHECK_NEAR(geom::toDouble(b.min.x), 1.0, 1e-9);
        CHECK_NEAR(geom::toDouble(b.max.y), 6.0, 1e-9);

        const geom::Polygon c = circlePolygon(0, 0, 10.0, 256);
        CHECK_NEAR(geom::area(c.external), 3.14159265358979 * 100.0, 0.5);
        CHECK(geom::isCCW(c.external));

        CHECK(makeRectMulti(0, 0, 2, 3).size() == 1);
    }

    // --- placeShape: rotation is about the shape origin ---
    {
        geom::MultiPolygon shape = makeRectMulti(0, 0, 10, 5);
        NestedPart np;
        np.angle = 0.0;
        geom::Box b = placeBounds(shape, np);
        CHECK_NEAR(b.width(), 10.0, 1e-9);
        CHECK_NEAR(b.height(), 5.0, 1e-9);

        np.angle = 1.5707963267948966;  // 90 degrees
        b = placeBounds(shape, np);
        CHECK_NEAR(b.width(), 5.0, 1e-6);
        CHECK_NEAR(b.height(), 10.0, 1e-6);

        np.angle = 0.0;
        np.flipped = true;
        b = placeBounds(shape, np);
        CHECK_NEAR(b.width(), 10.0, 1e-9);
    }

    // --- sheet / part measures ---
    {
        Sheet s;
        s.width = 100.0;
        s.height = 50.0;
        CHECK_NEAR(s.area(), 5000.0, 1e-9);
        const geom::Polygon o = sheetPolygon(s);
        CHECK_NEAR(geom::area(o.external), 5000.0, 1e-6);

        Part p;
        p.rawShape = makeRectMulti(0, 0, 20, 10);
        p.shape = p.rawShape;
        p.multiplicity = 3;
        CHECK_NEAR(p.area(), 200.0, 1e-9);
        CHECK_NEAR(p.width(), 20.0, 1e-9);
        CHECK_NEAR(p.height(), 10.0, 1e-9);
    }

    // --- CommonCutProperties follows the original serialiser's field order ---
    {
        CommonCutProperties c;
        CHECK(sizeof(c) >= 8 * 5);
        CHECK(c.allowed == 0);
        CHECK_NEAR(c.gap, 0.0, 0.0);
        CHECK(c.leadinType == 0);
        CHECK(c.noHoles == 0);
        CHECK(c.onlyBiModules == 0);
    }

    // --- multiline: the three offcut doubles and the mode tags ---
    {
        Order o;
        o.commonCutModeTag = 1;   // preset mode
        o.commonCutPresetIndex2 = 0;
        CommonCutProperties preset;
        preset.allowed = 7;
        preset.gap = 1.5;
        o.commonCutPresets.push_back(preset);
        const CommonCutProperties got = o.commonCutProperties();
        CHECK(got.allowed == 7);
        CHECK_NEAR(got.gap, 1.5, 1e-12);

        o.commonCutModeTag = 0;   // explicit mode -> objective ratio
        o.commonCutObjectiveNum = 3.0;
        o.commonCutObjectiveDen = 4.0;
        o.commonCutModeA = 2;
        const CommonCutProperties got2 = o.commonCutProperties();
        CHECK(got2.allowed == 2);
        CHECK_NEAR(got2.maxRegardingRatio, 0.75, 1e-12);

        o.multitorchModeTag = 0;
        o.multitorchNbTorches = 4;
        o.multitorchMinDistance = 11.0;
        const MultitorchProperties mp = o.multitorchProperties();
        CHECK(mp.nbTorches == 4);
        CHECK_NEAR(mp.minTorchDistance, 11.0, 1e-12);
    }

    // --- order level aggregates ---
    {
        Order o;
        Sheet s;
        s.width = 100.0;
        s.height = 100.0;
        s.quantity = 2;
        o.sheets.push_back(s);
        Part p;
        p.rawShape = makeRectMulti(0, 0, 10, 10);
        p.multiplicity = 5;
        o.parts.push_back(p);
        CHECK(o.totalPartInstances() == 5);
        CHECK_NEAR(o.totalPartArea(), 500.0, 1e-9);
        CHECK_NEAR(o.totalSheetArea(), 20000.0, 1e-9);
    }

    // --- solution statistics (RE stats.cpp FillRatio / UsedSurfaceAux) ---
    {
        Solution s;
        Nesting n;
        n.sheetArea = 1000.0;
        n.usedSurface = 400.0;
        s.nestings.push_back(n);
        CHECK_NEAR(s.usedSurface(), 400.0, 1e-9);
        CHECK_NEAR(s.sheetArea(), 1000.0, 1e-9);
        CHECK_NEAR(s.fillRatio(), 0.4, 1e-12);
        CHECK(s.totalNestedParts() == 0);
    }

    return check::finish("test_model");
}
