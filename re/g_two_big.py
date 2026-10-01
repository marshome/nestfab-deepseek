"""Structured extraction for 0x135040 (1396 B) and 0x135780 (1250 B)."""
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


for fn in (0x135040, 0x135780):
    lines = list(disasm(fn))
    print()
    print("=== 0x%x nins=%d size=%s ===" % (fn, len(lines), (PROF.get(fn) or {}).get("size")))
    print("--- entry ---")
    for ins in lines[:14]:
        print("   %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))
    print("--- ret sites ---")
    for i, ins in enumerate(lines):
        if ins.mnemonic == "ret":
            print("   ret @0x%x, preceding 8:" % ins.address)
            for j in range(max(0, i - 8), i + 1):
                print("      %-8x %s %s" % (lines[j].address, lines[j].mnemonic, lines[j].op_str))
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
    print("   " + " | ".join("%s x%d" % (k, c[k]) for k in order[:18]))
    print("--- rodata constants ---")
    seen = set()
    for ins in lines:
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t not in seen and t not in STRS:
                    seen.add(t)
                    print("   @0x%-8x data@0x%-8x = %r" % (ins.address, t, f64(t)))
    print("--- FP ops ---")
    n = 0
    for ins in lines:
        if ins.mnemonic in ("movsd", "addsd", "subsd", "mulsd", "divsd", "sqrtsd", "ucomisd",
                            "comisd", "maxsd", "minsd", "cvtsi2sd", "cvttsd2si", "andpd", "xorpd"):
            print("   %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))
            n += 1
            if n >= 30:
                print("   ... (truncated)")
                break
