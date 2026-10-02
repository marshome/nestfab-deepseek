#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Find a class's constructor and destructor by the instruction that installs its vtable.

THE LAYOUT, MEASURED by dumping 0xA3CFC0 (re/vtables.json gives `vtable_rva` = 0xA3CFD0 for Engine::InfiniteEngine):

    0xA3CFD0: 0x0000000000000000     the address point, NULL as this ABI leaves it
    0xA3CFD8: 0x000000006BED90F0     the RTTI typeinfo, at +8
    0xA3CFE0: 0x000000006BC19B20     SLOT 0, whose value is 0x759B20
    0xA3CFE8: 0x000000006BC19AD0     SLOT 1 = 0x759AD0
    0xA3CFF0: 0x000000006BC19A80     SLOT 2 = 0x759A80

so the FIRST SLOT'S ADDRESS is `vtable_rva + 0x10`, and a function that installs the vtable does

    0x759AD6  lea rax, [0xA3CFE0]     ; the first slot's ADDRESS
    0x759AE7  mov [rcx], rax          ; into the object's first quadword

**TWO BUGS MADE AN EARLIER VERSION REPORT ZERO**, and both are worth stating because they are the same mistake in two places: the
dictionary was keyed on the slots' VALUES (0x759B20) while the references are the slots' ADDRESSES (0xA3CFE0), and the offsets were computed
from the base rather than from `base + 0x10`. **The slots' values are code to call; their addresses are what a vtable pointer holds.**

    python g_find_ctors.py [--class Multi::NestingNester] [--limit 20]
"""
import argparse
import collections
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import load_prof, rip_targets  # noqa: E402

ADDRESS_POINT = 0x10    # the first slot's address, past the NULL address point and the typeinfo


def vtable_index():
    """{slot address -> (qualified name, slot index, vtable base)} -- keyed on ADDRESSES, which is what code references."""
    data = json.loads(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8").read())
    index = {}
    for mangled, entry in data.items():
        qualified = (entry.get("demangled") or "").strip()
        if not qualified:
            continue
        base = int(entry["vtable_rva"])
        for slot, _value in enumerate(entry.get("slots") or []):
            index[base + ADDRESS_POINT + slot * 8] = (qualified, slot, base)
    return index


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--class", dest="owner")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args(argv)

    profile = load_prof()
    index = vtable_index()
    hits = collections.defaultdict(list)
    for address, info in profile.items():
        if not info.get("size"):
            continue
        for target in rip_targets(address):
            found = index.get(target)
            if found:
                hits[found[2]].append((address, found[1]))

    print("slot addresses indexed: %d; vtables with at least one referenced slot: %d"
          % (len(index), len(hits)))
    print("")

    if args.owner:
        for base, entries in sorted(hits.items()):
            names = {q for q, _s, b in index.values() if b == base}
            if args.owner not in names:
                continue
            print("%s, vtable base 0x%X" % (args.owner, base))
            for start, slot in sorted(set(entries)):
                info = profile.get(start) or {}
                what = {0: "slot 0 -- what a CONSTRUCTOR installs",
                        1: "slot 1 -- the deleting destructor",
                        2: "slot 2 -- the destructor"}.get(slot, "slot %d" % slot)
                print("   function 0x%-8X (%5s B) references %s" % (start, info.get("size"), what))
            if not entries:
                print("   no code references this vtable")
        return 0

    rows = []
    for base, entries in hits.items():
        names = {q for q, _s, b in index.values() if b == base}
        rows.append((sorted(names)[0] if names else "?", base, sorted(set(entries))))
    rows.sort(key=lambda row: (-len(row[2]), row[0]))
    print("%-42s %-10s %s" % ("class", "vtable", "slot-0 references (constructor candidates)"))
    total_slot0 = 0
    for name, base, refs in rows[:args.limit]:
        slot0 = [start for start, slot in refs if slot == 0]
        total_slot0 += len(slot0)
        print("%-42s 0x%-8X %s" % (name[:42], base, " ".join("0x%X" % s for s in slot0[:3]) or "-- none --"))
    print("")
    print("across all %d vtables with a reference, %d reference SLOT 0, which is what a constructor installs."
          % (len(rows), total_slot0))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
