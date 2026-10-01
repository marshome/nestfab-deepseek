"""The three small sub-calls: 0x8C4FF0 (147 B), 0x5CF6B0 (235 B), 0x5CE7F0 (381 B)."""
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


for fn in (0x8C4FF0, 0x5CF6B0, 0x5CE7F0):
    prof = PROF.get(fn) or {}
    print()
    print("=== 0x%x size=%s nins=%s ===" % (fn, prof.get("size"), prof.get("nins")))
    for ins in disasm(fn, count=75):
        ctx = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS:
                    ctx.append("STR@%x %r" % (t, STRS[t][:32]))
                else:
                    ctx.append("data@%x=%r" % (t, f64(t)))
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
        print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))
    print("   -- calls --")
    seen = []
    for ins in disasm(fn):
        if ins.mnemonic == "call":
            op = ins.operands[0]
            t = ("0x%x %s" % (op.imm, NAMES.get(op.imm, ""))) if op.type == X86_OP_IMM else "[reg]"
            if t not in seen:
                seen.append(t)
    print("      " + " | ".join(seen[:16]))
