# -*- coding: utf-8 -*-
"""An offset's readers and writers, each with the function name the module gives itself: that is where a field gets named.

Usage: python g_field_names.py 0x2AB0 [--range 0x1C0 0x2C0] [--min 1]

The slot names in lcns/launching_order.hpp are placeholders because the widths are evidence and the meanings were not. The
meanings are recoverable from the callers, and not by guessing: this module names its own functions in the log line and the
assertion every one of them carries, and a setter's name is its field's name. `SetSheetPriority` writes the priority;
`GetNumberOfMarks` reads the number of marks.

For each offset this prints the functions that READ it and the functions that WRITE it, with those names, so a field's
meaning is read off the operations that touch it:

    +0x1F8   written by SetPartVariantAuthorizations, read by GetSheetPriority

It also keeps the two directions apart, because a reader and a writer of the same offset are the strongest pair available:
a `Get` and a `Set` with the same noun is a field name that came from the module rather than from a translation of an
offset into English.
"""
import io
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_names as N             # noqa: E402
from lib import disasm, load_prof  # noqa: E402

ACCESS = re.compile(r"\[([a-z0-9]+)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\]")
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
STACK = ("rsp", "rbp")


def canonical(reg):
    return ALIAS.get(reg, reg)


def handles(body):
    """Registers carrying the first argument and the object behind its first pointer."""
    carries = {"rcx"}
    for ins in body:
        m = MOVE.match(ins.op_str)
        if ins.mnemonic != "mov" or not m:
            continue
        if canonical(m.group(2)) in carries:
            carries.add(canonical(m.group(1)))
    behind = set()
    for _round in range(3):
        for ins in body:
            m = MOVE.match(ins.op_str)
            if ins.mnemonic != "mov" or not m:
                continue
            src = re.sub(r"^(byte|word|dword|qword|xmmword|oword) ptr ", "", m.group(2).strip())
            mm = re.match(r"^\[([a-z0-9]+)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\]$", src)
            if mm and canonical(mm.group(1)) in (carries | behind) and not mm.group(2):
                behind.add(canonical(m.group(1)))
            elif canonical(m.group(2)) in behind:
                behind.add(canonical(m.group(1)))
    return carries | behind


def main(argv):
    if not argv:
        print("give a function whose first argument is the object, for example 0x2AB0")
        return 2
    anchor = int(argv[0], 0)
    lo, hi = 0, 0x800
    if "--range" in argv:
        lo = int(argv[argv.index("--range") + 1], 0)
        hi = int(argv[argv.index("--range") + 2], 0)
    minimum = int(argv[argv.index("--min") + 1]) if "--min" in argv else 1
    profile = load_prof()

    reads = defaultdict(set)
    writes = defaultdict(set)
    for addr, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        body = [i for i in disasm(addr) if i.address < addr + size]
        bases = handles(body)
        for ins in body:
            for m in ACCESS.finditer(ins.op_str):
                if canonical(m.group(1)) not in bases:
                    continue
                offset = int(m.group(2), 16) if m.group(2) else 0
                if not (lo <= offset <= hi):
                    continue
                # a store is one whose memory operand is the destination
                head = ins.op_str.split(",")[0].strip()
                if head.startswith(("byte ptr [", "word ptr [", "dword ptr [", "qword ptr [", "xmmword ptr [", "[")):
                    writes[offset].add(addr)
                else:
                    reads[offset].add(addr)

    # the offsets the anchor itself touches, so the output is about that object
    anchor_size = (profile.get(anchor) or {}).get("size") or 0
    anchor_body = [i for i in disasm(anchor) if i.address < anchor + anchor_size]
    anchor_offsets = set()
    for ins in anchor_body:
        for m in ACCESS.finditer(ins.op_str):
            if canonical(m.group(1)) in handles(anchor_body) and m.group(2):
                anchor_offsets.add(int(m.group(2), 16))

    print("the anchor 0x%X touches %d offsets in 0x%X..0x%X: %s"
          % (anchor, len(anchor_offsets), lo, hi, " ".join("+0x%X" % o for o in sorted(anchor_offsets))))
    print("")
    for offset in sorted(set(reads) | set(writes)):
        if offset not in anchor_offsets and len(reads[offset]) + len(writes[offset]) < minimum:
            continue
        rnames = sorted(set(N.direct(a) for a in reads[offset] if N.direct(a)))
        wnames = sorted(set(N.direct(a) for a in writes[offset] if N.direct(a)))
        if len(reads[offset]) + len(writes[offset]) < minimum and not rnames and not wnames:
            continue
        print("+0x%-6X  readers %-3d  writers %-3d" % (offset, len(reads[offset]), len(writes[offset])))
        if rnames:
            print("            read by : %s" % ", ".join(rnames[:8]))
        if wnames:
            print("            written : %s" % ", ".join(wnames[:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
