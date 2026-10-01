// tests/test_nester.cpp -- strategies, placement validity, compaction, finalisation,
//                          common cut detection and the engine entry point.
#include "check.hpp"
#include "lcns/engine.hpp"
#include "lcns/nester.hpp"

#include <set>

using namespace lcns;

namespace {

Order makeSimpleOrder(double partW = 20.0, double partH = 20.0, int count = 4) {
    Order o;
    Sheet s;
    s.id = 0;
    s.width = 100.0;
    s.height = 100.0;
    o.sheets.push_back(s);

    Part p;
    p.id = 0;
    p.rawShape = makeRectMulti(0, 0, partW, partH);
    p.shape = p.rawShape;
    p.multiplicity = count;
    o.parts.push_back(p);
    return o;
}

// independent overlap check, using the geometry rather than the engine's validator
bool anyOverlap(const Order& o, const Nesting& n) {
    for (std::size_t i = 0; i < n.parts.size(); ++i) {
        for (std::size_t j = i + 1; j < n.parts.size(); ++j) {
            const NestedPart& a = n.parts[i];
            const NestedPart& b = n.parts[j];
            const geom::MultiPolygon ma = placeShape(o.parts[static_cast<std::size_t>(a.partIndex)].shape, a);
            const geom::MultiPolygon mb = placeShape(o.parts[static_cast<std::size_t>(b.partIndex)].shape, b);
            geom::MultiPolygon ta = ma, tb = mb;
            for (auto& poly : ta) {
                for (auto& p : poly.external) {
                    p.x += geom::toFixed(a.x);
                    p.y += geom::toFixed(a.y);
                }
            }
            for (auto& poly : tb) {
                for (auto& p : poly.external) {
                    p.x += geom::toFixed(b.x);
                    p.y += geom::toFixed(b.y);
                }
            }
            if (!ta.empty() && !tb.empty() &&
                geom::ringsOverlap(ta.front().external, tb.front().external)) {
                return true;
            }
        }
    }
    return false;
}

}  // namespace

