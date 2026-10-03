# -*- coding: utf-8 -*-
"""Arrays of records: the indexed access pattern, and the field set of the record it walks.

Usage: python g_arrays.py [--min-fields 3] [--top 20] [--stride 0x50]

A member that holds a vector or an array of records is visible in the instructions the same way an embedded sub-object is,
but with a scaled index:

    mov rax, [rbx + 0x10]        ; the array's begin
    lea rdx, [rax + rcx*8]       ; the element, stride 8
    mov r12, [rdx + 0x18]        ; a field of the element
    lea rsi, [rdx + 0x30]        ; the element's inline buffer

so the shape is a scaled index (rcx*8, rcx*2, or a shift) followed by constant offsets from the indexed register. This
reports, per stride, the field sets reached through such a register -- which is the record's layout -- and the functions that
walk it, with their recovered names.

`--stride 0x50` answers a specific question this project has open: the order's destructor releases arrays of 0x50 byte records
whose fields are unknown, and the same 0x50 stride appears in the strategies' methods.
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
SCALED = re.compile(r"^([a-z0-9]+), \[([a-z0-9]+) \+ ([a-z0-9]+)\*([1248])\]$")
SCALED_SHIFT = re.compile(r"^([a-z0-9]+), \[([a-z0-9]+) \+ ([a-z0-9]+)\]$")
LEA_DIRECT = re.compile(r"^([a-z0-9]+), \[([a-z0-9]+) \+ ([a-z0-9]+)\*([1248])\]$")
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


def walked_records(body):
    """stride -> {field offset: width} for registers derived as a scaled element address."""
    derived = {}
    for ins in body:
        m = LEA_DIRECT.match(ins.op_str)
        if ins.mnemonic == "lea" and m:
            derived[canonical(m.group(1))] = int(m.group(4))
    out = defaultdict(dict)
    for ins in body:
        for m in ACCESS.finditer(ins.op_str):
            reg = canonical(m.group(1))
            if reg not in derived or not m.group(2):
                continue
            stride = derived[reg]
            offset = int(m.group(2), 16)
            out[stride][offset] = max(out[stride].get(offset, 0), width_of(ins.op_str))
    return out


def main(argv):
    min_fields = int(argv[argv.index("--min-fields") + 1]) if "--min-fields" in argv else 3
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 20
    only_stride = int(argv[argv.index("--stride") + 1], 0) if "--stride" in argv else None
    profile = load_prof()

    by_stride = defaultdict(lambda: defaultdict(set))
    for addr, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        body = [i for i in disasm(addr) if i.address < addr + size]
        for stride, fields in walked_records(body).items():
            if len(fields) < min_fields:
                continue
            if only_stride is not None and stride != only_stride:
                continue
            by_stride[stride][tuple(sorted(fields.items()))].add(addr)

    print("record strides visible as a scaled index, with the fields reached through the element register:")
    print("")
    rows = []
    for stride, shapes in by_stride.items():
        for shape, fns in shapes.items():
            rows.append((len(fns), stride, shape, fns))
    rows.sort(key=lambda r: (-r[0], r[1]))
    shown = 0
    for count, stride, shape, fns in rows:
        if shown >= top:
            break
        shown += 1
        labels = sorted(set(N.direct(a) for a in fns if N.direct(a)))
        print("=== stride 0x%-4X  %d functions  %d fields" % (stride, count, len(shape)))
        print("    fields: %s" % " ".join("+0x%X:%s" % (o, w or "?") for o, w in shape[:22]))
        if labels:
            print("    named among them: %s" % ", ".join(labels[:8]))
        print("    e.g. %s" % ", ".join("0x%X" % f for f in sorted(fns)[:6]))
        print("")
    if only_stride is not None and only_stride not in by_stride:
        print("no function derives a record address at stride 0x%X with %d+ fields" % (only_stride, min_fields))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
