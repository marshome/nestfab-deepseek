// lcns/lp_clp.hpp -- the REAL COIN-OR backend: OsiClpSolverInterface, downloaded and linked.
//
// Human instruction (goal round 2): a third party library must be DOWNLOADED AND LINKED, not
// reverse engineered. The dump proves the original statically links COIN-OR Clp through
// OsiClpSolverInterface (see third_party/README.md section 1), so this backend drives exactly that
// interface instead of the hand written `Simplex` substitute.
//
// It implements the recovered `Lp::LinearProgram` / `Coin::CoinLP` contract (re/REPORT.md 7.3):
//     reset()                          slot 3, 0x679660
//     addColumn(cost, lower, upper)    slot 4, 0x6792C0
//     addRow(n, index, value, rhs)     slot 5, 0x679670
//     solve()                          slot 8, 0x679D00 (flush + solve)
//     primal() / dual()                slots 10 / 11
// and keeps the same storage shape the binary uses: three parallel per-column vectors, one per-row
// rhs vector, and a 16 byte (value, row, column) triplet list that is sorted in place, column
// major, before anything reaches the solver -- that in place sort is 0x7CA830.
#pragma once

#include <cstddef>
#include <memory>
#include <vector>

#include "lcns/lp.hpp"

namespace lcns {
namespace lp {

// True when this build links the COIN-OR archives built by third_party/CMakeLists.txt.
#ifdef LCNS_HAS_CLP
class ClpLinearProgram : public LinearProgram {
public:
    void reset() override;
    void addColumn(double cost, double lower, double upper) override;
    void addRow(std::size_t n, const int* index, const double* value, double rhs) override;
    int solve() override;

    const std::vector<double>& primal() const override { return primal_; }
    double objective() const override { return objective_; }
    std::vector<double> dual() const override { return dual_; }

    std::size_t columns() const { return columnCost_.size(); }
    std::size_t rows() const { return rowRhs_.size(); }
    LpStatus status() const { return status_; }
    // Coefficients dropped because they addressed a column that does not exist. Kept visible
    // instead of silently ignored (the same diagnostic SimplexLinearProgram exposes).
    std::size_t droppedCoefficients() const { return droppedCoefficients_; }
    // Iterations reported by Clp (0 when the model was rejected before it got there).
    int iterations() const { return iterations_; }

private:
    struct Triplet {
        double value = 0.0;   // [+0x00]
        int row = 0;          // [+0x08]
        int column = 0;       // [+0x0c]  primary sort key (column major), as 0x7CA830 sorts
    };
    void canonicalise();

    std::vector<double> columnCost_;     // RE +0x18
    std::vector<double> columnLower_;    // RE +0x30
    std::vector<double> columnUpper_;    // RE +0x48
    std::vector<double> rowRhs_;         // RE +0x60
    std::vector<Triplet> coefficients_;  // RE +0x90

    std::vector<double> primal_;
    std::vector<double> dual_;
    double objective_ = 0.0;
    LpStatus status_ = LpStatus::Optimal;
    std::size_t droppedCoefficients_ = 0;
    int iterations_ = 0;
};

// Convenience factory so callers do not need the concrete type.
std::unique_ptr<LinearProgram> makeClpLinearProgram();
#endif  // LCNS_HAS_CLP

}  // namespace lp
}  // namespace lcns
