"""Is the parameter block produced by 0x185A40 tractable?

SetCommonCutParameters does:
    3C4ED  call 0x185A40(rbp = rsp+0xF0, rsi = arg2, r12)
    3C4F2  [Pb+0x188] = [rsp+0xF0]
    3C508  [Pb+0x190] = [rsp+0xF8]
    3C51A  [Pb+0x198] = [rsp+0x100]
    ... one qword per Pb field up to +0x1C0, then a dword and a word
So the struct written at rsp+0xF0 is the parameter block itself. Print 0x185A40's size and the
stack offsets it writes, which gives the block's field pairing.
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
fn = 0x185A40
prof = PROF.get(fn) or {}
print("=== 0x%x %s size=%s nins=%s ===" % (fn, NAMES.get(fn, "?"), prof.get("size"),
                                           prof.get("nins")))
print()
print("--- first 45 instructions ---")
for ins in disasm(fn, count=45):
    note = ""
    if ins.mnemonic == "call":
        op = ins.operands[0]
        note = ("call 0x%x %s" % (op.imm, NAMES.get(op.imm, ""))) if op.type == X86_OP_IMM else "call [reg]"
    print("   %-8x %-44s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, note))

print()
print("--- stack slots written (as [rsp+N]) ---")
w = Counter()
for ins in disasm(fn):
    if ins.operands and ins.mnemonic.startswith(("mov", "movsd", "movups", "movaps")):
        d = ins.operands[0]
        if d.type == X86_OP_MEM and ins.reg_name(d.mem.base) == "rsp":
            w[d.mem.disp] += 1
for disp, n in sorted(w.items()):
    print("   [rsp+0x%x] x%d" % (disp, n))

print()
print("--- all calls ---")
seen = []
for ins in disasm(fn):
    if ins.mnemonic == "call":
        op = ins.operands[0]
        t = op.imm if op.type == X86_OP_IMM else None
        k = (t, NAMES.get(t, "") if t else "[reg]")
        if k not in seen:
            seen.append(k)
for t, n in seen:
    print("   0x%-8x %s" % (t or 0, n))
