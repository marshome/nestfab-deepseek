# -*- coding: utf-8 -*-
"""What a function talks about: the strings its own body loads, in order.

Usage: python g_talks.py 0x8A9510 [--limit 40] [--calls]

The cheapeast exports are blocked by three functions that call each other -- 0x8A9510 (4479 B), 0x8A82F0 (1517 B) and 0x8A8F90
(824 B) -- and reading 4479 bytes of strace from the top is slow. What identifies a function faster than its instructions is its
VOCABULARY: the strings it loads name the thing it does, and this project has three channels that prove it (assertion
conditions, `__PRETTY_FUNCTION__` arguments, and the member expressions inside them).

So this lists, in instruction order, every `lea reg, [rip+disp]` whose target is a readable string, with the calls interleaved so
the shape is visible: a function that loads `valid`, `version` and `number_of_nested_parts` and calls a JSON writer is a
serialiser, and no instruction reading is needed to know that.

`--calls` also prints each call in order with its target's size, so a body reads as a sequence of named steps and the places
where an unknown function sits become the next thing to look at.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_names as N  # noqa: E402
import lib as LIB    # noqa: E402
from lib import disasm, load_prof, rva2off  # noqa: E402

LEA = re.compile(r"^([a-z0-9]+), \[rip \+ 0x([0-9a-f]+)\]$")
PRINTABLE = re.compile(rb"[\x20-\x7e]{3,}")


def image():
    return LIB.data() if callable(getattr(LIB, "data", None)) else LIB.data


def main(argv):
    target = int(argv[0], 0)
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else 40
    show_calls = "--calls" in argv
    blob = image()
    profile = load_prof()
    info = profile.get(target) or {}
    size = info.get("size") or 0
    print("0x%X  %d bytes  %d callees  name: %s" % (target, size, len(info.get("callees") or []), N.direct(target) or "(none)"))
    print("")
    body = [i for i in disasm(target) if i.address < target + size]
    shown = 0
    for ins in body:
        m = LEA.match(ins.op_str)
        if ins.mnemonic == "lea" and m:
            code_address = ins.address + ins.size + int(m.group(2), 16)
            try:
                file_offset = rva2off(code_address)
            except Exception:
                continue
            if file_offset is None or not (0 <= file_offset < len(blob)):
                continue
            chunk = blob[file_offset:file_offset + 80]
            match = PRINTABLE.match(chunk)
            if not match or len(match.group(0)) < 3:
                continue
            text = match.group(0).decode("ascii", "replace")
            print("  0x%-8X str  %s" % (ins.address, text))
            shown += 1
            if shown >= limit:
                break
            continue
        if show_calls and ins.mnemonic == "call":
            mm = re.search(r"0x([0-9a-f]+)", ins.op_str)
            if mm:
                callee = int(mm.group(1), 16)
                callee_size = (profile.get(callee) or {}).get("size") or 0
                label = N.direct(callee) or ""
                if callee in profile:
                    print("  0x%-8X call 0x%X (%d B) %s" % (ins.address, callee, callee_size, label))
    print("")
    print("%d strings shown; the vocabulary above is what this function is about" % shown)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
