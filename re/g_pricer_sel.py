"""Resolve the six pricer factories and find who selects among them (the default variant)."""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()
# vtable address points (vptr targets) recovered earlier
KNOWN = {
    0xA3B0C0: "Prc::BoxPriceComputer",
    0xA3B100: "Prc::HullPriceComputer",
    0xA3B140: "Prc::AlphaPriceComputer",
    0xA3B180: "Prc::LinearCombinationPricer",
    0xA3B1C0: "Row::BasicDistancer",
    0xA3B1F0: "Row::Squeezer",
    0xA3B280: "Coin::CoinLP",
    0xA3ADA0 + 0x10: "Lp::LinearProgram",
    0xA3AED0 + 0x10: "Prc::PriceComputer",
}


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


FACTORIES = [0x4D9AD0, 0x4D9B00, 0x4D9B30, 0x4D9CD0, 0x4D9DE0, 0x4D9F80, 0x4D64C0]
print("=== what each factory installs ===")
for f in FACTORIES:
    prof = PROF.get(f) or {}
    print()
    print("--- 0x%x size=%s nins=%s" % (f, prof.get("size"), prof.get("nins")))
    for ins in disasm(f, count=40):
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in KNOWN:
                    print("      @0x%-7x lea -> 0x%x  = %s" % (ins.address, t, KNOWN[t]))
                elif t in STRS:
                    print("      @0x%-7x str -> %r" % (ins.address, STRS[t][:60]))
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM:
            t = ins.operands[0].imm
            print("      @0x%-7x call 0x%x %s" % (ins.address, t, name_of(t)))

print()
print("=== callers of each factory (the selection sites) ===")
for f in FACTORIES:
    callers = []
    for rva in sorted(PROF):
        try:
            for ins in disasm(rva):
                if (ins.mnemonic == "call" and ins.operands
                        and ins.operands[0].type == X86_OP_IMM and ins.operands[0].imm == f):
                    callers.append((rva, ins.address))
        except Exception:
            continue
    print("  0x%-8x <- %s" % (f, ", ".join("0x%x@0x%x %s" % (c, s, name_of(c))
                                          for c, s in callers) or "NO caller"))
