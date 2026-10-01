// tests/test_linear_program.cpp -- the recovered Lp::LinearProgram / Coin::CoinLP layer and the
// sheet selection LP that `BuildAndSolveLp` (0x7D7200, ..\multi\database.cpp:450) drives:
//
//     minimise   sum_s price_s * x_s
//     s.t.       sum_s counts[s][p] * x_s >= demand[p]      for every part p
//                x_s >= 0
#include "check.hpp"
#include "lcns/lp.hpp"
#include "lcns/lp_clp.hpp"

#include <limits>
#include <memory>
#include <string>
#include <vector>

using namespace lcns;
using namespace lcns::lp;

namespace {

constexpr double kInf = std::numeric_limits<double>::infinity();

// A LinearProgram that only records the calls, used to check the recovered call sequence of
// BuildAndSolveLp independently of the simplex.
class RecordingLp : public LinearProgram {
public:
    struct Column {
        double cost = 0.0;
        double lower = 0.0;
        double upper = 0.0;
    };
    struct Row {
        std::vector<int> index;
        std::vector<double> value;
        double rhs = 0.0;
    };

    void reset() override {
        ++resets;
        columns.clear();
        rows.clear();
    }
    void addColumn(double cost, double lower, double upper) override {
        Column c;
        c.cost = cost;
        c.lower = lower;
        c.upper = upper;
        columns.push_back(c);
    }
    void addRow(std::size_t n, const int* index, const double* value, double rhs) override {
        Row r;
        r.rhs = rhs;
        for (std::size_t i = 0; i < n; ++i) {
            r.index.push_back(index[i]);
            r.value.push_back(value[i]);
        }
        rows.push_back(r);
    }
    int solve() override {
        ++solves;
        primalValue.assign(columns.size(), 0.0);
        dualValue.assign(rows.size(), 0.0);
        return result;
    }
    const std::vector<double>& primal() const override { return primalValue; }
    double objective() const override { return objectiveValue; }
    std::vector<double> dual() const override { return dualValue; }

    int resets = 0;
    int solves = 0;
    int result = 0;
    double objectiveValue = 0.0;
    std::vector<Column> columns;
    std::vector<Row> rows;
    std::vector<double> primalValue;
    std::vector<double> dualValue;
};

}  // namespace

