"""The node family used by 0x137A90: 0x134F50, 0x134F90, 0x134FA0, 0x135010, 0x135030,
0x136D00, 0x136D10, 0x136D20, 0x137800, plus 0x134FB0/0x134FC0 if present.

Print sizes first, then the bodies of everything small enough to read in full -- these are the
accessors that reveal the node layout (and hence what core+0x08/+0x10 mean).
"""
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
FAMILY = [0x134F30, 0x134F50, 0x134F90, 0x134FA0, 0x134FB0, 0x134FC0, 0x134FD0, 0x134FE0,
          0x134FF0, 0x135000, 0x135010, 0x135030, 0x136C90, 0x136CA0, 0x136CB0, 0x136D00,
          0x136D10, 0x136D20, 0x136D30, 0x137800, 0x1331A0, 0x1333C0]


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


print("=== sizes ===")
for fn in FAMILY:
    prof = PROF.get(fn)
    if not prof:
        print("   0x%-8x  (not in profile)" % fn)
        continue
    print("   0x%-8x size=%-6s nins=%-5s %s" % (fn, prof.get("size"), prof.get("nins"),
                                                NAMES.get(fn, "")))

print()
print("=== bodies (only functions <= 120 bytes) ===")
for fn in FAMILY:
    prof = PROF.get(fn) or {}
    if not prof or (prof.get("size") or 0) > 120:
        continue
    print()
    print("--- 0x%x size=%s" % (fn, prof.get("size")))
    for ins in disasm(fn):
        ctx = ""
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                ctx = ("STR@%x %r" % (t, STRS[t][:36])) if t in STRS else ("data@%x=%r" % (t, f64(t)))
        print("      %-8x %-40s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, ctx))
