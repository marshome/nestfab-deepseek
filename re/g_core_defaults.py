"""Read the default config doubles and the three accessors that may override them.

0x6AABC0 prologue:
    xmm2 = [0x9B1A40] ; xmm3 = [0x9B1A48] ; xmm4 = [0x9B1A50]
    core[+0x08] = xmm2 ; core[+0x18] = xmm3 ; core[+0x20] = xmm4 ; core[+0x10] = 0 ; core[+0x30] = 0
    if (0x4FC2F0(arg2)) goto 0x6AC20A
    if (0x4FC300()) {
        rax = 0x4FC3C0(arg2)
        core[+0x20] = [rax+0x08]
        core[+0x18] = [rax+0x10]     <- the threshold actually used by 0x13C380
        core[+0x28] = (byte)[rax+0x18]
        core[+0x30] = [rax+0x20]
    }
"""
import struct
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()


def f64(rva):
    off = rva2off(rva)
    return struct.unpack("<d", data[off:off + 8])[0] if off is not None else None


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


print("=== default config doubles ===")
for rva in (0x9B1A40, 0x9B1A48, 0x9B1A50, 0x9B1A58):
    print("   0x%-8x = %r" % (rva, f64(rva)))

print()
for fn in (0x4FC2F0, 0x4FC300, 0x4FC3C0):
    prof = PROF.get(fn) or {}
    print("=== 0x%x %s size=%s nins=%s ===" % (fn, name_of(fn), prof.get("size"), prof.get("nins")))
    for ins in disasm(fn, count=40):
        note = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                note.append("STR@%x %r" % (t, STRS[t][:50]) if t in STRS else "data@%x" % t)
            elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                note.append("%s(0x%x)" % (name_of(op.imm), op.imm))
        print("   %-8x %-44s %s" % (ins.address, ins.mnemonic + " " + ins.op_str,
                                    ("; " + " | ".join(note)) if note else ""))
    print()

print("=== who else writes core+0x18 / core+0x20 after construction (setter search) ===")
print("    (scan for `movsd [reg+0x18/0x20]` near references to 0xA3BB40 / 0x6AABC0)")
for rva in sorted(PROF):
    try:
        ref = False
        for ins in disasm(rva):
            for op in ins.operands:
                if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                    t = ins.address + ins.size + op.mem.disp
                    if t in (0xA3BB40,):
                        ref = True
        if ref:
            print("   references 0xA3BB40: 0x%-8x %s size=%s" % (rva, name_of(rva),
                                                                 (PROF.get(rva) or {}).get("size")))
    except Exception:
        continue
