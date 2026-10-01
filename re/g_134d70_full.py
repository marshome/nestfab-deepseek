"""0x134D70 in full (437 B / 101 insns): the flag computation for element +0x40 / +0x41."""
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


lines = list(disasm(0x134D70))
print("=== 0x134D70 size=%s nins=%s ===" % ((PROF.get(0x134D70) or {}).get("size"), len(lines)))
for ins in lines:
    ctx = []
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            if t in STRS:
                ctx.append("STR@%x %r" % (t, STRS[t][:28]))
            else:
                ctx.append("data@%x=%r" % (t, f64(t)))
        elif op.type == X86_OP_IMM and ins.mnemonic == "call":
            ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
    print("   %-8x %-40s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))

print()
print("=== jump targets ===")
tg = sorted({op.imm for ins in lines for op in ins.operands
             if op.type == X86_OP_IMM and ins.mnemonic.startswith("j")})
print("   " + ", ".join("0x%x" % t for t in tg))
