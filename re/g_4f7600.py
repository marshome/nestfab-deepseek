"""0x4F7600 (9 B!) and the two helpers of the record-table builder 0x5C4950."""
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
for fn in (0x4F7600, 0x5C3F00, 0x5C3FF0):
    p = PROF.get(fn) or {}
    print()
    print("=== 0x%x size=%s nins=%s %s" % (fn, p.get("size"), p.get("nins"), NAMES.get(fn, "")))
    for ins in disasm(fn, count=25):
        note = ""
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM:
            note = "%s(0x%x)" % (NAMES.get(ins.operands[0].imm, "?"), ins.operands[0].imm)
        print("      %-8x %-38s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, note))

print()
print("=== 0x5C4950: where it writes the record table (the out is [rsp+0x120]) ===")
for ins in disasm(0x5C4950):
    if 0x5C4A10 <= ins.address <= 0x5C4B30:
        print("   %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))
