"""Dump 0x585CA0 -- the function that drives the exact convolution for the no-fit map.

Signature recovered earlier from register usage:
    (out, polygon2, polygon1, int max_complexity, bool, double tolerance)
It is called from ComputeNoFitSheetMap 0x665F40 and from 0x674680 / 0x7E6010 / 0x6673F0 /
0x665BF0 / 0x55FC70. Reading it answers: how are NON CONVEX operands handled?
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
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or "sub_%x" % rva


OUT = r"D:\Nesting\nestfab\re\out_g_585ca0.txt"
with open(OUT, "w", encoding="utf-8") as fh:
    for rva in (0x585CA0, 0x585EB0):
        print("#### 0x%X %s size=%s nins=%s" % (rva, name_of(rva),
                                               (PROF.get(rva) or {}).get("size"),
                                               (PROF.get(rva) or {}).get("nins")), file=fh)
        for ins in disasm(rva):
            s = "%-8x %-38s" % (ins.address, ins.mnemonic + " " + ins.op_str)
            notes = []
            for op in ins.operands:
                if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                    t = ins.address + ins.size + op.mem.disp
                    if t in STRS:
                        notes.append("STR@%x %r" % (t, STRS[t][:80]))
                    else:
                        notes.append("data@%x" % t)
                elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                    notes.append("%s(0x%x)" % (name_of(op.imm), op.imm))
            if notes:
                s += "   ; " + " | ".join(notes)
            print(s, file=fh)
        print(file=fh)
print("wrote", OUT)
