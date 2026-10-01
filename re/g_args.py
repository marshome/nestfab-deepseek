"""0x5CEE50 and 0x5D38C0: what do they build from the per-part 48 byte element buffer?

Argument flow recovered so far:
  0x6AABC0: call 0x134470(rcx = rsp+0x190, rdx = rsp+0x1b0 (the 48-byte element buffer),
                         r8 = rsp+0x1d0, r9 = core+8)
  0x134470: rbp = rcx (out); rdi = rdx (buffer); rsi = r8; r12 = r9 (config)
            loop element rbx -> call 0x133DE0(rcx = rdi (buffer), rdx = rsi, r8 = rbx, r9 = r12)
  0x133DE0: rbx = rcx (buffer); r13 = rdx; r12 = r8 (loop element); rsi = r9 (config)
            call 0x5CEE50(rsp+0x170, rdx = the loop element)
            call 0x5D38C0(rsp+0x40, rdx = rbx (buffer), r8 = rsp+0x170)
            call 0x5CD800(rsp+0xE0, rdx = rsp+0x40)      -> the candidate's box
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
for fn in (0x5CEE50, 0x5D38C0):
    prof = PROF.get(fn) or {}
    print()
    print("=== 0x%x %s size=%s nins=%s ===" % (fn, NAMES.get(fn, "?"), prof.get("size"),
                                               prof.get("nins")))
    for ins in disasm(fn, count=55):
        ctx = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS:
                    ctx.append("STR@%x %r" % (t, STRS[t][:34]))
                else:
                    off = rva2off(t)
                    v = struct.unpack("<d", data[off:off + 8])[0] if off else None
                    ctx.append("data@%x=%r" % (t, v))
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
