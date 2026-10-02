#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""For every virtual slot: what the function IS, and who reaches it.

The chain the human asked for is slot -> implementation -> callers, and re/vtables.json holds the first link while re/prof (through lib)
holds the other two. This joins them:

    python g_vslot_impl.py [--class Multi::NestingNester] [--shared] [--top 30]

  * per slot: the address, the function's SIZE, its DIRECT caller count, and whether the profile knows it at all;
  * --shared: slots in different classes that point at the SAME address, which is what an inherited or a shared implementation is;
  * --class: one class's six or eight slots read out with their sizes, which is the shape of its interface.

WHY THE SHARED VIEW MATTERS. Eleven nester classes sharing a six-slot interface will share some slots outright -- a base implementation
that only some override -- and a slot pointing at the same address in several classes is EVIDENCE of a common base that the RTTI does not
state. That is the kind of clue the human means by following the thread: the vtables say which functions are one function.

A SELF-CHECK, per the rule: Engine::InfiniteEngine's slot 2 must be 0x759A80, which is already recorded. If not, the slot decoding is wrong.
"""
import argparse
import collections
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib as LIB           # noqa: E402
from lib import load_prof   # noqa: E402

FOREIGN = ("N8CryptoPP", "N5boost", "N6Json", "N9__gnu_cxx", "NSt7__cxx11", "N10__cxxabiv1", "N6Locale", "NSt6locale",
           "N5Clp", "N4Coin", "N8CoinUtils", "N3Osi", "N3Cbc", "N11CoinPresolve", "N6Ipopt", "N5Ipopt")

SELF_CHECK_OWNER = "Engine::InfiniteEngine"
SELF_CHECK_SLOT = 2
SELF_CHECK_ADDRESS = 0x759A80


def load_slots():
    data = json.loads(io.open(os.path.join(HERE, "vtables.json"), encoding="utf-8").read())
    out = []
    for mangled, entry in data.items():
        if any(mangled.startswith(prefix) for prefix in FOREIGN):
            continue
        owner = (entry.get("demangled") or "").strip()
        for index, address in enumerate(entry.get("slots") or []):
            out.append((owner, index, int(address)))
    return out


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--class", dest="owner")
    parser.add_argument("--shared", action="store_true")
    parser.add_argument("--top", type=int, default=30)
    args = parser.parse_args(argv)

    profile = load_prof()
    slots = load_slots()

    check = [row for row in slots if row[0] == SELF_CHECK_OWNER and row[1] == SELF_CHECK_SLOT]
    ok = check and check[0][2] == SELF_CHECK_ADDRESS
    print("SELF-CHECK: %s slot %d is 0x%X?  %s"
          % (SELF_CHECK_OWNER, SELF_CHECK_SLOT, SELF_CHECK_ADDRESS, bool(ok)))
    if not ok:
        print("REFUSING TO REPORT: the one slot already on record is not reproduced.")
        return 2
    print("")

    if args.owner:
        rows = [row for row in slots if row[0] == args.owner]
        print("%s: %d slot(s)" % (args.owner, len(rows)))
        for owner, index, address in sorted(rows, key=lambda r: r[1]):
            info = profile.get(address) or {}
            print("   slot %-2d 0x%-8X %6s B  %4d callers  %s"
                  % (index, address, info.get("size") or "?", len(set(info.get("callers") or [])),
                     "" if address in profile else "NOT IN THE PROFILE"))
        return 0

    if args.shared:
        by_address = collections.defaultdict(list)
        for owner, index, address in slots:
            by_address[address].append((owner, index))
        shared = {address: users for address, users in by_address.items() if len(users) > 1}
        print("addresses used by more than one class's slot: %d" % len(shared))
        print("")
        ranked = sorted(shared.items(), key=lambda kv: -len(kv[1]))
        for address, users in ranked[:args.top]:
            info = profile.get(address) or {}
            owners = sorted({owner for owner, _index in users})
            print("   0x%-8X %6s B  %4d callers  %2d classes" % (address, info.get("size") or "?",
                                                                  len(set(info.get("callers") or [])), len(owners)))
            print("        %s" % ", ".join(owners[:6]))
        return 0

    # the default view: the slots with the most callers, which are the ones a reconstruction meets first
    print("the virtual slots by how many times their function is called:")
    print("")
    rows = sorted(slots, key=lambda r: -len(set((profile.get(r[2]) or {}).get("callers") or [])))
    print("%-34s %-5s %-9s %-7s %s" % ("class", "slot", "address", "bytes", "callers"))
    for owner, index, address in rows[:args.top]:
        info = profile.get(address) or {}
        print("%-34s %-5d 0x%-8X %-7s %d"
              % (owner[:34], index, address, info.get("size") or "?", len(set(info.get("callers") or []))))
    print("")
    print("A slot whose function has many callers is one that is also called directly, so its address is reachable by two routes -- which")
    print("is why the ledger can establish it from a call site even when the vtable is the only way to know WHICH slot it fills.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
