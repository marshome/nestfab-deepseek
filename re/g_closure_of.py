# -*- coding: utf-8 -*-
"""Print the closure of one or more exports, leaves first, so the shared work is visible.

Usage: python g_closure_of.py 208 252
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
    wanted = [int(x) for x in argv]
    shared = {}
    for e in table:
        ord0 = (e.get("ords") or [0])[0]
        if ord0 not in wanted:
            continue
        name = e.get("name") or ("sub_%05X" % e["rva"])
        seen = {}
        q = deque((t, 1) for t in callees(e["rva"]) if domain(t))
        while q:
            a, d = q.popleft()
            if a in seen and seen[a] <= d:
                continue
            seen[a] = d
            for t in callees(a):
                if domain(t):
                    q.append((t, d + 1))
        for a in seen:
            shared.setdefault(a, []).append(ord0)
        print("=== ordinal %d %s (0x%X, %d B): %d domain functions, %d bytes"
              % (ord0, name, e["rva"], e["size"], len(seen),
                 sum(((profile.get(a) or {}).get("size") or 0) for a in seen)))
        # leaves first: depth descending, and within a depth the small ones first
        for a, d in sorted(seen.items(), key=lambda kv: (-kv[1], (profile.get(kv[0]) or {}).get("size") or 0)):
            own = [t for t in callees(a) if domain(t)]
            print("    depth %d  0x%-8X %6s B  own domain deps %d  %s"
                  % (d, a, (profile.get(a) or {}).get("size"), len(own),
                     "LEAF" if not own else ""))
        print("")
    print("functions needed by more than one of these exports:")
    for a, ords in sorted(shared.items(), key=lambda kv: -len(kv[1])):
        if len(ords) > 1:
            print("    0x%-8X %6s B  ordinals %s" % (a, (profile.get(a) or {}).get("size"), sorted(ords)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
