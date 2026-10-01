// lcns/lp.hpp -- a dense simplex and a column-generation loop.
//
// The reverse engineering found a real LP stack: `Lp::LinearProgram` <- `Coin::CoinLP`
// (wrapping ClpSimplex), the `Prc::PriceComputer` family and `Row::Distancer/Squeezer`, with
// COIN-OR Clp 1.15.3 statically linked. It also showed that the classes ARE constructed and
// reachable (`Multi::CompactNester::Run` is an ancestor of the pricer factory at 0x4D64C0),
// but it could NOT prove that a Dantzig-Wolfe master problem exists (re/REPORT.md 7.3).
//
// This header therefore provides an explicit, self contained implementation of the two
// pieces that make such an architecture meaningful: a primal simplex over the standard form
// min c'x s.t. Ax = b, x >= 0 (two phase, Bland's rule to avoid cycling, explicit B^-1 so
// dual prices are available), and a column-generation driver around it. The pricing
// subproblem is pluggable; `NestingPatternPricer` (lp_nesting.cpp) plugs an actual nesting run
// into it.
#pragma once

#include <cstddef>
#include <memory>
#include <string>
#include <vector>

namespace lcns {
namespace lp {

enum class RowSense { LessEqual, Equal, GreaterEqual };

enum class SimplexStatus { Optimal, Infeasible, Unbounded, IterationLimit };

const char* toString(SimplexStatus s);

// ---------------------------------------------------------------------------
// Dense two phase primal simplex.
//   variables x >= 0, rows of the form  a.x <= b   |   a.x = b   |   a.x >= b
// Dual prices for the rows come out of the final basis inverse: y = c_B * B^-1.
// ---------------------------------------------------------------------------
class Simplex {
public:
    Simplex() = default;

    void reserve(std::size_t rows, std::size_t cols);
    // adds a constraint row; `coeffs` is indexed by column
    void addRow(const std::vector<double>& coeffs, RowSense sense, double rhs);
    // adds a variable with its objective coefficient; returns its index
    int addColumn(double cost);
    void setCost(int column, double cost);

    std::size_t rows() const { return m_; }
    std::size_t columns() const { return n_; }

    SimplexStatus solve(int maxIterations = 4000);

    double objective() const { return objective_; }
    const std::vector<double>& primal() const { return primal_; }  // size == columns()
    const std::vector<double>& dual() const { return dual_; }      // size == rows()
    int iterations() const { return iterations_; }

    // reduced cost of a candidate column that is not (yet) in the problem: c - y.a
    double reducedCost(double cost, const std::vector<double>& coeffs) const;

private:
    std::size_t m_ = 0;                       // rows
    std::size_t n_ = 0;                       // structural columns
    std::vector<double> cost_;                // structural costs
    std::vector<std::vector<double>> a_;      // row major, structural columns
    std::vector<double> b_;
    std::vector<RowSense> sense_;

    double objective_ = 0.0;
    std::vector<double> primal_;
    std::vector<double> dual_;
    int iterations_ = 0;
};

// ---------------------------------------------------------------------------
// Lp::LinearProgram / Coin::CoinLP  (recovered hierarchy, see re/REPORT.md)
//
// The dump contains a real LP stack
//     Prc::PriceComputer     (abstract root)
//       Lp::LinearProgram    (abstract)
//         Coin::CoinLP       (wraps ClpSimplex; vptr at +0, ClpSimplex* at +8)
// CoinLP's vtable address point is 0xA3B280, so slot k lives at vptr + 8k:
//     slot 2            init/reinit (configures the solver)
//     slot 3  0x679660  reset: a 4 byte `mov [rcx+0x10], dl` flag setter
//     slot 4  0x6792C0  append ONE COLUMN (cost/lower/upper into parallel std::vector<double>
//                       members at +0x18/+0x30/+0x48, objective read through the solver vtable
//                       +0x220)
//     slot 5  0x679670  append ONE ROW (sparse indices + values + rhs into member vectors)
//     slot 6/7          further append/getters
//     slot 8  0x679D00  flush + solve (calls 0x7CA830, returns a status)
//     slot 9/10/11/12   forwarding thunks: solve / primal / dual / re-flush with a flag
//
// The recovered driver `BuildAndSolveLp` (0x7D7200, 1520 bytes, source path
// `..\multi\database.cpp`, assert `biggest_sheet->price()` at line 450) builds a *set covering
// / cutting stock sheet selection* LP, NOT a Dantzig-Wolfe pattern master problem:
//     minimise   sum_s price_s * x_s
//     s.t.       sum_s counts[s][p] * x_s >= demand[p]     for every part p
//                x_s >= 0
// One column per candidate sheet record, one row per part, plus a unit coefficient slack column
// whenever a part does not appear on any sheet.  `Database` (0x6A6AD0) consumes the result by
// reading slot 10 (the primal vector) and mapping it back onto the sheet records.
// ---------------------------------------------------------------------------
class LinearProgram {
public:
    virtual ~LinearProgram() = default;

