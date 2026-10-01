"""Dump the self-contained no-fit kernel sub_5A47B0 (327 insns, zero calls) and resolve
the 5-byte thunk sub_9984B0 that NoFitMapWithoutHoles calls 111 times."""
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
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or "sub_%x" % rva


# 1. resolve the thunk
insns = list(disasm(0x9984B0))
print("=== thunk 0x9984B0 ===")
for ins in insns:
    note = ""
    if ins.mnemonic == "jmp" and ins.operands and ins.operands[0].type == X86_OP_IMM:
        note = "  -> 0x%x %s" % (ins.operands[0].imm, name_of(ins.operands[0].imm))
    print("   %-8x %s %s%s" % (ins.address, ins.mnemonic, ins.op_str, note))

# 2. dump the kernel with annotations
OUT = r"D:\Nesting\nestfab\re\out_g_5a47b0.txt"
with open(OUT, "w", encoding="utf-8") as fh:
    print("#### 0x5A47B0 kernel  size=%s nins=%s" % ((PROF.get(0x5A47B0) or {}).get("size"),
                                                     (PROF.get(0x5A47B0) or {}).get("nins")), file=fh)
    for ins in disasm(0x5A47B0):
        s = "%-8x %-34s" % (ins.address, ins.mnemonic + " " + ins.op_str)
        notes = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS:
                    notes.append("STR@%x %r" % (t, STRS[t][:70]))
                else:
                    notes.append("data@%x" % t)
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                notes.append(name_of(op.imm))
        if notes:
            s += "   ; " + " | ".join(notes)
        print(s, file=fh)
print("wrote", OUT)
