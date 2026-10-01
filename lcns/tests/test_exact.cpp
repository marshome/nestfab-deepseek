// tests/test_exact.cpp -- the exact fixed-point kernel and the 128-bit predicates.
#include "check.hpp"
#include "lcns/geom.hpp"

using namespace lcns::geom;

int main() {
    // --- 128-bit multiply, the operation the original implements with imul/mul + adc/sbb ---
    {
        const std::int64_t a = 3'000'000'000ll;
        const std::int64_t b = 4'000'000'000ll;
        const Int128 r = mul64(a, b);
        CHECK_NEAR(r.toDouble(), 1.2e19, 1e15);
        CHECK(!r.isNegative());
    }
    {
        const Int128 r = mul64(-5, 7);
        CHECK(r.isNegative());
        CHECK_NEAR(r.toDouble(), -35.0, 1e-9);
    }
    {
        const Int128 r = mul64(-3, -3);
        CHECK(!r.isNegative());
        CHECK_NEAR(r.toDouble(), 9.0, 1e-9);
    }
    {
        // boundary: 2^62 * 2^62 == 2^124 must stay exact in 128 bits
        const std::int64_t v = 1ll << 62;
        const Int128 r = mul64(v, v);
        CHECK_NEAR(r.toDouble(), 2.1267647932558654e37, 1e33);
    }

    // --- fixed point scale 1e10 (RE constant @ 0x9AD708) ---
    CHECK_NEAR(kScale, 1e10, 0.0);
    CHECK(toFixed(1.0) == kScaleI);
    CHECK_NEAR(toDouble(toFixed(123.456)), 123.456, 1e-9);
    CHECK(toFixed(-2.5) == -25000000000ll);

    // --- orientation predicate ---
    const FPoint o{0, 0};
    const FPoint a{toFixed(10.0), 0};
    const FPoint b{0, toFixed(10.0)};
    CHECK(orient2d(o, a, b) > 0);   // counter clockwise
    CHECK(orient2d(o, b, a) < 0);   // clockwise
    CHECK(orient2d(o, a, FPoint{toFixed(20.0), 0}) == 0);  // collinear
    // a case where double arithmetic would be inconclusive
    CHECK(orient2d(FPoint{0, 0}, FPoint{kScaleI, kScaleI}, FPoint{kScaleI, kScaleI}) == 0);

    // --- cross sign ---
    CHECK(crossSign(FPoint{toFixed(1), 0}, FPoint{0, toFixed(1)}) > 0);
    CHECK(crossSign(FPoint{0, toFixed(1)}, FPoint{toFixed(1), 0}) < 0);
    CHECK(crossSign(FPoint{toFixed(2), toFixed(2)}, FPoint{toFixed(3), toFixed(3)}) == 0);

    // --- quadrant classification, exactly the RE scheme ---
    CHECK(quadrantOf(toFixed(1), toFixed(1)) == 1);
    CHECK(quadrantOf(toFixed(1), 0) == 2);
    CHECK(quadrantOf(toFixed(1), toFixed(-1)) == 2);
    CHECK(quadrantOf(toFixed(-1), toFixed(-1)) == 3);
    CHECK(quadrantOf(0, toFixed(-1)) == 3);
    CHECK(quadrantOf(toFixed(-1), toFixed(1)) == 4);
    CHECK(quadrantOf(0, 0) == 4);

    // --- fixed point angle, RE: 0x5C22D0 (degrees scaled by 1e10, wrapped into [0, 360e10)) ---
    {
        CHECK(kFullTurnFixedDegrees == 3600000000000ll);
        // the recovered helper returns 0 for the degenerate direction
        CHECK(angleToFixedDegrees(0.0, 0.0) == 0);
        CHECK(angleToFixedDegrees(FPoint{0, 0}.x, FPoint{0, 0}.y) == 0);
        // the four cardinal directions land exactly on the recovered magic values
        CHECK(angleToFixedDegrees(1.0, 0.0) == 0);
        CHECK(angleToFixedDegrees(0.0, 1.0) == 900000000000ll);       //  90e10
        CHECK(angleToFixedDegrees(-1.0, 0.0) == 1800000000000ll);     // 180e10
        CHECK(angleToFixedDegrees(0.0, -1.0) == 2700000000000ll);     // 270e10
        // 45 degrees, and the wrap for a negative angle (-45 -> 315 degrees)
        CHECK_NEAR(static_cast<double>(angleToFixedDegrees(1.0, 1.0)), 450000000000.0, 1.0);
        CHECK_NEAR(static_cast<double>(angleToFixedDegrees(1.0, -1.0)), 3150000000000.0, 1.0);
        // every result stays inside the half open turn, and fixed point input agrees
        const double dirs[8][2] = {{1, 0},  {1, 1},   {0, 1},  {-1, 1},
                                   {-1, 0}, {-1, -1}, {0, -1}, {1, -1}};
        for (const auto& d : dirs) {
            const fixed_t v = angleToFixedDegrees(d[0], d[1]);
            CHECK(v >= 0);
            CHECK(v < kFullTurnFixedDegrees);
            CHECK(angleToFixedDegrees(toFixed(d[0]), toFixed(d[1])) == v);
        }
        // the 90/180/270 values are the ones the sin block in 0x1380D0 compares against
        CHECK(angleToFixedDegrees(0.0, 1.0) == 0xD18C2E2800ll);
        CHECK(angleToFixedDegrees(-1.0, 0.0) == 0x1A3185C5000ll);
        CHECK(angleToFixedDegrees(0.0, -1.0) == 0x274A48A7800ll);
    }

    return check::finish("test_exact");
}
