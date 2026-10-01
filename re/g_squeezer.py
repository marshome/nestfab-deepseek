"""Row::Squeezer cost 0x1380D0: identify its small helpers first, then read the numeric core.

helpers called by 0x1380D0 : 0x5C22D0 (157 B), 0x134FA0 (68 B), 0x134FF0 (21 B)
plus sqrt x2, sin x1.
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


print("=== small helpers ===")
for rva in (0x5C22D0, 0x134FA0, 0x134FF0, 0x134F00, 0x134E00):
    prof = PROF.get(rva) or {}
    if not prof:
        print("  0x%x : not in profile" % rva)
        continue
    print()
    print("--- 0x%x %s size=%s nins=%s" % (rva, name_of(rva), prof.get("size"), prof.get("nins")))
    for ins in disasm(rva):
        notes = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS:
                    notes.append("STR@%x %r" % (t, STRS[t][:60]))
                else:
                    notes.append("data@%x" % t)
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                notes.append("%s(0x%x)" % (name_of(op.imm), op.imm))
        print("    %-8x %-40s %s" % (ins.address, ins.mnemonic + " " + ins.op_str,
                                     ("; " + " | ".join(notes)) if notes else ""))

print()
print("=== 0x1380D0: the instruction windows around each call ===")
lines = []
for ins in disasm(0x1380D0):
    lines.append(ins)
for idx, ins in enumerate(lines):
    if ins.mnemonic == "call":
        op = ins.operands[0]
        tgt = op.imm if op.type == X86_OP_IMM else None
        print()
        print("  ---- call at 0x%x -> %s ----" % (ins.address,
                                                  name_of(tgt) if tgt else ins.op_str))
        for j in range(max(0, idx - 9), min(len(lines), idx + 4)):
            print("      %-8x %-38s" % (lines[j].address, lines[j].mnemonic + " " + lines[j].op_str))
