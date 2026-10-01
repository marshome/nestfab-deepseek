"""0x8BEFC0's tail: confirm the vector's begin/end/cap and that one element is appended."""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402

lines = list(disasm(0x8BEFC0))
start = next(i for i, ins in enumerate(lines) if ins.address >= 0x8BF070)
print("=== 0x8BEFC0 tail ===")
for ins in lines[start:]:
    print("   %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))

print()
print("=== the caller's setup in 0x134470 (what tag/angle are passed) ===")
for ins in disasm(0x134470):
    if 0x1344C5 <= ins.address <= 0x134540:
        print("   %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))
