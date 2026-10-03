# -*- coding: utf-8 -*-
"""Every function that calls the base constructor at 0xB4DA0, and what its own object looks like.

**THE BASE CONSTRUCTOR IS NOT EMPTY.** 0xB4DA0 writes `[rcx]` (the base vtable), `[rcx + 8]`, `[rcx + 0x10] = 99999`, `[rcx + 0x14] = -1` and `[rcx + 0x18]`, so
**the base class has four data fields and the current declaration has none.** This lists the constructors that call it, **because the set of them is the set of
derived classes, and their sizes bound how big the base part is.**

    python -u g_base_ctor.py 0xB4DA0
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

STORE = re.compile(r"^mov (byte|dword|qword) ptr \[(\w+)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\], (.+)$")


def main():
    address = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0xB4DA0
    profile = load_prof()
    entry = profile.get(address) or {}
    size = entry.get("size") or 0

    print("=" * 96)
    print("0x%X  size=%s  callers=%s" % (address, size, len(entry.get("callers") or [])))
    print("=" * 96)
    print("what it writes:")
    for instruction in disasm(address):
        if instruction.address >= address + size:
            break
        found = STORE.match(instruction.op_str)
        if found:
            print("   %08X  [%s + %s] <- %s"
                  % (instruction.address, found.group(2), found.group(3) or "0x0", found.group(4)))
    print("")

    print("**THE CALLERS -- each is another derived class's constructor, or a factory:**")
    for caller in sorted(entry.get("callers") or []):
        caller_entry = profile.get(caller) or {}
        caller_size = caller_entry.get("size") or 0
        allocation = None
        stores = 0
        for instruction in disasm(caller):
            if caller_size and instruction.address >= caller + caller_size:
                break
            if instruction.mnemonic == "mov" and instruction.op_str.startswith("ecx, 0x"):
                allocation = instruction.op_str.split(",")[-1].strip()
            if STORE.match(instruction.op_str):
                stores += 1
        print("   0x%08X  %-6s bytes  %-2d store(s)  %s"
              % (caller, caller_size, stores, ("allocates %s" % allocation) if allocation else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
