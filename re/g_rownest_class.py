"""Is 0x6AABC0 the body of RowNester::Run (0x913E0), or a different class in the same TU?

The project declares `RowNester : public Nester // RE 0xA3BB30, Run = 0x913E0`, while the body
that builds the Row::Squeezer is 0x6AABC0 (..\\multi\\row_nester.cpp). Determine the relation:
  * who calls 0x6AABC0
  * what 0x8F210 (its only caller one level up) is and what vtable it installs
  * whether 0x913E0 reaches 0x6AABC0
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
KNOWN_AP = {
    0xA3BB30: "Nester (project note)",
    0xA3BB60: "?",
    0xA3BB90: "?",
    0xA3BBC0: "?",
}


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


def callers_of(target):
    out = []
    for rva in sorted(PROF):
        try:
            for ins in disasm(rva):
                if (ins.mnemonic == "call" and ins.operands
                        and ins.operands[0].type == X86_OP_IMM and ins.operands[0].imm == target):
                    out.append((rva, ins.address))
        except Exception:
            continue
    return out


print("=== callers of 0x6AABC0 ===")
for rva, site in callers_of(0x6AABC0):
    print("   0x%-8x %-24s size=%-6s @0x%x" % (rva, name_of(rva), (PROF.get(rva) or {}).get("size"), site))

print()
print("=== does 0x913E0 (RowNester::Run?) reach 0x6AABC0? ===")
prof = PROF.get(0x913E0) or {}
print("   0x913E0 size=%s nins=%s" % (prof.get("size"), prof.get("nins")))
calls = set()
for ins in disasm(0x913E0):
    if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM:
        calls.add(ins.operands[0].imm)
print("   direct callees: %s" % ", ".join("0x%x %s" % (c, name_of(c)) for c in sorted(calls)))

print()
print("=== 0x8F210 in full (the caller of the strategy body) ===")
for ins in disasm(0x8F210):
    note = []
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            if t in KNOWN_AP:
                note.append("AP->%s" % KNOWN_AP[t])
            elif t in STRS:
                note.append("STR@%x %r" % (t, STRS[t][:40]))
            else:
                note.append("data@%x" % t)
        elif op.type == X86_OP_IMM and ins.mnemonic == "call":
            note.append("%s(0x%x)" % (name_of(op.imm), op.imm))
    print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str,
                                ("; " + " | ".join(note)) if note else ""))
