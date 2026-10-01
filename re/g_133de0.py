"""Stage 2: 0x133DE0's entry (how it uses its arguments) and its tail (what it returns).

Its call list already shows it assembles the row structures: 0x5CD800 (bbox), 0x1333D0 (Item ctor),
0x136B80 -> 0x138A20 (Row::Squeezer ctor). So it is the "assemble and price a candidate" routine
that 0x134470 calls in its min-over-candidates loop. Read both ends to recover the cost arithmetic.
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
lines = list(disasm(0x133DE0))
print("=== 0x133DE0: first 62 instructions ===")
for ins in lines[:62]:
    ctx = []
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            ctx.append("STR@%x %r" % (t, STRS[t][:40]) if t in STRS else "data@%x" % t)
        elif op.type == X86_OP_IMM and ins.mnemonic == "call":
            ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
    print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))

print()
print("=== 0x133DE0: last 55 instructions (the return value) ===")
for ins in lines[-55:]:
    ctx = []
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            ctx.append("STR@%x %r" % (t, STRS[t][:40]) if t in STRS else "data@%x" % t)
        elif op.type == X86_OP_IMM and ins.mnemonic == "call":
            ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
    print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))

print()
print("=== FP instructions across the whole function ===")
for ins in lines:
    if ins.mnemonic in ("movsd", "addsd", "subsd", "mulsd", "divsd", "sqrtsd", "ucomisd",
                        "comisd", "cvtsi2sd", "cvttsd2si", "maxsd", "minsd"):
        ctx = ""
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                ctx = ("STR@%x %r" % (t, STRS[t][:40])) if t in STRS else ("data@%x" % t)
        print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, ctx))
