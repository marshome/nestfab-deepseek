"""Where is the row container core+0x48 (held at [rsp+0x58]) written inside 0x6AABC0?"""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()
lines = list(disasm(0x6AABC0))

print("=== every instruction mentioning [rsp+0x58] (the core+0x48 vector) ===")
for i, ins in enumerate(lines):
    if "[rsp + 0x58]" in ins.op_str:
        print("   %-8x %-42s" % (ins.address, ins.mnemonic + " " + ins.op_str))
        for j in range(max(0, i - 6), i):
            print("        %-8x %s %s" % (lines[j].address, lines[j].mnemonic, lines[j].op_str))

print()
print("=== the 0x4F7600 result element: what does the copy loop target (r13) look like? ===")
for i, ins in enumerate(lines):
    if ins.address in (0x6AB4A6, 0x6AB4AB, 0x6AB4AE):
        for j in range(i, min(len(lines), i + 6)):
            print("   %-8x %-42s" % (lines[j].address, lines[j].mnemonic + " " + lines[j].op_str))
        break

print()
print("=== calls in 0x6AB4A6..0x6AB6B0 (the element copy loop) ===")
for ins in lines:
    if 0x6AB4A6 <= ins.address <= 0x6AB6B0 and ins.mnemonic == "call":
        op = ins.operands[0]
        tgt = "0x%x %s" % (op.imm, NAMES.get(op.imm, "")) if op.type == X86_OP_IMM else "[reg]"
        print("   %-8x call %s" % (ins.address, tgt))
