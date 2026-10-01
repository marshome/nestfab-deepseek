"""Member-offset signature of every CoinLP vtable slot, so slots 4..8 can be told apart.

Slot 4 (0x6792C0) was shown to append into +0x18 / +0x30 / +0x48. The other append-style slots
(5 = 0x679670, 6 = 0x679940, 7 = 0x679420) must touch different members; listing every
`[reg+disp]` write/read offset per slot identifies which member each one maintains.
"""
import sys
from collections import Counter

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()

SLOTS = {
    2: (0x679C20, "init / reset"),
    3: (0x679660, "flag setter"),
    4: (0x6792C0, "append -> +0x18 / +0x30 / +0x48"),
    5: (0x679670, "append (per part)"),
    6: (0x679940, "?"),
    7: (0x679420, "?"),
    8: (0x679D00, "submit + solve"),
}


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


for k, (rva, why) in SLOTS.items():
    writes = Counter()
    reads = Counter()
    calls = []
    stack = Counter()
    for ins in disasm(rva):
        if not ins.operands:
            continue
        m = ins.mnemonic
        dst = ins.operands[0]
        if dst.type == X86_OP_MEM and dst.mem.base not in (0, X86_REG_RIP):
            reg = ins.reg_name(dst.mem.base)
            if reg in ("rsp", "rbp"):
                stack[dst.mem.disp] += 1
            elif m.startswith(("mov", "add", "sub", "or", "and", "xor", "movsd", "movaps",
                               "movups", "movapd", "movd", "movq")):
                writes[(reg, dst.mem.disp)] += 1
        for op in ins.operands[1:]:
            if op.type == X86_OP_MEM and op.mem.base not in (0, X86_REG_RIP):
                reg = ins.reg_name(op.mem.base)
                if reg not in ("rsp", "rbp"):
                    reads[(reg, op.mem.disp)] += 1
        if m == "call":
            op = ins.operands[0]
            if op.type == X86_OP_IMM:
                calls.append(name_of(op.imm) or "0x%x" % op.imm)
            else:
                calls.append("[" + ins.op_str.split("[")[-1])
    print()
    print("=== slot %d = 0x%x  %s  size=%s nins=%s" % (k, rva, why,
                                                      (PROF.get(rva) or {}).get("size"),
                                                      (PROF.get(rva) or {}).get("nins")))
    print("   writes : %s" % ", ".join("[%s+0x%x]x%d" % (r, d, n)
                                       for (r, d), n in sorted(writes.items(), key=lambda kv: -kv[1])[:14]))
    print("   reads  : %s" % ", ".join("[%s+0x%x]x%d" % (r, d, n)
                                       for (r, d), n in sorted(reads.items(), key=lambda kv: -kv[1])[:14]))
    print("   calls  : %s" % ", ".join(sorted(set(calls))[:12]))
