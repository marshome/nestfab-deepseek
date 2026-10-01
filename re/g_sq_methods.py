"""The Row::Squeezer member methods used by the per-candidate path.

0x133DE0 does, on the squeezer it built at rsp+0x110:
    0x137FE0(rsp+0x110, r9 = rsp+0x60, ...)
    0x136D30(rsp+0x110)
    xmm0 = cfg[+0x00] ; xmm1 = cfg[+0x08]
    0x136CB0(rsp+0x110, xmm0, xmm1)
    0x136CA0(rsp+0x110)          <- its double return is what 0x133DE0 hands back
Read them all.
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
for fn in (0x136CA0, 0x136CB0, 0x136D30, 0x137FE0, 0x136D50):
    prof = PROF.get(fn) or {}
    print()
    print("=== 0x%x %s size=%s nins=%s ===" % (fn, NAMES.get(fn, "?"), prof.get("size"),
                                               prof.get("nins")))
    for ins in disasm(fn, count=60):
        ctx = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                ctx.append("STR@%x %r" % (t, STRS[t][:38]) if t in STRS else "data@%x" % t)
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
        print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))
