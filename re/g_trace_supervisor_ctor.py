# -*- coding: utf-8 -*-
"""Trace 0x32700 the way the objective says: establish the object register, then list the stores into it.

r12 is the destination (`mov r12, rcx` at 0x3271D) and rbx is the 0x530 byte allocation (`mov ecx, 0x530` at 0x32720 then `mov rbx, rax` at
0x32736). The state pointer goes in at 0x032AD2 `mov qword [r12 + 8], rbx`, so the object the destructor walks is `rbx`.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

FUNCTION = 0x32700
STORE = re.compile(r"^(byte|word|dword|qword|xmmword) ptr \[(\w+)(?: \+ (0x[0-9a-f]+))?\], (.+)$")


def main():
    size = (load_prof().get(FUNCTION) or {}).get("size") or 0
    print("0x%X, %d bytes" % (FUNCTION, size))
    print("")

    stores = []
    reads = []
    for instruction in disasm(FUNCTION):
        if instruction.address >= FUNCTION + size:
            break
        found = STORE.match(instruction.op_str)
        if not found:
            continue
        base = found.group(2)
        offset = int(found.group(3), 16) if found.group(3) else 0
        if base in ("rbx", "r12"):
            stores.append((base, offset, instruction.address, found.group(1), found.group(4)[:22]))

    print("stores into rbx (the 0x530 object) and r12 (the Supervisor): %d" % len(stores))
    for base, offset, address, kind, value in sorted(stores, key=lambda row: (row[0], row[1])):
        print("   [%-3s + 0x%-4X] at %06X  %-7s <- %s" % (base, offset, address, kind, value))

    print("")
    print("=== and the rip-relative addresses it loads, which name vtables")
    for instruction in disasm(FUNCTION):
        if instruction.address >= FUNCTION + size:
            break
        match = re.match(r"^r\w+, \[rip \+ (0x[0-9a-f]+)\]$", instruction.op_str)
        if instruction.mnemonic == "lea" and match:
            target = (instruction.address + instruction.size) + int(match.group(1), 16)
            print("   %06X -> 0x%X" % (instruction.address, target))
    return 0


if __name__ == "__main__":
    sys.exit(main())
