# -*- coding: utf-8 -*-
"""The member offsets of chosen functions, side by side, for finding a shared type by hand.

Usage: python g_members.py 0x2AB0 0x5007C0 0x870070 0x22A20

Global clustering was the wrong instrument: with a permissive threshold it merges every offset in the module into one
cluster, and with a strict one it fragments into single functions, because the same object is reached through rbx in one
function and r13 in the next. What works is to look at a handful of functions at once and see which offsets they agree on.

For each function this prints, grouped by the register that carries the object:

  * the offsets reached through it, sorted, with the width of the access;
  * a marker when the register was assigned from rcx, which means it carries the FIRST ARGUMENT -- this module's objects
    are almost always the first argument, so that is the column to compare.

Reading two functions down the same column is how the shared types were found by hand: 0x2AB0 and 0x5007C0 both walk the
object at +0x1C8/+0x1D0/+0x1D8, and 0x22A20 and 0x5007C0 both walk the container at +0x250/+0x258.
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

ACCESS = re.compile(r"\[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\]")
MOV_FROM_RCX = re.compile(r"^([a-z0-9]+), rcx$")
WIDTHS = (("xmmword", 16), ("oword", 16), ("qword", 8), ("dword", 4), ("word", 2), ("byte", 1))
STACK = ("rsp", "rbp")


def width_of(text):
    for name, width in WIDTHS:
        if name in text:
            return width
    return 0


def main(argv):
    addrs = [int(a, 0) for a in argv if a.startswith("0x")]
    if not addrs:
        print("give one or more function addresses")
        return 2
    profile = load_prof()
    for addr in addrs:
        size = (profile.get(addr) or {}).get("size") or 0
        body = [i for i in disasm(addr) if i.address < addr + size]
        bases = {"rcx"}
        for ins in body:
            m = MOV_FROM_RCX.match(ins.op_str)
            if ins.mnemonic == "mov" and m:
                bases.add(m.group(1))
        per_base = defaultdict(dict)
        for ins in body:
            for m in ACCESS.finditer(ins.op_str):
                reg = m.group(1)
                if reg in STACK:
                    continue
                offset = int(m.group(2), 16) if m.group(2) else 0
                width = width_of(ins.op_str) or 0
                per_base[reg][offset] = max(per_base[reg].get(offset, 0), width)
        print("=== 0x%X (%d bytes)%s" % (addr, size, ("  " + N.direct(addr)) if N.direct(addr) else ""))
        for reg in sorted(per_base, key=lambda r: (r not in bases, -len(per_base[r]))):
            offsets = per_base[reg]
            if not offsets:
                continue
            mark = " <- first argument" if reg in bases else ""
            items = sorted(offsets.items())
            text = " ".join("+0x%X:%s" % (o, w or "?") for o, w in items)
            print("  %-4s (%2d offsets)%s" % (reg, len(items), mark))
            line = []
            for o, w in items:
                line.append("+0x%X:%s" % (o, w or "?"))
                if len(line) == 12:
                    print("        %s" % " ".join(line))
                    line = []
            if line:
                print("        %s" % " ".join(line))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
