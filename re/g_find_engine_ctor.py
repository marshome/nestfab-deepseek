# -*- coding: utf-8 -*-
"""Find the ENGINE BASE constructor: a function that writes a vptr AND initialises +0x08, +0x10 and +0x18.

**THE COPY CONSTRUCTOR AT 0x754DE0 BOUNDED THE OBJECT AT 0x20 -- a vptr and three pointers -- AND COULD NOT NAME THE FIELDS because it copies the source's vptr rather
than installing one.** The function that INSTALLS a vptr is the constructor, and it is the one that can say what the three pointers are.

**AND THE DISCRIMINATOR IS THE `lea`**: a constructor writes `lea rax, [rip + disp]` and then stores `rax`, **while a copy constructor moves a register that came from
its argument.** So this looks for a `lea`-then-store pair, which is the shape a vptr installation has and a copy does not.

    python -u g_find_engine_ctor.py [lo hi]
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))

from lib import disasm, load_prof  # noqa: E402

LEA = re.compile(r"^lea (\w+), \[rip \+ (0x[0-9a-f]+)\]$")
STORE = re.compile(r"^mov (?:qword|dword) ptr \[(r\w+)(?: \+ (0x[0-9a-f]+))?\], (\w+)$")


def main():
    lo = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x700000
    hi = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x770000
    profile = load_prof()

    for address in sorted(profile):
        size = (profile[address] or {}).get("size") or 0
        if not size or not (lo <= address <= hi) or size > 300:
            continue
        body = []
        for instruction in disasm(address):
            if instruction.address >= address + size:
                break
            body.append(instruction)
        # a vptr installation: lea reg, [rip+d] ... mov [obj], reg
        vptr = None
        offsets = set()
        for instruction in body:
            found = LEA.match(instruction.op_str)
            if instruction.mnemonic == "lea" and found:
                vptr = (found.group(1), instruction.address + instruction.size + int(found.group(2), 16))
                continue
            stored = STORE.match(instruction.op_str)
            if instruction.mnemonic == "mov" and stored and vptr and stored.group(3) == vptr[0] and not stored.group(2):
                offsets.add(0)
            elif instruction.mnemonic == "mov" and stored and stored.group(2):
                offsets.add(int(stored.group(2), 16))
        if vptr and 0 in offsets and {0x8, 0x10, 0x18} <= offsets:
            callers = len((profile[address] or {}).get("callers") or [])
            print("0x%06X  %4d bytes  %2d callers  installs vtable rva 0x%X and writes +0x08 +0x10 +0x18"
                  % (address, size, callers, vptr[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
