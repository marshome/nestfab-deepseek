# -*- coding: utf-8 -*-
"""Embedded sub-objects: a member whose offsets are reached through a register derived from the parent.

Usage: python g_embedded_structs.py [--min-fields 3] [--top 40] [--class-slot RVA]

A large structure often contains smaller ones by value, and the instructions say so plainly:

    lea rbx, [rcx + 0x120]      ; rbx is the ADDRESS of the member at +0x120, which is a sub-object
    mov eax, [rbx + 0x8]        ; its field at +0x8
    mov [rbx + 0xC], edx        ; and another

so the pattern is a register loaded with the ADDRESS of a member and then dereferenced at constant offsets. That is a
sub-object, and its field set is what the derived register touches -- a declaration that can stand on its own, independent of
the parent.

This walks every function, follows the address derivations (`lea`, and `mov reg, [reg2 + off]` where the result is then
dereferenced), and reports each derived base with the offsets reached through it. Grouped by the parent offset, repeated
bases across many functions are sub-objects; a base used once is a local.

The tool also reports the candidates that recur, because a sub-object is shared: a member that is one type across twenty
functions is a type, and one that differs every time is not.
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_names as N             # noqa: E402
from lib import disasm, load_prof  # noqa: E402

ACCESS = re.compile(r"\[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\]")
LEA_MEMBER = re.compile(r"^([a-z0-9]+), \[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\]$")
MOV_MEMBER = re.compile(r"^([a-z0-9]+), (?:qword ptr )?\[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\]$")
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


def candidates(body):
    """(parent offset, {field offset: width}) for every register the body derives as a member address."""
    derives = {}
    # first pass: registers that carry the address of the first argument's member
    for ins in body:
        m = LEA_MEMBER.match(ins.op_str)
        if ins.mnemonic == "lea" and m and canonical(m.group(2)) == "rcx":
            derives[canonical(m.group(1))] = int(m.group(3), 16) if m.group(3) else 0
        elif ins.mnemonic == "mov" and m and canonical(m.group(2)) == "rcx" and not m.group(3):
            derives[canonical(m.group(1))] = 0
    out = defaultdict(dict)
    for ins in body:
        for m in ACCESS.finditer(ins.op_str):
            reg = canonical(m.group(1))
            if reg not in derives or not m.group(2):
                continue
            offset = int(m.group(2), 16)
            out[derives[reg]][offset] = max(out[derives[reg]].get(offset, 0), width_of(ins.op_str))
    return out


def main(argv):
    min_fields = int(argv[argv.index("--min-fields") + 1]) if "--min-fields" in argv else 3
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 40
    profile = load_prof()

    # parent offset -> shape -> {functions}
    shapes = defaultdict(lambda: defaultdict(set))
    for addr, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        body = [i for i in disasm(addr) if i.address < addr + size]
        for parent, fields in candidates(body).items():
            if len(fields) < min_fields:
                continue
            shape = tuple(sorted(fields.items()))
            shapes[parent][shape].add(addr)

    print("parent offsets with an embedded sub-object candidate (a member whose address is derived):")
    print("")
    rows = []
    for parent, by_shape in shapes.items():
        for shape, fns in by_shape.items():
            rows.append((len(fns), parent, shape, fns))
    rows.sort(key=lambda r: (-len(r[0]), r[1]) if False else (-r[0], r[1]))
    shown = 0
    for count, parent, shape, fns in rows:
        if shown >= top:
            break
        shown += 1
        labels = sorted(set(N.direct(a) for a in fns if N.direct(a)))
        print("=== parent +0x%-4X  %d functions  %d fields" % (parent, count, len(shape)))
        print("    fields: %s" % " ".join("+0x%X:%s" % (o, w or "?") for o, w in shape[:20]))
        if labels:
            print("    named among them: %s" % ", ".join(labels[:6]))
        print("    e.g. %s" % ", ".join("0x%X" % f for f in sorted(fns)[:5]))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
