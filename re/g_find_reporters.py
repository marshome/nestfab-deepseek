# -*- coding: utf-8 -*-
"""Find every reporter-family function: the entry points that take strings from their callers.

Usage: python g_find_reporters.py [min-callers] [limit]

The assertion reporter 0x60A620 is not the only one. A function that receives a condition, a method name and a file name --
or a format string and its arguments -- is a naming oracle for everything that calls it, and this module has hundreds of
them: one logger at 0x64AEA0, a second assertion entry at 0x60B060, the dbg::symlog family the labels pass already uses.

The test for "is this one of them" is deliberately cheap and needs no reading: the FunctionData profile records how many
rip-relative literals a function's CALLERS hand it. A function whose callers consistently load three or more distinct
strings just before the call, and which has many callers, is a reporter. Sorting by that count puts the biggest oracle
first, which is the one worth harvesting next.

Output is one line per candidate with its caller count, the number of distinct string arguments its callers pass, the
strings themselves, and what this project already says the function is.
"""
import io
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_leverage as L          # noqa: E402
import g_toolchain as T         # noqa: E402
import lib as LIB               # noqa: E402
from lib import disasm, load_prof, rva2off  # noqa: E402

IMAGE = LIB.data if isinstance(LIB.data, (bytes, bytearray)) else LIB.data()
WINDOW = 30


def string_at(rva, limit=120):
    try:
        off = rva2off(rva)
    except Exception:
        return None
    if off is None or off < 0 or off >= len(IMAGE):
        return None
    out = []
    for b in IMAGE[off:off + limit]:
        if b == 0:
            break
        if 32 <= b < 127:
            out.append(chr(b))
        else:
            return None
    text = "".join(out)
    return text if len(text) >= 2 else None


def main(argv):
    min_callers = int(argv[0]) if argv else 20
    limit = int(argv[1]) if len(argv) > 1 else 40
    profile = load_prof()

    # every rip-relative literal load, so a call site can be described by its preceding loads
    sites = defaultdict(list)          # callee -> [(caller, [texts])]
    for addr, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        body = [i for i in disasm(addr) if i.address < addr + size]
        for index, ins in enumerate(body):
            if ins.mnemonic not in ("call", "jmp"):
                continue
            m = re.search(r"0x([0-9a-f]+)", ins.op_str)
            if not m:
                continue
            callee = int(m.group(1), 16)
            texts = []
            for i in range(max(0, index - WINDOW), index):
                mm = re.search(r"\[rip [+-] 0x([0-9a-f]+)\]", body[i].op_str)
                if not mm:
                    continue
                disp = int(mm.group(1), 16)
                if "[rip - " in body[i].op_str:
                    disp = -disp
                nxt = body[i + 1].address if i + 1 < len(body) else body[i].address + 8
                text = string_at(nxt + disp)
                if text:
                    texts.append(text)
            if texts:
                sites[callee].append((addr, texts))

    rows = []
    for callee, entries in sites.items():
        if len(entries) < min_callers:
            continue
        distinct = set()
        for _caller, texts in entries:
            for t in texts:
                distinct.add(t)
        rows.append((len(distinct), len(entries), callee, sorted(distinct)))
    rows.sort(key=lambda r: (-r[0], -r[1]))

    print("candidate reporter-family functions: %d (a function whose callers hand it %d+ distinct strings)"
          % (len(rows), 1))
    print("")
    print("%-9s %-8s %-9s %s" % ("rva", "callers", "strings", "sample strings"))
    shown = 0
    for nstrings, ncallers, callee, texts in rows:
        if shown >= limit:
            break
        if nstrings < 3:
            continue
        shown += 1
        kind = "domain"
        if callee in T.BOILERPLATE:
            kind = "boilerplate"
        elif callee in getattr(T, "IMPLEMENTED", ()):
            kind = "implemented"
        elif callee in L.VERIFIED:
            kind = "verified"
        else:
            k = T.kind(callee, profile)
            if k:
                kind = k
        size = (profile.get(callee) or {}).get("size")
        sample = " | ".join(t[:36] for t in texts[:3])
        print("0x%-7X %-8d %-9d %-11s %s  %s" % (callee, ncallers, nstrings, kind, size, sample))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
