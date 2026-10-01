"""Where does xmm6 (the returned value) get written in 0x135C70?"""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402

lines = list(disasm(0x135C70))
print("=== every instruction touching xmm6 ===")
for i, ins in enumerate(lines):
    if "xmm6" in ins.op_str:
        print("   %-8x %-38s" % (ins.address, ins.mnemonic + " " + ins.op_str))
        # show a little context after a write into xmm6
        if ins.operands and ins.operands[0].type == 1 and ins.reg_name(ins.operands[0].reg) == "xmm6":
            for j in range(i + 1, min(len(lines), i + 7)):
                print("        | %-8x %s %s" % (lines[j].address, lines[j].mnemonic, lines[j].op_str))
