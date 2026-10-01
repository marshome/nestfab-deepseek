"""Resolve the virtual call 0x137A90 makes on its 4th argument (r12).

0x137BFE  rax = [r12] ; rcx = r12 ; rdx = [rbp] ; call qword [rax + 0x10]
So the callee is the vtable slot at (vptr + 0x10), i.e. slot 2 of the address point. If r12 is the
Row::Squeezer (whose vptr is 0xA3B1F0), the slot resolves inside the 0x13xxxx row translation unit.
Dump the tables at 0xA3B1E0-0xA3B230 and 0xA3B1B0-0xA3B1E0.
"""
import struct
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

IMAGE = 0x6B4C0000
PROF = load_prof()


def read_q(rva):
    off = rva2off(rva)
    return struct.unpack("<Q", data[off:off + 8])[0] if off is not None else None


def desc(va):
    if not va:
        return "0"
    rva = va - IMAGE if va >= IMAGE else va
    prof = PROF.get(rva) or {}
    return "VA 0x%-12x RVA 0x%-8x size=%-6s %s" % (va, rva, prof.get("size"),
                                                    NAMES.get(rva, ""))


print("=== the vtable reachable from 0xA3B1F0 (the Row::Squeezer vptr) ===")
for ap, label in ((0xA3B1F0, "Row::Squeezer"), (0xA3B1C0, "Row::BasicDistancer")):
    print()
    print("--- %s : address point 0x%x ---" % (label, ap))
    base = ap - 0x10
    print("   [base-8]  (typeinfo?)  : %s" % desc(read_q(base - 8)))
    print("   [base]    (offset-to-top): %s" % desc(read_q(base)))
    for k in range(8):
        print("   slot %d  [%s+0x%02x] : %s" % (k, "vptr", 0x10 * k, desc(read_q(ap + 0x10 * k))))

print()
print("=== what 0x137A90 passes to that slot ===")
for ins in disasm(0x137A90, count=40):
    if 0x137BF0 <= ins.address <= 0x137C1F:
        print("   %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))
