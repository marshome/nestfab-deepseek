"""0x5C4C50: the generator that fills the candidate-angle element vector.

Called as 0x5C4C50(buffer, tag, axisDouble) from 0x8BEFC0 (which 0x134470 drives with tag=0 and
90 degrees), and earlier from 0x6AABC0. Read its structure, calls and constants.
"""
import struct
import sys
from collections import Counter

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()
fn = 0x5C4C50
prof = PROF.get(fn) or {}
print("=== 0x%x size=%s nins=%s ===" % (fn, prof.get("size"), prof.get("nins")))


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


for ins in disasm(fn, count=75):
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
    print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))

print()
print("=== all calls ===")
for ins in disasm(fn):
    if ins.mnemonic == "call":
        op = ins.operands[0]
        if op.type == X86_OP_IMM:
            print("   @0x%-8x 0x%x %s" % (ins.address, op.imm, NAMES.get(op.imm, "")))
        else:
            print("   @0x%-8x [reg]" % ins.address)

print()
print("=== rodata constants ===")
seen = set()
for ins in disasm(fn):
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            if t not in seen and t not in STRS:
                seen.add(t)
                print("   @0x%-8x data@0x%-8x = %r" % (ins.address, t, f64(t)))
