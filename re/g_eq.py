# -*- coding: utf-8 -*-
"""Pin the shrink formula in EquivalentSmallerDefects (0x4BC9E0) and read GetOriginalNesting."""
import struct
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_RIP  # noqa: E402
from g_fs import analyze  # noqa: E402

PROF = load_prof()


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


def window(fn, lo, hi):
    print()
    print("--- 0x%x window [0x%x, 0x%x] ---" % (fn, lo, hi))
    for ins in disasm(fn):
        if ins.address < lo:
            continue
        if ins.address > hi:
            break
        ctx = []
        for o in ins.operands:
            if o.type == X86_OP_MEM and o.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + o.mem.disp
                ctx.append("STR %r" % STRS[t][:40] if t in STRS else "d@0x%x=%r" % (t, f64(t)))
        print("   %-8x %-38s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))


window(0x4BC9E0, 0x4BCA20, 0x4BCA80)     # the 0.5 use
window(0x4BC9E0, 0x4BCC60, 0x4BCE00)     # the loop: 1e-06 / -0.0 / 4.0 / assertions
analyze(0x4BB040)
