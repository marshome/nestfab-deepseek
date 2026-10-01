# -*- coding: utf-8 -*-
"""Function structure analyzer: what a function reads/writes, without printing 400 instructions.

Usage: python re/g_fs.py 0x4bc9e0 [0x4bb040 ...]

Prints per function: size, call surface, string refs in address order, FP constants, small
immediates, and a FIELD OFFSET HISTOGRAM (which [base+off] slots it touches) -- the last one is the
fastest way to read a struct layout out of a body.
"""
import struct
import sys
from collections import Counter, defaultdict

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


def analyze(fn, max_lines=0):
    p = PROF.get(fn) or {}
    lines = list(disasm(fn))
    print("=" * 76)
    print("=== 0x%x  size=%s  nins=%d ===" % (fn, p.get("size"), len(lines)))

    calls = []
    for ins in lines:
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM:
            t = ins.operands[0].imm
            calls.append((ins.address, t))
    uniq = []
    for _a, t in calls:
        if t not in [u for u in uniq]:
            uniq.append(t)
    print("--- call surface (%d calls, %d distinct) ---" % (len(calls), len(uniq)))
    for t in uniq:
        print("   0x%-8x size=%-6s %s" % (t, (PROF.get(t) or {}).get("size"), NAMES.get(t, "")))

    print("--- string refs (address order) ---")
    for ins in lines:
        for o in ins.operands:
            if o.type == X86_OP_MEM and o.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + o.mem.disp
                if t in STRS:
                    print("   %-8x %-30s %r" % (ins.address, ins.mnemonic + " " + ins.op_str,
                                                STRS[t][:64]))

    print("--- FP constants / rip data ---")
    for ins in lines:
        if ins.mnemonic not in ("movsd", "movss", "addsd", "subsd", "mulsd", "divsd", "ucomisd",
                                "comisd", "andpd", "xorpd", "cvtsi2sd", "cvttsd2si", "pxor"):
            continue
        for o in ins.operands:
            if o.type == X86_OP_MEM and o.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + o.mem.disp
                if t not in STRS:
                    print("   %-8x %-30s data@0x%x = %r" % (ins.address,
                                                            ins.mnemonic + " " + ins.op_str, t, f64(t)))

    print("--- field offsets touched (base+disp), by offset ---")
    hist = defaultdict(Counter)
    for ins in lines:
        for o in ins.operands:
            if o.type == X86_OP_MEM and o.mem.base != X86_REG_RIP and 0 < o.mem.disp < 0x800:
                hist[o.mem.disp][ins.mnemonic] += 1
    row = []
    for off in sorted(hist):
        n = sum(hist[off].values())
        row.append("+0x%x:%d" % (off, n))
    for i in range(0, len(row), 12):
        print("   " + "  ".join(row[i:i + 12]))

    imm = Counter()
    for ins in lines:
        for o in ins.operands[1:]:
            if o.type == X86_OP_IMM and 0 < o.imm < 0x2000:
                imm[o.imm] += 1
    print("--- small immediates ---")
    print("   " + ", ".join("%d x%d" % (k, v) for k, v in sorted(imm.items())))
    if max_lines:
        print("--- first %d instructions ---" % max_lines)
        for ins in lines[:max_lines]:
            print("   %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        analyze(int(arg, 16) if arg.lower().startswith("0x") else int(arg))
