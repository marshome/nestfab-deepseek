"""Origin of the core's two doubles (+0x18 threshold, +0x20 coefficient).

0x8F210 passes `rdx = <result of call 0x30260>` to 0x6AABC0, which fills the 208 byte core.
Find where the core's +0x18 / +0x20 are written and what they are read from, and what 0x30260 is.
"""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


def notes_for(ins):
    note = []
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            note.append("STR@%x %r" % (t, STRS[t][:50]) if t in STRS else "data@%x" % t)
        elif op.type == X86_OP_IMM and ins.mnemonic == "call":
            note.append("%s(0x%x)" % (name_of(op.imm), op.imm))
    return note


print("=== 0x6AABC0 prologue (first 70 instructions) ===")
for i, ins in enumerate(disasm(0x6AABC0, count=70)):
    n = notes_for(ins)
    print("   %-8x %-44s %s" % (ins.address, ins.mnemonic + " " + ins.op_str,
                                ("; " + " | ".join(n)) if n else ""))

print()
print("=== every store to [reg+0x18] / [reg+0x20] inside 0x6AABC0 ===")
for ins in disasm(0x6AABC0):
    if not ins.operands or ins.mnemonic not in ("mov", "movsd", "movaps", "movapd", "movups"):
        continue
    d = ins.operands[0]
    if d.type == X86_OP_MEM and d.mem.base not in (0, X86_REG_RIP) and d.mem.disp in (0x18, 0x20):
        base = ins.reg_name(d.mem.base)
        if base in ("rsp", "rbp"):
            continue
        print("   %-8x %-44s %s" % (ins.address, ins.mnemonic + " " + ins.op_str,
                                    ("; " + " | ".join(notes_for(ins))) if notes_for(ins) else ""))

print()
print("=== 0x30260 in full ===")
prof = PROF.get(0x30260) or {}
print("   size=%s nins=%s" % (prof.get("size"), prof.get("nins")))
for ins in disasm(0x30260, count=60):
    n = notes_for(ins)
    print("   %-8x %-44s %s" % (ins.address, ins.mnemonic + " " + ins.op_str,
                                ("; " + " | ".join(n)) if n else ""))
