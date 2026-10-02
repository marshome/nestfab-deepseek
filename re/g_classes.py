# -*- coding: utf-8 -*-
"""Every class in the module, its virtual methods, and the object offsets each one touches.

Usage: python g_classes.py [--min-slots 3] [--top 40] [--class NAME] [--members]

re/vtables.json has 443 vtables with demangled class names and their slot RVAs, and the slots are plain RVAs -- verified by
disassembling one. That makes it a source this project has never used: the class name of a function, with no call graph and
no name recovery involved.

For each class this prints its methods with, per slot, the offsets the method touches through its FIRST argument -- the
object -- which is the class's own member layout seen from the outside. Three things fall out of that:

  * a class whose methods all agree on a range of offsets is a type with a known member list;
  * a method can be NAMED by the module (the assertion channel) and still have no class, and a method can have a class and no
    name; the two together give Class::Method;
  * two classes whose member offsets coincide are the same layout reached through different vtables, which is how a base
    class shows itself.

`--members` prints, for one class, the union of the offsets its methods touch, which is the closest thing to a declaration
that the data supports.
"""
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_leverage as L          # noqa: E402
import g_names as N             # noqa: E402
import g_toolchain as T         # noqa: E402
from lib import disasm, load_prof  # noqa: E402

ACCESS = re.compile(r"\[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\]")
MOVE = re.compile(r"^([a-z0-9]+), ([a-z0-9]+)$")
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


def this_offsets(addr, profile):
    """(offsets, sizes) for the object the method's first argument points at."""
    size = (profile.get(addr) or {}).get("size") or 0
    if size <= 0:
        return {}, 0
    body = [i for i in disasm(addr) if i.address < addr + size]
    carries = {"rcx"}
    for _round in range(4):
        for ins in body:
            m = MOVE.match(ins.op_str)
            if ins.mnemonic == "mov" and m and canonical(m.group(2)) in carries:
                carries.add(canonical(m.group(1)))
    offsets = {}
    for ins in body:
        for m in ACCESS.finditer(ins.op_str):
            if canonical(m.group(1)) in carries and m.group(2):
                offsets[int(m.group(2), 16)] = offsets.get(int(m.group(2), 16), 0) + 1
    return offsets, size


def main(argv):
    only = argv[argv.index("--class") + 1] if "--class" in argv else None
    show_members = "--members" in argv
    min_slots = int(argv[argv.index("--min-slots") + 1]) if "--min-slots" in argv else 3
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 40
    profile = load_prof()
    data = json.load(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8"))

    rows = []
    for name, info in data.items():
        slots = [s for s in (info.get("slots") or []) if s in profile]
        if len(slots) < min_slots:
            continue
        rows.append((len(slots), name, slots))
    rows.sort(key=lambda r: -r[0])

    print("classes with %d+ slots in the profile: %d" % (min_slots, len(rows)))
    print("")
    shown = 0
    for nslots, name, slots in rows:
        if only and only not in name:
            continue
        shown += 1
        if shown > top:
            break
        tally = Counter()
        named = []
        for index, slot in enumerate(slots):
            offsets, size = this_offsets(slot, profile)
            for offset, count in offsets.items():
                tally[offset] += 1
            label = N.direct(slot)
            if label:
                named.append((index, label, slot, size))
        print("=== %-52s %2d slots" % (name[:52], nslots))
        if named:
            for index, label, slot, size in named[:6]:
                print("      slot %-3d %-30s 0x%-8X %5d B  (named by the module)" % (index, label, slot, size))
        busiest = [o for o, c in tally.most_common(14)]
        if busiest:
            print("      object offsets its methods touch: %s" % " ".join("+0x%X" % o for o in sorted(busiest)))
        if show_members and tally:
            union = sorted(tally)
            print("      union of all offsets: %s" % " ".join("+0x%X" % o for o in union[:40]))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
