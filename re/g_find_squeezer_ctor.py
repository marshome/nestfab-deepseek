# -*- coding: utf-8 -*-
"""Find the real Row::Squeezer constructor: whoever installs vtable pointer 0xA3B1E0.

**THE CONSTRUCTOR 0x138A20 DOES NOT INSTALL IT.** It installs 0xA3B1F0 -- which is `Squeezer`'s own `[vtable + 0x20]`, a THUNK -- into the object it
allocates, and only writes the 0x270 byte Impl pointer at `[this + 8]`. The vtable pointer `Squeezer` itself uses is 0xA3B1E0, the same address
`Row::BasicDistancer`'s table holds at its `+0x20`, so `Squeezer` shares the thunk with the base. **SOMEONE ELSE INSTALLS 0xA3B1E0**, and this finds
them.
"""
import io
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

TARGET = 0xA3B1E0
IMAGE_BASE = 0x6B4C0000


def main():
    # show the thunk first
    offset = 0
    import lib
    print("the value 0xA3B1E0 resolves to code at RVA 0x%X:" % (TARGET - IMAGE_BASE))
    for instruction in disasm(TARGET - IMAGE_BASE, count=6):
        print("   %06X %-12s %s" % (instruction.address, instruction.mnemonic, instruction.op_str))
    print("")

    profile = load_prof()
    hits = []
    for address, info in profile.items():
        size = info.get("size") or 0
        if not size:
            continue
        for instruction in disasm(address):
            if instruction.address >= address + size:
                break
            if instruction.mnemonic != "lea" or "rip" not in instruction.op_str:
                continue
            for operand in instruction.operands:
                if operand.type == 3 and operand.mem.base == 41:
                    if instruction.address + instruction.size + operand.mem.disp == TARGET:
                        hits.append((address, instruction.address, size))
    print("functions that lea 0x%X:" % TARGET)
    for function, site, size in hits:
        callers = len(set((profile.get(function) or {}).get("callers") or []))
        print("   0x%-8X at 0x%-8X  %d bytes, %d callers" % (function, site, size, callers))
    if not hits:
        print("   none -- so the pointer is written from data rather than computed by an lea")
    return 0


if __name__ == "__main__":
    sys.exit(main())
