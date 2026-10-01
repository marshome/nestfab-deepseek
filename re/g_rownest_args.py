"""Argument setup of the two calls inside Multi::RowNester (0x6AABC0 = ..\\multi\\row_nester.cpp)."""
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


def window(fn, site, back=30, fwd=10):
    print()
    print("=== 0x%x inside 0x%x %s ===" % (site, fn, name_of(fn)))
    lines = list(disasm(fn))
    for idx, ins in enumerate(lines):
        if ins.address == site:
            for j in range(max(0, idx - back), min(len(lines), idx + fwd)):
                notes = []
                for op in lines[j].operands:
                    if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                        t = lines[j].address + lines[j].size + op.mem.disp
                        if t in STRS:
                            notes.append("STR@%x %r" % (t, STRS[t][:40]))
                        else:
                            notes.append("data@%x" % t)
                    elif op.type == X86_OP_IMM and lines[j].mnemonic == "call":
                        notes.append("%s(0x%x)" % (name_of(op.imm), op.imm))
                print("   %-8x %-42s %s" % (lines[j].address, lines[j].mnemonic + " " + lines[j].op_str,
                                            ("; " + " | ".join(notes)) if notes else ""))
            break


window(0x6AABC0, 0x6AC10C)
window(0x6AABC0, 0x6AB72E)

print()
print("=== every call inside 0x6AABC0, in order, with the callee name ===")
seen = []
for ins in disasm(0x6AABC0):
    if ins.mnemonic == "call":
        op = ins.operands[0]
        if op.type == X86_OP_IMM:
            nm = name_of(op.imm)
            if (op.imm, nm) not in seen:
                seen.append((op.imm, nm))
                print("   @0x%-8x 0x%-8x %s" % (ins.address, op.imm, nm))
