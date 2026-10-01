// lcns/lp.cpp -- dense two phase primal simplex and a column generation driver.
#include "lcns/lp.hpp"
#include "lcns/recovery.hpp"

#include <algorithm>
#include <cmath>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <sstream>

LCNS_STRUCTURAL(module.lp);
namespace lcns {
namespace lp {
namespace {

constexpr double kTol = 1e-9;
constexpr double kInf = std::numeric_limits<double>::infinity();

// Set LCNS_LP_TRACE=1 in the environment to dump simplex iterations (development aid).
bool traceEnabled() {
    static const bool on = std::getenv("LCNS_LP_TRACE") != nullptr;
    return on;
}
void trace(const char* fmt, ...) {
    if (!traceEnabled()) return;
    va_list args;
    va_start(args, fmt);
    std::vfprintf(stderr, fmt, args);
    va_end(args);
}

// Standard form assembled from the user rows:
//   [ structural columns | one slack or (surplus + artificial) per row ]
// Rows are normalised so that the right hand side is non negative and every row has exactly
// one +1 column of its own, which makes the initial basis the identity matrix.
struct StandardForm {
    std::size_t rows = 0;
    std::size_t nStruct = 0;
    std::size_t total = 0;
    std::vector<std::vector<double>> a;      // rows x total
    std::vector<double> b;
    std::vector<double> c;                   // objective (structural only, extended)
    std::vector<char> isArtificial;
};

StandardForm build(const std::vector<std::vector<double>>& rowsA,
                   const std::vector<RowSense>& sense, const std::vector<double>& rhs,
                   const std::vector<double>& cost, std::size_t nStruct) {
    StandardForm sf;
    sf.rows = rowsA.size();
    sf.nStruct = nStruct;
    sf.a.assign(sf.rows, std::vector<double>(nStruct, 0.0));
    sf.b = rhs;
    sf.c.assign(nStruct, 0.0);
    // isArtificial is indexed by COLUMN index, so the structural columns need their entries
    // before any slack/surplus/artificial column is appended
    sf.isArtificial.assign(nStruct, 0);
    for (std::size_t i = 0; i < nStruct && i < cost.size(); ++i) sf.c[i] = cost[i];

    const auto pushColumn = [&sf](char artificial) {
        for (auto& row : sf.a) row.push_back(0.0);
        sf.c.push_back(0.0);
        sf.isArtificial.push_back(artificial);
        return sf.a.empty() ? std::size_t{0} : sf.a.front().size() - 1;
    };

    for (std::size_t r = 0; r < sf.rows; ++r) {
        for (std::size_t j = 0; j < nStruct; ++j) sf.a[r][j] = rowsA[r][j];
        RowSense s = sense[r];
        if (sf.b[r] < 0.0) {
            for (std::size_t j = 0; j < nStruct; ++j) sf.a[r][j] = -sf.a[r][j];
            sf.b[r] = -sf.b[r];
            if (s == RowSense::LessEqual) s = RowSense::GreaterEqual;
            else if (s == RowSense::GreaterEqual) s = RowSense::LessEqual;
        }
        if (s == RowSense::LessEqual) {
            const std::size_t col = pushColumn(0);
            sf.a[r][col] = 1.0;                     // slack
        } else {
            if (s == RowSense::GreaterEqual) {
                const std::size_t col = pushColumn(0);
                sf.a[r][col] = -1.0;                // surplus
            }
            const std::size_t art = pushColumn(1);
            sf.a[r][art] = 1.0;                     // artificial
        }
    }
    sf.total = sf.a.empty() ? nStruct : sf.a.front().size();
    return sf;
}

// Revised simplex with an explicit basis inverse so dual prices are available.
struct RevisedSimplex {
    const StandardForm& sf;
    std::vector<std::size_t> basis;
    std::vector<std::vector<double>> binv;
    std::vector<double> xb;
    std::vector<double> y;

    explicit RevisedSimplex(const StandardForm& form) : sf(form) {}

    void reset() {
        const std::size_t m = sf.rows;
        basis.assign(m, 0);
        binv.assign(m, std::vector<double>(m, 0.0));
        xb = sf.b;
        y.assign(m, 0.0);
        // the +1 column created for row r is its own basis column
        for (std::size_t r = 0; r < m; ++r) {
            std::size_t chosen = sf.total;
            for (std::size_t j = sf.nStruct; j < sf.total; ++j) {
                if (std::fabs(sf.a[r][j] - 1.0) < 1e-12) {
                    // prefer an artificial for rows that have one
                    if (sf.isArtificial[j]) {
                        chosen = j;
                        break;
                    }
                    if (chosen == sf.total) chosen = j;
                }
            }
            basis[r] = chosen;
            binv[r][r] = 1.0;
        }
    }

