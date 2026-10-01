"""Context around each of the four sites that construct a Coin::CoinLP.

REPORT.md 7.3 gives the construction sites (the vtable address point 0xA3B280 is `lea`-ed at
0x26777C inside 0x267760, whose forwarding ctor 0x267730 is called from four places). This
prints the immediate context of each call so it is visible what happens to the object next.
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


SITES = [
    (0x59AED, "caller 0x59AC0", "contains the string \"linear\""),
    (0x24E2DB, "caller 0x24E2D0", ""),
    (0x25B0EF, "caller 0x25B040", ""),
    (0x6A6B73, "caller 0x6A6AD0", "class name contains \"Database\""),
]

for site, who, extra in SITES:
    print()
    print("===== construction site @0x%x   in %s %s =====" % (site, who, extra))
    owner_fn = None
    for rva in sorted(PROF):
        ext = func_extent(rva)
        if ext and ext[0] <= site < ext[1]:
            owner_fn = rva
            break
    if owner_fn is None:
        print("   (owner not found)")
        continue
    print("   owner 0x%x %s size=%s" % (owner_fn, name_of(owner_fn),
                                        (PROF.get(owner_fn) or {}).get("size")))
    lo = site - 0x60
    started = False
    for ins in disasm(owner_fn, maxlen=None):
        if ins.address < lo:
            continue
        started = True
        mark = " <<< construct" if ins.address == site else ""
        s = "   %-8x %-40s" % (ins.address, ins.mnemonic + " " + ins.op_str)
        notes = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS:
                    notes.append("STR@%x %r" % (t, STRS[t][:60]))
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                notes.append(name_of(op.imm) or ("0x%x" % op.imm))
        if notes:
            s += "  ; " + " | ".join(notes)
        print(s + mark)
        if ins.address > site + 0x90:
            break
    if not started:
        print("   (no instructions decoded in window)")
