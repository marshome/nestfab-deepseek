# -*- coding: utf-8 -*-
"""Read a function's STRING LITERALS and its calls -- the two things that identify what it is FOR.

**`lib.strings_of(rva)` ALREADY RESOLVES EVERY RIP-RELATIVE OPERAND THAT POINTS AT A KNOWN STRING**, so this does not need to compute displacements: an earlier version
did that by hand and called an `image_bytes()` that does not exist. **The module's own words are the evidence**, which is how `0x60A620` is known to be an internal-error
reporter and `0x910BA0` is known to be libstdc++.

    python -u g_read_function.py 0x978010 0x60A620
"""
import io
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))

from lib import disasm, load_prof, strings_of  # noqa: E402


def main():
    profile = load_prof()
    for argument in sys.argv[1:]:
        address = int(argument, 16)
        entry = profile.get(address) or {}
        size = entry.get("size") or 0
        print("=" * 96)
        print("0x%X  size=%s  insns=%s  callers=%s  callees=%s"
              % (address, size, entry.get("nins"), len(entry.get("callers") or []), len(entry.get("callees") or [])))
        print("=" * 96)

        texts = strings_of(address)
        print("STRINGS (%d):" % len(texts))
        for target, text in texts[:26]:
            print("   0x%08X  %r" % (target, text[:84]))
        print("")

        calls = []
        for instruction in disasm(address):
            if size and instruction.address >= address + size:
                break
            if instruction.mnemonic in ("call", "jmp"):
                calls.append((instruction.address, instruction.mnemonic, instruction.op_str))
        print("CALLS AND JUMPS (%d):" % len(calls))
        for at, mnemonic, op in calls[:24]:
            print("   %08X %-5s %s" % (at, mnemonic, op))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
