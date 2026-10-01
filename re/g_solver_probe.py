"""Which LP solver does the dump actually reference: OR-Tools, or COIN-OR Clp?

Searches the whole file (not just the printable-string table) for the markers each library
would leave behind, and reports hit counts with RVAs.
"""
import re
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")

PATH = r"D:\Nesting\nestfab\libcns_dump_64.dll"
with open(PATH, "rb") as fh:
    blob = fh.read()
print("file size", len(blob))

# The dump maps RVA == file offset for the first section (.text starts at 0x1000), which is
# what the earlier analysis relied on; report offsets as RVAs accordingly.
PATTERNS = {
    "--- OR-Tools ---": [
        rb"ortools", rb"OR-Tools", rb"operations_research", rb"GlopParameters", rb"glop",
        rb"MPSolver", rb"linear_solver", rb"sat_parameters", rb"SatParameters",
        rb"operations-research", rb"BopParameters", rb"RoutingModel", rb"cp_model",
    ],
    "--- COIN-OR ---": [
        rb"ClpSimplex", rb"ClpParameters", rb"CoinLP", rb"CoinUtils", rb"OsiClp", rb"OsiSolver",
        rb"CoinBuild", rb"CoinPackedMatrix", rb"ClpModel", rb"ClpInterior", rb"COIN",
        rb"clp", rb"CoinMessageHandler", rb"Idiot", rb"ClpPdco",
    ],
    "--- other LP solvers ---": [
        rb"glpk", rb"GLPK", rb"lp_solve", rb"HiGHS", rb"highs", rb"Gurobi", rb"gurobi",
        rb"CbcModel", rb"Cbc", rb"SoPlex", rb"Xpress", rb"CPLEX", rb"cplex",
    ],
    "--- lcns LP layer (recovered names) ---": [
        rb"LinearProgram", rb"PriceComputer", rb"ColumnGener", rb"column_gener",
        rb"Prc::", rb"Lp::", rb"Simplex", rb"simplex",
    ],
}

for title, pats in PATTERNS.items():
    print()
    print(title)
    for p in pats:
        rx = re.compile(p, re.IGNORECASE)
        hits = [m.start() for m in rx.finditer(blob)]
        if not hits:
            print("   %-26s 0" % p.decode())
            continue
        sample = []
        for off in hits[:4]:
            lo = max(0, off - 30)
            hi = min(len(blob), off + 70)
            ctx = blob[lo:hi]
            ctx = bytes(c if 32 <= c < 127 else 0x2E for c in ctx)
            sample.append("rva 0x%x: %s" % (off, ctx.decode("ascii", "replace")))
        print("   %-26s %d hit(s)" % (p.decode(), len(hits)))
        for s in sample:
            print("        " + s)
