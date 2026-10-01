// tests/test_lp.cpp -- dense simplex (two phase, duals) and column generation.
#include "check.hpp"
#include "lcns/lp.hpp"
#include "lcns/lp_column_generation.hpp"
#include "lcns/lp_nesting.hpp"

#include <memory>

using namespace lcns;
using namespace lcns::lp;

int main() {
    // --- trivial: min x + y s.t. x + y >= 4 ---
    {
        Simplex s;
        s.reserve(1, 2);
        s.addColumn(1.0);
        s.addColumn(1.0);
        s.addRow({1.0, 1.0}, RowSense::GreaterEqual, 4.0);
        const SimplexStatus st = s.solve();
        CHECK(st == SimplexStatus::Optimal);
        CHECK_NEAR(s.objective(), 4.0, 1e-7);
        CHECK_NEAR(s.primal()[0] + s.primal()[1], 4.0, 1e-7);
        // the dual of ">= 4" is 1
        CHECK(s.dual().size() == 1);
        CHECK_NEAR(s.dual()[0], 1.0, 1e-7);
    }

    // --- a corner optimum with two rows ---
    {
        // min 2x + 3y s.t. x + y >= 4, x + 2y >= 6  -> x = 2, y = 2, cost 10
        Simplex s;
        s.reserve(2, 2);
        s.addColumn(2.0);
        s.addColumn(3.0);
        s.addRow({1.0, 1.0}, RowSense::GreaterEqual, 4.0);
        s.addRow({1.0, 2.0}, RowSense::GreaterEqual, 6.0);
        CHECK(s.solve() == SimplexStatus::Optimal);
        CHECK_NEAR(s.objective(), 10.0, 1e-7);
        CHECK_NEAR(s.primal()[0], 2.0, 1e-7);
        CHECK_NEAR(s.primal()[1], 2.0, 1e-7);
    }

    // --- equality rows ---
    {
        // min x + y s.t. 2x + 3y = 12, x + y = 5 -> x = 3, y = 2, cost 5
        Simplex s;
        s.reserve(2, 2);
        s.addColumn(1.0);
        s.addColumn(1.0);
        s.addRow({2.0, 3.0}, RowSense::Equal, 12.0);
        s.addRow({1.0, 1.0}, RowSense::Equal, 5.0);
        CHECK(s.solve() == SimplexStatus::Optimal);
        CHECK_NEAR(s.objective(), 5.0, 1e-7);
        CHECK_NEAR(s.primal()[0], 3.0, 1e-7);
        CHECK_NEAR(s.primal()[1], 2.0, 1e-7);
    }

    // --- upper bound style row and a negative right hand side ---
    {
        // min x s.t. x <= 7 (rhs positive, slack basis)
        Simplex s;
        s.reserve(1, 1);
        s.addColumn(1.0);
        s.addRow({1.0}, RowSense::LessEqual, 7.0);
        CHECK(s.solve() == SimplexStatus::Optimal);
        CHECK_NEAR(s.objective(), 0.0, 1e-9);

        // force x >= 5 with a negative rhs form: -x <= -5
        Simplex t;
        t.reserve(1, 1);
        t.addColumn(1.0);
        t.addRow({-1.0}, RowSense::LessEqual, -5.0);
        CHECK(t.solve() == SimplexStatus::Optimal);
        CHECK_NEAR(t.objective(), 5.0, 1e-7);
        CHECK_NEAR(t.primal()[0], 5.0, 1e-7);
    }

    // --- infeasible ---
    {
        Simplex s;
        s.reserve(2, 1);
        s.addColumn(0.0);
        s.addRow({1.0}, RowSense::GreaterEqual, 1.0);
        s.addRow({-1.0}, RowSense::GreaterEqual, 0.0);   // x <= 0
        CHECK(s.solve() == SimplexStatus::Infeasible);
        CHECK(std::string(toString(SimplexStatus::Infeasible)) == "infeasible");
    }

    // --- unbounded ---
    {
        Simplex s;
        s.reserve(0, 1);
        s.addColumn(-1.0);   // minimise -x with no constraint
        CHECK(s.solve() == SimplexStatus::Unbounded);
    }

    // --- reduced cost of a column that is not in the problem ---
    {
        Simplex s;
        s.reserve(1, 2);
        s.addColumn(1.0);
        s.addColumn(1.0);
        s.addRow({1.0, 1.0}, RowSense::GreaterEqual, 4.0);
        CHECK(s.solve() == SimplexStatus::Optimal);
        // a new column with cost 0.5 and coefficient 1 improves (rc = 0.5 - 1 = -0.5)
        CHECK_NEAR(s.reducedCost(0.5, {1.0}), -0.5, 1e-7);
        // a column with cost 2 is not worth adding
        CHECK(s.reducedCost(2.0, {1.0}) > 0.0);
    }

    // --- master problem: set covering over patterns ---
    {
        // demand 4 of one part; a pattern holds 3 of it
        MasterProblem master({4});
        Pattern p1;
        p1.counts = {3};
        p1.cost = 1.0;
        master.addPattern(p1);
        Pattern p2;
        p2.counts = {1};
        p2.cost = 1.0;
        master.addPattern(p2);
        CHECK(master.solve() == SimplexStatus::Optimal);
        // cheapest mix: 1 x (3) + 1 x (1) = 2 sheets, or 4/3 x (3) = 1.333 sheets
        CHECK_NEAR(master.objective(), 4.0 / 3.0, 1e-6);
        CHECK(master.partPrices().size() == 1);
        CHECK_NEAR(master.partPrices()[0], 1.0 / 3.0, 1e-6);
        CHECK(master.sheetsUsed() == 2);   // ceil(4/3)
    }

    // --- greedy pricer: classic cutting stock LP bound ---
    {
        // One part type, length 3, capacity 10, demand 4. Seed with the trivially feasible
        // "one item per sheet" pattern, then let pricing find the three-item pattern.
        // The LP optimum is 4/3 sheets.
        MasterProblem master({4});
        Pattern seed;
        seed.counts = {1};
        seed.cost = 1.0;
        master.addPattern(seed);
        GreedyPricer pricer({3.0}, 1, 10.0);
        CHECK(std::string(pricer.name()) == "GreedyPricer");
        const ColumnGenerationResult r = columnGeneration(master, pricer, 20);
        CHECK(r.optimal);
        CHECK_NEAR(r.objective, 4.0 / 3.0, 1e-6);
        CHECK(!r.used.empty());
        CHECK(r.sheetsUsed == 2);
        CHECK(r.columnsAdded == 1);      // {3} is the only improving column
    }
    {
        // Two part types: demand 3 of length 4, demand 2 of length 5, capacity 10.
        // The greedy pricer is only a heuristic, so require improvement rather than the exact
        // LP optimum. 22 units of length over 10 unit sheets bounds the objective from below.
        MasterProblem master({3, 2});
        Pattern seedA;
        seedA.counts = {1, 0};
        seedA.cost = 1.0;
        master.addPattern(seedA);
        Pattern seedB;
        seedB.counts = {0, 1};
        seedB.cost = 1.0;
        master.addPattern(seedB);

        GreedyPricer pricer({4.0, 5.0}, 1, 10.0);
        const ColumnGenerationResult r = columnGeneration(master, pricer, 30);
        CHECK(r.columnsAdded >= 1);
        CHECK(r.objective < 5.0);            // strictly better than one item per sheet
        CHECK(r.objective >= 2.2 - 1e-9);    // cannot beat total length / capacity
        CHECK(r.iterations >= 1);
    }

    // --- an unseeded master is reported, not looped on ---
    {
        MasterProblem empty({3});
        GreedyPricer pricer({2.0}, 1, 10.0);
        const ColumnGenerationResult r = columnGeneration(empty, pricer, 5);
        CHECK(!r.optimal);
        CHECK(r.columnsAdded == 0);
        CHECK(r.message.find("initial column") != std::string::npos);
        CHECK(empty.demand().size() == 1);
    }

    // --- column generation is bounded and reports its state ---
    {
        MasterProblem master({5});
        // a pricer that never finds anything useful
        class DeadPricer : public lp::ColumnPricer {
        public:
            const char* name() const override { return "DeadPricer"; }
            Pattern price(const std::vector<double>&, double, double* rc) const override {
                Pattern p;
                p.counts = {1};
                p.cost = 100.0;
                if (rc) *rc = 99.0;
                return p;
            }
        } dead;
        // seed one column so the master is feasible
        Pattern seed;
        seed.counts = {1};
        seed.cost = 1.0;
        master.addPattern(seed);
        const ColumnGenerationResult r = columnGeneration(master, dead, 5);
        CHECK(r.optimal);
        CHECK(r.columnsAdded == 0);
        CHECK_NEAR(r.objective, 5.0, 1e-6);
    }

    // --- pricing powered by a real nesting run ---
    {
        Order order;
        Sheet s;
        s.width = 100.0;
        s.height = 100.0;
        order.sheets.push_back(s);
        Part p;
        p.rawShape = makeRectMulti(0, 0, 20, 20);
        p.shape = p.rawShape;
        p.multiplicity = 1;
        order.parts.push_back(p);

        EngineParams params;
        params.timeLimitSeconds = 0.5;
        params.maxIterations = 8;
        params.beam.maxAngleSteps = 2;
        NestingPatternPricer pricer(order, params);
        CHECK(std::string(pricer.name()) == "NestingPatternPricer");

        double rc = 0.0;
        const Pattern pattern = pricer.price({1.0}, 0.0, &rc);
        CHECK(pricer.runs() == 1);
        CHECK(pattern.counts.size() == 1);
        CHECK(pattern.counts[0] >= 1);      // the engine must place at least one copy
        CHECK(pattern.sheets == 1);
        // 20x20 parts on a 100x100 sheet: 25 fit, so the density is 1.0 and rc = 1 - 25
        CHECK(pattern.counts[0] > 1);
        CHECK(rc < 0.0);

        // demand 10: seed with "one part per sheet", then let the nesting pricer improve it
        MasterProblem master({10});
        Pattern seed;
        seed.counts = {1};
        seed.cost = 1.0;
        master.addPattern(seed);
        const ColumnGenerationResult r = columnGeneration(master, pricer, 6);
        CHECK(r.iterations >= 1);
        CHECK(r.columnsAdded >= 1);
        CHECK(r.objective > 0.0);
        CHECK(r.objective < 10.0);   // the 25-per-sheet pattern must beat one per sheet
    }

    return check::finish("test_lp");
}
