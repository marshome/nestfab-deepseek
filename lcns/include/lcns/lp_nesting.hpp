// lcns/lp_nesting.hpp -- pricing subproblem driven by an actual nesting run.
//
// The reverse engineering could not prove that the recovered `Prc::PriceComputer` family
// implements Dantzig-Wolfe dual pricing (re/REPORT.md 7.3): its implementations return
// geometric surface measures (BoxSurface = a bounding box area, HullSurface / AlphaSurface =
// precomputed coefficients, LinearCombination = a weighted average). What it *did* prove is
// that the pricing layer is reachable from the nesting engine and that an LP wrapper over Clp
// exists. This header closes that loop in the most direct way available: the master problem is
// a set covering over patterns, and the pricing subproblem is a real nesting run whose value
// weights come from the master's dual prices.
#pragma once

#include "lcns/engine.hpp"
#include "lcns/lp.hpp"
#include "lcns/lp_column_generation.hpp"

namespace lcns {
namespace lp {

class NestingPatternPricer : public ColumnPricer {
public:
    explicit NestingPatternPricer(const Order& order, EngineParams params = {});

    const char* name() const override { return "NestingPatternPricer"; }

    // `partPrices` are the master's dual prices; a part with a high price is worth placing.
    // The multiplicity handed to the engine is derived from the price so that valuable parts
    // dominate the single sheet run.
    Pattern price(const std::vector<double>& partPrices, double sheetPrice,
                  double* reducedCost) const override;

    // runs made so far (diagnostics)
    int runs() const { return runs_; }

private:
    const Order& order_;
    EngineParams params_;
    mutable int runs_ = 0;
};

}  // namespace lp
}  // namespace lcns
