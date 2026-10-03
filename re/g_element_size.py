# -*- coding: utf-8 -*-
"""Attribute each element register to ITS element size, so the record's fields stop being contaminated.

Usage: python g_element_size.py [--size 0x50] [--top 20]

re/g_element_50.py looked for `lea reg, [a + b*4] ; shl reg, 3` and then collected every offset reached through every such
register in the body. A function that walks two arrays of different element sizes therefore mixed their fields: the aggregate
ran past +0x50 and even to +0xA50, which no 0x50 byte record can contain. The fix is to keep the SIZE WITH THE REGISTER:

    lea rdi, [rax + rax*4]      ; rax * 5
    shl rdi, 3                  ; rdi = index * 40, so RDI belongs to 0x50 byte elements

so `rdi` is only ever used for 0x50 records, and the fields reached through it are that record's fields and nothing else. The
same function may contain `lea rsi, [rcx + rcx*8] ; shl rsi, 3` for 0x48 byte elements, and the two sets are kept apart.

The general shape is worth stating because it is how ANY element size becomes visible: a `lea` that multiplies by k followed by
a shift by s is an element size of k * 2^s, and the register it lands in is that element's register.

This prints, per size, the fields reached through the registers that compute THAT size, and the functions that do it.
"""
import argparse
import io
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_names as N             # noqa: E402
from lib import disasm, load_prof  # noqa: E402

ACCESS = re.compile(r"\[([a-z0-9]+)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\]")# Every pattern below is matched against a SPACE-STRIPPED operand, because that is the only way one pattern reads both
# `lea rdi, [rax + rax*4]` and `lea rdi,[rax+rax*4]`, and capstone produces the spaced form while objdump produces the other.
# Two rounds were lost this session to patterns that assumed one spelling.
LEA_MUL = re.compile(r"^([a-z0-9]+),\[([a-z0-9]+)\+([a-z0-9]+)\*([1248])\]$")
LEA_MUL_DISP = re.compile(r"^([a-z0-9]+),\[([a-z0-9]+)\+([a-z0-9]+)\*([1248])\+(0x[0-9a-f]+)\]$")
SHL = re.compile(r"^([a-z0-9]+),([0-9]+)$")
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
    """register -> (element size, displacement), from `lea reg,[a + b*k]` followed by `shl reg,s`.

    The multiplier is NOT the scale factor. `lea rdi, [rax + rax*4]` computes `rax + rax*4`, which is rax * 5, and the scale
    in the encoding is 4 because the base contributes the implicit 1. Reading the scale as the multiplier gives 0x40 where the
    element is 0x50 -- a 3-byte-per-element error that would have been invisible, since the tool still reported a plausible
    size. So the multiplier is `1 + k` when base and index are the SAME register and `k` when they differ.
    """
    out = {}
    for position, ins in enumerate(body):
        operand = ins.op_str.replace(" ", "")
        m = LEA_MUL.match(operand) or LEA_MUL_DISP.match(operand)
        if ins.mnemonic != "lea" or not m:
            continue
        reg = canonical(m.group(1))
        base, index_register = canonical(m.group(2)), canonical(m.group(3))
        scale = int(m.group(4))
        multiplier = scale + 1 if base == index_register else scale
        displacement = int(m.group(5), 16) if m.lastindex == 5 else 0
        for follow in body[position + 1:position + 3]:
            s = SHL.match(follow.op_str.replace(" ", ""))
            if follow.mnemonic == "shl" and s and canonical(s.group(1)) == reg:
                out[reg] = (multiplier << int(s.group(2)), displacement)
                break
    return out


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=lambda v: int(v, 0), default=None)
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args(argv)
    profile = load_prof()

    by_size = defaultdict(dict)
    functions = defaultdict(set)
    for addr, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        body = [i for i in disasm(addr) if i.address < addr + size]
        registers = element_registers(body)
        if not registers:
            continue
        for reg, (element, _displacement) in registers.items():
            if args.size is not None and element != args.size:
                continue
            functions[element].add(addr)
        for ins in body:
            for m in ACCESS.finditer(ins.op_str.replace(" ", "")):
                reg = canonical(m.group(1))
                if reg not in registers or not m.group(2):
                    continue
                element = registers[reg][0]
                if args.size is not None and element != args.size:
                    continue
                offset = int(m.group(2), 16)
                by_size[element][offset] = max(by_size[element].get(offset, 0), width_of(ins.op_str))

    print("element sizes computed in the module, and the fields reached through the registers that compute them:")
    print("")
    for element in sorted(by_size):
        fields = by_size[element]
        if not fields:
            continue
        print("=== size 0x%-6X  %d functions index it" % (element, len(functions[element])))
        print("    fields: %s" % " ".join("+0x%X:%s" % (o, fields[o] or "?") for o in sorted(fields)))
        inside = [o for o in fields if o < element]
        outside = [o for o in fields if o >= element]
        print("    inside the element: %s" % (" ".join("+0x%X" % o for o in inside) or "none"))
        if outside:
            print("    PAST the element (a different register leaked in): %s" % " ".join("+0x%X" % o for o in outside))
        labels = sorted(set(N.direct(a) for a in functions[element] if N.direct(a)))
        if labels:
            print("    named among the functions: %s" % ", ".join(labels[:6]))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
