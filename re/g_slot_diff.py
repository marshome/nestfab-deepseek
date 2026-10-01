"""Normalised diff of the three near-identical append slots 5 / 6 / 7.

They share an identical member-offset signature (all three push 16 byte {value,a,b} triplets
into the +0x90 group), so the difference must be in control flow / extra calls. Normalise each
instruction to (mnemonic, operand kinds, explicit displacements) and diff the sequences.
"""
import re
import sys
import difflib

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

REG = re.compile(r"\b(r[a-z0-9]+|e[a-z]{2}|xmm\d+)\b")


def name_of(rva):
    return NAMES.get(rva) or "0x%x" % rva


def shape(ins):
    """mnemonic + operand kinds + displacements, registers abstracted away."""
    parts = []
    for op in ins.operands:
        if op.type == X86_OP_REG:
            parts.append("R")
        elif op.type == X86_OP_IMM:
            t = op.imm
            parts.append("CALL(%s)" % name_of(t) if ins.mnemonic == "call" else "imm")
        elif op.type == X86_OP_MEM:
            base = "RIP" if op.mem.base == X86_REG_RIP else "R"
            parts.append("M[%s+0x%x]" % (base, op.mem.disp))
        else:
            parts.append("?")
    return "%s %s" % (ins.mnemonic, ",".join(parts))


SLOTS = {5: 0x679670, 6: 0x679940, 7: 0x679420}
seqs = {}
for k, rva in SLOTS.items():
    seqs[k] = [shape(i) for i in disasm(rva)]
    print("slot %d = 0x%x : %d instructions" % (k, rva, len(seqs[k])))

print()
print("=== slot 5 vs slot 6 ===")
d = list(difflib.unified_diff(seqs[5], seqs[6], "slot5", "slot6", n=2, lineterm=""))
for line in d[:60]:
    print("   " + line)
print("   (diff lines: %d)" % len(d))

print()
print("=== slot 5 vs slot 7 ===")
d = list(difflib.unified_diff(seqs[5], seqs[7], "slot5", "slot7", n=2, lineterm=""))
for line in d[:60]:
    print("   " + line)
print("   (diff lines: %d)" % len(d))

print()
print("=== indirect calls per slot (target register) ===")
for k, rva in SLOTS.items():
    ind = []
    for ins in disasm(rva):
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type != X86_OP_IMM:
            ind.append((ins.address, ins.op_str))
    print("   slot %d: %s" % (k, ind if ind else "none"))
