# -*- coding: utf-8 -*-
"""Identify the vtables the Supervisor constructor installs: the `lea` targets ARE the table bases, not RVAs after subtraction.

**THE ONE FACT THAT SETTLES IT:** `re/vtables.json` records `Multi::Supervisor` with `vtable_rva = 0xA3B4D0`, and the constructor's `lea` at 0x032713 computes
**0xA3B4E0 = 0xA3B4D0 + 0x10**. So a stored value of the form `<recorded base> + 0x10` is the pointer a constructor installs, and `lib.u64` reads at an RVA --
**the value IS the RVA and no subtraction belongs anywhere.**
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib  # noqa: E402

# the five lea targets the trace found in 0x32700, plus the Supervisor's own
TARGETS = [0xA3B4E0, 0xA3BCF0, 0xA3B9B0, 0xA560C0, 0xA3B8F0, 0xA3BCC0]


def name_of(typeinfo_rva):
    if not (0 < typeinfo_rva < 0xB43000):
        return "(not an rva in the image)"
    name_rva = lib.u64(typeinfo_rva + 8)
    if not (0 < name_rva < 0xB43000):
        return "(the name pointer is not an rva)"
    offset = lib.rva2off(name_rva)
    if offset is None:
        return "(no file offset)"
    return lib.pe.get_data(offset, 200).split(b"\x00", 1)[0].decode("utf-8", "replace")


def main():
    data = lib.json.loads(open(os.path.join(HERE, "vtables.json"), encoding="utf-8").read())
    recorded = {}
    for value in data.values():
        recorded.setdefault(value["vtable_rva"] + 0x10, []).append(value.get("demangled"))

    print("%-12s %-12s %-10s %s" % ("installed", "base", "slots", "identity"))
    for target in TARGETS:
        base = target - 0x10
        words = [lib.u64(base + index * 8) for index in range(4)]
        known = recorded.get(target)
        if known:
            identity = "%s (recorded)" % ", ".join(known)
        elif words[1]:
            identity = "%s (from its typeinfo)" % name_of(words[1])
        else:
            identity = "no typeinfo"
        slots = 0
        probe = target
        while probe < 0xB43000:
            word = lib.u64(probe)
            if word in (0, None) or not (0 < word < 0xB43000):
                break
            slots += 1
            probe += 8
            if slots > 40:
                break
        print("%-12s 0x%-9X %-10d %s" % ("0x%X" % target, base, slots, identity))
    return 0


if __name__ == "__main__":
    sys.exit(main())
