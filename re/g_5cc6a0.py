"""0x5CC6A0: the function whose xmm0 becomes element+0xa0 (via 0x135C70)."""
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


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


for fn in (0x5C51A0, 0x5CC6A0):
    p = PROF.get(fn) or {}
    print()
    print("=== 0x%x size=%s nins=%s ===" % (fn, p.get("size"), p.get("nins")))
    for ins in disasm(fn, count=50):
        ctx = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS:
                    ctx.append("STR@%x %r" % (t, STRS[t][:30]))
                else:
                    ctx.append("data@%x=%r" % (t, f64(t)))
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
        print("   %-8x %-40s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))
    print("   -- calls --")
    seen = []
    for ins in disasm(fn):
        if ins.mnemonic == "call":
            op = ins.operands[0]
            t = ("0x%x %s" % (op.imm, NAMES.get(op.imm, ""))) if op.type == X86_OP_IMM else "[reg]"
            if t not in seen:
                seen.append(t)
    print("      " + " | ".join(seen[:14]))
