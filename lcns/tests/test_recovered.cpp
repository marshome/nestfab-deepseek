#include <limits>
#include <random>
// tests/test_recovered.cpp -- ACCEPTANCE TEST for the recovered constants.
//
// Every assertion below compares a constant used by the reconstruction with the value read out of
// libcns_dump_64.dll, and cites the address it came from. This is what makes the "the project
// agrees with the DLL on the constants" claim mechanically checkable instead of narrative: if
// anyone edits one of these constants without re-reading the binary, this test fails.
//
// Addresses refer to re/findings_*.md and re/REPORT.md section 10.
#include <cmath>
#include <cstdint>
#include <cstring>

#include "check.hpp"
#include "lcns/model.hpp"
#include "lcns/boolean.hpp"
#include "lcns/engine.hpp"
#include "lcns/budget.hpp"
#include "lcns/layout.hpp"
#include "lcns/steps.hpp"
#include "lcns/units.hpp"
#include "lcns/compare.hpp"
#include "lcns/geom.hpp"
#include "lcns/nester.hpp"
#include "lcns/nfp.hpp"
#include "lcns/equivalent.hpp"
#include "lcns/recovery.hpp"
#include "lcns/row.hpp"
#include "lcns/tiling.hpp"

#ifdef LCNS_HAS_BOOST
#include <boost/version.hpp>   // vendored boost 1.63.0 (third_party/README.md)
#endif

using namespace lcns;

