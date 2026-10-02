# -*- coding: utf-8 -*-
"""Who calls this, and who calls the callers.

Usage: python g_callers.py 0x9449E0 [0x921CC0 ...]

A function's own body decides what it does; its callers decide what it is. The closure tools answer "what does this
depend on", and this one answers the other direction, which is what distinguishes an engine routine that a strategy calls
from a locale facet that the stream machinery installs. The profile gives the function boundaries, so the walk is over
real functions rather than over an address range.

The callers are reported with their size, whether they belong to the closure of ordinal 51, and their own first
instructions, so the reader can go one step up without another tool.
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
    targets = set(int(a, 0) for a in argv if a.startswith("0x"))
    if not targets:
        print("give at least one address")
        return 2
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
    rva = None
    for e in table:
        if (e.get("ords") or [0])[0] == 51:
            rva = e["rva"]
            break
    closure = {rva: 0}
    q = deque((t, 1) for t in callees(rva) if domain(t))
    while q:
        a, d = q.popleft()
        if a in closure and closure[a] <= d:
            continue
        closure[a] = d
        for t in callees(a):
            if domain(t):
                q.append((t, d + 1))

    # every function in the image whose body calls one of the targets
    callers = {t: [] for t in targets}
    for addr, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        body = None
        for ins in disasm(addr):
            if ins.address >= addr + size:
                break
            if ins.mnemonic not in ("call", "jmp"):
                continue
            m = re.search(r"0x([0-9a-f]+)", ins.op_str)
            if not m:
                continue
            t = int(m.group(1), 16)
            if t in callers:
                callers[t].append(addr)
                if body is None:
                    body = [i for i in disasm(addr) if i.address < addr + size][:4]

    for t in sorted(targets):
        unique = sorted(set(callers[t]))
        inside = [c for c in unique if c in closure]
        outside = [c for c in unique if c not in closure]
        print("=== who calls 0x%X (%s, size %s, in closure: %s): %d callers, %d of them inside the closure"
              % (t, T.kind(t, profile), (profile.get(t) or {}).get("size"),
                 ("depth %d" % closure[t]) if t in closure else "no", len(unique), len(inside)))
        if inside:
            print("  inside the closure (nearest callers decide what this is):")
            for c in inside[:24]:
                size = (profile.get(c) or {}).get("size")
                head = [i for i in disasm(c) if i.address < c + (size or 0)][:3]
                print("    0x%-8X %6s B  depth %-2d  %s" % (c, size, closure[c],
                      " ; ".join("%s %s" % (i.mnemonic, i.op_str) for i in head)))
        else:
            print("  no caller inside the closure; the callers are library or unrelated code:")
            for c in outside[:12]:
                size = (profile.get(c) or {}).get("size")
                head = [i for i in disasm(c) if i.address < c + (size or 0)][:3]
                print("    0x%-8X %6s B  kind %-11s  %s" % (c, size, T.kind(c, profile),
                      " ; ".join("%s %s" % (i.mnemonic, i.op_str) for i in head)))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
