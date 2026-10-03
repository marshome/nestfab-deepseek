# -*- coding: utf-8 -*-
"""Count the SSE argument registers too, because a probe that reads only rcx/rdx/r8/r9 REFUSES a function that takes doubles.

**THE THIRD TIME THE PROBE WAS THE WRONG SIDE.** It refused `SetMarkMode` on "the module reads 2 argument(s) and `setMarkMode_188D0` takes 4", and the function is:

    0188EB  mov rsi, rcx          ; argument 1
    0188EE  mov ebp, edx          ; argument 2
    0188F0  movapd xmm7, xmm2     ; **argument 3, a double**
    0188F4  movapd xmm6, xmm3     ; **argument 4, a double**

**so the implementation's `(void* order, int flag, double first, double second)` is exactly right and the refusal was the tool's.** The Windows x64 calling
convention puts the first four floating-point arguments in xmm0..xmm3, so a function that takes two ints and two doubles reads rcx, edx, xmm2 and xmm3 -- and a
rule that only knows the integer registers cannot see half of it.

**AND THE ORDER MATTERS WHEN THE TWO KINDS ARE MIXED.** Positionally, rcx/rdx/r8/r9 and xmm0..xmm3 are separate sequences, so `(void*, int, double, double)` is
rcx, edx, xmm2, xmm3 -- **the xmm index is NOT the argument index.** This counts each kind separately.
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))

from lib import disasm, load_prof  # noqa: E402

INTEGER = ["rcx", "rdx", "r8", "r9"]
HALVES = {"ecx": "rcx", "edx": "rdx", "r8d": "r8", "r9d": "r9",
          "cx": "rcx", "dx": "rdx", "r8w": "r8", "r9w": "r9",
          "cl": "rcx", "dl": "rdx", "r8b": "r8", "r9b": "r9"}
# xmm0 is never an argument: the first floating-point argument is xmm0, so the four are xmm0..xmm3
XMM = ["xmm0", "xmm1", "xmm2", "xmm3"]


def used(address, size, limit=60):
    integers, floats = set(), set()
    count = 0
    for instruction in disasm(address):
        if instruction.address >= address + size or count >= limit:
            break
        count += 1
        destination, _sep, source = instruction.op_str.partition(",")
        first = destination.strip().split(" ")[-1]
        for whole in INTEGER:
            for form in [whole] + [half for half, parent in HALVES.items() if parent == whole]:
                if re.search(r"\b%s\b" % re.escape(form), source) and first != form:
                    integers.add(whole)
        for whole in XMM:
            if re.search(r"\b%s\b" % re.escape(whole), source) and first != whole:
                floats.add(whole)
    return integers, floats


def main():
    api = io.open(os.path.join(ROOT, "lcns", "src", "api_exports.cpp"), encoding="utf-8", errors="replace").read()
    forwarding = io.open(os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc"),
                         encoding="utf-8", errors="replace").read()
    header = io.open(os.path.join(ROOT, "lcns", "include", "lcns", "exports_impl.hpp"), encoding="utf-8",
                     errors="replace").read()
    profile = load_prof()

    entries = [(int(m.group(1)), m.group(2)) for m in
               re.finditer(r"^\s*\{(\d+),\s*reinterpret_cast<void\*>\(&([\w:]+)\)\}", forwarding, re.M)]
    rows = re.findall(r'\{"([^"]+)",\s*(\d+),\s*(\d+),\s*0x([0-9A-Fa-f]+)u,\s*(\d+)u,', api)
    info = {int(row[1]): (row[0], int(row[3], 16), int(row[4])) for row in rows}
    wrappers = {}
    for match in re.finditer(r'extern "C"[^;{]*?\b(\w+)\s*\([^)]*\)\s*\{(.*?)\n\}', api, re.S):
        wrappers[match.group(1)] = " ".join(match.group(2).split())

    print("the ordinals whose wrapper does NOT dispatch, with the module's arguments counted BOTH ways")
    print("%-5s %-34s %-22s %s" % ("ord", "export", "module reads", "implementation takes"))
    for ordinal, symbol in sorted(entries):
        name, rva, size = info.get(ordinal, (None, 0, 0))
        if name is None or "impl::" in wrappers.get(name, ""):
            continue
        integers, floats = used(rva, size)
        short = symbol.split("::")[-1]
        declaration = re.search(r"^[^\n]*\b%s\s*\(([^;]*)\)\s*;" % re.escape(short), header, re.M)
        takes = declaration.group(1) if declaration else "(no declaration)"
        print("%-5d %-34s %-22s %s"
              % (ordinal, name[:34], "%d int + %d xmm" % (len(integers), len(floats)), takes[:44]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
