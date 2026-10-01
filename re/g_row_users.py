"""How do 0x13C380 (416 B) and 0x134470 (572 B) use the Row::Squeezer they build?

Compressed view: calls, double moves, member offsets and control flow only.
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
KEEP = ("movsd", "movapd", "addsd", "subsd", "mulsd", "divsd", "sqrtsd", "ucomisd", "comisd",
        "call", "ret", "jmp", "je", "jne", "jbe", "jae", "jb", "ja", "jl", "jg", "jle", "jge",
        "test", "cmp", "lea", "mov", "xor", "pxor")


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


for fn in (0x13C380, 0x134470):
    prof = PROF.get(fn) or {}
    print()
    print("=== 0x%x %s size=%s nins=%s ===" % (fn, name_of(fn), prof.get("size"), prof.get("nins")))
    for ins in disasm(fn):
        if ins.mnemonic not in KEEP:
            continue
        if ins.mnemonic in ("mov", "lea") and ins.operands:
            d = ins.operands[0]
            # keep only register<-memory/imm and memory<-register moves that matter
            if d.type == X86_OP_MEM and 0 <= d.mem.disp < 0x300 and ins.reg_name(d.mem.base) not in (
                    "rsp", "rbp"):
                pass
            elif d.type == 3 and d.mem.base == 41:
                pass
            elif ins.mnemonic == "mov" and d.type == 1:
                pass
            else:
                continue
        notes = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                notes.append("STR@%x %r" % (t, STRS[t][:40]) if t in STRS else "data@%x" % t)
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                notes.append("%s(0x%x)" % (name_of(op.imm), op.imm))
        print("   %-8x %-40s %s" % (ins.address, ins.mnemonic + " " + ins.op_str,
                                    ("; " + " | ".join(notes)) if notes else ""))
