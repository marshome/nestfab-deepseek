"""0x137800 (636 B): the appender that fills O's container.

0x137A90 ends with `call 0x137800(O, rdi = best element pointer, xmm2 = score)`, so this is the
producer of the 16-byte {pointer, double} records. Read its entry and the stores into O.
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
prof = PROF.get(0x137800) or {}
print("=== 0x137800 size=%s nins=%s ===" % (prof.get("size"), prof.get("nins")))


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


for ins in disasm(0x137800, count=80):
    ctx = []
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            if t in STRS:
                ctx.append("STR@%x %r" % (t, STRS[t][:34]))
            else:
                ctx.append("data@%x=%r" % (t, f64(t)))
        elif op.type == X86_OP_IMM and ins.mnemonic == "call":
            ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
    print("   %-8x %-44s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))

print()
print("=== calls in order ===")
for ins in disasm(0x137800):
    if ins.mnemonic == "call":
        op = ins.operands[0]
        if op.type == X86_OP_IMM:
            print("   @0x%-8x 0x%x %s" % (ins.address, op.imm, NAMES.get(op.imm, "")))
        else:
            print("   @0x%-8x [reg]" % ins.address)
