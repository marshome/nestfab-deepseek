"""Attempt to recover the field layout of the three Prc data-only types from their log/
construction sites, since they have NO typeinfo object (orphan name strings only).

0x220ED0 (563 B) logs 'AP ' and 'AlphaSurfacePricer '.
0x23B080 (922 B) logs 'Pb pricing ' and lives in old_beam.cpp.
Field writes (`movsd [reg+off], xmm`, `mov [reg+off], imm`) reveal a struct layout.
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
OUT = r"D:\Nesting\nestfab\re\out_g_prc_layout.txt"
fh = open(OUT, "w", encoding="utf-8")


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


for rva, tag in ((0x220ED0, "AlphaSurfacePricer / DimPricer log site"),
                 (0x23B080, "Pb pricing (old_beam.cpp)")):
    prof = PROF.get(rva) or {}
    print("#### 0x%X %s  size=%s nins=%s" % (rva, tag, prof.get("size"), prof.get("nins")), file=fh)
    for ins in disasm(rva):
        s = "%-8x %-42s" % (ins.address, ins.mnemonic + " " + ins.op_str)
        notes = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                notes.append("STR@%x %r" % (t, STRS[t][:60]) if t in STRS else "data@%x" % t)
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                notes.append("%s(0x%x)" % (name_of(op.imm), op.imm))
        if notes:
            s += "   ; " + " | ".join(notes)
        print(s, file=fh)
    print(file=fh)

# field-write summary: which offsets of which structs get written
print(file=fh)
print("#### field writes (movsd / mov to [reg+disp])", file=fh)
for rva in (0x220ED0, 0x23B080):
    print("--- 0x%x" % rva, file=fh)
    for ins in disasm(rva):
        if ins.mnemonic in ("movsd", "movss", "mov", "movaps", "movups") and ins.operands:
            dst = ins.operands[0]
            if dst.type == X86_OP_MEM and dst.mem.base != X86_REG_RIP and dst.mem.disp != 0:
                print("    %-8x %-42s" % (ins.address, ins.mnemonic + " " + ins.op_str), file=fh)
fh.close()
print("wrote", OUT)
