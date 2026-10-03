# -*- coding: utf-8 -*-
"""Class names for the functions the module names: the virtual methods this project has a name for.

Usage: python g_class_methods.py [--min-slots 1] [--top 60]

re/vtables.json maps a slot RVA to a demangled class, and re/name_registry.json maps an RVA to the name the module gives the
function in its own assertion or log line. Join the two and a function that had only a name gets a class as well:

    Class::Method    where Class comes from RTTI and Method from the module's own words

That is a second axis of identification the project has not used, and it is free: neither side needs a body read. This prints
the join, grouped by class, with the object offsets each method touches, so a class's member list builds up from its own
methods rather than from a frequency count.

It also reports the two gaps: functions with a name and no class (free functions, statics, and anything not virtual) and
classes whose methods have no name.
"""
import io
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_names as N             # noqa: E402
from lib import disasm, load_prof  # noqa: E402

ACCESS = re.compile(r"\[([a-z0-9]+)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\]")
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
    size = (profile.get(addr) or {}).get("size") or 0
    if size <= 0:
        return set()
    body = [i for i in disasm(addr) if i.address < addr + size]
    carries = {"rcx"}
    for _round in range(4):
        for ins in body:
            m = MOVE.match(ins.op_str)
            if ins.mnemonic == "mov" and m and canonical(m.group(2)) in carries:
                carries.add(canonical(m.group(1)))
    out = set()
    for ins in body:
        for m in ACCESS.finditer(ins.op_str):
            if canonical(m.group(1)) in carries and m.group(2):
                out.add(int(m.group(2), 16))
    return out


def demangle_simple(name):
    """A readable class name out of the mangled one, without a demangler: the tail before the E, with std substituted."""
    text = name
    if text.startswith("N") and text.endswith("E"):
        text = text[1:-1]
    text = text.replace("St7__cxx11", "std::").replace("St", "std::")
    text = re.sub(r"(\d+)([A-Za-z_][A-Za-z0-9_]*)", lambda m: m.group(2), text)
    return text.replace("N8CryptoPP", "CryptoPP::").replace("CryptoPP", "CryptoPP::", 1) if "CryptoPP" in text else text


def main(argv):
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 60
    profile = load_prof()
    data = json.load(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8"))

    by_class = defaultdict(list)
    seen = {}
    for name, info in data.items():
        for index, slot in enumerate(info.get("slots") or []):
            if slot not in profile or slot in seen:
                continue
            seen[slot] = name
            label = N.direct(slot)
            if label:
                by_class[name].append((index, slot, label))

    total_named_virtual = sum(len(v) for v in by_class.values())
    print("functions the module names that are virtual: %d, across %d classes" % (total_named_virtual, len(by_class)))
    print("")
    rows = sorted(by_class.items(), key=lambda kv: -len(kv[1]))
    shown = 0
    for name, methods in rows:
        shown += 1
        if shown > top:
            break
        print("=== %s  (%d named methods)" % (name[:60], len(methods)))
        for index, slot, label in sorted(methods)[:10]:
            offsets = sorted(this_offsets(slot, profile))
            print("      slot %-3d 0x%-8X %-34s offsets %s" % (index, slot, label,
                                                               " ".join("+0x%X" % o for o in offsets[:8]) or "-"))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
