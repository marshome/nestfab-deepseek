"""Who references the rodata tags 'AP ' (0x9C1C92) and 'DP ' (0x9C1CAA), and the two names?

These are rodata strings, so references to them ARE reliable (unlike string-table hits inside
.text). If a constructor that takes the double 0.5 references 'AP ' while the one taking 0.1
references 'DP ', the BoostAlpha / DimAlpha attribution is settled.
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


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


WATCH = {
    0x9C1C92: "'AP '",
    0x9C1C96: "'AlphaSurfacePricer '",
    0x9C1CAA: "'DP '",
    0x9C1CAE: "'DimPricer '",
    0x9C1CC0: "'static_cast<long long>(pricer.m_prices[p]) >= 0'",
    0xA22260: "N3Prc10BoostAlphaE",
    0xA222A0: "N3Prc13SurfaceCoeffsE",
    0xA22340: "N3Prc8DimAlphaE",
}

print("=== code references to the pricer tag strings and orphan RTTI names ===")
for target, label in WATCH.items():
    sites = []
    for rva in sorted(PROF):
        try:
            for ins in disasm(rva):
                for op in ins.operands:
                    if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                        t = ins.address + ins.size + op.mem.disp
                        if t == target:
                            sites.append((rva, ins.address))
        except Exception:
            continue
    print()
    print("  %-52s @0x%x : %d reference(s)" % (label, target, len(sites)))
    for rva, site in sites[:10]:
        extra = ""
        prof = PROF.get(rva) or {}
        print("      in 0x%-8x %-26s size=%-5s @0x%x" % (rva, name_of(rva), prof.get("size"), site))
        extra = extra
