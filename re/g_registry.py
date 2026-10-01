"""Inspect the reflection registry 0x6CC9D0 around its three orphan-type name references.

The three names Prc::BoostAlpha / SurfaceCoeffs / DimAlpha have no typeinfo object yet ARE
referenced by 0x6CC9D0 (18272 B), which looks like a name registry / reflection table. A table
that also lists members would give the field layouts outright.
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


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


SITES = [0x6CCB6E, 0x6CD080, 0x6CD631]
print("=== instruction windows around the three name references in 0x6CC9D0 ===")
lines = list(disasm(0x6CC9D0))
for target in SITES:
    for idx, ins in enumerate(lines):
        if ins.address == target:
            print()
            print("--- site 0x%x ---" % target)
            for j in range(max(0, idx - 10), min(len(lines), idx + 12)):
                note = []
                for op in lines[j].operands:
                    if op.type == X86_OP_MEM and lines[j].operands and lines[j].operands[0].type == X86_OP_MEM:
                        pass
                    if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                        t = lines[j].address + lines[j].size + op.mem.disp
                        if t in STRS:
                            note.append("STR@%x %r" % (t, STRS[t][:60]))
                        else:
                            note.append("data@%x" % t)
                    elif op.type == X86_OP_IMM and lines[j].mnemonic == "call":
                        note.append("%s(0x%x)" % (name_of(op.imm), op.imm))
                print("   %-8x %-42s %s" % (lines[j].address, lines[j].mnemonic + " " + lines[j].op_str,
                                            ("; " + " | ".join(note)) if note else ""))
            break

print()
print("=== rodata strings near the three RTTI names (0xA22240-0xA22380) ===")
for rva in sorted(STRS):
    if 0xA22240 <= rva <= 0xA22390:
        print("   0x%-8x %r" % (rva, STRS[rva][:70]))
