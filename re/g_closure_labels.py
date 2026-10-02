# -*- coding: utf-8 -*-
"""Print the string labels and the head of every function still in a closure.

Usage: python g_closure_labels.py 51 [head]

g_labels.py prints the labels of an export entry point, and g_label_classify.py classifies a whole closure by them, but
neither shows the label next to the body of the individual functions of this closure. Most of what remains in a closure
this size is toolchain or library code, and such a function almost always announces itself: it loads a literal and hands
it to the logger or to the string machinery. This prints every literal a function loads, with the target address, followed
by the first few instructions, so one run classifies a batch.

Nothing is written; classifications go through g_classify.py so the reason is recorded next to the address.
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
import lib as LIB               # noqa: E402
from lib import disasm, load_prof, rva2off  # noqa: E402

IMAGE = LIB.data if isinstance(LIB.data, (bytes, bytearray)) else LIB.data()
SMALL_FOR_TOOLCHAIN = 64


def printable(data):
    out = []
    for b in data:
        if b == 0:
            break
        if 32 <= b < 127:
            out.append(chr(b))
        else:
            return "".join(out)
    return "".join(out)


def string_at(rva, limit=72):
    try:
        off = rva2off(rva)
    except Exception:
        return None
    if off is None or off < 0 or off >= len(IMAGE):
        return None
    text = printable(IMAGE[off:off + limit])
    return text if len(text) >= 3 else None


def literals(body):
    """(instruction address, target address, text) for every rip-relative literal the body loads."""
    out = []
    for index, ins in enumerate(body):
        m = re.search(r"\[rip [+-] 0x([0-9a-f]+)\]", ins.op_str)
        if not m:
            continue
        disp = int(m.group(1), 16)
        if "[rip - " in ins.op_str:
            disp = -disp
        nxt = body[index + 1].address if index + 1 < len(body) else ins.address + 8
        target = nxt + disp
        text = string_at(target)
        if text:
            out.append((ins.address, target, text))
    return out


def main(argv):
    ordinal = int(argv[0])
    head = int(argv[1]) if len(argv) > 1 else 10
    only = argv[2] if len(argv) > 2 else None
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
        if (e.get("ords") or [0])[0] == ordinal:
            rva = e["rva"]
            break
    assert rva is not None

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
    order = sorted(seen, key=lambda a: (seen[a], size_of(a)))
    for a in order:
        if only and only.upper() not in ("%X" % a):
            continue
        size = size_of(a)
        body = [i for i in disasm(a) if i.address < a + size]
        lits = literals(body)
        deps = [t for t in callees(a) if domain(t)]
        print("=== 0x%X (%d B, depth %d, deps %d)%s" % (a, size, seen[a], len(deps), "  LEAF" if not deps else ""))
        for addr, target, text in lits:
            print("    literal 0x%X -> 0x%X %r" % (addr, target, text))
        for x in body[:head]:
            print("    %08x %-18s %s" % (x.address, x.mnemonic, x.op_str))
        if len(body) > head:
            print("    ... %d more" % (len(body) - head))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
