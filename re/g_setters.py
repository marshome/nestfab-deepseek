"""Confirm the two setters: SetPipeMode (0xFCF0) -> +0x170, SetCommonCutParameters (0x3C3F0) ->
+0x1A0/+0x1A8/+0x1B0/+0x1B8/+0x1C0.

Those are exactly the gate byte and the five fields that Multi::RowNester's core reads through
0x4FC2F0 / 0x4FC300 / 0x4FC3C0.
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
WATCH = {0x170, 0x1A0, 0x1A8, 0x1B0, 0x1B8, 0x1C0}


def dump(fn, only_watch=False):
    prof = PROF.get(fn) or {}
    print()
    print("=== 0x%x %s size=%s nins=%s ===" % (fn, NAMES.get(fn, "?"), prof.get("size"),
                                               prof.get("nins")))
    lines = list(disasm(fn))
    for idx, ins in enumerate(lines):
        hit = False
        if ins.operands and ins.mnemonic.startswith(("mov", "or", "and", "xor", "add", "sub")):
            d = ins.operands[0]
            if d.type == X86_OP_MEM and d.mem.disp in WATCH and d.mem.base not in (0, 41):
                if ins.reg_name(d.mem.base) not in ("rsp", "rbp"):
                    hit = True
        if only_watch and not hit:
            continue
        ctx = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                ctx.append("STR@%x %r" % (t, STRS[t][:40]) if t in STRS else "data@%x" % t)
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                ctx.append("%s(0x%x)" % (NAMES.get(op.imm, "?"), op.imm))
        mark = "  <== WATCH" if hit else ""
        print("   %-8x %-42s %s%s" % (ins.address, ins.mnemonic + " " + ins.op_str,
                                      "; ".join(ctx), mark))


dump(0xFCF0, only_watch=True)
dump(0x3C3F0, only_watch=True)

print()
print("=== callers of SetPipeMode (0xFCF0) ===")
for rva in sorted(PROF):
    try:
        for ins in disasm(rva):
            if (ins.mnemonic == "call" and ins.operands
                    and ins.operands[0].type == X86_OP_IMM and ins.operands[0].imm == 0xFCF0):
                print("   0x%-8x %s size=%s" % (rva, NAMES.get(rva, "?"),
                                                (PROF.get(rva) or {}).get("size")))
    except Exception:
        continue
