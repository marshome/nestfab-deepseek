"""0x136350's internal geometry: 0x1355C0, 0x135040, 0x135780.

0x136350 calls 0x1355C0(rsp+0x50, element) right after setting up, then 0x5CD800 takes the bbox of
that, and 0x135040 is called twice (0x136497, 0x1364EF) before 0x135780. Get sizes, calls and the
constants so the geometry chain is visible.
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


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


print("=== sizes ===")
for fn in (0x1355C0, 0x135040, 0x135780, 0x135C70, 0x5CE7F0, 0x5CF6B0, 0x8C4FF0, 0x134D70):
    prof = PROF.get(fn)
    print("   0x%-8x size=%-6s nins=%-5s %s" % (fn, (prof or {}).get("size"),
                                                (prof or {}).get("nins"), NAMES.get(fn, "")))

for fn in (0x1355C0, 0x135040, 0x135780):
    print()
    print("=== 0x%x ===" % fn)
    for ins in disasm(fn, count=45):
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
    print("      " + " | ".join(seen[:14]))
