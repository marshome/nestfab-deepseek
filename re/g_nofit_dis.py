"""Disassemble the nofit_map.cpp cluster, which was enumerated but never disassembled.

The Minkowski convolution primitive (exact/convolution.cpp) WAS recovered instruction by
instruction; what was never opened is the code that consumes the raw convolution and turns it
into a valid no-fit polygon for non convex inputs:
    NoFitMapWithoutHoles        0x59E9D0  (10198 B, 2154 insns)
    0x59CD10                    0x59CD10  ( 7356 B, 1619 insns)
    0x59C560                    0x59C560  ( 1961 B,  420 insns)
    0x5A11B0                    0x5A11B0  ( 4990 B, 1225 insns)
    0x5A2690                    0x5A2690  ( 2286 B,  527 insns)
    0x5A3AA0                    0x5A3AA0  ( 2633 B,  676 insns)
"""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from g3_dis import dump, label_fn  # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:  # pragma: no cover - fall back to the profile names
    NAMES = {}

PROF = load_prof()


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or "?"

TARGETS = [0x59C560, 0x59CD10, 0x59E9D0, 0x5A11B0, 0x5A2690, 0x5A3AA0]

OUT = r"D:\Nesting\nestfab\re\out_g_nofit_dis.txt"
with open(OUT, "w", encoding="utf-8") as fh:
    import contextlib

    with contextlib.redirect_stdout(fh):
        for rva in TARGETS:
            dump(rva)
            print()
print("wrote", OUT)

# Also collect the call edges and any floating point / integer comparison structure,
# so the shape of the algorithm can be read without the full listing.
print()
print("=== call edges out of each target ===")
for rva in TARGETS:
    callees = {}
    for ins in disasm(rva):
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM:
            t = ins.operands[0].imm
            callees[t] = callees.get(t, 0) + 1
    print("0x%x %s ->" % (rva, name_of(rva) or "?"))
    for t, n in sorted(callees.items(), key=lambda kv: -kv[1]):
        print("    x%-3d %s" % (n, label_fn(t)))

print()
print("=== assertion / string references inside each target ===")
for rva in TARGETS:
    ext = func_extent(rva)
    if not ext:
        continue
    seen = set()
    print("0x%x %s:" % (rva, name_of(rva) or "?"))
    for ins in disasm(rva):
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS and t not in seen:
                    seen.add(t)
                    print("    @0x%x %r" % (t, STRS[t][:100]))