int main() {
    CHECK(std::string(toString(LpStatus::Optimal)) == "optimal");
    CHECK(std::string(toString(LpStatus::Infeasible)) == "infeasible");
    CHECK(static_cast<int>(LpStatus::Optimal) == 0);   // solve() == 0 is the only success code

    // --- 1 part / 1 sheet, hand-checkable optimum -----------------------------
    {
        // min 2x s.t. 3x >= 6  ->  x = 2 sheets, cost 4, part price 2/3
        std::vector<SheetContent> sheets(1);
        sheets[0].counts = {3};
        sheets[0].price = 2.0;

        SimplexLinearProgram lp;
        const SheetSelectionResult r = buildAndSolveLp(sheets, {6}, lp);
        CHECK(r.solved);
        CHECK(r.status == static_cast<int>(LpStatus::Optimal));
        CHECK_NEAR(r.objective, 4.0, 1e-9);
        CHECK(r.values.size() == 1u);
        CHECK_NEAR(r.values[0], 2.0, 1e-9);
        CHECK(r.duals.size() == 1u);
        CHECK_NEAR(r.duals[0], 2.0 / 3.0, 1e-9);
        CHECK(!r.insertedSlack);
        CHECK(r.slackColumns == 0);
        CHECK(!r.zeroPriceOnBiggestSheet);
        CHECK_NEAR(r.biggestSheetPrice, 2.0, 1e-12);
        // the program itself agrees
        CHECK(lp.columns() == 1u);
        CHECK(lp.rows() == 1u);
        CHECK(lp.primal().size() == lp.columns());
        CHECK_NEAR(lp.objective(), 4.0, 1e-9);
        CHECK_NEAR(lp.primal()[0], 2.0, 1e-9);
    }

    // --- the classic case: two sheets must both be used -----------------------
    {
        // sheet A carries part 0, sheet B carries part 1; demand (2, 1)
        std::vector<SheetContent> sheets(2);
        sheets[0].counts = {1, 0};
        sheets[0].price = 1.0;
        sheets[1].counts = {0, 1};
        sheets[1].price = 1.0;

        SimplexLinearProgram lp;
        const SheetSelectionResult r = buildAndSolveLp(sheets, {2, 1}, lp);
        CHECK(r.solved);
        CHECK_NEAR(r.objective, 3.0, 1e-9);
        CHECK(r.values.size() == 2u);
        CHECK_NEAR(r.values[0], 2.0, 1e-9);
        CHECK_NEAR(r.values[1], 1.0, 1e-9);
        // both rows are tight here, so both prices are 1
        CHECK(r.duals.size() == 2u);
        CHECK_NEAR(r.duals[0], 1.0, 1e-9);
        CHECK_NEAR(r.duals[1], 1.0, 1e-9);
        CHECK(!r.insertedSlack);
    }

    // --- ">=" rows: over covering is allowed and the cheapest cover wins -------
    {
        // demand (1, 2): part 1 needs two of sheet A, and then part 0 is over covered (2 >= 1)
        std::vector<SheetContent> sheets(2);
        sheets[0].counts = {1, 1};
        sheets[0].price = 1.0;
        sheets[1].counts = {1, 0};
        sheets[1].price = 10.0;              // covering part 1 with B is hopeless

        SimplexLinearProgram lp;
        const SheetSelectionResult r = buildAndSolveLp(sheets, {1, 2}, lp);
        CHECK(r.solved);
        CHECK_NEAR(r.objective, 2.0, 1e-9);   // 2 sheets of A, not 1 A + 1 B (11)
        CHECK(r.values.size() == 2u);
        CHECK_NEAR(r.values[0], 2.0, 1e-9);
        CHECK_NEAR(r.values[1], 0.0, 1e-9);
        // the over covered row has a zero price, the binding one a price of 1
        CHECK_NEAR(r.duals[0], 0.0, 1e-7);
        CHECK_NEAR(r.duals[1], 1.0, 1e-7);
    }

    // --- a part that appears on no sheet: the slack column keeps it feasible ---
    {
        // part 1 is on no sheet; demand (3, 2) -> x_sheet = 3 and x_slack = 2
        std::vector<SheetContent> sheets(1);
        sheets[0].counts = {1, 0};
        sheets[0].price = 2.0;

        SimplexLinearProgram lp;
        const SheetSelectionResult r = buildAndSolveLp(sheets, {3, 2}, lp);
        CHECK(r.solved);
        CHECK(r.insertedSlack);
        CHECK(r.slackColumns == 1);
        CHECK(lp.columns() == 2u);            // one sheet column + one slack column
        CHECK(lp.rows() == 2u);
        CHECK(r.values.size() == 2u);         // primal() covers the slack column too
        CHECK_NEAR(r.values[0], 3.0, 1e-9);
        CHECK_NEAR(r.values[1], 2.0, 1e-9);   // the unit coefficient slack supplies demand 2
        // slack costs the cheapest sheet price (2.0): 3 * 2 + 2 * 2
        CHECK_NEAR(r.objective, 10.0, 1e-9);
        CHECK(r.objective > 0.0);
        CHECK(r.duals.size() == 2u);
        CHECK_NEAR(r.duals[0], 2.0, 1e-9);
        CHECK_NEAR(r.duals[1], 2.0, 1e-9);
    }
    {
        // no sheet at all: every part gets its own slack column (fallback cost 1.0)
        const std::vector<SheetContent> none;
        SimplexLinearProgram lp;
        const SheetSelectionResult r = buildAndSolveLp(none, {2, 3}, lp);
        CHECK(r.solved);
        CHECK(r.insertedSlack);
        CHECK(r.slackColumns == 2);
        CHECK(lp.columns() == 2u);
        CHECK(r.values.size() == 2u);
        CHECK_NEAR(r.values[0], 2.0, 1e-9);
        CHECK_NEAR(r.values[1], 3.0, 1e-9);
        CHECK_NEAR(r.objective, 5.0, 1e-9);
        CHECK(r.objective > 0.0);
        CHECK(r.zeroPriceOnBiggestSheet);     // vacuous: there is no sheet with a price
    }

    // --- prices matter: the cheaper of two equivalent sheets is selected ------
    {
        std::vector<SheetContent> sheets(2);
        sheets[0].counts = {1};
        sheets[0].price = 5.0;
        sheets[1].counts = {1};
        sheets[1].price = 2.0;

        SimplexLinearProgram lp;
        const SheetSelectionResult r = buildAndSolveLp(sheets, {1}, lp);
        CHECK(r.solved);
        CHECK(r.values.size() == 2u);
        CHECK_NEAR(r.values[0], 0.0, 1e-9);   // the expensive sheet stays at zero
        CHECK_NEAR(r.values[1], 1.0, 1e-9);   // the cheap one carries the demand
        CHECK_NEAR(r.objective, 2.0, 1e-9);
        // both columns are still priced correctly
        CHECK_NEAR(r.duals[0], 2.0, 1e-9);
    }

    // --- sizes and dual signs for a many column program ----------------------
    {
        // 3 sheets, 2 parts, no slack: primal() must have one entry per column
        std::vector<SheetContent> sheets(3);
        sheets[0].counts = {4, 1};
        sheets[0].price = 1.0;
        sheets[1].counts = {2, 2};
        sheets[1].price = 1.5;
        sheets[2].counts = {0, 5};
        sheets[2].price = 2.0;

        SimplexLinearProgram lp;
        const SheetSelectionResult r = buildAndSolveLp(sheets, {7, 4}, lp);
        CHECK(r.solved);
        CHECK(r.values.size() == 3u);
        CHECK(lp.primal().size() == lp.columns());
        CHECK(r.duals.size() == 2u);
        CHECK(lp.dual().size() == lp.rows());
        for (double y : r.duals) CHECK_MSG(y >= -1e-9, "duals of >= rows must be non negative");
        // the solution must actually cover the demand
        double cover0 = 0.0;
        double cover1 = 0.0;
        for (std::size_t s = 0; s < sheets.size(); ++s) {
            cover0 += sheets[s].counts[0] * r.values[s];
            cover1 += sheets[s].counts[1] * r.values[s];
        }
        CHECK(cover0 >= 7.0 - 1e-7);
        CHECK(cover1 >= 4.0 - 1e-7);
        CHECK_NEAR(r.objective, 1.0 * r.values[0] + 1.5 * r.values[1] + 2.0 * r.values[2], 1e-9);
    }

    // --- the invariant the binary asserts on (database.cpp:450) ---------------
    {
        std::vector<SheetContent> zero(1);
        zero[0].counts = {1};
        zero[0].price = 0.0;
        SimplexLinearProgram lp;
        const SheetSelectionResult r = buildAndSolveLp(zero, {1}, lp);
        CHECK(r.solved);
        CHECK(r.zeroPriceOnBiggestSheet);     // biggest_sheet->price() == 0 in the original
        CHECK_NEAR(r.biggestSheetPrice, 0.0, 1e-12);
        CHECK_NEAR(r.objective, 0.0, 1e-12);

        std::vector<SheetContent> mixed(2);
        mixed[0].counts = {1};
        mixed[0].price = 0.0;
        mixed[1].counts = {1};
        mixed[1].price = 3.0;
        SimplexLinearProgram lp2;
        const SheetSelectionResult r2 = buildAndSolveLp(mixed, {1}, lp2);
        CHECK(!r2.zeroPriceOnBiggestSheet);
        CHECK_NEAR(r2.biggestSheetPrice, 3.0, 1e-12);
        CHECK_NEAR(r2.objective, 0.0, 1e-12);  // the free sheet covers the demand
    }

    // --- the recovered call sequence, recorded against the interface ----------
    {
        // 3 sheet records, 2 parts, one sheet covers nothing at all
        std::vector<SheetContent> sheets(3);
        sheets[0].counts = {2, 0};
        sheets[0].price = 1.5;
        sheets[1].counts = {0, 3};
        sheets[1].price = 2.5;
        sheets[2].counts = {0, 0};
        sheets[2].price = 0.5;

        RecordingLp lp;
        lp.objectiveValue = 7.25;
        const SheetSelectionResult r = buildAndSolveLp(sheets, {4, 6}, lp);

        CHECK(lp.resets == 1);                // slot 3 once, before anything is appended
        CHECK(lp.solves == 1);                // slot 8 once, after the model is complete
        CHECK(lp.columns.size() == 3u);       // slot 4: one column per sheet record
        CHECK_NEAR(lp.columns[0].cost, 1.5, 1e-12);
        CHECK_NEAR(lp.columns[1].cost, 2.5, 1e-12);
        CHECK_NEAR(lp.columns[2].cost, 0.5, 1e-12);
        for (const RecordingLp::Column& c : lp.columns) {
            CHECK_NEAR(c.lower, 0.0, 1e-12);  // x_s >= 0
            CHECK(c.upper > 1e300);           // effectively unbounded above
        }
        CHECK(lp.rows.size() == 2u);          // slot 5: one row per part
        CHECK_NEAR(lp.rows[0].rhs, 4.0, 1e-12);
        CHECK_NEAR(lp.rows[1].rhs, 6.0, 1e-12);
        CHECK(lp.rows[0].index.size() == 1u); // only sheet 0 carries part 0
        CHECK(lp.rows[0].index[0] == 0);
        CHECK_NEAR(lp.rows[0].value[0], 2.0, 1e-12);
        CHECK(lp.rows[1].index.size() == 1u); // only sheet 1 carries part 1
        CHECK(lp.rows[1].index[0] == 1);
        CHECK_NEAR(lp.rows[1].value[0], 3.0, 1e-12);
        CHECK(!r.insertedSlack);              // every part is covered, so no slack column
        CHECK(r.solved);
        CHECK_NEAR(r.objective, 7.25, 1e-12);
        CHECK(r.values.size() == 3u);
        CHECK(r.duals.size() == 2u);
    }
    {
        // the same, with a part that appears on no sheet: the slack column is appended and
        // referenced with a unit coefficient by that part's row
        std::vector<SheetContent> sheets(1);
        sheets[0].counts = {1};
        sheets[0].price = 3.0;

        RecordingLp lp;
        const SheetSelectionResult r = buildAndSolveLp(sheets, {2, 5}, lp);
        CHECK(lp.columns.size() == 2u);       // sheet column 0 + slack column 1
        CHECK_NEAR(lp.columns[1].cost, 3.0, 1e-12);   // cheapest sheet price
        CHECK(lp.rows.size() == 2u);
        CHECK(lp.rows[0].index.size() == 1u);
        CHECK(lp.rows[0].index[0] == 0);
        CHECK(lp.rows[1].index.size() == 1u);
        CHECK(lp.rows[1].index[0] == 1);      // the slack column
        CHECK_NEAR(lp.rows[1].value[0], 1.0, 1e-12);
        CHECK(r.insertedSlack);
        CHECK(r.slackColumns == 1);
        CHECK(r.values.size() == 2u);
    }

    // --- SimplexLinearProgram: bounds, reset and diagnostics ------------------
    {
        // min -x with 0 <= x <= 3 -> x = 3 (the upper bound is a real constraint)
        SimplexLinearProgram lp;
        lp.addColumn(-1.0, 0.0, 3.0);
        CHECK(lp.solve() == static_cast<int>(LpStatus::Optimal));
        CHECK(lp.status() == LpStatus::Optimal);
        CHECK_NEAR(lp.primal()[0], 3.0, 1e-9);
        CHECK_NEAR(lp.objective(), -3.0, 1e-9);
    }
    {
        // min x with 1 <= x <= 4 -> x = 1: the finite lower bound is honoured exactly
        SimplexLinearProgram lp;
        lp.addColumn(1.0, 1.0, 4.0);
        CHECK(lp.solve() == 0);
        CHECK_NEAR(lp.primal()[0], 1.0, 1e-9);
        CHECK_NEAR(lp.objective(), 1.0, 1e-9);
    }
    {
        // min x with x >= 2 and no upper bound -> x = 2
        SimplexLinearProgram lp;
        lp.addColumn(1.0, 2.0, kInf);
        CHECK(lp.solve() == 0);
        CHECK_NEAR(lp.primal()[0], 2.0, 1e-9);
        CHECK_NEAR(lp.objective(), 2.0, 1e-9);
    }
    {
        // a free column (lower bound at -infinity) is split, not clamped: min x s.t. x >= -3
        SimplexLinearProgram lp;
        lp.addColumn(1.0, -kInf, kInf);
        const int index[1] = {0};
        const double value[1] = {1.0};
        lp.addRow(1, index, value, -3.0);
        CHECK(lp.solve() == 0);
        CHECK_NEAR(lp.primal()[0], -3.0, 1e-9);
        CHECK_NEAR(lp.objective(), -3.0, 1e-9);
        CHECK(lp.dual().size() == lp.rows());   // the internal split columns stay hidden
    }
    {
        // an empty column domain is reported, never silently dropped
        SimplexLinearProgram lp;
        lp.addColumn(1.0, 5.0, 2.0);
        CHECK(lp.solve() == static_cast<int>(LpStatus::Infeasible));
        CHECK(lp.status() == LpStatus::Infeasible);
        CHECK(lp.primal().size() == 1u);
    }
    {
        // reset() drops the model, the solution and the diagnostics
        SimplexLinearProgram lp;
        lp.addColumn(1.0, 0.0, kInf);
        const int index[1] = {0};
        const double value[1] = {1.0};
        lp.addRow(1, index, value, 4.0);
        CHECK(lp.solve() == 0);
        CHECK_NEAR(lp.objective(), 4.0, 1e-9);
        CHECK(lp.columns() == 1u);
        CHECK(lp.rows() == 1u);

        lp.reset();
        CHECK(lp.columns() == 0u);
        CHECK(lp.rows() == 0u);
        CHECK(lp.primal().empty());
        CHECK(lp.dual().empty());
        CHECK_NEAR(lp.objective(), 0.0, 1e-12);
    }
    {
        // a coefficient that addresses a column which does not exist is counted, not ignored
        SimplexLinearProgram lp;
        lp.addColumn(1.0, 0.0, kInf);
        const int index[2] = {0, 7};
        const double value[2] = {1.0, 1.0};
        lp.addRow(2, index, value, 1.0);
        CHECK(lp.solve() == 0);
        CHECK(lp.droppedCoefficients() == 1u);
        CHECK_NEAR(lp.objective(), 1.0, 1e-9);
    }
    {
        // columns may be added after rows; the row coefficient addresses the column by index
        SimplexLinearProgram lp;
        const int index[1] = {0};
        const double value[1] = {1.0};
        lp.addRow(1, index, value, 2.0);
        lp.addColumn(3.0, 0.0, kInf);
        CHECK(lp.solve() == 0);
        CHECK_NEAR(lp.objective(), 6.0, 1e-9);
    }

#ifdef LCNS_HAS_CLP
    // ---------------------------------------------------------------------------------------
    // The REAL COIN-OR backend (OsiClpSolverInterface, downloaded and linked -- see
    // third_party/README.md) must agree with the built in Simplex on the same models.
    // This is the test that makes "the LP layer is the original one" checkable rather than
    // a claim: both backends go through the SAME recovered driver `buildAndSolveLp` (0x7D7200).
    // ---------------------------------------------------------------------------------------
    {
        // All three sheets cost 1.0 here, so the optimum is DEGENERATE: (2,0,1) and (0,1,2) both
        // cover the demand at objective 3. Comparing primal vertices across two different solvers
        // would therefore be wrong; what must agree is the objective and the dual prices, and each
        // backend's own answer must be feasible and hit its objective.
        const std::vector<SheetContent> sheets = {
            {{1, 1}, 1.0}, {{2, 0}, 1.0}, {{0, 2}, 1.0}};
        const std::vector<int> demand = {2, 4};

        SimplexLinearProgram builtin;
        const SheetSelectionResult a = buildAndSolveLp(sheets, demand, builtin);

        ClpLinearProgram real;
        const SheetSelectionResult b = buildAndSolveLp(sheets, demand, real);

        CHECK(a.solved);
        CHECK(b.solved);
        CHECK_NEAR(a.objective, b.objective, 1e-7);
        CHECK_NEAR(a.objective, 3.0, 1e-7);
        CHECK(a.duals.size() == b.duals.size());
        CHECK(b.values.size() == sheets.size() + static_cast<std::size_t>(b.slackColumns));

        // each backend's primal must satisfy the demand rows ...
        for (std::size_t p = 0; p < demand.size(); ++p) {
            double coveredA = 0.0, coveredB = 0.0;
            for (std::size_t s = 0; s < sheets.size() && s < a.values.size(); ++s) {
                if (p < sheets[s].counts.size()) coveredA += sheets[s].counts[p] * a.values[s];
            }
            for (std::size_t s = 0; s < sheets.size() && s < b.values.size(); ++s) {
                if (p < sheets[s].counts.size()) coveredB += sheets[s].counts[p] * b.values[s];
            }
            CHECK(coveredA >= static_cast<double>(demand[p]) - 1e-7);
            CHECK(coveredB >= static_cast<double>(demand[p]) - 1e-7);
        }
        // ... and both must reproduce the objective from their own prices (dual feasibility)
        double costA = 0.0, costB = 0.0;
        for (std::size_t s = 0; s < sheets.size(); ++s) {
            if (s < a.values.size()) costA += sheets[s].price * a.values[s];
            if (s < b.values.size()) costB += sheets[s].price * b.values[s];
        }
        CHECK_NEAR(costA, a.objective, 1e-7);
        CHECK_NEAR(costB, b.objective, 1e-7);
        CHECK(real.droppedCoefficients() == 0u);
    }
    {
        // A model with a UNIQUE optimum: min 2x+3y s.t. x+y>=4, x+2y>=6 -> x=y=2, obj 10,
        // duals (1,1). Here the two backends must agree vertex by vertex as well.
        SimplexLinearProgram builtin;
        builtin.addColumn(2.0, 0.0, kInf);
        builtin.addColumn(3.0, 0.0, kInf);
        const int ix[2] = {0, 1};
        const double v1[2] = {1.0, 1.0};
        const double v2[2] = {1.0, 2.0};
        builtin.addRow(2, ix, v1, 4.0);
        builtin.addRow(2, ix, v2, 6.0);
        CHECK(builtin.solve() == static_cast<int>(LpStatus::Optimal));

        ClpLinearProgram real;
        real.addColumn(2.0, 0.0, kInf);
        real.addColumn(3.0, 0.0, kInf);
        real.addRow(2, ix, v1, 4.0);
        real.addRow(2, ix, v2, 6.0);
        CHECK(real.solve() == static_cast<int>(LpStatus::Optimal));

        CHECK_NEAR(real.objective(), builtin.objective(), 1e-7);
        CHECK_NEAR(real.objective(), 10.0, 1e-7);
        CHECK(real.primal().size() == 2u);
        CHECK_NEAR(real.primal()[0], 2.0, 1e-6);
        CHECK_NEAR(real.primal()[1], 2.0, 1e-6);
        CHECK(real.dual().size() == 2u);
        CHECK_NEAR(real.dual()[0], 1.0, 1e-6);
        CHECK_NEAR(real.dual()[1], 1.0, 1e-6);
    }
    {
        // the empty-domain diagnostic is reported, not repaired, by the real backend too
        ClpLinearProgram lp;
        lp.addColumn(1.0, 5.0, 1.0);            // lower > upper
        CHECK(lp.solve() == static_cast<int>(LpStatus::Infeasible));
        CHECK(lp.columns() == 1u);
    }
    {
        // reset() drops the model, the solution and the diagnostics
        ClpLinearProgram lp;
        lp.addColumn(1.0, 0.0, kInf);
        lp.addColumn(2.0, 0.0, kInf);
        const int index[2] = {0, 1};
        const double value[2] = {1.0, 1.0};
        lp.addRow(2, index, value, 3.0);
        CHECK(lp.solve() == static_cast<int>(LpStatus::Optimal));
        CHECK_NEAR(lp.objective(), 3.0, 1e-7);
        CHECK(lp.primal().size() == 2u);
        CHECK(lp.dual().size() == 1u);
        lp.reset();
        CHECK(lp.columns() == 0u);
        CHECK(lp.rows() == 0u);
    }
    {
        // the factory hands back the real backend as a LinearProgram
        std::unique_ptr<LinearProgram> lp = makeClpLinearProgram();
        CHECK(lp != nullptr);
        lp->addColumn(1.0, 0.0, kInf);
        const int index[1] = {0};
        const double value[1] = {1.0};
        lp->addRow(1, index, value, 4.0);
        CHECK(lp->solve() == static_cast<int>(LpStatus::Optimal));
        CHECK_NEAR(lp->objective(), 4.0, 1e-7);
    }
#endif  // LCNS_HAS_CLP

    return check::finish("test_linear_program");
}
