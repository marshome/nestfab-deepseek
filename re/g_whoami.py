# -*- coding: utf-8 -*-
"""Ask which class a function belongs to, and which vtable slot it is.

Usage: python g_whoami.py 0x2AB0 0x5007C0 0x870070 0x92ECB0
       python g_whoami.py --named          (every function the naming channels recovered, with its class)
       python g_whoami.py --closure 51     (everything in a closure, with its class)

A vtable slot IS a virtual method, so the class comes from the compiler's own RTTI and needs no reading. This is the lookup
that turns "0x5007C0 is 716 bytes" into "0x5007C0 is slot 3 of the class whose vtable is 0xA3B470", and it costs nothing:
re/vtables.json has the slot RVAs and the class names, and the slot RVAs are plain RVAs.

Bound methods additionally report the object offsets the method touches through its first argument, which is that class's
member region seen from one of its own methods.
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


def canonical(reg):
    return ALIAS.get(reg, reg)


def width_of(text):
    for name, width in WIDTHS:
        if name in text:
            return width
    return 0


_SLOTS = None


def slots():
    """slot rva -> (class vtable rva, class name, slot index)."""
    global _SLOTS
    if _SLOTS is not None:
        return _SLOTS
    data = json.load(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8"))
    index = {}
    for mangled, info in data.items():
        name = mangled
        if name.startswith("N"):
            name = name[1:]
        if name.endswith("E"):
            name = name[:-1]
        parts = []
        for match in re.finditer(r"(\d+)([A-Za-z_][A-Za-z0-9_]*)", name):
            parts.append(match.group(2)[:int(match.group(1))])
        readable = "::".join(p for p in parts if not p.startswith("__cxx11")) or mangled
        for index_in_table, slot in enumerate(info.get("slots") or []):
            if slot is None:
                continue
            index.setdefault(slot, []).append((info.get("vtable_rva") or 0, readable, index_in_table))
    _SLOTS = index
    return index


def object_fields(addr, profile):
    """offset -> width, for the object the function takes as its first argument."""
    size = (profile.get(addr) or {}).get("size") or 0
    if size <= 0:
        return {}
    body = [i for i in disasm(addr) if i.address < addr + size]
    carries = {"rcx"}
    for _round in range(3):
        for ins in body:
            m = MOVE.match(ins.op_str)
            if ins.mnemonic == "mov" and m and canonical(m.group(2)) in carries:
                carries.add(canonical(m.group(1)))
    out = {}
    for ins in body:
        for m in ACCESS.finditer(ins.op_str):
            if canonical(m.group(1)) in carries and m.group(2):
                offset = int(m.group(2), 16)
                out[offset] = max(out.get(offset, 0), width_of(ins.op_str))
    return out


def main(argv):
    profile = load_prof()
    index = slots()

    if "--named" in argv:
        reg = json.load(io.open(os.path.join(HERE, "name_registry.json"), encoding="utf-8"))
        bound = 0
        free = 0
        for key, value in sorted(reg.items(), key=lambda kv: int(kv[0], 16)):
            own = [v for v in value.get("via") or [] if not v.startswith("via ")]
            if not value.get("methods") or not own:
                continue
            addr = int(key, 16)
            entries = index.get(addr)
            label = value["methods"][0]
            if entries:
                vtable, cls, position = entries[0]
                print("0x%-8X %-34s = %s::(slot %d)   vtable 0x%X" % (addr, label, cls, position, vtable))
                bound += 1
            else:
                free += 1
        print("")
        print("named functions that are virtual methods: %d   free or non-virtual: %d" % (bound, free))
        return 0

    if "--closure" in argv:
        ordinal = int(argv[argv.index("--closure") + 1])
        import g_leverage as L
        table = json.loads(io.open(os.path.join(HERE, "exports_table.json"), encoding="utf-8").read())
        root = None
        for e in table:
            if (e.get("ords") or [0])[0] == ordinal:
                root = e["rva"]
                break
        if root is None:
            print("ordinal not found")
            return 2
        seen = {root}
        queue = [root]
        while queue:
            a = queue.pop()
            for c in (profile.get(a) or {}).get("callees") or []:
                if c in profile and c not in seen:
                    seen.add(c)
                    queue.append(c)
        bound = 0
        for addr in sorted(seen):
            entries = index.get(addr)
            if not entries:
                continue
            vtable, cls, position = entries[0]
            bound += 1
            print("0x%-8X %-32s %s::(slot %d)" % (addr, N.direct(addr) or "", cls, position))
        print("")
        print("closure of ordinal %d: %d functions, %d of them virtual methods" % (ordinal, len(seen), bound))
        return 0

    addrs = [int(a, 0) for a in argv if a.startswith("0x")]
    if not addrs:
        print("give one or more function addresses, or --named, or --closure ORDINAL")
        return 2
    for addr in addrs:
        size = (profile.get(addr) or {}).get("size")
        label = N.direct(addr) or ""
        print("0x%X  %s B  %s" % (addr, size, label))
        entries = index.get(addr) or []
        if not entries:
            print("    not a virtual method (no vtable holds this address)")
        for vtable, cls, position in entries:
            print("    vtable 0x%-8X class %-30s slot %d" % (vtable, cls, position))
        fields = object_fields(addr, profile)
        if fields:
            print("    object offsets: %s" % " ".join("+0x%X:%s" % (o, fields[o] or "?") for o in sorted(fields)))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
