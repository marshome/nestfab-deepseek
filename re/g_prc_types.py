"""Close the last tractable unknown: Prc::BoostAlpha / SurfaceCoeffs / DimAlpha.

findings_lp.md said these three have RTTI *name strings* but "zero 8-byte pointer references",
concluding they are non polymorphic. That check looked for code referencing the NAME STRINGS.
The right chain is: typeinfo object -> its name string; code references the TYPEINFO object
(e.g. `lea reg,[rip+typeinfo]`). So:
  1. find the typeinfo objects that point at the name strings
  2. find every code site that `lea`s those typeinfo objects
  3. dump the surrounding code, which is where the class is constructed or type-checked
"""
import struct
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_MEM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()

NAME_STRINGS = {
    0xA22260: "N3Prc10BoostAlphaE",
    0xA222A0: "N3Prc13SurfaceCoeffsE",
    0xA22340: "N3Prc8DimAlphaE",
    0xA22280: "N3Prc13PriceComputerE",
}

print("=== 1. typeinfo objects that reference each name string ===")
typeinfos = {}
for target, label in NAME_STRINGS.items():
    needle = struct.pack("<Q", target)
    offs = []
    start = 0
    while True:
        i = data.find(needle, start)
        if i < 0:
            break
        offs.append(i)
        start = i + 1
    print("  %-28s @0x%-8x referenced by %d qword(s)" % (label, target, len(offs)))
    for off in offs:
        rva = off  # .text/.data are RVA==offset for the mapped region; report both
        # the typeinfo object starts 8 bytes before its name pointer (SI) or is the name pointer itself
        cand = off - 8
        print("        qword at file off 0x%x (rva 0x%x); candidate typeinfo object 0x%x"
              % (off, off, cand))
        typeinfos.setdefault(cand, []).append(label)

print()
print("=== 2. code sites that lea those candidate typeinfo objects ===")
for cand, labels in sorted(typeinfos.items()):
    hits = []
    for rva in sorted(PROF):
        try:
            for ins in disasm(rva):
                for op in ins.operands:
                    if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                        t = ins.address + ins.size + op.mem.disp
                        if t == cand:
                            hits.append((rva, ins.address, ins.mnemonic + " " + ins.op_str))
        except Exception:
            continue
    print("  typeinfo 0x%-8x (%s): %d code reference(s)" % (cand, ",".join(labels), len(hits)))
    for rva, site, text in hits[:12]:
        print("      0x%-8x @0x%-8x  %s   [in %s]" % (rva, site, text, NAMES.get(rva) or ""))

print()
print("=== 3. code around the AlphaSurfacePricer / DimPricer log strings ===")
for rva, s in ((0x220ED0, "AlphaSurfacePricer/DimPricer log site"),
               (0x23B080, "Pb pricing / old_beam.cpp")):
    prof = PROF.get(rva) or {}
    print()
    print("--- 0x%x %s size=%s nins=%s" % (rva, s, prof.get("size"), prof.get("nins")))
    seen_strings = []
    for ins in disasm(rva):
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS:
                    seen_strings.append((ins.address, t, STRS[t][:70]))
    for site, t, text in seen_strings:
        print("    @0x%-7x STR@0x%-8x %r" % (site, t, text))
