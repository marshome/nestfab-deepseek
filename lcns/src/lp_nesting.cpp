// lcns/lp_nesting.cpp
#include "lcns/lp_nesting.hpp"

#include <algorithm>
#include <cmath>

namespace lcns {
namespace lp {

NestingPatternPricer::NestingPatternPricer(const Order& order, EngineParams params)
    : order_(order), params_(params) {}

Pattern NestingPatternPricer::price(const std::vector<double>& partPrices, double sheetPrice,
                                    double* reducedCost) const {
    ++runs_;

    // one sheet, multiplicities driven by the dual prices
    Order single;
    single.objective = order_.objective;
    single.origin = order_.origin;
    single.interpartGap = order_.interpartGap;
    single.multitorchAllowed = order_.multitorchAllowed;
    single.multitorchNbTorches = order_.multitorchNbTorches;
    single.multitorchMinDistance = order_.multitorchMinDistance;
    single.multitorchMaxDistance = order_.multitorchMaxDistance;
    single.parts = order_.parts;
    if (!order_.sheets.empty()) single.sheets.push_back(order_.sheets.front());

    double maxPrice = 0.0;
    for (double p : partPrices) maxPrice = std::max(maxPrice, p);

    int totalMultiplicity = 0;
    for (std::size_t i = 0; i < single.parts.size(); ++i) {
        const double price = i < partPrices.size() ? partPrices[i] : 0.0;
        int m = 1;
        if (maxPrice > 0.0 && price > 0.0) {
            // scale by relative value; at least one copy so the pattern is never empty
            m = std::max(1, static_cast<int>(std::lround(8.0 * price / maxPrice)));
        }
        single.parts[i].multiplicity = m;
        totalMultiplicity += m;
    }
    if (totalMultiplicity <= 0) totalMultiplicity = static_cast<int>(single.parts.size());

    EngineParams p = params_;
    p.timeLimitSeconds = std::min(2.0, std::max(0.2, params_.timeLimitSeconds));
    p.maxIterations = std::min(64, std::max(8, params_.maxIterations));
    p.beam.width = std::min(4, std::max(1, params_.beam.width));
    p.beam.maxAngleSteps = std::min(8, std::max(2, params_.beam.maxAngleSteps));
    p.compactAtEnd = false;
    p.finalizeBottomLeft = false;
    p.renestInHoles = false;

    Engine engine;
    const EngineResult r = engine.run(single, p);

    Pattern pattern;
    pattern.counts.assign(order_.parts.size(), 0);
    for (const auto& nesting : r.solution.nestings) {
        for (const auto& np : nesting.parts) {
            if (np.partIndex >= 0 && np.partIndex < static_cast<int>(pattern.counts.size())) {
                pattern.counts[static_cast<std::size_t>(np.partIndex)] += 1;
            }
        }
    }
    pattern.sheets = 1;
    pattern.cost = 1.0 + std::max(0.0, sheetPrice);

    if (reducedCost) {
        double value = 0.0;
        for (std::size_t i = 0; i < pattern.counts.size(); ++i) {
            value += static_cast<double>(pattern.counts[i]) *
                     (i < partPrices.size() ? partPrices[i] : 0.0);
        }
        *reducedCost = pattern.cost - value;
    }
    return pattern;
}

}  // namespace lp
}  // namespace lcns
