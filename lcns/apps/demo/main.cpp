// apps/demo/main.cpp -- standalone nesting demo built on the reconstructed algorithm core.
//
// Builds a small problem (one plate, a few shapes including a part with a hole), runs the
// engine, prints the statistics and writes an SVG + an HTML report.
#include "lcns/boolean.hpp"
#include "lcns/engine.hpp"
#include "lcns/io.hpp"
#include "lcns/nester.hpp"

#include <cstdio>
#include <fstream>
#include <string>

using namespace lcns;

namespace {

void writeTextFile(const std::string& path, const std::string& text) {
    std::ofstream f(path, std::ios::binary);
    if (f) f << text;
}

Part makeRectPart(int id, double w, double h, int qty) {
    Part p;
    p.id = id;
    p.rawShape = makeRectMulti(0, 0, w, h);
    p.shape = p.rawShape;
    p.multiplicity = qty;
    return p;
}

Part makeCirclePart(int id, double r, int qty) {
    Part p;
    p.id = id;
    const geom::Polygon c = circlePolygon(0, 0, r, 48);
    p.rawShape = geom::MultiPolygon{c};
    p.shape = p.rawShape;
    p.multiplicity = qty;
    return p;
}

Part makeFramePart(int id, double w, double h, double wall, int qty) {
    Part p;
    p.id = id;
    geom::Polygon poly = rectPolygon(0, 0, w, h);
    poly.inners.push_back(geom::reverse(rectPolygon(wall, wall, w - 2 * wall, h - 2 * wall).external));
    p.rawShape = geom::MultiPolygon{poly};
    p.shape = p.rawShape;
    p.multiplicity = qty;
    return p;
}

void printSolution(const Order& order, const EngineResult& res) {
    std::printf("\n--- result -------------------------------------------------\n");
    std::printf("strategies run : %d\n", res.strategiesRun);
    std::printf("seconds        : %.3f%s\n", res.seconds, res.cancelled ? "  (cancelled)" : "");
    std::printf("nestings       : %zu\n", res.solution.nestings.size());
    std::printf("nested parts   : %d of %d requested\n", res.solution.totalNestedParts(),
                order.totalPartInstances());
    std::printf("used surface   : %.1f\n", res.solution.usedSurface());
    std::printf("sheet surface  : %.1f\n", res.solution.sheetArea());
    std::printf("fill ratio     : %.2f %%\n", res.solution.fillRatio() * 100.0);
    std::printf("score          : %.1f\n", res.score);
    for (std::size_t i = 0; i < res.solution.nestings.size(); ++i) {
        const Nesting& n = res.solution.nestings[i];
        const geom::Box b = n.cachedBounds;
        std::printf("  nesting %zu: sheet %d, %zu parts, bbox %.1f x %.1f\n", i, n.sheetIndex,
                    n.parts.size(), b.width(), b.height());
        if (!n.multitorchInfos.empty()) {
            std::printf("    multitorch infos: %zu (nb_torches=%d)\n", n.multitorchInfos.size(),
                        n.multitorchInfos.front().infoNbTorches);
        }
    }
    if (res.commonCuts.number > 0.0) {
        std::printf("common cuts    : %.0f segments, total length %.1f, regarding %.1f\n",
                    res.commonCuts.number, res.commonCuts.commonCutLength,
                    res.commonCuts.regardingLength);
    }
    if (!res.log.empty()) {
        std::printf("first log lines:\n");
        for (std::size_t i = 0; i < res.log.size() && i < 5; ++i) {
            std::printf("  %s\n", res.log[i].c_str());
        }
    }
}

}  // namespace

