"""The loop inside 0x6AABC0 that fills the row container core+0x48.

It is the region around 0x6AB394 / 0x6AB3E8 where 0x4FC5A0 (GetNumberOfParts) and 0x4FC5B0 (GetPart)
are called. Dump it and look for the push back into the vector whose begin is core+0x48, and for
the element's structure (48 bytes, first qword a pointer).
"""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()


def show(start, count, label):
    print()
    print("=== %s : 0x%x + %d ===" % (label, start, count))
    for ins in disasm(start, count=count):
        ctx = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                ctx.append("STR@%x %r" % (t, STRS[t][:44]) if t in STRS else "data@%x" % t)
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
        print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))


show(0x6AB360, 62, "container fill loop (before/around GetPart)")
show(0x6AB560, 40, "after the loop: the LIFO buffers and 0x134470")
