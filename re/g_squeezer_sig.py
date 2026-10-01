"""Signature of 0x1380D0 from its call site in Row::Squeezer slot2 = 0x13A360."""
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


print("=== call sites of 0x1380D0 anywhere ===")
for rva in sorted(PROF):
    try:
        for ins in disasm(rva):
            if (ins.mnemonic == "call" and ins.operands
                    and ins.operands[0].type == X86_OP_IMM and ins.operands[0].imm == 0x1380D0):
                print("   in 0x%x %s @0x%x" % (rva, name_of(rva), ins.address))
    except Exception:
        continue

print()
print("=== 0x13A360 window around its call to 0x1380D0 ===")
lines = list(disasm(0x13A360))
for idx, ins in enumerate(lines):
    if (ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM
            and ins.operands[0].imm == 0x1380D0):
        for j in range(max(0, idx - 26), min(len(lines), idx + 14)):
            note = []
            for op in lines[j].operands:
                if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                    t = lines[j].address + lines[j].size + op.mem.disp
                    if t in STRS:
                        note.append("STR@%x %r" % (t, STRS[t][:60]))
                    else:
                        note.append("data@%x" % t)
                elif op.type == X86_OP_IMM and lines[j].mnemonic == "call":
                    note.append("%s(0x%x)" % (name_of(op.imm), op.imm))
            print("   %-8x %-40s %s" % (lines[j].address, lines[j].mnemonic + " " + lines[j].op_str,
                                        ("; " + " | ".join(note)) if note else ""))
        print()

print("=== what 0x13A360 itself looks like (head) ===")
for ins in disasm(0x13A360, count=30):
    note = []
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            if t in STRS:
                note.append("STR@%x %r" % (t, STRS[t][:60]))
            else:
                note.append("data@%x" % t)
        elif op.type == X86_OP_IMM and ins.mnemonic == "call":
            note.append("%s(0x%x)" % (name_of(op.imm), op.imm))
    print("   %-8x %-40s %s" % (ins.address, ins.mnemonic + " " + ins.op_str,
                                ("; " + " | ".join(note)) if note else ""))
