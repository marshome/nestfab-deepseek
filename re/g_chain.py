"""Confirm the exact call chain of the non-convex no-fit path.

0x585CA0 (adapter, converts to exact representation) -> 0x5A2530 -> 0x5A11B0
    -> 0x59E9D0 NoFitMapWithoutHoles -> 0x59CD10 x4
and 0x59CD10 itself calls 0x5A2530, which would make the whole thing recursive.
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


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


for rva in (0x5A2530, 0x5A11B0, 0x59CD10):
    print()
    print("===== 0x%x %s (size %s) =====" % (rva, name_of(rva) or "(unnamed)",
                                             (PROF.get(rva) or {}).get("size")))
    for ins in disasm(rva):
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM:
            t = ins.operands[0].imm
            print("    @0x%-7x call 0x%-8x %s" % (ins.address, t, name_of(t)))

print()
print("=== who calls 0x5A11B0 and 0x5A2530 (recursion check) ===")
for target in (0x5A11B0, 0x5A2530, 0x5A2690):
    callers = []
    for rva in sorted(PROF):
        try:
            for ins in disasm(rva):
                if (ins.mnemonic == "call" and ins.operands
                        and ins.operands[0].type == X86_OP_IMM
                        and ins.operands[0].imm == target):
                    callers.append((rva, ins.address))
        except Exception:
            continue
    print("0x%x %s <- %s" % (target, name_of(target) or "(unnamed)",
                             ", ".join("0x%x@0x%x" % (f, s) for f, s in callers) or "none"))
