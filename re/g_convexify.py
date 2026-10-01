"""Who uses the exact convolution wrapper (0x585CA0), and is the Convexifier reached from
the no-fit path? This decides how the original handles NON CONVEX operands."""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_IMM  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


WATCH = {
    0x585CA0: "convolution wrapper (exact kernel entry)",
    0x585EB0: "sub_585EB0 (calls sub_59C560)",
    0x93FD50: "Convexifier 0x93FD50",
    0x940AE0: "Convexifier 0x940AE0",
    0x5A47B0: "ConvexHull kernel sub_5A47B0",
    0x59E9D0: "NoFitMapWithoutHoles",
}

print("=== callers ===")
found = {k: [] for k in WATCH}
for rva, info in sorted(PROF.items()):
    try:
        insns = list(disasm(rva))
    except Exception:
        continue
    for ins in insns:
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM:
            t = ins.operands[0].imm
            if t in found:
                found[t].append(rva)

for t, who in WATCH.items():
    print()
    print("0x%x %s   size=%s" % (t, who, (PROF.get(t) or {}).get("size")))
    for fn in sorted(set(found[t])):
        print("    <- 0x%-8x %-38s size=%s" % (fn, name_of(fn), (PROF.get(fn) or {}).get("size")))

print()
print("=== names of the interesting NFP-side callers ===")
for a in (0x55FC70, 0x665BF0, 0x665F40, 0x6673F0, 0x674680, 0x7E6010, 0x5A2530, 0x5A11B0,
          0x59CD10, 0x59C560, 0x585EB0, 0x582C00, 0x5972C0, 0x174860, 0x1A0940):
    print("    0x%-8x %-34s size=%s nins=%s" % (a, name_of(a) or "(unnamed)",
                                               (PROF.get(a) or {}).get("size"),
                                               (PROF.get(a) or {}).get("nins")))
