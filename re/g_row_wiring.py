"""Where is the Row:: layer wired in? Climb from the constructors of BasicDistancer / Squeezer.

REPORT.md 7.3 listed the address-point references:
    Row::BasicDistancer 0xA3B1C0 -> 0x136AFE
    Row::Squeezer       0xA3B1F0 -> 0x138A34, 0x138BE8, 0x138CAA, 0x138D74
Find the owning functions and then every caller, one and two levels up, to see whether the
nester ever constructs them (i.e. whether row generation is reachable from nesting at all).
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


def owner_of(addr):
    for rva in sorted(PROF):
        ext = func_extent(rva)
        if ext and ext[0] <= addr < ext[1]:
            return rva
    return None


def callers_of(target, depth=2, seen=None, out=None):
    if seen is None:
        seen = set()
        out = []
    if target in seen or depth < 0:
        return out
    seen.add(target)
    for rva in sorted(PROF):
        try:
            for ins in disasm(rva):
                if (ins.mnemonic == "call" and ins.operands
                        and ins.operands[0].type == X86_OP_IMM and ins.operands[0].imm == target):
                    out.append((rva, ins.address, depth))
                    callers_of(rva, depth - 1, seen, out)
                    break
        except Exception:
            continue
    return out


TARGETS = {
    0xA3B1C0: "Row::BasicDistancer vtable address point",
    0xA3B1F0: "Row::Squeezer vtable address point",
}
for ap, label in TARGETS.items():
    print()
    print("=== references to %s (0x%x) ===" % (label, ap))
    sites = []
    for rva in sorted(PROF):
        try:
            for ins in disasm(rva):
                for op in ins.operands:
                    if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                        t = ins.address + ins.size + op.mem.disp
                        if t == ap:
                            sites.append((rva, ins.address))
        except Exception:
            continue
    owners = sorted(set(owner_of(s) for _, s in sites if owner_of(s)))
    for rva, site in sites:
        o = owner_of(site)
        print("   @0x%-8x in 0x%-8x %-22s size=%s" % (site, o or 0, name_of(o or 0),
                                                      (PROF.get(o or 0) or {}).get("size")))
    print("   -- callers, two levels up --")
    for o in owners:
        chain = callers_of(o, 2)
        if not chain:
            print("      0x%x %s : NO caller at all" % (o, name_of(o)))
        for f, s, d in chain[:12]:
            print("      %s0x%-8x %-24s size=%s (call @0x%x)"
                  % ("  " * (2 - d), f, name_of(f), (PROF.get(f) or {}).get("size"), s))