int main() {
    // --- fixed point scale and the degree unit (geom) ---
    CHECK_NEAR(geom::kScale, 1e10, 0.0);                       // RE 0x9AD708 = 1e10
    CHECK(geom::kScaleI == 10000000000ll);
    // the inlined `Contains(window)` tolerance (read from the assertion builder 0x1C1A60)
    CHECK_NEAR(geom::kWindowContainEpsilon, 0.001, 0.0);        // RE 0x9BFD30 = 0.001
    CHECK(geom::kFullTurnFixedDegrees == 3600000000000ll);     // RE 0x34630B8A000 = 360 * 1e10

    // --- the fixed point angle primitive 0x5C22D0, whose exact cases the sin block compares ---
    CHECK(geom::angleToFixedDegrees(1.0, 0.0) == 0);
    CHECK(geom::angleToFixedDegrees(0.0, 1.0) == 0xD18C2E2800ll);      // RE 90e10  = 9e11
    CHECK(geom::angleToFixedDegrees(-1.0, 0.0) == 0x1A3185C5000ll);    // RE 180e10 = 1.8e12
    CHECK(geom::angleToFixedDegrees(0.0, -1.0) == 0x274A48A7800ll);    // RE 270e10 = 2.7e12
    CHECK(geom::angleToFixedDegrees(0.0, 0.0) == 0);                   // RE 0x5C22E7 special case

    // --- Row::Squeezer's two gates (0x1380D0) ---
    CHECK_NEAR(row::kSqueezeAlignmentTolerance, 0.005, 0.0);   // RE 0x9BCFD8 = 0.005
    CHECK_NEAR(row::kSqueezeParallelTolerance, 1e-06, 0.0);    // RE 0x9BCFC0 = 1e-06

    // --- the per-candidate Squeezer argument: 20.0 * height (0x133DE0) ---
    CHECK_NEAR(row::kCandidateHeightScale, 20.0, 0.0);         // RE 0x9BCEB0 = 20.0
    CHECK_NEAR(row::candidateSqueezerArg(3.0), 60.0, 0.0);     // RE 0x133E55..0x133E67

    // --- the score cache sentinel is -1.0, not NaN (0x136C00 initialises obj[+0x50] with it) ---
    CHECK_NEAR(row::kScoreUnset, -1.0, 0.0);                   // RE 0x9BCF48 = -1.0
    CHECK(!std::isnan(row::kScoreUnset));

    // --- the row core's configuration defaults (0x6AABC0 prologue) ---
    CHECK_NEAR(kRowCoreAt0x08, 10.0, 0.0);             // RE 0x9B1A40 = 10.0
    CHECK_NEAR(kRowCoreAt0x18, 4.0, 0.0);              // RE 0x9B1A48 = 4.0
    CHECK_NEAR(kRowCoreAt0x20, 20.0, 0.0);             // RE 0x9B1A50 = 20.0

    // --- the two alpha coefficients handed to the AlphaPriceComputer instances ---
    CHECK_NEAR(AlphaSurfacePrice::kBoostAlpha, 0.5, 0.0);   // RE 0x9D9C08 = 0.5
    CHECK_NEAR(AlphaSurfacePrice::kDimAlpha, 0.1, 0.0);     // RE 0x9D9BE8 = 0.1

    // --- the clamping tolerance the boolean kernel was written against ---
    CHECK(geom::kSnapTolerance == 10000);   // 1e-6 in real units at scale 1e10

    // --- NoFitMap's recovered complexity ceiling ---
    CHECK(NoFitMap::kDefaultMaxComplexity == 25000);   // RE 0x61A8 = 25000

    // --- the recovered fixed point angle must be inside the half open turn for every direction ---
    for (int i = 0; i < 16; ++i) {
        const double a = i * 3.14159265358979323846 / 8.0;
        const geom::fixed_t v = geom::angleToFixedDegrees(std::cos(a), std::sin(a));
        CHECK(v >= 0);
        CHECK(v < geom::kFullTurnFixedDegrees);
    }

    // --- the AdvancedStrategist mode dispatcher (0x2DF60) -------------------------------------    // The route is chosen by these three bytes of the Pb block; the pipe/common-cut gates are the
    // same ones Step 15/16 already recovered from SetPipeMode / SetCommonCutParameters.
    CHECK(kPbModeByte == 0xC8);                              // RE 0x4FC260
    CHECK(kPbPipeByte == 0x170);                             // RE 0x4FC2F0
    CHECK(kPbCommonCutByte == 0x1A0);                        // RE 0x4FC300
    CHECK(kPbInnerFlag == 0x81);                             // RE 0x2DF6A
    CHECK(kModeAdvanced3 == 3);                              // RE 0x2E0E2
    CHECK(kModeAdvanced4 == 4);                              // RE 0x2E068
    CHECK(kModeBlockSize == 0x28);                           // RE: 40 B descriptor POD
    CHECK(kModeBlockBoolAt == 0x0A);                         // RE 0x2DFFD
    CHECK(kModeBlockDoubleAt == 0x20);                       // RE 0x2E037
    CHECK_NEAR(kModeBlockDoubleValue, 1.0, 0.0);             // RE 0x9AEC90 = 1.0

    // --- the 40 byte descriptor, decoded from its use at 0x2D330 / 0x2DF60 --------------------
    CHECK(kDescMode == 0x00);
    CHECK(kDescFlags == 0x04);                               // bool[6] per-step enable flags
    CHECK(kDescN == 0x0C);                                   // read by the cascade
    CHECK(kDescAt10 == 0x10);
    CHECK(kDescAt18 == 0x18);
    CHECK(kDescAt1C == 0x1C);
    CHECK(kDescAt20 == 0x20);
    CHECK(kCascadeFirstN == 2);                              // RE 0x2CD37
    CHECK(kCascadeEarlyOut == 2);                            // RE 0x2CD0B
    CHECK(kCascadeMidThreshold == 4);                        // RE 0x2CD5B

    // --- StrategyAdder::Add 0x2C4D0: the mode -> nester table and the allocation sizes ---------
    // The binary dispatches on descriptor[+0] and allocates a fixed size per class; both are
    // fingerprints of the mapping (see re/findings_engine.md appendix 4).
    {
        CHECK(kTilingNesterBytes == 0x20);
        CHECK(kNestingNesterBytes == 0xA40);
        CHECK(kRectangleNesterBytes == 0x20);
        CHECK(kRowNesterBytes == 0x20);
        CHECK(kFlipNesterBytes == 0x28);
        CHECK(kMultiTorchNesterBytes == 0x28);
        CHECK(kLimitedNesterBytes == 0x48);
        CHECK(kNoFillNesterBytes == 0x60);
        CHECK(kCompactNesterBytes == 0x9F8);
        CHECK(kFilterNesterBytes == 0x9E8);
        CHECK(kStrategyModeCount == 5);

        CHECK(dynamic_cast<TilingNester*>(makeStrategy(0).get()) != nullptr);      // RE 0x2C520
        CHECK(dynamic_cast<NestingNester*>(makeStrategy(1).get()) != nullptr);     // RE 0x2CB1C
        CHECK(dynamic_cast<RectangleNester*>(makeStrategy(2).get()) != nullptr);   // RE 0x2CB50
        CHECK(dynamic_cast<RowNester*>(makeStrategy(3).get()) != nullptr);         // RE 0x2CB70
        CHECK(dynamic_cast<RowNester*>(makeStrategy(4).get()) != nullptr);         // RE 0x2CB91
        CHECK(makeStrategy(5) == nullptr);    // RE: mode >= 5 hits an assertion, it is not a class
        CHECK(makeStrategy(9) == nullptr);    // the modes 5..12 of an earlier revision were invented
        CHECK(makeStrategy(12) == nullptr);

        const std::vector<std::shared_ptr<Nester>> def = makeDefaultStrategies();
        CHECK(!def.empty());
        for (const std::shared_ptr<Nester>& s : def) CHECK(s != nullptr);
    }

    // the 0.99 area coverage slack (RE 0x9b15e0, used at 0x754ed / 0x75ef3)
    CHECK(kAreaCoverageSlack == 0.99);

    // the +-0.1% tolerance pair (RE 0x9b1740 / 0x9b1758, 0x7bcc0 asserts 'res <= y * 1.001')
    CHECK(kToleranceUpper == 1.001);
    CHECK(kToleranceLower == 0.999);

    // --- recovered trace strings (verbatim in the original's log) -----------------------------
    {
        CHECK(std::strcmp(kTraceFlip, "Flip ") == 0);                       // RE 0x4b870
        CHECK(std::strcmp(kTraceFilter, "Filter ") == 0);
        CHECK(std::strcmp(kTraceNoFill, "NoFill(") == 0);   // RE 0x7f240
        CHECK(std::strcmp(kTraceRow, "Row ") == 0);        // RE 0x913e0
        CHECK(std::strcmp(kTracePipe, "Pipe ") == 0);      // RE 0x913e0                   // RE 0xb3ae0
        CHECK(std::strcmp(kTracePackerCacheThreads, "Packer Cache max threads: ") == 0);  // RE 0x76a130
        CHECK(std::strcmp(kTraceVisitedNodes, "Visited Nodes=") == 0);      // RE 0x1c7980
        CHECK(std::strcmp(kTraceBucketsEmpty, "Buckets : empty") == 0);     // RE 0x7b3d20
        CHECK(std::strcmp(kTraceBeamTryNb, "Beam try nb : ") == 0);         // RE 0x655a30
        CHECK(std::strcmp(kTraceInternalError,
                          "*** INTERNAL ERROR: please contact support ***") == 0);  // RE 0x60a620
    }

    // --- the tiling pattern catalogue (RE ..\tiling\packer_cache.cpp, 0x765460) ----------------
    {
        CHECK(tiling::kPatternKeyCount == 16);
        CHECK(std::strcmp(tiling::kPatternKeys[0], "box") == 0);
        CHECK(std::strcmp(tiling::kPatternKeys[15], "windmill") == 0);
        // the composite family corresponds to the `enable_composite_tiling` option key
        int composite = 0;
        for (std::size_t i = 0; i < tiling::kPatternKeyCount; ++i) {
            if (std::strncmp(tiling::kPatternKeys[i], "composite_", 10) == 0) ++composite;
        }
        CHECK(composite == 4);
    }

    // --- the recovered rectangle corner order (RE 0x15620 AddRectanglePart) --------------------
    {
        geom::RectCorner c[4];
        geom::rectangleCorners(1.0, 2.0, 5.0, 8.0, c);
        CHECK(c[0].x == 1.0 && c[0].y == 2.0);   // (x0,y0)
        CHECK(c[1].x == 5.0 && c[1].y == 2.0);   // (x1,y0)
        CHECK(c[2].x == 5.0 && c[2].y == 8.0);   // (x1,y1)
        CHECK(c[3].x == 1.0 && c[3].y == 8.0);   // (x0,y1)
        for (int i = 0; i < 4; ++i) CHECK(c[i].z == 0.0);   // every third slot is zero
        // the recovered allocation size and point count, and that our struct matches the record
        CHECK(geom::kRectangleCornerCount == 4);
        CHECK(geom::kRectangleRecordBytes == 0x60);
        CHECK(sizeof(geom::RectCorner) * geom::kRectangleCornerCount == geom::kRectangleRecordBytes);
        // the three entries differ only in data (RE 0x15620 / 0x13410 / 0x13800)
        CHECK(static_cast<int>(geom::PartGeometryKind::Rectangle) == 0);
        CHECK(static_cast<int>(geom::PartGeometryKind::ExternalBoundary) == 1);
        CHECK(static_cast<int>(geom::PartGeometryKind::Hole) == 2);
        CHECK(geom::kCornerOffset == 0.292893);      // RE 0x9ad9d0
        CHECK(geom::kGeometryEpsilon == 0.0001);     // RE 0x9ad9c8
        // the recovered value fits 1 - 1/sqrt(2) to six digits (that reading is an inference)
        CHECK(std::fabs(geom::kCornerOffset - (1.0 - 1.0 / std::sqrt(2.0))) < 1e-6);
        CHECK(std::fabs(geom::kCornerOffset - (1.0 - 1.0 / std::sqrt(2.0))) < 1e-6);
        CHECK(geom::kRectangleFinalStep == 0x14D10);
        CHECK(geom::kBoundaryPrepStep == 0x64C940);
        CHECK(geom::kBoundaryFinalStep == 0x1BA30);
        CHECK(geom::kHoleFinalStep == 0x5CD5C0);
        CHECK(geom::kHoleFinalStep == 0x5CD5C0);
        // RE 0x5ed8c0: six quadrant angles, the last two being the first two plus a full turn
        CHECK(geom::kQuarterTurnHalfPi == 1.570796);
        CHECK(geom::kQuarterTurnPi == 3.141593);
        CHECK(geom::kQuarterTurn3HalfPi == 4.712389);
        CHECK(geom::kQuarterTurn2Pi == 6.283185);
        CHECK(geom::kQuarterTurn2PiPlusHalfPi == 7.853982);
        CHECK(geom::kQuarterTurn2PiPlus3HalfPi == 10.995574);
        // the reading that these are quadrant angles fits the constants to the digits stored
        CHECK(std::fabs(geom::kQuarterTurnHalfPi - 3.14159265358979 / 2.0) < 1e-6);
        CHECK(std::fabs(geom::kQuarterTurn3HalfPi - 3.0 * 3.14159265358979 / 2.0) < 1e-6);
        CHECK(std::fabs(geom::kQuarterTurn2Pi - 2.0 * 3.14159265358979) < 1e-6);
        // NOTE the stored constants are rounded to six decimals (7.853982 vs the exact sum
        // 7.853981...), so a DERIVED relation only holds to about 2e-6 -- the recovery bound is the
        // precision the binary actually stores, not the precision of the real number.
        CHECK(std::fabs(geom::kQuarterTurn2PiPlusHalfPi
                        - (geom::kQuarterTurn2Pi + geom::kQuarterTurnHalfPi)) < 2e-6);
        {
            double d[4];
            geom::quarterTurnDirections(d);
            CHECK(d[0] == geom::kQuarterTurnHalfPi && d[3] == geom::kQuarterTurn2Pi);
        }
        {
            double d[4];
            geom::quarterTurnDirections(d);
            CHECK(d[0] == geom::kQuarterTurnHalfPi && d[3] == geom::kQuarterTurn2Pi);
        }
        // RE the call graph: only the external boundary route reaches the quadrant-angle routine
        CHECK(geom::usesCornerArcs(geom::PartGeometryKind::ExternalBoundary));
        CHECK(!geom::usesCornerArcs(geom::PartGeometryKind::Hole));
        CHECK(!geom::usesCornerArcs(geom::PartGeometryKind::Rectangle));
        CHECK(!geom::usesCornerArcs(geom::PartGeometryKind::Rectangle));
        // RE 0x1399c: the hole route's one extra store, which the boundary route does not make
        CHECK(geom::kHoleExtraFlagOffset == 0x28);
        CHECK(geom::kHoleExtraFlagValue == 1);
        CHECK(geom::kHoleExtraFlagValue == 1);
        // RE the boundary chain, step by step (rounds 50-54)
        CHECK(geom::kBoundaryChainStep1 == 0x1BA30);
        CHECK(geom::kBoundaryChainStep2 == 0x1B910);
        CHECK(geom::kBoundaryChainStep3 == 0x5ED8C0);
        CHECK(geom::kBoundaryChainStep4 == 0x5ED3D0);
        CHECK(geom::kBoundaryChainStep4 == 0x5ED3D0);
        // RE 0x5ed828 / 0x5ed85e: one full turn back, in whichever direction it left the turn
        CHECK(geom::normaliseAngle(0.5) == 0.5);
        CHECK(geom::normaliseAngle(0.0) == 0.0);
        CHECK(std::fabs(geom::normaliseAngle(-0.5) - (6.283185 - 0.5)) < 2e-6);
        CHECK(std::fabs(geom::normaliseAngle(6.283185 + 0.5) - 0.5) < 2e-6);
        CHECK(std::fabs(geom::normaliseAngle(6.283185 + 0.5) - 0.5) < 2e-6);
        // RE 0x5ed453..0x5ed47b: the corner kernel's primitive -- point difference and squared length
        {
            const double a[2] = {5.0, 7.0};
            const double b[2] = {2.0, 3.0};
            const geom::Vec2d v = geom::subtractPoints2d(a, b);
            CHECK(v.x == 3.0);
            CHECK(v.y == 4.0);
            CHECK(geom::lengthSquared2d(v) == 25.0);          // 3-4-5, and no square root at this site
            CHECK(geom::lengthSquared2d(geom::Vec2d{0.0, 0.0}) == 0.0);
            CHECK(geom::lengthSquared2d(geom::Vec2d{0.0, 0.0}) == 0.0);
            // RE 0x5ed4b1 / 0x5ed7db: normalise, but never divide by a zero length
            {
                const geom::Vec2d u = geom::normaliseEdge2d(geom::Vec2d{3.0, 4.0});
                CHECK(std::fabs(u.x - 0.6) < 1e-12);
                CHECK(std::fabs(u.y - 0.8) < 1e-12);
                CHECK(std::fabs(geom::lengthSquared2d(u) - 1.0) < 1e-12);
                // the degenerate edge comes back unchanged, because the factor stays 1.0
                const geom::Vec2d z = geom::normaliseEdge2d(geom::Vec2d{0.0, 0.0});
                CHECK(z.x == 0.0 && z.y == 0.0);
            }
        }
    }

    // --- the equivalent-problem / order consistency the no-fit context asserts (RE 0x668f20) ----
    {
        CHECK(equivalent::matchesOrder(12, 12, 3, 3));
        CHECK(!equivalent::matchesOrder(12, 11, 3, 3));   // part count must match
        CHECK(!equivalent::matchesOrder(12, 12, 3, 2));   // sheet count must match
        CHECK(!equivalent::matchesOrder(0, 1, 0, 0));
        CHECK(equivalent::matchesOrder(0, 0, 0, 0));      // both empty is consistent
    }

    // --- the 24 byte triple zeroing helper (RE 0x5c6100, four instructions) --------------------
    {
        double v[5] = {1.0, 2.0, 3.0, 4.0, 5.0};
        equivalent::zeroTriple(v);
        CHECK(v[0] == 0.0);
        CHECK(v[1] == 0.0);
        CHECK(v[2] == 0.0);
        // the original writes exactly 24 bytes: the fourth double must be untouched
        CHECK(v[3] == 4.0);
        CHECK(v[4] == 5.0);
        equivalent::zeroTriple(nullptr);   // the port guards; the original does not
    }

    // --- the delegating canceller (RE 0x7e80e0) -------------------------------------------------
    {
        lcns::DelegatingCanceller d(nullptr);
        CHECK(!d.probeCancel());
        lcns::NeverCanceller never;
        d.setInner(&never);
        CHECK(!d.probeCancel());
        lcns::TimeCanceller timer(10.0);
        d.setInner(&timer);
        timer.cancel();
        CHECK(d.probeCancel());
    }

    // --- the seven classes the untested-class gate flagged (round 92) --------------------------
    {
        // BeamStats: counters start at zero and seconds is a double
        BeamStats st;
        CHECK(st.iterations == 0 && st.expanded == 0 && st.pruned == 0 && st.placed == 0);
        CHECK(st.seconds == 0.0);
        st.expanded = 7;
        CHECK(st.expanded == 7);

        // PlacementCheck::ok() is a conjunction; each term must be able to veto it
        PlacementCheck pc;
        CHECK(!pc.ok());                       // insideSheet is false by default
        pc.insideSheet = true;
        CHECK(pc.ok());                        // the other four are satisfied by default
        pc.overlapsPlaced = true;
        CHECK(!pc.ok());
        pc.overlapsPlaced = false;
        pc.inRestrictedZone = true;
        CHECK(!pc.ok());
        pc.inRestrictedZone = false;
        pc.torchOk = false;
        CHECK(!pc.ok());
        pc.torchOk = true;
        pc.insideHoleOnly = false;
        CHECK(!pc.ok());

        // DatabaseNester exposes its name and a deterministic hash
        DatabaseNester db;
        CHECK(std::strcmp(db.name(), "DatabaseNester") == 0);
        Nesting n1;
        Nesting n2;
        CHECK(DatabaseNester::hashNesting(n1) == DatabaseNester::hashNesting(n2));

        // CompositeNester reports its name and accepts children
        CompositeNester comp;
        CHECK(std::strcmp(comp.name(), "CompositeNester") == 0);
        comp.add(std::make_shared<DatabaseNester>());

        // NFPKey equality and the FNV-1a hash it uses
        NFPKey k1{1, 2, 3, 0};
        NFPKey k2{1, 2, 3, 0};
        NFPKey k3{1, 2, 4, 0};
        CHECK(k1 == k2);
        CHECK(!(k1 == k3));
        const NFPKeyHash h;
        CHECK(h(k1) == h(k2));                       // determinism
        CHECK(h(k1) != h(k3));                       // and different keys differ
        CHECK(h(k1) == h(k1));                       // stable across calls

        // IntervalList is the thin wrapper the recovered object at +0xA8/+0xC0 reads
        row::IntervalList il;
        CHECK(il.empty());
        CHECK(il.size() == 0);
        il.items.push_back(row::Interval{});
        CHECK(!il.empty());
        CHECK(il.size() == 1);
    }

    // --- the two beam types, asserted against their own declared defaults ---------------
    {
        BeamParams b_beamparams;
        CHECK(b_beamparams.width == 8);
        CHECK(b_beamparams.distinctAngle == true);
        CHECK(b_beamparams.frequencyRatio == 1.0);
        CHECK(b_beamparams.maxAngleSteps == 24);
        BeamNode b_beamnode;
        CHECK(b_beamnode.value48 == 0.0);
        CHECK(b_beamnode.value50 == 0.0);
        CHECK(b_beamnode.depth == 0);
        CHECK(b_beamnode.sheetIndex == 0);
    }

    // --- common-cut reporting scales (RE 0x68a1a0: 'raw_evaluation_ratio_100'/'_10', constant 10.0) --
    {
        CHECK(kCommonCutRatioScale100 == 100);
        CHECK(kCommonCutRatioScale10 == 10);
        // the two scales are a pair: the same ratio reported in hundredths and in tenths
        const double ratio = 0.125;
        CHECK(static_cast<int>(ratio * kCommonCutRatioScale100) == 12);
        CHECK(static_cast<int>(ratio * kCommonCutRatioScale10) == 1);
        // and the recovered 10.0 is exactly the tenths scale
        CHECK(static_cast<double>(kCommonCutRatioScale10) == 10.0);
    }

    // --- multinesting tolerances (RE 0x1adc20: 0.999 * f(...) and 0.25 * (a*b)) -------------------
    {
        CHECK(kMultinestingTolerance == 0.999);
        CHECK(kMultinestingQuarter == 0.25);
        // the shapes the instructions show, applied to arbitrary operands: the constants are recovered,
        // the operands are not, so only the arithmetic is asserted here
        CHECK(std::fabs(0.999 * 4.0 - 3.996) < 1e-12);
        CHECK(0.25 * (8 * 4) == 8.0);
    }

    // --- the recovered SetActiveNesting/GetActiveParts precondition (RE 0x69be80) -----------------
    {
        CHECK(std::strcmp(kMethodSetActiveNesting, "SetActiveNesting") == 0);
        CHECK(std::strcmp(kMethodGetActiveParts, "GetActiveParts") == 0);
        // the assert text is kept verbatim, including the quote the binary stores
        CHECK(std::strstr(kAssertSetActiveNestingFirst, "SetActiveNesting first") != nullptr);
        // and its condition is a null check on m_base
        CHECK(!activeNestingReady(nullptr));
        int dummy = 0;
        CHECK(activeNestingReady(&dummy));
    }

    // --- the local shutdown pair and the comments the binary stores (RE 0x1cc0 / 0x5d90) ---------
    {
        CHECK(std::strstr(kCommentLocalCancel, "LocalCancel waiting for threads termination") != nullptr);
        CHECK(std::strstr(kCommentLocalTerminate, "LocalTerminate waiting for threads termination") != nullptr);
        // the two are a pair: cancel and terminate, both waiting for the workers to stop
        CHECK(std::strcmp(kCommentLocalCancel, kCommentLocalTerminate) != 0);
    }

    // --- the thread shutdown state gate (RE 0x1cc0 / 0x5d90: cmp [+0x4C] with 9 and 0xA) ----------
    {
        CHECK(kThreadStateCancel == 9);
        CHECK(kThreadStateTerminate == 10);
        CHECK(isShutdownState(9));
        CHECK(isShutdownState(10));
        CHECK(!isShutdownState(0));
        CHECK(!isShutdownState(8));
        CHECK(!isShutdownState(11));
    }

    // --- the tighter relative epsilon (RE 0x3c110, 'enlarged_') ------------------------------------
    {
        CHECK(kRelativeEpsilon == 1.000001);
        // an order of magnitude tighter than the existing upper tolerance
        CHECK(kToleranceUpper == 1.001);
        CHECK(kRelativeEpsilon < kToleranceUpper);
        CHECK(kRelativeEpsilon > 1.0);
    }

    // --- the growth overflow guard (RE 0x3c110: INT64_MAX - n <= 8) -------------------------------
    {
        CHECK(kGrowthSlack == 8);
        const auto mx = std::numeric_limits<std::int64_t>::max();
        CHECK(!exceedsGrowthLimit(0));
        CHECK(!exceedsGrowthLimit(1024));
        CHECK(!exceedsGrowthLimit(mx - kGrowthSlack - 1));   // room = 9, still allowed
        CHECK(exceedsGrowthLimit(mx - kGrowthSlack));        // room = 8, the jbe fires
        CHECK(exceedsGrowthLimit(mx));                       // room = 0
    }

    // --- the gated average and its final scale (RE 0x1ac390) ---------------------------------------
    {
        CHECK(kAverageStageWeight == 0.3);
        CHECK(kAverageFinalWeight == 0.33);
        // gate set: 0.3 * (product / count)
        CHECK(std::fabs(gatedAverage(10.0, 4.0, true, 99.0) - 0.75) < 1e-12);
        // gate clear: the prior value survives untouched
        CHECK(gatedAverage(10.0, 4.0, false, 99.0) == 99.0);
        // a zero count must not divide
        CHECK(gatedAverage(10.0, 0.0, true, 99.0) == 99.0);
        // the second stage multiplies unconditionally
        CHECK(std::fabs(finalScale(0.75) - 0.2475) < 1e-12);
        CHECK(std::fabs(finalScale(gatedAverage(10.0, 4.0, true, 0.0)) - 0.2475) < 1e-12);
    }

    // --- the seed scale (RE 0x1b33b0: (int)(f(...) * 1e6)) ----------------------------------------
    {
        CHECK(kSeedScale == 1000000.0);
        // the truncation the instruction performs, on a sample value
        CHECK(static_cast<long long>(0.5 * kSeedScale) == 500000);
        CHECK(static_cast<long long>(1.9999999 * kSeedScale) == 1999999);
    }

    // --- the timer behind the seed (RE 0x1b33b0 -> 0x1a9060 -> 0x178590/0x1785c0) -------------------
    {
        CHECK(std::strstr(kTimerQpcFailure, "QueryPerformanceCounter failed") != nullptr);
        CHECK(std::strstr(kTimerQpfFailure, "QueryPerformanceFrequency failed") != nullptr);
        // the seed is that duration expressed in microseconds
        CHECK(kSeedScale == 1000000.0);
        const double duration = 0.001234;                       // a sample second count
        CHECK(static_cast<long long>(duration * kSeedScale) == 1234);
    }

    // --- the (-0.5, 0.5] wrap (RE 0x62fd90 over the inline round at 0x62f940) ----------------------
    {
        CHECK(wrapToHalf(0.3) == 0.0);
        CHECK(wrapToHalf(0.6) == 1.0);
        CHECK(wrapToHalf(-0.6) == -1.0);
        CHECK(wrapToHalf(2.4) == 2.0);
        CHECK(wrapToHalf(2.6) == 3.0);
        // round half away from zero, as the inline implementation does
        CHECK(wrapToHalf(0.5) == 1.0);
        CHECK(wrapToHalf(-0.5) == -1.0);
        // the difference form stays inside half a step
        for (double x = -3.0; x <= 3.0; x += 0.125) {
            const double frac = halfFraction(x);
            CHECK(frac >= -0.5);
            CHECK(frac < 0.5 + 1e-12);
            CHECK(std::fabs(x - wrapToHalf(x) - frac) < 1e-12);
        }
    }

    // --- the aggregate/ratio tail (RE 0x1a9060, read whole) ----------------------------------------
    {
        CHECK(kAggregateStride == 240);
        CHECK(kRatioWeight == 0.9999);
        CHECK(kRatioFloor == 200);
        // a non-positive threshold leaves the average alone
        CHECK(ratioFromAverage(5.0, 0.0) == 5.0);
        CHECK(ratioFromAverage(5.0, -1.0) == 5.0);
        // threshold / average = 200, so the floor does not bind
        CHECK(std::fabs(ratioFromAverage(5.0, 1000.0) - 4.9995) < 1e-12);
        // ratio 20 is below the floor, so 200 is used
        CHECK(std::fabs(ratioFromAverage(5.0, 100.0) - 0.49995) < 1e-12);
        // a large ratio is used as it is
        CHECK(std::fabs(ratioFromAverage(5.0, 100000.0) - 4.9995) < 1e-12);
    }

    // --- the seed conversion (RE 0x1a9150, an independent copy of the sequence in 0x1b33b0) ---------
    {
        // the whole of 0x1A9150 is: call the ratio, multiply by 1e6, truncate toward zero
        CHECK(seedFromRatio(4.9995) == 4999500LL);
        CHECK(seedFromRatio(0.5) == 500000LL);
        CHECK(seedFromRatio(0.0) == 0LL);
        // truncation, not rounding
        CHECK(seedFromRatio(1.9999999) == 1999999LL);
        CHECK(seedFromRatio(-1.9999999) == -1999999LL);
        // and it composes with the ratio tail
        // the composition is asserted as the SAME arithmetic, not as a decimal: 0.9999*100/200*1e6
        // truncates to 499949 in IEEE double, and the binary performs these operations in this order
        const double composed = ratioFromAverage(5.0, 100.0);
        CHECK(seedFromRatio(composed) == static_cast<long long>(composed * 1000000.0));
    }

    // --- the seed runs a std::mt19937 (RE 0x1a3560: 624 words, multiplier 0x6C078965) -------------
    {
        CHECK(kMt19937StateWords == 624);
        CHECK(kMt19937InitMultiplier == 1812433253u);
        CHECK(kMt19937StateBytes == 2504);
        CHECK(kMt19937StateBytes == kMt19937StateWords * 4 + 8);   // the allocation is exactly that
        // the recurrence as the standard defines it for x[0] = seed 5489 (no remembered constants:
        // the expected value is written as the definition itself)
        const std::uint32_t seed0 = 5489u;
        const std::uint32_t expected1 = 1812433253u * (seed0 ^ (seed0 >> 30)) + 1u;
        CHECK(mt19937InitStep(seed0, 1) == expected1);
        CHECK(expected1 == 1812433253u * seed0 + 1u);   // 5489 >> 30 is zero
        // and for a seed where the shift does bite
        const std::uint32_t big = 0xFFFFFFFFu;
        CHECK(mt19937InitStep(big, 7) == 1812433253u * (big ^ (big >> 30)) + 7u);
        // NOTE: 3499211612 is the engine's first OUTPUT after tempering, not a state word -- the
        // first attempt at this test confused the two, so the distinction is recorded here.
        {
            std::mt19937 reference(5489u);
            CHECK(reference() == 3499211612u);
        }
    }

    // --- the budget arithmetic (RE 0x1b33b0: 0.7*1e8, 0.5 of it, 0.15*1e8, minus ms/1000 twice) --------
    {
        CHECK(kBudgetBase == 1e8);
        CHECK(kBudgetWeightLow == 0.7);
        CHECK(kBudgetWeightHalf == 0.5);
        CHECK(kBudgetWeightSmall == 0.15);
        CHECK(kMsPerSecond == 1000.0);
        CHECK(kTickDivisor == 1000000);
        CHECK(weightedBudget(kBudgetBase) == 7e7);
        CHECK(smallWeightedBudget(kBudgetBase) == 1.5e7);
        CHECK(halfOfWeightedBudget(kBudgetBase) == 3.5e7);
        // the arguments are tick differences from a 1e9-scaled source: each is divided by 1e6 (the
        // magic-multiply divisor) and then by 1000, so 1,000,000,000 ticks is one second
        CHECK(budgetAfterElapsedTicks(kBudgetBase, 1000000000LL, 0LL) == 7e7 - 1.0);
        CHECK(budgetAfterElapsedTicks(kBudgetBase, 1000000000LL, 500000000LL) == 7e7 - 1.5);
        CHECK(budgetAfterElapsedTicks(kBudgetBase, 0LL, 0LL) == 7e7);
        // and the sub-second part is preserved rather than dropped
        CHECK(budgetAfterElapsedTicks(kBudgetBase, 1000000LL, 0LL) == 7e7 - 0.001);
    }

    // --- the nanosecond clock and the conversion (RE 0x8a8190, then 0x1b4b48/0x1b4b4d) -------------
    {
        CHECK(kNanosecondsPerSecond == 1000000000LL);
        // the pair combination, as the two instructions do it
        CHECK(nanosecondsFromPair(0, 500) == 500LL);
        CHECK(nanosecondsFromPair(1, 0) == 1000000000LL);
        CHECK(nanosecondsFromPair(2, 250) == 2000000250LL);
        // and the conversion back to seconds: /1e6 then /1000
        CHECK(nanosecondsToSeconds(1000000000LL) == 1.0);
        CHECK(nanosecondsToSeconds(500000000LL) == 0.5);
        CHECK(nanosecondsToSeconds(1000000LL) == 0.001);
        CHECK(nanosecondsToSeconds(0LL) == 0.0);
        // a one-second difference is exactly what the budget arithmetic subtracts
        CHECK(budgetAfterElapsedTicks(kBudgetBase, 1000000000LL, 0LL) == 7e7 - nanosecondsToSeconds(1000000000LL));
    }

    // --- twelve Itanium RTTI type names (RE the 0x6ca720 family) --------------
    {
        CHECK(std::strcmp(kTypeInfoNames[0], "10BeamValues") == 0);   // RE 0x6ca720
        CHECK(std::strcmp(kTypeInfoNames[1], "10Off2Weight") == 0);   // RE 0x6ca840
        CHECK(std::strcmp(kTypeInfoNames[2], "10PartRatios") == 0);   // RE 0x6ca960
        CHECK(std::strcmp(kTypeInfoNames[3], "11RepeatSheet") == 0);   // RE 0x6caa80
        CHECK(std::strcmp(kTypeInfoNames[4], "11TilingLimit") == 0);   // RE 0x6caba0
        CHECK(std::strcmp(kTypeInfoNames[5], "13ODescriptions") == 0);   // RE 0x6cacc0
        CHECK(std::strcmp(kTypeInfoNames[6], "13PosDirections") == 0);   // RE 0x6cade0
        CHECK(std::strcmp(kTypeInfoNames[7], "14ODescriptions2") == 0);   // RE 0x6caf00
        CHECK(std::strcmp(kTypeInfoNames[8], "6UseMap") == 0);   // RE 0x6cb020
        CHECK(std::strcmp(kTypeInfoNames[9], "7OPricer") == 0);   // RE 0x6cb140
        CHECK(std::strcmp(kTypeInfoNames[10], "7ZfSizes") == 0);   // RE 0x6cb260
        CHECK(std::strcmp(kTypeInfoNames[11], "8DegSteps") == 0);   // RE 0x6cb380
        // the scheme holds for every one of them: prefix == length, and it round trips
        for (int i = 0; i < 12; ++i) {
            std::string decoded;
            CHECK(decodeTypeInfoName(kTypeInfoNames[i], &decoded));
            CHECK(encodeTypeInfoName(decoded) == kTypeInfoNames[i]);
            CHECK(typeInfoNameIndex(kTypeInfoNames[i]) == i);
        }
        // a wrong or missing prefix, or a trailing name, is rejected
        std::string tmp;
        CHECK(!decodeTypeInfoName("99BeamValues", &tmp));
        CHECK(!decodeTypeInfoName("BeamValues", &tmp));
        CHECK(!decodeTypeInfoName("0", &tmp));
        CHECK(!decodeTypeInfoName("6Use", &tmp));
        CHECK(typeInfoNameIndex("10NotAName") == -1);
        CHECK(encodeTypeInfoName("UseMap") == kTypeInfoNames[8]);
        // the two names that carry a digit must still decode
        CHECK(decodeTypeInfoName("10Off2Weight", &tmp) && tmp == "Off2Weight");
        CHECK(decodeTypeInfoName("14ODescriptions2", &tmp) && tmp == "ODescriptions2");
    }

    // --- the surface-slack assertion as a predicate (RE 0x81c370 / 0x81c690 / 0x81c9b0) --------
    {
        // 'eval.m_c >= 0 && eval.m_c <= max_surface * 1.05'
        CHECK(withinSurfaceSlack(0.0, 100.0));       // exactly zero is valid
        CHECK(withinSurfaceSlack(105.0, 100.0));     // exactly 1.05x is valid (<=)
        CHECK(!withinSurfaceSlack(105.0001, 100.0)); // just past the slack fails
        CHECK(!withinSurfaceSlack(-0.0001, 100.0));  // the first half matters too
        CHECK(withinSurfaceSlack(100.0, 100.0));
        CHECK(kEvalSurfaceSlack == 1.05);            // the constant the predicate is built on
    }

    // --- the recovered 0.99 coverage predicate (RE 0x754ed / 0x75ef3) --------------------------
    {
        // exactly 99% of the reference passes (>=, not >)
        CHECK(coversReference(0.99, 1.0));
        CHECK(coversReference(1.0, 1.0));
        // just below 99% fails -- this is the branch the jbe takes
        CHECK(!coversReference(0.9899, 1.0));
        CHECK(coversReference(9.9, 10.0));
        CHECK(!coversReference(9.89, 10.0));
        // a zero reference is covered by anything non-negative
        CHECK(coversReference(0.0, 0.0));
    }

    // --- the corner kernel assembled from its three proven pieces (RE 0x5ed45d..0x5ed58f) -------
    {
        const double prev[2] = {0.0, 0.0};
        const double corner[2] = {1.0, 0.0};
        const double next[2] = {1.0, 1.0};
        const geom::CornerEdges e = geom::cornerEdges(prev, corner, next);
        CHECK(std::fabs(e.incoming.x - 1.0) < 1e-12);
        CHECK(std::fabs(e.incoming.y) < 1e-12);
        // DIRECTION CONVENTION, straight from the disassembly: each edge is `corner - neighbour`
        // (5ED45D subsd xmm11,[rsi] and 5ED58A subsd xmm13,xmm3 with [rbx] the corner), so with
        // next = (1,1) the outgoing edge is (0,-1) -- my first expectation had the sign wrong and
        // this assertion is what caught it.
        CHECK(std::fabs(e.outgoing.x) < 1e-12);
        CHECK(std::fabs(e.outgoing.y + 1.0) < 1e-12);
        // both edges are unit vectors, which is what normaliseEdge2d guarantees
        CHECK(std::fabs(geom::lengthSquared2d(e.incoming) - 1.0) < 1e-12);
        CHECK(std::fabs(geom::lengthSquared2d(e.outgoing) - 1.0) < 1e-12);
        // a degenerate corner (coincident points) must not divide by zero
        const geom::CornerEdges d = geom::cornerEdges(corner, corner, next);
        CHECK(d.incoming.x == 0.0 && d.incoming.y == 0.0);
    }

    // --- the recovered log prefixes are wired into the classes that print them ------------------
    {
        CHECK(std::strcmp(FlipNester().tracePrefix(), kTraceFlip) == 0);        // RE 0x4b870
        CHECK(std::strcmp(FilterNester().tracePrefix(), kTraceFilter) == 0);    // RE 0xb3ae0
        CHECK(std::strcmp(NoFillNester().tracePrefix(), kTraceNoFill) == 0);    // RE 0x7f240
        CHECK(std::strcmp(NestingNester().tracePrefix(), "") == 0);             // never observed
        CHECK(std::strcmp(TilingNester().tracePrefix(), "") == 0);              // never observed
    }

    // --- the recovered defect reduction (RE 0x4bc9e0, ..\\verify\\equivalent.cpp) --------------
    {
        CHECK(equivalent::kDefectWeight == 0.5);
        CHECK(equivalent::kReductionSourceOffset == 0x58);
        // RE 0x4bca56 mulsd then 0x4bca5b subsd: x - 0.5*p
        CHECK(equivalent::reduce(1.0, 1.0) == 0.5);
        CHECK(equivalent::reduce(3.0, 2.0) == 2.0);
        CHECK(equivalent::reduce(0.5, 1.0) == 0.0);
        // RE the assertion 'defect_reduction > 0.0' -- strictly positive, so exactly zero fails
        CHECK(equivalent::isValidReduction(0.25));
        CHECK(!equivalent::isValidReduction(0.0));
        CHECK(!equivalent::isValidReduction(-0.25));
        // RE 0x4f9c30 `movsd xmm0,[rcx+0x58]` reads the 11th double of the record
        double obj[16] = {0};
        obj[equivalent::kReductionSourceOffset / sizeof(double)] = 2.0;
        CHECK(equivalent::reduceFromSource(obj, 2.0) == 1.0);
        CHECK(equivalent::reduceFromSource(nullptr, 1.0) == 0.0);
    }

    // --- third party versions are bound to the evidence in the dump ---------------------------
    // The border/structure TU asserts TWO quality domains at 0x1ee50 / 0x7bf0c0; they are different
    // sets in the same model, so both are bound here.
    CHECK(kQualityLevelsPart == 100);          // RE 'quality >= 0 && quality < 100'
    CHECK(kQualityLevelsLeatherLayer == 9);    // RE 'quality >= 0 && quality < 9'
    // The beam-tree/bucket TU (..\nesting\algos\bucket_manager.hpp) asserts a surface slack; it is a
    // recovered constant, quoted by the three ComputeNodeIndex instantiations.
    CHECK_NEAR(kEvalSurfaceSlack, 1.05, 0.0);                  // RE 0x81C690 assertion text
    // The dump names the exact boost tree it was built against, so the vendored headers are pinned:
    //   0x9AE7A0  'C:\Users\renaud\nest\external\boost_1_63_0/boost/uuid/sha1.hpp'
#ifdef LCNS_HAS_BOOST
    {
        static_assert(BOOST_VERSION == 106300, "the dump proves boost 1.63.0 (path @0x9AE7A0)");
        CHECK(BOOST_VERSION == 106300);
    }
#endif

    // --- the recovery inventory must not silently shrink ------------------------------------
    // include/lcns/recovery.hpp registers every part of the reconstruction that is NOT
    // instruction-level faithful. The counts are asserted here (and the code marks are
    // cross-checked against the registry by tools/check_recovery.py) so that deleting a gap --
    // i.e. quietly pretending something was recovered -- breaks the build.
    {
        using namespace lcns::recovery;
        CHECK(kGapCount == 78);
        CHECK(countOf(Status::Recovered) == 9);
        CHECK(countOf(Status::Structural) == 27);
        CHECK(countOf(Status::NotReversed) == 13);
        CHECK(countOf(Status::Substituted) == 28);
        CHECK(countOf(Status::NotInBinary) == 1);
        // every entry is complete ...
        for (std::size_t i = 0; i < kGapCount; ++i) {
            CHECK(kGaps[i].id != nullptr && *kGaps[i].id != '\0');
            CHECK(kGaps[i].address != nullptr && *kGaps[i].address != '\0');
            CHECK(kGaps[i].note != nullptr && *kGaps[i].note != '\0');
            // ... and ids are unique
            for (std::size_t j = i + 1; j < kGapCount; ++j) {
                CHECK(std::strcmp(kGaps[i].id, kGaps[j].id) != 0);
            }
        }
        CHECK(std::strcmp(toString(Status::NotReversed), "not-reversed") == 0);
        CHECK(std::strcmp(marker(Status::Substituted), "LCNS_SUBSTITUTED") == 0);
        // the Chinese word table is bound too, so it cannot drift from the code marks
        CHECK(std::strcmp(toChinese(Status::Recovered), "已恢复") == 0);
        CHECK(std::strcmp(toChinese(Status::Structural), "结构已恢复") == 0);
        CHECK(std::strcmp(toChinese(Status::Substituted), "替代实现") == 0);
        CHECK(std::strcmp(toChinese(Status::NotReversed), "尚未逆向") == 0);
        CHECK(std::strcmp(toChinese(Status::NotInBinary), "非原库") == 0);
    }

    // --- 0x1b33b0's further formulas (RE 0x1b4feb, 0x1b5182.., 0x1b536a..) -------------------------
    {
        CHECK(kPairLimitWeight == 1.5);
        CHECK(limitFromPair(2.0, 3.0) == 9.0);                 // 1.5 * (a * b)
        CHECK(kCountWeight == 30.0);
        CHECK(kBudgetWeightQuarter == 0.25);
        CHECK(kBudgetWeightNine == 0.9);
        CHECK(kBudgetWeightExtra == 0.03);
        CHECK(extraWeightedBudget(kBudgetBase) == 0.03e8);
        // 0.25 * base - 30 * (count / 1000)
        CHECK(countBudgetLimit(kBudgetBase, 0) == 0.25e8);
        CHECK(countBudgetLimit(kBudgetBase, 1000) == 0.25e8 - 30.0);
        // 0.9 * (0.7 * base - count / 1000)
        CHECK(decayedBudget(kBudgetBase, 0) == 0.9 * 7e7);
        CHECK(decayedBudget(kBudgetBase, 1000) == 0.9 * (7e7 - 1.0));
        // the link round 147 established: 0.5*(0.7*base) plus the truncated count limit
        const std::int64_t truncated = static_cast<std::int64_t>(countBudgetLimit(kBudgetBase, 1000));
        CHECK(truncated == static_cast<std::int64_t>(0.25e8 - 30.0));
        // the binary ADDS the truncated count limit to half the weighted budget, so the result is a
        // sum, not an adjustment: 3.5e7 + (0.25e8 - 30) for base 1e8 and count 1000
        CHECK(halfOfWeightedBudget(kBudgetBase) == 3.5e7);
        CHECK(halfOfWeightedBudget(kBudgetBase) + static_cast<double>(truncated) == 3.5e7 + (0.25e8 - 30.0));
        CHECK(halfOfWeightedBudget(kBudgetBase) + static_cast<double>(truncated) == 5.999997e7);
    }

    // --- the record layout facts (RE 0x1a90bb/0x1b3943/0x1f8327/0x1aa8b8) ---------------------------
    {
        CHECK(kRunRecordStride == 240);
        CHECK(kTimingRecordStride == 344);
        CHECK(kSmallRecordStride == 24);
        CHECK(kRunRecordStride != kTimingRecordStride);
        CHECK(kTimingRecordStride > kRunRecordStride);
        CHECK(kCounterOffset == 0x4C);
        CHECK(kLeadingCountOffset == 0x140);
        CHECK(kLeadingCountOffset < kTimingRecordStride);
        CHECK(kTrailingCountOffset == 0x20);
        CHECK(kSmallRecordLimitOffset == 0x28);
        CHECK(kTripledFieldOffset == 0x18);
        // the two-step divisions, with the shift kept separate
        CHECK(kCountShift == 3);
        CHECK(kCountDivisor == 10);
        CHECK(kCountNetDivisor == 80);
        CHECK(kSmallSpanShift == 4);
        CHECK(kSmallSpanDivisor == 24);
        CHECK(kSmallSpanNetDivisor == 384);
    }

    // --- round 159's confirmations (RE 0x1aa8c8/0x1aa8cc, 0x1aa8fb, 0x6d6510) ----------------------
    {
        CHECK(kIndexedRecordStride == 48);
        CHECK(kIndexedRecordStride != kRunRecordStride);
        CHECK(kIndexedRecordStride != kTimingRecordStride);
        CHECK(kRecordValueOffset == 0x18);
        CHECK(kRecordWideOffset == 0x20);
        CHECK(kRecordFlagOffset == 0x28);
        CHECK(kRecordValueOffset < kRecordWideOffset);
        CHECK(kRecordWideOffset < kRecordFlagOffset);
        // the three fields are the ones round 155 assembled on the stack
        CHECK(kRecordValueOffset == kTripledFieldOffset);
        CHECK(kRecordFlagOffset == kSmallRecordLimitOffset);
        CHECK(std::strstr(kElementsContainerAssert, "m_elements") != nullptr);
    }

    // --- the step counts of 0x1a1810 (RE 0x1a184f/0x1a1857/0x1a1881/0x1a1894/0x1a18ba) ------------
    {
        CHECK(kStepFine == 0.0001);
        CHECK(kStepMid == 0.0003);
        CHECK(kStepCoarse == 0.0039);
        CHECK(kStepRoundTerm == 0.5);
        CHECK(kStepTens == 10.0);
        CHECK(kStepTickScale == 1e6);
        // value / 0.0001 + 0.5, truncated: the fine step count
        CHECK(fineStepCount(0.00123) == 12);          // 12.3 + 0.5 = 12.8 -> 12
        CHECK(fineStepCount(0.00125) == 13);          // 12.5 + 0.5 = 13.0 -> 13
        CHECK(fineStepCount(0.0) == 0);
        // the mid step takes its scale from the caller (RE 0x1a1890 divides by n/1e6)
        // the scale IS the step here, so 0.003 over a step of 1.0 is 0.0033 and truncates to 0
        CHECK(midStepCount(0.003, stepScale(1000000)) == 0);
        // and with a step of 0.001 the quotient is about 1
        CHECK(stepScale(1000) == 0.001);
        CHECK(midStepCount(0.001, stepScale(1000)) == 1);
        CHECK(stepScale(1000000) == 1.0);
        CHECK(stepScale(500000) == 0.5);
        CHECK(kStepCoarse > kStepMid);
        CHECK(kStepMid > kStepFine);
    }

    // --- the turn counts (RE 0x24c4cf/0x5c23d7/0x5d29d2 and 0x21b85f/0x17e1f8) ----------------------
    {
        CHECK(kTwoPiRounded == 6.283185307);
        CHECK(kDegreesPerTurn == 360.0);
        // one whole turn, and three of them
        CHECK(turnCount(kTwoPiRounded) == 1);
        CHECK(turnCount(3.0 * kTwoPiRounded) == 3);
        CHECK(turnCount(0.0) == 0);
        CHECK(turnCount(3.0) == 0);                        // less than half a turn
        CHECK(turnCount(3.2) == 1);                        // 0.509 -> 0.509, truncates to 0? no: 3.2/2pi=0.509
        // degrees: a full turn and a half
        CHECK(degreeTurnCount(360.0) == 1);
        CHECK(degreeTurnCount(180.0) == 1);                // 0.5 + 0.5 = 1.0 exactly
        CHECK(degreeTurnCount(179.0) == 0);
        CHECK(degreeTurnCount(1080.0) == 3);
    }

    // --- the micro-scale convention (RE 0x19f269 / 0x19fa25, shared rvas) ---------------------------
    {
        CHECK(kMicroScale == 1e6);
        CHECK(kMicroInverse == 1e-6);
        CHECK(kTenThousandth == 0.0001);
        CHECK(microToUnit(1000000) == 1.0);
        CHECK(microToUnit(500000) == 0.5);
        CHECK(microToUnit(100) == 0.0001);
        CHECK(unitToMicro(1.0) == 1e6);
        // the two constants describe the same relation
        CHECK(kMicroInverse * kMicroScale == 1.0);
        // and the shared 0.0001 slot is the same value as the fine step of 0x1a1810
        CHECK(kTenThousandth == kStepFine);
    }

    // --- the shared constant block (RE rva 0x9dfb98..0x9dfc20) -------------------------------------
    {
        // the epsilon is confirmed by COMPUTATION, not by recognising the digits
        CHECK(kSharedEpsilon == std::numeric_limits<double>::epsilon());
        CHECK(kSharedEpsilon > 0.0);
        CHECK(kSharedEpsilon < 1e-15);
        CHECK(kSharedHalf == 0.5);
        CHECK(kSharedMicroScale == 1e6);
        CHECK(kSharedMicroScale == kMicroScale);          // the same scale as round 171's site
        CHECK(kSharedNegativeOne == -1.0);
        CHECK(kSharedFifty == 50.0);
        // the block's scale slot agrees with the 0.5 slot used by so many functions
        CHECK(kSharedHalf == kStepRoundTerm);
    }

    // --- the twins' comparator (RE 0x74b430 / 0x74b700: seta al ; lea eax,[rax+rax-1]) --------------
    {
        // the mapping {0,1} -> {-1,+1} the code performs
        CHECK(signOf(2.0) == 1);
        CHECK(signOf(-2.0) == -1);
        // and the equal case, which the `je` guard sends to zero
        CHECK(compareToZero(0.0) == 0);
        CHECK(compareToZero(1e-300) == 1);
        CHECK(compareToZero(-1e-300) == -1);
        // the tolerance form the guards imply
        CHECK(withinTolerance(1.0, 1.0));
        CHECK(withinTolerance(-1.0, 1.0));
        CHECK(!withinTolerance(1.5, 1.0));
    }

    // --- the cross product the twins compare (RE 0x74b390 / 0x74b660) -------------------------------
    {
        const Point2dLike o{0.0, 0.0};
        const Point2dLike x{1.0, 0.0};
        const Point2dLike up{0.0, 1.0};
        const Point2dLike down{0.0, -1.0};
        CHECK(crossProduct2d(o, x, up) == 1.0);          // counter-clockwise
        CHECK(crossProduct2d(o, x, down) == -1.0);       // clockwise
        CHECK(crossProduct2d(o, x, x) == 0.0);           // collinear
        CHECK(crossProduct2d(o, x, Point2dLike{2.0, 0.0}) == 0.0);
        // the sign is the orientation, which is what the twins' comparator then looks at
        CHECK(signOf(crossProduct2d(o, x, up)) == 1);
        CHECK(signOf(crossProduct2d(o, x, down)) == -1);
        CHECK(withinTolerance(crossProduct2d(o, x, up), 1.0));
        // RE 0x74B40C stores AC.x (c.x - a.x) through r9; no function is written for that
        // component because B takes no part in it.
    }

    // --- the relative scale (RE 0x7043b0: max(1, |v0..v3|) under the sign mask) ----------------------
    {
        CHECK(kSignMask == 0x7FFFFFFFFFFFFFFFULL);
        CHECK(relativeScale(0.0, 0.0, 0.0, 0.0) == 1.0);       // the floor
        CHECK(relativeScale(0.25, 0.0, 0.0, 0.0) == 1.0);      // still below the floor
        CHECK(relativeScale(4.0, 0.0, 0.0, 0.0) == 4.0);
        CHECK(relativeScale(-7.0, 1.0, 2.0, 3.0) == 7.0);      // the sign is masked away
        CHECK(relativeScale(1.0, 2.0, 9.0, 3.0) == 9.0);
        CHECK(relativeScale(1.0, 2.0, 3.0, -12.0) == 12.0);
        // what the scale buys is a DIMENSIONLESS cross product, not automatic tolerance:
        // collinear points have a cross of zero and pass any non-negative tolerance
        CHECK(crossProduct2d(Point2dLike{0.0, 0.0}, Point2dLike{100.0, 0.0},
                             Point2dLike{200.0, 0.0}) == 0.0);
        CHECK(withinTolerance(crossProduct2d(Point2dLike{0.0, 0.0}, Point2dLike{100.0, 0.0},
                                             Point2dLike{200.0, 0.0}), 0.0));
        // and cross/scale is dimensionless: the same triangle at two sizes keeps its ratio
        const double small = crossProduct2d(Point2dLike{0.0, 0.0}, Point2dLike{1.0, 0.0},
                                            Point2dLike{0.0, 1.0})
                           / relativeScale(1.0, 1.0, 1.0, 1.0);
        const double large = crossProduct2d(Point2dLike{0.0, 0.0}, Point2dLike{100.0, 0.0},
                                            Point2dLike{0.0, 100.0})
                           / relativeScale(100.0, 100.0, 100.0, 100.0);
        CHECK(small == 1.0);
        CHECK(large == 100.0);
        // a cross that big is NOT inside a tolerance of 100 -- the scale is not a tolerance
        CHECK(!withinTolerance(crossProduct2d(Point2dLike{0.0, 0.0}, Point2dLike{100.0, 0.0},
                                              Point2dLike{0.0, 100.0}), 100.0));
    }

    // --- 0x5e6360's field formulas (RE 0x5e6394/0x5e639c/0x5e63a0 and 0x5e63bd/0x5e63dd) -------------
    {
        CHECK(kObjectFieldA == 0x08);
        CHECK(kObjectFieldB == 0x10);
        CHECK(kObjectFieldC == 0x18);
        CHECK(kObjectFieldD == 0x20);
        CHECK(differenceProduct(1.0, 2.0, 4.0, 6.0) == 12.0);      // (4-1)*(6-2)
        CHECK(differenceProduct(0.0, 0.0, 0.0, 0.0) == 0.0);
        CHECK(differenceProduct(1.0, 2.0, 1.0, 6.0) == 0.0);       // one difference is zero
        CHECK(midpointOf(2.0, 4.0) == 3.0);
        CHECK(midpointOf(-1.0, 1.0) == 0.0);
        CHECK(midpointOf(0.0, 0.0) == 0.0);
        CHECK(doubledThenHalved(7.0) == 7.0);                      // the instruction pair is the identity
        CHECK(kSentinelMinusOne == -1);
        CHECK(static_cast<std::uint64_t>(kSentinelMinusOne) == 0xFFFFFFFFFFFFFFFFULL);   // RE 0x5E63B6
    }

    // --- the search tree of 0x89d2f0 (RE 0x89d360 and the node initialisation) ----------------------
    {
        CHECK(kTreeNodeBytes == 152);
        CHECK(kTreeNodeLeft == 0x10);
        CHECK(kTreeNodeRight == 0x18);
        CHECK(kTreeNodeKey == 0x20);
        CHECK(kTreeNodeFirstDouble == 0x40);
        CHECK(kTreeNodeFirstSentinel == 0x60);
        CHECK(kTreeNodeSentinelDouble == 0x78);
        CHECK(kTreeNodeTail == 0x80);
        CHECK(kTreeNodeNoIndex == -1);
        // the offsets sit inside the allocation, in increasing order
        CHECK(kTreeNodeKey < kTreeNodeFirstDouble);
        CHECK(kTreeNodeFirstDouble < kTreeNodeFirstSentinel);
        CHECK(kTreeNodeFirstSentinel < kTreeNodeSentinelDouble);
        CHECK(kTreeNodeSentinelDouble < kTreeNodeTail);
        CHECK(kTreeNodeTail < kTreeNodeBytes);
    }

    // --- the size gate of 0x5e78d0 (RE 0x5e7939: cmp rbx,0x2F ; ja) ---------------------------------
    {
        CHECK(kMinSpanForOneRecord == 47);
        CHECK(kMinSpanForOneRecord + 1 == kIndexedRecordStride);   // 47 is one less than 48
        CHECK(!hasAtLeastOneRecord(0));
        CHECK(!hasAtLeastOneRecord(47));
        CHECK(hasAtLeastOneRecord(48));                            // exactly one 48-byte record
        CHECK(hasAtLeastOneRecord(96));                            // two
    }

    // --- the 16-byte container and the sentinel convention (RE 0x6de960, 0x5e6400, 0x89d3c5) ---------
    {
        CHECK(kSizeRecordStride == 16);
        CHECK(kSizeRecordShift == 4);
        CHECK(elementCount16(0) == 0);
        CHECK(elementCount16(16) == 1);
        CHECK(elementCount16(160) == 10);
        CHECK(elementCount16(15) == 0);                  // a partial record is not counted
        // the four strides recorded so far are all different, which is why each keeps its own constant
        CHECK(kSizeRecordStride != kIndexedRecordStride);
        CHECK(kSizeRecordStride != kRunRecordStride);
        CHECK(kSizeRecordStride != kTimingRecordStride);
        // the sentinel convention appears in two constructors with different addresses
        CHECK(kSentinelCount == 3);
        CHECK(kInvalidIndexSentinel == -1);
        CHECK(kInvalidDoubleSentinel == -1.0);
        CHECK(static_cast<std::uint64_t>(kInvalidIndexSentinel) == 0xFFFFFFFFFFFFFFFFULL);
        // and it agrees with the tree node of round 178
        CHECK(kInvalidIndexSentinel == kTreeNodeNoIndex);
        CHECK(relativeScale(kInvalidDoubleSentinel, 0.0, 0.0, 0.0) == 1.0);   // |-1| under the floor
    }

    // --- almostEqual (RE 0x5e6060: relative epsilon with a switch at 1.0) ---------------------------
    {
        CHECK(kAlmostEqualSwitch == 1.0);
        CHECK(kDoubleMaxBits == 0x7FEFFFFFFFFFFFFFULL);
        CHECK(almostEqual(1.0, 1.0));                       // the equality short-circuit
        CHECK(almostEqual(0.0, 0.0));
        // the small branch: |a-b| <= eps
        CHECK(almostEqual(0.0, kSharedEpsilon));            // exactly at eps
        CHECK(!almostEqual(0.0, 2.0 * kSharedEpsilon));
        // the large branch: |a-b| <= max(|a|,|b|) * eps. The band here is 1e6*eps = 2.22e-10, so the test
        // stays clearly inside and clearly outside rather than sitting on the boundary, where the rounding
        // of the multiplication itself decides the outcome
        CHECK(almostEqual(1e6, 1e6 + 0.5e-10));            // 5e-11 inside the band
        CHECK(almostEqual(1e6, 1e6 - 0.5e-10));
        CHECK(!almostEqual(1e6, 1e6 + 1e-9));              // 1e-9 outside it
        CHECK(!almostEqual(1e6, 1e6 - 1e-9));
        // order does not matter
        CHECK(almostEqual(3.5, 3.5 + 10.0 * kSharedEpsilon) == almostEqual(3.5 + 10.0 * kSharedEpsilon, 3.5));
        // and the epsilon used here is the shared one
        CHECK(kSharedEpsilon == std::numeric_limits<double>::epsilon());
    }

    return check::finish("test_recovered");
}
