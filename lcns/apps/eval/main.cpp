// nest_eval -- solve an lcns problem.json and report machine readable statistics.
//
// The benchmark strip is deliberately over-long (effectively unbounded), so `fill_ratio`
// (used / whole sheet) is NOT the cutting & packing density. `rho` is the density defined the way
// the literature does: sum(part areas) / (fixed_side * achieved_length), where the achieved length
// is the bounding box of the placed parts along the unbounded axis. `tools/run_benchmarks.py`
// picks the right side from the instance metadata and computes rho, but the raw quantities are
// printed here so the number can be recomputed independently.
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#include "lcns/boolean.hpp"
#include "lcns/engine.hpp"
#include "lcns/io.hpp"

namespace {

struct Args {
    std::string problem;
    std::string outDir;
    double timeLimit = 20.0;
    int iterations = 1000;
    unsigned seed = 0;
    int threads = 1;
    int beamWidth = 6;
    int angleSteps = 12;
    bool renest = true;
    bool compact = true;
    bool bottomLeft = true;
    bool csv = false;
    bool quiet = false;
};

void usage() {
    std::printf(
        "usage: nest_eval <problem.json> [options]\n"
        "  --time <s>        time limit per run (default 20)\n"
        "  --iterations <n>  maximum iterations (default 1000)\n"
        "  --seed <n>        RNG seed (default 0)\n"
        "  --threads <n>     worker threads (default 1)\n"
        "  --beam <n>        beam width (default 6)\n"
        "  --angles <n>      maximum angle steps (default 12)\n"
        "  --out <dir>       write solution.json / solution.svg there\n"
        "  --csv             print one CSV line instead of key=value lines\n"
        "  --quiet           suppress the extra report\n");
}

std::string readFile(const std::string& path, bool* ok) {
    std::FILE* f = std::fopen(path.c_str(), "rb");
    if (!f) {
        *ok = false;
        return {};
    }
    std::string data;
    char buf[1 << 16];
    std::size_t n;
    while ((n = std::fread(buf, 1, sizeof(buf), f)) > 0) data.append(buf, n);
    std::fclose(f);
    *ok = true;
    return data;
}

}  // namespace

