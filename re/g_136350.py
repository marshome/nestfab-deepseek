"""0x136350: the constructor of the 216-byte element stored in Item+0x58 / Item+0x70.

Its member writes give the element's layout, which is the last missing piece of the per-part path.
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
prof = PROF.get(0x136350) or {}
print("=== 0x136350 size=%s nins=%s ===" % (prof.get("size"), prof.get("nins")))


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


for ins in disasm(0x136350, count=70):
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

print()
print("=== all calls ===")
for ins in disasm(0x136350):
    if ins.mnemonic == "call":
        op = ins.operands[0]
        if op.type == X86_OP_IMM:
            print("   @0x%-8x 0x%x %s" % (ins.address, op.imm, NAMES.get(op.imm, "")))
        else:
            print("   @0x%-8x [reg]" % ins.address)

print()
print("=== writes by base/offset (top 30) ===")
w = Counter()
for ins in disasm(0x136350):
    if not ins.operands:
        continue
    d = ins.operands[0]
    if d.type == X86_OP_MEM and d.mem.base not in (0, 41) and d.mem.index == 0:
        reg = ins.reg_name(d.mem.base)
        if reg not in ("rsp", "rbp") and ins.mnemonic.startswith(
                ("mov", "movsd", "movups", "movaps", "movapd", "add", "or", "and", "xor", "lea")):
            w[(reg, d.mem.disp)] += 1
for (reg, disp), n in sorted(w.items(), key=lambda kv: (kv[0][1], kv[0][0]))[:30]:
    print("   [%s+0x%x] x%d" % (reg, disp, n))
