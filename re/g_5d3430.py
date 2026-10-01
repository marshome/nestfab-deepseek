"""0x5D3430 (1156 B / 282 insns): structured extraction."""
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


lines = list(disasm(0x5D3430))
print("=== 0x5D3430 nins=%d size=%s ===" % (len(lines), (PROF.get(0x5D3430) or {}).get("size")))

print()
print("--- entry ---")
for ins in lines[:16]:
    print("   %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))

print()
print("--- ret sites ---")
for i, ins in enumerate(lines):
    if ins.mnemonic == "ret":
        print("   ret @0x%x, preceding 10:" % ins.address)
        for j in range(max(0, i - 10), i + 1):
            print("      %-8x %s %s" % (lines[j].address, lines[j].mnemonic, lines[j].op_str))

print()
print("--- calls ---")
c = Counter()
order = []
for ins in lines:
    if ins.mnemonic == "call":
        op = ins.operands[0]
        key = ("0x%x %s" % (op.imm, NAMES.get(op.imm, ""))) if op.type == X86_OP_IMM else "[reg]"
        c[key] += 1
        if key not in order:
            order.append(key)
for k in order:
    print("   %-38s x%d" % (k, c[k]))

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
print("--- FP ops ---")
for ins in lines:
    if ins.mnemonic in ("movsd", "addsd", "subsd", "mulsd", "divsd", "sqrtsd", "ucomisd",
                        "comisd", "maxsd", "minsd", "cvtsi2sd", "cvttsd2si", "andpd", "xorpd"):
        print("   %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))
