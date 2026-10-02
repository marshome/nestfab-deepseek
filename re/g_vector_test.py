# -*- coding: utf-8 -*-
"""Test the hypothesis: is the 0x18 byte element a std::vector header {begin, end, capacity}?

First attempt at this was an inline shell command whose `$` anchor passed through PowerShell as a literal backslash-dollar, so the
pattern matched nothing and reported zero. **That is the third time this session a one-liner's quoting has produced a false
negative**, and the fix is the one already recorded twice: write the tool as a FILE. This is that file.

libstdc++'s std::vector is three pointers -- begin, end, capacity_of_allocation -- which is 0x18 bytes on x86-64. So if the 0x18
element this project has seen five times is a vector, then every sighting should show the same three-slot discipline: reads of
+0x00 and +0x08 as a begin/end pair, a write of +0x08 and +0x10 after an allocation, and a `sub` of the two as a count.

This looks for that discipline in two ways:
  1. functions that store to +0x00, +0x08 AND +0x10 of the same register -- the "install a fresh vector" shape;
  2. functions that read +0x00 and +0x08 and then `sub` them -- the "count the elements" shape.
"""
import collections
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

STORE = re.compile(r"^\[([a-z0-9]+)(?:\s*\+\s*(0x[0-9a-f]+))?\],\s*(r[a-z0-9]+)$")
LOAD = re.compile(r"^([a-z0-9]+),\s*\[([a-z0-9]+)(?:\s*\+\s*(0x[0-9a-f]+))?\]$")
SUB = re.compile(r"sub\s+([a-z0-9]+),\s*([a-z0-9]+)")


def main():
    profile = load_prof()
    install = []
    count = []
    for address, info in sorted(profile.items()):
        size = info.get("size") or 0
        if not (40 <= size <= 1200):
            continue
        if address < 0x400000 or address > 0x9B0000:
            continue
        try:
            body = [i for i in disasm(address) if i.address < address + size]
        except Exception:
            continue
        if len(body) < 15:
            continue

        stores = collections.defaultdict(set)
        loads = collections.defaultdict(set)
        subs = []
        for ins in body:
            if ins.mnemonic == "mov":
                m = STORE.match(ins.op_str.strip())
                if m:
                    offset = int(m.group(2), 16) if m.group(2) else 0
                    if offset <= 0x20:
                        stores[m.group(1)].add(offset)
                m = LOAD.match(ins.op_str.strip())
                if m:
                    offset = int(m.group(3), 16) if m.group(3) else 0
                    if offset <= 0x20:
                        loads[m.group(2)].add(offset)
            m = SUB.match(ins.op_str.strip())
            if m:
                subs.append((m.group(1), m.group(2)))

        for register, offsets in stores.items():
            if {0x00, 0x08, 0x10} <= offsets:
                install.append((address, size, register, sorted(offsets)))
                break
        for register, offsets in loads.items():
            if {0x00, 0x08} <= offsets:
                for dest, source in subs:
                    if dest in register or source in register:
                        count.append((address, size, register, sorted(offsets)))
                        break
                else:
                    continue
                break

    print("=== the \"install a fresh vector\" shape: stores to +0, +8 and +0x10")
    print("found %d function(s)" % len(install))
    for address, size, register, offsets in install[:12]:
        callers = len(set((profile.get(address) or {}).get("callers") or []))
        print("   0x%-8X %4d B  reg %-4s offs %-22s callers %d" % (address, size, register, offsets, callers))
    print("")
    print("=== the \"count the elements\" shape: reads +0 and +8 then subs")
    print("found %d function(s)" % len(count))
    for address, size, register, offsets in count[:12]:
        callers = len(set((profile.get(address) or {}).get("callers") or []))
        print("   0x%-8X %4d B  reg %-4s offs %-22s callers %d" % (address, size, register, offsets, callers))
    print("")
    # and the specific addresses this project already knows
    print("=== the known sightings, checked against the two shapes")
    known = {0x23BF0: "the grow primitive", 0x22E40: "the element walk", 0x5CD5C0: "the box filler",
             0xC1A0: "the 24-byte move into order+0x188", 0x14A60: "the inline grow", 0x8C5090: "the nested walk"}
    for address, label in known.items():
        in_install = any(a == address for a, _s, _r, _o in install)
        in_count = any(a == address for a, _s, _r, _o in count)
        print("   0x%-8X %-34s install=%s count=%s" % (address, label, in_install, in_count))
    return 0


if __name__ == "__main__":
    sys.exit(main())
