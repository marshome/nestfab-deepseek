"""Print the assertion strings and ordered call sequence for the nofit_map cluster."""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()

TARGETS = [
    (0x59E9D0, "NoFitMapWithoutHoles"),
    (0x59CD10, "sub_59CD10"),
    (0x59C560, "sub_59C560"),
    (0x5A11B0, "sub_5A11B0"),
    (0x59C400, "sub_59C400"),
    (0x5A47B0, "sub_5A47B0"),
    (0x5BDD10, "sub_5BDD10"),
    (0x57D810, "sub_57D810"),
    (0x582940, "sub_582940"),
]

for rva, tag in TARGETS:
    print()
    print("===== 0x%x %s =====" % (rva, tag))
    ext = func_extent(rva)
    prof = PROF.get(rva) or {}
    print("    extent %s size %s insns %s" % ([hex(x) for x in ext] if ext else None,
                                             prof.get("size"), prof.get("nins")))
    for ins in disasm(rva):
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS:
                    print("    @0x%-7x %r" % (ins.address, STRS[t][:110]))
    calls = []
    for ins in disasm(rva):
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM:
            calls.append((ins.address, ins.operands[0].imm))
    print("    -- called functions in order --")
    seen = set()
    for site, t in calls:
        if t in seen:
            continue
        seen.add(t)
        nm = NAMES.get(t) or (PROF.get(t) or {}).get("name") or ""
        print("       @0x%-7x -> 0x%-8x %s" % (site, t, nm))
