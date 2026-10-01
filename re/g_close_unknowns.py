"""Targeted dumps to close the remaining unknowns, one file each.

  out_g_1380d0.txt     Row::Squeezer cost 0x1380D0 (476 insns) -- the formula
  out_g_267a30.txt     Clp load routine 0x267A30 (the callee of 0x7CA830)
  out_g_7ca830.txt     0x7CA830 (3778 B) -- its Clp entry points and branch structure
  out_g_factory.txt    the pricer factory 0x4D64C0 and its neighbours
"""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


TARGETS = [
    (0x1380D0, "Row::Squeezer cost function", r"D:\Nesting\nestfab\re\out_g_1380d0.txt"),
    (0x267A30, "Clp load routine", r"D:\Nesting\nestfab\re\out_g_267a30.txt"),
    (0x7CA830, "assembly routine", r"D:\Nesting\nestfab\re\out_g_7ca830.txt"),
    (0x4D64C0, "pricer factory", r"D:\Nesting\nestfab\re\out_g_factory.txt"),
]

for rva, tag, path in TARGETS:
    prof = PROF.get(rva) or {}
    with open(path, "w", encoding="utf-8") as fh:
        print("#### 0x%X %s  size=%s nins=%s" % (rva, tag, prof.get("size"), prof.get("nins")),
              file=fh)
        for ins in disasm(rva):
            s = "%-8x %-44s" % (ins.address, ins.mnemonic + " " + ins.op_str)
            notes = []
            for op in ins.operands:
                if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                    t = ins.address + ins.size + op.mem.disp
                    if t in STRS:
                        notes.append("STR@%x %r" % (t, STRS[t][:70]))
                    else:
                        notes.append("virt@%x" % t if t > 0x1000 else "data@%x" % t)
                elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                    notes.append("%s(0x%x)" % (name_of(op.imm), op.imm))
            if notes:
                s += "   ; " + " | ".join(notes)
            print(s, file=fh)
    print("wrote", path)

# callee summary for the three big ones, so Clp entry points stand out
for rva in (0x1380D0, 0x267A30, 0x7CA830, 0x4D64C0):
    print()
    print("=== 0x%x %s callees ===" % (rva, name_of(rva)))
    seen = {}
    for ins in disasm(rva):
        if ins.mnemonic == "call":
            op = ins.operands[0]
            if op.type == X86_OP_IMM:
                seen[op.imm] = seen.get(op.imm, 0) + 1
            else:
                print("    virtual: %s" % ins.op_str)
    for t, n in sorted(seen.items(), key=lambda kv: -kv[1]):
        print("    x%-3d 0x%-8x %-24s size=%s" % (n, t, name_of(t), (PROF.get(t) or {}).get("size")))
