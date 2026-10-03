# -*- coding: utf-8 -*-
"""Where a member offset stops being used: an object's end, and the functions that show it.

Usage: python g_extent.py 0x1C8 [--step 0x400] [--min-users 20]

A structure's end is visible in the same data as its members. If [base+0x2A8] is touched by 97 functions and [base+0x858] by
three, the object ends in between, and the offsets the most functions agree on below that line are the ones a declaration
has to get right.

This walks the whole module, counts how many functions touch each non-stack offset, and prints the count in bands, so the
fall-off is visible instead of guessed. It is the check that the object 0x22A20 builds is far larger than the 0x1C8 bytes it
allocates: 0x1C8 is only the part the constructor initialises, and the offsets above it stay in the same grid, which means
the object is at least a kilobyte and the destructor 0x5007C0 walks more than the constructor wrote.
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_names as N             # noqa: E402
from lib import disasm, load_prof  # noqa: E402

ACCESS = re.compile(r"\[([a-z0-9]+)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\]")
STACK = ("rsp", "rbp")


def main(argv):
    start = int(argv[0], 0) if argv else 0x1C8
    step = int(argv[argv.index("--step") + 1], 0) if "--step" in argv else 0x400
    min_users = int(argv[argv.index("--min-users") + 1]) if "--min-users" in argv else 20
    profile = load_prof()

    users = defaultdict(set)
    for addr, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        for ins in disasm(addr):
            if ins.address >= addr + size:
                break
            for m in ACCESS.finditer(ins.op_str):
                if m.group(1) in STACK:
                    continue
                offset = int(m.group(2), 16) if m.group(2) else 0
                users[offset].add(addr)

    top = max((o for o, u in users.items() if len(u) >= min_users), default=0)
    print("the last offset in the module touched by %d or more functions: +0x%X" % (min_users, top))
    print("")
    print("band      offsets   touched by 20+   the busiest offset in the band")
    band = start
    while band < top + step:
        lo, hi = band, band + step
        in_band = [o for o in users if lo <= o < hi]
        strong = [o for o in in_band if len(users[o]) >= min_users]
        if in_band:
            busy = max(in_band, key=lambda o: len(users[o]))
            print("+0x%-6X %-9d %-15d +0x%-6X (%d functions)"
                  % (lo, len(in_band), len(strong), busy, len(users[busy])))
        band = hi
    print("")
    # the member grid of the object the constructor allocates, printed as a declaration would
    print("the offsets between +0x1C8 and +0x2C0, as a member list:")
    line = []
    for offset in sorted(o for o in users if start <= o <= 0x2C0):
        line.append("+0x%X(%d)" % (offset, len(users[offset])))
        if len(line) == 8:
            print("    %s" % " ".join(line))
            line = []
    if line:
        print("    %s" % " ".join(line))
    print("")
    # who uses the members the destructor walks, with their names
    print("the functions that touch +0x2A8 (the node list), by name:")
    for addr in sorted(users.get(0x2A8, ()))[:20]:
        print("    0x%-8X %s" % (addr, N.direct(addr) or ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
