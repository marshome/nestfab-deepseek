"""Accessors in the database TU (0x4F0000-0x500000) that compute Pb+0x198 / +0x1B8 / +0x1C0.

The Pb accessors live in this range (0x4FC2F0, 0x4FC300, 0x4FC3A0, 0x4FC3C0, 0x4FC5A0, ...),
so a getter for the fields feeding core+0x28/+0x30/+0x38 should be a small function here whose
only work is `mov rax,[rcx]` plus an `add`/`lea` with that displacement.
"""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_MEM, X86_OP_IMM  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()
WANT = (0x170, 0x178, 0x180, 0x188, 0x190, 0x198, 0x1A0, 0x1A8, 0x1B0, 0x1B8, 0x1C0)

print("=== small accessors in the database TU touching those Pb offsets ===")
for rva in sorted(PROF):
    if not (0x4F0000 <= rva < 0x500000):
        continue
    prof = PROF.get(rva) or {}
    size = prof.get("size") or 0
    if size > 40:
        continue
    offs = []
    for ins in disasm(rva):
        if ins.mnemonic in ("add", "lea", "mov", "movzx", "movsd", "cmp") and ins.operands:
            for op in ins.operands:
                if op.type == X86_OP_MEM and op.mem.disp in WANT and op.mem.base not in (0, 41):
                    offs.append(op.mem.disp)
    if not offs:
        continue
    print()
    print("--- 0x%x %s size=%s offsets=%s" % (rva, NAMES.get(rva, "?"), size,
                                              ",".join("0x%x" % o for o in sorted(set(offs)))))
    for ins in disasm(rva):
        print("      %-8x %s %s" % (ins.address, ins.mnemonic, ins.op_str))
