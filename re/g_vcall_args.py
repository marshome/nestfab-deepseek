"""Confirm the arguments of the virtual call at 0x137C0C (slot 1 = 0x13A360).

Expected: rcx = r12 (the Row::Squeezer), rdx = [rbp] (the previous record's node pointer),
r8 = rbx (the current 216 byte element). If so, the score is Squeezer::cost(prevNode, element).
"""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402

PROF = load_prof()
lines = list(disasm(0x137A90))
start = next(i for i, ins in enumerate(lines) if ins.address >= 0x137B30)
end = next(i for i, ins in enumerate(lines) if ins.address > 0x137C90)
print("=== 0x137B30 .. 0x137C90 (the record/node setup and the virtual call) ===")
for ins in lines[start:end]:
    print("   %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))

print()
print("=== 0x13A360's prologue (is it (this, lo, hi)?) ===")
for ins in disasm(0x13A360, count=12):
    print("   %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))
