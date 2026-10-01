// lcns/nfp.cpp
#include "lcns/nfp.hpp"
#include "lcns/recovery.hpp"

#include "lcns/boolean.hpp"

#include <algorithm>

LCNS_STRUCTURAL(module.nfp);
namespace lcns {

NoFitMap::NoFitMap(int maxComplexity) : maxComplexity_(maxComplexity) {}

void NoFitMap::setMaximumComplexity(int c) { maxComplexity_ = c > 0 ? c : kDefaultMaxComplexity; }
int NoFitMap::maximumComplexity() const { return maxComplexity_; }

void NoFitMap::clear() {
    cache_.clear();
    cachedPolygons_ = 0;
}

std::size_t NoFitMap::cachedPolygons() const { return cachedPolygons_; }
std::size_t NoFitMap::entryCount() const { return cache_.size(); }

bool NoFitMap::tooComplex() const {
    return cachedPolygons_ > static_cast<std::size_t>(maxComplexity_);
}

const NFPEntry& NoFitMap::get(const Order& order, int partIndex, int sheetIndex, bool flip,
                              int angleStep, double angleRadians) {
    // RE 0x665C06/0x665D92: if the cache grew past the threshold, drop everything
    if (cachedPolygons_ > kCacheClearThreshold) clear();

    const NFPKey key{partIndex, sheetIndex, angleStep, flip ? 1 : 0};
    auto it = cache_.find(key);
    if (it != cache_.end()) return it->second;

    NFPEntry e = build(order, partIndex, sheetIndex, flip, angleStep, angleRadians);
    cachedPolygons_ += e.map.size();
    auto res = cache_.emplace(key, std::move(e));
    return res.first->second;
}

NFPEntry NoFitMap::build(const Order& order, int partIndex, int sheetIndex, bool flip,
                         int angleStep, double angleRadians) {
    NFPEntry e;
    e.key = NFPKey{partIndex, sheetIndex, angleStep, flip ? 1 : 0};
    e.partIndex = partIndex;
    e.sheetIndex = sheetIndex;
    e.flipped = flip;
    e.angle = angleRadians;

    if (partIndex < 0 || partIndex >= static_cast<int>(order.parts.size())) return e;
    if (sheetIndex < 0 || sheetIndex >= static_cast<int>(order.sheets.size())) return e;

    const Part& part = order.parts[static_cast<std::size_t>(partIndex)];
    const Sheet& sheet = order.sheets[static_cast<std::size_t>(sheetIndex)];
    e.sheetOutline = sheetPolygon(sheet);

    // oriented part, holes included (non-convex geometry is handled by minkowskiMulti)
    NestedPart orient;
    orient.flipped = flip;
    orient.angle = angleRadians;
    const geom::MultiPolygon partMulti = placeShape(part.shape, orient);
    if (partMulti.empty() || partMulti.front().external.size() < 3) return e;

    // NFP(sheet, part) = sheet (+) -part : the locus of part-reference translations at which
    // the part touches the sheet border. minkowskiMulti keeps the sheet's own holes.
    geom::MultiPolygon sheetMulti;
    sheetMulti.push_back(e.sheetOutline);
    e.map = geom::nfpMulti(sheetMulti, partMulti);

    // restricted zones and sheet defects behave like extra forbidden obstacles; union their
    // no-fit loci into the same entry so candidate generation sees them.
    for (const auto& z : sheet.restrictedZones) {
        geom::MultiPolygon zm;
        zm.push_back(z);
        e.map = geom::unite(e.map, geom::nfpMulti(zm, partMulti));
    }
    for (const auto& z : sheet.defects) {
        geom::MultiPolygon zm;
        zm.push_back(z);
        e.map = geom::unite(e.map, geom::nfpMulti(zm, partMulti));
    }
    return e;
}

// ---------------------------------------------------------------------------
NoFitNesting::NoFitNesting(NoFitMap& map, int sheetIndex) : map_(&map), sheetIndex_(sheetIndex) {}

void NoFitNesting::addNestedPart(const NoFitPlacement& p) { placements_.push_back(p); }
void NoFitNesting::clear() { placements_.clear(); }

geom::MultiPolygon NoFitNesting::forbiddenRegion(const Order& order, int partIndex, bool flip,
                                                double angle,
                                                const geom::MultiPolygon& partShape) const {
    (void)map_;
    (void)partIndex;  // kept for parity with the recovered entry points
    (void)flip;       // the candidate's orientation is already baked into `partShape`
    (void)angle;
    geom::MultiPolygon acc;
    bool first = true;

    for (const auto& pl : placements_) {
        if (pl.partIndex < 0 || pl.partIndex >= static_cast<int>(order.parts.size())) continue;
        const Part& other = order.parts[static_cast<std::size_t>(pl.partIndex)];
        NestedPart onp;
        onp.angle = pl.angle;
        onp.flipped = pl.flipped;
        const geom::MultiPolygon placed = placeShape(other.shape, onp);
        if (placed.empty()) continue;

        // forbidden translation set = placement position + NFP(placed, candidate)
        geom::MultiPolygon reg = geom::nfpMulti(placed, partShape);
        const geom::fixed_t dx = geom::toFixed(pl.x);
        const geom::fixed_t dy = geom::toFixed(pl.y);
        for (auto& poly : reg) {
            for (auto& p : poly.external) { p.x += dx; p.y += dy; }
            for (auto& h : poly.inners) { for (auto& p : h) { p.x += dx; p.y += dy; } }
        }
        if (first) {
            acc = std::move(reg);
            first = false;
        } else {
            acc = geom::unite(acc, reg);
        }
    }
    // a true union, not a polygon list: overlapping forbidden areas are merged
    return acc.empty() ? acc : geom::normalize(acc);
}

bool NoFitNesting::forbiddenContains(const geom::MultiPolygon& region, geom::FPoint reference) {
    for (const auto& p : region) {
        if (geom::pointInPolygon(p, reference)) return true;
    }
    return false;
}

bool NoFitNesting::forbiddenIntersects(const geom::MultiPolygon& region,
                                      const geom::MultiPolygon& shape) {
    for (const auto& r : region) {
        for (const auto& s : shape) {
            if (geom::ringsOverlap(r.external, s.external)) return true;
            if (!r.external.empty() && geom::pointInRing(r.external, s.external.front())) return true;
        }
    }
    return false;
}

}  // namespace lcns
