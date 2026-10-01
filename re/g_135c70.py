"""0x135C70 (1748 B): what does it compute? It produces element+0xa0 (0x13670F), the numerator
of the ratio at 0x137C76. Structured extraction: entry, calls, constants, FP ops, tail.

0x136350 calls it as `rcx = rsi` (rsi = rsp+0x50 there, the container built by 0x1355C0-ish work)
and takes xmm0 as the answer.
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


lines = list(disasm(0x135C70))
print("=== 0x135C70 nins=%d size=%s ===" % (len(lines), (PROF.get(0x135C70) or {}).get("size")))

print()
print("--- entry ---")
for ins in lines[:22]:
    print("   %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))

print()
print("--- tail ---")
for ins in lines[-22:]:
    print("   %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))

print()
print("--- calls ---")
c = Counter()
order = []
for ins in lines:
    if ins.mnemonic == "call":
        op = ins.operands[0]
        if op.type == X86_OP_IMM:
            key = "0x%x %s" % (op.imm, NAMES.get(op.imm, ""))
        else:
            key = "[reg]"
        c[key] += 1
        if key not in order:
            order.append(key)
for k in order:
    print("   %-40s x%d" % (k, c[k]))

print()
print("--- rodata constants ---")
seen = set()
for ins in lines:
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            if t not in seen and t not in STRS:
                seen.add(t)
                print("   @0x%-8x data@0x%-8x = %r" % (ins.address, t, f64(t)))

print()
print("--- FP ops (first 40) ---")
n = 0
for ins in lines:
    if ins.mnemonic in ("movsd", "addsd", "subsd", "mulsd", "divsd", "sqrtsd", "ucomisd",
                        "comisd", "maxsd", "minsd", "cvtsi2sd", "cvttsd2si", "andpd", "xorpd"):
        print("   %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))
        n += 1
        if n >= 40:
            break
