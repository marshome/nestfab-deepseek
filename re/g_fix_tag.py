"""Verify the correction: element+0x08/+0x10 hold a copy of the {tag, angle} source record.

0x1355C0 calls 0x5CEE50(element + 8), and 0x5CEE50 reads byte[x] as the tag and [x+8] as the angle.
So element+0x08 must be the tag qword and element+0x10 the angle -- not a container's begin/end.
Check 0x133190 (called with [element], expected to yield the part's geometry container) and
0x136350's arg3 at its call sites.
"""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402

PROF = load_prof()
for fn in (0x133190, 0x5C5F30, 0x5D3430, 0x5C5260):
    prof = PROF.get(fn)
    if not prof:
        print("   0x%-8x (not in profile)" % fn)
        continue
    print()
    print("--- 0x%x size=%s nins=%s" % (fn, prof.get("size"), prof.get("nins")))
    for ins in disasm(fn, count=14):
        print("      %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))

print()
print("=== 0x136350: what r8 (arg3) is at the 0x1355C0 call and at the fill sites ===")
for ins in disasm(0x1355C0):
    if 0x1355C0 <= ins.address <= 0x1355F7:
        print("   %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))
print("   --- and in 0x136350 around its own prologue stores ---")
for ins in disasm(0x136350, count=30):
    print("   %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))
