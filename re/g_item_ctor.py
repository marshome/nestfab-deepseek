"""Item (0x90 bytes) layout, from its constructor 0x1333D0.

0x6AABC0 calls it as
    6AB757  call 0x1333D0(newObj, rsp+0x1b0, edx=partIndex, r8, r9=r15, [rsp+0x20]=r15,
                          [rsp+0x28]=core+8)
and then stores the returned pointer into the vector at core+0x48. The stores it makes into its
own object give the Item layout.
"""
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
prof = PROF.get(0x1333D0) or {}
print("=== 0x1333D0 %s size=%s nins=%s ===" % (NAMES.get(0x1333D0, "?"), prof.get("size"),
                                               prof.get("nins")))
for ins in disasm(0x1333D0, count=90):
    ctx = []
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            ctx.append("STR@%x %r" % (t, STRS[t][:44]) if t in STRS else "data@%x" % t)
        elif op.type == X86_OP_IMM and ins.mnemonic == "call":
            ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
    print("   %-8x %-44s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))

print()
print("=== all member writes (base = this register) and their offsets ===")
writes = Counter()
for ins in disasm(0x1333D0):
    if not ins.operands:
        continue
    d = ins.operands[0]
    if d.type == X86_OP_MEM and d.mem.base not in (0, 41) and d.mem.index == 0:
        reg = ins.reg_name(d.mem.base)
        if reg in ("rsp", "rbp"):
            continue
        if ins.mnemonic.startswith(("mov", "add", "or", "and", "xor")):
            writes[(reg, d.mem.disp)] += 1
for (reg, disp), n in sorted(writes.items(), key=lambda kv: (kv[0][0], kv[0][1])):
    print("   [%s+0x%x] x%d" % (reg, disp, n))
