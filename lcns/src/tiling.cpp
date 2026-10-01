// lcns/tiling.cpp
#include "lcns/tiling.hpp"
#include "lcns/recovery.hpp"

#include <algorithm>
#include <cmath>

LCNS_SUBSTITUTED(module.tiling);
namespace lcns {
namespace tiling {

// ---------------------------------------------------------------------------
// --- PackerCache ---
void PackerCache::clear() {
    keys_.clear();
    entries_ = 0;
}
void PackerCache::store(const std::string& key) {
    if (!contains(key)) keys_.push_back(key);
    entries_ = keys_.size();
}
bool PackerCache::contains(const std::string& key) const {
    return std::find(keys_.begin(), keys_.end(), key) != keys_.end();
}

// ---------------------------------------------------------------------------
// --- BiModulePattern ---
BiModulePattern::BiModulePattern(double moduleW, double moduleH)
    : moduleW_(moduleW), moduleH_(moduleH) {}

void BiModulePattern::setModules(int partA, int partB) {
    partA_ = partA;
    partB_ = partB;
}

std::vector<PatternCell> BiModulePattern::layout(double sheetW, double sheetH, int budget) const {
    std::vector<PatternCell> out;
    const double stepX = moduleW_ + spacing_;
    const double stepY = moduleH_ + spacing_;
    if (stepX <= 0.0 || stepY <= 0.0) return out;
    const int cols = moduleW_ <= sheetW
                         ? static_cast<int>(std::floor((sheetW - moduleW_) / stepX + 1e-9)) + 1
                         : 0;
    const int rows = moduleH_ <= sheetH
                         ? static_cast<int>(std::floor((sheetH - moduleH_) / stepY + 1e-9)) + 1
                         : 0;
    int placed = 0;
    for (int r = 0; r < rows; ++r) {
        for (int c = 0; c < cols; ++c) {
            // RE: the two modules alternate like a checkerboard
            const bool even = ((r + c) % 2) == 0;
            const int part = even ? partA_ : partB_;
            if (part < 0) continue;
            if (budget > 0 && placed >= budget) return out;
            PatternCell cell;
            cell.partIndex = part;
            cell.x = c * stepX;
            cell.y = r * stepY;
            cell.angle = 0.0;
            cell.flipped = false;
            cell.footprint = geom::Box{geom::FPoint{geom::toFixed(cell.x), geom::toFixed(cell.y)},
                                       geom::FPoint{geom::toFixed(cell.x + moduleW_),
                                                    geom::toFixed(cell.y + moduleH_)},
                                       true};
            out.push_back(cell);
            ++placed;
        }
    }
    return out;
}

// ---------------------------------------------------------------------------
// --- MultiOrientedPartPattern ---
MultiOrientedPartPattern::MultiOrientedPartPattern(int partIndex) : partIndex_(partIndex) {}

void MultiOrientedPartPattern::addOrientation(double angleRadians, bool flipped) {
    orientations_.push_back(Orientation{angleRadians, flipped});
}

void MultiOrientedPartPattern::setCellSize(double w, double h) {
    cellW_ = w;
    cellH_ = h;
}

std::vector<PatternCell> MultiOrientedPartPattern::layout(double sheetW, double sheetH,
                                                          int budget) const {
    std::vector<PatternCell> out;
    if (orientations_.empty() || partIndex_ < 0) return out;
    const double cw = cellW_ > 0.0 ? cellW_ : 1.0;
    const double ch = cellH_ > 0.0 ? cellH_ : 1.0;
    const double stepX = cw + spacing_;
    const double stepY = ch + spacing_;
    const int cols = cw <= sheetW ? static_cast<int>(std::floor((sheetW - cw) / stepX + 1e-9)) + 1
                                  : 0;
    const int rows = ch <= sheetH ? static_cast<int>(std::floor((sheetH - ch) / stepY + 1e-9)) + 1
                                  : 0;
    int placed = 0;
    std::size_t next = 0;
    for (int r = 0; r < rows; ++r) {
        for (int c = 0; c < cols; ++c) {
            if (budget > 0 && placed >= budget) return out;
            // cycle through the orientations so that the cell holds every variant
            const Orientation& o = orientations_[next % orientations_.size()];
            ++next;
            PatternCell cell;
            cell.partIndex = partIndex_;
            cell.x = c * stepX;
            cell.y = r * stepY;
            cell.angle = o.angle;
            cell.flipped = o.flipped;
            cell.footprint = geom::Box{geom::FPoint{geom::toFixed(cell.x), geom::toFixed(cell.y)},
                                       geom::FPoint{geom::toFixed(cell.x + cw),
                                                    geom::toFixed(cell.y + ch)},
                                       true};
            out.push_back(cell);
            ++placed;
        }
    }
    return out;
}

// ---------------------------------------------------------------------------
namespace {
double usedArea(const std::vector<PatternCell>& cells) {
    double a = 0.0;
    for (const auto& c : cells) a += c.area();
    return a;
}
}  // namespace

LCNS_SUBSTITUTED(tiling.eval.density);
double DensityEvaluator::evaluate(const std::vector<PatternCell>& cells, double sheetArea) const {
    return sheetArea > 0.0 ? usedArea(cells) / sheetArea : 0.0;
}

LCNS_SUBSTITUTED(tiling.eval.unlimited_density);
double UnlimitedDensityEvaluator::evaluate(const std::vector<PatternCell>& cells,
                                          double sheetArea) const {
    (void)sheetArea;
    double a = 0.0, bx = 0.0, by = 0.0;
    for (const auto& c : cells) {
        a += c.area();
        bx = std::max(bx, geom::toDouble(c.footprint.max.x));
        by = std::max(by, geom::toDouble(c.footprint.max.y));
    }
    const double envelope = bx * by;
    return envelope > 0.0 ? a / envelope : 0.0;
}

LCNS_SUBSTITUTED(tiling.eval.unlimited_x_density);
double UnlimitedXDensityEvaluator::evaluate(const std::vector<PatternCell>& cells,
                                           double sheetArea) const {
    (void)sheetArea;
    double a = 0.0, bx = 0.0;
    for (const auto& c : cells) {
        a += c.area();
        bx = std::max(bx, geom::toDouble(c.footprint.max.x));
    }
    return bx > 0.0 ? a / bx : 0.0;
}

LCNS_SUBSTITUTED(tiling.eval.quantity);
double QuantityEvaluator::evaluate(const std::vector<PatternCell>& cells, double sheetArea) const {
    (void)sheetArea;
    return static_cast<double>(cells.size());
}

LCNS_SUBSTITUTED(tiling.eval.reusable);
double ReusableEvaluator::evaluate(const std::vector<PatternCell>& cells, double sheetArea) const {
    const double density = sheetArea > 0.0 ? usedArea(cells) / sheetArea : 0.0;
    // penalise patterns that leave no room for an offcut strip
    double maxY = 0.0;
    for (const auto& c : cells) maxY = std::max(maxY, geom::toDouble(c.footprint.max.y));
    const double leftover = sheetArea > 0.0 ? 1.0 - density : 0.0;
    return density + 0.25 * leftover;
}

LCNS_SUBSTITUTED(tiling.eval.oblique);
double ObliqueEvaluator::evaluate(const std::vector<PatternCell>& cells, double sheetArea) const {
    double score = 0.0;
    for (const auto& c : cells) {
        const double a = std::fmod(std::fabs(c.angle), 3.14159265358979323846);
        if (a > 1e-6) score += c.area();
    }
    return sheetArea > 0.0 ? score / sheetArea : 0.0;
}

LCNS_SUBSTITUTED(tiling.eval.multitorch);
double MultitorchEvaluator::evaluate(const std::vector<PatternCell>& cells, double sheetArea) const {
    if (cells.empty() || nbTorches_ <= 1) return 0.0;
    // count how many distinct torch lines the pattern uses; fewer lines means fewer
    // reconfigurations, which is what the original rewards
    std::vector<double> lines;
    for (const auto& c : cells) {
        const double y = geom::toDouble(c.footprint.min.y);
        bool found = false;
        for (double& v : lines) {
            if (std::fabs(v - y) < 1e-9) {
                found = true;
                break;
            }
        }
        if (!found) lines.push_back(y);
    }
    const double lineRatio = static_cast<double>(lines.size()) / static_cast<double>(cells.size());
    const double density = sheetArea > 0.0 ? usedArea(cells) / sheetArea : 0.0;
    return density * (1.0 - 0.5 * lineRatio);
}

// ---------------------------------------------------------------------------
std::vector<PatternCell> BoxMultiTiler::best(const std::vector<std::vector<PatternCell>>& candidates,
                                            double sheetArea, double* score) const {
    std::vector<PatternCell> bestCells;
    double bestScore = -1e300;
    for (const auto& cand : candidates) {
        double s = 0.0;
        if (evaluators_.empty()) {
            s = usedArea(cand);
        } else {
            for (const auto& e : evaluators_) s += e->evaluate(cand, sheetArea);
        }
        if (s > bestScore) {
            bestScore = s;
            bestCells = cand;
        }
    }
    if (score) *score = bestScore;
    return bestCells;
}

std::vector<PatternCell> SqueezeMultiTiler::squeeze(const std::vector<PatternCell>& cells,
                                                   double sheetW, double sheetH) const {
    (void)evaluators_;
    std::vector<PatternCell> out = cells;
    // compact each row towards x = 0 and each column towards y = 0, then clamp into the sheet
    for (auto& c : out) {
        const double w = geom::toDouble(c.footprint.max.x - c.footprint.min.x);
        const double h = geom::toDouble(c.footprint.max.y - c.footprint.min.y);
        if (c.x + w > sheetW) c.x = std::max(0.0, sheetW - w);
        if (c.y + h > sheetH) c.y = std::max(0.0, sheetH - h);
        c.footprint = geom::Box{geom::FPoint{geom::toFixed(c.x), geom::toFixed(c.y)},
                                geom::FPoint{geom::toFixed(c.x + w), geom::toFixed(c.y + h)}, true};
    }
    return out;
}

}  // namespace tiling
}  // namespace lcns
