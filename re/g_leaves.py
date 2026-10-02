# -*- coding: utf-8 -*-
"""Print the smallest leaves of an export closure together with their bodies.

Usage: python g_leaves.py 51 10

A leaf is a domain function with no domain dependencies of its own, so it can be implemented as soon as it is understood.
Printing the bodies in the same run means one round trip per batch instead of two.
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
    want = int(argv[1]) if len(argv) > 1 else 10
    profile = load_prof()
    kinds = {}

    def domain(addr):
        if addr in L.VERIFIED or addr in T.BOILERPLATE:
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
    rva = None
    for e in table:
        if (e.get("ords") or [0])[0] == ordinal:
            rva = e["rva"]
            name = e.get("name")
            break
    assert rva is not None, "ordinal not found"

    seen = {}
    q = deque((t, 1) for t in callees(rva) if domain(t))
    while q:
        a, d = q.popleft()
        if a in seen and seen[a] <= d:
            continue
        seen[a] = d
        for t in callees(a):
            if domain(t):
                q.append((t, d + 1))

    leaves = [a for a in seen if not [t for t in callees(a) if domain(t)]]
    leaves.sort(key=lambda a: (profile.get(a) or {}).get("size") or 0)
    print("ordinal %d %s: closure %d functions, %d leaves; showing the %d smallest leaves"
          % (ordinal, name, len(seen), len(leaves), min(want, len(leaves))))
    for a in leaves[:want]:
        size = (profile.get(a) or {}).get("size")
        print("")
        print("=== 0x%X (%s B, depth %d):" % (a, size, seen[a]))
        body = [x for x in disasm(a) if not size or x.address < a + size]
        for x in body[:18]:
            print("   %08x %-18s %s" % (x.address, x.mnemonic, x.op_str))
        if len(body) > 18:
            print("   ... %d more instructions" % (len(body) - 18))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
