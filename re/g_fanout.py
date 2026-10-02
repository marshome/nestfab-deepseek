# -*- coding: utf-8 -*-
"""Rank the unread functions by CALLER COUNT, so "which layer to read" is a number.

Usage: python g_fanout.py [--top 30] [--min 20] [--exclude-library]

The previous round's diagnosis was that what remains divides into a shared primitive layer and exports whose own logic is large, and
that the layer is the better investment because 0x5CD800 alone is reached from 113 places. That judgement needs a measurement, and
this is it: for every function in the profile that no script has READ, count how many distinct functions call it.

The count is the leverage. A function called from 133 places settles a fragment of 133 paths; one called from 2 settles a fragment of
two. Ranking by it turns "read the layer next" from an intention into the first line of a list.

"Read" is approximated by the ledger and by the code: a function counts as read when it appears in a claim at INSTRUCTION or better,
or when its address appears in an `RE 0x...` comment under lcns/. That is an approximation and the tool says so, because the honest
alternative -- asking a script what it has looked at -- is not available.

Library code is excluded by default: the allocator, the C++ runtime and the iostreams have hundreds of callers each and are
CLASSIFIED rather than recovered, which re/CATEGORIES.md records. Including them would put the allocator at the top of every list,
which is true and useless.
"""
import argparse
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import g_leverage as L          # noqa: E402
import g_toolchain as T         # noqa: E402
from lib import load_prof       # noqa: E402

# the runtime and the allocator, which are classified rather than recovered
LIBRARY_RANGES = [(0x998000, 0x99A000), (0x9A0000, 0x9B0000), (0x8C0000, 0x8D0000), (0x63F000, 0x640000)]


def read_addresses():
    """Every function address a claim or an RE comment names."""
    out = set()
    data = json.load(io.open(os.path.join(HERE, "ledger.json"), encoding="utf-8"))
    for claim in data["claims"]:
        if claim["grade"] not in ("INSTRUCTION", "MEASURED", "CONSTRUCTOR", "DIFFERENTIAL"):
            continue
        for m in re.finditer(r"0x([0-9A-Fa-f]{4,7})", claim.get("witness", "") + " " + claim.get("predicate", "")):
            out.add(int(m.group(1), 16))
    for pattern in ("lcns/src/*.cpp", "lcns/include/lcns/*.hpp", "lcns/include/lcns/**/*.hpp", "lcns/tests/*.cpp"):
        for path in glob.glob(os.path.join(ROOT, pattern), recursive=True):
            text = io.open(path, encoding="utf-8", errors="replace").read()
            for m in re.finditer(r"RE\s*0x([0-9A-Fa-f]{4,7})", text):
                out.add(int(m.group(1), 16))
    return out


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--min", type=int, default=15)
    parser.add_argument("--exclude-library", action="store_true", default=True)
    parser.add_argument("--include-library", dest="exclude_library", action="store_false")
    args = parser.parse_args(argv)

    profile = load_prof()
    read = read_addresses()
    print("functions the ledger or the code names: %d" % len(read))

    def is_library(address):
        if not args.exclude_library:
            return False
        if address in T.BOILERPLATE or address in getattr(T, "IMPLEMENTED", ()):
            return True
        return any(low <= address < high for low, high in LIBRARY_RANGES)

    rows = []
    for address, info in profile.items():
        callers = len(set(info.get("callers") or []))
        if callers < args.min:
            continue
        if address in read or is_library(address):
            continue
        size = info.get("size") or 0
        rows.append((callers, size, address))
    rows.sort(reverse=True)

    print("unread functions with %d or more callers: %d" % (args.min, len(rows)))
    print("")
    print("%-9s %-9s %-9s %s" % ("callers", "bytes", "rva", "note"))
    for callers, size, address in rows[:args.top]:
        print("%-9d %-9d 0x%-8X %s" % (callers, size, address, ""))
    print("")
    total = sum(c for c, _s, _a in rows)
    print("the top %d account for %d caller edges between them" % (min(args.top, len(rows)), sum(c for c, _s, _a in rows[:args.top])))
    print("")
    print("The count is the leverage: a function called from 133 places settles a fragment of 133 paths and one called from two")
    print("settles two. 'Read' is approximated by the ledger's claims and by the RE comments under lcns/, which is an approximation")
    print("and is stated rather than hidden.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
