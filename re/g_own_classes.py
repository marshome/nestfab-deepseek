# -*- coding: utf-8 -*-
"""The module's own classes, one line each: vptr, size in slots, member region, and the fields' widths.

Usage: python g_own_classes.py [--top 80] [--fields VTABLE_RVA]

re/vtables.json is RTTI the compiler emitted, and its slot RVAs are plain RVAs, so each class arrives with its virtual method
bodies. This lists only the classes that belong to this module -- Multi, Tiling, Utils, RCompact, Engine, Structure and the few
without a namespace -- and for each one gives:

    vptr        the vtable's rva, so a vtable pointer stored in an object can be matched to it
    slots       how many virtual methods it has
    members     the union of the offsets its methods touch through their first argument, which is the object
    widths      for each of those offsets, the width of the access, which is what a declaration needs

`--fields` prints one class's member list in the form a struct would be written in, with the width of every field.
"""
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_names as N             # noqa: E402
from lib import disasm, load_prof  # noqa: E402

ACCESS = re.compile(r"\[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\]")
MOVE = re.compile(r"^([a-z0-9]+), ([a-z0-9]+)$")
WIDTHS = (("xmmword", 16), ("oword", 16), ("qword", 8), ("dword", 4), ("word", 2), ("byte", 1))
ALIAS = {}
for _full, _names in {"rax": ("eax", "ax", "al"), "rbx": ("ebx", "bx", "bl"), "rcx": ("ecx", "cx", "cl"),
                      "rdx": ("edx", "dx", "dl"), "rsi": ("esi", "si", "sil"), "rdi": ("edi", "di", "dil")}.items():
    ALIAS[_full] = _full
    for _n in _names:
        ALIAS[_n] = _full
for _r in range(8, 16):
    for _s in ("", "d", "w", "b"):
        ALIAS["r%d%s" % (_r, _s)] = "r%d" % _r

THIRD_PARTY = ("CryptoPP", "Coin", "Clp", "Osi", "boost", "std", "__cxxabiv1", "Json", "locale", "basic_", "N5boost")


def canonical(reg):
    return ALIAS.get(reg, reg)


def width_of(text):
    for name, width in WIDTHS:
        if name in text:
            return width
    return 0


def pretty(mangled):
    text = mangled
    if text.startswith("_Z"):
        text = text[2:]
    if text.startswith("N"):
        text = text[1:]
    if text.endswith("E"):
        text = text[:-1]
    parts = []
    for match in re.finditer(r"(\d+)([A-Za-z_][A-Za-z0-9_]*)", text):
        length = int(match.group(1))
        word = match.group(2)[:length]
        if word.startswith("__cxx11"):
            continue
        parts.append(word)
    name = "::".join(parts)
    return name if name else mangled


def class_fields(slots, profile):
    """(offset -> rva that shows it, offset -> width) for the object the methods take as their first argument."""
    seen = {}
    widths = {}
    for slot in slots:
        size = (profile.get(slot) or {}).get("size") or 0
        if size <= 0:
            continue
        body = [i for i in disasm(slot) if i.address < slot + size]
        carries = {"rcx"}
        for _round in range(3):
            for ins in body:
                m = MOVE.match(ins.op_str)
                if ins.mnemonic == "mov" and m and canonical(m.group(2)) in carries:
                    carries.add(canonical(m.group(1)))
        for ins in body:
            for m in ACCESS.finditer(ins.op_str):
                if canonical(m.group(1)) not in carries or not m.group(2):
                    continue
                offset = int(m.group(2), 16)
                seen.setdefault(offset, slot)
                widths[offset] = max(widths.get(offset, 0), width_of(ins.op_str))
    return seen, widths


def main(argv):
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 80
    only_vtable = int(argv[argv.index("--fields") + 1], 0) if "--fields" in argv else None
    profile = load_prof()
    data = json.load(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8"))

    rows = []
    for mangled, info in data.items():
        name = pretty(mangled)
        if any(marker in name or marker in mangled for marker in THIRD_PARTY):
            continue
        slots = [s for s in (info.get("slots") or []) if s in profile]
        if not slots:
            continue
        seen, widths = class_fields(slots, profile)
        rows.append((info.get("vtable_rva") or 0, name, mangled, slots, seen, widths))
    rows.sort()

    if only_vtable is not None:
        for vtable, name, mangled, slots, seen, widths in rows:
            if vtable != only_vtable:
                continue
            print("class %s   vtable 0x%X   %d slots" % (name, vtable, len(slots)))
            for slot in slots:
                label = N.direct(slot)
                print("    slot 0x%-8X %6s B  %s" % (slot, (profile.get(slot) or {}).get("size"), label or ""))
            print("")
            print("the object's fields, as the methods reveal them:")
            previous = 0
            for offset in sorted(seen):
                if offset > previous:
                    print("    unsigned char unnamed%03X[0x%X];%s" % (previous, offset - previous,
                                                                      "   // not touched by any method" if offset - previous > 1 else ""))
                width = widths.get(offset, 0)
                kind = {1: "std::uint8_t", 2: "std::uint16_t", 4: "std::uint32_t", 8: "std::uint64_t",
                        16: "unsigned char[16]"}.get(width, "unsigned char[?]")
                print("    %-20s field%03X;%s" % (kind, offset, ("   // shown by 0x%X" % seen[offset])))
                previous = offset + max(width, 1)
            return 0
        print("no class with vtable 0x%X" % only_vtable)
        return 2

    print("this module's classes (vtable, class, slots, member region):")
    print("")
    print("%-9s %-34s %5s  %s" % ("vtable", "class", "slots", "member offsets, low to high"))
    for vtable, name, mangled, slots, seen, widths in rows[:top]:
        offsets = sorted(seen)
        text = " ".join("+0x%X" % o for o in offsets[:16])
        if len(offsets) > 16:
            text += " ... %d more" % (len(offsets) - 16)
        print("0x%-7X %-34s %5d  %s" % (vtable, name[:34], len(slots), text))
    print("")
    print("%d classes in this module" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
