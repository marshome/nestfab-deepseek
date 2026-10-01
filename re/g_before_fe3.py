"""What is xmm0 just before 0x135FE3 (the single write of the returned xmm6)?"""
import struct
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_MEM, X86_REG_RIP  # noqa: E402

PROF = load_prof()


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


for lo, hi in ((0x135F30, 0x135FF0), (0x135DE0, 0x135E45)):
    print("=== 0x%x .. 0x%x ===" % (lo, hi))
    for ins in disasm(0x135C70):
        if lo <= ins.address <= hi:
            ctx = []
            for op in ins.operands:
                if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                    t = ins.address + ins.size + op.mem.disp
                    ctx.append("data@%x=%r" % (t, f64(t)))
            print("   %-8x %-38s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))
    print()
