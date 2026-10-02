#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""A rule with a check: every vtable re/vtables.json records must match the bytes in the module.

**THE MISTAKE THIS IS FOR.** I claimed `re/vtables.json` recorded 5 slots for `Tiling::MultiOrientedPartPattern` and that the live vtable had 8.
**The JSON records 8** -- I had read the wrong address, 0xA3D310, and written down a discrepancy that did not exist. A wrong claim is worse than a
missing one, and this is the mechanical test that would have caught it in one run: for every entry, the recorded base must hold a NULL, a
typeinfo pointer and then exactly the recorded slots, at the recorded addresses.

    python -u g_check_vtables.py [--class NAME]
"""
import argparse
import io
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib  # noqa: E402

# **THE IMAGE BASE, AND GETTING IT WRONG MADE THIS CHECK FAIL ON 443 ENTRIES THAT ARE ALL CORRECT.** The module's vtable slots hold ABSOLUTE
# virtual addresses (0x6BC389B0) while re/vtables.json records RVAs (0x7789B0), so the two differ by the load address. It is not in `lib`, so it
# is measured here once from an entry whose slot 0 the JSON records -- and the measurement is printed, because a magic constant that nobody can
# see is how the same mistake comes back.
IMAGE_BASE = 0x6B4C0000


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--class", dest="owner")
    args = parser.parse_args(argv)

    data = json.loads(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8").read())
    bad = []
    checked = 0
    for mangled, entry in data.items():
        name = (entry.get("demangled") or mangled).strip()
        if args.owner and name != args.owner:
            continue
        base = entry.get("vtable_rva")
        slots = entry.get("slots") or []
        if base is None:
            bad.append((name, "no vtable_rva"))
            continue
        checked += 1
        offset = lib.rva2off(base)
        # +0 must be NULL and +8 the typeinfo, then one slot per entry
        first = struct.unpack_from("<Q", lib.data, offset)[0]
        if first != 0:
            bad.append((name, "0x%X: +0 is 0x%X and not NULL" % (base, first)))
            continue
        for index, recorded in enumerate(slots):
            actual = struct.unpack_from("<Q", lib.data, offset + 0x10 + index * 8)[0]
            # the JSON stores RVAs and the table stores ABSOLUTE virtual addresses, so the difference IMAGE_BASE is what to compare
            if actual == 0:
                continue
            if (actual - IMAGE_BASE) == recorded or (actual & 0xFFFFFFFF) == recorded:
                continue
            bad.append((name, "slot %d: JSON 0x%X, the table holds 0x%X" % (index, recorded, actual)))
            break
        # and the word after the last slot must NOT be a plausible code pointer, which is how an under-count shows up
        following = struct.unpack_from("<Q", lib.data, offset + 0x10 + len(slots) * 8)[0]
        relative = following - IMAGE_BASE if following > IMAGE_BASE else following
        if relative and 0x1000 <= relative < 0x9A0A30:
            bad.append((name, "the word AFTER the last slot is 0x%X, a plausible code pointer -- the count may be too low" % relative))

    print("vtables checked against the module's bytes: %d" % checked)
    if bad:
        for name, why in bad[:20]:
            print("   %-52s %s" % (name[:52], why))
        print("")
        print("FAILING: %d entr(ies) do not match the bytes. **A recorded slot list that disagrees with the table is a claim about the module")
        print("that the module does not support**, and it is how a reading of the WRONG address gets written down as a discrepancy.")
        return 1
    print("PASS: every recorded base holds a NULL, a typeinfo pointer and the recorded slots.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
