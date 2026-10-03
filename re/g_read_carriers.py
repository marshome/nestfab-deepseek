# -*- coding: utf-8 -*-
"""Read the three offset-named carriers' ACTUAL declarations, so the offsets are read and not recomputed.

**THE COMPARISON ABOVE SAID `IntFieldCarrier::field58` IS AT +0x64, WHICH IS WRONG.** +0x58 and +0x64 are different bytes, and the field's own NAME says +0x58 --
so the tool's arithmetic drifted and the pairing `field58 -> Order::padding08` is a false match. **A field whose name is its offset and whose comment disagrees
with its name is a field with two wrong halves**, and this reads what is actually declared.
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
LAYOUT = os.path.join(ROOT, "lcns", "include", "lcns", "dll_layout.hpp")

CARRIERS = ["IntFieldCarrier", "OptionFlagCarrier", "UnknownFlagCarrier", "LocalEngineCarrier"]


def main():
    text = io.open(LAYOUT, encoding="utf-8", errors="replace").read()
    for name in CARRIERS:
        match = re.search(r"(?:/\*\*.*?\*/\s*)?struct\s+%s\s*\{(.*?)\n\};" % re.escape(name), text, re.S)
        if not match:
            print("=== %s -- NOT FOUND" % name)
            continue
        print("=== %s" % name)
        for line in match.group(1).split("\n"):
            if line.strip():
                print("   %s" % line.strip()[:104])
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
