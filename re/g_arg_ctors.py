"""Item (5): the constructors of 0x133DE0's arg1 (rsp+0x1b0) and arg2 (rsp+0x1d0).

0x6AABC0 calls 0x134470(rcx = rsp+0x190, rdx = rsp+0x1b0, r8 = rsp+0x1d0, r9 = core+8).
Read the setup region of 0x6AABC0 plus 0x5C4950 (which built rsp+0x1d0) and 0x4F7600.
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


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


print("=== sizes ===")
for fn in (0x4F7600, 0x5C4950, 0x6AABC0):
    p = PROF.get(fn) or {}
    print("   0x%-8x size=%-6s nins=%-5s %s" % (fn, p.get("size"), p.get("nins"), NAMES.get(fn, "")))

print()
print("=== 0x6AABC0: the region that fills rsp+0x1b0 / rsp+0x1d0 and calls 0x134470 ===")
for ins in disasm(0x6AABC0):
    if 0x6AB2E0 <= ins.address <= 0x6AB3F0:
        ctx = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                ctx.append("STR@%x %r" % (t, STRS[t][:30]) if t in STRS else "data@%x=%r" % (t, f64(t)))
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
        print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))

print()
print("=== 0x5C4950 (the record-table builder) ===")
p = PROF.get(0x5C4950) or {}
print("   size=%s nins=%s" % (p.get("size"), p.get("nins")))
for ins in disasm(0x5C4950, count=40):
    ctx = []
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            ctx.append("STR@%x %r" % (t, STRS[t][:30]) if t in STRS else "data@%x=%r" % (t, f64(t)))
        elif op.type == X86_OP_IMM and ins.mnemonic == "call":
            ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
    print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))
