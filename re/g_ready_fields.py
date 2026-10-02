# -*- coding: utf-8 -*-
"""The ready exports' tail writes, and the type of the object sitting at the offset they write.

Usage: python g_ready_fields.py

An earlier round confirmed the pattern by hand: SetPipeMode (0xFCF0) writes the gate byte at +0x170, and
SetCommonCutParameters (0x3C3F0) writes +0x1A0, +0x1A8, +0x1B0, +0x1B8 and +0x1C0, which are exactly the fields that
Multi::RowNester's core reads through 0x4FC2F0 / 0x4FC300 / 0x4FC3C0. So an export that ENDS by writing a field of the order
names that field with its own name, and there are nine such exports that need no other reading at all.

This prints, for each of them, every store past +0x100 with the register and the value, and then answers the second half of
the question: if the value being stored came from a global vtable address (a `lea rax, [rip + ...]` a few instructions
earlier), which class's vtable is it? vtables.json maps those addresses to the demangled classes, and that is what turns
"the export writes +0x1A0" into "the export installs a ClpSimplex there".
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_names as N             # noqa: E402
import lib as LIB               # noqa: E402
from lib import disasm, load_prof, rva2off  # noqa: E402

IMAGE = LIB.data if isinstance(LIB.data, (bytes, bytearray)) else LIB.data()
READY = (0xD050, 0xEC90, 0xD1A0, 0xE010, 0xE940, 0xF130, 0x13E30, 0x13FE0, 0x188D0)
STORE = re.compile(r"^(byte|word|dword|qword|xmmword) ptr \[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\], (.+)$")
LEA = re.compile(r"^([a-z0-9]+), \[rip \+ 0x([0-9a-f]+)\]$")


def vtables():
    path = os.path.join(HERE, "vtables.json")
    try:
        data = json.load(io.open(path, encoding="utf-8"))
    except Exception:
        return {}
    index = {}
    for name, info in data.items():
        rva = info.get("vtable_rva")
        if rva:
            index[rva - 16] = name
            index[rva] = name
    return index


def main():
    profile = load_prof()
    vt = vtables()
    print("vtables indexed by address point: %d" % len(vt))
    print("")
    for addr in READY:
        info = profile.get(addr) or {}
        size = info.get("size") or 0
        body = [i for i in disasm(addr) if i.address < addr + size]
        hold = "rcx"
        for ins in body[:6]:
            m = re.match(r"^(rbx|rdi|rsi|r12|r13|r14|r15), rcx$", ins.op_str)
            if m:
                hold = m.group(1)
                break
        print("=== 0x%X  %-36s %4d B  first argument in %s" % (addr, N.direct(addr) or "", size, hold))
        shown = 0
        for index, ins in enumerate(body):
            m = STORE.match(ins.op_str)
            if not m:
                continue
            offset = int(m.group(3), 16) if m.group(3) else 0
            if offset < 0x100:
                continue
            value = m.group(4)
            note = ""
            if value in ("rax", "rdx", "rcx", "rbx") or True:
                for back in range(index - 1, max(-1, index - 8), -1):
                    lm = LEA.match(body[back].op_str)
                    if body[back].mnemonic == "lea" and lm and lm.group(1) == value:
                        nxt = body[back + 1].address if back + 1 < len(body) else body[back].address + 8
                        target = nxt + int(lm.group(2), 16)
                        cls = vt.get(target)
                        note = "  ; lea from 0x%X%s" % (target, (" = %s" % cls) if cls else "")
                        break
            print("    %08x  %s+0x%-5X %-8s <- %-8s%s" % (ins.address, m.group(2), offset, m.group(1), value, note))
            shown += 1
        if shown == 0:
            print("    no store past +0x100")
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
