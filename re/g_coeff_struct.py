"""Who passes the 5-double coefficient struct to the pricer assembly 0x4D64C0?

obj (rdx of 0x4D64C0) is read at +0x00/+0x08/+0x10/+0x18/+0x20 as the four weights plus one more.
Its callers are 0x185EF0, 0x1A5B20, 0x4D84D0, 0x69D7C0 x2. Dump the context around each call so
the struct's origin (and therefore which RTTI name it carries) becomes visible.
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


SITES = [(0x185EF0, 0x186968), (0x1A5B20, 0x1A5E32), (0x4D84D0, 0x4D8588),
         (0x69D7C0, 0x69D865), (0x69D7C0, 0x69D9DA)]

for fn, site in SITES:
    prof = PROF.get(fn) or {}
    print()
    print("===== call to 0x4D64C0 at 0x%x, inside 0x%x %s size=%s nins=%s"
          % (site, fn, name_of(fn), prof.get("size"), prof.get("nins")))
    lines = list(disasm(fn))
    for idx, ins in enumerate(lines):
        if ins.address == site:
            for j in range(max(0, idx - 24), min(len(lines), idx + 8)):
                note = []
                for op in lines[j].operands:
                    if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                        t = lines[j].address + lines[j].size + op.mem.disp
                        if t in STRS:
                            note.append("STR@%x %r" % (t, STRS[t][:70]))
                        else:
                            note.append("data@%x" % t)
                    elif op.type == X86_OP_IMM and lines[j].mnemonic == "call":
                        note.append("%s(0x%x)" % (name_of(op.imm), op.imm))
                print("   %-8x %-40s %s" % (lines[j].address, lines[j].mnemonic + " " + lines[j].op_str,
                                            ("; " + " | ".join(note)) if note else ""))
            break
    # and any typeinfo / string the function references
    strings = []
    for ins in disasm(fn):
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in STRS and STRS[t] not in strings:
                    strings.append(STRS[t])
    if strings:
        print("   strings in 0x%x: %s" % (fn, [s[:48] for s in strings[:6]]))
