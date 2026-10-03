# -*- coding: utf-8 -*-
"""Who references each engine vtable, and in what instruction.

**A DIRECT SEARCH FOR "STORES A VPTR" DEPENDS ON KNOWING THE SHAPE, AND THE SHAPE IS THE UNKNOWN.** So this goes the other way: the vtable's RVA is a known constant, and
any function that installs it must have that constant as the target of a rip-relative operand. **That is a fact about the image rather than a guess at an idiom.**
"""
import io
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))

import lib                                                        # noqa: E402
from lib import disasm, load_prof                                 # noqa: E402

VTABLES = json.load(io.open(os.path.join(ROOT, "re", "vtables.json"), encoding="utf-8"))
ENGINES = {name: entry["vtable_rva"] for name, entry in VTABLES.items()
           if name.startswith("N6Engine") and "Observer" not in name}


def main():
    profile = load_prof()
    functions = sorted(profile)
    print("looking for references to %d engine vtables" % len(ENGINES))
    print("")
    for name, vtable in sorted(ENGINES.items(), key=lambda kv: kv[1]):
        hits = []
        for address in functions:
            size = (profile[address] or {}).get("size") or 0
            if not size or size > 2000:
                continue
            for instruction in disasm(address):
                if instruction.address >= address + size:
                    break
                found = re.search(r"\[rip \+ (0x[0-9a-f]+)\]", instruction.op_str)
                if not found:
                    continue
                if instruction.address + instruction.size + int(found.group(1), 16) == vtable:
                    hits.append((address, (profile[address] or {}).get("size"), instruction.address,
                                 instruction.mnemonic + " " + instruction.op_str))
                    break
        print("%-30s vtable 0x%-7X %d referencing function(s)" % (name, vtable, len(hits)))
        for function, size, at, text in hits[:4]:
            print("      in 0x%-8X (%s bytes) at 0x%X: %s" % (function, size, at, text[:60]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
