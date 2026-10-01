"""0x137A90 (1175 B / 261 insns): the record merge that fills the score container.

Entry (from 0x137FE0's loop): rcx = [rbx] (a pointer), edx = byte [rbx+8] (a tag),
r8 = rbp (the rsp+0x110 object), r9 = r12. Print the head and tail with jump targets annotated so
the block structure is visible without reading all 261 instructions at once.
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
lines = list(disasm(0x137A90))
prof = PROF.get(0x137A90) or {}
print("=== 0x137A90 size=%s nins=%s ===" % (prof.get("size"), prof.get("nins")))


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


def show(seq):
    for ins in seq:
        ctx = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS:
                    ctx.append("STR@%x %r" % (t, STRS[t][:34]))
                else:
                    ctx.append("data@%x=%r" % (t, f64(t)))
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
        print("   %-8x %-44s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))


print()
print("--- head: first 95 ---")
show(lines[:95])
print()
print("--- tail: last 60 ---")
show(lines[-60:])

print()
print("=== all jump targets inside the function (block boundaries) ===")
targets = sorted({op.imm for ins in lines for op in ins.operands
                  if op.type == X86_OP_IMM and ins.mnemonic.startswith("j")})
print("   " + ", ".join("0x%x" % t for t in targets))
