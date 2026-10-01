"""0x134470 (572 B / 146 insns) -- the per-part path that also takes the core's config block.

Called from 0x6AABC0 once per Part:
    6AB716  r12 = rbp + 8                      ; the config block
    6AB72E  call 0x134470(rcx=r15, rdx=rsp+0x1b0, r8=rsp+0x1d0, r9=r12)
Compressed view: calls, floating point, member offsets and control flow.
"""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()
prof = PROF.get(0x134470) or {}
print("=== 0x134470 %s size=%s nins=%s ===" % (NAMES.get(0x134470, "?"), prof.get("size"),
                                               prof.get("nins")))
for ins in disasm(0x134470):
    keep = (ins.mnemonic.startswith(("mov", "call", "j", "cmp", "test", "add", "sub", "lea",
                                     "ret", "pxor", "xor", "ucomi", "comi", "mul", "div", "sqrt",
                                     "and", "or"))
            or ins.mnemonic in ("movsd", "movapd", "addsd", "subsd", "mulsd", "divsd", "sqrtsd"))
    if not keep:
        continue
    ctx = []
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            ctx.append("STR@%x %r" % (t, STRS[t][:44]) if t in STRS else "data@%x" % t)
        elif op.type == X86_OP_IMM and ins.mnemonic == "call":
            ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
    print("   %-8x %-44s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))
