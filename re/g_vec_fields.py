"""Stores/reads of the vector's own fields [rbp+0x48]/[rbp+0x50]/[rbp+0x58] inside 0x6AABC0.

If the vector end ([rbp+0x50]) is never advanced, the container handed to 0x13C380 is empty and
that call would take 0x5CD800's empty-container path -- so the fill must come from somewhere.
"""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()
lines = list(disasm(0x6AABC0))
print("=== instructions touching [rbp+0x48] / [rbp+0x50] / [rbp+0x58] ===")
for i, ins in enumerate(lines):
    s = ins.op_str
    if any(("[rbp + 0x%x]" % o) in s for o in (0x48, 0x50, 0x58)):
        print("   %-8x %-44s" % (ins.address, ins.mnemonic + " " + s))

print()
print("=== any call whose args come from [rsp+0x58] region or that writes 0x50-relative ===")
print("   (also: is 0x6AB8AB / 0x6AB8DD the only reader of [rsp+0x58]?)")
for ins in lines:
    if "[rsp + 0x58]" in ins.op_str:
        print("   %-8x %-44s" % (ins.address, ins.mnemonic + " " + ins.op_str))

print()
print("=== instructions in 0x6AB800..0x6AB8F0 (the region using [rsp+0x58]) ===")
for ins in lines:
    if 0x6AB800 <= ins.address <= 0x6AB8F0:
        note = ""
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == 2:
            note = "call 0x%x %s" % (ins.operands[0].imm, NAMES.get(ins.operands[0].imm, ""))
        elif ins.mnemonic == "call":
            note = "call [reg]"
        print("   %-8x %-44s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, note))
