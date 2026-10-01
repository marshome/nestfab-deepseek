"""0x135C70's return sites: what is in xmm0 at each ret, and the comparison context."""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402

lines = list(disasm(0x135C70))
idx = [i for i, ins in enumerate(lines) if ins.mnemonic == "ret"]
print("=== %d ret sites ===" % len(idx))
for i in idx:
    print()
    print("   ret @0x%x, the 12 instructions before it:" % lines[i].address)
    for ins in lines[max(0, i - 12):i + 1]:
        print("      %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))

print()
print("=== context around the two comparisons ===")
for lo, hi in ((0x135D90, 0x135DD0), (0x135E40, 0x135E80)):
    print("   --- 0x%x .. 0x%x" % (lo, hi))
    for ins in lines:
        if lo <= ins.address <= hi:
            print("      %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))
