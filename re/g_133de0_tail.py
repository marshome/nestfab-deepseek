"""What does 0x133DE0 return, and what happens between the Squeezer construction and the epilogue?

The FP scan found no floating point work after 0x133F2D, yet 0x134470 compares its return value in
xmm0 -- so either a callee leaves it there, or a movsd hides in the region before the epilogue at
0x1342D4. Print 0x133F00..0x1342D6 in full (that is the body between the ctor and the cleanup).
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
lines = [i for i in disasm(0x133DE0)]
start = None
for k, ins in enumerate(lines):
    if ins.address >= 0x133F00:
        start = k
        break
end = None
for k, ins in enumerate(lines):
    if ins.address >= 0x1342D6:
        end = k
        break
print("=== 0x133DE0 body: 0x133F00 .. 0x1342D6 (%d instructions) ===" % (end - start))
for ins in lines[start:end]:
    ctx = []
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            ctx.append("STR@%x %r" % (t, STRS[t][:38]) if t in STRS else "data@%x" % t)
        elif op.type == X86_OP_IMM and ins.mnemonic == "call":
            ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
    if ins.mnemonic in ("mov", "movsd", "lea", "call", "ret", "jmp") or \
       any(op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP for op in ins.operands):
        print("   %-8x %-44s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))
