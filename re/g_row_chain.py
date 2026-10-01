"""The Row:: construction chain: what does the strategy body actually build?

Chain recovered last round:
    0x6AABC0 (strategy body) -> 0x13C380 @0x6AC10C, 0x134470 @0x6AB72E
    0x134470 -> 0x133DE0 -> ...
    0x13C380/0x134470 -> 0x136B80 (99 B) -> Row::Squeezer ctor (0x138A20 / 0x138D60)
Dump the small links fully and the two call sites with their argument setup.
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


def dump(rva, count=None, note_rip=True):
    prof = PROF.get(rva) or {}
    print()
    print("=== 0x%x %s size=%s nins=%s ===" % (rva, name_of(rva), prof.get("size"), prof.get("nins")))
    for ins in disasm(rva, count=count):
        notes = []
        if note_rip:
            for op in ins.operands:
                if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                    t = ins.address + ins.size + op.mem.disp
                    if t in STRS:
                        notes.append("STR@%x %r" % (t, STRS[t][:60]))
                    else:
                        notes.append("data@%x" % t)
                elif op.type == X86_OP_IMM and ins.mnemonic == "call":
                    notes.append("%s(0x%x)" % (name_of(op.imm), op.imm))
        print("   %-8x %-42s %s" % (ins.address, ins.mnemonic + " " + ins.op_str,
                                    ("; " + " | ".join(notes)) if notes else ""))


def window(fn, site, back=24, fwd=8):
    print()
    print("=== window around 0x%x inside 0x%x %s ===" % (site, fn, name_of(fn)))
    lines = list(disasm(fn))
    for idx, ins in enumerate(lines):
        if ins.address == site:
            for j in range(max(0, idx - back), min(len(lines), idx + fwd)):
                notes = []
                for op in lines[j].operands:
                    if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                        t = lines[j].address + lines[j].size + op.mem.disp
                        notes.append("STR@%x %r" % (t, STRS[t][:50]) if t in STRS else "data@%x" % t)
                    elif op.type == X86_OP_IMM and lines[j].mnemonic == "call":
                        notes.append("%s(0x%x)" % (name_of(op.imm), op.imm))
                print("   %-8x %-42s %s" % (lines[j].address, lines[j].mnemonic + " " + lines[j].op_str,
                                            ("; " + " | ".join(notes)) if notes else ""))
            break


dump(0x136B80)
dump(0x138A20)
window(0x6AABC0, 0x6AC10C)
window(0x6AABC0, 0x6AB72E)
