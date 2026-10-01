"""What does the pipe-mode branch (0x6AC20A) of the row core do?

0x6AABC0 does `test al,al ; jne 0x6AC20A` on the pipe-mode gate (Pb+0x170), so 0x6AC20A is the
pipe-mode path that skips the common-cut override. Read it and its continuation.
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
    print("=== %s : 0x%x + %d instructions ===" % (label, start, count))
    for ins in disasm(start, count=count):
        ctx = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                ctx.append("STR@%x %r" % (t, STRS[t][:44]) if t in STRS else "data@%x" % t)
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
        print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))


show(0x6AC20A, 55, "the pipe-mode path")