int main(int argc, char** argv) {
    Args a;
    for (int i = 1; i < argc; ++i) {
        const std::string s = argv[i];
        auto next = [&](double def) -> double { return (i + 1 < argc) ? std::atof(argv[++i]) : def; };
        if (s == "--time") a.timeLimit = next(a.timeLimit);
        else if (s == "--iterations") a.iterations = static_cast<int>(next(a.iterations));
        else if (s == "--seed") a.seed = static_cast<unsigned>(next(a.seed));
        else if (s == "--threads") a.threads = static_cast<int>(next(a.threads));
        else if (s == "--beam") a.beamWidth = static_cast<int>(next(a.beamWidth));
        else if (s == "--angles") a.angleSteps = static_cast<int>(next(a.angleSteps));
        else if (s == "--out") { if (i + 1 < argc) a.outDir = argv[++i]; }
        else if (s == "--csv") a.csv = true;
        else if (s == "--no-renest") a.renest = false;
        else if (s == "--no-compact") a.compact = false;
        else if (s == "--no-bl") a.bottomLeft = false;
        else if (s == "--quiet") a.quiet = true;
        else if (s == "-h" || s == "--help") { usage(); return 0; }
        else if (!s.empty() && s[0] != '-') a.problem = s;
    }
    if (a.problem.empty()) {
        usage();
        return 2;
    }

    bool ok = false;
    const std::string text = readFile(a.problem, &ok);
    if (!ok) {
        std::fprintf(stderr, "cannot read %s\n", a.problem.c_str());
        return 1;
    }

    lcns::Order order;
    std::string err;
    if (!lcns::loadProblem(text, order, &err)) {
        std::fprintf(stderr, "cannot parse %s: %s\n", a.problem.c_str(), err.c_str());
        return 1;
    }

    lcns::EngineParams params;
    params.threads = a.threads;
    params.seed = a.seed;
    params.timeLimitSeconds = a.timeLimit;
    params.maxIterations = a.iterations;
    params.beam.width = a.beamWidth;
    params.beam.maxAngleSteps = a.angleSteps;
    params.cascadeBudgets = true;
    params.compactAtEnd = a.compact;
    params.finalizeBottomLeft = a.bottomLeft;
    params.renestInHoles = a.renest;

    lcns::Engine engine;
    const lcns::EngineResult res = engine.run(order, params, nullptr);

    // bounding box and area of everything that actually got placed
    lcns::geom::Box box;
    double placedArea = 0.0;
    int nested = 0;
    for (const lcns::Nesting& n : res.solution.nestings) {
        for (const lcns::NestedPart& np : n.parts) {
            if (np.partIndex < 0 || np.partIndex >= static_cast<int>(order.parts.size())) continue;
            const lcns::geom::MultiPolygon placed =
                lcns::placedShape(order.parts[static_cast<std::size_t>(np.partIndex)], np);
            const lcns::geom::Box b = lcns::geom::bounds(placed);
            if (!b.valid) continue;
            if (!box.valid) {
                box = b;
            } else {
                if (b.min.x < box.min.x) box.min.x = b.min.x;
                if (b.min.y < box.min.y) box.min.y = b.min.y;
                if (b.max.x > box.max.x) box.max.x = b.max.x;
                if (b.max.y > box.max.y) box.max.y = b.max.y;
            }
            placedArea += lcns::geom::multiArea(placed);
            ++nested;
        }
    }
    const double w = box.valid ? box.width() : 0.0;
    const double h = box.valid ? box.height() : 0.0;
    const double sheetArea = res.solution.sheetArea();
    const double fill = sheetArea > 0.0 ? placedArea / sheetArea : 0.0;

    if (a.csv) {
        std::printf("%s,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.3f,%d\n", a.problem.c_str(),
                    order.totalPartInstances(), nested, placedArea, w, h, fill,
                    res.solution.usedSurface(), res.seconds, res.cancelled ? 1 : 0);
    } else {
        std::printf("problem        = %s\n", a.problem.c_str());
        std::printf("part_instances = %d\n", order.totalPartInstances());
        std::printf("nested         = %d\n", nested);
        std::printf("placed_area    = %.6f\n", placedArea);
        std::printf("bbox_w         = %.6f\n", w);
        std::printf("bbox_h         = %.6f\n", h);
        std::printf("sheet_w        = %.6f\n", static_cast<double>(order.sheets[0].width));
        std::printf("sheet_h        = %.6f\n", static_cast<double>(order.sheets[0].height));
        std::printf("sheet_area     = %.6f\n", sheetArea);
        std::printf("fill_ratio     = %.6f\n", fill);
        std::printf("used_surface   = %.6f\n", res.solution.usedSurface());
        std::printf("seconds        = %.3f\n", res.seconds);
        std::printf("strategies     = %d\n", res.strategiesRun);
        std::printf("cancelled      = %d\n", res.cancelled ? 1 : 0);
        if (!a.quiet) {
            for (const lcns::Nesting& n : res.solution.nestings) {
                const lcns::geom::Box b = n.cachedBounds;
                std::printf("nesting        = sheet %d, %zu parts, bbox %.1f x %.1f\n", n.sheetIndex,
                            n.parts.size(), b.width(), b.height());
            }
        }
    }

    if (!a.outDir.empty()) {
        const std::string base = a.outDir + "/" + std::string("solution");
        {
            std::FILE* f = std::fopen((base + ".json").c_str(), "wb");
            if (f) {
                const std::string s = lcns::saveSolution(res.solution, order, true);
                std::fwrite(s.data(), 1, s.size(), f);
                std::fclose(f);
            }
        }
        lcns::writeSvg(base + ".svg", order, res.solution);
    }
    return 0;
}
