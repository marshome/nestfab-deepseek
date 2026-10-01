"""Find the function that actually constructs the Prc pricers.

REPORT.md 7.3 listed `lea` sites of the four price-computer vtable address points as
0x4D9AE2 / 0x4D9B12 / 0x4D9B4E / 0x4D9D04 / 0x4D9E22 / 0x4D9FD9 and attributed them to
"0x4D64C0 = pricer factory". 0x4D64C0 is only 2257 bytes (ends at 0x4D6D91), so those sites lie
in a DIFFERENT function. Locate it and read how the variant is selected.
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
    best = None
    for rva in sorted(PROF):
        ext = func_extent(rva)
        if ext and ext[0] <= addr < ext[1]:
            best = rva
            break
    return best


SITES = [0x4D9AE2, 0x4D9B12, 0x4D9B4E, 0x4D9D04, 0x4D9E22, 0x4D9FD9]
print("=== owner functions of the price-computer construction sites ===")
owners = {}
for s in SITES:
    o = owner_of(s)
    if o is None:
        print("  0x%x : no owner" % s)
        continue
    owners.setdefault(o, []).append(s)
    print("  0x%-8x -> owner 0x%-8x %-20s size=%s" % (s, o, name_of(o),
                                                      (PROF.get(o) or {}).get("size")))

print()
print("=== each owner: strings + call structure (to see the selection) ===")
for o, sites in sorted(owners.items()):
    prof = PROF.get(o) or {}
    print()
    print("--- 0x%x %s size=%s nins=%s   (%d site(s))" % (o, name_of(o), prof.get("size"),
                                                          prof.get("nins"), len(sites)))
    seen = []
    for ins in disasm(o):
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS and (t, STRS[t]) not in seen:
                    seen.append((t, STRS[t]))
    for t, s in seen[:14]:
        print("      STR@0x%-8x %r" % (t, s[:70]))
    # the compares near each construction site give the selection
    lines = list(disasm(o))
    for target in sites:
        for idx, ins in enumerate(lines):
            if ins.address == target:
                print("      --- site 0x%x, preceding 16 instructions ---" % target)
                for j in range(max(0, idx - 16), idx + 2):
                    print("          %-8x %-40s" % (lines[j].address,
                                                    lines[j].mnemonic + " " + lines[j].op_str))
                break
