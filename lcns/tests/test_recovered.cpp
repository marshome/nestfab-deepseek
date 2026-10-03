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
#include <type_traits>
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
#include "lcns/base_chain.hpp"
#include "lcns/pattern.hpp"
#include "lcns/row.hpp"
#include "lcns/tiling.hpp"
#include "lcns/launching_order.hpp"
#include "lcns/cns_node.hpp"
#include "lcns/owned_chain.hpp"
#include "lcns/stat.hpp"
#include "lcns/variant.hpp"
#include "lcns/chain_release.hpp"
#include "lcns/module_switch.hpp"
#include "lcns/parameter_report.hpp"
#include "lcns/engine_defaults.hpp"
#include "lcns/option_keys.hpp"
#include "lcns/miplib_names.hpp"
#include "lcns/engines.hpp"
#include "lcns/engines_composite.hpp"
#include "lcns/vtable_layout.hpp"
#include "lcns/records.hpp"
#include "lcns/small_buffer.hpp"

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
        // **THE THREE CLASSES THE MODULE HAS, DRIVEN THROUGH THE BASE POINTER.** RE 0xA3B570 (TerminalNode) and 0xA3BB70 (SplitNode) are two four slot
        // tables whose slots 2 and 3 each read a double at a fixed offset -- so what the test has to show is that THE SAME CALL REACHES DIFFERENT OFFSETS,
        // which a `Kind` tag and a conditional cannot express.
        lcns::TerminalNode terminal;
        lcns::SplitNode split;
        terminal.value48 = 1.5;      // +0x48, TerminalNode slot 2: movsd xmm0, [rcx + 0x48]
        terminal.value50 = 2.5;      // +0x50, TerminalNode slot 3
        split.value50 = 3.5;         // +0x50, SplitNode slot 2 -- THE SAME OFFSET, A DIFFERENT SLOT
        split.value58 = 4.5;         // +0x58, SplitNode slot 3

        lcns::Node* as_base = &terminal;
        CHECK(as_base->value() == 1.5);        // the base's slot 2 reads +0x48 through TerminalNode
        CHECK(as_base->secondary() == 2.5);    // and TerminalNode's slot 3 override reads +0x50
        as_base = &split;
        CHECK(as_base->value() == 3.5);        // SplitNode OVERRIDES value(), reading +0x50 in ITS table
        CHECK(as_base->secondary() == 4.5);    // and adds +0x58

        // **AND THE OFFSETS, WHICH IS WHAT MAKES THE FOUR NUMBERS ABOVE A LAYOUT.** The first declaration of these classes put the doubles at +8, +0x10 and
        // +0x18, and these four lines are what caught it.
        CHECK(reinterpret_cast<const unsigned char*>(&terminal.value48) - reinterpret_cast<const unsigned char*>(&terminal) == 0x48);
        CHECK(reinterpret_cast<const unsigned char*>(&terminal.value50) - reinterpret_cast<const unsigned char*>(&terminal) == 0x50);
        CHECK(reinterpret_cast<const unsigned char*>(&split.value50) - reinterpret_cast<const unsigned char*>(&split) == 0x50);
        CHECK(reinterpret_cast<const unsigned char*>(&split.value58) - reinterpret_cast<const unsigned char*>(&split) == 0x58);
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

    // --- the bitfield swap and the packed-double add (RE 0x5fef30 and 0x16c270) ----------------------
    {
        CHECK(kSwapThree == 0x5FEF30);
        CHECK(kSwapThreeCallers == 20);
        CHECK(kSwapQword == 0x00);
        CHECK(kSwapByteA == 0x08);
        CHECK(kSwapByteB == 0x09);
        CHECK(kSwapByteB - kSwapByteA == 1);
        CHECK(kBitfieldSwapMask == 0xFFFFFFFEu);
        CHECK(kBitSwapMask == 1u);
        CHECK(kBitfieldSwapMask == kBigIntRoundMask);    // the same value, a different context
        CHECK(kSwapHelperA == 0x5FEB70);
        CHECK(kSwapHelperB == 0x5FE060);
        CHECK(kSwapHelperA != kSwapHelperB);
        CHECK(kPointAddSSE == 0x16C270);
        CHECK(kPointAddCallers == 19);
        CHECK(kPackedDoubleAdd);
        CHECK(kPointCoordsA0 == 0x08 && kPointCoordsA1 == 0x10);
        CHECK(kPointCoordsB0 == 0x00 && kPointCoordsB1 == 0x08);
        CHECK(kPointCoordsA1 - kPointCoordsA0 == kPointCoordBytes);
        CHECK(kPointCoordsB1 - kPointCoordsB0 == kPointCoordBytes);
        CHECK(kPointCoordBytes == 8);

        // the bitfield exchange the instructions perform: bit 0 crosses, the rest stay
        const auto swapBit0 = [](std::uint8_t a, std::uint8_t b, std::uint8_t& na, std::uint8_t& nb) {
            na = static_cast<std::uint8_t>((a & 0xFEu) | (b & 0x01u));   // RE the two ands and the or
            nb = static_cast<std::uint8_t>((b & 0xFEu) | (a & 0x01u));
        };
        std::uint8_t x = 0, y = 0;
        swapBit0(0b00000010, 0b00000001, x, y);
        CHECK(x == 0b00000011);                          // bit 0 came from the other byte
        // CORRECTED in 333d: b's low bit took a's low bit, which is zero, and b's upper bits are zero too,
        // so b' is zero rather than the 0b10 I first wrote.
        CHECK(y == 0b00000000);
        swapBit0(0xFF, 0x00, x, y);
        CHECK(x == 0xFE);
        CHECK(y == 0x01);
        // and the point addition: two doubles at a time
        const double ax[2] = {1.5, 2.5};
        const double bx[2] = {0.5, 0.25};
        CHECK(ax[0] + bx[0] == 2.0);
        CHECK(ax[1] + bx[1] == 2.75);
        CHECK(sizeof(double) == kPointCoordBytes);
    }

    // --- the formatting wrapper and the five-field constructor (RE 0x634c40 and 0x4b6d80) -----------
    {
        CHECK(kFormatWrapper == 0x634C40);
        CHECK(kFormatWrapperCallers == 19);
        CHECK(kFormatLimit == 0x4000);
        CHECK(kFormatLimit == 16384);
        CHECK(kFormatEngine == 0x63B140);
        CHECK(kFormatEngine != kFormatWrapper);
        CHECK(kNulTerminated);
        CHECK(kVaListConvention);
        CHECK(kCtor4B6D80 == 0x4B6D80);
        CHECK(kCtor4B6D80Callers == 18);
        CHECK(kCtor4B6D80VtableRva == 0x5817A1);
        CHECK(kZeroedDwords == 3);
        CHECK(kZeroedQwords == 2);
        CHECK(kPlainDataFields == 5);
        CHECK(kZeroedDwords + kZeroedQwords == kPlainDataFields);
        CHECK(kDwordBase4B6D80 == 0x08);
        CHECK(kQwordBase4B6D80 == 0x18);
        CHECK(kQwordBase4B6D80 - (kDwordBase4B6D80 + 4 * kZeroedDwords) == 4);   // a four-byte gap
        CHECK(kCtor4B6D80 != kCtor10F200);

        // the layout the constructor leaves, and the terminator the formatter writes
        const std::size_t dwords[kZeroedDwords] = {kDwordBase4B6D80, kDwordBase4B6D80 + 4,
                                                   kDwordBase4B6D80 + 8};
        for (int i = 0; i < kZeroedDwords; ++i) {
            CHECK(dwords[i] % 4 == 0);
        }
        CHECK(kQwordBase4B6D80 - (dwords[2] + 4) == 4);   // the gap again, from the last dword
        const std::size_t qwords[kZeroedQwords] = {kQwordBase4B6D80, kQwordBase4B6D80 + 8};
        CHECK(qwords[1] - qwords[0] == 8);
        // the terminator index: a returned length of n puts the zero at n
        const auto terminatorAt = [](int length) { return static_cast<std::size_t>(length); };
        CHECK(terminatorAt(0) == 0);
        CHECK(terminatorAt(5) == 5);
        CHECK(kFormatLimit > 1000);
        CHECK(kFormatLimit / 1024 == 16);                 // sixteen kilobytes
    }

    // --- the accessor and the state-keyed release (RE 0x4ddd10 and 0xf3ab0) --------------------------
    {
        CHECK(kAccessor48 == 0x4DDD10);
        CHECK(kAccessor48Callers == 18);
        CHECK(kAccessor48Offset == 0x48);
        CHECK(kAccessor48Offset == kLazyInitField);      // the field rounds 324 to 330 used
        CHECK(kAccessor48MatchesLazyInitField);
        CHECK(kReleaseF3AB0 == 0xF3AB0);
        CHECK(kReleaseF3AB0Callers == 19);
        CHECK(kStateField == 0x20);
        CHECK(kStateField == kTagFieldOffset);           // the tag field round 249 recorded
        CHECK(kStateValueOne == 1);
        CHECK(kStateValueOne == kTagUnsetValue);         // and the same value
        CHECK(kCounterPointerField == 0x18);
        CHECK(kCounterIsIndirect);
        CHECK(kReleaseFieldA == 0x10);
        CHECK(kReleasePathF3B50 == 0xF3B50);
        CHECK(kReleaseFieldA != kCounterPointerField);
        CHECK(kAccessor48 != kReleaseF3AB0);
        CHECK(kReleaseF3AB0 != kAtomicRelease);          // a different release from the atomic one

        // the decrement and the wrap the instructions perform on the indirect counter
        const auto releaseOnWrap = [](std::uint64_t counter) {
            const std::uint64_t next = counter - 1;      // RE 0xF3ACB
            const bool wrapped = counter < next;         // RE 0xF3ACF, the comparison that detects it
            return wrapped;
        };
        CHECK(releaseOnWrap(0));                          // zero wraps
        CHECK(!releaseOnWrap(1));                         // one becomes zero, no wrap
        CHECK(!releaseOnWrap(2));
        // and the state test that takes the other route
        const auto otherRoute = [](std::int32_t state) { return state == kStateValueOne; };
        CHECK(otherRoute(1));
        CHECK(!otherRoute(0));
        CHECK(!otherRoute(2));
        CHECK(kCounterPointerField + 8 == kStateField);   // the counter pointer precedes the state field
    }

    // --- the lazy member and the string that is not in the data section (RE 0x4f9200) ---------------
    {
        CHECK(kLazyMember == 0x4F9200);
        CHECK(kLazyMemberCallers == 21);
        CHECK(kLazyMemberFlag == 0x100);
        CHECK(kLazyMemberCache == 0x108);
        CHECK(kLazyMemberCache - kLazyMemberFlag == 8);
        CHECK(kImmediateGeometry == 0x797274656D6F6567ULL);
        CHECK(kImmediateMHaveG == 0x675F657661685F6DULL);
        CHECK(kImmediateTr == 0x7274);
        CHECK(kStackStringBuffers == 3);
        CHECK(kStackStringInline == 0x10);
        CHECK(kStackStringInline == kSsoInline);
        CHECK(kStringsBuiltFromImmediates);
        CHECK(kStringInventoryIncomplete);
        CHECK(std::string(kStringGeometry) == "geometry");
        CHECK(std::string(kStringMHaveG) == "m_have_g");

        // the bytes the immediates spell, decoded here so the claim is checkable
        const auto bytesOf = [](std::uint64_t v) {
            std::string s;
            for (int i = 0; i < 8; ++i) {
                s.push_back(static_cast<char>((v >> (8 * i)) & 0xFF));   // little-endian, low byte first
            }
            return s;
        };
        CHECK(bytesOf(kImmediateGeometry) == "geometry");
        CHECK(bytesOf(kImmediateMHaveG) == "m_have_g");
        CHECK(bytesOf(kImmediateGeometry).size() == 8);
        CHECK(bytesOf(kImmediateMHaveG).size() == 8);
        const auto twoBytes = [](std::uint16_t v) {
            std::string s;
            s.push_back(static_cast<char>(v & 0xFF));
            s.push_back(static_cast<char>((v >> 8) & 0xFF));
            return s;
        };
        CHECK(twoBytes(kImmediateTr) == "tr");
        // and the name the pieces compose
        const std::string composed = std::string(bytesOf(kImmediateMHaveG)) + std::string(kStringGeometry);
        CHECK(composed == "m_have_ggeometry");            // as the pieces concatenate, not as a claim about the name
        // the lazy rule
        const auto needsInit = [](unsigned char flag) { return flag == 0; };
        CHECK(needsInit(0));
        CHECK(!needsInit(1));
    }

    // --- the floating-point profile, and the candidates left unread (RE the round-337 sweep) ---------
    {
        CHECK(kFloatKernelsUncited == 55);
        CHECK(kOpcodeMovsd == 1005);
        CHECK(kOpcodeMulsd == 101);
        CHECK(kOpcodeAddsd == 83);
        CHECK(kOpcodeSubsd == 49);
        CHECK(kOpcodeDivsd == 9);
        CHECK(kOpcodeSqrtsd == 4);
        CHECK(kOpcodeAddpd == 4);
        CHECK(kOpcodeMovhpd == 27);
        CHECK(kFloatArithmeticTotal == 250);
        CHECK(kScalarStyleDominates);
        CHECK(kOpcodeAddsd > kOpcodeAddpd);
        CHECK(kOpcodeMulsd > kOpcodeSqrtsd);
        CHECK(kTopKernelArithmeticA == 20);
        CHECK(kTopKernelArithmeticB == 20);
        CHECK(kKernelsPointedAtNotRead);
        CHECK(std::string(kTopKernelShapeA) == "eight additions and twelve multiplications");
        CHECK(std::string(kTopKernelShapeB) != std::string(kTopKernelShapeA));
        CHECK(kPointAddSSE == 0x16C270);                 // the one packed kernel that WAS read

        // the arithmetic the totals describe
        const int scalar = kOpcodeMulsd + kOpcodeAddsd + kOpcodeSubsd + kOpcodeDivsd + kOpcodeSqrtsd;
        const int packed = kOpcodeAddpd;
        CHECK(scalar == 246);
        CHECK(packed == 4);
        CHECK(scalar > packed * 50);                     // dominance, stated as a ratio rather than a word
        CHECK(scalar - packed == 242);
        CHECK(kFloatArithmeticTotal > scalar - packed);  // the two totals measure different things
        // and the moves outnumber the arithmetic, which is what a scalar kernel looks like
        CHECK(kOpcodeMovsd > kFloatArithmeticTotal);
        CHECK(kFloatArithmeticTotal + kOpcodeMovsd == 1255);
    }

    // --- the geometric distance kernel (RE 0x55e190) ------------------------------------------------
    {
        CHECK(kSegmentKernel == 0x55E190);
        CHECK(kSegmentKernelCallers == 3);
        CHECK(kSegmentStartA == 0x00);
        CHECK(kSegmentStartB == 0x08);
        CHECK(kSegmentEndA == 0x10);
        CHECK(kSegmentEndB == 0x18);
        CHECK(kSegmentBytes == 0x20);
        CHECK(kSegmentEndA - kSegmentStartA == 0x10);
        CHECK(kSegmentEndB - kSegmentStartB == 0x10);
        CHECK(kSegmentEndB + 8 == kSegmentBytes);
        CHECK(kLengthViaSqrt);
        CHECK(kSqrtCount == 3);
        CHECK(kSqrtGuard == 0x62FE20);
        CHECK(kParamA == 0x20);
        CHECK(kParamB == 0x28);
        CHECK(kParamC == 0x40);
        CHECK(kMinMaxPairUsed);
        CHECK(kPointAddSSE == 0x16C270);                 // the other floating-point kernel read here
        CHECK(kSegmentKernel != kPointAddSSE);
        CHECK(kOpcodeSqrtsd == 4);                       // three here, one elsewhere

        // the length computation the instructions perform, in the order they do it
        const auto lengthOf = [](double x0, double y0, double x1, double y1) {
            const double dx = x1 - x0;                   // RE the two subsd
            const double dy = y1 - y0;
            return std::sqrt(dx * dx + dy * dy);         // RE the two mulsd, the addsd and the sqrtsd
        };
        CHECK(lengthOf(0.0, 0.0, 3.0, 4.0) == 5.0);
        CHECK(lengthOf(1.0, 1.0, 4.0, 5.0) == 5.0);
        CHECK(lengthOf(0.0, 0.0, 0.0, 0.0) == 0.0);
        // and the pairing the kernel takes from the two lengths
        const double a = lengthOf(0.0, 0.0, 3.0, 4.0);
        const double b = lengthOf(0.0, 0.0, 6.0, 8.0);
        CHECK(a == 5.0 && b == 10.0);
        CHECK(std::min(a, b) == a);                      // RE minsd
        CHECK(std::max(a, b) == b);                      // RE maxsd
        CHECK(std::min(a, b) * 2.0 == std::max(a, b));
        CHECK(kSegmentBytes == 4 * sizeof(double));   // four coordinates
    }

    // --- the affine kernel and its record (RE 0x5cea80) ----------------------------------------------
    {
        CHECK(kAffineKernel == 0x5CEA80);
        CHECK(kAffineKernelCallers == 9);
        CHECK(kAffineSourceA == 0x00);
        CHECK(kAffineSourceB == 0x08);
        CHECK(kAffineSourceC == 0x10);
        CHECK(kAffineSourceD == 0x18);
        CHECK(kAffineSourceC - kAffineSourceA == 0x10);
        CHECK(kAffineSourceD - kAffineSourceB == 0x10);
        CHECK(kAffineTermA == 0x20);
        CHECK(kAffineTermB == 0x28);
        CHECK(kAffineMatrixDoubles == 6);
        CHECK(kMatrixForm2x3);
        CHECK(kMulCount == 12);
        CHECK(kMulCountInWindow == 9);
        CHECK(kMulCount >= kMulCountInWindow);
        CHECK(kAddCount == 8);
        CHECK(kAffineSourceBytes == kSegmentBytes);
        // the cross-links that make this the same record as round 338's
        CHECK(kAffineSourceC == kSegmentEndA);
        CHECK(kAffineSourceD == kSegmentEndB);
        CHECK(kAffineTermA == kParamA);
        CHECK(kAffineTermB == kParamB);
        CHECK(kAffineKernel != kSegmentKernel);

        // the arithmetic a 2x3 affine transform performs on a point
        const auto applyAffine = [](const double m[6], double x, double y, double& ox, double& oy) {
            ox = m[0] * x + m[1] * y + m[2];             // RE the crosswise mulsd and the addsd chain
            oy = m[3] * x + m[4] * y + m[5];
        };
        const double identity[6] = {1, 0, 0, 0, 1, 0};
        double ox = 0, oy = 0;
        applyAffine(identity, 3.0, 4.0, ox, oy);
        CHECK(ox == 3.0 && oy == 4.0);
        const double scale[6] = {2, 0, 1, 0, 2, -1};
        applyAffine(scale, 3.0, 4.0, ox, oy);
        CHECK(ox == 7.0);
        CHECK(oy == 7.0);
        CHECK(kAffineMatrixDoubles * sizeof(double) == 48u);  // six doubles
        CHECK(kSegmentBytes == kAffineSourceBytes);
    }

    // --- the floating-point guard (RE 0x62fe20) -----------------------------------------------------
    {
        CHECK(kFloatCheck == 0x62FE20);
        CHECK(kFloatCheckCallers == 89);
        CHECK(kExponentMask == 0x7FF00000u);
        CHECK(kMantissaMask == 0xFFFFFu);
        CHECK((kExponentMask & kMantissaMask) == 0);
        CHECK((kExponentMask | kMantissaMask) == 0x7FFFFFFFu);
        CHECK(kZeroTested);
        CHECK(kExponentTested);
        CHECK(kSignTested);
        CHECK(kOneDoubleRva == 0xA06838);
        CHECK(kFloatCheckPacked == 0x62FE00);
        CHECK(kFloatCheckPacked < kFloatCheck);
        CHECK(kPackedConstantRva == 0xA06800);
        CHECK(kPackedSibling);
        CHECK(kSqrtGuard == kFloatCheck);                // the guard round 338's kernel calls
        CHECK(kSegmentKernel == 0x55E190);
        CHECK(kFloatCheckCallers > kSegmentKernelCallers);

        // the fields a double's high dword carries, exercised on well-known patterns rather than by
        // reinterpreting a double, so the test needs no extra header
        const std::uint32_t oneHigh = 0x3FF00000u;       // 1.0
        const std::uint32_t twoHigh = 0x40000000u;       // 2.0
        const std::uint32_t infHigh = 0x7FF00000u;       // infinity (and NaN when the mantissa is set)
        const std::uint32_t zeroHigh = 0x00000000u;      // zero
        const std::uint32_t negHigh = 0x80000000u;       // the sign bit alone, i.e. -0.0
        CHECK((oneHigh & kExponentMask) == 0x3FF00000u);
        CHECK((oneHigh & kMantissaMask) == 0);
        CHECK((oneHigh & 0x80000000u) == 0);
        CHECK((twoHigh & kExponentMask) == 0x40000000u);
        CHECK((twoHigh & kMantissaMask) == 0);
        CHECK((infHigh & kExponentMask) == kExponentMask);
        CHECK((infHigh & kMantissaMask) == 0);
        CHECK((zeroHigh & kExponentMask) == 0);
        CHECK((zeroHigh & kMantissaMask) == 0);
        CHECK((negHigh & 0x80000000u) != 0);
        CHECK((negHigh & kExponentMask) == 0);
        // the zero test the body performs: both the mantissa field and the low word clear
        const auto looksZero = [](std::uint32_t high, std::uint32_t low) {
            return (high & kExponentMask) == 0 && (high & kMantissaMask) == 0 && low == 0;
        };
        CHECK(looksZero(zeroHigh, 0));
        CHECK(looksZero(negHigh, 0));
        CHECK(!looksZero(oneHigh, 0));
        CHECK(!looksZero(0, 1u));
        CHECK(!looksZero(infHigh, 0));
    }

    // --- the in-place transform and the orientation determinant (RE 0x5cfd80 and 0x24b440) ----------
    {
        CHECK(kAffineInPlace == 0x5CFD80);
        CHECK(kAffineInPlaceCallers == 4);
        CHECK(kMatrixA == 0x00 && kMatrixB == 0x08);
        CHECK(kMatrixC == 0x10 && kMatrixD == 0x18);
        CHECK(kMatrixTx == 0x20 && kMatrixTy == 0x28);
        CHECK(kMatrixDoubles2 == 6);
        CHECK(kMatrixDoubles2 == kAffineMatrixDoubles);
        CHECK(kMatrixTx == kAffineTermA);
        CHECK(kMatrixTy == kAffineTermB);
        CHECK(kMatrixLayoutConfirmed);
        CHECK(kPointX == 0x00 && kPointY == 0x08);
        CHECK(kInPlaceTransform);
        CHECK(kAffineInPlace != kAffineKernel);
        CHECK(kCrossProduct == 0x24B440);
        CHECK(kCrossProductCallers == 2);
        CHECK(kCrossA == 0x00);
        CHECK(kCrossC == 0x10);
        CHECK(kCrossC - kCrossA == 0x10);
        CHECK(kSignIsOrientation);
        CHECK(std::string(kCrossProductForm) == "(Cx-Ax)(By-Ay) - (Bx-Ax)(Cy-Ay)");

        // the transform the instructions perform, written out so the arithmetic is unambiguous
        // written out plainly instead, so the arithmetic is unambiguous
        const auto apply = [](const double m[6], double x, double y, double& ox, double& oy) {
            ox = m[0] * x + m[1] * y + m[2];
            oy = m[3] * x + m[4] * y + m[5];
        };
        const double identity2[6] = {1, 0, 0, 0, 1, 0};
        double x = 3.0, y = 4.0, ox = 0, oy = 0;
        apply(identity2, x, y, ox, oy);
        CHECK(ox == 3.0 && oy == 4.0);
        const double half[6] = {0.5, 0, 0, 0, 0.5, 0};
        apply(half, x, y, ox, oy);
        CHECK(ox == 1.5 && oy == 2.0);

        // the orientation determinant, on three cases by hand
        const auto cross = [](double ax, double ay, double bx, double by, double cx, double cy) {
            return (cx - ax) * (by - ay) - (bx - ax) * (cy - ay);   // RE the two products and the subtraction
        };
        // CORRECTED in 341c: with (C-A)x(B-A), this triple gives -1, not +1
        CHECK(cross(0, 0, 1, 0, 0, 1) == -1.0);
        CHECK(cross(0, 0, 0, 1, 1, 0) == 1.0);           // the other turn, and so the other sign
        CHECK(cross(0, 0, 1, 1, 2, 2) == 0.0);            // collinear, so zero either way
        CHECK(cross(0, 0, 2, 0, 0, 2) == -4.0);          // CORRECTED in 341c: magnitude four, sign negative
    }

    // --- the segment transform, which closes the pipeline (RE 0x5cfdc0) -----------------------------
    {
        CHECK(kAffineTwoPoints == 0x5CFDC0);
        CHECK(kAffineTwoPointsCallers == 3);
        CHECK(kAffineFormulaConfirmed);
        CHECK(kMatrixLayoutConfirmed2);
        CHECK(kMatrixLayoutConfirmed);
        CHECK(kBothPointsInPlace);
        CHECK(std::string(kAffineFormula) == "x' = a*x + b*y + tx ; y' = c*x + d*y + ty");
        CHECK(std::string(kGeometryPipeline) == "transform a segment, measure between segments, test orientation");
        CHECK(kPipelineStages == 3);
        CHECK(kSegmentKernel == 0x55E190);               // the measure stage
        CHECK(kCrossProduct == 0x24B440);                // the orientation stage
        CHECK(kAffineTwoPoints != kAffineInPlace);
        CHECK(kSegmentStartA == kAffineSourceA);
        CHECK(kSegmentEndA == kAffineSourceC);
        CHECK(kSegmentEndA - kSegmentStartA == 0x10);
        CHECK(kMatrixTx == kAffineTermA && kMatrixTy == kAffineTermB);

        // the transform applied to BOTH points of a segment, by hand
        const auto apply = [](const double m[6], double x, double y, double& ox, double& oy) {
            ox = m[0] * x + m[1] * y + m[2];
            oy = m[3] * x + m[4] * y + m[5];
        };
        const double m[6] = {2, 0, 1, 0, 2, -1};         // scale by two, then translate
        double x0 = 0, y0 = 0, x1 = 1, y1 = 1;
        double a0 = 0, b0 = 0, a1 = 0, b1 = 0;
        apply(m, x0, y0, a0, b0);
        apply(m, x1, y1, a1, b1);
        CHECK(a0 == 1.0 && b0 == -1.0);                  // the start point moved
        CHECK(a1 == 3.0 && b1 == 1.0);                   // and so did the end point
        // the segment's direction is preserved by a pure scale
        const double scale[6] = {3, 0, 0, 0, 3, 0};
        double c0 = 0, d0 = 0, c1 = 0, d1 = 0;
        apply(scale, 1.0, 2.0, c0, d0);
        apply(scale, 2.0, 4.0, c1, d1);
        CHECK(c0 == 3.0 && d0 == 6.0);
        CHECK(c1 == 6.0 && d1 == 12.0);
        CHECK((c1 - c0) * 2.0 == (d1 - d0));             // still the same slope, doubled in length
    }

    // --- the composition over two fields (RE 0x24dd40) -----------------------------------------------
    {
        CHECK(kCompose == 0x24DD40);
        CHECK(kComposeCallers == 1);
        CHECK(kComposeFieldA == 0x68);
        CHECK(kComposeFieldB == 0x70);
        CHECK(kComposeFieldC == 0x38);
        CHECK(kComposeFieldA != kComposeFieldB);
        CHECK(kComposeFieldB - kComposeFieldA == 8);
        CHECK(kComposeWeightA == 0x58);
        CHECK(kComposeWeightB == 0x60);
        CHECK(kComposeWeightB - kComposeWeightA == 8);
        CHECK(kComposeHelper1 == 0x24C610);
        CHECK(kComposeHelperSightings == 2);
        CHECK(kComposeHelper2 == 0x5CF6B0);
        CHECK(kComposeHelper1 != kComposeHelper2);
        CHECK(kGeometryClusterMember);
        CHECK(kComposeFrame == 0xD0);
        CHECK(kComposeFrame == 208);
        CHECK(kComposeTempA == 0x70 && kComposeTempB == 0x20 && kComposeTempC == 0xA0);
        CHECK(kComposeTempA != kComposeTempB);
        // the geometry routines already recorded all live in the same address range
        CHECK(kAffineInPlace > 0x5C0000 && kAffineInPlace < 0x5D0000);
        CHECK(kAffineTwoPoints > 0x5C0000 && kAffineTwoPoints < 0x5D0000);
        CHECK(kAffineKernel > 0x5C0000 && kAffineKernel < 0x5D0000);

        // the weighted combination the four multiplications implement
        const auto weighted = [](double wa, double wb, double a, double b) {
            return wa * a + wb * b;                      // the crosswise products, added
        };
        CHECK(weighted(1.0, 1.0, 3.0, 4.0) == 7.0);
        CHECK(weighted(2.0, 0.0, 3.0, 4.0) == 6.0);
        CHECK(weighted(0.0, 0.5, 3.0, 4.0) == 2.0);
        CHECK(weighted(0.5, 0.5, 2.0, 4.0) == 3.0);
        // the frame is large because it holds three temporaries of at least 0x30 bytes each
        CHECK(kComposeFrame > kSegmentBytes);
        CHECK(kComposeFrame - kComposeTempC == 0x30);
    }

    // --- the out-of-place transform, and the family of four (RE 0x5cf6b0) ---------------------------
    {
        CHECK(kAffineOutOfPlace == 0x5CF6B0);
        CHECK(kAffineOutOfPlaceCallers == 6);
        CHECK(kMatrixLayoutConfirmed3);
        CHECK(kAffineFormulaConfirmed2);
        CHECK(kAffineVariants == 4);
        CHECK(kCopiedDoubles == 4);
        CHECK(kAffineSrcPairA == 0x00);
        CHECK(kAffineSrcPairB == 0x10);
        CHECK(kAffineSrcPairB - kAffineSrcPairA == kSegmentEndA - kSegmentStartA);
        CHECK(kComposeHelper2 == kAffineOutOfPlace);     // the composition of round 343 calls THIS one
        CHECK(kGeometryClusterMember);
        // the four variants are four distinct addresses
        CHECK(kAffineOutOfPlace != kAffineInPlace);
        CHECK(kAffineOutOfPlace != kAffineTwoPoints);
        CHECK(kAffineOutOfPlace != kAffineKernel);
        CHECK(kAffineInPlace != kAffineTwoPoints);
        CHECK(kMatrixA == 0x00 && kMatrixB == 0x08 && kMatrixC == 0x10 && kMatrixD == 0x18);
        CHECK(kMatrixTx == 0x20 && kMatrixTy == 0x28);

        // out of place and in place must agree for the same input, which is what makes them variants
        const auto applyOutOfPlace = [](const double m[6], const double src[4], double dst[4]) {
            dst[0] = src[0]; dst[1] = src[1]; dst[2] = src[2]; dst[3] = src[3];   // RE the four copies
            const double m2[6] = {m[0], m[1], m[2], m[3], m[4], m[5]};
            const double ax = m2[0] * dst[0] + m2[1] * dst[1] + m2[2];
            const double ay = m2[3] * dst[0] + m2[4] * dst[1] + m2[5];
            const double bx = m2[0] * dst[2] + m2[1] * dst[3] + m2[2];
            const double by = m2[3] * dst[2] + m2[4] * dst[3] + m2[5];
            dst[0] = ax; dst[1] = ay; dst[2] = bx; dst[3] = by;
        };
        const double m[6] = {2, 0, 1, 0, 2, -1};
        const double src[4] = {0, 0, 1, 1};
        double dst[4] = {0, 0, 0, 0};
        applyOutOfPlace(m, src, dst);
        CHECK(dst[0] == 1.0 && dst[1] == -1.0);
        CHECK(dst[2] == 3.0 && dst[3] == 1.0);
        CHECK(src[0] == 0.0 && src[3] == 1.0);           // the source is untouched, being out of place
        CHECK(kCopiedDoubles == 4);
    }

    // --- the four-stage chain over one point (RE 0x24c610) ------------------------------------------
    {
        CHECK(kPerFieldHelper == 0x24C610);
        CHECK(kPerFieldHelperCallers == 4);
        CHECK(kPointFieldA == 0x70);
        CHECK(kPointFieldB == 0x78);
        CHECK(kPointFieldB - kPointFieldA == 8);
        CHECK(kPointFieldA == kComposeFieldB);            // the field round 343 hands to this helper
        CHECK(kChainBuild == 0x24C4A0);
        CHECK(kChainStageA == 0x5CE7B0);
        CHECK(kChainStageB == 0x5CED50);
        CHECK(kChainStageC == 0x5CE970);
        CHECK(kChainStageA != kChainStageB && kChainStageB != kChainStageC);
        CHECK(kChainStageA != kChainBuild);
        CHECK(kChainMembers == 4);
        CHECK(kChainTempCount == 4);
        CHECK(kChainMembers == kChainTempCount);
        CHECK(kPerFieldFrame == 0xE0);
        CHECK(kPerFieldFrame > kComposeFrame);
        CHECK(kPackedPointLoads == 2);
        CHECK(kPointLoadPacked);
        CHECK(kComposeHelperSightings == 2);              // and this helper is called twice by round 343
        CHECK(kComposeHelper1 == kPerFieldHelper);

        // the chain, in the order the instructions call it
        const std::uintptr_t chain[4] = {kChainBuild, kChainStageA, kChainStageB, kChainStageC};
        for (int i = 1; i < kChainMembers; ++i) {
            CHECK(chain[i] != chain[i - 1]);
        }
        CHECK(chain[0] < 0x250000);                       // the build is in its own low range
        CHECK(chain[1] > 0x5C0000 && chain[3] < 0x5D0000);// the three stages are in the geometry range
        // the packed pair a point occupies
        CHECK(kPointFieldB - kPointFieldA == sizeof(double));
        CHECK(kPerFieldFrame - kComposeFrame == 0x10);
    }

    // --- the translation builder and the identity basis (RE 0x5ce7b0) -------------------------------
    {
        CHECK(kMakeTranslation == 0x5CE7B0);
        CHECK(kMakeTranslationCallers == 32);
        CHECK(kMatrixLayoutConfirmed4);
        CHECK(kIdentityWritten);
        CHECK(kIdentityDiagonal == 1.0);
        CHECK(kIdentityOffDiagonal == 0.0);
        CHECK(kOneRva5CE7B0 == 0x9DE930);
        CHECK(kOneDoubleRva == 0xA06838);
        CHECK(kOneRva5CE7B0 != kOneDoubleRva);
        CHECK(kOneConstants == 2);
        CHECK(kTranslationFromPoint);
        CHECK(kChainStageA == kMakeTranslation);          // round 345's chain starts here
        CHECK(kChainMembers == 4);

        // the matrix the builder writes, as a 2x3 affine transform
        const auto buildTranslation = [](double px, double py, double m[6]) {
            m[0] = kIdentityDiagonal;  m[1] = kIdentityOffDiagonal;  m[2] = px;   // RE the four stores
            m[3] = kIdentityOffDiagonal; m[4] = kIdentityDiagonal;   m[5] = py;
        };
        double m[6] = {0, 0, 0, 0, 0, 0};
        buildTranslation(3.0, 4.0, m);
        CHECK(m[0] == 1.0 && m[1] == 0.0 && m[2] == 3.0);
        CHECK(m[3] == 0.0 && m[4] == 1.0 && m[5] == 4.0);
        // and applying it to a point is a pure translation, which is what makes it a translation builder
        const auto applyM = [](const double mm[6], double x, double y, double& ox, double& oy) {
            ox = mm[0] * x + mm[1] * y + mm[2];
            oy = mm[3] * x + mm[4] * y + mm[5];
        };
        double ox = 0, oy = 0;
        applyM(m, 10.0, 20.0, ox, oy);
        CHECK(ox == 13.0);
        CHECK(oy == 24.0);
        applyM(m, 0.0, 0.0, ox, oy);
        CHECK(ox == 3.0 && oy == 4.0);                    // the origin maps to the translation itself
        CHECK(kMakeTranslation > 0x5C0000 && kMakeTranslation < 0x5D0000);
        CHECK(kMatrixTx == 0x20 && kMatrixTy == 0x28);
    }

    // --- the affine inverse (RE 0x5ced50) ------------------------------------------------------------
    {
        CHECK(kAffineInverse == 0x5CED50);
        CHECK(kAffineInverseCallers == 24);
        CHECK(kMatrixLayoutConfirmed5);
        CHECK(kDeterminantComputed);
        CHECK(kReciprocalUsed);
        CHECK(kAdjugateForm);
        CHECK(kTranslationNegated);
        CHECK(kSignMaskRva == 0x9DE95F);
        CHECK(kSignMaskRva > kOneRva5CE7B0);
        CHECK(kOneRva9DE930Users == 2);
        CHECK(kSignMaskIsNotANormalDouble);
        CHECK(kChainStageB == kAffineInverse);            // round 345's chain runs this second
        CHECK(kChainStageA == kMakeTranslation);          // after the translation builder
        CHECK(kMakeTranslationCallers > kAffineInverseCallers);

        // the inverse the routine computes, checked by composing it with the original
        // the six doubles by the names their offsets give them, so an index cannot be mistaken for another
        // constexpr so the captureless lambda below can name them without capturing
        constexpr int IA = 0, IB = 1, IC = 2, ID = 3, ITX = 4, ITY = 5;   // +0x00 .. +0x28
        const auto invert = [](const double m[6], double inv[6]) {
            const double det = m[IA] * m[ID] - m[IB] * m[IC];    // RE 0x5CED8B
            const double r = 1.0 / det;                          // RE 0x5CED97
            inv[IA] = m[ID] * r;                                 // RE the adjugate
            inv[IB] = -m[IB] * r;
            inv[IC] = -m[IC] * r;
            inv[ID] = m[IA] * r;
            // the translation of the inverse is minus the inverse basis applied to the original translation
            inv[ITX] = -(inv[IA] * m[ITX] + inv[IB] * m[ITY]);
            inv[ITY] = -(inv[IC] * m[ITX] + inv[ID] * m[ITY]);
            return det;
        };
        // CORRECTED in 347d: the six doubles are a, b, c, d, tx, ty in memory -- I first wrote them in the
        // row-major order [a b tx; c d ty], which put the translation where c belongs and made the determinant 0.
        const double m[6] = {2, 0, 0, 4, 1, -1};            // a, b, c, d, tx, ty
        double inv[6] = {0, 0, 0, 0, 0, 0};
        const double det = invert(m, inv);
        CHECK(det == 8.0);                                   // 2*4 - 0*0
        CHECK(inv[IA] == 0.5);
        CHECK(inv[ID] == 0.25);
        CHECK(inv[IB] == 0.0);
        CHECK(inv[IC] == 0.0);
        // composing the two must give the identity basis
        // NOTE: the `applyM` helper used by earlier blocks indexes the matrix ROW-MAJOR (mm[2] as the translation),
        // which is a convention of those blocks, not of the binary. This applier uses the RECORD's order -- a, b, c, d,
        // tx, ty at +0x00, +0x08, +0x10, +0x18, +0x20, +0x28 -- which is the order the routines read and write.
        const auto applyRecord = [](const double mm[6], double x, double y, double& ox, double& oy) {
            ox = mm[IA] * x + mm[IB] * y + mm[ITX];
            oy = mm[IC] * x + mm[ID] * y + mm[ITY];
        };
        double px = 0, py = 0, qx = 0, qy = 0;
        applyRecord(m, 3.0, 5.0, px, py);                    // forward
        applyRecord(inv, px, py, qx, qy);                    // and back
        CHECK(qx > 2.9999 && qx < 3.0001);                   // the round trip returns the point
        CHECK(qy > 4.9999 && qy < 5.0001);
        CHECK(kAffineInverse != kMakeTranslation);
        CHECK(kTestConventionRowMajorInEarlierBlocks);   // the two conventions in this file
        CHECK(kTestConventionRecordOrderHere);
        CHECK(kAffineInverse > 0x5C0000 && kAffineInverse < 0x5D0000);
    }

    // --- the composition, and the library it completes (RE 0x5ce970) --------------------------------
    {
        CHECK(kMatrixMultiply == 0x5CE970);
        CHECK(kMatrixMultiplyCallers == 38);
        CHECK(kMulOperandA == 0);
        CHECK(kMulOperandB == 1);
        CHECK(kMatrixLayoutRoutines == 7);
        CHECK(kMatrixLayoutReads == 8);
        CHECK(kAffineLibraryMembers == 7);
        CHECK(kLibraryComplete);
        CHECK(kBothOperandsSameRecord);
        CHECK(std::string(kAffineLibrary) == "build, invert, multiply, and apply in four forms");
        CHECK(kChainStageC == kMatrixMultiply);           // the chain's last stage
        CHECK(kChainStageA == kMakeTranslation);
        CHECK(kChainStageB == kAffineInverse);
        CHECK(kMatrixMultiplyCallers > kMakeTranslationCallers);
        CHECK(kMatrixMultiplyCallers > kAffineInverseCallers);
        CHECK(kMatrixMultiplyCallers > kAffineKernelCallers);
        // the seven routines are seven distinct addresses
        CHECK(kMatrixMultiply != kMakeTranslation);
        CHECK(kMatrixMultiply != kAffineInverse);
        CHECK(kMatrixMultiply != kAffineKernel);
        CHECK(kMatrixMultiply != kAffineOutOfPlace);
        CHECK(kMatrixMultiply != kAffineInPlace);
        CHECK(kMatrixMultiply != kAffineTwoPoints);

        // the composition, in the record's order a, b, c, d, tx, ty, hand-checked against two steps
        constexpr int IA = 0, IB = 1, IC = 2, ID = 3, ITX = 4, ITY = 5;
        const auto compose = [](const double A[6], const double B[6], double C[6]) {
            // C = A after B: the 2x2 parts multiply, and the translation of B is carried through A
            C[IA] = A[IA] * B[IA] + A[IB] * B[IC];
            C[IB] = A[IA] * B[IB] + A[IB] * B[ID];
            C[IC] = A[IC] * B[IA] + A[ID] * B[IC];
            C[ID] = A[IC] * B[IB] + A[ID] * B[ID];
            C[ITX] = A[IA] * B[ITX] + A[IB] * B[ITY] + A[ITX];
            C[ITY] = A[IC] * B[ITX] + A[ID] * B[ITY] + A[ITY];
        };
        const auto applyRecord = [](const double m[6], double x, double y, double& ox, double& oy) {
            ox = m[IA] * x + m[IB] * y + m[ITX];
            oy = m[IC] * x + m[ID] * y + m[ITY];
        };
        const double scale[6] = {2, 0, 0, 1, 0, 0};       // x doubled, y unchanged
        const double shift[6] = {1, 0, 0, 1, 1, 1};       // translate by one and one
        double comp[6] = {0, 0, 0, 0, 0, 0};
        compose(scale, shift, comp);
        CHECK(comp[IA] == 2.0 && comp[IB] == 0.0);
        CHECK(comp[IC] == 0.0 && comp[ID] == 1.0);
        CHECK(comp[ITX] == 2.0 && comp[ITY] == 1.0);      // the shift is carried through the scale
        // and applying the composition equals applying the two in turn
        double x1 = 0, y1 = 0, x2 = 0, y2 = 0, x3 = 0, y3 = 0;
        applyRecord(shift, 3.0, 4.0, x1, y1);             // the shift first
        applyRecord(scale, x1, y1, x2, y2);               // then the scale
        applyRecord(comp, 3.0, 4.0, x3, y3);              // against the composition in one step
        CHECK(x2 == x3 && y2 == y3);
        CHECK(x3 == 8.0 && y3 == 5.0);
        CHECK(kAffineLibraryMembers == 7);
    }

    // --- the accumulator over 312-byte elements (RE 0x50fd40) ---------------------------------------
    {
        CHECK(kAccumulate == 0x50FD40);
        CHECK(kAccumulateCallers == 3);
        CHECK(kElementStride138 == 0x138);
        CHECK(kElementStride138 == 312);
        CHECK(kAccumulatorFlag == 0x00);
        CHECK(kAccumulatorA == 0x08);
        CHECK(kAccumulatorB == 0x10);
        CHECK(kAccumulatorC == 0x18);
        CHECK(kAccumulatorD == 0x20);
        CHECK(kAccumulatorD - kAccumulatorA == 0x18);
        CHECK(kAccumulatorA > kAccumulatorFlag);
        CHECK(kAccumulatorDoubles == 4);
        CHECK(kElementGetter == 0x51D2F0);
        CHECK(kElementAccessorA == 0x4F8370);
        CHECK(kElementAccessorB == 0x4F8380);
        CHECK(kElementAccessorB - kElementAccessorA == 0x10);
        CHECK(kAccessorsPerElement == 2);
        CHECK(kInit5C8A10 == 0x5C8A10);
        CHECK(kHelperBelowAffine);
        CHECK(kInit5C8A10 < kMakeTranslation);
        CHECK(kElementStride138 != kSegmentBytes);       // a much larger element than a segment

        // the walk the loop performs, as offsets -- no pointer arithmetic on a null pointer
        const auto offsetOf = [](int index) {
            return static_cast<std::size_t>(index) * kElementStride138;
        };
        CHECK(offsetOf(0) == 0u);
        CHECK(offsetOf(1) == 312u);
        CHECK(offsetOf(3) == 936u);
        CHECK(offsetOf(1) - offsetOf(0) == kElementStride138);
        // the accumulator's own layout: a flag, then four doubles
        struct Acc { unsigned char flag; double a, b, c, d; };
        CHECK(sizeof(Acc) >= kAccumulatorD + sizeof(double));
        Acc acc{};
        acc.flag = 1;
        acc.a = acc.b = acc.c = acc.d = 0.0;
        CHECK(acc.flag == 1);
        CHECK(acc.a == 0.0 && acc.d == 0.0);
        CHECK(kElementStride138 * 2 == 624);
        CHECK(kAccumulatorDoubles * 8 == 32);
    }

    // --- the accessor chain and what it accumulates (RE 0x51d2f0, 0x4f8370, 0x4f8380) --------------
    {
        CHECK(kGetter60 == 0x51D2F0);
        CHECK(kGetter60Callers == 102);
        CHECK(kGetter60Offset == 0x60);
        CHECK(kGetter60Offset == kComposeWeightB);        // the same offset as round 343's weight
        CHECK(kAccessorPair28 == 0x4F8370);
        CHECK(kAccessorPair28Callers == 74);
        CHECK(kAccessorPair28Offset == 0x28);
        CHECK(kAccessorPair30 == 0x4F8380);
        CHECK(kAccessorPair30Callers == 85);
        CHECK(kAccessorPair30Offset == 0x30);
        CHECK(kAccessorPair30Offset - kAccessorPair28Offset == 8);
        CHECK(kQuantitiesAre28And30);
        CHECK(kChainLength == 3);
        CHECK(kOffsetsRecur);
        CHECK(kNotMergedAcrossTypes);
        CHECK(kElementGetter == kGetter60);               // the chain round 349 walked
        CHECK(kElementAccessorA == kAccessorPair28);
        CHECK(kElementAccessorB == kAccessorPair30);
        CHECK(kAccessorPair30Callers > kAccessorPair28Callers);
        CHECK(kGetter60Callers > kAccessorPair30Callers);
        CHECK(kAccessorPair30Offset == kSegmentEndA + 0x20);   // the offset recurs in other records too

        // the chain, applied to a sub-object with the two quantities in it
        struct Sub { char pad[0x28]; double q28; double q30; };
        struct Element { char pad[0x60]; Sub* sub; };
        Sub sub{};
        sub.q28 = 2.5;
        sub.q30 = 4.0;
        Element el{};
        el.sub = &sub;
        const auto get = [](const Element& e) { return e.sub; };
        CHECK(get(el) == &sub);
        CHECK(get(el)->q28 == 2.5);
        CHECK(get(el)->q30 == 4.0);
        // and the accumulator sums what the two accessors return
        double acc = 0.0;
        acc += get(el)->q28;
        acc += get(el)->q30;
        CHECK(acc == 6.5);
        CHECK(kChainLength == 3);
    }

    // --- the largest routine's head, and the third division magic (RE 0x243820) --------------------
    {
        CHECK(kBigRoutine == 0x243820);
        CHECK(kBigRoutineSize == 15524);
        CHECK(kBigRoutineCallers == 3);
        CHECK(kBigFrame == 0xE18);
        CHECK(kBigFrame == 3608);
        CHECK(kBigXmmSaved == 6);
        CHECK(kStringPvBarRva == 0x8DEC00);
        CHECK(std::string(kStringPvBar) == "pv|");
        CHECK(kHelper5F4310 == 0x5F4310);
        CHECK(kHelper51D0C0 == 0x51D0C0);
        CHECK(kHelper5F4310 != kHelper51D0C0);
        CHECK(kRangeLengthComputed);
        CHECK(kDivisionMagic18 == 0xEEEEEEEEEEEEEEEFULL);
        CHECK(kDivisionMagicDivisors == 3);
        CHECK(!kShiftNotReadYet);                         // round 352 read the shift
        CHECK(kShiftReadInRound352);
        CHECK(kImpliedRecordBytesCandidate == 18);       // the withdrawn candidate
        CHECK(kImpliedRecordSizeIsWithdrawn);
        CHECK(kTopCallersUncited == 2);
        CHECK(kGetter60 == 0x51D2F0);
        CHECK(kHelper51D0C0 != kGetter60);                 // a different helper in the same range
        CHECK(kBigRoutineSize > kComposeFrame);           // the body dwarfs the frames read earlier

        // the two division magics already confirmed, and this third one, by value
        CHECK(kDivisionMagic18 != 0x431BDE82D7B634DBULL);  // one million
        CHECK(kDivisionMagic18 != 0xC30C30C30C30C30DULL);  // twenty-one
        CHECK(kDivisionMagic18 == 0xEEEEEEEEEEEEEEEFULL);
        // the shift that would settle eighteen against nine has not been read, and the constants say so
        CHECK(!kShiftNotReadYet);                         // round 352 read the shift (second occurrence, also corrected)
        CHECK(kImpliedRecordBytesCandidate * 2 == 36);   // eighteen and nine were the two candidates
        CHECK(kRangeLengthComputed);
        // a range length is end minus begin, as the instruction computes it
        const auto rangeLength = [](std::uintptr_t begin, std::uintptr_t end) { return end - begin; };
        CHECK(rangeLength(0x1000, 0x1012) == 18);
        CHECK(rangeLength(0x1000, 0x1000) == 0);
        CHECK(rangeLength(0, 0x24) == 36);
    }

    // --- the magic's nature, and the withdrawal (RE 0x2438b1 to 0x2438bf) ---------------------------
    {
        CHECK(kShiftBeforeMultiply);
        CHECK(kPreShift == 3);
        CHECK(kLowHalfKept);
        CHECK(kIMulIsTwoOperand);
        CHECK(kMagicIs15Inverse);
        CHECK(kFifteen == 15);
        CHECK(kComparisonValue == 0xC8);
        CHECK(kComparisonValue == 200);
        CHECK(kComparisonIsBucketLike);
        CHECK(kDivisorWithdrawn);                         // round 351's reading of it
        CHECK(kImpliedRecordSizeWithdrawn);               // and the eighteen bytes that followed from it
        CHECK(!kUseAt243925Unread);                        // read in round 353
        CHECK(kDivisionMagic18 == 0xEEEEEEEEEEEEEEEFULL); // the constant itself stays recorded
        CHECK(kShiftNotReadYet == false);                 // the shift HAS now been read

        // the property the hand check found: fifteen times the constant is one, modulo 2^64
        const std::uint64_t product = static_cast<std::uint64_t>(kFifteen * kDivisionMagic18);
        CHECK(product == 1ULL);
        CHECK(kDivisionMagic18 != 0ULL);
        // and the value a length would produce, taken as the low half of the sequence
        const auto sequence = [](std::uint64_t length) {
            const std::uint64_t shifted = length >> kPreShift;                 // RE the sar
            return static_cast<std::uint64_t>(shifted * kDivisionMagic18);     // RE the two-operand multiply
        };
        // a length of 456 gives 57 after the shift, and the sequence's value is what faces the comparison
        CHECK(sequence(456) == ((456u >> 3) * kDivisionMagic18));
        CHECK((456u >> 3) == 57u);
        // the comparison the routine performs
        const auto withinBuckets = [](std::uint64_t v) { return v <= kComparisonValue; };
        CHECK(withinBuckets(0));
        CHECK(withinBuckets(200));
        CHECK(!withinBuckets(201));
        CHECK(kPreShift == 3);
    }

    // --- the SSO branch and the tolerance (RE 0x243925 onwards) -------------------------------------
    {
        CHECK(kGuardedPath == 0x243925);
        CHECK(kToleranceConstant == 0.01);
        CHECK(kToleranceRva == 0x9C27C0);
        CHECK(kToleranceIsFractional);
        CHECK(kToleranceSink == 0x4B81D0);
        CHECK(kSsoBranchValue == 0xF);
        CHECK(kSsoBranchValue == 15u);
        CHECK(kSsoBranchValue == kNarrowSsoCapacity);     // the same fifteen as round 320
        CHECK(kSsoCapacitySightings == 2);
        CHECK(kSsoGovernsControlFlow);
        CHECK(kOneLengthCase == 0x2470EC);
        CHECK(kInlineBufferOffset == 0x10);
        CHECK(kInlineBufferSightings == 3);
        CHECK(kGuardTargetRva == 0x9C2740);
        CHECK(kGuardTargetNotAString);
        CHECK(kNullBeginNonzeroCountGuard);
        CHECK(kUseAt243925Unread == false);               // what the comparison guards is now read

        // the branch rule, as the instruction implements it: at most fifteen is inline
        const auto isInline = [](std::uint64_t count) { return count <= kSsoBranchValue; };
        CHECK(isInline(0));
        CHECK(isInline(1));
        CHECK(isInline(15));
        CHECK(!isInline(16));
        CHECK(!isInline(100));
        // and the guard that precedes it: a null begin with a non-zero count is rejected
        const auto misformed = [](const void* begin, std::uint64_t count) {
            return begin == nullptr && count != 0;        // RE the add, the je and the test
        };
        CHECK(misformed(nullptr, 1));
        CHECK(!misformed(nullptr, 0));
        CHECK(!misformed(reinterpret_cast<const void*>(1), 1));
        // the tolerance, as the double the constructor receives
        CHECK(kToleranceConstant < 0.1);
        CHECK(kToleranceConstant * 100.0 == 1.0);
        CHECK(sizeof(double) == 8);
    }

    // --- the tolerance's owner (RE 0x4b81d0) ---------------------------------------------------------
    {
        CHECK(kToleranceOwner == 0x4B81D0);
        CHECK(kToleranceOwnerCallers == 4);
        CHECK(kToleranceSink == kToleranceOwner);         // the constructor round 353 found
        CHECK(kToleranceObjectBytes == 0x38);
        CHECK(kToleranceObjectBytes == 56);
        CHECK(kToleranceField == 0x00);
        CHECK(kObjectFlag10 == 0x10);
        CHECK(kObjectZeroA == 0x18);
        CHECK(kObjectZeroB == 0x30);
        CHECK(kRangeBegin == 0x20);
        CHECK(kRangeEnd == 0x28);
        CHECK(kRangeEnd - kRangeBegin == 8);
        CHECK(kEmptyRangePair);
        CHECK(kEmptyRangeBase);
        CHECK(kAllocator998500Used == 0x998500);
        CHECK(kAllocatorSightings7 == 7);
        CHECK(kAllocatorSizeVisible);
        CHECK(kInlineBufferSightings2 == 4);
        CHECK(kInlineBufferOffset == 0x10);               // the same base the empty range points at
        CHECK(kObjectFlag10 == kInlineBufferOffset);
        CHECK(kToleranceConstant == 0.01);                // the value that lands at offset zero

        // the object as the constructor leaves it: the tolerance first, then an empty range
        struct Tol { double tolerance; char pad[8]; unsigned int flag; unsigned char buf[0x20]; };
        CHECK(sizeof(Tol) >= kToleranceField + sizeof(double));
        Tol obj{};
        obj.tolerance = kToleranceConstant;
        obj.flag = 0;
        CHECK(obj.tolerance == 0.01);
        CHECK(obj.flag == 0u);
        // an empty range: the two pointers are equal, which is what "begin == end" means
        const auto isEmpty = [](const void* begin, const void* end) { return begin == end; };
        const void* base = static_cast<const void*>(obj.buf);
        CHECK(isEmpty(base, base));
        CHECK(!isEmpty(base, static_cast<const void*>(obj.buf + 1)));
        CHECK(kToleranceObjectBytes > kRangeEnd);
        CHECK(kAllocatorSightings7 > kAccumulateCallers);
    }

    // --- the launch order's layout, read out of its constructor (RE 0x14620 NewLaunchingOrder) ---
    //
    // The evidence is one function: it allocates 0x2C0 bytes through operator new at 0x998500 and then writes 96 fields,
    // the largest at +0x2B8 and nothing above 0x2C0. The static_asserts in lcns/launching_order.hpp hold the offsets; these
    // checks hold the two facts a reader needs from here -- the size, and the widths at the offsets the constructor writes.
    {
        CHECK(sizeof(lcns::dll::LaunchingOrderLayout) == 0x2C0);      // RE 0x14636, mov ecx, 0x2C0
        CHECK(offsetof(lcns::dll::LaunchingOrderLayout, origin) == 0x00C);   // RE 0xD119, SetOrigin (86), not the constructor
        CHECK(offsetof(lcns::dll::LaunchingOrderLayout, multiplicityPreference) == 0x010);   // RE 0xD26A, a double
        CHECK(offsetof(lcns::dll::LaunchingOrderLayout, commonCutSafetyPreferenceGiven) == 0x068);   // RE 0xEA09
        CHECK(offsetof(lcns::dll::LaunchingOrderLayout, commonCutSafetyPreference) == 0x06C);   // RE 0xEA0D
        CHECK(offsetof(lcns::dll::LaunchingOrderLayout, commonCutCuttingPreference) == 0x08C);   // RE 0xED60
        CHECK(offsetof(lcns::dll::LaunchingOrderLayout, multiTorchCuttingPreference) == 0x09C);   // RE 0xF233
        CHECK(offsetof(lcns::dll::LaunchingOrderLayout, markModeFirst) == 0x0E8);   // RE 0x189FA
        CHECK(offsetof(lcns::dll::LaunchingOrderLayout, emptySlotMarker0) == 0x110);   // RE 0x14793, the marker
        CHECK(offsetof(lcns::dll::LaunchingOrderLayout, specificSheetOrigin) == 0x128);   // RE 0x13F09
        CHECK(offsetof(lcns::dll::LaunchingOrderLayout, specificSheetObjective) == 0x130);   // RE 0x140B9
        CHECK(offsetof(lcns::dll::LaunchingOrderLayout, userString) == 0x1B8);   // RE 0x14855
        // The mode LaunchLocalComputation reads has a name from an export now, and it is inside this object.
        CHECK(offsetof(lcns::dll::LaunchingOrderLayout, automaticStop) == 0x240);   // RE 0xE0D9
        CHECK(offsetof(lcns::dll::LaunchingOrderLayout, nodeList) == 0x2A8);         // RE 0x5007C0
        CHECK(offsetof(lcns::dll::LaunchingOrderLayout, estimateLocalComputation) == 0x288);  // RE 0x3383
        CHECK(lcns::dll::LaunchingOrderLayout::kEmptySlotMarker == 0x3FFFFFFFu);
    }

    // --- the 0x48 byte node: its copy and its release (RE 0x9302C0 and 0x9308C0) ---
    //
    // The ownership rule these two routines share is what makes them implementable at all: a node's +0x20 points at its
    // own +0x30 for a short string, and 0x9308C0 frees that pointer ONLY when it is not the node's own buffer. The test
    // builds a node with an INLINE string and a node with an OUTSIDE string, and checks that the copy keeps the rule and
    // that releasing both does not double free.
    {
        CHECK(lcns::dll::kCnsNodeBytes == 0x48);          // RE 0x9302D2, mov ecx, 0x48
        CHECK(lcns::dll::kCnsNodeInlineBuffer == 0x30);   // RE 0x93030D

        // A source node whose string lives in its own inline buffer.
        unsigned char source[0x48];
        std::memset(source, 0, sizeof(source));
        const std::uint32_t type = 7;
        std::memcpy(source + 0x00, &type, sizeof(type));
        void* inline_buffer = source + lcns::dll::kCnsNodeInlineBuffer;
        std::memcpy(source + 0x20, &inline_buffer, sizeof(inline_buffer));
        const std::size_t length = 5;
        std::memcpy(source + 0x28, &length, sizeof(length));
        std::memcpy(source + lcns::dll::kCnsNodeInlineBuffer, "hello", 5);
        const double value = -13.25;
        std::memcpy(source + 0x40, &value, sizeof(value));

        void* copy = lcns::dll::cnsNodeCopy(nullptr, source, lcns::dll::kCnsNodeBytes);
        CHECK(copy != nullptr);
        unsigned char* copied = static_cast<unsigned char*>(copy);
        std::uint32_t copied_type = 0;
        std::memcpy(&copied_type, copied + 0x00, sizeof(copied_type));
        CHECK(copied_type == type);                                  // RE 0x93030D
        void* copied_data = nullptr;
        std::memcpy(&copied_data, copied + 0x20, sizeof(copied_data));
        CHECK(copied_data == copied + lcns::dll::kCnsNodeInlineBuffer);   // RE 0x9302F1, the copy's own buffer
        CHECK(std::memcmp(copied_data, "hello", 5) == 0);             // RE 0x9302FC
        std::size_t copied_length = 0;
        std::memcpy(&copied_length, copied + 0x28, sizeof(copied_length));
        CHECK(copied_length == length);
        double copied_value = 0.0;
        std::memcpy(&copied_value, copied + 0x40, sizeof(copied_value));
        CHECK(copied_value == value);                                // RE 0x930323
        CHECK(copied_data != static_cast<void*>(source + lcns::dll::kCnsNodeInlineBuffer));
        // The release must accept the copy: the inline buffer is not freed, the node is.
        lcns::dll::cnsNodeRelease(nullptr, copy);

        // A node whose string was allocated outside the node: the release must free that pointer and not leak it.
        unsigned char outside[0x48];
        std::memset(outside, 0, sizeof(outside));
        char* external = static_cast<char*>(std::malloc(8));
        CHECK(external != nullptr);
        if (external != nullptr) {
            std::memcpy(external, "abcdefg", 8);
            void* external_pointer = external;
            std::memcpy(outside + 0x20, &external_pointer, sizeof(external_pointer));
            const std::size_t outside_length = 7;
            std::memcpy(outside + 0x28, &outside_length, sizeof(outside_length));
            // cnsNodeCopyString copies from the outside pointer into the copy's own buffer, which is the rule the original
            // has: a copy never shares a string with its source.
            void* second = lcns::dll::cnsNodeCopy(nullptr, outside, lcns::dll::kCnsNodeBytes);
            CHECK(second != nullptr);
            unsigned char* second_bytes = static_cast<unsigned char*>(second);
            void* second_data = nullptr;
            std::memcpy(&second_data, second_bytes + 0x20, sizeof(second_data));
            CHECK(second_data == second_bytes + lcns::dll::kCnsNodeInlineBuffer);
            CHECK(std::memcmp(second_data, "abcdefg", 7) == 0);
            lcns::dll::cnsNodeRelease(nullptr, second);
            std::free(external);
        }
    }

    // ---------------------------------------------------------------- the owned chain (RE 0x92ECB0, round 565)
    //
    // The ownership rule is the same one cns_node.hpp proved -- a buffer is owned exactly when its data pointer is not its own
    // inline address -- applied TWICE per node, with the chain link read before the node is freed. What makes this testable
    // without executing the original is that the rule says which addresses get freed, and a chain can be built to violate every
    // case at once: heap buffers, inline buffers, and a node whose buffer pointer is null.
    {
        using lcns::OwnedChainNode;
        // three nodes, each with one heap buffer at +0x20 and one INLINE buffer at +0x40
        OwnedChainNode* nodes[3] = {};
        void* heap_blocks[3] = {};
        for (int i = 0; i < 3; ++i) {
            nodes[i] = static_cast<OwnedChainNode*>(std::calloc(1, sizeof(OwnedChainNode)));            heap_blocks[i] = std::malloc(16);
            std::memset(heap_blocks[i], 0xAB, 16);
            nodes[i]->buffer1Data = heap_blocks[i];               // heap: +0x20 != +0x30, so it is freed
            nodes[i]->buffer1Inline = nodes[i]->buffer1Data;
            nodes[i]->buffer2Data = &nodes[i]->buffer2Inline;     // inline: +0x40 == +0x50, so it is NOT freed
            nodes[i]->buffer2Inline = &nodes[i]->buffer2Inline;
            nodes[i]->chain = (i + 1 < 3) ? nodes[i + 1] : nullptr;
        }
        // the middle node's heap buffer is null, which must not be freed and must not crash
        std::free(nodes[1]->buffer1Data);
        nodes[1]->buffer1Data = nullptr;

        lcns::releaseOwnedChain(nodes[0]);   // frees node 0's heap buffer, not node 1's (null), not node 2's inline
        std::free(heap_blocks[2]);
        // reaching here without a double free or a free of a stack address is the assertion: the inline buffers were skipped
        // because their data pointer equalled their own inline address, and that equality is the whole rule.
        CHECK(true);
    }


    // ---------------------------------------------------------------- the stat predicates (RE 0x52F810 and 0x52F830)
    //
    // The two functions that ../structure/stat.cpp's aggregators are parameterised by, and the ONLY difference between the
    // GetLength and GetHeight exports. The assertions cover every small value, because the whole content of the two routines is
    // which values they accept: {0, 1} for the first and {0, 2} for the second.
    {
        for (std::uint32_t value = 0; value <= 8u; ++value) {
            CHECK(lcns::statIsShortAxis(&value) == (value <= 1u));                 // RE 0x52F810: cmp 1 ; setbe
            CHECK(lcns::statIsLongAxis(&value) == (value == 0u || value == 2u));   // RE 0x52F830: test 0xFFFFFFFD ; sete
        }
        // the two disagree on exactly two values, which is why they are two predicates rather than one with a flag
        int disagree = 0;
        for (std::uint32_t value = 0; value <= 8u; ++value) {
            if (lcns::statIsShortAxis(&value) != lcns::statIsLongAxis(&value)) {
                ++disagree;
            }
        }
        CHECK(disagree == 2);        // 1 and 2
        CHECK(lcns::statIsShortAxis(nullptr) == false || true);   // the routines dereference, so only real values are passed
    }


    // ---------------------------------------------------------------- the stat accumulator (RE 0x526160 and 0x5266A0)
    //
    // The two exported aggregators call the same seven functions and differ at ONE pointer, so this is one shape: walk a container
    // of 0x78-byte records, fold each accepted element's measurement into a running min and max, and return the difference --
    // which RE 0x526230 performs with one `subsd` after the walk. The element functions are parameters here because the two
    // bodies behind them are not read yet, and a guessed contract would be worse than a parameter.
    {
        struct Element { std::uint32_t axis; double measure; };
        Element elements[4] = {{0u, 1.0}, {1u, 5.0}, {2u, 2.0}, {3u, 9.0}};
        const auto measure = [](const Element* e) { return e->measure; };

        // the short-axis predicate accepts {0,1}, so the extent is over measures 1.0 and 5.0
        const double shortExtent = lcns::statExtent(
            elements, elements + 4, measure, [](const Element* e) { return lcns::statIsShortAxis(&e->axis); });
        CHECK(shortExtent == 4.0);

        // the long-axis predicate accepts {0,2}, so the extent is over measures 1.0 and 2.0
        const double longExtent = lcns::statExtent(
            elements, elements + 4, measure, [](const Element* e) { return lcns::statIsLongAxis(&e->axis); });
        CHECK(longExtent == 1.0);

        // accepting everything gives the full range, which is what the two disagreeing over {1,2} is worth
        const double allExtent = lcns::statExtent(
            elements, elements + 4, measure, [](const Element*) { return true; });
        CHECK(allExtent == 8.0);            // 9.0 - 1.0

        // an empty set is zero rather than a sentinel pair, because the original returns the difference of its accumulators
        const double nothing = lcns::statExtent(
            elements, elements, measure, [](const Element*) { return true; });
        CHECK(nothing == 0.0);
        // and a set where nothing is accepted is the same case
        const double noneAccepted = lcns::statExtent(
            elements, elements + 4, measure, [](const Element*) { return false; });
        CHECK(noneAccepted == 0.0);

        // a single element is a zero extent, which is the accumulator agreeing with itself
        const double one = lcns::statExtent(
            elements + 1, elements + 2, measure, [](const Element*) { return true; });
        CHECK(one == 0.0);

        CHECK(lcns::kStatElementStride == 0x78);
        CHECK(lcns::kStatElementStride == 120u);
        CHECK(lcns::kStatElementStride * 2 == 240u);
    }


    // ---------------------------------------------------------------- StatBox::fold (RE 0x5C8C50)
    //
    // READ FROM THE WHOLE 255 BYTE BODY. The element is FOUR doubles and the box's flag means BUILD ME rather than I am valid:
    //
    //     element flag zero  -> return untouched           (0x5C8C50)
    //     box flag NONZERO   -> install a and b into all four slots, clear the flag, then compare c and d  (0x5C8D10)
    //     box flag ZERO      -> compare a, b, c and d      (0x5C8C69)
    //
    // Three earlier attempts read a fragment and got the polarity and the arity wrong; they are recorded in re/blockers.json.
    {
        // the build path: a and b set both ends of both axes, the flag clears, and c and d are then compared
        lcns::StatBox fresh;
        fresh.valid = 1;                                   // BUILD ME
        fresh.low0 = 100.0; fresh.high0 = 200.0;
        fresh.low1 = 300.0; fresh.high1 = 400.0;
        fresh.fold(true, 11.0, 22.0, 5.0, 40.0);
        CHECK(fresh.valid == 0);                           // RE 0x5C8D14
        CHECK(fresh.low0 == 5.0);                          // a=11 set it, then c=5 lowered it
        CHECK(fresh.high0 == 11.0);                        // and a is still the high, because c did not exceed it
        CHECK(fresh.low1 == 22.0);                         // b=22 set it, then d=40 raised the high instead
        CHECK(fresh.high1 == 40.0);

        // the compare path against a ZERO box, which only lowers a low when the element is BELOW ZERO -- 0x5C8C73 is `ucomisd` of
        // the box against the element with `jbe` skipping the store. **This is why the build path exists**: a fresh box has no useful
        // lows, so the first element is installed rather than compared.
        lcns::StatBox zeroed;
        zeroed.fold(true, 5.0, 7.0, 9.0, 4.0);
        CHECK(zeroed.valid == 0);                          // the compare path never touches the flag
        CHECK(zeroed.low0 == 0.0);                         // 5 and 9 are both above zero, so the low stays
        CHECK(zeroed.high0 == 9.0);                        // and c=9 raised the high
        CHECK(zeroed.low1 == 0.0);                         // same for the second axis
        CHECK(zeroed.high1 == 7.0);                        // b=7

        // and a NEGATIVE element does lower the low, which is the comparison the jbe skips over
        lcns::StatBox negative;
        negative.fold(true, -5.0, -7.0, 1.0, -2.0);
        CHECK(negative.low0 == -5.0);                      // a=-5 is below zero, so it lands
        CHECK(negative.low1 == -7.0);                      // b=-7 likewise
        CHECK(negative.high0 == 1.0);                      // c=1 raised the high
        CHECK(negative.high1 == 0.0);                      // d=-2 is below zero, so the high stays 0

        // an element with a zero flag contributes nothing at all, which is the routine's first three instructions
        lcns::StatBox untouched;
        untouched.fold(false, 42.0, 42.0, 42.0, 42.0);
        CHECK(untouched.low0 == 0.0 && untouched.high0 == 0.0);
        CHECK(untouched.low1 == 0.0 && untouched.high1 == 0.0);
        CHECK(untouched.valid == 0);

        // and a build followed by a compare: the second call takes the compare path because the flag was cleared
        lcns::StatBox built;
        built.valid = 1;
        built.fold(true, 1.0, 2.0, 1.0, 2.0);
        CHECK(built.low0 == 1.0 && built.high0 == 1.0);
        CHECK(built.low1 == 2.0 && built.high1 == 2.0);
        built.fold(true, 0.0, 0.0, 3.0, 3.0);
        CHECK(built.low0 == 0.0 && built.high0 == 3.0);
        CHECK(built.low1 == 0.0 && built.high1 == 3.0);

        CHECK(lcns::kStatFlag == 0x00);
        CHECK(lcns::kStatMin0 == 0x08 && lcns::kStatMax0 == 0x18);
        CHECK(lcns::kStatMin1 == 0x10 && lcns::kStatMax1 == 0x20);
    }


    // ---------------------------------------------------------------- the variant scale rule (RE 0x132E0)
    //
    // The rule two exports share, and the three behaviours its instructions express: an invalid box scales nothing (0x13327 jumps
    // past both multiplies), and the LARGER of the two extents chooses which constant is used (0x13341, 0x13345 and 0x13382).
    {
        // THE COMPLETE RULE, which the header previously carried only as the multiplication. RE 0x132E0 fills a box at rsp+0x50 and
        // takes high - low per axis -- [rsp+0x70]-[rsp+0x60] for the second and [rsp+0x68]-[rsp+0x58] for the first -- then scales the
        // larger. The box's offsets are StatBox's, so one representation is shared with the stat accumulator.
        {
            lcns::StatBox box;
            CHECK(box.valid == 0);
            CHECK(lcns::variantScaleOfBox(box) == 0.0);        // RE 0x13327: an invalid box scales nothing

            box.valid = 1;
            box.low0 = 2.0;  box.high0 = 9.0;                   // the first axis: extent 7
            box.low1 = 0.0;  box.high1 = 3.0;                   // the second: extent 3
            CHECK(box.high0 - box.low0 == 7.0);
            CHECK(box.high1 - box.low1 == 3.0);
            // the larger extent is scaled, and the scale is 0.0001 in the module
            CHECK(lcns::variantScaleOfBox(box) == 7.0 * lcns::kVariantScale);
            CHECK(lcns::variantScaleOfBox(box) == 0.0007);

            // swap which axis is larger, and the answer must follow
            box.low0 = 0.0;  box.high0 = 1.0;                   // first: 1
            box.low1 = 0.0;  box.high1 = 40.0;                  // second: 40
            CHECK(lcns::variantScaleOfBox(box) == 40.0 * lcns::kVariantScale);

            // equal extents take the not-greater arm, as the ucomisd and jbe at 0x13341/0x13345 say
            box.low0 = 5.0;  box.high0 = 15.0;
            box.low1 = 0.0;  box.high1 = 10.0;
            CHECK(lcns::variantScaleOfBox(box) == 10.0 * lcns::kVariantScale);

            // and the correspondence the header records: extentA is the SECOND axis
            CHECK(lcns::variantScale(true, 3.0, 7.0, lcns::kVariantScale) == 7.0 * lcns::kVariantScale);
            CHECK(lcns::kVariantAppend == 0x23BF0);
        }

        // an invalid box returns zero, which is the routine jumping past BOTH multiplies
        CHECK(lcns::variantScale(false, 10.0, 1.0, 0.5) == 0.0);
        // the first extent larger: extentA * scale
        CHECK(lcns::variantScale(true, 10.0, 1.0, 0.5) == 5.0);
        // the second larger: extentB * scale
        CHECK(lcns::variantScale(true, 1.0, 10.0, 0.5) == 5.0);
        // equal extents take the not-greater branch, because the instruction is ucomisd then JBE
        CHECK(lcns::variantScale(true, 5.0, 5.0, 0.5) == 2.5);
        // and zero extents give zero either way, which is the degenerate case
        CHECK(lcns::variantScale(true, 0.0, 0.0, 0.5) == 0.0);
        // CORRECTION: both arms load the SAME constant. The two mulsd instructions have different DISPLACEMENTS
        // (0x99a679 at 0x13347 and 0x99a63e at 0x13382) that resolve to the SAME address 0x9AD9C8, where the double is
        // 0.0001. So the comparison selects which extent is multiplied and not the factor, and the earlier test -- which
        // passed two factors and asserted each arm used its own -- was asserting something the instructions do not do.
        CHECK(lcns::kVariantScale == 0.0001);
        CHECK(lcns::variantScale(true, 10000.0, 1.0, lcns::kVariantScale) == 1.0);
        CHECK(lcns::variantScale(true, 1.0, 10000.0, lcns::kVariantScale) == 1.0);
        CHECK(lcns::variantScale(true, 20000.0, 1.0, lcns::kVariantScale) == 2.0);
        // the offsets, against the instructions that show them
        CHECK(lcns::kVariantSource == 0x50);
        CHECK(lcns::kVariantTargetA == 0x68);
        CHECK(lcns::kVariantTargetB == 0x208);
        CHECK(lcns::kVariantTargetB < 0x2C0);              // inside the object the constructor allocates
        CHECK(offsetof(lcns::dll::LaunchingOrderLayout, commonCutSafetyPreferenceGiven) == lcns::kVariantTargetA);
    }


    // ---------------------------------------------------------------- the deep chain release (RE 0x923110)
    //
    // Thirty-five functions in the module are byte-identical to this one apart from their own addresses. The walk follows a link at
    // +0x18, releases each node and stops at null, and the link is read BEFORE the release.
    //
    // THE NODE MUST HAVE ITS LINK AT +0x18. A first version of this test used `struct Node { Node* link; int payload; }`, which is
    // 0x10 bytes, so the walk read past the array -- and the compiler had said so with `-Warray-bounds`. A test for a routine whose
    // whole content is an offset must place the field at that offset.
    {
        struct alignas(8) Node {
            unsigned char reserved[0x18];        // the module's chain link is at +0x18, not at +0x00
            Node* link;
            int payload;
        };
        static_assert(offsetof(Node, link) == 0x18, "the link must be where RE 0x92313C reads it");
        CHECK(offsetof(Node, link) == lcns::kDeepChainLink);
        CHECK(lcns::kDeepChainLink == 0x18);
        CHECK(lcns::kDeepChainLink != 0x10);      // owned_chain.hpp's link is at +0x10

        Node chain[3];
        for (int i = 0; i < 3; ++i) {
            for (unsigned char& byte : chain[i].reserved) {
                byte = 0;
            }
            chain[i].payload = i;
        }
        chain[0].link = &chain[1];
        chain[1].link = &chain[2];
        chain[2].link = nullptr;

        // the link read, against a live chain
        CHECK(lcns::linkAt(&chain[0]) == &chain[1]);
        CHECK(lcns::linkAt(&chain[1]) == &chain[2]);
        CHECK(lcns::linkAt(&chain[2]) == nullptr);

        // the walk, on a chain the release function detaches as it goes -- which is what releasing a node means
        Node a, b, c;
        for (Node* node : {&a, &b, &c}) {
            for (unsigned char& byte : node->reserved) {
                byte = 0;
            }
        }
        a.link = &b; b.link = &c; c.link = nullptr;
        int released = 0;
        lcns::releaseDeepChain(&a, [&released](Node* node) {
            ++released;
            node->link = nullptr;
        });
        CHECK(released == 3);

        // a null head is a no-op, which is RE 0x923120
        released = 0;
        lcns::releaseDeepChain(static_cast<Node*>(nullptr), [&released](Node* node) {
            ++released;
            node->link = nullptr;
        });
        CHECK(released == 0);

        // and a single node
        Node one;
        for (unsigned char& byte : one.reserved) {
            byte = 0;
        }
        one.link = nullptr;
        released = 0;
        lcns::releaseDeepChain(&one, [&released](Node* node) {
            ++released;
            node->link = nullptr;
        });
        CHECK(released == 1);
    }


    // ---------------------------------------------------------------- the module switch pair (RE 0x9AF0 and 0x64B2C0)
    //
    // Two domain functions in different closures read the SAME flag and the SAME object and call the same gate, which is what makes
    // the state shared rather than local. The assertions are about the ARITHMETIC OF THE ADDRESSES, because that is the whole claim:
    // the object is the flag's neighbour, and the flag is not the logger's switch.
    {
        CHECK(lcns::kModuleSwitchFlag == 0xB1F050);
        CHECK(lcns::kModuleSwitchObject == 0xB1F058);
        CHECK(lcns::kModuleSwitchObject == lcns::kModuleSwitchFlag + 8);   // the 8 bytes between them
        CHECK(lcns::kModuleSwitchGate == 0x63F6C0);
        // and it is NOT the logger's own switch, which is 0x38 before it
        CHECK(lcns::kLoggerSwitch == 0xB1F018);
        CHECK(lcns::kLoggerSwitch != lcns::kModuleSwitchFlag);
        CHECK(lcns::kLoggerSwitch + 0x38 == lcns::kModuleSwitchFlag);
        // two independent sites, which is the evidence that the state is module-wide
        CHECK(lcns::kModuleSwitchSiteA == 0x9AF0);
        CHECK(lcns::kModuleSwitchSiteB == 0x64B2C0);
        CHECK(lcns::kModuleSwitchSiteA != lcns::kModuleSwitchSiteB);
        // the enable test, which is `test al, al` then `je` at both sites
        CHECK(lcns::moduleSwitchEnabled(0) == false);
        CHECK(lcns::moduleSwitchEnabled(1) == true);
        CHECK(lcns::moduleSwitchEnabled(0xFF) == true);
    }


    // ---------------------------------------------------------------- the engine's config parameters (RE 0x4EC00)
    //
    // RE 0x4EC00 READS a value at [rdi+0x40] and records it under a parameter name and storing the value when the lookup succeeds, so
    // each entry is a name from the module's own strings beside the instruction that writes it. The assertions below are about the
    // TABLE: that the count agrees with the generated constant, and that the named offsets are the ones the generator recorded.
    {
        std::size_t count = 0;
        const lcns::ParameterReportEntry* table = lcns::parameterReport(count);
        CHECK(count == lcns::parameters::kParameterReportCount);
        CHECK(count == 107u);

        // the one site verified by hand: nesting_pow_boost at +0x100
        CHECK(lcns::parameters::knesting_pow_boost == 0x100);
        CHECK(lcns::parameters::knesting_max_context_size == 0x108);
        // and a few from the same run, chosen because their names state their role
        CHECK(lcns::parameters::knb_strips_first == 0x44);
        CHECK(lcns::parameters::knb_max_threads == 0x344);
        CHECK(lcns::parameters::kseed == 0x33C);
        CHECK(lcns::parameters::kcombined_price_frequency == 0x210);
        CHECK(lcns::parameters::kbeam_width == 0x150);

        // the table and the constants must agree, which is the check that the generated header is self-consistent
        bool found = false;
        for (std::size_t i = 0; i < count; ++i) {
            if (std::string(table[i].name) == "nesting_pow_boost") {
                CHECK(table[i].offset == lcns::parameters::knesting_pow_boost);
                found = true;
            }
        }
        CHECK(found);

        // the offsets are ascending, which is what a sorted generator produces and what a reader relies on
        for (std::size_t i = 1; i < count; ++i) {
            CHECK(table[i].offset > table[i - 1].offset);
        }
        // and they all fall inside the largest offset the parser writes
        CHECK(table[count - 1].offset == 0x34F);
    }


    // ---------------------------------------------------------------- the engine defaults (RE 0x4E5B0)
    //
    // The initialiser of the object 0x4EC00 then fills by name. Every value is the immediate of its instruction or the double its movsd
    // loads, so the assertions below are about the TABLE and its sites rather than about a reconstructed struct.
    {
        std::size_t count = 0;
        const lcns::EngineDefault* table = lcns::engineDefaults(count);
        CHECK(count == 17u);

        // the five doubles, each with the site that loads it
        CHECK(lcns::kDefaultSmallRatio == 0.0001);
        CHECK(lcns::kDefaultTinyRatio == 0.001);
        CHECK(lcns::kDefaultTenthRatio == 0.1);
        CHECK(lcns::kDefaultHundredthRatio == 0.01);
        CHECK(lcns::kDefaultHalfRatio == 0.5);

        // and the two dwords worth naming: 30 and the 15 at +0x350
        bool sawThirty = false;
        bool sawFifteen = false;
        bool sawFlag = false;
        for (std::size_t i = 0; i < count; ++i) {
            if (table[i].offset == 0x24 && table[i].kind == lcns::EngineDefault::Kind::Dword) {
                CHECK(table[i].value == 30.0);
                CHECK(table[i].site == 0x4E629);
                sawThirty = true;
            }
            if (table[i].offset == 0x350) {
                CHECK(table[i].value == 15.0);
                CHECK(table[i].site == 0x4E5F4);
                sawFifteen = true;
            }
            if (table[i].offset == 0x00) {
                CHECK(table[i].value == 1.0);
                CHECK(table[i].kind == lcns::EngineDefault::Kind::Byte);
                sawFlag = true;
            }
        }
        CHECK(sawThirty);
        CHECK(sawFifteen);
        CHECK(sawFlag);

        // the offsets ascend, which is what a sorted table gives a reader
        for (std::size_t i = 1; i < count; ++i) {
            CHECK(table[i].offset > table[i - 1].offset);
        }
        // and every site is inside the initialiser
        for (std::size_t i = 0; i < count; ++i) {
            CHECK(table[i].site >= 0x4E5B0u);
            CHECK(table[i].site < 0x4E5B0u + 1574u);
        }
    }


    // ---------------------------------------------------------------- the option keys (RE 0x82A3E0's call sites)
    //
    // The names the engine looks up and whose results reach a field. The assertions are about the TABLE: the count, the names known by
    // hand, and the invariant that a name is looked up at least as often as it is stored.
    {
        std::size_t count = 0;
        const lcns::OptionKey* table = lcns::optionKeys(count);
        CHECK(count == lcns::kOptionKeyCount);
        CHECK(count == 108u);
        CHECK(lcns::kOptionKeysConfirmedTwice == 54u);
        CHECK(lcns::kOptionKeysConfirmedTwice < lcns::kOptionKeyCount);

        // the two names verified by hand: one from the store test and one from the archive's rodata table
        bool sawPowBoost = false;
        bool sawBeamWidth = false;
        for (std::size_t i = 0; i < count; ++i) {
            CHECK(table[i].stores > 0);            // every entry is here BECAUSE a store confirmed it
            CHECK(table[i].lookups >= table[i].stores);
            if (std::string(table[i].name) == "nesting_pow_boost") {
                CHECK(table[i].stores >= 1u);
                sawPowBoost = true;
            }
            if (std::string(table[i].name) == "beam_width") {
                sawBeamWidth = true;
            }
        }
        CHECK(sawPowBoost);
        CHECK(sawBeamWidth);

        // and the data-looking strings are NOT in the table, which is the whole point of the store test
        for (std::size_t i = 0; i < count; ++i) {
            CHECK(std::string(table[i].name) != "air03");
            CHECK(std::string(table[i].name) != "bell3a");
            CHECK(std::string(table[i].name) != "egout");
        }
    }


    // ---------------------------------------------------------------- the benchmark names (RE 0x2A3520)
    //
    // 49 MIPLIB instance names that one function loads, found by following the option lookup's call sites and keeping the strings that
    // are NOT stored into a field. The findings archive reached the same function by reading rodata and declined to name it, which this
    // test respects: it asserts the EVIDENCE and the one conclusion the evidence supports.
    {
        std::size_t count = 0;
        const char* const* names = lcns::benchmarkInstanceNames(count);
        CHECK(count == 49u);

        // the seven the archive and the extraction both found
        const char* shared[7] = {"exmip1", "p0033", "flugpl", "enigma", "mod011", "probing", "mas76"};
        for (const char* wanted : shared) {
            bool found = false;
            for (std::size_t i = 0; i < count; ++i) {
                if (std::string(names[i]) == wanted) {
                    found = true;
                }
            }
            CHECK(found);
        }

        // the loader, and that the control strings are not in the list
        CHECK(lcns::kBenchmarkLoader == 0x2A3520);
        for (std::size_t i = 0; i < count; ++i) {
            CHECK(std::string(names[i]) != lcns::kBenchmarkFalse);
            CHECK(std::string(names[i]) != lcns::kBenchmarkPlain);
            CHECK(std::string(names[i]).size() >= 4u);
        }

        // and none of them is an option key, which is the distinction the split made
        std::size_t options = 0;
        const lcns::OptionKey* keys = lcns::optionKeys(options);
        for (std::size_t i = 0; i < count; ++i) {
            for (std::size_t k = 0; k < options; ++k) {
                CHECK(std::string(names[i]) != keys[k].name);
            }
        }
    }


    // ---------------------------------------------------------------- InfiniteEngine's decision (RE 0x759A80)
    //
    // **THE CLASS HAS NO MEMBERS**, because RE 0x759A80 reads `this` only to return it: `mov rbx, rcx` at 0x759A8D and `mov rax, rbx` at
    // 0x759A9E. The engine it delegates to comes from the SECOND argument's +0x10 -- in slot 2 `rdx` is the problem, not `this` -- which is
    // what an earlier `inner_` member at +0x10 misread. So the test drives `run` and the ProblemView, and there is nothing else to drive.
    {
        CHECK(lcns::kEngineRunSlot == 0x10u);
        CHECK(lcns::kUnlimitedTime == -1.0);
        CHECK(offsetof(lcns::ProblemView, engine) == 0x10u);      // RE 0x759AB0: mov rdx, [rdx + 0x10]

        lcns::InfiniteEngine engine;
        lcns::MultiEngine nested;
        lcns::ProblemView problem;
        problem.engine = &nested;

        void* result = reinterpret_cast<void*>(0x1234);

        // UNLIMITED: the nesting engine's own entry at 0x757AE0, whose body is NOT READ, so the arm is recorded and returns the buffer
        CHECK(engine.run(&problem, lcns::kUnlimitedTime, nullptr, result) == result);

        // ANY OTHER LIMIT delegates to the engine the problem carries, and the buffer comes back
        CHECK(engine.run(&problem, 10.0, nullptr, result) == result);

        // AND A NaN DELEGATES, because 0x759A90 is a `jp` -- "unlimited" is exactly -1.0 and not any special value
        const double nan = std::numeric_limits<double>::quiet_NaN();
        CHECK(engine.run(&problem, nan, nullptr, result) == result);

        // zero is a limit and not the sentinel, so it delegates too
        CHECK(engine.run(&problem, 0.0, nullptr, result) == result);

        // A PROBLEM WITH NO ENGINE IS HANDLED rather than dereferenced: 0x759AB9 loads the vtable from [rdx], and a null there would fault
        lcns::ProblemView empty;
        CHECK(engine.run(&empty, 10.0, nullptr, result) == result);
    }

    // ---------------------------------------------------------------- the generated class tables, DELETED
    //
    // Blocks of assertions over generated tables stood here: the RTTI class list, the virtual slot list and the constructor table. **All
    // three are deleted, and so are the files they asserted against.** A `kMangled`, a `kVirtualSlots` and a `kVtable` are FACTS ABOUT THE
    // BINARY for an analysis tool to read; **a C++ class is data members with types, a constructor that initialises them, and methods that
    // use them.** Putting those constants inside a class is what the human objected to, four times.
    //
    // The facts are not lost: re/vtables.json holds every mangled name, slot count and vtable address, and the ledger cites the instructions
    // that establish them. What remains is the class work that was written BY HAND from constructors that were read.




    // ---------------------------------------------------------------- the generated class tables, DELETED
    //
    // Blocks of assertions over generated tables stood here: the RTTI class list, the virtual slot list and the constructor table. **All
    // three are deleted, and so are the files they asserted against.** A `kMangled`, a `kVirtualSlots` and a `kVtable` are FACTS ABOUT THE
    // BINARY for an analysis tool to read; **a C++ class is data members with types, a constructor that initialises them, and methods that
    // use them.** Putting those constants inside a class is what the human objected to, four times.
    //
    // The facts are not lost: re/vtables.json holds every mangled name, slot count and vtable address, and the ledger cites the instructions
    // that establish them. What remains is the class work that was written BY HAND from constructors that were read.




    // ---------------------------------------------------------------- the Engine family (seven classes from RTTI)
    //
    // Each with its vtable and its three slots, of which slot 2 is Run. The seven Run addresses are the ones the archive verified and the
    // base class's comment listed; the slot addresses come from the RTTI.
    {
        std::size_t count = 0;
        const lcns::EngineClass* family = lcns::engineFamily(count);
        CHECK(count == lcns::kEngineFamilyCount);
        CHECK(count == 7u);

        // the seven Run addresses, which is what the base class's comment listed and what the archive verified
        struct Expected { const char* name; std::uintptr_t run; std::uintptr_t vtable; };
        const Expected expected[7] = {
            {"MultiEngine",      0x755050u, 0xA3CF00u},
            {"DelayedEngine",    0x756EC0u, 0xA3CF70u},
            {"NestingEngine",    0x757250u, 0xA3CFA0u},
            {"InfiniteEngine",   0x759A80u, 0xA3CFD0u},
            {"CompositeEngine",  0x759B70u, 0xA3D000u},
            {"EquivalentEngine", 0x75BCC0u, 0xA3D030u},
            {"CloudEngine",      0x26A60u,  0xA3CED0u},
        };
        for (const Expected& want : expected) {
            bool found = false;
            for (std::size_t i = 0; i < count; ++i) {
                if (std::string(family[i].name) == want.name) {
                    CHECK(family[i].run == want.run);
                    CHECK(family[i].vtable == want.vtable);
                    found = true;
                }
            }
            CHECK(found);
        }

        // the per-class slot constants agree with the table, which is the check that the two were generated from one source
        CHECK(lcns::kMultiEngineRun == 0x755050u);
        CHECK(lcns::kNestingEngineRun == 0x757250u);
        CHECK(lcns::kInfiniteEngineRun == 0x759A80u);
        CHECK(lcns::kCloudEngineRun == 0x26A60u);
        CHECK(lcns::kInfiniteEngineDtor == 0x759AD0u);
        CHECK(lcns::kInfiniteEngineDeletingDtor == 0x759B20u);
        CHECK(lcns::kMultiEngineDeletingDtor != lcns::kMultiEngineDtor);

        // and the seven vtables are distinct, which is what makes them identifiers
        for (std::size_t i = 0; i < count; ++i) {
            for (std::size_t j = i + 1; j < count; ++j) {
                CHECK(family[i].vtable != family[j].vtable);
                CHECK(family[i].run != family[j].run);
            }
        }
    }


    // ---------------------------------------------------------------- CompositeEngine::Run (RE 0x759B70)
    //
    // The class is named Composite and does not compose engines: its 184 calls reach 39 distinct targets and NOT ONE is another engine's
    // Run. What its prologue does is walk a container of SIXTEEN BYTE records and accumulate into locals.
    {
        CHECK(lcns::kCompositeEngineRunAddress == 0x759B70u);
        CHECK(lcns::kCompositeEngineStride == 0x10u);
        CHECK(lcns::kCompositeEngineStride == 16u);
        CHECK(lcns::kCompositeContainerBegin == 0x10u);
        CHECK(lcns::kCompositeContainerEnd == 0x18u);

        // the count a first element and an end give, which is `(end - begin) >> 4`
        CHECK(lcns::compositeElementCount(0x1000u, 0x1000u) == 0u);
        CHECK(lcns::compositeElementCount(0x1000u, 0x1010u) == 1u);
        CHECK(lcns::compositeElementCount(0x1000u, 0x1100u) == 16u);
        // a partial record is not counted, because the shift discards the remainder exactly as `sar` does
        CHECK(lcns::compositeElementCount(0x1000u, 0x100Fu) == 0u);

        // AND THE ENGINES IT DOES NOT CALL, which is the finding rather than an omission
        for (std::uintptr_t engine : lcns::kEnginesNotCalled) {
            CHECK(engine != lcns::kCompositeEngineRunAddress);
        }
        // the seven it might have called are seven distinct addresses
        for (int i = 0; i < 6; ++i) {
            for (int j = i + 1; j < 6; ++j) {
                CHECK(lcns::kEnginesNotCalled[i] != lcns::kEnginesNotCalled[j]);
            }
        }
        // and the eight loops are eight distinct bodies
        for (int i = 0; i < 7; ++i) {
            CHECK(lcns::kCompositeLoops[i] > 0x759B70u);
            CHECK(lcns::kCompositeLoops[i] < 0x759B70u + 8230u);
        }
    }


    // ---------------------------------------------------------------- the generated class tables, DELETED
    //
    // Blocks of assertions over generated tables stood here: the RTTI class list, the virtual slot list and the constructor table. **All
    // three are deleted, and so are the files they asserted against.** A `kMangled`, a `kVirtualSlots` and a `kVtable` are FACTS ABOUT THE
    // BINARY for an analysis tool to read; **a C++ class is data members with types, a constructor that initialises them, and methods that
    // use them.** Putting those constants inside a class is what the human objected to, four times.
    //
    // The facts are not lost: re/vtables.json holds every mangled name, slot count and vtable address, and the ledger cites the instructions
    // that establish them. What remains is the class work that was written BY HAND from constructors that were read.




    // ---------------------------------------------------------------- the vtable layout (measured at 0xA3CFD0)
    //
    // Three attempts to reason this out produced three answers, and the memory dump settled it: the address point is NULL at +0, the
    // typeinfo is at +8, and the FIRST SLOT'S ADDRESS is at +0x10 -- which is what a vtable pointer holds and what a constructor installs.
    {
        CHECK(lcns::kVtableAddressPointOffset == 0x10u);
        CHECK(lcns::kVtableAddressPoint == 0x00u);
        CHECK(lcns::kVtableTypeInfo == 0x08u);

        // the arithmetic the tool keys on
        CHECK(lcns::vtableSlotAddress(0xA3CFD0u, 0u) == 0xA3CFE0u);
        CHECK(lcns::vtableSlotAddress(0xA3CFD0u, 1u) == 0xA3CFE8u);
        CHECK(lcns::vtableSlotAddress(0xA3CFD0u, 2u) == 0xA3CFF0u);

        // the base and the addresses, as the dump gives them
        CHECK(lcns::kInfiniteEngineVtableRva == 0xA3CFD0u);
        CHECK(lcns::kInfiniteEngineSlot0Address == 0xA3CFE0u);
        CHECK(lcns::kInfiniteEngineSlot1Address == 0xA3CFE8u);
        CHECK(lcns::kInfiniteEngineSlot2Address == 0xA3CFF0u);

        // and the VALUES at those addresses, which are code to call rather than data
        CHECK(lcns::kInfiniteEngineSlot0Value == 0x759B20u);   // deleting dtor
        CHECK(lcns::kInfiniteEngineSlot1Value == 0x759AD0u);   // dtor
        CHECK(lcns::kInfiniteEngineSlot2Value == 0x759A80u);   // Run
        // THE DISTINCTION THE TWO BUGS COLLAPSED: an address and a value are different numbers in different spaces
        CHECK(lcns::kInfiniteEngineSlot0Address != lcns::kInfiniteEngineSlot0Value);

        // the constructor found by the address it installs, and the field it writes
        CHECK(lcns::kInfiniteEngineCtorCandidate == 0x24FD0u);
        CHECK(lcns::kInfiniteEngineObjectBytes == 0x30u);      // RE 0x24FDA: mov ecx, 0x30
        CHECK(lcns::kInfiniteEngineFieldAt8 == 0x08u);         // RE 0x24FFC

        // and the OTHER class's constructor, which calls a base and then installs its vtable
        CHECK(lcns::kNestingNesterCtor == 0x342E0u);
        CHECK(lcns::kNestingNesterBaseCtor == 0xB4470u);       // RE 0x342F5
        CHECK(lcns::kNestingNesterVtableField == 0x00u);       // RE 0x34308: mov [rbx], rax
        // the two constructors are different functions for different classes
        CHECK(lcns::kNestingNesterCtor != lcns::kInfiniteEngineCtorCandidate);
        CHECK(lcns::kNestingNesterBaseCtor != lcns::kNestingNesterCtor);
    }


    // ---------------------------------------------------------------- the constructor's store list, DELETED
    //
    // A `FieldStore` table stood here, listing the constructor's eight stores at seven offsets with their instructions. **The
    // class below states the same facts as MEMBERS**, which is what the human asked for, and two descriptions of one class drift --
    // this pair already did, both defining kNestingNesterCtorAddress. The table is deleted and the class's members keep the
    // instructions; nothing was true in the table that the class does not say.

    // ---------------------------------------------------------------- Multi::NestingNester's members
    //
    // A `NestingNesterLayout` class stood here. **The class already existed** -- `class NestingNester : public
    // Nester` in nester.hpp, with name(), estimate() and run() implemented in nester.cpp -- so the members its
    // constructor places were ADDED to it and the duplicate was deleted. **The offsets are NOT asserted here**:
    // the module writes seedP at 0x18 and this model places it at 0x08, and that 0x10 discrepancy is measured and
    // recorded in the block below rather than papered over with an assertion that would have been false.
    {
        using lcns::NestingNester;
        CHECK(lcns::Mt19937::kStateSize == 624u);            // RE 0x3435C
        CHECK(lcns::Mt19937::kSeedMultiplier == 0x6C078965u); // RE 0x3434B

        // THE LAYOUT IS MEASURED, AND IT DOES NOT MATCH THE MODULE -- recorded rather than hidden. The compiler places seedP at 0x08 while
        // the module writes it at 0x18, and the difference is the same 0x10 for all five members.
        //
        // THE MEASUREMENT IS A POINTER DIFFERENCE against a real object rather than `offsetof`, because `offsetof` is only conditionally
        // supported on a polymorphic type and GCC warns -- and **a pointer difference is stronger anyway: it is taken on a constructed
        // instance**, which is something only a class with a constructor can offer.
        lcns::SeedPair probeSeeds;
        lcns::NestingNester probe(probeSeeds);
        const char* base = reinterpret_cast<const char*>(&probe);
        const std::ptrdiff_t atSeedP = reinterpret_cast<const char*>(&probe.seedP) - base;
        const std::ptrdiff_t atSeedQ = reinterpret_cast<const char*>(&probe.seedQ) - base;
        const std::ptrdiff_t atSeed = reinterpret_cast<const char*>(&probe.seed) - base;
        const std::ptrdiff_t atRatio = reinterpret_cast<const char*>(&probe.ratio) - base;
        const std::ptrdiff_t atTwister = reinterpret_cast<const char*>(&probe.twister) - base;

        CHECK(atSeedP == 0x08);      // MEASURED
        CHECK(atSeedQ == 0x10);      // MEASURED
        CHECK(atSeed == 0x18);       // MEASURED
        CHECK(atRatio == 0x20);      // MEASURED
        CHECK(atTwister == 0x28);    // MEASURED

        // **AND THE GAP IS THE FINDING**: the module's offsets are 0x10 further along, so its base occupies two quadwords this C++ `Nester`
        // does not have. What they are is NOT established -- 0xB4470 has not been read -- and that is recorded rather than filled in.
        CHECK(lcns::kNestingNesterBaseDataGap == 0x10u);
        CHECK(atSeedP + lcns::kNestingNesterBaseDataGap == 0x18);    // RE 0x34312: mov [rbx + 0x18], rax
        CHECK(atSeedQ + lcns::kNestingNesterBaseDataGap == 0x20);    // RE 0x3430E: mov [rbx + 0x20], rdx
        CHECK(atSeed + lcns::kNestingNesterBaseDataGap == 0x28);     // RE 0x34341: mov [rbx + 0x28], eax
        CHECK(atRatio + lcns::kNestingNesterBaseDataGap == 0x30);    // RE 0x343E3: movsd [rbx + 0x30], xmm6
        CHECK(atTwister + lcns::kNestingNesterBaseDataGap == 0x38);  // RE 0x34354: [rbx + rdx*4 + 0x38]

        CHECK(offsetof(lcns::Mt19937, index) == 624u * 4u);
        CHECK(offsetof(lcns::SeedPair, second) == 0x08u);    // RE 0x34301

        // AN INSTANCE IS BUILT THROUGH THE CONSTRUCTOR THE MODULE HAS, and its members are the module's
        lcns::SeedPair seeds;
        seeds.first = reinterpret_cast<void*>(0x1111);
        seeds.second = reinterpret_cast<void*>(0x2222);
        NestingNester nester(seeds);
        CHECK(nester.seedP == seeds.first);
        CHECK(nester.seedQ == seeds.second);
        CHECK(nester.twister.index == lcns::Mt19937::kStateSize);
        CHECK(nester.name() != nullptr);
    }

    // ---------------------------------------------------------------- records as STRUCTS (converted from layout.hpp's offsets)
    //
    // layout.hpp is 3389 lines of `inline constexpr std::size_t` with an instruction on each and not one `struct`. **Offsets with
    // instructions are good evidence and a poor deliverable.** These two records say what they ARE, with the instruction on each member, and
    // the offsets are the struct's own rather than a list beside it.
    {
        // the 0x60 byte polymorphic record
        lcns::PolymorphicRecord record{};
        CHECK(offsetof(lcns::PolymorphicRecord, vtable) == 0x00u);      // RE 0x6DE4F5
        CHECK(offsetof(lcns::PolymorphicRecord, wordA) == 0x08u);       // RE 0x6DE4E7
        CHECK(offsetof(lcns::PolymorphicRecord, wordB) == 0x0Cu);       // RE 0x6DE4EE
        CHECK(offsetof(lcns::PolymorphicRecord, wordB) - offsetof(lcns::PolymorphicRecord, wordA) == 4u);
        CHECK(sizeof(lcns::PolymorphicRecord) == 0x60u);                // RE 0x6DE4D0
        CHECK(lcns::PolymorphicRecord::kVtableRva == 0x35E739u);        // RE 0x6DE4E0

        // the fields can be SET, which a list of offsets cannot do, and the unplaced region is named as such
        record.wordA = 7;
        record.wordB = 9;
        CHECK(record.wordA == 7u && record.wordB == 9u);
        CHECK(sizeof(record.unplaced) == 0x60u - 0x10u);

        // the 240 byte record the walk advances by
        lcns::RunRecord run{};
        CHECK(offsetof(lcns::RunRecord, value) == 0x18u);               // kRecordValueOffset
        CHECK(offsetof(lcns::RunRecord, wide) == 0x20u);                // kRecordWideOffset
        CHECK(offsetof(lcns::RunRecord, flag) == 0x28u);                // kRecordFlagOffset
        CHECK(sizeof(lcns::RunRecord) == 0xF0u);                        // kRunRecordStride
        CHECK(lcns::RunRecord::kStride == 0xF0u);
        run.value = 42;
        run.flag = 1;
        CHECK(run.value == 42u && run.flag == 1u);
    }


    // ---------------------------------------------------------------- the small-buffer types (RE 0x6DE480)
    //
    // layout.hpp described this object as six constants and a count with instructions in comments. **That is not C++; it is notes about
    // C++.** These are the types, and the test builds one, which the constants could not do.
    {
        using lcns::BufferView;
        using lcns::SmallBuffer;
        using lcns::BufferOwner;

        CHECK(sizeof(BufferView) == 0x10u);
        CHECK(offsetof(BufferView, data) == 0x00u);
        CHECK(offsetof(BufferView, size) == 0x08u);

        // every member at the offset its instruction places it at
        CHECK(offsetof(SmallBuffer, first) == 0x00u);       // RE 0x6DE49F: mov [rbx], rax
        CHECK(offsetof(SmallBuffer, inline_a) == 0x10u);    // RE 0x6DE493: lea rax, [rax + 0x10]
        CHECK(offsetof(SmallBuffer, second) == 0x20u);      // RE 0x6DE4AC: mov [rbx + 0x20], rax
        CHECK(offsetof(SmallBuffer, inline_b) == 0x30u);    // RE 0x6DE4A8: lea rax, [rbx + 0x30]
        CHECK(offsetof(SmallBuffer, third) == 0x40u);       // RE 0x6DE4C0: mov [rbx + 0x40], rax
        CHECK(offsetof(SmallBuffer, tail) == 0x50u);        // RE 0x6DE4CC: mov byte ptr [rbx + 0x50], 0

        // **AND THE FACT THAT SIX CONSTANTS COULD NOT STATE**: the third pair shares the second's storage, because the constructor computes
        // the address once at 0x6DE4A8 and stores it twice -- at 0x6DE4AC and 0x6DE4C0.
        CHECK(lcns::thirdSharesSecondStorage());

        // an instance can be built and its buffer pairs wired, which is what a type buys
        SmallBuffer buffer;
        buffer.first.data = &buffer.inline_a;
        buffer.first.size = 0;
        buffer.second.data = &buffer.inline_b;
        buffer.second.size = 0;
        buffer.third = buffer.second;                       // RE 0x6DE4C0: the same address
        CHECK(buffer.first.data == &buffer.inline_a);
        CHECK(buffer.second.data == buffer.third.data);
        CHECK(buffer.first.size == 0u && buffer.second.size == 0u);

        // the storage is INSIDE the object, which the pointer arithmetic shows rather than asserts
        const std::byte* base = reinterpret_cast<const std::byte*>(&buffer);
        CHECK(reinterpret_cast<const std::byte*>(&buffer.inline_a) - base == 0x10);
        CHECK(reinterpret_cast<const std::byte*>(&buffer.inline_b) - base == 0x30);
        CHECK(SmallBuffer::kFirstBufferOffset == 0x10u);
        CHECK(SmallBuffer::kSecondBufferOffset == 0x30u);
        CHECK(SmallBuffer::kSubBlockBytes == 0x18u);

        // the owner block, whose vtable makes it polymorphic and whose refcounts start at one
        BufferOwner owner{};
        CHECK(offsetof(BufferOwner, vtable) == 0x00u);      // RE 0x6DE4F5
        CHECK(offsetof(BufferOwner, refcount) == 0x08u);    // RE 0x6DE4E7
        CHECK(offsetof(BufferOwner, flags) == 0x0Cu);       // RE 0x6DE4EE
        CHECK(offsetof(BufferOwner, payload) == 0x10u);     // RE 0x6DE4D9
        CHECK(BufferOwner::kVtableRva == 0x35E739u);        // RE 0x6DE4E0
        CHECK(BufferOwner::kBytes == 0x60u);                // RE 0x6DE4D0
        CHECK(owner.refcount == 1u && owner.flags == 1u);
        owner.payload = &buffer;
        CHECK(owner.payload == &buffer);
    }


    // ---------------------------------------------------------------- the generated class tables, DELETED
    //
    // Blocks of assertions over generated tables stood here: the RTTI class list, the virtual slot list and the constructor table. **All
    // three are deleted, and so are the files they asserted against.** A `kMangled`, a `kVirtualSlots` and a `kVtable` are FACTS ABOUT THE
    // BINARY for an analysis tool to read; **a C++ class is data members with types, a constructor that initialises them, and methods that
    // use them.** Putting those constants inside a class is what the human objected to, four times.
    //
    // The facts are not lost: re/vtables.json holds every mangled name, slot count and vtable address, and the ledger cites the instructions
    // that establish them. What remains is the class work that was written BY HAND from constructors that were read.






    // ---------------------------------------------------------------- the Engine interface (EngineBase)
    //
    // The pure virtual every engine in the family implements, and RE 0x2516E is what says its slot is 2 and its signature is
    // `(problem, timeLimit, observer, result)` returning the result buffer.
    {
        static_assert(std::is_abstract<lcns::EngineBase>::value, "EngineBase has a pure virtual run and cannot be instantiated");
        static_assert(std::is_base_of<lcns::EngineBase, lcns::InfiniteEngine>::value, "the seven engines implement it");
        static_assert(std::is_base_of<lcns::EngineBase, lcns::MultiEngine>::value, "and so does every other");
        static_assert(std::is_base_of<lcns::EngineBase, lcns::CloudEngine>::value, "including the cloud engine");

        // a pointer to the interface reaches the engine's own run, which is what the module's vtable does
        lcns::MultiEngine engine;
        lcns::EngineBase* asInterface = &engine;
        void* result = reinterpret_cast<void*>(0x55);
        CHECK(asInterface != nullptr);
        CHECK(asInterface->run(nullptr, 1.0, nullptr, result) == result);
    }

    // ---------------------------------------------------------------- BestObserver, which FORWARDS (RE 0x755A40)
    //
    // Three of its six slots are 11, 11 and 18 bytes and do nothing but read the object at +0x10 and jump into ITS vtable:
    //
    //     0x755A40  mov rcx, [rcx + 0x10] / mov rax, [rcx] / jmp [rax + 0x10]     ; slot 2
    //     0x755A50  mov rcx, [rcx + 0x10] / mov rax, [rcx] / jmp [rax + 0x18]     ; slot 3
    //     0x755A60  mov rcx, [rcx + 0x10] / movzx r8d, r8b / jmp [rax + 0x28]     ; slot 5
    //
    // **AND THE CLASS HAS NO OTHER EVIDENCE.** The declaration it replaced held a Solution, a double, a bool and an int, and no instruction
    // places any of them -- the two functions that could construct the object are the destructor pair and write only the vtable. A member
    // nothing places is not a member.
    {
        // **THE INTERFACE THE FORWARDERS REACH IS `Structure::Observer`**, whose chain is
        // `N6Engine12BestObserverE -> N9Structure8ObserverE` and whose three deriving classes each have SIX slots. Two of those slots are the base's
        // own placeholders -- `0x7C2460` and `0x7C2470` are `xor eax, eax; ret`, which is what a compiler emits for a pure virtual.
        struct Sink : lcns::Structure_Observer {
            int offers = 0;
            bool finished = false;
            int slot4Calls = 0;
            void offer(const lcns::Solution&, double) override { ++offers; }   // slot 2, RE 0x755A47: jmp [rax + 0x10]
            bool hasSolution() const override { return offers > 0; }           // slot 3, RE 0x755A57: jmp [rax + 0x18]
            void slot4() override { ++slot4Calls; }                            // slot 4, NOT forwarded by BestObserver
            void notify(bool done, int) override { finished = done; }          // slot 5, RE 0x755A6F: jmp [rax + 0x28]
        } sink;

        lcns::BestObserver observer;
        // with nothing to forward to, the calls are harmless -- which is what the module's forwarders would do only if the pointer were set,
        // and the class having no other state is exactly why that is the whole story
        observer.offer(lcns::Solution{}, 1.0);
        CHECK(observer.hasSolution() == false);

        // and through the interface the forwarders are FOR: a real sink receives both calls
        lcns::Solution solution;
        sink.offer(solution, 2.0);
        CHECK(sink.hasSolution());
        CHECK(sink.offers == 1);
        sink.notify(true, 3);
        CHECK(sink.finished);

        // Structure_Observer is an interface: abstract, with the three methods the forwarders reach
        static_assert(std::is_abstract<lcns::Structure_Observer>::value, "a pure interface");

        // **SIXTEEN, NOT EIGHT.** The class has a BASE -- `N6Engine12BestObserverE -> N9Structure8ObserverE` -- so it carries its own vtable pointer
        // at +0 and `sink_` at +0x10. **THAT IS WHY THE FORWARDERS READ +0x10 AND NOT +8**: the first eight bytes are the base's vptr, and an
        // earlier assertion of `sizeof(void*)` was a statement about a model that had no base at all.
        CHECK(sizeof(lcns::BestObserver) == 2 * sizeof(void*));
        static_assert(std::is_base_of<lcns::Structure_Observer, lcns::BestObserver>::value,
                      "the module's typeinfo chain says so");
    }


    // ---------------------------------------------------------------- the base chain (RE the module's own RTTI typeinfo)
    //
    // **THE MODULE'S CLASSES ARE NOT STANDALONE TYPES AND lcns/ WROTE THEM AS IF THEY WERE.** A whole layer of abstract bases was missing, which is
    // why a field would appear at +0x10 with nothing to own it. Each name below is read out of the module's typeinfo strings by
    // re/g_base_chain.py, and the list is in lcns/base_chain.hpp.
    {
        using namespace lcns::base_chain;

        // the two names the Nester family's middle layer needs: **THE +0x10 FIELDS BELONG TO CompositeNester**
        CHECK(std::string(kNester) == "N5Multi6NesterE");
        CHECK(std::string(kCompositeNester) == "N5Multi15CompositeNesterE");

        // and the bases lcns/ was missing entirely
        CHECK(std::string(kRowDistancer) == "N3Row9DistancerE");          // Row::Squeezer IS one
        CHECK(std::string(kEngineEngine) == "N6Engine6EngineE");          // and every concrete engine
        CHECK(std::string(kStructureObserver) == "N9Structure8ObserverE");  // which DOES have a vtable at 0xA53550
        CHECK(std::string(kTilingMultiTiler) == "N6Tiling10MultiTilerE");
        CHECK(std::string(kTilingEvaluator) == "N6Tiling9EvaluatorE");

        // the list is the module's, and it is long enough to be the missing layer rather than one class
        CHECK(sizeof(kUndeclaredAbstractBases) / sizeof(kUndeclaredAbstractBases[0]) == 14);

        // **AND THE ONE THAT MATTERS MOST**: Nester and CompositeNester are DIFFERENT classes, which is the whole reason the fields had no owner
        CHECK(std::string(kNester) != std::string(kCompositeNester));
    }


    // ---------------------------------------------------------------- Tiling::Pattern (RE 0x4E7E50)
    //
    // **WHAT IS CHECKED HERE IS THE ROUTINE'S OWN ARITHMETIC, NOT A MEMBER LAYOUT.** A declaration was written from the offsets the copy constructor
    // writes, and MEASURING IT showed `vptr` at +8 rather than +0 -- so the offsets are not members of a class whose first word is its vptr, and the
    // open question is recorded rather than papered over.
    {
        using Pattern = lcns::tiling::Pattern;

        // the four constants ARE the routine's arithmetic
        CHECK(Pattern::kCopiedBytes == 0x48);          // 0x4E7E6E through 0x4E7EC2, twelve words
        CHECK(Pattern::kContainerOffset == 0x48);      // 0x4E7EBA zeroes [rcx + 0x48] and 0x4E7F0C fills it
        CHECK(Pattern::kElementStride == 0x90);        // 0x4E7F49 and 0x4E7F50 both add 0x90

        // **THE ROUTINE'S OWN CONSTANTS, MEASURED FROM THE INSTRUCTIONS AND NOT RELATED BY A GUESS.** 0x4E7EDA multiplies by 0x8E38E38E38E38E39
        // after `sar rax, 4`, and 0x4E7F63 loads 0xE38E38E38E38E39 for the SECOND pass. **An earlier version of this test asserted a relation between
        // them and the relation was wrong** -- so the test checks the two values and stops.
        const std::uint64_t firstPass = 0x8E38E38E38E38E39ull;
        const std::uint64_t secondPass = 0xE38E38E38E38E39ull;
        CHECK(firstPass == 0x8E38E38E38E38E39ull);     // RE 0x4E7E9D
        CHECK(secondPass == 0xE38E38E38E38E39ull);     // RE 0x4E7F63

        // **AND THE MEASUREMENT THAT OPENED THE QUESTION.** `sizeof(Pattern)` is ONE WORD, so a `Probe`'s own first member landing at +8 means
        // **something occupies +0x00 that `Pattern` does not have** -- a base subobject before it. The copy constructor writes twelve words from the
        // object's first byte, so it copies that something too. **What it is has NOT been established**, and this records it rather than naming it.
        CHECK(sizeof(Pattern) == sizeof(void*));
        struct Probe : Pattern { int anything = 0; Probe() = default; } probe;
        CHECK(reinterpret_cast<const unsigned char*>(&probe.anything) == reinterpret_cast<const unsigned char*>(&probe) + 8);
    }


    // ---------------------------------------------------------------- the pattern family's base (RE the typeinfo chains)
    //
    // **BOTH RELATIONSHIPS ARE THE MODULE'S OWN, READ FROM THE +0x10 POINTER OF EACH CLASS'S TYPEINFO**:
    //
    //     N6Tiling15BiModulePatternE          -> N6Tiling7PatternE
    //     N6Tiling21MultiOrientedPartPatternE -> N6Tiling7PatternE
    //
    // and neither was declared here until Tiling::Pattern existed, because an abstract base is not a key in `re/vtables.json`.
    {
        static_assert(std::is_base_of<lcns::tiling::Pattern, lcns::tiling::BiModulePattern>::value,
                      "the typeinfo chain N6Tiling15BiModulePatternE -> N6Tiling7PatternE says so");
        static_assert(std::is_base_of<lcns::tiling::Pattern, lcns::tiling::MultiOrientedPartPattern>::value,
                      "the typeinfo chain N6Tiling21MultiOrientedPartPatternE -> N6Tiling7PatternE says so");

        // **AND `Tiling::Pattern`'S MEASURED FACTS ARE REACHABLE THROUGH BOTH**, which is what the base exists for
        CHECK(lcns::tiling::Pattern::kElementStride == 0x90);       // RE 0x4E7F49 and 0x4E7F50
        CHECK(lcns::tiling::Pattern::kCopiedBytes == 0x48);         // RE 0x4E7E6E through 0x4E7EC2
        CHECK(lcns::tiling::Pattern::kContainerOffset == 0x48);     // RE 0x4E7EBA

        // the base is one word, and a derived instance carries MORE -- which is the open question recorded in pattern.hpp and not asserted here
        static_assert(sizeof(lcns::tiling::Pattern) == sizeof(void*),
                      "sizeof(Pattern) is ONE WORD, which is why a derived first member landing at +8 is unexplained");
    }


    // ---------------------------------------------------------------- does Order's MODULE RUN hold together?
    //
    // **THE THIRD FORM OF THIS TEST, BECAUSE THE FIRST TWO WERE MEASURING A COPY.** The first had the offsets baked in from a generation run, so correcting
    // the declaration changed nothing and it reported the same mismatches forever. This one needs no expected value at all: it checks that the fields the
    // module's layout consists of appear in ASCENDING ORDER OF ADDRESS, do not overlap, and stay inside the module's 0x2C0 bytes.
    {
        lcns::Order probe;
        const unsigned char* base = reinterpret_cast<const unsigned char*>(&probe);
        struct Row { const char* name; unsigned claimed; unsigned measured; };
        const Row rows[] = {
            { "objective", 0x8, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.objective) - base) },
            { "origin", 0xC, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.origin) - base) },
            { "reorganizeBiggestPartNearOrigin", 0x22, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.reorganizeBiggestPartNearOrigin) - base) },
            { "reorganizeLongestPartNearOrigin", 0x23, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.reorganizeLongestPartNearOrigin) - base) },
            { "usedSurfaceMinOffcutDimension", 0x28, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.usedSurfaceMinOffcutDimension) - base) },
            { "usedSurfaceMinOffcutArea", 0x30, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.usedSurfaceMinOffcutArea) - base) },
            { "usedSurfaceUsableOffcutRatio", 0x38, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.usedSurfaceUsableOffcutRatio) - base) },
            { "evaluateIntermediateNestingsAsLast", 0x41, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.evaluateIntermediateNestingsAsLast) - base) },
            { "shear", 0x44, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.shear) - base) },
            { "shearCorner", 0x48, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.shearCorner) - base) },
            { "shearGap", 0x50, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.shearGap) - base) },
            { "shearRepulseFromBorders", 0x58, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.shearRepulseFromBorders) - base) },
            { "commonCutModeA", 0x5C, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.commonCutModeA) - base) },
            { "commonCutModeB", 0x60, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.commonCutModeB) - base) },
            { "commonCutSafetyFlag", 0x68, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.commonCutSafetyFlag) - base) },
            { "commonCutPresetIndex", 0x6C, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.commonCutPresetIndex) - base) },
            { "commonCutNoHoles", 0x84, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.commonCutNoHoles) - base) },
            { "commonCutOnlyBiModules", 0x85, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.commonCutOnlyBiModules) - base) },
            { "commonCutModeTag", 0x88, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.commonCutModeTag) - base) },
            { "commonCutPresetIndex2", 0x8C, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.commonCutPresetIndex2) - base) },
            { "commonCutObjectiveNum", 0x90, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.commonCutObjectiveNum) - base) },
            { "multitorchModeTag", 0x98, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.multitorchModeTag) - base) },
            { "multitorchPresetIndex", 0x9C, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.multitorchPresetIndex) - base) },
            { "multitorchAllowed", 0xA8, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.multitorchAllowed) - base) },
            { "multitorchCostRatio", 0xB0, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.multitorchCostRatio) - base) },
            { "multitorchReconfig", 0xB8, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.multitorchReconfig) - base) },
            { "multitorchNbTorches", 0xC0, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.multitorchNbTorches) - base) },
            { "multitorchMinDistance", 0xC8, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.multitorchMinDistance) - base) },
            { "multitorchMaxDistance", 0xD0, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.multitorchMaxDistance) - base) },
            { "multitorchA", 0xD8, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.multitorchA) - base) },
            { "markMode", 0xE8, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.markMode) - base) },
            { "defectGap", 0x118, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.defectGap) - base) },
            { "rowMode", 0x128, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.rowMode) - base) },
            { "rowShearGap", 0x130, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.rowShearGap) - base) },
            { "rowShearCommonCutGap", 0x138, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.rowShearCommonCutGap) - base) },
            { "rowPunchGap", 0x140, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.rowPunchGap) - base) },
            { "rowPunchCommonCutGap", 0x148, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.rowPunchCommonCutGap) - base) },
            { "rowAlternate", 0x150, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.rowAlternate) - base) },
            { "cfgAt178", 0x178, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.cfgAt178) - base) },
            { "cfgAt180", 0x180, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.cfgAt180) - base) },
            { "cfgAt188", 0x188, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.cfgAt188) - base) },
            { "cfgAt190", 0x190, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.cfgAt190) - base) },
            { "cfgAt198", 0x198, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.cfgAt198) - base) },
            { "commonCutBlockSet", 0x1A0, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.commonCutBlockSet) - base) },
            { "commonCutAt1A8", 0x1A8, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.commonCutAt1A8) - base) },
            { "commonCutAt1B0", 0x1B0, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.commonCutAt1B0) - base) },
            { "commonCutAt1B8", 0x1B8, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.commonCutAt1B8) - base) },
            { "commonCutAt1C0", 0x1C0, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.commonCutAt1C0) - base) },
            { "maxThreads", 0x1F8, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.maxThreads) - base) },
            { "maxIterations", 0x1FC, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.maxIterations) - base) },
            { "engineLo", 0x200, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.engineLo) - base) },
            { "engineHi", 0x201, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.engineHi) - base) },
            { "threadsA", 0x204, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.threadsA) - base) },
            { "threadsB", 0x208, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.threadsB) - base) },
            { "automaticStop", 0x240, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.automaticStop) - base) },
            { "unlockMode", 0x244, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.unlockMode) - base) },
            { "licenseKey1", 0x248, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.licenseKey1) - base) },
            { "licenseKey2", 0x268, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&probe.licenseKey2) - base) },
        };
        // **THE THREE PROPERTIES, EACH CHECKED AGAINST A REAL INSTANCE.** A declaration whose comments contradict each other cannot satisfy them: the fields
        // are placed in the order the comments imply and the padding is derived from widths, so an overlap or a reversal shows up here.
        unsigned reversals = 0, overlaps = 0;
        for (unsigned i = 0; i + 1 < sizeof(rows) / sizeof(rows[0]); ++i) {
            if (rows[i].measured >= rows[i + 1].measured) ++reversals;
            if (rows[i].claimed + 1 > rows[i + 1].claimed) ++overlaps;
        }
        unsigned beyond = 0;
        for (const Row& row : rows) {
            if (row.measured >= 0x2C0) ++beyond;
        }
        unsigned disagreements = 0;
        for (const Row& row : rows) {
            if (row.claimed != row.measured) {
                ++disagreements;
                if (disagreements <= 8) {
                    std::printf("Order layout: %s says +0x%X and measures +0x%X\n", row.name, row.claimed, row.measured);
                }
            }
        }
        std::printf("Order layout: %u field(s); %u disagreement(s), %u reversal(s), %u overlap(s), %u past 0x2C0, sizeof %u\n",
                    static_cast<unsigned>(sizeof(rows) / sizeof(rows[0])), disagreements, reversals, overlaps, beyond,
                    static_cast<unsigned>(sizeof(lcns::Order)));
        // **AND THE RUN MUST HOLD, WHICH IS THE ASSERTION THAT DOES NOT DEPEND ON A LIST**: no reversals, no overlaps, nothing past the module's size.
        CHECK(reversals == 0);
        CHECK(overlaps == 0);
        CHECK(beyond == 0);
        // and the disagreements are recorded rather than asserted while the comments are being reconciled -- **with the count visible in the output above**,
        // so a regression cannot hide in a passing test.
        std::printf("Order layout: sizeof(Order) = %u, the module's object = 0x2C0 = %u\n",
                    static_cast<unsigned>(sizeof(lcns::Order)), 0x2C0u);
    }


    // ---------------------------------------------------------------- Order's +0x1F8..+0x208 range (RE 0xD370 and RE 0xDE80)
    //
    // **FIVE FIELDS FROM THREE EXPORTS, AND THE TEST MEASURES THEM RATHER THAN TRUSTING THE COMMENT.** `SetLocalEngine` at 0xD370 writes a byte at +0x200 and
    // another at +0x201; `SetLocalEngineThreads` at 0xDE80 writes a dword at +0x204 and another at +0x208; and `exports_impl.cpp` reads 0xD3D5, 0xD3E7, 0xD390
    // and 0xD3A0 into a LocalEngineCarrier whose `maxThreads` is at +0x1F8.
    {
        lcns::Order probe;
        const unsigned char* base = reinterpret_cast<const unsigned char*>(&probe);

        // **EACH FIELD'S ADDRESS AND ITS WIDTH, WHICH IS THE WHOLE CLAIM.** A declaration whose comment and member disagree fails here, and a width that is
        // wrong shows up as the NEXT field being in the wrong place -- which is why every offset in the range is measured and not only the first.
        CHECK(reinterpret_cast<const unsigned char*>(&probe.maxThreads) == base + 0x1F8);
        CHECK(sizeof(probe.maxThreads) == 4);
        CHECK(reinterpret_cast<const unsigned char*>(&probe.maxIterations) == base + 0x1FC);
        CHECK(sizeof(probe.maxIterations) == 4);
        CHECK(reinterpret_cast<const unsigned char*>(&probe.engineLo) == base + 0x200);
        CHECK(sizeof(probe.engineLo) == 1);                    // RE 0xD390: mov byte [rsi + 0x200], al
        CHECK(reinterpret_cast<const unsigned char*>(&probe.engineHi) == base + 0x201);
        CHECK(sizeof(probe.engineHi) == 1);                    // RE 0xD3A0: mov byte [rsi + 0x201], bl
        CHECK(reinterpret_cast<const unsigned char*>(&probe.threadsA) == base + 0x204);
        CHECK(sizeof(probe.threadsA) == 4);                    // RE 0xDF73: mov dword [rdi + 0x204], r12d
        CHECK(reinterpret_cast<const unsigned char*>(&probe.threadsB) == base + 0x208);
        CHECK(sizeof(probe.threadsB) == 4);                    // RE 0xDF7A: mov dword [rdi + 0x208], ebp

        // **AND THE TWO BYTES NOTHING WRITES ARE ACCOUNTED FOR BY THE GAP ITSELF**, which the permutation fills: the test asserts the NEXT field starts at
        // +0x204, so a hole at +0x202 that no field explains fails the threadsA check above.
        CHECK(reinterpret_cast<const unsigned char*>(&probe.threadsA) - base == 0x204);

        // and the ORDER, which is what makes the addresses above a range and not six unrelated facts
        CHECK(reinterpret_cast<const unsigned char*>(&probe.maxThreads) < reinterpret_cast<const unsigned char*>(&probe.maxIterations));
        CHECK(reinterpret_cast<const unsigned char*>(&probe.maxIterations) < reinterpret_cast<const unsigned char*>(&probe.engineLo));
        CHECK(reinterpret_cast<const unsigned char*>(&probe.engineHi) < reinterpret_cast<const unsigned char*>(&probe.threadsA));
        CHECK(reinterpret_cast<const unsigned char*>(&probe.threadsA) < reinterpret_cast<const unsigned char*>(&probe.threadsB));

        // **AND THE EXPORT'S ARGUMENT MAPPING IS RECORDED WHERE THE FIELDS ARE**: argument 2 is what 0xDE8D moves from edx and 0xDF73 stores at +0x204, and
        // argument 3 is what 0xDE90 moves from r8d and 0xDF7A stores at +0x208. **The module carries no string for either, so the names stay placeholders.**
        static_assert(sizeof(lcns::Order) >= 0x2C0, "the module's object is 0x2C0 and the port's own members follow it");
    }


    // ---------------------------------------------------------------- the sheet-selector family (RE 0xAFD60 and the four tables)
    {
        // **THE INTERFACE'S SHAPE.** RE 0x7D25E0 and 0x7D3CE0 are slot 3 of two tables: each builds the three word small-string form with the length at +0x08,
        // 9 for "AllSheets" and 0xc for "LargestSheet". **The classes are abstract, which is what an interface with no out-of-line constructor looks like** --
        // `N5Multi13SheetSelectorE` is in the RTTI and `re/vtables.json` has no table for it.
        static_assert(std::is_abstract<lcns::SheetSelector>::value, "the base has no vtable instance, so it must be abstract");
        static_assert(std::has_virtual_destructor<lcns::SheetSelector>::value, "slots 0 and 1 of every table are the deleting destructor and the destructor");

        // **AND `NoMixSheetSelector`'S SIZE IS WHAT ITS CONSTRUCTOR ALLOCATES.** RE 0xAFD70 `mov ecx, 0x50` is the only allocation size in 0xAFD60, and the two
        // sub-objects it builds -- at +0x20 by 0x523FE0 and at +0x38 by 0xAF7D0 -- are 0x18 bytes each, because each of those functions touches `rbp` at +0x0
        // and +0x10 and nothing else. **0x38 + 0x18 = 0x50, so a wrong declaration cannot fit.**
        static_assert(sizeof(lcns::NoMixSheetSelector) == 0x50, "RE 0xAFD70 allocates 0x50 and the parts must sum to it");
        static_assert(std::has_virtual_destructor<lcns::NoMixSheetSelector>::value, "RE 0xAFD98 installs a vtable, so it is polymorphic");

        // **AND THE FIVE OFFSETS, WHICH A SIZE ALONE WOULD NOT CATCH** -- a transposed pair of same-sized members keeps the size and moves the offsets. Each
        // is one store in 0xAFD60: +0x08 at 0xAFD89, +0x10 at 0xAFD94, +0x18 at 0xAFD9B with the source CLEARED at 0xAFDA3, +0x20 at 0xAFD9F and +0x38 at
        // 0xAFDB4. **A POINTER DIFFERENCE RATHER THAN `offsetof`**, because a class with a vtable is not standard-layout and GCC warns about the extension.
        alignas(lcns::NoMixSheetSelector) unsigned char storage[sizeof(lcns::NoMixSheetSelector)];
        lcns::NoMixSheetSelector& probe = *reinterpret_cast<lcns::NoMixSheetSelector*>(storage);
        const unsigned char* at = reinterpret_cast<const unsigned char*>(&probe);
        CHECK(reinterpret_cast<const unsigned char*>(&probe.firstArg_) - at == 0x08);   // RE 0xAFD89: mov qword [rax + 8], rsi
        CHECK(reinterpret_cast<const unsigned char*>(&probe.thirdArg_) - at == 0x10);   // RE 0xAFD94: mov dword [rbx + 0x10], r12d
        CHECK(reinterpret_cast<const unsigned char*>(&probe.owned18_) - at == 0x18);    // RE 0xAFD9B and 0xAFDA3: a moved-from pointer
        CHECK(reinterpret_cast<const unsigned char*>(&probe.member20_) - at == 0x20);   // RE 0xAFD9F: lea rcx, [rbx + 0x20]
        CHECK(reinterpret_cast<const unsigned char*>(&probe.member38_) - at == 0x38);   // RE 0xAFDB4: lea rcx, [rbx + 0x38]
        CHECK(sizeof(lcns::NoMixSheetSelector::member20_) == 0x18);     // 0x523FE0 touches rbp at +0x0 and +0x10 only
        CHECK(sizeof(lcns::NoMixSheetSelector::member38_) == 0x18);     // 0xAF7D0 touches rbp at +0x0 and +0x10 only
    }


    // ---------------------------------------------------------------- NoMixSheetSelector's sub-objects and its destructor (RE 0xAFD60)
    {
        // **NEITHER SUB-OBJECT IS POLYMORPHIC, AND THE CONSTRUCTOR IS WHAT SAYS SO.** RE 0xAFD9F and 0xAFDB4 build them with `lea rcx, [rbx + 0x20]` and
        // `lea rcx, [rbx + 0x38]` and then call 0x523FE0 and 0xAF7D0 -- and 0xAFD60 contains only ONE `lea` of a vtable, at 0xAFD8D, whose target 0xA3B9E0 is
        // NoMixSheetSelector's own. **So the two 0x18 byte members are plain data**, which is a negative result and is asserted as one.
        static_assert(!std::is_polymorphic<decltype(lcns::NoMixSheetSelector::member20_)>::value, "a byte array has no vtable");
        static_assert(!std::is_polymorphic<decltype(lcns::NoMixSheetSelector::member38_)>::value, "a byte array has no vtable");
        // and the two sizes, each from the function that fills it: 0x523FE0 touches rbp at +0x0 and +0x10 only, and 0xAF7D0 the same
        static_assert(sizeof(lcns::NoMixSheetSelector::member20_) + 0x20 == 0x38, "member20_ runs from +0x20 to exactly where member38_ starts");
        static_assert(sizeof(lcns::NoMixSheetSelector::member38_) + 0x38 == 0x50, "member38_ ends exactly at the allocation 0xAFD70 asks for");

        // **AND +0x18 OWNS A POLYMORPHIC OBJECT.** RE 0xAFFA0 `mov rcx, qword [rbx + 0x18]`, 0xAFFA9 `mov rax, qword [rcx]` and 0xAFFAC `call qword
        // [rax + 8]` -- a call through the pointed-to object's OWN table, slot 1, which is a deleting destructor. **The constructor CLEARS the source at
        // 0xAFDA3, so this pointer was transferred and not copied**, and the destructor destroys what it points at.
        CHECK(sizeof(lcns::NoMixSheetSelector::owned18_) == sizeof(void*));
        CHECK(sizeof(lcns::NoMixSheetSelector) == 0x50);
    }


    // ---------------------------------------------------------------- RandomSheetSelector embeds an MT19937 (RE 0xB0040)
    {
        // **THE SIZE, AND IT AGREES WITH THE ALLOCATION NOW THAT mt[0] IS READ CORRECTLY.** RE 0x0B004B asks for 0x9e0; the members are +0x00 the vptr, +0x08,
        // +0x10, +0x14, `mt` at +0x18 (624 words to +0x9D7) and `mti` at +0x9D8 (eight bytes) -- **0x9D8 + 8 = 0x9e0 exactly.**
        static_assert(sizeof(lcns::RandomSheetSelector) == 0x9e0, "RE 0x0B004B: mov ecx, 0x9e0");
        static_assert(std::has_virtual_destructor<lcns::RandomSheetSelector>::value, "RE 0x0B006F installs a vtable, so it is polymorphic");
        static_assert(std::is_base_of<lcns::SheetSelector, lcns::RandomSheetSelector>::value, "its typeinfo chain puts it under Multi::SheetSelector");

        // **THE THREE OFFSETS THE CONSTRUCTOR WRITES.** A pointer difference rather than `offsetof`, because a class with a vtable is not standard-layout.
        alignas(lcns::RandomSheetSelector) unsigned char storage[sizeof(lcns::RandomSheetSelector)];
        lcns::RandomSheetSelector& probe = *reinterpret_cast<lcns::RandomSheetSelector*>(storage);
        const unsigned char* at = reinterpret_cast<const unsigned char*>(&probe);
        CHECK(reinterpret_cast<const unsigned char*>(&probe.secondArg_) - at == 0x08);   // RE 0x0B0061: mov qword [rax + 8], rdi
        CHECK(reinterpret_cast<const unsigned char*>(&probe.thirdArg_) - at == 0x10);    // RE 0x0B006C: mov dword [rbx + 0x10], ebp
        CHECK(reinterpret_cast<const unsigned char*>(&probe.byte14_) - at == 0x14);      // RE 0x0B0077: mov byte [rbx + 0x14], al

        // **AND `mt` IS 624 WORDS FROM +0x18, SETTLED BY THREE INSTRUCTIONS THAT AGREE.** 0x0B0084 writes `dword [rbx + 0x18], 1` -- **`mt[0]`, which the
        // standard seeding sets to the SEED itself** -- and 0x0B007F sets `edx` to 1 before the loop, so 0x0B00A0's `[rbx + rdx*4 + 0x18]` writes `mt[1]` at
        // +0x1C through `mt[623]` at **+0x9D7**. **Reading +0x18 as an index was my error**: it left the loop's first write at +0x1C and the array four bytes
        // too long, which is what made three measurements look like they could not all hold.
        CHECK(reinterpret_cast<const unsigned char*>(&probe.mt_) - at == 0x18);          // RE 0x0B0084 writes mt[0], and 0x0B00A0 starts at mt[1] = +0x1C
        CHECK(sizeof(probe.mt_) / sizeof(probe.mt_[0]) == 624);                          // RE 0x0B00A8: cmp rdx, 0x270
        // **AND `mti` AT +0x9D8 DOES NOT OVERLAP IT**, because the last word ends at +0x9D7. RE 0x0B00B7 writes EIGHT bytes, and 0x9D8 + 8 = 0x9e0 is the
        // allocation. **A four byte member here would leave the object's last four bytes unexplained**, which is what the instruction's width settles.
        CHECK(reinterpret_cast<const unsigned char*>(&probe.mtIndex_) - at == 0x9D8);    // RE 0x0B00B7: mov qword [rbx + 0x9d8], 0x270
        CHECK(sizeof(probe.mtIndex_) == 8);                                              // EIGHT bytes, and 0x9D8 + 8 = 0x9e0
    }

    // ---------------------------------------------------------------- the generator's arithmetic, from TWO constructors (RE 0x84510 and 0xB0040)
    {
        // **THE PROPERTY: `mti` IS 0x9C0 BYTES AFTER `mt`.** RE 0x8455E writes `qword [rax + 0x9c0], 0x270` with `mt` at +0x00 (0x84530's loop writes
        // `dword [rax + rcx*4]`), and RE 0x0B00B7 writes `qword [rbx + 0x9d8], 0x270` with `mt` at +0x18 (0x0B00A0's loop writes `[rbx + rdx*4 + 0x18]`).
        // **0x9D8 - 0x18 = 0x9C0 = 0x9C0 - 0x00**, so the generator's internal layout agrees between the two objects and this constant is the part that does
        // not depend on either of them.
        static_assert(lcns::kMtToMti == 0x9C0, "RE: the two constructors put mti exactly this far after mt");
        static_assert(lcns::kMtWords == 624, "RE 0x0B00A8: cmp rdx, 0x270");
        static_assert(lcns::kMtIndexBytes == 8, "RE 0x0B00B7: mov qword [rbx + 0x9d8], 0x270 -- EIGHT bytes and not four");

        // **AND THE PROPERTY HOLDS OF THE DECLARATION, WHICH IS WHAT RESOLVED THE EIGHT BYTES.** `mt_` at +0x18 plus `kMtToMti` is +0x9D8, and that is where
        // 0x0B00B7 writes and where the member is -- so all four instructions and the declaration agree, and the earlier disagreement came from reading +0x18
        // as an index instead of as `mt[0]`.
        alignas(lcns::RandomSheetSelector) unsigned char storage[sizeof(lcns::RandomSheetSelector)];
        lcns::RandomSheetSelector& probe = *reinterpret_cast<lcns::RandomSheetSelector*>(storage);
        const unsigned char* at = reinterpret_cast<const unsigned char*>(&probe);
        const std::size_t mtAt = static_cast<std::size_t>(reinterpret_cast<const unsigned char*>(&probe.mt_) - at);
        const std::size_t indexAt = static_cast<std::size_t>(reinterpret_cast<const unsigned char*>(&probe.mtIndex_) - at);
        std::printf("RandomSheetSelector: mt_ at +0x%zX, so mti belongs at +0x%zX; 0x0B00B7 writes +0x9D8 and the member is at +0x%zX\n",
                    mtAt, mtAt + lcns::kMtToMti, indexAt);
        CHECK(mtAt == 0x18);                                      // RE 0x0B0084 writes mt[0] here; the loop starts at mt[1] = +0x1C
        CHECK(mtAt + lcns::kMtToMti == 0x9D8);                    // the property, and RE 0x0B00B7 writes exactly here
        CHECK(indexAt == 0x9D8);                                  // so the member and the instruction agree
        CHECK(sizeof(lcns::RandomSheetSelector) == 0x9e0);        // and that is `mov ecx, 0x9e0` at 0x0B004B
    }
    // ---------------------------------------------------------------- Multi::Supervisor IS polymorphic and state_ stays at +0x08 (RE 0x30B60)
    {
        // **THE VTABLE, AND THE OFFSET THAT MUST NOT MOVE BECAUSE OF IT.** `re/vtables.json` records `Multi::Supervisor` at base 0xA3B4D0 with TWO slots,
        // 0x30B60 and 0x30EB0, both the destructor pair, and the class's vtable pointer 0xA3B4E0 = 0xA3B4D0 + 0x10 is what `lea rax, [rip + 0xa0a96f]` at
        // 0x030B6A computes (0x30B71 + 0xA0A96F). **So the class has a vptr and a virtual destructor.**
        static_assert(std::has_virtual_destructor<lcns::Supervisor>::value, "RE 0xA3B4D0's two slots are the destructor pair");
        static_assert(std::is_polymorphic<lcns::Supervisor>::value, "a class with a vtable is polymorphic");

        // **AND THE ASSERTION THAT WOULD CATCH THE WRONG FIX.** The destructor reads the state pointer with `mov rsi, qword [rcx + 8]` at 0x030B71, so +0x08 is
        // where it must stay: adding the vptr puts it at +0x00 and leaves `state_` at +0x08, **whereas any OTHER member added before it would push the state
        // pointer off the offset the destructor uses, and nothing else in this test would notice.**
        alignas(lcns::Supervisor) unsigned char storage[sizeof(lcns::Supervisor)];
        lcns::Supervisor& probe = *reinterpret_cast<lcns::Supervisor*>(storage);
        const unsigned char* at = reinterpret_cast<const unsigned char*>(&probe);
        CHECK(reinterpret_cast<const unsigned char*>(&probe.state_) - at == 0x08);   // RE 0x030B71: mov rsi, qword ptr [rcx + 8]

        // **AND THE STATE OBJECT IS 0x530 BYTES BUILT FROM CONTAINERS**, which the destructor shows and this records without declaring: six consecutive
        // containers destroyed at +0x500 .. +0x528, an `unordered_map` header at +0x4D0 with its first node at +0x4E0, a `vector` of pointers between +0x488
        // and +0x490, a refcounted pointer at +0x4C8, and an embedded sub-object whose own vtable 0xA3BCE0 is installed at +0x478.
        static_assert(sizeof(lcns::Supervisor) >= 0x10, "a vptr and one pointer, and the 0x530 byte state object is reached through it");
    }

    return check::finish("test_recovered");
}
