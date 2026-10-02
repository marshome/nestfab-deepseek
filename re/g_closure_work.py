# -*- coding: utf-8 -*-
"""The whole closure of an export in work order, with the bodies needed for the next batch.

Usage: python g_closure_work.py 51 [bodies] [maxbytes]

g_closure_of.py prints the closure leaves first but truncates the bodies, and g_leaves.py prints only the smallest few,
so a batch of twenty leaves cost three or four runs. This one prints every function of the closure sorted by depth and
then by size -- the order in which it can be implemented -- and then, for the leaves that no shape recognised and that no
registry has claimed, the complete body up to maxbytes. That is the reading a human still has to do, in one screen.

It writes nothing: the classification goes through g_classify.py and the registry through the batch script, so an
accidental run cannot change the project.
"""
import io
import json
import os
import re
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_leverage as L          # noqa: E402
import g_toolchain as T         # noqa: E402
from lib import disasm, load_prof  # noqa: E402

SMALL_FOR_TOOLCHAIN = 64


def main(argv):
    ordinal = int(argv[0])
    want_bodies = int(argv[1]) if len(argv) > 1 else 20
    maxbytes = int(argv[2]) if len(argv) > 2 else 400
    profile = load_prof()
    kinds = {}

    def done(addr):
        return addr in L.VERIFIED or addr in T.BOILERPLATE or addr in getattr(T, "IMPLEMENTED", ())

    def domain(addr):
        if done(addr):
            return False
        if addr not in profile:
            return False
        if addr not in kinds:
            k = T.kind(addr, profile)
            size = (profile.get(addr) or {}).get("size") or 0
            kinds[addr] = k if (k is not None and k != "domain" and size <= SMALL_FOR_TOOLCHAIN) else "domain"
        return kinds[addr] == "domain"

    def callees(addr):
        out = []
        size = (profile.get(addr) or {}).get("size")
        for ins in disasm(addr):
            if size and ins.address >= addr + size:
                break
            if ins.mnemonic in ("call", "jmp"):
                m = re.search(r"0x([0-9a-f]+)", ins.op_str)
                if m:
                    out.append(int(m.group(1), 16))
        return out

    table = json.loads(io.open(os.path.join(L.ROOT, "re", "exports_table.json"), encoding="utf-8").read())
    rva = name = None
    for e in table:
        if (e.get("ords") or [0])[0] == ordinal:
            rva, name = e["rva"], e.get("name")
            break
    assert rva is not None, "ordinal not found"

    seen = {rva: 0}
    q = deque((t, 1) for t in callees(rva) if domain(t))
    while q:
        a, d = q.popleft()
        if a in seen and seen[a] <= d:
            continue
        seen[a] = d
        for t in callees(a):
            if domain(t):
                q.append((t, d + 1))

    size_of = lambda a: (profile.get(a) or {}).get("size") or 0
    order = sorted(seen.items(), key=lambda kv: (-kv[1], size_of(kv[0])))
    total = sum(size_of(a) for a in seen)
    print("ordinal %d %s (0x%X): %d domain functions, %d bytes" % (ordinal, name, rva, len(seen), total))
    print("")
    for a, d in order:
        deps = [t for t in callees(a) if domain(t)]
        print("    depth %-2d 0x%-8X %6d B  own domain deps %-3d %s"
              % (d, a, size_of(a), len(deps), "LEAF" if not deps else ""))
    print("")

    leaves = [a for a in seen if not [t for t in callees(a) if domain(t)]]
    leaves.sort(key=size_of)
    shown = 0
    for a in leaves:
        size = size_of(a)
        if size > maxbytes:
            continue
        if shown >= want_bodies:
            break
        shown += 1
        print("=== 0x%X (%d B, depth %d)" % (a, size, seen[a]))
        for x in disasm(a):
            if x.address >= a + size:
                break
            print("    %08x %-18s %s" % (x.address, x.mnemonic, x.op_str))
        print("")
    print("leaves: %d, bodies shown: %d" % (len(leaves), shown))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
