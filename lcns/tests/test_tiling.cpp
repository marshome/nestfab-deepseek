// tests/test_tiling.cpp -- repeated pattern tiling and the evaluator family.
#include "check.hpp"
#include "lcns/engine.hpp"
#include "lcns/tiling.hpp"

#include <memory>

using namespace lcns;
using namespace lcns::tiling;

int main() {
    // --- BiModulePattern: a checkerboard of two modules ---
    {
        BiModulePattern pat(20.0, 10.0);
        pat.setModules(0, 1);
        const auto cells = pat.layout(100.0, 50.0, 0);
        CHECK(!cells.empty());
        // 100/20 = 5 columns, 50/10 = 5 rows -> 25 cells
        CHECK(cells.size() == 25);
        // the two modules must alternate
        bool sawA = false, sawB = false;
        for (const auto& c : cells) {
            if (c.partIndex == 0) sawA = true;
            if (c.partIndex == 1) sawB = true;
        }
        CHECK(sawA && sawB);
        // the checkerboard property holds for neighbours
        const PatternCell& c0 = cells.front();
        const PatternCell& c1 = cells[1];
        CHECK(c0.partIndex != c1.partIndex);
        // cells are inside the sheet
        for (const auto& c : cells) {
            CHECK(c.x >= 0.0);
            CHECK(c.y >= 0.0);
            CHECK(c.x + 20.0 <= 100.0 + 1e-9);
            CHECK(c.y + 10.0 <= 50.0 + 1e-9);
        }
    }

    // --- spacing is honoured ---
    {
        BiModulePattern pat(20.0, 10.0);
        pat.setModules(0, 0);
        pat.setSpacing(5.0);
        const auto cells = pat.layout(100.0, 50.0, 0);
        // step 25 x 15 : columns 0,25,50,75 (4), rows 0,15,30 (3) -> 12
        CHECK(cells.size() == 12);
        CHECK_NEAR(cells[1].x - cells[0].x, 25.0, 1e-9);
    }

    // --- budget caps the number of cells ---
    {
        BiModulePattern pat(10.0, 10.0);
        pat.setModules(0, 0);
        const auto cells = pat.layout(100.0, 100.0, 7);
        CHECK(cells.size() == 7);
    }

    // --- MultiOrientedPartPattern cycles through the orientations ---
    {
        MultiOrientedPartPattern pat(3);
        pat.setCellSize(10.0, 10.0);
        pat.addOrientation(0.0, false);
        pat.addOrientation(1.5707963267948966, true);
        CHECK(pat.orientationCount() == 2);
        const auto cells = pat.layout(50.0, 50.0, 0);
        CHECK(cells.size() == 25);
        CHECK(cells[0].partIndex == 3);
        CHECK_NEAR(cells[0].angle, 0.0, 1e-12);
        CHECK(!cells[0].flipped);
        CHECK_NEAR(cells[1].angle, 1.5707963267948966, 1e-12);
        CHECK(cells[1].flipped);
        // cycles back to the first orientation
        CHECK_NEAR(cells[2].angle, 0.0, 1e-12);
    }

    // --- evaluators ---
    {
        BiModulePattern pat(10.0, 10.0);
        pat.setModules(0, 0);
        const auto cells = pat.layout(100.0, 100.0, 0);   // 100 cells of 100 -> 10000
        const double sheetArea = 10000.0;

        DensityEvaluator density;
        CHECK_NEAR(density.evaluate(cells, sheetArea), 1.0, 1e-9);
        CHECK(std::string(density.name()) == "DensityEvaluator");

        QuantityEvaluator qty;
        CHECK_NEAR(qty.evaluate(cells, sheetArea), 100.0, 1e-9);

        UnlimitedDensityEvaluator un;
        CHECK_NEAR(un.evaluate(cells, sheetArea), 1.0, 1e-9);

        UnlimitedXDensityEvaluator unx;
        // linear density: used area per unit of x extent (unbounded, unlike a true density)
        CHECK_NEAR(unx.evaluate(cells, sheetArea), 100.0, 1e-9);

        ReusableEvaluator reuse;
        CHECK(reuse.evaluate(cells, sheetArea) > 0.0);

        ObliqueEvaluator oblique;
        CHECK_NEAR(oblique.evaluate(cells, sheetArea), 0.0, 1e-12);  // all axis aligned
        auto tilted = cells;
        for (auto& c : tilted) c.angle = 0.7;
        CHECK(oblique.evaluate(tilted, sheetArea) > 0.9);

        // RE 0x4E8410: the constructor takes an int and TWO DOUBLES, all three written into the object it allocates
        MultitorchEvaluator torch(4, 1.0, 1.0);
        CHECK(torch.evaluate(cells, sheetArea) > 0.0);
        CHECK_NEAR(torch.evaluate({}, sheetArea), 0.0, 1e-12);
    }

    // --- BoxMultiTiler picks the best candidate ---
    {
        BiModulePattern dense(10.0, 10.0);
        dense.setModules(0, 0);
        BiModulePattern sparse(20.0, 20.0);
        sparse.setModules(0, 0);
        const auto c1 = dense.layout(100.0, 100.0, 0);
        const auto c2 = sparse.layout(100.0, 100.0, 0);

        BoxMultiTiler tiler;
        tiler.add(std::make_shared<DensityEvaluator>());
        double score = 0.0;
        const auto best = tiler.best({c1, c2}, 10000.0, &score);
        CHECK(best.size() == c1.size());
        CHECK_NEAR(score, 1.0, 1e-9);
    }

    // --- SqueezeMultiTiler clamps cells into the sheet ---
    {
        auto cells = MultiOrientedPartPattern(0).layout(100.0, 100.0, 0);
        (void)cells;
        BiModulePattern pat(30.0, 30.0);
        pat.setModules(0, 0);
        auto c = pat.layout(100.0, 100.0, 0);
        SqueezeMultiTiler squeeze;
        const auto squeezed = squeeze.squeeze(c, 100.0, 100.0);
        CHECK(squeezed.size() == c.size());
        for (const auto& cell : squeezed) {
            CHECK(cell.x >= 0.0);
            CHECK(cell.y >= 0.0);
            CHECK(cell.x + 30.0 <= 100.0 + 1e-9);
            CHECK(cell.y + 30.0 <= 100.0 + 1e-9);
        }
    }

    // --- PackerCache remembers keys ---
    {
        PackerCache cache;
        CHECK(!cache.contains("a"));
        cache.store("a");
        cache.store("b");
        cache.store("a");
        CHECK(cache.contains("a"));
        CHECK(cache.size() == 2);
        cache.clear();
        CHECK(cache.size() == 0);
        CHECK(!cache.contains("a"));
    }

    // --- TilingNester is reachable through the engine and still produces valid nestings ---
    {
        Order order;
        Sheet sheet;
        sheet.width = 200.0;
        sheet.height = 100.0;
        order.sheets.push_back(sheet);

        Part p;
        p.id = 0;
        p.rawShape = makeRectMulti(0, 0, 20, 20);
        p.shape = p.rawShape;
        p.multiplicity = 20;
        order.parts.push_back(p);
        Part q;
        q.id = 1;
        q.rawShape = makeRectMulti(0, 0, 10, 10);
        q.shape = q.rawShape;
        q.multiplicity = 20;
        order.parts.push_back(q);

        NoFitMap nfp;
        Random rng(3);
        SolveContext ctx;
        ctx.order = &order;
        ctx.nfp = &nfp;
        ctx.rng = &rng;
        ctx.beam.maxAngleSteps = 4;
        ctx.log = nullptr;

        TilingNester nester;
        const Solution s = nester.run(ctx);
        CHECK(s.valid);
        CHECK(!s.nestings.empty());
        CHECK(s.totalNestedParts() > 0);
        CHECK(s.totalNestedParts() <= order.totalPartInstances());
        CHECK_NEAR(s.usedSurface(), [&] {
            double a = 0.0;
            for (const auto& n : s.nestings)
                for (const auto& np : n.parts) a += order.parts[static_cast<std::size_t>(np.partIndex)].area();
            return a;
        }(), 1e-6);
        CHECK(std::string(nester.name()) == "TilingNester");
    }

    return check::finish("test_tiling");
}
