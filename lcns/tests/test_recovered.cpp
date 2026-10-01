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
#include "lcns/text_tags.hpp"
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
        CHECK(kGapCount == 84);
        CHECK(countOf(Status::Recovered) == 11);
        CHECK(countOf(Status::Structural) == 31);
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
        // the gate is "> 47 bytes" and serves more than one record type (round 190), so it is
        // NOT tied to the 48-byte stride; that cross-assertion was withdrawn
        CHECK(kMinSpanForOneRecord == 47);
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

    // --- the 16-byte record is a 2D point (RE 0x708020/0x70802a with 0x6de940) ----------------------
    {
        CHECK(kPoint2dSize == 16);
        CHECK(sizeof(Point2dLike) == kPoint2dSize);          // the static assertion, also checked at run time
        CHECK(kPoint2dSize == kSizeRecordStride);            // the stride 0x6DE940 shifts by four for
        CHECK(kPoint2dSize == 2 * sizeof(double));           // two doubles per element
        // the 47-byte gate belongs to the 48-byte records, NOT to these points: for a 16-byte record it
        // would mean 'at least three points'. The two are different types, so the assertion says so.
        CHECK(kPoint2dSize != kIndexedRecordStride);         // 16 is not 48
        CHECK(kMinSpanForOneRecord == 47);   // the gate alone, not tied to a record size
        Point2dLike p{1.5, -2.5};
        CHECK(p.x == 1.5);
        CHECK(p.y == -2.5);
    }

    // --- the polygon area of 0x70c810 (RE 0x70c881..0x70c8ee: the shoelace sum times 0.5) ------------
    {
        CHECK(kAreaHalf == 0.5);
        const Point2dLike square[4] = {{0.0, 0.0}, {2.0, 0.0}, {2.0, 2.0}, {0.0, 2.0}};
        const Point2dLike tri[3] = {{0.0, 0.0}, {4.0, 0.0}, {0.0, 3.0}};
        const Point2dLike line[3] = {{0.0, 0.0}, {1.0, 0.0}, {2.0, 0.0}};
        CHECK(polygonArea(square, 4) == 4.0);
        CHECK(polygonArea(tri, 3) == 6.0);
        CHECK(polygonArea(line, 3) == 0.0);                 // collinear: no area
        CHECK(polygonArea(square, 2) == 0.0);               // fewer than three points
        CHECK(polygonArea(nullptr, 4) == 0.0);
        // the shoelace term is the one the loop accumulates
        CHECK(shoelaceTerm(square[0], square[1]) == 0.0);   // (0+0) * (0-2)
        CHECK(4.0 * kAreaHalf == 2.0);
    }

    // --- the 4-byte accessors (RE 0x5c61d0/0x5c5260/0x5c5f30/0x5c5270 identities, 0x5c5f40 the getter) --
    {
        CHECK(kIdentityAccessorCount == 4);
        CHECK(kGetterFieldOffset == 0x18);
        CHECK(kGetterFieldOffset == kObjectFieldC);          // the same offset 0x5E6360 touches
        CHECK(kGetterFieldOffset == kTreeNodeRight);         // and the tree node's right child
        CHECK(kGetterFieldOffset != kCounterOffset);         // but not the thread state field at 0x4C
    }

    // --- the equal-or-sign atom of 0x5e78d0 (RE 0x5e79a7 + 0x5e79b7/0x5e79e2) ----------------------
    {
        CHECK(kPredicateSignCount == 3);
        CHECK(signCompare(1.0, 1.0) == 0);                 // almost equal gives zero
        CHECK(signCompare(1.0, 0.0) == 1);
        CHECK(signCompare(0.0, 1.0) == -1);
        // the atom's zero branch uses almostEqual, not exact equality
        CHECK(signCompare(1.0, 1.0 + 0.5 * std::numeric_limits<double>::epsilon()) == 0);
        // and it composes with the orientation comparator's own vocabulary
        const Point2dLike o{0.0, 0.0};
        const Point2dLike x{1.0, 0.0};
        const Point2dLike up{0.0, 1.0};
        const Point2dLike down{0.0, -1.0};
        CHECK(signCompare(crossProduct2d(o, x, up), crossProduct2d(o, x, down)) == 1);
        CHECK(signCompare(crossProduct2d(o, x, up), crossProduct2d(o, x, up)) == 0);
    }

    // --- the 2D midpoint of 0x707fd0 (RE 0x708083..0x7080ae) ----------------------------------------
    {
        const Point2dLike a{0.0, 0.0};
        const Point2dLike b{4.0, 6.0};
        const Point2dLike m = midpoint2d(a, b);
        CHECK(m.x == 2.0);
        CHECK(m.y == 3.0);
        CHECK(midpoint2d(a, a).x == 0.0);
        // order does not matter
        CHECK(midpoint2d(b, a).x == m.x);
        CHECK(midpoint2d(b, a).y == m.y);
        // and it agrees with the scalar helper the same 0.5 feeds
        CHECK(midpoint2d(a, b).x == midpointOf(a.x, b.x));
        CHECK(midpoint2d(a, b).y == midpointOf(a.y, b.y));
        CHECK(kMidpointWalkPredicate == 0x72DAC0);
    }

    // --- 0x72dac0: the points differ unless BOTH coordinates are almost equal (RE 0x72dbca/0x72db49) -----
    {
        const double eps = std::numeric_limits<double>::epsilon();
        const Point2dLike a{1.0, 1.0};
        CHECK(kPointComparePredicate == 0x72DAC0);
        CHECK(!pointsDiffer(a, a));                            // both equal -> no difference
        CHECK(!pointsDiffer(a, Point2dLike{1.0 + 0.5 * eps, 1.0}));   // x within eps
        CHECK(!pointsDiffer(a, Point2dLike{1.0, 1.0 + 0.5 * eps}));   // y within eps
        CHECK(pointsDiffer(a, Point2dLike{1.0 + 1e-9, 1.0}));         // x beyond eps -> true regardless of y
        CHECK(pointsDiffer(a, Point2dLike{1.0, 1.0 + 1e-9}));         // y beyond eps
        CHECK(pointsDiffer(a, Point2dLike{1.0 + 1e-9, 1.0 + 1e-9}));
        CHECK(pointAlmostEqual(a, a));
        CHECK(pointsDiffer(a, a) == !pointAlmostEqual(a, a));
        // and it composes with the midpoint routine of round 193
        const Point2dLike m = midpoint2d(a, Point2dLike{3.0, 3.0});
        CHECK(pointAlmostEqual(m, Point2dLike{2.0, 2.0}));
    }

    // --- the gate family means "at least k points" (RE 0x5e37b5 cmp rsi,0x1f) ----------------------
    {
        CHECK(kTwoPointSpan == 31);
        CHECK(kThreePointSpan == 47);
        CHECK(kTwoPointSpan == kMinSpanForOneRecord - 16);   // 47 - 16 = 31, one more point's worth
        CHECK(pointsInSpan(0) == 0);
        CHECK(pointsInSpan(15) == 0);
        CHECK(pointsInSpan(16) == 1);
        CHECK(pointsInSpan(31) == 1);                        // 31 bytes is still only one point
        CHECK(pointsInSpan(32) == 2);
        CHECK(pointsInSpan(48) == 3);
        CHECK(!hasAtLeastPoints(31, 2));                     // the `jbe` at 0x5E37B9
        CHECK(hasAtLeastPoints(32, 2));
        CHECK(!hasAtLeastPoints(47, 3));
        CHECK(hasAtLeastPoints(48, 3));
        CHECK(kPolygonDelimiter == ',');
    }

    // --- the five-qword record (RE 0x734634..0x734674) and the stream fallback (RE 0x9920fb) ---------
    {
        CHECK(kFiveFieldRecord == 5);
        CHECK(kRecordWord5Offset == 0x20);
        CHECK(kFiveFieldRecordBytes == 40);
        CHECK(kRecordWord5Offset == kTreeNodeKey);            // the same offset the tree keys on
        CHECK(kRecordWord5Offset == kGetterFieldOffset + 8);  // and the getter's field is one word earlier
        CHECK(kOstreamSetstateBit == 1);
        CHECK((static_cast<unsigned>(kOstreamSetstateBit) | 1u) == 1u);   // RE the `or edx,1`
    }

    // --- the geometry type vocabulary in rodata (RE rva 0x9df0ed..0x9df155) --------------------------
    {
        CHECK(std::string(kTagPoint) == "POINT");
        CHECK(std::string(kTagVector) == "VECTOR(");
        CHECK(std::string(kTagMultiPoint) == "MULTIPOINT(");
        CHECK(std::string(kTagMultiVector) == "MULTIVECTOR(");
        CHECK(std::string(kTagAngle) == "Angle(");
        CHECK(std::string(kTagDegreeSuffix) == " deg)");
        CHECK(std::string(kTagBoxEmpty) == "BOX(empty)");
        CHECK(std::string(kTagBox) == "BOX(");
        CHECK(std::string(kTagSegment) == "SEGMENT(");
        CHECK(std::string(kTagOrientation) == "ORIENTATION(");
        CHECK(std::string(kTagIn) == "' in (");
        CHECK(kGeometryTagCount == 10);
        // RE 0x9DF0F6: the address the printer loads is a single space
        CHECK(std::string(kCoordinateSeparator) == " ");
        CHECK(std::string(kCoordinateSeparator).size() == 1);
        // RE 0x9DF139
        CHECK(std::string(kElementSeparator) == "), ");
        // the multi- forms are "MULTI" followed by the singular form, which is how the table reads
        CHECK(std::string(kTagMultiPoint) == std::string("MULTI") + kTagPoint + "(");
        CHECK(std::string(kTagMultiVector) == std::string("MULTI") + kTagVector);
        // and the singular point tag carries no parenthesis while the vector one does
        CHECK(std::string(kTagPoint).find('(') == std::string::npos);
        CHECK(std::string(kTagVector).back() == '(');
    }

    // --- the rectangle of four doubles (RE 0x5e5e1c `and edx,3` with 0x5e5e35 `shl rdx,4`) -------------
    {
        CHECK(kBoxCornerCount == 4);
        CHECK(kBoxCornerBytes == 16);
        CHECK(kBoxCornerBytes == kPoint2dSize);              // a corner is a point
        CHECK(cornerIndex(0) == 0);
        CHECK(cornerIndex(3) == 3);
        CHECK(cornerIndex(4) == 0);                          // modulo four, as the `and` does
        CHECK(cornerIndex(7) == 3);
        // the four fields of the object of round 177 are FOUR DOUBLES, eight bytes apart: two points,
        // (x1,y1,x2,y2), from which the four corners are derived by permutation
        CHECK(kObjectFieldA + 8 == kObjectFieldB);
        CHECK(kObjectFieldB + 8 == kObjectFieldC);
        CHECK(kObjectFieldC + 8 == kObjectFieldD);
        CHECK(kObjectFieldD - kObjectFieldA == 3 * sizeof(double));
        CHECK(kObjectFieldD - kObjectFieldA != 3 * kBoxCornerBytes);   // not four stored points
        // and the container's block
        CHECK(kContainerBlockBytes == 504);
        CHECK(kContainerBlockBytes % kBoxCornerBytes == 8);  // 504 = 31 points + 8
        CHECK(kContainerFieldLow < kContainerFieldHigh);
    }

    // --- the large object of 0x5e6200 and the container fields (RE the offsets it touches) -------------
    {
        CHECK(kLargeObjectByteFieldA == 0xB8);
        CHECK(kLargeObjectByteFieldB == 0xBD);
        CHECK(kLargeObjectFieldA == 0x150);
        CHECK(kLargeObjectFieldB == 0x155);
        CHECK(kLargeObjectLastField == 0x158);
        CHECK(kLargeObjectSpacing == 5);
        CHECK(kLargeObjectByteFieldB - kLargeObjectByteFieldA == kLargeObjectSpacing);
        CHECK(kLargeObjectFieldB - kLargeObjectFieldA == kLargeObjectSpacing);
        CHECK(kLargeObjectMinBytes == kLargeObjectLastField + 1);
        // 0x158 is also the timing-record stride of round 156; the object merely has a field there
        CHECK(kLargeObjectLastField == kTimingRecordStride);
        CHECK(kContainerLastField == 0x40);
        CHECK(kContainerFieldStep == 8);
        CHECK((kContainerLastField - kContainerFieldLow) / kContainerFieldStep == 6);   // seven fields
    }

    // --- the bounding box of 0x72dbd0 (RE 0x72dbee/0x72dbf9 seeds and the four comparisons) ----------
    {
        CHECK(kBoundingMaxBits == 0x7FEFFFFFFFFFFFFFULL);
        CHECK(kBoundingMinBits == 0xFFEFFFFFFFFFFFFFULL);
        CHECK(kBoxMinXOffset == 0x00);
        CHECK(kBoxMinYOffset == 0x08);
        CHECK(kBoxMaxXOffset == 0x10);
        CHECK(kBoxMaxYOffset == 0x18);
        CHECK(kBoxStride == 4 * sizeof(double));
        CHECK(kBoxPointStride == kPoint2dSize);
        CHECK(sizeof(Box2d) == kBoxStride);
        const Point2dLike pts[4] = {{1.0, 2.0}, {-3.0, 4.0}, {5.0, -6.0}, {0.0, 0.0}};
        const Box2d b = boundingBox(pts, 4);
        CHECK(b.minX == -3.0);
        CHECK(b.minY == -6.0);
        CHECK(b.maxX == 5.0);
        CHECK(b.maxY == 4.0);
        // an empty list keeps the seeds, which is what the function does when it returns early
        const Box2d empty = boundingBox(nullptr, 0);
        CHECK(empty.minX > empty.maxX);
        CHECK(empty.minY > empty.maxY);
        // a single point collapses the box onto itself
        const Box2d one = boundingBox(pts, 1);
        CHECK(one.minX == one.maxX);
        CHECK(one.minY == one.maxY);
        CHECK(kGeometryDispatchCases == 3);
    }

    // --- the two strides in one body (RE 0x72b6b9/0x72b6bd and 0x72b6ce/0x72b6d5) --------------------
    {
        CHECK(kNestedStrideCheck == 2);
        // the instructions compute n*3 then shift, so the arithmetic is checked rather than the address
        for (std::size_t n = 0; n < 8; ++n) {
            CHECK(((n + n * 2) << 4) == n * 48);
            CHECK(((n + n * 2) << 3) == n * 24);
        }
        CHECK(kIndexedRecordStride == 48);
        CHECK(kSmallRecordStride == 24);
        CHECK(kIndexDivMagic == 0xC30C30C30C30C30DULL);
        CHECK(kIndexDivShift == 4);
    }

    // --- the blocked container of 0x704400 (RE 0x704420, 0x70445a/0x70445e and 0x704469) --------------
    {
        CHECK(kBlockElements == 21);
        CHECK(kBlockFastPathLimit == 20);
        CHECK(kBlockElementStride == 24);
        CHECK(kBlockFastPathLimit + 1 == kBlockElements);
        CHECK(kBlockElementStride == kSmallRecordStride);              // the 24 of round 157
        CHECK(kBlockElements * kBlockElementStride == kContainerBlockBytes);   // the 504 of round 200
        CHECK(kIndexDivisor == 21);                                   // and the divisor of round 203
        CHECK(kIndexDivisor == static_cast<int>(kBlockElements));
        // the addressing the instructions perform: blocks[q] + (i - 21*q)*24
        for (std::size_t i = 0; i <= 42; ++i) {
            const std::size_t q = i / kBlockElements;
            const std::size_t r = i - kBlockElements * q;
            CHECK(r < kBlockElements);
            CHECK(kBlockElementStride * r < kContainerBlockBytes);
            // the fast path is taken exactly while the index fits in the first block
            CHECK((i <= kBlockFastPathLimit) == (q == 0));
        }
    }

    // --- the tree lookup (RE 0x924ecc/0x924ede/0x924f04) and the 16-byte push_back (0x8c370d) ----------
    {
        CHECK(kTreeLookupOutNode == 0x00);
        CHECK(kTreeLookupOutFlag == 0x08);
        // the layout this lookup walks is the one round 178 recorded, so the two agree
        CHECK(kTreeNodeLeft == 0x10);
        CHECK(kTreeNodeRight == 0x18);
        CHECK(kTreeNodeKey == 0x20);
        CHECK(kTreeLookupOutFlag == kTreeNodeFirstDouble - 0x38);   // 0x40 - 0x38 = 8, the flag word
        CHECK(kPushBackElementBytes == 0x10);
        CHECK(kPushBackElementBytes == kPoint2dSize);
        CHECK(kPushBackElementBytes == kBoxPointStride);
        CHECK(kPushBackElementBytes == kBoxCornerBytes);
    }

    // --- the 48-byte record's defaults (RE 0x5ce310) and the translate helper (RE 0x136c50) -----------
    {
        CHECK(kRecord48Doubles == 6);
        CHECK(kRecord48Doubles * static_cast<int>(sizeof(double)) == static_cast<int>(kIndexedRecordStride));
        CHECK(kRecord48Defaults[0] == -1.0);
        CHECK(kRecord48Defaults[1] == -1.0);
        CHECK(kRecord48Defaults[2] == 0.0);
        CHECK(kRecord48Defaults[3] == -1.0);
        CHECK(kRecord48Defaults[4] == 0.0);
        CHECK(kRecord48Defaults[5] == 0.0);
        // the pattern is: -1 at the even slots, 0 at the third and the last two
        CHECK(kRecord48Defaults[1] == kRecord48Defaults[0]);
        CHECK(kRecord48Defaults[3] == kRecord48Defaults[0]);
        CHECK(kRecord48Defaults[2] == kRecord48Defaults[4]);
        CHECK(kRecord48Defaults[4] == kRecord48Defaults[5]);

        CHECK(kTranslateFieldOffset == 0x08);
        CHECK(kTranslateStride == 0x10);
        CHECK(kTranslateStride == kPoint2dSize);          // one point per step
        CHECK(kTranslateInvalidate == 0x50);
        CHECK(kTranslateInvalidValue == -1.0);
        CHECK(kTranslateInvalidValue == kInvalidDoubleSentinel);   // the same sentinel as rounds 178/180
        CHECK(kDefaultAngleDegrees == 90.0);
    }

    // --- the tolerance'd orientation test (RE 0x24b7cb) and the array test (RE 0x5436d8) --------------
    {
        CHECK(kOrientationEpsilon == 0.001);
        CHECK(kOrientationFieldCount == 4);
        CHECK(kArrayCompareEpsilon == 0.0001);
        CHECK(kArrayCompareStride == 8);
        CHECK(kArrayCompareEpsilon < kOrientationEpsilon);      // the two tolerances differ by ten times
        CHECK(kOrientationEpsilon / kArrayCompareEpsilon == 10.0);

        // the shape the orientation test performs: a determinant compared with the tolerance,
        // then its sign when it is outside the band
        // four points, so every parameter is used, mirroring the function's own dependence on four corners
        const auto orientation = [](const Point2dLike& a, const Point2dLike& b,
                                    const Point2dLike& c, const Point2dLike& d) {
            const double det = (b.x - a.x) * (d.y - a.y) - (c.x - a.x) * (b.y - a.y);
            if (std::fabs(det) < kOrientationEpsilon) {
                return 0;
            }
            return det < 0.0 ? 1 : 0;
        };
        CHECK(orientation({0.0, 0.0}, {1.0, 0.0}, {0.0, 1.0}, {1.0, 1.0}) == 0);    // positive determinant
        CHECK(orientation({0.0, 0.0}, {1.0, 0.0}, {0.0, -1.0}, {1.0, -1.0}) == 1);  // negative
        CHECK(orientation({0.0, 0.0}, {1.0, 0.0}, {2.0, 0.0}, {3.0, 0.0}) == 0);    // inside the band

        // the dominance test: any second[i] above first[i] + eps is a violation
        const auto dominates = [](const double* first, const double* second, std::size_t n) {
            for (std::size_t i = 0; i < n; ++i) {
                if (second[i] > first[i] + kArrayCompareEpsilon) {
                    return 1;
                }
            }
            return 0;
        };
        const double a[2] = {1.0, 2.0};
        const double b[2] = {1.0 + 0.5 * kArrayCompareEpsilon, 2.0};
        const double c[2] = {1.0, 2.0 + 2 * kArrayCompareEpsilon};
        CHECK(dominates(a, b, 2) == 0);      // inside the tolerance
        CHECK(dominates(a, c, 2) == 1);      // outside it
        CHECK(dominates(a, a, 2) == 0);

        CHECK(kCtorFlagByteOffset == 0x140);
        CHECK(kCtorZeroQwordOffset == 0x138);
        CHECK(kCtorFlagByteOffset - kCtorZeroQwordOffset == 8);   // the flag follows the zeroed word
        CHECK(kCtorDoubleDefault == 1.0);
        CHECK(kCtorDoubleDefault == kAlmostEqualSwitch);          // the same 1.0 literal as round 185
    }

    // --- the ratio comparator (RE 0x7db718/0x7db736) and the block indexing (RE 0x5522e3) -------------
    {
        CHECK(kRatioCompareMargin == 50.0);
        CHECK(kRatioCompareMargin == kSharedFifty);            // the shared block's 50.0 from round 172
        CHECK(kRatioNumeratorOffset == 0x28);
        CHECK(kRatioDenominatorOffset == 0x30);
        CHECK(kRatioPrimaryOffset == 0x38);
        CHECK(kRatioDenominatorOffset - kRatioNumeratorOffset == 8);
        CHECK(kRatioPrimaryOffset - kRatioDenominatorOffset == 8);   // three consecutive doubles
        CHECK(kComparatorKeyWords == 4);

        // the rule the instructions implement: margin first, then the cross multiplied ratio
        const auto ratioLess = [](double aNum, double aDen, double aPri,
                                  double bNum, double bDen, double bPri) {
            if (std::fabs(aPri - bPri) >= kRatioCompareMargin) {
                return bPri > aPri;                       // RE 0x7DB752/0x7DB756
            }
            return aNum * bDen < bNum * aDen;             // RE 0x7DB736/0x7DB73B/0x7DB74A
        };
        // 1/2 against 1/4: the cross product is 1*4 < 1*2, i.e. 4 < 2, which is false
        CHECK(!ratioLess(1.0, 2.0, 0.0, 1.0, 4.0, 0.0));
        CHECK(ratioLess(1.0, 4.0, 0.0, 1.0, 2.0, 0.0));       // 0.25 < 0.5
        CHECK(ratioLess(0.0, 1.0, 10.0, 0.0, 1.0, 100.0));    // far apart: the primary field decides
        CHECK(!ratioLess(0.0, 1.0, 100.0, 0.0, 1.0, 10.0));

        CHECK(kScale095 == 0.95);
        CHECK(kScaledSumTerms == 2);
        CHECK(kTenfoldFactor == 10.0);
        CHECK(kDequeBlockSize == 512);
        CHECK(kDequeBlockMask == kDequeBlockSize - 1);
        CHECK((1 << kDequeBlockShift) == static_cast<int>(kDequeBlockSize));
    }

    // --- the tiling cancel guard (RE 0x7d355d) and the negated box centre (RE 0x1dd870) ---------------
    {
        CHECK(kTilingCancelThreshold == 0.75);   // RE 0x7D355D: the literal at rva 0x9AF938
        CHECK(kCancelFlagOffset == 0x10);
        CHECK(kCancelOuterFlagOffset == 0x348);
        CHECK(kCancelFlagOffset != kCancelOuterFlagOffset);
        CHECK(std::string(kTagTilingCancelled) == "Tiling time cancelled !");
        CHECK(std::string(kTagTilingCancelled)[0] == 'T');                // a domain message, not a symbol

        // the guard's shape: at or below the threshold the other path is taken, above it the cancellation fires
        const auto overThreshold = [](double progress) { return progress > kTilingCancelThreshold; };
        CHECK(!overThreshold(0.5));
        CHECK(!overThreshold(0.75));                                       // the `jbe` keeps 0.75 on the other path
        CHECK(overThreshold(0.7501));

        CHECK(kBoxCentreHalf == 0.5);
        CHECK(kBoxCentreHalf == kSharedHalf);                              // the shared block's 0.5
        CHECK(kSignFlipMask == 0x8000000000000000ULL);
        CHECK(kSignFlipMask == 1ULL << 63);                                // exactly the sign bit
        // the two coordinate pairs the routine sums are the box fields of round 202
        CHECK(kBoxCentreFromBoxFieldA == 0x08);
        CHECK(kBoxCentreFromBoxFieldC == 0x18);
        const auto centre = [](const Box2d& b) {
            return Point2dLike{(b.minY + b.maxY) * kBoxCentreHalf, (b.minX + b.maxX) * kBoxCentreHalf};
        };
        const Box2d b{1.0, 3.0, 5.0, 7.0};
        const Point2dLike c = centre(b);
        CHECK(c.x == 5.0);
        CHECK(c.y == 3.0);
        // and the negation the routine applies afterwards, as the sign bit
        CHECK((-c.x) == -5.0);
        CHECK((-c.y) == -3.0);
    }

    // --- the 120-byte scan (RE 0x4b82a3), the 48 multiply (RE 0x99f4ce) and the 32-bit limits ---------
    {
        CHECK(kScanStride120 == 0x78);
        CHECK(kScanStride120 == 120);
        CHECK(kScanTolerance == 0.01);
        CHECK(kScanFlag == 1);
        CHECK(kRecord48Mul == 0x30);
        CHECK(kRecord48Mul == kIndexedRecordStride);          // the 48 of round 159, multiplied directly
        CHECK(kElementCompareTolerance == 0.001);
        // the tolerances recorded so far are distinct, which is why each keeps its own constant
        CHECK(kElementCompareTolerance == kOrientationEpsilon);
        CHECK(kScanTolerance != kElementCompareTolerance);
        CHECK(kArrayCompareEpsilon != kElementCompareTolerance);

        CHECK(kInt32MaxExact == 2147483647.0);
        CHECK(kInt32MaxExact == static_cast<double>(0x7FFFFFFF));
        CHECK(kUint32MaxExact == 4294967295.0);
        CHECK(kUint32MaxExact == static_cast<double>(0xFFFFFFFFu));
        CHECK(kUint32MaxExact == 2.0 * kInt32MaxExact + 1.0);   // 2^32-1 = 2*(2^31-1) + 1
        CHECK(kSaturationHalves == 2);

        // the two strides seen in this round are different records
        CHECK(kScanStride120 != kIndexedRecordStride);
        CHECK(kScanStride120 != kRunRecordStride);
        CHECK(kScanStride120 != kTimingRecordStride);
        CHECK(kScanStride120 != kSizeRecordStride);
    }

    // --- the cancel tiers (RE 0x7d34de/0x7d34e6/0x7d34eb), the initialiser and the type anchors ---------
    {
        CHECK(kCancelTierLow == 0.3);
        CHECK(kCancelTierMid == 0.5);
        CHECK(kCancelTierHigh == 0.75);
        CHECK(kCancelKindBoundary == 3);
        CHECK(kCancelTierLow < kCancelTierMid);
        CHECK(kCancelTierMid < kCancelTierHigh);
        // the tier the instructions select, stated as the comparison they perform
        const auto tierFor = [](int kind) { return kind <= kCancelKindBoundary ? kCancelTierMid : kCancelTierLow; };
        CHECK(tierFor(0) == kCancelTierMid);
        CHECK(tierFor(3) == kCancelTierMid);          // the `jbe` keeps the boundary on the 0.5 side
        CHECK(tierFor(4) == kCancelTierLow);
        // and the guard fires above the tier, which is the `ja` at 0x7D3502
        const auto fires = [&](int kind, double progress) { return tierFor(kind) > progress; };
        CHECK(fires(0, 0.25));
        CHECK(!fires(0, 0.6));
        CHECK(fires(9, 0.25));
        CHECK(!fires(9, 0.4));

        CHECK(kInitConstant006 == 0.06);
        CHECK(kInitWord138 == 0x138);
        CHECK(kInitWord138 == kCtorZeroQwordOffset);   // round 215 zeroes the same field
        CHECK(kInitField58 == 0x58);
        CHECK(kInitField58 < kInitWord138);
        CHECK(kInitPairFirst == 0);
        CHECK(kInitPairSecond == 0x14);
        CHECK(kInitPairSecond == 20);
        CHECK(kInitEntryStride == 24);
        CHECK(kInitEntryStride == kSmallRecordStride); // the 24 of round 157
        CHECK((3 * 8) == kInitEntryStride);            // `lea rax,[rax+rax*2]` then scaled by eight

        CHECK(kDefaultStubA == 0x7C2460);
        CHECK(kDefaultStubB == 0x7C2470);
        CHECK(kDefaultStubB - kDefaultStubA == kDefaultStubGap);
        // both were computed from the two displacements rather than copied
        CHECK(kDefaultStubA == 0x7C68E5 + 7 - 0x448C);
        CHECK(kDefaultStubB == 0x7C6904 + 7 - 0x449B);
        // and the bytes there are a stub that returns zero, which is why these are NOT type anchors
        CHECK(kDefaultStubEncoding == 0x9090909090C3C031ULL);
        CHECK(static_cast<std::uint8_t>(kDefaultStubEncoding) == 0x31);          // xor
        CHECK(static_cast<std::uint8_t>(kDefaultStubEncoding >> 8) == 0xC0);     // eax
        CHECK(static_cast<std::uint8_t>(kDefaultStubEncoding >> 16) == 0xC3);    // ret
        CHECK(static_cast<std::uint8_t>(kDefaultStubEncoding >> 24) == 0x90);    // nop
    }

    // --- the hash table of 0x1c65b0 (RE 0x1c667e/0x1c668b/0x1c669b/0x1c66a7) -------------------------
    {
        CHECK(kHashFieldOffset == 0x48);
        CHECK(kBucketCount == 128);
        CHECK(kBucketShift == 7);
        CHECK((1 << kBucketShift) == kBucketCount);
        CHECK(kBucketEntryStride == 24);
        CHECK(kBucketEntryStride == kSmallRecordStride);      // the 24 of round 157
        CHECK(kBucketChainOffset == 0x10);
        CHECK(kRefCountOffset == 0x08);

        // reproduce the sign-corrected modulo and quotient the four instructions around the `and`/`sar` perform
        const auto modBuckets = [](std::int32_t h) {
            const std::int32_t correction = static_cast<std::int32_t>(
                static_cast<std::uint32_t>(h) >> 31 ? 0x7F : 0);   // the `shr edx,0x19` term is 0 or 0x7F
            return ((h + correction) & 0x7F) - correction;
        };
        const auto divBuckets = [](std::int32_t h) {
            const std::int32_t adjusted = h >= 0 ? h : h + 0x7F;   // the `cmovns` keeps h when non-negative
            return adjusted >> kBucketShift;
        };
        for (std::int32_t h = -300; h <= 300; h += 7) {
            const int expectedMod = h % kBucketCount;
            const int expectedDiv = h / kBucketCount;              // C++ truncates toward zero, like the code
            CHECK(modBuckets(h) == expectedMod);
            CHECK(divBuckets(h) == expectedDiv);
            // NOTE: the remainder keeps the sign of the hash, exactly as C's % does -- it is NOT a floored
            // modulo. My first version asserted it was non-negative, which the instructions do not do, and
            // that wrong assumption is what this comment replaces.
            CHECK(modBuckets(h) + kBucketCount >= 0);
        }
        CHECK(modBuckets(0) == 0);
        CHECK(divBuckets(0) == 0);
        CHECK(modBuckets(128) == 0);
        CHECK(divBuckets(128) == 1);
        CHECK(modBuckets(-128) == 0);
        CHECK(divBuckets(-128) == -1);
        // a bucket's byte offset from the entry stride
        CHECK(3 * kBucketEntryStride == 72);                       // `lea rdx,[rbx+rbx*2]` then scaled by 8
    }

    // --- the adaptive budget guard (RE 0x65c198/0x65c1a8/0x65c1d0/0x65c1de) ---------------------------
    {
        CHECK(kGuardBudgetOffset == 0x00);
        CHECK(kGuardLimitOffset == 0x08);
        CHECK(kGuardCountOffset == 0x0C);
        CHECK(kGuardLimitOffset < kGuardCountOffset);          // limit then counter, both below 0x10
        CHECK(kGuardDivisorMs == 1000.0);
        CHECK(kGuardRetryTerm == 2.0);
        CHECK(kGuardTypeSlotA == 0x10);
        CHECK(kGuardTypeSlotB == 0x18);
        CHECK(kGuardTypeSlotB - kGuardTypeSlotA == 8);         // consecutive vtable slots

        // the expression the instructions build, evaluated step by step:
        //   (elapsed_ns / 1e6) / 1000 / (count + 2)  plus the same for the earlier interval
        const auto adapted = [](double elapsedNs, int count) {
            const double millis = elapsedNs / kMicroScale;                 // the /1e6 magic of round 148
            return (millis / kGuardDivisorMs) / (static_cast<double>(count) + kGuardRetryTerm);
        };
        CHECK(adapted(0.0, 0) == 0.0);
        CHECK(adapted(2.0e6, 0) == 0.001);    // 2 ms -> 0.002 / 2 = 0.001
        CHECK(adapted(2.0e9, 0) == 1.0);      // 2000 ms -> 2.0 / 2 = 1.0
        // larger counts shrink the adapted figure, which is the point of dividing by (count + 2)
        CHECK(adapted(2.0e9, 8) < adapted(2.0e9, 0));
        CHECK(adapted(2.0e9, 8) == 0.2);      // 2.0 / 10 = 0.2
        // and the comparison against the budget is a strict `seta`
        const auto exceeds = [&](double elapsedNs, int count, double budget) {
            return adapted(elapsedNs, count) > budget;
        };
        CHECK(exceeds(2.0e9, 8, 0.1));
        CHECK(!exceeds(2.0e9, 8, 0.3));
    }

    // --- the hour wraparound (RE 0x5c2273/0x5c22aa) and the steps constructor (RE 0x1bf1a0) -----------
    {
        CHECK(kNanosecondsPerHour == 3600000000000ULL);
        CHECK(kNanosecondsPerHour == 3600ULL * 1000000000ULL);        // one hour, in nanoseconds
        CHECK(kNanosecondsPerHourMax == kNanosecondsPerHour - 1ULL);
        CHECK(kHourRoundTerm == 0.5);
        CHECK(kDegreesFullTurn == 360.0);
        CHECK(kDegreesFullTurn == kDegreesPerTurn);                   // the 360 of round 168

        // the wraparound the two constants implement
        const auto wrapHours = [](std::int64_t ns) {
            const std::int64_t hour = static_cast<std::int64_t>(kNanosecondsPerHour);
            while (ns < 0) {
                ns += hour;
            }
            while (ns > static_cast<std::int64_t>(kNanosecondsPerHourMax)) {
                ns -= hour;
            }
            return ns;
        };
        CHECK(wrapHours(0) == 0);
        CHECK(wrapHours(1000) == 1000);
        CHECK(wrapHours(static_cast<std::int64_t>(kNanosecondsPerHour)) == 0);
        CHECK(wrapHours(static_cast<std::int64_t>(kNanosecondsPerHour) + 5) == 5);
        CHECK(wrapHours(-5) == static_cast<std::int64_t>(kNanosecondsPerHour) - 5);
        CHECK(wrapHours(-static_cast<std::int64_t>(kNanosecondsPerHour)) == 0);
        CHECK(wrapHours(static_cast<std::int64_t>(kNanosecondsPerHour) - 1) ==
              static_cast<std::int64_t>(kNanosecondsPerHourMax));

        CHECK(kStepsField0 == 0x00);
        CHECK(kStepsField8 == 0x08);
        CHECK(kStepsDoubleA == 0x10);
        CHECK(kStepsDoubleB == 0x18);
        CHECK(kStepsDoubleC == 0x20);
        CHECK(kStepsFlag28 == 0x28);
        CHECK(kStepsField30 == 0x30);
        CHECK(kStepsDoubleB - kStepsDoubleA == 8);                    // three consecutive doubles
        CHECK(kStepsDoubleC - kStepsDoubleB == 8);
        CHECK(kStepsDefaultPlus == 1.0);
        CHECK(kStepsDefaultMinus == -1.0);
        CHECK(kStepsDefaultMinus == -kStepsDefaultPlus);
    }

    // --- the machine-kind preset table (RE 0x7f41de..0x7f427b) and the 1e-6 test (RE 0x14f5fb) --------
    {
        CHECK(kPresetCount == 9);
        CHECK(kPresetStride == 4);
        CHECK(kPresetKindOneValue == 1);
        CHECK(kPresetKindTwoValue == 2);
        // the hex the instructions write, converted by hand and checked against the arrays
        CHECK(kPresetKindOne[0] == 0x14);
        CHECK(kPresetKindOne[2] == 0x64);
        CHECK(kPresetKindOne[3] == 0x0A);
        CHECK(kPresetKindOne[5] == 0x32);
        CHECK(kPresetKindTwo[0] == 0x28);
        CHECK(kPresetKindTwo[3] == 0x14);
        CHECK(kPresetOther[0] == 0x64);
        CHECK(kPresetOther[3] == 0x32);
        // the tail is shared by all three variants, which is what the jump to 0x7F41F9 means
        CHECK(kPresetKindOne[4] == kPresetKindTwo[4]);
        CHECK(kPresetKindTwo[4] == kPresetOther[4]);
        CHECK(kPresetKindOne[5] == kPresetKindTwo[5]);
        CHECK(kPresetKindTwo[5] == kPresetOther[5]);
        for (int i = 6; i < kPresetCount; ++i) {
            CHECK(kPresetKindOne[i] == kPresetKindTwo[i]);
            CHECK(kPresetKindTwo[i] == kPresetOther[i]);
            CHECK(kPresetKindOne[i] == 20);
        }
        // and only the first entry differs between the second and third variants at that position
        CHECK(kPresetKindTwo[1] == kPresetOther[1]);
        CHECK(kPresetKindOne[1] == kPresetOther[1]);

        CHECK(kContainTolerance == 1e-06);
        CHECK(kContainTolerance < kElementCompareTolerance);          // smaller than the 0.001 of round 218
        CHECK(kContainFlagOffset == 0x28);
        CHECK(kContainSizeOffset == 0x38);
        CHECK(kContainSizeOffset - kContainFlagOffset == 0x10);
        CHECK(kContainSizeOffset == kRatioPrimaryOffset);             // the same +0x38 the comparator reads
        CHECK(kContainCoordinateCount == 4);
    }

    // --- the two initialisers (RE 0x704260 and 0x2b3990) and the shared unit literal --------------------
    {
        CHECK(kCtor098Bytes == 0x98);
        CHECK(kCtor098UnitCount == 4);
        CHECK(kCtor098UnitA == 0x30);
        CHECK(kCtor098UnitB == 0x48);
        CHECK(kCtor098UnitC == 0x68);
        CHECK(kCtor098UnitD == 0x80);
        // the spacings the instructions produce, hand checked above
        CHECK(kCtor098UnitB - kCtor098UnitA == 0x18);
        CHECK(kCtor098UnitC - kCtor098UnitB == 0x20);
        CHECK(kCtor098UnitD - kCtor098UnitC == 0x18);
        CHECK(kCtor098UnitB - kCtor098UnitA == 24);
        CHECK(kCtor098UnitC - kCtor098UnitB == 32);
        // every unit entry sits inside the object, and the flags do too
        CHECK(kCtor098UnitD + 8 <= kCtor098Bytes);
        CHECK(kCtor098FlagA < kCtor098UnitC);
        CHECK(kCtor098FlagB < kCtor098Bytes);
        CHECK(kCtor098FlagB - kCtor098FlagA == 0x38);

        CHECK(kCtor4CUnit == 0x30);
        CHECK(kCtor4CBlock == 0x38);
        CHECK(kCtor4CBlockBytes == 0x10);
        CHECK(kCtor4CDword == 0x48);
        CHECK(kCtor4CBytes == 0x4C);
        CHECK(kCtor4CPairA == 0x18);
        CHECK(kCtor4CPairB == 0x20);
        CHECK(kCtor4CPairB - kCtor4CPairA == 8);              // two consecutive doubles
        CHECK(kCtor4CBlock + kCtor4CBlockBytes == kCtor4CDword);   // the block ends where the dword starts
        CHECK(kCtor4CDword + 4 == kCtor4CBytes);                   // and the object ends after the dword

        CHECK(kSharedUnitRva == 0x9DFBC8);
        // the unit literal the four entries use is the same value as the other unit defaults landed so far
        CHECK(kStepsDefaultPlus == 1.0);
        CHECK(kCtorDoubleDefault == 1.0);
    }

    // --- the ratio family's second member (RE 0x724e40) and the two new sizes (RE 0x724ed7, 0x18052a) ----
    {
        CHECK(kRatioFamilyMargin == kRatioCompareMargin);       // the same 50.0 the round-216 member reads
        CHECK(kRatioFamilyPrimaryA == 0x50);
        CHECK(kRatioFamilyPrimaryB == 0x88);
        CHECK(kRatioFamilyNumA == 0x40);
        CHECK(kRatioFamilyDenA == 0x80);
        CHECK(kRatioFamilyNumB == 0x78);
        CHECK(kRatioFamilyDenB == 0x48);
        CHECK(kRatioFamilyTag == 6);
        // round 243: the field-identical group splits by tag, so "twins" was an overstatement
        CHECK(kRatioFamilyTagA == 6);
        CHECK(kRatioFamilyTagB == 5);
        CHECK(kRatioFamilyTagCount == 2);
        CHECK(kRatioFamilyTagA != kRatioFamilyTagB);
        CHECK(kRatioFamilyTag == kRatioFamilyTagA);
        // round 244: each tag has two sites, and the same rule runs on stack copies too
        CHECK(kRatioFamilyTagSites6 == 2);
        CHECK(kRatioFamilyTagSites5 == 2);
        CHECK(kRatioFamilyTagSites6 + kRatioFamilyTagSites5 == 4);
        CHECK(kRatioFamilyStackPrimaryA == 0xD0);
        CHECK(kRatioFamilyStackPrimaryB == 0x108);
        CHECK(kRatioFamilyStackTag == 0x160);
        CHECK(kRatioFamilyStackPrimaryB > kRatioFamilyStackPrimaryA);
        CHECK(kRatioFamilyStackTag > kRatioFamilyStackPrimaryB);
        CHECK(kRatioFamilyStackPrimaryB - kRatioFamilyStackPrimaryA == 0x38);
        CHECK(kRatioFamilyStackTag - kRatioFamilyStackPrimaryB == 0x58);
        CHECK(kRatioFamilyMembers == 3);
        // the fields of this member are distinct from the round-216 member's, which is why it is a second member
        CHECK(kRatioFamilyPrimaryA != kRatioPrimaryOffset);
        CHECK(kRatioFamilyNumA != kRatioNumeratorOffset);
        // round 231: a near twin of the second member, so two of the three are that pair
        CHECK(kRatioFamilyTwins == 3);   // corrected in round 232
        CHECK(kRatioFamilyTwins <= kRatioFamilyMembers);
        // round 232's member scan: three functions share the ratio field set, and two more pairs exist
        CHECK(kRatioFamilyTwins == 3);
        CHECK(kRatioFamilyRatioFields == 7);
        CHECK(kRatioFamilyAlmostFieldA == 0x30);
        CHECK(kRatioFamilyAlmostFieldB == 0x38);
        CHECK(kRatioFamilyAlmostFieldB - kRatioFamilyAlmostFieldA == 8);
        CHECK(kAlmostEqualPredicate == 0x5E6060);
        CHECK(kRatioFamilyAlmostPair == 2);
        CHECK(kRatioFamilyTreePair == 2);
        // the ratio fields the twin group shares are the ones rounds 216/227 landed
        CHECK(kRatioFamilyPrimaryA == 0x50);
        CHECK(kRatioFamilyNumA == 0x40);
        CHECK(kRatioFamilyNumB == 0x78);
        CHECK(kRatioFamilyDenA == 0x80);
        CHECK(kRatioFamilyDenB == 0x48);
        CHECK(kUseSiteTreeChildA == 0x10);
        CHECK(kUseSiteTreeChildB == 0x18);
        // and the family has a use site: a tree walk that calls the round-216 comparator
        CHECK(kComparatorUseSite == 0x716DA0);
        CHECK(kUseSiteTreeKey == 0x20);
        CHECK(kUseSiteTreeChildA == 0x10);
        CHECK(kUseSiteTreeChildB == 0x18);
        CHECK(kUseSiteTreeChildA == kTreeNodeLeft);              // the tree layout of round 178
        CHECK(kUseSiteTreeChildB == kTreeNodeRight);
        CHECK(kUseSiteTreeKey == kTreeNodeKey);
        // round 235: the same walk in the other direction, calling the same comparator
        CHECK(kTreeLookupGreater == 0x716DA0);
        CHECK(kTreeLookupLess == 0x714D40);
        CHECK(kTreeLookupDirections == 2);
        CHECK(kTreeLookupAlloc == 0x68);
        CHECK(kTreeLookupAlloc == 104);
        CHECK(kTreeLookupGreater != kTreeLookupLess);
        CHECK(kComparatorUseSite == kTreeLookupGreater);   // the constant still names the same function

        // the rule, restated for this member's fields
        const auto ratioLess = [](double aNum, double aDen, double aPri,
                                  double bNum, double bDen, double bPri) {
            if (std::fabs(aPri - bPri) >= kRatioFamilyMargin) {
                return bPri > aPri;
            }
            return aNum * bDen < bNum * aDen;
        };
        // 1/2 against 1/4: 1*4 < 1*2 is 4 < 2, false
        CHECK(!ratioLess(1.0, 2.0, 0.0, 1.0, 4.0, 0.0));
        // 1/4 against 1/2: 1*2 < 1*4 is 2 < 4, true
        CHECK(ratioLess(1.0, 4.0, 0.0, 1.0, 2.0, 0.0));
        // far apart, so the margin path decides on the primary field
        CHECK(ratioLess(0.0, 1.0, 10.0, 0.0, 1.0, 100.0));

        CHECK(kStride56 == 56);
        CHECK(kStride56 == 7 * 8);
        CHECK(kStride56 != kScanStride120);
        CHECK(kStride56 != kIndexedRecordStride);
        CHECK(kStride56 != kSmallRecordStride);

        CHECK(kSize148 == 0x148);
        CHECK(kSize148 == 328);
        CHECK(kSize148 != kContainerBlockBytes);
        CHECK(kSize148 != kFiveFieldRecordBytes);
    }

    // --- the constructor family (RE 0x220780/0x22079b/0x2202a3/0x220243) --------------------------------
    {
        CHECK(kCtorFamilyUnitRva == 0x9C1BF0);
        CHECK(kCtorFamilyCallee == 0x1FD6C0);
        CHECK(kCtorFamilyMembers == 4);
        // round 237: the identity quad laid down twice
        CHECK(kIdentityQuadPattern[0] == 0.0);
        CHECK(kIdentityQuadPattern[1] == 1.0);
        CHECK(kIdentityQuadPattern[2] == 0.0);
        CHECK(kIdentityQuadPattern[3] == 0.0);
        CHECK(kIdentityQuadPattern[1] == kCtorDoubleDefault);   // the shared unit literal
        CHECK(kIdentityQuadCount == 2);
        CHECK(kSentinelQwordUses == 5);
        CHECK(kSentinelQwordUses > 0);
        CHECK(kIdentityQuadStride == 0x98);
        CHECK(kIdentityQuadStride == kCtor098Bytes);            // the same shape as round 226's object
        // round 236: a wrapper that allocates twice
        CHECK(kAlloc0x50 == 0x50);
        CHECK(kAlloc0x1B8 == 0x1B8);
        CHECK(kAlloc0x50 == 80);
        CHECK(kAlloc0x1B8 == 440);
        CHECK(kWrapperVtable == 0x00);
        CHECK(kWrapperFirstField == 0x08);
        CHECK(kWrapperSource == 0x40);
        CHECK(kWrapperBody == 0x48);
        CHECK(kWrapperBody - kWrapperSource == 8);
        CHECK(kWrapperZeroedQwords == 7);
        // round 239: the record container joined against the tree
        CHECK(kJoinBeginOffset == 0x10);
        CHECK(kJoinEndOffset == 0x30);
        CHECK(kJoinRecordFlag == 0x20);
        CHECK(kJoinRecordKey == 0x30);
        CHECK(kJoinKeyWords == 4);
        CHECK(kJoinRecordDoubleA == 0x58);
        CHECK(kJoinRecordDoubleB == 0x60);
        CHECK(kJoinRecordDoubleC == 0x68);
        CHECK(kJoinRecordDoubleB - kJoinRecordDoubleA == 8);
        CHECK(kJoinRecordDoubleC - kJoinRecordDoubleB == 8);
        CHECK(kJoinRecordDoubleA - kJoinRecordKey == 0x28);
        CHECK(kJoinEndOffset > kJoinBeginOffset);
        CHECK(kJoinRecordFlag < kJoinRecordKey);
        // round 240: the family's fifth member and the 152-byte stride
        CHECK(kStride152 == 152);
        CHECK(kStride152 == 19 * 8);
        CHECK(kStride152Words == 19);
        CHECK(kStride152 != kStride56);
        CHECK(kStride152 != kScanStride120);
        CHECK(kStride152 != kIndexedRecordStride);
        CHECK(kFamilyMember5Base == 0x30);
        CHECK(kFamilyMember5Primary == 0x40);
        CHECK(kFamilyMember5Primary == kFamilyMember5Base + 0x10);
        CHECK(kFamilyMember5Primary == kRatioAlmostPrimary);   // two members share this primary offset
        CHECK(kRatioFamilyMembers2 == 5);
        // round 241: the mapper, a 40-byte walk and the twins' offsets confirmed again
        CHECK(kRecordStride40 == 0x28);
        CHECK(kRecordStride40 == 40);
        CHECK(kRecordStride40 != kStride56);
        CHECK(kRecordStride40 != kStride152);
        CHECK(kRecordStride40 != kScanStride120);
        CHECK(kMapperFieldA == 0x78);
        CHECK(kMapperFieldB == 0x80);
        CHECK(kMapperCompare == 0x48);
        CHECK(kMapperFieldA == kRatioFamilyNumB);
        CHECK(kMapperFieldB == kRatioFamilyDenA);
        CHECK(kMapperCompare == kRatioFamilyDenB);
        CHECK(kMapperFieldB - kMapperFieldA == 8);
        CHECK(kStride152Sightings == 2);
        // round 242: the pairwise loop
        CHECK(kPairwiseCallee == 0x824B40);
        // round 247: that callee is the container element accessor, with thirty callers
        CHECK(kAccessorMagic == 0x82FA0BE82FA0BE83ULL);
        CHECK(kAccessorElementBytes == 0x158);
        CHECK(kAccessorElementBytes == 344);
        CHECK(kAccessorElementBytes == kCtorFamilyRecordBytes);   // the same 344 as round 230
        CHECK(kAccessorElementBytes == kSize158);
        CHECK(kAccessorElementBytes != kSize148);
        CHECK(kAccessorShift == 3);
        CHECK(kAccessorCallers == 30);
        CHECK(kAccessorCallers > kRatioFamilyTagSites6 + kRatioFamilyTagSites5);
        CHECK(kPairwiseElementStride == 0x10);
        CHECK(kPairwiseElementStride == kPoint2dSize);
        CHECK(kPairwiseCallsPerStep == 2);
        CHECK(kSentinelSightings == 5);
        CHECK(kNineMultiplier == 9);
        CHECK(kNineMultiplier * 2 == 18);          // the doubling step of the 19-word form
        CHECK(kNineMultiplier * 2 + 1 == kStride152Words);
        CHECK(kWrapperSource - kWrapperFirstField == 0x38);
        CHECK(kAlloc0x1B8 != kSize158);
        CHECK(kAlloc0x50 != kSize148);
        CHECK(kCtorPairAWord == 0x138);
        CHECK(kCtorPairAFlag == 0x140);
        CHECK(kCtorPairBWord == 0x148);
        CHECK(kCtorPairBFlag == 0x150);
        CHECK(kCtorPairSpacing == 0x10);
        CHECK(kCtorPairAFlag - kCtorPairAWord == 8);          // the flag follows its zeroed word
        CHECK(kCtorPairBFlag - kCtorPairBWord == 8);
        CHECK(kCtorPairBWord - kCtorPairAWord == kCtorPairSpacing);
        CHECK(kCtorPairBFlag - kCtorPairAFlag == kCtorPairSpacing);
        // round 215 read the first pair, this round the second, so the layout is confirmed twice
        CHECK(kCtorFlagByteOffset == kCtorPairAFlag);
        CHECK(kCtorZeroQwordOffset == kCtorPairAWord);
        CHECK(kCtorDoubleDefault == 1.0);

        CHECK(kSize158 == 0x158);
        CHECK(kSize158 == 344);
        CHECK(kSize158 == kTimingRecordStride);               // the stride of round 156, as an allocation size
        CHECK(kSize158 != kSize148);                           // and that round's other size is different
        // round 230's fourth member, and the third sighting of 0x158
        CHECK(kCtorFamilyRecordBytes == 0x158);
        CHECK(kCtorFamilyRecordBytes == kSize158);
        CHECK(kCtorFamilyRecordBytes == kTimingRecordStride);
        CHECK(kCtorVecVtable == 0x00);
        CHECK(kCtorVecUnit == 0x08);
        CHECK(kCtorVecZeroA == 0x10);
        CHECK(kCtorVecZeroB == 0x18);
        CHECK(kCtorVecZeroC == 0x20);
        CHECK(kCtorVecArgument == 0x28);
        CHECK(kCtorVecSource == 0x30);
        CHECK(kCtorVecZeroC - kCtorVecZeroA == 0x10);          // three zeroed words, eight bytes apart
        CHECK(kCtorVecArgument - kCtorVecZeroC == 8);
        CHECK(kCtorVecSource - kCtorVecArgument == 8);
    }

    // --- the family rule completed (RE 0x7dc401/0x7dc416/0x7dc42e) -------------------------------------
    {
        CHECK(kRatioAlmostNum == 0x30);
        CHECK(kRatioAlmostDen == 0x38);
        CHECK(kRatioAlmostPair == 2);
        // round 238: this pair's own primary offset and its three key words
        CHECK(kRatioAlmostPrimary == 0x40);
        CHECK(kRatioAlmostKeyWords == 3);
        CHECK(kRatioAlmostKeyA == 0x20);
        CHECK(kRatioAlmostKeyB == 0x18);
        CHECK(kRatioAlmostKeyC == 0x10);
        CHECK(kRatioAlmostKeyA > kRatioAlmostKeyB);
        CHECK(kRatioAlmostKeyB > kRatioAlmostKeyC);
        // each member has a different primary offset, which is why the table has three entries
        CHECK(kRatioAlmostPrimary != kRatioPrimaryOffset);
        CHECK(kRatioAlmostPrimary != kRatioFamilyPrimaryA);
        // CORRECTED in round 238: the ratio offsets are NOT shared either. My first version asserted
        // they were, and the failure showed the opposite: the twin group reads +0x40/+0x80 and +0x78/+0x48,
        // while this pair reads +0x30/+0x38. Only the 50.0 literal and the RULE are shared across members.
        CHECK(kRatioAlmostNum != kRatioFamilyNumA);
        CHECK(kRatioAlmostDen != kRatioFamilyDenB);
        CHECK(kRatioAlmostNum == 0x30 && kRatioAlmostDen == 0x38);
        CHECK(kRatioFamilyNumA == 0x40 && kRatioFamilyDenB == 0x48);
        CHECK(kRatioFamilyRuleCases == 3);
        CHECK(kRatioAlmostDen - kRatioAlmostNum == 8);
        CHECK(kAlmostEqualPredicate == 0x5E6060);        // the predicate the tie test calls

        // the rule as the instructions implement it: -1, 0 or +1, with the tie test in the middle
        const auto compare = [](double aNum, double aDen, double aPri,
                                double bNum, double bDen, double bPri) {
            if (std::fabs(aPri - bPri) >= kRatioCompareMargin) {
                if (aPri == bPri) return 0;
                return aPri > bPri ? 1 : -1;                       // RE 0x7DC3F8/0x7DC3FC
            }
            const double crossA = aNum * bDen;                      // RE 0x7DC401
            const double crossB = bNum * aDen;                      // RE 0x7DC416
            if (almostEqual(crossA, crossB)) {                      // RE 0x7DC42E/0x7DC433
                return 0;                                           // the comparison falls through
            }
            return crossA > crossB ? 1 : -1;                        // RE 0x7DC437/0x7DC43B
        };
        // case 1: 1/2 against 1/4 -- cross products 4 and 2, so the first ratio is greater
        CHECK(compare(1.0, 2.0, 0.0, 1.0, 4.0, 0.0) == 1);
        // case 2: 1/2 against 2/4 -- both cross products are 4, so the tie test reports equality
        CHECK(compare(1.0, 2.0, 0.0, 2.0, 4.0, 0.0) == 0);
        // case 3: far apart primaries, so the margin path decides on the primary field
        CHECK(compare(1.0, 2.0, 10.0, 1.0, 2.0, 100.0) == -1);
        CHECK(compare(1.0, 2.0, 100.0, 1.0, 2.0, 10.0) == 1);
        // and the tie test is the same epsilon the predicate of round 185 uses
        CHECK(almostEqual(4.0, 4.0));
        CHECK(!almostEqual(4.0, 2.0));
    }

    // --- the four widely called primitives (RE 0x86a2c0, 0x5c4d30, 0x8774f0, 0x8aa7e0) ----------------
    {
        CHECK(kReleaseCounterOffset == 0x10);
        CHECK(kReleaseCounterOffset == 16);
        CHECK(kReleaseDealloc == 0x9984B0);
        CHECK(kReleaseCallers == 61);
        CHECK(kReleaseDecrement == 0xFFFFFFFFu);
        CHECK(static_cast<std::int32_t>(kReleaseDecrement) == -1);      // it is -1 as an int32
        // the release, restated: only a non-positive old count goes on to the deallocator
        const auto release = [](int count) { return count <= 0; };
        CHECK(release(0));
        CHECK(release(-1));
        CHECK(!release(1));
        CHECK(!release(2));

        CHECK(kCompareByteOffset == 0x00);
        CHECK(kCompareWordOffset == 0x08);
        CHECK(kCompareCallers == 39);
        CHECK(kCompareIsStrictGreater);
        // the predicate answers "greater", never -1: equality is zero and less-than is zero too
        const auto greater = [](unsigned char aB, std::int64_t aW,
                                unsigned char bB, std::int64_t bW) {
            if (aB != bB) return aB > bB;
            return aW > bW;
        };
        CHECK(greater(1, 0, 0, 9));        // the byte decides
        CHECK(!greater(0, 9, 1, 0));
        CHECK(greater(5, 10, 5, 9));       // equal bytes, so the word decides
        CHECK(!greater(5, 9, 5, 10));
        CHECK(!greater(5, 9, 5, 9));       // equality is not "greater"

        CHECK(kThunkTarget == 0x8771C0);
        CHECK(kThunkCallers == 67);
        CHECK(kOnceCallee == 0x63F6A8);
        CHECK(kOnceCallers == 65);
        CHECK(kOnceCallers > kReleaseCallers);
    }

    // --- the tag-aware comparator and the tagged sign object (RE 0xf2000 and 0xf12c0) ----------------
    {
        CHECK(kTagFieldOffset == 0x20);
        CHECK(kTagUnsetValue == 1);
        CHECK(kDelegateCompare == 0xF1F50);
        CHECK(kBothUnsetNegates);
        CHECK(kTagAwareCallers == 66);
        // the comparator as the instructions implement it, including the negation in the both-unset case
        const auto cmp = [](int aTag, int bTag, int delegated) {
            if (aTag == kTagUnsetValue) {
                if (bTag != kTagUnsetValue) return -1;      // RE 0xF2024
                return -delegated;                          // RE 0xF2030
            }
            if (bTag == kTagUnsetValue) return 1;           // RE 0xF2040
            return delegated;                               // RE 0xF2014
        };
        CHECK(cmp(1, 0, 7) == -1);          // only the left is unset
        CHECK(cmp(0, 1, 7) == 1);           // only the right is unset
        CHECK(cmp(1, 1, 7) == -7);          // both unset: the delegate's answer is negated
        CHECK(cmp(1, 1, -3) == 3);
        CHECK(cmp(0, 0, -3) == -3);         // neither unset: the delegate decides

        CHECK(kSignVtableRva == 0x960411);
        CHECK(kKindOffset == 0x10);
        CHECK(kKindValue2 == 2);
        CHECK(kSignOffset == 0x20);
        CHECK(kSignOffset == kTagFieldOffset);          // the sign and the tag share the offset
        CHECK(kPayloadBytes == 0x10);
        CHECK(kPayloadAlloc == 0xFE1F0);
        CHECK(kLazyInitCallee == 0xEEEE0);
        CHECK(kSignObjectCallers == 64);

        CHECK(kSsoCapacity == 0x14);
        CHECK(kSsoSize == 0x00);
        CHECK(kSsoData == 0x18);
        CHECK(kSsoTailCall == 0x9984A0);
        CHECK(kSsoCallers == 58);
        CHECK(!kSsoInference);                           // upgraded in round 291: proven by the assignment
        CHECK(kSsoData > kSsoCapacity);
    }

    // --- the bit-length algorithm and the container walk (RE 0xf1aa0 and 0x8f2ca0) ------------------
    {
        CHECK(kBigIntCountOffset == 0x10);
        CHECK(kBigIntWordsOffset == 0x18);
        CHECK(kBitsPerWord == 0x40);
        CHECK(kBitsPerWord == 64);
        CHECK(kBitShiftPerWord == 6);
        CHECK(1 << kBitShiftPerWord == kBitsPerWord);
        CHECK(kBitLengthBisect);
        CHECK(kBitLengthCallers == 55);

        // the algorithm the instructions implement: skip trailing zero words, then find the top set bit
        const auto bitLength = [](const std::vector<std::uint64_t>& w) {
            std::size_t n = w.size();
            while (n > 0 && w[n - 1] == 0) --n;          // RE 0xF1AB0/0xF1AB6
            if (n == 0) return 0;                        // RE 0xF1AAD -> 0xF1B10
            std::uint64_t top = w[n - 1];
            int bits = 0;
            while (top) { top >>= 1; ++bits; }           // the bisection's answer for one word
            return static_cast<int>((n - 1) * kBitsPerWord) + bits;   // RE 0xF1AC4
        };
        CHECK(bitLength({}) == 0);
        CHECK(bitLength({0}) == 0);
        CHECK(bitLength({0, 0, 0}) == 0);
        CHECK(bitLength({1}) == 1);
        CHECK(bitLength({0x80}) == 8);
        CHECK(bitLength({0xFF}) == 8);
        CHECK(bitLength({0x100}) == 9);
        CHECK(bitLength({0, 1}) == 65);                  // one whole word plus one bit
        CHECK(bitLength({0, 1, 0, 0}) == 65);            // trailing zeros do not count
        CHECK(bitLength({~0ULL}) == 64);

        CHECK(kWalkBeginOffset == 0x00);
        CHECK(kWalkEndOffset == 0x08);
        CHECK(kWalkElementStride == 0x10);
        CHECK(kWalkElementStride == kPoint2dSize);
        CHECK(kWalkCallers == 51);
        CHECK(kWalkEndOffset > kWalkBeginOffset);
    }

    // --- the byte-length sibling and the add-then-shift identities (RE 0xf19e0 and 0xf1ac4) -----------
    {
        CHECK(kBytesPerWord == 8);
        CHECK(kByteShiftPerWord == 3);
        CHECK(kByteLengthCallers == 50);
        CHECK(kBitsPerWord == kBytesPerWord * 8);
        CHECK(1 << kByteShiftPerWord == kBytesPerWord);

        // the same algorithm as the bit version, but answering in bytes
        const auto byteLength = [](const std::vector<std::uint64_t>& w) {
            std::size_t n = w.size();
            while (n > 0 && w[n - 1] == 0) --n;
            if (n == 0) return 0;
            std::uint64_t top = w[n - 1];
            int bits = 0;
            while (top) { top >>= 1; ++bits; }
            return static_cast<int>((n - 1) * kBytesPerWord) + (bits + 7) / 8;
        };
        CHECK(byteLength({}) == 0);
        CHECK(byteLength({0}) == 0);
        CHECK(byteLength({1}) == 1);
        CHECK(byteLength({0x100}) == 2);
        CHECK(byteLength({0, 1}) == 9);                  // eight whole bytes plus one
        CHECK(byteLength({~0ULL}) == 8);

        // the two addends are 2**26 - 1 and 2**29 - 1, and the idioms they implement are (count-1)*64 and
        // (count-1)*8 in 32-bit arithmetic -- asserted for several counts rather than stated in prose
        CHECK(kBitsScaleAddend == (1u << 26) - 1);
        CHECK(kBytesScaleAddend == (1u << 29) - 1);
        for (std::uint32_t count = 1; count <= 5; ++count) {
            const std::uint32_t viaAdd = (count + kBitsScaleAddend) << 6;
            const std::uint32_t direct = (count - 1u) * kBitsPerWord;
            CHECK(viaAdd == direct);
            const std::uint32_t viaAddBytes = (count + kBytesScaleAddend) * 8u;
            const std::uint32_t directBytes = (count - 1u) * kBytesPerWord;
            CHECK(viaAddBytes == directBytes);
        }

        CHECK(kSearchHelper == 0x869EF0);
        CHECK(kLengthHelper == 0x63F238);
        CHECK(kSearchDefault == -1);
        CHECK(kSearchCallers == 37);
    }

    // --- the formatter and the gated getter block (RE 0x77f2d0 and 0x945370) -------------------------
    {
        CHECK(kFormatterAlloc == 0x30);
        CHECK(kFormatterAlloc == 48);
        CHECK(kFormatterTextHelper == 0xC71D0);
        CHECK(kFormatterRelease == 0x9984B0);
        CHECK(kFormatterRelease == kReleaseDealloc);     // the same deallocator round 248 found
        CHECK(kFormatterVtableA == 0x2D39DC);
        CHECK(kFormatterVtableB == 0x2C2F49);
        CHECK(kFormatterVtableC == 0x2BFA55);
        CHECK(kFormatterVtableA != kFormatterVtableB);
        CHECK(kFormatterVtableB != kFormatterVtableC);
        CHECK(kFormatterCallers == 43);
        // the domain string this formatter builds
        CHECK(std::string(kTagBerDecodeError) == "BER decode error");
        CHECK(std::string(kTagBerDecodeError).size() == 16);

        CHECK(kGetterFieldA == 0xF0);
        CHECK(kGetterFieldB == 0xF8);
        CHECK(kGetterStep == 8);
        CHECK(kGetterFieldB - kGetterFieldA == kGetterStep);
        CHECK(kGetterCheckA == 0x990540);
        CHECK(kGetterGetA == 0x9916E0);
        CHECK(kGetterCheckB == 0x990840);
        CHECK(kGetterGetB == 0x9919E0);
        CHECK(kGetterCheckC == 0x990780);
        CHECK(kGetterCheckA != kGetterCheckB);
        CHECK(kGetterGetA != kGetterGetB);
        CHECK(kGetterCallers == 42);
    }

    // --- the big-integer family's third member and the tag's second sighting (RE 0xf1580) -----------
    {
        CHECK(kBigIntIsZero == 0xF1580);
        CHECK(kBigIntFamilyMembers == 3);
        CHECK(kBigIntZeroCallers == 44);
        CHECK(kBigIntFirstWordFastPath);
        CHECK(kTagSecondSighting == 1);
        // it uses the same tag field and the same unset value as round 249's comparator
        CHECK(kTagFieldOffset == 0x20);
        CHECK(kTagUnsetValue == 1);
        // and the same layout as the other two members
        CHECK(kBigIntCountOffset == 0x10);
        CHECK(kBigIntWordsOffset == 0x18);
        CHECK(kBigIntWordsOffset - kBigIntCountOffset == 8);

        // the predicate the instructions implement: tagged means "not zero" answers false
        const auto isZero = [](std::uint32_t tag, const std::vector<std::uint64_t>& w) {
            if (static_cast<int>(tag) == kTagUnsetValue) return false;       // RE 0xF1580/0xF15C0
            if (!w.empty() && w[0] != 0) return false;                       // RE 0xF158C
            std::size_t n = w.size();
            while (n > 0 && w[n - 1] == 0) --n;                              // RE 0xF15A0/0xF15A6
            return n == 0;                                                   // RE 0xF15AE
        };
        CHECK(!isZero(1, {}));            // tagged: never "zero"
        CHECK(!isZero(1, {0, 0}));
        CHECK(isZero(0, {}));
        CHECK(isZero(0, {0, 0, 0}));
        CHECK(!isZero(0, {1}));
        CHECK(!isZero(0, {0, 1}));
        CHECK(isZero(2, {0, 0}));         // a tag that is not the unset value behaves like zero-tagged

        CHECK(kExceptionHelper == 0x63F6A8);
        CHECK(kExceptionHelper == kOnceCallee);
        CHECK(kExceptionAlloc == 8);
        CHECK(kExceptionCallers == 36);
    }

    // --- the nested-container destructor and the toolchain exclusion (RE 0x8ce510 and 0xc71d0) ------
    {
        CHECK(kNestedOuterBegin == 0x00);
        CHECK(kNestedOuterEnd == 0x08);
        CHECK(kNestedInnerBegin == 0x18);
        CHECK(kNestedInnerEnd == 0x20);
        CHECK(kInnerStride24 == 0x18);
        CHECK(kOuterStride48 == 0x30);
        CHECK(kInnerStride24 == 24);
        CHECK(kOuterStride48 == 48);
        CHECK(kNestedInnerEnd - kNestedInnerBegin == 8);
        CHECK(kNestedInnerBegin < kOuterStride48);            // the inner pair sits inside the outer element
        CHECK(kNestedOuterEnd - kNestedOuterBegin == 8);
        CHECK(kSharedDealloc == 0x9984B0);
        CHECK(kSharedDealloc == kFormatterRelease);           // rounds 248/252/254 all use it
        CHECK(kSharedDealloc == kReleaseDealloc);
        CHECK(kNestedDestructorCallers == 36);
        CHECK(kSharedDeallocSightings == 3);

        // the toolchain routine carries libstdc++'s own assertion text, so it is not domain code
        CHECK(kStdStringConstruct == 0xC71D0);
        CHECK(kStdStringConstructCallers == 11);
        // CORRECTED in round 254: round 252 called this helper "the text building helper", but the two
        // addresses are the SAME -- the formatter builds a std::string, so its helper IS _M_construct.
        CHECK(kStdStringConstruct == kFormatterTextHelper);
        CHECK(kStdStringConstruct == 0xC71D0);
    }

    // --- the list-block destructor and the allocation path (RE 0xc2510 and 0x998920) ----------------
    {
        CHECK(kListNodeNext == 0x00);
        CHECK(kListNodeBuffer == 0x10);
        CHECK(kListNodeLength == 0x18);
        CHECK(kListHeadOffset == 0x20);
        CHECK(kListNodeBuffer < kListNodeLength);
        CHECK(kListNodeLength < kListHeadOffset);
        CHECK(kListReleaseHelper == 0xFE240);
        CHECK(kListDestructorCallers == 58);
        CHECK(kSharedDeallocSightings2 == 4);
        CHECK(kSharedDeallocSightings == 3);                  // round 254 counted the earlier three
        CHECK(kSharedDealloc == 0x9984B0);

        CHECK(kAlloc8 == 8);
        CHECK(kAllocHelper == 0x9988C0);
        CHECK(kThrowHelper == 0x999030);
        CHECK(kAlloc8Callers == 44);
        CHECK(kHelperSightings == 3);
        CHECK(kAllocHelper != kExceptionHelper);   // the allocator is not the exception helper
        // the allocator and the throw path are the ones rounds 252/253 already recorded
        CHECK(kAllocHelper == 0x9988C0);
        CHECK(kThrowHelper == 0x999030);
    }

    // --- the big-integer copy assignment, the most called function read so far (RE 0xf3460) ---------
    {
        CHECK(kBigIntAssign == 0xF3460);
        CHECK(kBigIntAssignCallers == 162);
        CHECK(kBigIntAlloc == 0x78F740);
        CHECK(kBigIntCopy == 0x63F2F8);
        CHECK(kBigIntCapSixteen == 16);
        CHECK(kBigIntCapThirtyTwo == 32);
        CHECK(kBigIntCapSixtyFour == 64);
        CHECK(kBigIntCapSixteen * 2 == kBigIntCapThirtyTwo);
        CHECK(kBigIntCapThirtyTwo * 2 == kBigIntCapSixtyFour);
        CHECK(kBigIntCapLadderKnown == 3);
        CHECK(kBigIntAssignSelfGuard);
        CHECK(kBigIntSmallBranchUnknown);        // the <= 8 branch was not dumped: not guessed

        // the capacity the instructions choose, for the counts whose thresholds were actually read
        const auto capacity = [](std::uint64_t words) -> std::uint64_t {
            if (words <= 8) return 0;                    // NOT READ: the branch at 0xF3592
            if (words <= kBigIntCapSixteen) return kBigIntCapSixteen;
            if (words <= kBigIntCapThirtyTwo) return kBigIntCapThirtyTwo;
            if (words <= kBigIntCapSixtyFour) return kBigIntCapSixtyFour;
            std::uint64_t cap = 1;                        // RE 0xF354E..0xF3588
            while (cap < words) cap <<= 1;
            return cap;
        };
        CHECK(capacity(9) == 16);
        CHECK(capacity(16) == 16);
        CHECK(capacity(17) == 32);
        CHECK(capacity(32) == 32);
        CHECK(capacity(33) == 64);
        CHECK(capacity(64) == 64);
        CHECK(capacity(65) == 128);                       // the next power of two
        CHECK(capacity(129) == 256);
        // and the copy is always count * 8 bytes
        CHECK(kBigIntCapSixteen * 8 == 128);
        CHECK(kBigIntAssignCallers > kAccessorCallers);
    }

    // --- the reset routine and the two cross-links it settles (RE 0x87d8e0) -------------------------
    {
        CHECK(kResetEntry == 0x87D8E0);
        CHECK(kResetCallers == 53);
        CHECK(kResetPredicate == 0x822590);
        CHECK(kResetSubCall == 0x87D270);
        CHECK(kResetSubCallB == 0x87D4E0);
        CHECK(kResetEmbedded == 0x48);
        CHECK(kResetTripleA == 0x08);
        CHECK(kResetTripleB == 0x10);
        CHECK(kResetTripleC == 0x18);
        CHECK(kResetTripleB - kResetTripleA == 8);
        CHECK(kResetTripleC - kResetTripleB == 8);
        CHECK(kResetZeroA == 0x20);
        CHECK(kResetZeroB == 0x28);
        CHECK(kResetZeroC == 0x30);
        CHECK(kResetSource == 0x5C);
        CHECK(kResetCopyA == 0x60);
        CHECK(kResetCopyB == 0x64);
        CHECK(kResetCopyB - kResetCopyA == 4);
        CHECK(kResetByteA == 0x79);
        CHECK(kResetByteB == 0x7A);
        CHECK(kResetByteB - kResetByteA == 1);

        // cross-link 1: this routine clears the very flags round 226 recorded on the 0x98-byte object
        CHECK(kCtor098FlagA == 0x58);
        CHECK(kCtor098FlagB == 0x90);
        // cross-link 2: it calls the target of round 248's five-byte thunk directly
        CHECK(kThunkTarget == 0x8771C0);
        CHECK(kResetEntry != kThunkTarget);
    }

    // --- the non-null predicate and the polymorphic status query (RE 0x822590 and 0x87d270) ---------
    {
        CHECK(kNonNullPredicate == 0x822590);
        CHECK(kNonNullFieldOffset == 0x00);
        CHECK(kNonNullCallers == 36);
        // an eight-byte function that is exactly "the field is not null"
        const auto nonNull = [](const void* p) { return p != nullptr; };
        CHECK(!nonNull(nullptr));
        CHECK(nonNull(reinterpret_cast<const void*>(1)));
        CHECK(nonNull(static_cast<const void*>(&kNonNullCallers)));

        CHECK(kStatusQuery == 0x87D270);
        CHECK(kInterfaceOffset == 0x98);
        CHECK(kVtableSlotA == 0x18);
        CHECK(kVtableSlotB == 0x30);
        CHECK(kVtableSlotC == 0x68);
        CHECK(kStatusSentinel == -1);
        CHECK(kStatusOne == 1);
        CHECK(kStatusTwo == 2);
        CHECK(kVtableSlotC - kVtableSlotB == 0x38);
        CHECK(kVtableSlotB - kVtableSlotA == 0x18);
        CHECK(kStatusHelper == 0x8772A0);
        CHECK(kStatusCountA == 0x20);
        CHECK(kStatusCountB == 0x28);
        CHECK(kStatusCountB - kStatusCountA == 8);
        CHECK(kStatusFlag == 0x7A);
        // the flag the query reads is the very byte round 258's reset clears
        CHECK(kStatusFlag == kResetByteB);

        // the answer the instructions compute: "not the sentinel"
        const auto answered = [](std::int32_t code) { return code != kStatusSentinel; };
        CHECK(!answered(-1));
        CHECK(answered(0));
        CHECK(answered(1));
        CHECK(answered(2));
    }

    // --- the buffer releaser and the trampoline (RE 0x87d4e0 and 0x8772a0) --------------------------
    {
        CHECK(kByteTrioA == 0x78);
        CHECK(kOptionalBuffer == 0x68);
        CHECK(kSecondBuffer == 0xA0);
        CHECK(kBlockA0 == 0xA0);
        CHECK(kBlockA0End == 0xB8);
        CHECK(kBlockA0Qwords == 4);
        CHECK(kBlockA0End - kBlockA0 == (kBlockA0Qwords - 1) * 8);
        CHECK(kBlockA0End - kBlockA0 == 24);
        CHECK(kReleaserAlt == 0x9984A0);
        CHECK(kReleaserCallers == 2);
        // the second releaser is NOT the widely shared one
        CHECK(kReleaserAlt != kSharedDealloc);
        CHECK(kSharedDealloc == 0x9984B0);
        // cross-link: this routine uses the FIRST byte of the trio whose other two round 258 clears
        CHECK(kByteTrioA + 1 == kResetByteA);
        CHECK(kByteTrioA + 2 == kResetByteB);
        CHECK(kResetByteB == kStatusFlag);
        CHECK(kOptionalBuffer < kByteTrioA);

        CHECK(kTrampoline == 0x8772A0);
        CHECK(kTrampolineInner == 0x877120);
        CHECK(kTrampolineTarget == 0x65C940);
        CHECK(kTrampolineCallers == 4);
        CHECK(kTrampoline != kTrampolineInner);
        CHECK(kTrampoline != kTrampolineTarget);
    }

    // --- the object destructor and the intrusive assignment (RE 0x87f2a0 and 0x8aabf0) --------------
    {
        CHECK(kObjectDestructor == 0x87F2A0);
        CHECK(kObjectVtableRva == 0x1D6394);
        CHECK(kSubObjectA == 0x48);
        CHECK(kSubObjectB == 0x38);
        CHECK(kSubObjectA == kResetEmbedded);          // the same sub-object the reset works through
        CHECK(kSubObjectTailCall == 0x8AABC0);
        CHECK(kObjectDestructorCallers == 35);
        // it calls the round-258 reset and the round-248 thunk, which is the corroboration
        CHECK(kResetEntry == 0x87D8E0);
        CHECK(kThunkTarget == 0x8771C0);

        CHECK(kIntrusiveAssign == 0x8AABF0);
        CHECK(kCounterOffsetHere == 0x00);
        CHECK(kIntrusiveReleaseHelper == 0x8AA690);
        CHECK(kIntrusiveAssignCallers == 35);
        CHECK(kSharedDeallocSightings3 == 5);
        CHECK(kCounterOffsetsDiffer);
        // the two counters really are at different offsets: observed, not reconciled
        CHECK(kCounterOffsetHere != kReleaseCounterOffset);
        CHECK(kReleaseCounterOffset == 0x10);

        // the assignment as the instructions perform it: increment the new, decrement the old, release at zero
        const auto assign = [](int& oldCount, int& newCount, bool& released) {
            ++newCount;                                 // RE 0x8AABFB
            released = (--oldCount == 0);               // RE 0x8AAC02/0x8AAC06
            return true;
        };
        int oldCount = 1, newCount = 0; bool released = false;
        assign(oldCount, newCount, released);
        CHECK(oldCount == 0);
        CHECK(newCount == 1);
        CHECK(released);                                // the outgoing counter reached zero
        int oldCount2 = 3, newCount2 = 0; bool released2 = false;
        assign(oldCount2, newCount2, released2);
        CHECK(oldCount2 == 2);
        CHECK(!released2);
    }

    // --- the two-byte string path and the C-string constructor (RE 0x9118c0 and 0x20c080) -----------
    {
        CHECK(kWideInsert == 0x9118C0);
        CHECK(kMaxSizeWide == 0x3FFFFFFFFFFFFFFFULL);
        CHECK(kMaxSizeWide == (1ULL << 62) - 1);
        CHECK(kWideCharBytes == 2);
        CHECK(kWideData == 0x00);
        CHECK(kWideSize == 0x08);
        CHECK(kWideCapacity == 0x10);
        CHECK(kWideSize - kWideData == 8);
        CHECK(kWideCapacity - kWideSize == 8);
        CHECK(kMemcpyHelper == 0x63F2F8);
        CHECK(kWideInsertCallers == 49);
        CHECK(kWideTerminator);
        // the copier is the one the big-integer assignment uses: one helper, several types
        CHECK(kMemcpyHelper == kBigIntCopy);
        // max_size for two-byte elements: the largest count whose byte length fits a signed 64-bit value
        CHECK(kMaxSizeWide == static_cast<std::uint64_t>((std::numeric_limits<std::int64_t>::max)()) / 2);

        CHECK(kFromCString == 0x20C080);
        CHECK(kSsoInline == 0x10);
        CHECK(kSsoInline == kWideCapacity);
        CHECK(kFromCStringTail == 0x20BFC0);
        CHECK(kFromCStringCallers == 32);
        // it calls the length helper round 251 landed
        CHECK(kLengthHelper == 0x63F238);

        // the addressing scales by two, which is what the lea forms do
        for (std::uint64_t i = 0; i < 4; ++i) {
            CHECK(i * kWideCharBytes == i * 2);
        }
        CHECK(kWideCharBytes * 8 == 16);
    }

    // --- the tag dispatch and the constructor that corrects two figures (RE 0xf49e0, 0x87edf0) -------
    {
        CHECK(kTagDispatch == 0xF49E0);
        CHECK(kTagDispatchCore == 0xF17C0);
        CHECK(kTagDispatchA == 0xF4830);
        CHECK(kTagDispatchB == 0xF1B20);
        CHECK(kTagDispatchCallers == 34);
        CHECK(kBigIntFamilyMembers3 == 4);
        CHECK(kTagSightings == 5);
        // the tag field and its unset value are the ones rounds 249/253 landed
        CHECK(kTagFieldOffset == 0x20);
        CHECK(kTagUnsetValue == 1);
        // the dispatch takes the larger word count first, as cmovae does
        const auto larger = [](std::uint64_t a, std::uint64_t b) { return a >= b ? a : b; };
        CHECK(larger(3, 5) == 5);
        CHECK(larger(5, 3) == 5);
        CHECK(larger(4, 4) == 4);

        CHECK(kObjectCtor == 0x87EDF0);
        CHECK(kObjectCtorVtableRva == 0x1D67ED);
        CHECK(kObjectCtorThunk == 0x8774E0);
        CHECK(kObjectCtorHelper == 0x8AAB00);
        CHECK(kObjectCtorCallers == 35);
        // CORRECTION: the byte group is a QUARTET, not the trio round 260 recorded
        CHECK(kByteQuartetA == 0x78);
        CHECK(kByteQuartetB == 0x79);
        CHECK(kByteQuartetC == 0x7A);
        CHECK(kByteQuartetD == 0x7B);
        CHECK(kByteQuartetD - kByteQuartetA == 3);
        CHECK(kByteQuartetA == kByteTrioA);
        CHECK(kByteQuartetC == kResetByteB);          // round 258's bytes are the middle two
        CHECK(kByteQuartetD == kStatusFlag + 1);
        // and the object starts with a capacity of 512
        CHECK(kInitialCapacity == 0x200);
        CHECK(kInitialCapacity == 512);
        CHECK(kInitialCapacity == kDequeBlockSize);   // the same value as round 218's block size
        CHECK(kObjectCtorThunk != kThunkCallers);     // the thunk is 0x8774E0, not the caller count
        CHECK(kObjectCtorThunk != 0x8774F0);          // and it is a DIFFERENT thunk from round 248's
    }

    // --- the ladder's second member and the refcount initialiser (RE 0xf17c0 and 0x8aab00) ----------
    {
        CHECK(kLadderSecondMember == 0xF17C0);
        CHECK(kLadderLowerBranch == 0xF1940);
        CHECK(kLadderLowerBranch != kBigIntCapSixteen);   // an address, not the capacity 16
        CHECK(kWordAllocator == 0xFE1F0);
        CHECK(kZeroFillHelper == 0x63F2E8);
        CHECK(kZeroFillHelper != kMemcpyHelper);          // a fill is not the copier
        CHECK(kImpossibleCaseTraps);
        CHECK(kLadderSecondCallers == 17);
        // both members use the same sixteen threshold, and the allocator is round 249's
        CHECK(kBigIntCapSixteen == 0x10);
        CHECK(kWordAllocator == kPayloadAlloc);
        // the allocation is capacity words, eight bytes each
        CHECK(kBigIntCapSixteen * 8 == 128);

        CHECK(kRefcountInit == 0x8AAB00);
        CHECK(kRefcountInitHelper == 0x8A81C0);
        CHECK(kRefcountOnceA == 0x63F6C0);
        CHECK(kRefcountOnceB == 0x63F6B8);
        CHECK(kRefcountOnceA != kRefcountOnceB);
        CHECK(kRefcountClock == 0x65C4C0);
        CHECK(kRefcountInitCallers == 132);
        CHECK(kRefcountInitAtomic);
        // the once-check pair is the one round 253's exception plumbing used
        CHECK(kRefcountOnceA == 0x63F6C0);
        // and this is the second most called function read so far
        CHECK(kRefcountInitCallers < kBigIntAssignCallers);
        CHECK(kRefcountInitCallers > kAccessorCallers);
    }

    // --- the even-rounded word count and the per-limb kernel (RE 0xf1b20 and 0xf4830) ----------------
    {
        CHECK(kBigIntRoundMask == 0xFFFFFFFEu);
        CHECK(kBigIntRoundMask == 0xFFFFFFFFu - 1u);
        CHECK(kBigIntGrowStep == 1);
        CHECK(kBigIntDispatchBranch == 0xF1B20);
        CHECK(kBigIntDispatchBranchCallers == 4);
        CHECK(!kOperationIdentityOpen);                 // corrected in round 266: it IS identified
        // the arithmetic the instructions do, for the first few counts
        const auto rounded = [](std::uint32_t n) { return (n + kBigIntGrowStep) & kBigIntRoundMask; };
        CHECK(rounded(0) == 0);
        CHECK(rounded(1) == 2);
        CHECK(rounded(2) == 2);
        CHECK(rounded(3) == 4);
        CHECK(rounded(4) == 4);
        CHECK(rounded(5) == 6);
        for (std::uint32_t n = 0; n < 16; ++n) {
            CHECK(rounded(n) % 2 == 0);                 // always even
            CHECK(rounded(n) >= n);                     // never smaller than the count
        }

        CHECK(kLimbRoutine == 0xF4830);
        CHECK(kLimbKernel == 0xEF280);
        CHECK(kLimbRoutineCallers == 4);
        CHECK(kLimbCountCases == 3);
        // the tail copy is the memcpy the assignment and the wide-string path also use
        CHECK(kMemcpyHelper == 0x63F2F8);

        CHECK(kRegistryGuard == 0x8A81C0);
        CHECK(kRegistryInit == 0x8A9510);
        CHECK(kRegistryKind == 2);
        CHECK(kOnceHelperSightings == 3);
        CHECK(kOnceCallee == 0x63F6A8);                 // the once helper round 248 landed
    }

    // --- the kernel is addition, so the identity is settled (RE 0xef280) ---------------------------
    {
        CHECK(kLimbAdd == 0xEF280);
        CHECK(kAddIsAddition);
        CHECK(kLimbsPerIteration == 2);
        CHECK(kLimbAddCallers == 17);
        CHECK(kAdditionSite == kTagDispatch);           // the operation of rounds 263/265
        CHECK(!kOperationIdentityOpen);                 // the round-265 open question is closed

        // the carry propagation the instructions implement, limb by limb
        const auto addWithCarry = [](const std::vector<std::uint64_t>& a,
                                     const std::vector<std::uint64_t>& b) {
            std::vector<std::uint64_t> out(a.size(), 0);
            std::uint64_t carry = 0;                  // the incoming carry, held in rsi
            for (std::size_t i = 0; i < a.size(); ++i) {
                const std::uint64_t first = a[i] + b[i];        // RE 0xEF296
                const bool carried = first < a[i];              // RE 0xEF29A (jb)
                const std::uint64_t second = first + carry;     // RE 0xEF29C
                const bool carriedAgain = second < first;       // RE 0xEF2A8 (setb)
                out[i] = second;
                carry = (carried || carriedAgain) ? 1u : 0u;    // RE the carry chain
            }
            return out;
        };
        const auto r1 = addWithCarry({1, 2}, {3, 4});
        CHECK(r1[0] == 4);
        CHECK(r1[1] == 6);
        // a carry out of the low limb is folded into the next one
        const auto r2 = addWithCarry({~0ULL, 0}, {1, 0});
        CHECK(r2[0] == 0);
        CHECK(r2[1] == 1);
        const auto r3 = addWithCarry({~0ULL, ~0ULL}, {1, 0});
        CHECK(r3[0] == 0);
        CHECK(r3[1] == 0);
        CHECK(kLimbsPerIteration * 8 == 16);             // two limbs per iteration is sixteen bytes

        CHECK(kRegistryInitRoutine == 0x8A9510);
        CHECK(kRegistryKindField == 0x00);
        CHECK(kRegistryCountField == 0x10);
        CHECK(kRegistryCountValue == 0x2E);
        CHECK(kRegistryCountValue == 46);
        CHECK(kRegistryArrayA == 0x08);
        CHECK(kRegistryArrayB == 0x18);
        CHECK(kRegistryArrayB - kRegistryArrayA == 0x10);
        CHECK(kRegistryInitCallers == 2);
    }

    // --- addition confirmed twice, and the comparison path's kernel (RE 0xf4830 and 0xf1b20) ---------
    {
        CHECK(kAddRoutine == 0xF4830);
        CHECK(kAddClearsTag);
        CHECK(kCarryIntoTail);
        CHECK(kAddRoutineCallers == 4);
        CHECK(kAdditionConfirmations == 2);
        CHECK(kLimbAdd == 0xEF280);                     // the kernel the routine calls
        CHECK(kTagUnsetValue == 1);                     // and the tag it clears is the "unset" one

        // the carry into the tail that the routine performs
        const auto foldCarry = [](std::uint64_t& limb, std::uint64_t carry) {
            const std::uint64_t before = limb;
            limb = before + carry;                      // RE 0xF48AA
            return limb < before;                       // RE 0xF48AD (setb)
        };
        std::uint64_t limb = 5;
        CHECK(!foldCarry(limb, 1));
        CHECK(limb == 6);
        limb = ~0ULL;
        CHECK(foldCarry(limb, 1));                      // it carries again
        CHECK(limb == 0);

        CHECK(kCompareKernel == 0xEF300);
        CHECK(kReverseLimbCompare);
        CHECK(kComparePathCallers == 4);
        CHECK(!kSignResultOpen);    // settled in round 269: the routine subtracts, it is not a sign                         // the sign result is NOT claimed
        // the two kernels are different addresses
        CHECK(kCompareKernel != kLimbAdd);
        CHECK(kCompareKernel != kWordAllocator);

        // the descending scan the comparison path performs, limb by limb from the top
        const auto compareFromTop = [](const std::vector<std::uint64_t>& a,
                                       const std::vector<std::uint64_t>& b) {
            for (std::size_t i = a.size(); i-- > 0;) {  // RE 0xF1B86
                if (a[i] != b[i]) return a[i] < b[i];   // RE 0xF1B98 (jbe continues the scan)
            }
            return false;
        };
        CHECK(compareFromTop({1, 2}, {1, 2}) == false);
        CHECK(compareFromTop({1, 2}, {1, 3}) == true);
        // CORRECTED in round 267: I had these two backwards. The TOP limb is index 1, so {9,1} against {1,2}
        // compares 1 with 2 -- less, hence true -- and {1,1} against {9,0} compares 1 with 0, hence false.
        CHECK(compareFromTop({9, 1}, {1, 2}) == true);   // 1 < 2 at the top
        CHECK(compareFromTop({1, 1}, {9, 0}) == false);  // 1 is not < 0 at the top
    }

    // --- the subtraction kernel, the mirror of the addition (RE 0xef300) ---------------------------
    {
        CHECK(kLimbSub == 0xEF300);
        CHECK(kSubIsSubtraction);
        CHECK(kLimbSubCallers == 14);
        CHECK(kKernelPair == 2);
        CHECK(kLimbSubBytes == 111);
        CHECK(kLimbAddBytes == 114);
        CHECK(kLimbSubBytes < kLimbAddBytes);
        CHECK(kComparisonUsesSubtraction);
        CHECK(!kSignResultOpen);                        // settled in round 269: it subtracts
        CHECK(kKernelAdd == kLimbAdd);
        CHECK(kKernelSub == kCompareKernel);
        CHECK(kKernelAdd != kKernelSub);

        // the borrow propagation the instructions perform, limb by limb
        const auto subWithBorrow = [](const std::vector<std::uint64_t>& a,
                                      const std::vector<std::uint64_t>& b) {
            std::vector<std::uint64_t> out(a.size(), 0);
            std::uint64_t borrow = 0;                   // the incoming borrow
            for (std::size_t i = 0; i < a.size(); ++i) {
                const std::uint64_t first = a[i] - b[i];        // RE 0xEF319
                const bool borrowed = a[i] < b[i];              // RE 0xEF320 (setb)
                const std::uint64_t second = first - borrow;    // RE 0xEF324
                const bool borrowedAgain = first < borrow;      // RE 0xEF330 (setb)
                out[i] = second;
                borrow = (borrowed || borrowedAgain) ? 1u : 0u; // RE the borrow chain
            }
            return out;
        };
        const auto d1 = subWithBorrow({5, 5}, {1, 2});
        CHECK(d1[0] == 4);
        CHECK(d1[1] == 3);
        // borrowing out of the low limb
        const auto d2 = subWithBorrow({0, 1}, {1, 0});
        CHECK(d2[0] == ~0ULL);
        CHECK(d2[1] == 0);
        // subtracting a number from itself gives zero
        const auto d3 = subWithBorrow({7, 7}, {7, 7});
        CHECK(d3[0] == 0);
        CHECK(d3[1] == 0);
        // and the addition kernel's carry chain is the same shape, reversed
        CHECK(kLimbsPerIteration == 2);
    }

    // --- the subtraction routine and the answered sign question (RE 0xf1b20) -----------------------
    {
        CHECK(kSubRoutine == 0xF1B20);
        CHECK(kBorrowIntoTail);
        CHECK(kSubClearsTag);
        CHECK(kSubRoutineCallers == 4);
        CHECK(kSubtractionSites == 2);
        CHECK(kAdditionSites == 2);
        CHECK(kAdditionSites == kSubtractionSites);
        CHECK(!kSignResultOpen);                        // it is a subtraction, not a sign
        CHECK(kOrderingScanInferred);                   // the scan's purpose is an inference, and says so
        CHECK(kLimbSub == 0xEF300);                     // the kernel it calls
        CHECK(kAddClearsTag);                           // both operations clear the tag
        CHECK(kSubClearsTag);

        // folding the borrow into the top limb, as the routine does
        const auto foldBorrow = [](std::uint64_t& top, std::uint64_t borrow) {
            const std::uint64_t before = top;
            top = before - borrow;                      // RE 0xF1CA2
            return top > before;                        // a wrap, i.e. the borrow was not absorbed
        };
        std::uint64_t top = 5;
        CHECK(!foldBorrow(top, 1));
        CHECK(top == 4);
        top = 0;
        CHECK(foldBorrow(top, 1));                      // it wraps
        CHECK(top == ~0ULL);
        top = 7;
        CHECK(!foldBorrow(top, 0));
        CHECK(top == 7);
    }

    // --- the close retry and the corrected "thunk" (RE 0x8771c0 and 0x8774e0) ----------------------
    {
        CHECK(kCloseHelper == 0x8771C0);
        CHECK(kCloseRetryCode == 4);
        CHECK(kCloseCallee == 0x63F3E0);
        CHECK(kCloseHandle == 0x00);
        CHECK(kCloseFlag == 0x08);
        CHECK(kCloseCallers == 3);
        CHECK(kCloseUsesGlobalCallback);
        CHECK(kCloseRetries);

        CHECK(kClearPair == 0x8774E0);
        CHECK(kClearPairQword == 0x00);
        CHECK(kClearPairByte == 0x08);
        CHECK(kClearPairBytes == 12);
        CHECK(kClearPairCallers == 4);
        CHECK(kClearPairNotThunk);                      // round 263 called it a thunk: corrected
        CHECK(kClearPairBytes != 5);                    // a thunk is five bytes; this is not one
        // cross-link: the byte it clears is the flag the close helper reads
        CHECK(kClearPairByte == kCloseFlag);
        CHECK(kClearPairQword == kCloseHandle);
        // and it is NOT the round-248 thunk, whose target is elsewhere
        CHECK(kClearPair != kThunkTarget);
        CHECK(kObjectCtorThunk == kClearPair);          // the address recorded in round 263 was right

        // the retry loop the close performs, on the code the instructions compare against
        const auto shouldRetry = [](std::int32_t errorCode) { return errorCode == kCloseRetryCode; };
        CHECK(shouldRetry(4));
        CHECK(!shouldRetry(0));
        CHECK(!shouldRetry(5));
    }

    // --- the thirty-two byte vector growth (RE 0x8f1e20) -------------------------------------------
    {
        CHECK(kVector32 == 0x8F1E20);
        CHECK(kElement32Shift == 5);
        CHECK(kElement32 == 0x20);
        CHECK(kElement32 == 32);
        CHECK((1u << kElement32Shift) == kElement32);
        CHECK(kMaxSizeVec32 == 0x7FFFFFFFFFFFFFFULL);
        CHECK(kVectorFailure == static_cast<std::uint64_t>(-32));
        CHECK(kVectorMinCapacity == 0x20);
        CHECK(kVectorAlloc == 0x998500);
        CHECK(kVector32Callers == 27);
        CHECK(kVectorGrowsByDoubling);

        // the capacity the routine computes: double, with the minimum and the guard applied
        const auto grow = [](std::uint64_t bytes) -> std::uint64_t {
            std::uint64_t capacity = bytes >> kElement32Shift;   // RE 0x8F1E42
            if (capacity == 0) return kVectorMinCapacity;        // RE 0x8F1E70
            capacity += capacity;                                // RE 0x8F1E4B
            if (capacity > kMaxSizeVec32) return kVectorFailure; // RE 0x8F1E5D
            return capacity;
        };
        CHECK(grow(0) == 32);
        CHECK(grow(32) == 2);            // one element becomes two
        CHECK(grow(64) == 4);
        CHECK(grow(96) == 6);
        CHECK(grow(1) == 32);            // less than one element falls back to the minimum
        CHECK(grow(kMaxSizeVec32 * kElement32) == kVectorFailure);
        // the failure value is minus the element size, as the movabs shows
        CHECK(static_cast<std::int64_t>(kVectorFailure) == -32);
    }

    // --- the import-thunk block and the forwarder through it (RE 0x63f3e0 and 0x877120) -------------
    {
        CHECK(kImportThunkBlock == 0x63F3E0);
        CHECK(kImportThunkStride == 8);
        CHECK(kImportThunkStride == 0x63F3E8 - 0x63F3E0);
        CHECK(kImportStubClose == 0x63F3E0);            // the FIRST stub, which the close reaches
        CHECK(kImportStubClose == kImportThunkBlock);   // the close's stub is the block's first entry
        CHECK(kImportStubForwarder - kImportThunkBlock == 0xD8);   // the forwarder's is 0xD8 in
        CHECK(kCloseCalleeIsImport);                    // round 270's callee is an import stub
        CHECK(kImportStubsAreNotDomain);                // so it must not count as domain work
        CHECK(kCloseCallee == kImportStubClose);        // and it is the address round 270 recorded

        CHECK(kForwarder == 0x877120);
        CHECK(kForwarderDeref == 0x00);
        CHECK(kForwarderCallee == 0x63F4B8);
        CHECK(kForwarderCalleeIsImportStub);
        CHECK(kForwarderDeref == 0);                    // the object's FIRST field, dereferenced
        CHECK(kForwarderCallers == 7);
        CHECK(kForwarderFailureA == 0x62F280);
        CHECK(kForwarderFailureB == 0x998A60);
        // the two sites are DIFFERENT: I had conflated them, and the gate caught the false equality
        CHECK(kForwarderCallee != kCloseCallee);
        CHECK(kForwarderCallee == kImportStubForwarder);
        CHECK(kCloseCallee == kImportStubClose);
        // and the trampoline of round 260 routes here
        CHECK(kTrampolineInner == kForwarder);
    }

    // --- the string replace/insert path (RE 0x910c20) -----------------------------------------------
    {
        CHECK(kStringReplace == 0x910C20);
        CHECK(kStringAllocHelper == 0x910BA0);
        CHECK(kReplaceCopySites == 3);
        CHECK(kSsoCheckOffset == 0x10);
        CHECK(kSsoCheckOffset == kWideCapacity);
        CHECK(kReplaceData == 0x00);
        CHECK(kReplaceSize == 0x08);
        CHECK(kStringReplaceCallers == 43);
        CHECK(kSsoComparedByAddress);
        CHECK(kSharedDeallocSightings4 == 6);
        CHECK(kSharedDeallocSightings4 > kSharedDeallocSightings2);
        // the three copies use the memcpy helper the other paths use
        CHECK(kMemcpyHelper == 0x63F2F8);
        CHECK(kSharedDealloc == 0x9984B0);

        // the tail length the routine computes, and the size it ends with
        const auto tailLength = [](std::int64_t size, std::int64_t pos, std::int64_t count) {
            return size - pos - count;                  // RE 0x910C52/0x910C58/0x910C60
        };
        CHECK(tailLength(10, 3, 4) == 3);
        CHECK(tailLength(10, 0, 0) == 10);
        CHECK(tailLength(10, 10, 0) == 0);
        CHECK(tailLength(5, 5, 0) == 0);
        const auto newSize = [](std::int64_t size, std::int64_t count, std::int64_t added) {
            return size - count + added;                // the size the replacement produces
        };
        CHECK(newSize(10, 4, 7) == 13);
        CHECK(newSize(10, 0, 0) == 10);
        // the SSO branch is taken when the data pointer still points at the inline buffer
        const auto usesInline = [](const void* data, const void* inlineBuf) { return data == inlineBuf; };
        const char buf[32] = {};
        CHECK(usesInline(buf, buf));
        CHECK(!usesInline(buf + 1, buf));
    }

    // --- the deallocator alias, the forwarder and the two string constructors (RE 0x86a2b0..0xd0670) -
    {
        CHECK(kDeallocAlias == 0x86A2B0);
        CHECK(kDeallocAlias != kSharedDealloc);
        CHECK(kAliasCallers == 27);
        CHECK(kDeallocEntryPoints == 2);
        CHECK(kSharedDealloc == 0x9984B0);
        CHECK(kForwarderF0F00 == 0xF1550);
        CHECK(kForwardTarget == 0xF0F00);
        CHECK(kForwardCallers == 26);
        CHECK(kForwarderF0F00 != kForwardTarget);

        CHECK(kStringViewCtor == 0x7B1F20);
        CHECK(kStringViewVtableRva == 0x2A0DC3);
        CHECK(kStringViewKind == 0x08);
        CHECK(kStringViewObject == 0x10);
        CHECK(kStringViewInline == 0x20);
        CHECK(kStringViewInline > kStringViewObject);
        CHECK(kStringViewCallers == 26);
        CHECK(kStringViewUsesMConstruct);
        // it builds through the routine round 254 identified as std::string's _M_construct
        CHECK(kStringViewUsesMConstruct && kStdStringConstruct == 0xC71D0);

        CHECK(kFromCString2 == 0xD0670);
        CHECK(kFromCString2Callers == 24);
        CHECK(kLengthHelperSightings == 3);
        CHECK(kFromCStringSites == 2);
        CHECK(kFromCString2 != kFromCString);
        CHECK(kLengthHelper == 0x63F238);
        // the two C-string sites share the length helper and the inline-buffer offset
        CHECK(kFromCStringSites == 2 && kSsoInline == 0x10);
    }

    // --- the alias map and the deallocator's real scale (RE the round-277 sweep) --------------------
    {
        CHECK(kDeallocTarget == 0x9984B0);
        CHECK(kDeallocTarget == kSharedDealloc);
        CHECK(kDeallocCallers == 5721);
        CHECK(kDeallocAliasCount == 34);
        CHECK(kDeallocCallers > kBigIntAssignCallers);      // far more called than the copy assignment
        CHECK(kDeallocCallers > kAccessorCallers);
        CHECK(kTinyAliasCount == 39);
        CHECK(kTinyAliasTargets == 6);
        CHECK(kDeallocAliasCount < kTinyAliasCount);        // most aliases, but not all of them
        CHECK(kAliasTarget991F20 == 0x991F20);
        CHECK(kAliasTarget991F20Callers == 10);
        CHECK(kAliasTarget998CB0 == 0x998CB0);
        CHECK(kAliasTarget5860 == 0x5860);
        // the three alias targets are distinct from each other and from the deallocator
        CHECK(kAliasTarget991F20 != kAliasTarget998CB0);
        CHECK(kAliasTarget998CB0 != kAliasTarget5860);
        CHECK(kAliasTarget5860 != kDeallocTarget);
        CHECK(kDeallocEntryPoints2 == 36);
        CHECK(kDeallocAliasCount + 2 == kDeallocEntryPoints2);   // the routine plus its aliases
    }

    // --- the two structural micro-classes (RE the round-278 sweep) ---------------------------------
    {
        CHECK(kAccessorClassCount == 12);
        CHECK(kAccessorClassTopOffsets == 9);
        CHECK(kDefaultStubClassCount == 0);
        CHECK(kAccessorAddressesUnlanded);              // left out on purpose, see the comment
        CHECK(kAccessorClassCount > 0);
        CHECK(kDefaultStubClassCount >= 0);
        // the default stub encoding round 223 identified
        CHECK(kDefaultStubEncoding == 0x9090909090C3C031ULL);
        CHECK(kDefaultStubGap == 0x10);
    }

    // --- the second nested teardown and the two sweeps (RE 0x687480) --------------------------------
    {
        CHECK(kNested2Buffer == 0x00);
        CHECK(kNested2Begin == 0x18);
        CHECK(kNested2End == 0x20);
        CHECK(kNested2End - kNested2Begin == 8);
        CHECK(kNested2InnerStride == 0x18);
        CHECK(kNested2InnerStride == kInnerStride24);       // the same inner stride as round 254
        CHECK(kNested2Callers == 25);
        CHECK(kNested2FreeSites == 3);
        CHECK(kNested2FreeSites == 3 && kSharedDealloc == 0x9984B0);
        // the offsets coincide with round 254's INNER pair, which is a different level of the shape
        CHECK(kNested2Begin == kNestedInnerBegin);
        CHECK(kNested2End == kNestedInnerEnd);
        // but round 254's OUTER pair is elsewhere, so the two layouts are not the same
        CHECK(kNestedOuterBegin != kNested2Begin);
        CHECK(kNestedOuterEnd != kNested2End);

        CHECK(kSetterClassCount == 0);
        CHECK(kSetterClassEmpty);                           // zero, reported as zero
        CHECK(kMultiGetterCount == 11);
        CHECK(kMultiGetterOffsets == 8);
        CHECK(kMultiGetterCount < kAccessorClassCount + 11);  // consistent with the round-278 sweep
        CHECK(kAccessorAddressesUnlanded);                  // these stay unlanded too
    }

    // --- the get-or-create accessor and the BER-linked finaliser (RE 0x799f60 and 0x10f770) ---------
    {
        CHECK(kGetOrCreate == 0x799F60);
        CHECK(kGetOrCreateVtableRva == 0x2B1FB2);
        CHECK(kGetOrCreateFlagA == 0x10);
        CHECK(kGetOrCreateFlagB == 0x11);
        CHECK(kGetOrCreateFlagB - kGetOrCreateFlagA == 1);
        CHECK(kGetOrCreateSource == 0x08);
        CHECK(kGetOrCreateInterface == 0x18);
        CHECK(kGetOrCreateCtor == 0x799BA0);
        CHECK(kGetOrCreateBytes == 0x30);
        CHECK(kGetOrCreateBytes == 48);
        CHECK(kGetOrCreateCallers == 27);
        CHECK(kVtableSlotD == 0x08);
        CHECK(kVtableSlotD < kVtableSlotA);            // a fourth, lower slot

        CHECK(kFinaliseWithRetry == 0x10F770);
        CHECK(kBerErrorFormatter == 0x77F2D0);
        CHECK(kBerDecoderSite == kFinaliseWithRetry);
        CHECK(kStatusCall == 0x11A780);
        CHECK(kFinaliseFlagA == 0x28);
        CHECK(kFinaliseFlagB == 0x29);
        CHECK(kFinaliseFlagB - kFinaliseFlagA == 1);
        CHECK(kFinalisePointer == 0x30);
        CHECK(kStatusExpected == 2);
        CHECK(kFinaliseCallers == 24);
        CHECK(kRetriesOnNonZeroWord);
        // the domain link: the formatter this routine reports through is the one carrying the BER text
        CHECK(std::string(kTagBerDecodeError) == "BER decode error");
        CHECK(kBerErrorFormatter != kStringReplace);
        CHECK(kBerErrorFormatter != kGetOrCreate);
    }

    // --- the BER length reader and the four-byte vector (RE 0x11a780 and 0x90d6b0) ------------------
    {
        CHECK(kBerLengthReader == 0x11A780);
        CHECK(kBerVtableSlotA == 0xB8);
        CHECK(kBerVtableSlotB == 0xC0);
        CHECK(kBerVtableSlotB - kBerVtableSlotA == 8);
        CHECK(kBerLengthCallers == 9);
        CHECK(kBigEndian16);
        CHECK(kBerSlotKindArgument == 2);
        CHECK(kTypeLiteralSite == 0x11A7DF);
        CHECK(kVtableSlotsKnown == 6);
        // the six slots now known, in ascending order
        CHECK(kVtableSlotD == 0x08 && kVtableSlotA == 0x18 && kVtableSlotB == 0x30);
        CHECK(kVtableSlotC == 0x68 && kBerVtableSlotA == 0xB8 && kBerVtableSlotB == 0xC0);
        // the big-endian assembly the instructions perform
        const auto bigEndian16 = [](std::uint8_t low, std::uint8_t high) {
            return static_cast<std::uint16_t>((static_cast<std::uint16_t>(high) << 8) |
                                              static_cast<std::uint16_t>(low));
        };
        CHECK(bigEndian16(0x34, 0x12) == 0x1234);
        CHECK(bigEndian16(0x00, 0x01) == 0x0100);
        CHECK(bigEndian16(0xFF, 0x00) == 0x00FF);
        CHECK(bigEndian16(0x34, 0x12) != 0x3412);      // it is big-endian, not little

        CHECK(kVector4 == 0x90D6B0);
        CHECK(kVector4 != kVector32);
        CHECK(kElement4Shift == 2);
        CHECK(kElement4 == 4);
        CHECK((1u << kElement4Shift) == kElement4);
        CHECK(kMaxSizeVec64 == 0x3FFFFFFFFFFFFFFFULL);
        CHECK(kMaxSizeVec64 == kMaxSizeWide);          // the same constant the two-byte string uses
        CHECK(kVector4Failure == static_cast<std::uint64_t>(-4));
        CHECK(static_cast<std::int64_t>(kVector4Failure) == -4);
        CHECK(kVector4MinCapacity == 4);
        CHECK(kVector4Callers == 23);
    }

    // --- the chain walk inside the BER reader (RE 0x11a780) -----------------------------------------
    {
        CHECK(kVtableSlotStep == 0x158);
        CHECK(kChainTypeField == 0xC0);
        CHECK(kChainTypeField == kBerVtableSlotB);      // the field compared is the slot loaded at entry
        CHECK(kChainUnroll == 3);
        CHECK(kVtableSlotsKnown2 == 7);
        CHECK(kVtableSlotsKnown2 == kVtableSlotsKnown + 1);
        CHECK(kChainMismatchBranch == 0x11A8B0);
        CHECK(kChainNullBranch == 0x11A932);
        CHECK(kBerLengthCallers2 == 9);
        // the seven slots now known, each distinct
        CHECK(kVtableSlotD == 0x08 && kVtableSlotA == 0x18 && kVtableSlotB == 0x30);
        CHECK(kVtableSlotC == 0x68 && kBerVtableSlotA == 0xB8 && kBerVtableSlotB == 0xC0);
        CHECK(kVtableSlotStep == 0x158);
        CHECK(kVtableSlotStep > kBerVtableSlotB);

        // the walk the instructions implement: step until null, accept only a matching type
        struct Node { int type; Node* next; };
        const auto finds = [](Node* head, int want) {
            for (Node* n = head; n != nullptr; n = n->next) {          // RE the slot +0x158 step
                if (n->type == want) return true;                      // RE 0x11A816
            }
            return false;
        };
        Node c{7, nullptr}, b{3, &c}, a{3, &b};
        CHECK(finds(&a, 7));
        CHECK(!finds(&a, 5));
        CHECK(finds(nullptr, 3) == false);
        CHECK(kChainUnroll * 1 == 3);                   // three copies of the block, one loop
    }

    // --- the branch bodies and the corrected +0xc0 reading (RE 0x11a8b0..0x11a91a) ------------------
    {
        CHECK(kSlotIsCalled);
        CHECK(kChainBranchArgs == 2);
        CHECK(kVtableSlotE == 0x110);
        CHECK(kVtableSlotsKnown3 == 8);
        CHECK(kVtableSlotsKnown3 == kVtableSlotsKnown2 + 1);
        CHECK(kGlobalGateRva == 0xA06744);
        CHECK(kGateArgA == 0xA066ED);
        CHECK(kGateArgB == 0xA06726);
        CHECK(kGateArgA != kGateArgB);
        CHECK(kGateConstant == 1);
        CHECK(kSlotBothComparedAndCalled);
        // the correction: +0xc0 is the slot read at entry, compared per node and CALLED on the mismatch path
        CHECK(kChainTypeField == 0xC0);
        CHECK(kChainTypeField == kBerVtableSlotB);
        CHECK(kSlotIsCalled && kSlotBothComparedAndCalled);
        // the eight slots, all distinct and ascending
        CHECK(kVtableSlotD == 0x08 && kVtableSlotA == 0x18 && kVtableSlotB == 0x30);
        CHECK(kVtableSlotC == 0x68 && kBerVtableSlotA == 0xB8 && kBerVtableSlotB == 0xC0);
        CHECK(kVtableSlotE == 0x110 && kVtableSlotStep == 0x158);
        CHECK(kVtableSlotE < kVtableSlotStep);
        // the tail call takes the object and the value, which is the shape both branches share
        CHECK(kChainBranchArgs == 2 && kChainUnroll == 3);
    }

    // --- the guarded call pattern at four sites (RE 0x11a8e5..0x11a9cc) -----------------------------
    {
        CHECK(kGateCallSlot == 0x110);
        CHECK(kGateCallSlot == kVtableSlotE);
        CHECK(kGateSites == 4);
        CHECK(kGateBytesRead == 3);
        CHECK(kGateBytesRead < kGateSites);             // the fourth is deliberately unread
        CHECK(kGateByteA == 0xA06744);
        CHECK(kGateByteB == 0xA066F7);
        CHECK(kGateByteC == 0xA066A9);
        CHECK(kGateByteA != kGateByteB);
        CHECK(kGateByteB != kGateByteC);
        CHECK(kGateByteA != kGateByteC);
        CHECK(kGateInitAddress == 0xA06664);
        CHECK(kGateInit == 0x998DA0);
        CHECK(kGateArgsPerSite == 2);
        CHECK(kGateConstant2 == 1);
        CHECK(kGateConstant2 == kGateConstant);
        CHECK(kFourthGateByteUnread);                   // unread, not guessed
        CHECK(kGlobalGateRva == kGateByteA);            // round 283's byte is the first of the three

        // the pattern the instructions implement: call only when the byte is set, otherwise initialise and retry
        const auto guarded = [](bool& gate, int& calls, int& inits) {
            if (!gate) { ++inits; gate = true; }        // RE 0x11A9CC then back to the call
            ++calls;                                    // RE the call through slot +0x110
        };
        bool gate = false; int calls = 0, inits = 0;
        guarded(gate, calls, inits);
        CHECK(gate);
        CHECK(calls == 1);
        CHECK(inits == 1);
        guarded(gate, calls, inits);
        CHECK(calls == 2);
        CHECK(inits == 1);                              // initialised once
    }

    // --- the second status reader and the BER reader's callers (RE 0x111a50) ------------------------
    {
        CHECK(kStatusReaderB == 0x111A50);
        CHECK(kStatusReaderBbytes == 74);
        CHECK(kStatusReaderFamily == 2);
        CHECK(kStatusReadersAmongCallers == 2);
        CHECK(kStatusReaderFamily == kStatusReadersAmongCallers);
        CHECK(kStatusOutOffset == 0x2E);
        CHECK(kStatusExpected2 == 2);
        CHECK(kStatusExpected2 == kStatusExpected);
        CHECK(kBerReaderCaller == kBerLengthReader);
        CHECK(kBerReaderCallers == 9);
        CHECK(kBerReaderCallers > kStatusReadersAmongCallers);
        // the two readers are distinct routines over the SAME layout
        CHECK(kStatusReaderB != kFinaliseWithRetry);
        CHECK(kFinaliseFlagA == 0x28 && kFinaliseFlagB == 0x29 && kFinalisePointer == 0x30);
        CHECK(kFinaliseCallers == 24);

        // the shared retry logic both readers implement
        const auto readWithRetry = [](bool& flag, std::uint16_t& status, int& reports) {
            flag = true;                                 // RE 0x111A58
            while (status != 0) {                        // RE 0x111A90
                ++reports;                               // RE 0x111A8A
                status = 0;                              // the retry succeeds
            }
            return true;
        };
        bool flag = false;
        std::uint16_t status = 1;
        int reports = 0;
        readWithRetry(flag, status, reports);
        CHECK(flag);
        CHECK(status == 0);
        CHECK(reports == 1);
        std::uint16_t already = 0;
        int none = 0;
        readWithRetry(flag, already, none);
        CHECK(none == 0);                                // nothing to report
    }

    // --- the destructor-reader and the bit-to-byte conversion (RE 0x10f810 and 0xf7b90) -------------
    {
        CHECK(kStatusReaderC == 0x10F810);
        CHECK(kStatusReaderCbytes == 153);
        CHECK(kStatusReaderFamily2 == 3);
        CHECK(kStatusReaderFamily == 2);                // round 285 counted two; the third joins here
        CHECK(kFinalisedFlagFrees);
        CHECK(kReaderIsDestructor);
        CHECK(kStatusReaderCDirectCallers == 0);        // reached through a vtable, as a destructor is
        CHECK(kFinaliseFlagA == 0x28 && kFinaliseFlagB == 0x29 && kFinalisePointer == 0x30);
        CHECK(kStatusReaderC != kStatusReaderB);
        CHECK(kStatusReaderC != kFinaliseWithRetry);

        CHECK(kBerByteCount == 0xF7B90);
        CHECK(kBitToByteAddend == 7);
        CHECK(kBitToByteShift == 3);
        CHECK((1 << kBitToByteShift) == 8);
        CHECK(kBitToByteCtor == 0x7B0160);
        CHECK(kBitToByteAlloc == 0x30);
        CHECK(kBitToByteAlloc == kGetOrCreateBytes);
        CHECK(kVtableSlotF == 0x90);
        CHECK(kVtableSlotsKnown4 == 9);
        CHECK(kVtableSlotsKnown4 == kVtableSlotsKnown3 + 1);
        CHECK(kThrowSite == 0x999030);

        // the conversion the instructions perform
        const auto bitsToBytes = [](std::uint32_t bits) {
            return (bits + kBitToByteAddend) >> kBitToByteShift;
        };
        CHECK(bitsToBytes(0) == 0);
        CHECK(bitsToBytes(1) == 1);
        CHECK(bitsToBytes(8) == 1);
        CHECK(bitsToBytes(9) == 2);
        CHECK(bitsToBytes(16) == 2);
        CHECK(bitsToBytes(17) == 3);
        CHECK(bitsToBytes(0x100) == 32);
        // it is a CEILING, not a truncation
        CHECK(bitsToBytes(7) == 1);
        CHECK(bitsToBytes(7) != 7 / 8);

        // the lifecycle rule: a set flag frees, a clear one reads the status
        const auto actsAs = [](bool finalised) { return finalised ? "free" : "read"; };
        CHECK(std::string(actsAs(true)) == "free");
        CHECK(std::string(actsAs(false)) == "read");
    }

    // --- the length check and the inline-buffer constructor (RE 0xf7470 and 0x6de430) --------------
    {
        CHECK(kBerValidate == 0xF7470);
        CHECK(kBitToByteSites == 2);
        CHECK(kValidateHelper == 0x77A460);
        CHECK(kSizeCall == 0x1186C0);
        CHECK(kLengthCheckThrows);
        CHECK(kBerValidateCallers == 0);
        CHECK(kBerValidate != kBerByteCount);           // two distinct sites of the same conversion
        CHECK(kBitToByteAddend == 7 && kBitToByteShift == 3);

        // the check the instructions perform: the size must be at least ceil(bits/8)
        const auto accepts = [](std::uint64_t size, std::uint32_t bits) {
            const std::uint64_t needed = (bits + 7) >> 3;
            return size >= needed;                      // RE 0xF74E6 (jb -> the throw path)
        };
        CHECK(accepts(2, 16));
        CHECK(accepts(3, 17));
        CHECK(!accepts(1, 16));
        CHECK(!accepts(0, 1));
        CHECK(accepts(1, 8));
        CHECK(!accepts(0, 8));

        CHECK(kCtor96 == 0x6DE430);
        CHECK(kCtor96VtableRva == 0x35D94F);
        CHECK(kCtor96Dword == 0x10);
        CHECK(kCtor96Pointer == 0x18);
        CHECK(kCtor96Inline == 0x20);
        CHECK(kCtor96InlineTarget == 0x30);
        CHECK(kCtor96InlineTarget > kCtor96Inline);
        CHECK(kCtor96InlineTarget - kCtor96Inline == 0x10);
        CHECK(kAlloc60 == 0x60);
        CHECK(kAlloc60 == 96);
        CHECK(kAlloc60 > kGetOrCreateBytes);
        CHECK(kCtor96Callers == 23);
        CHECK(kAllocatorSightings == 5);
        CHECK(kCtor96Helper == 0x888FA0);
    }

    // --- the InputBuffer object and the tenth slot (RE 0x77a460 and 0x1186c0) ------------------------
    {
        CHECK(kInputBufferCtor == 0x77A460);
        CHECK(kInputBufferRva == 0x23C577);
        CHECK(std::string(kTagInputBuffer) == "InputBuffer");
        CHECK(std::string(kTagInputBuffer).size() == 11);
        CHECK(kInputBufferMarker == 0x14);
        CHECK(kInputBufferMarkerValue == 0xFFFFFFFFu);
        CHECK(static_cast<std::int32_t>(kInputBufferMarkerValue) == -1);
        CHECK(kInputBufferByte == 0x18);
        CHECK(kInputBufferByte == kInputBufferMarker + 4);
        CHECK(kInputBufferPtrA == 0x00);
        CHECK(kInputBufferPtrB == 0x08);
        CHECK(kInputBufferDescriptorRva == 0x28DF88);
        CHECK(kInputBufferPtrOffsets == 2);
        CHECK(kInputBufferCallers == 6);
        CHECK(kInputBufferHelper == 0x118260);

        CHECK(kSizeAccessor == 0x1186C0);
        CHECK(kVtableSlotG == 0x160);
        CHECK(kVtableSlotsKnown5 == 10);
        CHECK(kVtableSlotsKnown5 == kVtableSlotsKnown4 + 1);
        CHECK(kVtableSlotG > kVtableSlotStep);          // the tenth is the highest offset so far
        CHECK(kSizeAccessorGateRva == 0xA08935);
        CHECK(kSizeAccessorSentinel == -1);
        CHECK(kGuardPatternSightings == 3);
        CHECK(kSizeAccessorCallers == 6);
        CHECK(!kHelperClassificationOpen);              // settled in round 289: the callee IS CryptoPP
        // the domain strings this area carries
        CHECK(std::string(kTagBerDecodeError) == "BER decode error");
        CHECK(std::string(kTagInputBuffer) == "InputBuffer");
    }

    // --- the settled classification and the rule it produced (RE 0x118260) --------------------------
    {
        CHECK(kCryptoPpSelfTest == 0x118260);
        CHECK(kSelfTestProbe == 0xD5970);
        CHECK(kSelfTestStatus == 0xD5990);
        CHECK(kSelfTestStatusDisabled == 1);
        CHECK(kSelfTestTextA == 0x89F8E6);
        CHECK(kSelfTestCtor == 0x1171F0);
        CHECK(kSelfTestAlloc == 0x30);
        CHECK(kSelfTestCallers == 169);
        CHECK(!kHelperClassificationOpen);              // closed: it references CryptoPP's own text
        CHECK(kDomainCallingLibraryStaysDomain);        // and the rule the case produced
        // the caller of the self-test is domain code, and that does not change either classification
        CHECK(kInputBufferHelper == kCryptoPpSelfTest);
        CHECK(kInputBufferCtor == 0x77A460);
        CHECK(kInputBufferCtor != kCryptoPpSelfTest);
        CHECK(kSelfTestCallers > kBerReaderCallers);
        CHECK(kSelfTestCallers > kBigIntAssignCallers);

        // the status the routine acts on: disabled only when the value is exactly one
        const auto disabled = [](std::int32_t status) { return status == kSelfTestStatusDisabled; };
        CHECK(disabled(1));
        CHECK(!disabled(0));
        CHECK(!disabled(2));

        // the rule restated: classification of caller and callee are independent
        const auto callerIsDomain = [] { return true; };        // the 'InputBuffer' constructor
        const auto calleeIsLibrary = [] { return true; };       // CryptoPP's self-test
        CHECK(callerIsDomain() && calleeIsLibrary());
        CHECK(kDomainCallingLibraryStaysDomain == (callerIsDomain() && calleeIsLibrary()));
    }

    // --- the triple-buffer record and the copy assignment (RE 0x6de430 and 0x418bd0) ----------------
    {
        CHECK(kInlineBufferA == 0x10);
        CHECK(kInlineBufferB == 0x20);
        CHECK(kInlineBufferC == 0x40);
        CHECK(kInlineTargetA == 0x20);
        CHECK(kInlineTargetB == 0x30);
        CHECK(kInlineTargetC == 0x50);
        CHECK(kInlineBufferPairs == 3);
        CHECK(kInlineBufferB - kInlineBufferA == 0x10);
        CHECK(kInlineTargetB - kInlineTargetA == 0x10);
        CHECK(kInlineTargetB - kInlineBufferB == 0x10);   // each buffer points one step ahead of itself
        CHECK(kInlineTargetC - kInlineBufferC == 0x10);
        CHECK(kInlineTargetC - kInlineTargetB == 0x20);
        CHECK(kRecordVtable == 0x00);
        CHECK(kRecordWordA == 0x08);
        CHECK(kRecordWordB == 0x0C);
        CHECK(kRecordWordB - kRecordWordA == 4);
        CHECK(kRecordVtableRva == 0x35E739);
        CHECK(kRecordBytes == 0x60);
        CHECK(kRecordBytes == kAlloc60);

        CHECK(kCopyAssign == 0x418BD0);
        CHECK(kCopyField == 0x04);
        CHECK(kCopyCapacity == 0x14);
        CHECK(kCopyCapacity == kSsoCapacity);            // the field round 249 recorded
        CHECK(kCopyHelper == 0x63F258);
        CHECK(kHelperClusterStep == 0x20);
        CHECK(kCopyHelper == kHelperClusterBase + kHelperClusterStep);
        CHECK(kCopyHelper != kLengthHelper);             // a different helper in the same cluster
        CHECK(kCopyAssignCallers == 25);

        // the three buffers and their targets, as the constructor lays them out
        struct Pair { std::size_t buf; std::size_t target; };
        const Pair pairs[3] = {{kInlineBufferA, kInlineTargetA},
                               {kInlineBufferB, kInlineTargetB},
                               {kInlineBufferC, kInlineTargetC}};
        for (int i = 0; i < kInlineBufferPairs; ++i) {
            CHECK(pairs[i].target - pairs[i].buf == 0x10);
        }
        CHECK(pairs[1].buf - pairs[0].buf == 0x10);
        CHECK(pairs[2].buf - pairs[1].buf == 0x20);
    }

    // --- the layout proven, and the record's two counters (RE 0x418bd0 and 0x6de430) ----------------
    {
        CHECK(kSsoConfirmed);
        CHECK(!kSsoInference);                          // it moved from inference to evidence
        CHECK(kSsoField00 == 0x00);
        CHECK(kSsoField04 == 0x04);
        CHECK(kSsoField10 == 0x10);
        CHECK(kSsoField14 == 0x14);
        CHECK(kSsoField18 == 0x18);
        CHECK(kSsoField14 == kSsoCapacity);
        CHECK(kSsoField18 == kSsoData);
        CHECK(kSsoAlloc == 0x9984E0);
        CHECK(kReleaserAltSightings == 3);            // updated in round 321: three sightings
        CHECK(kReleaserAlt == 0x9984A0);
        CHECK(kCopyAssignCallers2 == 25);
        CHECK(kCopyAssignCallers2 == kCopyAssignCallers);
        // the fields are distinct and ordered as the layout has them
        CHECK(kSsoField00 < kSsoField04 && kSsoField04 < kSsoField10);
        CHECK(kSsoField10 < kSsoField14 && kSsoField14 < kSsoField18);

        CHECK(kRecordCounterA == 0x08);
        CHECK(kRecordCounterB == 0x0C);
        CHECK(kRecordCounterB - kRecordCounterA == 4);
        CHECK(kRecordCounters == 2);
        CHECK(kRecordCountedTwice);
        CHECK(kRecordCounterA == kRecordWordA);         // the counter round 290 saw set to one
        CHECK(kRecordCounterB == kRecordWordB);
        CHECK(kRecordLinkA == 0x40);
        CHECK(kRecordLinkB == 0x48);
        CHECK(kVtableSlotH == 0x10);
        CHECK(kVtableSlotsKnown6 == 11);
        CHECK(kVtableSlotsKnown6 == kVtableSlotsKnown5 + 1);
        CHECK(kRecordFinalCall == 0x9135D0);

        // the dual-counter release: each counter is decremented, and zero on either frees
        const auto release = [](int& strong, int& weak) {
            --strong;                                    // RE 0x6DE505
            const bool freed = (strong == 0);
            --weak;                                      // RE 0x6DE52B
            return freed;
        };
        int strong = 1, weak = 1;
        CHECK(release(strong, weak));
        CHECK(strong == 0);
        CHECK(weak == 0);
        int strong2 = 2, weak2 = 3;
        CHECK(!release(strong2, weak2));
        CHECK(strong2 == 1 && weak2 == 2);
    }

    // --- the pointer-array deep copy and the 408-byte record (RE 0x418bd0) --------------------------
    {
        CHECK(kElementBytes198 == 0x198);
        CHECK(kElementBytes198 == 408);
        CHECK(kPointerMaxCount == 0xFFFFFFFFFFFFFFFULL);
        CHECK(kPointerMaxCount == (1ULL << 60) - 1);
        // one past the limit is exactly two to the sixtieth, which is what the guard encodes
        CHECK(kPointerMaxCount + 1 == (static_cast<std::uint64_t>(1) << 60));
        CHECK(kVectorOfPointers);
        CHECK(kRecordHeaderBytes == 6);
        CHECK(kRecordDword == 0x00);
        CHECK(kRecordByteA == 0x04);
        CHECK(kRecordByteB == 0x05);
        CHECK(kRecordByteB - kRecordByteA == 1);
        CHECK(kRecordPayload == 0x06);
        CHECK(kRecordPayload == kRecordByteB + 1);
        CHECK(kRecordHeaderBytes == kRecordPayload);
        CHECK(kPayloadCopier == 0x63F258);
        CHECK(kPayloadCopierSightings == 2);
        CHECK(kPayloadCopier == kCopyHelper);            // the helper round 290 found
        CHECK(kOuterCount == 0x00);
        CHECK(kOuterArray == 0x18);
        CHECK(kOuterArray == kSsoField18);               // the same buffer the assignment frees
        CHECK(kElementBytes198 > kRecordBytes);          // larger than the 0x60 record

        // the scaling and the guard the instructions use
        const auto bytesFor = [](std::uint64_t count) { return count * 8; };   // RE 0x418CCC
        CHECK(bytesFor(0) == 0);
        CHECK(bytesFor(1) == 8);
        CHECK(bytesFor(100) == 800);
        const auto withinLimit = [](std::uint64_t count) { return count <= kPointerMaxCount; };
        CHECK(withinLimit(0));
        CHECK(withinLimit(kPointerMaxCount));
        CHECK(!withinLimit(kPointerMaxCount + 1));
    }

    // --- the array teardown and the string assignment (RE 0x418bd0 and 0x9135d0) --------------------
    {
        CHECK(kArrayStride == 8);
        CHECK(kArrayElementsFreed);
        CHECK(kArrayFreeCallee == 0x9984B0);
        CHECK(kArrayFreeCallee == kSharedDealloc);
        CHECK(kSharedDeallocSightings5 == 7);
        CHECK(kSharedDeallocSightings5 == kSharedDeallocSightings4 + 1);
        CHECK(kArrayFreeLoopCallers == 25);
        // the stride matches the pointer scaling of round 292: both say eight
        CHECK(kArrayStride == 8 && kVectorOfPointers);
        CHECK(kArrayStride < kElementBytes198);

        CHECK(kStringAssign == 0x9135D0);
        CHECK(kStringAssignData == 0x00);
        CHECK(kStringAssignSize == 0x08);
        CHECK(kStringAssignCapacity == 0x10);
        CHECK(kStringAssignData == kWideData);
        CHECK(kStringAssignSize == kWideSize);
        CHECK(kStringAssignCapacity == kWideCapacity);
        CHECK(kStringAssignCallers == 32);
        CHECK(kStringAssignSsoCheck);
        CHECK(kStringAssignInlineBranch == 0x913684);
        CHECK(kStringAssignInlineBranch > kStringAssign);
        CHECK(kStringAssignCapacity == kSsoInline);      // the inline buffer sits where the capacity does

        // the SSO decision the instructions make: inline when the data pointer still points into the object
        const auto usesInline = [](const void* data, const void* self) {
            return data == static_cast<const char*>(self) + kStringAssignCapacity;
        };
        char obj[64] = {};
        CHECK(usesInline(obj + kStringAssignCapacity, obj));
        CHECK(!usesInline(obj, obj));

        // the teardown loop: free every non-null element, eight bytes apart
        int freed = 0;
        void* elements[3] = {reinterpret_cast<void*>(1), nullptr, reinterpret_cast<void*>(2)};
        for (std::size_t i = 0; i < 3; ++i) {
            if (elements[i] != nullptr) ++freed;         // RE 0x418D86/0x418D8B
        }
        CHECK(freed == 2);
        CHECK(kArrayStride * 3 == 24);
    }

    // --- the inline capacity and the release rule (RE 0x9135d0) -------------------------------------
    {
        CHECK(kSmallCapacity == 7);
        CHECK(kSmallCapacity == kStringInlineCapacity);
        CHECK(kSmallCapacity < kSsoInline);
        CHECK(kStringRealloc == 0x913640);
        CHECK(kStringAllocBySize == 0x913690);
        CHECK(kFreeOnlyIfHeap);
        CHECK(kGrowthDoubling);
        CHECK(kStringAssignDouble == 2);
        CHECK(kSharedDeallocSightings6 == 8);
        CHECK(kSharedDeallocSightings6 == kSharedDeallocSightings5 + 1);
        CHECK(kSharedDealloc == 0x9984B0);
        CHECK(kStringRealloc != kStringAssign);
        CHECK(kStringRealloc > kStringAssign);

        // the release rule the instructions implement: free only when the data is not inline
        const auto release = [](const char* data, const char* inlineBuf, int& frees) {
            if (data != inlineBuf) { ++frees; return true; }   // RE 0x913658/0x91365B
            return false;
        };
        char obj[64] = {};
        int frees = 0;
        CHECK(!release(obj + kSsoInline, obj + kSsoInline, frees));
        CHECK(frees == 0);
        CHECK(release(obj, obj + kSsoInline, frees));
        CHECK(frees == 1);

        // the capacity comparison that decides whether to reallocate
        const auto needsGrowth = [](std::size_t capacity, std::size_t size) { return capacity < size; };
        CHECK(!needsGrowth(kSmallCapacity, 7));
        CHECK(needsGrowth(kSmallCapacity, 8));
        CHECK(needsGrowth(16, 32));
        CHECK(!needsGrowth(32, 32));
        CHECK(kSmallCapacity * 2 == 14);
    }

    // --- the growth policy and its clamp (RE 0x913690) -----------------------------------------------
    {
        CHECK(kGrowthHelper == 0x913690);
        CHECK(kMaxSizeShared == 0x3FFFFFFFFFFFFFFFULL);
        CHECK(kMaxSizeShared == (1ULL << 62) - 1);
        CHECK(kMaxSizeShared == kMaxSizeWide);
        CHECK(kMaxSizeShared == kMaxSizeVec64);
        CHECK(kCapacitySentinel == 0x8000000000000000ULL);
        CHECK(kCapacitySentinel == (static_cast<std::uint64_t>(1) << 63));
        CHECK(kGrowthHelperCallers == 48);
        CHECK(kGrowthRulePlusOneDouble);
        CHECK(kGrowthPrefersDoublingCapacity);
        CHECK(kOverflowHelper == 0x979E70);
        CHECK(kGrowthAllocator == 0x998500);
        CHECK(kAllocatorSightings2 == 6);

        // the policy, in the order of the branches the instructions take
        const auto newCapacity = [](std::uint64_t capacity, std::uint64_t requested) -> std::uint64_t {
            if (capacity > kMaxSizeShared) return kCapacitySentinel;             // RE 0x9136A4
            if (capacity > requested) return 2 * (capacity + 1);                 // RE 0x9136A9/0x9136B1
            const std::uint64_t doubled = 2 * requested;                         // RE 0x9136C0
            if (capacity >= doubled) return 2 * (capacity + 1);                  // RE 0x9136C3
            if (doubled <= kMaxSizeShared) return doubled;                       // RE 0x9136CB/0x9136E3
            return kMaxSizeShared;                                               // RE 0x9136CD
        };
        // the four hand-computed cases
        CHECK(newCapacity(4, 10) == 20);      // capacity below the request: twice the request
        CHECK(newCapacity(50, 10) == 102);    // capacity above it: 2 * (50 + 1)
        CHECK(newCapacity(4, 4) == 8);        // at it: twice the request
        CHECK(newCapacity(8, 4) == 18);       // capacity already past twice the request: 2 * (8 + 1)
        // CORRECTED in round 295c: 0 is not ABOVE 0, so twice-the-request (0) is taken and the capacity does
        // reach it, so the 2*(capacity+1) rule applies.
        CHECK(newCapacity(0, 0) == 2);
        // CORRECTED in round 295c: twice the request is 2 and the capacity 1 does not reach it.
        CHECK(newCapacity(1, 1) == 2);
        CHECK(newCapacity(2, 1) == 6);        // here the capacity DOES exceed the request: 2 * (2 + 1)
        // the clamp is reached only past the max_size
        CHECK(newCapacity(kMaxSizeShared + 1, 1) == kCapacitySentinel);
        CHECK(newCapacity(kMaxSizeShared, 0) == 2 * (kMaxSizeShared + 1));   // wraps, as the arithmetic does
    }

    // --- the length-error thrower (RE 0x979e70) ------------------------------------------------------
    {
        CHECK(kThrowLengthError == 0x979E70);
        CHECK(kLengthErrorObjectBytes == 8);
        CHECK(kLengthErrorTypeRva == 0x8EF3B);
        CHECK(kLengthErrorTypeOffset == 0x10);
        CHECK(kLengthErrorArgumentRva == 0xA7003);
        CHECK(kLengthErrorDescriptor == 0x979E85);
        CHECK(kThrowLengthErrorCallers == 676);
        CHECK(kThrowHelperSightings == 5);
        CHECK(kAllocatorSightings3 == 4);
        CHECK(kLengthErrorShapeOnly);                    // shape-based, said so
        CHECK(kThrowSite == 0x999030);                   // the same throw helper round 286 found
        CHECK(kThrowLengthError != kGrowthHelper);
        CHECK(kThrowLengthError > kGrowthHelper);
        CHECK(kThrowLengthErrorCallers > kDeallocAliasCount);
        CHECK(kThrowLengthErrorCallers > kSelfTestCallers);

        // CORRECTED in round 296c: the one word the thrower stores is a POINTER to the type, because the
        // instruction is `mov qword [rax], rdx` and rdx came from the global's +0x10. It is not a length field,
        // and the two addresses loaded afterwards are ARGUMENTS to the throw helper, not fields of the object.
        struct ExceptionHeader { void* type; };
        CHECK(sizeof(ExceptionHeader) == kLengthErrorObjectBytes);
        CHECK(kLengthErrorObjectBytes == sizeof(void*));
        CHECK(kLengthErrorTypeOffset == 0x10);
        ExceptionHeader h{nullptr};
        h.type = &h;
        CHECK(h.type == &h);
        CHECK(kLengthErrorObjectBytes != sizeof(std::size_t) * 2);

        // the growth helper reaches this path only past the max_size, which round 295 asserted
        CHECK(kMaxSizeShared == 0x3FFFFFFFFFFFFFFFULL);
        CHECK(kGrowthHelper == 0x913690);
    }

    // --- the runtime's throw entry point and its ABI string (RE 0x999030) ---------------------------
    {
        CHECK(kCxaThrow == 0x999030);
        CHECK(kCxaMagic == 0x474E5543432B2B00ULL);
        CHECK(kCxaHeaderOffset == 0x40);
        CHECK(kUncaughtOffset == 0x08);
        CHECK(kCxaGlobals == 0x998CB0);
        CHECK(kCxaTypeLookupA == 0x963560);
        CHECK(kCxaTypeLookupB == 0x962F10);
        CHECK(kCxaThrowCallers == 476);
        CHECK(kCxaFieldOffset == 0x60);
        CHECK(kCxaIdentifiedByString);
        CHECK(kThrowSite == kCxaThrow);                  // the helper rounds 286 and 296 reached
        CHECK(kThrowLengthError != kCxaThrow);
        CHECK(kCxaTypeLookupA != kCxaTypeLookupB);
        CHECK(kCxaThrowCallers < kThrowLengthErrorCallers);   // 476 throw sites, 676 length-error sites
        CHECK(kCxaThrowCallers > kThrowHelperSightings);      // and far more than the sightings count

        // the ABI string, taken from the immediate's byte sequence
        const auto magic = [](std::uint64_t v) {
            char out[9] = {};
            for (int i = 0; i < 8; ++i) {
                out[i] = static_cast<char>((v >> (8 * (7 - i))) & 0xFF);   // the immediate read big-endian
            }
            return std::string(out, 8);
        };
        const std::string m = magic(kCxaMagic);
        CHECK(m.size() == 8);
        CHECK(m[0] == 'G');
        CHECK(m[1] == 'N');
        CHECK(m[2] == 'U');
        CHECK(m[3] == 'C');
        CHECK(m[4] == 'C');
        CHECK(m[5] == '+');
        CHECK(m[6] == '+');
        CHECK(m[7] == '\0');
        CHECK(m.substr(0, 7) == "GNUCC++");
        // and the two hex digits that spell it
        CHECK((kCxaMagic >> 56) == 0x47);
        CHECK(((kCxaMagic >> 48) & 0xFF) == 0x4E);
        CHECK(((kCxaMagic >> 40) & 0xFF) == 0x55);

        // the header arithmetic the routine performs
        CHECK(kCxaHeaderOffset == kCxaFieldOffset - 0x20);
        CHECK(kUncaughtOffset % 4 == 0);                 // a dword counter
    }

    // --- the in-place InputBuffer and the self-test gate (RE 0x10fd40) ------------------------------
    {
        CHECK(kInputBufferLocal == 0x60);
        CHECK(kInputBufferLocalMarker == 0x74);
        CHECK(kInputBufferLocalByte == 0x78);
        CHECK(kInputBufferLocalLink == 0x80);
        // the three relative offsets agree with the constructor of round 288
        CHECK(kInputBufferLocalMarker - kInputBufferLocal == kInputBufferMarker);
        CHECK(kInputBufferLocalByte - kInputBufferLocal == kInputBufferByte);
        CHECK(kInputBufferLocalLink - kInputBufferLocal == 0x20);
        CHECK(kInputBufferMarker == 0x14);
        CHECK(kInputBufferByte == 0x18);
        CHECK(kInputBufferInPlace);
        CHECK(kInputBufferMarkerValue == 0xFFFFFFFFu);

        CHECK(kSelfTestFirst);
        CHECK(kSelfTestArgument == 0);
        CHECK(kFlagProbe == 0x1170B0);
        CHECK(kSelfTestFirst && kCryptoPpSelfTest == 0x118260);
        CHECK(kVtableSlotI == 0xA0);
        CHECK(kVtableSlotsKnown7 == 12);
        CHECK(kVtableSlotsKnown7 == kVtableSlotsKnown6 + 1);
        CHECK(kVtableSlotI > kVtableSlotF);              // above the ninth slot
        CHECK(kVtableSlotI < kVtableSlotE);              // and below the eighth
        CHECK(kDriverCallers == 1);

        // the relative-offset arithmetic the instructions perform
        const std::size_t base = kInputBufferLocal;
        CHECK(base + kInputBufferMarker == kInputBufferLocalMarker);
        CHECK(base + kInputBufferByte == kInputBufferLocalByte);
        CHECK(base + 0x20 == kInputBufferLocalLink);
        // and the three constructions of the same object are distinct routines
        CHECK(kInputBufferCtor != kCryptoPpSelfTest);   // a constructor, not the self-test
        CHECK(kDriverCallers == 1);                    // and this driver is reached once
        CHECK(kInputBufferCtor == 0x77A460);
    }

    // --- the driver's control flow and its signed status (RE 0x10fd40) ------------------------------
    {
        CHECK(kVtableSlotA0CallSites == 2);
        CHECK(kSlotA0ReturnsPointer);
        CHECK(kStatusByteSignTest);
        CHECK(kNegativeStatusBranch == 0x10FF07);
        CHECK(kStatusComparedField == 0x58);
        CHECK(kDriverFailureSites == 3);
        CHECK(kDriverReportsVia == 0x77F2D0);
        CHECK(kDriverReportsVia == kBerErrorFormatter);   // the formatter of round 280
        CHECK(kLocalConstruct == 0xC33F0);
        CHECK(kResultObject == 0xA0);
        CHECK(kVtableSlotI == 0xA0);                      // the slot and the frame offset coincide numerically
        CHECK(kStatusComparedField != kResultObject);     // but the compared field is elsewhere
        CHECK(kDriverCallers == 1);

        // the sign test the instruction performs on the first byte
        const auto isNegative = [](std::uint8_t raw) {
            return static_cast<std::int8_t>(raw) < 0;     // RE 0x10FE09 (js after movzx)
        };
        CHECK(!isNegative(0));
        CHECK(!isNegative(1));
        CHECK(!isNegative(127));
        CHECK(isNegative(128));                           // 0x80 is -128
        CHECK(isNegative(0xFF));                          // and 0xFF is -1
        CHECK(!isNegative(0x7F));

        // and the equality the driver checks: the probe's byte against the field
        const auto matches = [](std::uint8_t probe, std::uint8_t field) { return probe == field; };
        CHECK(matches(3, 3));
        CHECK(!matches(3, 4));
        CHECK(matches(0, 0));
    }

    // --- the decoding loop and the continuation bit (RE 0x10ff07..0x10ff74) -------------------------
    {
        CHECK(kContinuationBit == 0x80);
        CHECK(kContinuationMask == 0x7F);
        CHECK(kContinuationMask == static_cast<std::uint8_t>(~kContinuationBit));
        CHECK(kContinuationMask == 127);
        CHECK(kAccumulatorOffset == 0x90);
        CHECK(kAccumulatorShift == 8);
        CHECK(kAccumulatorMaxBytes == 8);
        CHECK(kAccumulatorTopShift == 0x38);
        CHECK(kAccumulatorTopShift == kAccumulatorMaxBytes * 8 - 8);
        CHECK(kAccumulatorDone == 0x110105);
        CHECK(kBigEndianAccumulate);
        CHECK(kContinuationBitIsSignBit);
        CHECK(kAccumulatorSource == 0xA0);
        CHECK(kAccumulatorSource == kResultObject);      // the bytes come from the object at +0xA0
        CHECK(kAccumulatorSource == kVtableSlotI);       // and the slot of the same name fetches them

        // the counter the leading byte yields, and the assembly the loop performs
        const auto furtherBytes = [](std::uint8_t lead) {
            return static_cast<unsigned>(lead & kContinuationMask);
        };
        CHECK(furtherBytes(0x81) == 1);
        CHECK(furtherBytes(0x82) == 2);
        CHECK(furtherBytes(0x01) == 1);
        CHECK(furtherBytes(0xFF) == 127);
        CHECK(((0x81 & kContinuationBit) != 0));          // the bit says "more follows"

        const auto assemble = [](const std::uint8_t* bytes, std::size_t n) {
            std::uint64_t acc = 0;
            for (std::size_t i = 0; i < n; ++i) {
                acc = (acc << kAccumulatorShift) | bytes[i];   // RE 0x10FF40/0x10FF44
            }
            return acc;
        };
        const std::uint8_t two[2] = {0x01, 0x02};
        CHECK(assemble(two, 2) == 0x0102);
        const std::uint8_t three[3] = {0x01, 0x00, 0x00};
        CHECK(assemble(three, 3) == 0x010000);
        CHECK(assemble(three, 3) == 65536);
        const std::uint8_t one[1] = {0x7F};
        CHECK(assemble(one, 1) == 127);
        // and the overflow the guard catches: nine bytes cannot fit
        const std::uint8_t nine[9] = {1, 2, 3, 4, 5, 6, 7, 8, 9};
        CHECK(assemble(nine, 9) != 0);
        CHECK((assemble(nine, 8) >> kAccumulatorTopShift) != 0);   // the top byte is set: the check fires
    }

    // --- the driver pair and their differing byte sources (RE 0x110b00) -----------------------------
    {
        CHECK(kDriverSibling == 0x110B00);
        CHECK(kDriverSiblingCallers == 2);
        CHECK(kDriverFrameBytes == 0x108);
        CHECK(kDriverFrameBytes == 264);
        CHECK(kVtableSlotJ == 0xB0);
        CHECK(kVtableSlotsKnown8 == 13);
        CHECK(kVtableSlotsKnown8 == kVtableSlotsKnown7 + 1);
        CHECK(kDriverPair == 2);
        CHECK(kDriversDifferInSource);
        CHECK(kDriverByteSourceA == 0xB0);
        CHECK(kDriverByteSourceB == 0x1170B0);
        CHECK(kDriverByteSourceA != kDriverByteSourceB);   // the difference, asserted
        CHECK(kDriverLocal == 0x60);
        CHECK(kDriverMarker == 0x74);
        CHECK(kDriverByte == 0x78);
        CHECK(kDriverProbe == 0x4A);
        // the in-place object sits at the same offsets in BOTH drivers
        CHECK(kDriverMarker - kDriverLocal == kInputBufferMarker);
        CHECK(kDriverByte - kDriverLocal == kInputBufferByte);
        CHECK(kDriverLocal == kInputBufferLocal);
        CHECK(kDriverMarker == kInputBufferLocalMarker);
        CHECK(kDriverByte == kInputBufferLocalByte);
        CHECK(kDriverProbe == 0x4A && kInputBufferLocal != kDriverProbe);

        // both call the self-test first, and both reach the same slot for further bytes
        CHECK(kSelfTestFirst);
        CHECK(kCryptoPpSelfTest == 0x118260);
        CHECK(kVtableSlotA0CallSites == 2);
    }

    // --- how much the two drivers share, by measurement (RE 0x110b00 and 0x10fd40) -----------------
    {
        CHECK(kDriverTwinOffset == 0x1C7);
        CHECK(kSiblingNegativeBranch == 0x110CC7);
        CHECK(kSiblingNegativeBranch - kDriverSibling == kDriverTwinOffset);
        CHECK(kNegativeStatusBranch - 0x10FD40 == kDriverTwinOffset);   // the same relative offset
        CHECK(kSiblingSharedAt == 0x85);
        CHECK(kFirstDriverSharedAt == 0x81);
        CHECK(kPrologueDelta == 4);
        CHECK(kSiblingSharedAt - kFirstDriverSharedAt == kPrologueDelta);
        CHECK(kDriversStructurallySame);
        CHECK(!kDriversByteIdentical);                    // not supported, so not claimed
        CHECK(kDriversShareBody);
        // the two functions are the same size, so the four bytes must be compensated elsewhere
        CHECK(kDriverSibling != 0x10FD40);
        CHECK(kDriverFrameBytes == 0x108);

        // the arithmetic the two measurements encode, restated so a compiler computes it too
        const std::size_t twinA = kSiblingNegativeBranch - kDriverSibling;
        const std::size_t twinB = kNegativeStatusBranch - 0x10FD40;
        CHECK(twinA == twinB);
        CHECK(twinA == kDriverTwinOffset);
        const std::size_t delta = kSiblingSharedAt - kFirstDriverSharedAt;
        CHECK(delta == kPrologueDelta);
        CHECK(delta != 0);                                // if it were zero the prologues would match
    }

    // --- the difference localised, from fourteen measured offsets (RE 0x110b00) ---------------------
    {
        CHECK(kDifferenceRegionStart == 0x85);
        CHECK(kDifferenceRegionEnd == 0x1C7);
        CHECK(kDifferenceRegionStart < kDifferenceRegionEnd);
        CHECK(kDifferenceLocalized);
        CHECK(kBranchOffsetsIdentical);
        CHECK(kOffsetsCompared == 14);
        CHECK(kBranchOffset0 == kDriverTwinOffset);
        CHECK(kBranchOffset1 == 0x1CB);
        CHECK(kBranchOffset2 == 0x200);
        CHECK(kBranchOffset3 == 0x213);
        CHECK(kBranchOffset0 < kBranchOffset1 && kBranchOffset1 < kBranchOffset2);
        CHECK(kBranchOffset2 < kBranchOffset3);

        // the four hand-computed relative offsets, for both functions
        const std::uintptr_t sibling = kDriverSibling;
        const std::uintptr_t first = 0x10FD40;
        CHECK(0x110CC7 - sibling == kBranchOffset0);
        CHECK(0x110CCB - sibling == kBranchOffset1);        // 0x1CB, four bytes past the first
        CHECK(0x10FF40 - first == kBranchOffset2);
        CHECK(0x10FF53 - first == kBranchOffset3);
        CHECK(0x10FF07 - first == kBranchOffset0);
        // so the branch offsets agree, and the earlier four-byte difference lies before them
        CHECK(0x110B85 - sibling == kDifferenceRegionStart);
        CHECK(0x10FDC1 - first == kFirstDriverSharedAt);
        CHECK(kDifferenceRegionStart - kFirstDriverSharedAt == kPrologueDelta);
        CHECK(!kDriversByteIdentical);                       // still not identical overall
    }

    // --- the third driver and its differences (RE 0x112150) -----------------------------------------
    {
        CHECK(kDriverThird == 0x112150);
        CHECK(kDriverThirdFrame == 0x128);
        CHECK(kDriverThirdFrame == 296);
        CHECK(kDriverFrameBytes == 0x108);
        CHECK(kDriverThirdFrame > kDriverFrameBytes);
        CHECK(kDriverVtables3 == 4);
        CHECK(kDriverVtablesPair == 2);
        CHECK(kDriverVtables3 > kDriverVtablesPair);
        CHECK(kThirdLocal == 0xA0);
        CHECK(kHelper111890 == 0x111890);
        CHECK(kHelper111890Size == 0x30);
        CHECK(kHelper111890Size == kGetOrCreateBytes);
        CHECK(kDriverThirdCallers == 0);
        CHECK(kInPlaceConfirmations == 4);
        // the same in-place offsets as the pair, once more
        CHECK(kInputBufferLocal == 0x60);
        CHECK(kInputBufferLocalMarker - kInputBufferLocal == kInputBufferMarker);
        CHECK(kInputBufferLocalByte - kInputBufferLocal == kInputBufferByte);
        CHECK(kThirdLocal == kResultObject);

        // the three drivers are distinct, and only the third has four vtable pointers
        CHECK(kDriverThird != kDriverSibling);
        CHECK(kDriverThird != 0x10FD40);
        CHECK(kDriverVtables3 != kDriverVtablesPair);
        CHECK(kDriverThirdFrame - kDriverFrameBytes == 0x20);   // thirty-two bytes more of frame
        CHECK(kSelfTestFirst);                                  // and the same gate, again
    }

    // --- the second in-place object and what it adds (RE 0x112150) ----------------------------------
    {
        CHECK(kLocalBase1 == 0x60);
        CHECK(kLocalBase2 == 0xA0);
        CHECK(kLocalBase3 == 0x40);
        CHECK(kLocalBase2 - kLocalBase1 == 0x40);
        CHECK(kInPlaceConfirmations2 == 5);
        CHECK(kInPlaceConfirmations == 4);               // round 304 counted four; this is the fifth
        CHECK(kSelfTestCallsHere == 2);
        CHECK(kInputBufferByte2 == 0x28);
        CHECK(kInputBufferByte2 == kInputBufferByte + 0x10);
        CHECK(kInputBufferByte2 != kInputBufferByte);    // a field the constructor never set
        CHECK(kVtableSlotK == 0x38);
        CHECK(kVtableSlotsKnown9 == 14);
        CHECK(kVtableSlotsKnown9 == kVtableSlotsKnown8 + 1);
        CHECK(kHelper111E90 == 0x111E90);
        CHECK(kHelper111890Calls == 2);
        CHECK(kHelper111890 == 0x111890);

        // the second object's relative offsets, computed rather than copied
        CHECK(0xB4 - kLocalBase2 == kInputBufferMarker);
        CHECK(0xB8 - kLocalBase2 == kInputBufferByte);
        CHECK(0xC0 - kLocalBase2 == 0x20);
        CHECK(0xC8 - kLocalBase2 == kInputBufferByte2);
        // and the same relation holds for the first object's local frame
        CHECK(kInputBufferLocalMarker - kInputBufferLocal == kInputBufferMarker);
        CHECK(kInputBufferMarker == 0x14);

        // the two objects are distinct frames, and only one helper size is used for both
        CHECK(kLocalBase1 != kLocalBase2);
        CHECK(kHelper111890Size == kGetOrCreateBytes);
        CHECK(kSelfTestCallsHere * kHelper111890Calls == 4);
        CHECK(kVtableSlotK != kVtableSlotI);             // the two slots differ
        CHECK(kVtableSlotK < kVtableSlotI);              // and 0x38 comes before 0xA0
    }

    // --- the strict sweep that found nothing (RE the round-306 sweep) --------------------------------
    {
        CHECK(kStrictThunkFound == 0);
        CHECK(kSweepClusters == 2);
        CHECK(kSweepSizeCap == 32);
        CHECK(kLibraryAddressesRegistered == 548);
        CHECK(kThunkClassLocalised);
        CHECK(!kSweepCriterionRelaxed);                  // a zero result, not a loosened test
        CHECK(kTinyAliasCount == 39);                    // the class round 277 DID find, elsewhere
        CHECK(kTinyAliasTargets == 6);
        CHECK(kDeallocAliasCount == 34);
        // the comparison that makes the zero meaningful: the earlier sweep's region was different
        CHECK(kTinyAliasCount > kStrictThunkFound);
        CHECK(kSweepSizeCap < kDeallocCallers);
        CHECK(kSweepCriterionRelaxed == false);
    }

    // --- the parser's required tag, and what tag six means (RE 0x111e90) ----------------------------
    {
        CHECK(kRequiredTag == 6);
        CHECK(kTag6IsOid);
        CHECK(kByteReader == 0x117050);
        CHECK(kByteReaderSites == 2);
        CHECK(kTagSlot == 0x29);
        CHECK(kSecondSlot == 0x2A);
        CHECK(kSecondSlot == kTagSlot + 1);
        CHECK(kZeroedFields == 3);
        CHECK(kZeroedBase == 0x30);
        CHECK(kParserCallers == 2);
        CHECK(kParserBytes == 692);
        CHECK(kBerErrorFormatter == 0x77F2D0);
        // the ASN.1 universal tags this work now rests on, stated as standard facts
        const std::uint8_t kUniversalOid = 0x06;
        const std::uint8_t kUniversalInteger = 0x02;
        const std::uint8_t kUniversalOctetString = 0x04;
        CHECK(kRequiredTag == kUniversalOid);
        CHECK(kUniversalOid != kUniversalInteger);
        CHECK(kUniversalOctetString == 0x04);
        // and the continuation bit of round 300 belongs to the same encoding family
        CHECK(kContinuationBit == 0x80);
        CHECK(kContinuationMask == 0x7F);
        CHECK(kAccumulatorMaxBytes == 8);

        // the acceptance the parser performs: the tag must equal six, or the error path runs
        const auto accepted = [](std::uint8_t tag) { return tag == kRequiredTag; };
        CHECK(accepted(6));
        CHECK(!accepted(5));
        CHECK(!accepted(0));
        CHECK(!accepted(0xFF));
    }

    // --- the twin accessors and the driver difference they explain (RE 0x117050 and 0x1170b0) --------
    {
        CHECK(kByteReaderTwin == 0x1170B0);
        CHECK(kByteReader == 0x117050);
        CHECK(kByteReaderTwin - kByteReader == kTwinDelta);
        CHECK(kTwinDelta == 0x60);
        CHECK(kTwinBytes == 92);
        CHECK(kByteReaderStep == 0x158);
        CHECK(kTwinStep == 0x160);
        CHECK(kByteReaderStep != kTwinStep);
        CHECK(kByteReaderTail == 0xA0);
        CHECK(kTwinTail == 0xB0);
        CHECK(kByteReaderTail != kTwinTail);
        CHECK(kByteReaderNull == 0xA8);
        CHECK(kVtableSlotsKnown10 == 15);
        CHECK(kVtableSlotsKnown10 == kVtableSlotsKnown9 + 1);
        CHECK(kTailCallsThroughSlot);
        CHECK(kHelpersMirrorDrivers);

        // the closure: the sibling driver's byte source is this twin's tail slot
        CHECK(kDriverByteSourceA == kTwinTail);
        CHECK(kDriverByteSourceB == kByteReaderTwin);
        CHECK(kDriversDifferInSource);
        CHECK(kByteReaderNull == kByteReaderTail + 8);   // the null path takes the next slot along
        CHECK(kByteReaderTail == kVtableSlotI);          // the same +0xA0 the drivers call
        CHECK(kTwinTail == kVtableSlotJ);                // and the same +0xB0

        // the two accessors' shapes, side by side
        struct Accessor { std::size_t step; std::size_t tail; };
        const Accessor a{kByteReaderStep, kByteReaderTail};
        const Accessor b{kTwinStep, kTwinTail};
        CHECK(a.step != b.step && a.tail != b.tail);
        CHECK(b.step - a.step == 8);                     // adjacent slots, eight bytes apart
        CHECK(b.tail - a.tail == 0x10);
    }

    // --- the OID loop and the arithmetic left open (RE 0x111e90) -------------------------------------
    {
        CHECK(kOidContinuationTest);
        CHECK(kParserElementShift == 2);
        CHECK(kParserElementBytes == 4);
        CHECK(kParserElementBytes == (1u << kParserElementShift));
        CHECK(kParserStride == 8);
        CHECK(kParserStride != kParserElementBytes);
        CHECK(kAsn1FirstArcBase == 40);
        CHECK(kOidArithmeticFactor == 41);
        CHECK(kOidArithmeticFactor == 1 + 8 * 5);
        CHECK(kOidArithmeticFactor != kAsn1FirstArcBase);
        CHECK(kOidArithmeticUninterpreted);              // left open on purpose
        CHECK(kFactorEqualsTagSlotOffset);
        CHECK(kTagSlot == 0x29);
        CHECK(kOidArithmeticFactor == kTagSlot);         // the coincidence, asserted as a coincidence only
        CHECK(kContinuationBit == 0x80);                 // the same bit round 300 identified
        CHECK(kRequiredTag == 6);

        // what the four instructions compute, step by step
        const auto factorOf = [](std::uint8_t b) {
            const std::uint32_t four = static_cast<std::uint32_t>(b) * 4u;   // lea eax,[rcx*4]
            const std::uint32_t five = four + b;                              // add eax,ecx
            return static_cast<std::uint32_t>(b) + five * 8u;                 // lea eax,[r8+rax*8]
        };
        CHECK(factorOf(1) == 41);
        CHECK(factorOf(0) == 0);
        CHECK(factorOf(2) == 82);
        CHECK(factorOf(255) == 41u * 255u);
        // and the base-forty rule it superficially resembles would give a different number
        CHECK(factorOf(2) != 2 * kAsn1FirstArcBase);
        CHECK(kParserElementBytes * 2 == 8);
    }

    // --- the OID loop as a second assembler site (RE 0x11208A) ---------------------------------------
    {
        CHECK(kOidMask == 0x7F);
        CHECK(kOidMask == kContinuationMask);            // the same mask as the length loop
        CHECK(kOidShift == 8);
        CHECK(kOidShift == kAccumulatorShift);           // the same shift
        CHECK(kOidOverflowShift == 0x38);
        CHECK(kOidOverflowShift == kAccumulatorTopShift);// the same overflow test
        CHECK(kOidDoneBranch == 0x11212E);
        CHECK(kOidOverflowBranch == 0x11213D);
        CHECK(kAssemblerSites == 4);                     // updated in round 316: four sites, not two
        CHECK(kAssemblerShapeShared);
        CHECK(kAccumulatorRegisters == 2);
        CHECK(kContinuationBit == 0x80);
        CHECK(kOidContinuationTest);

        // the count the mask yields and the assembly both sites perform, run once more
        const auto count = [](std::uint8_t lead) { return static_cast<unsigned>(lead & kOidMask); };
        CHECK(count(0x81) == 1);
        CHECK(count(0x02) == 2);
        CHECK(count(0x7F) == 0x7F);
        const auto assemble = [](const std::uint8_t* b, std::size_t n) {
            std::uint64_t acc = 0;
            for (std::size_t i = 0; i < n; ++i) acc = (acc << kOidShift) | b[i];
            return acc;
        };
        const std::uint8_t two[2] = {0x2A, 0x03};
        CHECK(assemble(two, 2) == 0x2A03);
        CHECK(assemble(two, 2) == 10755);
        // the overflow test fires only when the top byte is set
        const std::uint8_t eight[8] = {1, 0, 0, 0, 0, 0, 0, 0};
        CHECK((assemble(eight, 8) >> kOidOverflowShift) == 1);
        const std::uint8_t seven[7] = {1, 0, 0, 0, 0, 0, 0};
        CHECK((assemble(seven, 7) >> kOidOverflowShift) == 0);
    }

    // --- the parser's error surface and its minimum of two (RE 0x111e90) ---------------------------
    {
        CHECK(kParserErrorSites == 4);
        CHECK(kErrorSiteStride == 5);
        CHECK(kParserErrorFirst == 0x11212E);
        CHECK(kParserErrorLast == 0x11213D);
        CHECK(kParserErrorLast - kParserErrorFirst == 3 * kErrorSiteStride);
        CHECK(kParserMinElements == 2);
        CHECK(kParserGrow == 0x90D560);
        CHECK(kGrowArgumentIsDifference);
        CHECK(kCompareHelper == 0x63F300);
        CHECK(kCompareHelperDelta == 8);
        CHECK(kCompareHelper == kMemcpyHelper + kCompareHelperDelta);
        CHECK(kHelperClusterMembers == 5);
        CHECK(kParserErrorFirst == kOidDoneBranch);      // the done branch is the first error entry
        CHECK(kReadNullBranch == 0x112138);
        CHECK(kBerErrorFormatter == 0x77F2D0);
        CHECK(kDriverReportsVia == kBerErrorFormatter);

        // the argument the growth call receives, for the two cases round 309 singled out
        const auto growBy = [](std::size_t count) { return kParserMinElements - count; };
        CHECK(growBy(0) == 2);
        CHECK(growBy(1) == 1);
        CHECK(growBy(2) == 0);
        CHECK(kParserElementShift == 2 && kParserElementBytes == 4);
        // and the four entries are consecutive instructions, each five bytes long
        CHECK(2 * kErrorSiteStride == 10);
        CHECK(kParserErrorSites * kErrorSiteStride == 20);   // the error surface occupies twenty bytes
    }

    // --- the driver family's fourth member (RE 0x112740) --------------------------------------------
    {
        CHECK(kDriverFourth == 0x112740);
        CHECK(kDriverFourthCallers == 9);
        CHECK(kDriverFamily == 4);
        CHECK(kDriverVtables4 == 3);
        CHECK(kDriverVtableCountsDiffer == 1);           // 2, 2, 4 and 3
        CHECK(kInPlaceConfirmations3 == 6);
        CHECK(kInPlaceConfirmations2 == 5);              // round 305 counted five before this
        CHECK(kDriverFamilyHelperShared);
        CHECK(kFamilyReadingIsTemplate);
        // the frames: the pair at 0x108, the third and fourth at 0x128
        CHECK(kDriverFrameBytes == 0x108);
        CHECK(kDriverThirdFrame == 0x128);
        CHECK(kDriverThirdFrame > kDriverFrameBytes);
        // the four vtable counts, recorded rather than merged
        const int counts[4] = {kDriverVtablesPair, kDriverVtablesPair, kDriverVtables3, kDriverVtables4};
        CHECK(counts[0] == 2);
        CHECK(counts[1] == 2);
        CHECK(counts[2] == 4);
        CHECK(counts[3] == 3);
        CHECK(counts[0] == counts[1]);                   // the pair agrees with itself
        CHECK(counts[2] != counts[3]);
        int sum = 0;
        for (int i = 0; i < kDriverFamily; ++i) sum += counts[i];
        CHECK(sum == 11);                                // 2 + 2 + 4 + 3, added up
        // the shared traits
        CHECK(kSelfTestFirst);
        CHECK(kHelper111890Size == 0x30);
        CHECK(kHelper111890Calls >= 2);
        CHECK(kInputBufferLocalMarker - kInputBufferLocal == kInputBufferMarker);
    }

    // --- the second type reader and the two standard tags (RE 0x112740) ----------------------------
    {
        CHECK(kIntegerReader == 0x112740);
        CHECK(kRequiredTagInteger == 2);
        CHECK(kRequiredTag == 6);
        CHECK(kRequiredTagInteger != kRequiredTag);
        CHECK(kTagSlot2 == 0x34);
        CHECK(kSecondSlot2 == 0x35);
        CHECK(kSecondSlot2 == kTagSlot2 + 1);
        CHECK(kSecondSlot2 - kTagSlot2 == kSecondSlot - kTagSlot);   // same adjacency in both readers
        CHECK(kTypeReaderFamily == 2);
        CHECK(kTypeReadersShareShape);
        CHECK(kContinuationTestSites == 3);
        CHECK(kIntegerHelper == 0x118470);
        CHECK(kIntegerReaderCallers == 9);
        CHECK(kDriverFourth == kIntegerReader);          // the fourth driver IS the INTEGER reader
        CHECK(kParserBytes == 692);
        CHECK(kRequiredTag == 6 && kTag6IsOid);

        // the two standard tags, and the acceptance each reader performs
        const std::uint8_t kInteger = 0x02;
        const std::uint8_t kOid = 0x06;
        CHECK(kRequiredTagInteger == kInteger);
        CHECK(kRequiredTag == kOid);
        const auto integerAccepted = [](std::uint8_t t) { return t == kRequiredTagInteger; };
        const auto oidAccepted = [](std::uint8_t t) { return t == kRequiredTag; };
        CHECK(integerAccepted(2) && !integerAccepted(6));
        CHECK(oidAccepted(6) && !oidAccepted(2));
        // each reader rejects the other's tag, which is what makes them different readers
        CHECK(!integerAccepted(kRequiredTag));
        CHECK(!oidAccepted(kRequiredTagInteger));
        CHECK(kContinuationBit == 0x80);
        CHECK(kAssemblerSites == 4);
    }

    // --- the family's split and the flag-driven drivers (RE 0x10fd40 and 0x110b00) -----------------
    {
        CHECK(kFirstTwoDriversTagless);
        CHECK(kDriverFamilySplits);
        CHECK(kDriverFlagA == 0x88);
        CHECK(kDriverFlagB == 0x89);
        CHECK(kDriverFlagC == 0xF0);
        CHECK(kDriverFlagB - kDriverFlagA == 1);
        CHECK(kDriverWordA == 0x4C);
        CHECK(kDriverWordB == 0x4E);
        CHECK(kDriverWordB - kDriverWordA == 2);
        CHECK(kDriverGateConstantOffset == 0x20);
        CHECK(kGateConstant == 1);                       // the same constant round 283 recorded
        CHECK(!kThirdMemberListUnread);                  // closed in round 315: the list was read
        CHECK(kTypeReaderFamily == 2);                   // two of the four demand a tag
        CHECK(kDriverFamily == 4);
        CHECK(kRequiredTag == 6 && kRequiredTagInteger == 2);

        // CORRECTED in round 315b: among the four DRIVERS only one demands a tag. Round 314 counted
        // kTypeReaderFamily (= 2) as if both type readers were drivers, but 0x111e90 is the OID reader
        // which 0x112150 CALLS, so it is not one of the four. The overlap is exactly one member.
        const int driversWithTag = kDriversWithTag;
        const int tagless = kTaglessDrivers;
        CHECK(driversWithTag == 1);
        CHECK(tagless == 3);
        CHECK(driversWithTag + tagless == kDriverFamily);
        CHECK(kTypeReaderFamily == 2);
        CHECK(kSetOverlap == 1);
        CHECK(kTypeReaderFamily - kSetOverlap == 1);      // one type reader is not a driver
        // and the two tagless ones share their flag offsets with each other, not with the readers
        CHECK(kDriverFlagA != kTagSlot);
        CHECK(kDriverWordA != kTagSlot2);
        CHECK(kDriverFlagA > kTagSlot2);
        // the sixteen-bit fields are half the size of the four-byte parser elements
        CHECK(kParserElementBytes == 4);
        CHECK(kDriverWordB - kDriverWordA == kParserElementBytes / 2);
    }

    // --- the third member, and the corrected accounting (RE 0x112150) -------------------------------
    {
        CHECK(kTaglessDrivers == 3);
        CHECK(kDriversWithTag == 1);
        CHECK(kTaglessDrivers + kDriversWithTag == kDriverFamily);
        CHECK(kSetOverlap == 1);
        CHECK(kTypeReaderFamily == 2);
        CHECK(kTypeReaderFamily - kSetOverlap == 1);
        CHECK(kThirdMemberTagless);
        CHECK(kThirdMemberSmallImmediates == 34);
        CHECK(kThirdMemberNonZeroCompare == 0);          // nothing to compare a tag against
        CHECK(kThirdMemberWordFields == 7);
        CHECK(!kThirdMemberListUnread);                  // round 314's flag, closed by this round
        CHECK(kFirstTwoDriversTagless);
        CHECK(kDriverFamilySplits);
        CHECK(kDriverThird != kDriverSibling);
        CHECK(kDriverThird != kDriverFourth);
        CHECK(kDriverSibling != kDriverFourth);
        CHECK(kDriversWithTag == 1 && kRequiredTagInteger == 2);
        CHECK(kIntegerReader != kDriverThird);
        CHECK(kRequiredTag == 6);
        // the three tagless members are three of the four, and the fourth is the INTEGER reader
        CHECK(kDriverFourth == kIntegerReader);
        CHECK(kTaglessDrivers == kDriverFamily - 1);
        CHECK(kThirdMemberWordFields < kThirdMemberSmallImmediates);
    }

    // --- DER's minimal form and the four-byte path (RE 0x112740) ------------------------------------
    {
        CHECK(kLeadingZeroCheck);
        CHECK(kMinimalEncodingRequired);
        CHECK(kLeadingZeroViolation == 0x112B45);
        CHECK(kIntegerFastPathBytes == 4);
        CHECK(kIntegerFastPath == 0x112E70);
        CHECK(kLengthMustMatch);
        CHECK(kLengthMismatch == 0x112EEE);
        CHECK(kSite4AccumulatorBits == 32);
        CHECK(kIntegerZeroByte == 0);
        CHECK(kAssemblerSites == 4);                     // four sites now, the twin pair among them
        CHECK(kAssemblerShapeShared);
        CHECK(kContinuationTestSites == 3);
        CHECK(kRequiredTagInteger == 2);

        // the minimal-form rule, as the instructions check it
        const auto minimallyEncoded = [](const std::uint8_t* bytes, std::size_t n) {
            if (n == 0) return true;
            if (n <= kIntegerFastPathBytes) return true;         // RE 0x11282D: the fast path skips the scan
            for (std::size_t i = 0; i + kIntegerFastPathBytes < n; ++i) {
                if (bytes[i] != kIntegerZeroByte) return false;  // RE 0x112848
            }
            return true;
        };
        const std::uint8_t good[5] = {0x01, 0x02, 0x03, 0x04, 0x05};
        CHECK(!minimallyEncoded(good, 5));                        // a non-zero byte in the scanned range
        const std::uint8_t zeros[5] = {0, 0, 0, 0, 0x05};
        CHECK(minimallyEncoded(zeros, 5));
        const std::uint8_t four[4] = {1, 2, 3, 4};
        CHECK(minimallyEncoded(four, 4));                         // the fast path accepts it outright
        const std::uint8_t six[6] = {0, 1, 0, 0, 0, 2};
        CHECK(!minimallyEncoded(six, 6));
        // and the thirty-two bit accumulator's ceiling, against the sixty-four bit sites
        CHECK(kSite4AccumulatorBits < 64);
        CHECK((1ull << kSite4AccumulatorBits) == 4294967296ull);
    }

    // --- the reused loop, the second error surface, and the narrowed claim (RE 0x112740) -----------
    {
        CHECK(kFastPathJumpsToLoop);
        CHECK(kIntegerLoopEntry == 0x11285C);
        CHECK(kZeroLengthBranch == 0x112883);
        CHECK(kIntegerErrorSites == 4);
        CHECK(kErrorSurfacePatternSites == 2);
        CHECK(kErrorSiteStride == 5);                    // the same stride as round 311's block
        CHECK(kParserErrorSites == 4);
        CHECK(kIntegerWordFields == 5);                  // corrected in round 318: five, not three
        CHECK(kIntegerWordBase == 0x3C);
        CHECK(kIntegerSource == 0x112EFD);
        CHECK(kMinimalEncodingReadingNarrowed);          // my own claim, narrowed
        CHECK(kZeroScanSkippedUnder4Bytes);
        CHECK(kLeadingZeroCheck);                        // the check still exists
        CHECK(kIntegerFastPathBytes == 4);

        // the two error blocks have the same shape: four entries, five bytes apart
        const std::uintptr_t integerEntries[4] = {0x112EEE, 0x112EF3, 0x112EF8, 0x112EFD};
        for (int i = 1; i < kIntegerErrorSites; ++i) {
            CHECK(integerEntries[i] - integerEntries[i - 1] == kErrorSiteStride);
        }
        CHECK(integerEntries[3] - integerEntries[0] == 3 * kErrorSiteStride);
        CHECK(kParserErrorLast - kParserErrorFirst == integerEntries[3] - integerEntries[0]);

        // and the condition my round-316 sentence was missing
        const auto scanApplies = [](std::size_t bytes) { return bytes > kIntegerFastPathBytes; };
        CHECK(!scanApplies(1));
        CHECK(!scanApplies(4));
        CHECK(scanApplies(5));
        CHECK(scanApplies(9));
        CHECK(kIntegerFastPathBytes * 2 == 8);
    }

    // --- five sixteen-bit fields and two indirect calls (RE 0x112740) -------------------------------
    {
        CHECK(kIntegerWordFieldsUpdated);
        CHECK(kIntegerWordFields == 5);
        CHECK(kIntegerWordStride == 2);
        CHECK(kIntegerWordFirst == 0x38);
        CHECK(kIntegerWordLast == 0x40);
        CHECK((kIntegerWordLast - kIntegerWordFirst) / kIntegerWordStride + 1 == kIntegerWordFields);
        CHECK(kIndirectCallSites == 2);
        CHECK(kIndirectViaRegister);
        CHECK(kWordDispatchTargets == 3);
        CHECK(kWordDispatchA == 0x112CD2);
        CHECK(kWordDispatchB == 0x112CA2);
        CHECK(kWordDispatchC == 0x112C32);
        CHECK(kWordDispatchA != kWordDispatchB && kWordDispatchB != kWordDispatchC);
        CHECK(kIntegerWordBase == 0x3C);                 // round 317's lowest of the three it had seen
        CHECK(kIntegerWordFirst < kIntegerWordBase);     // and the chain revealed two more below it

        // the five fields, laid out as the comparisons treat them
        const std::size_t words[5] = {kIntegerWordFirst, kIntegerWordFirst + kIntegerWordStride,
                                      kIntegerWordBase, kIntegerWordBase + kIntegerWordStride,
                                      kIntegerWordLast};
        for (int i = 1; i < kIntegerWordFields; ++i) {
            CHECK(words[i] - words[i - 1] == kIntegerWordStride);
        }
        CHECK(words[0] == 0x38);
        CHECK(words[4] == 0x40);
        CHECK(kIntegerWordFields * kIntegerWordStride == 10);   // they occupy ten bytes
        // round 315 saw seven words in the OTHER routine over the same base offsets
        CHECK(kThirdMemberWordFields == 7);
        CHECK(kThirdMemberWordFields > kIntegerWordFields);
    }

    // --- the words hold BER lengths (RE 0x112740) ----------------------------------------------------
    {
        CHECK(kWordFieldsAreLengths);
        CHECK(kLengthReaderSites2 == 2);
        CHECK(kLengthDestA == 0x38);
        CHECK(kLengthDestB == 0x3C);
        CHECK(kLengthDestA == kIntegerWordFirst);
        CHECK(kLengthDestB == kIntegerWordBase);
        CHECK(kBerLengthReader == 0x11A780);             // the reader rounds 281-284 described
        CHECK(kStatusAcceptanceSites == 4);
        CHECK(kStatusExpected == 2);
        CHECK(kStatusExpected2 == 2);
        CHECK(kStatusCall == 0x11A780);
        CHECK(kBerReaderCaller == kBerLengthReader);     // round 285's caller-list entry for it
        CHECK(kIntegerIsALengthCaller);
        CHECK(kObjectLinkA == 0xC0);
        CHECK(kObjectLinkB == 0x100);
        CHECK(kLocalBase4 == 0xE0);
        CHECK(kLocalBase4Inferred);
        CHECK(kObjectLinkA - 0x20 == kLocalBase2);       // 0xC0 minus the link offset is the local at 0xA0
        CHECK(kObjectLinkB - 0x20 == kLocalBase4);
        CHECK(kIntegerWordFields == 5);
        CHECK(kWordDispatchTargets == 3);

        // the two destinations are two of the five words, and both are in the chain
        const std::size_t words[5] = {kIntegerWordFirst, kIntegerWordFirst + kIntegerWordStride,
                                      kIntegerWordBase, kIntegerWordBase + kIntegerWordStride,
                                      kIntegerWordLast};
        bool foundA = false, foundB = false;
        for (int i = 0; i < kIntegerWordFields; ++i) {
            if (words[i] == kLengthDestA) foundA = true;
            if (words[i] == kLengthDestB) foundB = true;
        }
        CHECK(foundA && foundB);
        // and the acceptance code the callers share
        const auto accepted = [](std::int32_t status) { return status == kStatusExpected; };
        CHECK(accepted(2));
        CHECK(!accepted(1));
        CHECK(!accepted(0));
    }

    // --- the narrow string's constructor and the two capacities (RE 0x9a0480) ----------------------
    {
        CHECK(kNarrowStringCtor == 0x9A0480);
        CHECK(kNarrowStringCallers == 34);
        CHECK(kNarrowSsoCapacity == 15);
        CHECK(kNarrowSsoCapacity == 0xF);
        CHECK(kWideSsoChars == 7);                       // round 294's number, for the other type
        CHECK(kSsoRelationHolds);
        CHECK(kWideSsoChars * 2 + kScasbElementBytes == kNarrowSsoCapacity);
        CHECK(kSmallCapacity == 7);                      // the same round-294 constant, unchanged
        CHECK(kStrlenViaScasb);
        CHECK(kScasbElementBytes == 1);
        CHECK(kEmptyCase == 0x9A050B);
        CHECK(kInlineCase == 0x9A04D4);
        CHECK(kInlineCase != kEmptyCase);                // the two targets are different places
        CHECK(kStringAllocHelper == 0x910BA0);
        CHECK(kStringAllocHelperSightings == 2);
        CHECK(kStringAllocHelper != kStringAssign);
        // the inline buffer offset is the same in both string types
        CHECK(kStringAssignCapacity == 0x10);
        CHECK(kSsoInline == 0x10);
        CHECK(kNarrowStringCtor != kStringAssign);

        // the decision the instructions make: fifteen characters fit, sixteen do not
        const auto staysInline = [](std::size_t chars) { return chars <= kNarrowSsoCapacity; };
        CHECK(staysInline(0));
        CHECK(staysInline(15));
        CHECK(!staysInline(16));
        CHECK(staysInline(kWideSsoChars));               // seven is well inside
        CHECK(!staysInline(kNarrowSsoCapacity + 1));
        CHECK(kNarrowSsoCapacity + 1 == 16);
    }

    // --- the two small destructors (RE 0x4b32f0 and 0x656000) ---------------------------------------
    {
        CHECK(kDtorSmall == 0x4B32F0);
        CHECK(kDtorSmallVtableRva == 0x585231);
        CHECK(kDtorSmallField == 0x18);
        CHECK(kDtorSmallField == kSsoField18);
        CHECK(kDtorSmallCallers == 23);
        CHECK(kReleaserAlt == 0x9984A0);
        CHECK(kReleaserAltSightings == 3);
        CHECK(kTwoFieldDtor == 0x656000);
        CHECK(kTwoFieldA == 0x58);
        CHECK(kTwoFieldB == 0x10);
        CHECK(kTwoFieldA != kTwoFieldB);
        CHECK(kTwoFieldHelper == 0x891B40);
        CHECK(kTwoFieldSites == 2);
        CHECK(kTwoFieldCallers == 22);
        CHECK(kTwoFieldRelease);
        CHECK(kCallThenTailCall);
        CHECK(kDtorSmall != kTwoFieldDtor);
        CHECK(kSharedDealloc != kReleaserAlt);            // the two releasers remain distinct

        // the shape both routines implement: release a field only when it is non-null
        const auto releaseIfSet = [](void* p, int& releases) {
            if (p != nullptr) { ++releases; return true; }
            return false;
        };
        int releases = 0;
        CHECK(!releaseIfSet(nullptr, releases));
        CHECK(releases == 0);
        CHECK(releaseIfSet(reinterpret_cast<void*>(1), releases));
        CHECK(releases == 1);
        // and the second routine releases both fields, the first by call and the last by tail call
        CHECK(kTwoFieldSites == 2 && kTwoFieldSites - 1 == 1);
        CHECK(kTwoFieldB < kTwoFieldA);
    }

    // --- the third nested layout and the forwarding constructor (RE 0x8f7dd0 and 0x888ff0) ---------
    {
        CHECK(kNested3Begin == 0x00);
        CHECK(kNested3End == 0x08);
        CHECK(kNested3Begin == kNestedOuterBegin);       // round 254's outer pair, again
        CHECK(kNested3End == kNestedOuterEnd);
        CHECK(kNested3InnerStride == 0x10);
        CHECK(kNested3InnerStride != kNested2InnerStride);
        CHECK(kNested3InnerStride != kInnerStride24);
        CHECK(kNested3InnerField == 0x08);
        CHECK(kNested3InnerField != kNested2Buffer);     // a different field of the inner element
        CHECK(kNested3Callers == 22);
        CHECK(kNested3Releaser == kTwoFieldHelper);      // round 321's helper, second sighting
        CHECK(kReleaseHelperSightings == 2);
        CHECK(kNestedLayouts == 4);                      // updated in round 328: four layouts
        CHECK(kSharedDeallocSightings7 == 8);
        CHECK(kSharedDeallocSightings7 == kSharedDeallocSightings5 + 1);
        CHECK(kSharedDealloc == 0x9984B0);
        CHECK(kCtorForward == 0x888FF0);
        CHECK(kCtorForwardTarget == 0x86B750);
        CHECK(kDescriptorRva2 == 0x17FB39);
        CHECK(kDescriptorOffset2 == 0x10);
        CHECK(kCtorForwardCallers == 21);
        CHECK(kDescriptorOffsetRepeats);

        // the three layouts side by side: same shape, different numbers, never merged
        struct Layout { std::size_t begin, end, stride, field; };
        // EXTENDED in round 328e: this array is bounded by kNestedLayouts, so when that count went from three to
        // four the array had to grow with it -- the loop below was reading a fourth element that did not exist.
        const Layout layouts[4] = {{kNestedOuterBegin, kNestedOuterEnd, kInnerStride24, kNested2Buffer},
                                   {kNested2Begin, kNested2End, kNested2InnerStride, kNested2Buffer},
                                   {kNested3Begin, kNested3End, kNested3InnerStride, kNested3InnerField},
                                   {kNested4PairC, kNested4PairD, kNested4FieldA, kNested4FieldB}};
        static_assert(kNestedLayouts == 4, "the array and the count have to agree");
        for (int i = 0; i < kNestedLayouts; ++i) {
            CHECK(layouts[i].end - layouts[i].begin == 8);
        }
        CHECK(layouts[0].stride == 0x18);
        CHECK(layouts[1].stride == 0x18);
        CHECK(layouts[2].stride == 0x10);
        CHECK(layouts[2].field == 0x08);
        CHECK(layouts[0].field == layouts[1].field);     // the first two release the same field
        CHECK(layouts[2].field != layouts[0].field);     // the third does not
        CHECK(kDescriptorOffset2 == kLengthErrorTypeOffset);   // the idiom repeats
    }

    // --- the wide append and its terminator (RE 0x913540) -------------------------------------------
    {
        CHECK(kWideAppend == 0x913540);
        CHECK(kWideAppendCallers == 23);
        CHECK(kElementBytesWide == 2);
        CHECK(kWideSsoChecks == 3);
        CHECK(kTerminatorBytes == 2);
        CHECK(kTerminatorValue == 0);
        CHECK(kWideAppendGrow == 0x913710);
        CHECK(kSingleElementPath == 1);
        CHECK(kMemcpySightingsAtAppend == 1);
        // the trio, a third time
        CHECK(kWideData == 0x00);
        CHECK(kWideSize == 0x08);
        CHECK(kWideCapacity == 0x10);
        CHECK(kStringAssignData == kWideData && kStringAssignSize == kWideSize);
        CHECK(kStringAssignCapacity == kWideCapacity);
        CHECK(kSsoInline == kWideCapacity);
        CHECK(kMemcpyHelper == 0x63F2F8);
        CHECK(kWideAppend != kStringAssign);
        CHECK(kWideAppendGrow != kWideInsert);

        // the arithmetic the instructions perform: an element is two bytes, and the terminator follows
        const auto byteOffset = [](std::size_t elements) { return elements * kElementBytesWide; };
        CHECK(byteOffset(0) == 0);
        CHECK(byteOffset(1) == 2);
        CHECK(byteOffset(7) == 14);
        CHECK(byteOffset(15) == 30);
        const auto terminatorAt = [](std::size_t newSize) { return newSize * kElementBytesWide; };
        CHECK(terminatorAt(0) == 0);
        CHECK(terminatorAt(3) == 6);
        CHECK(terminatorAt(3) + kTerminatorBytes == 8);
        // and the capacity check: appending beyond the capacity takes the grow path
        const auto needsGrow = [](std::size_t newSize, std::size_t capacity) { return newSize > capacity; };
        CHECK(!needsGrow(15, 15));
        CHECK(needsGrow(16, 15));
        CHECK(kSmallCapacity == 7);
    }

    // --- the move assignment and the slot's first role (RE 0x10f220 and 0x10fbb0) -------------------
    {
        CHECK(kMoveAssignment == 0x10F220);
        CHECK(kMoveAssignmentCallers == 21);
        CHECK(kMovePointer == 0x08);
        CHECK(kMoveByte == 0x10);
        CHECK(kMoveNullsSource);
        CHECK(kMoveIdentifiedByNullStore);
        CHECK(kSlotDRole);
        CHECK(std::string(kSlotDRoleName) == "release");
        CHECK(kVtableSlotD == 0x08);                     // the slot this role belongs to
        CHECK(kVtableSlotD == kMovePointer);
        CHECK(kLazyInit50 == 0x10FBB0);
        CHECK(kLazyInit50Callers == 23);
        CHECK(kLazyInitFlag == 0x50);
        CHECK(kLazyInitField == 0x48);
        CHECK(kLocalConstruct2 == 0xC3A40);
        CHECK(kLocalConstruct == 0xC33F0);
        CHECK(kLocalConstruct2 != kLocalConstruct);      // different addresses, not merged
        CHECK(kLocalConstruct2 - kLocalConstruct == 0x650);
        CHECK(kLocalConstructFamily == 2);
        CHECK(kLazyInitFlag > kLazyInitField);

        // the move the instructions perform, and the order they do it in
        struct Owner { void* p; unsigned char flag; };
        const auto moveAssign = [](Owner& dst, Owner& src, int& releases) {
            if (dst.p != nullptr) ++releases;            // RE 0x10F25A, the virtual release
            dst.flag = src.flag;                         // RE 0x10F243
            dst.p = src.p;                               // RE 0x10F25D
            src.p = nullptr;                             // RE 0x10F246, the null store
        };
        Owner a{reinterpret_cast<void*>(1), 3}, b{reinterpret_cast<void*>(2), 9};
        int releases = 0;
        moveAssign(a, b, releases);
        CHECK(releases == 1);                            // the old destination was released
        CHECK(a.p == reinterpret_cast<void*>(2));        // and took the source's
        CHECK(b.p == nullptr);                           // while the source is left empty
        CHECK(a.flag == 9);
        // the lazy flag: only the first call initialises
        const auto needsInit = [](unsigned char flag) { return flag == 0; };
        CHECK(needsInit(0));
        CHECK(!needsInit(1));
    }

    // --- the flag pair, slot +0x30, and the sentinel (RE 0x10fbb0) -----------------------------------
    {
        CHECK(kLazyInitFlag2 == 0x51);
        CHECK(kLazyInitFlag == 0x50);
        CHECK(kLazyInitFlag2 - kLazyInitFlag == kFlagPairStride);
        CHECK(kFlagPairStride == 1);
        CHECK(kFlagPairIdiom);
        CHECK(kFlagPairCount == 3);
        CHECK(kFinaliseFlagA == 0x28 && kFinaliseFlagB == 0x29);
        CHECK(kFinaliseFlagB - kFinaliseFlagA == kFlagPairStride);   // the same spacing there
        CHECK(kSlotBUsed);
        CHECK(kVtableSlotB == 0x30);
        CHECK(kSlotBArgConstant == 1);
        CHECK(kGateConstant == 1);                       // the same constant the guarded calls push
        CHECK(kNeighbourHelper == 0x10F8C0);
        CHECK(kNeighbourDelta == 0x2F0);
        CHECK(kNeighbourHelper + kNeighbourDelta == kLazyInit50);
        CHECK(kAllOnesSentinel == 0xFFFFFFFFFFFFFFFFULL);
        CHECK(kAllOnesSentinel == static_cast<std::uint64_t>(-1));
        CHECK(static_cast<std::int64_t>(kAllOnesSentinel) == -1);
        CHECK(kStatusSentinel == -1);                    // round 260's sentinel, the same value
        CHECK(kGlobalArgRva == 0x8F7E31);
        CHECK(kFinalCall10FBB0 == 0xC2510);
        CHECK(kSentinelUser == 0xC2EC0);

        // the three flag pairs, with the spacing between members of each
        const std::size_t pairs[3][2] = {{kFinaliseFlagA, kFinaliseFlagB},
                                         {kFinaliseFlagA, kFinaliseFlagB},
                                         {kLazyInitFlag, kLazyInitFlag2}};
        for (int i = 0; i < kFlagPairCount; ++i) {
            CHECK(pairs[i][1] - pairs[i][0] == kFlagPairStride);
        }
        CHECK(pairs[0][0] == pairs[1][0]);               // the first two are the same object's fields
        CHECK(pairs[2][0] != pairs[0][0]);               // the third is elsewhere
        // and the sentinel arithmetic
        CHECK(kAllOnesSentinel + 1 == 0);
        CHECK(~kAllOnesSentinel == 0);
    }

    // --- the twin pair and the atomic release (RE 0x111b50 and 0x862030) ----------------------------
    {
        CHECK(kLazyForceVariant == 0x111B50);
        CHECK(kLazyForceCallers == 21);
        CHECK(kSlot110Impl == 0xC2EC0);
        CHECK(kSlot110Impl == kSentinelUser);            // the routine its twin calls directly
        CHECK(kSlot110ImplInferred);                     // marked inferred, not read
        CHECK(kForceSetsFlagUnconditionally);
        CHECK(kTwinDelta326 == 0x1FA0);                // corrected in 326c: the delta is 0x1FA0
        CHECK(kLazyForceVariant - kLazyInit50 == kTwinDelta326);
        CHECK(kLazyInit50 == 0x10FBB0);
        CHECK(kLazyInitFlag == 0x50 && kLazyInitFlag2 == 0x51);
        CHECK(kVtableSlotE == 0x110);
        CHECK(kSlotBUsed);                               // the same slot +0x30 is used by both
        CHECK(kLocalConstruct2 == 0xC3A40);              // and the same init helper
        CHECK(kNeighbourHelper == 0x10F8C0);
        CHECK(kAllOnesSentinel == 0xFFFFFFFFFFFFFFFFULL);

        CHECK(kAtomicRelease == 0x862030);
        CHECK(kAtomicReleaseCallers == 20);
        CHECK(kRefcountOffset3 == 0x10);
        CHECK(kAtomicDecrement);
        CHECK(kReleaseIfBelowOne);
        CHECK(kDecrementAmount == -1);
        CHECK(kReleasePath == 0x862040);
        CHECK(kRefcountOffsetsKnown == 3);
        CHECK(kRefcountOffset3 != kRecordCounterA);      // a third offset, not merged with +0x08
        CHECK(kRefcountOffset3 != kRecordCounterB);      // nor with +0x0C
        CHECK(kRecordCounters == 2);

        // the atomic decrement's decision, for the values that matter
        const auto shouldRelease = [](std::int32_t old) { return old <= 0; };
        CHECK(shouldRelease(0));
        CHECK(shouldRelease(-1));
        CHECK(!shouldRelease(1));
        CHECK(!shouldRelease(2));
        // CORRECTED in round 326c: the xadd returns the OLD value and the branch is `jle`, so the release path
        // runs when the old value was at or below ZERO -- a count of one decrements to zero and does NOT release.
        std::int32_t count = 1;
        const std::int32_t old = count;
        count += kDecrementAmount;
        CHECK(old == 1);
        CHECK(!shouldRelease(old));                       // one becomes zero, no release
        CHECK(count == 0);
        std::int32_t already = 0;
        const std::int32_t old0 = already;
        already += kDecrementAmount;
        CHECK(old0 == 0);
        CHECK(shouldRelease(old0));                       // an already-zero counter releases
        CHECK(already == -1);
    }

    // --- the refcount trio and the borrow rule (RE 0x862040, 0x862050 and 0x86b750) ------------------
    {
        CHECK(kAtomicIncrement == 0x862050);
        CHECK(kAtomicReleaseTarget == 0x9984B0);
        CHECK(kAtomicReleaseTarget == kSharedDealloc);   // the release is the shared deallocator
        CHECK(kRefcountTrio == 3);
        CHECK(kRefcountPayloadOffset == 0x18);
        CHECK(kSharedDeallocSightings8 == 9);
        CHECK(kSharedDeallocSightings8 == kSharedDeallocSightings5 + 2);
        CHECK(kObtainRef == 0x86B750);
        CHECK(kObtainRefCallers == 12);
        CHECK(kBorrowFlagOffset == -8);
        CHECK(kRefcountBaseDelta == -0x18);
        CHECK(kBorrowSentinelNegative);
        CHECK(kBorrowPath == 0x86B780);
        CHECK(kCounterOffsetSites == 4);
        CHECK(k888FF0IsRefHolder);
        CHECK(kRefcountOffset3 == 0x10);                 // the counter the trio works on
        CHECK(kCtorForwardTarget == kObtainRef);         // and the constructor that reaches it
        CHECK(kAtomicRelease == 0x862030);

        // the layout the two routines agree on
        const std::ptrdiff_t base = kRefcountBaseDelta;
        CHECK(base + static_cast<std::ptrdiff_t>(kRefcountOffset3) == -8);   // the flag sits eight past the base
        CHECK(base == -0x18);
        CHECK(kBorrowFlagOffset == base + static_cast<std::ptrdiff_t>(kRefcountOffset3));   // -0x18 + 0x10 = -8
        CHECK(kRefcountPayloadOffset - kRefcountOffset3 == 8);     // payload eight past the counter
        // the trio's three operations, in order of what they do
        std::int32_t count = 1;
        ++count;                                          // RE 0x862050
        CHECK(count == 2);
        const std::int32_t old = count;
        count += kDecrementAmount;                        // RE 0x862035
        CHECK(old == 2 && count == 1);
        CHECK(!(old <= 0));                               // no release for a healthy count
        // and the borrow rule: a negative flag skips the increment
        const auto countsThis = [](std::int32_t flag) { return flag >= 0; };
        CHECK(countsThis(0));
        CHECK(countsThis(1));
        CHECK(!countsThis(-1));
        CHECK(kCounterOffsetSites * 4 == 16);
    }

    // --- the four-level teardown (RE 0x67db10) ------------------------------------------------------
    {
        CHECK(kNested4 == 0x67DB10);
        CHECK(kNested4Callers == 21);
        CHECK(kNested4Outer == 0x28);
        CHECK(kNested4Address == 0x18);
        CHECK(kNested4FieldA == 0x10);
        CHECK(kNested4FieldB == 0x18);
        CHECK(kNested4PairA == 0x28 && kNested4PairB == 0x30);
        CHECK(kNested4PairC == 0x18 && kNested4PairD == 0x20);
        CHECK(kNested4PairB - kNested4PairA == 8);
        CHECK(kNested4PairD - kNested4PairC == 8);
        CHECK(kNested4PairC == kNestedInnerBegin);       // round 254's inner pair, at a third level here
        CHECK(kNested4PairD == kNestedInnerEnd);
        CHECK(kNested4Helper == 0x939E00);
        CHECK(kNested4Levels == 4);
        CHECK(kNestedLayouts2 == 4);
        CHECK(kNestedLayouts == 4);
        CHECK(kSharedDeallocSightings9 == 10);
        CHECK(kSharedDeallocSightings9 == kSharedDeallocSightings5 + 3);
        CHECK(kNested4ReusesRound254Pair);
        CHECK(kSharedDealloc == 0x9984B0);
        CHECK(kNested4 != kNested3Begin);            // a distinct address from the other layouts

        // the four layouts' innermost strides and pairs, side by side
        struct Depth { std::size_t pairA, pairB; };
        const Depth depths[4] = {{kNestedOuterBegin, kNestedOuterEnd},
                                 {kNested2Begin, kNested2End},
                                 {kNested3Begin, kNested3End},
                                 {kNested4PairC, kNested4PairD}};
        for (int i = 0; i < 4; ++i) {
            CHECK(depths[i].pairB - depths[i].pairA == 8);
        }
        CHECK(depths[3].pairA == 0x18);              // the deepest level's pair starts at +0x18
        CHECK(kNestedLayouts == 4);
        CHECK(kNested4Levels > kNestedLayouts - 1);
    }

    // --- the list walk and the destruction order (RE 0x67db10) --------------------------------------
    {
        CHECK(kOuterIsLinkedList);
        CHECK(kListNextOffset == 0x10);
        CHECK(kListNextOffset == kNested4FieldA);        // the same field rounds 328 read as a level
        CHECK(kNested4Stages == 3);
        CHECK(kDestructionOrderRecorded);
        CHECK(kExitFreesFirstField);
        CHECK(kExitField == 0x00);
        CHECK(kNested4DepthReadingCorrected);            // my round-328 name for the shape, narrowed
        CHECK(kNested4Levels == 4);                      // the old count stands, its meaning does not
        CHECK(kSharedDeallocSightings10 == 11);
        CHECK(kSharedDeallocSightings10 == kSharedDeallocSightings5 + 4);
        CHECK(kSharedDealloc == 0x9984B0);
        CHECK(kNested4Helper == 0x939E00);

        // the walk the instructions implement: follow the next link until it is null
        struct Rec { int payload; Rec* next; };
        Rec c{3, nullptr}, b{2, &c}, a{1, &b};
        int visited = 0;
        for (Rec* p = &a; p != nullptr; p = p->next) {   // RE the re-entry at 0x67DBBF
            ++visited;
        }
        CHECK(visited == 3);
        CHECK(a.next == &b);
        CHECK(c.next == nullptr);
        // and the three stages, in the order the routine frees them
        const char* stages[3] = {"elements", "record array", "outer field"};
        CHECK(std::string(stages[0]) == "elements");
        CHECK(std::string(stages[2]) == "outer field");
        CHECK(kNested4Stages == 3);
    }

    // --- the twins' constructor and the corrected name (RE 0x111ad0) --------------------------------
    {
        CHECK(kTwinsCtor == 0x111AD0);
        CHECK(kTwinsCtorCallers == 21);
        CHECK(kTwinsCtorVtableRvaA == 0x934222);
        CHECK(kTwinsCtorVtableRvaB == 0x93439C);
        CHECK(kTwinsCtorVtableRvaA != kTwinsCtorVtableRvaB);
        CHECK(k50IsFlag);
        CHECK(k51IsValue);
        CHECK(k51FromArgument);
        CHECK(kFlagPairNarrowed);                        // my round-325 name, corrected
        CHECK(kPairIsFlagPlusValue);
        CHECK(kFlagPairIdiom);                           // the observation stands
        CHECK(kFlagPairCount == 3);                      // and so do the three sightings
        CHECK(kFlagPairStride == 1);
        CHECK(kCtorUsesFirstHelper);
        CHECK(kHelperFamilyBothObserved);
        CHECK(kLocalConstruct == 0xC33F0);               // the helper this constructor calls
        CHECK(kLocalConstruct2 == 0xC3A40);              // and the one the twins call
        CHECK(kLocalConstruct != kLocalConstruct2);
        CHECK(kTwinsCtor != kLazyInit50 && kTwinsCtor != kLazyForceVariant);
        CHECK(kLazyInitFlag == 0x50 && kLazyInitFlag2 == 0x51);
        CHECK(kLazyInitField == 0x48);

        // the state the constructor leaves, and the flag's meaning
        struct Obj { unsigned char flag; unsigned char value; };
        const auto construct = [](unsigned char arg) { Obj o{}; o.flag = 0; o.value = arg; return o; };
        const Obj a = construct(7);
        CHECK(a.flag == 0);                              // not yet initialised
        CHECK(a.value == 7);
        const Obj b = construct(0);
        CHECK(b.flag == 0 && b.value == 0);
        // the flag is therefore what the lazy initialiser tests, and the value is configuration
        const auto needsInit = [](const Obj& o) { return o.flag == 0; };
        CHECK(needsInit(a));
        CHECK(needsInit(b));
        CHECK(a.value != b.value);
    }

    // --- the forty-byte append and the prefix compare (RE 0x8ab830 and 0x82a450) --------------------
    {
        CHECK(kAppend40 == 0x8AB830);
        CHECK(kAppend40Callers == 20);
        CHECK(kElement40 == 0x28);
        CHECK(kElement40 == 40);
        CHECK(kElementQwords == 5);
        CHECK(kElementQwords * 8 == kElement40);
        CHECK(kContainerPairA == 0x08);
        CHECK(kContainerPairB == 0x10);
        CHECK(kContainerPairB - kContainerPairA == 8);
        CHECK(kGrow8AB5D0 == 0x8AB5D0);
        CHECK(kGrow8AB5D0 != kParserGrow);               // a different grow helper from the parser's
        CHECK(kPrefixCompare == 0x82A450);
        CHECK(kPrefixCompareCallers == 20);
        CHECK(kMinViaCmov);
        CHECK(kCompareSizeField == 0x08);
        CHECK(kCompareSizeField == kContainerPairA);
        CHECK(kCompareHelperSightings == 2);
        CHECK(kCompareHelperRoleIsCompare);
        CHECK(kCompareHelper == 0x63F300);
        CHECK(kCompareHelper == kMemcpyHelper + kCompareHelperDelta);
        CHECK(kAppend40 != kPrefixCompare);

        // the copy and the advance the append performs
        const auto bytesCopied = [](int qwords) { return qwords * 8; };
        CHECK(bytesCopied(kElementQwords) == kElement40);
        CHECK(kElement40 * 2 == 80);
        // the min the compare computes, by the same rule cmovbe uses
        const auto minOf = [](std::uint64_t a, std::uint64_t b) { return a <= b ? a : b; };
        CHECK(minOf(3, 5) == 3);
        CHECK(minOf(5, 3) == 3);
        CHECK(minOf(4, 4) == 4);
        CHECK(minOf(0, 7) == 0);
        // and the outcome rule: zero bytes compared means equal so far
        CHECK(minOf(0, 0) == 0);
        CHECK(kCompareHelperSightings * 4 == 8);
    }

    // --- three threads meeting (RE 0x10f200 and 0xf7260) --------------------------------------------
    {
        CHECK(kCtor10F200 == 0x10F200);
        CHECK(kCtor10F200Callers == 20);
        CHECK(kCtor10F200VtableRva == 0x939AD9);
        CHECK(kFlagAt10 == 0x10);
        CHECK(kFlagAt10 == kMoveByte);                   // the same byte the move of round 324 copies
        CHECK(kFlagAt10InitOne);
        CHECK(kMoveAssignment == 0x10F220);
        CHECK(kMoveAssignment - kCtor10F200 == 0x20);    // the constructor sits a step before the move

        CHECK(kFunctionF7260 == 0xF7260);
        CHECK(kFunctionF7260Callers == 20);
        CHECK(kFunctionF7260VtableRva == 0x95A45B);
        CHECK(kGlobalGuardRva == 0x91084E);
        CHECK(kF7260Helper == 0xF7010);
        CHECK(kFunctionF7260FieldA == 0x10);
        CHECK(kFunctionF7260FieldB == 0x18);
        CHECK(kInputBufferCtor == 0x77A460);
        CHECK(kInputBufferCtorCallSites == 2);           // rounds 288 and this
        CHECK(kLazyInitCallee == 0xEEEE0);
        CHECK(kLazyInitCalleeSightings == 2);            // rounds 259 and this
        CHECK(kTagUwvshRva == 0xF72C8);
        CHECK(kTagUwvsh == 3);                           // rounds 263, 281 and this
        CHECK(kTypeTagStoredAtZero);
        CHECK(kTypeTagIsAMarker);
        CHECK(kTypeLiteralSite == 0x11A7DF);             // one of the earlier sightings
        CHECK(kFunctionF7260FieldA != kFunctionF7260FieldB);

        // the state the two constructors leave
        struct Moved { void* p; unsigned char b; };
        const auto ctor10F200 = [] { Moved m{}; m.p = nullptr; m.b = 1; return m; };
        const Moved a = ctor10F200();
        CHECK(a.p == nullptr);
        CHECK(a.b == 1);
        // and the tag marker the other routine installs
        const std::string tag = "UWVSH";
        CHECK(tag.size() == 5);
        CHECK(tag == std::string("UWVSH"));
        CHECK(kTagUwvsh == 3);
        CHECK(kInputBufferCtorCallSites + kLazyInitCalleeSightings == 4);
    }

    return check::finish("test_recovered");
}
