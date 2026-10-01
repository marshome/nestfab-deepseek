"""Read BuildAndSolveLp (0x7D7200) -- the function that consumes a Coin::CoinLP.

Established just now:
    0x59AC0:  call 0x267730   ; construct Coin::CoinLP into a stack slot
              call 0x7D7200   ; BuildAndSolveLp(context, &coinLp)
and "BuildAndSolveLp" is a recovered internal name (out_g_names.txt), i.e. the function's own
symlog label. REPORT.md 7.3 listed "what LP Clp actually solves" as NOT determined; this is
that function.
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
TARGET = 0x7D7200


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


print("=== strings referenced inside 0x7D7200 (its own symlog label included) ===")
for ins in disasm(TARGET):
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            t = ins.address + ins.size + op.mem.disp
            if t in STRS:
                print("    @0x%-7x %r" % (ins.address, STRS[t][:100]))

print()
print("=== callees of 0x7D7200, in order ===")
for ins in disasm(TARGET):
    if ins.mnemonic == "call":
        op = ins.operands[0]
        if op.type == X86_OP_IMM:
            print("    @0x%-7x call 0x%-8x %s" % (ins.address, op.imm, name_of(op.imm)))
        elif op.type == X86_OP_MEM:
            print("    @0x%-7x call qword ptr [%s + 0x%x]   <- virtual dispatch"
                  % (ins.address, ins.op_str.split("[")[-1].split(" ")[0], op.mem.disp))

print()
print("=== callers of 0x7D7200 ===")
for rva in sorted(PROF):
    try:
        for ins in disasm(rva):
            if (ins.mnemonic == "call" and ins.operands
                    and ins.operands[0].type == X86_OP_IMM and ins.operands[0].imm == TARGET):
                print("    0x%-8x @0x%-8x %s" % (rva, ins.address, name_of(rva)))
    except Exception:
        continue

OUT = r"D:\Nesting\nestfab\re\out_g_buildandsolvelp.txt"
with open(OUT, "w", encoding="utf-8") as fh:
    print("#### 0x7D7200 BuildAndSolveLp size=%s nins=%s" % (
        (PROF.get(TARGET) or {}).get("size"), (PROF.get(TARGET) or {}).get("nins")), file=fh)
    for ins in disasm(TARGET):
        s = "%-8x %-40s" % (ins.address, ins.mnemonic + " " + ins.op_str)
        notes = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                notes.append("STR@%x %r" % (t, STRS[t][:70]) if t in STRS else "data@%x" % t)
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                notes.append("%s(0x%x)" % (name_of(op.imm), op.imm))
        if notes:
            s += "   ; " + " | ".join(notes)
        print(s, file=fh)
print()
print("wrote", OUT)
