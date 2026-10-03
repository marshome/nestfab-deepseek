# -*- coding: utf-8 -*-
"""Every engine class's vtable, from `re/vtables.json` rather than from a guess at an address.

**THE PREVIOUS VERSION HARD-CODED SEVEN VTABLE ADDRESSES TAKEN FROM PROSE, AND FIVE OF THEM WERE WRONG** -- it reported zero slots for `InfiniteEngine` and one for
`DelayedEngine`, which is what reading the wrong address looks like. **`re/vtables.json` has 443 entries keyed by MANGLED NAME, which is an oracle rather than a
location**, so the lookup is by name and the slots come with it.
"""
import io
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
VTABLES = os.path.join(ROOT, "re", "vtables.json")

WANTED = ["Engine", "InfiniteEngine", "MultiEngine", "DelayedEngine", "NestingEngine",
          "EquivalentEngine", "CloudEngine", "CompositeEngine", "EngineBase"]


def main():
    data = json.load(io.open(VTABLES, encoding="utf-8"))
    print("vtables.json holds %d entries" % len(data))
    print("")
    for wanted in WANTED:
        matches = [(name, entry) for name, entry in data.items() if wanted in name]
        if not matches:
            print("%-18s no entry whose mangled name contains it" % wanted)
            continue
        for name, entry in matches[:3]:
            slots = entry.get("slots") or []
            print("%-18s %-46s vtable rva 0x%-7X %d slot(s): %s"
                  % (wanted, name[:46], entry.get("vtable_rva", 0), len(slots),
                     " ".join("0x%X" % s for s in slots[:6])))
    print("")
    print("**AND THE NAMES OF THE ENGINE FAMILY, SO THE SET IS KNOWN RATHER THAN ASSUMED:**")
    for name in sorted(n for n in data if "Engine" in n and "Crypto" not in n and "Hex" not in n and "Proxy" not in n):
        print("   %-46s %d slot(s)" % (name[:46], len(data[name].get("slots") or [])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