    // slot 3 (0x679660): drop the accumulated model and any previous solution
    virtual void reset() = 0;
    // slot 4 (0x6792C0): append one column (objective cost and bounds)
    virtual void addColumn(double cost, double lower, double upper) = 0;
    // slot 5 (0x679670): append one ">=" row, given as a sparse (index, value) list and a rhs
    virtual void addRow(std::size_t n, const int* index, const double* value, double rhs) = 0;
    // slot 8 (0x679D00): flush the model into the solver, then solve; 0 == success
    virtual int solve() = 0;
    // slot 10: primal values, one per column that was added
    virtual const std::vector<double>& primal() const = 0;
    virtual double objective() const = 0;
    // slot 11: dual prices, one per row that was added
    virtual std::vector<double> dual() const = 0;
};

// Codes returned by LinearProgram::solve(); 0 (Optimal) is the only success code.
enum class LpStatus : int { Optimal = 0, Infeasible = 1, Unbounded = 2, IterationLimit = 3 };

const char* toString(LpStatus s);

// ---------------------------------------------------------------------------
// The interface implemented on top of the dense `Simplex` above.
//
// How column bounds are handled -- this is the one point the recovered CoinLP does not pin
// down, so here is exactly what happens (no bound is ever silently ignored):
//   * a finite lower bound `lo` is eliminated exactly by substitution x_j = lo + z_j with
//     z_j >= 0; the constant `sum_j cost_j * lo_j` is added back into objective();
//   * a lower bound of -infinity (or -COIN_DBL_MAX / -DBL_MAX, the Clp "no bound" spelling)
//     makes the column free and it is split exactly into x_j = z+ - z-, z+, z- >= 0;
//   * a finite upper bound becomes an explicit internal `<=` row (z_j <= hi - lo, or
//     z+ - z- <= hi for a free column);
//   * a lower bound of +COIN_DBL_MAX, or lower > upper, describes an empty domain: solve()
//     reports LpStatus::Infeasible instead of quietly dropping the bound.
// The upper bound rows are internal: dual() reports one price per *structural* row (in addRow
// order) and primal() one value per *structural* column, exactly as the callers expect.
// `Simplex` only knows x >= 0, so the model is stored here and flushed into a freshly built
// Simplex on every solve() -- which is what CoinLP slot 8 (flush + solve) does as well.
// ---------------------------------------------------------------------------
class SimplexLinearProgram : public LinearProgram {
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
    // Coefficients of addRow that addressed a column which does not exist at solve() time.
    // Such a coefficient cannot be represented and is dropped; the counter keeps that visible.
    std::size_t droppedCoefficients() const { return droppedCoefficients_; }

private:
    // The member layout below mirrors the recovered Coin::CoinLP object, taken from the write
    // offsets of its vtable slots:
    //   slot 4 (0x6792C0) writes [this+0x20] / [this+0x38] / [this+0x50], i.e. the END pointers
    //     of three std::vector<double> whose begin pointers are +0x18 / +0x30 / +0x48 -> the
    //     three per-column attributes (cost, lower, upper);
    //   slots 5/6/7 (0x679670 / 0x679940 / 0x679420) write the end pointers at +0x68 / +0x80 /
    //     +0x98, i.e. further vectors at +0x60 / +0x78 / +0x90, and slot 8's callee 0x7CA830
    //     opens by std::sort-ing the 16 byte elements of the vector at +0x90 IN PLACE;
    //   that element type is 16 bytes -- `double` at +0, `int` at +8, `int` at +0xc -- which is
    //     precisely what 0x267A30 (the std::sort instantiation) compares, as
    //     (int@+0xc, int@+8, double@+0).
    // The coefficient matrix is therefore kept as a COO triplet list ordered column-major, which
    // is what that sort produces and what Clp's CoinPackedMatrix consumes by default. Which of the
    // two ints is the row is inferred from that same order (column-major primary key = column).
    struct Triplet {
        double value = 0.0;   // [+0x00]
        int row = 0;          // [+0x08]  secondary sort key
        int column = 0;       // [+0x0c]  primary sort key
    };

    // Sorts the triplet list in place with the recovered key order (column, row, value); this is
    // what 0x7CA830 does to the +0x90 vector before anything is handed to the solver.
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
};

// ---------------------------------------------------------------------------
// Input and output of the recovered `BuildAndSolveLp`.
// ---------------------------------------------------------------------------
struct SheetContent {
    std::vector<int> counts;   // counts[p] = how many of part p this sheet yields
    double price = 0.0;        // sheet->price(); the LP cost of this column
};

struct SheetSelectionResult {
    bool solved = false;              // solve() returned 0 (optimal)
    int status = 0;                   // the raw LinearProgram::solve() code
    double objective = 0.0;           // minimum sum_s price_s * x_s
    std::vector<double> values;       // one per column: the sheets, then the slack columns
    std::vector<double> duals;        // one per part (one per ">=" row)
    bool insertedSlack = false;       // at least one part appears on no sheet
    int slackColumns = 0;             // how many unit coefficient slack columns were added
    // The binary asserts `biggest_sheet->price()` at `..\multi\database.cpp:450`; here the check
    // is *returned* instead of aborting.  "Biggest" = the largest `price` among `sheets` (the
    // sheet records carry no area in this model), so the flag is true when that price is 0
    // (including the vacuous case of an empty `sheets` vector).
    bool zeroPriceOnBiggestSheet = false;
    double biggestSheetPrice = 0.0;
};

// Faithful translation of `BuildAndSolveLp` (0x7D7200):
//     lp.reset();                                                  // slot 3
//     for (sheet : sheets) lp.addColumn(sheet.price, 0, +inf);      // slot 4, one col per sheet
//     for (p)   { gather counts[s][p] != 0; lp.addRow(..., demand[p]); }   // slot 5, one row/part
//     return lp.solve() == 0;                                       // slot 8, flush + solve
// When a part appears on no sheet at all, a slack column with coefficient 1.0 is appended and
// referenced by that row, so the program stays feasible; the slack costs the cheapest sheet
// price (1.0 when `sheets` is empty).  Columns are appended in order, so a column's index is the
// number of columns added before it -- the interface therefore needs no `columns()` getter.
SheetSelectionResult buildAndSolveLp(const std::vector<SheetContent>& sheets,
                                     const std::vector<int>& demand, LinearProgram& lp);

}  // namespace lp
}  // namespace lcns
