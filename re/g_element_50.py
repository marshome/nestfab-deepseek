# -*- coding: utf-8 -*-
"""The 0x50 byte element, and the instruction that gives its size.

Usage: python g_element_50.py [--top 20]

The 0x50 byte records the order's destructor 0x5007C0 releases were being looked for as an array with the stride in a
displacement. That is the wrong shape. The compiler computes the element size when it needs an element's address:

    lea rdi, [rax + rax*4]      ; rax * 5
    shl rdi, 3                  ; * 8  = rax * 40 = 0x50

and the container's end is the same arithmetic:

    lea rax, [rcx + 0x28]       ; the inline buffer
    sub rdx, rax
    shr rdx, 3                  ; the element count
    lea r14, [rsi + rdx*8 + 0x50]   ; rsi + count * 8 + 0x50 -- the END pointer

so `lea rdi,[rax+rax*4] ; shl rdi,3` is the marker that says "elements of 0x50 bytes", and a function that contains it is
one that indexes such an array. This finds those functions, and then reports the fields reached through the register the
multiply produced -- which is the element's layout.

That is how a type whose size is not written anywhere becomes visible: the size is computed, and the computation is
findable.
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
LEA5 = re.compile(r"^([a-z0-9]+), \[([a-z0-9]+) \+ ([a-z0-9]+)\*4\]$")
SHL3 = re.compile(r"^([a-z0-9]+), 3$")
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


def element_registers(body):
    """The registers that hold a 0x50 byte element address: lea reg,[a + b*4] followed by shl reg,3."""
    out = set()
    for index, ins in enumerate(body):
        m = LEA5.match(ins.op_str)
        if ins.mnemonic != "lea" or not m:
            continue
        reg = canonical(m.group(1))
        for follow in body[index + 1:index + 3]:
            s = SHL3.match(follow.op_str)
            if follow.mnemonic == "shl" and s and canonical(s.group(1)) == reg:
                out.add(reg)
                break
    return out


def main(argv):
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 20
    profile = load_prof()

    hits = []
    aggregate = {}
    for addr, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        body = [i for i in disasm(addr) if i.address < addr + size]
        regs = element_registers(body)
        if not regs:
            continue
        fields = {}
        for ins in body:
            for m in ACCESS.finditer(ins.op_str):
                if canonical(m.group(1)) in regs and m.group(2):
                    offset = int(m.group(2), 16)
                    fields[offset] = max(fields.get(offset, 0), width_of(ins.op_str))
                    aggregate[offset] = max(aggregate.get(offset, 0), width_of(ins.op_str))
        hits.append((addr, size, sorted(fields.items()), regs))

    print("functions that compute a 0x50 byte element address (lea reg,[a+b*4] then shl reg,3): %d" % len(hits))
    print("")
    for addr, size, fields, regs in sorted(hits, key=lambda h: -h[1])[:top]:
        label = N.direct(addr) or ""
        print("    0x%-8X %6d B  element fields: %-42s %s"
              % (addr, size, " ".join("+0x%X:%s" % (o, w or "?") for o, w in fields[:8]) or "-", label))
    print("")
    print("the element's fields, aggregated over every function that indexes one:")
    if aggregate:
        print("    %s" % " ".join("+0x%X:%s" % (o, aggregate[o] or "?") for o in sorted(aggregate)))
    else:
        print("    none -- the functions compute the address but never touch a field through it, which happens when the");
        print("    element is only being moved or freed, as in a destructor.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
