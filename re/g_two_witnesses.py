# -*- coding: utf-8 -*-
"""Field names with two independent witnesses: a getter and a setter that agree on the offset.

Usage: python g_two_witnesses.py [--range 0x0 0x2C0] [--all]

Single-offset accessors name a field, but one witness can be wrong -- a function may touch one offset and have a name that
describes something else. Two witnesses cannot both be wrong in the same way if they are INDEPENDENT, so this accepts a name
only when at least two named single-offset accessors touch the same offset, and it prints the whole user set so a reader can
see whether the agreement is real or a coincidence of a narrow window.

An accessor here is a function of at most 0x100 bytes that touches exactly one offset through its first argument -- the same
rule re/g_named_fields.py uses, and the reason that tool's first version stamped everything 'CommonCutParameters' is in its
own comment.

Output: offset, the name the module gives it, the accessors that agree, and whether they read or write, which is what tells
a getter from a setter.
"""
import io
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_names as N             # noqa: E402
import g_toolchain as T         # noqa: E402
from lib import disasm, load_prof  # noqa: E402

ACCESS = re.compile(r"\[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\]")
MOVE = re.compile(r"^([a-z0-9]+), (.+)$")
ALIAS = {}
for _full, _names in {"rax": ("eax", "ax", "al"), "rbx": ("ebx", "bx", "bl"), "rcx": ("ecx", "cx", "cl"),
                      "rdx": ("edx", "dx", "dl"), "rsi": ("esi", "si", "sil"), "rdi": ("edi", "di", "dil")}.items():
    ALIAS[_full] = _full
    for _n in _names:
        ALIAS[_n] = _full
for _r in range(8, 16):
    for _s in ("", "d", "w", "b"):
        ALIAS["r%d%s" % (_r, _s)] = "r%d" % _r


def canonical(reg):
    return ALIAS.get(reg, reg)


def handles(body):
    carries = {"rcx"}
    for ins in body:
        m = MOVE.match(ins.op_str)
        if ins.mnemonic == "mov" and m and canonical(m.group(2)) in carries:
            carries.add(canonical(m.group(1)))
    behind = set()
    for _round in range(3):
        for ins in body:
            m = MOVE.match(ins.op_str)
            if ins.mnemonic != "mov" or not m:
                continue
            src = re.sub(r"^(byte|word|dword|qword|xmmword|oword) ptr ", "", m.group(2).strip())
            mm = re.match(r"^\[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\]$", src)
            if mm and canonical(mm.group(1)) in (carries | behind) and not mm.group(2):
                behind.add(canonical(m.group(1)))
            elif canonical(m.group(2)) in behind:
                behind.add(canonical(m.group(1)))
    return carries | behind


def main(argv):
    lo, hi = 0, 0x800
    if "--range" in argv:
        lo = int(argv[argv.index("--range") + 1], 0)
        hi = int(argv[argv.index("--range") + 2], 0)
    unclassified = "--all" in argv
    profile = load_prof()

    witnesses = defaultdict(list)
    for addr, info in profile.items():
        size = info.get("size") or 0
        if size == 0 or size > 0x100:
            continue
        name = N.direct(addr)
        if not name:
            continue
        if not unclassified and (addr in T.BOILERPLATE or addr in L_VERIFIED()):
            continue
        body = [i for i in disasm(addr) if i.address < addr + size]
        bases = handles(body)
        offsets = set()
        kind = None
        for ins in body:
            for m in ACCESS.finditer(ins.op_str):
                if canonical(m.group(1)) not in bases:
                    continue
                offset = int(m.group(2), 16) if m.group(2) else 0
                if not (lo <= offset <= hi):
                    continue
                offsets.add(offset)
                head = ins.op_str.split(",")[0].strip()
                if head.startswith(("byte ptr [", "word ptr [", "dword ptr [", "qword ptr [", "xmmword ptr [", "[")):
                    kind = "write"
                elif kind is None:
                    kind = "read"
        if len(offsets) == 1:
            offset = next(iter(offsets))
            witnesses[offset].append((addr, size, name, kind or "read"))

    agreed = {o: w for o, w in witnesses.items() if len(w) >= 2}
    single = {o: w for o, w in witnesses.items() if len(w) == 1}
    print("single-offset accessors: %d over %d offsets" % (sum(len(w) for w in witnesses.values()), len(witnesses)))
    print("offset with TWO OR MORE independent witnesses: %d  <-- these are the names to trust" % len(agreed))
    print("")
    for offset in sorted(agreed):
        entries = sorted(agreed[offset], key=lambda e: e[2])
        print("+0x%-6X  %s" % (offset, ", ".join("%s(%s,0x%X)" % (n, k, a) for a, _s, n, k in entries[:5])))
    print("")
    print("offsets with a single witness (a lead, not a name): %d" % len(single))
    for offset in sorted(single)[:30]:
        a, s, n, k = single[offset][0]
        print("    +0x%-6X  %-34s %s 0x%X" % (offset, n, k, a))
    return 0


_verified = None


def L_VERIFIED():
    global _verified
    if _verified is None:
        import g_leverage as L
        _verified = set(L.VERIFIED)
    return _verified


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
