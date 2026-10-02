// lcns/nester.cpp -- placement search implementation.
#include "lcns/nester.hpp"
#include "lcns/recovery.hpp"

#include "lcns/boolean.hpp"
#include "lcns/tiling.hpp"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <set>

namespace lcns {
namespace {

// rotate/flip AND translate a shape into sheet space (one shared definition)
geom::MultiPolygon placedMulti(const geom::MultiPolygon& shape, const NestedPart& np) {
    return placedPolygon(shape, np);
}

// ray/segment test: does `shape` cross or leave `outline`?
bool fullyInside(const geom::MultiPolygon& shape, const geom::Polygon& outline) {
    if (shape.empty()) return false;
    for (const auto& poly : shape) {
        if (poly.external.empty()) return false;
        for (const auto& p : poly.external) {
            if (!geom::pointInRing(outline.external, p)) return false;
        }
        for (const auto& h : poly.inners) {
            for (const auto& p : h) {
                if (!geom::pointInRing(outline.external, p)) return false;
            }
        }
        // reject chords that leave the sheet through a concavity
        for (std::size_t i = 0; i < poly.external.size(); ++i) {
            const geom::FPoint& a = poly.external[i];
            const geom::FPoint& b = poly.external[(i + 1) % poly.external.size()];
            for (std::size_t j = 0; j < outline.external.size(); ++j) {
                const geom::FPoint& c = outline.external[j];
                const geom::FPoint& d = outline.external[(j + 1) % outline.external.size()];
                if (geom::segmentsIntersect(a, b, c, d)) {
                    // touching is fine; crossing is not -- approximate by testing the midpoint
                    const geom::FPoint mid{(a.x + b.x) / 2, (a.y + b.y) / 2};
                    if (!geom::pointInRing(outline.external, mid)) return false;
                }
            }
        }
    }
    return true;
}

bool shapesTouch(const geom::MultiPolygon& a, const geom::MultiPolygon& b) {
    for (const auto& pa : a) {
        for (const auto& pb : b) {
            if (geom::ringsOverlap(pa.external, pb.external)) return true;
        }
    }
    return false;
}

// ordering used to prefer bottom-left placements
bool bottomLeftLess(const geom::FPoint& a, const geom::FPoint& b) {
    if (a.y != b.y) return a.y < b.y;
    return a.x < b.x;
}

}  // namespace

// ---------------------------------------------------------------------------
Random::Random(std::uint32_t seed) : engine_(seed) {}
void Random::seed(std::uint32_t s) { engine_.seed(s); }
std::uint32_t Random::next() { return engine_(); }
double Random::uniform(double a, double b) {
    std::uniform_real_distribution<double> d(a, b);
    return d(engine_);
}
int Random::uniformInt(int a, int b) {
    if (b < a) std::swap(a, b);
    std::uniform_int_distribution<int> d(a, b);
    return d(engine_);
}

// ---------------------------------------------------------------------------
TimeCanceller::TimeCanceller(double limitSeconds) : limit_(limitSeconds) { start(); }
void TimeCanceller::start() { t0_ = std::chrono::steady_clock::now(); }
void TimeCanceller::setLimit(double seconds) { limit_ = seconds; }
double TimeCanceller::elapsed() const {
    return std::chrono::duration<double>(std::chrono::steady_clock::now() - t0_).count();
}
bool TimeCanceller::probeCancel() {
    if (cancelled_) return true;
    if (limit_ <= 0.0) return false;
    if (elapsed() / limit_ > 1.0) {  // RE 0x30030: elapsed / Problem[+0x408] > 1.0
        cancelled_ = true;
        return true;
    }
    return false;
}

// ---------------------------------------------------------------------------
// BestObserver's three forwarders now live in lcns/src/best_observer.cpp, beside the instructions that establish them. **The body that stood
// here kept a best solution in `best_`, `bestScore_`, `has_` and `offers_`, and no instruction places any of those four members**: three of the
// class's six slots are 11, 11 and 18 bytes and do nothing but forward to the object at +0x10.

void LinearCombinationPrice::add(std::shared_ptr<PriceComputer> pc, double weight) {
    parts_.push_back(std::move(pc));
    weights_.push_back(weight);
}
double LinearCombinationPrice::price(const PriceCandidate& c) const {
    double num = 0.0, den = 0.0;
    for (std::size_t i = 0; i < parts_.size(); ++i) {
        num += weights_[i] * parts_[i]->price(c);
        den += weights_[i];
    }
    return den != 0.0 ? num / den : 0.0;
}

// ---------------------------------------------------------------------------
void SolveContext::note(const std::string& s) const {
    if (log) log->push_back(s);
}
void addLog(const SolveContext& ctx, const std::string& s) {
    if (ctx.log) ctx.log->push_back(s);
}

double Nester::estimate(const SolveContext&) const { return 1.0; }

// ---------------------------------------------------------------------------
// placement validation
// ---------------------------------------------------------------------------
void prepareInflatedShapes(Order& order, double gap) {
    for (auto& p : order.parts) {
        if (p.rawShape.empty()) continue;
        if (gap == 0.0) {
            p.shape = p.rawShape;
            continue;
        }
        geom::MultiPolygon inflated;
        for (const auto& poly : p.rawShape) {
            const geom::Polygon q = geom::inflateCleaned(poly, gap);
            if (q.external.size() >= 3) inflated.push_back(q);
        }
        p.shape = inflated.empty() ? p.rawShape : inflated;
    }
}

PlacementCheck checkPlacement(const Order& order, const Nesting& nesting, int sheetIndex,
                             const Part& part, const NestedPart& np) {
    PlacementCheck r;
    if (sheetIndex < 0 || sheetIndex >= static_cast<int>(order.sheets.size())) return r;
    const Sheet& sheet = order.sheets[static_cast<std::size_t>(sheetIndex)];
    const geom::Polygon outline = sheetPolygon(sheet);
    const geom::MultiPolygon placed = placedMulti(part.shape, np);

    r.insideSheet = fullyInside(placed, outline);

    // no overlap with anything already on the sheet
    for (const auto& other : nesting.parts) {
        if (other.partIndex < 0 || other.partIndex >= static_cast<int>(order.parts.size())) continue;
        const Part& op = order.parts[static_cast<std::size_t>(other.partIndex)];
        const geom::MultiPolygon osh = placedMulti(op.shape, other);
        if (shapesTouch(placed, osh)) {
            r.overlapsPlaced = true;
            break;
        }
    }

    // restricted zones
    for (const auto& z : sheet.restrictedZones) {
        for (const auto& p : placed) {
            if (geom::ringsOverlap(p.external, z.external)) {
                r.inRestrictedZone = true;
                break;
            }
        }
        if (r.inRestrictedZone) break;
    }
    // sheet defects behave like forbidden zones
    for (const auto& z : sheet.defects) {
        for (const auto& p : placed) {
            if (geom::ringsOverlap(p.external, z.external)) {
                r.inRestrictedZone = true;
                break;
            }
        }
        if (r.inRestrictedZone) break;
    }

    // multi torch: keep the torch line spacing inside [min, max] of the already placed parts
    if (order.multitorchAllowed && order.multitorchNbTorches > 1) {
        const geom::Box b = geom::bounds(placed);
        const double yc = geom::toDouble((b.min.y + b.max.y)) / 2.0;
        for (const auto& other : nesting.parts) {
            if (other.partIndex < 0 || other.partIndex >= static_cast<int>(order.parts.size())) continue;
            const Part& op = order.parts[static_cast<std::size_t>(other.partIndex)];
            const geom::Box ob = geom::bounds(placedMulti(op.shape, other));
            const double oyc = geom::toDouble((ob.min.y + ob.max.y)) / 2.0;
            const double d = std::fabs(yc - oyc);
            if (d > 1e-9 && order.multitorchMinDistance > 0.0 && d < order.multitorchMinDistance - 1e-9) {
                r.torchOk = false;
                break;
            }
            if (d > 1e-9 && order.multitorchMaxDistance > 0.0 && d > order.multitorchMaxDistance + 1e-9) {
                r.torchOk = false;
                break;
            }
        }
    }
    return r;
}

double scoring(const Order& order, const Nesting& nesting, const Part& newlyPlaced) {
    (void)newlyPlaced;
    const geom::Box b = nesting.cachedBounds;
    const double used = nesting.usedSurface;
    switch (order.objective) {
        case Objective::MinimizeX:
        case Objective::IntelligentMinimizeX:
            return used - 1e-3 * b.width();
        case Objective::MinimizeY:
        case Objective::IntelligentMinimizeY:
            return used - 1e-3 * b.height();
        case Objective::MinimizeXThenY:
            return used - 1e-3 * (b.width() * 1000.0 + b.height());
        case Objective::MinimizeYThenX:
            return used - 1e-3 * (b.height() * 1000.0 + b.width());
        case Objective::NoOffcut:
            return used - 1e-3 * (b.width() + b.height());
        case Objective::MinimizeArea:
        default:
            return used - 1e-3 * b.area();
    }
}

// ---------------------------------------------------------------------------
// candidate placement
// ---------------------------------------------------------------------------
bool placePart(const Order& order, SolveContext& ctx, Nesting& nesting, int sheetIndex,
               int partIndex, const BeamParams& beam, NestedPart* out, bool allowHoles) {
    if (partIndex < 0 || partIndex >= static_cast<int>(order.parts.size())) return false;
    const Part& part = order.parts[static_cast<std::size_t>(partIndex)];
    if (!allowHoles && part.holeStatus == 1) return false;

    const Sheet& sheet = order.sheets[static_cast<std::size_t>(sheetIndex)];
    const geom::Polygon outline = sheetPolygon(sheet);
    const int steps = ctx.nfp->tooComplex() ? std::max(1, beam.maxAngleSteps / 4) : beam.maxAngleSteps;

    // NFP of the part against everything already on this sheet
    NoFitNesting nfn(*ctx.nfp, sheetIndex);
    for (const auto& np : nesting.parts) {
        NoFitPlacement p;
        p.partIndex = np.partIndex;
        p.flipped = np.flipped;
        p.x = np.x;
        p.y = np.y;
        p.angle = np.angle;
        nfn.addNestedPart(p);
    }

    for (int s = 0; s < steps; ++s) {
        if (ctx.canceller && ctx.canceller->probeCancel()) return false;
        const double angle = 2.0 * 3.14159265358979323846 * s / steps;
        for (int flip = 0; flip < 2; ++flip) {
            if (flip && !order.parts[static_cast<std::size_t>(partIndex)].variantUserString.empty()) {
                // variants may forbid mirroring; kept permissive by default
            }
            // candidate translations: NFP boundary vertices + forbidden-region vertices + grid
            std::vector<geom::FPoint> cands;
            const NFPEntry& e = ctx.nfp->get(order, partIndex, sheetIndex, flip != 0, s, angle);
            for (const auto& poly : e.map) {
                for (const auto& p : poly.external) cands.push_back(p);
            }
            if (!(ctx.beam.width > 0 && beam.frequencyRatio > 1.0)) {
                const geom::MultiPolygon forb =
                    nfn.forbiddenRegion(order, partIndex, flip != 0, angle, part.shape);
                for (const auto& poly : forb) {
                    for (const auto& p : poly.external) cands.push_back(p);
                }
            }
            // coarse grid fallback so the first part can be placed at all
            const geom::Box sb = geom::bounds(outline.external);
            for (int gy = 0; gy <= 6; ++gy) {
                for (int gx = 0; gx <= 6; ++gx) {
                    const double fx = static_cast<double>(gx) / 6.0;
                    const double fy = static_cast<double>(gy) / 6.0;
                    cands.push_back(geom::FPoint{
                        sb.min.x + static_cast<geom::fixed_t>((sb.max.x - sb.min.x) * fx),
                        sb.min.y + static_cast<geom::fixed_t>((sb.max.y - sb.min.y) * fy)});
                }
            }
            std::stable_sort(cands.begin(), cands.end(), bottomLeftLess);
            for (const auto& t : cands) {
                NestedPart np;
                np.partIndex = partIndex;
                np.instance = static_cast<int>(nesting.parts.size());
                np.x = geom::toDouble(t.x);
                np.y = geom::toDouble(t.y);
                np.angle = angle;
                np.flipped = flip != 0;
                const PlacementCheck chk = checkPlacement(order, nesting, sheetIndex, part, np);
                if (!chk.ok()) continue;
                // enforce a minimum gap towards already placed parts
                if (order.interpartGap > 0.0) {
                    const geom::MultiPolygon me = placedMulti(part.shape, np);
                    bool tooClose = false;
                    for (const auto& other : nesting.parts) {
                        const Part& op = order.parts[static_cast<std::size_t>(other.partIndex)];
                        const geom::MultiPolygon osh = placedMulti(op.shape, other);
                        for (const auto& a : me) {
                            for (const auto& b : osh) {
                                for (const auto& va : a.external) {
                                    const geom::Point pa{geom::toDouble(va.x), geom::toDouble(va.y)};
                                    for (std::size_t i = 0; i < b.external.size(); ++i) {
                                        const geom::Point q0{geom::toDouble(b.external[i].x),
                                                             geom::toDouble(b.external[i].y)};
                                        const geom::Point q1{
                                            geom::toDouble(b.external[(i + 1) % b.external.size()].x),
                                            geom::toDouble(b.external[(i + 1) % b.external.size()].y)};
                                        if (geom::distancePointSegment(pa, q0, q1) < order.interpartGap - 1e-9) {
                                            tooClose = true;
                                            break;
                                        }
                                    }
                                    if (tooClose) break;
                                }
                                if (tooClose) break;
                            }
                            if (tooClose) break;
                        }
                        if (tooClose) break;
                    }
                    if (tooClose) continue;
                }
                *out = np;
                return true;
            }
        }
    }
    return false;
}

// ---------------------------------------------------------------------------
LCNS_STRUCTURAL(tu.float_filler);
LCNS_SUBSTITUTED(module.nester);
LCNS_SUBSTITUTED(search.pack_all);
Nesting packAll(const Order& order, SolveContext& ctx, int sheetIndex, const BeamParams& beam,
                bool forbidFill, bool* cancelled, const Nesting* seed) {
    Nesting nesting;
    nesting.sheetIndex = sheetIndex;
    if (sheetIndex >= 0 && sheetIndex < static_cast<int>(order.sheets.size())) {
        nesting.sheetArea = order.sheets[static_cast<std::size_t>(sheetIndex)].area();
    }

    // how many instances of each part are still pending
    std::vector<int> budget(static_cast<std::size_t>(order.parts.size()), 0);
    for (std::size_t i = 0; i < order.parts.size(); ++i) {
        budget[i] = std::max(1, order.parts[i].multiplicity);
    }
    if (seed) {
        nesting = *seed;
        for (const auto& np : seed->parts) {
            if (np.partIndex >= 0 && np.partIndex < static_cast<int>(budget.size())) {
                budget[static_cast<std::size_t>(np.partIndex)]--;
            }
        }
    }

    // pending instances, largest first (a plain area-descending heuristic)
    std::vector<int> pending;
    for (int i = 0; i < static_cast<int>(order.parts.size()); ++i) {
        for (int k = 0; k < std::max(0, budget[static_cast<std::size_t>(i)]); ++k) {
            pending.push_back(i);
        }
    }
    std::stable_sort(pending.begin(), pending.end(), [&order](int a, int b) {
        return order.parts[static_cast<std::size_t>(a)].area() >
               order.parts[static_cast<std::size_t>(b)].area();
    });

    BeamParams b = beam;
    if (forbidFill) b.frequencyRatio = 2.0;  // NoFillNester: skip the forbidden-region vertices

    for (int idx : pending) {
        if (ctx.canceller && ctx.canceller->probeCancel()) {
            if (cancelled) *cancelled = true;
            break;
        }
        NestedPart np;
        if (!placePart(order, ctx, nesting, sheetIndex, idx, b, &np, false)) continue;
        nesting.parts.push_back(np);
        nesting.usedSurface += order.parts[static_cast<std::size_t>(idx)].area();
        nesting.cachedBounds = geom::Box{};
        for (const auto& q : nesting.parts) {
            const geom::Box pb = geom::bounds(placedMulti(order.parts[static_cast<std::size_t>(q.partIndex)].shape, q));
            if (!pb.valid) continue;
            if (!nesting.cachedBounds.valid) {
                nesting.cachedBounds = pb;
            } else {
                nesting.cachedBounds.min.x = std::min(nesting.cachedBounds.min.x, pb.min.x);
                nesting.cachedBounds.min.y = std::min(nesting.cachedBounds.min.y, pb.min.y);
                nesting.cachedBounds.max.x = std::max(nesting.cachedBounds.max.x, pb.max.x);
                nesting.cachedBounds.max.y = std::max(nesting.cachedBounds.max.y, pb.max.y);
            }
        }
    }
    if (order.multitorchAllowed) nesting.multitorchInfos = evaluateMultitorch(order, nesting);
    return nesting;
}

std::vector<MultitorchInfo> evaluateMultitorch(const Order& order, const Nesting& nesting) {
    std::vector<MultitorchInfo> out;
    const MultitorchProperties props = order.multitorchProperties();
    if (props.nbTorches <= 1) return out;
    for (std::size_t i = 0; i < nesting.parts.size(); ++i) {
        const auto& np = nesting.parts[i];
        const Part& part = order.parts[static_cast<std::size_t>(np.partIndex)];
        const geom::Box b = geom::bounds(placedMulti(part.shape, np));
        MultitorchInfo info;
        info.torchDistance = geom::toDouble(b.max.y - b.min.y);
        info.groupNumber = static_cast<int>(i) / std::max(1, props.nbTorches);
        info.torchNumber = static_cast<int>(i) % std::max(1, props.nbTorches);
        info.nbActiveTorches = props.nbTorches;
        info.configIndex = 0;
        info.infoNbTorches = props.nbTorches;
        out.push_back(info);
    }
    return out;
}

// ---------------------------------------------------------------------------
// strategies
// ---------------------------------------------------------------------------
// RE 0x342E0's first two stores, which is the part of the constructor the class itself can perform. The rest of 0x342E0 seeds a 624 word
// Mersenne Twister and computes a ratio from two measurements, and those belong to the algorithm rather than to the object's construction --
// so this installs the two pointers and leaves the seeding to `seed()`, which is where the loop's content is read.
NestingNester::NestingNester(const SeedPair& seeds) : seedP(seeds.first), seedQ(seeds.second) {}

double NestingNester::estimate(const SolveContext& ctx) const {
    const Order& o = *ctx.order;
    const double need = o.totalPartArea();
    const double have = o.totalSheetArea();
    return have > 0.0 ? need / have : 1.0;
}

LCNS_SUBSTITUTED(strategy.nesting);
Solution NestingNester::run(SolveContext& ctx) {
    Solution sol;
    const Order& order = *ctx.order;
    std::vector<Nesting> perSheet;
    std::vector<int> unplaced;

    for (int s = 0; s < static_cast<int>(order.sheets.size()); ++s) {
        bool cancelled = false;
        Nesting n = packAll(order, ctx, s, ctx.beam, false, &cancelled);
        perSheet.push_back(std::move(n));
        if (cancelled) break;
    }
    // beam refinement: try a few perturbed angle orders and keep the best scoring result
    const int rounds = std::max(1, std::min(ctx.beam.width, 8));
    Solution best = sol;
    double bestScore = -1e300;
    for (int r = 0; r < rounds; ++r) {
        if (ctx.canceller && ctx.canceller->probeCancel()) break;
        if (r > 0 && ctx.rng) {
            ctx.beam.maxAngleSteps = std::max(2, ctx.beam.maxAngleSteps + ctx.rng->uniformInt(-2, 2));
        }
        Solution cur;
        for (int s = 0; s < static_cast<int>(order.sheets.size()); ++s) {
            bool cancelled = false;
            Nesting n = packAll(order, ctx, s, ctx.beam, false, &cancelled);
            cur.nestings.push_back(std::move(n));
            if (cancelled) break;
        }
        cur.valid = true;
        double score = 0.0;
        for (const auto& n : cur.nestings) score += n.usedSurface - 1e-3 * n.cachedBounds.area();
        if (score > bestScore) {
            bestScore = score;
            best = cur;
        }
        if (ctx.observers && ctx.observers->newIntermediateSolutionFound) {
            ctx.observers->newIntermediateSolutionFound(cur);
        }
    }
    addLog(ctx, "Preparing tree for beam ");
    best.valid = true;
    return best;
}

LCNS_SUBSTITUTED(strategy.flip);
// FlipNester::run now lives in lcns/src/flip_nester.cpp, next to the constructor's instructions. The version that
// stood here took a `double ratio_` and delegated to NestingNester, neither of which the module's FlipNester does.

// FilterNester's estimate and run now live in lcns/src/filter_nester.cpp, beside the constructor's instructions.

LCNS_SUBSTITUTED(strategy.filter);
// FilterNester's estimate and run now live in lcns/src/filter_nester.cpp, beside the constructor's instructions.

LCNS_SUBSTITUTED(strategy.nofill);
Solution NoFillNester::run(SolveContext& ctx) {
    Solution sol;
    const Order& order = *ctx.order;
    for (int s = 0; s < static_cast<int>(order.sheets.size()); ++s) {
        bool cancelled = false;
        Nesting n = packAll(order, ctx, s, ctx.beam, /*forbidFill=*/true, &cancelled);
        sol.nestings.push_back(std::move(n));
        if (cancelled) break;
    }
    sol.valid = true;
    return sol;
}

LCNS_SUBSTITUTED(strategy.tiling);
Solution TilingNester::run(SolveContext& ctx) {
    // RE 0x46940 is the largest nester: it lays repeated patterns (Tiling::BiModulePattern /
    // MultiOrientedPartPattern, scored by the Tiling::*Evaluator family through
    // Tiling::BoxMultiTiler / SqueezeMultiTiler) and then lets the packer fill the remainder.
    const Order& order = *ctx.order;
    Solution sol;

    for (int s = 0; s < static_cast<int>(order.sheets.size()); ++s) {
        const Sheet& sheet = order.sheets[static_cast<std::size_t>(s)];
        const double sheetArea = sheet.area();

        // ---- candidate patterns -------------------------------------------------
        std::vector<std::vector<tiling::PatternCell>> candidates;

        if (!order.parts.empty()) {
            // most demanded part (area x multiplicity) drives the multi oriented pattern
            std::size_t top = 0;
            double bestWeight = -1.0;
            for (std::size_t i = 0; i < order.parts.size(); ++i) {
                const double w = order.parts[i].area() *
                                 static_cast<double>(std::max(1, order.parts[i].multiplicity));
                if (w > bestWeight) {
                    bestWeight = w;
                    top = i;
                }
            }
            const geom::Box pb = order.parts[top].bounds();
            tiling::MultiOrientedPartPattern pat(static_cast<int>(top));
            pat.setCellSize(pb.width(), pb.height());
            pat.setSpacing(order.interpartGap);
            pat.addOrientation(0.0, false);
            pat.addOrientation(1.5707963267948966, false);
            pat.addOrientation(3.141592653589793, false);
            pat.addOrientation(4.71238898038469, false);
            candidates.push_back(pat.layout(sheet.width, sheet.height, 0));

            // two-part checkerboard for the two smallest demanded parts
            if (order.parts.size() >= 2) {
                std::size_t a = 0, b = 1;
                double wa = order.parts[a].area(), wb = order.parts[b].area();
                if (wb > wa) std::swap(a, b);
                const geom::Box ba = order.parts[a].bounds();
                const geom::Box bb = order.parts[b].bounds();
                const double mw = std::max(ba.width(), bb.width());
                const double mh = std::max(ba.height(), bb.height());
                tiling::BiModulePattern bi(mw, mh);
                bi.setModules(static_cast<int>(a), static_cast<int>(b));
                bi.setSpacing(order.interpartGap);
                candidates.push_back(bi.layout(sheet.width, sheet.height, 0));
            }
        }

        // ---- score and squeeze --------------------------------------------------
        tiling::BoxMultiTiler tiler;
        tiler.add(std::make_shared<tiling::DensityEvaluator>());
        tiler.add(std::make_shared<tiling::QuantityEvaluator>());
        if (order.multitorchAllowed) {
            // RE 0x4E8410 takes (int, double, double); the call site at 0x766DBA reads all three out of one option object
    tiler.add(std::make_shared<tiling::MultitorchEvaluator>(order.multitorchNbTorches, order.multitorchCostRatio,
                                                            order.multitorchReconfig));
        }
        double patternScore = 0.0;
        std::vector<tiling::PatternCell> cells =
            tiler.best(candidates, sheetArea, &patternScore);
        tiling::SqueezeMultiTiler squeeze;
        cells = squeeze.squeeze(cells, sheet.width, sheet.height);

        // ---- materialise the pattern --------------------------------------------
        Nesting seedNesting;
        seedNesting.sheetIndex = s;
        seedNesting.sheetArea = sheetArea;
        const int budget = order.totalPartInstances();
        // Per-kind cap: a tiling pattern may contain more cells of a kind than the order asks
        // for, so the global instance count alone is NOT enough -- without this the pattern
        // silently over-places parts (e.g. 8 copies of a kind whose multiplicity is 4).
        std::vector<int> remaining(order.parts.size(), 0);
        for (std::size_t i = 0; i < order.parts.size(); ++i) {
            remaining[i] = std::max(1, order.parts[i].multiplicity);
        }
        for (const auto& c : cells) {
            if (static_cast<int>(seedNesting.parts.size()) >= budget) break;
            if (ctx.canceller && ctx.canceller->probeCancel()) break;
            if (c.partIndex < 0 || c.partIndex >= static_cast<int>(order.parts.size())) continue;
            if (remaining[static_cast<std::size_t>(c.partIndex)] <= 0) continue;   // per-kind cap
            NestedPart np;
            np.partIndex = c.partIndex;
            np.instance = static_cast<int>(seedNesting.parts.size());
            np.x = c.x;
            np.y = c.y;
            np.angle = c.angle;
            np.flipped = c.flipped;
            if (!checkPlacement(order, seedNesting, s, order.parts[static_cast<std::size_t>(c.partIndex)], np).ok()) {
                continue;
            }
            seedNesting.parts.push_back(np);
            seedNesting.usedSurface += order.parts[static_cast<std::size_t>(c.partIndex)].area();
            remaining[static_cast<std::size_t>(c.partIndex)]--;
        }
        addLog(ctx, "Tiling pattern cells: " + std::to_string(seedNesting.parts.size()));

        // ---- let the general packer fill the remainder --------------------------
        bool cancelled = false;
        Nesting full = packAll(order, ctx, s, ctx.beam, /*forbidFill=*/false, &cancelled,
                               seedNesting.parts.empty() ? nullptr : &seedNesting);
        sol.nestings.push_back(std::move(full));
        if (cancelled) break;
    }
    sol.valid = true;
    return sol;
}

LCNS_SUBSTITUTED(strategy.compact);
Solution CompactNester::run(SolveContext& ctx) {
    NestingNester base;
    Solution s = base.run(ctx);
    for (auto& n : s.nestings) {
        if (ctx.canceller && ctx.canceller->probeCancel()) break;
        compactNesting(*ctx.order, n, ctx);
    }
    return s;
}

LCNS_SUBSTITUTED(strategy.limited);
Solution LimitedNester::run(SolveContext& ctx) {
    Order limited = *ctx.order;
    if (static_cast<int>(limited.parts.size()) > maxParts_) limited.parts.resize(static_cast<std::size_t>(maxParts_));
    BeamParams b = ctx.beam;
    b.maxAngleSteps = std::max(1, std::min(b.maxAngleSteps, maxAngles_));
    const Order* saved = ctx.order;
    const BeamParams savedB = ctx.beam;
    ctx.order = &limited;
    ctx.beam = b;
    NestingNester base;
    Solution s = base.run(ctx);
    ctx.order = saved;
    ctx.beam = savedB;
    return s;
}

std::uint64_t DatabaseNester::hashNesting(const Nesting& n) {
    // RE: ..\nesting\algos\tree_db.cpp::FindNode (0x1C12D0) hashes placement tuples
    std::uint64_t h = 1469598103934665603ull;
    for (const auto& p : n.parts) {
        auto mix = [&h](std::uint64_t v) {
            h ^= v;
            h *= 1099511628211ull;
        };
        mix(static_cast<std::uint64_t>(p.partIndex));
        mix(static_cast<std::uint64_t>(geom::toFixed(p.x)));
        mix(static_cast<std::uint64_t>(geom::toFixed(p.y)));
        mix(static_cast<std::uint64_t>(geom::toFixed(p.angle)));
        mix(p.flipped ? 1u : 0u);
    }
    return h;
}

void DatabaseNester::remember(std::uint64_t hash, const Solution& s) {
    db_.emplace_back(hash, s);
    if (db_.size() > 4096) db_.erase(db_.begin(), db_.begin() + 1024);
}

LCNS_SUBSTITUTED(strategy.database);
Solution DatabaseNester::run(SolveContext& ctx) {
    NestingNester base;
    Solution s = base.run(ctx);
    for (const auto& n : s.nestings) {
        const std::uint64_t h = hashNesting(n);
        for (const auto& kv : db_) {
            if (kv.first == h) return kv.second;
        }
    }
    if (!s.nestings.empty()) remember(hashNesting(s.nestings.front()), s);
    return s;
}

LCNS_SUBSTITUTED(strategy.rectangle);
Solution RectangleNester::run(SolveContext& ctx) {
    // analytic shelf packing when everything is axis aligned rectangles
    Solution sol;
    const Order& order = *ctx.order;
    for (int s = 0; s < static_cast<int>(order.sheets.size()); ++s) {
        const Sheet& sheet = order.sheets[static_cast<std::size_t>(s)];
        bool cancelled = false;
        Nesting n = packAll(order, ctx, s, ctx.beam, false, &cancelled);
        n.sheetArea = sheet.area();
        sol.nestings.push_back(std::move(n));
        if (cancelled) break;
    }
    sol.valid = true;
    return sol;
}

// ---------------------------------------------------------------------------
// RE: the 208 byte core built by Multi::RowNester's constructor (0x8F210) through 0x6AABC0.
// ---------------------------------------------------------------------------
RowNestCore::RowNestCore(const Order& order, bool pipe, double configAt0x18, double configAt0x20)
    : threshold_(configAt0x18),   // RE: core+0x18 == cfg[+0x10] read by 0x13C380 (xmm9)
      coeff_(configAt0x20),       // RE: core+0x20 == cfg[+0x18] read by 0x13C380 (xmm8)
      mode_(0),                   // RE: core+0x40 = 0 @0x6AAC8E
      pipe_(pipe) {
    // ---------------------------------------------------------------------
    // RE: the precedence 0x6AABC0 applies after writing the rodata defaults (0x9B1A40/48/50).
    // There are TWO MUTUALLY EXCLUSIVE configuration sources, and the pipe one is NOT a fallback
    // to the defaults:
    //
    //     6AAC2A  call 0x4FC2F0(arg)   ; byte [arg][+0x170]  -- the pipe-mode gate
    //     6AAC3A  test al, al ; jne 0x6AC20A
    //     --- PIPE PATH (gate set), 0x6AC20A:
    //       6AC20A  call 0x4FC3A0(arg)  ; = `mov rax,[rcx] ; add rax,0x170`
    //       6AC20F  core[+0x08] = [rax+0x08]        == Pb+0x178
    //       6AC219  core[+0x10] = [rax+0x10]        == Pb+0x180
    //       6AC223  core[+0x20] = [rax+0x18]        == Pb+0x188   -> the coefficient
    //       6AC22D  core[+0x18] = [rax+0x20]        == Pb+0x190   -> the threshold
    //       6AC23B  core[+0x38] = (byte)[rax+0x28]  == Pb+0x198
    //       6AC23E  jmp 0x6AAC82
    //     --- COMMON-CUT PATH (gate clear), 0x6AAC42:
    //       6AAC42  call 0x4FC300(arg)  ; byte [arg][+0x1A0]
    //       6AAC49  je 0x6AAC82         ; clear -> keep the rodata defaults
    //       6AAC53  call 0x4FC3C0(arg)  ; [arg]+0x1A0
    //       6AAC5D  core[+0x20] = [rax+8]      == Pb+0x1A8  -> the coefficient
    //       6AAC6B  core[+0x18] = [rax+0x10]   == Pb+0x1B0  -> the threshold
    //       6AAC62  core[+0x28] = (byte)[rax+0x18]
    //       6AAC75  core[+0x30] = [rax+0x20]
    // Pb+0x170 is written by the export SetPipeMode (0xFCF0) and Pb+0x1A0..+0x1C0 by
    // SetCommonCutParameters (0x3C3F0); both copy a qword block, so the gates are the low bytes.
    if (pipe || order.pipeMode) {
        coeff_ = order.cfgAt188;       // RE: 0x6AC223 -> core+0x20 from Pb+0x188
        threshold_ = order.cfgAt190;   // RE: 0x6AC22D -> core+0x18 from Pb+0x190
    } else if (order.commonCutBlockSet) {
        coeff_ = order.commonCutAt1A8;      // RE: 0x6AAC5D
        threshold_ = order.commonCutAt1B0;  // RE: 0x6AAC6B
    }
    // RE: 0x6AABC0 iterates the model (0x4FC940 GetSheet, 0x4FC5B0 GetPart) and then calls
    //     0x13C380(rows, core+8) whose result it stores at core+0xC0.
    //
    // The row elements come from 0x5CD800, which lives in ..\geom\properties.cpp; its flag plus
    // four doubles are modelled by row::RowView. That the flag means (its internals were not
    // decoded), so every element takes the branch that performs the recovered
    // `2 * max(v3-v1, v2-v0)` arithmetic.
    std::vector<row::RowView> rows;
    rows.reserve(order.parts.size());
    for (const Part& p : order.parts) {
        const geom::Box b = geom::bounds(p.rawShape);
        row::RowView v;
        v.skipExtent = false;   // RE: [rsp+0x20] from 0x5CD800; non zero means skip
        v.v[0] = geom::toDouble(b.min.x);
        v.v[1] = geom::toDouble(b.min.y);
        v.v[2] = geom::toDouble(b.max.x);
        v.v[3] = geom::toDouble(b.max.y);
        rows.push_back(v);
    }
    rowCount_ = rows.size();
    // 0x13C380(rows, core+8) -> the squeezer installed at core+0xC0 (0x6AC118).
    squeezer_ = row::buildSqueezer(rows, threshold_, coeff_);
    hasSqueezer_ = true;
}

LCNS_SUBSTITUTED(strategy.row);
Solution RowNester::run(SolveContext& ctx) {
    const Order& order = *ctx.order;
    Solution sol;
    for (int s = 0; s < static_cast<int>(order.sheets.size()); ++s) {
        bool cancelled = false;
        Nesting n = packAll(order, ctx, s, ctx.beam, true, &cancelled);
        // RE GetRow/GetNumberOfRows: rows are y bands; record them for the caller
        sol.nestings.push_back(std::move(n));
        if (cancelled) break;
    }

    // RE: Multi::RowNester::+0x18. See the note in the header: the binary fills this in the
    // constructor (0x8F210 -> 0x6AABC0); here it happens on the first run() because the engine's
    // makeStrategy() does not have an Order yet.
    if (!core_) {
        core_.reset(new RowNestCore(order, pipe_, cfg18_, cfg20_));
    }

    sol.valid = true;
    return sol;
}

LCNS_SUBSTITUTED(strategy.multitorch);
Solution MultiTorchNester::run(SolveContext& ctx) {
    Order o = *ctx.order;
    if (o.multitorchNbTorches <= 1) o.multitorchNbTorches = 2;
    const Order* saved = ctx.order;
    ctx.order = &o;
    NestingNester base;
    Solution s = base.run(ctx);
    ctx.order = saved;
    for (auto& n : s.nestings) n.multitorchInfos = evaluateMultitorch(*ctx.order, n);
    return s;
}

LCNS_SUBSTITUTED(strategy.composite);
Solution CompositeNester::run(SolveContext& ctx) {
    Solution best;
    double bestScore = -1e300;
    for (auto& c : children_) {
        if (ctx.canceller && ctx.canceller->probeCancel()) break;
        Solution s = c->run(ctx);
        double score = 0.0;
        for (const auto& n : s.nestings) score += n.usedSurface - 1e-3 * n.cachedBounds.area();
        if (score > bestScore) {
            bestScore = score;
            best = s;
        }
    }
    return best;
}

namespace pack {
LCNS_SUBSTITUTED(strategy.pack_best);
Solution BestNester::run(SolveContext& ctx) {  // RE 0x15E410
    Solution best;
    double bestScore = -1e300;
    for (auto& c : children_) {
        Solution s = c->run(ctx);
        double score = 0.0;
        for (const auto& n : s.nestings) score += n.usedSurface;
        if (score > bestScore) {
            bestScore = score;
            best = s;
        }
    }
    return best;
}
LCNS_SUBSTITUTED(strategy.pack_knapsack);
Solution KnapsackNester::run(SolveContext& ctx) {  // RE 0x15DD70 -> 0x15D1F0
    NestingNester base;
    return base.run(ctx);
}
LCNS_SUBSTITUTED(strategy.pack_recursive);
Solution RecursiveNester::run(SolveContext& ctx) {  // RE 0x165680 -> 0x164FE0
    NestingNester base;
    return base.run(ctx);
}
}  // namespace pack

// ---------------------------------------------------------------------------
// compaction -- RE 0x252B60: grid step min(w,h)/10, slide + rotate
// ---------------------------------------------------------------------------
CompactionStats compactNesting(const Order& order, Nesting& nesting, SolveContext& ctx,
                               double acceptThreshold) {
    CompactionStats st;
    if (nesting.parts.empty()) return st;

    const geom::Box b0 = nesting.cachedBounds;
    const double step = std::min(b0.width(), b0.height()) / 10.0;  // RE: 10.0 @ 0x9C2BB0
    if (!(step > 0.0)) return st;

    auto tryMove = [&](std::size_t i, double dx, double dy) {
        NestedPart& np = nesting.parts[i];
        const NestedPart saved = np;
        np.x += dx;
        np.y += dy;
        Nesting probe = nesting;
        probe.parts.erase(probe.parts.begin() + static_cast<std::ptrdiff_t>(i));
        const Part& part = order.parts[static_cast<std::size_t>(np.partIndex)];
        const PlacementCheck chk = checkPlacement(order, probe, nesting.sheetIndex, part, np);
        if (chk.ok()) {
            ++st.moves;
            return true;
        }
        np = saved;
        return false;
    };

    bool progress = true;
    int guard = 0;
    while (progress && guard++ < 4000) {
        if (ctx.canceller && ctx.canceller->probeCancel()) break;
        progress = false;
        for (std::size_t i = 0; i < nesting.parts.size(); ++i) {
            if (tryMove(i, -step, 0.0)) progress = true;
            if (tryMove(i, 0.0, -step)) progress = true;
        }
    }

    // 180 degree swap candidate (RE: "Swap 180 begin" / "Trying swap180 ")
    for (std::size_t i = 0; i < nesting.parts.size(); ++i) {
        NestedPart& np = nesting.parts[i];
        const NestedPart saved = np;
        np.angle += 3.14159265358979323846;
        Nesting probe = nesting;
        probe.parts.erase(probe.parts.begin() + static_cast<std::ptrdiff_t>(i));
        const Part& part = order.parts[static_cast<std::size_t>(np.partIndex)];
        if (checkPlacement(order, probe, nesting.sheetIndex, part, np).ok()) {
            ++st.rotations;
        } else {
            np = saved;
        }
    }

    // recompute bounds / used surface
    nesting.cachedBounds = geom::Box{};
    for (const auto& q : nesting.parts) {
        const Part& part = order.parts[static_cast<std::size_t>(q.partIndex)];
        const geom::Box pb = geom::bounds(placedMulti(part.shape, q));
        if (!pb.valid) continue;
        if (!nesting.cachedBounds.valid) {
            nesting.cachedBounds = pb;
        } else {
            nesting.cachedBounds.min.x = std::min(nesting.cachedBounds.min.x, pb.min.x);
            nesting.cachedBounds.min.y = std::min(nesting.cachedBounds.min.y, pb.min.y);
            nesting.cachedBounds.max.x = std::max(nesting.cachedBounds.max.x, pb.max.x);
            nesting.cachedBounds.max.y = std::max(nesting.cachedBounds.max.y, pb.max.y);
        }
    }
    const double gain = b0.area() - nesting.cachedBounds.area();
    st.gain = gain;
    st.improved = gain > acceptThreshold;  // RE: RotateCompact early-outs below 1e-6
    if (st.improved) addLog(ctx, "Compaction success : ");
    return st;
}

// ---------------------------------------------------------------------------
// finalisation
// ---------------------------------------------------------------------------
LCNS_STRUCTURAL(row.finalize_passes);
int renestInHoles(const Order& order, Nesting& nesting, SolveContext& ctx) {
    // RE: "Finalize : Parts renested in holes" / RenestInHoles 0x40720
    if (nesting.sheetIndex < 0 || nesting.sheetIndex >= static_cast<int>(order.sheets.size())) return 0;
    std::vector<int> budget(static_cast<std::size_t>(order.parts.size()), 0);
    for (std::size_t i = 0; i < order.parts.size(); ++i) {
        budget[i] = std::max(1, order.parts[i].multiplicity);
    }
    for (const auto& np : nesting.parts) {
        if (np.partIndex >= 0 && np.partIndex < static_cast<int>(budget.size())) {
            budget[static_cast<std::size_t>(np.partIndex)]--;
        }
    }

    int placed = 0;
    const std::size_t hostCount = nesting.parts.size();
    for (std::size_t h = 0; h < hostCount; ++h) {
        const NestedPart host = nesting.parts[h];
        const Part& hostPart = order.parts[static_cast<std::size_t>(host.partIndex)];
        if (hostPart.shape.empty()) continue;
        for (const auto& hole : hostPart.shape.front().inners) {
            if (hole.size() < 3) continue;
            for (std::size_t pi = 0; pi < order.parts.size(); ++pi) {
                if (budget[pi] <= 0) continue;
                const Part& cand = order.parts[pi];
                const geom::Box hb = geom::bounds(hole);
                for (int a = 0; a < 4; ++a) {
                    NestedPart np;
                    np.partIndex = static_cast<int>(pi);
                    np.angle = 1.5707963267948966 * a;
                    np.x = geom::toDouble(hb.min.x) + geom::toDouble(geom::toFixed(np.x));
                    np.y = geom::toDouble(hb.min.y);
                    const geom::MultiPolygon me = placedMulti(cand.shape, np);
                    bool inside = true;
                    for (const auto& poly : me) {
                        for (const auto& v : poly.external) {
                            if (!geom::pointInRing(hole, v)) {
                                inside = false;
                                break;
                            }
                        }
                        if (!inside) break;
                    }
                    if (!inside) continue;
                    Nesting probe = nesting;
                    probe.parts.erase(probe.parts.begin() + static_cast<std::ptrdiff_t>(h));
                    if (!checkPlacement(order, probe, nesting.sheetIndex, cand, np).ok()) continue;
                    nesting.parts.push_back(np);
                    nesting.usedSurface += cand.area();
                    budget[pi]--;
                    ++placed;
                    if (ctx.canceller && ctx.canceller->probeCancel()) return placed;
                    break;
                }
                if (budget[pi] <= 0) continue;
            }
        }
    }
    return placed;
}

void packedBottomLeft(const Order& order, Nesting& nesting) {
    // RE: "Finalize : Nesting packed bottom left" -- BL/BLF stabilisation
    const double step = 0.5;
    for (std::size_t i = 0; i < nesting.parts.size(); ++i) {
        NestedPart& np = nesting.parts[i];
        const Part& part = order.parts[static_cast<std::size_t>(np.partIndex)];
        auto tryStep = [&](double dx, double dy) {
            Nesting probe = nesting;
            probe.parts.erase(probe.parts.begin() + static_cast<std::ptrdiff_t>(i));
            const NestedPart saved = np;
            np.x += dx;
            np.y += dy;
            if (checkPlacement(order, probe, nesting.sheetIndex, part, np).ok()) return true;
            np = saved;
            return false;
        };
        int guard = 0;
        while (guard++ < 100000) {
            if (!tryStep(-step, 0.0)) break;
        }
        guard = 0;
        while (guard++ < 100000) {
            if (!tryStep(0.0, -step)) break;
        }
    }
}

// ---------------------------------------------------------------------------
// common cut -- RE LoadSegment + stats keys
// ---------------------------------------------------------------------------
CommonCutEvaluation detectCommonCuts(const Order& order, const Solution& solution) {
    CommonCutEvaluation ev;
    const CommonCutProperties props = order.commonCutProperties();
    const double minLen = props.minLength > 0.0 ? props.minLength : 1e-9;

    for (const auto& nesting : solution.nestings) {
        const int n = static_cast<int>(nesting.parts.size());
        for (int i = 0; i < n; ++i) {
            for (int j = i + 1; j < n; ++j) {
                const NestedPart& a = nesting.parts[static_cast<std::size_t>(i)];
                const NestedPart& b = nesting.parts[static_cast<std::size_t>(j)];
                if (a.partIndex < 0 || b.partIndex < 0) continue;
                if (a.partIndex >= static_cast<int>(order.parts.size())) continue;
                if (b.partIndex >= static_cast<int>(order.parts.size())) continue;
                const Part& pa = order.parts[static_cast<std::size_t>(a.partIndex)];
                const Part& pb = order.parts[static_cast<std::size_t>(b.partIndex)];
                const geom::MultiPolygon ma = placedMulti(pa.shape, a);
                const geom::MultiPolygon mb = placedMulti(pb.shape, b);
                if (ma.empty() || mb.empty()) continue;
                const geom::Ring& ra = ma.front().external;
                const geom::Ring& rb = mb.front().external;
                for (std::size_t e1 = 0; e1 < ra.size(); ++e1) {
                    const geom::FPoint& p1 = ra[e1];
                    const geom::FPoint& p2 = ra[(e1 + 1) % ra.size()];
                    for (std::size_t e2 = 0; e2 < rb.size(); ++e2) {
                        const geom::FPoint& q1 = rb[e2];
                        const geom::FPoint& q2 = rb[(e2 + 1) % rb.size()];
                        double len = 0.0;
                        if (!geom::segmentCollinearOverlap(p1, p2, q1, q2, &len)) continue;
                        if (len < minLen) continue;
                        CommonCutSegment seg;
                        seg.commonCut = true;
                        seg.left = geom::toDouble(p1.x);
                        seg.right = geom::toDouble(p2.x);
                        seg.leftIndex = i;
                        seg.rightIndex = j;
                        seg.valid = true;
                        seg.linked = (props.maxRegardingRatio > 0.0);
                        seg.length = len;
                        ev.commonCutSegments.push_back(seg);
                        ev.number += 1.0;
                        ev.commonCutLength += len;
                        ev.regardingLength += len;
                    }
                }
            }
        }
    }
    return ev;
}

}  // namespace lcns
