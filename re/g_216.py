"""What is the 216-byte element? Look at 0x1333D0 filling Item+0x58 / Item+0x70.

The writes to [r14+0x60] (container A's end) and [r14+0x78] (container B's end) mark the fill
sites. Read the region around them, plus every operator new size in 0x1333D0.
"""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_MEM, X86_OP_IMM  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

prof = load_prof().get(0x1333D0) or {}
print("=== 0x1333D0 size=%s nins=%s ===" % (prof.get("size"), prof.get("nins")))
lines = list(disasm(0x1333D0))

print()
print("=== every `mov ecx, <n>` / operator new near it ===")
for i, ins in enumerate(lines):
    if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM \
            and ins.operands[0].imm == 0x998500:
        for j in range(max(0, i - 4), i + 1):
            print("   %-8x %s %s" % (lines[j].address, lines[j].mnemonic, lines[j].op_str))
        print("   ---")

print()
print("=== the fill region 0x133A00..0x133B80 ===")
for ins in lines:
    if 0x133A00 <= ins.address <= 0x133B80:
        note = ""
        if ins.mnemonic == "call":
            op = ins.operands[0]
            note = ("0x%x %s" % (op.imm, NAMES.get(op.imm, ""))) if op.type == X86_OP_IMM else "[reg]"
        print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, note))
