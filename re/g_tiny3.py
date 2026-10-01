"""The three remaining tiny accessors of the node family."""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()
for fn in (0x136D00, 0x136D10, 0x136D20, 0x136D30, 0x136D40, 0x136D50, 0x136C60, 0x136C70,
           0x136C80):
    prof = PROF.get(fn)
    if not prof:
        print("   0x%-8x (not in profile)" % fn)
        continue
    print()
    print("--- 0x%x size=%s nins=%s" % (fn, prof.get("size"), prof.get("nins")))
    for ins in disasm(fn, count=24):
        ctx = ""
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                ctx = ("STR@%x %r" % (t, STRS[t][:36])) if t in STRS else ("data@%x" % t)
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                ctx = "%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm)
        print("      %-8x %-40s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, ctx))
