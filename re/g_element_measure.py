# -*- coding: utf-8 -*-
"""The element measurement 0x524EE0: its callees, its writes, and what it is for.

The previous attempt reported ZERO direct calls for a function the profile says has twenty callees, and the reason was in the
command line rather than the code: a `$` anchor written through PowerShell's quoting became a literal backslash-dollar, so the
pattern required a real dollar sign at the end of an operand. **The tool was right and the invocation was wrong**, which is the
fifth time this session that a number which could not be true pointed at the machinery -- and the first time the machinery was a
shell rather than a script.

This reads the function properly and records: its callees and their sizes, the offsets it writes on its first argument, and the
strings it builds.
"""
import collections
import glob
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import lib as LIB  # noqa: E402
from lib import disasm, load_prof, rva2off  # noqa: E402

TARGET = 0x524EE0
DIRECT = re.compile(r"^0x([0-9a-f]+)$")
ACCESS = re.compile(r"\[([a-z0-9]+)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\]")
PRINTABLE = re.compile(rb"[\x20-\x7e]{4,}")
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


def layout_names():
    out = {}
    for line in io.open(os.path.join(ROOT, "lcns", "include", "lcns", "launching_order.hpp"),
                        encoding="utf-8", errors="replace").read().split("\n"):
        m = re.match(r"\s*(?:std::uint\d+_t|double|unsigned char)\s+(\w+);\s*//\s*\+0x([0-9A-Fa-f]+)", line)
        if m:
            out[int(m.group(2), 16)] = m.group(1)
    return out


def main():
    profile = load_prof()
    size = (profile.get(TARGET) or {}).get("size") or 0
    body = [i for i in disasm(TARGET) if i.address < TARGET + size]
    print("0x%X  %d bytes  %d instructions  callers %d" % (TARGET, size, len(body),
                                                           len((profile.get(TARGET) or {}).get("callers") or [])))

    calls = [int(m.group(1), 16) for ins in body if ins.mnemonic == "call"
             for m in [DIRECT.match(ins.op_str.strip())] if m]
    counted = collections.Counter(calls)
    # a call whose target lands INSIDE this function is a local jump, not a callee
    inside = {t for t in counted if TARGET <= t < TARGET + size}
    print("direct calls: %d, distinct %d, of which INSIDE this function: %d" % (len(calls), len(counted), len(inside)))
    print("")
    print("%-12s %-5s %-8s %s" % ("target", "times", "bytes", "note"))
    for target, times in counted.most_common(14):
        info = profile.get(target) or {}
        note = "inside this function" if target in inside else ""
        print("0x%-10X %-5d %-8s %s" % (target, times, info.get("size"), note))
    print("")

    # the offsets reached through the FIRST argument and its copies
    carries = {"rcx"}
    for _round in range(3):
        for ins in body:
            m = re.match(r"^([a-z0-9]+), ([a-z0-9]+)$", ins.op_str)
            if ins.mnemonic == "mov" and m and canonical(m.group(2)) in carries:
                carries.add(canonical(m.group(1)))
    known = layout_names()
    offsets = collections.Counter()
    for ins in body:
        for m in ACCESS.finditer(ins.op_str.replace(" ", "")):
            if canonical(m.group(1)) in carries and m.group(2):
                offsets[int(m.group(2), 16)] += 1
    print("offsets reached through the first argument's registers: %d" % len(offsets))
    for offset, times in sorted(offsets.items())[:20]:
        print("    +0x%-6X x%-3d %s" % (offset, times, known.get(offset, "")))
    print("")

    blob = LIB.data() if callable(getattr(LIB, "data", None)) else LIB.data
    words = []
    for match in PRINTABLE.finditer(blob):
        pass
    for ins in body:
        m = re.search(r"movabs\s+r[a-z0-9]+, (0x[0-9a-f]+)", ins.op_str)
        if m:
            value = int(m.group(1), 16)
            raw = value.to_bytes(8, "little")
            if all(32 <= b < 127 for b in raw):
                words.append((ins.address, raw.decode("ascii")))
    print("strings built from immediates inside this function: %d" % len(words))
    for address, text in words[:10]:
        print("    0x%-8X %r" % (address, text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
