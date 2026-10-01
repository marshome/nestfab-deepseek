"""The four exact-angle branches of 0x5CEE50 (0x5CEFE0, 0x5CF000, 0x5CF020, 0x5CF040).

They handle angle 0 / 90 / 180 / 270 degrees; the general path computes cos/sin and stores
{cos, -sin, sin, cos, 0, 0}. Print each branch so the exact constants are known.
"""
import struct
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
    print("=== %s (0x%x + %d) ===" % (label, start, count))
    for ins in disasm(start, count=count):
        ctx = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS:
                    ctx.append("STR@%x %r" % (t, STRS[t][:30]))
                else:
                    off = rva2off(t)
                    v = struct.unpack("<d", data[off:off + 8])[0] if off else None
                    ctx.append("data@%x=%r" % (t, v))
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
        print("   %-8x %-40s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))


show(0x5CEFE0, 12, "angle == 0")
show(0x5CF000, 12, "angle == 90e10")
show(0x5CF020, 12, "angle == 180e10")
show(0x5CF040, 14, "angle == 270e10")
show(0x5CEF59, 20, "after the general path: the tag getter and the rest")