    void computeDuals(const std::vector<double>& cost) {
        const std::size_t m = sf.rows;
        y.assign(m, 0.0);
        for (std::size_t r = 0; r < m; ++r) {
            const double cb = cost[basis[r]];
            if (cb == 0.0) continue;
            for (std::size_t j = 0; j < m; ++j) y[j] += cb * binv[r][j];
        }
    }

    std::size_t selectEntering(const std::vector<double>& cost, std::vector<double>& d,
                               bool bland, bool skipArtificial = false) {
        computeDuals(cost);
        d.assign(sf.total, 0.0);
        std::size_t best = sf.total;
        double bestVal = -kTol;
        for (std::size_t j = 0; j < sf.total; ++j) {
            if (skipArtificial && sf.isArtificial[j]) continue;
            double ya = 0.0;
            for (std::size_t r = 0; r < sf.rows; ++r) ya += y[r] * sf.a[r][j];
            d[j] = cost[j] - ya;
            if (d[j] < -kTol) {
                if (bland) return j;
                if (d[j] < bestVal) {
                    bestVal = d[j];
                    best = j;
                }
            }
        }
        if (traceEnabled()) {
            std::fprintf(stderr, "[lp]   nStruct=%zu total=%zu basis:", sf.nStruct, sf.total);
            for (std::size_t r = 0; r < sf.rows; ++r) std::fprintf(stderr, " c%zu", basis[r]);
            std::fprintf(stderr, " | duals:");
            for (double v : y) std::fprintf(stderr, " %g", v);
            std::fprintf(stderr, " | rc:");
            for (std::size_t j = 0; j < sf.total; ++j) {
                std::fprintf(stderr, " c%zu=%g%s", j, d[j], sf.isArtificial[j] ? "(art)" : "");
            }
            std::fprintf(stderr, " | best=%zu\n", best);
        }
        return best;
    }

    // Pivot column `j` into row `r` unconditionally (used to drive a zero valued artificial
    // out of the basis after phase 1). Recomputes the basic values from B^-1 * b.
    bool pivotOn(std::size_t r, std::size_t j) {
        const std::size_t m = sf.rows;
        double u = 0.0;
        for (std::size_t k = 0; k < m; ++k) u += binv[r][k] * sf.a[k][j];
        if (std::fabs(u) < 1e-9) return false;
        for (std::size_t k = 0; k < m; ++k) binv[r][k] /= u;
        for (std::size_t rr = 0; rr < m; ++rr) {
            if (rr == r) continue;
            double f = 0.0;
            for (std::size_t k = 0; k < m; ++k) f += binv[rr][k] * sf.a[k][j];
            if (f == 0.0) continue;
            for (std::size_t k = 0; k < m; ++k) binv[rr][k] -= f * binv[r][k];
        }
        for (std::size_t rr = 0; rr < m; ++rr) {
            double sum = 0.0;
            for (std::size_t k = 0; k < m; ++k) sum += binv[rr][k] * sf.b[k];
            xb[rr] = sum;
        }
        basis[r] = j;
        return true;
    }

    bool pivot(std::size_t e, double& delta) {
        const std::size_t m = sf.rows;
        std::vector<double> u(m, 0.0);
        for (std::size_t r = 0; r < m; ++r) {
            double s = 0.0;
            for (std::size_t j = 0; j < m; ++j) s += binv[r][j] * sf.a[j][e];
            u[r] = s;
        }
        std::size_t leave = m;
        double bestRatio = kInf;
        for (std::size_t r = 0; r < m; ++r) {
            if (u[r] > kTol) {
                const double ratio = xb[r] / u[r];
                if (ratio < bestRatio - 1e-12) {
                    bestRatio = ratio;
                    leave = r;
                }
            }
        }
        if (leave == m) return false;  // unbounded
        delta = bestRatio;
        const double pivotVal = u[leave];
        for (std::size_t j = 0; j < m; ++j) binv[leave][j] /= pivotVal;
        for (std::size_t r = 0; r < m; ++r) {
            if (r == leave) continue;
            const double f = u[r];
            if (f == 0.0) continue;
            for (std::size_t j = 0; j < m; ++j) binv[r][j] -= f * binv[leave][j];
        }
        for (std::size_t r = 0; r < m; ++r) xb[r] -= bestRatio * u[r];
        xb[leave] = bestRatio;
        basis[leave] = e;
        return true;
    }

