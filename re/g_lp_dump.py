"""Is 0x7CA830 a dump of the LP to a file, or a hand-off into the solver?

Facts so far: it sorts a vector of 16-byte {double,int,int} triplets (std::sort at 0x267A30),
then emits ~18 formatted numbers separated by the 3-space string '   ' through an ostream, with
exception handling around the stream. That is the shape of Clp's LP/MPS writer or an app side
debug dump -- NOT of loadProblem(). Settle it by looking for a dump path string and by
identifying the stream helpers.
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


print("=== strings that look like an LP/MPS/problem dump path ===")
keys = (".lp", ".mps", "cns", "Temp", "dump", "writeLp", "log")
for rva, s in sorted(STRS.items()):
    ls = s.lower()
    if any(k.lower() in ls for k in keys) and len(s) < 80:
        if any(k in s for k in (".lp", ".mps", "cns", "Temp", "dump")):
            print("    @0x%-8x %r" % (rva, s[:78]))

print()
print("=== who references a .lp / .mps / cns path string ===")
path_rvas = [r for r, s in STRS.items()
             if (".lp" in s or ".mps" in s or "cns_" in s) and len(s) < 80]
for target in path_rvas[:12]:
    for rva in sorted(PROF):
        try:
            for ins in disasm(rva):
                for op in ins.operands:
                    if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                        t = ins.address + ins.size + op.mem.disp
                        if t == target:
                            print("    %r @0x%x  referenced by 0x%x %s @0x%x"
                                  % (STRS[target][:50], target, rva, name_of(rva), ins.address))
        except Exception:
            continue

print()
print("=== identify the stream helpers ===")
for rva in (0x978010, 0x978750, 0x8264E0, 0x88BE60, 0x867BF0, 0x867DF0, 0x8693D0, 0x8691A0):
    prof = PROF.get(rva) or {}
    print("  --- 0x%x %s size=%s nins=%s" % (rva, name_of(rva), prof.get("size"), prof.get("nins")))
    strings = []
    callees = set()
    for ins in disasm(rva, count=60):
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS:
                    strings.append(STRS[t][:50])
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM:
            callees.add(ins.operands[0].imm)
    if strings:
        print("      strings: %s" % [s for s in strings[:4]])
    if callees:
        print("      callees: %s" % ", ".join("0x%x %s" % (c, name_of(c)) for c in list(callees)[:5]))
