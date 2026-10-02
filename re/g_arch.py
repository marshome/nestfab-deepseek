# -*- coding: utf-8 -*-
"""The module's class list: every vtable, its size, its member offsets, and whether this project has touched it.

Usage: python g_arch.py [--min-slots 4] [--top 60] [--own] [--class NAME]

re/vtables.json is RTTI the compiler emitted and nobody had used: 443 vtables with demangled class names and slot RVAs that
are plain RVAs, so each class comes with its virtual method bodies. For each class this reports

  * the vtable address, so the same layout reached through two vtables can be recognised;
  * the number of slots and the object offsets the methods touch through their first argument, which is the member region;
  * how many of the methods this project has already identified, implemented, verified or classified -- so the list is also a
    progress map by class rather than by function;
  * the module's own name for any method the naming channels recovered, which is how a class gets a readable method list.

`--own` keeps only the classes whose namespace is this module's (Multi, Engine, Structure, Tiling, Nesting, Exact, Verify,
Geom, and the few that carry no namespace), which drops CryptoPP, Coin, Clp and the standard library.
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

THIRD_PARTY = ("CryptoPP", "Coin", "Clp", "Osi", "boost", "std::", "__gnu_cxx", "Json", "locale", "basic_")


def canonical(reg):
    return ALIAS.get(reg, reg)


def pretty(mangled):
    """Decode just enough of the Itanium mangling to read a class name: the length-prefixed components."""
    text = mangled
    if text.startswith("_Z"):
        text = text[2:]
    if text.startswith("N"):
        text = text[1:]
    if text.endswith("E"):
        text = text[:-1]
    out = []
    for match in re.finditer(r"(\d+)([A-Za-z_][A-Za-z0-9_]*)", text):
        length = int(match.group(1))
        word = match.group(2)[:length]
        out.append(word)
    if not out:
        return mangled
    reserved = {"St": "std", "Sa": "std::allocator", "Sb": "std::basic_string"}
    parts = []
    for word in out:
        if word in reserved:
            word = reserved[word]
        if word.startswith("__cxx11"):
            continue
        parts.append(word)
    name = "::".join(parts)
    return name if name else mangled


def is_third_party(name):
    return any(marker in name for marker in THIRD_PARTY)


def main(argv):
    min_slots = int(argv[argv.index("--min-slots") + 1]) if "--min-slots" in argv else 4
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 60
    own_only = "--own" in argv
    only = argv[argv.index("--class") + 1] if "--class" in argv else None
    profile = load_prof()
    data = json.load(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8"))

    rows = []
    for mangled, info in data.items():
        slots = [s for s in (info.get("slots") or []) if s in profile]
        if len(slots) < min_slots:
            continue
        name = pretty(mangled)
        if own_only and is_third_party(name):
            continue
        if only and only.lower() not in name.lower():
            continue
        tally = Counter()
        touched = 0
        for slot in slots:
            size = (profile.get(slot) or {}).get("size") or 0
            if size <= 0:
                continue
            if slot in T.BOILERPLATE or slot in getattr(T, "IMPLEMENTED", ()) or slot in L.VERIFIED:
                touched += 1
            body = [i for i in disasm(slot) if i.address < slot + size]
            carries = {"rcx"}
            for _round in range(3):
                for ins in body:
                    m = MOVE.match(ins.op_str)
                    if ins.mnemonic == "mov" and m and canonical(m.group(2)) in carries:
                        carries.add(canonical(m.group(1)))
            for ins in body:
                for m in ACCESS.finditer(ins.op_str):
                    if canonical(m.group(1)) in carries and m.group(2):
                        tally[int(m.group(2), 16)] += 1
        busiest = [o for o, _c in tally.most_common(16)]
        rows.append((len(slots), name, mangled, info.get("vtable_rva"), touched, busiest))

    rows.sort(key=lambda r: -r[0])
    print("classes (vtables with %d+ slots present): %d%s" % (min_slots, len(rows), "  [own only]" if own_only else ""))
    print("")
    print("%-7s %-44s %5s %6s  %s" % ("vtable", "class", "slots", "known", "member offsets its methods touch"))
    for nslots, name, mangled, vtable, touched, busiest in rows[:top]:
        print("0x%-5X %-44s %5d %6d  %s" % (vtable or 0, name[:44], nslots, touched,
                                            " ".join("+0x%X" % o for o in sorted(busiest)[:12])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
