"""Readers of the Pb fields that feed the row core's +0x28 / +0x30 / +0x38.

The core takes them from Pb+0x198 (byte, pipe path), Pb+0x1B8 (byte) and Pb+0x1C0 (double).
If named exports read those offsets, their names give the semantics. Scan for instructions whose
SOURCE operand is [reg+offset] for those offsets.
"""
import sys
from collections import defaultdict

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()
OFFS = (0x170, 0x198, 0x1A0, 0x1A8, 0x1B0, 0x1B8, 0x1C0)

hits = defaultdict(set)
for rva in sorted(PROF):
    try:
        for ins in disasm(rva):
            for op in ins.operands[1:]:
                if op.type == X86_OP_MEM and op.mem.disp in OFFS and op.mem.base not in (0, 41):
                    if ins.reg_name(op.mem.base) in ("rsp", "rbp"):
                        continue
                    hits[op.mem.disp].add(rva)
    except Exception:
        continue

for off in OFFS:
    fns = sorted(hits.get(off, ()))
    named = [f for f in fns if NAMES.get(f)]
    print()
    print("=== Pb+0x%-4x read in %d function(s); %d named ===" % (off, len(fns), len(named)))
    for f in named[:14]:
        prof = PROF.get(f) or {}
        print("     0x%-8x %-32s size=%s" % (f, NAMES.get(f), prof.get("size")))
    unnamed = [f for f in fns if not NAMES.get(f)]
    if unnamed:
        print("     (unnamed readers: %s%s)"
              % (", ".join("0x%x" % f for f in unnamed[:12]),
                 " ..." if len(unnamed) > 12 else ""))

print()
print("=== all named exports that read ANY of them ===")
allnamed = sorted({f for fns in hits.values() for f in fns if NAMES.get(f)})
for f in allnamed:
    offs = sorted(o for o in OFFS if f in hits.get(o, ()))
    print("   0x%-8x %-34s size=%-6s offsets=%s"
          % (f, NAMES.get(f), (PROF.get(f) or {}).get("size"),
             ",".join("0x%x" % o for o in offs)))
