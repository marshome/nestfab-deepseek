# -*- coding: utf-8 -*-
"""Find the constructor that installs `Supervisor`'s state-object vtable at +0x478, and list what builds the 0x530 object.

**THE DESTRUCTOR 0x30B60 GIVES THE SHAPE AND NOT THE CONSTRUCTION**: it installs the class's own vtable through `lea rax, [rip + 0xa0a96f]` at 0x030B6A, reads the
state pointer with `mov rsi, [rcx + 8]`, calls `0x63F6D0` on SIX consecutive containers at +0x500 .. +0x528, walks an `unordered_map` at +0x4D0, and installs ONE
sub-object vtable at +0x478 with `lea rax, [rip + 0xa0b092]` at 0x030C57. **The class's own constructor is what establishes the layout**, so this finds every
function that stores the same two rip-relative addresses.
"""
import io
import os
import re
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

TARGETS = {
    0x30B6A + 0xA0A96F: "the class vtable installed at 0x030B6A (rip+0xa0a96f)",
    0x30C57 + 0xA0B092: "the sub-object vtable installed at 0x030C57 (rip+0xa0b092)",
}


def main():
    profile = load_prof()
    print("the two addresses the destructor stores:")
    for address, why in TARGETS.items():
        print("   0x%X   %s" % (address, why))
    print("")

    found = collections.defaultdict(list)
    for function, info in profile.items():
        size = info.get("size") or 0
        if not size:
            continue
        for instruction in disasm(function):
            if instruction.address >= function + size:
                break
            match = re.match(r"^r\w+, \[rip \+ (0x[0-9a-f]+)\]$", instruction.op_str)
            if instruction.mnemonic != "lea" or not match:
                continue
            target = (instruction.address + len(instruction.bytes)) + int(match.group(1), 16)
            if target in TARGETS:
                found[target].append((function, instruction.address))

    for address, why in TARGETS.items():
        sites = found.get(address, [])
        print("0x%X -- %d site(s)   %s" % (address, len(sites), why))
        for function, site in sites[:10]:
            size = (profile.get(function) or {}).get("size")
            print("      fn 0x%-8X at 0x%-8X  (%s bytes)" % (function, site, size))
        if not sites:
            print("      the address is not loaded by any function in the profile")
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