    bool hasArtificialInBasis() const {
        for (std::size_t r = 0; r < sf.rows; ++r) {
            if (sf.isArtificial[basis[r]]) return true;
        }
        return false;
    }
};

SimplexStatus runPhase(RevisedSimplex& rs, const std::vector<double>& cost, int maxIterations,
                       int& iterations, bool skipArtificial = false, const char* label = "") {
    std::vector<double> d;
    int stall = 0;
    const int blandAfter = static_cast<int>(rs.sf.rows) + 8;
    while (iterations < maxIterations) {
        const std::size_t e = rs.selectEntering(cost, d, stall > blandAfter, skipArtificial);
        if (e >= rs.sf.total) return SimplexStatus::Optimal;
        trace("[lp %s] enter col %zu rc=%g (stall %d)\n", label, e, d[e], stall);
        double delta = 0.0;
        if (!rs.pivot(e, delta)) return SimplexStatus::Unbounded;
        ++iterations;
        if (delta > 1e-11) {
            stall = 0;
        } else {
            ++stall;
        }
    }
    return SimplexStatus::IterationLimit;
}

}  // namespace

const char* toString(SimplexStatus s) {
    switch (s) {
        case SimplexStatus::Optimal: return "optimal";
        case SimplexStatus::Infeasible: return "infeasible";
        case SimplexStatus::Unbounded: return "unbounded";
        case SimplexStatus::IterationLimit: return "iteration-limit";
    }
    return "?";
}

// ---------------------------------------------------------------------------
LCNS_SUBSTITUTED(lp.simplex_fallback);
void Simplex::reserve(std::size_t rows, std::size_t cols) {
    // capacity only: columns are created by addColumn(), rows by addRow()
    a_.reserve(rows);
    b_.reserve(rows);
    sense_.reserve(rows);
    cost_.reserve(cols);
}

void Simplex::addRow(const std::vector<double>& coeffs, RowSense sense, double rhs) {
    std::vector<double> row(n_, 0.0);
    for (std::size_t j = 0; j < n_ && j < coeffs.size(); ++j) row[j] = coeffs[j];
    a_.push_back(std::move(row));
    sense_.push_back(sense);
    b_.push_back(rhs);
    ++m_;
}

int Simplex::addColumn(double c) {
    for (auto& row : a_) row.push_back(0.0);
    cost_.push_back(c);
    return static_cast<int>(n_++);
}

void Simplex::setCost(int column, double c) {
    if (column >= 0 && column < static_cast<int>(n_)) cost_[static_cast<std::size_t>(column)] = c;
}

SimplexStatus Simplex::solve(int maxIterations) {
    iterations_ = 0;
    primal_.assign(n_, 0.0);
    dual_.assign(m_, 0.0);
    objective_ = 0.0;

    for (double c : cost_) {
        if (c < -kTol && m_ == 0) return SimplexStatus::Unbounded;
    }
    if (m_ == 0) return SimplexStatus::Optimal;

    StandardForm sf = build(a_, sense_, b_, cost_, n_);
    RevisedSimplex rs(sf);
    rs.reset();

    // ---- phase 1 ----
    if (sf.rows > 0) {
        std::vector<double> c1(sf.total, 0.0);
        bool anyArtificial = false;
        for (std::size_t j = 0; j < sf.total; ++j) {
            if (sf.isArtificial[j]) {
                c1[j] = 1.0;
                anyArtificial = true;
            }
        }
        if (anyArtificial) {
            const SimplexStatus s1 = runPhase(rs, c1, maxIterations, iterations_, false, "p1");
            if (s1 == SimplexStatus::Unbounded) return SimplexStatus::Unbounded;
            double infeas = 0.0;
            for (std::size_t r = 0; r < sf.rows; ++r) {
                if (sf.isArtificial[rs.basis[r]]) infeas += rs.xb[r];
            }
            trace("[lp] phase1 infeas=%g rows=%zu total=%zu\n", infeas, sf.rows, sf.total);
            if (infeas > 1e-7) return SimplexStatus::Infeasible;

            // Drive any artificial that is still basic (at value zero) out of the basis.
            // Big-M is numerically fragile on degenerate rows, so this is done explicitly.
            for (std::size_t r = 0; r < sf.rows; ++r) {
                if (!sf.isArtificial[rs.basis[r]]) continue;
                bool driven = false;
                for (std::size_t j = 0; j < sf.total && !driven; ++j) {
                    if (sf.isArtificial[j]) continue;
                    bool basic = false;
                    for (std::size_t k = 0; k < sf.rows; ++k) {
                        if (rs.basis[k] == j) {
                            basic = true;
                            break;
                        }
                    }
                    if (basic) continue;
                    driven = rs.pivotOn(r, j);
                }
                // an all zero row is redundant; the artificial stays basic at zero with cost 0
            }
        }
    }

    // ---- phase 2: artificials keep cost 0 and can never re-enter ----
    std::vector<double> c2 = sf.c;
    c2.resize(sf.total, 0.0);
    const SimplexStatus s2 = runPhase(rs, c2, std::max(1, maxIterations - iterations_),
                                      iterations_, /*skipArtificial=*/true, "p2");
    trace("[lp] phase2 status=%s basis:", toString(s2));
    for (std::size_t r = 0; r < sf.rows; ++r) {
        trace(" [%zu]=c%zu xb=%g%s", r, rs.basis[r], rs.xb[r],
              sf.isArtificial[rs.basis[r]] ? "(art)" : "");
    }
    trace("\n");
    if (s2 == SimplexStatus::Unbounded) return SimplexStatus::Unbounded;

    rs.computeDuals(c2);
    dual_ = rs.y;
    for (std::size_t r = 0; r < sf.rows; ++r) {
        if (rs.basis[r] < n_) primal_[rs.basis[r]] = rs.xb[r];
    }
    for (std::size_t j = 0; j < n_; ++j) objective_ += cost_[j] * primal_[j];
    return s2 == SimplexStatus::IterationLimit ? SimplexStatus::IterationLimit
                                               : SimplexStatus::Optimal;
}

double Simplex::reducedCost(double c, const std::vector<double>& coeffs) const {
    double ya = 0.0;
    for (std::size_t r = 0; r < dual_.size() && r < coeffs.size(); ++r) ya += dual_[r] * coeffs[r];
    return c - ya;
}

// ---------------------------------------------------------------------------
// Lp::LinearProgram / Coin::CoinLP reconstruction (see include/lcns/lp.hpp).
namespace {

// Clp / COIN-OR spell "no bound" as +/-COIN_DBL_MAX.  Anything of that magnitude is treated as
// an infinite bound here too, so a caller that passes -DBL_MAX obtains a free column and a
// caller that passes +DBL_MAX obtains an unbounded-above one, as intended.
constexpr double kBigBound = 1e300;

bool lowerIsBounded(double v) { return v > -kBigBound; }
bool upperIsBounded(double v) { return v < kBigBound; }

LpStatus fromSimplex(SimplexStatus s) {
    switch (s) {
        case SimplexStatus::Optimal: return LpStatus::Optimal;
        case SimplexStatus::Infeasible: return LpStatus::Infeasible;
        case SimplexStatus::Unbounded: return LpStatus::Unbounded;
        case SimplexStatus::IterationLimit: return LpStatus::IterationLimit;
    }
    return LpStatus::Infeasible;
}

}  // namespace

const char* toString(LpStatus s) {
    switch (s) {
        case LpStatus::Optimal: return "optimal";
        case LpStatus::Infeasible: return "infeasible";
        case LpStatus::Unbounded: return "unbounded";
        case LpStatus::IterationLimit: return "iteration-limit";
    }
    return "?";
}

// ---- SimplexLinearProgram -------------------------------------------------
void SimplexLinearProgram::reset() {
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
}

void SimplexLinearProgram::addColumn(double cost, double lower, double upper) {
    // RE slot 4 (0x6792C0): one value into each of the three parallel double vectors.
    columnCost_.push_back(cost);
    columnLower_.push_back(lower);
    columnUpper_.push_back(upper);
    primal_.push_back(0.0);  // primal() stays sized before the first solve()
}

void SimplexLinearProgram::addRow(std::size_t n, const int* index, const double* value,
                                  double rhs) {
    // RE slot 5/6/7: the row's right hand side plus one 16 byte {value,row,column} triplet per
    // non zero coefficient.
    const int row = static_cast<int>(rowRhs_.size());
    rowRhs_.push_back(rhs);
    if (index != nullptr && value != nullptr) {
        coefficients_.reserve(coefficients_.size() + n);
        for (std::size_t k = 0; k < n; ++k) {
            Triplet t;
            t.value = value[k];
            t.row = row;
            t.column = index[k];
            coefficients_.push_back(t);
        }
    }
    dual_.push_back(0.0);  // dual() stays sized before the first solve()
}

// RE: the in-place sort 0x7CA830 performs on the +0x90 triplet vector. The key order is exactly
// the one 0x267A30 compares: int@+0xc (column) first, then int@+8 (row), then the double.
LCNS_RECOVERED(lp.canonicalise);
void SimplexLinearProgram::canonicalise() {
    std::stable_sort(coefficients_.begin(), coefficients_.end(),
                     [](const Triplet& a, const Triplet& b) {
                         if (a.column != b.column) return a.column < b.column;
                         if (a.row != b.row) return a.row < b.row;
                         return a.value < b.value;
                     });
}

int SimplexLinearProgram::solve() {
    canonicalise();   // RE: slot 8 calls 0x7CA830 before the solver is touched

    primal_.assign(columnCost_.size(), 0.0);
    dual_.assign(rowRhs_.size(), 0.0);
    objective_ = 0.0;
    droppedCoefficients_ = 0;

    // A column with an empty domain makes the whole program infeasible.
    for (std::size_t j = 0; j < columnCost_.size(); ++j) {
        const double lo = columnLower_[j];
        const double hi = columnUpper_[j];
        const bool empty = lo >= kBigBound ||
                           (lowerIsBounded(lo) && upperIsBounded(hi) && lo > hi + 1e-12);
        if (empty) {
            status_ = LpStatus::Infeasible;
            return static_cast<int>(status_);
        }
    }

    // Where each structural column ended up in the simplex: x_j = shift + z_plus [- z_minus].
    // z_minus is only used for a free (split) column.
    struct Placement {
        int plus = -1;
        int minus = -1;
        double shift = 0.0;
    };
    std::vector<Placement> place(columnCost_.size());

    Simplex simplex;
    simplex.reserve(rowRhs_.size() + columnCost_.size(), columnCost_.size() * 2);
    double constant = 0.0;
    for (std::size_t j = 0; j < columnCost_.size(); ++j) {
        const double cost = columnCost_[j];
        const double lo = columnLower_[j];
        Placement p;
        if (lowerIsBounded(lo)) {
            p.shift = lo;  // x_j = lo + z, z >= 0
            p.plus = simplex.addColumn(cost);
            constant += cost * p.shift;
        } else {
            p.plus = simplex.addColumn(cost);  // free column: x_j = z+ - z-
            p.minus = simplex.addColumn(-cost);
        }
        place[j] = p;
    }

    // Upper bounds: internal rows, filtered out of dual() below.
    for (std::size_t j = 0; j < columnCost_.size(); ++j) {
        const double hi = columnUpper_[j];
        if (!upperIsBounded(hi)) continue;
        const Placement& p = place[j];
        std::vector<double> row(simplex.columns(), 0.0);
        row[static_cast<std::size_t>(p.plus)] = 1.0;
        double rhs = hi - p.shift;
        if (p.minus >= 0) {
            row[static_cast<std::size_t>(p.minus)] = -1.0;  // z+ - z- <= upper
            rhs = hi;
        }
        simplex.addRow(row, RowSense::LessEqual, rhs);
    }
    const std::size_t firstStructural = simplex.rows();

    // Structural rows, adjusted for the lower bound shifts. The triplet list is column-major, so
    // gather the per-row terms with one pass instead of scanning it per row.
    std::vector<std::vector<std::pair<int, double>>> perRow(rowRhs_.size());
    for (const Triplet& t : coefficients_) {
        if (t.column < 0 || static_cast<std::size_t>(t.column) >= columnCost_.size()) {
            ++droppedCoefficients_;
            continue;
        }
        if (t.row < 0 || static_cast<std::size_t>(t.row) >= rowRhs_.size()) {
            ++droppedCoefficients_;
            continue;
        }
        perRow[static_cast<std::size_t>(t.row)].emplace_back(t.column, t.value);
    }
    for (std::size_t i = 0; i < rowRhs_.size(); ++i) {
        std::vector<double> row(simplex.columns(), 0.0);
        double rhs = rowRhs_[i];
        for (const auto& term : perRow[i]) {
            const Placement& p = place[static_cast<std::size_t>(term.first)];
            row[static_cast<std::size_t>(p.plus)] += term.second;
            if (p.minus >= 0) row[static_cast<std::size_t>(p.minus)] -= term.second;
            rhs -= term.second * p.shift;
        }
        simplex.addRow(row, RowSense::GreaterEqual, rhs);
    }

    status_ = fromSimplex(simplex.solve());

    const std::vector<double>& sp = simplex.primal();
    for (std::size_t j = 0; j < columnCost_.size(); ++j) {
        const Placement& p = place[j];
        double v = p.shift;
        if (p.plus >= 0 && static_cast<std::size_t>(p.plus) < sp.size()) {
            v += sp[static_cast<std::size_t>(p.plus)];
        }
        if (p.minus >= 0 && static_cast<std::size_t>(p.minus) < sp.size()) {
            v -= sp[static_cast<std::size_t>(p.minus)];
        }
        primal_[j] = v;
    }
    // The shifts removed `constant` from the objective; put it back so objective() describes
    // the user's variables, not the shifted ones.  (Only meaningful when solve() returned 0.)
    objective_ = simplex.objective() + constant;

    const std::vector<double>& sd = simplex.dual();
    for (std::size_t i = 0; i < rowRhs_.size(); ++i) {
        const std::size_t at = firstStructural + i;
        if (at < sd.size()) dual_[i] = sd[at];
    }
    return static_cast<int>(status_);
}

// ---- BuildAndSolveLp ------------------------------------------------------
LCNS_STRUCTURAL(lp.pricers);
LCNS_NOT_REVERSED(lp.column_generation_unproven);
SheetSelectionResult buildAndSolveLp(const std::vector<SheetContent>& sheets,
                                     const std::vector<int>& demand, LinearProgram& lp) {
    SheetSelectionResult res;

    lp.reset();  // slot 3

    // One column per sheet record, cost = sheet->price(), x_s >= 0 (the model states x_s >= 0;
    // the recovered CoinLP stashes the Clp "no bound" sentinels in its parallel bound vectors).
    for (const SheetContent& sheet : sheets) {
        lp.addColumn(sheet.price, 0.0, std::numeric_limits<double>::infinity());
    }

    // The invariant the binary asserts on: the "biggest" sheet must have a non zero price.
    for (const SheetContent& sheet : sheets) {
        res.biggestSheetPrice = std::max(res.biggestSheetPrice, sheet.price);
    }
    res.zeroPriceOnBiggestSheet = res.biggestSheetPrice == 0.0;

    // Cost of the slack column.  The binary shows only a unit coefficient and a hash-like column
    // index, so the price is a reconstruction choice: buying one more sheet of the cheapest kind
    // (1.0 when there is no sheet to price at all).
    double slackCost = 1.0;
    if (!sheets.empty()) {
        slackCost = sheets.front().price;
        for (const SheetContent& sheet : sheets) slackCost = std::min(slackCost, sheet.price);
    }

    // One row per part; columns are appended in order, so the next free column index is the
    // number of columns added so far.
    std::size_t nextColumn = sheets.size();
    for (std::size_t p = 0; p < demand.size(); ++p) {
        std::vector<int> index;
        std::vector<double> value;
        for (std::size_t s = 0; s < sheets.size(); ++s) {
            const double c = p < sheets[s].counts.size()
                                 ? static_cast<double>(sheets[s].counts[p])
                                 : 0.0;
            if (c != 0.0) {
                index.push_back(static_cast<int>(s));
                value.push_back(c);
            }
        }
        if (index.empty()) {
            // A part that appears on no sheet: give the row a unit coefficient slack column so
            // that the program stays feasible instead of being reported infeasible.
            lp.addColumn(slackCost, 0.0, std::numeric_limits<double>::infinity());
            index.push_back(static_cast<int>(nextColumn));
            value.push_back(1.0);
            ++nextColumn;
            ++res.slackColumns;
            res.insertedSlack = true;
        }
        lp.addRow(index.size(), index.data(), value.data(), static_cast<double>(demand[p]));
    }

    res.status = lp.solve();
    res.solved = res.status == 0;
    res.objective = lp.objective();
    res.values = lp.primal();
    res.duals = lp.dual();
    return res;
}

}  // namespace lp
}  // namespace lcns
