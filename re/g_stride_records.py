# -*- coding: utf-8 -*-
"""Arrays with a constant stride written as a displacement: `lea reg, [base + index*1 + STRIDE]`.

Usage: python g_stride_records.py 0x50 [--top 20]

re/g_arrays.py matched any scaled memory reference, which includes `mov [rcx], eax`-style addressing, so its stride groups
were noise. The shape that actually identifies an array of records with a known size is a scaled index with the stride in the
DISPLACEMENT:

    lea rdx, [rcx + rax*1 + 0x50]     ; element index+1 of an array of 0x50 byte records
    mov r12, [rdx + 0x18]             ; a field of that record

or a scaled index with a shifted count. This scans for the first form, groups by the stride, and reports the field set and
the functions for each -- which is the record's layout.

`0x50` is the stride this project needs: the order's destructor 0x5007C0 releases arrays of 0x50 byte records whose fields are
unknown, and the same 0x50 appears in the strategies.
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
LEA_STRIDE = re.compile(r"^([a-z0-9]+), \[([a-z0-9]+) \+ ([a-z0-9]+)\*1 \+ (0x[0-9a-f]+)\]$")
LEA_STRIDE_SCALED = re.compile(r"^([a-z0-9]+), \[([a-z0-9]+) \+ ([a-z0-9]+)\*([248]) \+ (0x[0-9a-f]+)\]$")
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


def main(argv):
    want = int(argv[0], 0) if argv and argv[0].startswith("0x") else 0x50
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 20
    profile = load_prof()

    shapes = defaultdict(set)
    sites = defaultdict(list)
    for addr, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        body = [i for i in disasm(addr) if i.address < addr + size]
        derived = {}
        for index, ins in enumerate(body):
            m = LEA_STRIDE.match(ins.op_str) or LEA_STRIDE_SCALED.match(ins.op_str)
            if ins.mnemonic != "lea" or not m:
                continue
            stride = 1 if m.lastindex == 4 else int(m.group(4))
            displacement = int(m.group(m.lastindex), 16)
            derived[canonical(m.group(1))] = stride * displacement if stride > 1 else displacement
            sites[displacement].append((addr, ins.address, stride))
        fields = {}
        for ins in body:
            for m in ACCESS.finditer(ins.op_str):
                reg = canonical(m.group(1))
                if reg in derived and m.group(2):
                    fields[int(m.group(2), 16)] = max(fields.get(int(m.group(2), 16), 0), width_of(ins.op_str))
        if fields and want in sites:
            pass
        for displacement in set(sites):
            pass
        # attribute this function's fields to the stride it used
        for reg, displacement in derived.items():
            pass
        if fields and derived:
            for displacement in set(derived.values()):
                shapes[displacement].add(addr)

    # the focused answer for the stride asked about
    print("arrays whose stride is written as a displacement of 0x%X:" % want)
    print("")
    count = 0
    for addr, iaddr, stride in sorted((a, i, s) for d in (want,) for a, i, s in sites.get(d, [])):
        size = (profile.get(addr) or {}).get("size")
        label = N.direct(addr) or ""
        print("    0x%-8X %6s B  lea at 0x%-8X scale %d  %s" % (addr, size, iaddr, stride, label))
        count += 1
        if count >= top:
            break
    if count == 0:
        print("    none")
    print("")
    print("the record's fields, from the functions that derive such an address:")
    aggregate = {}
    for addr, iaddr, stride in sites.get(want, []):
        size = (profile.get(addr) or {}).get("size") or 0
        body = [i for i in disasm(addr) if i.address < addr + size]
        derived = {}
        for ins in body:
            m = LEA_STRIDE.match(ins.op_str)
            if ins.mnemonic == "lea" and m and int(m.group(4), 16) == want:
                derived[canonical(m.group(1))] = want
        for ins in body:
            for m in ACCESS.finditer(ins.op_str):
                reg = canonical(m.group(1))
                if reg in derived and m.group(2):
                    offset = int(m.group(2), 16)
                    aggregate[offset] = max(aggregate.get(offset, 0), width_of(ins.op_str))
    if aggregate:
        print("    %s" % " ".join("+0x%X:%s" % (o, aggregate[o] or "?") for o in sorted(aggregate)))
    else:
        print("    no field access through the derived register was found in those functions")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