int main(int argc, char** argv) {
    const std::string outDir = (argc > 1) ? argv[1] : ".";

    Order order;
    order.objective = Objective::MinimizeArea;
    order.origin = NestingOrigin::BottomLeft;
    order.interpartGap = 2.0;
    order.timeLimitSeconds = 5.0;
    order.maxIterations = 60;
    order.markMode = true;
    order.markSize = 1.0;

    Sheet sheet;
    sheet.id = 0;
    sheet.width = 1000.0;
    sheet.height = 500.0;
    sheet.price = 42.0;
    sheet.quantity = 1;
    order.sheets.push_back(sheet);

    // the same shapes the recovered API can create
    order.parts.push_back(makeRectPart(0, 200.0, 120.0, 3));   // AddRectanglePart
    order.parts.push_back(makeCirclePart(1, 60.0, 2));         // AddCircularPart
    order.parts.push_back(makeFramePart(2, 160.0, 160.0, 30.0, 2));  // hole -> renest target
    order.parts.push_back(makeRectPart(3, 90.0, 40.0, 4));     // AddPolygonPart

    std::printf("problem: %zu sheet(s), %zu part kind(s), %d instances\n", order.sheets.size(),
                order.parts.size(), order.totalPartInstances());
    std::printf("total part area %.1f, sheet area %.1f (lower bound fill %.1f %%)\n",
                order.totalPartArea(), order.totalSheetArea(),
                100.0 * order.totalPartArea() / order.totalSheetArea());

    EngineParams params;
    params.threads = 1;
    params.seed = 12345;
    params.timeLimitSeconds = 5.0;
    params.maxIterations = 60;
    params.beam.width = 6;
    params.beam.maxAngleSteps = 12;
    params.cascadeBudgets = true;
    params.compactAtEnd = true;
    params.finalizeBottomLeft = true;
    params.renestInHoles = true;

    Observers obs;
    obs.start = [] { std::printf("engine: start\n"); };
    obs.stop = [] { std::printf("engine: stop\n"); };
    // The recovered observer interface fires v4 on every intermediate solution; only report
    // actual improvements here to keep the console readable.
    double bestFill = -1.0;
    obs.newIntermediateSolutionFound = [&bestFill](const Solution& s) {
        const double f = s.fillRatio();
        if (f > bestFill + 1e-9) {
            bestFill = f;
            std::printf("  observer v4 NewIntermediateSolutionFound: improved to %.2f %%\n",
                        f * 100.0);
        }
    };
    obs.newNestingFound = [](const Solution& s) {
        std::printf("  observer v5 NewNestingFound: %d parts\n", s.totalNestedParts());
    };

    Engine engine;
    const EngineResult res = engine.run(order, params, &obs);
    printSolution(order, res);

    const std::string svgPath = outDir + "/solution.svg";
    const std::string htmlPath = outDir + "/solution.html";
    if (writeSvg(svgPath, order, res.solution)) {
        std::printf("wrote %s\n", svgPath.c_str());
    }
    {
        std::FILE* f = std::fopen(htmlPath.c_str(), "wb");
        if (f) {
            const std::string html = toHtmlReport(order, res.solution);
            std::fwrite(html.data(), 1, html.size(), f);
            std::fclose(f);
            std::printf("wrote %s\n", htmlPath.c_str());
        }
    }

    // --- incidentals: DXF, JSON and the offcut report -------------------------
    const std::string dxfPath = outDir + "/solution.dxf";
    if (writeDxf(dxfPath, order, res.solution)) {
        std::printf("wrote %s (R12, layers SHEET/PART/HOLES)\n", dxfPath.c_str());
    }
    const std::string problemPath = outDir + "/problem.json";
    const std::string solutionPath = outDir + "/solution.json";
    writeTextFile(problemPath, saveProblem(order, true));
    writeTextFile(solutionPath, saveSolution(res.solution, order, true));
    std::printf("wrote %s and %s\n", problemPath.c_str(), solutionPath.c_str());

    // reload what we just wrote to prove the round trip
    {
        Order reloaded;
        std::string err;
        if (loadProblem(saveProblem(order, false), reloaded, &err)) {
            std::printf("problem round trip: %zu part kind(s), %zu sheet(s)\n",
                        reloaded.parts.size(), reloaded.sheets.size());
        } else {
            std::printf("problem round trip FAILED: %s\n", err.c_str());
        }
    }

    const geom::MultiPolygon off = offcuts(order, res.solution);
    std::printf("offcuts        : %zu remnant ring set(s), %.1f of recoverable surface\n", off.size(),
                geom::multiArea(off));
    for (std::size_t i = 0; i < off.size() && i < 6; ++i) {
        const geom::Box b = geom::bounds(off[i].external);
        // net area: the outer ring minus every inner ring (a frame's bore leaves a usable island)
        double net = geom::area(off[i].external);
        for (const auto& h : off[i].inners) net -= geom::area(h);
        std::printf("  offcut %zu: %.1f x %.1f envelope, net area %.1f, %zu hole(s)\n", i,
                    b.width(), b.height(), net, off[i].inners.size());
    }

    return res.solution.totalNestedParts() > 0 ? 0 : 1;
}
