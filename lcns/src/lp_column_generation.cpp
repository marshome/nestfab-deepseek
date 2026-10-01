// lcns/lp_column_generation.cpp -- implementation of the reconstruction extension.
// Nothing here exists in libcns_dump_64.dll; see lp_column_generation.hpp.
#include "lcns/lp_column_generation.hpp"
#include "lcns/recovery.hpp"

#include <algorithm>
#include <cmath>

LCNS_NOT_IN_BINARY(lp.column_generation);
namespace lcns {
namespace lp {

// ---------------------------------------------------------------------------
MasterProblem::MasterProblem(std::vector<int> demand) : demand_(std::move(demand)) {}

int MasterProblem::addPattern(const Pattern& p) {
    patterns_.push_back(p);
    return static_cast<int>(patterns_.size()) - 1;
}

SimplexStatus MasterProblem::solve(int maxIterations) {
    Simplex s;
    s.reserve(0, patterns_.size());
    for (const auto& p : patterns_) s.addColumn(p.cost);

    for (std::size_t i = 0; i < demand_.size(); ++i) {
        std::vector<double> row(patterns_.size(), 0.0);
        for (std::size_t j = 0; j < patterns_.size(); ++j) {
            row[j] = i < patterns_[j].counts.size() ? static_cast<double>(patterns_[j].counts[i])
                                                    : 0.0;
        }
        s.addRow(row, RowSense::GreaterEqual, static_cast<double>(demand_[i]));
    }
    if (sheetLimit_ > 0) {
        std::vector<double> row(patterns_.size(), 1.0);
        s.addRow(row, RowSense::LessEqual, static_cast<double>(sheetLimit_));
    }

    const SimplexStatus st = !patterns_.empty() ? s.solve(maxIterations) : SimplexStatus::Infeasible;
    iterations_ = s.iterations();
    objective_ = s.objective();
    lambdas_ = s.primal();
    partPrices_.assign(demand_.size(), 0.0);
    for (std::size_t i = 0; i < demand_.size() && i < s.dual().size(); ++i) {
        partPrices_[i] = s.dual()[i];
    }
    sheetPrice_ = (sheetLimit_ > 0 && s.dual().size() > demand_.size())
                      ? s.dual()[demand_.size()]
                      : 0.0;
    simplex_ = std::move(s);
    return st;
}

int MasterProblem::sheetsUsed() const {
    double total = 0.0;
    for (std::size_t j = 0; j < lambdas_.size() && j < patterns_.size(); ++j) {
        total += lambdas_[j] * patterns_[j].sheets;
    }
    return static_cast<int>(std::ceil(total - 1e-9));
}

// ---------------------------------------------------------------------------
GreedyPricer::GreedyPricer(std::vector<double> partSizes, int sheetCount, double sheetCapacity)
    : sizes_(std::move(partSizes)), sheetCount_(sheetCount), capacity_(sheetCapacity) {
    (void)sheetCount_;
}

Pattern GreedyPricer::price(const std::vector<double>& partPrices, double sheetPrice,
                            double* reducedCost) const {
    Pattern p;
    p.counts.assign(sizes_.size(), 0);
    p.sheets = 1;
    p.cost = 1.0 + std::max(0.0, sheetPrice);

    double used = 0.0;
    bool progress = true;
    while (progress) {
        progress = false;
        std::size_t best = sizes_.size();
        double bestDensity = 1e-12;
        for (std::size_t i = 0; i < sizes_.size(); ++i) {
            if (i >= partPrices.size() || partPrices[i] <= 0.0) continue;
            if (sizes_[i] <= 0.0) continue;
            if (used + sizes_[i] > capacity_ + 1e-9) continue;
            const double density = partPrices[i] / sizes_[i];
            if (density > bestDensity) {
                bestDensity = density;
                best = i;
            }
        }
        if (best < sizes_.size()) {
            p.counts[best] += 1;
            used += sizes_[best];
            progress = true;
        }
    }
    if (reducedCost) {
        double value = 0.0;
        for (std::size_t i = 0; i < p.counts.size(); ++i) {
            value += static_cast<double>(p.counts[i]) * (i < partPrices.size() ? partPrices[i] : 0.0);
        }
        *reducedCost = p.cost - value;
    }
    return p;
}

// ---------------------------------------------------------------------------
ColumnGenerationResult columnGeneration(MasterProblem& master, const ColumnPricer& pricer,
                                        int maxIterations, double tolerance,
                                        std::size_t maxColumns) {
    ColumnGenerationResult res;
    // The master is a set covering LP: without any column it is infeasible by construction, so
    // the caller must seed at least one feasible pattern. Say so instead of looping.
    if (master.patternCount() == 0) {
        res.message = "master has no initial column; seed one feasible pattern first";
        return res;
    }
    for (int it = 0; it < maxIterations; ++it) {
        const SimplexStatus st = master.solve();
        res.iterations = it + 1;
        if (st != SimplexStatus::Optimal) {
            res.message = std::string("master not optimal: ") + toString(st);
            res.objective = master.objective();
            return res;
        }
        if (master.patternCount() >= maxColumns) {
            res.message = "column budget exhausted";
            break;
        }
        double rc = 0.0;
        const Pattern p = pricer.price(master.partPrices(), master.sheetPrice(), &rc);
        if (rc >= -tolerance) {
            res.optimal = true;
            break;
        }
        bool allZero = true;
        for (int c : p.counts) {
            if (c != 0) {
                allZero = false;
                break;
            }
        }
        if (allZero) {
            res.message = "pricer produced an empty column";
            break;
        }
        master.addPattern(p);
        ++res.columnsAdded;
    }

    master.solve();
    res.objective = master.objective();
    res.sheetsUsed = master.sheetsUsed();
    const auto& lambdas = master.lambdas();
    const auto& patterns = master.patterns();
    for (std::size_t j = 0; j < lambdas.size() && j < patterns.size(); ++j) {
        if (lambdas[j] > 1e-9) res.used.emplace_back(patterns[j], lambdas[j]);
    }
    if (res.message.empty()) res.message = res.optimal ? "optimal" : "iteration limit";
    return res;
}

}  // namespace lp
}  // namespace lcns
