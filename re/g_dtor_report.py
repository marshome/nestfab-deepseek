# -*- coding: utf-8 -*-
"""The order's destructor decomposed: four member destructors and sixteen frees, and nothing else.

Usage: python g_dtor_report.py [--destructor 0x5007C0]

RE 0x5007C0 is 716 bytes and looks like a lot of code. It has 22 calls and SEVEN distinct targets, which is the whole of it:

    0x9984B0   x16   the allocator's free (5 bytes)
    0x92B340   x1    605 bytes, 147 callers
    0x92B940   x1    597 bytes, 118 callers
    0x92BBA0   x1    687 bytes
    0x92ECB0   x1    791 bytes, 180 callers   -- implemented this session as releaseOwnedChain
    0x531F20   x1    71 bytes
    0x63F6D0   x1    a thunk through the import table

so the order's destructor is four member destructors, sixteen individual frees, one 71 byte helper and one thunk. The offsets it
touches on the order itself are +0x0C, +0x10, +0x18, +0x20, +0x30, +0x40, +0x50, +0x60, +0x78 and then +0x1D0, +0x1F8, +0x208,
+0x228, +0x230, +0x240, +0x250, +0x258, +0x268, +0x270, +0x280, +0x2A8, +0x2B8 -- all inside the 0x2C0 the constructor
allocates, which is the check that says the two functions describe one object.

This tool prints that decomposition for any destructor-like function, because "716 bytes" and "four members to destroy" are very
different amounts of work and the difference is one call count away.
"""
import argparse
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_leverage as L  # noqa: E402
from lib import disasm, load_prof  # noqa: E402


def main(argv):
    target = 0x5007C0
    if "--destructor" in argv:
        target = int(argv[argv.index("--destructor") + 1], 0)
    profile = load_prof()
    size = (profile.get(target) or {}).get("size") or 0
    body = [i for i in disasm(target) if i.address < target + size]
    print("0x%X  %d bytes  %d instructions" % (target, size, len(body)))

    calls = []
    for ins in body:
        if ins.mnemonic != "call":
            continue
        m = re.search(r"0x([0-9a-f]+)", ins.op_str)
        if m:
            calls.append(int(m.group(1), 16))
    counted = collections.Counter(calls)
    print("%d calls, %d distinct targets" % (len(calls), len(counted)))
    print("")
    print("%-12s %-5s %-8s %-9s %s" % ("target", "times", "bytes", "callers", "note"))
    for callee, times in counted.most_common():
        info = profile.get(callee) or {}
        note = ""
        if callee == 0x9984B0:
            note = "the allocator's free"
        elif callee in L.VERIFIED:
            note = "recovered in this project: %s" % L.VERIFIED[callee]
        elif info.get("size") is None:
            note = "a thunk (not a function in the profile)"
        print("0x%-10X %-5d %-8s %-9s %s"
              % (callee, times, info.get("size"), len(info.get("callers") or []), note))

    offsets = sorted({int(m.group(1), 16) for ins in body
                      for m in [re.search(r"\[r[a-z0-9]+ \+ (0x[0-9a-f]+)\]", ins.op_str)] if m})
    print("")
    print("offsets touched, all of them: %s" % " ".join("+0x%X" % o for o in offsets))
    print("")
    print("So the work here is the call count, not the byte count: %d distinct targets to understand rather than %d bytes."
          % (len(counted), size))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
