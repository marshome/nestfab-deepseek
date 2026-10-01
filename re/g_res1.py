"""Residual items (1) and (2): 0x8BEFC0 (the candidate-angle source) and 0x134D70 (the flags).

0x134470 does:
    1344FC  call 0x8BEFC0(rcx = rsp+0x70, rdx = rsp+0x3f, r8 = rsp+0x40)
and 0x136350 does:
    136433  call 0x1333C0(rdi) ; 13643E call 0x134D70(rsp+0x50, rax) -> al ; 13644B byte [rbx+0x40] = al
Print sizes, prologues, calls and constants for both.
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


for fn, label in ((0x8BEFC0, "candidate-angle source"), (0x134D70, "the flag computation")):
    prof = PROF.get(fn) or {}
    print()
    print("=== 0x%x (%s) size=%s nins=%s ===" % (fn, label, prof.get("size"), prof.get("nins")))
    for ins in disasm(fn, count=60):
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
        print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(ctx)))
    print("   -- all calls --")
    for ins in disasm(fn):
        if ins.mnemonic == "call":
            op = ins.operands[0]
            if op.type == X86_OP_IMM:
                print("      @0x%-8x 0x%x %s" % (ins.address, op.imm, NAMES.get(op.imm, "")))
            else:
                print("      @0x%-8x [reg]" % ins.address)
