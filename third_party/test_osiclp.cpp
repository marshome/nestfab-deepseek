// Proof that the locally built COIN-OR Osi+Clp can be linked and driven from lcns.
//
// The LP is handed over in MPS form so the test does not depend on CoinPackedMatrix's (old and
// easy to get wrong) construction API -- and it exercises Clp's own reader as a bonus.
//
//   min x + 2y   s.t.  x + y >= 1,  x - y <= 0,  x,y >= 0    -> optimum x = y = 0.5, obj = 1.5
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <fstream>
#include <string>

#include "OsiClpSolverInterface.hpp"

static const char* kMps =
    "NAME          LCNSLINK\n"
    "ROWS\n"
    " N  COST\n"
    " G  R1\n"
    " L  R2\n"
    "COLUMNS\n"
    "    X         COST      1.0   R1        1.0\n"
    "    X         R2        1.0\n"
    "    Y         COST      2.0   R1        1.0\n"
    "    Y         R2       -1.0\n"
    "RHS\n"
    "    RHS       R1        1.0\n"
    "BOUNDS\n"
    " LO BND       X         0.0\n"
    " LO BND       Y         0.0\n"
    "ENDATA\n";

int main() {
    const std::string path = "lcns_osiclp_link_test.mps";
    {
        std::ofstream f(path.c_str());
        f << kMps;
    }

    OsiClpSolverInterface si;
    si.readMps(path.c_str(), "");
    si.setObjSense(1.0);              // minimise
    si.initialSolve();

    const double* x = si.getColSolution();
    const int n = si.getNumCols();
    std::printf("cols=%d rows=%d  status=%d  x=%.6f y=%.6f  obj=%.6f\n",
                n, si.getNumRows(), static_cast<int>(si.isProvenOptimal()),
                n > 0 ? x[0] : -1.0, n > 1 ? x[1] : -1.0, si.getObjValue());

    const bool ok = n == 2 && si.isProvenOptimal() && std::fabs(x[0] - 0.5) < 1e-6 &&
                    std::fabs(x[1] - 0.5) < 1e-6 && std::fabs(si.getObjValue() - 1.5) < 1e-6;
    std::printf("%s\n", ok ? "OSICLP-LINK-OK" : "OSICLP-LINK-FAILED");
    std::remove(path.c_str());
    return ok ? 0 : 1;
}
