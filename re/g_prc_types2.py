"""Corrected probe for Prc::BoostAlpha / SurfaceCoeffs / DimAlpha.

Mistake in the previous attempt: pointers stored in the DATA section of a memory dump hold the
runtime absolute VA (ImageBase + RVA, ImageBase = 0x6B4C0000), not the bare RVA. RIP-relative
`lea` targets on the other hand resolve to the bare RVA when computed from the file. So:
  * to find the typeinfo object of a name string, search for pack("<Q", ImageBase + name_rva)
  * to find code that uses a typeinfo object, compute the lea target as a bare RVA
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
IMAGE_BASE = 0x6B4C0000


def u64_at(rva):
    off = rva2off(rva)
    if off is None or off + 8 > len(data):
        return None
    return u64(off)


print("=== sanity: known typeinfo objects ===")
for ti, label in ((0xA17D50, "Prc::PriceComputer"), (0xA17D40, "Lp::LinearProgram"),
                  (0xA17D60, "Prc::BoxPriceComputer"), (0xA17EA0, "Coin::CoinLP")):
    v = u64_at(ti + 8)
    print("  typeinfo 0x%-8x %-24s [+8] = 0x%x  -> name RVA 0x%x %r"
          % (ti, label, v or 0, (v or 0) - IMAGE_BASE, STRS.get((v or 0) - IMAGE_BASE, "")[:40]))

NAME_STRINGS = {
    0xA22260: "N3Prc10BoostAlphaE",
    0xA222A0: "N3Prc13SurfaceCoeffsE",
    0xA22340: "N3Prc8DimAlphaE",
    0xA22280: "N3Prc13PriceComputerE",
    0xA222C0: "N3Prc16BoxPriceComputerE",
}

print()
print("=== 1. who points at each name string (absolute VA search) ===")
typeinfos = {}
for target, label in NAME_STRINGS.items():
    needle = struct.pack("<Q", IMAGE_BASE + target)
    offs = []
    start = 0
    while True:
        i = data.find(needle, start)
        if i < 0:
            break
        offs.append(i)
        start = i + 1
    print("  %-30s rva 0x%-8x : %d pointer(s)" % (label, target, len(offs)))
    for off in offs:
        print("        stored at file off 0x%x -> typeinfo object at 0x%x" % (off, off - 8))
        typeinfos.setdefault(off - 8, []).append(label)

print()
print("=== 2. code sites that lea those typeinfo objects (bare RVA) ===")
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
    print("  typeinfo 0x%-8x (%-30s): %d code ref(s)"
          % (cand, ",".join(labels), len(hits)))
    for rva, site, text in hits[:10]:
        print("      0x%-8x @0x%-8x  %-38s [in %s]" % (rva, site, text, NAMES.get(rva) or ""))

print()
print("=== 3. the two log sites, full string inventory ===")
for rva in (0x220ED0, 0x23B080):
    prof = PROF.get(rva) or {}
    print()
    print("--- 0x%x size=%s nins=%s" % (rva, prof.get("size"), prof.get("nins")))
    for ins in disasm(rva):
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS:
                    print("    @0x%-7x STR@0x%-8x %r" % (ins.address, t, STRS[t][:70]))
