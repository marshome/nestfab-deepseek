"""Locate where the no-fit pipeline actually invokes the exact convolution primitive.

findings_geometry.md recovered the convolution core (0x596100) and its wrappers
(0x596F20 ConvolutionRaw, 0x597500, 0x585CA0, 0x5867C0 GetConvolutionLoops,
0x5873E0 GetNoFitConvolutions) but never connected them to the nofit_map.cpp cluster.
This script finds every caller of those wrappers.
"""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_IMM  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()

CONV = {
    0x596100: "convolution core",
    0x596F20: "ConvolutionRaw",
    0x597500: "sub_597500 (called by GetConvolutionLoops/GetNoFitConvolutions)",
    0x585CA0: "convolution wrapper (out,poly2,poly1,max_complexity,bool,tol)",
    0x5867C0: "GetConvolutionLoops",
    0x5873E0: "GetNoFitConvolutions",
    0x59E9D0: "NoFitMapWithoutHoles",
    0x59CD10: "sub_59CD10",
    0x59C560: "sub_59C560",
}


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


print("=== every function that calls a convolution entry point ===")
callers = {k: [] for k in CONV}
for rva, info in sorted(PROF.items()):
    try:
        insns = list(disasm(rva))
    except Exception:
        continue
    for ins in insns:
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM:
            t = ins.operands[0].imm
            if t in callers:
                callers[t].append((rva, ins.address))

for target, who in CONV.items():
    print()
    print("0x%x  %s   <- %d call site(s)" % (target, who, len(callers[target])))
    seen = {}
    for fn, site in callers[target]:
        seen.setdefault(fn, []).append(site)
    for fn, sites in sorted(seen.items()):
        print("    from 0x%-8x %-40s x%d" % (fn, name_of(fn), len(sites)))
