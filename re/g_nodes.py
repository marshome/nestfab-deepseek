"""Where do the score nodes come from? Read the merge 0x137A90 and its small helpers.

0x137A90 (1175 B) starts by calling 0x1331A0 and 0x1333C0 on the rsp+0x110 object, and 0x136C90 on
rsi; it reads [rax+0x10]/[rax+0x18] as doubles and walks a container backwards by 0x10. Print the
helpers in full plus 0x137A90's calls, constants and member writes.
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


def dump(fn, count=None):
    prof = PROF.get(fn) or {}
    print()
    print("=== 0x%x %s size=%s nins=%s ===" % (fn, NAMES.get(fn, "?"), prof.get("size"),
                                               prof.get("nins")))
    for ins in disasm(fn, count=count):
        ctx = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS:
                    ctx.append("STR@%x %r" % (t, STRS[t][:38]))
                else:
                    v = f64(t)
                    ctx.append("data@%x=%r" % (t, v))
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
        print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))


for f in (0x1331A0, 0x1333C0, 0x136C90):
    dump(f, count=30)

print()
print("=== 0x137A90: calls in order ===")
for ins in disasm(0x137A90):
    if ins.mnemonic == "call":
        op = ins.operands[0]
        nm = NAMES.get(op.imm, "") if op.type == X86_OP_IMM else "[reg]"
        t = ("0x%x" % op.imm) if op.type == X86_OP_IMM else ""
        print("   @0x%-8x %s %s" % (ins.address, t, nm))

print()
print("=== 0x137A90: rodata constants ===")
seen = set()
for ins in disasm(0x137A90):
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            if t not in seen and t not in STRS:
                seen.add(t)
                print("   @0x%-8x data@0x%-8x = %r" % (ins.address, t, f64(t)))
            elif t in STRS and t not in seen:
                seen.add(t)
                print("   @0x%-8x STR@0x%-8x %r" % (ins.address, t, STRS[t][:44]))

print()
print("=== 0x137A90: writes by base/offset (top 20) ===")
w = Counter()
for ins in disasm(0x137A90):
    if not ins.operands:
        continue
    d = ins.operands[0]
    if d.type == X86_OP_MEM and d.mem.base not in (0, 41) and d.mem.index == 0:
        reg = ins.reg_name(d.mem.base)
        if reg not in ("rsp", "rbp") and ins.mnemonic.startswith(
                ("mov", "movsd", "movups", "movaps", "add", "or", "and", "xor")):
            w[(reg, d.mem.disp)] += 1
for (reg, disp), n in sorted(w.items(), key=lambda kv: -kv[1])[:20]:
    print("   [%s+0x%x] x%d" % (reg, disp, n))
