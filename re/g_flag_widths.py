# -*- coding: utf-8 -*-
"""For each flag setter, find the store that writes ITS field, by reading the function's real extent.

**THE PREVIOUS PROBE STARTED EVERY DISASSEMBLY AT A FIXED OFFSET AND RAN 120 BYTES**, so for a function whose real body is 40 bytes it read on into the NEXT function --
`setFillLastNestingStrategy 0x40` appeared to write `0x44` and `0x48`, which belong to `setShearMode` and `setPartialShearMode`. **A probe that does not know where a
function ends attributes its neighbours' stores to it.**

**SO THE FUNCTION'S EXTENT COMES FROM /re/exports_table.json** -- the size the project already measured -- and only the store inside that extent counts.
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

from lib import disasm  # noqa: E402

STORE = re.compile(r"^(byte|word|dword|qword) ptr \[(\w+)(?: \+ (0x[0-9a-f]+))?\],")

# the implementation -> the export whose row carries its rva
WANTED = {
    "setPartCommonCutMode": "SetPartCommonCutMode",
    "setFloatingMode": "CNS_SetFloatingMode",
    "setOriginPackingMode": "CNS_SetOriginPackingMode",
    "setFillLastNestingStrategy": "SetFillLastNestingStrategy",
    "setEvaluateIntermediateNestingsAsLast": "CNS_SetEvaluateIntermediateNesting",
    "setReorganizeBiggestPartNearOrigin": "SetReorganizeBiggestPartNearOrigin",
    "setReorganizeLongestPartNearOrigin": "SetReorganizeLongestPartNearOrigin",
    "setShearMode": "SetShearMode",
    "setPartialShearMode": "SetPartialShearMode",
}


def table():
    path = os.path.join(ROOT, "re", "exports_table.json")
    data = json.load(io.open(path, encoding="utf-8"))
    rows = data if isinstance(data, list) else data.get("exports", data.get("rows", []))
    out = {}
    for row in rows:
        if isinstance(row, dict) and "name" in row:
            out[row["name"]] = (int(row.get("rva", 0)), int(row.get("size", 0)))
    return out


def main():
    rows = table()
    print("%-40s %-9s %s" % ("implementation", "writes", "at"))
    for function, export in WANTED.items():
        if export not in rows:
            print("%-40s (no row for %s)" % (function, export))
            continue
        rva, size = rows[export]
        stores = []
        for instruction in disasm(rva):
            if instruction.address >= rva + size:
                break
            found = STORE.match(instruction.op_str)
            if found and found.group(2) in ("rsi", "rbx", "rdi", "rcx", "rax"):
                stores.append("%s @%s" % (found.group(1), found.group(3) or "+0x0"))
        print("%-40s %-9s %s" % (function, size, ", ".join(stores) or "(no store)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
