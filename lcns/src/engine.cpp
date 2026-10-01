// lcns/engine.cpp
#include "lcns/engine.hpp"
#include "lcns/recovery.hpp"

#include <algorithm>
#include <fstream>
#include <sstream>
#include <thread>

LCNS_STRUCTURAL(module.engine);
namespace lcns {
namespace {

double solutionScore(const Solution& s) {
    double v = 0.0;
    for (const auto& n : s.nestings) v += n.usedSurface - 1e-3 * n.cachedBounds.area();
    return v;
}

// placedMultiPublic() used to live here with its own copy of the rotation+translation; it is now
// model::placedPolygon(), the single definition, so the duplicate is gone.

}  // namespace

// ---------------------------------------------------------------------------
// RE 0x2CCF0: cascade the budget
// ---------------------------------------------------------------------------
LCNS_NOT_REVERSED(engine.advanced_strategist);
std::vector<int> StrategyDescriber::cascade() const {
    std::vector<int> out;
    int cur = n > 0 ? n : 1;
    out.push_back(cur);
    if (cur > 2) { cur = 2; out.push_back(cur); }
    if (cur > 4) { cur = (cur + 1) / 2; out.push_back(cur); cur = cur - 1; out.push_back(cur); }
    else if (cur > 1) { out.push_back(cur - 1); }
    return out;
}

// ---------------------------------------------------------------------------
// RE Multi::StrategyAdder::Add 0x2C4D0
// ---------------------------------------------------------------------------
std::shared_ptr<Nester> makeStrategy(int mode) {
    switch (mode) {
        case 2:  return std::make_shared<RectangleNester>();
        case 3:  return std::make_shared<RowNester>(false);
        case 4:  return std::make_shared<RowNester>(true);
        case 5:  return std::make_shared<CompactNester>();
        case 6:  return std::make_shared<FilterNester>();
        case 7:  return std::make_shared<NoFillNester>();
        case 8:  return std::make_shared<LimitedNester>(64, 8);
        case 9:  return std::make_shared<TilingNester>();
        case 10: return std::make_shared<MultiTorchNester>();
        case 11: return std::make_shared<DatabaseNester>();
        case 12: return std::make_shared<FlipNester>();
        case 1:
        default: return std::make_shared<NestingNester>();
    }
}

LCNS_NOT_REVERSED(engine.beam_tree);
std::vector<std::shared_ptr<Nester>> makeDefaultStrategies() {
    return {makeStrategy(1), makeStrategy(12), makeStrategy(9),
            makeStrategy(2), makeStrategy(3), makeStrategy(6)};
}

// ---------------------------------------------------------------------------
Supervisor::Supervisor(const Order& order, SolveContext& ctx, EngineParams params)
    : order_(order), ctx_(ctx), params_(params) {}

void Supervisor::addStrategy(std::shared_ptr<Nester> n, const StrategyDescriber& d) {
    strategies_.emplace_back(std::move(n), d);
}

Solution Supervisor::run(BestObserver* sink) {
    Solution best;
    double bestScore = -1e300;
    if (strategies_.empty()) return best;

    BestObserver local;
    BestObserver* obs = sink ? sink : &local;

    for (auto& kv : strategies_) {
        if (ctx_.canceller && ctx_.canceller->probeCancel()) break;
        ctx_.order = &order_;
        // RE: 0x2CCF0 cascade -- repeat the same strategy with shrinking budgets
        std::vector<int> budgets{1};
        if (params_.cascadeBudgets) budgets = kv.second.cascade();
        for (int b : budgets) {
            if (ctx_.canceller && ctx_.canceller->probeCancel()) break;
            ctx_.maxIterations = std::max(1, params_.maxIterations / std::max(1, b));
            Solution s = kv.first->run(ctx_);
            const double sc = solutionScore(s);
            std::lock_guard<std::mutex> lk(mu_);
            obs->offer(s, sc);
            if (sc > bestScore) {
                bestScore = sc;
                best = s;
            }
        }
    }

    // finalisation passes, in the recovered order
    for (auto& n : best.nestings) {
        if (params_.renestInHoles) renestInHoles(order_, n, ctx_);
        if (params_.compactAtEnd) compactNesting(order_, n, ctx_);
        if (params_.finalizeBottomLeft) packedBottomLeft(order_, n);
    }
    best.valid = true;
    return best;
}

// ---------------------------------------------------------------------------
EngineResult Engine::run(const Order& order, const EngineParams& params, Observers* obs) {
    EngineResult res;
    const auto t0 = std::chrono::steady_clock::now();

    // working copy: parts are inflated by half the interpart gap (with self-intersection
    // removal), which is what the recovered AddInflatedToolPathToPart pipeline does
    Order prepared = order;
    if (order.interpartGap != 0.0) {
        prepareInflatedShapes(prepared, order.interpartGap * 0.5);
    }

    TimeCanceller canceller(params.timeLimitSeconds > 0.0 ? params.timeLimitSeconds
                                                          : order.timeLimitSeconds);
    NoFitMap nfp;
    nfp.setMaximumComplexity(NoFitMap::kDefaultMaxComplexity);
    Random rng(params.seed != 0 ? params.seed : 5489u);

    SolveContext ctx;
    ctx.order = &prepared;
    ctx.nfp = &nfp;
    ctx.canceller = &canceller;
    ctx.observers = obs;
    ctx.rng = &rng;
    ctx.beam = params.beam;
    ctx.timeLimitSeconds = params.timeLimitSeconds;
    ctx.maxIterations = params.maxIterations;
    ctx.log = &res.log;

    if (obs && obs->start) obs->start();

    Supervisor sup(prepared, ctx, params);
    auto strategies = makeDefaultStrategies();
    int mode = 1;
    for (auto& s : strategies) {
        StrategyDescriber d;
        d.mode = mode++;
        d.name = s->name();
        d.n = std::max(2, params.maxIterations / 4);
        sup.addStrategy(s, d);
    }

    Solution best = sup.run(nullptr);
    res.solution = best;
    res.strategiesRun = static_cast<int>(sup.strategyCount());
    res.score = solutionScore(best);
    res.cancelled = canceller.probeCancel();

    if (order.commonCutModeA != 0 || order.commonCutModeB != 0 || order.commonCutOnlyBiModules) {
        res.commonCuts = detectCommonCuts(prepared, res.solution);
    }

    if (obs && obs->newNestingFound) obs->newNestingFound(res.solution);
    if (obs && obs->stop) obs->stop();

    res.seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    return res;
}

// ---------------------------------------------------------------------------
// SVG reporting -- format recovered from ..\structure\svg_io.cpp (see re/findings_svg_io.md).
// The element order, the attribute spelling and the style fragments below are the ones the binary
// emits from 0x7CCDF0 and its style helpers:
//   header   0x7CCFBB '<svg width="'  + N + 'px" height="' + N + 'px" viewBox="' ... then
//            ' xmlns="http://www.w3.org/2000/svg"' ' version="1.1" '
//            ' xmlns:xlink="http://www.w3.org/1999/xlink">'
//   defs     0x7CCDF0 '<pattern id="diagonalHatch' ... '" patternUnits="userSpaceOnUse" width="'
//            ... '" height="' ... '"> <path d="M-1,1 l2,-2 M0,' ... ' l2,-2" style="stroke:rgb('
//            ... '); stroke-width:0.1%; fill-opacity:0.7; stroke-opacity:0.7' ... '" /> </pattern>'
//   body     0x7CCDF0 '<g transform="scale(1,-1)">' ... '<g transform="translate(' x ',' y ')">'
//            '<g fill-rule="evenodd"><path d="' ... ';fill:none"/>' ... '</g></g>' '</svg>'
//   styles   0x5DAEB0 'fill:none;stroke:black;stroke-width:0.1%'
//            0x5DDDD0 ');stroke:rgb(0, 0, 0);stroke-width:0.1%'  +  ';fill:rgb('
//            0x5DC9D0 ');stroke:rgb(0, 0, 0);stroke-width:0.2%'
//            0x5DE320 ');stroke:rgb(192, 0, 0);stroke-width:0.1%'   <- the mark colour
//            0x5DCE70 'fill: url(#diagonalHatch' + '); stroke-width:0.1%; fill-opacity:0.7; stroke-opacity:0.7'
//            0x5D9BF0 ';stroke-opacity:0.4;fill:rgb(128,128,128);stroke:rgb(0,0,0);'
//            0x516380 'fill:white'  /  'fill-opacity:0.8;fill:black;stroke:black;stroke-width:0.1%'
//   marks    0x7CCDF0 '<circle cx="' cy="' '" r="0.5%">'   (a PERCENT radius, not a user value)
// ---------------------------------------------------------------------------
namespace {

// Append an SVG path for a polygon ring (the binary writes 'd="M x,y L ... Z"' style data).
void svgRingPath(std::ostringstream& os, const geom::Ring& r) {
    if (r.empty()) return;
    os << "M" << geom::toDouble(r.front().x) << "," << geom::toDouble(r.front().y);
    for (std::size_t i = 1; i < r.size(); ++i) {
        os << " L" << geom::toDouble(r[i].x) << "," << geom::toDouble(r[i].y);
    }
    os << " Z";
}

// One element per polygon: outer ring plus its holes with fill-rule evenodd.
void svgPolygonPath(std::ostringstream& os, const geom::MultiPolygon& mp, const std::string& style) {
    for (const auto& p : mp) {
        os << "      <path fill-rule=\"evenodd\" d=\"";
        svgRingPath(os, p.external);
        for (const auto& h : p.inners) {
            os << " ";
            svgRingPath(os, h);
        }
        os << "\" style=\"" << style << "\"/>\n";
    }
}

}  // namespace

LCNS_STRUCTURAL(tu.svg_io);
std::string toSvg(const Order& order, const Solution& solution, bool includeMarks) {
    std::ostringstream os;
    std::vector<geom::Box> boxes;
    double totalW = 0.0, totalH = 0.0;
    for (const auto& sh : order.sheets) {
        const geom::Box b = geom::bounds(sheetPolygon(sh).external);
        boxes.push_back(b);
        totalW = std::max(totalW, geom::toDouble(b.max.x - b.min.x));
        totalH += geom::toDouble(b.max.y - b.min.y) + kSheetGap;
    }
    const double W = totalW + 2.0 * kSheetMargin;
    const double H = totalH + 2.0 * kSheetMargin;

    os << "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
    os << "<!-- generated by lcns::toSvg; element order and styles recovered from "
          "..\\structure\\svg_io.cpp -->\n";
    os << "<svg width=\"" << W << "px\" height=\"" << H << "px\" viewBox=\"0 0 " << W << " " << H
       << "\" xmlns=\"http://www.w3.org/2000/svg\" version=\"1.1\" "
          "xmlns:xlink=\"http://www.w3.org/1999/xlink\">\n";

    // The hatch pattern the binary defines once and references as fill: url(#diagonalHatch0).
    // Its pitch is a runtime number in the binary (0x7CCFDD..), so the value here is ours.
    os << "  <defs><pattern id=\"diagonalHatch0\" patternUnits=\"userSpaceOnUse\" width=\""
       << kHatchPitch << "\" height=\"" << kHatchPitch << "\"> <path d=\"M-1,1 l2,-2 M0,"
       << kHatchPitch << " l" << kHatchPitch << ",-" << kHatchPitch
       << " M3,5 l2,-2\" style=\"stroke:rgb(192, 0, 0); stroke-width:0.1%; fill-opacity:0.7; "
          "stroke-opacity:0.7\" /> </pattern></defs>\n";

    // The binary flips the layout (y up) into SVG space (y down) with a single outer group.
    os << "  <g transform=\"scale(1,-1)\">\n";
    double yOffset = kSheetMargin;
    for (std::size_t s = 0; s < order.sheets.size(); ++s) {
        const Sheet& sh = order.sheets[static_cast<std::size_t>(s)];
        const geom::Polygon outline = sheetPolygon(sh);
        const geom::Box& sb = boxes[s];
        const double shH = geom::toDouble(sb.max.y - sb.min.y);
        const double tx = kSheetMargin - geom::toDouble(sb.min.x);
        const double ty = -(yOffset + geom::toDouble(sb.max.y));   // see the note above
        os << "    <g transform=\"translate(" << tx << "," << ty << ")\">\n";

        os << "      <path d=\"";
        svgRingPath(os, outline.external);
        os << "\" style=\"fill:white;stroke:rgb(0, 0, 0);stroke-width:0.2%\"/>\n";

        // sheet defects: hatched, per 0x5DCE70's 'fill: url(#diagonalHatch'
        for (const auto& d : sh.defects) {
            os << "      <path fill-rule=\"evenodd\" d=\"";
            svgRingPath(os, d.external);
            for (const auto& h : d.inners) {
                os << " ";
                svgRingPath(os, h);
            }
            os << "\" style=\"" << kSvgHatchFill << kSvgStrokeBlack << "\"/>\n";
        }

        const Nesting* nesting = nullptr;
        for (const auto& n : solution.nestings) {
            if (n.sheetIndex == static_cast<int>(s)) { nesting = &n; break; }
        }
        if (nesting) {
            for (const auto& np : nesting->parts) {
                if (np.partIndex < 0 || np.partIndex >= static_cast<int>(order.parts.size())) continue;
                const Part& part = order.parts[static_cast<std::size_t>(np.partIndex)];
                // place the part with a translate group and keep the shape in its own frame,
                // exactly like the binary's '<g transform="translate(x,y)">'
                const geom::MultiPolygon local = placeShape(part.shape, np);
                os << "      <g transform=\"translate(" << np.x << "," << np.y << ")\">\n";
                svgPolygonPath(os, local, kSvgPartFill);
                os << "      </g>\n";
                if (includeMarks && order.markMode) {
                    const geom::Box pb = geom::bounds(local);
                    if (pb.valid) {
                        os << "      <circle cx=\"" << (geom::toDouble(pb.min.x) + np.x)
                           << "\" cy=\"" << (geom::toDouble(pb.min.y) + np.y)
                           << "\" r=\"" << kSvgMarkRadiusPct << "%\" style=\"" << kSvgMarkStyle
                           << "\"/>\n";
                    }
                }
            }
        }
        os << "    </g>\n";
        yOffset += shH + kSheetGap;
    }
    os << "  </g>\n";
    if (includeMarks) os << "  <!-- layer: __marks__ -->\n";
    os << "</svg>\n";
    return os.str();
}

bool writeSvg(const std::string& path, const Order& order, const Solution& solution,
              bool includeMarks) {
    std::ofstream f(path, std::ios::binary);
    if (!f) return false;
    f << toSvg(order, solution, includeMarks);
    return f.good();
}

std::string toHtmlReport(const Order& order, const Solution& solution) {
    std::ostringstream os;
    os << "<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\">"
          "<link rel=\"stylesheet\" href=\"cns_solution.css\">"
          "<title>CNS solution report</title></head><body>\n";
    os << "<h1>CNS - unknown</h1>\n";
    if (order.parts.empty() || order.sheets.empty()) {
        os << "<h1> Problem contains invalid parts. </h1>\n";
    }
    os << "<p>fill ratio: " << solution.fillRatio() * 100.0 << " %</p>\n";
    os << "<p>nestings: " << solution.nestings.size()
       << ", nested parts: " << solution.totalNestedParts() << "</p>\n";
    os << "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"800\" height=\"100\"></svg>\n";
    os << "<pre>" << toSvg(order, solution) << "</pre>\n";
    os << "</body></html>\n";
    return os.str();
}

}  // namespace lcns
