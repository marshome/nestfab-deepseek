// lcns/model.cpp
#include "lcns/model.hpp"
#include "lcns/recovery.hpp"

#include <algorithm>
#include <cmath>

LCNS_RECOVERED(module.model);
namespace lcns {
namespace {

geom::Ring xformRing(const geom::Ring& r, double angle, bool flip) {
    const double c = std::cos(angle), s = std::sin(angle);
    geom::Ring o;
    o.reserve(r.size());
    for (const auto& p : r) {
        double x = geom::toDouble(p.x);
        double y = geom::toDouble(p.y);
        if (flip) x = -x;
        const double nx = x * c - y * s;
        const double ny = x * s + y * c;
        o.push_back(geom::FPoint{geom::toFixed(nx), geom::toFixed(ny)});
    }
    return o;
}

}  // namespace

geom::Polygon rectPolygon(double x, double y, double w, double h) {
    geom::Polygon p;
    p.external = geom::toRing({{x, y}, {x + w, y}, {x + w, y + h}, {x, y + h}});
    if (!geom::isCCW(p.external)) p.external = geom::reverse(p.external);
    return p;
}

geom::Polygon circlePolygon(double cx, double cy, double r, int segments) {
    if (segments < 3) segments = 3;
    std::vector<geom::Point> pts;
    pts.reserve(static_cast<std::size_t>(segments));
    for (int i = 0; i < segments; ++i) {
        const double a = 6.283185307179586476925286766559 * i / segments;
        pts.push_back(geom::Point{cx + r * std::cos(a), cy + r * std::sin(a)});
    }
    geom::Polygon p;
    p.external = geom::toRing(pts);
    if (!geom::isCCW(p.external)) p.external = geom::reverse(p.external);
    return p;
}

geom::MultiPolygon makeRectMulti(double x, double y, double w, double h) {
    return geom::MultiPolygon{rectPolygon(x, y, w, h)};
}

geom::MultiPolygon placeShape(const geom::MultiPolygon& shape, const NestedPart& np) {
    geom::MultiPolygon out;
    out.reserve(shape.size());
    for (const auto& p : shape) {
        geom::Polygon q;
        q.external = xformRing(p.external, np.angle, np.flipped);
        for (const auto& h : p.inners) q.inners.push_back(xformRing(h, np.angle, np.flipped));
        out.push_back(std::move(q));
    }
    return out;
}

geom::Box placeBounds(const geom::MultiPolygon& shape, const NestedPart& np) {
    return geom::bounds(placeShape(shape, np));
}

// rotation + flip + translation: the one definition of "where this part actually is"
LCNS_NOT_REVERSED(model.item_unknown_fields);
geom::MultiPolygon placedPolygon(const geom::MultiPolygon& shape, const NestedPart& np) {
    geom::MultiPolygon m = placeShape(shape, np);
    const geom::fixed_t dx = geom::toFixed(np.x);
    const geom::fixed_t dy = geom::toFixed(np.y);
    if (dx == 0 && dy == 0) return m;
    for (auto& poly : m) {
        for (auto& p : poly.external) {
            p.x += dx;
            p.y += dy;
        }
        for (auto& h : poly.inners) {
            for (auto& p : h) {
                p.x += dx;
                p.y += dy;
            }
        }
    }
    return m;
}

geom::MultiPolygon placedShape(const Part& part, const NestedPart& np) {
    return placedPolygon(part.shape, np);
}

geom::Polygon sheetPolygon(const Sheet& s) {
    if (s.nonRectangular && !s.shape.empty()) return s.shape.front();
    return rectPolygon(0.0, 0.0, s.width, s.height);
}

geom::Polygon Sheet::outline() const { return sheetPolygon(*this); }

double Sheet::area() const {
    if (nonRectangular && !shape.empty()) {
        double a = 0.0;
        for (const auto& p : shape) {
            a += geom::area(p.external);
            for (const auto& h : p.inners) a -= geom::area(h);
        }
        return a;
    }
    return width * height;
}

double Part::area() const {
    double a = 0.0;
    for (const auto& p : rawShape) {
        a += geom::area(p.external);
        for (const auto& h : p.inners) a -= geom::area(h);
    }
    return a;
}

double Solution::usedSurface() const {
    double s = 0.0;
    for (const auto& n : nestings) s += n.usedSurface;
    return s;
}

double Solution::sheetArea() const {
    double s = 0.0;
    for (const auto& n : nestings) s += n.sheetArea;
    return s;
}

double Solution::fillRatio() const {
    const double t = sheetArea();
    return t > 0.0 ? usedSurface() / t : 0.0;
}

int Solution::totalNestedParts() const {
    int t = 0;
    for (const auto& n : nestings) t += static_cast<int>(n.parts.size());
    return t;
}

CommonCutProperties Order::commonCutProperties() const {
    if (commonCutModeTag == 1 && commonCutPresetIndex2 >= 0 &&
        commonCutPresetIndex2 < static_cast<int>(commonCutPresets.size())) {
        return commonCutPresets[static_cast<std::size_t>(commonCutPresetIndex2)];
    }
    CommonCutProperties p;
    p.allowed = commonCutModeA;
    p.gap = interpartGap;
    p.originalPartGap = interpartGap;
    p.maxRegardingRatio =
        commonCutObjectiveDen != 0.0 ? commonCutObjectiveNum / commonCutObjectiveDen : 0.0;
    p.noHoles = commonCutNoHoles;
    p.onlyBiModules = commonCutOnlyBiModules;
    return p;
}

MultitorchProperties Order::multitorchProperties() const {
    if (multitorchModeTag == 1 && multitorchPresetIndex >= 0 &&
        multitorchPresetIndex < static_cast<int>(multitorchPresets.size())) {
        return multitorchPresets[static_cast<std::size_t>(multitorchPresetIndex)];
    }
    MultitorchProperties p;
    p.nbTorches = multitorchNbTorches;
    p.minTorchDistance = multitorchMinDistance;
    p.maxTorchDistance = multitorchMaxDistance;
    p.reconfigurationCost = multitorchReconfig;
    return p;
}

int Order::totalPartInstances() const {
    int t = 0;
    for (const auto& p : parts) t += std::max(1, p.multiplicity);
    return t;
}

double Order::totalPartArea() const {
    double a = 0.0;
    for (const auto& p : parts) a += p.area() * std::max(1, p.multiplicity);
    return a;
}

double Order::totalSheetArea() const {
    double a = 0.0;
    for (const auto& s : sheets) a += s.area() * std::max(1, s.quantity);
    return a;
}

}  // namespace lcns
