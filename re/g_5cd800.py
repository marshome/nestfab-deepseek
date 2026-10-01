"""What is 0x5CD800 (..\\geom\\properties.cpp) and what does its bool flag mean?

It returns a flag plus four doubles, consumed by 0x13C380. Look at how it fills its out struct and
what it calls; that identifies the flag and the four doubles.
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


prof = PROF.get(0x5CD800) or {}
print("=== 0x5CD800 %s size=%s nins=%s ===" % (name_of(0x5CD800), prof.get("size"),
                                               prof.get("nins")))
lines = list(disasm(0x5CD800))
print("--- first 55 ---")
for ins in lines[:55]:
    note = []
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            note.append("STR@%x %r" % (t, STRS[t][:46]) if t in STRS else "data@%x" % t)
        elif op.type == X86_OP_IMM and ins.mnemonic == "call":
            note.append("%s(0x%x)" % (name_of(op.imm), op.imm))
    print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str,
                                ("; " + " | ".join(note)) if note else ""))
print("--- last 45 ---")
for ins in lines[-45:]:
    note = []
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            note.append("STR@%x %r" % (t, STRS[t][:46]) if t in STRS else "data@%x" % t)
        elif op.type == X86_OP_IMM and ins.mnemonic == "call":
            note.append("%s(0x%x)" % (name_of(op.imm), op.imm))
    print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str,
                                ("; " + " | ".join(note)) if note else ""))

print()
print("=== callees of 0x5CD800 ===")
seen = []
for ins in lines:
    if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM:
        t = ins.operands[0].imm
        if t not in [s[0] for s in seen]:
            seen.append((t, name_of(t)))
for t, n in seen:
    print("   0x%-8x %s" % (t, n))
