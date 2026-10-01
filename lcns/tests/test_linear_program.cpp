// tests/test_linear_program.cpp -- the recovered Lp::LinearProgram / Coin::CoinLP layer and the
// sheet selection LP that `BuildAndSolveLp` (0x7D7200, ..\multi\database.cpp:450) drives:
//
//     minimise   sum_s price_s * x_s
//     s.t.       sum_s counts[s][p] * x_s >= demand[p]      for every part p
//                x_s >= 0
#include "check.hpp"
#include "lcns/lp.hpp"

#include <limits>
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

    return check::finish("test_linear_program");
}
