"""How does SetCommonCutParameters (0x3C3F0) fill the stack block it copies into Pb+0x190..?

The stores at 0x3C531/0x3C540/0x3C54F/0x3C55E/0x3C56D read from [rsp+0x100], [rsp+0x108],
[rsp+0x110], [rsp+0x118], ... so the pairing between the export's arguments and the Pb fields is
visible in how that stack region is filled.
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


def show(start, count, label, watch=()):
    print()
    print("=== %s ===" % label)
    for ins in disasm(start, count=count):
        ctx = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                ctx.append("STR@%x %r" % (t, STRS[t][:40]) if t in STRS else "data@%x" % t)
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
        mark = ""
        s = ins.op_str
        if any(("[rsp + 0x%x]" % w) in s for w in watch):
            mark = "   <== watch"
        print("   %-8x %-44s %s%s" % (ins.address, ins.mnemonic + " " + s, "; ".join(ctx), mark))


# the region that fills [rsp+0x100..0x130] before the copy into Pb
show(0x3C3F0, 70, "SetCommonCutParameters prologue (0x3C3F0 + 70)",
     watch=(0x100, 0x108, 0x110, 0x118, 0x120, 0x128, 0x130))
show(0x3C4D0, 30, "just before the Pb stores (0x3C4D0 + 30)",
     watch=(0x100, 0x108, 0x110, 0x118, 0x120))