int main() {
    // --- Random mirrors the embedded std::mt19937 (RE seed constant 0x6C078965) ---
    {
        Random r(5489u);
        const std::uint32_t a = r.next();
        Random r2(5489u);
        CHECK(a == r2.next());  // deterministic
        Random r3(1u);
        CHECK(r3.next() != a);
        const int v = r.uniformInt(3, 5);
        CHECK(v >= 3 && v <= 5);
    }

    // --- TimeCanceller: elapsed / limit > 1.0 (RE 0x30030) ---
    {
        TimeCanceller c(0.0);   // 0 == no limit
        CHECK(!c.probeCancel());
        TimeCanceller c2(1000.0);
        CHECK(!c2.probeCancel());
        CHECK(c2.limit() == 1000.0);
        CHECK(c2.elapsed() >= 0.0);
        NeverCanceller n;
        CHECK(!n.probeCancel());  // RE RCompactCanceller never cancels
        Canceller base;
        CHECK(!base.probeCancel());  // RE base returns false (0x7D7D20)
        base.cancel();
        CHECK(base.probeCancel());
    }

    // --- pricing: Box = bbox area, LinearCombination = weighted mean (RE 0x7CA370) ---
    {
        PriceCandidate c;
        c.box = geom::Box{geom::FPoint{0, 0}, geom::FPoint{geom::toFixed(10), geom::toFixed(4)}, true};
        c.hullSurface = 25.0;
        c.alphaSurface = 7.0;
        BoxSurfacePrice box;
        HullSurfacePrice hull;
        AlphaSurfacePrice alpha;
        CHECK_NEAR(box.price(c), 40.0, 1e-9);
        CHECK_NEAR(hull.price(c), 25.0, 1e-9);
        CHECK_NEAR(alpha.price(c), 7.0, 1e-9);
        LinearCombinationPrice lc;
        lc.add(std::make_shared<BoxSurfacePrice>(), 1.0);
        lc.add(std::make_shared<HullSurfacePrice>(), 3.0);
        CHECK_NEAR(lc.price(c), (1.0 * 40.0 + 3.0 * 25.0) / 4.0, 1e-9);
        CHECK(std::string(box.name()) == "BoxSurface");
        CHECK(std::string(lc.name()) == "LinearCombination");
    }

    // --- StrategyDescriber::cascade, the RE 0x2CCF0 sequence ---
    {
        StrategyDescriber d;
        d.n = 1;
        auto c1 = d.cascade();
        CHECK(c1.front() == 1);
        d.n = 2;
        auto c2 = d.cascade();
        CHECK(c2.front() == 2);
        d.n = 8;
        auto c8 = d.cascade();
        CHECK(c8.size() >= 2);
        CHECK(c8[0] == 8);
        CHECK(c8[1] == 2);
    }

    // --- StrategyAdder mapping (RE 0x2C4D0) ---
    {
        CHECK(std::string(makeStrategy(1)->name()) == "NestingNester");
        CHECK(std::string(makeStrategy(2)->name()) == "RectangleNester");
        CHECK(std::string(makeStrategy(3)->name()) == "RowNester");
        CHECK(std::string(makeStrategy(4)->name()) == "RowNester(pipe)");
        CHECK(std::string(makeStrategy(5)->name()) == "CompactNester");
        CHECK(std::string(makeStrategy(6)->name()) == "FilterNester");
        CHECK(std::string(makeStrategy(7)->name()) == "NoFillNester");
        CHECK(std::string(makeStrategy(12)->name()) == "FlipNester");
        CHECK(makeDefaultStrategies().size() >= 4);
        CHECK(std::string(pack::BestNester().name()) == "Pack::BestNester");
        CHECK(std::string(pack::KnapsackNester().name()) == "Pack::KnapsackNester");
        CHECK(std::string(pack::RecursiveNester().name()) == "Pack::RecursiveNester");
    }

    // --- end to end: 4 rectangles of 20x20 on a 100x100 sheet ---
    {
        const Order order = makeSimpleOrder();
        EngineParams params;
        params.threads = 1;
        params.timeLimitSeconds = 5.0;
        params.maxIterations = 40;
        params.beam.width = 4;
        params.beam.maxAngleSteps = 4;

        Engine engine;
        const EngineResult res = engine.run(order, params);
        CHECK(res.solution.valid);
        CHECK(!res.solution.nestings.empty());
        CHECK(res.solution.totalNestedParts() >= 4);
        CHECK(!res.cancelled);
        CHECK(res.seconds >= 0.0);
        CHECK(!res.log.empty());

        for (const auto& n : res.solution.nestings) {
            CHECK(!anyOverlap(order, n));
            CHECK(n.sheetArea > 0.0);
            CHECK(n.usedSurface > 0.0);
        }
        const double fr = res.solution.fillRatio();
        CHECK_MSG(fr > 0.10 && fr <= 1.0, "fill ratio in a sane range");
    }

    // --- placement validity is enforced: a part outside the sheet must be rejected ---
    {
        const Order order = makeSimpleOrder();
        NoFitMap nfp;
        Random rng(1);
        SolveContext ctx;
        ctx.order = &order;
        ctx.nfp = &nfp;
        ctx.rng = &rng;
        Nesting empty;
        empty.sheetIndex = 0;
        empty.sheetArea = 10000.0;

        NestedPart good;
        good.partIndex = 0;
        good.x = 0.0;
        good.y = 0.0;
        CHECK(checkPlacement(order, empty, 0, order.parts[0], good).ok());

        NestedPart outside;
        outside.partIndex = 0;
        outside.x = 95.0;   // 95 + 20 > 100
        outside.y = 0.0;
        CHECK(!checkPlacement(order, empty, 0, order.parts[0], outside).ok());

        NestedPart overlapping = good;
        overlapping.x = 10.0;  // overlaps the part at (0,0)
        Nesting withOne = empty;
        withOne.parts.push_back(good);
        CHECK(checkPlacement(order, withOne, 0, order.parts[0], overlapping).overlapsPlaced);
    }

    // --- compaction keeps the solution valid and can only shrink the bounding box ---
    {
        Order order = makeSimpleOrder();
        EngineParams params;
        params.maxIterations = 20;
        params.beam.maxAngleSteps = 4;
        params.timeLimitSeconds = 5.0;
        Engine engine;
        EngineResult res = engine.run(order, params);

        NoFitMap nfp;
        Random rng(7);
        SolveContext ctx;
        ctx.order = &order;
        ctx.nfp = &nfp;
        ctx.rng = &rng;
        for (auto& n : res.solution.nestings) {
            const geom::Box before = n.cachedBounds;
            const CompactionStats st = compactNesting(order, n, ctx);
            CHECK(st.gain >= -1e-6);
            CHECK(n.cachedBounds.area() <= before.area() + 1e-3);
            CHECK(!anyOverlap(order, n));
            packedBottomLeft(order, n);
            CHECK(!anyOverlap(order, n));
            const int added = renestInHoles(order, n, ctx);
            CHECK(added >= 0);
        }
    }

    // --- common cut detection on a hand built solution (two adjacent rectangles) ---
    {
        Order order;
        Part p;
        p.id = 0;
        p.rawShape = makeRectMulti(0, 0, 20, 20);
        p.shape = p.rawShape;
        order.parts.push_back(p);

        Solution sol;
        Nesting n;
        n.sheetIndex = 0;
        n.sheetArea = 10000.0;
        NestedPart a;
        a.partIndex = 0;
        a.x = 0.0;
        a.y = 0.0;
        NestedPart b;
        b.partIndex = 0;
        b.x = 20.0;
        b.y = 0.0;
        n.parts.push_back(a);
        n.parts.push_back(b);
        sol.nestings.push_back(n);

        const CommonCutEvaluation ev = detectCommonCuts(order, sol);
        CHECK(!ev.commonCutSegments.empty());
        CHECK(ev.number >= 1.0);
        CHECK_NEAR(ev.commonCutLength, 20.0, 1e-6);
        CHECK(ev.commonCutSegments.front().valid);
        CHECK(ev.commonCutSegments.front().leftIndex == 0);
        CHECK(ev.commonCutSegments.front().rightIndex == 1);

        // separated parts must not report a common cut
        Solution far;
        Nesting n2 = n;
        n2.parts[1].x = 200.0;
        far.nestings.push_back(n2);
        const CommonCutEvaluation ev2 = detectCommonCuts(order, far);
        CHECK(ev2.commonCutSegments.empty());
    }

    // --- observers are wired like the recovered 6 slot interface ---
    {
        const Order order = makeSimpleOrder();
        int started = 0, stopped = 0, inter = 0, found = 0;
        Observers obs;
        obs.start = [&] { ++started; };
        obs.stop = [&] { ++stopped; };
        obs.newIntermediateSolutionFound = [&](const Solution&) { ++inter; };
        obs.newNestingFound = [&](const Solution&) { ++found; };

        EngineParams params;
        params.maxIterations = 8;
        params.beam.maxAngleSteps = 3;
        params.timeLimitSeconds = 5.0;
        Engine engine;
        engine.run(order, params, &obs);
        CHECK(started == 1);
        CHECK(stopped == 1);
        CHECK(inter >= 1);
        CHECK(found == 1);
    }

    // --- SVG / HTML reporting (DrawSVG family, cns_solution.css, __marks__ layer) ---
    {
        const Order order = makeSimpleOrder();
        EngineParams params;
        params.maxIterations = 8;
        params.beam.maxAngleSteps = 3;
        Engine engine;
        const EngineResult res = engine.run(order, params);
        const std::string svg = toSvg(order, res.solution);
        CHECK(svg.find("<svg") != std::string::npos);
        CHECK(svg.find("__marks__") != std::string::npos);
        // --- the recovered format of ..\structure\svg_io.cpp (writer 0x7CCDF0) ---
        CHECK(svg.find("px\" height=\"") != std::string::npos);              // RE 0x7CCFE8
        CHECK(svg.find("version=\"1.1\"") != std::string::npos);             // RE header
        CHECK(svg.find("xmlns:xlink=\"http://www.w3.org/1999/xlink\"") != std::string::npos);
        CHECK(svg.find("<pattern id=\"diagonalHatch") != std::string::npos);  // RE 0x7CCDF0 defs
        CHECK(svg.find("patternUnits=\"userSpaceOnUse\"") != std::string::npos);
        CHECK(svg.find("<g transform=\"scale(1,-1)\">") != std::string::npos);
        CHECK(svg.find("<g transform=\"translate(") != std::string::npos);
        CHECK(svg.find("fill-rule=\"evenodd\"") != std::string::npos);       // RE '<g fill-rule="evenodd">'
        CHECK(svg.find("stroke-width:0.1%") != std::string::npos);           // RE 0x5DDDD0
        CHECK(svg.find("fill:white") != std::string::npos);                  // RE 0x516380
        const std::string html = toHtmlReport(order, res.solution);
        CHECK(html.find("cns_solution.css") != std::string::npos);
    }

    // --- RE 0x6AABC0 @0x6AC10C: RowNester builds a Row::Squeezer from the placed rows ---
    {
        const Order order = makeSimpleOrder();
        NoFitMap nfp;
        Random rng(7);
        SolveContext ctx;
        ctx.order = &order;
        ctx.nfp = &nfp;
        ctx.rng = &rng;

        RowNester rn;
        CHECK(rn.core() == nullptr);   // RE: this+0x18, built on the first run()
        // RE: core+0x18 -> cfg[+0x10] (the cost threshold) and core+0x20 -> cfg[+0x18].
        // Their defaults are the recovered rodata constants (0x9B1A48 = 4.0, 0x9B1A50 = 20.0).
        CHECK_NEAR(rn.cfg18(), kRowCoreAt0x18, 1e-12);
        CHECK_NEAR(rn.cfg20(), kRowCoreAt0x20, 1e-12);
        rn.setRowConfig(12.5, 0.75);
        CHECK_NEAR(rn.cfg18(), 12.5, 1e-12);
        CHECK_NEAR(rn.cfg20(), 0.75, 1e-12);

        const Solution s = rn.run(ctx);
        CHECK(rn.core() != nullptr);                             // RE: [rbx+0x18] = core @0x8F257
        CHECK(rn.core()->hasSqueezer());                         // RE: core+0xC0 @0x6AC118
        CHECK(rn.core()->squeezer().enabled());                  // RE: inner[+8] = 1
        CHECK_NEAR(rn.core()->threshold(), 12.5, 1e-12);         // RE: core+0x18 = cfg[+0x10]
        CHECK_NEAR(rn.core()->coeff(), 0.75, 1e-12);             // RE: core+0x20 = cfg[+0x18]
        CHECK_NEAR(rn.core()->squeezer().threshold(), 12.5, 1e-12);  // xmm9 -> inner[+0x10]
        CHECK_NEAR(rn.core()->squeezer().coeff(), 0.75, 1e-12);      // xmm8 -> inner[+0x00]
        CHECK(rn.core()->mode() == 0);                           // RE: core+0x40
        CHECK(rn.core()->rowCount() == order.parts.size());       // RE: one element per part
        // The extent argument is 2 * (v3 - v1) of the LAST element (0x13C46F assigns, not max),
        // or 0 when that element is flagged valid -- both are legal, so only finiteness here.
        CHECK(std::isfinite(rn.core()->squeezer().twiceMaxExtent()));
        // The core is built once (the binary builds it in the constructor).
        const RowNestCore* first = rn.core();
        rn.run(ctx);
        CHECK(rn.core() == first);
        CHECK(s.valid);
    }

    // --- RE 0x6AABC0's configuration precedence for the row core ---
    {
        Order o = makeSimpleOrder();

        // 1) no gates: the rodata defaults 0x9B1A48 = 4.0 / 0x9B1A50 = 20.0 stand
        {
            const RowNestCore c(o, false);
            CHECK_NEAR(c.threshold(), kRowCoreAt0x18, 1e-12);
            CHECK_NEAR(c.coeff(), kRowCoreAt0x20, 1e-12);
        }
        // 2) the common-cut block is present (Pb+0x1A0 set) -> Pb+0x1B0 / +0x1A8 win
        o.commonCutBlockSet = true;
        o.commonCutAt1B0 = 3.5;
        o.commonCutAt1A8 = 7.5;
        {
            const RowNestCore c(o, false);
            CHECK_NEAR(c.threshold(), 3.5, 1e-12);   // RE: core+0x18 = [problem+0x1B0]
            CHECK_NEAR(c.coeff(), 7.5, 1e-12);       // RE: core+0x20 = [problem+0x1A8]
        }
        // 3) pipe mode ON takes the OTHER source (not the defaults):
        //    RE 0x6AC20A reads Pb+0x188 -> core+0x20 (coefficient) and Pb+0x190 -> core+0x18
        //    (threshold) through the base 0x4FC3A0 = `mov rax,[rcx] ; add rax,0x170`.
        o.cfgAt188 = 11.5;
        o.cfgAt190 = 2.25;
        {
            const RowNestCore c(o, /*pipe=*/true);
            CHECK_NEAR(c.threshold(), 2.25, 1e-12);   // RE: 0x6AC22D, Pb+0x190
            CHECK_NEAR(c.coeff(), 11.5, 1e-12);       // RE: 0x6AC223, Pb+0x188
        }
        //    ... and the same when the problem itself carries the pipe-mode flag (Pb+0x170)
        o.pipeMode = true;
        {
            const RowNestCore c(o, /*pipe=*/false);
            CHECK_NEAR(c.threshold(), 2.25, 1e-12);
            CHECK_NEAR(c.coeff(), 11.5, 1e-12);
        }
        //    the pipe source wins over the common-cut block (0x6AAC3A precedes 0x6AAC42)
        {
            const RowNestCore c(o, /*pipe=*/false);
            CHECK_NEAR(c.threshold(), 2.25, 1e-12);
            CHECK_NEAR(c.coeff(), 11.5, 1e-12);
        }
        //    with pipe mode off, the common-cut block is the source again
        o.pipeMode = false;
        {
            const RowNestCore c(o, /*pipe=*/false);
            CHECK_NEAR(c.threshold(), 3.5, 1e-12);
            CHECK_NEAR(c.coeff(), 7.5, 1e-12);
        }
    }

    // --- a strategy must never place more instances of a kind than the order asks for ---------
    // Regression: TilingNester materialised a tiling pattern and only capped the GLOBAL instance
    // count, so a kind whose multiplicity was 4 could appear 8 times in the final nesting
    // (observed as nested=28 for an order of 24 instances). The per-kind cap fixes it.
    {
        Order o;
        Sheet s;
        s.id = 0;
        s.width = 400.0;
        s.height = 200.0;
        s.quantity = 1;
        o.sheets.push_back(s);
        o.timeLimitSeconds = 0.4;
        o.maxIterations = 30;
        o.objective = Objective::MinimizeArea;

        struct Kind { double w, h; int mult; };
        const Kind kinds[3] = {{80.0, 60.0, 4}, {50.0, 40.0, 2}, {30.0, 30.0, 1}};
        for (int k = 0; k < 3; ++k) {
            Part p;
            p.id = k;
            p.rawShape = makeRectMulti(0, 0, kinds[k].w, kinds[k].h);
            p.shape = p.rawShape;
            p.multiplicity = kinds[k].mult;
            o.parts.push_back(p);
        }

        EngineParams params;
        params.timeLimitSeconds = 0.4;
        params.maxIterations = 30;
        Engine engine;
        const EngineResult res = engine.run(o, params, nullptr);

        std::vector<int> placedPerKind(o.parts.size(), 0);
        for (const auto& n : res.solution.nestings) {
            for (const auto& np : n.parts) {
                if (np.partIndex >= 0 && np.partIndex < static_cast<int>(placedPerKind.size())) {
                    placedPerKind[static_cast<std::size_t>(np.partIndex)]++;
                }
            }
        }
        for (std::size_t i = 0; i < o.parts.size(); ++i) {
            // `multiplicity` means "at least one", matching Order::totalPartInstances()
            CHECK(placedPerKind[i] <= std::max(1, o.parts[i].multiplicity));
        }
        CHECK(res.solution.totalNestedParts() <= o.totalPartInstances());
    }

    return check::finish("test_nester");
}
