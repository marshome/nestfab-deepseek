// lcns/lp_column_generation.hpp -- NOT PART OF THE BINARY.
//
// The reverse engineering established that libcns_dump_64.dll has NO Dantzig-Wolfe master
// problem: `Prc::LinearCombinationPricer` is a weighted average of geometric surface measures
// driven from `..\nesting\algos\old_beam.cpp`, and the only real LP is the sheet selection
// covering problem built by `BuildAndSolveLp` (0x7D7200, ..\multi\database.cpp) which is
// mirrored in <lcns/lp.hpp> as `lp::buildAndSolveLp`.
//
// Everything in THIS header is a reconstruction extension: it was written to explore the
// column-generation reading of `Prc::PriceComputer` and is deliberately kept out of lp.hpp so
// that lp.hpp stays a faithful mirror. See re/findings_lp_use.md sections 3 and 9.
#pragma once

#include <cstddef>
#include <string>
#include <utility>
#include <vector>

#include "lcns/lp.hpp"

namespace lcns {
namespace lp {

// ---------------------------------------------------------------------------
// Set partitioning style master problem for nesting:
//   minimise    sum_p cost_p * lambda_p
//   subject to  sum_p count_{p,i} * lambda_p  >=  demand_i     for every part i
//               sum_p lambda_p                <=  nbSheets
//               lambda_p >= 0
// ---------------------------------------------------------------------------
struct Pattern {
    std::vector<int> counts;   // per part index
    double cost = 1.0;         // e.g. one sheet
    int sheets = 1;
};

class MasterProblem {
public:
    explicit MasterProblem(std::vector<int> demand);

    void setSheetLimit(int maxSheets) { sheetLimit_ = maxSheets; }
    int sheetLimit() const { return sheetLimit_; }
    const std::vector<int>& demand() const { return demand_; }

    int addPattern(const Pattern& p);          // returns the column index
    const std::vector<Pattern>& patterns() const { return patterns_; }
    std::size_t patternCount() const { return patterns_.size(); }

    SimplexStatus solve(int maxIterations = 4000);
    double objective() const { return objective_; }
    const std::vector<double>& partPrices() const { return partPrices_; }  // one per part
    double sheetPrice() const { return sheetPrice_; }
    const std::vector<double>& lambdas() const { return lambdas_; }
    int iterations() const { return iterations_; }

    // number of sheets implied by the current lambda solution, rounded up
    int sheetsUsed() const;

private:
    std::vector<int> demand_;
    int sheetLimit_ = 0;
    std::vector<Pattern> patterns_;
    Simplex simplex_;
    double objective_ = 0.0;
    std::vector<double> partPrices_;
    double sheetPrice_ = 0.0;
    std::vector<double> lambdas_;
    int iterations_ = 0;
    std::size_t built_ = 0;  // patterns already pushed into the simplex
};

// ---------------------------------------------------------------------------
// Pricing: given the master's dual prices, propose a column with negative reduced cost.
// Named ColumnPricer, not PriceComputer, to avoid clashing with the geometric
// lcns::PriceComputer (Prc::PriceComputer in the recovered code).
// ---------------------------------------------------------------------------
class ColumnPricer {
public:
    virtual ~ColumnPricer() = default;
    virtual const char* name() const = 0;
    // must return a pattern; `reducedCost` is filled with (cost - sum u_i*count_i + v)
    virtual Pattern price(const std::vector<double>& partPrices, double sheetPrice,
                          double* reducedCost) const = 0;
};

// Greedy knapsack style pricer over part "values" equal to their dual price.
class GreedyPricer : public ColumnPricer {
public:
    GreedyPricer(std::vector<double> partSizes, int sheetCount, double sheetCapacity);
    const char* name() const override { return "GreedyPricer"; }
    Pattern price(const std::vector<double>& partPrices, double sheetPrice,
                  double* reducedCost) const override;

private:
    std::vector<double> sizes_;
    int sheetCount_;
    double capacity_;
};

struct ColumnGenerationResult {
    double objective = 0.0;
    int iterations = 0;
    int columnsAdded = 0;
    int sheetsUsed = 0;
    bool optimal = false;
    std::vector<std::pair<Pattern, double>> used;   // pattern and its lambda
    std::string message;
};

// Runs the classic loop: solve master -> price -> add column while the reduced cost is
// below -tolerance and the column budget is not exhausted.
ColumnGenerationResult columnGeneration(MasterProblem& master, const ColumnPricer& pricer,
                                        int maxIterations = 50, double tolerance = 1e-7,
                                        std::size_t maxColumns = 4096);

}  // namespace lp
}  // namespace lcns
