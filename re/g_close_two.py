"""Close two residual items:
  (a) 0x4F7690 -- the Part accessor that yields the 48 byte element container
  (b) which core fields (rbp+0x00/0x08/0x10/0x18/0x20/0x28/0x30/0x38/0x40) are actually READ
      inside 0x6AABC0, which shows what core+0x28 / +0x30 / +0x38 are for.
"""
import sys
from collections import Counter

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


print("=== (a) 0x4F7690 ===")
prof = PROF.get(0x4F7690) or {}
print("   size=%s nins=%s %s" % (prof.get("size"), prof.get("nins"), name_of(0x4F7690)))
for ins in disasm(0x4F7690, count=30):
    note = []
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            note.append("STR@%x %r" % (t, STRS[t][:40]) if t in STRS else "data@%x" % t)
        elif op.type == X86_OP_IMM and ins.mnemonic == "call":
            note.append("%s(0x%x)" % (name_of(op.imm), op.imm))
    print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str, "; ".join(note)))

print()
print("=== (b) reads of core fields inside 0x6AABC0 (rbp = the core) ===")
OFFS = (0x00, 0x08, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38, 0x40, 0xC0)
reads = Counter()
writes = Counter()
first_read = {}
for ins in disasm(0x6AABC0):
    if not ins.operands:
        continue
    d = ins.operands[0]
    if d.type == X86_OP_MEM and ins.reg_name(d.mem.base) == "rbp" and d.mem.disp in OFFS:
        if ins.mnemonic.startswith(("mov", "movsd", "add", "or", "and", "xor", "test", "cmp")):
            writes[d.mem.disp] += 1
    for op in ins.operands[1:]:
        if op.type == X86_OP_MEM and ins.reg_name(op.mem.base) == "rbp" and op.mem.disp in OFFS:
            reads[op.mem.disp] += 1
            first_read.setdefault(op.mem.disp, ins.address)
for off in OFFS:
    print("   core+0x%-4x reads=%-4d writes=%-4d first read @0x%x"
          % (off, reads.get(off, 0), writes.get(off, 0), first_read.get(off, 0)))
