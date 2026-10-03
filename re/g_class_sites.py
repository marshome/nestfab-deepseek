# -*- coding: utf-8 -*-
"""Where each class is constructed, and how big its objects are.

Usage: python g_class_sites.py [--top 60] [--class NAME]

A class's vtable address is stored into the object by its constructor, so the instruction that materialises the vtable is the
place where the class is built:

    lea rax, [rip + disp]      ; the vtable address
    mov qword ptr [rcx], rax   ; installed into the object

Finding those two together gives, for every class in re/CLASSES.md, the functions that construct it and the object offset
they install it at. That is the module's object graph: which types exist, where they are created, and -- when the constructor
also allocates -- how large they are, since a `mov ecx, N ; call operator new` immediately before is the allocation.

This is the skeleton the frequency tools could not produce, and it comes from the compiler's own RTTI plus the store that
uses it.
"""
import io
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib as LIB               # noqa: E402
from lib import disasm, load_prof  # noqa: E402

ALLOC = re.compile(r"^ecx, (0x[0-9a-f]+)$")
STORE = re.compile(r"^(qword|dword) ptr \[([a-z0-9]+)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\], ([a-z0-9]+)$")
LEA = re.compile(r"^([a-z0-9]+), \[rip \+ 0x([0-9a-f]+)\]$")


def decode(mangled):
    text = mangled
    if text.startswith("_Z"):
        text = text[2:]
    if text.startswith("N"):
        text = text[1:]
    if text.endswith("E"):
        text = text[:-1]
    parts = []
    for match in re.finditer(r"(\d+)([A-Za-z0-9_]+)", text):
        word = match.group(2)[:int(match.group(1))]
        if word.startswith("__cxx"):
            continue
        parts.append("std" if word == "St" else word)
    return "::".join(parts) or mangled


FOREIGN = ("8CryptoPP", "4Coin", "3Clp", "3Osi", "5boost", "6Json", "NSt", "St", "__cxxabiv1", "__gnu_cxx", "6locale")


def main(argv):
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 60
    only = argv[argv.index("--class") + 1] if "--class" in argv else None
    profile = load_prof()
    data = json.load(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8"))

    # vtable address point (rva and rva + 16, the form a constructor stores) -> class name
    address_points = {}
    for mangled, info in data.items():
        if any(marker in mangled for marker in FOREIGN):
            continue
        rva = info.get("vtable_rva")
        if not rva:
            continue
        name = decode(mangled)
        address_points[rva] = name
        address_points[rva + 16] = name

    sites = defaultdict(list)
    for addr, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        body = [i for i in disasm(addr) if i.address < addr + size]
        allocation = None
        regs = {}
        for index, ins in enumerate(body):
            m = ALLOC.match(ins.op_str)
            if ins.mnemonic == "mov" and m:
                allocation = int(m.group(1), 16)
            lm = LEA.match(ins.op_str)
            if ins.mnemonic == "lea" and lm:
                nxt = body[index + 1].address if index + 1 < len(body) else ins.address + 8
                regs[lm.group(1)] = nxt + int(lm.group(2), 16)
                continue
            sm = STORE.match(ins.op_str)
            if ins.mnemonic == "mov" and sm:
                source = sm.group(4)
                if source in regs and regs[source] in address_points:
                    offset = int(sm.group(3), 16) if sm.group(3) else 0
                    sites[address_points[regs[source]]].append((addr, ins.address, offset, allocation))
    rows = sorted(sites.items(), key=lambda kv: -len(kv[1]))
    print("classes with a construction site found: %d" % len(rows))
    print("")
    shown = 0
    for name, entries in rows:
        if only and only.lower() not in name.lower():
            continue
        shown += 1
        if shown > top:
            break
        allocs = sorted(set(e[3] for e in entries if e[3]))
        print("=== %-34s %2d sites   allocation sizes: %s"
              % (name[:34], len(entries), ", ".join("0x%X" % a for a in allocs) or "-"))
        for addr, iaddr, offset, allocation in entries[:6]:
            print("      0x%-8X installs it at +0x%-4X  %s" % (addr, offset,
                                                               ("after new(0x%X)" % allocation) if allocation else ""))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
