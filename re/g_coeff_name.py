"""Attribute the 5-double coefficient struct (the `obj` of 0x4D64C0) to a name.

The three RTTI names Prc::BoostAlpha / Prc::SurfaceCoeffs / Prc::DimAlpha have NO typeinfo
object, so they can only be tied to code through the strings that name their members. Search
every string that looks like a coefficient/member identifier in the rprice translation unit,
then list which function references it.
"""
import re
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_MEM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()

KEYS = ["oeff", "urface", "lpha", "oost", "Dim", "weight", "Weight", "price", "Price",
        "specific", "Specific", "coef", "Coef"]


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


print("=== strings mentioning coefficient / alpha / surface identifiers ===")
hits = {}
for rva, s in sorted(STRS.items()):
    if not any(k in s for k in KEYS):
        continue
    if len(s) > 90:
        continue
    hits[rva] = s
for rva, s in list(hits.items())[:60]:
    print("   @0x%-8x %r" % (rva, s))
print("   total %d" % len(hits))

print()
print("=== which functions reference them (bounded scan) ===")
wanted = set(hits)
found = {}
for rva in sorted(PROF):
    try:
        for ins in disasm(rva):
            for op in ins.operands:
                if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                    t = ins.address + ins.size + op.mem.disp
                    if t in wanted:
                        found.setdefault(t, []).append((rva, ins.address))
    except Exception:
        continue
for t, sites in sorted(found.items()):
    fns = sorted(set(f for f, _ in sites))
    print("   %r" % STRS[t][:70])
    for f in fns[:6]:
        print("        referenced by 0x%-8x %-24s size=%s" % (f, name_of(f),
                                                              (PROF.get(f) or {}).get("size")))
