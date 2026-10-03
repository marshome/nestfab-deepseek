# -*- coding: utf-8 -*-
"""Read a function's head and its strings -- the two things that say what it is for."""
import io
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))

from lib import disasm, load_prof, strings_of  # noqa: E402

TARGETS = [(0x756EC0, "DelayedEngine::run"), (0x755050, "MultiEngine::run"),
           (0x75BCC0, "EquivalentEngine::run"), (0x759B70, "CompositeEngine::run")]


def main():
    profile = load_prof()
    for address, label in TARGETS:
        entry = profile.get(address) or {}
        size = entry.get("size") or 0
        print("=" * 96)
        print("0x%X  %s  (%s bytes)" % (address, label, size))
        print("=" * 96)
        count = 0
        for instruction in disasm(address):
            if instruction.address >= address + size or count >= 18:
                break
            print("   %06X %-12s %s" % (instruction.address, instruction.mnemonic, instruction.op_str))
            count += 1
        texts = strings_of(address)
        print("   strings (%d): %s" % (len(texts), str(texts[:3])[:110]))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
