"""What are element +0x98 / +0x99 / +0xa0? They are written inside 0x136350 at 0x1366A2..0x13670F."""
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


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


print("=== 0x136350: 0x136560 .. 0x136760 ===")
for ins in disasm(0x136350):
    if 0x136560 <= ins.address <= 0x136760:
        ctx = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS:
                    ctx.append("STR@%x %r" % (t, STRS[t][:28]))
                else:
                    ctx.append("data@%x=%r" % (t, f64(t)))
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
        print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))

print()
print("=== the two flag getters again, for reference ===")
for fn in (0x135010, 0x135030, 0x136D10):
    print("   -- 0x%x" % fn)
    for ins in disasm(fn, count=4):
        print("      %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))
