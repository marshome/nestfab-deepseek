// lcns/lp_clp.cpp -- LinearProgram on top of the REAL COIN-OR OsiClpSolverInterface.
//
// Built only when -DLCNS_WITH_CLP=ON and third_party/build-cmake/lib{clp,osi,coinutils}.a exist;
// see third_party/README.md for how those are produced (configure once for Clp's config header,
// then compile the sources with CMake because the autotools makefiles insist on re-running
// config.status --recheck and break on the space in "C:/Program Files/...").
#include "lcns/lp_clp.hpp"
#include "lcns/recovery.hpp"

#ifdef LCNS_HAS_CLP

#include <algorithm>
#include <cmath>
#include <limits>

#include "OsiClpSolverInterface.hpp"

LCNS_RECOVERED(lp.clp_backend);

namespace lcns {
namespace lp {

namespace {
constexpr double kInf = 1.0e30;   // Osi's "no bound" spelling in this stack
}

void ClpLinearProgram::reset() {
    columnCost_.clear();
    columnLower_.clear();
    columnUpper_.clear();
    rowRhs_.clear();
    coefficients_.clear();
    primal_.clear();
    dual_.clear();
    objective_ = 0.0;
    status_ = LpStatus::Optimal;
    droppedCoefficients_ = 0;
    iterations_ = 0;
}

void ClpLinearProgram::addColumn(double cost, double lower, double upper) {
    columnCost_.push_back(cost);
    columnLower_.push_back(lower);
    columnUpper_.push_back(upper);
}

void ClpLinearProgram::addRow(std::size_t n, const int* index, const double* value, double rhs) {
    const int row = static_cast<int>(rowRhs_.size());
    rowRhs_.push_back(rhs);
    for (std::size_t i = 0; i < n; ++i) {
        Triplet t;
        t.value = value[i];
        t.row = row;
        t.column = index[i];
        coefficients_.push_back(t);
    }
}

// RE 0x7CA830: std::sort over the 16 byte triplets by (column, row) before handing them to Clp.
void ClpLinearProgram::canonicalise() {
    std::sort(coefficients_.begin(), coefficients_.end(), [](const Triplet& a, const Triplet& b) {
        if (a.column != b.column) return a.column < b.column;
        return a.row < b.row;
    });
}

int ClpLinearProgram::solve() {
    primal_.clear();
    dual_.clear();
    objective_ = 0.0;
    iterations_ = 0;
    droppedCoefficients_ = 0;

    const int ncols = static_cast<int>(columnCost_.size());
    const int nrows = static_cast<int>(rowRhs_.size());

    // Reject (do not silently repair) an empty domain or an inverted row, exactly as the built in
    // backend documents for itself.
    for (int j = 0; j < ncols; ++j) {
        const double lo = columnLower_[static_cast<std::size_t>(j)];
        const double up = columnUpper_[static_cast<std::size_t>(j)];
        if (lo > up || lo >= kInf) {
            status_ = LpStatus::Infeasible;
            primal_.assign(static_cast<std::size_t>(ncols), 0.0);
            dual_.assign(static_cast<std::size_t>(nrows), 0.0);
            return static_cast<int>(status_);
        }
    }
    if (ncols == 0) {                      // nothing to optimise: the empty programme is optimal
        status_ = LpStatus::Optimal;
        objective_ = 0.0;
        dual_.assign(static_cast<std::size_t>(nrows), 0.0);
        return static_cast<int>(status_);
    }

    canonicalise();

    // Column major assembly straight from the canonical triplet list. The array form of
    // loadProblem is used on purpose: it takes exactly the column starts / row indices / values
    // shape the recovered sort produces, and it avoids CoinPackedMatrix's (old, easy to misuse)
    // construction API -- building the matrix column by column with an empty appendCol gave Clp a
    // model with no columns at all.
    std::vector<int> colStart(static_cast<std::size_t>(ncols) + 1, 0);
    std::vector<int> rowIndex;
    std::vector<double> element;
    rowIndex.reserve(coefficients_.size());
    element.reserve(coefficients_.size());
    std::size_t k = 0;
    for (int j = 0; j < ncols; ++j) {
        while (k < coefficients_.size() && coefficients_[k].column == j) {
            const Triplet& t = coefficients_[k];
            if (t.row >= 0 && t.row < nrows) {
                rowIndex.push_back(t.row);
                element.push_back(t.value);
            } else {
                ++droppedCoefficients_;
            }
            ++k;
        }
        colStart[static_cast<std::size_t>(j) + 1] = static_cast<int>(rowIndex.size());
    }
    // coefficients that address a column which never materialised
    for (; k < coefficients_.size(); ++k) ++droppedCoefficients_;

    std::vector<double> rowLower(static_cast<std::size_t>(nrows), 0.0);
    std::vector<double> rowUpper(static_cast<std::size_t>(nrows), kInf);
    for (int i = 0; i < nrows; ++i) rowLower[static_cast<std::size_t>(i)] = rowRhs_[static_cast<std::size_t>(i)];

    OsiClpSolverInterface si;
    si.setHintParam(OsiDoReducePrint, true, OsiHintDo);   // keep lcns' stdout clean
    si.messageHandler()->setLogLevel(0);
    si.loadProblem(ncols, nrows, colStart.data(), rowIndex.data(), element.data(),
                   columnLower_.data(), columnUpper_.data(), columnCost_.data(),
                   rowLower.data(), rowUpper.data());
    si.setObjSense(1.0);                                   // minimise
    si.initialSolve();

    const double* x = si.getColSolution();
    primal_.assign(x, x + ncols);
    const double* y = si.getRowPrice();
    dual_.assign(y, y + nrows);
    objective_ = si.getObjValue();
    iterations_ = si.getIterationCount();

    if (si.isProvenOptimal()) {
        status_ = LpStatus::Optimal;
    } else if (si.isProvenPrimalInfeasible()) {
        status_ = LpStatus::Infeasible;
    } else if (si.isProvenDualInfeasible()) {
        status_ = LpStatus::Unbounded;
    } else {
        status_ = LpStatus::IterationLimit;
    }
    return static_cast<int>(status_);
}

std::unique_ptr<LinearProgram> makeClpLinearProgram() {
    return std::unique_ptr<LinearProgram>(new ClpLinearProgram());
}

}  // namespace lp
}  // namespace lcns

#endif  // LCNS_HAS_CLP
