"""Did the reverse engineering establish the USE of COIN-OR Clp, or only its structure?

REPORT.md 7.3 established: the class hierarchy, the object layout (vptr at +0, ClpSimplex* at
+8), the four forwarding thunks, the constructor site 0x26777C (inside 0x267760), the init
constants, and the addColumn/addRow assembly routine 0x7CA830. What it explicitly lists as
NOT determined is "what LP Clp actually solves".

This script looks for the call sites that would constitute *use*:
  * the four ClpSimplex forwarding thunks 0x7CB700 / 0x7CB710 / 0x7CB720 / 0x7CB740
  * the assembly routine 0x7CA830 and slot 8 0x679D00
  * the constructor 0x267760 and its caller 0x267730
and dumps the constructor so the initialisation can be read.
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


TARGETS = {
    0x7CB700: "CoinLP slot +0x58 -> ClpSimplex[+0x248]",
    0x7CB710: "CoinLP slot +0x60 -> ClpSimplex[+0x228]",
    0x7CB720: "CoinLP slot +0x70 -> jmp 0x7CA830(r8d=1)",
    0x7CB740: "CoinLP slot +0x68 -> ClpSimplex[+0x230]",
    0x7CA830: "assembly routine (addColumn/addRow, 3778 B)",
    0x679D00: "CoinLP slot 8 (build/commit?)",
    0x6792C0: "Clp boundary-constant initialiser",
    0x267760: "CoinLP constructor",
    0x267730: "caller of the CoinLP constructor",
    0x7C9A10: "Clp objective accessor",
}

print("=== direct call sites of each target ===")
hits = {t: [] for t in TARGETS}
for rva in sorted(PROF):
    try:
        insns = list(disasm(rva))
    except Exception:
        continue
    for ins in insns:
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM:
            t = ins.operands[0].imm
            if t in hits:
                hits[t].append((rva, ins.address))

for t, why in TARGETS.items():
    print()
    print("0x%x  %s   size=%s" % (t, why, (PROF.get(t) or {}).get("size")))
    if not hits[t]:
        print("    NO direct call site anywhere in the image")
    for fn, site in hits[t]:
        print("    called from 0x%-8x @0x%-8x %s" % (fn, site, name_of(fn)))

print()
print("=== who references the CoinLP vtable address point 0xA3B280 ===")
for rva in sorted(PROF):
    try:
        insns = list(disasm(rva))
    except Exception:
        continue
    for ins in insns:
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t == 0xA3B280:
                    print("    0x%-8x @0x%-8x %s %s   (%s)" % (rva, ins.address, ins.mnemonic,
                                                               ins.op_str, name_of(rva)))

# dump the constructor and its caller
OUT = r"D:\Nesting\nestfab\re\out_g_coinlp_ctor.txt"
with open(OUT, "w", encoding="utf-8") as fh:
    for rva in (0x267730, 0x267760):
        ext = func_extent(rva)
        print("#### 0x%X %s  size=%s nins=%s ext=%s" % (
            rva, name_of(rva), (PROF.get(rva) or {}).get("size"),
            (PROF.get(rva) or {}).get("nins"),
            [hex(x) for x in ext] if ext else None), file=fh)
        for ins in disasm(rva):
            s = "%-8x %-40s" % (ins.address, ins.mnemonic + " " + ins.op_str)
            notes = []
            for op in ins.operands:
                if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                    t = ins.address + ins.size + op.mem.disp
                    if t in STRS:
                        notes.append("STR@%x %r" % (t, STRS[t][:80]))
                    else:
                        notes.append("data@%x" % t)
                elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                    notes.append("%s(0x%x)" % (name_of(op.imm), op.imm))
            if notes:
                s += "   ; " + " | ".join(notes)
            print(s, file=fh)
        print(file=fh)
print()
print("wrote", OUT)
