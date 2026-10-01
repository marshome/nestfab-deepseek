"""Verify the ABI claim and the Item container slots.

Claim: 0x5CD800 preserves rdi (Microsoft x64: rdi is callee-saved), so in 0x133DE0 the rdi at
0x133EC9 / 0x133E93 is still rsp+0x170. Check 0x5CD800's epilogue, and check that 0x1333D0 writes
the ends/caps at +0x60/+0x78 (two containers at +0x58 and +0x70).
"""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402

PROF = load_prof()
print("=== 0x5CD800 prologue and epilogue (does it save/restore rdi?) ===")
lines = list(disasm(0x5CD800))
for ins in lines[:8] + lines[-14:]:
    print("   %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))

print()
print("=== 0x1333D0: writes to Item +0x58..+0x88 (the two container slots) ===")
for ins in disasm(0x1333D0):
    if not ins.operands:
        continue
    d = ins.operands[0]
    if d.type == 3 and d.mem.base not in (0, 41):  # X86_OP_MEM
        pass
    try:
        if d.type == 3 and 0x58 <= d.mem.disp <= 0x88:
            print("   %-8x %-40s" % (ins.address, ins.mnemonic + " " + ins.op_str))
    except Exception:
        continue

print()
print("=== 0x137A90: how it uses P (the Item) ===")
for ins in disasm(0x137A90, count=40):
    if any(("[rbx" in ins.op_str, "[r13" in ins.op_str) for _ in [0]):
        print("   %-8x %-40s" % (ins.address, ins.mnemonic + " " + ins.op_str))
