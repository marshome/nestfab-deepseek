"""The append into core+0x48 (0x6AB75C / 0x6AB768 / 0x6AB77E) -- source and element content."""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

for ins in disasm(0x6AB6A0, count=100):
    note = ""
    if ins.mnemonic == "call":
        op = ins.operands[0]
        if op.type == 2:
            note = "call 0x%x %s" % (op.imm, NAMES.get(op.imm, ""))
        else:
            note = "call [reg]"
    print("   %-8x %-44s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, note))
