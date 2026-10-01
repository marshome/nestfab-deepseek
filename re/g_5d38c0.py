"""Settle the two element getters, then read 0x5D38C0's body in compressed form.

0x5C4CD0(element) was used as "the tag" and 0x5C4CE0(element) as "the angle"; both are tiny.
0x5D38C0 (1500 B / 359 insns) has only 5 calls (4x operator new + 0x5C5F50), so its body is mostly
data movement -- extract the FP work, the constants and the destination offsets instead of all
359 instructions.
"""
import struct
import sys
from collections import Counter

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


print("=== the two getters ===")
for fn in (0x5C4CD0, 0x5C4CE0, 0x5C5F50, 0x5C61D0):
    prof = PROF.get(fn)
    if not prof:
        print("   0x%-8x (not in profile)" % fn)
        continue
    print()
    print("--- 0x%x size=%s nins=%s" % (fn, prof.get("size"), prof.get("nins")))
    for ins in disasm(fn, count=20):
        print("      %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))

print()
print("=== 0x5D38C0: FP instructions ===")
for ins in disasm(0x5D38C0):
    if ins.mnemonic in ("movsd", "addsd", "subsd", "mulsd", "divsd", "sqrtsd", "ucomisd",
                        "comisd", "xorpd", "andpd", "orpd", "unpcklpd", "movapd", "movaps",
                        "movups", "pxor", "shufpd", "addpd", "subpd", "mulpd"):
        ctx = ""
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                ctx = ("STR@%x %r" % (t, STRS[t][:30])) if t in STRS else ("data@%x=%r" % (t, f64(t)))
        print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, ctx))

print()
print("=== 0x5D38C0: all calls ===")
for ins in disasm(0x5D38C0):
    if ins.mnemonic == "call":
        op = ins.operands[0]
        if op.type == X86_OP_IMM:
            print("   @0x%-8x 0x%x %s" % (ins.address, op.imm, NAMES.get(op.imm, "")))
        else:
            print("   @0x%-8x [reg]" % ins.address)

print()
print("=== 0x5D38C0: dest writes (top 24 by base/offset) ===")
w = Counter()
for ins in disasm(0x5D38C0):
    if not ins.operands:
        continue
    d = ins.operands[0]
    if d.type == X86_OP_MEM and d.mem.base not in (0, 41) and d.mem.index == 0:
        reg = ins.reg_name(d.mem.base)
        if reg not in ("rsp", "rbp") and ins.mnemonic.startswith(
                ("mov", "movsd", "movups", "movaps", "movapd", "add", "or", "and", "xor")):
            w[(reg, d.mem.disp)] += 1
for (reg, disp), n in sorted(w.items(), key=lambda kv: -kv[1])[:24]:
    print("   [%s+0x%x] x%d" % (reg, disp, n))
