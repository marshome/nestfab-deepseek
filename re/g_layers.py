# -*- coding: utf-8 -*-
"""Layer the dependencies of the unimplemented exports: domain versus platform versus diagnostic.

Round 416's leverage search said every one of the 154 unimplemented entry points is blocked, and the distribution showed
why: a handful of addresses block 40 to 100 exports each. But two of those are not domain code, and the search did not
distinguish them:

  * platform -- a function that reaches the outside world through the IAT (`call qword ptr [rip + ...]`). 0x62F280 is
    one: round 374 read it whole and found it building an "CCG " tagged argument block and making two indirect calls.
    It blocks 100 exports, and it is a toolchain boundary like libm's sqrt, not a dependency to reverse.
  * diagnostic -- a function that only builds strings and reports. 0x64AEA0 is one: round 369 showed its first act is to
    test a global switch and return immediately when it is off, so on the default path it does nothing. It blocks 45.

This script imports the earlier search rather than reproducing it, classifies each blocker, and reports which exports
become implementable once the two non-domain layers are set aside. Nothing here guesses: a blocker is called domain
unless its own instructions show it going through the IAT or into the logging helper 0x910BA0.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_leverage as L  # noqa: E402
from lib import disasm  # noqa: E402


def classify(addr):
    """platform / diagnostic / domain, from the function's own instructions."""
    text = []
    for ins in disasm(addr):
        text.append(ins.mnemonic + " " + ins.op_str)
    for t in text:
        if t.startswith("call qword ptr [rip"):
            return "platform"
    for t in text:
        if t == "call 0x910ba0":
            return "diagnostic"
    return "domain"


def main():
    done = L.forwarded_ordinals()
    table = json.loads(io.open(os.path.join(L.ROOT, "re", "exports_table.json"), encoding="utf-8").read())
    kinds = {}
    ready = []
    blocked = []
    for e in table:
        ord0 = (e.get("ords") or [0])[0]
        if ord0 in done:
            continue
        name = e.get("name") or ("sub_%05X" % e["rva"])
        targets = L.external_targets(e["rva"], e["size"])
        if not targets:
            ready.append((name, ord0, e["rva"], e["size"], "no external target at all"))
            continue
        bad = []
        for t in targets:
            if t in L.VERIFIED:
                continue
            if t not in kinds:
                kinds[t] = classify(t)
            if kinds[t] == "domain":
                bad.append(t)
        if not bad:
            ready.append((name, ord0, e["rva"], e["size"], "platform or diagnostic only"))
        else:
            blocked.append((name, ord0, e["rva"], e["size"], bad))

    print("=" * 70)
    print("LAYERED RESULT")
    print("")
    print("implementable without reading anything new: %d" % len(ready))
    for name, ord0, rva, size, why in ready[:60]:
        print("    0x%-6X ord %-4d %-34s %5d bytes  (%s)" % (rva, ord0, name, size, why))
    print("")
    print("still blocked on domain code: %d" % len(blocked))
    dom = {}
    for _n, _o, _r, _s, bad in blocked:
        for t in bad:
            dom[t] = dom.get(t, 0) + 1
    for t, c in sorted(dom.items(), key=lambda kv: -kv[1])[:14]:
        print("    0x%-8X %-11s blocks %3d exports" % (t, kinds.get(t, "?"), c))
    print("")
    print("blocker kinds, counted by distinct address:")
    for k in ("platform", "diagnostic", "domain"):
        n = len([t for t in kinds if kinds[t] == k])
        print("    %-11s %d" % (k, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
