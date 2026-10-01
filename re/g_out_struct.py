"""Verify the out-struct base register in 0x13C380 and the tiny helpers."""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP  # noqa: E402

PROF = load_prof()


def dump(fn, count=None):
    prof = PROF.get(fn) or {}
    print("=== 0x%x size=%s nins=%s ===" % (fn, prof.get("size"), prof.get("nins")))
    for ins in disasm(fn, count=count):
        note = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                note.append("STR@%x %r" % (t, STRS[t][:40]) if t in STRS else "data@%x" % t)
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                note.append("0x%x" % op.imm)
        print("   %-8x %-40s %s" % (ins.address, ins.mnemonic + " " + ins.op_str,
                                    ("; " + " | ".join(note)) if note else ""))


print("=== 0x13C380 prologue: where is r12 set? ===")
for ins in disasm(0x13C380, count=24):
    print("   %-8x %-40s" % (ins.address, ins.mnemonic + " " + ins.op_str))

for fn in (0x133190, 0x5C5260, 0x5C5F30, 0x5C8C50, 0x5CD360):
    print()
    dump(fn, count=18)

print()
print("=== 0x6AABC0: does it also call 0x5CD800 / 0x13C380 with the row container? ===")
for ins in disasm(0x6AABC0):
    if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM:
        if ins.operands[0].imm in (0x5CD800, 0x13C380, 0x133190, 0x5C5260):
            print("   0x%-8x call 0x%x" % (ins.address, ins.operands[0].imm))
