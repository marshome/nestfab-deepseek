"""Do the two setters write the same object the RowNester core reads?

SetPipeMode stores a QWORD at [rsi+0x170] while the gate 0x4FC2F0 reads a BYTE at [[arg]+0x170],
so the base objects must be compared before pairing them. Print the prologues and the value
sources feeding the five stores of SetCommonCutParameters.
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


def show(fn, first=20, windows=()):
    prof = PROF.get(fn) or {}
    print()
    print("=== 0x%x %s size=%s nins=%s ===" % (fn, NAMES.get(fn, "?"), prof.get("size"),
                                               prof.get("nins")))
    lines = list(disasm(fn))
    idxs = set(range(min(first, len(lines))))
    for target in windows:
        for i, ins in enumerate(lines):
            if ins.address == target:
                idxs |= set(range(max(0, i - 5), min(len(lines), i + 2)))
    for i in sorted(idxs):
        ins = lines[i]
        ctx = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                ctx.append("STR@%x %r" % (t, STRS[t][:40]) if t in STRS else "data@%x" % t)
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
        print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))


show(0xFCF0, first=16, windows=(0xFED8,))
show(0x3C3F0, first=16, windows=(0x3C531, 0x3C540))

print()
print("=== 0x4FC2F0 / 0x4FC300 / 0x4FC3C0 again, with base provenance ===")
for fn in (0x4FC2F0, 0x4FC300, 0x4FC3C0):
    show(fn, first=4)
