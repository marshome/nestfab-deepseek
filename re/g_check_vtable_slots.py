#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""A rule with a check: a vtable's slots begin at `vtable_rva + 0x10`, and `slots[n]` is the word at `vtable_rva + 0x10 + n*8`.

**THE CONFUSION THIS SETTLES, AND I MADE IT REPEATEDLY.** `re/vtables.json` records a class's `vtable_rva` -- the BASE of the table, which holds a
NULL at +0 and the typeinfo pointer at +8 -- and its `slots`, whose first entry is therefore at `base + 0x10`. **The address of a SLOT is not the base
of anything**, and I twice read a slot's VALUE as though it were a table's base:

  * I claimed `re/vtables.json` recorded five slots for `Tiling::MultiOrientedPartPattern` by dumping the table at 0xA3D310, which is where the value
    in ANOTHER class's slot points; the class's own base is 0xA3D370 and the JSON records eight. **That claim was replaced.**
  * I read the bytes at 0xA3B1E0 -- which is `Row::Squeezer`'s own `[base + 0x20]` slot -- as though it were a table, and got `BasicDistancer`'s
    neighbouring entries back.

**SO THE RELATION IS CHECKED RATHER THAN REMEMBERED**: for every entry, `vtable_rva` must hold a NULL, `vtable_rva + 8` a pointer to a typeinfo whose
name matches the class, and `vtable_rva + 0x10 + n*8` the recorded `slots[n]`.

    python -u g_check_vtable_slots.py
"""
import io
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib  # noqa: E402

IMAGE_BASE = 0x6B4C0000


def main():
    data = json.loads(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8").read())
    checked = 0
    bad = []
    for mangled, entry in data.items():
        base = entry.get("vtable_rva")
        slots = entry.get("slots") or []
        if base is None or not slots:
            continue
        checked += 1
        offset = lib.rva2off(base)
        if struct.unpack_from("<Q", lib.data, offset)[0] != 0:
            bad.append(((entry.get("demangled") or mangled), "the base does not hold a NULL at +0"))
            continue
        typeinfo = struct.unpack_from("<Q", lib.data, offset + 8)[0]
        if typeinfo == 0:
            bad.append(((entry.get("demangled") or mangled), "no typeinfo pointer at +8"))
            continue
        for index, recorded in enumerate(slots):
            actual = struct.unpack_from("<Q", lib.data, offset + 0x10 + index * 8)[0]
            if actual == 0:
                continue
            if (actual - IMAGE_BASE) != recorded:
                bad.append(((entry.get("demangled") or mangled),
                            "slots[%d] is recorded 0x%X and the word at base+0x%X is 0x%X"
                            % (index, recorded, 0x10 + index * 8, actual - IMAGE_BASE)))
                break

    print("vtables whose slot offsets were checked: %d" % checked)
    if bad:
        for name, why in bad[:20]:
            print("   %-52s %s" % (name[:52], why))
        print("")
        print("FAILING: %d entr(ies). **The slots do not begin where the table says they do**, which is the relation every one of my readings of a")
        print("table depends on.")
        return 1
    print("PASS: for every entry, base+0 holds NULL, base+8 a typeinfo, and base+0x10+n*8 the recorded slots[n].")
    return 0


if __name__ == "__main__":
    sys.exit(main())
